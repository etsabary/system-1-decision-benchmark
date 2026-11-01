"""Public offline checks for the50% reporting boundary and new local evidence."""
from collections import Counter
from urllib.parse import urlsplit
import csv,json,math,re
import publish_local_updates_2026_10_31 as b
from validate_direct_release import Page
import build_readable_report as read

def validate():
 all_s=b.load(b.DEST/'all_statistics.json');s=b.load(b.DEST/'statistics.json');old=b.load(b.OLD/'statistics.json')
 assert len(all_s['models'])==all_s['model_count']==66 and all(all_s['models'][k]==v for k,v in old['models'].items())
 assert s==b.main_view(all_s) and len(s['models'])==s['model_count']==56
 assert len(s['excluded_overall_model_ids'])==10 and all(m['accuracy']>=.5 for m in s['models'].values())
 assert s['local_model_count']==21 and s['hosted_decision_model_count']==31 and len(s['reference_model_ids'])==4
 assert set(s['models'])=={k for k,m in all_s['models'].items() if m['accuracy']>=.5}
 assert s['ranked_model_ids'][0]=='fastino_glide' and all_s['prior_statistics_sha256']==b.digest(b.OLD/'statistics.json')
 full_ids={mid for mid,label in b.CONFIGS.values()}&set(all_s['models']);assert len(full_ids)==5
 expected={'local_cox3b_int8':754,'local_jue25b':801,'local_iota4b_q8':738,'local_cerno4b_nf4':983,'local_dexy9b_nf4':833}
 qq={q['id']:q for q in b.visual.rows(b.ROOT/'results/releases/consolidated_2026-10-19/questions_1342.jsonl')}
 timing=list(csv.DictReader((b.DEST/'local_timing_evidence.csv').open()));assert len(timing)==6850
 screens=b.load(b.DEST/'screened_routes.json');assert len(screens)==3 and sorted(m['n'] for m in screens)==[20,20,100]
 md=b.load(b.DEST/'local_model_metadata.json');assert len(md)==8
 records={**{mid:all_s['models'][mid] for mid in full_ids},**{m['model_id']:m for m in screens}}
 for mid,m in records.items():
  rr=[r for r in timing if r['model_id']==mid];assert len(rr)==m['n']==len({r['item_id'] for r in rr})
  assert [int(r['request_index']) for r in rr]==list(range(1,len(rr)+1))
  for r in rr:
   assert r['attempt']=='1' and r['family_id']==qq[r['item_id']]['family_id'] and r['native_input_sha256']==qq[r['item_id']]['native_input_sha256']
   assert re.fullmatch('[0-9a-f]{64}',r['request_sha256']) and re.fullmatch('[0-9a-f]{64}',r['response_sha256'])
  assert Counter(r['status'] for r in rr)==m.get('first_statuses',m.get('statuses'))
  t=b.visual.quant([float(r['latency_ms']) for r in rr]);assert all(math.isclose(v,m['mean_response_ms' if k=='mean_ms' and mid in full_ids else k],rel_tol=1e-12) for k,v in t.items())
  assert md[mid]['device_observed']=='cuda:0' and md[mid]['vram_gb']==6 and md[mid]['cpu_fallback'] is False
  if mid in full_ids:
   assert len(rr)==1342 and {r['item_id'] for r in rr}==set(qq) and m['correct']==expected[mid]
   assert sum(x['n'] for x in m['families'].values())==1342 and sum(x['correct'] for x in m['families'].values())==m['correct']
   assert m['answered']+m['failed']==m['correct']+m['wrong_valid']+m['failed']==1342 and m['cost']['known_usd'] is None
   assert m['recoveries']==0 and m['dates_toronto']=={'2026-10-31':1342}
   assert m['execution_location']=='local' and m['hardware']=='NVIDIA RTX 2060'
 assert sum(x['context_limit_failures'] for x in screens)==4 and next(x for x in screens if x['n']==100)['correct']==17
 catalogue=b.load(b.DEST/'below_50.json');assert len(catalogue)>=25 and all(m['correct']/m['n']<.5 and math.isclose(m['accuracy'],m['correct']/m['n']) for m in catalogue)
 assert {r['model_id'] for r in catalogue if r['record_group']=='current_full'}==set(s['excluded_overall_model_ids'])
 assert any('Sonnet' in r['label'] and r['n']==110 and r['correct']==26 for r in catalogue)
 assert any('Qwen3-30B' in r['label'] and r['n']==1136 and r['correct']==564 for r in catalogue)
 assert all('Bivia' not in r['label'] for r in catalogue), 'Superseded low prefixes must not replace latest above50% sample'
 assert next(r for r in catalogue if 'Cribl' in r['label'])['format']=='Native choice (PyTorch)'
 for row in catalogue:
  if row.get('source_public_path'):assert b.digest(b.ROOT/row['source_public_path'])==row['source_sha256']
 for path in [b.DEST/'report.html',b.ROOT/'docs/report.html']:
  text=path.read_text();page=Page();page.feed(text)
  assert page.summary==s['ranked_model_ids'] and len(page.cells)==56*31 and len(page.ids)==len(set(page.ids))
  assert Counter(c['data-model'] for c in page.cells)=={mid:31 for mid in s['models']}
  assert all(x not in text for x in s['excluded_overall_model_ids'])
  assert all(x in text for x in ['56 configurations','50%','66 complete','Cerno','Jue','#7c3aed','#d97706','adaptive-model'])
  for cell in page.cells:
   f=s['models'][cell['data-model']]['families'][cell['data-category']];assert (int(cell['data-correct']),int(cell['data-n']))==(f['correct'],f['n']) and read.color(f['accuracy'])[0] in cell['style']
  for link in page.links:
   u=urlsplit(link)
   if not u.scheme and not u.netloc and u.path:assert (path.parent/u.path).exists(),(path,link)
   elif not u.path and u.fragment:assert u.fragment in page.ids,(path,link)
 for name in ['accuracy_speed_cost.svg',*[g[0]+'.svg' for g in read.GROUPS]]:
  text=(b.DEST/name).read_text();assert '#7c3aed' in text and '#d97706' in text
  assert 'Cerno 4B' in text and 'Jue 2.5B' in text
  assert all(all_s['models'][k]['label'] not in text for k in s['excluded_overall_model_ids'])
 csv_models=list(csv.DictReader((b.DEST/'model_statistics.csv').open()));assert [r['model_id'] for r in csv_models]==s['ranked_model_ids']
 assert len(list(csv.DictReader((b.DEST/'category_scores.csv').open())))==31
 functions=(b.ROOT/'documents/FUNCTIONS.md').read_text();assert 'Cerno 4B' in functions and all(all_s['models'][k]['label'] not in functions for k in s['excluded_overall_model_ids'])
 manifest=b.load(b.DEST/'manifest.json');assert manifest['main_models']==56 and manifest['all_full_models']==66
 assert manifest['prior_statistics_sha256']==b.digest(b.OLD/'statistics.json')
 for path in b.DEST.iterdir():
  if path.is_file():
   assert path.read_bytes()==(b.ROOT/'docs'/b.NAME/path.name).read_bytes()
   if path.name!='manifest.json':assert b.digest(path)==manifest['artifacts'][path.name],path
   if path.suffix in ['.json','.csv','.md','.svg','.html']:
    text=path.read_text();assert all(x not in text for x in ['/Users/','192.168.','"choice":','"probabilities":','"correct_option_id":','API_KEY=']),path
 print('PASS:56 qualifying configurations,66 preserved full records,6850 new first attempts,1736 category cells, all scopes/privacy/links/hashes.')
 return s
if __name__=='__main__':validate()
