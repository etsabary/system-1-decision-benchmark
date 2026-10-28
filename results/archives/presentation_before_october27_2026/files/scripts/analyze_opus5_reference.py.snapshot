"""Offline Opus5 scoring against the existing revision-bound private answer key.

No inference or credentials. Partial views are explicitly labelled. Writes only
aggregate, input-hashed reports under ignored runs/, never per-question keys.
"""
from __future__ import annotations

import argparse
from collections import Counter
from hashlib import sha256
from html import escape
import json
from math import comb
from pathlib import Path
import sys

import analyze_frontier_reference as scoring
import opus5_schema_reference as run
from repo_layout import repo_file


def paired(records, other, gold):
    left = {r['item_id']: r['status'] == 'ok' and r['choice'] == str(gold[r['item_id']])
            for r in records if r['attempt'] == 1}
    right = {r['item_id']: r['status'] == 'ok' and r['choice'] == str(gold[r['item_id']])
             for r in other if r['attempt'] == 1}
    assert len(right) == len(gold) == 1342
    common = set(left) & set(right)
    both = sum(left[i] and right[i] for i in common)
    only_opus = sum(left[i] and not right[i] for i in common)
    only_other = sum(right[i] and not left[i] for i in common)
    n = only_opus + only_other
    p = min(1.0, 2 * sum(comb(n, k) for k in range(min(only_opus, only_other) + 1)) / 2**n) if n else 1.0
    return {'matched_n': len(common), 'both_correct': both, 'only_opus_correct': only_opus,
            'only_other_correct': only_other, 'neither_correct': len(common)-both-only_opus-only_other,
            'exact_two_sided_mcnemar_p': p,
            'scope': 'Exploratory paired disagreement diagnostic, not adjusted for model selection or multiple comparisons'}


def html(report):
    s = report['statistics']
    def row(label, correct, n, median, p95, cost, missing):
        money = f'${cost:.6f}' if cost is not None else 'Unreported / promotional access'
        return (f'<tr><th>{escape(label)}</th><td>{correct}/{n} ({correct/n:.1%})</td>'
                f'<td>{median:.0f} ms</td><td>{p95:.0f} ms</td><td>{money}'
                + (f' + {missing} unreported' if missing else '') + '</td></tr>')
    rows = row(report['label'], s['correct'], s['n'], s['latency_first_all']['median_ms'],
               s['latency_first_all']['p95_ms'], s['cost_all_attempts']['known_usd'],
               s['cost_all_attempts']['missing_attempts'])
    for m in report['comparators']:
        rows += row(m['label'], m['correct'], m['n'], m['median_ms'], m['p95_ms'],
                    m['cost']['known_usd'], m['cost']['unknown_attempts'])
    families = []
    for fid, f in s['families'].items():
        if not f['n']:
            continue
        cells = [f] + [m['families'][fid] for m in report['comparators']]
        values = ''.join(f'<td style="background:hsl(205 65% {97-25*v["accuracy"]:.1f}%)">{v["correct"]}/{v["n"]}<br>{v["accuracy"]:.1%}</td>' for v in cells)
        families.append(f'<tr><th>{escape(fid+" — "+report["family_names"][fid])}</th>{values}</tr>')
    heads = ''.join('<th>'+escape(v)+'</th>' for v in [report['label']]+[m['label'] for m in report['comparators']])
    return ('<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            '<title>Opus 5 without thinking — benchmark</title><style>body{font:16px/1.5 system-ui;margin:2rem;max-width:1500px;color:#15202b}'
            'table{border-collapse:collapse;width:100%;margin:1rem 0}th,td{padding:.65rem;border:1px solid #cbd5e1;text-align:right}'
            'th:first-child{text-align:left;min-width:230px}thead{background:#fff3ca}.scroll{overflow:auto}code{background:#eef2f7}</style>'
            f'<h1>Opus 5 without thinking: {escape(report["status"])}</h1>'
            '<p>October 23, 2026. OpenRouter → Anthropic standard service. <code>thinking.type=disabled</code>, '
            '<code>output_config.effort=high</code>, no tools, 16-token output cap. Separately labelled constrained JSON-choice, '
            'the same grammar as Sonnet. First attempts determine accuracy and speed; recoveries are supplementary.</p>'
            '<p>All usable answers must explicitly report zero thinking tokens and no thinking blocks. Refusals are unsuccessful; '
            'missing reasoning telemetry is unverified and missing charges are unknown, not zero. Different dates and provider loads limit speed comparisons.</p>'
            '<div class="scroll"><table><thead><tr><th>Model</th><th>Correct</th><th>Median</th><th>p95</th><th>Actual bank cost (USD)</th></tr></thead><tbody>'
            + rows + '</tbody></table></div><p>Fastino cost is reported token usage × captured tariff, not returned monetary receipts. '
            'Earlier eight-question bare-ID trial and all compatibility probes remain separate.</p><h2>Category profiles</h2>'
            '<div class="scroll"><table><thead><tr><th>Category</th>'+heads+'</tr></thead><tbody>'+''.join(families)+'</tbody></table></div>'
            '<p>Exploratory development bank. Category sizes differ; six categories have only eight questions. '
            'The 37 author-development exclusions remain available in the separate 1,305-question diagnostic.</p></html>')


def analyze(partial=False):
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
    ledger = run.OUT / 'attempts.jsonl'
    raw = ledger.read_bytes()
    records = [json.loads(line) for line in raw.splitlines() if line.strip()]
    if not partial:
        run.validate(run.OUT, complete=True)
    assert not any(r['reasoning_text_present'] or (isinstance(r['reported_reasoning_tokens'], int)
                   and r['reported_reasoning_tokens'] > 0) for r in records), 'Thinking observed, including on an unsuccessful response'
    assert all((r['raw_response'].get('usage') or {}).get('service_tier') == 'standard'
               for r in records if r['status'] == 'ok'), 'Unexpected service tier'
    stats = scoring.summarize(records, gold, metadata)
    first = [r for r in records if r['attempt'] == 1]
    stats['mean_ms'] = sum(r['latency_ms'] for r in first) / len(first)
    original_ids = {q['item_id'] for q in run.d.read_csv(repo_file('corrected_2026-10-18/questions_1136.csv'))}
    stats['matched_original_1136'] = scoring.outcomes(records, {i: gold[i] for i in original_ids})
    stats['added_206'] = scoring.outcomes(records, {i: v for i, v in gold.items() if i not in original_ids})
    stats['initial_100'] = scoring.outcomes([r for r in records if r['request_index'] <= 100], gold)
    current_path = run.ROOT / 'results/releases/fastino_2026-10-23/statistics.json'
    current = json.loads(current_path.read_text())
    assert current['question_bank_sha256'] == run.native.BANK_HASH
    comparators = [current['models'][i] for i in ('fastino_glide', 'reference_sol', 'mammoth1', 'respan02', 'reference_sonnet')]
    paired_diagnostics = {}
    for name, path in (('fastino_glide', run.ROOT / 'runs/fastino_glide_2026-10-23/text/attempts.jsonl'),
                       ('reference_sol', run.native.base.OUT / 'attempts.jsonl')):
        other = drows(path)
        assert sum(r['status'] == 'ok' and r['choice'] == str(gold[r['item_id']])
                   for r in other if r['attempt'] == 1) == current['models'][name]['correct'], 'Comparator differs from its published score'
        paired_diagnostics[name] = paired(records, other, gold)
        bindings[str(path)] = sha256(path.read_bytes()).hexdigest()
    bare = drows(run.native.OUT / 'attempts.jsonl')
    report = {'status': 'PARTIAL_NOT_FULL_BANK' if partial else 'COMPLETE_1342',
              'label': 'Claude Opus 5 — thinking disabled, JSON-choice', 'model': run.MODEL,
              'created': run.d.timestamps(), 'bank_sha256': run.native.BANK_HASH,
              'statistics': stats, 'family_names': names, 'comparators': comparators,
              'paired_diagnostics': paired_diagnostics, 'scoring_bindings': bindings,
              'published_statistics_sha256': sha256(current_path.read_bytes()).hexdigest(),
              'bare_id_trial': {'n': len(bare), 'statuses_as_originally_recorded': dict(Counter(r['status'] for r in bare)),
                                'cost': run.chat.money(bare),
                                'note': 'Stopped after8:2 malformed/explanatory outputs and1 refusal. The original parser labelled the refusal with missing thinking/cost telemetry unexpected_reasoning; it is not evidence of actual thinking tokens. Ledger preserved unchanged.'},
              'compatibility_probe_cost_usd': float(run.probe_cost(run.OUT)),
              'bare_compatibility_probe_cost_usd': float(run.native.probe_cost(run.native.OUT)),
              'negative_control_cost_usd': None,
              'negative_control_cost_note': 'HTTP400 rejection omitted cost; not counted as a known zero-dollar receipt',
              'ledger_sha256': sha256(raw).hexdigest(), 'analyzer_sha256': sha256(Path(__file__).read_bytes()).hexdigest()}
    destination = run.OUT / 'analysis' / run.d.digest({'ledger': report['ledger_sha256'], 'analyzer': report['analyzer_sha256'], 'status': report['status']})[:16]
    destination.mkdir(parents=True, exist_ok=True)
    if (destination / 'summary.json').exists():
        previous = json.loads((destination / 'summary.json').read_text())
        assert {k: v for k, v in previous.items() if k != 'created'} == {k: v for k, v in report.items() if k != 'created'}
        report = previous
    run.d.save_bound(destination / 'summary.json', report)
    page = destination / 'report.html'
    if not page.exists():
        page.write_text(html(report))
    print(json.dumps({'status': report['status'], 'questions': stats['n'], 'correct': stats['correct'],
                      'accuracy': stats['accuracy'], 'initial_100': stats['initial_100'], 'statuses': stats['statuses'],
                      'latency': stats['latency_first_all'], 'mean_ms': stats['mean_ms'],
                      'cost': stats['cost_all_attempts'], 'thinking_counts': stats['reasoning_token_counts'],
                      'report': str(page)}, indent=2))
    return report


def drows(path):
    return run.d.rows(path)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--partial', action='store_true')
    args = parser.parse_args()
    analyze(args.partial)
