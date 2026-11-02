"""Public-data integrity checks for a System 1 v4 release; no API calls or keys."""
import argparse,csv,gzip,hashlib,json,math,re,statistics
from collections import Counter,defaultdict
from decimal import Decimal
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit,unquote

def sha(data):return hashlib.sha256(data).hexdigest()
def canon(x):return json.dumps(x,sort_keys=True,ensure_ascii=False,separators=(',',':'),allow_nan=False).encode()
def rows(p):return [json.loads(s) for s in p.read_text().splitlines() if s]
def csvrows(p):
 with (gzip.open(p,'rt',newline='') if p.suffix=='.gz' else p.open(newline='')) as f:return list(csv.DictReader(f))
def near(x,y):assert math.isclose(float(x),float(y),rel_tol=1e-10,abs_tol=1e-8),(x,y)
def q95(values):
 x=sorted(values);pos=(len(x)-1)*.95;lo=math.floor(pos);hi=math.ceil(pos);return x[lo]+(pos-lo)*(x[hi]-x[lo])
class Page(HTMLParser):
 def __init__(self):super().__init__();self.cells=[];self.links=[];self.images=[]
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  if tag=='td' and 'data-model' in a:self.cells.append(a)
  if tag=='a' and 'href' in a:self.links.append(a['href'])
  if tag=='img':self.images.append(a)

def validate(root,v2):
 manifest=json.loads((root/'manifest.json').read_text());assert manifest['questions']==2157 and manifest['categories']==43 and manifest['measured_models']==26
 actual={str(p.relative_to(root)) for p in root.rglob('*') if p.is_file() and p.name!='manifest.json'}
 assert actual==set(manifest['files_sha256'])
 for name,h in manifest['files_sha256'].items():assert sha((root/name).read_bytes())==h,name
 q=rows(root/'questions_2157.jsonl');old=rows(v2/'questions_2017.jsonl');meta=rows(root/'source_metadata_2157.jsonl')
 assert len(q)==len(meta)==2157 and q[:2017]==old and len({x['id'] for x in q})==2157
 qs={x['id']:x for x in q};assert set(qs)=={x['id'] for x in meta}
 for item in q:
  assert sha(canon(item['native_input']))==item['native_input_sha256']
  assert not any(k in item for k in ['expected_answer','correct_option_id','answer_key'])
 counts=Counter(x['family_id'] for x in q);assert len(counts)==43 and counts['F32']==23 and counts['F33']==200
 for item in q[1934:]:assert len(item['native_input']['questions']['decision']['criteria'])==(4 if item['family_id']=='F32' else 5)
 for x in meta[1934:]:
  assert x['origin_scope']=='borrowed' and x['source_url'] and x['source_item_id'] and x['source_content_sha256'] and x['license_url']
  assert ('MIT' in x['upstream_license'] and 'not established' in x['rights_limit']) if x['family_id']=='F32' else ('Apache' in x['upstream_license'])
 stats=json.loads((root/'statistics.json').read_text());models=stats['models'];ids=set(models);ranked=stats['ranked_model_ids'];assert len(ids)==26 and len(ranked)>0
 expected=sorted([m for m in ids if models[m]['correct']*100>=62*2157],key=lambda m:(-models[m]['correct'],m));assert ranked==expected and set(stats['below_cutoff'])==ids-set(ranked)
 cats=csvrows(root/'all_category_scores.csv');lookup={(x['model_id'],x['family_id']):x for x in cats};assert len(lookup)==26*43
 oldcats={(x['model_id'],x['family_id']):x for x in csvrows(v2/'all_category_scores.csv') if x['model_id'] in ids and x['family_id']!='F33'};assert len(oldcats)==26*42
 for key,c in oldcats.items():assert lookup[key]==c,key
 for mid,m in models.items():
  assert m['n']==2157 and 0<=m['correct']<=m['valid']<=2157
  near(m['accuracy'],m['correct']/2157);near(m['coverage'],m['valid']/2157);near(m['answer_accuracy_among_usable'],m['correct']/m['valid']);near(m['accuracy_upper_if_all_unusable_correct'],(m['correct']+2157-m['valid'])/2157)
  c=[lookup[mid,fid] for fid in counts];assert sum(int(x['correct']) for x in c)==m['correct'] and sum(int(x['n']) for x in c)==2157
  for x in c:assert int(x['n'])==counts[x['family_id']];near(x['accuracy'],int(x['correct'])/int(x['n']))
  near(m['macro_category_accuracy'],statistics.mean(float(x['accuracy']) for x in c))
 times=csvrows(root/'timing_evidence.csv.gz');costs=csvrows(root/'cost_evidence.csv.gz');assert len(times)==len(costs)==26*2157
 assert [x for x in times if x['component']!='v4_added140']==[x for x in csvrows(v2/'timing_evidence.csv.gz') if x['model_id'] in ids]
 assert [x for x in costs if x['component']!='v4_added140']==[x for x in csvrows(v2/'cost_evidence.csv.gz') if x['model_id'] in ids]
 t={(x['model_id'],x['item_id']):x for x in times};c={(x['model_id'],x['item_id']):x for x in costs};assert len(t)==len(c)==26*2157 and set(t)==set(c)
 grouped=defaultdict(list);group_family=defaultdict(list);status_counts=Counter();kinds=defaultdict(Counter);money=defaultdict(lambda:[Decimal(0),Decimal(0)])
 for key,x in t.items():
  y=c[key];mid,id=key;assert mid in ids and id in qs and x['family_id']==y['family_id']==qs[id]['family_id'] and x['input_sha256']==y['input_sha256']==qs[id]['native_input_sha256'] and x['source_record_sha256']==y['source_record_sha256'] and x['status']==y['status']
  ms=float(x['latency_ms']);assert math.isfinite(ms) and ms>=0;grouped[mid].append(ms);group_family[mid,x['family_id']].append(ms);status_counts[mid,x['status']]+=1
  kind=y['evidence_kind'];assert kind in {'reported','tariff_estimate','free_access_tariff','unknown','local_unmeasured'};kinds[mid][kind]+=1
  for ix,field in enumerate(['reported_usd','tariff_estimate_usd']):
   if y[field]:
    value=Decimal(y[field]);assert value.is_finite() and value>=0;money[mid][ix]+=value
  if kind in ('unknown','local_unmeasured'):assert not y['reported_usd'] and not y['tariff_estimate_usd']
 summaries=json.loads((root/'cost_statistics.json').read_text())['models'];assert set(summaries)==ids
 for mid,m in models.items():
  assert len(grouped[mid])==2157 and status_counts[mid,'ok']==m['valid']
  near(m['mean_ms'],statistics.mean(grouped[mid]));near(m['median_ms'],statistics.median(grouped[mid]));near(m['p95_ms'],q95(grouped[mid]))
  for fid in counts:
   z=lookup[mid,fid];v=group_family[mid,fid];assert len(v)==counts[fid];near(z['mean_ms'],statistics.mean(v));near(z['median_ms'],statistics.median(v));near(z['p95_ms'],q95(v))
  cs=summaries[mid];k=kinds[mid];assert (cs['reported_count'],cs['tariff_estimate_count'],cs['free_access_tariff_count'],cs['unknown_count'],cs['local_unmeasured_count'])==(k['reported'],k['tariff_estimate'],k['free_access_tariff'],k['unknown'],k['local_unmeasured'])
  if cs['known_subtotal_usd'] is not None:assert Decimal(cs['known_subtotal_usd'])==sum(money[mid]);near(cs['known_usd_per_1000'],sum(money[mid])*1000/2157)
 page=Page();page.feed((root/'report.html').read_text());assert all('alt' in x for x in page.images)
 matrix={(x['data-model'],x['data-category']):x for x in page.cells if 'data-correct' in x};ranks={(x['data-model'],x['data-category']):x for x in page.cells if 'data-rank-correct' in x}
 assert len(matrix)==len(ranks)==len(ranked)*43 and set(matrix)==set(ranks)=={(m,f) for m in ranked for f in counts}
 for key,x in matrix.items():assert x['data-correct']==lookup[key]['correct'] and x['data-n']==lookup[key]['n'] and ranks[key]['data-rank-correct']==x['data-correct']
 for link in page.links:
  url=urlsplit(link)
  if not url.scheme and not url.netloc and url.path:assert (root/unquote(url.path)).is_file(),link
 for image in page.images:
  url=urlsplit(image.get('src',''))
  if not url.scheme and not url.netloc and url.path:assert (root/unquote(url.path)).is_file(),url.path
 for path in root.rglob('*'):
  if path.is_file() and path.suffix in ('.json','.jsonl','.csv','.md','.txt','.html','.svg'):
   text=path.read_text();assert not any(s in text for s in ['/Users/','192.168.1.','API_KEY=','Bearer sk-','"expected_answer":','"correct_option_id":','"probabilities":']),path
 print(f'PASS: 2157 questions, 43 categories, 26 models, {len(ranked)} above cutoff, {len(times):,} timing and cost records, {len(matrix):,} coloured cells plus rankings; v3 inputs, selected evidence and unchanged category scores preserved.')

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('release',type=Path);p.add_argument('v2_release',type=Path);args=p.parse_args();validate(args.release,args.v2_release)
