"""Qwen3.8-Max reasoning-none reference through existing Hyper Charm access.

No purchases, top-ups, provider changes, tools or answer-dependent retries.
Reported USD-equivalent usage and Hypercredits are not a cash invoice. Hyper
does not expose reasoning-token telemetry here: record that as unknown, not0.
"""
from repo_layout import repo_file
import argparse
from collections import Counter
from decimal import Decimal
import json
import os
from pathlib import Path
import time
import sys

import bounded_reference_runner as controller
import frontier_reference as base

ROOT, BANK_HASH = base.ROOT, base.BANK_HASH
OUT = repo_file('runs/hyper_qwen38max_none_1342_2026-10-19', root=ROOT)
MODEL = 'qwen3.8-max'
SPEC = {'host': 'hyper.charm.land', 'path': '/v1/chat/completions'}
GUARD = Decimal('3.00')
d, chat, file_hash, reserve = base.d, base.chat, base.file_hash, base.reserve
sanitize = base.hygiene.sanitize_response


def credentials(env):
    values = {}
    if env and env.exists():
        for line in env.read_text().splitlines():
            if '=' in line and not line.lstrip().startswith('#'):
                k, v = line.split('=', 1)
                if k.strip() in ('HYPER_CHARM_API_KEY', 'HYPER_API_KEY'):
                    values[k.strip()] = v.strip().strip('"\'')
    return (os.environ.get('HYPER_CHARM_API_KEY') or os.environ.get('HYPER_API_KEY') or
            values.get('HYPER_CHARM_API_KEY') or values.get('HYPER_API_KEY'))


def payload(q):
    return {'model': MODEL, 'messages': [{'role': 'user', 'content': base.render(q) + chat.SUFFIX}],
            'max_tokens': 16, 'stream': False, 'reasoning_effort': 'none'}


def prepare():
    questions, old = base.prepare()
    plan = []
    for t in old:
        body = payload(questions[t['item_id']])
        plan.append({**t, 'model_id': 'hyper_qwen38max_none', 'model_requested': MODEL,
                     'request_payload_sha256': d.digest(body), 'request_body_bytes': len(d.canonical(body))})
    return questions, plan


def parse(response):
    value = chat.parse(response)
    raw = response.get('raw_response') or {}
    choices = raw.get('choices') or []
    message = choices[0].get('message', {}) if len(choices) == 1 and isinstance(choices[0], dict) else {}
    reasoning_present = bool(message.get('reasoning') or message.get('reasoning_content') or message.get('reasoning_details'))
    count = value['reported_reasoning_tokens']
    violation = reasoning_present or (count is not None and (isinstance(count, bool) or count != 0))
    failed = bool(response.get('transport_failure') or response.get('error') or response.get('http_status') != 200 or raw.get('error'))
    status = ('transport_failure' if response.get('transport_failure') else 'http_failure' if response.get('http_status') != 200 else
              'provider_error' if failed else 'unexpected_reasoning' if violation else value['status'])
    cost = value['usage'].get('cost')
    cost = cost if isinstance(cost, dict) else {}
    usd = cost.get('usd') if chat.number(cost.get('usd')) else None
    credits = cost.get('hypercredits') if chat.number(cost.get('hypercredits')) else None
    return {**value, 'status': status, 'choice': value['choice'] if status == 'ok' else None,
            'provider': 'Hyper Charm (request host)', 'provider_identity_source': 'TLS request host, not upstream provider telemetry',
            'reported_cost_usd': usd, 'accounted_cost_usd': usd,
            'reported_hypercredits': credits, 'cost_source': 'api_reported_usd_equivalent' if usd is not None else 'unreported',
            'cost_scope': 'Reported quota-debit valuation, not additional out-of-pocket billing',
            'reasoning_text_present': reasoning_present,
            'reasoning_verification': 'explicit_reported_zero' if count == 0 and not isinstance(count, bool) else 'requested_none_catalog_supported_no_token_telemetry',
            'model_output_failure': not failed and status != 'ok'}


def check_route(record):
    if record['status'] in ('transport_failure', 'http_failure', 'provider_error'):
        return
    assert record['model_returned'] == MODEL, 'Unexpected returned model'
    assert record['status'] != 'unexpected_reasoning' and not record['reasoning_text_present'], 'Reasoning-off contract violated'
    assert record['reported_cost_usd'] is not None and record['reported_hypercredits'] is not None, 'Successful response omitted quota accounting'


def validate_probe(out):
    probe = json.loads((out / 'compatibility_probe.json').read_text())
    dispatch = json.loads((out / 'probe_dispatch.json').read_text())
    assert probe['payload'] == dispatch['payload'] and d.digest(probe['payload']) == dispatch['request_payload_sha256']
    expected = payload({'instructions': '', 'context': '', 'question': '', 'options': [''] * 5})
    assert {k: v for k, v in probe['payload'].items() if k != 'messages'} == {k: v for k, v in expected.items() if k != 'messages'}
    record = {**probe['transport'], **parse(probe['transport'])}
    check_route(record)
    assert record['status'] == 'ok'
    return record


def probe_cost(out):
    return Decimal(str(validate_probe(out)['reported_cost_usd']))


def software():
    return {**base.software(), **{n: file_hash(repo_file(n, root=ROOT)) for n in ('bounded_reference_runner.py', 'hyper_reference.py', 'test_hyper_reference.py')}}


def freeze(out, plan):
    data = json.loads((out / 'model_metadata.json').read_text())['data']
    selected = [r for r in data if r['id'] == MODEL]
    assert len(selected) == 1
    model = selected[0]
    assert 'none' in [r['value'] for r in model['reasoning']['effort_levels']]
    assert Decimal(str(model['pricing']['input'])) == 2 and Decimal(str(model['pricing']['output'])) == 6
    validate_probe(out)
    d.save_bound(out / 'manifest.json', {'version': 'hyper-qwen38max-none-1342-v1', 'model': MODEL,
        'question_count': 1342, 'bank_sha256': BANK_HASH, 'request_plan': plan,
        'endpoint': 'https://' + SPEC['host'] + SPEC['path'],
        'settings': {k: v for k, v in payload({'instructions': '', 'context': '', 'question': '', 'options': [''] * 5}).items() if k != 'messages'},
        'prompt': 'Same1342 questions, option order and numeric-only suffix as Sol; no problem-specific prompt changes',
        'order_seed': base.SEED, 'concurrency': {'maximum': 1, 'policy': 'Sequential requests, respects existing conservative Hyper Charm account capacity'},
        'timing': 'Unmodified added_decisions.send, fresh HTTPS connect start through complete body; no queue/retry wait included',
        'comparison_limit': 'Same timing boundary, different provider and concurrency; not an OpenRouter route or synchronized infrastructure test',
        'retry': 'One recovery only for transport failure or HTTP408/429/5xx, never wrong/explanatory/truncated answers or HTTP200 errors',
        'primary': 'All1342 first attempts; recoveries supplementary. --limit can checkpoint a prefix without changing planned coverage.',
        'reasoning': 'reasoning_effort=none is catalog-supported and accepted; provider omits reasoning-token telemetry, so no verified-zero count is claimed',
        'identity_limit': 'Undated Hyper Charm alias; no independently attestable immutable weights or upstream backend supplied',
        'cost': 'API-reported USD-equivalent quota valuation and Hypercredits, separately from cash billing. No purchases/top-ups. Unknown not0.',
        'soft_usd_equivalent_guard': str(GUARD),
        'guard_limit': 'Local conservative byte-based reservations, not a vendor billing cap or quota-remaining guarantee',
        'development_policy': 'Same exploratory1342 bank;37 permanent author-development exclusions retained separately',
        'sources': ['https://hyper.charm.land/v1/models', 'https://help.aliyun.com/en/model-studio/qwen-api-via-openai-chat-completions']})
    d.save_bound(out / 'software.json', software())


def sealed_files(out):
    return ['manifest.json', 'software.json', 'model_metadata.json', 'compatibility_probe.json',
            'probe_dispatch.json', 'dispatches.jsonl', 'attempts.jsonl', 'results.jsonl'] + (['retry_waits.jsonl'] if (out / 'retry_waits.jsonl').exists() else [])


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


def execute(out, env, limit=1342):
    questions, plan = prepare()
    freeze(out, plan)
    attempts, results, done = controller.ledger_state(sys.modules[__name__], out, plan)
    if (out / 'completion.json').exists():
        validate(out, complete=True)
        print(json.dumps({'status': 'ALREADY_COMPLETE', 'paid_calls': 0}), flush=True)
        return
    key = credentials(env)
    assert key, 'Hyper Charm credential is not configured'
    for task in plan:
        if task['request_index'] in done or task['request_index'] > limit:
            continue
        body = d.canonical(payload(questions[task['item_id']]))
        assert d.digest(payload(questions[task['item_id']])) == task['request_payload_sha256']
        collected, fatal, started = [], None, time.perf_counter()
        for attempt in (1, 2):
            spent = probe_cost(out) + sum((Decimal(str(r['reported_cost_usd'])) if r['reported_cost_usd'] is not None else reserve(r) for r in attempts), Decimal(0))
            assert spent + reserve(task) <= GUARD, 'USD-equivalent soft usage guard reached'
            d.append(out / 'dispatches.jsonl', {**task, 'attempt': attempt, 'dispatch': d.timestamps()})
            response = sanitize(base.transport.send(body, key, SPEC))
            record = {**task, 'attempt': attempt, **response, **parse(response)}
            d.append(out / 'attempts.jsonl', record)
            attempts.append(record)
            collected.append(record)
            try:
                check_route(record)
                assert record['http_status'] not in (400, 401, 402, 403, 404, 413, 422), 'Client/access/quota rejection; no purchase or top-up'
            except Exception as exc:
                fatal = exc
                break
            if attempt == 1 and (record.get('transport_failure') or record['http_status'] in d.TRANSIENT):
                wait = d.retry_wait(record)
                d.append(out / 'retry_waits.jsonl', {'request_index': task['request_index'], 'seconds': wait})
                time.sleep(wait)
                continue
            break
        result = {**task, 'attempts': len(collected), 'first_status': collected[0]['status'], 'eventual_status': collected[-1]['status'],
                  'item_elapsed_ms': (time.perf_counter() - started) * 1000}
        d.append(out / 'results.jsonl', result)
        results.append(result)
        if fatal:
            raise fatal
        first, _ = chat.first_and_eventual(attempts)
        progress = {'model': MODEL, 'completed_cases': len(results), 'planned_cases': 1342, 'attempts': len(attempts),
                    'cost_usd_equivalent': chat.money(attempts), 'reported_hypercredits': sum(r['reported_hypercredits'] for r in attempts if r['reported_hypercredits'] is not None),
                    'first_statuses': dict(Counter(r['status'] for r in first.values())),
                    'first_latency': chat.quantiles([r['latency_ms'] for r in first.values()]), 'time': d.timestamps()}
        d.append(out / 'progress.jsonl', progress)
        if len(results) % 20 == 0 or len(results) in (limit, 1342):
            print(json.dumps(progress), flush=True)
    if len(results) < 1342:
        print(json.dumps({'status': 'CHECKPOINT_PARTIAL', 'settled_questions': len(results), 'planned_questions': 1342}), flush=True)
        return
    d.save_bound(out / 'completion.json', {'status': 'COMPLETE_1342', 'completed': d.timestamps(),
        'files_sha256': {n: file_hash(out / n) for n in sealed_files(out)}})
    validate(out, complete=True)
    print(json.dumps({'status': 'COMPLETE_1342', 'runtime_evidence': str(out)}), flush=True)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--execute', action='store_true')
    p.add_argument('--validate', action='store_true')
    p.add_argument('--env', type=Path)
    p.add_argument('--limit', type=int, default=1342)
    args = p.parse_args()
    assert 1 <= args.limit <= 1342 and not (args.execute and args.validate)
    if args.execute:
        execute(OUT, args.env, args.limit)
    elif args.validate:
        a, r = validate(OUT, complete=True)
        print(json.dumps({'validation': 'PASS', 'questions': len(r), 'attempts': len(a), 'paid_calls': 0}))
    else:
        print(json.dumps({'mode': 'DRY_RUN', 'model': MODEL, 'questions': len(prepare()[1]), 'paid_calls': 0}))


if __name__ == '__main__':
    main()
