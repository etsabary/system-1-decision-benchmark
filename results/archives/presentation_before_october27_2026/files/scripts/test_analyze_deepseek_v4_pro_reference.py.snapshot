"""Screening boundary checks; no model requests."""
import unittest

from analyze_deepseek_v4_pro_reference import gate


class Screening(unittest.TestCase):
    def stats(self, failed=0, median=1000):
        return {'n': 100, 'failed': failed, 'latency_first_all': {'median_ms': median}}

    def test_exact_cutoffs(self):
        initial = {'n': 100, 'accuracy': .5}
        self.assertTrue(gate(self.stats(4, 2000), initial)['pass'])
        self.assertFalse(gate(self.stats(5), initial)['pass'])
        self.assertFalse(gate(self.stats(0, 2000.01), initial)['pass'])
        self.assertFalse(gate(self.stats(), {'n': 100, 'accuracy': .49})['pass'])

    def test_incomplete_cannot_pass(self):
        self.assertFalse(gate(self.stats(), {'n': 99, 'accuracy': 1})['pass'])


if __name__ == '__main__':
    unittest.main()
