import unittest
from tools.benchmark import prepare, score, validate_cases


class Benchmark(unittest.TestCase):
    def setUp(self):
        self.case = dict(id='1', book='book-1', author='author-1', split='test', lang='nob',
                         original='han gik', reviewer_kind='human', reviewed_by='test fixture',
                         decisions=[dict(at=0, **{'from':'han'}, accepted=['han']),
                                    dict(at=4, **{'from':'gik'}, accepted=['gikk'])])

    def test_all_words_and_omissions_are_scored(self):
        result = score([self.case], [dict(id='1', changes=[])])
        self.assertEqual(result['total']['missed_normalisations'], 1)
        self.assertEqual(result['total']['correct_preservations'], 1)
        self.assertIsNone(result['total']['change_precision'])

    def test_wrong_and_right_changes(self):
        for target, metric in [('gikk','correct_changes'),('gikkk','incorrect_changes')]:
            result = score([self.case], [dict(id='1', changes=[dict(at=4, **{'from':'gik'}, to=target)])])
            self.assertEqual(result['total'][metric], 1)

    def test_incomplete_gold_cannot_be_scored(self):
        cases = prepare([self.case])
        with self.assertRaises(ValueError):
            score(cases, [dict(id='1', changes=[])])
        with self.assertRaises(ValueError):
            score(cases, [dict(id='1', changes=[])], human=False)

    def test_author_and_book_leakage_rejected(self):
        for other in [dict(self.case,id='2',book='book-2',split='train'),
                      dict(self.case,id='2',author='author-2',split='train')]:
            with self.assertRaises(ValueError):
                validate_cases([self.case, other])

    def test_duplicate_missing_or_stale_predictions_rejected(self):
        for predictions in [[], [dict(id='1',changes=[])] * 2,
                            [dict(id='1',changes=[dict(at=4,**{'from':'wrong'},to='gikk')])]]:
            with self.assertRaises(ValueError):
                score([self.case], predictions)
