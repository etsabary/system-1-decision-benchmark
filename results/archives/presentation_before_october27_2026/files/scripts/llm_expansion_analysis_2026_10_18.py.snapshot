"""Offline immutable exports and aggregate scoring of the screened October18 runs.

This module never sends inference requests or reads API credentials. Existing
36-model results remain unchanged. Only a separately supplied frozen gold key
may score saved answers. Exports retain original filenames and exact bytes so
the executor's completion and100-case-prefix bindings remain independently
verifiable. Active runs are not exported. Partial samples and failed interface
probes never receive fabricated full-bank scores or enter the main comparison.
"""
from __future__ import annotations
from repo_layout import logical_relative, repo_file
from repo_layout import frozen_file, source_file

import argparse
from collections import Counter
from contextlib import redirect_stdout
from copy import deepcopy
import csv
from decimal import Decimal
from hashlib import sha256
import io
import itertools
import json
from pathlib import Path
import re

import llm_field_2026_10_18 as ordinary
import tev_native_adapter_2026_10_18 as tev
import native_expansion_analysis as prior
from analysis_core import metrics, correct, valid, panels, panel_summary
from score_expansion import load_key, normalized_llm

ROOT = ordinary.ROOT
PUBLIC = repo_file('llm_additions_2026-10-18', root=ROOT)
OVERALL = repo_file('overall_llm_expanded_2026-10-18', root=ROOT)
BASE = repo_file('overall_expanded_2026-10-18/summary.json', root=ROOT)
MODELS = {**ordinary.MODELS, **tev.MODELS}
COMPAT_ONLY = {'tev1_4b', 'xing4_free'}
FILES = ('manifest.json', 'software.json', 'model_metadata.json', 'compatibility_probe.json',
         'probe_dispatches.jsonl', 'probe_attempts.jsonl', 'dispatches.jsonl', 'attempts.jsonl',
         'results.jsonl', 'screen_100.json', 'continuation_receipt.json', 'progress.jsonl',
         'retry_waits.jsonl', 'completion.json', 'STOPPED_SCREEN.json')
FORBIDDEN_FIELDS = {'user_id', 'account_id', 'is_byok', 'cost_details', 'authorization',
                    'api_key', 'gold_option', 'gold_text', 'gold_canonical', 'gold_answer',
                    'correct_first', 'correct_eventual', 'correct_option_id',
                    'choice_first_correct', 'choice_eventual_correct'}
POLICY = {'accuracy_below': .5, 'model_output_failures_fraction_at_least': .05,
          'median_ms_above': 2000, 'minimum_cases': 100, 'recheck_every_cases': 100}
ANALYSIS_SOURCES = ('llm_expansion_analysis_2026_10_18.py', 'test_llm_expansion_analysis_2026_10_18.py',
                    'native_expansion_analysis.py', 'analysis_core.py', 'matched_analysis.py',
                    'overall_analysis.py', 'score_expansion.py', 'text_additions.py',
                    'text_models.py', 'llm_screening_2026_10_18.py', 'tev_screening_2026_10_18.py')


def digest_file(path):
    return sha256(source_file(path).read_bytes()).hexdigest()


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + '\n')


def runner(model_id):
    return tev if model_id in tev.MODELS else ordinary


def source_dir(model_id):
    return runner(model_id).RUNS / model_id


def privacy_guard(data, filename):
    """Fail rather than rewrite evidence and thereby invalidate its prefix hashes."""
    text = data.decode('utf-8')
    assert '/Users/' not in text and '/home/' not in text, 'Owner path in export: ' + filename
    assert not re.search(r'sk-(?:or-v1-)?[A-Za-z0-9_-]{24,}', text), 'Credential-like string in export'
    def inspect(value):
        if isinstance(value, dict):
            assert not {str(k).lower() for k in value}.intersection(FORBIDDEN_FIELDS), 'Private field in export: ' + filename
            for child in value.values():
                inspect(child)
        elif isinstance(value, list):
            for child in value:
                inspect(child)
    if filename.endswith('.jsonl'):
        for line in text.splitlines():
            if line.strip():
                inspect(json.loads(line))
    elif filename.endswith('.json'):
        inspect(json.loads(text))


def classify(model_id, out=None):
    """A complete inference file alone is not enough: final policy must settle."""
    out = Path(out) if out is not None else source_dir(model_id)
    if (out / 'STOPPED_SCREEN.json').exists():
        return 'STOPPED_SCREEN'
    if (out / 'completion.json').exists():
        final = out / 'screening_decisions/after_1136.json'
        if not final.exists():
            return 'ACTIVE_OR_CONTROLLER_SETTLING'
        receipt = json.loads(final.read_text())
        return 'COMPLETE_1136' if receipt.get('decision') == 'continue' else 'COMPLETE_SCREEN_FAILED'
    probe = out / 'compatibility_probe.json'
    if probe.exists() and not ordinary.d.rows(out / 'attempts.jsonl'):
        record = json.loads(probe.read_text())
        if record['status'] in ('http_failure', 'provider_error', 'transport_failure', 'unexpected_reasoning'):
            return 'COMPATIBILITY_BLOCKED'
    return 'ACTIVE_OR_NOT_STARTED'


def gate_reasons(primary, compliance, latency):
    assert primary['attempted'] >= POLICY['minimum_cases']
    reasons = []
    if primary['accuracy_attempted'] < POLICY['accuracy_below']:
        reasons.append('accuracy_below_50_percent')
    if compliance['model_output_failures'] / primary['attempted'] >= POLICY['model_output_failures_fraction_at_least']:
        reasons.append('model_output_failures_at_least_5_percent')
    if latency['median_ms'] > POLICY['median_ms_above']:
        reasons.append('median_above_2000_ms')
    return reasons


def compliance(first):
    value = prior.llm16.compliance(first)
    value.update(planned=len(first), model_output_failure_fraction=value['model_output_failures'] / len(first) if first else None)
    value.pop('eligible_for_main_comparison', None)
    value['passes_output_format_screen'] = bool(first) and value['model_output_failure_fraction'] < .05
    return value


def controller_sources(model_id):
    names = ['llm_screening_2026_10_18.py']
    if model_id in tev.MODELS:
        names.append('tev_screening_2026_10_18.py')
    return {name: digest_file(frozen_file(repo_file(name, root=ROOT))) for name in names}


def validate_screen_decisions(model_id, out, keys=None):
    """Recount all bound cumulative prefixes, never treat100requests as IID."""
    out = Path(out)
    run = runner(model_id)
    state = classify(model_id, out)
    paths = sorted((out / 'screening_decisions').glob('after_*.json'))
    if state == 'COMPATIBILITY_BLOCKED':
        assert not paths and not ordinary.d.rows(out / 'attempts.jsonl')
        return []
    assert paths, 'Settled screened run omitted policy receipts'
    all_attempts = ordinary.d.rows(out / 'attempts.jsonl')
    first, _ = ordinary.chat.first_and_eventual(all_attempts)
    n = len(first)
    expected_counts = list(range(100, n + 1, 100))
    if n == 1136:
        expected_counts.append(1136)
    receipts = [json.loads(p.read_text()) for p in paths]
    assert [r['evaluated_first_attempts'] for r in receipts] == expected_counts, 'Policy recheck sequence changed'
    expected_controller = controller_sources(model_id)
    controller_name = 'tev_screening_2026_10_18.py' if model_id in tev.MODELS else 'llm_screening_2026_10_18.py'
    for receipt, count in zip(receipts, expected_counts):
        assert receipt['model_id'] == model_id and receipt['screen_policy'] == run.SCREEN_POLICY
        assert receipt['manifest_sha256'] == digest_file(out / 'manifest.json')
        assert receipt['screen_sha256'] == digest_file(out / 'screen_100.json')
        assert receipt['controller_sha256'] == expected_controller[controller_name], 'Policy controller source changed'
        assert all(receipt['cutoffs'][k] == v for k, v in POLICY.items()), 'Approved cutoffs changed'
        run.verify_prefixes(out, {'attempts.jsonl': receipt['attempts_prefix']})
        data = (out / 'attempts.jsonl').read_bytes()[:receipt['attempts_prefix']['bytes']]
        assert data.endswith(b'\n'), 'Bound attempt prefix must end at a JSONL boundary'
        attempts = [json.loads(line) for line in data.decode('utf-8').splitlines() if line.strip()]
        ff, ee = ordinary.chat.first_and_eventual(attempts)
        assert set(ff) == set(range(1, count + 1)), 'Screen is not the agreed sequential prefix'
        current = list(ff.values())
        value = compliance(current)
        assert receipt['compliance'] == value
        assert receipt['first_latency'] == ordinary.chat.quantiles([a['latency_ms'] for a in current])
        assert receipt['cost_all_attempts'] == ordinary.chat.money(attempts)
        primary = receipt['primary']
        assert primary['attempted'] == count
        assert primary['answered'] == sum(a['status'] == 'ok' for a in current)
        assert primary['correct'] + primary['wrong'] == primary['answered']
        assert primary['unanswered'] == count - primary['answered']
        assert primary['accuracy_attempted'] == primary['correct'] / count
        reasons = gate_reasons(primary, value, receipt['first_latency'])
        assert receipt['reasons'] == reasons
        assert receipt['decision'] == ('stop' if reasons else 'continue')
        assert receipt['gate_result'] == ('fail' if reasons else 'pass')
        if keys is not None:
            # Both recorded controllers actually used normalized_llm, including
            # Tev. Published Tev native metrics additionally retain probability
            # warnings, which must not be retrofitted into the frozen receipts.
            assert primary == metrics([normalized_llm(a) for a in current], keys)
            assert receipt['eventual'] == metrics([normalized_llm(a) for a in ee.values()], keys)
    if state == 'COMPLETE_1136':
        assert n == 1136 and all(r['decision'] == 'continue' for r in receipts)
    elif state in ('STOPPED_SCREEN', 'COMPLETE_SCREEN_FAILED'):
        assert receipts[-1]['decision'] == 'stop'
        assert all(r['decision'] == 'continue' for r in receipts[:-1])
        if (out / 'STOPPED_SCREEN.json').exists():
            assert json.loads((out / 'STOPPED_SCREEN.json').read_text()) == receipts[-1]
        run.verify_prefixes(out, {'attempts.jsonl': receipts[-1]['attempts_prefix']})
        assert receipts[-1]['attempts_prefix']['bytes'] == (out / 'attempts.jsonl').stat().st_size
    return receipts


def export(model_id):
    run, source, dest = runner(model_id), source_dir(model_id), PUBLIC / model_id
    state = classify(model_id, source)
    assert state in ('COMPLETE_1136', 'STOPPED_SCREEN', 'COMPLETE_SCREEN_FAILED', 'COMPATIBILITY_BLOCKED'), 'Never export an active or unsettled run'
    with redirect_stdout(io.StringIO()):
        run.validate(model_id, source, require_complete=state == 'COMPLETE_1136')
    validate_screen_decisions(model_id, source)
    names = [name for name in FILES if (source / name).exists()]
    names += [str(p.relative_to(source)) for p in sorted((source / 'screening_decisions').glob('after_*.json'))]
    assert {'manifest.json', 'software.json', 'model_metadata.json', 'compatibility_probe.json',
            'probe_dispatches.jsonl', 'probe_attempts.jsonl'} <= set(names)
    contents = {name: (source / name).read_bytes() for name in names}
    for name, data in contents.items():
        privacy_guard(data, name)
    hashes = {name: sha256(data).hexdigest() for name, data in contents.items()}
    audit = {'model_id': model_id, 'export_state': state,
             'previous_36_model_summary_sha256': digest_file(BASE),
             'source_evidence_sha256': hashes, 'controllers_sha256': controller_sources(model_id),
             'byte_preservation': 'Original sanitized capture bytes and filenames retained, including full manifest and prefix-bound ledgers',
             'privacy': 'No owner paths, account metadata, credentials, gold key or per-item correctness; reject instead of rewriting any unsafe bound evidence'}
    contents['source_audit.json'] = (json.dumps(audit, indent=2, ensure_ascii=False) + '\n').encode('utf-8')
    dest.mkdir(parents=True, exist_ok=True)
    for name, data in contents.items():
        path = dest / name
        if path.exists():
            assert path.read_bytes() == data, 'Never replace exported evidence: ' + model_id + '/' + name
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        if name in hashes:
            assert digest_file(source / name) == hashes[name], 'Source changed during export'
    checksums = {name: digest_file(dest / name) for name in sorted(contents)}
    ordinary.d.save_bound(dest / 'checksums.json', checksums)
    validate_export(model_id)
    return state


def export_settled():
    statuses = {}
    for model_id in MODELS:
        state = classify(model_id)
        statuses[model_id] = state
        if state in ('COMPLETE_1136', 'STOPPED_SCREEN', 'COMPLETE_SCREEN_FAILED', 'COMPATIBILITY_BLOCKED'):
            export(model_id)
    # This is a stage index, not immutable per-run evidence. Active ledgers and
    # their prefixes are deliberately absent; only their status is recorded.
    write(PUBLIC / 'export_index.json', {'states': statuses,
          'active_ledger_exports': False, 'compatibility_probes_are_scored': False,
          'exported_model_ids': [m for m in MODELS if (PUBLIC / m / 'checksums.json').exists()]})
    return statuses


def validate_export(model_id, keys=None):
    dest = PUBLIC / model_id
    checksums = json.loads((dest / 'checksums.json').read_text())
    for name, expected in checksums.items():
        data = (dest / name).read_bytes()
        assert sha256(data).hexdigest() == expected, 'Export checksum differs: ' + name
        privacy_guard(data, name)
    audit = json.loads((dest / 'source_audit.json').read_text())
    assert audit['model_id'] == model_id and audit['previous_36_model_summary_sha256'] == digest_file(BASE)
    assert audit['controllers_sha256'] == controller_sources(model_id)
    for name, expected in audit['source_evidence_sha256'].items():
        assert checksums[name] == expected, 'Export changed captured bytes: ' + name
    run = runner(model_id)
    assert classify(model_id, dest) == audit['export_state']
    with redirect_stdout(io.StringIO()):
        run.validate(model_id, dest, require_complete=audit['export_state'] == 'COMPLETE_1136', historical=True)
    receipts = validate_screen_decisions(model_id, dest, keys)
    if audit['export_state'] == 'COMPATIBILITY_BLOCKED':
        return {}, {}, [], receipts
    _, plan = run.prepare(model_id)
    attempts, _, _, _ = run.ledger_state(dest, plan)
    for a in attempts:
        run.check_identity(a)
    first, eventual = ordinary.chat.first_and_eventual(attempts)
    return first, eventual, attempts, receipts


def previous_rows(keys):
    rr = prior.previous_rows()
    base = json.loads(BASE.read_text())
    for model_id in base['native_added_october_18_model_ids']:
        first, _, _ = prior.validate_model(model_id)
        rr[model_id] = [prior.prior.normalized_native(a) for a in first.values()]
    assert set(rr) == set(base['models']) and len(rr) == 36
    for model_id, rows in rr.items():
        assert metrics(rows, keys) == base['models'][model_id]['primary'], 'Frozen prior score differs: ' + model_id
    return rr


def normalize(model_id, attempts):
    operation = prior.prior.normalized_native if model_id in tev.MODELS else normalized_llm
    return [operation(a) for a in attempts]


def model_summary(model_id, first, eventual, attempts, keys, metadata, selection):
    cfg = MODELS[model_id]
    ff, ee = list(first.values()), list(eventual.values())
    normalized = normalize(model_id, ff)
    primary = metrics(normalized, keys)
    cost = prior.native16.accounted_money(attempts)
    value = {'label': cfg['label'], 'model_requested': cfg['model'],
             'provider_tag': cfg['provider_tag'], 'provider_name': cfg['provider_name'],
             'route': 'OpenRouter',
             'condition': ('decision_specialized_generative_via_native_adapter_added_october_18'
                           if model_id in tev.MODELS else 'regular_llm_reasoning_off_added_october_18'),
             'classification': ('Decision-specialized generative model via OpenRouter native adapter'
                                if model_id in tev.MODELS else 'Regular generative LLM with reasoning disabled or natively nonthinking'),
             'primary': primary, 'eventual': metrics(normalize(model_id, ee), keys),
             'statuses_first': dict(Counter(a['status'] for a in ff)),
             'http_status_first': dict(Counter(str(a['http_status']) for a in ff)),
             'recovery_attempts': len(attempts) - len(ff),
             'cost_all_attempts': cost, 'cost_first_attempts': prior.native16.accounted_money(ff),
             'cost_basis': 'API-reported only; missing charges unknown, probes excluded',
             'known_usd_per_1000_questions': cost['known_usd'] / 1136 * 1000,
             'known_usd_per_primary_correct': cost['known_usd'] / primary['correct'] if primary['correct'] else None,
             'latency_first_all': ordinary.chat.quantiles([a['latency_ms'] for a in ff]),
             'latency_first_usable': ordinary.chat.quantiles([a['latency_ms'] for a in ff if a['status'] == 'ok']),
             'latency_first_http200': ordinary.chat.quantiles([a['latency_ms'] for a in ff if a['http_status'] == 200]),
             'input_tokens_all_attempts': sum(a['usage'].get('input_tokens' if model_id in tev.MODELS else 'prompt_tokens', 0) or 0 for a in attempts),
             'output_tokens_all_attempts': sum(a['usage'].get('output_tokens' if model_id in tev.MODELS else 'completion_tokens', 0) or 0 for a in attempts),
             'reasoning_tokens_histogram': dict(Counter(str(a['reported_reasoning_tokens']) for a in ff)),
             'reasoning_text_present_count': sum(a['reasoning_text_present'] for a in ff),
             'identities': dict(Counter(a['model_returned'] or 'unreported (error)' for a in ff)),
             'dates_toronto': dict(Counter(a['started']['toronto'][:10] for a in ff)),
             'panels': panel_summary(panels(normalized, keys, selection))}
    for field in ('role', 'level'):
        value['by_' + field] = {kind: metrics([a for a in normalized if metadata[a['item_id']][field] == kind], keys)
                                for kind in sorted({r[field] for r in metadata.values()})}
    if model_id in tev.MODELS:
        value['confidence'] = []
        for threshold in (.8, .9, .95):
            retained = [a for a in normalized if valid(a) and a['normalized_confidence'] is not None
                        and a['normalized_confidence'] >= threshold]
            value['confidence'].append({'threshold': threshold, 'coverage': len(retained) / 1136,
                                        **metrics(retained, keys)})
        value['architecture_limit'] = 'Typed native response does not establish a non-generative architecture or independently audit hidden internal processing'
    else:
        value['finish_reasons'] = dict(Counter(str(a['finish_reason']) for a in ff))
    return value, normalized


def partial_summary(model_id, first, eventual, attempts, receipts, keys, model_rows, metadata):
    ff = list(first.values())
    normalized = normalize(model_id, ff)
    ids = {a['item_id'] for a in normalized}
    return {'status': 'STOPPED_SCREEN', 'label': MODELS[model_id]['label'], 'planned': 1136,
            'completed_first_attempts': len(ff), 'full_bank_completed': len(ff) == 1136,
            'main_ranking_included': False, 'full_bank_extrapolation': False,
            'stop_reasons': receipts[-1]['reasons'],
            'primary_on_completed_only': metrics(normalized, keys),
            'eventual_on_completed_only': metrics(normalize(model_id, list(eventual.values())), keys),
            'output_compliance_completed': compliance(ff),
            'latency_completed_first': ordinary.chat.quantiles([a['latency_ms'] for a in ff]),
            'cost_recorded_attempts': prior.native16.accounted_money(attempts),
            'recorded_http_attempts': len(attempts), 'recovery_attempts': len(attempts) - len(ff),
            'screen_rechecks': [{'cases': r['evaluated_first_attempts'], 'decision': r['decision'],
                                 'reasons': r['reasons']} for r in receipts],
            'same_completed_subset': {m: metrics([r for r in rows if r['item_id'] in ids], keys)
                                      for m, rows in model_rows.items()},
            'by_family_completed_only': {family: metrics([a for a in normalized if metadata[a['item_id']]['family_id'] == family], keys)
                                         for family in sorted({metadata[i]['family_id'] for i in ids})},
            'selection_limit': 'Outcome-selected sequential prefix with dependent variants and uneven family coverage; not a representative full-bank estimate'}


def analyze(key_path, write_output=False, require_settled=False):
    keys = load_key(key_path)
    base = json.loads(BASE.read_text())
    assert base['model_count'] == 36 and base['publication']['ranked_model_count'] == 33
    summary = deepcopy(base)
    rr = previous_rows(keys)
    metadata = {r['item_id']: r for r in ordinary.d.read_csv(repo_file('data/item_metadata.csv', root=ROOT))}
    selection = json.loads((repo_file('data/selection_manifest.json', root=ROOT)).read_text())
    exported = [m for m in MODELS if (PUBLIC / m / 'checksums.json').exists()]
    assert exported, 'No settled exports to analyze'
    checked = {m: validate_export(m, keys) for m in exported}
    states = {m: classify(m, PUBLIC / m) for m in exported}
    added = [m for m in exported if states[m] == 'COMPLETE_1136']
    stopped = [m for m in exported if states[m] in ('STOPPED_SCREEN', 'COMPLETE_SCREEN_FAILED')]
    blocked = [m for m in exported if states[m] == 'COMPATIBILITY_BLOCKED']
    pending = [m for m in MODELS if m not in exported]
    if require_settled:
        assert not pending, 'Active/unexported configurations remain'
    all_new, partial_attempts, probes = [], [], []
    for m in added:
        first, eventual, attempts, receipts = checked[m]
        assert len(first) == len(eventual) == 1136 and all(r['gate_result'] == 'pass' for r in receipts)
        value, normalized = model_summary(m, first, eventual, attempts, keys, metadata, selection)
        rr[m] = normalized
        summary['models'][m] = value
        for family in summary['by_family']:
            group = [a for a in normalized if metadata[a['item_id']]['family_id'] == family['family_id']]
            family['models'][m] = metrics(group, keys)
        value['macro_family_accuracy'] = sum(f['models'][m]['accuracy_attempted'] for f in summary['by_family']) / 25
        summary['output_compliance'][m] = prior.llm16.compliance(list(first.values()))
        assert summary['output_compliance'][m]['eligible_for_main_comparison']
        value['screen_rechecks'] = [{'cases': r['evaluated_first_attempts'], 'decision': r['decision'], 'reasons': r['reasons']} for r in receipts]
        summary['sessions_utc'][m] = {'started': min(a['started']['utc'] for a in attempts),
                                      'completed': max(a['completed']['utc'] for a in attempts)}
        all_new.extend(attempts)
    for m, value in base['models'].items():
        assert summary['models'][m] == value, 'Prior result changed: ' + m
    for original, expanded in zip(base['by_family'], summary['by_family']):
        for m, value in original['models'].items():
            assert expanded['models'][m] == value, 'Prior family result changed'
    summary['partial_samples'] = {}
    for m in stopped:
        first, eventual, attempts, receipts = checked[m]
        summary['partial_samples'][m] = partial_summary(m, first, eventual, attempts, receipts, keys, rr, metadata)
        partial_attempts.extend(attempts)
    summary['compatibility_only'] = {}
    for m in exported:
        probe = json.loads((PUBLIC / m / 'compatibility_probe.json').read_text())
        probes.append(probe)
        if m in blocked:
            summary['compatibility_only'][m] = {'status': 'COMPATIBILITY_BLOCKED', 'label': MODELS[m]['label'],
                'model_requested': MODELS[m]['model'], 'provider_tag': MODELS[m]['provider_tag'],
                'http_status': probe['http_status'], 'probe_status': probe['status'],
                'error_message': probe['raw_response'].get('error', {}).get('message'),
                'latency_unscored_probe_ms': probe['latency_ms'],
                'reported_probe_cost_usd': probe['reported_cost_usd'],
                'benchmark_accuracy_available': False, 'main_ranking_included': False,
                'same_model_native_adapter_completed': m == 'tev1_4b' and 'tev1_4b_native' in added}
    summary.update(status='COMPLETE_SCREENED_OCTOBER_18_LLM_ADDITIONS' if not pending else 'PARTIAL_EXPORT_ACTIVE_RUNS_PENDING',
                   model_count=len(rr), total_scored_model_questions=len(rr) * 1136,
                   llm_added_october_18_model_ids=added, llm_stopped_october_18_model_ids=stopped,
                   llm_compatibility_blocked_october_18_model_ids=blocked,
                   pending_model_ids=pending, added_model_ids=base['added_model_ids'] + added)
    # Preserve base partial_runs verbatim, especially the stopped native Solar
    # process with one unresolved dispatch. New LLM samples live separately.
    assert summary.get('partial_runs') == base.get('partial_runs')
    index = {m: {a['item_id']: a for a in rows} for m, rows in rr.items()}
    shared = [i for i in metadata if all(valid(index[m][i]) for m in rr)]
    summary['all_tested_models_answered'] = len(shared)
    summary['none_of_tested_models_correct'] = sum(not any(correct(index[m][i], keys) for m in rr) for i in metadata)
    summary['accuracy_on_shared_answered'] = {m: metrics([a for a in rows if a['item_id'] in shared], keys) for m, rows in rr.items()}
    summary['pairwise'] = [{'a': a, 'b': b, **prior.prior.pairwise(rr[a], rr[b], keys)} for a, b in itertools.combinations(rr, 2)]
    eligible = base['publication']['eligible_model_ids'] + added
    ranked_cost = sum((Decimal(summary['models'][m]['cost_all_attempts']['exact_usd']) for m in eligible), Decimal(0))
    summary['publication'].update(eligible_model_ids=eligible, ranked_model_count=len(eligible),
        ranked_model_question_cases=len(eligible) * 1136,
        none_of_ranked_models_correct=sum(not any(correct(index[m][i], keys) for m in eligible) for i in metadata),
        ranked_accounted_cost={'exact_usd': str(ranked_cost), 'known_usd': float(ranked_cost),
                               'missing_attempts': sum(summary['models'][m]['cost_all_attempts']['missing_attempts'] for m in eligible)},
        october18_llm_selection={'policy': ordinary.SCREEN_POLICY, 'cutoffs': POLICY,
            'rechecks': 'Fixed first100 followed by cumulative100-case rechecks and final1136; stopped samples never extrapolated',
            'selection_limit': 'Operational author-approved outcome selection, not preregistered superiority testing; partials and failed probes excluded'})
    selected_cost = prior.native16.accounted_money(all_new)
    partial_cost = prior.native16.accounted_money(partial_attempts)
    probe_cost = prior.native16.accounted_money(probes)
    summary['llm_october_18_experiment_costs'] = {
        'selected_full_runs': selected_cost, 'stopped_samples': partial_cost,
        'compatibility_probes': probe_cost,
        'total_new_experiment': prior.native16.accounted_money(all_new + partial_attempts + probes),
        'selected_http_attempts': len(all_new), 'stopped_http_attempts': len(partial_attempts),
        'compatibility_probe_attempts': len(probes), 'probe_cost_in_main_ranking': False,
        'partial_cost_in_main_ranking': False, 'missing_charges_are_zero': False}
    for field in ('total_selected_accounted_cost', 'total_selected_reported_cost'):
        value = summary[field]
        total = Decimal(base[field]['exact_usd']) + Decimal(selected_cost['exact_usd'])
        value.update(exact_usd=str(total), known_usd=float(total),
                     missing_attempts=base[field]['missing_attempts'] + selected_cost['missing_attempts'])
        if 'reported_attempts' in value:
            value['reported_attempts'] = base[field]['reported_attempts'] + selected_cost['reported_attempts']
        value['october18_llm_added_basis'] = 'API-reported charges from selected complete runs only; stopped samples and compatibility probes excluded'
    summary['total_selected_http_attempts'] = base['total_selected_http_attempts'] + len(all_new)
    summary['limits'] = [
        ('The prior36-model native-addition stage did not include Tev or these additional ordinary LLM runs; '
         'the current expansion adds the separately documented screened chat/native-adapter cohorts.'
         if 'No Tev1 or additional regular LLM run is included' in limit else limit)
        for limit in summary['limits']]
    summary['limits'] += [
        'October18 chat additions were selected using author-approved operational cumulative-prefix gates: accuracy below50%, model-output failures at least5%, or first-attempt median above2000ms causes a hold. Prefixes contain dependent variants and unequal family counts, not independent representative samples.',
        'Only all1136 completed and gate-passing new runs enter the overall model comparison. Stopped samples retain their actual evaluated denominator and are not extrapolated; provider failures remain separate from model-output noncompliance.',
        'Ordinary new LLMs use unchanged original prompt_text plus numeric-only suffix, max_tokens16, pinned provider and disabled reasoning or a natively nonthinking checkpoint. Per-model concurrency2 and two-question barriers match the reference protocol; at most4 ordinary models were active through the controller.',
        'Tev1 uses OpenRouter native decision adaptation because that provider rejected its documented chat interface. Tev1 remains a decision-specialized generative model; native typed output does not establish a non-generative architecture or audit hidden internal processing.',
        'The failed Tev chat and Xing free-route compatibility probes have no benchmark accuracy. Probe charges and unknown charges are accounted separately; no paid format retries or wrong-answer retries were introduced.',
        'The prior36 full-run rows, their costs, timings and archived evidence remain unchanged. New tests are not contemporaneous reruns of those baselines.'
    ]
    sources = summary['source_files_sha256']
    sources[str(logical_relative(BASE, root=ROOT))] = digest_file(BASE)
    for name in ANALYSIS_SOURCES:
        sources[name] = digest_file(repo_file(name, root=ROOT))
    for path in sorted(PUBLIC.rglob('*')):
        if path.is_file():
            sources[str(logical_relative(path, root=ROOT))] = digest_file(path)
    if write_output:
        privacy_guard((json.dumps(summary) + '\n').encode('utf-8'), 'summary.json')
        write(OVERALL / 'summary.json', summary)
        with (OVERALL / 'family_comparison.csv').open('w', newline='') as stream:
            labels = {m: summary['models'][m]['label'] for m in eligible}
            writer = csv.DictWriter(stream, fieldnames=['family_id', 'family', 'n', *labels.values()], lineterminator='\n')
            writer.writeheader()
            writer.writerows({'family_id': f['family_id'], 'family': f['family'], 'n': f['n'],
                              **{label: f['models'][m]['correct'] for m, label in labels.items()}}
                             for f in summary['by_family'])
    else:
        assert summary == json.loads((OVERALL / 'summary.json').read_text()), 'Aggregate differs from regenerated evidence'
    print(json.dumps({'model_count': len(rr), 'ranked_models': len(eligible), 'pending': pending,
                      'full_new': {m: {'correct': summary['models'][m]['primary']['correct'],
                                       'median_ms': summary['models'][m]['latency_first_all']['median_ms']} for m in added},
                      'partial_samples': {m: summary['partial_samples'][m]['completed_first_attempts'] for m in stopped},
                      'experiment_costs': summary['llm_october_18_experiment_costs']}, indent=2))
    return summary


def validate_summary():
    value = json.loads((OVERALL / 'summary.json').read_text())
    base = json.loads(BASE.read_text())
    for m, old in base['models'].items():
        assert value['models'][m] == old
    assert value['partial_runs'] == base['partial_runs']
    assert value['publication']['excluded_model_ids'] == base['publication']['excluded_model_ids']
    assert value['model_count'] == len(value['models']) == 36 + len(value['llm_added_october_18_model_ids'])
    assert value['total_scored_model_questions'] == value['model_count'] * 1136
    assert value['publication']['ranked_model_count'] == 33 + len(value['llm_added_october_18_model_ids'])
    for name, expected in value['source_files_sha256'].items():
        assert digest_file(frozen_file(repo_file(name, root=ROOT))) == expected, 'Aggregate source changed: ' + name
    all_new, all_partial, probes = [], [], []
    for m in value['llm_added_october_18_model_ids']:
        first, _, attempts, _ = validate_export(m)
        row = value['models'][m]
        assert row['primary']['attempted'] == len(first) == 1136
        assert row['primary']['answered'] == sum(a['status'] == 'ok' for a in first.values())
        assert row['primary']['correct'] + row['primary']['wrong'] + row['primary']['unanswered'] == 1136
        assert sum(f['models'][m]['correct'] for f in value['by_family']) == row['primary']['correct']
        assert row['latency_first_all'] == ordinary.chat.quantiles([a['latency_ms'] for a in first.values()])
        assert row['cost_all_attempts'] == prior.native16.accounted_money(attempts)
        assert m in value['publication']['eligible_model_ids']
        all_new.extend(attempts)
    for m in value['llm_stopped_october_18_model_ids']:
        first, _, attempts, _ = validate_export(m)
        row = value['partial_samples'][m]
        assert row['completed_first_attempts'] == len(first)
        assert row['primary_on_completed_only']['attempted'] == len(first)
        assert not row['main_ranking_included'] and not row['full_bank_extrapolation']
        assert m not in value['models'] and m not in value['publication']['eligible_model_ids']
        assert row['cost_recorded_attempts'] == prior.native16.accounted_money(attempts)
        all_partial.extend(attempts)
    for m in value['llm_compatibility_blocked_october_18_model_ids']:
        first, _, attempts, _ = validate_export(m)
        assert not first and not attempts
        assert m not in value['models'] and not value['compatibility_only'][m]['benchmark_accuracy_available']
    for m in value['llm_added_october_18_model_ids'] + value['llm_stopped_october_18_model_ids'] + value['llm_compatibility_blocked_october_18_model_ids']:
        probes.append(json.loads((PUBLIC / m / 'compatibility_probe.json').read_text()))
    cost = value['llm_october_18_experiment_costs']
    assert cost['selected_full_runs'] == prior.native16.accounted_money(all_new)
    assert cost['stopped_samples'] == prior.native16.accounted_money(all_partial)
    assert cost['compatibility_probes'] == prior.native16.accounted_money(probes)
    assert cost['total_new_experiment'] == prior.native16.accounted_money(all_new + all_partial + probes)
    print('PASS: unchanged36 baselines, selected complete runs, byte-preserved bound ledgers, actual-denominator partials, separate probes, costs and timing')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--export', nargs='+', choices=MODELS)
    parser.add_argument('--export-settled', action='store_true')
    parser.add_argument('--answer-key', type=Path)
    parser.add_argument('--write', action='store_true')
    parser.add_argument('--require-settled', action='store_true')
    args = parser.parse_args()
    if args.export_settled:
        export_settled()
    for model_id in args.export or []:
        export(model_id)
    if args.answer_key:
        analyze(args.answer_key, args.write, args.require_settled)
    elif (OVERALL / 'summary.json').exists():
        validate_summary()
