"""Offline checks for the Joey addition and separately labelled Clairic adapter."""
import csv,math
from collections import Counter
from decimal import Decimal
from urllib.parse import urlsplit
from validate_direct_release import Page
import publish_october30_decisions as b
import build_readable_report as read

def historical(path):
 rel=path.relative_to(b.ROOT).as_posix();manifest=b.load(b.ARCHIVE/'manifest.json')
 if rel not in manifest['files']:return path
 saved=b.ARCHIVE/rel
 assert b.digest(saved)==manifest['files'][rel]['sha256']
 return saved

def validate():
 s=b.load(b.DEST/'statistics.json');old=b.load(b.OLD/'statistics.json');c=b.load(b.DEST/'clairic_compatibility.json')
 assert (s['model_count'],len(s['models']),s['primary_cases'],len(s['decision_model_ids']),len(s['single_pass_decision_ids']))==(61,61,81862,57,56)
 assert len(s['reference_model_ids'])==4 and s['local_model_count']==24 and s['hosted_decision_model_count']==33
 assert all(s['models'][k]==v for k,v in old['models'].items()) and set(s['models'])-set(old['models'])=={b.MID}
 assert s['ranked_model_ids']==sorted(s['models'],key=lambda k:(-s['models'][k]['correct'],k))
 assert s['ranked_model_ids'][0]=='fastino_glide' and s['total_http_attempts']==sum(m.get('attempts',m['n']) for m in s['models'].values())
 q={r['id']:r for r in b.prior.rows(b.ROOT/'results/releases/consolidated_2026-10-19/questions_1342.jsonl')}
 rows=list(csv.DictReader((b.DEST/'october30_timing_evidence.csv').open()));assert len(rows)==2684
 for mid,correct,expected_cost,stats in [(b.MID,773,Decimal('.00484453'),s['models'][b.MID]),('clairic_extraction',729,Decimal('.05851030'),c)]:
  a=[r for r in rows if r['model_id']==mid];assert len(a)==len({r['item_id'] for r in a})==1342 and {r['item_id'] for r in a}==set(q)
  assert stats['correct']==correct and sum(v['n'] for v in stats['families'].values())==1342 and sum(v['correct'] for v in stats['families'].values())==correct
  assert Counter(r['status'] for r in a)==stats.get('first_statuses',stats.get('statuses'))
  for r in a:
   assert r['attempt']=='1' and r['family_id']==q[r['item_id']]['family_id'] and r['native_input_sha256']==q[r['item_id']]['native_input_sha256']
   assert len(r['request_sha256'])==len(r['response_sha256'])==64
  t=b.prior.quant([float(r['latency_ms']) for r in a]);assert all(math.isclose(t[k],stats['mean_response_ms' if k=='mean_ms' and mid==b.MID else k],rel_tol=1e-12) for k in t)
  assert sum(Decimal(r['reported_cost_usd']) for r in a)==expected_cost
 assert c['included_in_native_ranking'] is False and c['statuses']=={'ok':1336,'invalid_answer':6}
 assert s['models'][b.MID]['observed_output_tokens']==1342 and s['models'][b.MID]['recoveries']==0
 for path in [b.DEST/'report.html',b.ROOT/'docs/report.html']:
  text=path.read_text();p=Page();p.feed(text);assert p.summary==s['ranked_model_ids'] and len(p.cells)==1891 and len(p.ids)==len(set(p.ids))
  assert all(x in text for x in ['61 configurations','33 hosted','Joey-1','Clairic','extraction','✦','#d97706','#7c3aed','44.1%'])
  for cell in p.cells:
   f=s['models'][cell['data-model']]['families'][cell['data-category']];assert (int(cell['data-correct']),int(cell['data-n']))==(f['correct'],f['n']) and read.color(f['accuracy'])[0] in cell['style']
  for link in p.links:
   u=urlsplit(link)
   if not u.scheme and not u.netloc and u.path:assert (path.parent/u.path).exists(),(path,link)
   elif not u.path and u.fragment:assert u.fragment in p.ids,(path,link)
 for path in b.DEST.iterdir():
  if path.is_file():assert path.read_bytes()==(b.ROOT/'docs'/b.NAME/path.name).read_bytes()
  if path.suffix in ['.json','.csv','.md','.svg','.html']:
   text=path.read_text();assert all(x not in text for x in ['/Users/','192.168.','"choice":','"probabilities":','"correct_option_id":','API_KEY='])
 manifest=b.load(b.DEST/'manifest.json');assert manifest['models']==61 and manifest['prior_statistics_sha256']==b.digest(b.OLD/'statistics.json')
 for name,h in manifest['artifacts'].items():assert b.digest(b.DEST/name)==h,name
 print('PASS: 61 configurations; 60 records unchanged; 2,684 new timings; 1,891 category cells; adapter separation, billing, privacy and links.')
 return s
if __name__=='__main__':validate()
