"""Offline validation of the D3 Flash distributed-local v5 successor."""
import argparse,collections,csv,gzip,hashlib,html,io,json,math,re,statistics,struct
from datetime import datetime
from pathlib import Path
from urllib.parse import unquote,urlsplit
import validate_system1_v5_provisional_2026_11_09 as base
import validate_system1_v5_singvl_2026_11_11 as singvl
MID='d3_flash_9b_q4km_llamacpp_ctx4096_lan';COLOR='#b2364b';FAILED='EXT-F31-018'
def read(p):return json.loads(p.read_text())
def rows(p):return list(csv.DictReader(io.StringIO(gzip.decompress(p.read_bytes()).decode() if p.name.endswith('.gz') else p.read_text())))
def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,ensure_ascii=False,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def validate(dest,prior,mirror=None):
    repo=Path(__file__).resolve().parents[1]
    singvl.validate(prior,repo/'results/releases/system1_v5_drex_2026-11-09')
    manifest=base.check_manifest(dest);assert manifest['frozen_singvl_v5_manifest_sha256']==base.sha(prior/'manifest.json')
    for name,expected in manifest['source_files_sha256'].items():assert base.sha(repo/name)==expected,name
    old,s=read(prior/'statistics.json'),read(dest/'statistics.json');models=s['models']
    oldcost=read(prior/'cost_statistics.json')['models'];cost=read(dest/'cost_statistics.json')['models']
    assert len(old['models'])==36 and len(models)==37 and set(models)==set(old['models'])|{MID}
    assert all(models[k]==v and cost[k]==oldcost[k] for k,v in old['models'].items())
    assert s['questions']==1456 and s['categories']==43 and s['minimum_overall_accuracy']==.45
    assert s['inclusion_threshold']==old['inclusion_threshold'] and s['superseded_model_ids']==old['superseded_model_ids']==['drex_max']
    ranked=sorted((k for k,v in models.items() if v['correct']*100>=45*1456 and k not in s['superseded_model_ids']),key=lambda k:(-models[k]['correct'],k))
    assert s['ranked_model_ids']==ranked and len(ranked)==30 and s['below_cutoff']==old['below_cutoff'] and len(s['below_cutoff'])==6
    assert [k for k in ranked if k!=MID]==old['ranked_model_ids'] and ranked.index(MID)==24
    assert (dest/'parent_singvl_audit_receipt.json').read_bytes()==(prior/'audit_receipt.json').read_bytes()
    receipt=read(dest/'audit_receipt.json');assert receipt['base_models_retained']==36 and receipt['models_added']==[MID]
    assert receipt['source_manifest_sha256']==base.sha(prior/'manifest.json') and receipt['no_scored_retries'] and receipt['failed_primary_retained'] and receipt['original744_preserved'] and receipt['continuation712_usable']
    for key in ['individual_timing_records','individual_cost_records','individual_correctness_records']:assert receipt[key]==53872
    for name,h in receipt['unchanged_files_sha256'].items():assert base.sha(dest/name)==h==base.sha(prior/name),name
    for name,h in manifest['unchanged_files_sha256'].items():assert base.sha(dest/name)==h,name
    qrows=base.jsonlines(dest/'questions_1456.jsonl');qs={x['id']:x for x in qrows};assert len(qs)==len(qrows)==1456
    families=collections.Counter(x['family_id'] for x in qrows);assert len(families)==43 and families['F32']==20 and families['F33']==200
    tables={}
    for name in ['timing_evidence.csv.gz','cost_evidence.csv.gz','correctness_evidence.csv.gz','all_category_scores.csv']:
        before=gzip.decompress((prior/name).read_bytes()) if name.endswith('.gz') else (prior/name).read_bytes()
        after=gzip.decompress((dest/name).read_bytes()) if name.endswith('.gz') else (dest/name).read_bytes();assert after.startswith(before),name
        rr=rows(dest/name);fields=['model_id','family_id'] if name=='all_category_scores.csv' else ['model_id','item_id'];idx={tuple(r[k] for k in fields):r for r in rr}
        per=43 if name=='all_category_scores.csv' else 1456
        assert len(rr)==len(idx)==37*per and sum(r['model_id']==MID for r in rr)==per
        assert set(rr[0])==set(rows(prior/name)[0])
        proof=receipt['csv_append_proofs'][name];assert proof['original_rows']==36*per and proof['appended_rows']==per and proof['old_csv_bytes_exact_prefix']
        assert proof['original_uncompressed_sha256']==hashlib.sha256(before).hexdigest();tables[name]=idx
    timing,costrows,flags,cats=[tables[n] for n in ['timing_evidence.csv.gz','cost_evidence.csv.gz','correctness_evidence.csv.gz','all_category_scores.csv']]
    m=models[MID];audit=read(dest/'d3_flash_model_audit.json')
    assert m['role']=='Local distributed' and m['n']==audit['n']==1456 and m['valid']==audit['valid']==1455
    assert m['correct']==audit['correct']==704 and audit['complete'] and audit['known_usage_records']==1455 and audit['missing_usage_records']==1
    assert m['zero_generation_attested'] is False and m['no_generated_reasoning_text_observed'] and m['raw_output_tokens']==0 and m['raw_usage_unknown_count']==1
    lat=[]
    for item,q in qs.items():
        t,c,f=timing[MID,item],costrows[MID,item],flags[MID,item]
        assert t['family_id']==c['family_id']==f['family_id']==q['family_id'] and t['input_sha256']==c['input_sha256']==q['native_input_sha256']
        assert t['source_record_sha256']==c['source_record_sha256'] and re.fullmatch('[0-9a-f]{64}',t['source_record_sha256'])
        assert t['status']==c['status']==('transport_failure' if item==FAILED else 'ok') and base.boolean(f['usable'])==(item!=FAILED)
        assert t['output_counter']==('' if item==FAILED else '0') and not c['reported_usd'] and not c['tariff_estimate_usd'] and c['evidence_kind']=='local_unmeasured'
        if item==FAILED:assert not base.boolean(f['correct']) and 'TimeoutError' in t['failure_kind'] and float(t['latency_ms'])>=30000
        v=float(t['latency_ms']);assert math.isfinite(v) and v>=0;lat.append(v)
    assert sum(base.boolean(flags[MID,k]['correct']) for k in qs)==704
    for key,value in [('accuracy',704/1456),('coverage',1455/1456),('answer_accuracy_among_usable',704/1455),('accuracy_upper_if_all_unusable_correct',705/1456)]:base.close(m[key],value)
    for key,value in [('mean_ms',statistics.mean(lat)),('median_ms',statistics.median(lat)),('p95_ms',base.q95(lat))]:base.close(m[key],value);base.close(audit[key],value)
    for fid,n in families.items():
        ids=[k for k,q in qs.items() if q['family_id']==fid];r=cats[MID,fid];assert int(r['n'])==n
        assert int(r['correct'])==sum(base.boolean(flags[MID,k]['correct']) for k in ids);base.close(r['accuracy'],int(r['correct'])/n)
        vv=[float(timing[MID,k]['latency_ms']) for k in ids]
        for key,value in [('mean_ms',statistics.mean(vv)),('median_ms',statistics.median(vv)),('p95_ms',base.q95(vv))]:base.close(r[key],value)
    base.close(m['macro_category_accuracy'],statistics.mean(float(cats[MID,f]['accuracy']) for f in families))
    c=cost[MID];assert c['n']==c['local_unmeasured_count']==1456
    for key in ['reported_count','tariff_estimate_count','free_access_tariff_count','unknown_count']:assert c[key]==0
    for key in ['reported_subtotal_usd','estimate_only_subtotal_usd','known_subtotal_usd','known_usd_per_1000']:assert c[key] is None
    u=sorted(rows(dest/'d3_flash_usage_evidence.csv.gz'),key=lambda x:int(x['sequence']))
    assert len(u)==1456 and {x['item_id'] for x in u}==set(qs) and [int(x['sequence']) for x in u]==list(range(1,1457))
    for x in u:
        bad=x['item_id']==FAILED;assert x['model_id']==MID and x['attempt']=='1'
        assert x['http_status']==('0' if bad else '200') and x['output_tokens']==('' if bad else '0') and x['returned_model']==('' if bad else 'd3-flash')
        assert bool(x['input_tokens'])==(not bad) and (not bad or int(x['sequence'])==744)
        assert x['phase']==('initial' if int(x['sequence'])<=744 else 'paced_continuation')
        assert float(x['minimum_start_interval_seconds'])==(0 if int(x['sequence'])<=744 else 1.6)
        assert re.fullmatch('[0-9a-f]{64}',x['canonical_record_sha256'])
        assert x['completed_at_utc']==timing[MID,x['item_id']]['collected_at_utc']
        assert x['source_record_sha256']==timing[MID,x['item_id']]['source_record_sha256'] and x['input_sha256']==qs[x['item_id']]['native_input_sha256']
    assert sum(int(x['input_tokens']) for x in u if x['input_tokens'])==audit['input_tokens']==m['input_tokens']==796665
    assert digest([[x['item_id'],x['source_record_sha256']] for x in u])==audit['source_record_digest']==receipt['new_record_digest']
    phases=read(dest/'d3_flash_transport_phases.json')
    assert phases['original744_preserved'] and phases['pooled_timing_from_individual_primaries']
    assert phases['minimum_start_interval_seconds']==1.6 and [x['phase'] for x in phases['phases']]==['initial','paced_continuation']
    assert digest([[x['item_id'],x['canonical_record_sha256']] for x in u[:744]])==phases['preserved_prefix_record_digest']
    failed=phases['failed_primary'];assert failed['item_id']==FAILED and failed['sequence']==744 and failed['retained'] and failed['replayed'] is False and failed['usage_available'] is False
    for i,subset in enumerate([u[:744],u[744:]]):
        ph=phases['phases'][i];vv=[float(timing[MID,x['item_id']]['latency_ms']) for x in subset]
        assert ph['n']==len(subset) and ph['usable']==(743 if i==0 else 712)
        for key,value in [('mean_ms',statistics.mean(vv)),('median_ms',statistics.median(vv)),('p95_ms',base.q95(vv))]:base.close(ph[key],value)
    starts=[datetime.fromisoformat(x['started_at_utc']).timestamp() for x in u]
    gaps=[starts[i]-starts[i-1] for i in range(744,1456)];assert min(gaps)>=1.59
    base.close(min(gaps),phases['minimum_observed_continuation_spacing_seconds'])
    analysis=read(dest/'d3_flash_analysis.json');assert analysis['correct']==704 and analysis['active_cohort_n']==30 and analysis['rank_among_current_active']==25
    assert len(analysis['categories'])==43 and {x['family_id'] for x in analysis['categories']}==set(families)
    for row in analysis['categories']:
        existing=cats[MID,row['family_id']]
        assert row['n']==int(existing['n']) and row['correct']==int(existing['correct'])
        for key in ['accuracy','mean_ms','median_ms','p95_ms']:base.close(row[key],float(existing[key]))
    comparison_rows=rows(dest/'d3_flash_category_comparison.csv')
    assert len(comparison_rows)==36*43 and len({(x['model_id'],x['family_id']) for x in comparison_rows})==36*43
    for row in comparison_rows:
        assert row['model_id'] in old['models'] and row['family_id'] in families
        assert int(row['n'])==families[row['family_id']]
        assert int(row['correct'])==int(cats[row['model_id'],row['family_id']]['correct'])
        assert int(row['new_correct'])==int(cats[MID,row['family_id']]['correct'])
    assert len(analysis['matched_comparisons'])==36 and {x['model_id'] for x in analysis['matched_comparisons']}==set(old['models'])
    for pair in analysis['matched_comparisons']:
        mid=pair['model_id'];newgood=[base.boolean(flags[MID,k]['correct']) for k in qs];oldgood=[base.boolean(flags[mid,k]['correct']) for k in qs]
        assert pair['n']==1456 and pair['new_correct']==704 and pair['correct']==models[mid]['correct']
        assert pair['both_correct']==sum(a and b for a,b in zip(newgood,oldgood))
        assert pair['new_only_correct']==sum(a and not b for a,b in zip(newgood,oldgood)) and pair['old_only_correct']==sum(b and not a for a,b in zip(newgood,oldgood))
    h=read(dest/'d3_flash_hardware.json');assert h['model_id']==MID and h['role']=='Local distributed' and h['color']==COLOR
    assert h['node_count']==h['gpu_count']==len(h['nodes'])==2 and h['nominal_total_vram_gb']==12
    assert all(n['gpu']=='NVIDIA RTX2060' and n['gpu_vram_gb']==6 for n in h['nodes'])
    assert h['gpu_placement_independently_attested'] is False and h['weight_file_hash_available'] is False and h['backend_context']==4096
    page,md=(dest/'report.html').read_text(),(dest/'README_V5.md').read_text()
    assert page.index('src="comparison_accuracy.png"')<page.index('<div class="comparison-table">')
    section=re.search(r'<section id="d3-flash-update">(.*?)</section>',page,re.S).group(1)
    assert '48.35%' in section and 'cooling' not in section.lower() and 'timeout' not in section.lower()
    assert 'cooling' not in (dest/'D3_FLASH_NOTES.md').read_text().lower() and 'unconfirmed' in (dest/'D3_FLASH_NOTES.md').read_text().lower()
    for text in ['rose','two-computer','Ryzen 7','Intel Core i7','6 GB','user-reported','unmetered','45%']:assert text in page and text in md,text
    desktop=re.search(r'<div class="comparison-table">.*?</table>',page,re.S).group()
    assert re.findall(r'data-overall-model="([^"]+)"',desktop)==ranked
    assert re.findall(r'<article class="mobile-card" data-overall-model="([^"]+)"',page)==ranked and COLOR in desktop
    for key in ranked:
        row=re.search(r'<tr data-overall-model="'+re.escape(key)+r'">(.*?)</tr>',desktop,re.S).group(1);model=models[key]
        assert f'{model["accuracy"]:.2%}' in row
        assert re.findall(r'data-speed-band="([^"]+)"',row)==[str(base.band(model[f],[250,500,1000])) for f in ['median_ms','p95_ms']]
        band=base.cost_band(cost[key]);assert re.findall(r'data-cost-band="([^"]+)"',row)==['unknown' if band is None else str(band)]*2
        assert html.escape(base.cost_label(cost[key])) in row
    for kind in ['accuracy','latency','cost']:
        data=(dest/('comparison_'+kind+'.png')).read_bytes();assert data[:8]==b'\x89PNG\r\n\x1a\n';w,height=struct.unpack('>II',data[16:24]);assert w>=1300 and height>=1600
    for svg in [dest/'overview.svg']+list(dest.glob('comparison_*.svg'))+list(dest.glob('categories_*.svg')):
        text=svg.read_text();assert COLOR in text and 'rose two-computer local' in text,svg
    for target in re.findall(r'(?:href|src)="([^"]+)"',page):
        url=urlsplit(html.unescape(target))
        if not url.scheme and not url.netloc and url.path:assert (dest/unquote(url.path)).exists(),target
    base.check_markdown_links(dest)
    for path in dest.rglob('*'):
        if path.is_file() and path.suffix not in ['.png','.svg']:
            data=gzip.decompress(path.read_bytes()) if path.name.endswith('.gz') else path.read_bytes()
            assert b'/Users/' not in data and b'"expected_answer"' not in data and b'"gold_answer"' not in data and b'"choice":' not in data,path
    if mirror:
        assert {str(p.relative_to(mirror)) for p in mirror.rglob('*') if p.is_file()}=={str(p.relative_to(dest)) for p in dest.rglob('*') if p.is_file()}
        for path in dest.rglob('*'):
            if path.is_file():assert path.read_bytes()==(mirror/path.relative_to(dest)).read_bytes(),path
        base.check_markdown_links(mirror)
    print('PASS: D3 Flash704/1456;37complete/30active/6below/1superseded;53872records;all36prior objects/prefixes preserved;failure/usage/pacing/hardware/cost/pooled timing/neutral summary/mirror verified.')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('release',type=Path);p.add_argument('prior',type=Path);p.add_argument('--mirror',type=Path);a=p.parse_args();validate(a.release.resolve(),a.prior.resolve(),a.mirror.resolve() if a.mirror else None)
