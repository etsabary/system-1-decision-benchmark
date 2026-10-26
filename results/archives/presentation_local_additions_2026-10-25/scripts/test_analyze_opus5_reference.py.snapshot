"""Offline regression checks for paired comparisons and honest missing costs."""
import unittest

import analyze_opus5_reference as run


class OpusAnalysis(unittest.TestCase):
    def rows(self, hits, n=1342):
        return [{'item_id': str(i), 'attempt': 1, 'status': 'ok',
                 'choice': '1' if i in hits else '2'} for i in range(n)]

    def test_matched_paired_counts_and_exact_probability(self):
        gold = {str(i): '1' for i in range(1342)}
        result = run.paired(self.rows({0, 1, 2}, 5), self.rows({0, 3}), gold)
        self.assertEqual(result['matched_n'], 5)
        self.assertEqual(result['both_correct'], 1)
        self.assertEqual(result['only_opus_correct'], 2)
        self.assertEqual(result['only_other_correct'], 1)
        self.assertEqual(result['neither_correct'], 1)
        self.assertEqual(result['exact_two_sided_mcnemar_p'], 1)

    def test_no_disagreements_has_probability_one(self):
        gold = {str(i): '1' for i in range(1342)}
        result = run.paired(self.rows({1}, 3), self.rows({1}), gold)
        self.assertEqual(result['exact_two_sided_mcnemar_p'], 1)

    def test_refusals_and_recoveries_do_not_replace_primary(self):
        gold = {str(i): '1' for i in range(1342)}
        records = [{'item_id': '0', 'attempt': 1, 'status': 'refusal', 'choice': None},
                   {'item_id': '0', 'attempt': 2, 'status': 'ok', 'choice': '1'}]
        result = run.paired(records, self.rows({0}), gold)
        self.assertEqual(result['only_other_correct'], 1)
        self.assertEqual(result['both_correct'], 0)

    def test_incomplete_comparator_is_rejected(self):
        gold = {str(i): '1' for i in range(1342)}
        with self.assertRaises(AssertionError):
            run.paired(self.rows({0}, 2), self.rows({0}, 2), gold)


if __name__ == '__main__':
    unittest.main()
