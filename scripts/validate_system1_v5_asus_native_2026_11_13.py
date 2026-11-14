"""Offline checks for separate ASUS native partial screens and unchanged full-bank results."""
import argparse,collections,csv,gzip,hashlib,html,io,json,math,re,statistics
from pathlib import Path
from urllib.parse import unquote,urlsplit
import validate_system1_v5_provisional_2026_11_09 as base
import validate_system1_v5_hosted_refresh_2026_11_13 as hosted

SPECS={
 'qev_05b_native_resident_ctx4096_screen100':dict(alias='qev-0.5b',correct=19,inputs=65459,abstained=5,missing_abstained=0,backbone='ken-jo/QEV-0.8B',revision='bb7107f413e855949462b900b26a622f4817160e'),
 'qev_13b_native_resident_ctx4096_screen100':dict(alias='qev-1.3b',correct=22,inputs=65459,abstained=2,missing_abstained=0,backbone='ken-jo/QEV-2B',revision='7534f3b77eddaff5de4e6e75801677b976b5d2f5'),
 'gs1_08b_native_resident_ctx4096_screen100':dict(alias='gs1-0.8b',correct=27,inputs=55188,abstained=0,missing_abstained=100,backbone=None,revision=None),
}
read=lambda p:json.loads(p.read_text());canonical=lambda x:json.dumps(x,sort_keys=True,ensure_ascii=False,separators=(',',':'),allow_nan=False).encode();digest=lambda x:hashlib.sha256(canonical(x)).hexdigest()
def data(p):return gzip.decompress(p.read_bytes()) if p.name.endswith('.gz') else p.read_bytes()
def rows(p):return list(csv.DictReader(io.StringIO(data(p).decode())))
def wilson_upper(k,n):
 z=1.959963984540054;p=k/n;return (p+z*z/(2*n)+z*math.sqrt(p*(1-p)/n+z*z/(4*n*n)))/(1+z*z/n)
def validate(dest,prior,mirror=None):
 repo=Path(__file__).resolve().parents[1];hosted.validate(prior,repo/'results/releases/system1_v5_gemini_decision1_2026-11-13')
 manifest=base.check_manifest(dest);assert manifest['version']=='v5-provisional-asus-native-screens' and manifest['frozen_hosted_refresh_manifest_sha256']==base.sha(prior/'manifest.json')
 for n,h in manifest['source_files_sha256'].items():assert base.sha(repo/n)==h,n
 old=read(prior/'statistics.json');assert read(dest/'statistics.json')==old and len(old['models'])==42 and len(old['ranked_model_ids'])==34 and len(old['below_cutoff'])==6 and len(old['superseded_model_ids'])==2
 for k,v in [('questions',1456),('categories',43),('measured_models',42),('main_models',34),('partial_screen_models',3),('partial_records_per_ledger',300)]:assert manifest[k]==v,k
 for k in ['minimum_overall_accuracy','inclusion_threshold','superseded_model_ids']:assert manifest[k]==old[k],k
 assert manifest['partial_screen_ids']==list(SPECS) and manifest['all_full_bank_files_unchanged'] is True
 unchanged={str(q.relative_to(prior)):base.sha(q) for q in prior.rglob('*') if q.is_file() and q.name not in ['report.html','README_V5.md','manifest.json']}
 assert manifest['unchanged_files_sha256']==unchanged
 for n,h in unchanged.items():assert base.sha(dest/n)==h,n
 assert (dest/'parent_hosted_refresh_manifest.json').read_bytes()==(prior/'manifest.json').read_bytes()
 summaries=read(dest/'asus_native_screen_statistics.json');models=summaries['models'];profiles=read(dest/'asus_native_screen_profiles.json');audit=read(dest/'asus_native_screen_audit.json')
 assert summaries['bank_questions']==1456 and summaries['bank_categories']==43 and summaries['full_bank_cutoff_percent']==45 and set(models)==set(profiles)==set(audit['models'])==set(SPECS)
 assert audit['status']=='author_offline_checks_passed' and audit['shared_first100_prefix'] and audit['no_full_bank_records_appended'] and audit['fresh_batch_review_verdict']=='APPROVE' and re.fullmatch('[0-9a-f]{64}',audit['fresh_batch_review_sha256'])
 qs={q['id']:q for q in base.jsonlines(dest/'questions_1456.jsonl')};reference=sorted((x for x in rows(prior/'hosted_refresh_usage_evidence.csv.gz') if x['model_id']=='pplx_decider13_native_20261112'),key=lambda x:int(x['sequence']))[:100];expected=[x['item_id'] for x in reference]
 tables={}
 for n in ['timing','cost','correctness','usage']:
  rr=rows(dest/f'asus_native_screen_{n}.csv.gz');idx={(x['model_id'],x['item_id']):x for x in rr};assert len(rr)==len(idx)==300 and {x['model_id'] for x in rr}==set(SPECS)
  for mid in SPECS:
   part=sorted((x for x in rr if x['model_id']==mid),key=lambda x:int(x['sequence']));assert len(part)==100 and [x['item_id'] for x in part]==expected and [int(x['sequence']) for x in part]==list(range(1,101))
  tables[n]=idx
 t,c,f,u=[tables[n] for n in ['timing','cost','correctness','usage']]
 for mid,spec in SPECS.items():
  m=models[mid];p=profiles[mid];proof=audit['models'][mid];sig=p['server_declared_runtime'];lat=[];tokens=[];abstained=[];ordered=[]
  assert m['model_id']==mid and m['alias']==spec['alias'] and m['n']==m['usable']==m['raw_usage_diagnostic_denominator']==m['abstention_flag_diagnostic_denominator']==100 and m['correct']==spec['correct']
  assert m['full_bank_questions']==1456 and m['unattempted']==1356 and all(m[k] is None for k in ['full_bank_accuracy','full_bank_cutoff_classification','full_bank_rank','reported_cost_usd','tariff_estimate_usd'])
  assert not m['continuation_authorized'] and m['first_attempts_only'] and all(m[k]==0 for k in ['scored_retries','request_errors','truncations','resident_runtime_changes','raw_output_tokens','unknown_output_counter_count']) and m['no_generated_reasoning_text_observed'] and m['zero_generation_independently_attested'] is False
  assert m['cost_basis']=='Local hardware and electricity unmetered, not zero' and m['collection_date_toronto']=='2026-11-13'
  assert p['alias']==spec['alias'] and sig['context_limit']==4096 and sig['native_llama_cpp'] is False and sig['device']=='cuda:0' and sig['all_parameters_cuda'] is True and sig['truncation'] is False and sig['engine']=='publisher PyTorch CUDA' and sig['gpu']=='NVIDIA GeForce RTX 2060'
  assert p['profile_signature_sha256']==digest(sig) and 'not independent' in p['identity_limit']
  if spec['backbone']:
   assert sig['body_identity']['backbone']=={'model_id':spec['backbone'],'revision':spec['revision']} and sig['body_identity']['architecture']=='option_readout' and sig['body_identity']['decision_views']==1 and sig['body_identity']['mode']=='accurate'
   assert sig['precision']=='FP32 CUDA text/readout; unused vision weights retain BF16 storage on GPU' and sig['attention_backend']=='FP32 memory-efficient CUDA SDPA; repeated KV'
  else:assert sig['body_identity']=={} and sig['precision']=='FP32 CUDA eager reference' and sig['parameter_dtypes']=={'torch.float32':532} and sig['attention_backend']=='publisher eager reference'
  assert proof['source_alias']==spec['alias'] and proof['attempts']==100 and proof['no_scored_retries'] and proof['readiness_and_pre_score_diagnostics_excluded'] and proof['fresh_independent_review_verdict']=='APPROVE' and proof['exact_native_formatter_usage_matches']==100
  for key in ['source_manifest_sha256','screen_handoff_sha256','root_screen_review_sha256','fresh_independent_review_sha256','first100_raw_records_digest','plan_sha256','public_record_source_digest']:assert re.fullmatch('[0-9a-f]{64}',proof[key]),key
  assert proof['source_manifest_sha256']==p['source_manifest_sha256'] and proof['plan_sha256']==m['plan_sha256'] and proof['first100_raw_records_digest']==m['selected_records_prefix_sha256']
  for i,item in enumerate(expected):
   tt,cc,ff,uu=t[mid,item],c[mid,item],f[mid,item],u[mid,item];q=qs[item]
   for key in ['model_id','item_id','sequence','family_id','input_sha256','payload_sha256','source_record_sha256','canonical_record_sha256','raw_response_sha256']:assert tt[key]==cc[key]==ff[key]==uu[key],key
   assert tt['family_id']==q['family_id'] and tt['input_sha256']==q['native_input_sha256'] and int(tt['sequence'])==i+1
   assert tt['payload_sha256']==digest({'model':spec['alias'],**q['native_input']})
   for key in ['input_sha256','payload_sha256','source_record_sha256','canonical_record_sha256','raw_response_sha256']:assert re.fullmatch('[0-9a-f]{64}',tt[key]),key
   assert tt['http_status']=='200' and tt['status']=='ok' and base.boolean(tt['usable']) and base.boolean(ff['usable']) and not base.boolean(tt['resident_runtime_changed']) and 0<=float(tt['server_load_seconds'])<=.01
   v=float(tt['latency_ms']);assert math.isfinite(v) and v>=0;lat.append(v)
   assert cc['evidence_kind']=='local_unmetered' and all(not cc[k] for k in ['amount','currency','reported_usd','tariff_estimate_usd']) and 'not zero' in cc['qualification']
   assert uu['attempt']=='1' and uu['returned_model']==spec['alias'] and uu['output_tokens']=='0' and uu['input_images']=='0' and int(uu['input_tokens'])>0 and uu['resident_pid_server_declared']==str(sig['resident_pid']) and base.boolean(uu['model_reused_server_declared']) and float(uu['load_seconds_server_declared'])==float(tt['server_load_seconds']) and uu['context_limit_server_declared']=='4096' and uu['runtime_signature_sha256']==p['profile_signature_sha256']
   tokens.append(int(uu['input_tokens']));abstained.append(uu['abstained_server_declared']);ordered.append([item,tt['source_record_sha256']])
  assert digest(ordered)==proof['public_record_source_digest'] and sum(tokens)==m['input_tokens']==spec['inputs'] and sum(base.boolean(f[mid,i]['correct']) for i in expected)==spec['correct']
  assert sum(x=='True' for x in abstained)==m['abstained_true_count']==spec['abstained'] and sum(x=='' for x in abstained)==m['abstained_missing_count']==spec['missing_abstained'] and sum(x=='False' for x in abstained)==m['abstained_false_count']
  base.close(m['sample_accuracy'],spec['correct']/100)
  for key,value in [('mean_ms',statistics.mean(lat)),('median_ms',statistics.median(lat)),('p95_ms',base.q95(lat))]:base.close(m[key],value)
  base.close(m['wilson95_upper'],wilson_upper(spec['correct'],100));assert m['wilson95_upper']<.45 and 'sequential screening heuristic' in m['stop_reason']
 page,md=(dest/'report.html').read_text(),(dest/'README_V5.md').read_text();section=re.search(r'<section id="asus-native-screens">.*?</section>',page,re.S).group()
 assert page.index(section)<page.index('<section id="below-cutoff">') and re.findall(r'data-asus-screen="([^"]+)"',section)==list(SPECS)
 for phrase in ['19/100','22/100','27/100','not 1,456-question scores','not a formal repeated-look guarantee','unmetered, not zero','original BF16 runtime was not measured','server','GET /props','scored normally']:
  assert phrase.lower() in section.lower() and phrase.lower() in md.lower(),phrase
 # Removing only the new module and nav link must recover the exact full-bank parent report.
 stripped=page.replace(section,'').replace('<a href="#asus-native-screens">ASUS native screens</a>','');stripped=re.sub(r'/\*ASUS_SCREEN_START\*/.*?/\*ASUS_SCREEN_END\*/','',stripped,flags=re.S);assert stripped==(prior/'report.html').read_text()
 assert re.findall(r'<article class="mobile-card" data-overall-model="([^"]+)"',page)==old['ranked_model_ids'] and not set(SPECS)&set(old['models'])
 assert re.findall(r'data-asus-screen-card="([^"]+)"',section)==list(SPECS) and 'class="mobile-card"' not in section and 'data-overall-model=' not in section
 for mid,m in models.items():
  row=re.search(r'<tr data-asus-screen="'+mid+r'">(.*?)</tr>',section,re.S).group(1);card=re.search(r'<article class="asus-screen-card" data-asus-screen-card="'+mid+r'">(.*?)</article>',section,re.S).group(1)
  for text in [row,card]:
   assert re.findall(r'data-speed-band="([^"]+)"',text)==[str(base.band(m[k],[250,500,1000])) for k in ['median_ms','p95_ms']] and 'data-cost-band="unknown"' in text and '#edf0f2' in text
  if mid.startswith('qev_'):assert 'FP32 text/readout' in row and 'FP32 text/readout' in card
 assert '@media(max-width:700px){.asus-screen-table{display:none}.asus-screen-cards{display:grid;gap:14px}}' in page
 assert page.index('src="comparison_accuracy.png"')<page.index('<div class="comparison-table">')
 for target in re.findall(r'(?:href|src)="([^"]+)"',page):
  url=urlsplit(html.unescape(target))
  if not url.scheme and not url.netloc and url.path:assert (dest/unquote(url.path)).exists(),target
 base.check_markdown_links(dest)
 for q in dest.rglob('*'):
  if q.is_file() and q.suffix not in ['.png','.svg']:
   b=data(q)
   for forbidden in [b'/Users/',b'192.168.',b'"choice":',b'"expected_answer"',b'"gold_answer"']:assert forbidden not in b,q
 if mirror:
  assert {str(q.relative_to(dest)) for q in dest.rglob('*') if q.is_file()}=={str(q.relative_to(mirror)) for q in mirror.rglob('*') if q.is_file()}
  for q in dest.rglob('*'):
   if q.is_file():assert q.read_bytes()==(mirror/q.relative_to(dest)).read_bytes(),q
 print('PASS: ASUS three separate100-item screens19/22/27;300joinedrecords;no full scores/classification/ranks;all42full results,61152mainledgers,categories,graphs,costs and historicalfiles byte-identical;profile/counters/abstention/cost/pooledtiming/privacy/mirror verified.')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('release',type=Path);p.add_argument('prior',type=Path);p.add_argument('--mirror',type=Path);a=p.parse_args();validate(a.release.resolve(),a.prior.resolve(),a.mirror.resolve() if a.mirror else None)
