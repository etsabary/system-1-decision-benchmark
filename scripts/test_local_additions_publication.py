"""Integrity boundaries for the three explicitly requested local additions."""
from collections import Counter
import csv
import json
import unittest

import publish_local_additions_2026_10_25 as b


class LocalAdditionsPublication(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.current = json.loads((b.DEST / 'statistics.json').read_text())
        cls.previous = json.loads((b.PREVIOUS / 'statistics.json').read_text())

    def test_public_evidence_and_named_category_cells(self):
        from validate_local_additions_2026_10_25 import validate
        result = validate()
        self.assertEqual((result['model_count'], result['local_model_count']), (49, 18))

    def test_previous_measurements_and_timing_rows_are_preserved(self):
        old = self.previous['models']
        self.assertEqual({mid: self.current['models'][mid] for mid in old}, old)
        self.assertTrue((b.DEST / 'local_timing_evidence.csv').read_bytes().startswith(
            (b.PREVIOUS / 'local_timing_evidence.csv').read_bytes()))

    def test_failed_inputs_remain_in_the_full_bank_denominator(self):
        for name, correct, failed in [
            ('pplx-decider:flash-v1.2-mixed4', 971, 3),
            ('d3:flash-artemis-iq3_m', 995, 3),
            ('jeb:9b-v2.1-iq4_xs', 855, 7),
        ]:
            model = self.current['models'][b.mid(name)]
            self.assertEqual((model['n'], model['correct'], model['failed']), (1342, correct, failed))
            self.assertEqual(model['accuracy'], correct / 1342)
            self.assertEqual(model['recoveries'], 0)
        with (b.DEST / 'local_timing_evidence.csv').open() as stream:
            statuses = Counter(row['status'] for row in csv.DictReader(stream))
        self.assertEqual(statuses, {'ok': 24136, 'truncated_or_unverified': 6, 'http_failure': 14})

    def test_local_cost_and_precision_are_explicit(self):
        expected = {
            'd3:flash-artemis-iq3_m': 'IQ3_M / Artemis per-tensor mixed precision',
            'jeb:9b-v2.1-iq4_xs': 'IQ4_XS',
            'pplx-decider:flash-v1.2-mixed4': 'sensitivity-allocated mixed Q2_K–Q6_K, FP32 decision readout',
        }
        for name, precision in expected.items():
            model = self.current['models'][b.mid(name)]
            self.assertEqual(model['precision'], precision)
            self.assertEqual(model['hardware'], 'NVIDIA RTX 2060')
            self.assertEqual(model['vram_gb'], 6)
            self.assertIsNone(model['cost']['known_usd'])
            self.assertIsNone(model['cost']['known_usd_per_1000'])


if __name__ == '__main__':
    unittest.main()
