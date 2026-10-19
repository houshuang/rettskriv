import copy
import json
import unittest
from tools.context_ranker import apply, packet, targets


class ConstrainedRanker(unittest.TestCase):
    def setUp(self):
        self.cases = [dict(id='one', book='one', author='author', split='dev', lang='nob',
                           original='Han lader geværet.',
                           rank_targets=[dict(at=4, **{'from':'lader'}, candidates=['lader','lar'])],
                           decisions=[dict(secret_gold='MUST NOT LEAK')], reviewed_by='PRIVATE REVIEWER')]
        self.baseline = [dict(id='one', changes=[dict(at=4, **{'from':'lader'}, to='lar')])]

    def test_prompt_contains_no_gold_or_baseline(self):
        result = packet(self.cases)
        self.assertNotIn('MUST NOT LEAK', json.dumps(result))
        self.assertNotIn('PRIVATE REVIEWER', json.dumps(result))
        self.assertEqual(result, packet(self.cases))

    def test_abstention_removes_baseline_edit_without_mutation(self):
        before = copy.deepcopy(self.baseline)
        self.assertEqual(apply(self.cases,self.baseline,[dict(id='one',at=4,to=None)]),
                         [dict(id='one',changes=[])])
        self.assertEqual(before, self.baseline)

    def test_candidate_is_applied_at_original_offset(self):
        self.assertEqual(apply(self.cases,[dict(id='one',changes=[])],
                               [dict(id='one',at=4,to='lar')]),self.baseline)

    def test_incomplete_duplicate_stale_and_invented_answers_rejected(self):
        good = dict(id='one',at=4,to='lar')
        for answers in [[],[good,good],[dict(good,at=3)],[dict(good,id='other')],
                        [dict(good,to='lader gjerne')],[dict(good,confidence=1)]]:
            with self.subTest(answers=answers), self.assertRaises(ValueError):
                apply(self.cases,self.baseline,answers)

    def test_protected_target_cannot_be_overridden(self):
        self.cases[0]['protected'] = [(4,9)]
        self.assertEqual(targets(self.cases)[('one',4)]['candidates'], ['lader'])
        with self.assertRaises(ValueError):
            apply(self.cases,self.baseline,[dict(id='one',at=4,to='lar')])

    def test_stale_targets_and_baselines_rejected(self):
        self.cases[0]['rank_targets'][0]['from'] = 'ladet'
        with self.assertRaises(ValueError):
            packet(self.cases)
        self.setUp()
        for baseline in [[],self.baseline*2,[dict(id='one',changes=[dict(at=4,**{'from':'ladet'},to='lar')])]]:
            with self.assertRaises(ValueError):
                apply(self.cases,baseline,[dict(id='one',at=4,to=None)])

    def test_real_baseline_word_split_survives_target_selection(self):
        self.cases[0]['original'] = 'Han lader geværet tilslut.'
        change = dict(at=self.cases[0]['original'].index('tilslut'), **{'from':'tilslut'}, to='til slutt')
        baseline = [dict(id='one', changes=[change])]
        result = apply(self.cases, baseline, [dict(id='one', at=4, to=None)])
        self.assertEqual(result, baseline)
        with self.assertRaises(ValueError):
            apply(self.cases, baseline, [dict(id='one', at=4, to='lar gå')])
