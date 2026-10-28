"""Answer-blind Sonnet5.5 reference: between_tools, no tools, 1342 questions.

Reuses the frozen Sol bank/render/order and the unchanged historical HTTP timer.
Native Anthropic messages are needed to express the actual no-thinking mode.
No paid requests occur without --execute; previous compatibility probes remain
separate from every scored question.
"""
from repo_layout import repo_file
import argparse
from decimal import Decimal
import json
from pathlib import Path
import sys

import bounded_reference_runner as controller
import frontier_reference as base

ROOT, BANK_HASH = base.ROOT, base.BANK_HASH
OUT = repo_file('runs/sonnet55_no_thinking_2026-10-19', root=ROOT)
MODEL = 'anthropic/claude-sonnet-5.5'
SNAPSHOT = 'anthropic/claude-sonnet-5.5-20260928'
SPEC = {'host': 'openrouter.ai', 'path': '/api/v1/messages'}
GUARD = Decimal('3.00')
d, chat, file_hash, reserve = base.d, base.chat, base.file_hash, base.reserve


def payload(q):
    return {'model': MODEL, 'messages': [{'role': 'user', 'content': base.render(q) + chat.SUFFIX}],
            'max_tokens': 16, 'stream': False, 'thinking': {'type': 'between_tools'},
            'output_config': {'effort': 'high'},
            'provider': {'only': ['anthropic'], 'allow_fallbacks': False, 'require_parameters': True}}


def prepare():
    questions, old_plan = base.prepare()
    plan = []
    for old in old_plan:
        body = payload(questions[old['item_id']])
        plan.append({**old, 'model_id': 'sonnet55_none', 'model_requested': MODEL,
                     'message_sha256': d.digest(body['messages']),
                     'request_payload_sha256': d.digest(body), 'request_body_bytes': len(d.canonical(body))})
    return questions, plan


def sanitize(response):
    raw = response.get('raw_response')
    raw = raw if isinstance(raw, dict) else {}
    clean = {k: raw[k] for k in ('id', 'model', 'provider', 'type', 'role', 'stop_reason') if k in raw}
    if isinstance(raw.get('content'), list):
        clean['content'] = [{k: b[k] for k in ('type', 'text') if k in b} if isinstance(b, dict) else None for b in raw['content']]
    if isinstance(raw.get('usage'), dict):
        u = raw['usage']
        clean['usage'] = {k: u[k] for k in ('input_tokens', 'output_tokens', 'cache_read_input_tokens',
                             'cache_creation_input_tokens', 'cost', 'output_tokens_details', 'service_tier') if k in u}
    if raw.get('error'):
        e = raw['error']
        clean['error'] = {k: e[k] for k in ('code', 'message', 'type', 'param') if k in e} if isinstance(e, dict) else str(e)
    return {k: response[k] for k in ('http_status', 'error', 'response_headers', 'headers_latency_ms',
                    'transport_failure', 'started', 'completed', 'latency_ms') if k in response} | {'raw_response': clean}


def parse(response):
    raw = response.get('raw_response') or {}
    blocks = raw.get('content')
    blocks = blocks if isinstance(blocks, list) else []
    text_blocks = bool(blocks) and all(isinstance(b, dict) and b.get('type') == 'text' and isinstance(b.get('text'), str) for b in blocks)
    text = ''.join(b['text'] for b in blocks) if text_blocks else None
    choice = text.strip() if isinstance(text, str) else None
    raw_usage = raw.get('usage') or {}
    details = raw_usage.get('output_tokens_details') or {}
    reasoning_tokens = details.get('thinking_tokens')
    reasoning_present = any(isinstance(b, dict) and b.get('type') in ('thinking', 'redacted_thinking') for b in blocks)
    no_reasoning = isinstance(reasoning_tokens, int) and not isinstance(reasoning_tokens, bool) and reasoning_tokens == 0 and not reasoning_present
    failed = bool(response.get('transport_failure') or response.get('error') or response.get('http_status') != 200 or raw.get('error'))
    usable = not failed and no_reasoning and choice in chat.ALLOWED and raw.get('stop_reason') == 'end_turn' and text_blocks
    status = ('transport_failure' if response.get('transport_failure') else 'http_failure' if response.get('http_status') != 200 else
              'provider_error' if failed else 'unexpected_reasoning' if not no_reasoning else 'ok' if usable else 'invalid_output')
    cost = raw_usage.get('cost') if chat.number(raw_usage.get('cost')) else None
    # Anthropic's uncached input count excludes cache reads/writes; preserve raw
    # usage too, and normalize the aggregate input count for shared analysis.
    counts = [raw_usage.get(k, 0) for k in ('input_tokens', 'cache_read_input_tokens', 'cache_creation_input_tokens')]
    valid_counts = all(isinstance(v, int) and not isinstance(v, bool) and v >= 0 for v in counts)
    out_tokens = raw_usage.get('output_tokens', 0)
    assert isinstance(out_tokens, int) and not isinstance(out_tokens, bool) and out_tokens >= 0
    input_tokens = sum(counts) if valid_counts else 0
    usage = {'prompt_tokens': input_tokens, 'completion_tokens': out_tokens, 'total_tokens': input_tokens + out_tokens,
             'completion_tokens_details': {'reasoning_tokens': reasoning_tokens}}
    return {'status': status, 'choice': choice if usable else None, 'output_text': text,
            'finish_reason': raw.get('stop_reason'), 'model_returned': raw.get('model'),
            'provider': raw.get('provider'), 'request_id': raw.get('id'), 'usage': usage,
            'reported_cost_usd': cost, 'accounted_cost_usd': cost,
            'cost_source': 'api_reported' if cost is not None else 'unreported',
            'reported_reasoning_tokens': reasoning_tokens, 'reasoning_text_present': reasoning_present,
            'model_output_failure': not failed and status != 'ok'}


def check_route(record):
    if record['status'] in ('transport_failure', 'http_failure', 'provider_error'):
        return
    assert record['model_returned'] in (MODEL, SNAPSHOT) and record['provider'] == 'Anthropic', 'Unexpected route'
    assert record['reported_cost_usd'] is not None, 'Successful response omitted reported cost'
    assert record['status'] != 'unexpected_reasoning', 'No-thinking contract violated or unverified'
    assert record['reported_reasoning_tokens'] == 0 and not isinstance(record['reported_reasoning_tokens'], bool)
    assert not record['reasoning_text_present']


def validate_probe(out):
    path = out / 'preflight/native_probe_high.json'
    probe = json.loads(path.read_text())
    dispatch = json.loads((out / 'preflight/native_probe_high_dispatch.json').read_text())
    assert probe['payload'] == dispatch['payload']
    expected = payload({'instructions': '', 'context': '', 'question': '', 'options': [''] * 5})
    assert {k: v for k, v in probe['payload'].items() if k != 'messages'} == {k: v for k, v in expected.items() if k != 'messages'}
    record = {**sanitize(probe['transport']), **parse(probe['transport'])}
    check_route(record)
    assert record['status'] == 'ok' and record['choice'] == '3'
    return record


def probe_cost(out):
    validate_probe(out)
    values = [json.loads((out / 'preflight' / name).read_text())['transport']['raw_response']['usage']['cost']
              for name in ('native_probe_1.json', 'native_probe_high.json')]
    assert all(chat.number(v) for v in values)
    return sum((Decimal(str(v)) for v in values), Decimal(0))


def software():
    return {**base.software(), **{n: file_hash(repo_file(n, root=ROOT)) for n in ('bounded_reference_runner.py', 'sonnet55_reference.py', 'test_sonnet55_reference.py')}}


def freeze(out, plan):
    out.mkdir(parents=True, exist_ok=True)
    data = json.loads((out / 'model_metadata.json').read_text())['data']
    selected = [e for e in data['endpoints'] if e['tag'] == 'anthropic' and not e.get('service_tier') and e['status'] == 0]
    assert len(selected) == 1 and selected[0]['name'] == 'Anthropic | ' + SNAPSHOT
    assert Decimal(selected[0]['pricing']['prompt']) == Decimal('.000002')
    assert Decimal(selected[0]['pricing']['completion']) == Decimal('.00001')
    validate_probe(out)
    d.save_bound(out / 'manifest.json', {'version': 'sonnet55-no-thinking-1342-v1', 'model': MODEL,
        'catalog_snapshot': SNAPSHOT, 'identity_limit': 'Dated endpoint metadata, returned alias is not immutable-weight attestation',
        'question_count': 1342, 'bank_sha256': BANK_HASH, 'endpoint': 'https://' + SPEC['host'] + SPEC['path'],
        'settings': {k: v for k, v in payload({'instructions': '', 'context': '', 'question': '', 'options': [''] * 5}).items() if k != 'messages'},
        'prompt': 'Same unchanged1342 question text, five choices and numeric-only suffix as the Sol reference',
        'order_seed': base.SEED, 'concurrency': {'maximum': 2, 'questions_per_wave': 2, 'barrier': True},
        'timing': 'Unmodified added_decisions.send: fresh HTTPS connect start through full body, excludes preparation/queue/retry wait',
        'connect_timeout_seconds': 10, 'total_response_timeout_seconds': 90,
        'retry': 'One recovery only for transport failure or HTTP408/429/5xx, never wrong answers, explanations, refusal, truncation or HTTP200 errors',
        'primary': 'All1342 first attempts; failures remain unsuccessful. Recoveries supplementary.',
        'cost': 'API-reported only, all primary/recovery charges; both prior compatibility probes separately accounted, missing is unknown',
        'soft_cost_guard_usd': str(GUARD), 'guard_limit': 'Local soft guard with byte-based unknown/in-flight reservations, not a vendor billing cap',
        'no_reasoning': 'thinking.type=between_tools at high effort, no tools; must report0 thinking tokens and no thinking blocks',
        'development_policy': 'Same exploratory1342 bank; retain37 permanent author-development exclusions in a separate diagnostic',
        'sources': ['https://platform.claude.com/docs/en/models/sonnet-5-5/migration-guide'], 'request_plan': plan})
    d.save_bound(out / 'software.json', software())


def sealed_files(out):
    names = ['manifest.json', 'software.json', 'model_metadata.json', 'preflight/native_probe_1.json',
             'preflight/native_probe_high.json', 'preflight/native_probe_high_dispatch.json',
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
    attempts, results, done = controller.ledger_state(sys.modules[__name__], out, plan)
    if complete:
        receipt = json.loads((out / 'completion.json').read_text())
        assert receipt['status'] == 'COMPLETE_1342' and done == set(range(1, 1343))
        assert all(file_hash(out / n) == h for n, h in receipt['files_sha256'].items())
    return attempts, results


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out', type=Path, default=OUT)
    p.add_argument('--execute', action='store_true')
    p.add_argument('--validate', action='store_true')
    args = p.parse_args()
    assert not (args.execute and args.validate)
    if args.execute:
        # A separate full-bank Sol run must have completed first, as requested.
        base.validate(base.OUT, complete=True)
        controller.execute(sys.modules[__name__], args.out)
    elif args.validate:
        rows, results = validate(args.out, complete=True)
        print(json.dumps({'validation': 'PASS', 'questions': len(results), 'attempts': len(rows), 'paid_calls': 0}))
    else:
        _, plan = prepare()
        print(json.dumps({'mode': 'DRY_RUN', 'model': MODEL, 'questions': len(plan), 'paid_calls': 0}))


if __name__ == '__main__':
    main()
