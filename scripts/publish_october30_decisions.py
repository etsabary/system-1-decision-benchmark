"""Publish Joey-1 and a separate Clairic extraction compatibility result, offline."""
import csv,io,json,math,re,shutil,statistics,sys
from collections import Counter
from copy import deepcopy
from decimal import Decimal
from pathlib import Path
from html import escape
from markdown import markdown
import publish_october29_decisions as prior

ROOT=prior.ROOT
NAME='native_additions_2026-10-30';DEST=ROOT/'results/releases'/NAME
OLD=ROOT/'results/releases/adaptive_additions_2026-10-29'
ARCHIVE=ROOT/'results/archives/presentation_before_october30_2026'
RUN=ROOT.parent/'text-decision-hardening/runs/joey_clairic_2026-10-30'
MID='baseten_joey1'
load,write,digest=prior.load,prior.write,prior.digest

NOTE='''## October 30: Joey-1 and an extraction-model comparison

Joey-1 scored **773/1,342 (57.6%)**, with a **179 ms mean, 163 ms median and 256 ms p95**. All first attempts returned usable native decisions. OpenRouter reported **$0.00484453** for the full bank, or **$0.00360993 per 1,000 questions**. The reported output-token counter was one per decision; the native endpoint returned no prose or reasoning trace.

The larger Baseten models remain substantially more accurate: **Mammoth-1 84.9%** and **Elephant-1 74.8%**. Their recorded medians were 240 and 139 ms. Those October 21 runs used Baseten directly; Joey used OpenRouter on October 30. Dates and routes remain visible, so these speeds do not isolate model size. The earlier promotional access is not a permanent production price.

Joey was strong on comparisons (**38/40**) and forward conditionals (**42/46**). One-to-one assignments, such as matching people to roles under constraints, fell to **24/67**, versus Mammoth's 64 and Elephant's 60. Sequential procedures scored **11/48**. Its lower cost did not approach the leading models' accuracy on this bank.

**Clairic is reported separately as an extraction adapter.** It returned an integer option ID through OpenRouter's Extractions API and scored **729/1,342 (54.3%)**, with **293 / 263 / 444 ms mean / median / p95** and **$0.05851030** reported cost. Six returned numbers outside the supplied option IDs and count as unsuccessful. Directed reachability, following one-way paths, scored **40/43**; Boolean scope **13/54**, sequential procedures **12/48** and exact truth counting **21/71**. This measures the adapted interface, not a native choice endpoint.

The leaders and their earlier measurements are unchanged. [Clairic's labelled results and category scores](COMPATIBILITY_LINK) are outside the native decision ranking.

'''

def preserve():
 if (ARCHIVE/'manifest.json').exists():return
 files={}
 for name in ['README.md','docs/report.html','docs/index.html','docs/functions.html','docs/output_compliance.html','docs/sitemap.xml']:
  src=ROOT/name;dst=ARCHIVE/name;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst);files[name]=dict(path=name,sha256=digest(src))
 write(ARCHIVE/'manifest.json',dict(files=files))

def capture():
 assert not (DEST/'statistics.json').exists(),'Do not overwrite captured evidence'
 sys.path.insert(0,str(RUN))
 import runner as owner
 import score as scorer
 import audit_clairic
 j=scorer.score('text',True);c=audit_clairic.audit(True)
 qq,order,_=owner.F.inputs('text');gold,_,_=scorer.keys('text',qq)
 aa=owner.F.rows(RUN/'joey/text/attempts.jsonl');ca=owner.F.rows(RUN/'clairic/attempts.jsonl')
 old=load(OLD/'statistics.json');s=deepcopy(old)
 original={r['item_id'] for r in csv.DictReader((ROOT/'results/releases/corrected_2026-10-18/questions_1136.csv').open())}
 def outcome(rr,ids):
  z=[a for a in rr if a['item_id'] in ids];n=len(z);answered=sum(a['status']=='ok' for a in z);correct=sum(a['status']=='ok' and a['choice']==gold[a['item_id']] for a in z)
  return dict(n=n,correct=correct,answered=answered,failed=n-answered,wrong_valid=answered-correct,accuracy=correct/n if n else None)
 m=outcome(aa,set(qq));families={f:outcome(aa,{i for i,q in qq.items() if q['family_id']==f}) for f in j['families']}
 total=sum(Decimal(a['accounted_cost_usd']) for a in aa)
 m.update(model_id=MID,label='Joey-1',model_requested='baseten/joey-1',execution_location='hosted',route='OpenRouter → BaseTen',hardware='Provider hardware unreported',precision='Unreported',runtime='Native Decisions API',
  mean_response_ms=j['mean_ms'],median_ms=j['median_ms'],p95_ms=j['p95_ms'],families=families,first_statuses=j['statuses'],attempts=1342,recoveries=0,provider_failures=0,model_output_failures=0,
  probability_warnings=sum(not a['probabilities_valid'] for a in aa),accuracy_among_usable=m['accuracy'],macro_family_accuracy=statistics.mean(v['accuracy'] for v in families.values()),dates_toronto={'2026-10-30':1342},
  returned_identities=dict(Counter(a['model_returned'] for a in aa)),providers={'BaseTen':1342},observed_output_tokens=1342,output_token_telemetry='One counter per native decision; no prose or reasoning trace. Provider documents single-pass scoring.',
  original_1136=outcome(aa,original),added_206=outcome(aa,set(qq)-original),new_domains=outcome(aa,{i for i,q in qq.items() if q['family_id']>='F26'}),
  cost=dict(known_usd=float(total),known_decimal=str(total),exact_usd=float(total),known_attempts=1342,unknown_attempts=0,known_usd_per_1000=float(total)/1342*1000,scope='API-reported OpenRouter usage.cost',source='api_reported'))
 m['highest_scoring_categories']=sorted([dict(family_id=f,**v) for f,v in families.items() if v['n']>=20],key=lambda v:(-v['accuracy'],v['family_id']))
 m['lowest_scoring_categories']=sorted(m['highest_scoring_categories'],key=lambda v:(v['accuracy'],v['family_id']))
 s['models'][MID]=m;s['model_kinds'][MID]='Decision model';s['hosted_model_ids'].append(MID)
 s['ranked_model_ids']=sorted(s['models'],key=lambda k:(-s['models'][k]['correct'],k))
 s['decision_model_ids']=[k for k in s['ranked_model_ids'] if k not in s['reference_model_ids']]
 s['single_pass_decision_ids']=[k for k in s['decision_model_ids'] if k not in s['adaptive_model_ids']]
 s.update(model_count=61,decision_model_count=57,hosted_decision_model_count=33,primary_cases=81862,all_tested_primary_cases=81862,updated_date_toronto='2026-10-30',added_model_ids=[MID],prior_statistics_sha256=digest(OLD/'statistics.json'),status='COMPLETE_61_ROUTES_WITH_SEPARATE_EXTRACTION_COMPATIBILITY')
 assert all(s['models'][k]==v for k,v in old['models'].items())
 write(DEST/'statistics.json',s);write(DEST/'category_guide.json',load(OLD/'category_guide.json'))
 # Only aggregate adapter results and answer-free measurement evidence leave the owner run.
 clean={k:c[k] for k in ['n','correct','accuracy','mean_ms','median_ms','p95_ms','statuses','cost_usd','missing_cost','usage','scope','state']}
 clean.update(label='Clairic: extraction number adapter',model_requested='cloudflare/clairic',returned_identity='cloudflare/clairic-20261029',date='2026-10-30',included_in_native_ranking=False,
  families={f:{k:v[k] for k in ['name','n','correct','accuracy','mean_ms','median_ms','p95_ms','statuses']} for f,v in c['families'].items()},
  interface='POST /api/alpha/extractions; original state, question/instructions and options concatenated as state; one integer field requests the option ID. Null/out-of-range values fail; no answer remapping.',cost_source='API-reported OpenRouter usage.cost')
 write(DEST/'clairic_compatibility.json',clean)
 timing=[]
 for mid,records in [(MID,aa),('clairic_extraction',ca)]:
  for a in records:
   q=qq[a['item_id']];timing.append(dict(model_id=mid,item_id=a['item_id'],family_id=a['family_id'],index=a['request_index'],attempt=a['attempt'],native_input_sha256=q['native_input_sha256'],request_sha256=a['payload_sha256'],response_sha256=prior.hashval(a['transport']['raw_response']),status=a['status'],latency_ms=a['latency_ms'],input_tokens=a['usage']['input_tokens'],output_tokens=a['usage']['output_tokens'],reported_cost_usd=a['accounted_cost_usd']))
 stream=io.StringIO(newline='');w=csv.DictWriter(stream,fieldnames=list(timing[0]),lineterminator='\n');w.writeheader();w.writerows(timing);write(DEST/'october30_timing_evidence.csv',stream.getvalue())
 metadata={name:load(RUN/(name+'.json')) for name in ['joey_endpoints_start','joey_endpoints_end','clairic_endpoints_start','clairic_endpoints_end']}
 write(DEST/'model_metadata.json',metadata)
 write(DEST/'execution_protocol.json',dict(date='2026-10-30',bank_sha256=s['question_bank_sha256'],scored_retries=0,maximum_inflight_per_model=1,failure_cutoff='At least20: unusable>=5%',speed_cutoff='At least20: cumulative median>2000ms',timing='Fresh HTTPS connection through complete response body; preparation, scoring and idle excluded',
  joey=dict(endpoint='/api/alpha/decisions',provider_only='baseten',allow_fallbacks=False,model='baseten/joey-1',returned='baseten/joey-1-20261029',output_tokens='One native decision counter per call, no generated prose or reasoning trace'),
  clairic=dict(endpoint='/api/alpha/extractions',provider_only='cloudflare',allow_fallbacks=False,model='cloudflare/clairic',field=dict(type='number',integer=True,instructions='Return the numeric ID of the single option that correctly answers the question. Select only from the option IDs provided.'),output_tokens=0,comparison='Separately labelled extraction adaptation'),
  sources={name:owner.F.filehash(RUN/name) for name in ['runner.py','score.py','clairic.py','audit_clairic.py']}))
 write(DEST/'audit_receipt.json',dict(status='PASS',new_native_runs=1,new_native_first_attempts=1342,separate_extraction_first_attempts=1342,previous_60_model_records_unchanged=True,all_dispatches_resolved=True,private_key_reconciled=True,category_sums_verified=True,raw_responses_reparsed=True,public_scope='Aggregate correctness and answer-free timing/hashes only'))

def compatibility_page(c,guide):
 names={f:(guide[f].get('name',f) if isinstance(guide,dict) and f in guide else v['name']) for f,v in c['families'].items()}
 body='<h1>Clairic: extraction compatibility on text decisions</h1><p>October 30, 2026. OpenRouter → Cloudflare. This adapted extraction result is separate from the native decision ranking.</p><p><b>729/1,342 (54.3%)</b> · mean 293 ms · median 263 ms · p95 444 ms · API-reported cost $0.05851030. Six out-of-range answers remain unsuccessful first attempts.</p><p>'+escape(c['interface'])+'</p><table><thead><tr><th>Category</th><th>Correct</th><th>Accuracy</th></tr></thead><tbody>'
 for f,v in c['families'].items():
  bg,fg=prior.read.color(v['accuracy']);body+=f'<tr><th>{escape(f+" "+names[f])}</th><td>{v["correct"]}/{v["n"]}</td><td style="background:{bg};color:{fg}">{v["accuracy"]:.1%}</td></tr>'
 body+='</tbody></table><p><a href="clairic_compatibility.json">Aggregate scores</a> · <a href="october30_timing_evidence.csv">Answer-free timing evidence</a> · <a href="report.html">Full native comparison</a></p>'
 return '<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Clairic text compatibility</title><style>body{font:16px/1.6 system-ui;margin:30px auto;padding:0 20px;max-width:1100px;color:#172638}table{border-collapse:collapse;width:100%}th,td{padding:10px;border:1px solid #ccd}th{text-align:left}td{text-align:right}</style>'+body+'</html>'

def build():
 preserve()
 # Reuse the established readable tables, fixed color scales and adaptive styling.
 prior.DEST=DEST;prior.NAME=NAME;prior.OLD=OLD
 note=NOTE.replace('COMPATIBILITY_LINK','results/releases/'+NAME+'/clairic.html')
 prior.FINDINGS=note+prior.FINDINGS
 prior.METHOD='The October 30 addition uses the unchanged frozen 1,342 questions through OpenRouter, pinned to BaseTen for Joey. All 1,342 first attempts are usable. Clairic uses a separately labelled integer extraction field; six out-of-range IDs count as unsuccessful. Raw responses, request hashes, identity, coverage and category totals were reconciled offline with the frozen private key. The new answer-free timing export includes both models; no scored calls were retried.\n\n'+prior.METHOD
 from matplotlib.figure import Figure
 original=Figure.suptitle
 def title(fig,text,*a,**kw):return original(fig,str(text).replace('60 routes','61 routes'),*a,**kw)
 Figure.suptitle=title
 try:prior.build()
 finally:Figure.suptitle=original
 for path in [ROOT/'README.md',ROOT/'docs/report.html',ROOT/'docs/index.html',ROOT/'docs/functions.html',ROOT/'docs/output_compliance.html',DEST/'report.html',DEST/'analysis.md']:
  text=path.read_text().replace('60 configurations','61 configurations').replace('60 routes','61 routes').replace('60-configuration','61-configuration').replace('All 60','All 61').replace('all 60','all 61').replace('32 hosted decision','33 hosted decision').replace('32 hosted decisions','33 hosted decisions').replace('Updated October 29, 2026','Updated October 30, 2026')
  text=text.replace('october29_timing_evidence.csv','october30_timing_evidence.csv')
  if path.name=='analysis.md':text=text.replace('](results/releases/'+NAME+'/','](')
  if path.name=='report.html':
   target='clairic.html' if path.parent==DEST else NAME+'/clairic.html'
   text=text.replace('href="results/releases/'+NAME+'/clairic.html"','href="'+target+'"').replace('href="'+NAME+'/results/releases/'+NAME+'/clairic.html"','href="'+NAME+'/clairic.html"')
  write(path,text)
 write(DEST/'clairic.html',compatibility_page(load(DEST/'clairic_compatibility.json'),load(DEST/'category_guide.json')))
 seal()
 write(ROOT/'docs/sitemap.xml','<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url><loc>'+prior.SITE+'</loc><lastmod>2026-10-30</lastmod></url></urlset>')
 prior.previous.bind_layout()

def seal():
 manifest=dict(version='native-october30-1342-v1',models=61,questions_each=1342,separate_extraction_reference=True,prior_statistics_sha256=digest(OLD/'statistics.json'),artifacts={p.name:digest(p) for p in sorted(DEST.iterdir()) if p.is_file() and p.name!='manifest.json'})
 write(DEST/'manifest.json',manifest);shutil.copytree(DEST,ROOT/'docs'/NAME,dirs_exist_ok=True)

if __name__=='__main__':
 if '--capture' in sys.argv:capture()
 build()
