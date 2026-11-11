"""Offline validation of SingVL's distributed-local v5 successor."""
import argparse,collections,csv,gzip,hashlib,html,io,json,math,re,statistics,struct
from pathlib import Path
from urllib.parse import unquote,urlsplit
import validate_system1_v5_provisional_2026_11_09 as base
import validate_system1_v5_drex_2026_11_09 as drex
MID='singvl_s1_4b_q4km_llamacpp_ctx4096_lan'
COLOR='#b2364b'
def read(p):return json.loads(p.read_text())
def rows(p):return list(csv.DictReader(io.StringIO(gzip.decompress(p.read_bytes()).decode() if p.name.endswith('.gz') else p.read_text())))
def validate(dest,prior,mirror=None):
 repo=Path(__file__).resolve().parents[1]
 drex.validate(prior,repo/'results/releases/system1_v5_hosted_2026-11-09')
 manifest=base.check_manifest(dest)
 assert manifest['frozen_drex_v5_manifest_sha256']==base.sha(prior/'manifest.json')
 for name,digest in manifest['source_files_sha256'].items():assert base.sha(repo/name)==digest,name
 old,s=read(prior/'statistics.json'),read(dest/'statistics.json');models=s['models']
 oldcost=read(prior/'cost_statistics.json')['models'];cost=read(dest/'cost_statistics.json')['models']
 assert len(old['models'])==35 and len(models)==36 and set(models)==set(old['models'])|{MID}
 assert all(models[k]==v and cost[k]==oldcost[k] for k,v in old['models'].items())
 assert s['questions']==1456 and s['categories']==43 and s['minimum_overall_accuracy']==.45
 assert s['inclusion_threshold']==old['inclusion_threshold'] and s['superseded_model_ids']==old['superseded_model_ids']==['drex_max']
 ranked=sorted((k for k,v in models.items() if v['correct']*100>=45*1456 and k not in s['superseded_model_ids']),key=lambda k:(-models[k]['correct'],k))
 assert s['ranked_model_ids']==ranked and len(ranked)==29 and s['below_cutoff']==old['below_cutoff'] and len(s['below_cutoff'])==6
 assert [k for k in ranked if k!=MID]==old['ranked_model_ids']
 assert (dest/'parent_drex_audit_receipt.json').read_bytes()==(prior/'audit_receipt.json').read_bytes()
 receipt=read(dest/'audit_receipt.json');assert receipt['base_models_retained']==35 and receipt['models_added']==[MID]
 assert receipt['source_manifest_sha256']==base.sha(prior/'manifest.json') and receipt['no_scored_retries'] and receipt['original20_excluded']
 for k in ['individual_timing_records','individual_cost_records','individual_correctness_records']:assert receipt[k]==52416
 for name,h in receipt['unchanged_files_sha256'].items():assert base.sha(dest/name)==h==base.sha(prior/name),name
 for name in manifest['unchanged_files_sha256']:assert base.sha(dest/name)==manifest['unchanged_files_sha256'][name]
 qrows=base.jsonlines(dest/'questions_1456.jsonl');qs={x['id']:x for x in qrows};assert len(qs)==len(qrows)==1456
 families=collections.Counter(x['family_id'] for x in qrows);assert len(families)==43 and families['F32']==20 and families['F33']==200
 tables={}
 for name in ['timing_evidence.csv.gz','cost_evidence.csv.gz','correctness_evidence.csv.gz','all_category_scores.csv']:
  before=gzip.decompress((prior/name).read_bytes()) if name.endswith('.gz') else (prior/name).read_bytes()
  after=gzip.decompress((dest/name).read_bytes()) if name.endswith('.gz') else (dest/name).read_bytes();assert after.startswith(before),name
  rr=rows(dest/name);fields=['model_id','family_id'] if name=='all_category_scores.csv' else ['model_id','item_id'];idx={tuple(r[k] for k in fields):r for r in rr}
  per=43 if name=='all_category_scores.csv' else 1456;assert len(rr)==len(idx)==36*per and sum(r['model_id']==MID for r in rr)==per
  assert set(rr[0])==set(rows(prior/name)[0])
  proof=receipt['csv_append_proofs'][name];assert proof['original_rows']==35*per and proof['appended_rows']==per and proof['old_csv_bytes_exact_prefix']
  assert proof['original_uncompressed_sha256']==hashlib.sha256(before).hexdigest();tables[name]=idx
 timing,costrows,flags,cats=[tables[n] for n in ['timing_evidence.csv.gz','cost_evidence.csv.gz','correctness_evidence.csv.gz','all_category_scores.csv']]
 m=models[MID];audit=read(dest/'singvl_model_audit.json')
 assert m['role']=='Local distributed' and m['n']==m['valid']==audit['n']==audit['valid']==1456
 assert m['correct']==audit['correct']==698 and audit['complete']
 assert m['zero_generation_attested'] is False and m['no_generated_reasoning_text_observed'] and m['raw_output_tokens']==0
 lat=[]
 for item,q in qs.items():
  t,c,f=timing[MID,item],costrows[MID,item],flags[MID,item]
  assert t['family_id']==c['family_id']==f['family_id']==q['family_id'] and t['input_sha256']==c['input_sha256']==q['native_input_sha256']
  assert t['source_record_sha256']==c['source_record_sha256'] and re.fullmatch('[0-9a-f]{64}',t['source_record_sha256'])
  assert t['status']==c['status']=='ok' and base.boolean(f['usable'])
  assert t['output_counter']=='0' and not c['reported_usd'] and not c['tariff_estimate_usd'] and c['evidence_kind']=='local_unmeasured'
  v=float(t['latency_ms']);assert math.isfinite(v) and v>=0;lat.append(v)
 assert sum(base.boolean(flags[MID,k]['correct']) for k in qs)==698
 for key,v in [('accuracy',698/1456),('coverage',1),('answer_accuracy_among_usable',698/1456),('accuracy_upper_if_all_unusable_correct',698/1456)]:base.close(m[key],v)
 for key,v in [('mean_ms',statistics.mean(lat)),('median_ms',statistics.median(lat)),('p95_ms',base.q95(lat))]:base.close(m[key],v);base.close(audit[key],v)
 for fid,n in families.items():
  ids=[k for k,q in qs.items() if q['family_id']==fid];r=cats[MID,fid];assert int(r['n'])==n
  assert int(r['correct'])==sum(base.boolean(flags[MID,k]['correct']) for k in ids);base.close(r['accuracy'],int(r['correct'])/n)
  vv=[float(timing[MID,k]['latency_ms']) for k in ids]
  for key,v in [('mean_ms',statistics.mean(vv)),('median_ms',statistics.median(vv)),('p95_ms',base.q95(vv))]:base.close(r[key],v)
 base.close(m['macro_category_accuracy'],statistics.mean(float(cats[MID,f]['accuracy']) for f in families))
 c=cost[MID];assert c['n']==c['local_unmeasured_count']==1456
 for k in ['reported_count','tariff_estimate_count','free_access_tariff_count','unknown_count']:assert c[k]==0
 for k in ['reported_subtotal_usd','estimate_only_subtotal_usd','known_subtotal_usd','known_usd_per_1000']:assert c[k] is None
 u=rows(dest/'singvl_usage_evidence.csv.gz');assert len(u)==1456 and {x['item_id'] for x in u}==set(qs)
 assert all(x['model_id']==MID and x['attempt']=='1' and x['http_status']=='200' and x['output_tokens']=='0' and x['returned_model']=='sing-vl-s1' for x in u)
 assert sum(int(x['input_tokens']) for x in u)==audit['input_tokens']==m['input_tokens']
 source_digest=hashlib.sha256(json.dumps([[x['item_id'],x['source_record_sha256']] for x in sorted(u,key=lambda x:int(x['sequence']))],sort_keys=True,ensure_ascii=False,separators=(',',':'),allow_nan=False).encode()).hexdigest()
 assert source_digest==audit['source_record_digest']==receipt['new_record_digest']
 for x in u:assert x['source_record_sha256']==timing[MID,x['item_id']]['source_record_sha256'] and x['input_sha256']==qs[x['item_id']]['native_input_sha256']
 h=read(dest/'singvl_hardware.json');assert h['model_id']==MID and h['role']=='Local distributed' and h['color']==COLOR
 assert h['node_count']==h['gpu_count']==len(h['nodes'])==2 and h['nominal_total_vram_gb']==12
 assert [n['name'] for n in h['nodes']]==['ASUS TUF','Lenovo Legion'] and all(n['gpu']=='NVIDIA RTX2060' and n['gpu_vram_gb']==6 for n in h['nodes'])
 assert h['gpu_placement_independently_attested'] is False and h['backend_context']==h['adapter_input_limit']==4096
 assert h['original_screen']['excluded_from_current_score_and_timing'] and h['original_screen']['attempts']==20
 assert h['readiness']['long_request_input_tokens']==1597 and h['readiness']['oversize_rejected_http_status']==422
 page,md=(dest/'report.html').read_text(),(dest/'README_V5.md').read_text()
 assert page.index('src="comparison_accuracy.png"')<page.index('<div class="comparison-table">')
 for text in ['rose','two-computer','Ryzen 7','Intel Core i7','6 GB','user-reported','unmetered','45%']:assert text in page and text in md,text
 desktop=re.search(r'<div class="comparison-table">.*?</table>',page,re.S).group()
 assert re.findall(r'data-overall-model="([^"]+)"',desktop)==ranked
 assert re.findall(r'<article class="mobile-card" data-overall-model="([^"]+)"',page)==ranked
 assert COLOR in desktop and COLOR in page and '<section id="singvl-update">' in page
 assert 'Model-selected choices and the gold scoring key remain private.' in md
 for k in ranked:
  row=re.search(r'<tr data-overall-model="'+re.escape(k)+r'">(.*?)</tr>',desktop,re.S).group(1)
  model=models[k];assert f'{model["accuracy"]:.2%}' in row
  assert re.findall(r'data-speed-band="([^"]+)"',row)==[str(base.band(model[f],[250,500,1000])) for f in ['median_ms','p95_ms']]
  band=base.cost_band(cost[k]);assert re.findall(r'data-cost-band="([^"]+)"',row)==['unknown' if band is None else str(band)]*2
  assert html.escape(base.cost_label(cost[k])) in row
 for kind in ['accuracy','latency','cost']:
  data=(dest/('comparison_'+kind+'.png')).read_bytes();assert data[:8]==b'\x89PNG\r\n\x1a\n';w,hh=struct.unpack('>II',data[16:24]);assert w>=1300 and hh>=1600
 for svg in [dest/'overview.svg']+list(dest.glob('comparison_*.svg'))+list(dest.glob('categories_*.svg')):
  txt=svg.read_text();assert COLOR in txt and 'rose two-computer local' in txt,svg
 for target in re.findall(r'(?:href|src)="([^"]+)"',page):
  url=urlsplit(html.unescape(target))
  if not url.scheme and not url.netloc and url.path:assert (dest/unquote(url.path)).exists(),target
 base.check_markdown_links(dest)
 for p in dest.rglob('*'):
  if p.is_file() and p.suffix not in ('.png','.svg'):
   data=gzip.decompress(p.read_bytes()) if p.name.endswith('.gz') else p.read_bytes()
   assert b'/Users/' not in data and b'"expected_answer"' not in data and b'"gold_answer"' not in data and b'"choice":' not in data,p
 if mirror:
  assert {str(p.relative_to(mirror)) for p in mirror.rglob('*') if p.is_file()}=={str(p.relative_to(dest)) for p in dest.rglob('*') if p.is_file()}
  for p in dest.rglob('*'):
   if p.is_file():assert p.read_bytes()==(mirror/p.relative_to(dest)).read_bytes(),p
  base.check_markdown_links(mirror)
 print('PASS: SingVL698/1456;36complete/29active/6below/1superseded;52416records;all35prior objects/prefixes preserved;four-role color/hardware provenance/cost/pooled timing/mirror verified.')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('release',type=Path);p.add_argument('prior',type=Path);p.add_argument('--mirror',type=Path);a=p.parse_args();validate(a.release.resolve(),a.prior.resolve(),a.mirror.resolve() if a.mirror else None)
