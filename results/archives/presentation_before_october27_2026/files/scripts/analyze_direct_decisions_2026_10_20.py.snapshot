"""Offline revision-bound scoring/report; no inference and no credential reads."""
from repo_layout import repo_file
from repo_layout import source_file
import argparse
from collections import Counter
import csv
from decimal import Decimal
from hashlib import sha256
from html import escape
import io
import json
import math
from pathlib import Path

import direct_decisions_2026_10_20 as run
from analyze_frontier_reference import load_gold, outcomes

HARDENING=run.ROOT.parent/'text-decision-hardening'


def write_artifacts(dest,artifacts,sealed=False):
    """Build every file first and refuse to overwrite any differing sealed output."""
    if sealed:
        hashes={name:sha256(value.encode('utf-8')).hexdigest() for name,value in artifacts.items()}
        artifacts={**artifacts,'checksums.json':json.dumps(hashes,indent=2)+'\n'}
        # Preflight the entire set, not one file at a time after earlier writes.
        for name,value in artifacts.items():
            if (dest/name).exists():
                assert (dest/name).read_bytes()==value.encode('utf-8'),'Immutable report changed: '+name
    dest.mkdir(exist_ok=True)
    for name,value in artifacts.items():
        if not sealed or not (dest/name).exists():
            (dest/name).write_text(value,encoding='utf-8')


def cost(rows,field):
    values=[Decimal(str(r[field])) for r in rows if r.get(field) is not None]
    return dict(known_usd=float(sum(values,Decimal(0))),exact_decimal=str(sum(values,Decimal(0))),
                known_attempts=len(values),unknown_attempts=len(rows)-len(values))


def statistics(rows,gold,meta):
    first,last=run.chat.first_and_eventual(rows)
    values=list(first.values());s=outcomes(rows,gold)
    s['mean_response_ms']=math.fsum(r['latency_ms'] for r in values)/len(values) if values else None
    s.update(eventual=outcomes([{**r,'attempt':1} for r in last.values()],gold),
        latency=run.chat.quantiles([r['latency_ms'] for r in values]),
        attempts=len(rows),recoveries=len(rows)-len(values),
        first_statuses=dict(Counter(r['status'] for r in values)),
        cost=cost(rows,'accounted_cost_usd'),api_reported_cost=cost(rows,'reported_cost_usd'),
        cost_sources=dict(Counter(r['cost_source'] for r in rows)),
        probabilities_warning_count=sum(not r['probabilities_valid'] for r in values),
        returned_identities=dict(Counter(r['model_returned'] for r in values)),
        returned_versions=dict(Counter(str(r['returned_version']) for r in values)),
        dates_toronto=dict(Counter(r['started']['toronto'][:10] for r in values)),
        output_token_values=dict(Counter(str(r['usage'].get('output_tokens')) for r in values)),
        input_tokens=sum(r['usage'].get('input_tokens',0) for r in rows),
        families={fid:outcomes(rows,{i:g for i,g in gold.items() if meta[i]['family_id']==fid})
                  for fid in sorted({v['family_id'] for v in meta.values()})},
        release_exclusion_diagnostic=outcomes(rows,{i:g for i,g in gold.items()
            if not meta[i]['permanently_unscored_native_development']}),
        new_domains=outcomes(rows,{i:g for i,g in gold.items() if meta[i]['family_id']>='F26'}))
    original={q['item_id'] for q in run.d.read_csv(repo_file('corrected_2026-10-18/questions_1136.csv', root=run.ROOT))}
    s['original_1136']=outcomes(rows,{i:g for i,g in gold.items() if i in original})
    s['added_206']=outcomes(rows,{i:g for i,g in gold.items() if i not in original})
    return s


def html(report,published,names):
    guide=json.loads((repo_file('llm_references_2026-10-19/category_guide.json', root=run.ROOT)).read_text())
    new=report['models'];rows=[]
    for mid,m in published['models'].items():
        rows.append(dict(model_id=mid,label=m['label'],accuracy=m['accuracy'],correct=m['correct'],n=m['n'],
            median_ms=m['median_ms'],p95_ms=m['p95_ms'],cost=m['cost']['known_usd'],
            unknown=m['cost']['unknown_attempts'],kind=published['model_kinds'][mid],new=False))
    for mid,m in new.items():
        if m['complete']:
            s=m['statistics'];rows.append(dict(model_id=mid,label=m['label'],accuracy=s['accuracy'],
                correct=s['correct'],n=s['n'],median_ms=s['latency']['median_ms'],
                p95_ms=s['latency']['p95_ms'],cost=s['cost']['known_usd'],
                unknown=s['cost']['unknown_attempts'],kind='Decision model',new=True))
    rows.sort(key=lambda r:(-r['correct'],r['model_id']))
    body=[]
    for rank,r in enumerate(rows,1):
        css='llm' if r['kind']=='LLM reference' else 'new' if r['new'] else ''
        price=f"${r['cost']:.6f}"+(' + unknown' if r['unknown'] else '')
        if r['new'] and r['model_id']!='kettei_fat':price='Free public endpoint*'
        body.append(f'<tr class="{css}"><td>{rank}</td><th>{escape(r["label"])}</th>'
            f'<td>{r["correct"]}/{r["n"]} · {r["accuracy"]:.1%}</td>'
            f'<td>{r["median_ms"]/1000:.3f}s</td><td>{r["p95_ms"]/1000:.3f}s</td>'
            f'<td>{price}</td><td>{escape(r["kind"])}</td></tr>')
    partial=[];timings=[]
    for mid,m in new.items():
        s=m['statistics']
        timings.append(f'<tr><th>{escape(m["label"])}</th><td>{s["n"]}/1342</td>'
            f'<td>{"Complete" if m["complete"] else "Partial"}</td>'
            f'<td>{s["mean_response_ms"]:.1f} ms</td>'
            f'<td>{s["latency"]["median_ms"]:.1f} ms</td>'
            f'<td>{s["latency"]["p95_ms"]:.1f} ms</td></tr>')
        if not m['complete']:
            s=m['statistics'];partial.append(f'<p>{escape(m["label"])}: {s["n"]}/1342 completed; '
                f'{s["correct"]}/{s["n"]} correct so far. Partial run—not ranked.</p>')
    columns=[(mid,m['label'],m['statistics']['families']) for mid,m in new.items() if m['complete']]
    for mid in ('respan02','pplx_decider12','nimble_v4_max','reference_sol'):
        m=published['models'][mid];columns.append((mid,m['label'],m['families']))
    profiles=[]
    for mid,label,families in columns:
        if mid not in new:continue
        value=lambda fid:f'{families[fid]["correct"]}/{families[fid]["n"]}'
        profiles.append('<li><strong>'+escape(label)+'</strong>: if-then rules '+value('F02')+
            '; required conditions '+value('F03')+'; tracking what others know '+value('F17')+
            '; counting exactly true claims '+value('F09')+'; step-by-step procedures '+value('F13')+'.</li>')
    functions=[]
    for fid in sorted(names):
        name=guide[fid]['display_name']
        description=guide[fid]['what_it_tests']+' Example: '+guide[fid]['illustration']
        cells=[]
        for _,_,families in columns:
            value=families[fid];accuracy=value['accuracy'];shade=96-accuracy*24
            cells.append(f'<td style="background:hsl(205 65% {shade:.1f}%)">'
                f'{value["correct"]}/{value["n"]}<br>{accuracy:.1%}</td>')
        functions.append(f'<tr><th title="{escape(description,quote=True)}">{escape(fid+" — "+name)}</th>'+''.join(cells)+'</tr>')
    return ('<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
        '<title>Three new native decision models — 1,342 text questions</title><style>'
        'body{font:16px/1.55 system-ui;margin:2rem;color:#162536;max-width:1500px}table{border-collapse:collapse;width:100%}'
        'th,td{border:1px solid #cbd5e1;padding:.7rem;text-align:right}th{text-align:left}thead{background:#e2e8f0}'
        '.scroll{overflow:auto;margin:1rem 0 2rem}.llm{background:#fff7d6}.new{background:#e3f3ff;font-weight:600}'
        'small{color:#475569}h1{line-height:1.2}.notice{padding:1rem;background:#f1f5f9}</style>'
        '<h1>Three additional native decision models</h1><p>Full bank: 1,342 text questions, five choices, '
        '31 categories. New tests: October 20, 2026 (America/Toronto).</p><div class="notice">'
        +''.join(partial)+'<p>Blue rows: newly completed decision models. Pale yellow: no-reasoning LLM references. '
        'Existing results have not been rerun or changed. Incomplete models are never extrapolated into the ranking.</p></div>'
        '<h2>Average response times for the three additions</h2>'
        '<p>Average means the arithmetic mean. Median is the middle response; p95 is the response time '
        'at or below which approximately 95% of first attempts finished. Deliberate rate-limit waits are excluded.</p>'
        '<div class="scroll"><table><thead><tr><th>Model</th><th>Questions</th><th>Status</th>'
        '<th>Average</th><th>Median</th><th>p95</th></tr></thead><tbody>'+''.join(timings)+'</tbody></table></div>'
        '<h2>Full-bank comparison</h2>'
        '<div class="scroll"><table><thead><tr><th>Rank</th><th>Model</th><th>Correct / questions</th>'
        '<th>Median response</th><th>p95 response</th><th>Cost for full 1,342</th><th>Type</th></tr></thead><tbody>'
        +''.join(body)+'</tbody></table></div><p>*Public-free access, not an API-reported $0 charge or a guarantee '
        'of free production capacity. Sqwish uses its returned USD charge receipts; promotional credit does not change '
        'the metered price. Compatibility probes are separate from scored-run costs.</p>'
        '<h2>Different abilities behind the overall scores</h2><p>These five fixed examples cover rule following, '
        'knowledge tracking, exact counting and sequential execution. They are examples, not a replacement '
        'for all 31 categories below, and a perfect sample score does not guarantee reliability on new questions.</p><ul>'
        +''.join(profiles)+'</ul><h2>Performance across all 31 categories</h2><p>Each cell shows correct/questions and accuracy. '
        'Categories F26–F31 have only eight questions each: one answer changes a category score by 12.5 points.</p>'
        '<div class="scroll"><table><thead><tr><th>Category</th>'
        +''.join('<th>'+escape(label)+'</th>' for _,label,_ in columns)+'</tr></thead><tbody>'
        +''.join(functions)+'</tbody></table></div><h2>Measurement boundaries</h2>'
        '<p>One native request per question, original state/instructions/options, no generated explanations or '
        'agentic iteration. First attempts determine accuracy and response latency. One transient recovery is allowed '
        'and reported separately. Fresh HTTPS connect through the complete response uses the same timing definition '
        'as the previous benchmark. These are different dates, direct routes and provider hardware, not controlled '
        'isolated inference speeds. Rate/admission waits are outside that timer.</p>'
        '<p>Amos is paced below its public 60-request/minute cap. Sqwish starter access is paced to '
        '30 requests/minute and one active request. Therefore response latency is not batch throughput. '
        'No correctness-dependent retries or question changes. Named-model responses and zero output tokens '
        'are checked, but cannot prove immutable weights or undisclosed internal implementation.</p>'
        '<p><small>Development bank, not a pristine held-out release. The permanent 37-case development exclusions '
        'are retained in the separate 1,305-case diagnostic. Public endpoints may retain prompts; only public '
        'benchmark material—not Village conversations—is sent.</small></p></html>')


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--partial',action='store_true');args=p.parse_args()
    q,_=run.bank.prepare();gold,meta,names,bindings=load_gold(HARDENING,q)
    published=json.loads((repo_file('llm_references_2026-10-19/statistics.json', root=run.ROOT)).read_text())
    guide=json.loads((repo_file('llm_references_2026-10-19/category_guide.json', root=run.ROOT)).read_text())
    generated=run.d.timestamps() if args.partial else max(
        (json.loads((run.OUT/mid/'completion.json').read_text())['completed'] for mid in run.MODELS),
        key=lambda value:value['utc'])
    report=dict(status='PARTIAL_NOT_RELEASE' if args.partial else 'COMPLETE_THREE_DIRECT_1342',
        bank_sha256=run.bank.BANK_HASH,generated=generated,gold_source_bindings=bindings,models={},
        analysis_source_sha256={name:run.bank.file_hash(repo_file(name, root=run.ROOT)) for name in
            ('analyze_direct_decisions_2026_10_20.py','test_analyze_direct_decisions_2026_10_20.py',
             'llm_references_2026-10-19/statistics.json','llm_references_2026-10-19/category_guide.json')})
    for mid,cfg in run.MODELS.items():
        out=run.OUT/mid;complete=(out/'completion.json').exists()
        if not args.partial:assert complete,mid+' is not complete'
        if complete:
            rows,results,_=run.validate(mid,out,True)
        else:
            # A running process can legitimately have an in-flight dispatch.
            # This is a non-resumable snapshot, not a reconciliation receipt.
            rows=run.d.rows(out/'attempts.jsonl')
            results=run.d.rows(out/'results.jsonl')
        s=statistics(rows,gold,meta)
        if complete:
            assert s['n']==1342 and len(s['families'])==31
            assert sum(v['n'] for v in s['families'].values())==1342
        report['models'][mid]=dict(label=cfg['label'],complete=complete,statistics=s,
            evidence_sha256={name:run.bank.file_hash(out/name) for name in
                ('manifest.json','software.json','model_metadata.json','probe_dispatch.json','compatibility_probe.json',
                 'dispatches.jsonl','attempts.jsonl','results.jsonl','retry_waits.jsonl','completion.json','account_rate_amendment.json')
                if (out/name).exists()},compatibility=parse_probe(mid,out))
        if mid=='kettei_fat':
            amendment=json.loads((out/'account_rate_amendment.json').read_text())
            assert amendment['controller_sha256']==run.bank.file_hash(source_file(repo_file('continue_sqwish_2026_10_20.py', root=run.ROOT)))
            report['models'][mid]['account_rate_amendment']=amendment
    dest=run.OUT/('analysis_partial' if args.partial else 'analysis')
    stream=io.StringIO(newline='');writer=csv.writer(stream)
    writer.writerow(['model','complete','category_id','category','correct','questions_answered','accuracy'])
    for m in report['models'].values():
        for fid,v in m['statistics']['families'].items():
            writer.writerow([m['label'],m['complete'],fid,guide[fid]['display_name'],v['correct'],v['n'],v['accuracy']])
    write_artifacts(dest,{'summary.json':json.dumps(report,indent=2)+'\n',
        'report.html':html(report,published,names),'category_scores.csv':stream.getvalue()},sealed=not args.partial)
    print(json.dumps({'status':report['status'],'report':str(dest/'report.html'),
        'models':{mid:{k:m['statistics'][k] for k in ('n','correct','accuracy','latency','cost')} for mid,m in report['models'].items()}},indent=2))


def parse_probe(mid,out):
    value=json.loads((out/'compatibility_probe.json').read_text())
    parsed=run.parse(value['transport'],mid)
    return {k:parsed[k] for k in ('status','accounted_cost_usd','reported_cost_usd','cost_source')}


if __name__=='__main__':main()
