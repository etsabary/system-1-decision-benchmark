"""Shared journaled execution for additional no-reasoning references.

The earlier Sol runner stays frozen, unmodified. Adapters supply the protocol,
model identity, input plan and parser; this controller never reads correct keys.
"""
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from decimal import Decimal
from hashlib import sha256
import json
from pathlib import Path
import threading
import time

import added_decisions as transport
import decision_refresh as d
import text_models as chat


def ledger_state(adapter, out, plan):
    attempts, results, dispatches = (d.rows(out / n) for n in ('attempts.jsonl', 'results.jsonl', 'dispatches.jsonl'))
    done = d.reconcile(dispatches, attempts, results, plan)
    indexed = {p['request_index']: p for p in plan}
    for row in attempts + results + dispatches:
        assert all(row[k] == v for k, v in indexed[row['request_index']].items()), 'Ledger differs from frozen plan'
    first, last = chat.first_and_eventual(attempts)
    for row in attempts:
        assert all(row[k] == v for k, v in adapter.parse(row).items()), 'Parser evidence changed'
        adapter.check_route(row)
    for row in results:
        index = row['request_index']
        assert row['attempts'] == last[index]['attempt']
        assert row['first_status'] == first[index]['status'] and row['eventual_status'] == last[index]['status']
    return attempts, results, done


def execute(adapter, out, waves=0):
    questions, plan = adapter.prepare()
    adapter.freeze(out, plan)
    attempts, results, done = ledger_state(adapter, out, plan)
    if (out / 'completion.json').exists():
        adapter.validate(out, complete=True)
        print(json.dumps({'status': 'ALREADY_COMPLETE', 'paid_calls': 0}), flush=True)
        return
    key = d.api_key(adapter.ROOT.parent / 'jev/.env')
    assert key, 'OPENROUTER_API_KEY not configured'
    probe_cost = Decimal(str(adapter.probe_cost(out)))
    lock, halt, in_flight = threading.Lock(), threading.Event(), {}

    def one(task):
        body = d.canonical(adapter.payload(questions[task['item_id']]))
        assert sha256(body).hexdigest() == task['request_payload_sha256']
        collected, fatal, began = [], None, time.perf_counter()
        try:
            for attempt in (1, 2):
                signature = (task['request_index'], attempt)
                with lock:
                    if halt.is_set():
                        break
                    charged = probe_cost + sum((Decimal(str(r['reported_cost_usd'])) if r['reported_cost_usd'] is not None else adapter.reserve(r) for r in attempts), Decimal(0))
                    assert charged + sum(in_flight.values(), Decimal(0)) + adapter.reserve(task) <= adapter.GUARD, 'Soft cost guard reached'
                    d.append(out / 'dispatches.jsonl', {**task, 'attempt': attempt, 'dispatch': d.timestamps()})
                    in_flight[signature] = adapter.reserve(task)
                response = adapter.sanitize(transport.send(body, key, adapter.SPEC))
                record = {**task, 'attempt': attempt, **response, **adapter.parse(response)}
                with lock:
                    d.append(out / 'attempts.jsonl', record)
                    attempts.append(record)
                    in_flight.pop(signature)
                collected.append(record)
                try:
                    adapter.check_route(record)
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
                          'eventual_status': collected[-1]['status'], 'item_elapsed_ms': (time.perf_counter() - began) * 1000}
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
            progress = {'model': adapter.MODEL, 'completed_cases': len(results), 'planned_cases': 1342,
                        'attempts': len(attempts), 'cost_all_attempts': chat.money(attempts),
                        'first_statuses': dict(Counter(r['status'] for r in first.values())),
                        'first_latency': chat.quantiles([r['latency_ms'] for r in first.values()]), 'time': d.timestamps()}
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
    names = adapter.sealed_files(out)
    d.save_bound(out / 'completion.json', {'status': 'COMPLETE_1342', 'completed': d.timestamps(),
                                          'files_sha256': {n: adapter.file_hash(out / n) for n in names}})
    adapter.validate(out, complete=True)
    print(json.dumps({'status': 'COMPLETE_1342', 'runtime_evidence': str(out)}), flush=True)
