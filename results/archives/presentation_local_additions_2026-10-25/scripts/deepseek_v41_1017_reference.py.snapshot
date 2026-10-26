"""Answer-blind dated DeepSeek V4.1 Flash1017 reasoning-none reference.

The native DeepSeek and DeepInfra FP8 routes have separate ledgers. Never pool
route probes or change a route mid-run. Dry-run unless explicitly dispatched.
"""
from __future__ import annotations

import argparse
from decimal import Decimal
import json
from pathlib import Path
import ssl
import sys
import urllib.request

import bounded_reference_runner as controller
import frontier_reference as base
import llm_field_2026_10_18 as hygiene

ROOT, BANK_HASH = base.ROOT, base.BANK_HASH
MODEL = 'deepseek/deepseek-v4.1-flash-1017'
SNAPSHOT = 'deepseek/deepseek-v4.1-flash-20261017'
SPEC = {'host': 'openrouter.ai', 'path': '/api/v1/chat/completions'}
GUARD = Decimal('0.50')
ROUTES = {'deepseek': {'tag': 'deepseek', 'name': 'DeepSeek', 'prompt': '.00000015', 'output': '.0000006'},
          'deepinfra': {'tag': 'deepinfra/fp8', 'name': 'DeepInfra', 'prompt': '.000000098', 'output': '.000000294'}}
ROUTE = 'deepseek'
OUT = ROOT / 'runs/deepseek_v41_flash_1017_none_2026-10-23' / ROUTE
d, chat, file_hash, parse = base.d, base.chat, base.file_hash, base.parse
sanitize = hygiene.sanitize_response
PROBE = {'instructions': 'Use only the facts given.',
         'context': 'A parcel has three blue tokens worth 7 points each and two red tokens worth 5 points each.',
         'question': 'What is the total point value of the parcel?',
         'options': ['21', '26', '31', '35', '42']}


def configure(route):
    global ROUTE, OUT
    assert route in ROUTES
    ROUTE = route
    OUT = ROOT / 'runs/deepseek_v41_flash_1017_none_2026-10-23' / route


def payload(q):
    return {'model': MODEL, 'messages': [{'role': 'user', 'content': base.render(q) + chat.SUFFIX}],
            'max_tokens': 16, 'stream': False, 'usage': {'include': True},
            'reasoning': {'enabled': False, 'effort': 'none'},
            'provider': {'only': [ROUTES[ROUTE]['tag']], 'allow_fallbacks': False, 'require_parameters': True}}


def prepare():
    questions, old = base.prepare()
    plan = []
    for task in old:
        body = payload(questions[task['item_id']])
        plan.append({**task, 'model_id': 'deepseek_v41_1017_none_' + ROUTE, 'model_requested': MODEL,
                     'message_sha256': d.digest(body['messages']),
                     'request_payload_sha256': d.digest(body), 'request_body_bytes': len(d.canonical(body))})
    return questions, plan


def check_route(record):
    if record['status'] in ('transport_failure', 'http_failure', 'provider_error'):
        return
    assert record['provider'] == ROUTES[ROUTE]['name'], 'Unexpected backend; no silent fallback'
    assert record['model_returned'] in (MODEL, SNAPSHOT), 'Unexpected model/update identity'
    assert record['reported_cost_usd'] is not None, 'Success omitted API-reported charge'
    assert record['reported_reasoning_tokens'] == 0 and not isinstance(record['reported_reasoning_tokens'], bool), 'Reasoning tokens are not explicitly zero'
    assert not record['reasoning_text_present'] and record['status'] != 'unexpected_reasoning', 'No-reasoning contract violated or unverified'


def capture_metadata(out):
    path = out / 'model_metadata.json'
    if not path.exists():
        url = 'https://openrouter.ai/api/v1/models/' + MODEL + '/endpoints'
        with urllib.request.urlopen(url, context=ssl.create_default_context(cafile='/etc/ssl/cert.pem'), timeout=30) as response:
            data = json.load(response)
        d.save_bound(path, {'retrieved': d.timestamps(), **data})
    data = json.loads(path.read_text())['data']
    assert data['id'] == MODEL and 'October 17, 2026' in data['description']
    selected = [e for e in data['endpoints'] if e['tag'] == ROUTES[ROUTE]['tag'] and e['status'] == 0 and not e.get('service_tier')]
    assert len(selected) == 1 and selected[0]['name'] == ROUTES[ROUTE]['name'] + ' | ' + SNAPSHOT
    assert {'max_tokens', 'reasoning'} <= set(selected[0]['supported_parameters'])
    assert Decimal(selected[0]['pricing']['prompt']) == Decimal(ROUTES[ROUTE]['prompt'])
    assert Decimal(selected[0]['pricing']['completion']) == Decimal(ROUTES[ROUTE]['output'])
    return selected[0]


def probe(out):
    out.mkdir(parents=True, exist_ok=True)
    capture_metadata(out)
    target, dispatch = out / 'compatibility_probe.json', out / 'probe_dispatch.json'
    body = payload(PROBE)
    if not target.exists():
        assert not dispatch.exists(), 'Unresolved probe dispatch; do not replay'
        key = d.api_key(ROOT.parent / 'jev/.env')
        assert key
        d.save_bound(dispatch, {'payload': body, 'request_payload_sha256': d.digest(body), 'dispatch': d.timestamps()})
        response = sanitize(base.transport.send(d.canonical(body), key, SPEC))
        d.save_bound(target, {'payload': body, 'transport': response})
    record = validate_probe(out)
    print(json.dumps({'route': ROUTE, 'status': record['status'], 'choice': record['choice'],
                      'reasoning_tokens': record['reported_reasoning_tokens'],
                      'reasoning_text_present': record['reasoning_text_present'],
                      'cost_usd': record['reported_cost_usd'], 'latency_ms': record['latency_ms'],
                      'provider': record['provider'], 'model': record['model_returned']}), flush=True)


def validate_probe(out):
    saved = json.loads((out / 'compatibility_probe.json').read_text())
    dispatch = json.loads((out / 'probe_dispatch.json').read_text())
    assert saved['payload'] == payload(PROBE) == dispatch['payload']
    assert dispatch['request_payload_sha256'] == d.digest(saved['payload'])
    record = {**saved['transport'], **parse(saved['transport'])}
    check_route(record)
    assert record['status'] == 'ok' and record['choice'] == '3'
    return record


def probe_cost(out):
    return Decimal(str(validate_probe(out)['reported_cost_usd']))


def software():
    names = ('deepseek_v41_1017_reference.py', 'test_deepseek_v41_1017_reference.py',
             'bounded_reference_runner.py', 'frontier_reference.py', 'added_decisions.py',
             'decision_refresh.py', 'text_models.py', 'llm_field_2026_10_18.py', 'run_benchmark.py', 'repo_layout.py')
    return {name: file_hash(ROOT / 'scripts' / name) for name in names}


def freeze(out, plan):
    out.mkdir(parents=True, exist_ok=True)
    endpoint = capture_metadata(out)
    validate_probe(out)
    d.save_bound(out / 'manifest.json', {
        'version': 'deepseek-v41-flash-1017-reasoning-none-1342-v1', 'model': MODEL,
        'catalog_snapshot': SNAPSHOT, 'route': ROUTE, 'captured_endpoint': endpoint,
        'bank_sha256': BANK_HASH, 'question_count': 1342,
        'settings': {k: v for k, v in payload(PROBE).items() if k != 'messages'},
        'prompt': 'Unchanged frozen1342 question text, five choices, numeric-ID-only suffix and seeded Sol order; no tools,16 output tokens',
        'no_reasoning': 'reasoning.enabled=false and effort=none; every successful response must explicitly report0 reasoning tokens and no reasoning content',
        'identity_limit': 'Dated1017 route and provider metadata; returned alias is not immutable-weight attestation',
        'concurrency': {'maximum': 2, 'questions_per_wave': 2, 'barrier': True},
        'timing': 'Unmodified fresh-HTTPS/full-body timer, no local preparation/queue/retry waits',
        'primary': 'All1342 first attempts; unusable responses unsuccessful, no answer-dependent retries',
        'retry': 'At most1 recovery for transport failure or HTTP408/429/5xx; no retries for wrong valid answers, explanations, truncation or refusals',
        'cost': 'API-reported charges including recovery attempts; compatibility probe separate, missing never zero; native provider has scheduled tariffs',
        'soft_cost_guard_usd': str(GUARD), 'request_plan': plan,
        'development_policy': 'Same exploratory bank;37 author-development exclusions retained in separate1305 diagnostic',
        'sources': ['https://api-docs.deepseek.com/', 'https://api-docs.deepseek.com/api/create-chat-completion/',
                    'https://openrouter.ai/deepseek/deepseek-v4.1-flash-1017']})
    d.save_bound(out / 'software.json', software())


def reserve(task):
    return Decimal(task['request_body_bytes'] + 256) * Decimal('.0000003') + Decimal(16) * Decimal('.0000012')


def sealed_files(out):
    names = ['manifest.json', 'software.json', 'model_metadata.json', 'compatibility_probe.json',
             'probe_dispatch.json', 'dispatches.jsonl', 'attempts.jsonl', 'results.jsonl']
    if (out / 'retry_waits.jsonl').exists():
        names.append('retry_waits.jsonl')
    return names


def validate(out, complete=False):
    _, plan = prepare()
    manifest = json.loads((out / 'manifest.json').read_text())
    assert manifest['request_plan'] == plan and manifest['bank_sha256'] == BANK_HASH
    assert manifest['route'] == ROUTE
    assert json.loads((out / 'software.json').read_text()) == software(), 'Frozen execution software changed'
    validate_probe(out)
    attempts, results, done = controller.ledger_state(sys.modules[__name__], out, plan)
    if complete:
        receipt = json.loads((out / 'completion.json').read_text())
        assert receipt['status'] == 'COMPLETE_1342' and done == set(range(1, 1343))
        assert all(file_hash(out / n) == h for n, h in receipt['files_sha256'].items())
    return attempts, results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--route', choices=tuple(ROUTES), default='deepseek')
    action = parser.add_mutually_exclusive_group()
    action.add_argument('--probe', action='store_true')
    action.add_argument('--execute', action='store_true')
    action.add_argument('--validate', action='store_true')
    parser.add_argument('--waves', type=int, default=0)
    args = parser.parse_args()
    assert args.waves >= 0
    configure(args.route)
    if args.probe:
        probe(OUT)
    elif args.execute:
        controller.execute(sys.modules[__name__], OUT, args.waves)
    elif args.validate:
        attempts, results = validate(OUT, complete=True)
        print(json.dumps({'validation': 'PASS', 'questions': len(results), 'attempts': len(attempts), 'paid_calls': 0}))
    else:
        _, plan = prepare()
        print(json.dumps({'mode': 'DRY_RUN', 'model': MODEL, 'route': ROUTE, 'questions': len(plan), 'paid_calls': 0}))


if __name__ == '__main__':
    main()
