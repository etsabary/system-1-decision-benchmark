"""Validate versioned native Drex against the immutable hosted v5 release."""
import argparse
import collections
import gzip
import hashlib
import html
import json
import math
import re
import statistics
import struct
from decimal import Decimal
from datetime import datetime
from pathlib import Path
from urllib.parse import unquote, urlsplit

import validate_system1_v5_provisional_2026_11_09 as base
import validate_system1_v5_hosted_2026_11_09 as hosted


MID = 'drex_max_v11'
OLD = 'drex_max'


def validate(dest, prior, mirror=None):
    repo = Path(__file__).resolve().parents[1]
    hosted.validate(prior, repo / 'results/releases/system1_v5_provisional_2026-11-09')
    manifest = base.check_manifest(dest)
    assert manifest['frozen_hosted_v5_manifest_sha256'] == base.sha(prior / 'manifest.json')
    assert manifest['questions'] == 1456 and manifest['categories'] == 43
    assert 'v5' in manifest['version'].lower()
    old, new = base.load(prior / 'statistics.json'), base.load(dest / 'statistics.json')
    old_costs = base.load(prior / 'cost_statistics.json')['models']
    costs = base.load(dest / 'cost_statistics.json')['models']
    assert len(old['models']) == 34 and len(new['models']) == 35
    assert set(new['models']) == set(old['models']) | {MID}
    assert set(costs) == set(new['models'])
    assert new['questions'] == 1456 and new['categories'] == 43
    assert new['minimum_overall_accuracy'] == .45 and new['inclusion_threshold'] == old['inclusion_threshold']
    assert all(new['models'][mid] == model and costs[mid] == old_costs[mid] for mid, model in old['models'].items())
    for name in ['questions_1456.jsonl', 'source_metadata_1456.jsonl', 'category_guide.json',
                 'selection_provenance.json', 'removed_items.csv', 'retained_items.csv',
                 'removed_correctness_evidence.csv.gz', 'SOURCE_AND_LICENSES.md', 'PROJECT_LICENSE_MIT.txt',
                 'native_currency_cost_evidence.csv.gz', 'fx_receipt.json', 'hosted_model_audits.json',
                 'partial_models.json', 'KAI_CASE_NOTE.md', 'STRIKE_SCREEN_NOTES.md', 'LOCAL_SCREEN_NOTES.md',
                 'NEW_LOCAL_SCREEN_NOTES.md', 'OPENAI_DECISIONS_NOTES.md']:
        assert (dest / name).read_bytes() == (prior / name).read_bytes(), name
    for path in (prior / 'third_party_licenses').iterdir():
        assert (dest / 'third_party_licenses' / path.name).read_bytes() == path.read_bytes()
    assert (dest / 'parent_hosted_audit_receipt.json').read_bytes() == (prior / 'audit_receipt.json').read_bytes()
    receipt = base.load(dest / 'audit_receipt.json')
    assert receipt['source_release'] == prior.name and receipt['source_manifest_sha256'] == base.sha(prior / 'manifest.json')
    assert receipt['base_models_retained'] == 34 and receipt['models_added'] == [MID]
    assert receipt['prior_primary_rows_and_objects_unchanged'] and receipt['no_scored_retries']
    assert receipt['zero_generation_attested'] is False and receipt['nonzero_output_counters_preserved']
    for key in ['individual_timing_records', 'individual_cost_records', 'individual_correctness_records']:
        assert receipt[key] == 35 * 1456
    for name, digest in receipt['unchanged_files_sha256'].items():
        assert base.sha(dest / name) == digest == base.sha(prior / name), name

    question_rows = base.jsonlines(dest / 'questions_1456.jsonl')
    questions = {q['id']: q for q in question_rows}
    assert len(questions) == len(question_rows) == 1456
    families = collections.Counter(q['family_id'] for q in questions.values())
    assert len(families) == 43 and min(families.values()) > 0
    assert families['F32'] == 20 and families['F33'] == 200
    ledgers = {}
    for name in ['timing_evidence.csv.gz', 'cost_evidence.csv.gz', 'correctness_evidence.csv.gz', 'all_category_scores.csv']:
        before = gzip.decompress((prior / name).read_bytes()) if name.endswith('.gz') else (prior / name).read_bytes()
        after = gzip.decompress((dest / name).read_bytes()) if name.endswith('.gz') else (dest / name).read_bytes()
        assert after.startswith(before), ('Historical CSV bytes changed', name)
        fields = ('model_id', 'family_id') if name == 'all_category_scores.csv' else ('model_id', 'item_id')
        rows, index = hosted.indexed(dest / name, fields)
        expected_fields = set(base.rows(prior / name)[0])
        assert all(set(row) == expected_fields for row in rows), ('Unexpected public columns', name)
        per_model = 43 if name == 'all_category_scores.csv' else 1456
        assert len(rows) == len(index) == 35 * per_model
        assert sum(row['model_id'] == MID for row in rows) == per_model
        proof = receipt['csv_append_proofs'][name]
        assert proof['original_rows'] == 34 * per_model and proof['appended_rows'] == per_model
        assert proof['old_csv_bytes_exact_prefix']
        assert proof['original_uncompressed_sha256'] == hashlib.sha256(before).hexdigest()
        ledgers[name] = rows, index
    timing = ledgers['timing_evidence.csv.gz'][1]
    cost_rows, cost_index = ledgers['cost_evidence.csv.gz']
    flags = ledgers['correctness_evidence.csv.gz'][1]
    categories = ledgers['all_category_scores.csv'][1]
    m, audit = new['models'][MID], base.load(dest / 'drex_model_audit.json')
    assert m['n'] == audit['n'] == 1456 and audit['complete']
    assert audit['model_id'] == MID and m['role'] == 'Hosted native'
    correct = sum(base.boolean(flags[MID, item]['correct']) for item in questions)
    usable = sum(base.boolean(flags[MID, item]['usable']) for item in questions)
    assert correct == m['correct'] == audit['correct'] and usable == m['valid'] == audit['valid']
    assert m['new_request_failures'] == 1456 - usable
    base.close(m['accuracy'], correct / 1456)
    base.close(m['coverage'], usable / 1456)
    base.close(m['answer_accuracy_among_usable'], correct / usable if usable else 0)
    base.close(m['accuracy_upper_if_all_unusable_correct'], (correct + 1456 - usable) / 1456)
    values = []
    for item, q in questions.items():
        t, c, f = timing[MID, item], cost_index[MID, item], flags[MID, item]
        assert t['family_id'] == c['family_id'] == f['family_id'] == q['family_id']
        assert t['input_sha256'] == c['input_sha256'] == q['native_input_sha256']
        assert t['source_record_sha256'] == c['source_record_sha256']
        assert re.fullmatch('[0-9a-f]{64}', t['source_record_sha256'])
        assert t['status'] == c['status']
        assert base.boolean(f['usable']) == (t['status'] == 'ok')
        assert not base.boolean(f['correct']) or base.boolean(f['usable'])
        latency = float(t['latency_ms'])
        assert math.isfinite(latency) and latency >= 0
        values.append(latency)
    for field, expected in [('mean_ms', statistics.mean(values)), ('median_ms', statistics.median(values)), ('p95_ms', base.q95(values))]:
        base.close(m[field], expected)
        base.close(audit[field], expected)
    assert m['collection_dates_toronto'] == dict(collections.Counter(timing[MID, item]['collection_date_toronto'] for item in questions))
    for fid, count in families.items():
        ids = [item for item, q in questions.items() if q['family_id'] == fid]
        row = categories[MID, fid]
        assert int(row['n']) == count
        assert int(row['correct']) == sum(base.boolean(flags[MID, item]['correct']) for item in ids)
        base.close(row['accuracy'], int(row['correct']) / count)
        values = [float(timing[MID, item]['latency_ms']) for item in ids]
        for field, expected in [('mean_ms', statistics.mean(values)), ('median_ms', statistics.median(values)), ('p95_ms', base.q95(values))]:
            base.close(row[field], expected)
    base.close(m['macro_category_accuracy'], statistics.mean(float(categories[MID, fid]['accuracy']) for fid in families))

    usage_rows, usage = hosted.indexed(dest / 'drex_usage_evidence.csv.gz', ('model_id', 'item_id'))
    assert set(usage_rows[0]) == {'model_id', 'item_id', 'family_id', 'input_sha256', 'status', 'source_record_sha256',
                                  'sequence', 'attempt', 'input_tokens', 'output_tokens', 'http_status', 'effective_model'}
    assert len(usage_rows) == 1456 and set(usage) == {(MID, item) for item in questions}
    c = costs[MID]
    assert c['n'] == c['api_unknown_charge_count'] == 1456
    assert c['api_reported_charge_count'] == c['reported_count'] == c['free_access_tariff_count'] == c['local_unmeasured_count'] == 0
    assert c['reported_subtotal_usd'] is None and c['captured_input_tariff_usd_per_million'] == '0.03'
    assert c['cost_basis'] == 'captured_input_tariff_estimate' and c['output_billable'] is False
    estimate, input_tokens, output_tokens, nonzero, unknown = Decimal(0), 0, 0, 0, 0
    http_counts, sequences, limited = collections.Counter(), set(), set()
    for u in usage_rows:
        item = u['item_id']
        t, cost, f = timing[MID, item], cost_index[MID, item], flags[MID, item]
        for field in ['family_id', 'input_sha256', 'source_record_sha256', 'status']:
            assert u[field] == t[field] == cost[field]
        assert u['attempt'] == '1'
        sequences.add(int(u['sequence']))
        assert not cost['reported_usd']
        http_counts[u['http_status']] += 1
        if u['http_status'] == '429':
            limited.add(item)
            assert not base.boolean(f['usable']) and not base.boolean(f['correct'])
        if base.boolean(f['usable']):
            assert u['effective_model'] == 'drex-max-v1.1'
            assert u['http_status'] == '200'
            assert u['input_tokens'] and u['output_tokens']
        if u['input_tokens']:
            tokens = int(u['input_tokens'])
            assert tokens >= 0
            expected = Decimal(tokens) * Decimal('.03') / Decimal(1000000)
            assert cost['evidence_kind'] == 'tariff_estimate' and Decimal(cost['tariff_estimate_usd']) == expected
            estimate += expected
            input_tokens += tokens
        else:
            assert cost['evidence_kind'] == 'unknown' and not cost['tariff_estimate_usd']
            unknown += 1
        assert u['output_tokens'] == t['output_counter']
        if u['output_tokens']:
            output = int(u['output_tokens'])
            assert output >= 0
            output_tokens += output
            nonzero += output > 0
    assert len(sequences) == 1456 and min(sequences) in (0, 1)
    assert max(sequences) - min(sequences) == 1455
    assert len(limited) >= 2 and sum(http_counts.values()) == 1456
    assert dict(http_counts) == audit['http_status_counts']
    source_records = [[u['item_id'], u['source_record_sha256']] for u in sorted(usage_rows, key=lambda row: int(row['sequence']))]
    source_digest = hashlib.sha256(json.dumps(source_records, sort_keys=True, ensure_ascii=False, separators=(',', ':'), allow_nan=False).encode()).hexdigest()
    assert source_digest == audit['source_record_digest'] == receipt['new_record_digest']
    assert c['tariff_estimate_count'] == 1456 - unknown and c['unknown_count'] == unknown == audit['unknown_estimated_cost_count']
    assert Decimal(c['estimate_only_subtotal_usd']) == Decimal(c['known_subtotal_usd']) == Decimal(audit['tariff_estimate_usd']) == estimate
    assert Decimal(c['known_usd_per_1000']) == estimate * 1000 / 1456
    assert input_tokens == audit['input_tokens'] == m['input_tokens']
    assert output_tokens == audit['raw_output_tokens'] == m['raw_output_tokens']
    assert nonzero == audit['nonzero_output_counter_responses'] == m['nonzero_output_counter_responses']
    assert nonzero > 0 and m['zero_generation_attested'] is False and audit['zero_generation_attested'] is False
    assert m['no_generated_reasoning_text_observed'] and audit['no_generated_reasoning_text_observed']
    policy = base.load(dest / 'drex_counter_policy.json')
    assert policy['zero_required'] is False and policy['zero_generation_attested'] is False
    assert policy['native_choice_scored_without_argmax_substitution'] and policy['no_generated_reasoning_text_observed']
    assert policy['raw_output_tokens'] == output_tokens and policy['nonzero_output_counter_responses'] == nonzero
    assert policy['current_official_docs'] and re.fullmatch('[0-9a-f]{64}', policy['historical_policy_code_sha256'])
    provenance = base.load(dest / 'drex_version_provenance.json')
    assert provenance['model_id'] == MID and provenance['requested_model'] == 'drex-max-v1.1'
    assert provenance['provider'] == 'Nace native' and provenance['catalogue_declared_release_date'] == '2026-10-28'
    assert provenance['catalogue_model_entry']['name'] == 'drex-max-v1.1'
    assert provenance['catalogue_model_entry']['release_date'] == '2026-10-28'
    assert provenance['previous_model_id'] == OLD and provenance['previous_declared_checkpoint'] == 'nace-ai/drex-max-20261016'
    assert provenance['new_manifest_sha256'] == audit['manifest_sha256'] == receipt['new_manifest_sha256']
    assert audit['plan_sha256'] == receipt['new_plan_sha256']
    phases = base.load(dest / 'drex_transport_phases.json')
    assert phases['initial_concurrency'] == 2 and phases['initial_results'] == 322
    assert set(phases['retained_no_answer_http429_records']) == limited
    assert phases['amendment_proof_hashes']
    assert 'unattempted' in phases['continuation'].lower() and 'pacing' in phases['scope'].lower()
    assert phases['pause_after_sequence'] == 582 and phases['resume_first_sequence'] == 583
    assert phases['pause_reason'] == 'billing_check'
    assert phases['continuation_start_interval_seconds'] == .65
    assert phases['public_free_rate_limit_rpm'] == 120
    expected_phases = [(1, 322, 2), (323, 582, 1), (583, 1456, 1)]
    assert len(phases['phases']) == len(expected_phases)
    for phase, (first, last, workers) in zip(phases['phases'], expected_phases):
        assert phase['first_sequence'] == first and phase['last_sequence'] == last
        assert phase['requests'] == last - first + 1 and phase['workers'] == workers
        assert phase['global_start_interval_seconds'] == (None if workers == 2 else .65)
        group = [u for u in usage_rows if first <= int(u['sequence']) <= last]
        assert len(group) == phase['requests']
        latencies = [float(timing[MID, u['item_id']]['latency_ms']) for u in group]
        for field, expected in [('mean_ms', statistics.mean(latencies)), ('median_ms', statistics.median(latencies)), ('p95_ms', base.q95(latencies))]:
            base.close(phase[field], expected)
        assert phase['sum_recorded_dispatch_wait_ms'] >= 0
        assert phase['first_started_utc'] == min(timing[MID, u['item_id']]['collected_at_utc'] for u in group)
    started = datetime.fromisoformat(phases['collection_started_utc'])
    completed = datetime.fromisoformat(phases['collection_completed_utc'])
    base.close(phases['full_collection_wall_ms_including_pauses'], (completed - started).total_seconds() * 1000)
    assert phases['collection_started_utc'] == phases['phases'][0]['first_started_utc']
    assert phases['collection_completed_utc'] == phases['phases'][-1]['last_completed_utc']
    assert 'not model throughput' in phases['wallclock_interpretation'].lower()

    comp = base.load(dest / 'drex_comparison.json')
    assert comp['n'] == 1456 and comp['old']['model_id'] == OLD and comp['new']['model_id'] == MID
    for side, model in [('old', old['models'][OLD]), ('new', m)]:
        for field in ['correct', 'valid', 'accuracy', 'mean_ms', 'median_ms', 'p95_ms', 'collection_dates_toronto']:
            assert comp[side][field] == model[field]
    counts = collections.Counter((base.boolean(flags[OLD, item]['correct']), base.boolean(flags[MID, item]['correct'])) for item in questions)
    assert comp['both_correct'] == counts[True, True] and comp['both_incorrect'] == counts[False, False]
    assert comp['new_only_correct'] == counts[False, True] and comp['old_only_correct'] == counts[True, False]
    assert comp['correct_difference'] == m['correct'] - old['models'][OLD]['correct'] == comp['new_only_correct'] - comp['old_only_correct']
    base.close(comp['accuracy_difference_percentage_points'], 100 * comp['correct_difference'] / 1456)
    base.close(comp['median_difference_ms'], m['median_ms'] - old['models'][OLD]['median_ms'])
    base.close(comp['median_ratio'], m['median_ms'] / old['models'][OLD]['median_ms'])
    base.close(comp['p95_difference_ms'], m['p95_ms'] - old['models'][OLD]['p95_ms'])
    assert comp['old']['known_reported_cost_usd'] == old_costs[OLD]['reported_subtotal_usd']
    assert comp['old']['unknown_charge_count'] == old_costs[OLD]['unknown_count']
    assert Decimal(comp['new_estimate_to_old_known_reported_cost_ratio']) == estimate / Decimal(old_costs[OLD]['reported_subtotal_usd'])
    assert Decimal(comp['new']['tariff_estimate_usd']) == estimate
    assert comp['new']['unknown_estimated_cost_count'] == unknown and comp['new']['api_unknown_charge_count'] == 1456
    both_usable = [item for item in questions if base.boolean(flags[OLD, item]['usable']) and base.boolean(flags[MID, item]['usable'])]
    assert comp['both_usable_n'] == len(both_usable)
    assert comp['new_correct_on_both_usable'] == sum(base.boolean(flags[MID, item]['correct']) for item in both_usable)
    assert comp['old_correct_on_both_usable'] == sum(base.boolean(flags[OLD, item]['correct']) for item in both_usable)
    assert receipt['replacement_decision'] in {'supersede', 'retain'}
    superseded = new.get('superseded_model_ids', [])
    if receipt['replacement_decision'] == 'supersede':
        assert comp['replacement_decision'] == 'supersede_old_active_configuration' and superseded == [OLD]
        assert m['correct'] > old['models'][OLD]['correct'] and m['correct'] * 100 >= 45 * 1456
    else:
        assert comp['replacement_decision'] == 'retain_both_configurations' and superseded == []
    ranked = sorted((mid for mid, model in new['models'].items() if model['correct'] * 100 >= 45 * 1456 and mid not in superseded),
                    key=lambda mid: (-new['models'][mid]['correct'], mid))
    below = sorted((mid for mid, model in new['models'].items() if model['correct'] * 100 < 45 * 1456 and mid not in superseded),
                   key=lambda mid: (-new['models'][mid]['correct'], mid))
    assert ranked == new['ranked_model_ids'] and below == new['below_cutoff']
    assert not set(superseded) & (set(ranked) | set(below))
    assert set(ranked) | set(below) | set(superseded) == set(new['models'])
    assert [mid for mid in ranked if mid in old['ranked_model_ids']] == [mid for mid in old['ranked_model_ids'] if mid not in superseded]
    assert receipt['main_configurations'] == len(ranked) and receipt['below_cutoff_configurations'] == len(below)
    assert receipt['superseded_model_ids'] == superseded and receipt['superseded_configurations'] == len(superseded)

    page, readme = (dest / 'report.html').read_text(), (dest / 'README_V5.md').read_text()
    note = (dest / 'DREX_VERSION_NOTES.md').read_text()
    assert '45%' in page and '1,456' in page and 'Drex Max v1.1' in page
    assert 'Model-selected choices and the gold scoring key remain private.' in readme
    assert 'validate_system1_v5_drex_2026_11_09.py' in readme
    assert page.index('src="comparison_accuracy.png"') < page.index('<div class="comparison-table">')
    desktop = re.search(r'<div class="comparison-table">.*?</table>', page, re.S).group()
    desktop_ids = re.findall(r'data-overall-model="([^"]+)"', desktop)
    mobile_ids = re.findall(r'<article class="mobile-card" data-overall-model="([^"]+)"', page)
    assert desktop_ids == mobile_ids == ranked
    if superseded:
        assert 'superseded' in page.lower() and 'superseded' in readme.lower()
        assert OLD not in desktop_ids and OLD not in new['below_cutoff']
    assert 'not an API-reported' in note
    assert 'zero generation is not independently attested' in re.sub(r'\s+', ' ', note.lower())
    assert 'nonzero' in note.lower() and 'pacing' in note.lower() and 'unattempted' in note.lower()
    colors = ['#d8f1e8', '#fff4c2', '#ffe4ca', '#fbdedd']
    for mid in ranked:
        row = re.search(r'<tr data-overall-model="' + re.escape(mid) + r'">(.*?)</tr>', desktop, re.S).group(1)
        card = re.search(r'<article class="mobile-card" data-overall-model="' + re.escape(mid) + r'">(.*?)</article>', page, re.S).group(1)
        model, cost = new['models'][mid], costs[mid]
        assert f'{model["accuracy"]:.2%}' in row
        speeds = [str(base.band(model[field], [250, 500, 1000])) for field in ['median_ms', 'p95_ms']]
        assert re.findall(r'data-speed-band="([^"]+)"', row) == speeds
        assert re.findall(r'data-mobile-speed-band="([^"]+)"', card) == speeds
        band = base.cost_band(cost)
        expected = 'unknown' if band is None else str(band)
        assert re.findall(r'data-cost-band="([^"]+)"', row) == [expected] * 2
        assert re.findall(r'data-mobile-cost-band="([^"]+)"', card) == [expected] * 2
        assert re.findall(r'<td class="cost [^"]*" style="background:([^"]+)"', row) == ['#edf0f2' if band is None else colors[band]] * 2
        assert html.escape(base.cost_label(cost)) in row and html.escape(base.cost_label(cost, True)) in row
        if mid == 'reax_1_3':
            assert 'FX est.' in row
        if mid == MID:
            assert 'estimate' in row and 'FX est.' not in row
    for kind in ['accuracy', 'latency', 'cost']:
        image = (dest / ('comparison_' + kind + '.png')).read_bytes()
        assert image[:8] == b'\x89PNG\r\n\x1a\n'
        width, height = struct.unpack('>II', image[16:24])
        assert width >= 1300 and height >= 1600
    for target in re.findall(r'(?:href|src)="([^"]+)"', page):
        url = urlsplit(html.unescape(target))
        if not url.scheme and not url.netloc and url.path:
            assert (dest / unquote(url.path)).exists(), target
    base.check_markdown_links(dest)
    for path in dest.rglob('*'):
        if path.is_file() and path.suffix in {'.json', '.jsonl', '.csv', '.md', '.html'}:
            text = path.read_text()
            assert '/Users/' not in text and '"expected_answer"' not in text and '"gold_answer"' not in text, path
        elif path.is_file() and path.name.endswith('.csv.gz'):
            text = gzip.decompress(path.read_bytes()).decode()
            assert '/Users/' not in text and '"expected_answer"' not in text and '"gold_answer"' not in text, path
    if mirror:
        assert {str(p.relative_to(mirror)) for p in mirror.rglob('*') if p.is_file()} == {str(p.relative_to(dest)) for p in dest.rglob('*') if p.is_file()}
        for path in dest.rglob('*'):
            if path.is_file():
                assert path.read_bytes() == (mirror / path.relative_to(dest)).read_bytes(), path
        base.check_markdown_links(mirror)
    print(f'PASS: versioned native Drex successor; 35 complete / {len(ranked)} qualifying / {len(below)} below / {len(superseded)} superseded; all34 prior objects and49,504 records unchanged; frozen1,456 inputs; tariff estimates, unknown costs and native output counters preserved; comparison, links and mirror verified.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('release', type=Path)
    parser.add_argument('prior', type=Path)
    parser.add_argument('--mirror', type=Path)
    args = parser.parse_args()
    validate(args.release.resolve(), args.prior.resolve(), args.mirror.resolve() if args.mirror else None)
