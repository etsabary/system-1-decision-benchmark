"""Offline, frozen-key Fastino analysis. No credentials or inference transport.

Produces private, input-hashed aggregate JSON and an HTML report in ignored runs/.
Never writes per-question keys or correctness to a publication directory.
"""
import argparse
from collections import Counter
from decimal import Decimal
from hashlib import sha256
from html import escape
import json
from pathlib import Path
import sys

import fastino_glide_2026_10_23 as run
import decision_refresh as d
from analyze_frontier_reference import load_gold
from analyze_direct_decisions_2026_10_20 import statistics, cost
from repo_layout import repo_file


def probes(out):
    values = []
    for path in sorted(out.glob('probe_*_attempt_*.json')):
        value = json.loads(path.read_text())
        row = value['response']
        values.append(dict(row, **value['parsed']))
    return dict(attempts=len(values), cost=cost(values, 'accounted_cost_usd'),
                api_reported_cost=cost(values, 'reported_cost_usd'))


def analyze(image_answer_key):
    questions, _ = run.text_bank.prepare()
    hardening = run.ROOT.parent/'text-decision-hardening'
    sys.path.insert(0, str(hardening))
    import consolidated_analysis as authority
    # The October22 high-level folder cleanup relocated, but did not rewrite,
    # dated evidence. Adapt only this explicit directory; all original seals,
    # key hashes and question-to-key semantic checks still run unchanged.
    original_corrected = authority.CORRECTED
    try:
        authority.CORRECTED = repo_file('corrected_2026-10-18')
        gold, meta, names, bindings = load_gold(hardening, questions)
    finally:
        authority.CORRECTED = original_corrected
    bindings[str(hardening/'consolidated_analysis.py')] = run.file_hash(hardening/'consolidated_analysis.py')
    published = json.loads(repo_file('native_additions_2026-10-21/statistics.json').read_text())
    report = dict(created=d.timestamps(), model_requested=run.MODEL, source_urls=run.SOURCES,
        version_note='Authenticated live catalog says one-pass GLiDE v2.2; responses identify glide_v2. Hosted alias is not an immutable weight/version attestation.',
        scoring='First attempts including errors. Probes and recovery outcomes never replace first results.',
        cost_note='USD cost calculated from API input_tokens and captured $0.04/M input, $0 output tariff where monetary receipts absent. Probe costs are separate.',
        timing='Fresh HTTPS connect through complete response; same timer boundary as existing runs. Text max2 per barrier wave, image serial. No batching independent states.',
        groups={})
    hashes = {}
    for kind in ('text','image'):
        out = run.OUT/kind
        path = out/'attempts.jsonl'
        raw = path.read_bytes() if path.exists() else b''
        records = [json.loads(line) for line in raw.splitlines() if line.strip()]
        hashes[kind] = sha256(raw).hexdigest() if path.exists() else None
        if not records:
            continue
        # Complete or stopped streams are reconciled; live partial views never replay dispatches.
        settled = (out/'completion.json').exists() or (out/'stop.json').exists()
        if settled:
            run.validate(kind, out)
        if kind == 'text':
            scores = statistics(records, gold, meta)
            scores.update(median_ms=scores['latency']['median_ms'], p95_ms=scores['latency']['p95_ms'],
                          mean_ms=scores['mean_response_ms'])
            scores['family_names'] = names
            refs = [dict(model_id=k, label=m['label'], correct=m['correct'], n=m['n'], accuracy=m['accuracy'],
                    median_ms=m['median_ms'], p95_ms=m['p95_ms'], cost=m['cost'],
                    kind=published.get('model_kinds',{}).get(k,'Decision model')) for k,m in published['models'].items()]
            refs.sort(key=lambda v:(-v['accuracy'], v['median_ms']))
            scores['existing_full_bank_references'] = refs
            report['text_gold_bindings'] = bindings
        else:
            image = run.image_bank()
            with run.visual_imports():
                import analyze_native_images as image_analysis
                from score import load_key
            assert run.file_hash(image_answer_key) == image_analysis.KEY_HASH, 'Frozen image key changed'
            key = load_key(image_answer_key)
            qs, _, _ = image.inputs()
            assert set(key) == set(qs)
            provenance = {q['candidate_id']:q for q in d.rows(run.VISUAL/'data/provenance.jsonl')}
            scores = image_analysis.summarize(records, key, qs, provenance)
            scores['cost'] = cost(records,'accounted_cost_usd')
            scores['api_reported_cost'] = cost(records,'reported_cost_usd')
            scores['family_names'] = {f:n for f,(n,_) in image_analysis.FAMILIES.items()}
            baseline = json.loads((run.VISUAL/'native_images_2026-10-20/summary.json').read_text())
            refs = [dict(model_id=k, label=m['label'], correct=m['correct'], n=m['n'], accuracy=m['accuracy'],
                    median_ms=m['median_ms'], p95_ms=m['p95_ms'],
                    cost=dict(known_usd=float(m['core_cost']['accounted_usd']),
                              unknown_attempts=m['core_cost']['missing_api_records']), kind='Decision model')
                    for k,m in baseline['models'].items()]
            refs.sort(key=lambda v:(-v['accuracy'],v['median_ms']))
            scores['existing_full_bank_references'] = refs
            report['image_key_sha256'] = image_analysis.KEY_HASH
        n = scores['n']
        planned = 1342 if kind == 'text' else 200
        scores.update(planned=planned, complete=(out/'completion.json').exists(),
            stop=json.loads((out/'stop.json').read_text()) if (out/'stop.json').exists() else None,
            probe=probes(out), metadata=json.loads((out/'model_metadata.json').read_text()),
            usage_cost_per_1000_usd=scores['cost']['known_usd']*1000/n if n else None,
            statuses=dict(Counter(r['status'] for r in records if r['attempt']==1)),
            first_attempt_input_tokens=sum(r['usage'].get('input_tokens') or 0 for r in records if r['attempt']==1),
            retention_headers=dict(Counter(r['response_headers'].get('x-fastino-data-retention','unreported') for r in records)))
        report['groups'][kind] = scores
    report['ledger_sha256'] = hashes
    report['analyzer_sha256'] = run.file_hash(Path(__file__))
    dest = run.OUT/'analysis'/d.digest(dict(ledgers=hashes,analyzer=report['analyzer_sha256'],
        complete={k:s['complete'] for k,s in report['groups'].items()}))[:16]
    dest.mkdir(parents=True,exist_ok=True)
    # The snapshots are input-addressed; do not overwrite prior snapshots while runs progress.
    json_path = dest/'statistics.json'
    if json_path.exists():
        old = json.loads(json_path.read_text())
        assert old['ledger_sha256'] == hashes and old['analyzer_sha256'] == report['analyzer_sha256']
        report = old
    else:
        d.save_bound(json_path,report)
    html_path = dest/'report.html'
    html = render(report)
    if html_path.exists():
        assert html_path.read_text() == html
    else:
        html_path.write_text(html)
    return report, html_path


def render(report):
    body = ['<!doctype html><meta charset="utf-8"><title>Fastino GLiDE — benchmark results</title>',
        '<style>body{font:17px/1.5 system-ui;max-width:1300px;margin:35px auto;padding:0 25px;color:#203142}'
        'table{border-collapse:collapse;width:100%;margin:20px 0}th,td{text-align:left;padding:10px;border-bottom:1px solid #ccd5dd}'
        'thead{background:#eaf2f8}.new{background:#dceeff}.note{background:#f4f5f6;padding:15px}h2{margin-top:45px}</style>',
        '<h1>Fastino GLiDE — text and image decisions</h1>',
        '<p>'+escape(report['version_note'])+'</p>',
        '<p class="note">'+escape(report['scoring']+' '+report['cost_note'])+'</p>']
    for kind,s in report['groups'].items():
        body.append('<h2>'+kind.title()+f': {s["correct"]}/{s["n"]} · {s["accuracy"]:.1%}</h2>')
        state = 'Complete' if s['complete'] else 'Stopped: '+s['stop']['reason'] if s['stop'] else 'In progress — preliminary subset, not a full-bank rank'
        body.append(f'<p>{escape(state)}. Median {s["median_ms"]:.1f} ms; p95 {s["p95_ms"]:.1f} ms; mean {s["mean_ms"]:.1f} ms. '
                    f'Usage-based run cost ${s["cost"]["known_usd"]:.6f}; ${s["usage_cost_per_1000_usd"]:.6f} per 1,000. '
                    f'Unknown-cost attempts: {s["cost"]["unknown_attempts"]}. Probe cost: ${s["probe"]["cost"]["known_usd"]:.7f}.</p>')
        if kind == 'text':
            body.append('<p>Original 1,136: '+str(s['original_1136']['correct'])+'/'+str(s['original_1136']['n'])+
                        '; added 206: '+str(s['added_206']['correct'])+'/'+str(s['added_206']['n'])+'.</p>')
        rows = [dict(label='Fastino GLiDE (live catalog v2.2)', correct=s['correct'], n=s['n'], accuracy=s['accuracy'],
            median_ms=s['median_ms'],p95_ms=s['p95_ms'],cost=s['cost'],new=True)]
        rows.extend(s['existing_full_bank_references'][:8])
        if s['complete']:
            rows.sort(key=lambda r:(-r['accuracy'],r['median_ms']))
        body.append('<h3>Selected existing full-bank references</h3><p>Reference runs retain their original dates and measurements. Small accuracy gaps are not automatically statistically meaningful.</p>'
            '<table><thead><tr><th>Model</th><th>Correct / questions</th><th>Accuracy</th><th>Median</th><th>p95</th><th>Run cost</th></tr></thead><tbody>')
        for row in rows:
            amount = row['cost']['known_usd']
            price = f'${amount:.6f}' if amount is not None else 'Not reported'
            body.append('<tr'+(' class="new"' if row.get('new') else '')+'><th>'+escape(row['label'])+'</th>'+
                f'<td>{row["correct"]}/{row["n"]}</td><td>{row["accuracy"]:.1%}</td><td>{row["median_ms"]:.0f} ms</td>'+
                f'<td>{row["p95_ms"]:.0f} ms</td><td>{price}</td></tr>')
        body.append('</tbody></table><h3>Categories — Fastino</h3><table><thead><tr><th>Category</th><th>Correct / questions</th><th>Accuracy</th></tr></thead><tbody>')
        for fid,f in s['families'].items():
            name = s['family_names'][fid]
            if isinstance(name,dict):
                name = name.get('name') or str(name)
            acc = f['correct']/f['n'] if f['n'] else None
            pct = f'{acc:.1%}' if acc is not None else 'Not yet measured'
            body.append(f'<tr><th>{escape(fid+" — "+str(name))}</th><td>{f["correct"]}/{f["n"]}</td><td>{pct}</td></tr>')
        body.append('</tbody></table>')
    body.append('<p>'+escape(report['timing'])+'</p>')
    return '\n'.join(body)+'\n'


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--image-answer-key',type=Path,required=True)
    args = p.parse_args()
    report, path = analyze(args.image_answer_key)
    print(json.dumps(dict(report=str(path), results={k:{field:s[field] for field in
        ('n','correct','accuracy','median_ms','p95_ms','mean_ms','cost','complete','statuses')} for k,s in report['groups'].items()}),indent=2))
