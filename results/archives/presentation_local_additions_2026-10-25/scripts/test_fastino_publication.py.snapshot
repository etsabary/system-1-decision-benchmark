import json
import unittest
from unittest.mock import patch
import publish_fastino_2026_10_23 as b


class FastinoPublication(unittest.TestCase):
    def test_current_release(self):
        from validate_fastino_2026_10_23 import validate
        s=validate()
        self.assertEqual(s['models']['fastino_glide']['families']['F13']['correct'],18)

    def test_usage_price_is_not_a_monetary_receipt(self):
        s=json.loads((b.DEST/'statistics.json').read_text())
        f=s['models'][b.MID]
        self.assertTrue(b.price(b.MID,f).startswith('~$'))
        self.assertIsNone(f['cost']['api_reported_usd'])

    def test_no_new_questions_or_reweighting(self):
        s=json.loads((b.DEST/'statistics.json').read_text())
        old=json.loads((b.PREVIOUS_DEST/'statistics.json').read_text())
        self.assertEqual(s['question_bank_sha256'],old['question_bank_sha256'])
        for mid,model in old['models'].items():self.assertEqual(s['models'][mid],model)


if __name__=='__main__':unittest.main()
