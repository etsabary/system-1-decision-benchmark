"""Answer-blind GPT-6 Sol, reasoning-none reference on the frozen 1,342 bank.

Dry-run by default. Never loads a key of correct answers or changes a question.
Uses the existing unmodified HTTPS timer and strict numeric-answer contract.
Runtime evidence is written only below the ignored runs/ directory.
"""
from __future__ import annotations
from repo_layout import logical_relative, repo_file
from repo_layout import source_file

import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from decimal import Decimal
from hashlib import sha256
import json
from pathlib import Path
import random
import threading
import time

import added_decisions as transport
import decision_refresh as d
import llm_field_2026_10_18 as hygiene
import text_models as chat

ROOT = Path(__file__).resolve().parents[1]
BANK = repo_file('consolidated_2026-10-19/questions_1342.jsonl', root=ROOT)
BANK_HASH = '2db8cf8353f12b609d4df5330d94f53390c9c2919677dc793df4bb2d3cff7076'
OUT = repo_file('runs/gpt6_sol_none_1342_2026-10-19', root=ROOT)
MODEL = 'openai/gpt-6-sol'
SNAPSHOT = 'openai/gpt-6-sol-20260922'
SPEC = {'host': 'openrouter.ai', 'path': '/api/v1/chat/completions'}
GUARD = Decimal('3.00')
SEED = 2026101906


def file_hash(path):
    return sha256(source_file(path).read_bytes()).hexdigest()


def render(q):
    return (q['instructions'] + '\n\n' + q['context'] + '\n\n' + q['question'] +
            '\n\n' + '\n'.join(f'{i}. {o}' for i, o in enumerate(q['options'], 1)))


def payload(q):
    return {'model': MODEL, 'messages': [{'role': 'user', 'content': render(q) + chat.SUFFIX}],
            'max_tokens': 16, 'stream': False, 'usage': {'include': True},
            'reasoning': {'enabled': False, 'effort': 'none'}, 'service_tier': 'default',
            'provider': {'only': ['openai'], 'ignore': ['openai/flex', 'openai/fast'],
                         'allow_fallbacks': False, 'require_parameters': True}}


def prepare():
    assert file_hash(BANK) == BANK_HASH, 'Frozen 1342-question bank changed'
    rows = d.rows(BANK)
    questions = {q['id']: q for q in rows}
    assert len(rows) == len(questions) == 1342
    assert len({q['family_id'] for q in rows}) == 31
    allowed = {'id', 'family_id', 'family', 'instructions', 'context', 'question',
               'options', 'native_input', 'native_input_sha256'}
    for q in rows:
        assert set(q) == allowed and len(q['options']) == 5
        native = {'state': q['context'], 'questions': {'decision': {'type': 'choice',
                  'instructions': q['instructions'] + '\n\n' + q['question'],
                  'criteria': {str(i): v for i, v in enumerate(q['options'], 1)}}}}
        expanded = {'state': q['question'], 'questions': {'decision': {'type': 'choice',
                    'instructions': q['instructions'],
                    'criteria': {str(i): v for i, v in enumerate(q['options'], 1)}}}}
        assert q['native_input'] == native or (q['context'] == '' and q['native_input'] == expanded)
        assert d.digest(q['native_input']) == q['native_input_sha256']
    # Original prompts remain byte-for-byte identical, including both corrections.
    old = d.read_csv(repo_file('corrected_2026-10-18/questions_1136.csv', root=ROOT))
    assert len(old) == 1136
    for q in old:
        assert render(questions[q['item_id']]) == q['prompt_text']
    order = list(questions)
    random.Random(SEED).shuffle(order)
    plan = []
    for index, item_id in enumerate(order, 1):
        q = questions[item_id]
        body = payload(q)
        plan.append({'request_index': index, 'wave': (index - 1) // 2 + 1,
                     'item_id': item_id, 'family_id': q['family_id'],
                     'model_id': 'gpt6_sol_none', 'model_requested': MODEL,
                     'native_input_sha256': q['native_input_sha256'],
                     'message_sha256': d.digest(body['messages']),
                     'request_payload_sha256': d.digest(body),
                     'request_body_bytes': len(d.canonical(body))})
    return questions, plan


def parse(response):
    value = chat.parse(response)
    raw = response.get('raw_response') or {}
    choices = raw.get('choices')
    answer = choices[0] if isinstance(choices, list) and len(choices) == 1 and isinstance(choices[0], dict) else {}
    message = answer.get('message') or {}
    reasoning_text = bool(message.get('reasoning') or message.get('reasoning_content') or message.get('reasoning_details'))
    count = value['reported_reasoning_tokens']
    no_reasoning = isinstance(count, int) and not isinstance(count, bool) and count == 0 and not reasoning_text
    failed = bool(response.get('transport_failure') or response.get('error') or
                  response.get('http_status') != 200 or raw.get('error'))
    status = ('transport_failure' if response.get('transport_failure') else
              'http_failure' if response.get('http_status') != 200 else
              'provider_error' if failed else 'unexpected_reasoning' if not no_reasoning else value['status'])
    return {**value, 'status': status, 'choice': value['choice'] if status == 'ok' else None,
            'reasoning_text_present': reasoning_text,
            'accounted_cost_usd': value['reported_cost_usd'],
            'cost_source': 'api_reported' if value['reported_cost_usd'] is not None else 'unreported',
            'model_output_failure': not failed and status != 'ok'}


def check_route(record):
    if record['status'] in ('transport_failure', 'http_failure', 'provider_error'):
        return
    assert record['provider'] == 'OpenAI', 'Unexpected provider; no silent fallback'
    assert record['model_returned'] in (MODEL, SNAPSHOT), 'Unexpected model identity'
    assert record['reported_cost_usd'] is not None, 'Successful response omitted API-reported cost'
    assert record['reported_reasoning_tokens'] == 0 and not isinstance(record['reported_reasoning_tokens'], bool)
    assert not record['reasoning_text_present'] and record['status'] != 'unexpected_reasoning', 'Reasoning-none contract violated or unverified'


def software():
    return {name: file_hash(repo_file(name, root=ROOT)) for name in (
        'frontier_reference.py', 'test_frontier_reference.py', 'added_decisions.py',
        'decision_refresh.py', 'llm_field_2026_10_18.py', 'text_models.py', 'run_benchmark.py')}


def validate_probe(out):
    probe = json.loads((out / 'compatibility_probe.json').read_text())
    dispatch = json.loads((out / 'probe_dispatch.json').read_text())
    body = probe['payload']
    assert body == dispatch['payload'] and d.digest(body) == dispatch['request_payload_sha256']
    expected = payload({'instructions': '', 'context': '', 'question': '', 'options': [''] * 5})
    assert {k: v for k, v in body.items() if k != 'messages'} == {k: v for k, v in expected.items() if k != 'messages'}
    record = {**probe['transport'], **parse(probe['transport'])}
    check_route(record)
    assert record['status'] == 'ok' and record['choice'] == '3', 'Compatibility probe failed'
    return record


def freeze(out, plan):
    out.mkdir(parents=True, exist_ok=True)
    metadata = json.loads((out / 'model_metadata.json').read_text())['data']
    selected = [e for e in metadata['endpoints'] if e['tag'] == 'openai' and not e.get('service_tier') and e['status'] == 0]
    assert len(selected) == 1 and selected[0]['name'] == 'OpenAI | ' + SNAPSHOT
    assert Decimal(selected[0]['pricing']['prompt']) == Decimal('.000002')
    assert Decimal(selected[0]['pricing']['completion']) == Decimal('.00001')
    assert {'max_tokens', 'reasoning'} <= set(selected[0]['supported_parameters'])
    validate_probe(out)
    d.save_bound(out / 'manifest.json', {
        'version': 'frontier-no-reasoning-1342-v1', 'model': MODEL, 'catalog_snapshot': SNAPSHOT,
        'identity_limit': 'Dated endpoint metadata; returned alias alone is not immutable-weight attestation',
        'question_count': 1342, 'bank': str(logical_relative(BANK, root=ROOT)), 'bank_sha256': BANK_HASH,
        'endpoint': 'https://' + SPEC['host'] + SPEC['path'],
        'settings': {k: v for k, v in payload({'instructions': '', 'context': '', 'question': '', 'options': [''] * 5}).items() if k != 'messages'},
        'prompt': 'Exact original instructions, state, question and five choices, plus the established numeric-ID-only suffix; original corrected1136 prompt_text verified byte-for-byte',
        'order': {'kind': 'fixed shuffle of public1342 order', 'seed': SEED},
        'concurrency': {'maximum': 2, 'questions_per_wave': 2, 'barrier': 'Both cases settle before the next wave'},
        'timing': 'Unmodified added_decisions.send: fresh HTTPS connect start through full response body, monotonic timer, excludes preparation/queue/retry wait',
        'connect_timeout_seconds': 10, 'total_response_timeout_seconds': 90,
        'retry': 'At most one recovery for transport failure or HTTP408/429/5xx; no retries for explanations, truncation, refusals, HTTP200 error envelopes or wrong valid answers',
        'primary': 'Every first attempt; complete1342 denominator includes unusable responses',
        'screen': 'Full-bank frontier reference explicitly requested; older cheap-model screening cutoffs do not remove or stop this reference',
        'cost': 'API-reported charges, including recovery attempts; compatibility probe separately reported; unknown never zero',
        'soft_cost_guard_usd': str(GUARD),
        'guard_limit': 'Local soft guard, not a vendor billing cap. Unknown/in-flight calls conservatively reserve byte-based input plus16 output tokens.',
        'no_reasoning': 'reasoning.enabled=false and effort=none; every successful response must report exactly0 reasoning tokens and no reasoning content',
        'sources': ['https://developers.openai.com/api/docs/models/gpt-6-sol',
                    'https://developers.openai.com/api/docs/pricing'],
        'development_policy': 'Same1342 exploratory development bank, not a pristine held-out release; retain37 permanent author-development exclusions in the separate diagnostic',
        'request_plan': plan})
    d.save_bound(out / 'software.json', software())


def ledger_state(out, plan):
    attempts, results, dispatches = (d.rows(out / n) for n in ('attempts.jsonl', 'results.jsonl', 'dispatches.jsonl'))
    done = d.reconcile(dispatches, attempts, results, plan)
    indexed = {p['request_index']: p for p in plan}
    for row in attempts + results + dispatches:
        assert all(row[k] == v for k, v in indexed[row['request_index']].items()), 'Ledger differs from frozen plan'
    first, last = chat.first_and_eventual(attempts)
    for row in attempts:
        assert all(row[k] == v for k, v in parse(row).items()), 'Parser evidence changed'
        check_route(row)
    for row in results:
        index = row['request_index']
        assert row['attempts'] == last[index]['attempt']
        assert row['first_status'] == first[index]['status'] and row['eventual_status'] == last[index]['status']
    return attempts, results, done


def validate(out, complete=False):
    _, plan = prepare()
    manifest = json.loads((out / 'manifest.json').read_text())
    assert manifest['request_plan'] == plan and manifest['bank_sha256'] == BANK_HASH
    assert json.loads((out / 'software.json').read_text()) == software(), 'Frozen execution software changed'
    validate_probe(out)
    attempts, results, done = ledger_state(out, plan)
    if complete:
        receipt = json.loads((out / 'completion.json').read_text())
        assert receipt['status'] == 'COMPLETE_1342' and done == set(range(1, 1343))
        for name, digest in receipt['files_sha256'].items():
            assert file_hash(out / name) == digest, 'Sealed evidence changed: ' + name
    return attempts, results


def reserve(task):
    return Decimal(task['request_body_bytes'] + 256) * Decimal('.000002') + Decimal('16') * Decimal('.00001')


def execute(out, waves=0):
    questions, plan = prepare()
    freeze(out, plan)
    attempts, results, done = ledger_state(out, plan)
    if (out / 'completion.json').exists():
        validate(out, complete=True)
        print(json.dumps({'status': 'ALREADY_COMPLETE', 'paid_calls': 0}), flush=True)
        return
    key = d.api_key(ROOT.parent / 'jev/.env')
    assert key, 'OPENROUTER_API_KEY not configured'
    probe_cost = Decimal(str(validate_probe(out)['reported_cost_usd']))
    lock, halt = threading.Lock(), threading.Event()
    in_flight = {}

    def one(task):
        body = d.canonical(payload(questions[task['item_id']]))
        assert sha256(body).hexdigest() == task['request_payload_sha256']
        collected, fatal, began = [], None, time.perf_counter()
        try:
            for attempt in (1, 2):
                signature = (task['request_index'], attempt)
                with lock:
                    if halt.is_set():
                        break
                    charged = probe_cost + sum((Decimal(str(r['reported_cost_usd'])) if r['reported_cost_usd'] is not None else reserve(r) for r in attempts), Decimal(0))
                    assert charged + sum(in_flight.values(), Decimal(0)) + reserve(task) <= GUARD, 'Soft cost guard reached'
                    d.append(out / 'dispatches.jsonl', {**task, 'attempt': attempt, 'dispatch': d.timestamps()})
                    in_flight[signature] = reserve(task)
                response = hygiene.sanitize_response(transport.send(body, key, SPEC))
                record = {**task, 'attempt': attempt, **response, **parse(response)}
                with lock:
                    d.append(out / 'attempts.jsonl', record)
                    attempts.append(record)
                    in_flight.pop(signature)
                collected.append(record)
                try:
                    check_route(record)
                    assert record['http_status'] not in (400, 401, 402, 403, 404, 413, 422), 'Client rejection; stop for inspection'
                except Exception as exc:
                    fatal = exc
                    halt.set()
                    break
                if attempt == 1 and (record.get('transport_failure') or record['http_status'] in d.TRANSIENT):
                    wait = d.retry_wait(record)
                    with lock:
                        d.append(out / 'retry_waits.jsonl', {'request_index': task['request_index'], 'seconds': wait})
                    if halt.wait(wait):
                        break
                    continue
                break
            if collected:
                result = {**task, 'attempts': len(collected), 'first_status': collected[0]['status'],
                          'eventual_status': collected[-1]['status'],
                          'item_elapsed_ms': (time.perf_counter() - began) * 1000}
                with lock:
                    d.append(out / 'results.jsonl', result)
                    results.append(result)
            if fatal:
                raise fatal
        except Exception:
            halt.set()
            raise

    remaining = [p for p in plan if p['request_index'] not in done]
    with ThreadPoolExecutor(max_workers=2) as pool:
        for count, wave in enumerate(sorted({p['wave'] for p in remaining}), 1):
            errors = []
            for future in as_completed([pool.submit(one, p) for p in remaining if p['wave'] == wave]):
                try:
                    future.result()
                except Exception as exc:
                    errors.append(type(exc).__name__ + ': ' + str(exc))
            first, _ = chat.first_and_eventual(attempts)
            progress = {'completed_cases': len(results), 'planned_cases': 1342, 'attempts': len(attempts),
                        'cost_all_attempts': chat.money(attempts),
                        'first_statuses': dict(Counter(r['status'] for r in first.values())),
                        'first_latency': chat.quantiles([r['latency_ms'] for r in first.values()]),
                        'time': d.timestamps()}
            d.append(out / 'progress.jsonl', progress)
            if wave % 10 == 0 or errors or len(results) == 1342:
                print(json.dumps(progress), flush=True)
            if errors:
                d.save_bound(out / f'halt_{len(results)}.json', {'errors': errors, **progress})
                raise AssertionError('; '.join(errors))
            if waves and count >= waves and len(results) < 1342:
                print(json.dumps({'status': 'PAUSED_WAVE_LIMIT', **progress}), flush=True)
                return
    assert len(results) == 1342
    names = ['manifest.json', 'software.json', 'model_metadata.json', 'compatibility_probe.json',
             'probe_dispatch.json', 'dispatches.jsonl', 'attempts.jsonl', 'results.jsonl']
    if (out / 'retry_waits.jsonl').exists():
        names.append('retry_waits.jsonl')
    d.save_bound(out / 'completion.json', {'status': 'COMPLETE_1342', 'completed': d.timestamps(),
                                          'files_sha256': {n: file_hash(out / n) for n in names}})
    validate(out, complete=True)
    print(json.dumps({'status': 'COMPLETE_1342', 'runtime_evidence': str(out)}), flush=True)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out', type=Path, default=OUT)
    action = p.add_mutually_exclusive_group()
    action.add_argument('--execute', action='store_true')
    action.add_argument('--validate', action='store_true')
    p.add_argument('--waves', type=int, default=0)
    args = p.parse_args()
    assert args.waves >= 0
    if args.execute:
        execute(args.out, args.waves)
    elif args.validate:
        attempts, results = validate(args.out, complete=True)
        print(json.dumps({'validation': 'PASS', 'questions': len(results), 'attempts': len(attempts), 'paid_calls': 0}))
    else:
        _, plan = prepare()
        print(json.dumps({'mode': 'DRY_RUN', 'model': MODEL, 'questions': len(plan),
                          'reasoning': 'none', 'paid_calls': 0}))


if __name__ == '__main__':
    main()
