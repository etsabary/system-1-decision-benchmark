import json
import unittest

import publish_local_2026_10_25 as b


class LocalPublication(unittest.TestCase):
    def test_public_release(self):
        from validate_local_2026_10_25 import validate
        s=validate()
        self.assertEqual(s['model_count'],46)

    def test_local_cost_is_unmeasured_and_not_an_invented_zero(self):
        s=json.loads((b.DEST/'statistics.json').read_text())
        for mid in s['local_model_ids']:
            m=s['models'][mid]
            self.assertIsNone(m['cost']['known_usd'])
            self.assertEqual(b.price(mid,m),'Local compute cost unmeasured')
        self.assertNotIn('$0',b.price(s['local_model_ids'][0],s['models'][s['local_model_ids'][0]]))

    def test_previous_measurements_are_identical(self):
        s=json.loads((b.DEST/'statistics.json').read_text())
        previous=json.loads((b.prior.DEST/'statistics.json').read_text())
        self.assertEqual({mid:s['models'][mid] for mid in previous['models']},previous['models'])

    def test_screens_are_not_ranked_as_full_runs(self):
        s=json.loads((b.DEST/'statistics.json').read_text())
        screens=json.loads((b.DEST/'screened_routes.json').read_text())
        for row in screens:
            self.assertFalse(row['ranked'])
            self.assertLess(row['scored_attempts'],1342)
            self.assertNotIn(b.mid(row['model']),s['ranked_model_ids'])


if __name__=='__main__':unittest.main()
