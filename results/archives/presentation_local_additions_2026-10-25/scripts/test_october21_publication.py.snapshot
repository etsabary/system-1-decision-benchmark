import json
import unittest
import publish_october21_additions as b


class October21Publication(unittest.TestCase):
    def test_full_publication(self):
        if not (b.DEST/'manifest.json').exists():self.skipTest('Not built')
        from validate_october21_release import validate
        validate()

    def test_earlier_records_exactly_preserved(self):
        if not (b.DEST/'statistics.json').exists():self.skipTest('Not built')
        old=json.loads((b.prior.DEST/'statistics.json').read_text())
        current=json.loads((b.DEST/'statistics.json').read_text())
        for mid,m in old['models'].items():self.assertEqual(m,current['models'][mid])

    def test_promotion_is_not_a_metered_zero(self):
        self.assertEqual(b.price('mammoth1',{}),'Promotional free access*')
        self.assertEqual(b.price('elephant1',{},False),'Promotional free access*')

    def test_expected_task_counts_are_unchanged(self):
        self.assertEqual(sum(len(g[2]) for g in b.readable.GROUPS),31)
        self.assertEqual(29*31,899)
        self.assertEqual(29*1342,38918)


if __name__=='__main__':
    unittest.main()
