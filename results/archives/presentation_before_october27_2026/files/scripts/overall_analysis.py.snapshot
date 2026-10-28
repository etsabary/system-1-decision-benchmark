"""Offline addition export and combined analysis, preserving the October 15 runs.

The external original key is required for scoring. No API calls are made, and
neither the key nor per-question correctness is exported.
"""
from repo_layout import logical_relative, repo_file
from repo_layout import frozen_file, source_file
from collections import Counter
from copy import deepcopy
from decimal import Decimal
from hashlib import sha256
import argparse
import csv
import itertools
import json
from pathlib import Path

import added_decisions as runner
import matched_analysis as prior
from analysis_core import correct, metrics, panels, panel_summary, valid
from score_expansion import load_key, normalized_llm
from text_models import first_and_eventual, quantiles, rows

ROOT = runner.ROOT
ADDITIONS = repo_file('additions_2026-10-16', root=ROOT)
OVERALL = repo_file('overall_2026-10-16', root=ROOT)


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + '\n')


def export(model_id):
    source, dest = runner.RUNS / model_id, ADDITIONS / model_id
    completion = json.loads((source / 'completion.json').read_text())
    assert completion['status'] == 'COMPLETE_1136'
    for name, expected in completion['files_sha256'].items():
        assert sha256((source / name).read_bytes()).hexdigest() == expected
    manifest = json.loads((source / 'manifest.json').read_text())
    plan = manifest.pop('request_plan')
    contents = {
        'run_manifest.json': json.dumps(manifest, indent=2, ensure_ascii=False) + '\n',
        'request_plan.jsonl': ''.join(json.dumps(p, ensure_ascii=False) + '\n' for p in plan),
    }
    for name in ('software.json', 'model_metadata.json', 'dispatches.jsonl', 'results.jsonl', 'retry_waits.jsonl'):
        contents[name] = (source / name).read_text() if (source / name).exists() else ''
    attempts = []
    for value in rows(source / 'attempts.jsonl'):
        record = deepcopy(value)
        record['raw_response'] = prior.sanitize_raw(value['raw_response'])
        record['usage'] = record['raw_response'].get('usage') or {}
        attempts.append(record)
    contents['attempts.jsonl'] = ''.join(json.dumps(a, ensure_ascii=False, allow_nan=False) + '\n' for a in attempts)
    contents['source_audit.json'] = json.dumps({
        'completed': completion['completed'], 'source_run_files_sha256': completion['files_sha256'],
        'sanitization': 'Allowlisted model, provider, typed answers, usage and basic errors; no account metadata, credentials, owner paths, key or per-item correctness',
    }, indent=2) + '\n'
    dest.mkdir(parents=True, exist_ok=True)
    for name, text in contents.items():
        if (dest / name).exists():
            assert (dest / name).read_text() == text, 'Do not overwrite published run evidence'
        else:
            (dest / name).write_text(text)
    checksum = {name: sha256((dest / name).read_bytes()).hexdigest() for name in sorted(contents)}
    if (dest / 'checksums.json').exists():
        assert json.loads((dest / 'checksums.json').read_text()) == checksum
    else:
        write(dest / 'checksums.json', checksum)


def validate_model(model_id):
    dest = ADDITIONS / model_id
    for name, expected in json.loads((dest / 'checksums.json').read_text()).items():
        assert sha256((dest / name).read_bytes()).hexdigest() == expected, name
    software = json.loads((dest / 'software.json').read_text())
    assert sha256(frozen_file(source_file(repo_file('added_decisions.py', root=ROOT))).read_bytes()).hexdigest() == software['runner_sha256']
    assert sha256(frozen_file(source_file(repo_file('test_added_decisions.py', root=ROOT))).read_bytes()).hexdigest() == software['tests_sha256']
    manifest = json.loads((dest / 'run_manifest.json').read_text())
    assert sha256((repo_file('data/questions_1136.csv', root=ROOT)).read_bytes()).hexdigest() == manifest['questions_sha256']
    plan, attempts, results = (rows(dest / name) for name in ('request_plan.jsonl', 'attempts.jsonl', 'results.jsonl'))
    assert len(plan) == len(results) == 1136
    assert len({p['item_id'] for p in plan}) == 1136
    runner.d.reconcile(rows(dest / 'dispatches.jsonl'), attempts, results, plan)
    questions = {q['item_id']: q for q in runner.d.read_csv(repo_file('data/questions_1136.csv', root=ROOT))}
    assert {p['item_id'] for p in plan} == set(questions)
    indexed = {p['request_index']: p for p in plan}
    for p in plan:
        body = runner.payload(questions[p['item_id']], model_id)
        assert runner.d.digest(body) == p['request_payload_sha256']
        assert runner.d.digest(runner.d.packet(questions[p['item_id']])) == p['native_input_sha256']
        assert len(runner.d.canonical(body)) == p['request_body_bytes']
    for a in attempts:
        assert all(a[k] == v for k, v in indexed[a['request_index']].items())
        for key, value in runner.parse(a, model_id).items():
            assert a[key] == value, key
        runner.check_identity(a)
    first, eventual = first_and_eventual(attempts)
    assert len(first) == len(eventual) == 1136
    for r in results:
        i = r['request_index']
        assert r['first_status'] == first[i]['status'] and r['eventual_status'] == eventual[i]['status']
        assert r['attempts'] == sum(a['request_index'] == i for a in attempts)
    return first, eventual, attempts


def accounted_money(records):
    values = [Decimal(str(a['accounted_cost_usd'])) for a in records if a['accounted_cost_usd'] is not None]
    reported = [Decimal(str(a['reported_cost_usd'])) for a in records if a['reported_cost_usd'] is not None]
    total = sum(values, Decimal(0))
    return {'known_usd': float(total), 'exact_usd': str(total), 'accounted_attempts': len(values),
            'reported_usd': float(sum(reported, Decimal(0))), 'reported_attempts': len(reported),
            'missing_attempts': len(records) - len(values),
            'sources': dict(Counter(a['cost_source'] for a in records))}


def analyze(key_path, write_output=False):
    keys = load_key(key_path)
    base = json.loads((prior.MATCHED / 'summary.json').read_text())
    native_first, _, _ = prior.validate_refresh()
    llm_first, _ = first_and_eventual(rows(prior.EXPANSION / 'attempts.jsonl'))
    model_rows = {m: [normalized_llm(a) for a in llm_first.values() if a['model_requested'] == m] for m in prior.LLMS}
    for model, spec in prior.d.MODELS.items():
        model_rows[spec[0]] = [prior.normalized_native(a) for a in native_first.values() if a['model_requested'] == model]
    models = deepcopy(base['models'])
    metadata = {r['item_id']: r for r in runner.d.read_csv(repo_file('data/item_metadata.csv', root=ROOT))}
    selection = json.loads((repo_file('data/selection_manifest.json', root=ROOT)).read_text())
    all_added = []
    sessions = deepcopy(base['sessions_utc'])
    tested = [m for m in runner.MODELS if (ADDITIONS / m / 'checksums.json').exists()]
    assert tested, 'No completed additions exported'
    for model_id in tested:
        spec = runner.MODELS[model_id]
        first, eventual, attempts = validate_model(model_id)
        ff, ee = list(first.values()), list(eventual.values())
        normalized = [prior.normalized_native(a) for a in ff]
        model_rows[model_id] = normalized
        cost, primary = accounted_money(attempts), metrics(normalized, keys)
        confidence = []
        for cutoff in (.8, .9, .95):
            retained = [r for r in normalized if valid(r) and r['normalized_confidence'] is not None and r['normalized_confidence'] >= cutoff]
            confidence.append({'threshold': cutoff, **metrics(retained, keys), 'coverage': len(retained) / 1136})
        models[model_id] = {
            'label': spec['label'], 'condition': 'native_decisions_added_october_16',
            'model_requested': spec['model'], 'provider_tag': spec['provider_tag'], 'provider_name': spec['provider_name'],
            'route': 'OpenRouter' if spec['host'] == 'openrouter.ai' else 'Bespoke direct',
            'primary': primary, 'eventual': metrics([prior.normalized_native(a) for a in ee], keys),
            'statuses_first': dict(Counter(a['status'] for a in ff)),
            'http_status_first': dict(Counter(str(a['http_status']) for a in ff)),
            'recovery_attempts': len(attempts) - 1136, 'cost_all_attempts': cost, 'cost_first_attempts': accounted_money(ff),
            'cost_basis': 'API-reported' if all(a['cost_source'] == 'api_reported' for a in attempts) else 'Usage × published tariff where API charge absent; sources retained',
            'known_usd_per_1000_questions': cost['known_usd'] / 1136 * 1000,
            'known_usd_per_primary_correct': cost['known_usd'] / primary['correct'] if primary['correct'] else None,
            'latency_first_all': quantiles([a['latency_ms'] for a in ff]),
            'latency_first_usable': quantiles([a['latency_ms'] for a in ff if a['status'] == 'ok']),
            'latency_first_http200': quantiles([a['latency_ms'] for a in ff if a['http_status'] == 200]),
            'input_tokens_all_attempts': sum(a['usage'].get('input_tokens', 0) or 0 for a in attempts),
            'output_tokens_all_attempts': sum(a['usage'].get('output_tokens', 0) or 0 for a in attempts),
            'identities': dict(Counter(a['model_returned'] or 'unreported (error)' for a in ff)),
            'dates_toronto': dict(Counter(a['started']['toronto'][:10] for a in ff)), 'confidence': confidence,
        }
        for field in ('role', 'level'):
            models[model_id]['by_' + field] = {v: metrics([r for r in normalized if metadata[r['item_id']][field] == v], keys)
                                            for v in sorted({r[field] for r in metadata.values()})}
        models[model_id]['panels'] = panel_summary(panels(normalized, keys, selection))
        all_added.extend(attempts)
        sessions[model_id] = {'started': min(a['started']['utc'] for a in attempts),
                              'completed': max(a['completed']['utc'] for a in attempts)}
    by_family = []
    for family in base['by_family']:
        f = deepcopy(family)
        ids = {i for i, q in metadata.items() if q['family_id'] == f['family_id']}
        for model_id in tested:
            f['models'][model_id] = metrics([r for r in model_rows[model_id] if r['item_id'] in ids], keys)
        by_family.append(f)
    for model_id in tested:
        models[model_id]['macro_family_accuracy'] = sum(f['models'][model_id]['accuracy_attempted'] for f in by_family) / 25
    for model_id, rr in model_rows.items():
        assert len(rr) == len({r['item_id'] for r in rr}) == 1136
        assert metrics(rr, keys) == models[model_id]['primary']
    index = {m: {r['item_id']: r for r in rr} for m, rr in model_rows.items()}
    none = [i for i in metadata if not any(correct(index[m][i], keys) for m in models)]
    shared = [i for i in metadata if all(valid(index[m][i]) for m in models)]
    added_cost = accounted_money(all_added)
    total = Decimal(base['total_selected_reported_cost']['exact_usd']) + Decimal(added_cost['exact_usd'])
    reported = Decimal(base['total_selected_reported_cost']['exact_usd']) + sum(
        (Decimal(str(a['reported_cost_usd'])) for a in all_added if a['reported_cost_usd'] is not None), Decimal(0))
    summary = {**deepcopy(base),
        'status': 'COMPLETE_1136_PER_TESTED_MODEL_WITH_OCTOBER_16_ADDITIONS',
        'model_count': len(models), 'added_model_ids': tested,
        'pending_model_ids': [m for m in runner.MODELS if m not in tested],
        'total_scored_model_questions': len(models) * 1136,
        'models': models, 'by_family': by_family,
        'pairwise': [{'a': a, 'b': b, **prior.pairwise(model_rows[a], model_rows[b], keys)} for a, b in itertools.combinations(models, 2)],
        'none_of_tested_models_correct': len(none), 'all_tested_models_answered': len(shared),
        'accuracy_on_shared_answered': {m: metrics([r for r in rr if r['item_id'] in shared], keys) for m, rr in model_rows.items()},
        'sessions_utc': sessions, 'addition_cost': added_cost,
        'original_eleven_reported_cost': base['total_selected_reported_cost'],
        'total_selected_reported_cost': {
            'known_usd': float(reported), 'exact_usd': str(reported),
            'reported_attempts': base['total_selected_reported_cost']['reported_attempts'] + added_cost['reported_attempts'],
            'missing_attempts': base['total_selected_reported_cost']['missing_attempts'] + len(all_added) - added_cost['reported_attempts'],
            'basis': 'Only dollar charges returned by APIs; calculated Nimble tariff costs are excluded from this field'},
        'total_selected_accounted_cost': {'known_usd': float(total), 'exact_usd': str(total),
            'missing_attempts': base['total_selected_reported_cost']['missing_attempts'] + added_cost['missing_attempts'],
            'basis': 'October 15 API charges plus October 16 API charges or separately labelled tariff calculations'},
        'total_selected_http_attempts': base['total_selected_http_attempts'] + len(all_added),
        'addition_limits': [
            'Original eleven runs are October 15; additions are October 16; dates are visible and old results unchanged',
            'Same full-response timer, two concurrent requests/model and original choice content; not simultaneous sessions',
            'Microsoft uses OpenRouter/Azure; Nimble uses Bespoke direct, so route and hardware affect latency',
            'Documented text-only API inputs; image bank is unsupported, not scored zero or converted to text',
        ],
        'original_eleven_limits': base['limits'],
        'limits': [
            'Original eleven tested October 15, 2026; new three tested October 16; not simultaneous sessions',
            'Same original native choice content and full-response timing method; two concurrent requests per model',
            'Microsoft via OpenRouter/Azure; Nimble via Bespoke direct; backend hardware and routes differ',
            'API-reported dollar charges distinguished from Nimble usage-times-tariff calculations; no invoice reconciliation',
            'Nimble response repeats requested version name, not independent hidden-checkpoint attestation',
            '640 core questions plus 496 dependent variants; single shot, unchanged original key, no new key audit',
            'Strict first attempt is primary; no answer-dependent retries; image compatibility probes are not scored image runs',
        ],
        'source_files_sha256': {**base['source_files_sha256'],
            'matched_2026-10-15/summary.json': sha256((prior.MATCHED / 'summary.json').read_bytes()).hexdigest(),
            **{str(logical_relative(p, root=ROOT)): sha256(p.read_bytes()).hexdigest() for m in tested for p in (ADDITIONS / m).iterdir() if p.is_file()}},
    }
    if write_output:
        write(OVERALL / 'summary.json', summary)
        family_rows = [{'family_id': f['family_id'], 'family': f['family'], 'n': f['n'],
                        **{models[m]['label']: f['models'][m]['correct'] for m in models}} for f in by_family]
        with (OVERALL / 'family_comparison.csv').open('w', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=list(family_rows[0]))
            writer.writeheader()
            writer.writerows(family_rows)
        write(runner.RUNS / 'analysis_PRIVATE/none_correct_PRIVATE.json', none)
        print(json.dumps({'model_count': len(models), 'pending': summary['pending_model_ids'],
                          'added_results': {m: {'correct': models[m]['primary']['correct'],
                            'median_ms': models[m]['latency_first_all']['median_ms'],
                            'p95_ms': models[m]['latency_first_all']['p95_ms'], 'cost': models[m]['cost_all_attempts']} for m in tested}}, indent=2))
    else:
        assert summary == json.loads((OVERALL / 'summary.json').read_text())
        print('PASS: combined scores, all 25 families, panels, costs and timing reproduced; October 15 results unchanged')
    return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--export', choices=runner.MODELS, nargs='+')
    parser.add_argument('--answer-key', type=Path)
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    for model_id in args.export or []:
        export(model_id)
    if args.answer_key:
        analyze(args.answer_key, args.write)
    elif ADDITIONS.exists():
        for model_id in runner.MODELS:
            if (ADDITIONS / model_id).exists():
                validate_model(model_id)
        print('PASS: completed addition ledgers, identities, requests and costs; no key or API calls')
