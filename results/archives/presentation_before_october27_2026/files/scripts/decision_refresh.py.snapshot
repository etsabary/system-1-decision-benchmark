"""Answer-blind three-model Decisions refresh. Dry run unless --execute.

The questions, answer key and eight completed LLM runs are unchanged. This
runner never reads the answer key. Its HTTP timer matches the eight-LLM timer.
"""
from __future__ import annotations
from repo_layout import repo_file
from repo_layout import source_file

import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from hashlib import sha256
import http.client
import json
import math
import os
from pathlib import Path
import random
import ssl
import threading
import time
import urllib.request
from zoneinfo import ZoneInfo

from run_benchmark import canonical_bytes as canonical, digest, packet, read_csv, api_key

ROOT = Path(__file__).resolve().parents[1]
OUT = repo_file('runs/decision_refresh_2026-10-15/run_01', root=ROOT)
PATH = '/api/alpha/decisions'
MODELS = {
    'typesafe/jev-1.13': ('jev113', 'Jev 1.13', 'typesafe', 'TypeSafe', 'typesafe/jev-1.13-20260917'),
    'typesafe/jev-1.14': ('jev114', 'Jev 1.14', 'typesafe', 'TypeSafe', 'typesafe/jev-1.14-20261014'),
    'openai/gpt-6-luna-decisions': ('luna_decisions', 'Luna 6 Decisions', 'openai', 'OpenAI', 'openai/gpt-6-luna-decisions-20261006'),
}
ALLOWED = {'1', '2', '3', '4', '5'}
TRANSIENT = {408, 429, *range(500, 600)}
COST_GUARD = .5


def rows(path):
    return [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()] if Path(path).exists() else []


def append(path, value):
    with Path(path).open('a', encoding='utf-8') as stream:
        stream.write(json.dumps(value, ensure_ascii=False, allow_nan=False)+'\n')
        stream.flush()
        os.fsync(stream.fileno())


def save_bound(path, value):
    path = Path(path)
    if path.exists():
        assert json.loads(path.read_text()) == value, 'Immutable binding changed: '+path.name
    else:
        path.write_text(json.dumps(value, indent=2, ensure_ascii=False)+'\n')


def timestamps():
    now = datetime.now(timezone.utc)
    return {'utc': now.isoformat(), 'toronto': now.astimezone(ZoneInfo('America/Toronto')).isoformat()}


def payload(question, model):
    assert model in MODELS, 'Unapproved model'
    return {'model': model, **packet(question), 'provider': {
        'only': [MODELS[model][2]], 'allow_fallbacks': False, 'require_parameters': True}}


def prepare(out=OUT):
    questions = read_csv(repo_file('data/questions_1136.csv', root=ROOT))
    baseline = json.loads((repo_file('data/baseline_reference_manifest.json', root=ROOT)).read_text())
    assert sha256((repo_file('data/questions_1136.csv', root=ROOT)).read_bytes()).hexdigest() == baseline['questions_sha256']
    assert len(questions) == len({q['item_id'] for q in questions}) == 1136
    indexed = {q['item_id']: q for q in questions}
    order = list(dict.fromkeys(r['item_id'] for r in rows(repo_file('expansion_2026-10-15/request_plan.jsonl', root=ROOT))))
    assert set(order) == set(indexed) and len(order) == 1136
    rng, plan = random.Random(2026101503), []
    for position, item in enumerate(order):
        q = indexed[item]
        content = {k: q[k] for k in ('instructions', 'context', 'question')}
        content['options'] = [q[f'option_{i}'] for i in range(1, 6)]
        assert digest(content) == q['prompt_sha256']
        models = list(MODELS)
        rng.shuffle(models)
        for model in models:
            body = payload(q, model)
            plan.append({'request_index': len(plan)+1, 'question_position': position+1,
                         'wave': position//2+1, 'item_id': item, 'model_requested': model,
                         'prompt_sha256': q['prompt_sha256'], 'native_input_sha256': digest(packet(q)),
                         'request_payload_sha256': digest(body), 'request_body_bytes': len(canonical(body))})
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    save_bound(out/'manifest.json', {
        'version': 'three-decisions-refresh-20261015-v1',
        'models': {m: dict(zip(('summary_id', 'label', 'provider_tag', 'provider_name', 'required_snapshot'), v)) for m, v in MODELS.items()},
        'questions_sha256': baseline['questions_sha256'], 'questions_each': 1136, 'planned_cases': 3408,
        'endpoint': 'https://openrouter.ai'+PATH,
        'input': 'Exact original native choice state, instructions and five criteria; provider routing is the only added request field',
        'llm_reference_plan_sha256': sha256((repo_file('expansion_2026-10-15/request_plan.jsonl', root=ROOT)).read_bytes()).hexdigest(),
        'order': 'Same question order as eight LLMs; model launch order seed 2026101503',
        'concurrency': {'maximum_global': 6, 'maximum_per_model': 2, 'questions_per_wave': 2,
                        'barrier': 'All six cases settle before next two-question wave'},
        'timing': 'New HTTPS connection per attempt; monotonic connect through complete response body; excludes local queue/preparation; retry waits recorded separately',
        'connection_timeout_seconds': 10, 'total_timeout_seconds': 90,
        'primary': 'First attempt for all 1136 cases per model; failures remain unsuccessful',
        'retry': 'At most one recovery for transport failure or HTTP 408/429/5xx, never for a valid wrong answer or probability warning',
        'parser': 'Valid typed choice is scored independently of probability rounding; warnings and confidence validity retained',
        'provider_policy': 'Exact only tag, no fallback; required returned dated checkpoint and provider checked on every HTTP success',
        'known_spend_guard_usd': COST_GUARD, 'guard_limit': 'Soft stop before dispatch; missing/in-flight charges not a hard billing cap',
        'comparison_limit': 'Same day and client timing method, not simultaneous with eight LLMs; native and chat endpoints and backend hardware differ',
        'request_plan': plan,
    })
    save_bound(out/'software.json', {'runner_sha256': sha256(Path(__file__).read_bytes()).hexdigest(),
                                   'tests_sha256': sha256((source_file(repo_file('test_decision_refresh.py', root=ROOT))).read_bytes()).hexdigest()})
    return indexed, plan


def capture_metadata(out):
    path = Path(out)/'model_metadata.json'
    if path.exists():
        return
    context = ssl.create_default_context(cafile='/etc/ssl/cert.pem')
    captured = {}
    for model, spec in MODELS.items():
        url = 'https://openrouter.ai/api/v1/models/'+model+'/endpoints'
        data = json.load(urllib.request.urlopen(url, context=context, timeout=30))['data']
        endpoints = [e for e in data['endpoints'] if e['tag'] == spec[2] and e.get('status') == 0 and not e.get('service_tier')]
        assert len(endpoints) == 1 and spec[4] in endpoints[0]['name'], 'Required snapshot unavailable'
        assert float(endpoints[0]['pricing']['prompt'])*1e6 <= .15
        assert float(endpoints[0]['pricing']['completion']) == 0
        captured[model] = data
    save_bound(path, {'retrieved': timestamps(), 'models': captured})


def send(body, key):
    # Same function as the eight-LLM transport; only the global PATH differs.
    context = ssl.create_default_context(cafile='/etc/ssl/cert.pem')
    connection = http.client.HTTPSConnection('openrouter.ai', timeout=10, context=context)
    result = {'http_status': 0, 'raw_response': {}, 'error': '', 'response_headers': {},
              'headers_latency_ms': None, 'transport_failure': False, 'started': timestamps()}
    started = time.perf_counter()
    deadline = started+90
    try:
        connection.connect()
        sock = connection.sock
        sock.settimeout(max(.001, deadline-time.perf_counter()))
        connection.request('POST', PATH, body=body, headers={'Authorization': 'Bearer '+key,
                           'Content-Type': 'application/json', 'Accept': 'application/json'})
        sock.settimeout(max(.001, deadline-time.perf_counter()))
        response = connection.getresponse()
        result['http_status'] = response.status
        result['headers_latency_ms'] = (time.perf_counter()-started)*1000
        result['response_headers'] = {k.lower(): v for k,v in response.getheaders() if k.lower() in {
            'x-request-id', 'x-openrouter-request-id', 'retry-after', 'date', 'content-type', 'x-openrouter-cache-status'}}
        chunks, size = [], 0
        while True:
            left = deadline-time.perf_counter()
            if left <= 0:
                raise TimeoutError('90-second total response deadline')
            sock.settimeout(left)
            chunk = response.read1(65536)
            if not chunk:
                break
            chunks.append(chunk); size += len(chunk)
            if size > 4*1024**2:
                raise ValueError('Unexpected oversized option-ID response')
        text = b''.join(chunks).decode('utf-8').replace(key, '[REDACTED_API_KEY]')
        try:
            result['raw_response'] = json.loads(text)
        except ValueError:
            result['error'] = 'Non-JSON response: '+text[:300]
        if response.status != 200:
            result['error'] = 'HTTP '+str(response.status)
    except Exception as exc:
        result['error'] = (type(exc).__name__+': '+str(exc)).replace(key, '[REDACTED_API_KEY]')
        result['transport_failure'] = isinstance(exc, (OSError, http.client.HTTPException))
    finally:
        result['latency_ms'] = (time.perf_counter()-started)*1000
        result['completed'] = timestamps()
        connection.close()
    return result


def number(v):
    return not isinstance(v, bool) and isinstance(v, (int, float)) and math.isfinite(v) and v >= 0


def parse(response):
    raw = response.get('raw_response') or {}
    raw = raw if isinstance(raw, dict) else {}
    answers = raw.get('answers') or {}
    answer = answers.get('decision') or {} if isinstance(answers, dict) else {}
    answer = answer if isinstance(answer, dict) else {}
    choice = answer.get('choice')
    usable = response['http_status'] == 200 and not response['error'] and isinstance(choice, str) and choice in ALLOWED
    probs = answer.get('probabilities')
    valid_probs = isinstance(probs, dict) and set(probs) == ALLOWED
    if valid_probs:
        valid_probs = all(number(v) and v <= 1 for v in probs.values()) and abs(sum(probs.values())-1) <= 1e-6
    conf = answer.get('confidence')
    conf_valid = number(conf) and conf <= 1
    usage = raw.get('usage') or {}
    return {'status': 'ok' if usable else 'http_failure' if response['http_status'] != 200 else 'invalid_answer',
            'choice': choice if usable else None, 'probabilities': probs if valid_probs else None,
            'probabilities_valid': bool(valid_probs), 'confidence': conf if conf_valid else None,
            'confidence_valid': bool(conf_valid), 'model_returned': raw.get('model'),
            'provider': raw.get('provider'), 'request_id': raw.get('id'), 'usage': usage,
            'reported_cost_usd': usage.get('cost') if number(usage.get('cost')) else None}


def check_identity(record):
    if record['http_status'] == 200:
        spec = MODELS[record['model_requested']]
        assert record['model_returned'] == spec[4], 'Returned checkpoint differs from required version'
        assert record['provider'] == spec[3], 'Wrong backend provider'
        assert record['reported_cost_usd'] is not None, 'HTTP success omitted cost'


def reconcile(dispatches, attempts, results, plan):
    sig = lambda rr: [(r['request_index'], r['attempt']) for r in rr]
    ds, aa = sig(dispatches), sig(attempts)
    assert len(ds) == len(set(ds)) and len(aa) == len(set(aa)), 'Duplicate attempt signature'
    assert set(ds) == set(aa), 'Unresolved dispatch; do not repeat potentially billed call'
    done = {r['request_index'] for r in results}
    assert len(done) == len(results)
    assert {r['request_index'] for r in attempts} == done, 'Interrupted case needs reconciliation'
    assert done <= {r['request_index'] for r in plan}
    return done


def retry_wait(response):
    value = response.get('response_headers', {}).get('retry-after')
    try:
        return max(0, min(30, float(value)))
    except (TypeError, ValueError):
        try:
            return max(0, min(30, (parsedate_to_datetime(value)-datetime.now(timezone.utc)).total_seconds()))
        except (TypeError, ValueError):
            return 2


def execute(args):
    questions, plan = prepare(args.out)
    if not args.execute:
        print(json.dumps({'mode': 'DRY_RUN', 'models': 3, 'questions_each': 1136, 'requests': len(plan), 'paid_calls': 0}))
        return
    capture_metadata(args.out)
    key = api_key(ROOT.parent/'jev/.env')
    assert key, 'OPENROUTER_API_KEY is not configured'
    attempts, results = rows(args.out/'attempts.jsonl'), rows(args.out/'results.jsonl')
    done = reconcile(rows(args.out/'dispatches.jsonl'), attempts, results, plan)
    for record in attempts:
        check_identity(record)
    lock, halt = threading.Lock(), threading.Event()
    def one(task):
        body = canonical(payload(questions[task['item_id']], task['model_requested']))
        assert sha256(body).hexdigest() == task['request_payload_sha256']
        case_start, collected = time.perf_counter(), []
        try:
            for attempt in (1, 2):
                with lock:
                    if halt.is_set():
                        if collected:
                            break
                        return
                    assert math.fsum(a['reported_cost_usd'] or 0 for a in attempts) < COST_GUARD, 'Known-spend guard reached'
                    append(args.out/'dispatches.jsonl', {**task, 'attempt': attempt, 'dispatch': timestamps()})
                response = send(body, key)
                record = {**task, 'attempt': attempt, **response, **parse(response)}
                with lock:
                    append(args.out/'attempts.jsonl', record)
                    attempts.append(record)
                collected.append(record)
                if attempt == 1 and (record['transport_failure'] or record['http_status'] in TRANSIENT):
                    wait = retry_wait(response)
                    with lock:
                        append(args.out/'retry_waits.jsonl', {'request_index': task['request_index'], 'seconds': wait})
                    if halt.wait(wait):
                        break
                    continue
                break
            first, last = collected[0], collected[-1]
            with lock:
                terminal = {**task, 'first_status': first['status'], 'eventual_status': last['status'],
                            'attempts': len(collected), 'item_elapsed_ms': (time.perf_counter()-case_start)*1000}
                append(args.out/'results.jsonl', terminal)
                results.append(terminal)
                for record in collected:
                    check_identity(record)
                if last['http_status'] in (400, 401, 402, 403, 404, 413, 422):
                    raise ValueError('Client rejection; stop for inspection')
        except Exception:
            halt.set()
            raise
    waves, count = sorted({p['wave'] for p in plan if p['request_index'] not in done}), 0
    with ThreadPoolExecutor(max_workers=6) as pool:
        for wave in waves:
            todo = [p for p in plan if p['wave'] == wave and p['request_index'] not in done]
            errors = []
            for future in as_completed([pool.submit(one, task) for task in todo]):
                try:
                    future.result()
                except Exception as exc:
                    errors.append(type(exc).__name__+': '+str(exc))
            state = {'wave': wave, 'completed_cases': len(results), 'attempts': len(attempts),
                     'known_cost_usd': math.fsum(a['reported_cost_usd'] or 0 for a in attempts),
                     'missing_cost_attempts': sum(a['reported_cost_usd'] is None for a in attempts),
                     'first_status_counts': dict(Counter(r['first_status'] for r in results)),
                     'per_model_cases': dict(Counter(r['model_requested'] for r in results)), 'time': timestamps()}
            append(args.out/'progress.jsonl', state)
            print(json.dumps(state), flush=True)
            if errors:
                raise ValueError('; '.join(errors))
            count += 1
            if args.waves and count >= args.waves:
                return
    assert len(results) == 3408
    names = ['manifest.json', 'software.json', 'model_metadata.json', 'attempts.jsonl', 'dispatches.jsonl', 'results.jsonl']
    save_bound(args.out/'completion.json', {'status': 'COMPLETE_1136_EACH_THREE_DECISIONS', 'completed': timestamps(),
        'files_sha256': {n: sha256((args.out/n).read_bytes()).hexdigest() for n in names}})


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute', action='store_true')
    parser.add_argument('--waves', type=int, default=0)
    parser.add_argument('--out', type=Path, default=OUT)
    execute(parser.parse_args())
