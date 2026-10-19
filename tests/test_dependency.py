import unittest
import json
from pathlib import Path
from unittest.mock import patch
from types import SimpleNamespace

from rettskriv import book_engine
from rettskriv.dependency import DependencyResolver, Node, agreement, independent_finite, inverted_motion_frame
from rettskriv.historical_verbs import candidates, infinitives, identities, VerbIdentity

FIN = frozenset({'VerbForm=Fin', 'Tense=Past', 'Mood=Ind'})


def node(span, relation='root', head=None, children=(), upos='VERB', feats=FIN):
    return Node(span, upos, feats, relation, head, tuple(children))


class DependencyTests(unittest.TestCase):
    def test_frozen_real_parser_evidence(self):
        # These freeze actual model outputs, not invented gold dependency trees.
        # Live-model book evaluation is separate and requires the optional models.
        rows = json.loads((Path(__file__).parent / 'fixtures/dependency-evidence.json').read_text())
        for row in rows:
            trees = []
            for records in row['nodes']:
                trees.append({tuple(n['span']): Node(
                    tuple(n['span']), n['upos'], frozenset(n['feats']), n['relation'],
                    tuple(n['head']) if n['head'] else None,
                    tuple((rel, tuple(span) if span else None) for rel, span in n['children'])) for n in records})
            with self.subTest(row=row['id']):
                anchors = frozenset(tuple(a) for a in row['finite_anchors'])
                self.assertEqual(agreement(*trees, (row['at'], row['at'] + len(row['word'])), anchors), row['accepted'])

    def setUp(self):
        self.subject, self.anchor, self.target = (0, 3), (4, 9), (20, 27)
        self.object = (10, 18)
        self.tree = {
            self.subject: node(self.subject, 'nsubj', self.anchor, upos='PRON', feats=frozenset()),
            self.object: node(self.object, 'obj', self.anchor, upos='NOUN', feats=frozenset()),
            self.anchor: node(self.anchor, children=(('nsubj', self.subject), ('obj', self.object), ('conj', self.target))),
            self.target: node(self.target, 'conj', self.anchor),
        }

    def test_requires_aligned_finite_governor_and_subject(self):
        self.assertTrue(agreement(self.tree, self.tree, self.target))
        for replacement in [
            node(self.target, 'conj', (40, 44)),
            node(self.target, 'amod', self.anchor),
            node(self.target, 'conj', self.anchor, feats=frozenset({'VerbForm=Part'})),
        ]:
            other = dict(self.tree, **{})
            other[self.target] = replacement
            self.assertFalse(agreement(self.tree, other, self.target))
        for changed in [
            node(self.anchor, children=(('nsubj', self.subject), ('aux:pass', (30, 33)))),
            node(self.anchor, children=(('nsubj', self.subject), ('nsubj', (40, 44)))),
            node(self.anchor, children=(('nsubj', None),)),
            node(self.anchor, upos='ADJ'),
            node(self.anchor, 'conj', self.target),  # cycle
        ]:
            other = dict(self.tree)
            other[self.anchor] = changed
            self.assertFalse(agreement(other, other, self.target))
        other = dict(self.tree)
        other[self.target] = node(self.target, 'conj', self.anchor, (('nsubj', self.subject),))
        other[self.anchor] = node(self.anchor, upos='NOUN')
        self.assertFalse(agreement(other, other, self.target))

    def test_caption_subject_is_not_finite_evidence(self):
        tree = dict(self.tree)
        tree[self.anchor] = node(self.anchor, children=(('nsubj', self.subject),))
        self.assertFalse(agreement(tree, tree, self.anchor))
        self.assertFalse(agreement(tree, tree, self.target))
        self.assertTrue(agreement(tree, tree, self.target, frozenset({self.anchor})))
        tree[self.anchor] = self.tree[self.anchor]
        tree[self.object] = node(self.object, 'obj', self.anchor, (('case', None),), upos='NOUN')
        self.assertFalse(agreement(tree, tree, self.target))

    def test_historical_ambiguity_survives_modern_dictionary_uniqueness(self):
        eng = book_engine(['du vandede blomsten'])
        self.assertEqual({x.infinitive for x in infinitives('vande')}, {'vande', 'vanne'})
        self.assertIsNone(eng.weak_past('vandede'))
        self.assertIsNone(eng.weak_past('voksede'))
        choices = candidates(eng.bank, 'vande')
        self.assertEqual(len({c.lemma for c in choices}), 2)
        forms = {c.infinitive: c.forms for c in choices}
        self.assertIn('vannet', forms['vanne'])
        self.assertNotIn('vannet', forms['vande'])
        self.assertNotIn('vandet', forms['vanne'])

    def test_missing_morphology_cannot_hide_alternative_identity(self):
        eng = book_engine(['du vandede blomsten'])
        with patch('rettskriv.historical_verbs.infinitives', return_value=(
                VerbIdentity('vanne', 'reviewed'), VerbIdentity('missingidentity', 'reviewed'))):
            choices = candidates(eng.bank, 'vande')
        self.assertEqual(len(choices), 2)
        self.assertEqual(choices[1].forms, frozenset())
        self.assertEqual(choices[1].lemma, '')

    def test_inventory_has_modern_morphology(self):
        eng = book_engine(['tekst'])
        for source in identities():
            with self.subTest(source=source):
                for choice in candidates(eng.bank, source):
                    self.assertTrue(choice.lemma)
                    self.assertTrue(choice.forms)

    def test_bounded_inversion_proves_homograph_without_global_override(self):
        for source in [
            'Da han blev voxen, drog han ud paa Vikingetog og ægtede en Kvinde.',
            'Da hun var ung, drog hun hjem og ægtede en Mand.',
            'Da han var ung, drog han ud paa Heste og ægtede en Kvinde.',
        ]:
            eng = book_engine([source], nouncaps=True)
            tokens = eng.modernise(source).tokens
            anchor = next(t for t in tokens if t.lower == 'drog')
            with self.subTest(source=source):
                self.assertTrue(inverted_motion_frame(eng, tokens, anchor))
                self.assertIn((anchor.start, anchor.start + len(anchor.text)), independent_finite(eng, tokens))
            subject_at = source.index('han') if 'han' in source else source.index('hun')
            protected = eng.modernise(source, protected=[(subject_at, subject_at + 3)]).tokens
            self.assertFalse(inverted_motion_frame(eng, protected, anchor))
            with patch.object(eng, 'subject_name', return_value=True):
                self.assertFalse(inverted_motion_frame(eng, tokens, anchor))
        for source in [
            'Det drog han aldrig havde mødt, forfærdede Børnene.',
            'Da han blev voxen, drog han havde set og forfærdede Børn.',
            'Da han blev voxen, drog han ud havde rejst og ægtede en Kvinde.',
            'Da han blev voxen, drog han ud paa Ukjendtx og ægtede en Kvinde.',
            'Da han blev voxen, drog de ud paa Jagt og ægtede en Kvinde.',
            'Billedtekst: drog han ud og forfærdede Børn.',
        ]:
            eng = book_engine([source], nouncaps=True)
            tokens = eng.modernise(source).tokens
            anchor = next(t for t in tokens if t.lower == 'drog')
            with self.subTest(source=source):
                self.assertNotIn((anchor.start, anchor.start + len(anchor.text)), independent_finite(eng, tokens))

    def test_protected_names_and_unresolved_forms_are_not_anchors(self):
        eng = book_engine(['han gikk'])
        tokens = eng.modernise('han gikk').tokens
        self.assertTrue(independent_finite(eng, tokens))
        with patch.object(eng, 'subject_name', return_value=True):
            self.assertFalse(independent_finite(eng, tokens))
        with patch.object(eng, 'modern_lower', return_value=None):
            self.assertFalse(independent_finite(eng, tokens))
        with patch.dict(eng.lexicon, {'gikk': [SimpleNamespace(keep=True)]}):
            self.assertFalse(independent_finite(eng, tokens))
        protected = eng.modernise('han gikk', protected=[(4, 8)]).tokens
        self.assertFalse(independent_finite(eng, protected))

    def test_role_assignment_resolves_choice_but_not_carded_material(self):
        eng = book_engine(['Axel Thordsøn, der kaarede hende til sin Brud.'], nouncaps=True)
        text = eng.modernise('Axel Thordsøn, der kaarede hende til sin Brud.').text
        self.assertIn('kåret henne til sin brud', text)
        for following in [' Ulden til sin Brud', ' dem til sin Brud', ' den til sin Brud',
                          ' hende til sin Uld', ' hende til sin Dukke', ' hende, til sin Brud']:
            self.assertEqual(len(candidates(eng.bank, 'kaare', following=following)), 2)
        self.assertEqual({c.infinitive for c in candidates(eng.bank, 'kaare', following=' ham til sin Konge')}, {'kåre'})

    def test_opt_in_keeps_lexicon_protected_verse_and_language(self):
        def forbidden(_):
            self.fail('Parser should not be called')
        resolver = DependencyResolver(None, processors={'da': forbidden, 'nb': forbidden})
        for source, kwargs in [('du vandede blomsten', {}),
                               ('Knut forøgede ved store Gaver Misfornøielsen.', {'verse': True}),
                               ('Knut forøgede ved store Gaver Misfornøielsen.', {'protected': [(5, 13)]})]:
            eng = book_engine([source], nouncaps=True)
            self.assertEqual(eng.modernise(source, **kwargs).text,
                             eng.modernise(source, resolver=resolver, **kwargs).text)
        eng = book_engine(['Eg forøgede.'], lang='nno')
        eng.modernise('Eg forøgede.', resolver=resolver)

    def test_parse_failure_preserves_conservative_output(self):
        source = 'Den listige Knut, Konge i Danmark, forøgede ved store Gaver Misfornøielsen.'
        eng = book_engine([source], nouncaps=True)
        before = eng.modernise(source).text
        for lang in ['da', 'nb']:
            for error in [RuntimeError, OSError, AssertionError, TypeError]:
                def broken(_):
                    raise error('test model failed')
                resolver = DependencyResolver(None, processors={'da': lambda _: None, 'nb': lambda _: None})
                resolver.processors[lang] = broken
                with patch('rettskriv.dependency.aligned_nodes', return_value={}):
                    self.assertEqual(eng.modernise(source, resolver=resolver).text, before)
                self.assertEqual(resolver.errors, [f'{error.__name__}: test model failed'])


if __name__ == '__main__':
    unittest.main()
