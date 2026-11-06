"""Validate Terra's full-bank addition and the separate native Luna screen."""
import csv,gzip,hashlib,json,math,statistics,sys
from decimal import Decimal
from pathlib import Path
dest,prior=map(Path,sys.argv[1:]);sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def rows(p):
 with (gzip.open(p,'rt',newline='') if p.suffix=='.gz' else p.open(newline='')) as f:return list(csv.DictReader(f))
def q95(v):
 a=sorted(v);i=(len(a)-1)*.95;lo=math.floor(i);hi=math.ceil(i);return a[lo]+(i-lo)*(a[hi]-a[lo])
m=json.loads((dest/'manifest.json').read_text());assert m['prior_super_decider_manifest_sha256']==sha(prior/'manifest.json')
actual={str(p.relative_to(dest)) for p in dest.rglob('*') if p.is_file() and p.name!='manifest.json'};assert actual==set(m['files_sha256'])
for name,h in m['files_sha256'].items():assert sha(dest/name)==h,name
for name in ['questions_2157.jsonl','source_metadata_2157.jsonl','category_guide.json','SOURCE_AND_LICENSES.md','PROJECT_LICENSE_MIT.txt','transport_recoveries.json','model_collection_recoveries.json','model_context_diagnostics.json','KAI_CASE_NOTE.md','STRIKE_SCREEN_NOTES.md','LOCAL_SCREEN_NOTES.md','NEW_LOCAL_SCREEN_NOTES.md']:
 assert sha(dest/name)==sha(prior/name),name
for p in (prior/'third_party_licenses').iterdir():assert sha(dest/'third_party_licenses'/p.name)==sha(p)
old=json.loads((prior/'statistics.json').read_text());new=json.loads((dest/'statistics.json').read_text());mid='reference_terra61'
assert len(old['models'])==31 and len(new['models'])==32 and set(new['models'])==set(old['models'])|{mid}
assert all(new['models'][k]==v for k,v in old['models'].items())
t=new['models'][mid];assert t['n']==2157 and 2100<t['valid']<=2157 and t['accuracy']==t['correct']/2157 and t['role']=='LLM reference'
ranked=sorted((k for k,v in new['models'].items() if v['correct']*100>=62*2157),key=lambda k:(-new['models'][k]['correct'],k));assert ranked==new['ranked_model_ids']
for name,n in [('all_category_scores.csv',43),('timing_evidence.csv.gz',2157),('cost_evidence.csv.gz',2157)]:
 a=rows(prior/name);b=rows(dest/name);assert [x for x in b if x['model_id']!=mid]==a,name
 added=[x for x in b if x['model_id']==mid];assert len(added)==n and len({x['family_id'] if n==43 else x['item_id'] for x in added})==n
 if name=='all_category_scores.csv':assert sum(int(x['correct']) for x in added)==t['correct'] and sum(int(x['n']) for x in added)==2157
 if name=='timing_evidence.csv.gz':
  vals=[float(x['latency_ms']) for x in added];assert all(math.isfinite(x) and x>=0 for x in vals)
  assert abs(statistics.median(vals)-t['median_ms'])<1e-8 and abs(q95(vals)-t['p95_ms'])<1e-8
  assert sum(x['status']=='ok' for x in added)==t['valid']
 if name=='cost_evidence.csv.gz':
  costs=added;assert all(x['evidence_kind'] in ['reported','unknown'] for x in added)
oldcost=json.loads((prior/'cost_statistics.json').read_text())['models'];newcost=json.loads((dest/'cost_statistics.json').read_text())['models'];assert all(newcost[k]==v for k,v in oldcost.items());c=newcost[mid]
assert c['n']==2157 and c['reported_count']==t['valid'] and c['unknown_count']==2157-t['valid'] and c['tariff_estimate_count']==0
assert sum(Decimal(x['reported_usd']) for x in costs if x['reported_usd'])==Decimal(c['reported_subtotal_usd'])
a=json.loads((prior/'partial_models.json').read_text());b=json.loads((dest/'partial_models.json').read_text());assert b[:-1]==a
l=b[-1];assert l['provider_model_id']=='openai/gpt-6-luna-decisions' and l['sample_n']==181 and l['sample_correct']==82 and l['sample_usable']==180 and l['reused_baseline']['n']==1342 and l['reused_baseline']['correct']==758 and l['new_inputs_planned']==815 and l['unattempted_expansion_inputs']==634
pc=rows(dest/'luna_partial_cost.csv.gz');pt=rows(dest/'luna_partial_timing.csv.gz');assert len(pc)==len(pt)==181
assert sum(Decimal(x['reported_usd']) for x in pc if x['reported_usd'])==Decimal(l['reported_charge_usd']) and sum(x['evidence_kind']=='unknown' for x in pc)==1
page=(dest/'report.html').read_text();readme=(dest/'README_V4.md').read_text()
assert page.index('src="comparison_accuracy.png"')<page.index('<div class="comparison-table">') and readme.index('comparison_accuracy.png')<readme.index('| Configuration |')
assert page.index('<strong>Selection bias:')>page.index('src="comparison_cost.png"') and readme.index('**Selection bias:**')>readme.index('comparison_cost.png')
for s in ['data-incomplete-model="strike-1"','data-incomplete-model="hanzo-kai"','data-incomplete-model="luna-decisions-20261106"','Incomplete local screens','data-cost-band','data-mobile-speed-band','OPENAI_DECISIONS_NOTES.md']:
 assert s in page,s
assert 'h2o e4b' not in page.lower() and 'h2o e4b' not in readme.lower()
print(f'PASS: Terra full-bank result, {len(ranked)} qualifying configurations, {len(new["models"])} total. Prior evidence, costs, chart order and partial screens preserved.')
