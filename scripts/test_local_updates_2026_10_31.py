"""Focused reporting regressions: overall membership and evidence preservation."""
from copy import deepcopy
import unittest
import publish_local_updates_2026_10_31 as b

class MainMembership(unittest.TestCase):
 def source(self):
  models={k:dict(n=1342,correct=c,accuracy=c/1342,attempts=1342,recoveries=0,families={'F13':{'accuracy':.1}}) for k,c in [('below',670),('exact',671),('above',672)]}
  return dict(models=models,model_count=3,ranked_model_ids=['above','exact','below'],local_model_ids=['below','exact'],hosted_model_ids=['above'],reference_model_ids=[],adaptive_model_ids=[],model_kinds={k:'Decision' for k in models})
 def test_exact_half_qualifies_without_rounding(self):
  view=b.main_view(self.source());self.assertEqual(view['ranked_model_ids'],['above','exact']);self.assertEqual(view['excluded_overall_model_ids'],['below'])
 def test_same_membership_and_no_source_mutation(self):
  source=self.source();before=deepcopy(source);view=b.main_view(source)
  self.assertEqual(source,before);self.assertEqual(set(view['model_kinds']),set(view['models']))
  self.assertEqual(set(view['local_model_ids'])|set(view['hosted_model_ids']),set(view['models']))
  self.assertEqual(view['model_count'],2);self.assertEqual(view['all_tested_primary_cases'],3*1342)
  self.assertEqual(view['models']['exact'],source['models']['exact'])
 def test_category_score_is_not_overall_filter(self):
  view=b.main_view(self.source());self.assertIn('above',view['models']);self.assertEqual(view['models']['above']['families']['F13']['accuracy'],.1)

if __name__=='__main__':unittest.main()
