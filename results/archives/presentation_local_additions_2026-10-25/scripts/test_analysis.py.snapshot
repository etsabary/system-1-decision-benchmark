"""Small independent fixtures for scoring and option-meaning alignment."""
import unittest
from analysis_core import correct,metrics,panels,panel_summary,normalize
from run_benchmark import packet,digest
import json


class AnalysisTests(unittest.TestCase):
    def test_missing_answer_is_not_a_wrong_valid_choice(self):
        rows=[{"item_id":"a","normalized_status":"error","normalized_choice":"","probability_warning":""}]
        m=metrics(rows,{"a":{"gold_option":"1"}})
        self.assertEqual((m["answered"],m["wrong"],m["unanswered"]),(0,0,1))

    def test_probability_rounding_does_not_discard_a_choice(self):
        raw={"model":"fixture","answers":{"decision":{"choice":"2","confidence":.8,"probabilities":{"1":.05,"2":.79,"3":.05,"4":.05,"5":.05}}}}
        row={"item_id":"a","status":"invalid_response","http_status":"200","raw_response_json":json.dumps(raw)}
        n=normalize(row)
        self.assertTrue(correct(n,{"a":{"gold_option":"2"}}))
        self.assertIn("sum",n["probability_warning"])

    def test_rotated_numbers_are_compared_by_meaning(self):
        rows=[{"item_id":str(i),"normalized_status":"ok","normalized_choice":str(i)} for i in range(1,6)]
        keys={str(i):{"gold_option":str(i),f"option_{i}_canonical":"answer"} for i in range(1,6)}
        selection={"panels":{"rotations":[{"item_ids":list(keys)}],"contrasts":[],"candidate_checks":[]}}
        p=panel_summary(panels(rows,keys,selection))
        self.assertEqual(p["rotation"]["consistent"],1)
        self.assertEqual(p["rotation"]["all_correct"],1)


if __name__=="__main__":unittest.main()
