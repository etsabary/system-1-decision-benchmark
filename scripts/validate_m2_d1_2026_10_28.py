"""Verify M2 aggregate publication, preservation, timing and readable categories."""
import csv,hashlib,json,math,statistics
from collections import Counter
from pathlib import Path
from urllib.parse import urlsplit
from validate_direct_release import Page
import build_readable_report as read
ROOT=Path(__file__).resolve().parents[1];DEST=ROOT/'results/releases/local_m2_2026-10-28';OLD=ROOT/'results/releases/native_updates_2026-10-27'
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def validate():
 s=json.loads((DEST/'statistics.json').read_text());old=json.loads((OLD/'statistics.json').read_text());ids=['local_m2_d1_2b','local_m2_d1_omni_2b'];assert s['model_count']==56 and s['local_model_count']==22 and s['primary_cases']==75152 and all(s['models'][k]==v for k,v in old['models'].items());assert set(s['models'])-set(old['models'])==set(ids)
 timing=list(csv.DictReader((DEST/'m2_timing_evidence.csv').open()));assert len(timing)==2684
 for mid,expected in zip(ids,[795,814]):
  m=s['models'][mid];a=[x for x in timing if x['model_id']==mid];assert len(a)==1342 and len({x['item_id'] for x in a})==1342 and all(x['status']=='ok' and x['output_tokens']=='0' for x in a)
  assert m['n']==1342 and m['correct']==expected and sum(x['n'] for x in m['families'].values())==1342 and sum(x['correct'] for x in m['families'].values())==expected
  t=sorted(float(x['latency_ms']) for x in a);pos=(len(t)-1)*.95;lo=math.floor(pos);hi=math.ceil(pos)
  for x,y in [(m['median_ms'],statistics.median(t)),(m['mean_response_ms'],statistics.mean(t)),(m['p95_ms'],t[lo]+(t[hi]-t[lo])*(pos-lo))]:assert math.isclose(x,y,rel_tol=1e-12)
  assert m['execution_location']=='local' and m['hardware']=='Apple M2' and m['cost']['known_usd'] is None
 # The dated release remains authoritative after the live report advances.
 for p in [DEST/'report.html']:
  page=Page();page.feed(p.read_text());assert page.summary==s['ranked_model_ids'] and len(page.cells)==56*31 and len(page.ids)==len(set(page.ids));assert all(Counter(x['data-model'] for x in page.cells)[mid]==31 for mid in ids)
  for cell in page.cells:
   m=s['models'][cell['data-model']]['families'][cell['data-category']];assert int(cell['data-correct'])==m['correct'] and int(cell['data-n'])==m['n'] and read.color(m['accuracy'])[0] in cell['style']
  for mid in ids:assert s['models'][mid]['label'] in p.read_text()
  for link in page.links:
   u=urlsplit(link)
   if not u.scheme and not u.netloc and u.path:assert (p.parent/u.path).exists(),(p,link)
  assert '#a21caf' in p.read_text()
 svg=(DEST/'accuracy_speed_cost.svg').read_text();assert '#a21caf' in svg and '#7c3aed' in svg
 for p in DEST.iterdir():
  if p.is_file():
   assert p.read_bytes()==(ROOT/'docs'/DEST.name/p.name).read_bytes()
   if p.suffix in ('.json','.csv','.html','.svg','.md'):
    text=p.read_text();assert all(x not in text for x in ['/Users/','192.168.','"correct_option_id":','"probabilities":','"choice":'])
 manifest=json.loads((DEST/'manifest.json').read_text());assert manifest['prior_statistics_sha256']==digest(OLD/'statistics.json')
 for name,h in manifest['artifacts'].items():assert digest(DEST/name)==h,name
 print('PASS: 56 routes, 1,736 accuracy cells, 2,684 M2 timings, 54 preserved model records, local colours and links.')
if __name__=='__main__':validate()
