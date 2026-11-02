"""Boundary checks for the published speed and cost presentation bands."""
import unittest
from validate_system1_v3_presentation import band,money_cost,normalized,total

class PresentationBands(unittest.TestCase):
 def test_speed_boundaries(self):
  for value,expected in [(250,0),(250.01,1),(500,1),(500.01,2),(1000,2),(1000.01,3)]:
   with self.subTest(value=value):self.assertEqual(band(value,[250,500,1000]),expected)
 def test_cost_boundaries(self):
  for value,expected in [('0.01',0),('0.010001',1),('0.025',1),('0.025001',2),('0.05',2),('0.050001',3)]:
   with self.subTest(value=value):self.assertEqual(band(value,['.01','.025','.05']),expected)
 def test_unmetered_and_missing_costs_are_not_zero(self):
  c={'local_unmeasured_count':2017,'known_usd_per_1000':None,'known_subtotal_usd':None,'unknown_count':0,'free_access_tariff_count':0,'reported_count':0,'tariff_estimate_count':0}
  self.assertIsNone(money_cost(c));self.assertEqual(total(c),'Unmetered local');self.assertEqual(normalized(c),'Unmetered local')
  c.update(local_unmeasured_count=0,unknown_count=2017)
  self.assertIsNone(money_cost(c));self.assertEqual(total(c),'Unknown');self.assertEqual(normalized(c),'Unknown')
 def test_free_baseline_with_unknown_additions_stays_qualified(self):
  c={'local_unmeasured_count':0,'known_usd_per_1000':'0','known_subtotal_usd':'0','unknown_count':83,'free_access_tariff_count':1934,'reported_count':0,'tariff_estimate_count':0}
  self.assertIsNone(money_cost(c));self.assertEqual(total(c),'Free access + ?');self.assertEqual(normalized(c),'Free access + ?')

if __name__=='__main__':unittest.main()
