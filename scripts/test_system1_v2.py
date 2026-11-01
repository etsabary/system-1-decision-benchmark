"""Selection boundaries and input identity remain independent of presentation."""
from copy import deepcopy
import unittest
import publish_system1_v2 as b
class Selection(unittest.TestCase):
 def model(self,correct,n=1934,archival=False):return dict(n=n,correct=correct,accuracy=correct/n,archival=archival)
 def test_unrounded_62_percent_boundary(self):
  self.assertFalse(b.qualifies('a',self.model(1199)));self.assertTrue(b.qualifies('a',self.model(1200)))
  self.assertFalse(b.qualifies('a',self.model(6199,10000)));self.assertTrue(b.qualifies('a',self.model(6200,10000)))
 def test_explicit_retirement_and_adaptive_archive(self):
  for mid in b.EXCLUDED:self.assertFalse(b.qualifies(mid,self.model(1934)))
  self.assertFalse(b.qualifies('adaptive',self.model(1934,archival=True)))
 def test_selection_preserves_measurements_and_category_independence(self):
  source=dict(ranked_model_ids=['high','edge','low'],models={'high':self.model(1600),'edge':self.model(1200),'low':self.model(1199)})
  before=deepcopy(source);view=b.main_view(source);self.assertEqual(source,before);self.assertEqual(view['ranked_model_ids'],['high','edge']);self.assertEqual(view['models']['edge'],source['models']['edge'])
 def test_prose_spacing_preserves_ids_and_links(self):
  self.assertEqual(b.spaced('F26–F31 and P01–P10'), 'F26–F31 and P01–P10')
  text='scripts/publish_system1_v2.py and4B models';self.assertEqual(b.spaced(text),'scripts/publish_system1_v2.py and 4B models')
 def test_documented_commands_remain_executable(self):
  command='python3 scripts/validate_october21_release.py';self.assertEqual(b.spaced(command),command)
  command='python3 scripts/publish_system1_v2.py --output /tmp/system1-v2-rebuild';self.assertEqual(b.spaced(command),command)
  self.assertEqual(b.spaced('```sh\n'+command+'\n```'),'```sh\n'+command+'\n```')
if __name__=='__main__':unittest.main()
