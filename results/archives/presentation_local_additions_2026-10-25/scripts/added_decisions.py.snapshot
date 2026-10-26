"""Answer-blind October 16 additions. Dry-run unless --execute.

Each model has its own resumable ledger. Questions and options are unchanged;
the answer key is never read by this executor. No image-to-text substitution.
"""
from __future__ import annotations
from repo_layout import repo_file
from repo_layout import source_file

import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from decimal import Decimal
from hashlib import sha256
import http.client
import json
import math
import os
from pathlib import Path
import ssl
import threading
import time
import urllib.request

import decision_refresh as d

ROOT = Path(__file__).resolve().parents[1]
RUNS = repo_file('runs/additions_2026-10-16', root=ROOT)
ENV = ROOT.parent / 'jev/.env'
MODELS = {
    'microsoft_decision': {
        'label': 'Microsoft-Decision-1', 'model': 'microsoft/microsoft-decision-1',
        'host': 'openrouter.ai', 'path': '/api/alpha/decisions',
        'provider_tag': 'azure', 'provider_name': 'Azure',
        'identities': ['microsoft/microsoft-decision-1-20261009'],
        'key_name': 'OPENROUTER_API_KEY', 'input_usd_per_million': '0.042',
        'pricing_source': 'https://openrouter.ai/microsoft/microsoft-decision-1',
    },
    'nimble_v4': {
        'label': 'Nimble v4', 'model': 'nimble-v4',
        'host': 'api.bespokelabs.ai', 'path': '/v1/systemone',
        'provider_tag': 'bespoke-direct', 'provider_name': 'Bespoke Labs',
        'identities': ['nimble-v4', 'bespokelabs/nimble-v4'],
        'key_name': 'BESPOKE_API_KEY', 'input_usd_per_million': '0.04',
        'pricing_source': 'https://docs.bespokelabs.ai/nimble/pricing',
    },
    'nimble_v4_max': {
        'label': 'Nimble v4 Max', 'model': 'nimble-v4-max',
        'host': 'api.bespokelabs.ai', 'path': '/v1/systemone',
        'provider_tag': 'bespoke-direct', 'provider_name': 'Bespoke Labs',
        'identities': ['nimble-v4-max', 'bespokelabs/nimble-v4-max'],
        'key_name': 'BESPOKE_API_KEY', 'input_usd_per_million': '0.09',
        'pricing_source': 'https://docs.bespokelabs.ai/nimble/pricing',
    },
}
COST_GUARD = Decimal('0.50')


def credentials():
    values = {}
    if ENV.exists():
        for line in ENV.read_text().splitlines():
            if line.strip() and not line.lstrip().startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                values[key.strip()] = value.strip().strip('"\'')
    return {spec['key_name']: os.environ.get(spec['key_name']) or values.get(spec['key_name'], '')
            for spec in MODELS.values()}


def payload(question, model_id):
    spec = MODELS[model_id]
    value = {'model': spec['model'], **d.packet(question)}
    if spec['host'] == 'openrouter.ai':
        value['provider'] = {'only': [spec['provider_tag']], 'allow_fallbacks': False,
                             'require_parameters': True}
    return value


def prepare(model_id, out):
    spec = MODELS[model_id]
    baseline = json.loads((repo_file('data/baseline_reference_manifest.json', root=ROOT)).read_text())
    path = repo_file('data/questions_1136.csv', root=ROOT)
    assert sha256(path.read_bytes()).hexdigest() == baseline['questions_sha256']
    questions = {q['item_id']: q for q in d.read_csv(path)}
    order = list(dict.fromkeys(r['item_id'] for r in d.rows(repo_file('expansion_2026-10-15/request_plan.jsonl', root=ROOT))))
    assert len(questions) == len(order) == 1136 and set(order) == set(questions)
    plan = []
    for position, item in enumerate(order):
        q = questions[item]
        content = {k: q[k] for k in ('instructions', 'context', 'question')}
        content['options'] = [q[f'option_{i}'] for i in range(1, 6)]
        assert d.digest(content) == q['prompt_sha256']
        body = payload(q, model_id)
        plan.append({'request_index': position + 1, 'wave': position // 2 + 1,
                     'item_id': item, 'model_id': model_id, 'model_requested': spec['model'],
                     'prompt_sha256': q['prompt_sha256'], 'native_input_sha256': d.digest(d.packet(q)),
                     'request_payload_sha256': d.digest(body), 'request_body_bytes': len(d.canonical(body))})
    out.mkdir(parents=True, exist_ok=True)
    d.save_bound(out / 'manifest.json', {
        'version': 'october-16-native-decisions-v1', 'model_id': model_id, 'model': spec,
        'questions_sha256': baseline['questions_sha256'], 'questions_each': 1136,
        'planned_cases': 1136, 'endpoint': 'https://' + spec['host'] + spec['path'],
        'input': 'Exact original native choice state, instructions and five criteria; routing only added for OpenRouter',
        'timing': json.loads((repo_file('decision_refresh_2026-10-15/run_manifest.json', root=ROOT)).read_text())['timing'],
        'concurrency': {'maximum_per_model': 2, 'questions_per_wave': 2,
                        'barrier': 'Both cases settle before next wave'},
        'primary': 'First attempt; errors and invalid answers remain unsuccessful',
        'retry': 'At most one recovery for transport failure or HTTP 408/429/5xx; no answer-dependent retries',
        'order': 'Same question order as October 15 eight-LLM run',
        'cost': 'API-reported cost where present; otherwise Nimble input usage times captured public tariff, separately labelled; missing is never zero',
        'known_spend_guard_usd': str(COST_GUARD),
        'guard_limit': 'Soft dispatch guard; missing and in-flight charges prevent a hard billing cap',
        'images': 'Unsupported by documented text-only decision API; no OCR/caption replacement',
        'request_plan': plan,
    })
    d.save_bound(out / 'software.json', {'runner_sha256': sha256(Path(__file__).read_bytes()).hexdigest(),
                                       'tests_sha256': sha256((source_file(repo_file('test_added_decisions.py', root=ROOT))).read_bytes()).hexdigest()})
    return questions, plan


def capture_metadata(model_id, out):
    target = out / 'model_metadata.json'
    if target.exists():
        return
    spec = MODELS[model_id]
    if spec['host'] == 'openrouter.ai':
        url = 'https://openrouter.ai/api/v1/models/' + spec['model'] + '/endpoints'
        context = ssl.create_default_context(cafile='/etc/ssl/cert.pem')
        data = json.load(urllib.request.urlopen(url, context=context, timeout=30))['data']
        matches = [e for e in data['endpoints'] if e['tag'] == spec['provider_tag'] and e.get('status') == 0 and not e.get('service_tier')]
        assert len(matches) == 1 and spec['identities'][0] in matches[0]['name']
        assert Decimal(matches[0]['pricing']['prompt']) * 10**6 == Decimal(spec['input_usd_per_million'])
        assert Decimal(matches[0]['pricing']['completion']) == 0
        assert data['architecture']['input_modalities'] == ['text']
    else:
        data = {'source': 'https://docs.bespokelabs.ai/nimble/overview',
                'pricing_source': spec['pricing_source'], 'input_modalities': ['text', 'json'],
                'input_usd_per_million': spec['input_usd_per_million'], 'output_usd_per_million': '0',
                'limits_source': 'https://docs.bespokelabs.ai/nimble/limits-and-errors',
                'documented_concurrency_before_purchase': 4,
                'identity_limit': 'Named hosted version; no dated immutable checkpoint is documented'}
    d.save_bound(target, {'retrieved': d.timestamps(), 'data': data})


def send(body, key, spec):
    """Same full-body HTTPS timer as October 15; host and path are configurable."""
    context = ssl.create_default_context(cafile='/etc/ssl/cert.pem')
    connection = http.client.HTTPSConnection(spec['host'], timeout=10, context=context)
    result = {'http_status': 0, 'raw_response': {}, 'error': '', 'response_headers': {},
              'headers_latency_ms': None, 'transport_failure': False, 'started': d.timestamps()}
    started = time.perf_counter()
    deadline = started + 90
    try:
        connection.connect()
        sock = connection.sock
        sock.settimeout(max(.001, deadline - time.perf_counter()))
        connection.request('POST', spec['path'], body=body, headers={'Authorization': 'Bearer ' + key,
                           'Content-Type': 'application/json', 'Accept': 'application/json'})
        sock.settimeout(max(.001, deadline - time.perf_counter()))
        response = connection.getresponse()
        result['http_status'] = response.status
        result['headers_latency_ms'] = (time.perf_counter() - started) * 1000
        result['response_headers'] = {k.lower(): v for k, v in response.getheaders() if k.lower() in {
            'x-request-id', 'x-openrouter-request-id', 'retry-after', 'date', 'content-type', 'x-openrouter-cache-status'}}
        chunks, size = [], 0
        while True:
            left = deadline - time.perf_counter()
            if left <= 0:
                raise TimeoutError('90-second total response deadline')
            sock.settimeout(left)
            chunk = response.read1(65536)
            if not chunk:
                break
            chunks.append(chunk)
            size += len(chunk)
            if size > 4 * 1024**2:
                raise ValueError('Unexpected oversized option-ID response')
        text = b''.join(chunks).decode('utf-8').replace(key, '[REDACTED_API_KEY]')
        try:
            result['raw_response'] = json.loads(text)
        except ValueError:
            result['error'] = 'Non-JSON response: ' + text[:300]
        if response.status != 200:
            result['error'] = 'HTTP ' + str(response.status)
    except Exception as exc:
        result['error'] = (type(exc).__name__ + ': ' + str(exc)).replace(key, '[REDACTED_API_KEY]')
        result['transport_failure'] = isinstance(exc, (OSError, http.client.HTTPException))
    finally:
        result['latency_ms'] = (time.perf_counter() - started) * 1000
        result['completed'] = d.timestamps()
        connection.close()
    return result


def parse(response, model_id):
    parsed = d.parse(response)
    spec = MODELS[model_id]
    cost = parsed['reported_cost_usd']
    source = 'api_reported' if cost is not None else 'unreported'
    if cost is None and spec['host'] == 'api.bespokelabs.ai':
        tokens = parsed['usage'].get('input_tokens')
        if response['http_status'] == 200 and isinstance(tokens, int) and not isinstance(tokens, bool) and tokens >= 0:
            cost = float(Decimal(tokens) * Decimal(spec['input_usd_per_million']) / 10**6)
            source = 'usage_times_published_tariff'
        elif response['http_status'] >= 400:
            cost, source = 0.0, 'documented_no_charge_http_error'
    return {**parsed, 'accounted_cost_usd': cost, 'cost_source': source}


def check_identity(record):
    spec = MODELS[record['model_id']]
    if record['http_status'] == 200:
        assert record['model_returned'] in spec['identities'], 'Unexpected returned model; inspect before continuing'
        if spec['host'] == 'openrouter.ai':
            assert record['provider'] == spec['provider_name'], 'Wrong backend'
            assert record['reported_cost_usd'] is not None, 'OpenRouter success omitted cost'
        assert record['status'] == 'ok', 'Successful HTTP response omitted a usable typed decision'


def execute(args):
    model_id, out = args.model, args.out or RUNS / args.model
    questions, plan = prepare(model_id, out)
    if not args.execute:
        print(json.dumps({'mode': 'DRY_RUN', 'model': model_id, 'requests': len(plan), 'paid_calls': 0}))
        return
    spec = MODELS[model_id]
    key = credentials()[spec['key_name']]
    assert key, spec['key_name'] + ' is not configured'
    capture_metadata(model_id, out)
    attempts, results = d.rows(out / 'attempts.jsonl'), d.rows(out / 'results.jsonl')
    done = d.reconcile(d.rows(out / 'dispatches.jsonl'), attempts, results, plan)
    for record in attempts:
        check_identity(record)
    lock, halt = threading.Lock(), threading.Event()

    def one(task):
        body = d.canonical(payload(questions[task['item_id']], model_id))
        assert sha256(body).hexdigest() == task['request_payload_sha256']
        collected = []
        case_start = time.perf_counter()
        try:
            for attempt in (1, 2):
                with lock:
                    if halt.is_set():
                        return
                    assert Decimal(str(math.fsum(a['accounted_cost_usd'] or 0 for a in attempts))) < COST_GUARD
                    d.append(out / 'dispatches.jsonl', {**task, 'attempt': attempt, 'dispatch': d.timestamps()})
                response = send(body, key, spec)
                record = {**task, 'attempt': attempt, **response, **parse(response, model_id)}
                with lock:
                    d.append(out / 'attempts.jsonl', record)
                    attempts.append(record)
                collected.append(record)
                check_identity(record)
                if attempt == 1 and (record['transport_failure'] or record['http_status'] in d.TRANSIENT):
                    wait = d.retry_wait(response)
                    with lock:
                        d.append(out / 'retry_waits.jsonl', {'request_index': task['request_index'], 'seconds': wait})
                    if halt.wait(wait):
                        break
                    continue
                break
            with lock:
                terminal = {**task, 'first_status': collected[0]['status'], 'eventual_status': collected[-1]['status'],
                            'attempts': len(collected), 'item_elapsed_ms': (time.perf_counter() - case_start) * 1000}
                d.append(out / 'results.jsonl', terminal)
                results.append(terminal)
            if collected[-1]['http_status'] in (400, 401, 402, 403, 404, 413, 422):
                raise ValueError('Client rejection; stop for inspection')
        except Exception:
            halt.set()
            raise

    count = 0
    with ThreadPoolExecutor(max_workers=2) as pool:
        for wave in sorted({p['wave'] for p in plan if p['request_index'] not in done}):
            tasks = [p for p in plan if p['wave'] == wave and p['request_index'] not in done]
            errors = []
            for future in as_completed([pool.submit(one, task) for task in tasks]):
                try:
                    future.result()
                except Exception as exc:
                    errors.append(type(exc).__name__ + ': ' + str(exc))
            state = {'model_id': model_id, 'wave': wave, 'completed_cases': len(results),
                     'attempts': len(attempts), 'accounted_cost_usd': math.fsum(a['accounted_cost_usd'] or 0 for a in attempts),
                     'missing_cost_attempts': sum(a['accounted_cost_usd'] is None for a in attempts),
                     'first_status_counts': dict(Counter(r['first_status'] for r in results)), 'time': d.timestamps()}
            d.append(out / 'progress.jsonl', state)
            if errors:
                raise ValueError('; '.join(errors))
            if wave % 25 == 0 or len(results) == 1136 or args.waves:
                print(json.dumps(state), flush=True)
            count += 1
            if args.waves and count >= args.waves:
                return
    assert len(results) == 1136
    names = ['manifest.json', 'software.json', 'model_metadata.json', 'attempts.jsonl', 'dispatches.jsonl', 'results.jsonl']
    d.save_bound(out / 'completion.json', {'status': 'COMPLETE_1136', 'completed': d.timestamps(),
        'files_sha256': {name: sha256((out / name).read_bytes()).hexdigest() for name in names}})


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--model', choices=MODELS, required=True)
    parser.add_argument('--execute', action='store_true')
    parser.add_argument('--waves', type=int, default=0)
    parser.add_argument('--out', type=Path)
    execute(parser.parse_args())
