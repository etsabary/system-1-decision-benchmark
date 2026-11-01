import unittest
from decimal import Decimal
import publish_system1_v2_presentation as b


class PresentationTests(unittest.TestCase):
    def test_fixed_band_boundaries_use_unrounded_values(self):
        self.assertEqual(b.speed_band(250), 0)
        self.assertEqual(b.speed_band(250.001), 1)
        self.assertEqual(b.speed_band(1000), 2)
        self.assertEqual(b.speed_band(1000.001), 3)
        self.assertEqual(b.cost_band(Decimal('.010000')), 0)
        self.assertEqual(b.cost_band(Decimal('.01000001')), 1)
        self.assertEqual(b.cost_band(Decimal('.05')), 2)
        self.assertEqual(b.cost_band(Decimal('.05000001')), 3)
        self.assertIsNone(b.cost_band(None))

    def test_category_ties_do_not_use_latency(self):
        rows = [('a', {'correct': '39'}), ('b', {'correct': '39'}), ('c', {'correct': '37'})]
        self.assertEqual(b.competition_ranks(rows), {'a': 1, 'b': 1, 'c': 3})

    def test_missing_charge_is_not_free_or_normalized_to_receipts(self):
        c = dict(evidence_kind='reported_partial', known_usd_per_1000='4.1354808686', unknown_count=183, tariff_estimate_count=0, free_access_tariff_count=0)
        value, basis = b.cost_text(c)
        self.assertEqual(value, '$4.13548 + ?')
        self.assertIn('183 charges unknown', basis)
        self.assertIn('known subtotal only', basis)
        self.assertIn('incomplete', b.cost_cell(c))

    def test_free_access_and_unmetered_local_are_distinct(self):
        free = b.cost_text({'evidence_kind': 'free_access_tariff'})
        local = b.cost_text({'evidence_kind': 'local_unmeasured'})
        self.assertEqual(free[0], '$0 access*')
        self.assertIn('not a monetary receipt', free[1])
        self.assertEqual(local[0], 'Unmetered local')
        self.assertNotIn('$0', local[0])

    def test_all_categories_covered_once(self):
        fids = [fid for _, _, fs in b.GROUPS for fid in fs]
        self.assertEqual(len(fids), len(set(fids)))
        self.assertEqual(set(fids), {f'F{i:02}' for i in range(1,32)} | {f'P{i:02}' for i in range(1,11)})

    def test_isolated_rebuild_cannot_overwrite_source_release(self):
        with self.assertRaisesRegex(AssertionError, 'separate output directory'):
            b.build(b.SOURCE, publish=False)


if __name__ == '__main__': unittest.main()
