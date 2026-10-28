"""Separately labelled Sonnet5.5 JSON-choice reference; no thinking or tools.

The failed bare-ID trial is preserved, never pooled into this run. Questions,
option order, prompt text,16-token cap and HTTPS timer are unchanged. Only the
output grammar is constrained to a one-property JSON object with five choices.
"""
from repo_layout import repo_file
import argparse
from decimal import Decimal
import json
from pathlib import Path
import sys

import sonnet55_reference as native

ROOT, MODEL, SNAPSHOT, SPEC, GUARD = native.ROOT, native.MODEL, native.SNAPSHOT, native.SPEC, native.GUARD
OUT = repo_file('runs/sonnet55_schema_none_1342_2026-10-19', root=ROOT)
PROBE = repo_file('runs/sonnet55_schema_probe_2026-10-19/probe.json', root=ROOT)
BANK_HASH = native.BANK_HASH
d, chat, file_hash, reserve = native.d, native.chat, native.file_hash, native.reserve
sanitize, check_route = native.sanitize, native.check_route


def payload(q):
    body = native.payload(q)
    body['output_config']['format'] = {'type': 'json_schema', 'schema': {'type': 'object',
        'properties': {'choice': {'type': 'string', 'enum': ['1', '2', '3', '4', '5']}},
        'required': ['choice'], 'additionalProperties': False}}
    return body


def prepare():
    questions, old = native.prepare()
    plan = []
    for t in old:
        body = payload(questions[t['item_id']])
        plan.append({**t, 'model_id': 'sonnet55_schema_none',
                     'request_payload_sha256': d.digest(body), 'request_body_bytes': len(d.canonical(body))})
    return questions, plan


def parse(response):
    value = native.parse(response)
    try:
        parsed = json.loads(value['output_text'])
    except (ValueError, TypeError):
        parsed = None
    valid = (isinstance(parsed, dict) and set(parsed) == {'choice'} and
             isinstance(parsed['choice'], str) and parsed['choice'] in chat.ALLOWED)
    eligible = value['status'] in ('ok', 'invalid_output') and value['finish_reason'] == 'end_turn'
    return {**value, 'status': 'ok' if valid and eligible else value['status'] if not eligible else 'invalid_output',
            'choice': parsed['choice'] if valid and eligible else None,
            'model_output_failure': value['model_output_failure'] and not (valid and eligible)}


def validate_probe(out):
    probe = json.loads(PROBE.read_text())
    expected = payload({'instructions': '', 'context': '', 'question': '', 'options': [''] * 5})
    assert {k: v for k, v in probe['payload'].items() if k != 'messages'} == {k: v for k, v in expected.items() if k != 'messages'}
    record = {**probe['response'], **parse(probe['response'])}
    check_route(record)
    assert record['status'] == 'ok'
    return record


def probe_cost(out):
    return Decimal(str(validate_probe(out)['reported_cost_usd']))


def software():
    return {**native.software(), **{n: file_hash(repo_file(n, root=ROOT)) for n in ('sonnet55_schema_reference.py', 'test_sonnet55_schema_reference.py')}}


def freeze(out, plan):
    out.mkdir(parents=True, exist_ok=True)
    validate_probe(out)
    d.save_bound(out / 'model_metadata.json', json.loads((native.OUT / 'model_metadata.json').read_text()))
    d.save_bound(out / 'compatibility_probe.json', json.loads(PROBE.read_text()))
    prior = json.loads((native.OUT / 'manifest.json').read_text())
    settings = payload({'instructions': '', 'context': '', 'question': '', 'options': [''] * 5})
    d.save_bound(out / 'manifest.json', {**prior, 'version': 'sonnet55-json-choice-no-thinking-1342-v1',
        'settings': {k: v for k, v in settings.items() if k != 'messages'}, 'request_plan': plan,
        'format': 'Constrained JSON object with exactly one choice string1-5; no explanation field or tools',
        'compatibility_probe_sha256': file_hash(PROBE),
        'previous_bare_id_trial': 'Separate stopped110-case output-compliance finding, never pooled into this run',
        'cost': 'API-reported primary/recovery charges; JSON compatibility probe separate; earlier bare-ID trial costs remain separate'})
    d.save_bound(out / 'software.json', software())


def sealed_files(out):
    names = ['manifest.json', 'software.json', 'model_metadata.json', 'compatibility_probe.json',
             'dispatches.jsonl', 'attempts.jsonl', 'results.jsonl']
    if (out / 'retry_waits.jsonl').exists():
        names.append('retry_waits.jsonl')
    return names


def validate(out, complete=False):
    _, plan = prepare()
    manifest = json.loads((out / 'manifest.json').read_text())
    assert manifest['request_plan'] == plan and manifest['bank_sha256'] == BANK_HASH
    assert json.loads((out / 'software.json').read_text()) == software()
    validate_probe(out)
    attempts, results, done = native.controller.ledger_state(sys.modules[__name__], out, plan)
    if complete:
        receipt = json.loads((out / 'completion.json').read_text())
        assert receipt['status'] == 'COMPLETE_1342' and done == set(range(1, 1343))
        assert all(file_hash(out / n) == h for n, h in receipt['files_sha256'].items())
    return attempts, results


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--execute', action='store_true')
    p.add_argument('--validate', action='store_true')
    args = p.parse_args()
    assert not (args.execute and args.validate)
    if args.execute:
        native.base.validate(native.base.OUT, complete=True)
        native.controller.execute(sys.modules[__name__], OUT)
    elif args.validate:
        rows, results = validate(OUT, complete=True)
        print(json.dumps({'validation': 'PASS', 'questions': len(results), 'attempts': len(rows), 'paid_calls': 0}))
    else:
        print(json.dumps({'mode': 'DRY_RUN', 'model': MODEL, 'questions': len(prepare()[1]), 'paid_calls': 0}))


if __name__ == '__main__':
    main()
