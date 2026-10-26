import unittest
import tempfile
from pathlib import Path
import analyze_direct_decisions_2026_10_20 as a


class AccountingTests(unittest.TestCase):
    def test_unknown_charge_stays_unknown(self):
        value=a.cost([{'reported_cost_usd':None}],'reported_cost_usd')
        self.assertEqual(value['known_attempts'],0)
        self.assertEqual(value['unknown_attempts'],1)

    def test_decimal_charge_sum_is_not_rounded_to_cents(self):
        value=a.cost([{'charge':'.000001920'},{'charge':'.000000060'}],'charge')
        self.assertEqual(value['exact_decimal'],'0.000001980')
        self.assertEqual(value['unknown_attempts'],0)

    def test_recovery_does_not_replace_primary_score(self):
        rows=[{'item_id':'x','request_index':1,'attempt':1,'status':'http_failure','choice':None},
              {'item_id':'x','request_index':1,'attempt':2,'status':'ok','choice':'3'}]
        value=a.outcomes(rows,{'x':'3'})
        self.assertEqual(value['n'],1)
        self.assertEqual(value['correct'],0)

    def test_sealed_report_is_idempotent_and_refuses_partial_overwrites(self):
        with tempfile.TemporaryDirectory() as directory:
            dest=Path(directory)
            original={'a.json':'{"a":1}\n','z.html':'<p>original</p>','table.csv':'model,n\r\nd3,1342\r\n'}
            a.write_artifacts(dest,original,sealed=True)
            a.write_artifacts(dest,original,sealed=True)
            with self.assertRaises(AssertionError):
                a.write_artifacts(dest,{'a.json':'{"a":2}\n','z.html':'changed'},sealed=True)
            self.assertEqual((dest/'a.json').read_text(),original['a.json'])
            self.assertEqual((dest/'z.html').read_text(),original['z.html'])


if __name__=='__main__':unittest.main()
