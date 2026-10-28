"""Separate DeepSeek1017 no-reasoning JSON-choice compatibility reference.

The failed100-question bare-ID screen stays separate. No answers are retried or
substituted. Same frozen questions/order,16-token cap, route and HTTPS timer.
"""
import argparse
from decimal import Decimal
import json
import sys

import deepseek_v41_1017_reference as native

ROOT, MODEL, SNAPSHOT, BANK_HASH, SPEC, GUARD = native.ROOT, native.MODEL, native.SNAPSHOT, native.BANK_HASH, native.SPEC, native.GUARD
d, chat, file_hash, sanitize, reserve, base = native.d, native.chat, native.file_hash, native.sanitize, native.reserve, native.base
check_route = native.check_route
FORMAT = 'Constrained JSON-choice, exactly one choice:string1-5; same grammar as Sonnet and Opus'
OUT = ROOT / 'runs/deepseek_v41_flash_1017_none_2026-10-23/deepinfra_json_choice'


def configure(route):
    assert route == 'deepinfra'
    native.configure(route)


configure('deepinfra')


def payload(q):
    body = native.payload(q)
    body['response_format'] = {'type': 'json_schema', 'json_schema': {
        'name': 'decision', 'strict': True, 'schema': {'type': 'object',
        'properties': {'choice': {'type': 'string', 'enum': ['1', '2', '3', '4', '5']}},
        'required': ['choice'], 'additionalProperties': False}}}
    return body


def parse(response):
    value = native.parse(response)
    try:
        parsed = json.loads(value['output_text'])
    except (ValueError, TypeError):
        parsed = None
    valid = (isinstance(parsed, dict) and set(parsed) == {'choice'} and
             isinstance(parsed['choice'], str) and parsed['choice'] in chat.ALLOWED)
    eligible = value['status'] in ('ok', 'invalid_output') and value['finish_reason'] == 'stop'
    return {**value, 'status': 'ok' if valid and eligible else value['status'] if not eligible else 'invalid_output',
            'choice': parsed['choice'] if valid and eligible else None,
            'model_output_failure': value['model_output_failure'] and not (valid and eligible)}


def prepare():
    questions, old = native.prepare()
    plan = []
    for task in old:
        body = payload(questions[task['item_id']])
        plan.append({**task, 'model_id': 'deepseek_v41_1017_none_deepinfra_json_choice',
                     'request_payload_sha256': d.digest(body), 'request_body_bytes': len(d.canonical(body))})
    return questions, plan


def probe(out):
    out.mkdir(parents=True, exist_ok=True)
    native.capture_metadata(out)
    target, dispatch = out / 'compatibility_probe.json', out / 'probe_dispatch.json'
    body = payload(native.PROBE)
    if not target.exists():
        assert not dispatch.exists(), 'Unresolved probe dispatch; do not replay'
        key = d.api_key(ROOT.parent / 'jev/.env')
        assert key
        d.save_bound(dispatch, {'payload': body, 'request_payload_sha256': d.digest(body), 'dispatch': d.timestamps()})
        response = sanitize(base.transport.send(d.canonical(body), key, SPEC))
        d.save_bound(target, {'payload': body, 'transport': response})
    record = validate_probe(out)
    print(json.dumps({'status': record['status'], 'choice': record['choice'], 'latency_ms': record['latency_ms'],
                      'reasoning_tokens': record['reported_reasoning_tokens'], 'reasoning_text_present': record['reasoning_text_present'],
                      'cost_usd': record['reported_cost_usd'], 'provider': record['provider'], 'format': FORMAT}), flush=True)


def validate_probe(out):
    saved = json.loads((out / 'compatibility_probe.json').read_text())
    dispatch = json.loads((out / 'probe_dispatch.json').read_text())
    assert saved['payload'] == payload(native.PROBE) == dispatch['payload']
    assert dispatch['request_payload_sha256'] == d.digest(saved['payload'])
    record = {**saved['transport'], **parse(saved['transport'])}
    check_route(record)
    assert record['status'] == 'ok' and record['choice'] == '3'
    return record


def probe_cost(out):
    return Decimal(str(validate_probe(out)['reported_cost_usd']))


def software():
    return {**native.software(), **{name: file_hash(ROOT / 'scripts' / name) for name in
                                   ('deepseek_v41_1017_schema_reference.py', 'test_deepseek_v41_1017_schema_reference.py')}}


def freeze(out, plan):
    out.mkdir(parents=True, exist_ok=True)
    endpoint = native.capture_metadata(out)
    validate_probe(out)
    original = json.loads((native.OUT / 'manifest.json').read_text())
    d.save_bound(out / 'manifest.json', {**original, 'version': 'deepseek-v41-1017-json-choice-none-1342-v1',
        'settings': {k: v for k, v in payload(native.PROBE).items() if k != 'messages'},
        'format': FORMAT, 'request_plan': plan, 'captured_endpoint': endpoint,
        'bare_id_screen': 'Separate stopped100-case screen:10 explanatory/truncated outputs. No pooling or answer replacement.'})
    d.save_bound(out / 'software.json', software())


def sealed_files(out):
    return native.sealed_files(out)


def validate(out, complete=False):
    _, plan = prepare()
    manifest = json.loads((out / 'manifest.json').read_text())
    assert manifest['request_plan'] == plan and manifest['bank_sha256'] == BANK_HASH
    assert json.loads((out / 'software.json').read_text()) == software(), 'Frozen execution software changed'
    validate_probe(out)
    attempts, results, done = native.controller.ledger_state(sys.modules[__name__], out, plan)
    if complete:
        receipt = json.loads((out / 'completion.json').read_text())
        assert receipt['status'] == 'COMPLETE_1342' and done == set(range(1, 1343))
        assert all(file_hash(out / n) == h for n, h in receipt['files_sha256'].items())
    return attempts, results


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group()
    action.add_argument('--probe', action='store_true')
    action.add_argument('--execute', action='store_true')
    action.add_argument('--validate', action='store_true')
    parser.add_argument('--waves', type=int, default=0)
    args = parser.parse_args()
    assert args.waves >= 0
    if args.probe:
        probe(OUT)
    elif args.execute:
        native.controller.execute(sys.modules[__name__], OUT, args.waves)
    elif args.validate:
        attempts, results = validate(OUT, complete=True)
        print(json.dumps({'validation': 'PASS', 'n': len(results), 'attempts': len(attempts), 'paid_calls': 0}))
    else:
        _, plan = prepare()
        print(json.dumps({'mode': 'DRY_RUN', 'questions': len(plan), 'format': FORMAT, 'paid_calls': 0}))
