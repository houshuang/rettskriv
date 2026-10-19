import json
from pathlib import Path
import unittest
from unittest.mock import patch

from rettskriv import book_engine
from rettskriv.correlative import certified_adjunct, complete_pp, reduced_view
from rettskriv.dependency import DependencyResolver, Node, correlative_witness


class CorrelativeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.case = json.loads((Path(__file__).parent / 'fixtures/correlative-evidence.json').read_text())
        r = cls.case
        cls.engine = book_engine([r['source']], lang=r['lang'], year=r['year'], nouncaps=r['nouncaps'])
        cls.engine.names.update(r['names'])
        cls.trees = [{tuple(n['span']): Node(tuple(n['span']), n['upos'], frozenset(n['feats']),
                         n['relation'], tuple(n['head']) if n['head'] else None,
                         tuple((rel, tuple(at) if at else None) for rel, at in n['children']))
                      for n in tree} for tree in r['nodes']]

    def test_complete_pp_never_skips_unknown_or_finite_content(self):
        for text in ['ved denne Leilighed', 'ved et Offergilde paa Hlade*)', 'ved et Offergilde']:
            self.assertTrue(complete_pp(self.engine, text), text)
        for text in ['ved denne Fest', 'ved denne', 'ved denne Ubekjendtx', 'ved denne Leilighed som han havde',
                     'ved et Offergilde paa Ubekjendtx', 'ved et Offergilde paa Hlade (som Konge)',
                     'ved denne Leilighed og en Fest', 'ved et Offergilde paa Hlade**)']:
            self.assertFalse(complete_pp(self.engine, text), text)

    def test_real_source_mapping_and_optional_recovery(self):
        r, eng = self.case, self.engine
        baseline = eng.modernise(r['source'])
        cut, marker = certified_adjunct(eng, baseline.tokens, tuple(r['target']))
        expected = correlative_witness(*self.trees[:2], tuple(r['target']), marker)
        self.assertIsNotNone(expected)
        for normal in (False, True):
            view, mapping = reduced_view(baseline.tokens, cut, normal=normal)
            for token in baseline.tokens:
                if not token.word or cut[0] <= token.start < cut[1]:
                    continue
                original = (token.start, token.start + len(token.text))
                span = next(k for k, v in mapping.items() if v == original)
                self.assertEqual(view[span[0]:span[1]], token.out if normal else token.text)
            self.assertNotIn('saavel ved', view)
            self.assertNotIn('såvel ved', view)
        resolver = DependencyResolver(None, processors={'da': lambda _: None, 'nb': lambda _: None})
        with patch('rettskriv.dependency.aligned_nodes', side_effect=self.trees):
            result = eng.modernise(r['source'], resolver=resolver)
        changes = [(a.start, b.out) for a, b in zip(baseline.tokens, result.tokens) if a.out != b.out]
        self.assertEqual(changes, [(r['target'][0], r['expected'])])
        self.assertEqual(resolver.errors, [])
        self.assertEqual(''.join(t.text for t in result.tokens), r['source'])

    def test_protected_adjunct_and_wrong_original_arguments_refuse(self):
        r, eng = self.case, self.engine
        at = r['source'].index('Offergilde')
        protected = eng.modernise(r['source'], protected=[(at, at + 10)])
        self.assertIsNone(certified_adjunct(eng, protected.tokens, tuple(r['target'])))
        tokens = eng.modernise(r['source']).tokens
        _, marker = certified_adjunct(eng, tokens, tuple(r['target']))
        target = tuple(r['target'])
        bad = dict(self.trees[0])
        root = bad[target]
        bad[target] = Node(root.span, root.upos, root.feats, root.relation, root.head,
                            root.children + (('nsubj', (0, 6)),))
        self.assertIsNone(correlative_witness(bad, self.trees[1], target, marker))

    def test_reduced_parse_failure_never_partially_changes_text(self):
        r, eng = self.case, self.engine
        baseline = eng.modernise(r['source'])
        for position in (2, 3):
            outputs = self.trees[:position] + [RuntimeError('reduced parser failed')]
            resolver = DependencyResolver(None, processors={'da': lambda _: None, 'nb': lambda _: None})
            with patch('rettskriv.dependency.aligned_nodes', side_effect=outputs):
                result = eng.modernise(r['source'], resolver=resolver)
            self.assertEqual(result.text, baseline.text)
            self.assertEqual(resolver.errors, ['RuntimeError: reduced parser failed'])
