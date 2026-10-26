"""Answer-blind October 18 native-choice expansion; no scoring or gold-key access.

Reuses the unchanged October 16 full-response transport and October 15 native
question serializer. Existing runs are never modified. Explicit --execute is
required for paid calls; compatibility probes are separate from scored runs.
"""
from __future__ import annotations
from repo_layout import repo_file
from repo_layout import source_file

import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from decimal import Decimal
from hashlib import sha256
import json
import math
from pathlib import Path
import ssl
import threading
import time
import urllib.request

import added_decisions as old
import decision_refresh as d

ROOT = Path(__file__).resolve().parents[1]
RUNS = repo_file('runs/native_field_2026-10-18', root=ROOT)
SOURCES = [Path(__file__).name, 'test_native_field_2026_10_18.py',
           'added_decisions.py', 'decision_refresh.py', 'run_benchmark.py']
MODEL_ROWS = [
    ('liquid_ultra', 'Liquid d1-ultra', 'liquid/d1-ultra', 'liquid', 'Liquid', '20261015', '.042'),
    ('liquid_d1', 'Liquid d1', 'liquid/d1', 'liquid', 'Liquid', '20260930', '.020'),
    ('pplx_decider12', 'Perplexity Decider v1.2', 'perplexity/pplx-decider-v1.2', 'perplexity', 'Perplexity', '20261016', '.020'),
    ('pplx_flash12', 'Perplexity Decider Flash v1.2', 'perplexity/pplx-decider-flash-v1.2', 'perplexity', 'Perplexity', '20261016', '.010'),
    ('respan02', 'Respan Span-02', 'respan/span-02', 'respan', 'Respan', '20261015', '.010'),
    ('clef', 'Cloudflare Clef', 'cloudflare/clef', 'primeintellect', 'PrimeIntellect', '', '.042'),
    ('clef_flash', 'Cloudflare Clef Flash', 'cloudflare/clef-flash', 'primeintellect', 'PrimeIntellect', '', '.021'),
    ('clef_omni', 'Cloudflare Clef Omni', 'cloudflare/clef-omni', 'cloudflare', 'Cloudflare', '20261009', '.150'),
    ('mercury_decide', 'Mercury Decide', 'inception/mercury-decide', 'inception', 'Inception', '20260930', '.020'),
    ('solar_decide', 'Solar Decide', 'upstage/solar-decide', 'upstage', 'Upstage', '20260928', '.050'),
    ('solar_flash', 'Solar Decide Flash', 'upstage/solar-decide-flash', 'upstage', 'Upstage', '20261008', '.050'),
    ('drex20', 'Drex v2.0', 'nace-ai/drex-v2.0', 'deepinfra/us', 'DeepInfra', '20261009', '.060'),
    ('drex15', 'Drex v1.5', 'nace-ai/drex-v1.5', 'deepinfra/us', 'DeepInfra', '20261009', '.040'),
    ('classify1', 'ScaleDown Classify-1', 'scaledown/classify-1', 'scaledown', 'ScaleDown', '20260928', '.040'),
    ('kev4b', 'Kev 4B', 'jaredpalmer/kev-4b', 'phala', 'Phala', '20260924', '.042'),
]
MODELS = {i: dict(label=label, model=model, provider_tag=tag, provider_name=provider,
                  identities=[model + ('-' + date if date else '')],
                  input_usd_per_million=price, host='openrouter.ai', path='/api/alpha/decisions')
          for i, label, model, tag, provider, date, price in MODEL_ROWS}
MAX_KNOWN_COST_PER_MODEL = Decimal('.50')


def payload(question, model_id):
    spec = MODELS[model_id]
    return {'model': spec['model'], **d.packet(question), 'provider': {
        'only': [spec['provider_tag']], 'allow_fallbacks': False, 'require_parameters': True}}


def prepare(model_id, out):
    spec = MODELS[model_id]
    baseline = json.loads((repo_file('data/baseline_reference_manifest.json', root=ROOT)).read_text())
    assert sha256((repo_file('data/questions_1136.csv', root=ROOT)).read_bytes()).hexdigest() == baseline['questions_sha256']
    questions = {q['item_id']: q for q in d.read_csv(repo_file('data/questions_1136.csv', root=ROOT))}
    order = list(dict.fromkeys(r['item_id'] for r in d.rows(repo_file('expansion_2026-10-15/request_plan.jsonl', root=ROOT))))
    assert len(questions) == len(order) == 1136 and set(questions) == set(order)
    plan = []
    for n, item_id in enumerate(order):
        q = questions[item_id]
        original = {k: q[k] for k in ('instructions', 'context', 'question')}
        original['options'] = [q[f'option_{i}'] for i in range(1, 6)]
        assert d.digest(original) == q['prompt_sha256']
        body = payload(q, model_id)
        plan.append(dict(request_index=n+1, wave=n//2+1, item_id=item_id,
                         model_id=model_id, model_requested=spec['model'], prompt_sha256=q['prompt_sha256'],
                         native_input_sha256=d.digest(d.packet(q)), request_payload_sha256=d.digest(body),
                         request_body_bytes=len(d.canonical(body))))
    out.mkdir(parents=True, exist_ok=True)
    d.save_bound(out/'manifest.json', dict(version='native-field-2026-10-18-v1', model_id=model_id,
        model=spec, questions_sha256=baseline['questions_sha256'], planned_cases=1136,
        endpoint='https://openrouter.ai/api/alpha/decisions', request_plan=plan,
        timing=json.loads((repo_file('decision_refresh_2026-10-15/run_manifest.json', root=ROOT)).read_text())['timing'],
        concurrency=dict(maximum_per_model=2, questions_per_wave=2, maximum_active_models=5,
                         barrier='Both cases settle before next wave'),
        primary='First attempt / 1136; no correctness-dependent retries or exclusions',
        retry='At most one recovery for transport failure or HTTP 408/429/5xx only; HTTP-200 provider error envelopes are recorded, not retried',
        cost='API-reported charges; absent charges remain unknown; compatibility probes excluded',
        soft_known_spend_guard_usd=str(MAX_KNOWN_COST_PER_MODEL),
        identity_limit='Returned names and pinned backend are checked, not independent proof of immutable weights; Clef names have no dated checkpoint',
        input='Unchanged native state, instructions, question and five criteria', images_tested=False))
    d.save_bound(out/'software.json', {name: sha256(source_file(repo_file(name, root=ROOT)).read_bytes()).hexdigest() for name in SOURCES})
    return questions, plan


def metadata(model_id, out):
    target = out/'model_metadata.json'
    if target.exists():
        return json.loads(target.read_text())
    spec = MODELS[model_id]
    url = 'https://openrouter.ai/api/v1/models/' + spec['model'] + '/endpoints'
    ctx = ssl.create_default_context(cafile='/etc/ssl/cert.pem')
    with urllib.request.urlopen(url, context=ctx, timeout=30) as response:
        data = json.load(response)['data']
    matches = [e for e in data['endpoints'] if e['tag'] == spec['provider_tag'] and e.get('status') == 0 and not e.get('service_tier')]
    assert len(matches) == 1, 'Pinned active endpoint unavailable'
    endpoint = matches[0]
    assert spec['identities'][0] in endpoint['name']
    assert Decimal(endpoint['pricing']['prompt'])*10**6 == Decimal(spec['input_usd_per_million']), 'Tariff changed'
    assert Decimal(endpoint['pricing']['completion']) == 0
    assert 'text' in data['architecture']['input_modalities']
    value = dict(retrieved=d.timestamps(), source=url, selected_endpoint=endpoint, data=data)
    d.save_bound(target, value)
    return value


def parse(response):
    parsed = d.parse(response)
    raw = response.get('raw_response') or {}
    if isinstance(raw, dict) and raw.get('error'):
        parsed.update(status='provider_error', choice=None)
    elif response.get('transport_failure') or response.get('error'):
        parsed.update(status='transport_failure' if response.get('transport_failure') else 'response_error', choice=None)
    return {**parsed, 'accounted_cost_usd': parsed['reported_cost_usd'],
            'cost_source': 'api_reported' if parsed['reported_cost_usd'] is not None else 'unreported'}


def check_identity(record):
    spec = MODELS[record['model_id']]
    # Error envelopes do not attest a model identity. Preserve them as failures.
    raw = record.get('raw_response') or {}
    if record['http_status'] == 200 and not record.get('transport_failure') and not raw.get('error') and not record.get('error'):
        assert record['model_returned'] in spec['identities'], 'Unexpected model identity'
        assert record['provider'] == spec['provider_name'], 'Unexpected backend'
        assert record['reported_cost_usd'] is not None, 'Successful route omitted cost'


def retryable(record):
    return record.get('transport_failure', False) or record['http_status'] in d.TRANSIENT


def probe(model_id):
    out = RUNS/model_id
    questions, plan = prepare(model_id, out)
    metadata(model_id, out)
    if (out/'compatibility_probe.json').exists():
        r = json.loads((out/'compatibility_probe.json').read_text())
    else:
        assert not (out/'probe_dispatch.json').exists(), 'Unresolved probe dispatch; inspect without replay'
        task = plan[0]
        d.save_bound(out/'probe_dispatch.json', {**task, 'dispatch': d.timestamps()})
        response = old.send(d.canonical(payload(questions[task['item_id']], model_id)),
                            old.credentials()['OPENROUTER_API_KEY'], MODELS[model_id])
        r = {**task, 'stage': 'compatibility_not_scored', **response, **parse(response)}
        d.save_bound(out/'compatibility_probe.json', r)
    check_identity(r)
    assert r['status'] == 'ok', 'Compatibility gate failed: ' + r['status']
    return {k: r.get(k) for k in ('model_id', 'status', 'latency_ms', 'reported_cost_usd', 'model_returned', 'provider')}


def execute(model_id):
    out = RUNS/model_id
    questions, plan = prepare(model_id, out)
    probe(model_id)
    if (out/'completion.json').exists():
        receipt = json.loads((out/'completion.json').read_text())
        assert all(sha256((out/name).read_bytes()).hexdigest() == h for name, h in receipt['files_sha256'].items())
        return dict(model_id=model_id, status='ALREADY_COMPLETE_1136')
    attempts, results = d.rows(out/'attempts.jsonl'), d.rows(out/'results.jsonl')
    done = d.reconcile(d.rows(out/'dispatches.jsonl'), attempts, results, plan)
    for a in attempts:
        check_identity(a)
    key = old.credentials()['OPENROUTER_API_KEY']
    assert key
    lock, halt = threading.Lock(), threading.Event()

    def one(task):
        body = d.canonical(payload(questions[task['item_id']], model_id))
        assert sha256(body).hexdigest() == task['request_payload_sha256']
        collected = []
        start = time.perf_counter()
        try:
            for attempt in (1, 2):
                with lock:
                    if halt.is_set():
                        return
                    assert Decimal(str(math.fsum(a['accounted_cost_usd'] or 0 for a in attempts))) < MAX_KNOWN_COST_PER_MODEL
                    d.append(out/'dispatches.jsonl', {**task, 'attempt': attempt, 'dispatch': d.timestamps()})
                response = old.send(body, key, MODELS[model_id])
                r = {**task, 'attempt': attempt, **response, **parse(response)}
                with lock:
                    d.append(out/'attempts.jsonl', r)
                    attempts.append(r)
                collected.append(r)
                check_identity(r)
                if attempt == 1 and retryable(r):
                    wait = d.retry_wait(response)
                    with lock:
                        d.append(out/'retry_waits.jsonl', dict(request_index=task['request_index'], seconds=wait))
                    if halt.wait(wait):
                        break
                    continue
                break
            with lock:
                terminal = {**task, 'first_status': collected[0]['status'], 'eventual_status': collected[-1]['status'],
                            'attempts': len(collected), 'item_elapsed_ms': (time.perf_counter()-start)*1000}
                d.append(out/'results.jsonl', terminal)
                results.append(terminal)
            if collected[-1]['http_status'] in (400, 401, 402, 403, 404, 413, 422):
                raise ValueError('Client rejection; inspect before continuing')
        except Exception:
            halt.set()
            raise

    with ThreadPoolExecutor(max_workers=2) as pool:
        for wave in sorted({r['wave'] for r in plan if r['request_index'] not in done}):
            tasks = [r for r in plan if r['wave'] == wave and r['request_index'] not in done]
            errors = []
            for f in as_completed([pool.submit(one, task) for task in tasks]):
                try:
                    f.result()
                except Exception as exc:
                    errors.append(type(exc).__name__ + ': ' + str(exc))
            progress = dict(model_id=model_id, wave=wave, completed_cases=len(results), attempts=len(attempts),
                accounted_cost_usd=math.fsum(a['accounted_cost_usd'] or 0 for a in attempts),
                missing_cost_attempts=sum(a['accounted_cost_usd'] is None for a in attempts),
                first_status_counts=dict(Counter(r['first_status'] for r in results)), time=d.timestamps())
            d.append(out/'progress.jsonl', progress)
            if wave % 50 == 0 or len(results) == 1136 or errors:
                print(json.dumps(progress), flush=True)
            if errors:
                raise ValueError('; '.join(errors))
    assert len(results) == len({r['item_id'] for r in results}) == 1136
    d.reconcile(d.rows(out/'dispatches.jsonl'), attempts, results, plan)
    names = ['manifest.json', 'software.json', 'model_metadata.json', 'compatibility_probe.json',
             'probe_dispatch.json', 'attempts.jsonl', 'dispatches.jsonl', 'results.jsonl']
    d.save_bound(out/'completion.json', dict(status='COMPLETE_1136', completed=d.timestamps(),
        files_sha256={n: sha256((out/n).read_bytes()).hexdigest() for n in names}))
    return dict(model_id=model_id, status='COMPLETE_1136')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--models', nargs='+', choices=MODELS, default=list(MODELS))
    p.add_argument('--execute', action='store_true')
    p.add_argument('--probe-only', action='store_true')
    args = p.parse_args()
    if not args.execute:
        for m in args.models:
            _, plan = prepare(m, RUNS/m)
            print(json.dumps(dict(model_id=m, status='DRY_RUN', planned=len(plan), paid_calls=0)))
        return
    assert old.credentials()['OPENROUTER_API_KEY'], 'Missing OpenRouter key'
    failures = []
    with ThreadPoolExecutor(max_workers=5) as pool:
        work = {pool.submit(probe if args.probe_only else execute, m): m for m in args.models}
        for future in as_completed(work):
            m = work[future]
            try:
                print(json.dumps(future.result()), flush=True)
            except Exception as exc:
                failures.append(m)
                print(json.dumps(dict(model_id=m, status='STOPPED_FOR_INSPECTION', error=type(exc).__name__+': '+str(exc))), flush=True)
    if failures:
        raise SystemExit('Inspect models before resuming: ' + ', '.join(failures))


if __name__ == '__main__':
    main()
