"""Offline validation of four native hosted additions to the frozen v5 bank."""
import argparse,collections,csv,gzip,hashlib,html,io,json,math,re,statistics,struct
from decimal import Decimal
from pathlib import Path
from urllib.parse import unquote,urlsplit
import validate_system1_v5_provisional_2026_11_09 as base
import validate_system1_v5_gemini_decision1_2026_11_13 as gemini

# The public expected identities and totals bind this dated release, not future aliases.
SPECS={
 'pplx_decider13_native_20261112':('pplx-decider-v1.3','Perplexity direct',984,1,'0.01534610','0.02','0.00000194',767305),
 'pplx_decider_flash13_native_20261112':('pplx-decider-flash-v1.3','Perplexity direct',667,1,'0.00767305','0.01','0.00000097',767305),
 'heygen_decision1_openrouter_20261112':('heygen/heygen-decision-1-20261112','HeyGen',937,0,'0.16275784',None,'0.00001666',1162556),
 'heygen_decision1_turbo_openrouter_20261112':('heygen/heygen-decision-1-turbo-20261112','HeyGen',959,0,'0.13255038',None,'0.00001071',1472782),
}
read=lambda p:json.loads(p.read_text())
def ordinal(n):return str(n)+('th' if 10<=n%100<=20 else {1:'st',2:'nd',3:'rd'}.get(n%10,'th'))
def data(p):return gzip.decompress(p.read_bytes()) if p.name.endswith('.gz') else p.read_bytes()
def rows(p):return list(csv.DictReader(io.StringIO(data(p).decode())))
def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,ensure_ascii=False,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def validate(dest,prior,mirror=None):
 repo=Path(__file__).resolve().parents[1];gemini.validate(prior,repo/'results/releases/system1_v5_d3_flash_2026-11-11')
 manifest=base.check_manifest(dest);assert manifest['frozen_gemini_v5_manifest_sha256']==base.sha(prior/'manifest.json')
 for n,h in manifest['source_files_sha256'].items():assert base.sha(repo/n)==h,n
 old,s=read(prior/'statistics.json'),read(dest/'statistics.json');models=s['models'];costs=read(dest/'cost_statistics.json')['models'];oldcost=read(prior/'cost_statistics.json')['models']
 assert len(old['models'])==38 and len(models)==42 and set(models)==set(old['models'])|set(SPECS)
 assert set(costs)==set(models) and all(models[k]==v and costs[k]==oldcost[k] for k,v in old['models'].items())
 assert s['questions']==1456 and s['categories']==43 and s['minimum_overall_accuracy']==.45 and s['inclusion_threshold']==old['inclusion_threshold']
 assert s['inclusion_threshold']['minimum_correct']==656 and s['superseded_model_ids']==['drex_max','pplx_decider12']
 assert manifest['version']=='v5-provisional-hosted-refresh' and manifest['measured_models']==42 and manifest['main_models']==34
 for k in ['questions','categories','minimum_overall_accuracy','inclusion_threshold','superseded_model_ids']:assert manifest[k]==s[k],k
 assert manifest['replacement_decision']==read(dest/'drex_comparison.json')['replacement_decision']
 replacement=read(dest/'pplx_version_comparison.json');assert manifest['pplx_replacement_decision']==replacement['replacement_decision']=='supersede_old_active_configuration'
 assert replacement['old_model_id']=='pplx_decider12' and replacement['new_model_id']=='pplx_decider13_native_20261112' and replacement['correct_difference']==35
 base.close(replacement['new_median_to_old_ratio'],models[replacement['new_model_id']]['median_ms']/models['pplx_decider12']['median_ms'])
 ranked=sorted((k for k,v in models.items() if v['correct']*100>=45*1456 and k not in s['superseded_model_ids']),key=lambda k:(-models[k]['correct'],k))
 assert s['ranked_model_ids']==ranked and len(ranked)==34 and s['below_cutoff']==old['below_cutoff'] and len(s['below_cutoff'])==6
 assert [k for k in ranked if k not in SPECS]==[k for k in old['ranked_model_ids'] if k!='pplx_decider12']
 assert set(models)==set(ranked)|set(s['below_cutoff'])|set(s['superseded_model_ids'])
 assert not set(s['superseded_model_ids'])&(set(ranked)|set(s['below_cutoff']))
 assert (dest/'parent_gemini_audit_receipt.json').read_bytes()==(prior/'audit_receipt.json').read_bytes()
 receipt=read(dest/'audit_receipt.json');assert receipt['base_models_retained']==38 and receipt['models_added']==list(SPECS) and receipt['no_scored_retries'] and receipt['readiness_excluded']
 assert receipt['source_manifest_sha256']==base.sha(prior/'manifest.json')
 for k in ['individual_timing_records','individual_cost_records','individual_correctness_records']:assert receipt[k]==61152
 for n,h in receipt['unchanged_files_sha256'].items():assert base.sha(dest/n)==h==base.sha(prior/n),n
 for n,h in manifest['unchanged_files_sha256'].items():assert base.sha(dest/n)==h,n
 qslist=base.jsonlines(dest/'questions_1456.jsonl');qs={q['id']:q for q in qslist};families=collections.Counter(q['family_id'] for q in qslist)
 assert len(qslist)==len(qs)==1456 and len(families)==43 and families['F32']==20 and families['F33']==200
 tables={}
 for n in ['timing_evidence.csv.gz','cost_evidence.csv.gz','correctness_evidence.csv.gz','all_category_scores.csv']:
  before,after=data(prior/n),data(dest/n);assert after.startswith(before),n
  rr=rows(dest/n);fields=['model_id','family_id'] if n=='all_category_scores.csv' else ['model_id','item_id'];per=43 if n=='all_category_scores.csv' else 1456;idx={tuple(x[k] for k in fields):x for x in rr}
  assert len(rr)==len(idx)==42*per and set(rr[0])==set(rows(prior/n)[0])
  for mid in models:assert {k[1] for k in idx if k[0]==mid}==(set(families) if per==43 else set(qs))
  proof=receipt['csv_append_proofs'][n];assert proof['original_rows']==38*per and proof['appended_rows']==4*per and proof['old_csv_bytes_exact_prefix'] and proof['original_uncompressed_sha256']==hashlib.sha256(before).hexdigest();tables[n]=idx
 timing,cost,flags,cats=[tables[n] for n in ['timing_evidence.csv.gz','cost_evidence.csv.gz','correctness_evidence.csv.gz','all_category_scores.csv']]
 audits=read(dest/'hosted_refresh_model_audits.json');assert set(audits)==set(SPECS)
 usage=rows(dest/'hosted_refresh_usage_evidence.csv.gz');assert len(usage)==len({(x['model_id'],x['item_id']) for x in usage})==5824
 for mid,(snapshot,provider,correct,counter,amount,tariff,readiness,inputtotal) in SPECS.items():
  native=tariff is not None;m=models[mid];audit=audits[mid];c=costs[mid];lat=[];charges=[];estimates=[]
  assert m['role']=='Hosted native' and m['n']==m['valid']==audit['n']==audit['valid']==1456 and m['correct']==audit['correct']==correct
  assert audit['complete'] and audit['configuration_metadata_stable'] and audit['configuration_checks']==17 and audit['declared_snapshot']==snapshot and audit['provider']==provider and 'unknown' in audit['precision']
  assert m['zero_generation_attested'] is False and audit['zero_generation_independently_attested'] is False and m['no_generated_reasoning_text_observed']
  assert m['raw_output_tokens']==audit['raw_output_tokens']==counter*1456 and m['nonzero_output_counter_responses']==audit['nonzero_output_counter_responses']==counter*1456 and m['raw_usage_unknown_count']==0
  assert audit['counter_policy']['zero_required']==(not native) and audit['preview']==('turbo' in mid)
  for item,q in qs.items():
   t,cc,f=timing[mid,item],cost[mid,item],flags[mid,item]
   assert t['family_id']==cc['family_id']==f['family_id']==q['family_id'] and t['input_sha256']==cc['input_sha256']==q['native_input_sha256']
   assert t['source_record_sha256']==cc['source_record_sha256'] and re.fullmatch('[0-9a-f]{64}',t['source_record_sha256'])
   assert t['status']==cc['status']=='ok' and base.boolean(f['usable']) and t['output_counter']==str(counter)
   assert t['collection_date_toronto']==cc['collection_date_toronto']=='2026-11-13'
   assert cc['evidence_kind']==('tariff_estimate' if native else 'reported')
   v=float(t['latency_ms']);assert math.isfinite(v) and v>=0;lat.append(v)
   if native:
    assert not cc['reported_usd'];v=Decimal(cc['tariff_estimate_usd']);assert v.is_finite() and v>=0;estimates.append(v)
   else:
    assert not cc['tariff_estimate_usd'];v=Decimal(cc['reported_usd']);assert v.is_finite() and v>=0;charges.append(v)
  assert sum(base.boolean(flags[mid,i]['correct']) for i in qs)==correct
  for k,v in [('accuracy',correct/1456),('coverage',1),('answer_accuracy_among_usable',correct/1456),('accuracy_upper_if_all_unusable_correct',correct/1456)]:base.close(m[k],v)
  for k,v in [('mean_ms',statistics.mean(lat)),('median_ms',statistics.median(lat)),('p95_ms',base.q95(lat))]:base.close(m[k],v);base.close(audit[k],v)
  for fid,n in families.items():
   ids=[i for i,q in qs.items() if q['family_id']==fid];cc=cats[mid,fid];assert int(cc['n'])==n and int(cc['correct'])==sum(base.boolean(flags[mid,i]['correct']) for i in ids);base.close(cc['accuracy'],int(cc['correct'])/n);vv=[float(timing[mid,i]['latency_ms']) for i in ids]
   for k,v in [('mean_ms',statistics.mean(vv)),('median_ms',statistics.median(vv)),('p95_ms',base.q95(vv))]:base.close(cc[k],v)
  base.close(m['macro_category_accuracy'],statistics.mean(float(cats[mid,f]['accuracy']) for f in families))
  total=sum(estimates if native else charges);assert total==Decimal(amount)==Decimal(c['known_subtotal_usd']) and Decimal(c['known_usd_per_1000'])==total/Decimal(1456)*1000
  assert c['n']==1456 and all(c[k]==0 for k in ['free_access_tariff_count','unknown_count','local_unmeasured_count'])
  assert c['reported_count']==audit['reported_charge_count']==(0 if native else 1456) and c['tariff_estimate_count']==(1456 if native else 0) and audit['unknown_actual_charge_count']==(1456 if native else 0)
  if native:
   assert c['reported_subtotal_usd'] is None and audit['reported_cost_usd'] is None and Decimal(c['estimate_only_subtotal_usd'])==Decimal(audit['tariff_estimate_usd'])==total
   assert c['actual_charge_unknown_count']==1456 and c['actual_charge_telemetry']=='unreported' and c['captured_input_tariff_usd_per_million']==tariff
   assert Decimal(audit['readiness_tariff_estimate_excluded_usd'])==Decimal(readiness) and audit['readiness_reported_cost_excluded_usd'] is None
  else:
   assert c['estimate_only_subtotal_usd'] is None and Decimal(c['reported_subtotal_usd'])==Decimal(audit['reported_cost_usd'])==total and Decimal(audit['readiness_reported_cost_excluded_usd'])==Decimal(readiness)
  u=sorted((x for x in usage if x['model_id']==mid),key=lambda x:int(x['sequence']));assert len(u)==1456 and {x['item_id'] for x in u}==set(qs) and [int(x['sequence']) for x in u]==list(range(1,1457))
  for x in u:
   item=x['item_id'];assert x['attempt']=='1' and x['http_status']=='200' and x['output_tokens']==str(counter) and x['returned_model']==snapshot and x['provider']==provider and int(x['input_tokens'])>0
   assert x['family_id']==qs[item]['family_id'] and x['completed_at_utc']==timing[mid,item]['collected_at_utc'] and x['input_sha256']==qs[item]['native_input_sha256'] and x['source_record_sha256']==timing[mid,item]['source_record_sha256'] and re.fullmatch('[0-9a-f]{64}',x['canonical_record_sha256'])
   assert x['reported_usd']==cost[mid,item]['reported_usd'] and x['tariff_estimate_usd']==cost[mid,item]['tariff_estimate_usd']
   if native:assert Decimal(x['tariff_estimate_usd'])==Decimal(x['input_tokens'])*Decimal(tariff)/Decimal(1000000)
  assert sum(int(x['input_tokens']) for x in u)==audit['input_tokens']==m['input_tokens']==inputtotal
  assert digest([[x['item_id'],x['source_record_sha256']] for x in u])==audit['source_record_digest']==receipt['new_sources'][mid]['source_record_digest']
  assert receipt['new_sources'][mid]['independent_final_review_verdict']=='APPROVE' and re.fullmatch('[0-9a-f]{64}',receipt['new_sources'][mid]['independent_final_review_sha256'])
  assert receipt['new_sources'][mid]['source_manifest_sha256']==audit['manifest_sha256'] and receipt['new_sources'][mid]['plan_sha256']==audit['plan_sha256'] and receipt['new_sources'][mid]['first100_preserved']
 analysis=read(dest/'hosted_refresh_analysis.json');assert set(analysis)==set(SPECS)
 for mid in SPECS:
  a=analysis[mid];assert a['rank_among_release_active']==ranked.index(mid)+1 and a['active_cohort_n']==34 and a['correct']==models[mid]['correct'] and a['n']==1456
  assert len(a['categories'])==43 and {x['family_id'] for x in a['categories']}==set(families)
  for x in a['categories']:
   cc=cats[mid,x['family_id']];assert x['n']==int(cc['n']) and x['correct']==int(cc['correct'])
   for k in ['accuracy','mean_ms','median_ms','p95_ms']:base.close(x[k],float(cc[k]))
  assert set(a['matched_comparisons'])==set(models)-{mid}
  for other,pair in a['matched_comparisons'].items():
   newgood=[base.boolean(flags[mid,i]['correct']) for i in qs];oldgood=[base.boolean(flags[other,i]['correct']) for i in qs];common=[i for i in qs if base.boolean(flags[other,i]['usable'])]
   assert pair['n']==1456 and pair['new_correct']==models[mid]['correct'] and pair['reference_correct']==models[other]['correct'] and pair['new_minus_reference_correct']==models[mid]['correct']-models[other]['correct']
   assert pair['both_correct']==sum(a and b for a,b in zip(newgood,oldgood)) and pair['new_only_correct']==sum(a and not b for a,b in zip(newgood,oldgood)) and pair['reference_only_correct']==sum(b and not a for a,b in zip(newgood,oldgood)) and pair['neither_correct']==sum(not a and not b for a,b in zip(newgood,oldgood))
   assert pair['common_usable_n']==len(common) and pair['new_correct_common_usable']==sum(base.boolean(flags[mid,i]['correct']) for i in common) and pair['reference_correct_common_usable']==sum(base.boolean(flags[other,i]['correct']) for i in common)
 assert replacement['paired_outcomes']==analysis[replacement['new_model_id']]['matched_comparisons']['pplx_decider12']
 cr=rows(dest/'hosted_refresh_category_comparison.csv');assert len(cr)==len({(x['model_id'],x['reference_model'],x['family_id']) for x in cr})==4*41*43
 for x in cr:
  mid,other,fid=x['model_id'],x['reference_model'],x['family_id'];assert mid in SPECS and other in models and mid!=other and fid in families and int(x['n'])==families[fid] and int(x['new_correct'])==int(cats[mid,fid]['correct']) and int(x['reference_correct'])==int(cats[other,fid]['correct']) and int(x['new_minus_reference_correct'])==int(x['new_correct'])-int(x['reference_correct'])
 page,md=(dest/'report.html').read_text(),(dest/'README_V5.md').read_text();assert page.index('src="comparison_accuracy.png"')<page.index('<div class="comparison-table">')
 section=re.search(r'<section id="hosted-refresh">(.*?)</section>',page,re.S).group(1)
 for phrase in ['984/1,456','667/1,456','937/1,456','959/1,456','0.01534610','0.00767305','0.16275784','0.13255038','actual API monetary charges are unreported','one raw output-accounting token','preview','not an ordinary generative LLM reference','17 matching','not sustained throughput']:
  assert phrase in section and phrase in md,phrase
 for text in ['rose','two-computer','Ryzen 7','Intel Core i7','6 GB','user-reported','unmetered','45%','original dated cohort']:assert text in page and text in md,text
 for mid,phrase in [('d3_flash_9b_q4km_llamacpp_ctx4096_lan','ranking {rank} among 34'),('singvl_s1_4b_q4km_llamacpp_ctx4096_lan','ranks {rank} among the 34'),('gemini_decision1_openrouter_20261111','ranking {rank} among 34')]:assert phrase.format(rank=ordinal(ranked.index(mid)+1)) in page
 desktop=re.search(r'<div class="comparison-table">.*?</table>',page,re.S).group();assert re.findall(r'data-overall-model="([^"]+)"',desktop)==ranked and re.findall(r'<article class="mobile-card" data-overall-model="([^"]+)"',page)==ranked
 for mid in ranked:
  row=re.search(r'<tr data-overall-model="'+re.escape(mid)+r'">(.*?)</tr>',desktop,re.S).group(1);assert f'{models[mid]["accuracy"]:.2%}' in row and re.findall(r'data-speed-band="([^"]+)"',row)==[str(base.band(models[mid][k],[250,500,1000])) for k in ['median_ms','p95_ms']];band=base.cost_band(costs[mid]);assert re.findall(r'data-cost-band="([^"]+)"',row)==['unknown' if band is None else str(band)]*2 and html.escape(base.cost_label(costs[mid])) in row
  if mid.startswith('pplx_decider') and mid in SPECS:assert 'actual API charges unreported' in row
 for kind in ['accuracy','latency','cost']:
  b=(dest/f'comparison_{kind}.png').read_bytes();assert b[:8]==b'\x89PNG\r\n\x1a\n';w,h=struct.unpack('>II',b[16:24]);assert w>=1300 and h>=1600
 assert len(list(dest.glob('categories_*.svg')))==8
 for svg in [dest/'overview.svg']+list(dest.glob('comparison_*.svg'))+list(dest.glob('categories_*.svg')):
  text=svg.read_text();assert '#b2364b' in text and 'rose two-computer local' in text and all(mid in text for mid in SPECS),svg
 for target in re.findall(r'(?:href|src)="([^"]+)"',page):
  u=urlsplit(html.unescape(target))
  if not u.scheme and not u.netloc and u.path:assert (dest/unquote(u.path)).exists(),target
 base.check_markdown_links(dest)
 for p in dest.rglob('*'):
  if p.is_file() and p.suffix not in ['.png','.svg']:
   b=data(p)
   for forbidden in [b'/Users/',b'"choice":',b'"expected_answer"',b'"gold_answer"']:assert forbidden not in b,p
 if mirror:
  assert {str(p.relative_to(mirror)) for p in mirror.rglob('*') if p.is_file()}=={str(p.relative_to(dest)) for p in dest.rglob('*') if p.is_file()}
  for p in dest.rglob('*'):
   if p.is_file():assert p.read_bytes()==(mirror/p.relative_to(dest)).read_bytes(),p
  base.check_markdown_links(mirror)
 print('PASS: four native hosted additions;42complete/34active/6below/2superseded;61152records;all38priorobjects/prefixes;actual unreported charges separate from estimates;usage/counters/pooledtimings/categories/ranks/privacy/mirror verified.')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('release',type=Path);p.add_argument('prior',type=Path);p.add_argument('--mirror',type=Path);a=p.parse_args();validate(a.release.resolve(),a.prior.resolve(),a.mirror.resolve() if a.mirror else None)
