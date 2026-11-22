"""Check the dated November 22 release and optional byte-exact Pages mirror."""
import argparse
import collections
import gzip
import hashlib
import html
import json
import math
import re
import statistics
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from zoneinfo import ZoneInfo

import validate_system1_v5_liquid12_2026_11_17 as predecessor
import validate_system1_v5_provisional_2026_11_09 as base

VERSION = 'v5-provisional-baseten-ms-deepseek'
N = 1456
CUTOFF = 656
FILES = ('timing_evidence.csv.gz', 'cost_evidence.csv.gz',
         'correctness_evidence.csv.gz', 'all_category_scores.csv')
SPECS = {
    'bison1': ('baseten/bison-1', 'baseten/bison-1-20261120', 'BaseTen', 'baseten', 'mammoth1'),
    'groundhog1': ('baseten/groundhog-1', 'baseten/groundhog-1-20261120', 'BaseTen', 'baseten', 'elephant1'),
    'microsoft_decision11': ('microsoft/microsoft-decision-1.1', 'microsoft/microsoft-decision-1.1-20261117',
                             'Azure', 'azure', 'microsoft_decision'),
    'reference_deepseek41_flash1017': ('deepseek/deepseek-v4.1-flash-1017',
                                     'deepseek/deepseek-v4.1-flash-20261017',
                                     'DeepInfra', 'deepinfra/fp8', 'reference_terra61'),
}
CHAT = 'reference_deepseek41_flash1017'
HASH = re.compile(r'[0-9a-f]{64}')


def bytes_of(path):
    return gzip.decompress(path.read_bytes()) if path.suffix == '.gz' else path.read_bytes()


def payload_digest(mid, q):
    alias, _, _, tag, _ = SPECS[mid]
    routing = {'only': [tag], 'allow_fallbacks': False, 'require_parameters': True}
    if mid == CHAT:
        options = '\n'.join(f'{i}. {opt}' for i, opt in enumerate(q['options'], 1))
        prompt = '\n\n'.join((q['instructions'], q['context'], q['question'], options,
                              'Return only the numeric option ID (1, 2, 3, 4 or 5), without explanation.'))
        payload = {'model': alias, 'provider': routing, 'messages': [{'role': 'user', 'content': prompt}],
                   'max_tokens': 16, 'stream': False, 'usage': {'include': True}, 'service_tier': 'default',
                   'reasoning': {'enabled': False, 'effort': 'none'}}
    else:
        payload = {'model': alias, 'provider': routing, **q['native_input']}
    return hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True, allow_nan=False,
                                     separators=(',', ':')).encode()).hexdigest()


def read_table(dest, prior, receipt, name, model_ids, keys):
    before = bytes_of(prior / name)
    assert bytes_of(dest / name).startswith(before), name
    rows = base.rows(dest / name)
    by_model = collections.defaultdict(dict)
    dimension = 'family_id' if name == FILES[3] else 'item_id'
    for row in rows:
        mid, item = row['model_id'], row[dimension]
        assert item not in by_model[mid], (name, mid, item)
        by_model[mid][item] = row
    assert set(by_model) == model_ids and all(set(r) == keys for r in by_model.values()), name
    proofs = receipt['csv_append_proofs'][name]
    assert proofs == {'original_rows': 46 * len(keys), 'appended_rows': (len(model_ids) - 46) * len(keys),
                      'old_csv_bytes_exact_prefix': True,
                      'original_uncompressed_sha256': hashlib.sha256(before).hexdigest()}
    return by_model


def validate_pair(pair, one, two):
    assert set(one) == set(two)
    mask = [k for k in one if one[k][0] and two[k][0]]
    outcomes = collections.Counter((one[k][1], two[k][1]) for k in one)
    assert pair == {'n': len(one), 'both_correct': outcomes[True, True],
                    'new_only_correct': outcomes[True, False], 'reference_only_correct': outcomes[False, True],
                    'neither_correct': outcomes[False, False], 'commonly_usable': len(mask),
                    'new_correct_on_common': sum(one[k][1] for k in mask),
                    'reference_correct_on_common': sum(two[k][1] for k in mask)}


def validate(dest, prior, mirror=None, validate_parent=True):
    repo = Path(__file__).resolve().parents[1]
    if validate_parent:
        predecessor.validate(prior, repo/'results/releases/system1_v5_nimble_subq_2026-11-15')
    manifest = base.check_manifest(dest)
    assert manifest['version'] == VERSION
    assert manifest['frozen_liquid12_v5_manifest_sha256'] == base.sha(prior/'manifest.json')
    expected_scripts = {'scripts/publish_system1_v5_baseten_ms_deepseek_2026_11_22.py',
                        'scripts/validate_system1_v5_baseten_ms_deepseek_2026_11_22.py'}
    assert set(manifest['source_files_sha256']) == expected_scripts
    for name, digest in manifest['source_files_sha256'].items():
        assert base.sha(repo / name) == digest
    old = base.load(prior/'statistics.json')
    stats = base.load(dest/'statistics.json')
    models = stats['models']
    new = models.keys() - old['models'].keys()
    assert new and new <= SPECS.keys() and len(old['models']) == 46
    assert stats['version'] == VERSION and stats['questions'] == N and stats['categories'] == 43
    assert stats['inclusion_threshold'] == old['inclusion_threshold']
    assert stats['minimum_overall_accuracy'] == old['minimum_overall_accuracy'] == .45
    assert stats['inclusion_threshold']['minimum_correct'] == CUTOFF
    costs = base.load(dest/'cost_statistics.json')['models']
    old_costs = base.load(prior/'cost_statistics.json')['models']
    assert set(models) == set(costs)
    assert all(models[k] == v and costs[k] == old_costs[k] for k,v in old['models'].items())
    superseded = old['superseded_model_ids'] + (['microsoft_decision'] if 'microsoft_decision11' in new else [])
    ranked = sorted((k for k,v in models.items() if v['correct'] >= CUTOFF and k not in superseded),
                    key=lambda k:(-models[k]['correct'], k))
    below = sorted((k for k,v in models.items() if v['correct'] < CUTOFF and k not in superseded),
                   key=lambda k:(-models[k]['correct'], k))
    assert (stats['ranked_model_ids'], stats['below_cutoff'], stats['superseded_model_ids']) == (ranked, below, superseded)
    for field in ('questions','categories','minimum_overall_accuracy','inclusion_threshold','superseded_model_ids'):
        assert manifest[field] == stats[field]
    assert manifest['measured_models'] == len(models) and manifest['main_models'] == len(ranked)
    assert manifest['partial_screen_models'] == 3 and manifest['partial_records_per_ledger'] == 300
    for name in ('manifest.json','audit_receipt.json'):
        assert (dest / f'parent_liquid12_{name}').read_bytes() == (prior / name).read_bytes()
    receipt = base.load(dest/'audit_receipt.json')
    assert receipt['status'] == 'pass' and receipt['readiness_excluded'] is True and receipt['no_scored_retries'] is True
    assert set(receipt['models_added']) == new and receipt['base_models_retained'] == 46
    assert receipt['source_manifest_sha256'] == base.sha(prior/'manifest.json')
    assert HASH.fullmatch(receipt['source_measurement_summary_sha256']) and HASH.fullmatch(receipt['approval_sha256'])
    if new == SPECS.keys():
        reviews = receipt['independent_raw_review_sha256']
        assert set(reviews) == {'deepseek','native'} and all(HASH.fullmatch(h) for h in reviews.values())
        assert HASH.fullmatch(receipt['source_matched_results_sha256'])
    for label in ('timing','cost','correctness'):
        assert receipt[f'individual_{label}_records'] == len(models) * N
    assert (receipt['measured_configurations'], receipt['main_configurations'],
            receipt['below_cutoff_configurations'], receipt['superseded_configurations']) == (
           len(models), len(ranked), len(below), len(superseded))
    mutable = {*FILES, 'statistics.json', 'cost_statistics.json', 'manifest.json',
               'audit_receipt.json', 'README_V5.md', 'V5_SELECTION_NOTES.md', 'report.html'}
    protected = {str(p.relative_to(prior)) for p in prior.rglob('*')
                 if p.is_file() and p.suffix not in ('.png','.svg') and p.name not in mutable}
    assert protected == set(receipt['unchanged_files_sha256'])
    assert manifest['unchanged_files_sha256'] == receipt['unchanged_files_sha256']
    for name, digest in receipt['unchanged_files_sha256'].items():
        assert base.sha(prior/name) == base.sha(dest/name) == digest, name
    questions = {q['id']:q for q in base.jsonlines(dest/'questions_1456.jsonl')}
    groups = collections.defaultdict(list)
    for q in questions.values():
        groups[q['family_id']].append(q['id'])
    assert len(questions) == N and len(groups) == 43 and len(groups['F33']) == 200
    timing, fees, flags, cats = (
        read_table(dest, prior, receipt, name, set(models), set(groups) if name == FILES[3] else set(questions))
        for name in FILES)
    usable_correct = {mid:{k:(base.boolean(r['usable']),base.boolean(r['correct'])) for k,r in rr.items()}
                      for mid,rr in flags.items()}
    audits = base.load(dest/'nov22_model_audits.json')
    pairs = base.load(dest/'nov22_paired_comparisons.json')
    evidence = collections.defaultdict(dict)
    for row in base.rows(dest/'nov22_usage_evidence.csv.gz'):
        assert row['item_id'] not in evidence[row['model_id']]
        evidence[row['model_id']][row['item_id']] = row
    assert set(audits) == set(pairs) == set(evidence) == new
    for mid in new:
        alias, snapshot, vendor, tag, ref = SPECS[mid]
        a,m,c = audits[mid],models[mid],costs[mid]
        assert type(a['workers_per_model']) is int and a['workers_per_model'] >= 1
        assert a['first_primaries_only'] is True and a['scored_retries'] == 0 and a['readiness_excluded'] is True
        for key in ('source_item_evidence_sha256','run_manifest_sha256','readiness_sha256'):
            assert HASH.fullmatch(a[key])
        if mid == CHAT:
            assert a['precision'].casefold() == 'fp8'
        assert (a['requested_model'],a['declared_snapshot'],a['provider'],a['provider_tag']) == (alias,snapshot,vendor,tag)
        expected_api = 'https://openrouter.ai/api/v1/chat/completions' if mid == CHAT else 'https://openrouter.ai/api/alpha/decisions'
        assert a['route'] == expected_api
        assert m['role'] == ('LLM reference' if mid == CHAT else 'Hosted native')
        u_by_item = evidence[mid]
        assert set(u_by_item) == set(questions)
        assert {int(r['sequence']) for r in u_by_item.values()} == set(range(1,N+1))
        kinds = collections.Counter()
        statuses = collections.Counter()
        identities = collections.Counter()
        invalid_finish = collections.Counter()
        timestamps = collections.Counter()
        latencies = {}
        amounts = {'reported':Decimal(0), 'tariff_estimate':Decimal(0)}
        own = usable_correct[mid]
        for item,q in questions.items():
            t,fee,f,u = timing[mid][item],fees[mid][item],flags[mid][item],u_by_item[item]
            ok,right = own[item]
            assert not right or ok
            assert t['family_id'] == fee['family_id'] == f['family_id'] == u['family_id'] == q['family_id']
            assert t['input_sha256'] == fee['input_sha256'] == u['input_sha256'] == q['native_input_sha256']
            assert t['source_record_sha256'] == fee['source_record_sha256'] == u['source_record_sha256']
            assert HASH.fullmatch(t['source_record_sha256']) and payload_digest(mid,q) == u['payload_sha256']
            assert not u['raw_response_sha256'] or HASH.fullmatch(u['raw_response_sha256'])
            assert t['status'] == fee['status'] == u['status'] and (u['status'] == 'ok') == ok
            assert (u['requested_model'],u['provider_tag'],u['route'],u['attempt']) == (alias,tag,expected_api,'1')
            status = u['status']
            statuses[status] += 1
            assert status in {'ok','invalid_output','transport_failure','http_failure'}
            if status in {'ok','invalid_output'}:
                assert u['http_status']=='200' and u['provider'].casefold()==vendor.casefold()
                assert u['returned_model'] in ((alias,snapshot) if mid == CHAT else (snapshot,))
                identities[u['returned_model']] += 1
                if mid == CHAT:
                    assert u['reasoning_tokens']=='0' and not base.boolean(u['reasoning_text_present'])
                    if status == 'invalid_output':
                        invalid_finish[u['finish_reason'] or 'None'] += 1
                    else:
                        assert u['finish_reason'] == 'stop'
            assert u['reasoning_requested'] == ('none' if mid == CHAT else '')
            assert u['output_tokens'] == t['output_counter']
            for key in ('input_tokens','output_tokens','reasoning_tokens'):
                assert not u[key] or u[key].isdigit(), (mid,item,key)
            assert t['collected_at_utc'] == u['collected_at_utc']
            done = datetime.fromisoformat(t['collected_at_utc'].replace('Z','+00:00'))
            assert done.utcoffset().total_seconds() == 0
            day = done.astimezone(ZoneInfo('America/Toronto')).date().isoformat()
            assert t['collection_date_toronto'] == fee['collection_date_toronto'] == day
            timestamps[day] += 1
            latencies[item] = seconds = float(t['latency_ms'])
            assert math.isfinite(seconds) and seconds >= 0
            kind = fee['evidence_kind']
            assert kind in {'reported','tariff_estimate','unknown'}
            assert (fee['reported_usd'],fee['tariff_estimate_usd'],kind) == (
                    u['reported_usd'],u['tariff_estimate_usd'],u['cost_kind'])
            assert bool(fee['reported_usd']) == (kind=='reported')
            assert bool(fee['tariff_estimate_usd']) == (kind=='tariff_estimate')
            kinds[kind] += 1
            if kind in amounts:
                amount = Decimal(fee['reported_usd'] or fee['tariff_estimate_usd'])
                assert amount.is_finite() and amount >= 0
                amounts[kind] += amount
        valid, right = sum(ok for ok,right in own.values()),sum(right for ok,right in own.values())
        assert a['n'] == m['n'] == N and a['correct'] == m['correct'] == right and a['usable'] == m['valid'] == valid
        assert m['new_request_failures'] == N-valid
        assert (a['statuses'],a['returned_model_counts'],a['invalid_finish_reasons']) == tuple(map(dict,(statuses,identities,invalid_finish)))
        assert a['collection_dates_toronto'] == m['collection_dates_toronto'] == dict(timestamps)
        for key,value in [('accuracy',right/N),('coverage',valid/N),('accuracy_upper_if_all_unusable_correct',(right+N-valid)/N)]:
            base.close(m[key],value)
        if valid:
            base.close(m['answer_accuracy_among_usable'],right/valid)
        else:
            assert m['answer_accuracy_among_usable'] is None
        for key,fn in [('mean_ms',statistics.mean),('median_ms',statistics.median),('p95_ms',base.q95)]:
            base.close(m[key],fn(latencies.values()))
            base.close(a[key],fn(latencies.values()))
        for family,items in groups.items():
            cr = cats[mid][family]
            total = len(items)
            correct = sum(own[item][1] for item in items)
            assert (int(cr['n']),int(cr['correct'])) == (total,correct)
            base.close(cr['accuracy'],correct/total)
            values = [latencies[item] for item in items]
            for key,fn in [('mean_ms',statistics.mean),('median_ms',statistics.median),('p95_ms',base.q95)]:
                base.close(cr[key],fn(values))
        base.close(m['macro_category_accuracy'],statistics.mean(float(x['accuracy']) for x in cats[mid].values()))
        assert c == a['cost_summary'] and c['n'] == N and c['model_id'] == mid
        assert (c['reported_count'],c['tariff_estimate_count'],c['unknown_count']) == (
                kinds['reported'],kinds['tariff_estimate'],kinds['unknown'])
        assert c['actual_charge_unknown_count'] == N-kinds['reported']
        assert c['local_unmeasured_count'] == c['free_access_tariff_count'] == 0
        expected_total = sum(amounts.values(),Decimal(0)) if kinds['reported'] or kinds['tariff_estimate'] else None
        money_fields = [('reported_subtotal_usd',amounts['reported'] if kinds['reported'] else None),
                        ('estimate_only_subtotal_usd',amounts['tariff_estimate'] if kinds['tariff_estimate'] else None),
                        ('known_subtotal_usd',expected_total),
                        ('known_usd_per_1000',expected_total/Decimal(N)*1000 if expected_total is not None else None)]
        for key,value in money_fields:
            assert (Decimal(c[key]) if c[key] is not None else None) == value, (mid,key)
        assert a['raw_output_tokens'] == sum(int(x['output_tokens'] or '0') for x in u_by_item.values())
        assert a['known_output_counter_count'] == sum(bool(x['output_tokens']) for x in u_by_item.values())
        assert a['reported_zero_reasoning_count'] == sum(x['reasoning_tokens']=='0' for x in u_by_item.values())
        assert a['nonzero_reasoning_count'] == sum(x['reasoning_tokens'] not in ('0','') for x in u_by_item.values())
        assert a['reasoning_text_count'] == sum(base.boolean(x['reasoning_text_present']) for x in u_by_item.values())
        assert pairs[mid]['primary_reference'] == ref
        analyses = pairs[mid]['all_measured_pairs']
        assert set(analyses) == set(models)-{mid}
        for other,table in analyses.items():
            validate_pair(table, own, usable_correct[other])
    page = (dest/'report.html').read_text()
    assert '<section id="nov22-update">' in page and 'November 17 snapshot: Liquid d1.2' in page
    assert '<section id="asus-native-screens">' in page
    match = re.search(r'<section id="nov22-update">(.*?)</section>',page,re.S)
    for mid in new:
        m=models[mid]
        assert html.escape(m['label']) in match[1] and f"{m['correct']:,}/1,456 ({m['accuracy']:.2%})" in match[1]
    if CHAT in new:
        assert 'Accuracy on usable' in match[1] and (f"{models[CHAT]['answer_accuracy_among_usable']:.2%}" in match[1]
                                                     if models[CHAT]['valid'] else 'Unavailable' in match[1])
        assert f"{audits[CHAT]['statuses'].get('invalid_output',0):,} primaries failed the answer format" in match[1]
    assert set(re.findall(r'<article class="mobile-card" data-overall-model="([^"]+)"',page)) == set(ranked)
    for n in ('comparison_accuracy','comparison_latency','comparison_cost'):
        assert f'src="{n}.png"' in page and (dest/(n+'.svg')).is_file()
    for p in dest.glob('nov22*.json'):
        assert not re.search(r'/Users/|OPENROUTER_API_KEY|sk-or-v1-|"choice"\s*:',p.read_text())
    base.check_markdown_links(dest)
    if mirror:
        assert base.check_manifest(mirror) == manifest
        assert (mirror/'manifest.json').read_bytes() == (dest/'manifest.json').read_bytes()
    print(f'PASS: {len(models)} complete, {len(ranked)} active, {len(new)*N:,} new first primaries; '
          'historical prefixes, paired outcomes, exact cutoff, charges, payloads and reasoning telemetry verify.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('release',type=Path)
    parser.add_argument('parent',type=Path)
    parser.add_argument('--mirror',type=Path)
    args = parser.parse_args()
    validate(args.release,args.parent,args.mirror)
