"""Offline, revision-bound scoring of the V4 Pro no-reasoning reference.

No inference, credentials or question mutation. Partial reports have explicit
matched-prefix comparisons and are never presented as full-bank rankings.
"""
import argparse
from hashlib import sha256
from html import escape
import json
from pathlib import Path
import sys

import analyze_frontier_reference as scoring
import deepseek_v4_pro_reference as run
import opus5_schema_reference as opus
from repo_layout import repo_file


def gate(stats, initial):
    enough = initial['n'] == 100
    failures = []
    if enough and initial['accuracy'] < .5:
        failures.append('initial100_accuracy_below50pct')
    if stats['n'] and stats['failed'] * 20 >= stats['n']:
        failures.append('unusable_outputs_at_least5pct')
    if stats['n'] and stats['latency_first_all']['median_ms'] > 2000:
        failures.append('median_above2sec')
    return {'initial_screen_complete': enough, 'pass': enough and not failures, 'failures': failures}


def display(report):
    s = report['statistics']
    head = (f'<tr style="background:#fff3ce"><th>DeepSeek V4 Pro 0813 — no reasoning</th>'
            f'<td>{s["correct"]}/{s["n"]} ({s["accuracy"]:.1%})</td>'
            f'<td>{s["latency_first_all"]["median_ms"]:.0f} ms</td>'
            f'<td>{s["latency_first_all"]["p95_ms"]:.0f} ms</td>'
            f'<td>${s["cost_all_attempts"]["known_usd"]:.6f} + {s["cost_all_attempts"]["missing_attempts"]} unreported</td></tr>')
    rows = []
    family_rows = []
    for m in report['comparators']:
        color = '#fff3ce' if m['kind'] == 'LLM reference' else '#dceff8'
        c = m['cost']
        price = f'${c["known_usd"]:.6f}' if c['known_usd'] is not None else 'Promotional access / unreported'
        rows.append(f'<tr style="background:{color}"><th>{escape(m["label"])}</th>'
                    f'<td>{m["correct"]}/{m["n"]} ({m["accuracy"]:.1%})</td>'
                    f'<td>{m["median_ms"]:.0f} ms</td><td>{m["p95_ms"]:.0f} ms</td><td>{price}</td></tr>')
    for fid, name in report['family_names'].items():
        f = s['families'][fid]
        if not f['n']:
            continue
        name = 'Worst-case choices without probabilities' if fid == 'F28' else name
        cells = [f] + [m['matched_statistics']['families'][fid] for m in report['comparators']]
        values = ''.join(f'<td style="background:hsl(205 65% {97-25*v["accuracy"]:.1f}%)">{v["correct"]}/{v["n"]}<br>{v["accuracy"]:.1%}</td>' for v in cells)
        family_rows.append(f'<tr><th>{escape(fid+" — "+name)}</th>{values}</tr>')
    matched = ''.join(f'<tr><th>{escape(m["label"])}</th><td>{m["matched_statistics"]["correct"]}/{s["n"]} '
                      f'({m["matched_statistics"]["accuracy"]:.1%})</td></tr>' for m in report['comparators'])
    headers = '<th>DeepSeek V4 Pro</th>' + ''.join('<th>'+escape(m['label'])+'</th>' for m in report['comparators'])
    return ('<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            '<title>DeepSeek V4 Pro — no reasoning</title><style>body{font:16px/1.5 system-ui;margin:2rem;color:#15202b}'
            'table{border-collapse:collapse;min-width:100%;margin:1rem 0}th,td{padding:.65rem;border:1px solid #cbd5e1;text-align:right}'
            'th:first-child{text-align:left;min-width:230px}.scroll{overflow:auto}thead{background:#eef2f7}</style>'
            f'<h1>DeepSeek V4 Pro 0813: {escape(report["status"])}</h1>'
            '<p>October23,2026. OpenRouter → pinned DeepInfra FP8. Reasoning explicitly disabled; every successful response '
            'must report zero reasoning tokens and contain no reasoning text. Same frozen bank, seeded Sol order, prompts, '
            'five choices, bare numeric-ID contract,16 output tokens, no tools. First attempts determine scores and timing; '
            'no answer-dependent retries. Timer covers fresh HTTPS through complete response.</p>'
            '<p>Hyper Charm was tested first on one synthetic question, not on scored questions. It returned60 reasoning tokens '
            'despite both off switches and was rejected as a System1 route. Its quota valuation is separate from OpenRouter cash usage.</p>'
            '<h2>Run status and reference context</h2><p>Partial DeepSeek scores below must not be ranked against full-bank reference scores. '
            'The matched-prefix table provides like-for-like accuracy. Blue rows are decision models; pale yellow rows are LLM references.</p>'
            '<div class="scroll"><table><thead><tr><th>Model</th><th>Correct</th><th>Median</th><th>p95</th><th>Actual run cost, USD</th></tr></thead><tbody>'
            + head + ''.join(rows) + '</tbody></table></div>'
            '<p>Cost includes recovery attempts; probes are separate. Unknown is not zero. Fastino uses token usage×tariff; '
            'promotional access does not establish a production price. Opus and Sonnet use separately labelled constrained JSON output. '
            'Different test dates, providers and server loads limit timing comparisons.</p>'
            f'<h2>Accuracy on exactly the same {s["n"]} questions</h2><table><thead><tr><th>Model</th><th>Matched score</th></tr></thead><tbody>'
            f'<tr><th>DeepSeek V4 Pro</th><td>{s["correct"]}/{s["n"]} ({s["accuracy"]:.1%})</td></tr>' + matched + '</tbody></table>'
            '<h2>Matched-question category scores</h2><div class="scroll"><table><thead><tr><th>Category</th>'+headers+'</tr></thead><tbody>'
            + ''.join(family_rows) + '</tbody></table></div><p>Exploratory developing bank, not pristine held-out evidence. '
            'Six categories have only8 questions each in the full bank. The37 author-development exclusions remain a separate1305-question diagnostic.</p></html>')


def analyze(partial=False):
    records, _ = run.validate(run.OUT, complete=not partial)
    questions, _ = run.prepare()
    hardening = run.ROOT.parent / 'text-decision-hardening'
    sys.path.insert(0, str(hardening))
    import consolidated_analysis as authority
    original = authority.CORRECTED
    try:
        authority.CORRECTED = repo_file('corrected_2026-10-18')
        gold, metadata, names, bindings = scoring.load_gold(hardening, questions)
    finally:
        authority.CORRECTED = original
    stats = scoring.summarize(records, gold, metadata)
    first = [r for r in records if r['attempt'] == 1]
    assert not any(r['reasoning_text_present'] or (isinstance(r['reported_reasoning_tokens'], int)
                   and r['reported_reasoning_tokens'] > 0) for r in records), 'Observed thinking'
    stats['mean_ms'] = sum(r['latency_ms'] for r in first) / len(first)
    stats['initial_100'] = scoring.outcomes([r for r in records if r['request_index'] <= 100], gold)
    original_ids = {q['item_id'] for q in run.d.read_csv(repo_file('corrected_2026-10-18/questions_1136.csv'))}
    stats['matched_original_1136'] = scoring.outcomes(records, {i: gold[i] for i in original_ids})
    stats['added_206'] = scoring.outcomes(records, {i: v for i, v in gold.items() if i not in original_ids})
    current_path = run.ROOT / 'results/releases/fastino_2026-10-23/statistics.json'
    current = json.loads(current_path.read_text())
    assert current['question_bank_sha256'] == run.BANK_HASH
    bindings[str(current_path)] = run.file_hash(current_path)
    matched_ids = {r['item_id'] for r in first}
    comparators = []
    for mid, path in (
            ('fastino_glide', run.ROOT / 'runs/fastino_glide_2026-10-23/text/attempts.jsonl'),
            ('reference_sol', run.base.OUT / 'attempts.jsonl')):
        m = current['models'][mid]
        other = run.d.rows(path)
        assert sum(r['status'] == 'ok' and r['choice'] == str(gold[r['item_id']]) for r in other if r['attempt'] == 1) == m['correct']
        bindings[str(path)] = run.file_hash(path)
        subset = [r for r in other if r['item_id'] in matched_ids]
        matched_stats = {'families': {fid: scoring.outcomes(subset, {i: g for i, g in gold.items() if metadata[i]['family_id'] == fid}) for fid in names},
                         **scoring.outcomes(subset, gold)}
        comparators.append({'model_id': mid, **{k: m[k] for k in ('label', 'n', 'correct', 'accuracy', 'median_ms', 'p95_ms', 'cost')},
                            'kind': current['model_kinds'][mid], 'matched_statistics': matched_stats})
    if (opus.OUT / 'completion.json').exists():
        other, _ = opus.validate(opus.OUT, complete=True)
        o = scoring.summarize(other, gold, metadata)
        subset = [r for r in other if r['item_id'] in matched_ids]
        comparators.append({'model_id': 'opus5_schema_none', 'label': 'Opus5 — disabled, JSON-choice',
                            'n': o['n'], 'correct': o['correct'], 'accuracy': o['accuracy'],
                            'median_ms': o['latency_first_all']['median_ms'], 'p95_ms': o['latency_first_all']['p95_ms'],
                            'cost': {'known_usd': o['cost_all_attempts']['known_usd'], 'unknown_attempts': o['cost_all_attempts']['missing_attempts']},
                            'kind': 'LLM reference', 'matched_statistics': {'families': {fid: scoring.outcomes(subset, {i: g for i, g in gold.items() if metadata[i]['family_id'] == fid}) for fid in names},
                                                                       **scoring.outcomes(subset, gold)}})
        bindings[str(opus.OUT / 'attempts.jsonl')] = run.file_hash(opus.OUT / 'attempts.jsonl')
    hyper_path = run.OUT.parent / 'hyper_probe/compatibility_probe.json'
    hyper = json.loads(hyper_path.read_text())['transport']
    report = {'status': 'PARTIAL_NOT_FULL_BANK' if partial else 'COMPLETE_1342', 'created': run.d.timestamps(),
              'label': 'DeepSeek V4 Pro0813 — reasoning none', 'model': run.MODEL,
              'bank_sha256': run.BANK_HASH, 'route': 'OpenRouter -> DeepInfra FP8',
              'statistics': stats, 'screening': gate(stats, stats['initial_100']),
              'family_names': names, 'comparators': comparators, 'scoring_bindings': bindings,
              'probe_cost_usd': float(run.probe_cost(run.OUT)),
              'hyper_probe': {'reasoning_tokens': 60, 'cost_usd_equivalent': hyper['raw_response']['usage']['cost']['usd'],
                              'not_a_cash_invoice': True, 'ledger_sha256': run.file_hash(hyper_path)},
              'ledger_sha256': run.file_hash(run.OUT / 'attempts.jsonl'),
              'analyzer_sha256': sha256(Path(__file__).read_bytes()).hexdigest()}
    folder = run.OUT / 'analysis' / run.d.digest({k: report[k] for k in ('status', 'ledger_sha256', 'analyzer_sha256', 'scoring_bindings')})[:16]
    folder.mkdir(parents=True, exist_ok=True)
    if (folder / 'summary.json').exists():
        saved = json.loads((folder / 'summary.json').read_text())
        assert {k: v for k, v in saved.items() if k != 'created'} == {k: v for k, v in report.items() if k != 'created'}
        report = saved
    run.d.save_bound(folder / 'summary.json', report)
    page = folder / 'report.html'
    if not page.exists():
        page.write_text(display(report))
    print(json.dumps({'status': report['status'], 'n': stats['n'], 'correct': stats['correct'], 'accuracy': stats['accuracy'],
                      'initial_100': stats['initial_100'], 'statuses': stats['statuses'], 'screening': report['screening'],
                      'latency': stats['latency_first_all'], 'mean_ms': stats['mean_ms'],
                      'cost': stats['cost_all_attempts'], 'reasoning_counts': stats['reasoning_token_counts'], 'report': str(page)}, indent=2))
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--partial', action='store_true')
    analyze(parser.parse_args().partial)
