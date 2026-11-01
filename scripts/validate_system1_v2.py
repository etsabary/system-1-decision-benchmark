"""Public offline validation of v2 inputs, timing, selection, presentation and seals."""
import collections,csv,gzip,hashlib,io,json,math,re,xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit,unquote
import numpy as np
from datetime import date,datetime
from zoneinfo import ZoneInfo
import publish_system1_v2 as b
class Page(HTMLParser):
 def __init__(self):super().__init__();self.links=[];self.ids=[];self.overall=[];self.cells=[]
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  if a.get('id'):self.ids.append(a['id'])
  for key in ['href','src']:
   if a.get(key):self.links.append(a[key])
  if a.get('data-overall-model'):self.overall.append(a['data-overall-model'])
  if tag=='td' and 'data-correct' in a:self.cells.append(a)
def close(a,c):assert math.isclose(float(a),float(c),rel_tol=1e-10,abs_tol=1e-7),(a,c)
def rows(path):return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
def validate():
 d=b.SOURCE;seal=b.load(d/'manifest.json');all_s=b.load(d/'all_statistics.json');s=b.load(d/'statistics.json');guide=b.load(d/'category_guide.json');metadata=b.load(d/'model_metadata.json')
 assert seal['questions']==1934 and seal['categories']==41 and seal['main_models']==26 and seal['measured_models']==38 and seal['minimum_overall_accuracy']==.62
 for name,h in seal['artifacts'].items():assert b.sha(d/name)==h,name
 for name,h in seal['source_files_sha256'].items():assert b.sha(b.ROOT/name)==h,name
 assert s==b.main_view(all_s) and len(all_s['models'])==38 and len(s['models'])==26
 assert collections.Counter(m['role'] for m in s['models'].values())=={'Hosted native':20,'Local native':3,'LLM reference':3}
 assert {mid for mid,m in s['models'].items() if m['role']=='LLM reference'}=={'reference_sol','reference_opus5','reference_sonnet'}
 assert not {'kev4b','local_h2o_lightning_nemotron_4b','local_startlux_autothink4b','reference_qwen','jev113','local_h2o_lightning_4b'}&s['models'].keys()
 assert all(m['correct']*100>=62*m['n'] for m in s['models'].values())
 questions=rows(d/'questions_1934.jsonl');qq={q['id']:q for q in questions};meta={q['id']:q for q in rows(d/'metadata_core.jsonl')};assert len(questions)==len(qq)==1934 and set(qq)==set(meta)
 assert collections.Counter(q['component'] for q in meta.values())=={'original1342':1342,'logical192':192,'practical400':400}
 for q in questions:
  assert not {'expected_answer','correct_option_id','choice','probabilities'}&q.keys()
  raw=json.dumps(q['native_input'],sort_keys=True,separators=(',',':'),ensure_ascii=False).encode();assert hashlib.sha256(raw).hexdigest()==q['native_input_sha256']
  assert len(q['options'])==5 and q['family_id']==meta[q['id']]['family_id']
 old=rows(b.ROOT/'results/releases/consolidated_2026-10-19/questions_1342.jsonl');assert len(old)==1342
 for q in old:assert qq[q['id']]['native_input']==q['native_input'] and qq[q['id']]['native_input_sha256']==q['native_input_sha256']
 text=d/'questions_1934.txt';assert text.is_file() and len(b.csvrows(d/'questions_1934.csv'))==1934
 for q in b.csvrows(d/'questions_1934.csv'):
  source=qq[q['id']];assert all(q[k]==source[k] for k in ['family_id','family','instructions','context','question','native_input_sha256']);assert [q[f'option_{i}'] for i in range(1,6)]==source['options']
 families=collections.Counter(q['family_id'] for q in meta.values());assert len(families)==41 and set(guide)==set(families)
 for fid,n in families.items():assert guide[fid]['questions']==n
 assert all(families[f'P{i:02}']==40 for i in range(1,11)) and all(families[f'F{i}']==40 for i in range(26,32))
 with gzip.open(d/'timing_evidence.csv.gz','rt',newline='') as f:timing=list(csv.DictReader(f))
 assert len(timing)==73492 and not {'correct','expected_answer','choice','probabilities'}&timing[0].keys()
 grouped=collections.defaultdict(list)
 for r in timing:
  assert r['item_id'] in qq and r['input_sha256']==qq[r['item_id']]['native_input_sha256'];assert r['family_id']==meta[r['item_id']]['family_id'] and r['component']==meta[r['item_id']]['component']
  assert math.isfinite(float(r['latency_ms'])) and float(r['latency_ms'])>=0
  assert (r['status']=='ok')==(r['failure_kind']=='usable')
  assert not r['source_record_sha256'] or re.fullmatch('[a-f0-9]{64}',r['source_record_sha256'])
  date.fromisoformat(r['collection_date_toronto'])
  if r['collected_at_utc']:
   timestamp=datetime.fromisoformat(r['collected_at_utc']);assert timestamp.tzinfo is not None and timestamp.utcoffset().total_seconds()==0
   assert timestamp.astimezone(ZoneInfo('America/Toronto')).date().isoformat()==r['collection_date_toronto']
  else:assert r['collection_date_basis']=='historical_published_session_date_only'
  grouped[r['model_id']].append(r)
 assert set(grouped)==set(all_s['models'])
 cats=b.csvrows(d/'all_category_scores.csv');lookup={(c['model_id'],c['family_id']):c for c in cats};assert len(cats)==len(lookup)==1558
 for mid,m in all_s['models'].items():
  rr=grouped[mid];assert len(rr)==len({r['item_id'] for r in rr})==1934 and {r['item_id'] for r in rr}==set(qq)
  usable=[r for r in rr if r['status']=='ok'];assert len(usable)==m['valid'] and m['valid']-m['correct']==m['wrong_usable']
  failure=dict(collections.Counter(r['failure_kind'] for r in rr if r['status']!='ok'));assert failure==m['failure_counts']
  observed_dates=dict(collections.Counter(r['collection_date_toronto'] for r in rr));md=metadata[mid]
  assert observed_dates==md['collection_dates_toronto']==m['collection_dates_toronto']
  assert m['collection_first_date_toronto']==min(observed_dates) and m['collection_last_date_toronto']==max(observed_dates)
  assert dict(collections.Counter(r['collection_date_basis'] for r in rr))==md['collection_timestamp_basis_counts']
  assert dict(collections.Counter(r['source_origin'] for r in rr))==md['source_origin_counts']
  for component in ['original1342','logical192','practical400']:assert dict(collections.Counter(r['collection_date_toronto'] for r in rr if r['component']==component))==md['collection_dates_by_component'][component]
  for origin in md['source_origin_counts']:assert dict(collections.Counter(r['collection_date_toronto'] for r in rr if r['source_origin']==origin))==md['collection_dates_by_origin'][origin]
  close(m['accuracy'],m['correct']/1934);close(m['coverage'],m['valid']/1934);close(m['added_accuracy'],m['added_correct']/592)
  assert m['original_correct']+m['added_correct']==m['correct'] and m['logical_correct']+m['practical_correct']==m['added_correct']
  v=np.array([float(r['latency_ms']) for r in rr]);close(m['mean_ms'],v.mean());close(m['median_ms'],np.median(v));close(m['p95_ms'],np.quantile(v,.95));close(m['usable_median_ms'],np.median([float(r['latency_ms']) for r in usable]))
  cc=[c for c in cats if c['model_id']==mid];assert len(cc)==41 and sum(int(c['correct']) for c in cc)==m['correct'] and sum(int(c['n']) for c in cc)==1934
  for c in cc:
   assert c['family_id'] in guide and c['family']==guide[c['family_id']]['display_name'];assert int(c['n'])==families[c['family_id']];close(c['accuracy'],int(c['correct'])/int(c['n']))
   v=np.array([float(r['latency_ms']) for r in rr if r['family_id']==c['family_id']]);close(c['mean_ms'],v.mean());close(c['median_ms'],np.median(v));close(c['p95_ms'],np.quantile(v,.95))
  close(m['macro_category_accuracy'],statistics_mean([float(c['accuracy']) for c in cc]))
 maincats=b.csvrows(d/'category_scores.csv');assert maincats==[c for c in cats if c['model_id'] in s['models']]
 profiles,leaders,_,_=b.profiles_and_leaders(s,maincats,guide);assert b.csvrows(d/'model_profiles.csv')==[{k:str(v) for k,v in r.items()} for r in profiles];assert b.csvrows(d/'category_leaders.csv')==[{k:str(v) for k,v in r.items()} for r in leaders]
 for name in ['accuracy_speed','accuracy_latency','category_accuracy','category_relative_strength','original_vs_additions','local_coverage']:
  root=ET.parse(d/(name+'.svg')).getroot();description=root.find('.//{http://purl.org/dc/elements/1.1/}description');assert description is not None
  ids=json.loads(description.text)['model_ids'];expected=[mid for mid in s['ranked_model_ids'] if name!='local_coverage' or s['models'][mid]['role']=='Local native'];assert ids==expected
  assert json.loads(description.text)['minimum_overall_accuracy']==.62
  svg=(d/(name+'.svg')).read_text()
  for mid,m in all_s['models'].items():
   if mid not in s['models']:assert m['label'] not in svg,(name,mid)
 for path in [d/'report.html',b.ROOT/'docs/report.html']:
  page=Page();page.feed(path.read_text());assert page.overall==s['ranked_model_ids'] and len(page.cells)==1066 and len(page.ids)==len(set(page.ids))
  for c in page.cells:
   expected=lookup[(c['data-model'],c['data-category'])];assert c['data-correct']==expected['correct'] and c['data-n']==expected['n']
  for link in page.links:
   u=urlsplit(link)
   if not u.scheme and not u.netloc:
    if u.path:assert (path.parent/unquote(u.path)).is_file(),(path,link)
    elif u.fragment:assert u.fragment in page.ids,(path,link)
  assert 'System 1 Decision Benchmark v2' in path.read_text() and '62%' in path.read_text() and '1,934' in path.read_text()
 for path in d.iterdir():
  if not path.is_file():continue
  assert path.read_bytes()==(b.ROOT/'docs'/b.NAME/path.name).read_bytes(),path
  if path.suffix in ['.json','.jsonl','.csv','.md','.txt','.html','.svg']:
   content=path.read_text();assert all(x not in content for x in ['/Users/','192.168.1.116','192.168.1.89','API_KEY=','Bearer sk-','"expected_answer":','"correct_option_id":','"probabilities":']),path
 assert len(b.load(d/'historical_only.json'))==28
 assert b.load(d/'audit_receipt.json')['primary_records']==73492
 for entry in b.load(b.ARCHIVE/'manifest.json')['files'].values():assert b.sha(b.ARCHIVE/entry['path'])==entry['sha256']
 print('PASS: v2 bank1934/41;26main/38measured;73,492 timing rows;1558 category totals;62% graph membership; privacy, links, historical snapshots and seals.')
 return s
def statistics_mean(v):return sum(v)/len(v)
if __name__=='__main__':validate()
