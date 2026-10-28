"""Offline October 18 export and scoring. Inference never imports this module.

The original external key is required only for aggregate scoring. No key or
per-item correctness is written. The complete October 16 summary is preserved.
"""
from repo_layout import logical_relative, repo_file
from repo_layout import frozen_file
import argparse
from collections import Counter
from copy import deepcopy
from decimal import Decimal
from hashlib import sha256
import csv
import itertools
import json
from pathlib import Path

import native_field_2026_10_18 as runner
import matched_analysis as prior
import overall_analysis as native16
import text_additions as llm16
import text_models as chat
from analysis_core import metrics, correct, valid, panels, panel_summary
from score_expansion import load_key, normalized_llm

ROOT = runner.ROOT
PUBLIC = repo_file('native_additions_2026-10-18', root=ROOT)
OVERALL = repo_file('overall_expanded_2026-10-18', root=ROOT)
BASE = repo_file('overall_expanded_2026-10-16/summary.json', root=ROOT)
STOPPED = 'solar_decide'


def record_stop():
    """Bind the stopped process's final ledgers; never reconcile by replaying."""
    source=runner.RUNS/STOPPED
    target=source/'stop_receipt.json'
    if target.exists(): return json.loads(target.read_text())
    attempts=chat.rows(source/'attempts.jsonl')
    dispatches=chat.rows(source/'dispatches.jsonl')
    results=chat.rows(source/'results.jsonl')
    sig=lambda records:{(r['request_index'],r['attempt']) for r in records}
    unresolved=sig(dispatches)-sig(attempts)
    assert len(attempts)==len(results)==347 and len(dispatches)==348
    assert unresolved=={(347,1)}
    names=['manifest.json','software.json','model_metadata.json','compatibility_probe.json',
           'probe_dispatch.json','attempts.jsonl','dispatches.jsonl','results.jsonl','progress.jsonl']
    value=dict(status='STOPPED_BY_USER_LATENCY',recorded=runner.d.timestamps(),
        model_id=STOPPED,planned_questions=1136,completed_first_attempts=347,dispatched_attempts=348,
        reason='Benchmark author requested stopping this route because measured multi-second latency was impractical for the intended fast decisions.',
        process_exit_code=143,interruption='SIGTERM after fourteen other models completed; one response remained unrecorded',
        unresolved_dispatches=[dict(request_index=i,attempt=a) for i,a in sorted(unresolved)],
        unresolved_charge_attempts=len(unresolved),do_not_replay_unresolved_dispatches=True,
        source_files_sha256={name:sha256((source/name).read_bytes()).hexdigest() for name in names})
    runner.d.save_bound(target,value)
    return value


def export_partial():
    source=runner.RUNS/STOPPED
    receipt=json.loads((source/'stop_receipt.json').read_text())
    assert receipt['status']=='STOPPED_BY_USER_LATENCY'
    for name,h in receipt['source_files_sha256'].items():
        assert sha256((source/name).read_bytes()).hexdigest()==h,name
    dest=PUBLIC/(STOPPED+'_partial')
    manifest=json.loads((source/'manifest.json').read_text())
    plan=manifest.pop('request_plan')
    contents={'run_manifest.json':json.dumps(manifest,indent=2)+'\n',
              'request_plan.jsonl':''.join(json.dumps(r)+'\n' for r in plan)}
    for name in ('software.json','model_metadata.json','dispatches.jsonl','results.jsonl','probe_dispatch.json','stop_receipt.json'):
        contents[name]=(source/name).read_text()
    attempts=[]
    for a in chat.rows(source/'attempts.jsonl'):
        value=deepcopy(a);value['raw_response']=prior.sanitize_raw(a['raw_response'])
        value['usage']=value['raw_response'].get('usage') or {}
        attempts.append(value)
    contents['attempts.jsonl']=''.join(json.dumps(r,ensure_ascii=False,allow_nan=False)+'\n' for r in attempts)
    probe=json.loads((source/'compatibility_probe.json').read_text())
    probe['raw_response']=prior.sanitize_raw(probe['raw_response'])
    probe['usage']=probe['raw_response'].get('usage') or {}
    contents['compatibility_probe.json']=json.dumps(probe,indent=2)+'\n'
    dest.mkdir(parents=True,exist_ok=True)
    for name,text in contents.items():
        if (dest/name).exists():assert (dest/name).read_text()==text,name
        else:(dest/name).write_text(text)
    checksums={name:sha256((dest/name).read_bytes()).hexdigest() for name in sorted(contents)}
    runner.d.save_bound(dest/'checksums.json',checksums)


def validate_partial():
    dest=PUBLIC/(STOPPED+'_partial')
    for name,h in json.loads((dest/'checksums.json').read_text()).items():
        assert sha256((dest/name).read_bytes()).hexdigest()==h,name
    for name,h in json.loads((dest/'software.json').read_text()).items():
        assert sha256(frozen_file(repo_file(name, root=ROOT)).read_bytes()).hexdigest()==h,name
    attempts=chat.rows(dest/'attempts.jsonl');dispatches=chat.rows(dest/'dispatches.jsonl');results=chat.rows(dest/'results.jsonl')
    receipt=json.loads((dest/'stop_receipt.json').read_text())
    assert len(attempts)==len(results)==receipt['completed_first_attempts']==347
    assert len(dispatches)==receipt['dispatched_attempts']==348
    signature=lambda rows:[(r['request_index'],r['attempt']) for r in rows]
    ds,aa=signature(dispatches),signature(attempts)
    assert len(set(ds))==len(ds) and len(set(aa))==len(aa)
    unresolved=set(ds)-set(aa)
    assert unresolved=={(r['request_index'],r['attempt']) for r in receipt['unresolved_dispatches']}=={(347,1)}
    assert {r['request_index'] for r in results}=={r['request_index'] for r in attempts}
    plan=chat.rows(dest/'request_plan.jsonl');index={p['request_index']:p for p in plan}
    qs={q['item_id']:q for q in runner.d.read_csv(repo_file('data/questions_1136.csv', root=ROOT))}
    assert len(plan)==1136
    for r in attempts:
        assert r['attempt']==1 and all(r[k]==v for k,v in index[r['request_index']].items())
        assert r['request_payload_sha256']==runner.d.digest(runner.payload(qs[r['item_id']],STOPPED))
        runner.check_identity(r)
        for k,v in runner.parse(r).items():assert r[k]==v,k
    return attempts,receipt


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False)+'\n')


def export(model_id):
    source, dest = runner.RUNS/model_id, PUBLIC/model_id
    completion = json.loads((source/'completion.json').read_text())
    assert completion['status'] == 'COMPLETE_1136'
    for name, expected in completion['files_sha256'].items():
        assert sha256((source/name).read_bytes()).hexdigest() == expected, name
    manifest = json.loads((source/'manifest.json').read_text())
    plan = manifest.pop('request_plan')
    contents = {'run_manifest.json': json.dumps(manifest, indent=2, ensure_ascii=False)+'\n',
                'request_plan.jsonl': ''.join(json.dumps(p, ensure_ascii=False)+'\n' for p in plan)}
    for name in ('software.json', 'model_metadata.json', 'dispatches.jsonl', 'results.jsonl',
                 'retry_waits.jsonl', 'probe_dispatch.json'):
        contents[name] = (source/name).read_text() if (source/name).exists() else ''
    attempts = []
    for a in chat.rows(source/'attempts.jsonl'):
        value = deepcopy(a)
        value['raw_response'] = prior.sanitize_raw(a['raw_response'])
        value['usage'] = value['raw_response'].get('usage') or {}
        attempts.append(value)
    contents['attempts.jsonl'] = ''.join(json.dumps(a, ensure_ascii=False, allow_nan=False)+'\n' for a in attempts)
    probe = json.loads((source/'compatibility_probe.json').read_text())
    probe['raw_response'] = prior.sanitize_raw(probe['raw_response'])
    probe['usage'] = probe['raw_response'].get('usage') or {}
    contents['compatibility_probe.json'] = json.dumps(probe, indent=2, ensure_ascii=False)+'\n'
    contents['source_audit.json'] = json.dumps(dict(completed=completion['completed'],
        source_run_files_sha256=completion['files_sha256'],
        previous_22_model_summary_sha256=sha256(BASE.read_bytes()).hexdigest(),
        sanitization='Allowlisted identity, typed answer, usage and basic errors. No account metadata, credentials, owner paths, gold key or per-item correctness.'), indent=2)+'\n'
    dest.mkdir(parents=True, exist_ok=True)
    for name, text in contents.items():
        p = dest/name
        if p.exists():
            assert p.read_text() == text, 'Never replace exported evidence: '+name
        else:
            p.write_text(text)
    checksums = {name: sha256((dest/name).read_bytes()).hexdigest() for name in sorted(contents)}
    if (dest/'checksums.json').exists():
        assert json.loads((dest/'checksums.json').read_text()) == checksums
    else:
        write(dest/'checksums.json', checksums)


def validate_model(model_id):
    dest = PUBLIC/model_id
    checksums = json.loads((dest/'checksums.json').read_text())
    for name, expected in checksums.items():
        assert sha256((dest/name).read_bytes()).hexdigest() == expected, name
    audit = json.loads((dest/'source_audit.json').read_text())
    assert audit['previous_22_model_summary_sha256'] == sha256(BASE.read_bytes()).hexdigest()
    for name, expected in json.loads((dest/'software.json').read_text()).items():
        assert sha256(frozen_file(repo_file(name, root=ROOT)).read_bytes()).hexdigest() == expected, name
    manifest = json.loads((dest/'run_manifest.json').read_text())
    assert manifest['model'] == runner.MODELS[model_id]
    assert manifest['questions_sha256'] == sha256((repo_file('data/questions_1136.csv', root=ROOT)).read_bytes()).hexdigest()
    plan, attempts, results = (chat.rows(dest/n) for n in ('request_plan.jsonl', 'attempts.jsonl', 'results.jsonl'))
    assert len(plan) == len(results) == len({r['item_id'] for r in plan}) == 1136
    d = runner.d
    d.reconcile(chat.rows(dest/'dispatches.jsonl'), attempts, results, plan)
    qs = {q['item_id']: q for q in d.read_csv(repo_file('data/questions_1136.csv', root=ROOT))}
    assert set(qs) == {p['item_id'] for p in plan}
    index = {p['request_index']: p for p in plan}
    assert Counter(p['wave'] for p in plan) == Counter({i:2 for i in range(1,569)})
    for p in plan:
        q = qs[p['item_id']]
        body = runner.payload(q, model_id)
        assert p['request_payload_sha256'] == d.digest(body)
        assert p['native_input_sha256'] == d.digest(d.packet(q))
        assert p['prompt_sha256'] == q['prompt_sha256']
        assert p['request_body_bytes'] == len(d.canonical(body))
    grouped = {}
    for a in attempts:
        assert all(a[k] == v for k,v in index[a['request_index']].items())
        assert a['attempt'] in (1,2)
        for k,v in runner.parse(a).items():
            assert a[k] == v, k
        runner.check_identity(a)
        grouped.setdefault(a['request_index'], []).append(a)
    for group in grouped.values():
        assert [a['attempt'] for a in group] == list(range(1,len(group)+1))
        if len(group) == 2:
            assert runner.retryable(group[0]), 'Ineligible retry'
    first, eventual = chat.first_and_eventual(attempts)
    assert len(first) == len(eventual) == 1136
    for r in results:
        i = r['request_index']
        assert r['first_status'] == first[i]['status']
        assert r['eventual_status'] == eventual[i]['status']
        assert r['attempts'] == eventual[i]['attempt']
    probe = json.loads((dest/'compatibility_probe.json').read_text())
    assert probe['stage'] == 'compatibility_not_scored' and probe['status'] == 'ok'
    runner.check_identity(probe)
    assert runner.parse(probe)['choice'] == probe['choice']
    return first, eventual, attempts


def previous_rows():
    ff,_,_ = prior.validate_refresh()
    old_llm,_ = chat.first_and_eventual(chat.rows(prior.EXPANSION/'attempts.jsonl'))
    rr = {m:[normalized_llm(a) for a in old_llm.values() if a['model_requested'] == m] for m in chat.MODELS}
    for model,spec in prior.d.MODELS.items():
        rr[spec[0]] = [prior.normalized_native(a) for a in ff.values() if a['model_requested'] == model]
    for m in native16.runner.MODELS:
        first,_,_ = native16.validate_model(m)
        rr[m] = [prior.normalized_native(a) for a in first.values()]
    for m in llm16.MODELS:
        first,_,_ = llm16.validate_model(m)
        rr[m] = [normalized_llm(a) for a in first.values()]
    return rr


def analyze(key_path, write_output=False):
    keys = load_key(key_path)
    base = json.loads(BASE.read_text())
    summary = deepcopy(base)
    rr = previous_rows()
    for m, rows in rr.items():
        assert metrics(rows,keys) == base['models'][m]['primary'], m
    metadata = {r['item_id']:r for r in runner.d.read_csv(repo_file('data/item_metadata.csv', root=ROOT))}
    selection = json.loads((repo_file('data/selection_manifest.json', root=ROOT)).read_text())
    tested = [m for m in runner.MODELS if (PUBLIC/m/'checksums.json').exists()]
    assert len(tested) == 14 and STOPPED not in tested, 'Fourteen complete runs plus the explicitly stopped Solar diagnostic are required'
    partial_attempts,stop_receipt=validate_partial()
    all_new, probes = [], []
    for m in tested:
        first,eventual,attempts = validate_model(m)
        ff,ee = list(first.values()),list(eventual.values())
        normalized = [prior.normalized_native(a) for a in ff]
        rr[m] = normalized
        spec = runner.MODELS[m]
        primary = metrics(normalized,keys)
        cost = native16.accounted_money(attempts)
        summary['models'][m] = dict(label=spec['label'], condition='native_decisions_added_october_18',
            model_requested=spec['model'], provider_tag=spec['provider_tag'], provider_name=spec['provider_name'], route='OpenRouter',
            primary=primary, eventual=metrics([prior.normalized_native(a) for a in ee],keys),
            statuses_first=dict(Counter(a['status'] for a in ff)),
            http_status_first=dict(Counter(str(a['http_status']) for a in ff)),
            recovery_attempts=len(attempts)-1136, cost_all_attempts=cost, cost_first_attempts=native16.accounted_money(ff),
            cost_basis='API-reported; unreported charges remain unknown',
            known_usd_per_1000_questions=cost['known_usd']/1136*1000,
            known_usd_per_primary_correct=cost['known_usd']/primary['correct'] if primary['correct'] else None,
            latency_first_all=chat.quantiles([a['latency_ms'] for a in ff]),
            latency_first_usable=chat.quantiles([a['latency_ms'] for a in ff if a['status']=='ok']),
            latency_first_http200=chat.quantiles([a['latency_ms'] for a in ff if a['http_status']==200]),
            input_tokens_all_attempts=sum(a['usage'].get('input_tokens',0) or 0 for a in attempts),
            output_tokens_all_attempts=sum(a['usage'].get('output_tokens',0) or 0 for a in attempts),
            identities=dict(Counter(a['model_returned'] or 'unreported (error)' for a in ff)),
            dates_toronto=dict(Counter(a['started']['toronto'][:10] for a in ff)),
            panels=panel_summary(panels(normalized,keys,selection)))
        value = summary['models'][m]
        value['confidence'] = []
        for threshold in (.8,.9,.95):
            retained = [a for a in normalized if valid(a) and a['normalized_confidence'] is not None and a['normalized_confidence']>=threshold]
            value['confidence'].append(dict(threshold=threshold,coverage=len(retained)/1136,**metrics(retained,keys)))
        for field in ('role','level'):
            value['by_'+field] = {v:metrics([a for a in normalized if metadata[a['item_id']][field]==v],keys)
                                  for v in sorted({r[field] for r in metadata.values()})}
        for family in summary['by_family']:
            group = [a for a in normalized if metadata[a['item_id']]['family_id']==family['family_id']]
            family['models'][m] = metrics(group,keys)
        value['macro_family_accuracy'] = sum(f['models'][m]['accuracy_attempted'] for f in summary['by_family'])/25
        summary['output_compliance'][m] = llm16.compliance(ff)
        summary['sessions_utc'][m] = dict(started=min(a['started']['utc'] for a in attempts),
                                         completed=max(a['completed']['utc'] for a in attempts))
        all_new.extend(attempts)
        probes.append(json.loads((PUBLIC/m/'compatibility_probe.json').read_text()))
    for m,value in base['models'].items():
        assert summary['models'][m] == value, 'Earlier result changed: '+m
    summary.update(status='COMPLETE_1136_EACH_WITH_OCTOBER_18_NATIVE_ADDITIONS', model_count=len(rr),
        native_added_october_18_model_ids=tested, added_model_ids=base['added_model_ids']+tested,
        stopped_model_ids=[STOPPED],pending_model_ids=[],total_scored_model_questions=len(rr)*1136)
    indexed = {m:{a['item_id']:a for a in group} for m,group in rr.items()}
    shared = [i for i in metadata if all(valid(indexed[m][i]) for m in rr)]
    summary['all_tested_models_answered'] = len(shared)
    summary['none_of_tested_models_correct'] = sum(not any(correct(indexed[m][i],keys) for m in rr) for i in metadata)
    summary['accuracy_on_shared_answered'] = {m:metrics([a for a in group if a['item_id'] in shared],keys) for m,group in rr.items()}
    summary['pairwise'] = [dict(a=a,b=b,**prior.pairwise(rr[a],rr[b],keys)) for a,b in itertools.combinations(rr,2)]
    eligible = [m for m in summary['models'] if summary['output_compliance'][m]['eligible_for_main_comparison']]
    ranked_cost = sum((Decimal(str(summary['models'][m]['cost_all_attempts']['exact_usd'])) for m in eligible),Decimal(0))
    summary['publication'].update(eligible_model_ids=eligible, excluded_model_ids=[m for m in rr if m not in eligible],
        ranked_model_count=len(eligible), ranked_model_question_cases=len(eligible)*1136,
        none_of_ranked_models_correct=sum(not any(correct(indexed[m][i],keys) for m in eligible) for i in metadata),
        ranked_accounted_cost=dict(exact_usd=str(ranked_cost),known_usd=float(ranked_cost),
                                  missing_attempts=sum(summary['models'][m]['cost_all_attempts']['missing_attempts'] for m in eligible)))
    new_cost = native16.accounted_money(all_new)
    summary['native_october_18_cost'] = new_cost
    partial_norm=[prior.normalized_native(r) for r in partial_attempts]
    partial_ids={r['item_id'] for r in partial_norm}
    summary['partial_runs']={STOPPED:dict(status=stop_receipt['status'],label=runner.MODELS[STOPPED]['label'],
        reason=stop_receipt['reason'],planned=1136,completed_first_attempts=len(partial_attempts),
        dispatched_attempts=stop_receipt['dispatched_attempts'],unresolved_dispatches=stop_receipt['unresolved_dispatches'],
        primary_on_completed_only=metrics(partial_norm,keys),
        latency_completed_first=chat.quantiles([r['latency_ms'] for r in partial_attempts]),
        cost_recorded_attempts=native16.accounted_money(partial_attempts),
        additional_unresolved_charge_attempts=stop_receipt['unresolved_charge_attempts'],
        main_ranking_included=False,full_bank_extrapolation=False,
        same_completed_subset={m:metrics([r for r in group if r['item_id'] in partial_ids],keys) for m,group in rr.items()} )}
    probes.append(json.loads((PUBLIC/(STOPPED+'_partial')/'compatibility_probe.json').read_text()))
    summary['native_october_18_compatibility_probes'] = dict(count=len(probes), included_in_scored_cost=False,
        known_usd=float(sum((Decimal(str(a['reported_cost_usd'])) for a in probes if a['reported_cost_usd'] is not None),Decimal(0))),
        unknown_charge_attempts=sum(a['reported_cost_usd'] is None for a in probes))
    for field in ('total_selected_accounted_cost','total_selected_reported_cost'):
        value = summary[field]
        total = Decimal(base[field]['exact_usd'])+Decimal(new_cost['exact_usd'])
        value.update(exact_usd=str(total),known_usd=float(total),missing_attempts=base[field]['missing_attempts']+new_cost['missing_attempts'])
        if 'reported_attempts' in value:
            value['reported_attempts'] += new_cost['reported_attempts']
    summary['total_selected_http_attempts'] += len(all_new)
    summary['limits'] += [
        'October 18 additions use unchanged native choice serialization and full-body HTTPS timer, with two cases per wave and two concurrent requests per model; at most five active native models. They are not contemporaneous reruns of the October 15/16 baselines.',
        'Providers are pinned without fallback. Returned model names are not independent proof of fixed weights. Clef and Clef Flash return undated names.',
        'October 18 HTTP-200 provider error envelopes remain first-attempt failures and are not retried; only transport failures and HTTP 408/429/5xx receive one recovery.',
        'Solar Decide was stopped by the benchmark author for impractical latency after 347 recorded first responses and 348 dispatches. It has no full-bank score; one unresolved response/charge is preserved and must not be replayed.',
        'Tev1 is a decision-specialized generative model using a documented chat-letter interface, separate from these fifteen native API candidates. No Tev1 or additional regular LLM run is included.',
        'The question bank contains dependent rotations, contrasts and candidate checks. Overall accuracy is a descriptive result on this bank, not 1136 independent trials.'
    ]
    summary['source_files_sha256'][str(logical_relative(BASE, root=ROOT))] = sha256(BASE.read_bytes()).hexdigest()
    note = OVERALL/'current_pricing_note.json'
    if note.exists():
        summary['source_files_sha256'][str(logical_relative(note, root=ROOT))] = sha256(note.read_bytes()).hexdigest()
    for p in PUBLIC.rglob('*'):
        if p.is_file(): summary['source_files_sha256'][str(logical_relative(p, root=ROOT))] = sha256(p.read_bytes()).hexdigest()
    if write_output:
        write(OVERALL/'summary.json',summary)
        with (OVERALL/'family_comparison.csv').open('w',newline='') as stream:
            labels = {m:summary['models'][m]['label'] for m in eligible}
            writer = csv.DictWriter(stream,fieldnames=['family_id','family','n',*labels.values()],lineterminator='\n')
            writer.writeheader()
            writer.writerows(dict(family_id=f['family_id'],family=f['family'],n=f['n'],
                **{label:f['models'][m]['correct'] for m,label in labels.items()}) for f in summary['by_family'])
    else:
        assert summary == json.loads((OVERALL/'summary.json').read_text())
    print(json.dumps(dict(model_count=len(rr),ranked_models=len(eligible),new_cost=new_cost,
        new_results={m:dict(correct=summary['models'][m]['primary']['correct'],
                            median_ms=summary['models'][m]['latency_first_all']['median_ms']) for m in tested}),indent=2))
    return summary


def validate_summary():
    summary = json.loads((OVERALL/'summary.json').read_text())
    base = json.loads(BASE.read_text())
    assert summary['model_count'] == 36 and not summary['pending_model_ids']
    for m,value in base['models'].items(): assert summary['models'][m] == value,m
    for name,expected in summary['source_files_sha256'].items():
        assert sha256(frozen_file(repo_file(name, root=ROOT)).read_bytes()).hexdigest() == expected,name
    for m in summary['native_added_october_18_model_ids']:
        first,eventual,attempts = validate_model(m)
        value = summary['models'][m]
        assert summary['output_compliance'][m] == llm16.compliance(list(first.values()))
        assert value['cost_all_attempts'] == native16.accounted_money(attempts)
        assert value['latency_first_all'] == chat.quantiles([a['latency_ms'] for a in first.values()])
        assert value['primary']['attempted'] == 1136
        assert value['primary']['answered'] == sum(a['status']=='ok' for a in first.values())
        assert value['primary']['correct']+value['primary']['wrong'] == value['primary']['answered']
        assert value['recovery_attempts'] == len(attempts)-1136
    eligible = [m for m in summary['models'] if summary['output_compliance'][m]['eligible_for_main_comparison']]
    assert summary['publication']['eligible_model_ids'] == eligible
    aa,receipt=validate_partial()
    partial=summary['partial_runs'][STOPPED]
    assert not partial['main_ranking_included'] and not partial['full_bank_extrapolation']
    assert partial['completed_first_attempts']==len(aa)==347
    assert partial['additional_unresolved_charge_attempts']==1
    assert partial['cost_recorded_attempts']==native16.accounted_money(aa)
    print('PASS: 36 complete runs, prior 22 scores unchanged, one user-stopped partial with unresolved dispatch retained; immutable sources, payloads, ledgers, retries, identities, costs and timing')


if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--export',choices=runner.MODELS,nargs='+')
    p.add_argument('--export-complete',action='store_true')
    p.add_argument('--answer-key',type=Path)
    p.add_argument('--write',action='store_true')
    p.add_argument('--record-stop',action='store_true')
    args=p.parse_args()
    if args.record_stop:
        record_stop()
        export_partial()
    selected=args.export or []
    if args.export_complete:
        selected=[m for m in runner.MODELS if (runner.RUNS/m/'completion.json').exists()]
    for m in selected: export(m)
    if args.answer_key: analyze(args.answer_key,args.write)
    elif (OVERALL/'summary.json').exists(): validate_summary()
