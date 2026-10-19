"""Optional live-model regressions; normal tests do not install/download models."""
import json
import os
from pathlib import Path
import unittest

from rettskriv import book_engine


@unittest.skipUnless(os.environ.get('RETTSKRIV_DEPENDENCY_MODELS'), 'explicit local Stanza models required')
class LiveDependencyModels(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import torch
        from rettskriv.dependency import DependencyResolver
        torch.set_num_threads(4)
        cls.resolver = DependencyResolver(os.environ['RETTSKRIV_DEPENDENCY_MODELS'])
        cls.fixture = json.loads((Path(__file__).parent / 'fixtures/dependency-live.json').read_text())

    def test_reviewed_real_book_targets(self):
        for case in self.fixture['reviewed']:
            eng = book_engine([case['source']], lang=case['lang'], year=case['year'], nouncaps=case['nouncaps'])
            eng.names.update(case['names'])
            result = eng.modernise(case['source'], resolver=self.resolver)
            for target in case['targets']:
                with self.subTest(case=case['id'], target=target['at']):
                    token = next(t for t in result.tokens if t.word and t.start == target['at'])
                    self.assertEqual(token.text, target['word'])
                    self.assertEqual(token.out, target['expected'])
        self.assertEqual(self.resolver.errors, [])

    def test_no_new_edits_on_constructed_adversaries(self):
        for case in self.fixture['negatives']:
            eng = book_engine([case['source']], nouncaps=True)
            baseline = eng.modernise(case['source'])
            result = eng.modernise(case['source'], resolver=self.resolver)
            # Existing baseline decisions are not re-labelled as correct gold.
            with self.subTest(source=case['source']):
                self.assertEqual(result.text, baseline.text)
        self.assertEqual(self.resolver.errors, [])

    def test_inverted_homograph_preserves_protected_and_named_evidence(self):
        source = 'Da han blev voxen, drog han ud paa Vikingetog og ægtede en Kongedatter.'
        for word in ['drog', 'voxen', 'Vikingetog']:
            eng = book_engine([source], nouncaps=True)
            span = (source.index(word), source.index(word) + len(word))
            baseline = eng.modernise(source, protected=[span])
            result = eng.modernise(source, protected=[span], resolver=self.resolver)
            with self.subTest(protected=word):
                self.assertEqual(result.text, baseline.text)
        named = source.replace('drog', 'Drog')
        eng = book_engine([named], nouncaps=True)
        eng.names.add('Drog')
        self.assertEqual(eng.modernise(named, resolver=self.resolver).text,
                         eng.modernise(named).text)
        self.assertEqual(self.resolver.errors, [])

    def test_correlative_certification_and_outputs(self):
        from rettskriv.correlative import certified_adjunct
        cases = json.loads((Path(__file__).parent / 'fixtures/correlative-controls.json').read_text())
        for case in cases:
            eng = book_engine([case['source']], nouncaps=True)
            options = {'protected': case.get('protected', [])}
            before = eng.modernise(case['source'], **options)
            span = (case['at'], case['at'] + len(case['word']))
            with self.subTest(case=case['id']):
                self.assertEqual(certified_adjunct(eng, before.tokens, span) is not None,
                                 case['expect_certification'])
                result = eng.modernise(case['source'], resolver=self.resolver, **options)
                token = next(t for t in result.tokens if t.word and t.start == case['at'])
                expected = case['word'] if case['expected'] == 'preserve' else case['expected']
                self.assertEqual(token.out, expected)
        self.assertEqual(self.resolver.errors, [])
