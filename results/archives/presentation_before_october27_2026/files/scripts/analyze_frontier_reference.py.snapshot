"""Offline scoring of the frontier reference; never sends model requests.

The separate executor cannot read the supplied private key of correct answers.
This analyzer imports the existing revision-bound private scoring authority only
when explicitly given --hardening-root. All generated evidence stays in runs/.
"""
from __future__ import annotations
from repo_layout import repo_file

import argparse
from collections import Counter
import csv
from decimal import Decimal
from hashlib import sha256
from html import escape
import json
from pathlib import Path
import sys

import frontier_reference as run
import text_models as chat


def outcomes(records, gold):
    first = [r for r in records if r['attempt'] == 1 and r['item_id'] in gold]
    assert len(first) == len({r['item_id'] for r in first})
    correct = sum(r['status'] == 'ok' and r['choice'] == str(gold[r['item_id']]) for r in first)
    answered = sum(r['status'] == 'ok' for r in first)
    return {'n': len(first), 'correct': correct, 'answered': answered,
            'failed': len(first) - answered, 'wrong_valid': answered - correct,
            'accuracy': correct / len(first) if first else None}


def summarize(records, gold, metadata):
    first, last = chat.first_and_eventual(records)
    result = outcomes(records, gold)
    result['eventual'] = outcomes([{**r, 'attempt': 1} for r in last.values()], gold)
    result['latency_first_all'] = chat.quantiles([r['latency_ms'] for r in first.values()])
    result['latency_first_usable'] = chat.quantiles([r['latency_ms'] for r in first.values() if r['status'] == 'ok'])
    result['cost_all_attempts'] = chat.money(records)
    result['cost_all_attempts']['known_usd_per_1000'] = result['cost_all_attempts']['known_usd'] / len(first) * 1000 if first else None
    result['cost_first_attempts'] = chat.money(list(first.values()))
    result['cost_recovery_attempts'] = chat.money([r for r in records if r['attempt'] == 2])
    result['attempts'] = len(records)
    result['recoveries'] = len(records) - len(first)
    result['statuses'] = dict(Counter(r['status'] for r in first.values()))
    result['reasoning_token_counts'] = dict(Counter(str(r['reported_reasoning_tokens']) for r in first.values()))
    result['reasoning_text_responses'] = sum(r['reasoning_text_present'] for r in first.values())
    result['reasoning_verification_counts'] = dict(Counter(r.get('reasoning_verification', 'explicit_reported_zero' if r['reported_reasoning_tokens'] == 0 else 'unreported') for r in first.values()))
    if any('reported_hypercredits' in r for r in records):
        values = [Decimal(str(r['reported_hypercredits'])) for r in records if r.get('reported_hypercredits') is not None]
        result['hypercredits_all_attempts'] = {'known': float(sum(values, Decimal(0))),
            'missing_attempts': len(records) - len(values), 'scope': 'Provider-reported quota debit, not a cash invoice'}
    result['usage'] = {k: sum(r['usage'].get(k, 0) for r in records) for k in ('prompt_tokens', 'completion_tokens', 'total_tokens')}
    result['returned_identities'] = dict(Counter(r['model_returned'] or 'unreported' for r in records))
    result['providers'] = dict(Counter(r['provider'] or 'unreported' for r in records))
    result['dates_toronto'] = dict(Counter(r['started']['toronto'][:10] for r in first.values()))
    result['families'] = {fid: outcomes(records, {i: g for i, g in gold.items() if metadata[i]['family_id'] == fid})
                          for fid in sorted({m['family_id'] for m in metadata.values()})}
    covered = [v['accuracy'] for v in result['families'].values() if v['n']]
    result['macro_family_accuracy'] = sum(covered) / len(covered) if covered else None
    result['new_domains'] = outcomes(records, {i: g for i, g in gold.items() if metadata[i]['family_id'] >= 'F26'})
    result['release_exclusion_diagnostic'] = outcomes(records, {i: g for i, g in gold.items()
                                  if not metadata[i]['permanently_unscored_native_development']})
    return result


def load_gold(hardening_root, questions):
    sys.path.insert(0, str(hardening_root.resolve()))
    import consolidated_analysis as authority
    bindings = {}
    metadata, gold, names, _, _ = authority.bank(bindings)
    assert set(questions) == set(gold) == set(metadata)
    for item_id, q in questions.items():
        if item_id.startswith('J'):
            digest = run.d.digest({k: q[k] for k in ('instructions', 'context', 'question', 'options')})
        else:
            rendered = q['question'].strip() + '\n\n' + '\n'.join(f'{i}. {o}' for i, o in enumerate(q['options'], 1))
            digest = sha256(rendered.encode()).hexdigest()
        assert digest == metadata[item_id]['rendered_sha256'], 'Gold bound to different question/options: ' + item_id
        assert q['family_id'] == metadata[item_id]['family_id']
    return gold, metadata, names, bindings


def comparison(stats, records, gold, published):
    correct = {r['item_id'] for r in records if r['attempt'] == 1 and r['status'] == 'ok' and r['choice'] == str(gold[r['item_id']])}
    result = []
    for mid in published['ranked_model_ids']:
        old = published['models'][mid]
        other = {r['id'] for r in published['items'] if mid in r['correct_models']}
        assert len(other) == old['correct']
        result.append({'model_id': mid, 'label': old['label'], 'correct': old['correct'],
                       'n': old['n'], 'accuracy': old['accuracy'],
                       'median_ms': old['median_ms'], 'p95_ms': old['p95_ms'],
                       'cost_all_attempts_usd': old['cost']['known_usd'],
                       'cost_unknown_attempts': old['cost']['unknown_attempts'],
                       'accuracy_gap_percentage_points': (stats['accuracy'] - old['accuracy']) * 100,
                       'median_latency_ratio': stats['latency_first_all']['median_ms'] / old['median_ms'],
                       'known_cost_ratio': stats['cost_all_attempts']['known_usd'] / old['cost']['known_usd'],
                       'both_correct': len(correct & other), 'only_reference_correct': len(correct - other),
                       'only_decision_model_correct': len(other - correct),
                       'neither_correct': len(gold) - len(correct | other)})
    return result


def html_report(report, published, names):
    s = report['statistics']
    label = report['label']
    extras = report.get('other_frontier_references', [])
    leaders = published['ranked_model_ids'][:4] + ['jev114', 'luna_decisions']
    rows = [{'label': label + ' — frontier reference',
             'correct': s['correct'], 'n': s['n'], 'accuracy': s['accuracy'],
             'median_ms': s['latency_first_all']['median_ms'], 'p95_ms': s['latency_first_all']['p95_ms'],
             'cost': s['cost_all_attempts']['known_usd'], 'unknown': s['cost_all_attempts']['missing_attempts']}]
    for extra in extras:
        v = extra['statistics']
        rows.append({'label': extra['label'] + ' — frontier reference',
                     'correct': v['correct'], 'n': v['n'], 'accuracy': v['accuracy'],
                     'median_ms': v['latency_first_all']['median_ms'], 'p95_ms': v['latency_first_all']['p95_ms'],
                     'cost': v['cost_all_attempts']['known_usd'], 'unknown': v['cost_all_attempts']['missing_attempts']})
    for mid in leaders:
        v = published['models'][mid]
        rows.append({**v, 'cost': v['cost']['known_usd'], 'unknown': v['cost']['unknown_attempts']})
    summary = ''.join('<tr><th>' + escape(v['label']) + '</th><td>' + f"{v['correct']}/{v['n']} ({v['accuracy']:.1%})" +
                      f"</td><td>{v['median_ms']/1000:.3f}s</td><td>{v['p95_ms']/1000:.3f}s</td><td>${v['cost']:.6f}" +
                      (f" + {v['unknown']} unknown" if v['unknown'] else '') + '</td></tr>' for v in rows)
    family_rows = []
    for fid in sorted(names):
        cells = [s['families'][fid]] + [v['statistics']['families'][fid] for v in extras] + [published['models'][mid]['families'][fid] for mid in leaders]
        family_name = 'Worst-case choices without probabilities' if fid == 'F28' else names[fid]
        values = ''.join(f'<td style="background:hsl(205 70% {97-22*v["accuracy"]:.1f}%)">{v["correct"]}/{v["n"]}<br>{v["accuracy"]:.1%}</td>' for v in cells)
        family_rows.append(f'<tr><th>{escape(fid + " — " + family_name)}</th>{values}</tr>')
    headings = [label] + [v['label'] for v in extras] + [published['models'][mid]['label'] for mid in leaders]
    populations = []
    for name, value in [(label, s)] + [(r['label'], r['statistics']) for r in extras]:
        if 'matched_original_1136' in value:
            old, added = value['matched_original_1136'], value['added_206']
            populations.append((name, value['correct'], old['correct'], added['correct']))
    old_baseline = report.get('baseline_original_1136', {})
    if 'respan02' in old_baseline:
        full = published['models']['respan02']['correct']
        old = old_baseline['respan02']['correct']
        populations.append(('Respan Span-02', full, old, full - old))
    population_table = '<h2>Matched-bank diagnostic</h2><p>The full 1,342 remains the main result. These subsets show the effect of the additions, not separate leaderboard populations.</p><table><thead><tr><th>Model</th><th>All 1,342</th><th>Original 1,136</th><th>Added 206</th></tr></thead><tbody>'
    for name, full, old, added in populations:
        population_table += f'<tr><th>{escape(name)}</th><td>{full}/1342 ({full/1342:.1%})</td><td>{old}/1136 ({old/1136:.1%})</td><td>{added}/206 ({added/206:.1%})</td></tr>'
    population_table += '</tbody></table>'
    return ('<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            '<title>' + escape(label) + ' — frontier reference</title><style>'
            'body{font:16px/1.5 system-ui;margin:2rem;max-width:1500px;color:#15202b}h1{font-size:1.8rem}'
            'table{border-collapse:collapse;width:100%;margin:1.5rem 0}th,td{padding:.65rem;border:1px solid #cbd5e1;text-align:right}'
            'th:first-child{text-align:left;min-width:260px}thead{background:#e2e8f0}.scroll{overflow:auto}small{color:#475569}</style>'
            '<h1>' + escape(label) + ': 1,342-question frontier reference</h1>'
            '<p>Test date: October 19, 2026 (America/Toronto). OpenRouter → OpenAI, standard service tier; '
            .replace('OpenRouter → OpenAI, standard service tier; ', escape(report.get('route_description', 'OpenRouter → OpenAI, standard service tier')) + '; ') +
            '<code>' + escape(report.get('reasoning_description', 'reasoning.effort=none')) + '</code>, no tools, 16 output tokens maximum. ' +
            escape(report.get('reasoning_verification_note', 'Every successful response is checked for zero reasoning tokens.')) + '</p>'
            '<p>First attempts determine accuracy and speed. Transient recoveries are separate; their charges are included. '
            'Timing uses the same fresh-HTTPS/full-response timer as the decision-model comparison, but different dates, endpoints and loads are not controlled away.</p>'
            '<div class="scroll"><table><thead><tr><th>Model</th><th>Correct / questions</th><th>Median</th><th>p95</th><th>Full-bank reported cost / quota value (USD)</th></tr></thead><tbody>' + summary +
            '</tbody></table></div><p>Costs above cover 1,342-question runs, not costs per 1,000. ' + escape(report.get('cost_scope_note', 'API-reported charges.')) + ' This reference’s compatibility probes: '
            f'${report["compatibility_probe_cost_usd"]:.5f}, excluded from scored-run cost. Unknown charges are not zero.</p>' +
            population_table + '<h2>All 31 categories</h2><p>Each cell shows correct/questions and accuracy. New domains F26–F31 have only eight questions each.</p>'
            '<div class="scroll"><table><thead><tr><th>Category</th>' + ''.join('<th>' + escape(h) + '</th>' for h in headings) +
            '</tr></thead><tbody>' + ''.join(family_rows) + '</tbody></table></div>'
            '<p><small>Exploratory development bank, not a pristine held-out score. The 37 author-development cases retain their permanent release exclusions '
            'in the separate 1,305-case diagnostic. Model routes and question variants are correlated. This report does not alter the published decision-model leaderboard.</small></p></html>')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out', type=Path)
    p.add_argument('--model', choices=('sol', 'sonnet', 'sonnet-schema', 'hyper', 'minimax'), default='sol')
    p.add_argument('--compare-summary', type=Path, action='append', default=[])
    p.add_argument('--hardening-root', type=Path, required=True)
    p.add_argument('--partial', action='store_true', help='Read a snapshot of first attempts; never publish as a full-bank score')
    args = p.parse_args()
    active = run
    if args.model == 'sonnet':
        import sonnet55_reference as active
    elif args.model == 'sonnet-schema':
        import sonnet55_schema_reference as active
    elif args.model == 'hyper':
        import hyper_reference as active
    elif args.model == 'minimax':
        import minimax_sambanova_reference as active
    args.out = args.out or active.OUT
    questions, _ = run.prepare()
    gold, metadata, names, bindings = load_gold(args.hardening_root, questions)
    if args.partial:
        records = run.d.rows(args.out / 'attempts.jsonl')
        stats = summarize(records, gold, metadata)
        print(json.dumps({'status': 'PARTIAL_NOT_FULL_BANK', 'statistics': stats}, indent=2))
        return
    records, _ = active.validate(args.out, complete=True)
    stats = summarize(records, gold, metadata)
    assert stats['n'] == 1342 and sum(v['n'] for v in stats['families'].values()) == 1342
    published = json.loads((repo_file('consolidated_2026-10-19/statistics.json', root=run.ROOT)).read_text())
    # Individual correctness is deliberately absent from the public aggregate.
    # Resolve the exact private source by its already-published checksum.
    source_hash = json.loads((repo_file('consolidated_2026-10-19/manifest.json', root=run.ROOT)).read_text())['source_summary_sha256']
    candidates = list((args.hardening_root / 'runs/consolidated_1342_2026-10-19/analysis').glob('*/summary.json'))
    matching = [path for path in candidates if run.file_hash(path) == source_hash]
    assert len(matching) == 1, 'Cannot bind private item-level reference evidence'
    private_reference = json.loads(matching[0].read_text())
    assert {r['id'] for r in private_reference['items']} == set(gold)
    bindings[str(matching[0].resolve())] = source_hash
    paired_reference = {**published, 'items': private_reference['items']}
    original_ids = {r['item_id'] for r in run.d.read_csv(repo_file('corrected_2026-10-18/questions_1136.csv', root=run.ROOT))}
    stats['matched_original_1136'] = outcomes(records, {i: gold[i] for i in original_ids})
    stats['added_206'] = outcomes(records, {i: g for i, g in gold.items() if i not in original_ids})
    stats['initial_100'] = outcomes([r for r in records if r['request_index']<=100],gold)
    probe = active.validate_probe(args.out)
    probe_cost = active.probe_cost(args.out) if args.model != 'sol' else Decimal(str(probe['reported_cost_usd']))
    extras = []
    for path in args.compare_summary:
        other = json.loads(path.read_text())
        seal = json.loads((path.parent / 'checksums.json').read_text())
        assert run.file_hash(path) == seal['summary.json']
        assert other['bank_sha256'] == run.BANK_HASH and other['statistics']['n'] == 1342
        extras.append({k: other[k] for k in ('model', 'label', 'statistics')})
    labels = {'sol': 'GPT-6 Sol (reasoning none)', 'sonnet': 'Sonnet 5.5 (no thinking, bare ID)',
              'sonnet-schema': 'Sonnet 5.5 (no thinking, JSON-choice)', 'hyper': 'Qwen3.8-Max (none, Hyper Charm)',
              'minimax': 'MiniMax M3 (no thinking, SambaNova)'}
    legacy = json.loads((repo_file('corrected_2026-10-18/summary.json', root=run.ROOT)).read_text())
    report = {'status': 'COMPLETE_FRONTIER_REFERENCE_1342', 'model': active.MODEL,
              'label': labels[args.model],
              'route_description': ('Hyper Charm direct, sequential capacity1' if args.model == 'hyper' else
                                    'OpenRouter → SambaNova, pinned MiniMax M3 route' if args.model == 'minimax' else
                                    'OpenRouter → Anthropic, standard service' if args.model.startswith('sonnet') else 'OpenRouter → OpenAI, standard service tier'),
              'reasoning_description': ('reasoning_effort=none, documented/catalog-supported' if args.model == 'hyper' else
                                        'reasoning.enabled=false' if args.model == 'minimax' else
                                        'thinking.type=between_tools; effort=high; no tools' if args.model.startswith('sonnet') else 'reasoning.effort=none'),
              'reasoning_verification_note': ('Provider omits reasoning-token telemetry. The none setting is catalog-supported and requested explicitly; no reasoning text is allowed. Unknown token counts are not treated as verified zeros.' if args.model == 'hyper' else 'Every successful response reports exactly zero reasoning/thinking tokens, with no reasoning content.'),
              'cost_scope_note': ('Hyper Charm rows show provider-reported USD-equivalent quota usage, not additional cash billing; reported Hypercredits are retained separately. No purchases or top-ups were made.' if args.model == 'hyper' else 'API-reported charges, not funding fees. Hyper Charm reference rows, if present, are quota valuations rather than cash invoices.'),
              'baseline_original_1136': {mid: legacy['models'][mid]['primary'] for mid in published['ranked_model_ids']},
              'bank_sha256': run.BANK_HASH, 'other_frontier_references': extras,
              'statistics': stats, 'compatibility_probe_cost_usd': float(probe_cost),
              'total_known_spend_including_probe_usd': float(Decimal(stats['cost_all_attempts']['exact_usd']) + probe_cost),
              'comparisons': comparison(stats, records, gold, paired_reference),
              'gold_source_bindings': bindings, 'names': names,
              'completion_sha256': run.file_hash(args.out / 'completion.json'),
              'published_comparison_sha256': run.file_hash(repo_file('consolidated_2026-10-19/statistics.json', root=run.ROOT)),
              'analysis_source_sha256': run.file_hash(Path(__file__)),
              'limits': ['Exploratory development bank;37 permanently excluded author-development questions are not a held-out release score.',
                         'Same timing boundary, not synchronized inference. Dates, loads, endpoint/protocol and provider implementation can differ.',
                         'Cost excludes gateway funding fees; missing charges are unknown, never zero.',
                         'Full-bank frontier reference, not a newly qualified specialized decision model. No public ranking has been changed.']}
    report['operational_evidence'] = {name: run.file_hash(args.out/name)
        for name in ('operator_events.jsonl','provider_cooldown.json','provider_cooldown_extension.json',
                     'pacing_receipt.json','pacing_waits.jsonl') if (args.out/name).exists()}
    route_probes=args.out/'route_selection_probes.json'
    report['compatibility_probe_unknown_attempts'] = (sum(active.parse(v['transport'])['reported_cost_usd'] is None
        for v in json.loads(route_probes.read_text())) if route_probes.exists() else 0)
    analysis = args.out / 'analysis' / run.d.digest(report)[:16]
    analysis.mkdir(parents=True, exist_ok=True)
    run.d.save_bound(analysis / 'summary.json', report)
    with (analysis / 'category_scores.csv').open('w', newline='') as stream:
        writer = csv.writer(stream)
        writer.writerow(['family_id', 'family', 'questions', 'correct', 'accuracy'])
        for fid, value in stats['families'].items():
            writer.writerow([fid, names[fid], value['n'], value['correct'], value['accuracy']])
    (analysis / 'report.html').write_text(html_report(report, published, names))
    run.d.save_bound(analysis / 'checksums.json', {n: run.file_hash(analysis / n) for n in ('summary.json', 'category_scores.csv', 'report.html')})
    print(json.dumps({'status': report['status'], 'statistics': stats,
                      'compatibility_probe_cost_usd': float(probe_cost),
                      'report': str(analysis / 'report.html'), 'summary': str(analysis / 'summary.json')}, indent=2))


if __name__ == '__main__':
    main()
