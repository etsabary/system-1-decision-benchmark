"""Offline checks for the author-approved early-stop rule."""
import unittest
import llm_screening_2026_10_18 as s


class Screening(unittest.TestCase):
    def evaluate(self,correct=50,invalid=4,median=2000,n=100):
        return s.gate({'attempted':n,'accuracy_attempted':correct/n},
                      {'model_output_failures':invalid},{'median_ms':median})

    def test_boundaries(self):
        self.assertEqual(self.evaluate(),[])
        self.assertIn('accuracy_below_50_percent',self.evaluate(correct=49))
        self.assertIn('model_output_failures_at_least_5_percent',self.evaluate(invalid=5))
        self.assertIn('median_above_2000_ms',self.evaluate(median=2000.001))

    def test_actual_prefix_denominator(self):
        self.assertEqual(self.evaluate(correct=100,invalid=9,n=200),[])
        self.assertIn('model_output_failures_at_least_5_percent',self.evaluate(correct=100,invalid=10,n=200))

    def test_minimum_screen_and_multiple_causes(self):
        with self.assertRaises(AssertionError):self.evaluate(n=99)
        self.assertEqual(len(self.evaluate(correct=30,invalid=20,median=3000)),3)


if __name__=='__main__':unittest.main()
