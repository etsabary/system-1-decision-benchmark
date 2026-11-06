"""Check Super Decider's full-bank addition and preserve every earlier measurement."""
import csv, gzip, hashlib, json, sys
from pathlib import Path

dest, prior=map(Path,sys.argv[1:])
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
m=json.loads((dest/'manifest.json').read_text())
assert m['prior_prism_manifest_sha256']==sha(prior/'manifest.json')
actual={str(p.relative_to(dest)) for p in dest.rglob('*') if p.is_file() and p.name!='manifest.json'}
assert actual==set(m['files_sha256'])
for name,digest in m['files_sha256'].items():assert sha(dest/name)==digest,name
for name in ('questions_2157.jsonl','source_metadata_2157.jsonl','category_guide.json','SOURCE_AND_LICENSES.md','partial_models.json','KAI_CASE_NOTE.md','STRIKE_SCREEN_NOTES.md','LOCAL_SCREEN_NOTES.md','NEW_LOCAL_SCREEN_NOTES.md'):
 assert sha(dest/name)==sha(prior/name),name
old=json.loads((prior/'statistics.json').read_text());new=json.loads((dest/'statistics.json').read_text());mid='super_decider'
assert len(old['models'])==30 and len(new['models'])==31 and set(new['models'])==set(old['models'])|{mid}
assert all(new['models'][x]==v for x,v in old['models'].items())
p=new['models'][mid];assert p['n']==p['valid']==2157 and p['accuracy']==p['correct']/2157
assert (mid in new['ranked_model_ids'])==(p['correct']*100>=62*2157)
oldcost=json.loads((prior/'cost_statistics.json').read_text())['models'];newcost=json.loads((dest/'cost_statistics.json').read_text())['models']
assert all(newcost[x]==v for x,v in oldcost.items())
assert newcost[mid]['tariff_estimate_count']==2157 and newcost[mid]['reported_count']==0
def rows(p):
 with (gzip.open(p,'rt',newline='') if p.suffix=='.gz' else p.open(newline='')) as f:return list(csv.DictReader(f))
for name,n in [('all_category_scores.csv',43),('timing_evidence.csv.gz',2157),('cost_evidence.csv.gz',2157)]:
 oldrows=rows(prior/name);newrows=rows(dest/name)
 assert [x for x in newrows if x['model_id']!=mid]==oldrows,name
 assert sum(x['model_id']==mid for x in newrows)==n,name
page=(dest/'report.html').read_text();readme=(dest/'README_V4.md').read_text()
assert page.index('src="comparison_accuracy.png"')<page.index('<div class="comparison-table">')
assert readme.index('comparison_accuracy.png')<readme.index('| Configuration |')
assert page.index('<strong>Selection bias:')>page.index('src="comparison_cost.png"')
assert 'data-incomplete-model="strike-1"' in page and 'data-incomplete-model="hanzo-kai"' in page and 'Incomplete local screens' in page
assert 'h2o e4b' not in page.lower() and 'h2o e4b' not in readme.lower()
print('PASS: Super Decider complete-bank result added; previous measurements, partial screens, cost and chart presentation preserved.')
