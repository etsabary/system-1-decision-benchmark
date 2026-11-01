"""Publish audited local decisions and a >=50% main comparison. Offline only.

--capture reads private owner evidence once. Rebuilds use public sanitized data.
"""
from collections import Counter
from copy import deepcopy
from datetime import datetime
from zoneinfo import ZoneInfo
from html import escape
from pathlib import Path
import csv,io,json,math,re,shutil,statistics,subprocess,sys
from markdown import markdown
from matplotlib.figure import Figure
import publish_october29_decisions as visual
import publish_october30_decisions as previous
import build_readable_report as readable
from publish_consolidated_report import table

ROOT=Path(__file__).resolve().parents[1]
NAME='local_updates_2026-10-31';DEST=ROOT/'results/releases'/NAME
OLD=ROOT/'results/releases/native_additions_2026-10-30'
ARCHIVE=ROOT/'results/archives/presentation_before_october31_2026'
PRIVATE=ROOT.parent/'text-decision-hardening/runs/ollaya_lan_eight_2026-10-31'
MIN_ACCURACY=.5
CONFIGS={
 'cox:3b-int8':('local_cox3b_int8','Cox 3B INT8'),
 'adm:1-nf4':('local_adm1_nf4','ADM-1 NF4'),
 'jue:2.5b':('local_jue25b','Jue 2.5B'),
 'iota:4b-q8_0':('local_iota4b_q8','Iota 4B Q8_0'),
 'cerno:4b-v1.2-nf4':('local_cerno4b_nf4','Cerno 4B v1.2 NF4'),
 'cerno:9b-v1.2-nf4':('local_cerno9b_nf4','Cerno 9B v1.2 NF4'),
 'dexy:9b-nf4':('local_dexy9b_nf4','Dexy 9B NF4'),
 'mimo-decision:9b-nf4':('local_mimo9b_nf4','MiMo Decision 9B NF4'),
}
load,write,digest=visual.load,visual.write,visual.digest
PUBLIC_SOURCES=['scripts/publish_local_updates_2026_10_31.py','scripts/validate_local_updates_2026_10_31.py','scripts/test_local_updates_2026_10_31.py','scripts/october31_history.py']
PRESERVE=['README.md','documents/FUNCTIONS.md','docs/report.html','docs/index.html','docs/functions.html','docs/output_compliance.html','docs/sitemap.xml','scripts/layout_manifest.json','scripts/validate_october30_decisions.py']


def archive():
 target=ARCHIVE/'manifest.json'
 if target.exists():
  for name,entry in load(target)['files'].items():assert digest(ARCHIVE/entry['path'])==entry['sha256']
  return
 head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip();entries={}
 for name in PRESERVE:
  raw=subprocess.check_output(['git','show',head+':'+name],cwd=ROOT)
  assert raw==(ROOT/name).read_bytes(),'Overlapping changes: '+name
  dest=ARCHIVE/(name+'.snapshot');dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
  entries[name]={'path':name+'.snapshot','sha256':digest(dest)}
 write(target,{'commit':head,'files':entries})


def main_view(all_stats):
 """The reporting cutoff changes membership, never a measured model record."""
 s=deepcopy(all_stats);s['models']={k:v for k,v in s['models'].items() if v['accuracy']>=MIN_ACCURACY}
 keep=set(s['models']);s['ranked_model_ids']=sorted(keep,key=lambda k:(-s['models'][k]['correct'],k))
 for key in ['local_model_ids','hosted_model_ids','reference_model_ids','adaptive_model_ids']:
  s[key]=[k for k in all_stats[key] if k in keep]
 s['model_kinds']={k:v for k,v in all_stats['model_kinds'].items() if k in keep}
 s['decision_model_ids']=[k for k in s['ranked_model_ids'] if k not in s['reference_model_ids']]
 s['single_pass_decision_ids']=[k for k in s['decision_model_ids'] if k not in s['adaptive_model_ids']]
 s.update(model_count=len(keep),decision_model_count=len(s['decision_model_ids']),local_model_count=len(s['local_model_ids']),
  hosted_decision_model_count=len([k for k in s['hosted_model_ids'] if k not in s['reference_model_ids']]),primary_cases=len(keep)*1342,
  all_tested_primary_cases=all_stats['model_count']*1342,total_http_attempts=sum(m.get('attempts',m['n']) for m in s['models'].values()),
  total_recoveries=sum(m.get('recoveries',0) for m in s['models'].values()),full_bank_tested_model_count=all_stats['model_count'],
  excluded_overall_model_ids=[k for k in all_stats['ranked_model_ids'] if k not in keep],
  reporting_policy={'minimum_overall_accuracy':MIN_ACCURACY,'basis':'Unrounded first-attempt correct/n','scope':'Main ranking, figures, category tables, category leaders and narrative','evidence':'All full records remain in all_statistics.json; historical releases unchanged'})
 return s


def capture():
 assert not (DEST/'all_statistics.json').exists(),'Never recapture published evidence'
 sys.path.insert(0,str(PRIVATE))
 import continue_jue as owner
 owner.prime_key_cache()
 import analyze_frontier_reference as authority
 r=owner.r;qs,order,inventory,queue=owner.a.prepare(PRIVATE)
 gold,meta,_,bindings=authority.load_gold(r.ROOT,qs)
 summary=load(PRIVATE/'FINAL_REPORT.json');assert summary['model_count']==8 and summary['total_first_attempts']==6850
 old=load(OLD/'statistics.json');all_stats=deepcopy(old);new={};screens=[];timing=[];provenance={}
 original={x['item_id'] for x in csv.DictReader((ROOT/'results/releases/corrected_2026-10-18/questions_1136.csv').open())}
 for model in queue:
  mid,label=CONFIGS[model];d=r.folder(PRIVATE,model);aa=r.rows(d/'attempts.jsonl');dd=r.rows(d/'dispatches.jsonl')
  state=load(d/'state.json')['state'];assert load(d/'finalized.json')['state']==state and len(aa)==len(dd)
  metadata=inventory['metadata'][model];mi=metadata['model_info']
  for i,(a,dispatch) in enumerate(zip(aa,dd)):
   q=qs[order[i]];body=dict(model=model,**q['native_input'],keep_alive='10m')
   assert a['item_id']==dispatch['item_id']==q['id'] and a['request_index']==dispatch['request_index']==i+1 and a['attempt']==dispatch['attempt']==1
   assert a['native_input_sha256']==q['native_input_sha256'] and a['request_payload_sha256']==dispatch['request_payload_sha256']==r.digest(body)
   parsed=owner.a.parse(a['transport'],model,metadata);assert parsed['status']==a['status'] and parsed['choice']==a['choice']
   if model in owner.native.QUEUE:assert a['transport']['wire_payload_sha256']==a['request_payload_sha256']
   usage=a.get('usage') or {}
   timing.append(dict(model_id=mid,item_id=q['id'],family_id=q['family_id'],request_index=i+1,attempt=1,native_input_sha256=q['native_input_sha256'],request_sha256=a['request_payload_sha256'],response_sha256=visual.hashval(a['transport'].get('raw',a['transport'].get('raw_body',a['transport'].get('transport_error')))),status=a['status'],latency_ms=a['latency_ms'],input_tokens=usage.get('input_tokens'),output_tokens=usage.get('output_tokens'),http_status=a['transport'].get('http_status')))
  def outcome(ids):
   rows=[a for a in aa if a['item_id'] in ids];n=len(rows);valid=sum(a['status']=='ok' for a in rows);correct=sum(a['status']=='ok' and a['choice']==str(gold[a['item_id']]) for a in rows)
   return dict(n=n,correct=correct,answered=valid,failed=n-valid,wrong_valid=valid-correct,accuracy=correct/n if n else None)
  m=outcome(qs);t=visual.quant([a['latency_ms'] for a in aa]);statuses=dict(Counter(a['status'] for a in aa))
  dates=dict(Counter(datetime.fromisoformat(a['started_at']).astimezone(ZoneInfo('America/Toronto')).date().isoformat() for a in aa))
  context=sum(a['status']=='http_failure' and any(k in json.dumps(a['transport'].get('raw') or a['transport'].get('raw_body')).lower() for k in ['token','context','length']) for a in aa)
  public_md=dict(model_requested=model,serving_digest=metadata['digest'],source_revision=mi['local.source_revision'],representation=metadata['details'],device_observed='cuda:0',hardware='NVIDIA RTX 2060',vram_gb=6,hardware_source='Owner installation record; API confirms CUDA/VRAM but not GPU product name',cpu_fallback=mi['local.cpu_fallback'],local_quantization_changes_probabilities=mi.get('local.quantization_changes_probabilities',False),prompt_limit_tokens=mi['local.max_prompt_tokens'],identity_limit='Stable captured alias, source revision and serving digest; no independent weight attestation',source_evidence_sha256={n:digest(d/n) for n in ['attempts.jsonl','dispatches.jsonl','warmup.jsonl','admission_responses.jsonl']})
  provenance[mid]=public_md
  if state!='complete':
   assert (len(aa)==100 and m['accuracy']<.5) or (len(aa)==20 and m['failed']/20>=.05)
   screens.append(dict(model_id=mid,label=label,model_requested=model,execution_location='local',format='Native choice',scope='Partial screen',state=state,**m,**t,statuses=statuses,context_limit_failures=context,representation=metadata['details'],dates_toronto=dates,reason='Below50% on first100' if state=='stopped_low_accuracy' else 'Local context-limit failure screen; no full-bank score'))
   continue
  full=load(d/'full_report.json');assert m['n']==1342 and m['correct']==full['correct'] and t==full['timing']
  assert all(digest(d/name)==value for name,value in full['evidence_sha256'].items())
  families={f:outcome({i for i,q in qs.items() if q['family_id']==f}) for f in sorted({q['family_id'] for q in qs.values()})}
  assert {f['family_id']:(f['n'],f['correct']) for f in full['families']}=={f:(v['n'],v['correct']) for f,v in families.items()}
  profile=[dict(family_id=f,**v) for f,v in families.items() if v['n']>=20]
  m.update(model_id=mid,label=label,execution_location='local',hardware='NVIDIA RTX 2060',vram_gb=6,precision=metadata['details']['quantization_level'],runtime='Ollaya 0.17.0 · CUDA',route='Direct wired LAN · native SystemOne',model_requested=model,
   serving_digest=metadata['digest'],upstream_revision=mi['local.source_revision'],local_quantization_changes_probabilities=public_md['local_quantization_changes_probabilities'],mean_response_ms=t['mean_ms'],median_ms=t['median_ms'],p95_ms=t['p95_ms'],families=families,first_statuses=statuses,context_limit_failures=context,attempts=1342,recoveries=0,provider_failures=m['failed'],model_output_failures=0,probability_warnings=0,accuracy_among_usable=m['correct']/m['answered'],macro_family_accuracy=statistics.mean(v['accuracy'] for v in families.values()),dates_toronto=dates,returned_identities=dict(Counter(a['model_returned'] for a in aa)),providers={'Local Ollaya':1342},observed_output_tokens=sum((a.get('usage') or {}).get('output_tokens',0) for a in aa),output_token_telemetry='Native typed index counters0/1; no prose/visible reasoning trace; not a token-speed metric',original_1136=outcome(original),added_206=outcome(set(qs)-original),new_domains=outcome({i for i,q in qs.items() if q['family_id']>='F26'}),release_exclusion_diagnostic=outcome({i for i,v in meta.items() if not v['permanently_unscored_native_development']}),highest_scoring_categories=sorted(profile,key=lambda v:(-v['accuracy'],v['family_id'])),lowest_scoring_categories=sorted(profile,key=lambda v:(v['accuracy'],v['family_id'])),warmup_calls=len(r.rows(d/'warmup.jsonl')),cost=dict(kind='local_unmetered',known_usd=None,known_decimal=None,exact_usd=None,known_usd_per_1000=None,unknown_attempts=0,hardware_electricity_measured=False,scope='No metered API invoice; hardware/electricity unmeasured'))
  new[mid]=m
 all_stats['models'].update(new);all_stats['local_model_ids']+=list(new)
 all_stats['model_kinds'].update({k:'Decision / classifier' for k in new});all_stats['ranked_model_ids']=sorted(all_stats['models'],key=lambda k:(-all_stats['models'][k]['correct'],k))
 all_stats['decision_model_ids']=[k for k in all_stats['ranked_model_ids'] if k not in all_stats['reference_model_ids']];all_stats['single_pass_decision_ids']=[k for k in all_stats['decision_model_ids'] if k not in all_stats['adaptive_model_ids']]
 all_stats.update(model_count=66,decision_model_count=62,local_model_count=29,primary_cases=66*1342,all_tested_primary_cases=66*1342,updated_date_toronto='2026-10-31',added_model_ids=list(new),prior_statistics_sha256=digest(OLD/'statistics.json'),total_http_attempts=sum(m.get('attempts',m['n']) for m in all_stats['models'].values()),total_recoveries=sum(m.get('recoveries',0) for m in all_stats['models'].values()),status='66_FULL_RECORDS_PRESERVED_WITH_50_PERCENT_MAIN_REPORTING_CUTOFF')
 assert len(new)==5 and len(screens)==3 and all(all_stats['models'][k]==v for k,v in old['models'].items())
 write(DEST/'all_statistics.json',all_stats);write(DEST/'statistics.json',main_view(all_stats));write(DEST/'category_guide.json',load(OLD/'category_guide.json'));write(DEST/'screened_routes.json',screens);write(DEST/'local_model_metadata.json',provenance)
 stream=io.StringIO(newline='');w=csv.DictWriter(stream,fieldnames=list(timing[0]),lineterminator='\n');w.writeheader();w.writerows(timing);write(DEST/'local_timing_evidence.csv',stream.getvalue())
 write(DEST/'execution_protocol.json',dict(date_toronto='2026-10-31',questions=1342,question_bank_sha256=r.BANK_HASH,order_seed=r.SEED,one_model_and_request_at_a_time=True,scored_retries=0,loading_and_warmups_excluded=True,endpoint='/v1/systemone',transport='Direct wiredLAN, fresh HTTP connection through full response; public relay not used',accuracy_screen='Below50% on exactly first100',speed_screen='Cumulative median>2000ms after20',failure_screen='Unusable>=5% after20',native_envelope='Unchanged frozen state/questions; exact model added; optional keep_alive hint only on Cox/ADM, omitted for other native schemas before first scored call',context='Oversized synthetic input must explicitly reject; structured llama.cpp HTTP500 token-count rejection above captured limit accepted, generic500 rejected',limitations='Compact API omits explicit truncation/load-duration fields; synthetic rejection and captured limits remain interface evidence, not independent tokenizer attestation',local_cost='Hardware/electricity unmeasured',software_sha256={n:digest(PRIVATE/n) for n in ['executor.py','admission.py','native_envelope_queue.py','continue_jue.py','remaining_five.py']}))
 write(DEST/'audit_receipt.json',dict(status='PASS',new_full_runs=5,new_partial_screens=3,new_first_attempts=6850,prior_61_model_records_unchanged=True,question_bank_sha256=r.BANK_HASH,private_key_reconciled=True,source_binding_hashes=sorted(set(bindings.values())),all_dispatches_resolved=True,first_attempt_order_payload_and_raw_parse_verified=True,category_counts_verified=True,timing_verified=True,source_summary_sha256=digest(PRIVATE/'FINAL_REPORT.json'),public_scope='Aggregate correctness; answer-free timing/status/input-response hashes; sanitized metadata. No model choices, probabilities, per-item correctness or keys.'))


def bind_layout():
 """Bind published sources; other threads' untracked files are outside publication."""
 path=ROOT/'scripts/layout_manifest.json';value=load(path)
 tracked=set(subprocess.check_output(['git','ls-files','-z'],cwd=ROOT).decode().split('\0'))
 names=set(value['current_files'])|set(PUBLIC_SOURCES)|{'documents/FUNCTIONS.md','docs/sitemap.xml','scripts/README.md','results/README.md','documents/README.md','.github/workflows/october18-validate.yml'}
 names|={n for n in tracked if n.startswith('scripts/') and n.endswith('.py')}
 value['current_files']={n:digest(ROOT/n) for n in sorted(names) if (ROOT/n).is_file()}
 write(path,value)


def below50_rows(all_stats,screens):
 rows=[]
 for mid in all_stats['ranked_model_ids']:
  m=all_stats['models'][mid]
  if m['accuracy']<.5:rows.append(dict(model_id=mid,label=m['label'],execution_location=m.get('execution_location','hosted'),format='Selected LLM reference' if mid in all_stats['reference_model_ids'] else 'Native choice',scope='Current full 1,342',record_group='current_full',n=m['n'],correct=m['correct'],accuracy=m['accuracy'],reason='Overall below 50%',source='all_statistics.json',dates_toronto=sorted(m['dates_toronto'])))
 for m in screens:
  if m['accuracy']<.5:rows.append({k:m[k] for k in ['model_id','label','execution_location','format','scope','n','correct','accuracy']}|{'reason':'Below 50% on the first 100 questions','record_group':'screen','source':'screened_routes.json','dates_toronto':sorted(m['dates_toronto'])})
 return rows


def catalogue_markdown(rows):
 text='## Recorded results below 50%\n\nThese rows are separate from the main comparison. Full-bank runs, earlier 1,136-question runs and short screens retain their own denominators and interfaces. Format-failure scores measure the tested output contract as well as answer quality. A later qualifying format of the same model remains in the main comparison.\n\n'
 for group,title in [('current_full','Full runs removed from the current comparison'),('earlier_full','Earlier full-bank trials'),('screen','Stopped screens and output-format trials')]:
  selected=[r for r in rows if r['record_group']==group]
  text+='### '+title+'\n\n'+table(['Model / trial','Setting / format','Scope','Correct / tested','Accuracy','Reason'],[[r['label'],r['execution_location']+' · '+r['format'],r['scope'],f"{r['correct']}/{r['n']}",f"{r['accuracy']:.1%}",r['reason']] for r in selected])+'\n\n'
 return text


def findings(s):
 return '''## Cerno 4B approaches the stronger local configurations

Cerno 4B scored **983/1,342 (73.2%)** on the deliberately older RTX 2060 with 6 GB VRAM. D3 Flash Artemis retains **995 (74.1%)** and StartLux Instant **988 (73.6%)**. Cerno's **690 ms median** was longer than D3's 408 ms and Instant's 282 ms. Its mean / median / p95 were **725 / 690 / 1,112 ms**.

Cerno answered every comparison question (**40/40**), **50/52** rule-counterexample questions and **41/43** lookup questions correctly. These ask it to combine stated orderings, find a case that disproves a rule, or filter records by their conditions. Sequential procedures, applying each edit to the updated state, scored **11/48**. Truth-teller consistency scored **36/74**, and exact truth counting **35/71**. Its local NF4 conversion may differ from the upstream weights; this result applies to the recorded build.

## Jue is the fastest completed run in the new batch

Jue 2.5B scored **801/1,342 (59.7%)**, with **175 / 162 / 314 ms** mean / median / p95. It uses FP16 weights with FP32 LoRA, rather than a local low-bit conversion. Its cybersecurity specialization was not specifically evaluated by this general decision bank.

Jue selected records correctly in **40/43** lookup questions and found the governing source despite conflicting stale records in **39/43**. Sequential procedures scored **12/48**, object swaps **16/52**, and exact truth counting **24/71**. It answered 47 more questions correctly than Cox, with approximately one fifth Cox's 822 ms median latency.

## Dexy, Cox and Iota add distinct measured routes

Dexy 9B, a local NF4 conversion with INT8 embeddings, scored **833/1,342 (62.1%)** at **696 / 670 / 1,012 ms** mean / median / p95. Lookup and following directed paths each scored **39/43**; sequential procedures scored **10/48**. Cox's provider INT8 build scored **754 (56.2%)**, with **876 / 822 / 1,029 ms**. Iota's original joint-schema Q8_0 release scored **738 (55.0%)**, with **315 / 288 / 535 ms**. It is a different release from iota-decide-4b-v0.4.

Cox includes one lost connection. Jue, Cerno 4B and Dexy each include one context-limit failure; Iota returned usable decisions throughout. Every failure remains unsuccessful in the full denominator. No failed question was shortened or retried. The Cerno 9B and MiMo local builds stopped during context-limit screening and have no full-bank score; the [screening record](screened_routes.json) preserves their sample sizes and reasons.

## The main comparison now requires at least 50% overall

This is a reporting selection requested after measurement. It applies to the overall score, including failed first attempts, for every setting and model format. Exactly 50% qualifies. The same qualifying set appears in the overview, named-category tables, category leaders and narrative. Complete measured records remain available in [all statistics](all_statistics.json); [the separate below-50% catalogue](below_50.html) includes earlier LLM formats and short screens with their original sample sizes.

''' + previous.NOTE.replace('COMPATIBILITY_LINK','clairic.html') + visual.FINDINGS


METHOD='''The main display contains 56 configurations with at least50% overall accuracy. All66 complete1,342-question model records remain in the full evidence export, with every earlier score, timing, cost and test date unchanged. The ten removed full-bank rows and other below50 trials are listed separately. Short screens never enter the full-bank ranking.

The October31 additions use the same frozen1,342 native states, instructions and five choices, seed2026101906. Five complete runs and three partial screens account for6,850 first attempts. Only one local model and request ran at a time. Direct wiredLAN was used throughout. Loading, synthetic admission and warmups are outside the connection-to-complete-response timer. All first attempts, including failures, remain in the denominator and timing distribution. No scored retry or question truncation.

The normal screen stops a model after at least20 calls if cumulative median exceeds2,000ms or unusable responses reach5%. The user additionally authorized stopping below50% on exactly the first100. Two local builds stopped for context limits, and one stopped on accuracy. Those partial results do not measure a complete-bank accuracy. Other prior output-format and speed exclusions remain preserved in their dated diagnostics.

The owner identifies this deliberately accessible local setup as an RTX2060 with6GB VRAM. Live metadata confirms CUDA execution, allocated VRAM, precision, alias and stable source revisions, but does not independently attest the hardware product or weights. Cox INT8, ADM NF4 and Iota Q8_0 are provider-supplied representations. Jue uses FP16+FP32LoRA. Cerno, Dexy and MiMo use locally quantized builds, labelled in metadata. Compact native responses omit explicit truncation and load-duration fields; oversized synthetic inputs reject. Some llama.cpp context rejections use a structured HTTP500 with an explicit oversized token count, rather than4xx. Ordinary500 errors remain failures. Native typed-index counters0/1 do not expose reasoning.

All prior adaptive StartLux, Apple M2, hosted-provider and reasoning-off LLM settings remain attached to their original rows. Purple marks local CUDA, magenta Apple M2, blue hosted decisions and pale yellow LLM references. AutoThink retains its thick gold frame, dot pattern and generation proportions. Its authorized adaptive research exception is unchanged. Colors encode accuracy and speed/cost using the same fixed scales. Provider load, hardware, interfaces and dates differ; these are measured service timings, not isolated architectural speed comparisons. Local hardware and electricity costs are unmeasured.

Offline audits bound the private answer key, checked unique first attempts, native/wire request and response hashes, model revisions, CUDA placement, coverage, category sums and timing. Public artifacts contain aggregate correctness and answer-free timing/status/hash evidence. They do not include private keys, model choices, per-item correctness or private network details. Public checks reproduce coverage, timing and aggregate arithmetic; private-key accuracy cannot be independently rescored from public aggregates. Unequal category sizes and dependent variants remain qualifications of the developing bank.'''


def prose_spaces(text):
 for a,b in {'at least50':'at least 50','All66':'All 66','complete1,342':'complete 1,342','below50':'below 50','October31':'October 31','frozen1,342':'frozen 1,342','seed2026101906':'seed 2026101906','for6,850':'for 6,850','wiredLAN':'wired LAN','least20':'least 20','exceeds2,000ms':'exceeds 2,000 ms','reach5%':'reach 5%','first100':'first 100','Cerno9B':'Cerno 9B','RTX2060':'RTX 2060','with6GB':'with 6 GB','FP16+FP32LoRA':'FP16 + FP32 LoRA','HTTP500':'HTTP 500','rather than4xx':'rather than 4xx','Ordinary500':'Ordinary 500','counters0/1':'counters 0/1'}.items():text=text.replace(a,b)
 return text


def build():
 all_stats=load(DEST/'all_statistics.json');s=main_view(all_stats);guide=load(DEST/'category_guide.json');screens=load(DEST/'screened_routes.json')
 assert s['model_count']==56 and len(s['excluded_overall_model_ids'])==10
 archive();visual.DEST=DEST;visual.NAME=NAME;visual.previous.DEST=DEST
 visual.previous.exports(s,guide)
 original_title=Figure.suptitle
 def title(fig,text,*args,**kwargs):return original_title(fig,str(text).replace('60 routes',f"{s['model_count']} qualifying configurations"),*args,**kwargs)
 Figure.suptitle=title
 try:visual.overview(s);visual.category_plots(s);visual.adaptive_plot(s)
 finally:Figure.suptitle=original_title
 # Reuse the established local/hosted/reference colors, adaptive frame and readable tables.
 summary_md,summary_html=visual.summary(s)
 rows=below50_rows(all_stats,screens)
 historical=load(DEST/'historical_below50.json') if (DEST/'historical_below50.json').exists() else []
 rows+=historical;write(DEST/'below_50.json',rows)
 catalogue=catalogue_markdown(rows);write(DEST/'below_50.md',catalogue)
 catalogue_html='<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>System 1 benchmark: results below 50%</title><style>body{font:16px/1.6 system-ui;margin:32px auto;padding:0 24px;max-width:1500px}table{border-collapse:collapse;width:100%}td,th{border:1px solid #ccd;padding:10px;text-align:left}a{color:#16728c}</style><main>'+markdown(catalogue,extensions=['tables'])+'<p><a href="report.html">Return to the qualifying main comparison</a> · <a href="below_50.json">Source-labelled catalogue</a> · <a href="all_statistics.json">All complete 1,342-question records</a></p></main>'
 write(DEST/'below_50.html',catalogue_html)
 narrative=findings(s);method=prose_spaces(METHOD)
 groups=readable.markdown_groups(s,guide).replace('All 20 models','All 56 qualifying configurations').replace('all 20 models','all 56 qualifying configurations').replace(readable.NAME,'results/releases/'+NAME)
 groups=re.sub(r'https://etsabary.github.io/jev-1.14-comparison-benchmark/[^)# ]+/report.html',visual.SITE,groups)
 # Narrative links use release-local names; repository Markdown gets release paths.
 root_narrative=narrative
 for file in ['screened_routes.json','all_statistics.json','below_50.html','clairic.html']:root_narrative=root_narrative.replace(']('+file+')','](results/releases/'+NAME+'/'+file+')')
 intro='# System 1 Decision Benchmark\n\n**56 configurations meeting the 50% overall reporting cutoff**, each tested on the same **1,342 questions across31 categories**:31 hosted decisions,20 immediate local configurations, one adaptive local model and four selected no-reasoning LLM references. Updated October31,2026.\n\n**Fastino GLiDE leads overall at86.0%. D3 Flash Artemis leads immediate local configurations at74.1%. Cerno4B adds73.2%; Jue2.5B adds a162ms median at59.7%.**\n\n[Interactive report]('+visual.SITE+') · [Named categories]('+visual.SITE+'#functions) · [Adaptive AutoThink]('+visual.SITE+'#adaptive) · [Below50 results and trial scopes](results/releases/'+NAME+'/below_50.html)\n\n![Qualifying configurations: hosted blue, localCUDA purple, AppleM2 magenta, LLM references pale yellow; AutoThink framed in gold](results/releases/'+NAME+'/accuracy_speed_cost.png)\n\nPurple identifies local CUDA runs; magenta identifies AppleM2; blue identifies hosted decisions; pale yellow identifies LLM references. AutoThink retains a thick gold frame and dot pattern. All66 complete records remain available;10 overall scores below50% are outside the main comparison.\n\n## Main comparison\n\n'+summary_md+'\n\nMedian is the midpoint response time. p95 describes the slower tail:95% of measured responses completed within that time. Local hardware and electricity costs remain unmeasured.\n\n'
 intro=intro.replace('across31','across 31').replace(':31',': 31').replace('decisions,20','decisions, 20').replace('October31,2026','October 31, 2026').replace('at86.0%','at 86.0%').replace('at74.1%','at 74.1%').replace('Cerno4B adds73.2%','Cerno 4B adds 73.2%').replace('Jue2.5B adds a162ms median at59.7%','Jue 2.5B adds a 162 ms median at 59.7%').replace('Below50','Below 50%').replace('localCUDA','local CUDA').replace('AppleM2','Apple M2').replace('All66','All 66').replace(';10','; 10').replace('below50%','below 50%').replace('tail:95%','tail: 95%')
 end='\n\n## Method and evidence\n\n'+method+'\n\n[Main statistics](results/releases/'+NAME+'/statistics.json) · [All full-run statistics](results/releases/'+NAME+'/all_statistics.json) · [New timing evidence](results/releases/'+NAME+'/local_timing_evidence.csv) · [Screening outcomes](results/releases/'+NAME+'/screened_routes.json) · [Audit receipt](results/releases/'+NAME+'/audit_receipt.json) · [Question bank](results/releases/consolidated_2026-10-19/questions_1342.csv) · [scripts/](scripts/README.md). Historical check: `python3 scripts/validate_october21_release.py`.\n'
 write(ROOT/'README.md',intro+root_narrative+'\n\n'+groups+end)
 functions=readable.markdown_groups(s,guide,details=True).replace('All 20 models','All 56 qualifying configurations').replace('all 20 models','all 56 qualifying configurations').replace(readable.NAME,'../results/releases/'+NAME)
 functions=re.sub(r'https://etsabary.github.io/jev-1.14-comparison-benchmark/[^)# ]+/report.html',visual.SITE,functions)
 write(ROOT/'documents/FUNCTIONS.md','# Named functions: qualifying main comparison\n\nOnly configurations with at least50% overall appear here. Individual category scores below50% remain visible because the cutoff applies to overall accuracy.\n\n'.replace('least50%','least 50%').replace('below50%','below 50%')+functions)
 old_page=(OLD/'report.html').read_text();head=old_page[:old_page.index('<body>')+6]
 head=re.sub(r'<title>.*?</title>','<title>System 1 Decision Benchmark · 56 qualifying configurations</title>',head)
 head=re.sub(r'<meta name="description"[^>]+>','<meta name="description" content="56 qualifying configurations on 1,342 text questions; accuracy, speed, cost and 31 named categories. Separate below-50% catalogue retains failed trials.">',head)
 adaptive=old_page[old_page.index('<section id="adaptive"'):old_page.index('<section id="findings"')]
 cards=old_page[old_page.index('<div class="cards"'):old_page.index('<section id="overview"')]
 body='<main><h1>System 1 Decision Benchmark</h1><p>56 configurations meeting the50% overall reporting cutoff on the same1,342 questions across31 categories.31 hosted decisions,20 immediate local configurations, one adaptive local model and four selected reasoning-off LLM references. Updated October31,2026.</p><nav><a href="#overview">Main comparison</a> · <a href="#findings">Findings</a> · <a href="#functions">Named categories</a> · <a href="#adaptive">✦ AutoThink</a> · <a href="below_50.html">Below50 results</a> · <a href="#method">Method</a></nav>'+cards+'<section id="overview"><h2>Accuracy, speed and cost</h2><p>All main rows cover1,342 first attempts and score at least50% overall. Every graph, category table and category ranking uses this same qualifying set. The <a href="all_statistics.json">66 complete measured records</a> and <a href="below_50.html">separate below50 catalogue</a> retain excluded outcomes. Cell and speed/cost scales are unchanged.</p><div class="figure"><a href="accuracy_speed_cost.svg"><img src="accuracy_speed_cost.png" alt="56 qualifying configurations, accuracy and speed-cost comparison with local setup colors"></a></div>'+summary_html+visual.previous.prior.tables.prior.prior.legend_html()+'</section>'+adaptive+'<section id="findings">'+markdown(narrative,extensions=['tables'])+'</section>'+visual.mark_names(readable.clarity_section(s,guide),s).replace('All 60 routes','All 56 qualifying configurations').replace('all 60 routes','all 56 qualifying configurations')+'<section id="method"><h2>Method and evidence</h2>'+markdown(method)+'<p><a href="statistics.json">Main aggregates</a> · <a href="all_statistics.json">All full records</a> · <a href="local_timing_evidence.csv">New timing/hashes</a> · <a href="screened_routes.json">Stopped screens</a> · <a href="below_50.html">Below50 analysis list</a> · <a href="local_model_metadata.json">New local build metadata</a> · <a href="execution_protocol.json">Execution settings</a> · <a href="audit_receipt.json">Audit receipt</a> · <a href="../consolidated_2026-10-19/questions_1342.csv">Question bank</a></p></section></main></body></html>'
 for old,new in {'the50%':'the 50%','same1,342':'same 1,342','across31':'across 31','categories.31':'categories. 31','decisions,20':'decisions, 20','October31,2026':'October 31, 2026','Below50':'Below 50%','below50':'below-50%','cover1,342':'cover 1,342','least50%':'least 50%'}.items():body=body.replace(old,new)
 page=head+body;write(DEST/'report.html',page);write(DEST/'analysis.md',narrative+'\n\n'+catalogue+'\n\n## Method\n\n'+method)
 write(ROOT/'docs/report.html',visual.previous.prior.tables.prior.rebase(page,NAME))
 for name,anchor in [('index.html',''),('functions.html','#functions'),('output_compliance.html','#method')]:write(ROOT/'docs'/name,'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta http-equiv="refresh" content="0;url=report.html'+anchor+'"><title>System1 Decision Benchmark</title></head><body><a href="report.html'+anchor+'">56 qualifying configurations</a></body></html>')
 # Keep the prior extraction comparison and its evidence accessible at this release.
 for name in ['clairic.html','clairic_compatibility.json','october30_timing_evidence.csv']:shutil.copy2(OLD/name,DEST/name)
 for file in DEST.glob('*.svg'):write(file,'\n'.join(x.rstrip() for x in file.read_text().splitlines()))
 write(DEST/'manifest.json',dict(version='local-october31-1342-v1',main_models=56,all_full_models=66,main_accuracy_minimum=.5,prior_statistics_sha256=digest(OLD/'statistics.json'),artifacts={p.name:digest(p) for p in sorted(DEST.iterdir()) if p.is_file() and p.name!='manifest.json'}))
 shutil.copytree(DEST,ROOT/'docs'/NAME,dirs_exist_ok=True)
 write(ROOT/'docs/sitemap.xml','<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url><loc>'+visual.SITE+'</loc><lastmod>2026-10-31</lastmod></url></urlset>')
 bind_layout()
 print('Built56 qualifying configurations;66 full records preserved; no inference.')

if __name__=='__main__':
 if '--capture' in sys.argv:capture()
 if '--capture-only' not in sys.argv:build()
