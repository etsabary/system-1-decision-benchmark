"""Offline validation of the native Gemini Decision 1 v5 successor."""
import argparse, collections, csv, gzip, hashlib, html, io, json, math, re, statistics, struct
from decimal import Decimal
from pathlib import Path
from urllib.parse import unquote, urlsplit
import validate_system1_v5_provisional_2026_11_09 as base
import validate_system1_v5_d3_flash_2026_11_11 as d3

MID = 'gemini_decision1_openrouter_20261111'
SNAPSHOT = 'google/gemini-decision-1-20261111'
read = lambda p: json.loads(p.read_text())

def rows(p):
    return list(csv.DictReader(io.StringIO(gzip.decompress(p.read_bytes()).decode() if p.name.endswith('.gz') else p.read_text())))

def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,ensure_ascii=False,separators=(',',':'),allow_nan=False).encode()).hexdigest()

def validate(dest, prior, mirror=None):
    repo = Path(__file__).resolve().parents[1]
    d3.validate(prior,repo/'results/releases/system1_v5_singvl_2026-11-11')
    manifest = base.check_manifest(dest)
    assert manifest['frozen_d3_flash_v5_manifest_sha256'] == base.sha(prior/'manifest.json')
    for name, h in manifest['source_files_sha256'].items():
        assert base.sha(repo/name) == h,name
    old,s = read(prior/'statistics.json'),read(dest/'statistics.json')
    models = s['models']; costs = read(dest/'cost_statistics.json')['models']
    oldcosts = read(prior/'cost_statistics.json')['models']
    assert len(old['models']) == 37 and len(models) == 38 and set(models) == set(old['models'])|{MID}
    assert all(models[k] == v and costs[k] == oldcosts[k] for k,v in old['models'].items())
    assert s['questions'] == 1456 and s['categories'] == 43 and s['minimum_overall_accuracy'] == .45
    assert s['inclusion_threshold'] == old['inclusion_threshold'] and s['superseded_model_ids'] == ['drex_max']
    assert manifest['version'] == 'v5-provisional-gemini-decision1'
    assert manifest['questions'] == s['questions'] and manifest['categories'] == s['categories']
    assert manifest['measured_models'] == len(models) == 38 and manifest['main_models'] == len(s['ranked_model_ids']) == 31
    for key in ['minimum_overall_accuracy','inclusion_threshold','superseded_model_ids']:
        assert manifest[key] == s[key],key
    assert manifest['replacement_decision'] == read(dest/'drex_comparison.json')['replacement_decision']
    ranked = sorted((k for k,v in models.items() if v['correct']*100 >= 45*1456 and k not in s['superseded_model_ids']),key=lambda k:(-models[k]['correct'],k))
    assert s['ranked_model_ids'] == ranked and len(ranked) == 31 and ranked.index(MID) == 19
    assert [k for k in ranked if k != MID] == old['ranked_model_ids'] and s['below_cutoff'] == old['below_cutoff'] and len(s['below_cutoff']) == 6
    assert (dest/'parent_d3_flash_audit_receipt.json').read_bytes() == (prior/'audit_receipt.json').read_bytes()
    receipt = read(dest/'audit_receipt.json')
    assert receipt['base_models_retained'] == 37 and receipt['models_added'] == [MID] and receipt['no_scored_retries'] and receipt['readiness_excluded']
    assert receipt['source_manifest_sha256'] == base.sha(prior/'manifest.json')
    for key in ['individual_timing_records','individual_cost_records','individual_correctness_records']:
        assert receipt[key] == 55328
    for name,h in receipt['unchanged_files_sha256'].items():
        assert base.sha(dest/name) == h == base.sha(prior/name),name
    for name,h in manifest['unchanged_files_sha256'].items():
        assert base.sha(dest/name) == h,name
    qslist = base.jsonlines(dest/'questions_1456.jsonl'); qs = {q['id']:q for q in qslist}
    assert len(qslist) == len(qs) == 1456
    families = collections.Counter(q['family_id'] for q in qslist)
    assert len(families) == 43 and families['F32'] == 20 and families['F33'] == 200
    tables = {}
    for name in ['timing_evidence.csv.gz','cost_evidence.csv.gz','correctness_evidence.csv.gz','all_category_scores.csv']:
        before = gzip.decompress((prior/name).read_bytes()) if name.endswith('.gz') else (prior/name).read_bytes()
        after = gzip.decompress((dest/name).read_bytes()) if name.endswith('.gz') else (dest/name).read_bytes()
        assert after.startswith(before),name
        rr = rows(dest/name); fields = ['model_id','family_id'] if name == 'all_category_scores.csv' else ['model_id','item_id']
        idx = {tuple(x[k] for k in fields):x for x in rr}; per = 43 if name == 'all_category_scores.csv' else 1456
        assert len(rr) == len(idx) == 38*per and set(rr[0]) == set(rows(prior/name)[0])
        assert {key[1] for key in idx if key[0] == MID} == (set(families) if per == 43 else set(qs))
        proof = receipt['csv_append_proofs'][name]
        assert proof['original_rows'] == 37*per and proof['appended_rows'] == per and proof['old_csv_bytes_exact_prefix']
        assert proof['original_uncompressed_sha256'] == hashlib.sha256(before).hexdigest()
        tables[name] = idx
    timing,cost,flags,cats = [tables[n] for n in ['timing_evidence.csv.gz','cost_evidence.csv.gz','correctness_evidence.csv.gz','all_category_scores.csv']]
    m = models[MID]; audit = read(dest/'gemini_decision1_model_audit.json')
    assert m['role'] == 'Hosted native' and m['n'] == m['valid'] == audit['n'] == audit['valid'] == 1456
    assert m['correct'] == audit['correct'] == 798 and audit['complete'] and audit['configuration_metadata_stable'] and audit['configuration_checks'] == 18
    assert audit['precision'] == 'unknown; not inferred BF16' and audit['declared_snapshot'] == SNAPSHOT and audit['provider'] == 'Google AI Studio'
    assert m['zero_generation_attested'] is False and audit['zero_generation_independently_attested'] is False and m['no_generated_reasoning_text_observed']
    assert m['raw_output_tokens'] == audit['raw_output_tokens'] == m['raw_usage_unknown_count'] == 0
    lat=[]; charges=[]
    for item,q in qs.items():
        t,c,f = timing[MID,item],cost[MID,item],flags[MID,item]
        assert t['family_id'] == c['family_id'] == f['family_id'] == q['family_id']
        assert t['input_sha256'] == c['input_sha256'] == q['native_input_sha256']
        assert t['source_record_sha256'] == c['source_record_sha256'] and re.fullmatch('[0-9a-f]{64}',t['source_record_sha256'])
        assert t['status'] == c['status'] == 'ok' and base.boolean(f['usable']) and t['output_counter'] == '0'
        assert t['collection_date_toronto'] == c['collection_date_toronto'] == '2026-11-12'
        assert c['evidence_kind'] == 'reported' and not c['tariff_estimate_usd']
        v = float(t['latency_ms']); assert math.isfinite(v) and v >= 0; lat.append(v)
        charge = Decimal(c['reported_usd']); assert charge.is_finite() and charge >= 0; charges.append(charge)
    assert sum(base.boolean(flags[MID,item]['correct']) for item in qs) == 798
    for key,val in [('accuracy',798/1456),('coverage',1),('answer_accuracy_among_usable',798/1456),('accuracy_upper_if_all_unusable_correct',798/1456)]:
        base.close(m[key],val)
    for key,val in [('mean_ms',statistics.mean(lat)),('median_ms',statistics.median(lat)),('p95_ms',base.q95(lat))]:
        base.close(m[key],val); base.close(audit[key],val)
    for fid,n in families.items():
        ids = [i for i,q in qs.items() if q['family_id'] == fid]; c = cats[MID,fid]
        assert int(c['n']) == n and int(c['correct']) == sum(base.boolean(flags[MID,i]['correct']) for i in ids)
        base.close(c['accuracy'],int(c['correct'])/n)
        vv = [float(timing[MID,i]['latency_ms']) for i in ids]
        for key,val in [('mean_ms',statistics.mean(vv)),('median_ms',statistics.median(vv)),('p95_ms',base.q95(vv))]: base.close(c[key],val)
    base.close(m['macro_category_accuracy'],statistics.mean(float(cats[MID,f]['accuracy']) for f in families))
    c = costs[MID]; total = sum(charges)
    assert total == Decimal('0.0797482') == Decimal(audit['reported_cost_usd']) and c['n'] == c['reported_count'] == audit['reported_charge_count'] == 1456
    assert all(c[k] == 0 for k in ['tariff_estimate_count','free_access_tariff_count','unknown_count','local_unmeasured_count'])
    assert c['estimate_only_subtotal_usd'] is None and Decimal(c['reported_subtotal_usd']) == Decimal(c['known_subtotal_usd']) == total
    assert Decimal(c['known_usd_per_1000']) == total/Decimal(1456)*1000
    assert audit['unknown_actual_charge_count'] == 0 and Decimal(audit['readiness_reported_cost_excluded_usd']) == Decimal('0.0000116')
    u = sorted(rows(dest/'gemini_decision1_usage_evidence.csv.gz'),key=lambda x:int(x['sequence']))
    assert len(u) == 1456 and {x['item_id'] for x in u} == set(qs) and [int(x['sequence']) for x in u] == list(range(1,1457))
    for x in u:
        item = x['item_id']; assert x['model_id'] == MID and x['attempt'] == '1' and x['http_status'] == '200' and x['output_tokens'] == '0'
        assert x['returned_model'] == SNAPSHOT and x['provider'] == 'Google AI Studio' and int(x['input_tokens']) > 0
        assert x['completed_at_utc'] == timing[MID,item]['collected_at_utc'] and x['input_sha256'] == qs[item]['native_input_sha256']
        assert x['source_record_sha256'] == timing[MID,item]['source_record_sha256'] and re.fullmatch('[0-9a-f]{64}',x['canonical_record_sha256'])
        assert Decimal(x['reported_usd']) == Decimal(cost[MID,item]['reported_usd'])
    assert sum(int(x['input_tokens']) for x in u) == audit['input_tokens'] == m['input_tokens'] == 797482
    assert digest([[x['item_id'],x['source_record_sha256']] for x in u]) == audit['source_record_digest'] == receipt['new_record_digest']
    analysis = read(dest/'gemini_decision1_analysis.json')
    assert analysis['correct'] == 798 and analysis['rank_among_release_active'] == 20 and analysis['active_cohort_n'] == 31
    assert len(analysis['categories']) == 43 and {x['family_id'] for x in analysis['categories']} == set(families)
    for x in analysis['categories']:
        c = cats[MID,x['family_id']]; assert x['n'] == int(c['n']) and x['correct'] == int(c['correct'])
        for k in ['accuracy','mean_ms','median_ms','p95_ms']: base.close(x[k],float(c[k]))
    assert set(analysis['matched_comparisons']) == set(old['models'])
    for mid,pair in analysis['matched_comparisons'].items():
        newgood = [base.boolean(flags[MID,i]['correct']) for i in qs]; oldgood = [base.boolean(flags[mid,i]['correct']) for i in qs]
        common = [i for i in qs if base.boolean(flags[mid,i]['usable'])]
        assert pair['n'] == 1456 and pair['correct'] == models[mid]['correct'] and pair['new_minus_reference_correct'] == 798-models[mid]['correct']
        assert pair['both_correct'] == sum(a and b for a,b in zip(newgood,oldgood))
        assert pair['new_only_correct'] == sum(a and not b for a,b in zip(newgood,oldgood)) and pair['reference_only_correct'] == sum(b and not a for a,b in zip(newgood,oldgood))
        assert pair['common_usable_n'] == len(common) and pair['new_correct_common_usable'] == sum(base.boolean(flags[MID,i]['correct']) for i in common)
    cr = rows(dest/'gemini_decision1_category_comparison.csv')
    assert len(cr) == len({(x['reference_model'],x['family_id']) for x in cr}) == 37*43
    for x in cr:
        mid,fid=x['reference_model'],x['family_id']
        assert mid in old['models'] and fid in families and int(x['n']) == families[fid]
        assert int(x['new_correct']) == int(cats[MID,fid]['correct']) and int(x['reference_correct']) == int(cats[mid,fid]['correct'])
        assert int(x['new_minus_reference_correct']) == int(x['new_correct'])-int(x['reference_correct'])
    page,md = (dest/'report.html').read_text(),(dest/'README_V5.md').read_text()
    assert page.index('src="comparison_accuracy.png"') < page.index('<div class="comparison-table">')
    section = re.search(r'<section id="gemini-update">(.*?)</section>',page,re.S).group(1)
    for phrase in ['54.81%','798/1,456','372.08','495.57','0.0797482','0.0000116','Precision is unknown','20261111','not independently attested']: assert phrase in section,phrase
    for text in ['rose','two-computer','Ryzen 7','Intel Core i7','6 GB','user-reported','unmetered','45%']: assert text in page and text in md,text
    assert f'ranking {ranked.index("d3_flash_9b_q4km_llamacpp_ctx4096_lan")+1}th among 31' in page
    assert f'ranks {ranked.index("singvl_s1_4b_q4km_llamacpp_ctx4096_lan")+1}th among the 31' in page
    desktop = re.search(r'<div class="comparison-table">.*?</table>',page,re.S).group()
    assert re.findall(r'data-overall-model="([^"]+)"',desktop) == ranked
    assert re.findall(r'<article class="mobile-card" data-overall-model="([^"]+)"',page) == ranked
    for mid in ranked:
        row = re.search(r'<tr data-overall-model="'+re.escape(mid)+r'">(.*?)</tr>',desktop,re.S).group(1)
        assert f'{models[mid]["accuracy"]:.2%}' in row
        assert re.findall(r'data-speed-band="([^"]+)"',row) == [str(base.band(models[mid][k],[250,500,1000])) for k in ['median_ms','p95_ms']]
        band = base.cost_band(costs[mid]); assert re.findall(r'data-cost-band="([^"]+)"',row) == ['unknown' if band is None else str(band)]*2
        assert html.escape(base.cost_label(costs[mid])) in row
    for kind in ['accuracy','latency','cost']:
        data = (dest/f'comparison_{kind}.png').read_bytes(); assert data[:8] == b'\x89PNG\r\n\x1a\n'
        w,h = struct.unpack('>II',data[16:24]); assert w >= 1300 and h >= 1600
    assert len(list(dest.glob('categories_*.svg'))) == 8
    for svg in [dest/'overview.svg']+list(dest.glob('comparison_*.svg'))+list(dest.glob('categories_*.svg')):
        text = svg.read_text(); assert '#b2364b' in text and 'rose two-computer local' in text and MID in text,svg
    for target in re.findall(r'(?:href|src)="([^"]+)"',page):
        u = urlsplit(html.unescape(target))
        if not u.scheme and not u.netloc and u.path: assert (dest/unquote(u.path)).exists(),target
    base.check_markdown_links(dest)
    for p in dest.rglob('*'):
        if p.is_file() and p.suffix not in ['.png','.svg']:
            data = gzip.decompress(p.read_bytes()) if p.name.endswith('.gz') else p.read_bytes()
            for forbidden in [b'/Users/',b'"choice":',b'"expected_answer"',b'"gold_answer"']: assert forbidden not in data,p
    if mirror:
        assert {str(p.relative_to(mirror)) for p in mirror.rglob('*') if p.is_file()} == {str(p.relative_to(dest)) for p in dest.rglob('*') if p.is_file()}
        for p in dest.rglob('*'):
            if p.is_file(): assert p.read_bytes() == (mirror/p.relative_to(dest)).read_bytes(),p
        base.check_markdown_links(mirror)
    print('PASS: Gemini798/1456;38complete/31active/6below/1superseded;55328individualrecords;all37priorobjects/prefixes;identity/cost/usage/pooledtiming/ranks/mirror verified.')

if __name__ == '__main__':
    p=argparse.ArgumentParser();p.add_argument('release',type=Path);p.add_argument('prior',type=Path);p.add_argument('--mirror',type=Path)
    a=p.parse_args();validate(a.release.resolve(),a.prior.resolve(),a.mirror.resolve() if a.mirror else None)
