"""Offline audit of the dated Liquid d1.2 native v5 successor."""
import argparse, collections, csv, gzip, hashlib, html, io, json, math, re, statistics, struct
from decimal import Decimal
from pathlib import Path
from urllib.parse import unquote, urlsplit
import validate_system1_v5_provisional_2026_11_09 as base
import validate_system1_v5_nimble_subq_2026_11_15 as parent_validator
SPECS={
 'liquid12_ultra':dict(alias='liquid/d1.2-ultra',snapshot='liquid/d1.2-ultra-20261116',correct=956,amount='0.028928760',readiness='0.0000021',tariff='0.000000042',old='liquid_ultra',rank=10),
 'liquid12':dict(alias='liquid/d1.2',snapshot='liquid/d1.2-20261116',correct=805,amount='0.01377560',readiness='0.000001',tariff='0.00000002',old='liquid11_decision',rank=22),
}
ROUTING={'only':['liquid'],'allow_fallbacks':False,'require_parameters':True}
REVIEW='7aaa749f565fa052d57f5add2458c24c0142679727721d0e32972570c940dc57'
BUNDLE='d1ec944e58cc678dbdc476589ace361d165bfd1ba432e06d834af23b4fb677ea'
MANIFEST='a12c8b6e80d745c0e36a6cea5b0dcdcd3e05cddf7c839f26c123e9666be355cf'
PREFIX_PROOFS={
 'liquid12_ultra':('30b1125453a3b6d2607bceda27958905fd0e0bfe1e501a465c7e17ae3af32af5','2afaa775f74176644576613c549cad9736c33c077c87c6e12d44b441698effc9','913e08a5ff5e5a357c7a91e7ea11613f712ec9ed4495fad5bdcbd9c78d27073e'),
 'liquid12':('f41c0b7002ad7c62f2ef3f366cd9b1f0cee4c25bc8c75cdce09d9df720731517','33e31ad6e8690652e579110d34c41d0822005bc2758a207c53c5007a0b58074c','4fa937478202e427cd1ad5c9be711f9f775cde0232487b8631d12dc50d894360'),
}
read=lambda p:json.loads(p.read_text())
def data(p):return gzip.decompress(p.read_bytes()) if p.name.endswith('.gz') else p.read_bytes()
def rows(p):return list(csv.DictReader(io.StringIO(data(p).decode())))
def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True,ensure_ascii=False,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def validate(dest,prior,mirror=None,validate_parent=True):
 repo=Path(__file__).resolve().parents[1]
 if validate_parent:parent_validator.validate(prior,repo/'results/releases/system1_v5_asus_native_2026-11-13')
 manifest=base.check_manifest(dest)
 assert manifest['version']=='v5-provisional-liquid12' and manifest['frozen_nimble_subq_v5_manifest_sha256']==base.sha(prior/'manifest.json')
 for n,h in manifest['source_files_sha256'].items():assert base.sha(repo/n)==h,n
 old=read(prior/'statistics.json');s=read(dest/'statistics.json');models=s['models'];costs=read(dest/'cost_statistics.json')['models'];oldcost=read(prior/'cost_statistics.json')['models']
 assert len(old['models'])==44 and len(models)==46 and set(models)==set(old['models'])|set(SPECS) and set(costs)==set(models)
 assert all(models[k]==v and costs[k]==oldcost[k] for k,v in old['models'].items())
 assert s['questions']==1456 and s['categories']==43 and s['minimum_overall_accuracy']==.45 and s['inclusion_threshold']==old['inclusion_threshold'] and s['inclusion_threshold']['minimum_correct']==656
 replaced=['liquid_d1','liquid11_decision','liquid_ultra']
 assert s['superseded_model_ids']==old['superseded_model_ids']+replaced and len(s['superseded_model_ids'])==7 and s['below_cutoff']==old['below_cutoff'] and len(s['below_cutoff'])==6
 ranked=sorted((k for k,v in models.items() if v['correct']*100>=45*1456 and k not in s['superseded_model_ids']),key=lambda k:(-models[k]['correct'],k))
 assert s['ranked_model_ids']==ranked and len(ranked)==33 and set(models)==set(ranked)|set(s['below_cutoff'])|set(s['superseded_model_ids'])
 assert not set(s['superseded_model_ids'])&(set(ranked)|set(s['below_cutoff']))
 assert [k for k in ranked if k not in SPECS]==[k for k in old['ranked_model_ids'] if k not in replaced]
 assert {'pplx_decider13_native_20261112','pplx_decider_flash13_native_20261112'}<=set(ranked)
 for k in ['questions','categories','minimum_overall_accuracy','inclusion_threshold','superseded_model_ids']:assert manifest[k]==s[k],k
 assert manifest['measured_models']==46 and manifest['main_models']==33 and manifest['partial_screen_models']==3 and manifest['partial_records_per_ledger']==300
 for n in ['audit_receipt.json','manifest.json']:assert (dest/('parent_nimble_subq_'+n)).read_bytes()==(prior/n).read_bytes()
 receipt=read(dest/'audit_receipt.json');assert receipt['base_models_retained']==44 and receipt['models_added']==list(SPECS) and receipt['no_scored_retries'] and receipt['readiness_excluded'] and receipt['source_manifest_sha256']==base.sha(prior/'manifest.json')
 for k in ['individual_timing_records','individual_cost_records','individual_correctness_records']:assert receipt[k]==66976
 assert manifest['unchanged_files_sha256']==receipt['unchanged_files_sha256']
 for n,h in receipt['unchanged_files_sha256'].items():assert base.sha(dest/n)==h==base.sha(prior/n),n
 qs={q['id']:q for q in base.jsonlines(dest/'questions_1456.jsonl')};families=collections.Counter(q['family_id'] for q in qs.values())
 assert len(qs)==1456 and len(families)==43 and families['F32']==20 and families['F33']==200
 tables={}
 for n in ['timing_evidence.csv.gz','cost_evidence.csv.gz','correctness_evidence.csv.gz','all_category_scores.csv']:
  before,after=data(prior/n),data(dest/n);assert after.startswith(before),n
  rr=rows(dest/n);per=43 if n=='all_category_scores.csv' else 1456;second='family_id' if per==43 else 'item_id';idx={(x['model_id'],x[second]):x for x in rr}
  assert len(rr)==len(idx)==46*per and set(rr[0])==set(rows(prior/n)[0])
  for mid in models:assert {k[1] for k in idx if k[0]==mid}==(set(families) if per==43 else set(qs))
  p=receipt['csv_append_proofs'][n];assert p['original_rows']==44*per and p['appended_rows']==2*per and p['old_csv_bytes_exact_prefix'] and p['original_uncompressed_sha256']==hashlib.sha256(before).hexdigest();tables[n]=idx
 timing,cost,flags,cats=[tables[n] for n in ['timing_evidence.csv.gz','cost_evidence.csv.gz','correctness_evidence.csv.gz','all_category_scores.csv']]
 audits=read(dest/'liquid12_model_audits.json');usage=rows(dest/'liquid12_usage_evidence.csv.gz');assert set(audits)==set(SPECS) and len(usage)==len({(x['model_id'],x['item_id']) for x in usage})==2912
 for mid,spec in SPECS.items():
  m=models[mid];a=audits[mid];c=costs[mid];lat=[];reported=[]
  assert m['role']=='Hosted native' and m['n']==m['valid']==a['n']==a['usable']==1456 and m['correct']==a['correct']==spec['correct']
  assert a['complete'] and a['full_coverage'] and a['postflight_and_source_verified_completion'] and a['configuration_metadata_stable'] and a['configuration_checks']==18 and len(a['configuration_check_file_hashes'])==18 and all(re.fullmatch('[0-9a-f]{64}',x) for x in a['configuration_check_file_hashes'])
  assert a['first_primaries_only'] and a['scored_retries']==0 and a['precision']=='unknown hosted precision' and a['requested_model']==spec['alias'] and a['declared_snapshot']==spec['snapshot'] and a['provider']=='Liquid' and a['routing']==ROUTING and a['route']=='https://openrouter.ai/api/alpha/decisions'
  assert a['captured_pricing']=={'prompt':spec['tariff'],'completion':'0','discount':0}
  assert m['zero_generation_attested'] is False and m['no_generated_reasoning_text_observed'] and m['raw_output_tokens']==m['nonzero_output_counter_responses']==m['raw_usage_unknown_count']==0
  diag=a['all_primary_usage_diagnostics'];assert diag['input_tokens_all_primaries']==688780 and diag['output_tokens_all_primaries']==diag['nonzero_output_counter_count']==0
  for k in ['missing_input_usage_count','missing_output_usage_count','invalid_or_missing_probability_distribution_count','invalid_present_probability_distribution_count','argmax_disagreement_count']:assert diag[k]==0,k
  for item,q in qs.items():
   t,cc,f=timing[mid,item],cost[mid,item],flags[mid,item]
   assert t['family_id']==cc['family_id']==f['family_id']==q['family_id'] and t['input_sha256']==cc['input_sha256']==q['native_input_sha256']
   assert t['source_record_sha256']==cc['source_record_sha256'] and re.fullmatch('[0-9a-f]{64}',t['source_record_sha256']) and t['status']==cc['status']=='ok' and base.boolean(f['usable']) and t['output_counter']=='0'
   assert t['collection_date_toronto']==cc['collection_date_toronto']=='2026-11-17' and cc['evidence_kind']=='reported' and not cc['tariff_estimate_usd']
   v=float(t['latency_ms']);assert math.isfinite(v) and v>=0;lat.append(v);v=Decimal(cc['reported_usd']);assert v.is_finite() and v>=0;reported.append(v)
  assert sum(base.boolean(flags[mid,i]['correct']) for i in qs)==spec['correct']
  for k,v in [('accuracy',spec['correct']/1456),('coverage',1),('answer_accuracy_among_usable',spec['correct']/1456),('accuracy_upper_if_all_unusable_correct',spec['correct']/1456)]:base.close(m[k],v)
  for k,v in [('mean_ms',statistics.mean(lat)),('median_ms',statistics.median(lat)),('p95_ms',base.q95(lat))]:base.close(m[k],v);base.close(a[k],v)
  for fid,n in families.items():
   ids=[i for i,q in qs.items() if q['family_id']==fid];cc=cats[mid,fid]
   assert int(cc['n'])==n and int(cc['correct'])==sum(base.boolean(flags[mid,i]['correct']) for i in ids);base.close(cc['accuracy'],int(cc['correct'])/n);vv=[float(timing[mid,i]['latency_ms']) for i in ids]
   for k,v in [('mean_ms',statistics.mean(vv)),('median_ms',statistics.median(vv)),('p95_ms',base.q95(vv))]:base.close(cc[k],v)
  base.close(m['macro_category_accuracy'],statistics.mean(float(cats[mid,f]['accuracy']) for f in families))
  total=sum(reported);assert total==Decimal(spec['amount'])==Decimal(c['known_subtotal_usd'])==Decimal(c['reported_subtotal_usd'])==Decimal(a['reported_usd_subtotal'])
  assert Decimal(c['known_usd_per_1000'])==total/Decimal(1456)*1000 and c['n']==1456 and c['reported_count']==1456 and c['actual_charge_unknown_count']==0 and c['actual_charge_telemetry']=='reported' and c['estimate_only_subtotal_usd'] is None
  assert all(c[k]==0 for k in ['tariff_estimate_count','free_access_tariff_count','unknown_count','local_unmeasured_count']) and Decimal(a['readiness_reported_excluded_usd'])==Decimal(spec['readiness']) and a['reported_charge_count']==1456 and a['unknown_actual_charge_count']==0 and Decimal(a['captured_tariff_estimate_usd'])==0
  u=sorted((x for x in usage if x['model_id']==mid),key=lambda x:int(x['sequence']));assert len(u)==1456 and {x['item_id'] for x in u}==set(qs) and [int(x['sequence']) for x in u]==list(range(1,1457))
  for x in u:
   item=x['item_id'];assert x['attempt']=='1' and x['http_status']=='200' and x['status']=='ok' and x['output_tokens']=='0' and x['requested_model']==spec['alias'] and x['returned_model']==spec['snapshot'] and x['provider']=='Liquid' and x['route']==a['route'] and json.loads(x['routing_json'])==ROUTING
   assert x['family_id']==qs[item]['family_id'] and x['input_sha256']==qs[item]['native_input_sha256'] and x['completed_at_utc']==timing[mid,item]['collected_at_utc'] and x['source_record_sha256']==timing[mid,item]['source_record_sha256']
   for k in ['canonical_record_sha256','raw_response_sha256','payload_sha256']:assert re.fullmatch('[0-9a-f]{64}',x[k])
   assert x['payload_sha256']==digest({'model':spec['alias'],'provider':ROUTING,**qs[item]['native_input']})
   raw=json.loads(x['raw_usage_json']);assert raw['input_tokens']==int(x['input_tokens']) and raw['output_tokens']==0 and raw['is_byok'] is False
   assert Decimal(str(raw['cost']))==Decimal(x['reported_usd'])==Decimal(cost[mid,item]['reported_usd']) and not x['tariff_estimate_usd']
  assert sum(int(x['input_tokens']) for x in u)==m['input_tokens']==688780
  proof=receipt['new_sources'][mid];assert digest([[x['item_id'],x['source_record_sha256']] for x in u])==a['source_record_digest']==proof['source_record_digest'] and proof['first100_preserved'] and proof['independent_final_review_verdict']=='APPROVE'
  assert proof['independent_final_review_sha256']==REVIEW and proof['source_bundle_sha256']==BUNDLE and proof['source_manifest_sha256']==a['source_manifest_sha256']==MANIFEST
  for k in ['plan_sha256','first100_receipt_sha256','source_audit_sha256']:assert re.fullmatch('[0-9a-f]{64}',proof[k])
  assert ranked.index(mid)+1==spec['rank']
  proof=receipt['new_sources'][mid];seal,prefix,audit=PREFIX_PROOFS[mid]
  assert proof['source_manifest_sha256']==a['source_manifest_sha256']==MANIFEST and proof['source_bundle_sha256']==BUNDLE
  assert proof['independent_final_review_verdict']=='APPROVE' and proof['independent_final_review_sha256']==REVIEW and proof['first100_preserved'] and proof['first100_receipt_sha256']==seal and proof['source_audit_sha256']==audit
  assert digest([[x['item_id'],x['source_record_sha256']] for x in u])==a['source_record_digest']==proof['source_record_digest']
  assert digest([[x['item_id'],x['source_record_sha256']] for x in u[:100]])==prefix
  assert proof['plan_sha256']==a['plan_sha256'] and re.fullmatch('[0-9a-f]{64}',proof['plan_sha256'])
  pairs=read(dest/(mid+'_paired_comparison_all44.json'));assert set(pairs)==set(old['models'])
  for other,p in pairs.items():
   assert p['reference_model_id']==other and p['reference_cost_summary']==costs[other] and p['reference_label']==models[other]['label'] and p['active_reference']==(other in old['ranked_model_ids'])
   assert p['n']==1456 and p['new_usable']==1456 and p['reference_usable']==models[other]['valid']
   base.close(p['reference_median_ms'],models[other]['median_ms']);base.close(p['reference_p95_ms'],models[other]['p95_ms'])
   aa=[base.boolean(flags[mid,i]['correct']) for i in qs];bb=[base.boolean(flags[other,i]['correct']) for i in qs];common=[i for i in qs if base.boolean(flags[other,i]['usable'])]
   assert p['new_correct']==spec['correct'] and p['reference_correct']==models[other]['correct'] and p['correct_difference']==spec['correct']-models[other]['correct']
   assert p['both_correct']==sum(a and b for a,b in zip(aa,bb)) and p['new_only_correct']==sum(a and not b for a,b in zip(aa,bb)) and p['reference_only_correct']==sum(b and not a for a,b in zip(aa,bb)) and p['neither_correct']==sum(not a and not b for a,b in zip(aa,bb)) and p['common_usable_n']==len(common)
   assert p['new_correct_common_usable']==sum(base.boolean(flags[mid,i]['correct']) for i in common) and p['reference_correct_common_usable']==sum(base.boolean(flags[other,i]['correct']) for i in common)
  # Every category/reference row is a complete matched comparison, not a selected excerpt.
  comparisons=rows(dest/(mid+'_category_comparison_all44.csv'))
  indexed={(x['reference_model_id'],x['family_id']):x for x in comparisons}
  assert len(comparisons)==len(indexed)==44*43 and set(indexed)=={(other,fid) for other in old['models'] for fid in families}
  # The source producer takes the first frozen question label; P07/P10 retain historical aliases.
  bank_labels={fid:next(q['family'] for q in qs.values() if q['family_id']==fid) for fid in families}
  for (other,fid),x in indexed.items():
   ids=[i for i,q in qs.items() if q['family_id']==fid]
   assert x['reference_label']==models[other]['label'] and x['category']==bank_labels[fid] and int(x['n'])==families[fid]
   assert int(x['new_correct'])==int(cats[mid,fid]['correct']) and int(x['reference_correct'])==int(cats[other,fid]['correct']) and int(x['correct_difference'])==int(x['new_correct'])-int(x['reference_correct'])
   assert base.boolean(x['active_reference'])==(other in old['ranked_model_ids'])
   assert int(x['new_only_correct'])==sum(base.boolean(flags[mid,i]['correct']) and not base.boolean(flags[other,i]['correct']) for i in ids)
   assert int(x['reference_only_correct'])==sum(base.boolean(flags[other,i]['correct']) and not base.boolean(flags[mid,i]['correct']) for i in ids)
   assert int(x['common_usable_n'])==sum(base.boolean(flags[mid,i]['usable']) and base.boolean(flags[other,i]['usable']) for i in ids)
  analysis=read(dest/(mid+'_FINAL_ANALYSIS.json'));assert analysis['baseline']=='results/releases/system1_v5_nimble_subq_2026-11-15' and analysis['correct']==m['correct'] and analysis['usable']==1456 and analysis['comparisons_all44']==pairs and analysis['old_version_comparison']==pairs[spec['old']]
  assert analysis['status']=='public_derivative_of_historical_collection_analysis' and analysis['historical_collection_status']=='complete_private_not_published'
  assert analysis['current_release_scope']=='46 complete; 33 active; 6 below cutoff; 7 superseded; current ranks in liquid12_current_analysis.json'
  assert 'private source files' in analysis['source_hashes_scope'] and 'main_evidence_hashes' not in analysis and set(analysis['private_source_evidence_sha256'])=={'audit_summary.json','timing_evidence.csv.gz','cost_evidence.csv.gz','correctness_evidence.csv.gz','usage_evidence.csv.gz','SCREEN100_RECEIPT.json'}
  assert analysis['private_source_evidence_sha256']['SCREEN100_RECEIPT.json']==seal and analysis['private_source_evidence_sha256']['audit_summary.json']==audit
  assert 'Active graphs and publication membership are unchanged.' not in ' '.join(analysis['limits']) and analysis['public_derivative_provenance']['private_source_file_sha256'] in ['4d94cbad79b89209ed64c259da41ec0f38499a5c2280acf183044067cbf32bf9','f2e992855c08c191a7177ee79f374f22549f83998a0d2cecde553bb2e5cac637']
  strength=read(dest/(mid+'_STRENGTHS_WEAKNESSES.json'));cc=strength['all43categories'];assert len(cc)==43 and {x['family_id'] for x in cc}==set(families)
  for x in cc:assert x['n']==families[x['family_id']] and x['correct']==int(cats[mid,x['family_id']]['correct']) and x['previous_version_correct']==int(cats[spec['old'],x['family_id']]['correct'])
 current_document=read(dest/'liquid12_current_analysis.json');assert current_document['active_model_ids']==ranked and current_document['complete_configurations']==46 and current_document['active_configurations']==33
 current=current_document['interpretation'];assert set(current)==set(SPECS)
 for mid,spec in SPECS.items():
  a=current[mid];assert a['old_version_id']==spec['old'] and a['overall_accuracy_rank']==spec['rank'] and a['active_cohort_n']==33 and len(a['categories'])==43 and {x['family_id'] for x in a['categories']}==set(families)
  for x in a['categories']:
   fid=x['family_id'];good=int(cats[mid,fid]['correct']);before=int(cats[spec['old'],fid]['correct']);leader=max(int(cats[k,fid]['correct']) for k in ranked)
   assert x['n']==families[fid] and x['correct']==good and x['old_version_correct']==before and x['new_minus_old_correct']==good-before and x['current33_accuracy_rank']==1+sum(int(cats[k,fid]['correct'])>good for k in ranked) and x['leader_correct']==leader and set(x['leader_model_ids'])=={k for k in ranked if int(cats[k,fid]['correct'])==leader}
 pair=read(dest/'liquid12_pair_version_comparison.json');assert pair['n']==1456
 assert pair['scope']=='Public paired measurement derivative; current release has46complete/33active/6below/7superseded; historical collection-time ranks and flags are explicitly labelled.'
 assert 'file_sha256' not in pair and len(pair['private_source_files_sha256'])==8 and 'private source files' in pair['source_hashes_scope']
 assert pair['public_derivative_provenance']['private_source_file_sha256']=='f73ecba3406dac63f2cc90052cfda5d3aa083d1d87a07ce97f7ab08445db2fc7'
 assert pair['model_ids']==list(SPECS) and pair['categories']==43 and pair['correct']=={mid:spec['correct'] for mid,spec in SPECS.items()}
 ultra=[base.boolean(flags['liquid12_ultra',i]['correct']) for i in qs];standard=[base.boolean(flags['liquid12',i]['correct']) for i in qs]
 assert pair['both_correct']==sum(a and b for a,b in zip(ultra,standard)) and pair['ultra_only_correct']==sum(a and not b for a,b in zip(ultra,standard)) and pair['standard_only_correct']==sum(b and not a for a,b in zip(ultra,standard))
 assert pair['ultra_minus_standard_correct']==sum(ultra)-sum(standard) and pair['common_usable_n']==1456 and pair['common_usable_correct']==pair['correct']
 assert set(pair['historical_version_comparisons'])==set(SPECS)
 for mid,spec in SPECS.items():
  assert pair['historical_version_comparisons'][mid]==read(dest/(mid+'_paired_comparison_all44.json'))[spec['old']]
  for key,field in [('pooled_median_ms','median_ms'),('pooled_p95_ms','p95_ms')]:base.close(pair[key][mid],models[mid][field])
  assert Decimal(pair['reported_usd_subtotals'][mid])==Decimal(costs[mid]['reported_subtotal_usd']) and pair['unknown_actual_charge_count'][mid]==0 and pair['categories']==43 and pair['ultra_minus_standard_correct']==151 and pair['both_correct']==667 and pair['ultra_only_correct']==289 and pair['standard_only_correct']==138
 assert pair['historical_version_comparisons']=={mid:read(dest/(mid+'_paired_comparison_all44.json'))[spec['old']] for mid,spec in SPECS.items()}
 for x in pair['categories_pair']:
  fid=x['family_id'];ids=[i for i,q in qs.items() if q['family_id']==fid];assert x['n']==len(ids) and x['ultra_correct']==int(cats['liquid12_ultra',fid]['correct']) and x['standard_correct']==int(cats['liquid12',fid]['correct'])
  assert x['ultra_only_correct']==sum(base.boolean(flags['liquid12_ultra',i]['correct']) and not base.boolean(flags['liquid12',i]['correct']) for i in ids) and x['standard_only_correct']==sum(base.boolean(flags['liquid12',i]['correct']) and not base.boolean(flags['liquid12_ultra',i]['correct']) for i in ids)
 assert len(pair['categories_pair'])==43 and {x['family_id'] for x in pair['categories_pair']}==set(families)
 assert int(cats['liquid_ultra','F33']['correct'])==126 and int(cats['liquid12_ultra','F33']['correct'])==82
 page,md=(dest/'report.html').read_text(),(dest/'README_V5.md').read_text();section=re.search(r'<section id="liquid12-update">.*?</section>',page,re.S).group()
 for phrase in ['956/1,456','805/1,456','126/200','82/200','−44','1,256','58','+14','+28','0.028928760','0.01377560','0.028907928','0.01377218','two unknown','one','full-bank cost saving','Separate sessions','unknown','not sustained throughput','zero-generation','readiness','0.0000021','0.000001','all 43','269.87/983.44','224.86/391.23','AQuA','MAIQ']:
  assert phrase in section and phrase in md,phrase
 assert 'Those incomplete historical subtotals do not establish a full-bank cost saving.' in section and '<h3>Liquid d1.2-ultra · 10/33 overall</h3>' in section and '<h3>Liquid d1.2 · 22/33 overall</h3>' in section
 assert '<p class="version-alert"><strong>Ultra' in section and '126/200 to 82/200 (−44)' in section
 assert 'Historical section:' in page and 'November 15 snapshot' in md and '33-model' in md
 assert float(timing['liquid12_ultra','P200-F17-004']['latency_ms'])>8500
 assert int(cats['liquid12_ultra','F08']['correct'])==41 and max(int(cats[k,'F08']['correct']) for k in ranked)==43 and 1+sum(int(cats[k,'F08']['correct'])>41 for k in ranked)==3
 assert 'Assignment ranks 3/33 at 41/44 versus the 43/44 leader.' in section
 desktop=re.search(r'<div class="comparison-table">.*?</table>',page,re.S).group()
 assert re.findall(r'data-overall-model="([^"]+)"',desktop)==ranked and re.findall(r'<article class="mobile-card" data-overall-model="([^"]+)"',page)==ranked
 for mid in ranked:
  row=re.search(r'<tr data-overall-model="'+re.escape(mid)+r'">(.*?)</tr>',desktop,re.S).group(1)
  assert f'{models[mid]["accuracy"]:.2%}' in row and re.findall(r'data-speed-band="([^"]+)"',row)==[str(base.band(models[mid][k],[250,500,1000])) for k in ['median_ms','p95_ms']]
  band=base.cost_band(costs[mid]);assert re.findall(r'data-cost-band="([^"]+)"',row)==['unknown' if band is None else str(band)]*2 and html.escape(base.cost_label(costs[mid])) in row
 for p in prior.glob('asus_native*'):assert (dest/p.name).read_bytes()==p.read_bytes(),p.name
 inherited=re.search(r'<section id="asus-native-screens">.*?</section>',(prior/'report.html').read_text(),re.S).group();partial=re.search(r'<section id="asus-native-screens">.*?</section>',page,re.S).group()
 assert partial==inherited and page.index(partial)<page.index('<section id="below-cutoff">')
 for kind in ['accuracy','latency','cost']:
  b=(dest/f'comparison_{kind}.png').read_bytes();w,h=struct.unpack('>II',b[16:24]);assert b[:8]==b'\x89PNG\r\n\x1a\n' and w>=1300 and h>=1600
 assert len(list(dest.glob('categories_*.svg')))==8
 for svg in [dest/'overview.svg']+list(dest.glob('comparison_*.svg'))+list(dest.glob('categories_*.svg')):
  text=svg.read_text();assert '#b2364b' in text and 'rose two-computer local' in text and all(mid in text for mid in SPECS)
 for target in re.findall(r'(?:href|src)="([^"]+)"',page):
  u=urlsplit(html.unescape(target))
  if not u.scheme and not u.netloc and u.path:assert (dest/unquote(u.path)).exists(),target
 base.check_markdown_links(dest)
 for p in dest.rglob('*'):
  if p.is_file() and p.suffix not in ['.png','.svg']:
   b=data(p)
   for forbidden in [b'/Users/',b'192.168.',b'"choice":',b'"expected_answer"',b'"gold_answer"']:assert forbidden not in b,p
 if mirror:
  assert {str(p.relative_to(dest)) for p in dest.rglob('*') if p.is_file()}=={str(p.relative_to(mirror)) for p in mirror.rglob('*') if p.is_file()}
  for p in dest.rglob('*'):
   if p.is_file():assert p.read_bytes()==(mirror/p.relative_to(dest)).read_bytes(),p
 print('PASS: Liquid956/805;46complete/33active/6below/7superseded;66976records;44objects/64064prefixes;pooled timings/reported costs/aliases/categories/ranks/pairs/partials/privacy/mirror')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('release',type=Path);p.add_argument('prior',type=Path);p.add_argument('--mirror',type=Path);a=p.parse_args();validate(a.release.resolve(),a.prior.resolve(),a.mirror.resolve() if a.mirror else None)
