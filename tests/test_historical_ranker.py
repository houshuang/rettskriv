import copy
import json
from pathlib import Path
import unittest

from rettskriv import book_engine
from tools.sample_ranker import sample


class HistoricalPassages(unittest.TestCase):
    def test_documented_risky_candidates_remain_pending(self):
        cases = json.loads((Path(__file__).parent/'fixtures/historical-preservation.json').read_text())
        for case in cases:
            with self.subTest(case=case['id']):
                result = book_engine([case['original']],case['lang'],nouncaps=True).modernise(case['original'])
                token = next(t for t in result.tokens if t.start == case['target_at'])
                self.assertEqual(token.text,case['keep'])
                self.assertEqual(token.out,case['keep'])
                self.assertIn(token.reason,{'pending','ambiguous','name'})

    def test_real_word_split_stays_in_baseline_and_protection_excludes_target(self):
        text = 'Roti stoppede sin Pibe og begyndte at røge; tilslut gik han.'
        cases = [dict(id='sample',book='sample',author='Elster',split='dev',lang='nob',
                      original=text,nouncaps=True,protected=[(text.index('stoppede'),text.index('stoppede')+8)])]
        before = copy.deepcopy(cases)
        a,base = sample(cases)
        b,again = sample(cases)
        self.assertEqual((a,base),(b,again))
        self.assertEqual(cases,before)
        self.assertNotIn('stoppede',[t['from'] for t in a[0]['rank_targets']])
        self.assertTrue(any(e['from']=='tilslut' and e['to']=='til slutt' for e in base[0]['changes']))
        self.assertNotIn('decisions',a[0])  # sampling never invents labels

    def test_invalid_sampling_limit_rejected(self):
        cases = [dict(id='x',book='x',author='a',split='dev',lang='nob',original='han gik')]
        for limit in [0,-1,True,1.5]:
            with self.subTest(limit=limit),self.assertRaises(ValueError):
                sample(cases,limit)

    def test_dictionary_backed_variant_from_elster_and_explicit_protection(self):
        # Exact source substrings, Elster Tora Trondal blocks 115 and 229.
        for text in ["I et Øjeblik var de indviklede", "som atter for et Øjeblik havde"]:
            eng = book_engine([text], 'nob', nouncaps=True)
            result = eng.modernise(text)
            token = next(t for t in result.tokens if t.text == 'Øjeblik')
            self.assertEqual(token.out, 'øyeblikk')
            at = text.index('Øjeblik')
            protected = eng.modernise(text, protected=[(at, at + 7)])
            self.assertIn('Øjeblik', protected.text)
