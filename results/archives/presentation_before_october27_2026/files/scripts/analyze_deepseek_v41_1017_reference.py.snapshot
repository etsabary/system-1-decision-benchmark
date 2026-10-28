"""Offline dated DeepSeek no-reasoning scoring and local comparison report.

Never sends inference or exposes the supplied key. Old measurements remain
unchanged. A complete Opus run is included as a separately labelled reference.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
from html import escape
import json
from pathlib import Path
import sys

import analyze_frontier_reference as scoring
from analyze_opus5_reference import paired
import deepseek_v41_1017_reference as run
import opus5_schema_reference as opus
from repo_layout import repo_file


def display(report):
    stats = report['statistics']
    models = [{'label': 'DeepSeek V4.1 Flash 1017 — reasoning none', 'n': stats['n'],
               'correct': stats['correct'], 'accuracy': stats['accuracy'],
               'median_ms': stats['latency_first_all']['median_ms'], 'p95_ms': stats['latency_first_all']['p95_ms'],
               'cost': stats['cost_all_attempts']['known_usd'], 'missing': stats['cost_all_attempts']['missing_attempts'],
               'families': stats['families'], 'kind': 'LLM reference'}] + report['comparators']
    models.sort(key=lambda m: -m['accuracy'])
    rows = []
    for m in models:
        price = f'${m["cost"]:.6f}' if m['cost'] is not None else 'Promotional free access'
        extra = f' + {m["missing"]} unreported' if m['missing'] and m['cost'] is not None else ''
        tint = '#fff3ce' if m['kind'] == 'LLM reference' else '#dceff8'
        rows.append(f'<tr style="background:{tint}"><th>{escape(m["label"])}</th><td>{m["correct"]}/{m["n"]} ({m["accuracy"]:.1%})</td>'
                    f'<td>{m["median_ms"]:.0f} ms</td><td>{m["p95_ms"]:.0f} ms</td><td>{price}{extra}</td></tr>')
    headers = ''.join('<th>'+escape(m['label'])+'</th>' for m in models)
    families = []
    for fid, name in report['family_names'].items():
        name = 'Worst-case choices without probabilities' if fid == 'F28' else name
        cells = []
        for m in models:
            f = m['families'][fid]
            if not f['n']:
                cells.append('<td>Not tested yet</td>')
            else:
                cells.append(f'<td style="background:hsl(205 65% {97-25*f["accuracy"]:.1f}%)">{f["correct"]}/{f["n"]}<br>{f["accuracy"]:.1%}</td>')
        families.append('<tr><th>'+escape(fid+' — '+name)+'</th>'+''.join(cells)+'</tr>')
    return ('<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            '<title>New no-reasoning LLM references — October 23, 2026</title><style>body{font:16px/1.5 system-ui;margin:2rem;color:#15202b}'
            'table{border-collapse:collapse;min-width:100%;margin:1rem 0}th,td{padding:.65rem;border:1px solid #cbd5e1;text-align:right}'
            'th:first-child{text-align:left;min-width:220px}.scroll{overflow:auto}thead{background:#eef2f7}</style>'
            f'<h1>DeepSeek V4.1 Flash 1017: {escape(report["status"])}</h1>'
            '<p>Tested October 23, 2026. OpenRouter → DeepInfra FP8, pinned 1017 update; reasoning disabled, '
            '16 output tokens and no tools. '+escape(report['output_contract'])+'. Native DeepSeek route was blocked by existing account privacy policy; no settings were changed.</p>'
            '<p>Same frozen 1,342 questions and seeded order. First attempts determine scores and timing, including unsuccessful responses. '
            'Successful answers must report exactly zero reasoning tokens and no reasoning content. No retries for wrong answers or format failures.</p>'
            '<p>Blue rows are specialized decision models; pale yellow rows are no-reasoning LLM references. '
            'Opus and Sonnet use separately labelled JSON-choice output grammars. Costs below cover each actual 1,342-question run, not 1,000 questions. '
            'Different dates and server loads limit speed comparisons.</p><div class="scroll"><table><thead><tr><th>Model</th><th>Correct</th><th>Median</th><th>p95</th><th>Bank cost, USD</th></tr></thead><tbody>'
            + ''.join(rows) + '</tbody></table></div><p>Fastino cost is token usage × tariff, not returned monetary receipts. '
            'Unknown charges remain unknown; promotional access is not a zero-dollar production tariff. Probes and stopped format trials are separate.</p>'
            '<h2>All 31 categories</h2><div class="scroll"><table><thead><tr><th>Category</th>'+headers+'</tr></thead><tbody>'+''.join(families)+'</tbody></table></div>'
            '<p>Exploratory developing bank, not a pristine held-out ranking. The six newest categories each have eight questions. '
            'The 37 permanent author-development exclusions are retained in the separate 1,305-question diagnostic.</p></html>')


def analyze(partial=False):
    run.configure('deepinfra')
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
    path = run.OUT / 'attempts.jsonl'
    raw = path.read_bytes()
    records = [json.loads(line) for line in raw.splitlines() if line.strip()]
    if not partial:
        run.validate(run.OUT, complete=True)
    stats = scoring.summarize(records, gold, metadata)
    first = [r for r in records if r['attempt'] == 1]
    assert not any(r['reasoning_text_present'] or (isinstance(r['reported_reasoning_tokens'], int)
                   and r['reported_reasoning_tokens'] > 0) for r in records)
    stats['mean_ms'] = sum(r['latency_ms'] for r in first) / len(first)
    stats['initial_100'] = scoring.outcomes([r for r in records if r['request_index'] <= 100], gold)
    original_ids = {q['item_id'] for q in run.d.read_csv(repo_file('corrected_2026-10-18/questions_1136.csv'))}
    stats['matched_original_1136'] = scoring.outcomes(records, {i: gold[i] for i in original_ids})
    stats['added_206'] = scoring.outcomes(records, {i: v for i, v in gold.items() if i not in original_ids})
    published_path = run.ROOT / 'results/releases/fastino_2026-10-23/statistics.json'
    current = json.loads(published_path.read_text())
    assert current['question_bank_sha256'] == run.BANK_HASH
    comparators = []
    for mid in ('fastino_glide', 'reference_sol', 'mammoth1', 'respan02', 'reference_sonnet'):
        m = current['models'][mid]
        comparators.append({'model_id': mid, **{k: m[k] for k in ('label', 'n', 'correct', 'accuracy', 'median_ms', 'p95_ms', 'families')},
                            'cost': m['cost']['known_usd'], 'missing': m['cost']['unknown_attempts'], 'kind': current['model_kinds'][mid]})
    if (opus.OUT / 'completion.json').exists():
        opus_records, _ = opus.validate(opus.OUT, complete=True)
        o = scoring.summarize(opus_records, gold, metadata)
        comparators.append({'model_id': 'opus5_schema_none', 'label': 'Opus 5 — disabled, JSON-choice',
                            'n': o['n'], 'correct': o['correct'], 'accuracy': o['accuracy'],
                            'median_ms': o['latency_first_all']['median_ms'], 'p95_ms': o['latency_first_all']['p95_ms'],
                            'families': o['families'], 'cost': o['cost_all_attempts']['known_usd'],
                            'missing': o['cost_all_attempts']['missing_attempts'], 'kind': 'LLM reference'})
        bindings[str(opus.OUT / 'attempts.jsonl')] = run.file_hash(opus.OUT / 'attempts.jsonl')
    diagnostic = {}
    for mid, other_path in (('fastino_glide', run.ROOT / 'runs/fastino_glide_2026-10-23/text/attempts.jsonl'),
                            ('reference_sol', run.base.OUT / 'attempts.jsonl')):
        other = run.d.rows(other_path)
        assert sum(r['status'] == 'ok' and r['choice'] == str(gold[r['item_id']]) for r in other if r['attempt'] == 1) == current['models'][mid]['correct']
        diagnostic[mid] = paired(records, other, gold)
        bindings[str(other_path)] = run.file_hash(other_path)
    report = {'status': 'PARTIAL_NOT_FULL_BANK' if partial else 'COMPLETE_1342', 'created': run.d.timestamps(),
              'model': run.MODEL, 'route': 'OpenRouter → DeepInfra FP8', 'bank_sha256': run.BANK_HASH,
              'output_contract': getattr(run, 'FORMAT', 'Bare numeric-ID output contract'),
              'statistics': stats, 'family_names': names, 'comparators': comparators,
              'paired_diagnostics': diagnostic, 'scoring_bindings': bindings,
              'probe_cost_usd': float(run.probe_cost(run.OUT)),
              'native_provider_probe': 'Separate HTTP404: paid-model-training privacy policy excluded native DeepSeek endpoint; no settings changed',
              'ledger_sha256': sha256(raw).hexdigest(), 'analyzer_sha256': sha256(Path(__file__).read_bytes()).hexdigest(),
              'published_statistics_sha256': run.file_hash(published_path)}
    folder = run.OUT / 'analysis' / run.d.digest({k: report[k] for k in ('status', 'ledger_sha256', 'analyzer_sha256')})[:16]
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
                      'initial_100': stats['initial_100'], 'statuses': stats['statuses'], 'latency': stats['latency_first_all'],
                      'cost': stats['cost_all_attempts'], 'reasoning_counts': stats['reasoning_token_counts'], 'report': str(page)}, indent=2))
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--partial', action='store_true')
    parser.add_argument('--schema', action='store_true')
    args = parser.parse_args()
    if args.schema:
        import deepseek_v41_1017_schema_reference as run
    analyze(args.partial)
