"""Validate the full comparison, adaptive split, preservation and private-data boundary."""
import csv,json,math,statistics
from collections import Counter
from decimal import Decimal
from urllib.parse import urlsplit
from validate_direct_release import Page
import publish_october29_decisions as b
import build_readable_report as read

def validate():
 s=b.load(b.DEST/'statistics.json');old=b.load(b.OLD/'statistics.json')
 assert (s['model_count'],s['primary_cases'],s['local_model_count'],s['hosted_decision_model_count'])==(60,80520,24,32)
 assert len(s['models'])==60 and len(s['decision_model_ids'])==56 and len(s['single_pass_decision_ids'])==55 and s['adaptive_model_ids']==[b.AUTO]
 assert all(s['models'][k]==v for k,v in old['models'].items()) and set(s['models'])-set(old['models'])==set(b.IDS)
 assert s['ranked_model_ids']==sorted(s['models'],key=lambda m:(-s['models'][m]['correct'],m))
 assert s['ranked_model_ids'][0]=='fastino_glide' and s['total_http_attempts']==sum(m.get('attempts',m['n']) for m in s['models'].values())
 qq={q['id']:q for q in b.rows(b.ROOT/'results/releases/consolidated_2026-10-19/questions_1342.jsonl')}
 rr=list(csv.DictReader((b.DEST/'october29_timing_evidence.csv').open()));assert len(rr)==5368
 for mid,expected in zip(b.IDS,[1121,915,988,1005]):
  m=s['models'][mid];a=[r for r in rr if r['model_id']==mid];assert len(a)==len({r['item_id'] for r in a})==1342 and set(r['item_id'] for r in a)==set(qq)
  assert m['correct']==expected and m['correct']+m['wrong_valid']+m['failed']==1342 and sum(v['correct'] for v in m['families'].values())==expected and sum(v['n'] for v in m['families'].values())==1342
  assert Counter(r['status'] for r in a)==m['first_statuses']
  for r in a:
   q=qq[r['item_id']];assert r['attempt']=='1' and r['family_id']==q['family_id'] and r['native_input_sha256']==q['native_input_sha256'] and len(r['request_sha256'])==len(r['response_sha256'])==64
  t=b.quant([float(r['latency_ms']) for r in a]);assert all(math.isclose(t[k],m['mean_response_ms' if k=='mean_ms' else k],rel_tol=1e-12) for k in t)
  assert (all(r['output_tokens']=='' for r in a) and m['observed_output_tokens'] is None if mid==b.IDS[1] else sum(int(r['output_tokens'] or 0) for r in a)==m['observed_output_tokens']) and m['recoveries']==0 and m['dates_toronto']=={'2026-10-29':1342}
  if mid!=b.AUTO:assert all(int(r['output_tokens'] or 0)==0 for r in a)
 auto=s['models'][b.AUTO];a=[r for r in rr if r['model_id']==b.AUTO];gen=[r for r in a if int(r['output_tokens'])>0];zero=[r for r in a if int(r['output_tokens'])==0];p=auto['adaptive_generation']
 assert len(gen)==592 and len(zero)==750 and sum(int(r['output_tokens']) for r in gen)==288706 and sum(r['output_tokens']=='512' for r in a)==491
 for name,subset in [('reported_generation',gen),('reported_zero_generation',zero)]:
  t=b.quant([float(r['latency_ms']) for r in subset]);assert p['latency_by_reported_generation'][name]['n']==len(subset) and all(math.isclose(t[k],p['latency_by_reported_generation'][name][k],rel_tol=1e-12) for k in t)
 assert p['only_auto']+p['both_correct']==1005 and p['only_instant']+p['both_correct']==988 and sum(p[k] for k in ['only_auto','only_instant','both_correct','neither_correct'])==1342
 assert auto['families']['F13']['correct']==33 and auto['families']['F24']['correct']==21 and auto['p95_ms']>13000 and auto['mean_response_ms']>5700
 assert s['models'][b.IDS[2]]['families']['F13']['correct']==10 and s['models'][b.IDS[2]]['families']['F24']['correct']==42
 total=sum(Decimal(r['reported_cost_usd']) for r in rr if r['model_id']==b.IDS[1] and r['reported_cost_usd']);assert total==Decimal('.013644162')
 assert s['models'][b.IDS[0]]['cost']['known_usd'] is None and not s['models'][b.IDS[0]]['cost'].get('public_free_access')
 protocol=b.load(b.DEST/'execution_protocol.json');assert protocol[b.AUTO]['native_think_budget']==512 and not protocol[b.AUTO]['thought_text_exposed'] and 'exception' in protocol[b.AUTO]['speed_policy']
 for path in [b.DEST/'report.html',b.ROOT/'docs/report.html']:
  from validate_october30_decisions import historical
  text=historical(path).read_text();page=Page();page.feed(text);assert page.summary==s['ranked_model_ids'] and len(page.cells)==1860 and len(page.ids)==len(set(page.ids))
  assert all(phrase in text for phrase in ['✦','adaptive-model','#7c3aed','#d97706','55.9%','44.1%','13.12 s','sometimes thinks','512-token','1,342'])
  for c in page.cells:
   f=s['models'][c['data-model']]['families'][c['data-category']];assert (int(c['data-correct']),int(c['data-n']))==(f['correct'],f['n']) and read.color(f['accuracy'])[0] in c['style']
  for link in page.links:
   u=urlsplit(link)
   if not u.scheme and not u.netloc and u.path:assert (path.parent/u.path).exists(),(path,link)
   elif not u.path and u.fragment:assert u.fragment in page.ids,(path,link)
 for name in ['accuracy_speed_cost.svg',*[g[0]+'.svg' for g in read.GROUPS]]:
  t=(b.DEST/name).read_text();assert '#7c3aed' in t and '#d97706' in t and 'AutoThink' in t
 for path in b.DEST.iterdir():
  if path.is_file():assert path.read_bytes()==(b.ROOT/'docs'/b.NAME/path.name).read_bytes()
  if path.suffix in ['.json','.csv','.md','.svg','.html']:
   t=path.read_text();assert all(x not in t for x in ['/Users/','192.168.','"choice":','"probabilities":','"correct_option_id":','API_KEY='])
 manifest=b.load(b.DEST/'manifest.json');assert manifest['prior_statistics_sha256']==b.digest(b.OLD/'statistics.json')
 for name,h in manifest['artifacts'].items():assert b.digest(b.DEST/name)==h,name
 print('PASS: 60 configurations; 56 unchanged records; 5,368 timings; 1,860 category cells; adaptive split, billing, privacy and links.')
 return s
if __name__=='__main__':validate()
