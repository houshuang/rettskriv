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
