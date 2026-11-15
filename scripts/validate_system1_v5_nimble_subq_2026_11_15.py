"""Offline validation of the dated Nimble/SubQ native v5 version successor."""
import argparse,collections,csv,gzip,hashlib,html,io,json,math,re,statistics,struct
from decimal import Decimal
from pathlib import Path
from urllib.parse import unquote,urlsplit
import validate_system1_v5_provisional_2026_11_09 as base
import validate_system1_v5_asus_native_2026_11_13 as asus
SPECS={
 'nimble_v41_max':dict(snapshot='nimble-v4.1-max',provider='Bespoke Labs direct',correct=950,counter=2,amount='0.03103948',inputs=775987,readiness='0.00000412',old='nimble_v4_max',rank=11,host='api.bespokelabs.ai'),
 'subq_snap12':dict(snapshot='subq-snap-1.2',provider='Subquadratic direct',correct=927,counter=0,amount='0.03144932',inputs=786233,readiness='0.00000440',old='subq_snap_1_1',rank=14,host='api.subq.ai'),
}
read=lambda p:json.loads(p.read_text())
def data(p):return gzip.decompress(p.read_bytes()) if p.name.endswith('.gz') else p.read_bytes()
def rows(p):return list(csv.DictReader(io.StringIO(data(p).decode())))
def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True,ensure_ascii=False,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def validate(dest,prior,mirror=None):
 repo=Path(__file__).resolve().parents[1];asus.validate(prior,repo/'results/releases/system1_v5_hosted_refresh_2026-11-13')
 manifest=base.check_manifest(dest);assert manifest['version']=='v5-provisional-nimble-subq' and manifest['frozen_asus_v5_manifest_sha256']==base.sha(prior/'manifest.json')
 for n,h in manifest['source_files_sha256'].items():assert base.sha(repo/n)==h,n
 old=read(prior/'statistics.json');s=read(dest/'statistics.json');models=s['models'];costs=read(dest/'cost_statistics.json')['models'];oldcost=read(prior/'cost_statistics.json')['models']
 assert len(old['models'])==42 and len(models)==44 and set(models)==set(old['models'])|set(SPECS) and set(costs)==set(models)
 assert all(models[k]==v and costs[k]==oldcost[k] for k,v in old['models'].items())
 assert s['questions']==1456 and s['categories']==43 and s['minimum_overall_accuracy']==.45 and s['inclusion_threshold']==old['inclusion_threshold'] and s['inclusion_threshold']['minimum_correct']==656
 assert s['superseded_model_ids']==old['superseded_model_ids']+['nimble_v4_max','subq_snap_1_1'] and s['below_cutoff']==old['below_cutoff'] and len(s['below_cutoff'])==6
 ranked=sorted((k for k,v in models.items() if v['correct']*100>=45*1456 and k not in s['superseded_model_ids']),key=lambda k:(-models[k]['correct'],k))
 assert s['ranked_model_ids']==ranked and len(ranked)==34 and set(models)==set(ranked)|set(s['below_cutoff'])|set(s['superseded_model_ids'])
 assert not set(s['superseded_model_ids'])&(set(ranked)|set(s['below_cutoff']))
 assert [k for k in ranked if k not in SPECS]==[k for k in old['ranked_model_ids'] if k not in ['nimble_v4_max','subq_snap_1_1']]
 assert {'pplx_decider13_native_20261112','pplx_decider_flash13_native_20261112'}<=set(ranked)
 for k in ['questions','categories','minimum_overall_accuracy','inclusion_threshold','superseded_model_ids']:assert manifest[k]==s[k],k
 assert manifest['measured_models']==44 and manifest['main_models']==34 and manifest['partial_screen_models']==3 and manifest['partial_records_per_ledger']==300
 assert (dest/'parent_asus_audit_receipt.json').read_bytes()==(prior/'audit_receipt.json').read_bytes() and (dest/'parent_asus_manifest.json').read_bytes()==(prior/'manifest.json').read_bytes()
 receipt=read(dest/'audit_receipt.json');assert receipt['base_models_retained']==42 and receipt['models_added']==list(SPECS) and receipt['no_scored_retries'] and receipt['readiness_excluded'] and receipt['source_manifest_sha256']==base.sha(prior/'manifest.json')
 for k in ['individual_timing_records','individual_cost_records','individual_correctness_records']:assert receipt[k]==64064
 assert manifest['unchanged_files_sha256']==receipt['unchanged_files_sha256']
 for n,h in receipt['unchanged_files_sha256'].items():assert base.sha(dest/n)==h==base.sha(prior/n),n
 qs={q['id']:q for q in base.jsonlines(dest/'questions_1456.jsonl')};families=collections.Counter(q['family_id'] for q in qs.values());assert len(qs)==1456 and len(families)==43 and families['F32']==20 and families['F33']==200
 tables={}
 for n in ['timing_evidence.csv.gz','cost_evidence.csv.gz','correctness_evidence.csv.gz','all_category_scores.csv']:
  before,after=data(prior/n),data(dest/n);assert after.startswith(before),n
  rr=rows(dest/n);per=43 if n=='all_category_scores.csv' else 1456;second='family_id' if per==43 else 'item_id';idx={(x['model_id'],x[second]):x for x in rr};assert len(rr)==len(idx)==44*per and set(rr[0])==set(rows(prior/n)[0])
  for mid in models:assert {k[1] for k in idx if k[0]==mid}==(set(families) if per==43 else set(qs))
  p=receipt['csv_append_proofs'][n];assert p['original_rows']==42*per and p['appended_rows']==2*per and p['old_csv_bytes_exact_prefix'] and p['original_uncompressed_sha256']==hashlib.sha256(before).hexdigest();tables[n]=idx
 timing,cost,flags,cats=[tables[n] for n in ['timing_evidence.csv.gz','cost_evidence.csv.gz','correctness_evidence.csv.gz','all_category_scores.csv']]
 audits=read(dest/'nimble_subq_model_audits.json');usage=rows(dest/'nimble_subq_usage_evidence.csv.gz');assert set(audits)==set(SPECS) and len(usage)==len({(x['model_id'],x['item_id']) for x in usage})==2912
 for mid,spec in SPECS.items():
  m=models[mid];a=audits[mid];c=costs[mid];lat=[];est=[];assert m['role']=='Hosted native' and m['n']==m['valid']==a['n']==a['usable']==1456 and m['correct']==a['correct']==spec['correct']
  assert a['complete'] and a['configuration_metadata_stable'] and a['configuration_checks']==18 and len(a['configuration_check_file_hashes'])==18 and all(re.fullmatch('[0-9a-f]{64}',x) for x in a['configuration_check_file_hashes'])
  assert a['first_primaries_only'] and a['scored_retries']==0 and a['precision']=='unknown hosted precision' and a['declared_snapshot']==spec['snapshot'] and a['provider']==spec['provider']
  assert m['zero_generation_attested'] is False and m['no_generated_reasoning_text_observed'] and a['reported_cost_usd'] is None and a['reported_usd_subtotal'] is None
  assert m['raw_output_tokens']==spec['counter']*1456 and m['nonzero_output_counter_responses']==(1456 if spec['counter'] else 0) and m['raw_usage_unknown_count']==0
  diag=a['all_primary_usage_diagnostics'];assert diag['input_tokens_all_primaries']==spec['inputs'] and diag['output_tokens_all_primaries']==m['raw_output_tokens'] and diag['nonzero_output_counter_count']==m['nonzero_output_counter_responses']
  for k in ['missing_input_usage_count','missing_output_usage_count','invalid_or_missing_probability_distribution_count','invalid_present_probability_distribution_count','argmax_disagreement_count']:assert diag[k]==0,k
  for item,q in qs.items():
   t,cc,f=timing[mid,item],cost[mid,item],flags[mid,item];assert t['family_id']==cc['family_id']==f['family_id']==q['family_id'] and t['input_sha256']==cc['input_sha256']==q['native_input_sha256']
   assert t['source_record_sha256']==cc['source_record_sha256'] and re.fullmatch('[0-9a-f]{64}',t['source_record_sha256']) and t['status']==cc['status']=='ok' and base.boolean(f['usable']) and t['output_counter']==str(spec['counter'])
   assert t['collection_date_toronto']==cc['collection_date_toronto']=='2026-11-15' and cc['evidence_kind']=='tariff_estimate' and not cc['reported_usd'];v=float(t['latency_ms']);assert math.isfinite(v) and v>=0;lat.append(v);v=Decimal(cc['tariff_estimate_usd']);assert v.is_finite() and v>=0;est.append(v)
  assert sum(base.boolean(flags[mid,i]['correct']) for i in qs)==spec['correct']
  for k,v in [('accuracy',spec['correct']/1456),('coverage',1),('answer_accuracy_among_usable',spec['correct']/1456),('accuracy_upper_if_all_unusable_correct',spec['correct']/1456)]:base.close(m[k],v)
  for k,v in [('mean_ms',statistics.mean(lat)),('median_ms',statistics.median(lat)),('p95_ms',base.q95(lat))]:base.close(m[k],v);base.close(a[k],v)
  for fid,n in families.items():
   ids=[i for i,q in qs.items() if q['family_id']==fid];cc=cats[mid,fid];assert int(cc['n'])==n and int(cc['correct'])==sum(base.boolean(flags[mid,i]['correct']) for i in ids);base.close(cc['accuracy'],int(cc['correct'])/n);vv=[float(timing[mid,i]['latency_ms']) for i in ids]
   for k,v in [('mean_ms',statistics.mean(vv)),('median_ms',statistics.median(vv)),('p95_ms',base.q95(vv))]:base.close(cc[k],v)
  base.close(m['macro_category_accuracy'],statistics.mean(float(cats[mid,f]['accuracy']) for f in families));total=sum(est);assert total==Decimal(spec['amount'])==Decimal(c['known_subtotal_usd'])==Decimal(a['captured_tariff_estimate_usd'])
  assert Decimal(c['known_usd_per_1000'])==total/Decimal(1456)*1000 and c['n']==1456 and c['tariff_estimate_count']==1456 and c['actual_charge_unknown_count']==1456 and c['actual_charge_telemetry']=='unreported' and c['captured_input_tariff_usd_per_million']=='0.04'
  assert all(c[k]==0 for k in ['reported_count','free_access_tariff_count','unknown_count','local_unmeasured_count']) and c['reported_subtotal_usd'] is None and Decimal(c['estimate_only_subtotal_usd'])==total and Decimal(a['readiness_estimate_excluded_usd'])==Decimal(spec['readiness'])
  u=sorted((x for x in usage if x['model_id']==mid),key=lambda x:int(x['sequence']));assert len(u)==1456 and {x['item_id'] for x in u}==set(qs) and [int(x['sequence']) for x in u]==list(range(1,1457))
  for x in u:
   item=x['item_id'];assert x['attempt']=='1' and x['http_status']=='200' and x['status']=='ok' and x['output_tokens']==str(spec['counter']) and x['returned_model']==spec['snapshot'] and x['provider']==spec['provider'] and x['route']=='https://'+spec['host']+'/v1/systemone'
   assert x['family_id']==qs[item]['family_id'] and x['input_sha256']==qs[item]['native_input_sha256'] and x['completed_at_utc']==timing[mid,item]['collected_at_utc'] and x['source_record_sha256']==timing[mid,item]['source_record_sha256']
   for k in ['canonical_record_sha256','raw_response_sha256','payload_sha256']:assert re.fullmatch('[0-9a-f]{64}',x[k])
   assert x['payload_sha256']==digest({'model':spec['snapshot'],**qs[item]['native_input']}) and json.loads(x['raw_usage_json'])=={'input_tokens':int(x['input_tokens']),'output_tokens':spec['counter']}
   assert not x['reported_usd'] and x['tariff_estimate_usd']==cost[mid,item]['tariff_estimate_usd'] and Decimal(x['tariff_estimate_usd'])==Decimal(x['input_tokens'])*Decimal('0.04')/Decimal(1000000)
  assert sum(int(x['input_tokens']) for x in u)==m['input_tokens']==spec['inputs'];proof=receipt['new_sources'][mid];assert digest([[x['item_id'],x['source_record_sha256']] for x in u])==a['source_record_digest']==proof['source_record_digest'] and proof['first100_preserved'] and proof['independent_final_review_verdict']=='APPROVE'
  for k in ['independent_final_review_sha256','source_manifest_sha256','plan_sha256','first100_receipt_sha256']:assert re.fullmatch('[0-9a-f]{64}',proof[k])
  assert proof['independent_final_review_sha256']=='dddba509f2ff26a9825ef87ff60e4ef78cee193954785a5d78cc04fa316d1e49' and proof['final_review_addendum_verdict']=='APPROVE' and proof['final_review_addendum_sha256']=='3bd1a84a34ee67b2d86254f7c33fda16dfa20442f17a6f91a4b7cf599c44d833'
  assert ranked.index(mid)+1==spec['rank']
 # Bind all43category interpretations and version pairs to the main booleans, independently of receipt labels.
 analysis=read(dest/'nimble_subq_analysis.json');assert analysis['complete_configurations_after_append']==44 and analysis['active_configurations']==34 and set(analysis['current_active_model_ids'])==set(ranked)
 cr=rows(dest/'nimble_subq_category_comparison.csv');assert len(cr)==86 and len({(x['model_id'],x['family_id']) for x in cr})==86
 for mid,spec in SPECS.items():
  a=analysis['interpretation'][mid];assert a['overall_accuracy_rank']==spec['rank'] and a['active_cohort_n']==34 and a['overall_leader_correct']==max(models[x]['correct'] for x in ranked) and len(a['categories'])==43 and {x['family_id'] for x in a['categories']}==set(families) and len({x['family_id'] for x in a['categories']})==43
  for x in a['categories']:
   fid=x['family_id'];good=int(cats[mid,fid]['correct']);before=int(cats[spec['old'],fid]['correct']);leader=max(int(cats[k,fid]['correct']) for k in ranked);rank=1+sum(int(cats[k,fid]['correct'])>good for k in ranked)
   assert x['n']==families[fid] and x['correct']==good and x['old_version_correct']==before and x['new_minus_old_correct']==good-before and x['current34_accuracy_rank']==rank and x['leader_correct']==leader and set(x['leader_model_ids'])=={k for k in ranked if int(cats[k,fid]['correct'])==leader}
   rr=next(y for y in cr if y['model_id']==mid and y['family_id']==fid)
   for k in ['n','correct','old_version_correct','new_minus_old_correct','current34_accuracy_rank','leader_correct']:assert int(rr[k])==x[k]
  pairs=read(dest/(mid+'_paired_comparison_all42.json'));assert isinstance(pairs,dict) and set(pairs)==set(old['models'])
  for other,p in pairs.items():
   assert other in old['models'] and p['reference_model_id']==other
   aa=[base.boolean(flags[mid,i]['correct']) for i in qs];bb=[base.boolean(flags[other,i]['correct']) for i in qs];common=[i for i in qs if base.boolean(flags[other,i]['usable'])]
   assert p['both_correct']==sum(a and b for a,b in zip(aa,bb)) and p['new_only_correct']==sum(a and not b for a,b in zip(aa,bb)) and p['reference_only_correct']==sum(b and not a for a,b in zip(aa,bb)) and p['neither_correct']==sum(not a and not b for a,b in zip(aa,bb)) and p['common_usable_n']==len(common)
   assert p['new_correct_common_usable']==sum(base.boolean(flags[mid,i]['correct']) for i in common) and p['reference_correct_common_usable']==sum(base.boolean(flags[other,i]['correct']) for i in common)
 nv=read(dest/'nimble_version_comparison.json');sv=read(dest/'subq_version_comparison.json')
 assert nv['new_correct']==950 and nv['old_correct']==943 and nv['difference_correct']==7 and nv['common_usable_n']==1455 and nv['new_common_correct']==949 and nv['old_common_correct']==943 and nv['additional_correct_where_old_unusable']==1 and nv['old_estimated_record_count']==1235 and nv['old_unknown_record_count']==221
 assert Decimal(nv['new_full_bank_estimate_usd'])==Decimal(costs['nimble_v41_max']['known_subtotal_usd']) and Decimal(nv['old_known_estimated_subtotal_usd'])==Decimal(costs['nimble_v4_max']['known_subtotal_usd'])
 assert sv['new_correct']==927 and sv['old_correct']==943 and sv['difference_correct']==-16 and sv['price_or_estimated_bank_cost_improvement'] is False and sv['new_and_old_input_tokens']==786233
 assert Decimal(sv['new_and_old_estimated_bank_usd'])==Decimal(costs['subq_snap12']['known_subtotal_usd'])==Decimal(costs['subq_snap_1_1']['known_subtotal_usd'])
 for mid,v in [('nimble_v41_max',nv),('subq_snap12',sv)]:
  for k in ['median_ms','p95_ms']:base.close(v['new_'+k],models[mid][k]);base.close(v['old_'+k],models[SPECS[mid]['old']][k])
 page,md=(dest/'report.html').read_text(),(dest/'README_V5.md').read_text();section=re.search(r'<section id="nimble-subq-update">.*?</section>',page,re.S).group()
 for phrase in ['950/1,456','927/1,456','943/1,456','−16 correct','−1.0989','same estimate','0.03103948','0.03144932','221 unknown','1,235','precise billing-savings','two raw output-accounting tokens','18 matching','not sustained throughput','option-order invariance','85/200','124/200','89/200','81/200','88/200','no errors','first attempts','precision is unknown']:
  assert phrase in section and phrase in md,phrase
 assert '12,050.47' in section and float(timing['nimble_v41_max','J001879']['latency_ms'])>12000
 desktop=re.search(r'<div class="comparison-table">.*?</table>',page,re.S).group();assert re.findall(r'data-overall-model="([^"]+)"',desktop)==ranked and re.findall(r'<article class="mobile-card" data-overall-model="([^"]+)"',page)==ranked
 for mid in ranked:
  row=re.search(r'<tr data-overall-model="'+re.escape(mid)+r'">(.*?)</tr>',desktop,re.S).group(1);assert f'{models[mid]["accuracy"]:.2%}' in row and re.findall(r'data-speed-band="([^"]+)"',row)==[str(base.band(models[mid][k],[250,500,1000])) for k in ['median_ms','p95_ms']];band=base.cost_band(costs[mid]);assert re.findall(r'data-cost-band="([^"]+)"',row)==['unknown' if band is None else str(band)]*2 and html.escape(base.cost_label(costs[mid])) in row
 # Original ASUS data/cards are immutable; only the historical full-cohort scope sentence changes.
 for p in prior.glob('asus_native*'):assert (dest/p.name).read_bytes()==p.read_bytes(),p.name
 inherited=re.search(r'<section id="asus-native-screens">.*?</section>',(prior/'report.html').read_text(),re.S).group();partial=re.search(r'<section id="asus-native-screens">.*?</section>',page,re.S).group()
 assert re.findall(r'<article class="asus-screen-card".*?</article>',partial,re.S)==re.findall(r'<article class="asus-screen-card".*?</article>',inherited,re.S) and page.index(partial)<page.index('<section id="below-cutoff">')
 assert set(asus.SPECS).isdisjoint(models) and 'At the November 13' in partial and 'three partial screens' in partial
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
 print('PASS: Nimble950/SubQ927;44complete/34active/6below/4superseded;64064records;42priorobjects/61152prefixes;pooledtiming/Decimalcost/nativecounters/categories/ranks/ASUSpartials/privacy/mirror verified.')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('release',type=Path);p.add_argument('prior',type=Path);p.add_argument('--mirror',type=Path);a=p.parse_args();validate(a.release.resolve(),a.prior.resolve(),a.mirror.resolve() if a.mirror else None)
