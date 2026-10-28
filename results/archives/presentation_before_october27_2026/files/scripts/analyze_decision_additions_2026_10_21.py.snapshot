"""Offline, revision-bound scoring of the October 21 native additions."""
from repo_layout import repo_file
import argparse
from collections import Counter
from copy import deepcopy
import json
from pathlib import Path

import baseten_decisions_2026_10_21 as baseten
import decision_additions_2026_10_21 as router
import analyze_direct_decisions_2026_10_20 as scoring
from analyze_frontier_reference import load_gold, outcomes

ROOT = router.ROOT
OUT = repo_file('runs/decision_additions_analysis_2026-10-21', root=ROOT)
BASE = repo_file('direct_additions_2026-10-20/statistics.json', root=ROOT)
RUNS = {'mammoth1':baseten,'elephant1':baseten,'drex_max':router}


def normalize(mid, label, rows, s, probe):
    free = mid != 'drex_max'
    reported = s['api_reported_cost']
    return dict(model_id=mid,label=label,n=s['n'],correct=s['correct'],answered=s['answered'],
        wrong_valid=s['wrong_valid'],failed=s['failed'],accuracy=s['accuracy'],
        accuracy_among_usable=s['correct']/s['answered'] if s['answered'] else None,
        mean_response_ms=s['mean_response_ms'],median_ms=s['latency']['median_ms'],p95_ms=s['latency']['p95_ms'],
        attempts=s['attempts'],recoveries=s['recoveries'],first_statuses=s['first_statuses'],
        provider_failures=sum(r['attempt']==1 and (r['http_status']!=200 or r.get('transport_failure')) for r in rows),
        model_output_failures=sum(r['attempt']==1 and r['http_status']==200 and r['status']!='ok' for r in rows),
        probability_warnings=s['probabilities_warning_count'],eventual=s['eventual'],
        cost=dict(known_usd=None if free else reported['known_usd'],
            known_decimal=None if free else reported['exact_decimal'],
            known_usd_per_1000=None if free else reported['known_usd']/s['n']*1000,
            unknown_attempts=reported['unknown_attempts'],exact_usd=None if free else reported['known_usd'],
            public_free_access=free,accounted_access_cost_usd=s['cost']['known_usd'],
            scope='Captured promotional free access; no monetary receipts, not a permanent production price' if free else 'API-reported OpenRouter charges, all attempts'),
        families=s['families'],dates_toronto=s['dates_toronto'],returned_identities=s['returned_identities'],
        providers=dict(Counter(r['provider'] or 'Baseten direct' for r in rows if r['attempt']==1)),
        route=('Direct → Baseten → '+baseten.MODELS[mid]['model']) if free else 'OpenRouter → DeepInfra → nace-ai/drex-max',
        output_token_values=s['output_token_values'],input_tokens=s['input_tokens'],
        macro_family_accuracy=sum(v['accuracy'] for v in s['families'].values() if v['n'])/sum(bool(v['n']) for v in s['families'].values()),
        new_domains=s['new_domains'],release_exclusion_diagnostic=s['release_exclusion_diagnostic'],
        original_1136=s['original_1136'],added_206=s['added_206'],compatibility=probe)


def analyze(partial=False):
    qs,_ = router.bank.prepare()
    gold,meta,names,bindings = load_gold(ROOT.parent/'text-decision-hardening',qs)
    report = dict(status='PARTIAL_NOT_RANKED' if partial else 'COMPLETE_THREE_1342_OCT21',
        bank_sha256=router.bank.BANK_HASH,models={},gold_source_bindings=bindings,
        analysis_source_sha256={name:router.bank.file_hash(repo_file(name, root=ROOT)) for name in (
            'analyze_decision_additions_2026_10_21.py','analyze_direct_decisions_2026_10_20.py',
            'analyze_frontier_reference.py','test_analyze_decision_additions_2026_10_21.py')})
    records = {}
    for mid,runner in RUNS.items():
        out = runner.OUT/mid
        complete = (out/'completion.json').exists()
        if not partial:
            assert complete,mid+' is incomplete; never extrapolate a partial result'
        if complete:
            rows,_,_ = runner.validate(mid,out,True)
        else:
            rows = router.d.rows(out/'attempts.jsonl')
        assert rows,mid+' has no scored attempts'
        records[mid] = rows
        s = scoring.statistics(rows,gold,meta)
        parsed = runner.parse(json.loads((out/'compatibility_probe.json').read_text())['transport'],mid)
        probe = {k:parsed[k] for k in ('status','reported_cost_usd','accounted_cost_usd','cost_source')}
        report['models'][mid] = dict(label=runner.MODELS[mid]['label'],complete=complete,statistics=s,
            normalized=normalize(mid,runner.MODELS[mid]['label'],rows,s,probe),
            evidence_sha256={p.name:router.bank.file_hash(p) for p in sorted(out.iterdir())
                if p.name in ('manifest.json','software.json','model_metadata.json','compatibility_probe.json',
                              'probe_dispatch.json','attempts.jsonl','results.jsonl','dispatches.jsonl',
                              'retry_waits.jsonl','completion.json','admission_note.json')})
        # Reconstruct every scored body and check the same answer-blind bank.
        for row in rows:
            body = runner.payload(qs[row['item_id']],mid)
            assert router.d.digest(body)==row['request_payload_sha256']
        if complete:
            assert s['n']==1342 and s['latency']['median_ms'] <= 2000
            assert len(s['families'])==31 and sum(v['correct'] for v in s['families'].values())==s['correct']
    report['openrouter_controls'] = {}
    for mid in baseten.MODELS:
        rows = router.d.rows(router.OUT/mid/'attempts.jsonl')
        primary = {r['item_id']:r for r in records[mid] if r['attempt']==1}
        matched = [r for r in rows if r['attempt']==1 and r['item_id'] in primary]
        report['openrouter_controls'][mid] = dict(n=len(matched),scored=outcomes(matched,gold),
            direct_scored_same_subset=outcomes([primary[r['item_id']] for r in matched],gold),
            same_choice=sum(r['choice']==primary[r['item_id']]['choice'] for r in matched),
            latency=router.stats.quantiles([r['latency_ms'] for r in matched]),
            scope='Separate20-case route control only; never pooled into full-bank direct results')
    if not partial:
        report['completed'] = max((json.loads((runner.OUT/mid/'completion.json').read_text())['completed']
            for mid,runner in RUNS.items()),key=lambda t:t['utc'])
    return report


def combined(report):
    assert report['status']=='COMPLETE_THREE_1342_OCT21'
    s = deepcopy(json.loads(BASE.read_text()))
    old = deepcopy(s['models'])
    for mid,model in report['models'].items():
        assert model['complete'] and model['normalized']['n']==1342
        s['models'][mid] = model['normalized']
        s['model_kinds'][mid] = 'Decision model'
    s['ranked_model_ids'] = sorted(s['models'],key=lambda mid:(-s['models'][mid]['correct'],mid))
    s['decision_model_ids'] = [mid for mid in s['ranked_model_ids'] if mid not in s['reference_model_ids']]
    s.update(status='COMPLETE_26_DECISION_PLUS_3_LLM_REFERENCES_1342',model_count=29,decision_model_count=26,
        primary_cases=29*1342,all_tested_primary_cases=29*1342,added_model_ids=list(RUNS),
        updated_date_toronto=report['completed']['toronto'][:10],prior_statistics_sha256=router.bank.file_hash(BASE),
        total_http_attempts=sum(m['attempts'] for m in s['models'].values()),
        total_recoveries=sum(m['recoveries'] for m in s['models'].values()))
    assert all(s['models'][mid]==m for mid,m in old.items())
    return s


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--partial',action='store_true')
    args = p.parse_args()
    report = analyze(args.partial)
    dest = OUT/('partial' if args.partial else 'complete')
    dest.mkdir(parents=True,exist_ok=True)
    values = {'summary.json':json.dumps(report,indent=2)+'\n'}
    if not args.partial:
        values['statistics.json'] = json.dumps(combined(report),indent=2)+'\n'
    scoring.write_artifacts(dest,values,sealed=not args.partial)
    print(json.dumps({mid:{k:m['statistics'][k] for k in ('n','correct','accuracy','latency','cost')}
                      for mid,m in report['models'].items()},indent=2))


if __name__=='__main__':
    main()
