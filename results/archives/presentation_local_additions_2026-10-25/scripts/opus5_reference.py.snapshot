"""Answer-blind Opus 5 reference on the unchanged 1,342-question text bank.

Uses OpenRouter's native Anthropic messages protocol so thinking.type=disabled
is explicit, not merely a request to hide thinking. Dry-run unless --probe or
--execute is supplied. All credentials and runtime evidence stay outside Git.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
from decimal import Decimal
import json
from pathlib import Path
import ssl
import sys
import urllib.request

import bounded_reference_runner as controller
import frontier_reference as base
import sonnet55_reference as native

ROOT, BANK_HASH = base.ROOT, base.BANK_HASH
OUT = ROOT / 'runs/opus5_no_thinking_1342_2026-10-23'
MODEL = 'anthropic/claude-opus-5'
SNAPSHOT = 'anthropic/claude-opus-5-20260723'
SPEC = {'host': 'openrouter.ai', 'path': '/api/v1/messages'}
GUARD = Decimal('5.00')
d, chat, file_hash = base.d, base.chat, base.file_hash
sanitize, parse = native.sanitize, native.parse
PROBE = {'instructions': 'Use only the facts given.',
         'context': 'A parcel has three blue tokens worth 7 points each and two red tokens worth 5 points each.',
         'question': 'What is the total point value of the parcel?',
         'options': ['21', '26', '31', '35', '42']}


def payload(q):
    return {'model': MODEL,
            'messages': [{'role': 'user', 'content': base.render(q) + chat.SUFFIX}],
            'max_tokens': 16, 'stream': False, 'thinking': {'type': 'disabled'},
            'output_config': {'effort': 'high'},
            'provider': {'only': ['anthropic'], 'ignore': ['anthropic/fast'],
                         'allow_fallbacks': False, 'require_parameters': True}}


def prepare():
    questions, original = base.prepare()
    plan = []
    for old in original:
        body = payload(questions[old['item_id']])
        plan.append({**old, 'model_id': 'opus5_none', 'model_requested': MODEL,
                     'message_sha256': d.digest(body['messages']),
                     'request_payload_sha256': d.digest(body),
                     'request_body_bytes': len(d.canonical(body))})
    return questions, plan


def check_route(record):
    if record['status'] in ('transport_failure', 'http_failure', 'provider_error'):
        return
    assert record['model_returned'] in (MODEL, SNAPSHOT), 'Unexpected model identity'
    assert record['provider'] == 'Anthropic', 'Unexpected backend; no silent fallback'
    assert record['reported_cost_usd'] is not None, 'Success omitted API-reported cost'
    assert record['reported_reasoning_tokens'] == 0 and not isinstance(record['reported_reasoning_tokens'], bool), 'Thinking tokens must be explicitly zero'
    assert not record['reasoning_text_present'] and record['status'] != 'unexpected_reasoning', 'No-thinking contract violated or unverified'


def capture_metadata(out):
    target = out / 'model_metadata.json'
    if not target.exists():
        url = 'https://openrouter.ai/api/v1/models/' + MODEL + '/endpoints'
        with urllib.request.urlopen(url, context=ssl.create_default_context(cafile='/etc/ssl/cert.pem'), timeout=30) as response:
            data = json.load(response)
        d.save_bound(target, {'retrieved': d.timestamps(), **data})
    data = json.loads(target.read_text())['data']
    selected = [e for e in data['endpoints'] if e['tag'] == 'anthropic' and e['status'] == 0 and not e.get('service_tier')]
    assert len(selected) == 1 and selected[0]['name'] == 'Anthropic | ' + SNAPSHOT
    assert Decimal(selected[0]['pricing']['prompt']) == Decimal('.000005')
    assert Decimal(selected[0]['pricing']['completion']) == Decimal('.000025')
    return selected[0]


def probe(out):
    out.mkdir(parents=True, exist_ok=True)
    capture_metadata(out)
    key = d.api_key(ROOT.parent / 'jev/.env')
    assert key, 'OPENROUTER_API_KEY not configured'
    for name, effort in (('disabled_high', 'high'), ('disabled_xhigh_rejection', 'xhigh')):
        target = out / (name + '.json')
        dispatch = out / (name + '_dispatch.json')
        body = deepcopy(payload(PROBE))
        body['output_config']['effort'] = effort
        if not target.exists():
            assert not dispatch.exists(), 'Unresolved probe dispatch; do not replay'
            d.save_bound(dispatch, {'payload': body, 'request_payload_sha256': d.digest(body), 'dispatch': d.timestamps()})
            response = sanitize(base.transport.send(d.canonical(body), key, SPEC))
            d.save_bound(target, {'payload': body, 'transport': response})
        saved = json.loads(target.read_text())
        assert saved['payload'] == body
        response = saved['transport']
        record = {**response, **parse(response)}
        if effort == 'high':
            check_route(record)
            assert record['status'] == 'ok' and record['choice'] == '3', 'No-thinking/format compatibility probe failed'
        else:
            error = response['raw_response'].get('error')
            error_text = json.dumps(error).lower()
            assert response['http_status'] == 400 and ('thinking' in error_text or 'effort' in error_text), 'Disabled+xhigh negative control was not rejected as documented'
        print(json.dumps({'probe': name, 'http_status': response['http_status'],
                          'status': record['status'], 'choice': record['choice'],
                          'model_returned': record['model_returned'], 'provider': record['provider'],
                          'thinking_tokens': record['reported_reasoning_tokens'],
                          'thinking_blocks': record['reasoning_text_present'],
                          'latency_ms': response['latency_ms'], 'cost_usd': record['reported_cost_usd'],
                          'error': response['raw_response'].get('error')}), flush=True)
    validate_probe(out)


def validate_probe(out):
    saved = json.loads((out / 'disabled_high.json').read_text())
    dispatch = json.loads((out / 'disabled_high_dispatch.json').read_text())
    assert saved['payload'] == payload(PROBE) == dispatch['payload']
    assert dispatch['request_payload_sha256'] == d.digest(saved['payload'])
    record = {**saved['transport'], **parse(saved['transport'])}
    check_route(record)
    assert record['status'] == 'ok' and record['choice'] == '3'
    negative = json.loads((out / 'disabled_xhigh_rejection.json').read_text())
    expected = deepcopy(payload(PROBE))
    expected['output_config']['effort'] = 'xhigh'
    assert negative['payload'] == expected
    assert negative['transport']['http_status'] == 400
    return record


def probe_cost(out):
    return Decimal(str(validate_probe(out)['reported_cost_usd']))


def software():
    names = ('opus5_reference.py', 'test_opus5_reference.py', 'bounded_reference_runner.py',
             'sonnet55_reference.py', 'frontier_reference.py', 'added_decisions.py',
             'decision_refresh.py', 'text_models.py', 'run_benchmark.py', 'llm_field_2026_10_18.py', 'repo_layout.py')
    return {name: file_hash(ROOT / 'scripts' / name) for name in names}


def freeze(out, plan):
    out.mkdir(parents=True, exist_ok=True)
    endpoint = capture_metadata(out)
    validate_probe(out)
    d.save_bound(out / 'manifest.json', {
        'version': 'opus5-no-thinking-1342-v1', 'model': MODEL, 'catalog_snapshot': SNAPSHOT,
        'question_count': 1342, 'bank_sha256': BANK_HASH,
        'endpoint': 'https://' + SPEC['host'] + SPEC['path'], 'captured_endpoint': endpoint,
        'settings': {k: v for k, v in payload(PROBE).items() if k != 'messages'},
        'identity_limit': 'Named alias and dated endpoint catalog, not immutable-weight attestation',
        'prompt': 'Same frozen1342 questions, choices, numeric-ID-only suffix and seeded order as Sol; no answer key read by executor',
        'concurrency': {'maximum': 2, 'questions_per_wave': 2, 'barrier': True},
        'timing': 'Unmodified added_decisions.send: fresh HTTPS connect through full response body; excludes local preparation/queue/retry waits',
        'retry': 'One recovery for transport failure or HTTP408/429/5xx only; no retries for wrong answers or unusable/explanatory model outputs',
        'primary': 'Every first attempt on all1342; failures count as unsuccessful, recoveries supplementary',
        'no_thinking': 'thinking.type=disabled, output_config.effort=high, no tools; every successful response must explicitly report0 thinking tokens and no thinking blocks',
        'negative_control': 'Same synthetic probe with disabled+xhigh must be rejected withHTTP400 as documented',
        'soft_cost_guard_usd': str(GUARD), 'guard_limit': 'Local soft guard including conservative unknown/in-flight reservations, not vendor billing cap',
        'cost': 'API-reported charges for all primary/recovery calls; successful compatibility probe separately accounted; rejected control charges unreported, never assumed zero',
        'request_plan': plan,
        'sources': ['https://platform.claude.com/docs/en/build-with-claude/thinking',
                    'https://openrouter.ai/anthropic/claude-opus-5'],
        'development_policy': 'Same exploratory development bank;37 author-development exclusions remain in the separate1305 diagnostic'})
    d.save_bound(out / 'software.json', software())


def reserve(task):
    return Decimal(task['request_body_bytes'] + 256) * Decimal('.000005') + Decimal(16) * Decimal('.000025')


def sealed_files(out):
    names = ['manifest.json', 'software.json', 'model_metadata.json', 'disabled_high.json',
             'disabled_high_dispatch.json', 'disabled_xhigh_rejection.json',
             'disabled_xhigh_rejection_dispatch.json', 'dispatches.jsonl', 'attempts.jsonl', 'results.jsonl']
    if (out / 'retry_waits.jsonl').exists():
        names.append('retry_waits.jsonl')
    return names


def validate(out, complete=False):
    _, plan = prepare()
    manifest = json.loads((out / 'manifest.json').read_text())
    assert manifest['request_plan'] == plan and manifest['bank_sha256'] == BANK_HASH
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
    parser.add_argument('--out', type=Path, default=OUT)
    action = parser.add_mutually_exclusive_group()
    action.add_argument('--probe', action='store_true')
    action.add_argument('--execute', action='store_true')
    action.add_argument('--validate', action='store_true')
    parser.add_argument('--waves', type=int, default=0)
    args = parser.parse_args()
    assert args.waves >= 0
    if args.probe:
        probe(args.out)
    elif args.execute:
        controller.execute(sys.modules[__name__], args.out, args.waves)
    elif args.validate:
        attempts, results = validate(args.out, complete=True)
        print(json.dumps({'validation': 'PASS', 'questions': len(results), 'attempts': len(attempts), 'paid_calls': 0}))
    else:
        _, plan = prepare()
        print(json.dumps({'mode': 'DRY_RUN', 'model': MODEL, 'questions': len(plan), 'paid_calls': 0}))


if __name__ == '__main__':
    main()
