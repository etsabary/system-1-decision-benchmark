import unittest
import analyze_decision_additions_2026_10_21 as a


class AdditionAnalysisTests(unittest.TestCase):
    def test_partial_never_enters_combined_ranking(self):
        with self.assertRaises(AssertionError):
            a.combined({'status':'PARTIAL_NOT_RANKED'})

    def test_exact_original_question_bank(self):
        qs,plan = a.router.bank.prepare()
        self.assertEqual(len(qs),1342)
        self.assertEqual({p['item_id'] for p in plan},set(qs))
        self.assertEqual(a.router.bank.file_hash(a.router.bank.BANK),a.router.bank.BANK_HASH)


if __name__=='__main__':
    unittest.main()
