"""Publish and verify the Decisions refresh and the same-day eleven-model view.

Offline only. Scoring requires the external original answer key. No key or
individual correctness records are written to the public release.
"""
from repo_layout import logical_relative, repo_file
from repo_layout import frozen_file, source_file
import argparse
from collections import Counter
from copy import deepcopy
from datetime import datetime
from decimal import Decimal
from hashlib import sha256
import itertools
import json
from pathlib import Path
import re

import decision_refresh as d
from analysis_core import normalize, valid, correct, metrics, panels, panel_summary
from score_expansion import load_key, normalized_llm
from text_models import EXPANSION, HISTORICAL, MODELS as LLMS, first_and_eventual, money, quantiles, rows, read_csv

ROOT = d.ROOT
REFRESH = repo_file('decision_refresh_2026-10-15', root=ROOT)
MATCHED = repo_file('matched_2026-10-15', root=ROOT)


def write(path, value):
    Path(path).write_text(json.dumps(value, indent=2, ensure_ascii=False)+'\n')


def sanitize_raw(raw):
    """Allowlist rather than guessing all possible account-metadata fields."""
    result = {k: raw[k] for k in ('id', 'model', 'provider') if k in raw}
    if isinstance(raw.get('answers'), dict):
        result['answers'] = {name: {k: value[k] for k in ('type', 'choice', 'confidence', 'probabilities') if k in value}
                             for name, value in raw['answers'].items() if isinstance(value, dict)}
    if isinstance(raw.get('usage'), dict):
        result['usage'] = {k: raw['usage'][k] for k in ('input_tokens', 'output_tokens', 'cost') if k in raw['usage']}
    if isinstance(raw.get('error'), dict):
        result['error'] = {k: re.sub(r'user_[A-Za-z0-9_-]+', '[REDACTED_ACCOUNT]', str(raw['error'][k]))
                           if k == 'message' else raw['error'][k] for k in ('code', 'message') if k in raw['error']}
    return result


def export(source):
    source = Path(source)
    completion = json.loads((source/'completion.json').read_text())
    assert completion['status'] == 'COMPLETE_1136_EACH_THREE_DECISIONS'
    for name, expected in completion['files_sha256'].items():
        assert sha256((source/name).read_bytes()).hexdigest() == expected
    assert not REFRESH.exists(), 'Public refresh already exists; do not overwrite it'
    REFRESH.mkdir()
    manifest = json.loads((source/'manifest.json').read_text())
    plan = manifest.pop('request_plan')
    write(REFRESH/'run_manifest.json', manifest)
    write(REFRESH/'model_metadata.json', json.loads((source/'model_metadata.json').read_text()))
    write(REFRESH/'software.json', json.loads((source/'software.json').read_text()))
    (REFRESH/'request_plan.jsonl').write_text(''.join(json.dumps(p, ensure_ascii=False)+'\n' for p in plan))
    attempts = []
    for original in rows(source/'attempts.jsonl'):
        record = deepcopy(original)
        record['raw_response'] = sanitize_raw(original['raw_response'])
        record['usage'] = record['raw_response'].get('usage') or {}
        attempts.append(record)
    (REFRESH/'attempts.jsonl').write_text(''.join(json.dumps(a, ensure_ascii=False)+'\n' for a in attempts))
    for name in ('dispatches.jsonl', 'results.jsonl', 'retry_waits.jsonl'):
        (REFRESH/name).write_bytes((source/name).read_bytes() if (source/name).exists() else b'')
    write(REFRESH/'source_audit.json', {
        'source_run_files_sha256': completion['files_sha256'], 'completed': completion['completed'],
        'sanitization': 'Public raw API responses allowlist typed outputs, model/provider identity, usage and basic errors; account IDs, BYOK flags and other account metadata omitted',
        'privacy': 'No answer key, individual correctness, API credentials or local owner paths are included',
        'previous_release_commit': 'b9c7b1f3abb0e1728c7b4f8585d027b3c3a82921',
    })
    write(REFRESH/'checksums.json', {p.name: sha256(p.read_bytes()).hexdigest() for p in sorted(REFRESH.iterdir())})


def validate_refresh():
    manifest = json.loads((REFRESH/'run_manifest.json').read_text())
    for name, expected in json.loads((REFRESH/'checksums.json').read_text()).items():
        assert sha256((REFRESH/name).read_bytes()).hexdigest() == expected, name
    software = json.loads((REFRESH/'software.json').read_text())
    assert sha256(frozen_file(source_file(repo_file('decision_refresh.py', root=ROOT))).read_bytes()).hexdigest() == software['runner_sha256']
    assert sha256(frozen_file(source_file(repo_file('test_decision_refresh.py', root=ROOT))).read_bytes()).hexdigest() == software['tests_sha256']
    assert sha256((repo_file('data/questions_1136.csv', root=ROOT)).read_bytes()).hexdigest() == manifest['questions_sha256']
    assert manifest['timing'] == json.loads((EXPANSION/'run_manifest.json').read_text())['timing']
    plan, attempts, results = (rows(REFRESH/name) for name in ('request_plan.jsonl', 'attempts.jsonl', 'results.jsonl'))
    assert len(plan) == len(results) == 3408
    assert Counter(p['model_requested'] for p in plan) == Counter({m: 1136 for m in d.MODELS})
    assert len({(p['item_id'], p['model_requested']) for p in plan}) == 3408
    done = d.reconcile(rows(REFRESH/'dispatches.jsonl'), attempts, results, plan)
    assert len(done) == 3408
    questions = {q['item_id']: q for q in read_csv(repo_file('data/questions_1136.csv', root=ROOT))}
    indexed = {p['request_index']: p for p in plan}
    original_order = list(dict.fromkeys(p['item_id'] for p in rows(EXPANSION/'request_plan.jsonl')))
    assert list(dict.fromkeys(p['item_id'] for p in plan)) == original_order
    for p in plan:
        body = d.payload(questions[p['item_id']], p['model_requested'])
        assert p['request_payload_sha256'] == d.digest(body)
        assert p['native_input_sha256'] == d.digest(d.packet(questions[p['item_id']]))
        assert p['request_body_bytes'] == len(d.canonical(body))
    for a in attempts:
        assert all(a[k] == v for k, v in indexed[a['request_index']].items())
        for k, v in d.parse(a).items():
            assert a[k] == v, k
        d.check_identity(a)
    first, eventual = first_and_eventual(attempts)
    assert len(first) == len(eventual) == 3408
    for r in results:
        i = r['request_index']
        assert r['first_status'] == first[i]['status'] and r['eventual_status'] == eventual[i]['status']
        assert r['attempts'] == sum(a['request_index'] == i for a in attempts)
    return first, eventual, attempts


def normalized_native(a):
    return {**a, 'normalized_status': a['status'], 'normalized_choice': a['choice'] or '',
            'normalized_confidence': a['confidence'] if a['status'] == 'ok' else None,
            'probability_warning': 'Missing or non-normalized probabilities' if a['status'] == 'ok' and not a['probabilities_valid'] else ''}


def pairwise(aa, bb, keys):
    a, b = {r['item_id']: r for r in aa}, {r['item_id']: r for r in bb}
    assert set(a) == set(b)
    shared = [i for i in a if valid(a[i]) and valid(b[i])]
    transitions = Counter((correct(a[i], keys), correct(b[i], keys)) for i in a)
    return {'n': len(a), 'both_correct': transitions[True, True], 'both_unsuccessful': transitions[False, False],
            'only_a_correct': transitions[True, False], 'only_b_correct': transitions[False, True],
            'both_answered': len(shared),
            'same_choice_on_both_answered': sum(a[i]['normalized_choice'] == b[i]['normalized_choice'] for i in shared)}


def analyze(key_path, write_output=False):
    keys = load_key(key_path)
    first, eventual, attempts = validate_refresh()
    old = json.loads((EXPANSION/'summary.json').read_text())
    llm_first, llm_eventual = first_and_eventual(rows(EXPANSION/'attempts.jsonl'))
    llm_attempts = rows(EXPANSION/'attempts.jsonl')
    questions = read_csv(repo_file('data/questions_1136.csv', root=ROOT))
    metadata = {r['item_id']: r for r in read_csv(repo_file('data/item_metadata.csv', root=ROOT))}
    selection = json.loads((repo_file('data/selection_manifest.json', root=ROOT)).read_text())
    model_rows = {m: [normalized_llm(a) for a in llm_first.values() if a['model_requested'] == m] for m in LLMS}
    models = {m: deepcopy(old['models'][m]) for m in LLMS}
    for model, spec in d.MODELS.items():
        ff = [a for a in first.values() if a['model_requested'] == model]
        ee = [a for a in eventual.values() if a['model_requested'] == model]
        aa = [a for a in attempts if a['model_requested'] == model]
        normalized = [normalized_native(a) for a in ff]
        model_rows[spec[0]] = normalized
        cost, primary = money(aa), metrics(normalized, keys)
        confidence = []
        for cutoff in (.8, .9, .95):
            retained = [r for r in normalized if valid(r) and r['normalized_confidence'] is not None and r['normalized_confidence'] >= cutoff]
            confidence.append({'threshold': cutoff, **metrics(retained, keys), 'coverage': len(retained)/1136})
        models[spec[0]] = {
            'label': spec[1], 'condition': 'native_decisions_same_day_refresh',
            'provider_tag': spec[2], 'provider_name': spec[3], 'model_requested': model,
            'primary': primary, 'eventual': metrics([normalized_native(a) for a in ee], keys),
            'statuses_first': dict(Counter(a['status'] for a in ff)),
            'http_status_first': dict(Counter(str(a['http_status']) for a in ff)),
            'recovery_attempts': len(aa)-1136, 'cost_all_attempts': cost, 'cost_first_attempts': money(ff),
            'known_usd_per_1000_questions': cost['known_usd']/1136*1000,
            'known_usd_per_primary_correct': cost['known_usd']/primary['correct'] if primary['correct'] else None,
            'latency_first_all': quantiles([a['latency_ms'] for a in ff]),
            'latency_first_usable': quantiles([a['latency_ms'] for a in ff if a['status'] == 'ok']),
            'latency_first_http200': quantiles([a['latency_ms'] for a in ff if a['http_status'] == 200]),
            'input_tokens_all_attempts': sum(a['usage'].get('input_tokens', 0) or 0 for a in aa),
            'output_tokens_all_attempts': sum(a['usage'].get('output_tokens', 0) or 0 for a in aa),
            'identities': dict(Counter(a['model_returned'] or 'unreported (error)' for a in ff)),
            'dates_toronto': dict(Counter(a['started']['toronto'][:10] for a in ff)), 'confidence': confidence,
        }
    by_family = []
    for fid in sorted({r['family_id'] for r in metadata.values()}):
        ids = {i for i, r in metadata.items() if r['family_id'] == fid}
        by_family.append({'family_id': fid, 'family': metadata[next(iter(ids))]['family'], 'n': len(ids),
                          'models': {m: metrics([r for r in rr if r['item_id'] in ids], keys) for m, rr in model_rows.items()}})
    for m, rr in model_rows.items():
        assert len(rr) == len({r['item_id'] for r in rr}) == 1136
        assert set(r['item_id'] for r in rr) == set(metadata)
        assert set(metadata) <= set(keys)
        assert metrics(rr, keys) == models[m]['primary']
        for field in ('role', 'level'):
            models[m]['by_'+field] = {v: metrics([r for r in rr if metadata[r['item_id']][field] == v], keys)
                                     for v in sorted({r[field] for r in metadata.values()})}
        models[m]['panels'] = panel_summary(panels(rr, keys, selection))
        models[m]['macro_family_accuracy'] = sum(f['models'][m]['accuracy_attempted'] for f in by_family)/25
        if m in LLMS:
            assert models[m] == old['models'][m], 'Eight-LLM result changed: '+m
    index = {m: {r['item_id']: r for r in rr} for m, rr in model_rows.items()}
    shared = [i for i in metadata if all(valid(index[m][i]) for m in models)]
    none = [i for i in metadata if not any(correct(index[m][i], keys) for m in models)]
    repeat = {}
    for m, filename in HISTORICAL.items():
        previous = [normalize(r) for r in read_csv(repo_file('data', root=ROOT)/filename)]
        repeat[m] = {'previous_primary': old['models'][m]['primary'],
                     'previous_saved_latency': old['historical_speeds'][m]['full_bank_saved_latency_all_outcomes'],
                     'old_to_new': pairwise(previous, model_rows[m], keys)}
    refresh_times = {'started': min(a['started']['utc'] for a in attempts), 'completed': max(a['completed']['utc'] for a in attempts)}
    summary = {
        'status': 'COMPLETE_SAME_DAY_ELEVEN_MODELS_1136_EACH', 'total_scored_model_questions': 12496,
        'refresh_scored_model_questions': 3408, 'refresh_http_attempts': len(attempts),
        'refresh_total_reported_cost': money(attempts),
        'total_selected_http_attempts': len(llm_attempts)+len(attempts),
        'total_selected_reported_cost': money(llm_attempts+attempts),
        'models': models, 'by_family': by_family,
        'pairwise': [{'a': a, 'b': b, **pairwise(model_rows[a], model_rows[b], keys)} for a, b in itertools.combinations(models, 2)],
        'all_eleven_answered': len(shared),
        'accuracy_on_shared_answered': {m: metrics([r for r in rr if r['item_id'] in shared], keys) for m, rr in model_rows.items()},
        'none_of_eleven_correct': len(none), 'repeat_comparison': repeat,
        'sessions_utc': {'eight_regular_llms': {'started': old['started'], 'completed': old['completed']}, 'three_decisions': refresh_times},
        'questions_sha256': old['questions_sha256'], 'key_sha256': old['key_sha256'],
        'timing': json.loads((REFRESH/'run_manifest.json').read_text())['timing'],
        'limits': ['All eleven tested October 15, 2026 in Toronto; two sessions, not simultaneous',
                   'Same HTTP timing method and per-model concurrency; native Decisions and ordinary chat have different payloads and endpoints',
                   'Same OpenRouter front door, different backend hardware and quantization',
                   'Native Decisions expose dated snapshots; ordinary LLM aliases do not guarantee hidden checkpoint immutability',
                   '640 core questions plus 496 dependent variants; one pass, fixed generated bank, no new key audit',
                   'Strict first attempt is primary; recovery and post-hoc LLM leading-ID sensitivity separate'],
        'source_files_sha256': {str(logical_relative(p, root=ROOT)): sha256(p.read_bytes()).hexdigest() for p in [
            EXPANSION/'attempts.jsonl', EXPANSION/'summary.json', REFRESH/'attempts.jsonl', REFRESH/'request_plan.jsonl', REFRESH/'run_manifest.json']},
    }
    if write_output:
        MATCHED.mkdir(exist_ok=True)
        write(MATCHED/'summary.json', summary)
        import csv
        family_rows = [{'family_id': f['family_id'], 'family': f['family'], 'n': f['n'], **{models[m]['label']: f['models'][m]['correct'] for m in models}} for f in by_family]
        with (MATCHED/'family_comparison.csv').open('w', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=list(family_rows[0]))
            writer.writeheader(); writer.writerows(family_rows)
        private = d.OUT.parent/'analysis_PRIVATE'
        private.mkdir(exist_ok=True)
        write(private/'none_correct_PRIVATE.json', none)
        print(json.dumps({'status': summary['status'], 'refresh_cost': summary['refresh_total_reported_cost'],
                          'results': {m: {'correct': v['primary']['correct'], 'median_ms': v['latency_first_all']['median_ms'],
                                          'p95_ms': v['latency_first_all']['p95_ms'], 'cost': v['cost_all_attempts']} for m, v in models.items()}}, indent=2))
    else:
        assert summary == json.loads((MATCHED/'summary.json').read_text()), 'Published matched summary differs from external-key reproduction'
        print('PASS: all eleven same-day scores, 25 families, panels, confidence, costs, first/recovery timing and unchanged eight LLM results reproduced offline')
    return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--export-from', type=Path)
    parser.add_argument('--answer-key', type=Path)
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    if args.export_from:
        export(args.export_from)
    if args.answer_key:
        analyze(args.answer_key, args.write)
    else:
        validate_refresh()
        print('PASS: 3,408 exact Decisions refresh payloads, sanitized attempts, immutable checkpoints and matched HTTP timing protocol; offline only')
