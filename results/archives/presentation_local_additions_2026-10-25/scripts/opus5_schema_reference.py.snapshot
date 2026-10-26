"""Separately labelled Opus5 no-thinking JSON-choice reference.

The stopped8-case bare-ID trial is preserved and never pooled into this run.
The question text, order,16-token output cap, timer and disabled thinking remain
unchanged. The sole output is constrained to {"choice":"1".."5"}, as for Sonnet.
"""
from __future__ import annotations

import argparse
from decimal import Decimal
import json
from pathlib import Path
import sys

import opus5_reference as native

ROOT, MODEL, SNAPSHOT, SPEC, GUARD = native.ROOT, native.MODEL, native.SNAPSHOT, native.SPEC, native.GUARD
OUT = ROOT / 'runs/opus5_schema_no_thinking_1342_2026-10-23'
d, chat, file_hash = native.d, native.chat, native.file_hash
sanitize, reserve = native.sanitize, native.reserve


def payload(q):
    body = native.payload(q)
    body['output_config']['format'] = {'type': 'json_schema', 'schema': {
        'type': 'object', 'properties': {'choice': {'type': 'string', 'enum': ['1', '2', '3', '4', '5']}},
        'required': ['choice'], 'additionalProperties': False}}
    return body


def prepare():
    questions, old = native.prepare()
    plan = []
    for task in old:
        body = payload(questions[task['item_id']])
        plan.append({**task, 'model_id': 'opus5_schema_none',
                     'request_payload_sha256': d.digest(body), 'request_body_bytes': len(d.canonical(body))})
    return questions, plan


def parse(response):
    value = native.parse(response)
    raw = response.get('raw_response') or {}
    if response.get('http_status') == 200 and not response.get('error') and raw.get('stop_reason') == 'refusal':
        return {**value, 'status': 'refusal', 'choice': None, 'model_output_failure': True}
    try:
        decoded = json.loads(value['output_text'])
    except (ValueError, TypeError):
        decoded = None
    valid = (isinstance(decoded, dict) and set(decoded) == {'choice'} and
             isinstance(decoded['choice'], str) and decoded['choice'] in chat.ALLOWED)
    eligible = value['status'] in ('ok', 'invalid_output') and value['finish_reason'] == 'end_turn'
    status = 'ok' if valid and eligible else value['status'] if not eligible else 'invalid_output'
    return {**value, 'status': status, 'choice': decoded['choice'] if valid and eligible else None,
            'model_output_failure': value['model_output_failure'] and not (valid and eligible)}


def check_route(record):
    if record['status'] in ('transport_failure', 'http_failure', 'provider_error'):
        return
    assert record['model_returned'] in (MODEL, SNAPSHOT) and record['provider'] == 'Anthropic', 'Unexpected model or provider'
    if record['status'] == 'refusal':
        # A refusal is unsuccessful, not an answered question with verified0
        # reasoning tokens. Its missing charge remains unknown, never zero.
        return
    native.check_route(record)


def probe(out):
    out.mkdir(parents=True, exist_ok=True)
    native.capture_metadata(out)
    native.validate_probe(native.OUT)
    target, dispatch = out / 'compatibility_probe.json', out / 'probe_dispatch.json'
    body = payload(native.PROBE)
    if not target.exists():
        assert not dispatch.exists(), 'Unresolved probe dispatch; do not replay'
        key = d.api_key(ROOT.parent / 'jev/.env')
        assert key
        d.save_bound(dispatch, {'payload': body, 'request_payload_sha256': d.digest(body), 'dispatch': d.timestamps()})
        response = sanitize(native.base.transport.send(d.canonical(body), key, SPEC))
        d.save_bound(target, {'payload': body, 'transport': response})
    value = validate_probe(out)
    print(json.dumps({'probe': 'json_choice_disabled_high', 'status': value['status'],
                      'choice': value['choice'], 'thinking_tokens': value['reported_reasoning_tokens'],
                      'thinking_blocks': value['reasoning_text_present'], 'cost_usd': value['reported_cost_usd'],
                      'latency_ms': value['latency_ms'], 'provider': value['provider'], 'model': value['model_returned']}), flush=True)


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
                                   ('opus5_schema_reference.py', 'test_opus5_schema_reference.py')}}


def freeze(out, plan):
    out.mkdir(parents=True, exist_ok=True)
    endpoint = native.capture_metadata(out)
    validate_probe(out)
    d.save_bound(out / 'manifest.json', {
        'version': 'opus5-json-choice-no-thinking-1342-v1', 'model': MODEL,
        'catalog_snapshot': SNAPSHOT, 'bank_sha256': native.BANK_HASH, 'question_count': 1342,
        'endpoint': 'https://' + SPEC['host'] + SPEC['path'], 'captured_endpoint': endpoint,
        'settings': {k: v for k, v in payload(native.PROBE).items() if k != 'messages'},
        'prompt': 'Unchanged frozen1342 question text, choice order, numeric-ID suffix and seeded Sol order; JSON grammar only added, no tools',
        'format': 'Separately labelled JSON-choice exactly one property choice:string1-5, same output grammar as Sonnet reference',
        'bare_id_trial': 'Separate stopped8-case compliance trial; never pooled or substituted into this run',
        'no_thinking': 'Explicit thinking.type=disabled at high effort; successful responses require reported0 thinking tokens and no thinking blocks',
        'refusal': 'Unsuccessful first attempt; missing reasoning telemetry is unverified and missing monetary receipt remains unknown',
        'concurrency': {'maximum': 2, 'questions_per_wave': 2, 'barrier': True},
        'timing': 'Unmodified fresh-HTTPS/full-body added_decisions.send timer; no local preparation/queue/retry waits',
        'retry': 'At most1 recovery for transport failure or HTTP408/429/5xx; no retries for explanations, refusals, truncation or wrong valid answers',
        'cost': 'API-reported primary/recovery costs; missing charges unknown; probe and initial bare-ID trial costs kept separately',
        'soft_cost_guard_usd': str(GUARD), 'request_plan': plan,
        'development_policy': 'Same exploratory development bank;37 permanent author-development exclusions retained separately'})
    d.save_bound(out / 'software.json', software())


def sealed_files(out):
    names = ['manifest.json', 'software.json', 'model_metadata.json', 'compatibility_probe.json',
             'probe_dispatch.json', 'dispatches.jsonl', 'attempts.jsonl', 'results.jsonl']
    if (out / 'retry_waits.jsonl').exists():
        names.append('retry_waits.jsonl')
    return names


def validate(out, complete=False):
    _, plan = prepare()
    manifest = json.loads((out / 'manifest.json').read_text())
    assert manifest['request_plan'] == plan and manifest['bank_sha256'] == native.BANK_HASH
    assert json.loads((out / 'software.json').read_text()) == software(), 'Frozen execution software changed'
    validate_probe(out)
    attempts, results, done = native.controller.ledger_state(sys.modules[__name__], out, plan)
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
        native.controller.execute(sys.modules[__name__], args.out, args.waves)
    elif args.validate:
        attempts, results = validate(args.out, complete=True)
        print(json.dumps({'validation': 'PASS', 'questions': len(results), 'attempts': len(attempts), 'paid_calls': 0}))
    else:
        _, plan = prepare()
        print(json.dumps({'mode': 'DRY_RUN', 'model': MODEL, 'questions': len(plan), 'paid_calls': 0}))


if __name__ == '__main__':
    main()
