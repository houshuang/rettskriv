import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from rettskriv import book_engine, engine, modernise, modernise_result
from rettskriv.lexicon import load, parse_when
from rettskriv.statistics import precision_lower
from tools import accept_report


class Conditions(unittest.TestCase):
    def test_rejects_unknown_missing_empty_and_contradictory_conditions(self):
        for condition in ('nexxt=han', 'next', 'cap=yes', 'next=', 'next=han|',
                          'before=no', 'before=1900|1910', 'cap;lower', 'mid;initial'):
            with self.subTest(condition=condition), self.assertRaises(ValueError):
                parse_when(condition)

    def test_typed_names_validate_and_do_not_trust_notes(self):
        from rettskriv.text import tokenise
        eng = engine()
        for word in ['Hakon', 'Frederik', 'Rusland']:
            self.assertTrue(eng.subject_name(tokenise(word)[0]))
            self.assertFalse(eng.subject_name(tokenise(word.lower())[0]))
        for word in ['Menneskes', 'Dyrs', 'Krigens']:
            self.assertFalse(eng.subject_name(tokenise(word)[0]))
        for row in ['hakon,=,,,x,unknown', 'hakon,Håkon,,,x,name', 'hakon,=,cap,,x,name']:
            with tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                (root / 'bokmal').mkdir()
                (root / 'bokmal' / 'names.csv').write_text('source,target,when,note,origin,kind\n' + row + '\n')
                with patch('rettskriv.lexicon.LEXICON', root), self.assertRaises(ValueError):
                    load('nob')

    def test_shipped_lexicons_validate(self):
        self.assertTrue(load('nob'))
        self.assertTrue(load('nno'))


class Acceptance(unittest.TestCase):
    def setUp(self):
        self.units = [{'changes': [{'n': 1, 'from': 'gik', 'to': 'gikk'}]}]
        self.ok = dict(n='1', kind='ok', **{'from': 'gik', 'to': 'gikk'}, better='', note='')

    def test_explicit_correct_review(self):
        self.assertEqual(accept_report.validate(self.units, [self.ok])[0], 1)

    def test_rejects_missing_duplicate_unknown_and_stale_reviews(self):
        for rows in ([], [self.ok, self.ok], [dict(self.ok, n='2')],
                     [dict(self.ok, to='wrong')], [dict(self.ok, kind='typo')]):
            with self.subTest(rows=rows), self.assertRaises(ValueError):
                accept_report.validate(self.units, rows)

    def test_no_reviewer_files_cannot_report_zero_errors(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(accept_report, 'EVAL', Path(folder)):
            (Path(folder) / 'sample.json').write_text(json.dumps(self.units))
            with self.assertRaises(ValueError):
                accept_report.report('sample')
            self.assertFalse((Path(folder) / 'sample.review.tsv').exists())

    def test_confidence_is_not_observed_accuracy(self):
        self.assertAlmostEqual(precision_lower(30, 30), .904966147, places=8)
        self.assertLess(precision_lower(597, 597), .995)
        self.assertGreater(precision_lower(598, 598), .995)
        self.assertLess(precision_lower(99, 100), precision_lower(100, 100))
        self.assertEqual(precision_lower(0, 100), 0)


class LinguisticSafeguards(unittest.TestCase):
    def test_audited_homographs_abstain(self):
        self.assertEqual(modernise('han lader Geværet', nouncaps=True), 'han lader geværet')
        self.assertEqual(modernise('Han voksede Bordet.', nouncaps=True), 'Han voksede bordet.')

    def test_plural_uses_the_actual_paradigm(self):
        self.assertEqual(modernise('de sige det', nouncaps=True), 'de sier det')
        self.assertEqual(modernise('de tage det', nouncaps=True), 'de tar det')
        self.assertEqual(modernise('de skulle sige det', nouncaps=True), 'de skulle si det')

    def test_weak_past_does_not_introduce_frequent_irregular_reading(self):
        self.assertEqual(modernise('heldede han sig', nouncaps=True), 'hellet han seg')

    def test_passive_voice_is_not_changed_to_active(self):
        self.assertEqual(modernise('de bruges til Smykker', nouncaps=True), 'de brukes til smykker')

    def test_participles_are_not_past_tense_without_positive_context(self):
        for text, kept in [('vi var saa bedrøvede', 'bedrøvede'),
                           ('med sit kronede Hoved', 'kronede'),
                           ('de vare fuldkommen helbredede', 'helbredede')]:
            self.assertIn(kept, modernise(text, nouncaps=True))

    def test_abbreviated_title_protects_name(self):
        self.assertEqual(modernise('Jeg saae Hr. Baat.', nouncaps=True), 'Jeg så Hr. Baat.')
        # A full title can end a sentence: Lie Den Fremsynte block 111.
        self.assertIn('Presten', modernise('den lille Doktor . Præsten spillede', nouncaps=True))
        # A title after a title is not itself a surname (Pan blocks 44/190).
        self.assertEqual(modernise('Hr . Løjtnant Baat', nouncaps=True), 'Hr . Løytnant Baat')
        self.assertEqual(modernise('Hr . Kaptejn Baat', nouncaps=True), 'Hr . Kaptein Baat')
        # MeMo Pan block 174 spaces punctuation; also accept compact typography.
        result = modernise_result('Hr . Mack truer dig.', nouncaps=True)
        self.assertEqual(next(t.reason for t in result.tokens if t.text == 'Mack'), 'name')
        for title in ['Hr . ', 'Hr. ', 'Hr.', 'Hr \n.\n']:
            self.assertEqual(modernise('Jeg saae ' + title + 'Baat.', nouncaps=True),
                             'Jeg så ' + title + 'Baat.')

    def test_untrusted_candidate_cannot_feed_grammar(self):
        eng = engine()
        with patch.object(eng, 'rule_target', return_value=('si', ('not-trusted',))):
            self.assertIsNone(eng.modern_lower('xyzunknown'))
            self.assertIsNone(eng.plural_present('xyzunknown'))

    def test_full_morphology_retains_lemma_and_features(self):
        bank = engine().bank
        self.assertEqual(bank.inflect('si', 'verb:inf', 'verb:pres'), {'sier'})
        self.assertTrue(all(a.lemma and a.paradigm and a.tags for a in bank.analyses('huset')))
        self.assertTrue(any('be' in a.tags.split() for a in bank.analyses('huset')))

    def test_explicit_protected_spans_keep_original_and_offsets(self):
        text = 'Han skrev «gik ud» og gik.'
        start = text.index('gik'); end = text.index('»')
        result = modernise_result(text, protected=[(start, end)])
        self.assertEqual(result.text, 'Han skrev «gik ud» og gikk.')
        self.assertEqual(result.map_offset(start), start)
        self.assertEqual([c['from'] for c in result.changes], ['gik'])
        with self.assertRaises(ValueError):
            modernise(text, protected=[(-1, 3)])

    def test_book_state_is_not_shared(self):
        a = book_engine(['Jonas Lie skrev Bøger.'], nouncaps=False, year=1850)
        b = book_engine(['Huset var stort.'], nouncaps=True, year=1900)
        self.assertIsNot(a, b)
        self.assertEqual(a.year, 1850)
        self.assertFalse(a.nouncaps)
        self.assertEqual(a.modernise('og Lie sagde').text, 'og Lie sa')
        self.assertEqual(b.year, 1900)
        self.assertIs(a.bank, b.bank)
