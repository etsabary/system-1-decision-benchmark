"""Answer-blind October 21 additions on the unchanged 1,342-question bank.

Dry run by default. Isolated evidence, pinned backends, first-attempt scoring,
and a strict cumulative median screen after at least twenty scored cases.
"""
from repo_layout import logical_relative, repo_file
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from decimal import Decimal
import json
import os
from pathlib import Path
import ssl
import threading
import time
import urllib.request

from dotenv import dotenv_values
import added_decisions as transport
import decision_refresh as d
import direct_decisions_2026_10_20 as direct
import frontier_reference as bank
import text_models as stats

ROOT = Path(__file__).resolve().parents[1]
ADMISSION = repo_file('runs/decision_additions_2026-10-21', root=ROOT)
OUT = repo_file('runs/decision_additions_2026-10-21_01', root=ROOT)
ENV = Path('/Users/etsabary/Documents/repos/the village 14947/.env')
MODELS = {
    'mammoth1': dict(label='Mammoth-1', model='baseten/mammoth-1:free',
        provider_tag='baseten', provider_name='BaseTen', snapshot='baseten/mammoth-1-20261021:free', tariff='0'),
    'elephant1': dict(label='Elephant-1', model='baseten/elephant-1:free',
        provider_tag='baseten', provider_name='BaseTen', snapshot='baseten/elephant-1-20261021:free', tariff='0'),
    'drex_max': dict(label='Drex Max', model='nace-ai/drex-max',
        provider_tag='deepinfra', provider_name='DeepInfra', snapshot='nace-ai/drex-max-20261016', tariff='.06'),
}
SPEC = dict(host='openrouter.ai', path='/api/alpha/decisions')
SOFTWARE = ('decision_additions_2026_10_21.py', 'test_decision_additions_2026_10_21.py',
            'added_decisions.py', 'decision_refresh.py', 'direct_decisions_2026_10_20.py',
            'frontier_reference.py', 'text_models.py', 'run_benchmark.py')
FREE_LOCK = threading.Lock()
FREE_LAST = [0.0]


def credentials():
    key = str(os.environ.get('OPENROUTER_API_KEY') or dotenv_values(ENV).get('OPENROUTER_API_KEY') or '').strip()
    assert key, 'OPENROUTER_API_KEY missing'
    return key


def payload(q, mid):
    return dict(model=MODELS[mid]['model'], **q['native_input'], provider=dict(
        only=[MODELS[mid]['provider_tag']], allow_fallbacks=False, require_parameters=True))


def parse(response, mid):
    value = d.parse(response)
    raw = response.get('raw_response') or {}
    if raw.get('error'):
        value.update(status='provider_error', choice=None)
    if response.get('transport_failure'):
        value.update(status='transport_failure', choice=None)
    elif response.get('error') and response.get('http_status') == 200:
        value.update(status='response_error', choice=None)
    if value['status'] == 'ok':
        if value['model_returned'] not in (MODELS[mid]['model'], MODELS[mid]['snapshot'], MODELS[mid]['snapshot'].removesuffix(':free')):
            value.update(status='identity_mismatch', choice=None)
        elif value['provider'] != MODELS[mid]['provider_name']:
            value.update(status='provider_mismatch', choice=None)
        elif raw.get('reasoning') or raw.get('thinking') or any(
                value['usage'].get(k, 0) for k in ('reasoning_tokens','thinking_tokens')) or any(
                (value['usage'].get(k) or {}).get('reasoning_tokens',0)
                for k in ('output_tokens_details','completion_tokens_details')):
            value.update(status='unexpected_reasoning', choice=None)
    return dict(value, accounted_cost_usd=value['reported_cost_usd'],
                cost_source='api_reported' if value['reported_cost_usd'] is not None else 'unreported',
                returned_version=raw.get('version'))


def speed_stop(attempts):
    first = [r for r in attempts if r['attempt'] == 1]
    return len(first) >= 20 and stats.quantiles([r['latency_ms'] for r in first])['median_ms'] > 2000


def prepare(mid, out):
    questions, original = bank.prepare()
    plan = []
    for task in original:
        row = {k: task[k] for k in ('request_index', 'wave', 'item_id', 'family_id', 'native_input_sha256')}
        body = payload(questions[task['item_id']], mid)
        plan.append(dict(row, model_id=mid, model_requested=MODELS[mid]['model'],
                         request_payload_sha256=d.digest(body), request_body_bytes=len(d.canonical(body))))
    out.mkdir(parents=True, exist_ok=True)
    d.save_bound(out/'manifest.json', dict(version='oct21-native-1342-v1', model=MODELS[mid],
        endpoint='https://openrouter.ai/api/alpha/decisions', bank_sha256=bank.BANK_HASH,
        planned_cases=1342, request_plan=plan,
        input='Unchanged frozen native input, five original criteria in original order; no gold key accessed',
        order_seed=bank.SEED, concurrency='Two requests per model in two-case barrier waves',
        timing='Unchanged added_decisions.send; fresh HTTPS connect through complete response; rate/queue/retry waits excluded',
        free_pacing='Shared minimum 3.1 seconds between free-model dispatches, including probes and recovery calls',
        primary='Every first attempt, including failures; one transient-only recovery separate',
        speed_screen='Stop after any two-case wave at/after20 when cumulative first-attempt median exceeds2000ms',
        cost='API-reported usage.cost only; absent charge unknown, not invented zero. Promotional free tariff is not permanent pricing',
        soft_cost_guard_usd='.50', privacy='Public benchmark questions only, no Village private conversations',
        identity_limit='Pinned named backend and dated catalog identity, not immutable-weight attestation',
        generation_limit='Native decision endpoint, no requested reasoning/explanation. Nonzero output_tokens retained as reported usage, not proof of generation or thinking; undisclosed internals not independently verified',
        sources=['https://openrouter.ai/'+MODELS[mid]['model'],
                 'https://openrouter.ai/docs/api_reference/limits']))
    d.save_bound(out/'software.json', {name: bank.file_hash(repo_file(name, root=ROOT)) for name in SOFTWARE})
    return questions, plan


def metadata(mid, out):
    target = out/'model_metadata.json'
    if target.exists():
        return
    url = 'https://openrouter.ai/api/v1/models/'+MODELS[mid]['model']+'/endpoints'
    with urllib.request.urlopen(url, context=ssl.create_default_context(cafile='/etc/ssl/cert.pem'), timeout=25) as response:
        data = json.load(response)['data']
    selected = [e for e in data['endpoints'] if e['tag'] == MODELS[mid]['provider_tag']
                and e.get('status') == 0 and not e.get('service_tier')]
    assert len(selected) == 1
    assert selected[0]['name'] == MODELS[mid]['provider_name']+' | '+MODELS[mid]['snapshot']
    assert Decimal(selected[0]['pricing']['prompt'])*10**6 == Decimal(MODELS[mid]['tariff'])
    assert Decimal(selected[0]['pricing']['completion']) == 0
    assert data['architecture']['modality'] == 'text->decisions'
    d.save_bound(target, dict(retrieved=d.timestamps(), source=url, selected_endpoint=selected[0], data=data))


def send(body, key, mid):
    if MODELS[mid]['tariff'] == '0':
        with FREE_LOCK:
            wait = max(0, 3.1-(time.monotonic()-FREE_LAST[0]))
            if wait:
                time.sleep(wait)
            FREE_LAST[0] = time.monotonic()
    return transport.send(body, key, SPEC)


def probe(mid, out):
    path = out/'compatibility_probe.json'
    # Preserve the initial admission evidence; only catalog :free normalization
    # and the unsupported zero-output-token assumption changed before scoring.
    old = ADMISSION/mid
    if not path.exists() and (old/'compatibility_probe.json').exists():
        for name in ('probe_dispatch.json','compatibility_probe.json'):
            d.save_bound(out/name, json.loads((old/name).read_text()))
        d.save_bound(out/'admission_note.json', dict(
            source=str(logical_relative(old, root=ROOT)), source_sha256={name:bank.file_hash(old/name)
                for name in ('probe_dispatch.json','compatibility_probe.json')},
            change='No scored calls preceded this correction. Catalog free suffix is a routing variant; native output token counters are not a reliable reasoning detector.',
            evidence='Baseten technical report describes single-pass option logits; OpenRouter official Jev examples report nonzero output_tokens for native decisions',
            sources=['https://labs.baseten.co/articles/mammoth-1-and-elephant-1-frontier-decision-models',
                     'https://openrouter.ai/blog/insights/what-is-jev/']))
    if not path.exists():
        q = dict(native_input=dict(state='The switch is ON.', questions=dict(decision=dict(type='choice',
            instructions='Select the option matching the switch state exactly.',
            criteria=dict(zip('12345', ('OFF','UNKNOWN','ON','BROKEN','UNPLUGGED')))))))
        body = payload(q, mid)
        assert not (out/'probe_dispatch.json').exists(), 'Unresolved probe dispatch; inspect before any replay'
        d.save_bound(out/'probe_dispatch.json', dict(payload=body, sha256=d.digest(body), started=d.timestamps()))
        d.save_bound(path, dict(payload=body, transport=send(d.canonical(body), credentials(), mid)))
    value = json.loads(path.read_text())
    result = parse(value['transport'], mid)
    assert value['payload'] == json.loads((out/'probe_dispatch.json').read_text())['payload']
    assert result['status'] == 'ok' and result['choice'] == '3', 'Compatibility failed: '+result['status']
    return result


def validate(mid, out, complete=False):
    _, plan = prepare(mid, out)
    attempts, results, dispatches = (d.rows(out/name) for name in ('attempts.jsonl','results.jsonl','dispatches.jsonl'))
    done = d.reconcile(dispatches, attempts, results, plan)
    indexed = {p['request_index']:p for p in plan}
    for row in attempts+results+dispatches:
        assert all(row[k] == v for k,v in indexed[row['request_index']].items())
    for row in attempts:
        assert all(row[k] == v for k,v in parse(row, mid).items()), 'Parser drift'
    first, last = stats.first_and_eventual(attempts)
    for row in results:
        i = row['request_index']
        assert row['attempts'] == last[i]['attempt'] and row['first_status'] == first[i]['status']
        assert row['eventual_status'] == last[i]['status']
    if complete:
        assert len(done) == 1342
        for name, digest in json.loads((out/'completion.json').read_text())['files_sha256'].items():
            assert bank.file_hash(out/name) == digest
    return attempts, results, done


def execute(mid, limit=0):
    out = OUT/mid
    questions, plan = prepare(mid, out)
    with direct.model_lock(out):
        metadata(mid, out)
        p = probe(mid, out)
        print(json.dumps(dict(model=mid, probe=p['status'], latency_ms=p.get('latency_ms'),
                             returned=p['model_returned'], provider=p['provider'])), flush=True)
        attempts, results, done = validate(mid, out)
        if (out/'completion.json').exists():
            validate(mid, out, True)
            return
        if (out/'speed_screen_pause.json').exists() or speed_stop(attempts):
            print('PAUSED_SPEED_SCREEN '+mid, flush=True)
            return
        key = credentials()
        lock = threading.Lock()
        halt = threading.Event()
        def one(task):
            body = d.canonical(payload(questions[task['item_id']], mid))
            assert d.digest(json.loads(body)) == task['request_payload_sha256']
            collected = []
            began = time.perf_counter()
            for attempt in (1,2):
                with lock:
                    if halt.is_set():
                        return
                    known = sum(Decimal(str(a['accounted_cost_usd'])) if a['accounted_cost_usd'] is not None
                                else Decimal(a['request_body_bytes'])*Decimal('.00000006') for a in attempts)
                    assert known < Decimal('.50'), 'Soft cost guard'
                    d.append(out/'dispatches.jsonl', dict(task, attempt=attempt, dispatch=d.timestamps()))
                response = send(body, key, mid)
                row = dict(task, attempt=attempt, **response, **parse(response, mid))
                with lock:
                    d.append(out/'attempts.jsonl', row)
                    attempts.append(row)
                collected.append(row)
                fatal = row['status'] in ('identity_mismatch','provider_mismatch','unexpected_reasoning')
                if fatal or row['http_status'] in (400,401,402,403,404,413,422):
                    halt.set()
                    break
                if attempt == 1 and (row['transport_failure'] or row['http_status'] in d.TRANSIENT):
                    delay = max(1, d.retry_wait(row))
                    with lock:
                        d.append(out/'retry_waits.jsonl', dict(request_index=task['request_index'], seconds=delay))
                    if halt.wait(delay):
                        break
                    continue
                break
            if collected:
                with lock:
                    result = dict(task, attempts=len(collected), first_status=collected[0]['status'],
                                  eventual_status=collected[-1]['status'], item_elapsed_ms=(time.perf_counter()-began)*1000)
                    d.append(out/'results.jsonl', result)
                    results.append(result)
        remaining = [p for p in plan if p['request_index'] not in done]
        if limit:
            remaining = remaining[:limit]
        with ThreadPoolExecutor(max_workers=2) as pool:
            for wave in sorted({p['wave'] for p in remaining}):
                for future in as_completed([pool.submit(one,p) for p in remaining if p['wave'] == wave]):
                    future.result()
                first = [a for a in attempts if a['attempt'] == 1]
                progress = dict(model=mid,n=len(first),planned=1342,latency=stats.quantiles([a['latency_ms'] for a in first]),
                    statuses=dict(Counter(a['status'] for a in first)),
                    known_cost_usd=sum(a['accounted_cost_usd'] or 0 for a in attempts),time=d.timestamps())
                d.append(out/'progress.jsonl', progress)
                if len(first)%20 == 0 or halt.is_set():
                    print(json.dumps(progress), flush=True)
                if halt.is_set():
                    d.save_bound(out/('halt_'+str(len(first))+'.json'), progress)
                    return
                if speed_stop(attempts):
                    d.save_bound(out/'speed_screen_pause.json', progress)
                    print('PAUSED_SPEED_SCREEN '+mid, flush=True)
                    return
        if len(results) == 1342:
            names = ['manifest.json','software.json','model_metadata.json','probe_dispatch.json',
                     'compatibility_probe.json','dispatches.jsonl','attempts.jsonl','results.jsonl']
            if (out/'retry_waits.jsonl').exists():
                names.append('retry_waits.jsonl')
            if (out/'admission_note.json').exists():
                names.append('admission_note.json')
            d.save_bound(out/'completion.json', dict(status='COMPLETE_1342', completed=d.timestamps(),
                files_sha256={name:bank.file_hash(out/name) for name in names}))
            validate(mid, out, True)
            print('COMPLETE_1342 '+mid, flush=True)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--models', nargs='+', choices=MODELS, default=list(MODELS))
    p.add_argument('--execute', action='store_true')
    p.add_argument('--validate', action='store_true')
    p.add_argument('--limit', type=int, default=0)
    args = p.parse_args()
    if not args.execute:
        for mid in args.models:
            if args.validate:
                a,r,done = validate(mid, OUT/mid, (OUT/mid/'completion.json').exists())
                print(json.dumps(dict(model=mid, validated=len(done), attempts=len(a))))
            else:
                _,plan = prepare(mid, OUT/mid)
                print(json.dumps(dict(model=mid, dry_run=True, requests=len(plan), inference_calls=0)))
        return
    with ThreadPoolExecutor(max_workers=len(args.models)) as pool:
        jobs = {pool.submit(execute, mid, args.limit):mid for mid in args.models}
        errors = []
        for future in as_completed(jobs):
            try:
                future.result()
            except Exception as exc:
                errors.append(jobs[future])
                print(json.dumps(dict(model=jobs[future], error=type(exc).__name__+': '+str(exc))), flush=True)
        assert not errors, 'Execution stopped for '+', '.join(errors)


if __name__ == '__main__':
    main()
