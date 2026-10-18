from pathlib import Path
import tempfile
import unittest

from tools.apertium_probe import escape_text, statistics, units
from tools.benchmark import score
from tools.sample_external import sample


class ApertiumStream(unittest.TestCase):
    def test_escaped_delimiters_and_multiple_readings(self):
        parsed = units(r'^a\/b/a\/b<n>/other<n>$ ^x\$/x\$<n>$')
        self.assertEqual(parsed, [dict(surface='a/b', readings=['a/b<n>', 'other<n>']),
                                  dict(surface='x$', readings=['x$<n>'])])
        self.assertEqual(escape_text('a/b [c] ^$'), r'a\/b \[c\] \^\$')

    def test_malformed_stream_is_not_silently_counted(self):
        for stream in ['^x$', '^x/x', '^x/^y/y$', '^x/x$\\']:
            with self.subTest(stream=stream), self.assertRaises(ValueError):
                units(stream)

    def test_guessed_is_not_a_correctness_measure(self):
        counts = statistics(units('^foo/*foo$ ^bar/bar<n><cgguess>$ ^a/a<n>/a<v>$ ^./.<sent>$'))
        self.assertEqual(dict(counts), dict(word_cohorts=3, unknown=1, guessed=1,
                                           ambiguous=1, single_reading=1))


class ExternalSampling(unittest.TestCase):
    def test_reproducible_verbatim_and_unadjudicated(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)
            blocks = [('ord ' * 40) + str(i) for i in range(12)]
            (path/'source.txt').write_text('\n\n'.join(blocks), encoding='utf-8')
            catalogue = [dict(book='book', author='author', lang='nob', path='source.txt',
                              source='https://example.org/source')]
            result = sample(catalogue, path, 3, 'fixed-seed')
            self.assertEqual(result, sample(catalogue, path, 3, 'fixed-seed'))
            self.assertEqual(len(result), 3)
            for case in result:
                self.assertEqual(case['original'], blocks[case['source_block']])
                self.assertEqual(len(case['source_sha256']), 64)
                self.assertIsNone(case['reviewed_by'])
                self.assertTrue(all(d['accepted'] == [] for d in case['decisions']))
            with self.assertRaises(ValueError):
                score(result, [dict(id=c['id'],changes=[]) for c in result], human=False)

    def test_missing_provenance_rejected(self):
        with self.assertRaises(ValueError):
            sample([dict(book='book')], Path('.'), 1, 'seed')
        with self.assertRaises(ValueError):
            sample([], Path('.'), 0, 'seed')
