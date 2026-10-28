"""Answer-blind GLiDE native text/image runs. No calls without --probe/--execute.

One unchanged case per request. Frozen bank/order/assets; native choices only.
Scoring is deliberately separate. Runtime ledgers below ignored runs/ are private.
"""
import argparse
import base64
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from decimal import Decimal
import fcntl
from hashlib import sha256
import http.client
import json
import math
import os
from pathlib import Path
import ssl
import statistics
import sys
import threading
import time
import urllib.request

from dotenv import dotenv_values
import decision_refresh as d
import frontier_reference as text_bank
import text_models as stats

ROOT = Path(__file__).resolve().parents[1]
VISUAL = ROOT.parent / 'visual-decision-benchmark'
OUT = ROOT / 'runs/fastino_glide_2026-10-23'
ENV = ROOT.parent.parent / 'the village 14947/.env'
MODEL = 'fastino/GLiDE'
HOST = 'api.fastino.ai'
RATE = Decimal('0.04') / 1000000
GUARD = Decimal('0.50')
SOURCES = ['https://docs.fastino.ai/inference/systemone',
           'https://docs.fastino.ai/concepts/models',
           'https://fastino.ai/blog/training-glide-sota-decision-model']


def file_hash(path):
    return sha256(Path(path).read_bytes()).hexdigest()


def secret():
    value = os.environ.get('FASTINO_AI_API_KEY') or dotenv_values(ENV, interpolate=False).get('FASTINO_AI_API_KEY')
    assert value and str(value).strip(), 'FASTINO_AI_API_KEY missing'
    return str(value).strip()


@contextmanager
def visual_imports():
    """Sibling tools share generic module names; never leak their import path."""
    source = VISUAL/'scripts' if (VISUAL/'scripts/image_models_2026_10_20.py').exists() else VISUAL
    names = ('repo_layout','benchmark','image_models_2026_10_20','analyze_native_images','score')
    previous_path = list(sys.path)
    previous = {name:sys.modules.get(name) for name in names}
    try:
        for name in names:sys.modules.pop(name,None)
        sys.path.insert(0,str(source))
        yield
    finally:
        for name in names:
            sys.modules.pop(name,None)
            if previous[name] is not None:sys.modules[name]=previous[name]
        sys.path[:]=previous_path


_VISUAL_BANK = None


def image_bank():
    global _VISUAL_BANK
    if _VISUAL_BANK is None:
        with visual_imports():
            import image_models_2026_10_20
            _VISUAL_BANK = image_models_2026_10_20
    return _VISUAL_BANK


def image_payload(q, assets):
    parts = []
    assert 1 <= len(q['asset_ids']) <= 4
    for aid in q['asset_ids']:
        asset = assets[aid]
        raw = Path(asset['path']).read_bytes()
        assert sha256(raw).hexdigest() == asset['sha256'] and len(raw) <= 3932160
        assert asset['mime'] in ('image/png', 'image/jpeg', 'image/webp', 'image/gif')
        parts.append(dict(type='image_url', image_url=dict(
            url='data:' + asset['mime'] + ';base64,' + base64.b64encode(raw).decode('ascii'))))
    return dict(model=MODEL, store=False, state=parts, questions=dict(decision=dict(
        type='choice', instructions=q['question'] + '\n\nRules: ' + q['rules'],
        criteria={o['id']: o['text'] for o in q['options']})))


def payload(q, kind, assets):
    if kind == 'image':
        return image_payload(q, assets)
    return dict(model=MODEL, store=False, **q['native_input'])


def send(body):
    key = secret()
    conn = http.client.HTTPSConnection(HOST, timeout=10,
        context=ssl.create_default_context(cafile='/etc/ssl/cert.pem'))
    result = dict(http_status=0, raw_response={}, error='', response_headers={},
                  headers_latency_ms=None, transport_failure=False, started=d.timestamps())
    began = time.perf_counter()
    try:
        conn.connect()
        sock = conn.sock
        sock.settimeout(max(.001, 90 - (time.perf_counter() - began)))
        conn.request('POST', '/v1/systemone', body=body, headers={
            'X-API-Key': key, 'Content-Type': 'application/json', 'Accept': 'application/json'})
        sock.settimeout(max(.001, 90 - (time.perf_counter() - began)))
        response = conn.getresponse()
        result.update(http_status=response.status, headers_latency_ms=(time.perf_counter()-began)*1000,
            response_headers={k.lower(): v for k, v in response.getheaders() if k.lower() in
                ('date', 'retry-after', 'x-request-id', 'content-type', 'x-fastino-data-retention')})
        chunks, size = [], 0
        while True:
            left = 90 - (time.perf_counter() - began)
            if left <= 0:
                raise TimeoutError('90-second full-response deadline')
            sock.settimeout(left)
            chunk = response.read1(65536)
            if not chunk:
                break
            size += len(chunk)
            assert size <= 4*1024**2, 'Oversized native decision response'
            chunks.append(chunk)
        raw = b''.join(chunks).decode().replace(key, '[REDACTED_API_KEY]')
        try:
            result['raw_response'] = json.loads(raw)
        except ValueError:
            result['error'] = 'Non-JSON response: ' + raw[:300]
        if response.status != 200:
            result['error'] = 'HTTP ' + str(response.status)
    except Exception as exc:
        result.update(error=(type(exc).__name__+': '+str(exc)).replace(key, '[REDACTED_API_KEY]'),
                      transport_failure=isinstance(exc, (OSError, http.client.HTTPException)))
    finally:
        result.update(latency_ms=(time.perf_counter()-began)*1000, completed=d.timestamps())
        conn.close()
    return result


def number(v):
    return not isinstance(v, bool) and isinstance(v, (int, float)) and math.isfinite(v) and v >= 0


def parse(response, choices):
    raw = response.get('raw_response')
    raw = raw if isinstance(raw, dict) else {}
    answers = raw.get('answers')
    answer = answers.get('decision') if isinstance(answers, dict) else None
    answer = answer if isinstance(answer, dict) else {}
    usage = raw.get('usage')
    usage = usage if isinstance(usage, dict) else {}
    choice = answer.get('choice')
    ok = response['http_status'] == 200 and not response.get('error') and not raw.get('error')
    status = 'ok' if ok and isinstance(choice, str) and choice in choices else 'invalid_answer'
    if response['http_status'] != 200:
        status = 'http_failure'
    if response.get('transport_failure'):
        status = 'transport_failure'
    # Admission on Oct23 returned glide_v2; the authenticated catalog calls it v2.2.
    # Pin that observed identity, not the older "glide" identity in the docs.
    if status == 'ok' and raw.get('model') != 'glide_v2':
        status = 'identity_mismatch'
    reasoning = any(raw.get(k) or answer.get(k) for k in ('reasoning', 'thinking', 'reasoning_content', 'explanation'))
    if status == 'ok' and reasoning:
        status = 'unexpected_reasoning'
    p = answer.get('probabilities')
    valid = isinstance(p, dict) and set(p) == set(choices)
    if valid:
        valid = all(number(v) and v <= 1 for v in p.values()) and abs(math.fsum(p.values())-1) <= 1e-6
    receipt = usage.get('cost')
    receipt = receipt if number(receipt) else None
    tokens = usage.get('input_tokens')
    priced = isinstance(tokens, int) and not isinstance(tokens, bool) and tokens >= 0
    cost = receipt if receipt is not None else float(Decimal(tokens)*RATE) if priced else None
    confidence = answer.get('confidence')
    return dict(status=status, choice=choice if status == 'ok' else None,
        model_returned=raw.get('model'), returned_version=raw.get('version'), provider=raw.get('provider'),
        usage=usage, probabilities=p if valid else None, probabilities_valid=bool(valid),
        confidence=confidence if number(confidence) and confidence <= 1 else None,
        reported_cost_usd=receipt, accounted_cost_usd=cost,
        cost_source='api_reported' if receipt is not None else 'usage_times_published_tariff' if priced else 'unreported',
        reasoning_text_present=bool(reasoning), reported_output_tokens=usage.get('output_tokens'))


def transient(row):
    return row['transport_failure'] or row['http_status'] in d.TRANSIENT or row['http_status'] == 425


def speed_stop(rows):
    first = [r['latency_ms'] for r in rows if r['attempt'] == 1]
    return len(first) >= 20 and statistics.median(first) > 2000


@contextmanager
def lock(out):
    out.mkdir(parents=True, exist_ok=True)
    with (out / '.execution.lock').open('a') as handle:
        fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        try:
            yield
        finally:
            fcntl.flock(handle, fcntl.LOCK_UN)


def catalog(out):
    target = out / 'model_metadata.json'
    if not target.exists():
        url = 'https://' + HOST + '/v1/base-models?supports_inference=true'
        req = urllib.request.Request(url, headers={'X-API-Key': secret()})
        with urllib.request.urlopen(req, timeout=25,
                context=ssl.create_default_context(cafile='/etc/ssl/cert.pem')) as response:
            data = json.load(response)
        matches = [m for m in data['models'] if m['id'] == MODEL]
        assert len(matches) == 1
        selected = matches[0]
        assert Decimal(str(selected['input_price_per_million'])) == Decimal('.04')
        assert Decimal(str(selected['output_price_per_million'])) == 0
        d.save_bound(target, dict(retrieved=d.timestamps(), url=url, model=selected,
            sources=SOURCES, identity_limit='Hosted GLiDE alias; catalog version is recorded, not an immutable-weight attestation',
            image_admission='Docs support images; catalog capability may lag. Explicit image probes required before the image bank.'))
    return json.loads(target.read_text())


def probe(kind, out):
    catalog(out)
    assets = {}
    if kind == 'text':
        cases = [dict(id='PROBE_TEXT', native_input=dict(state='The switch is ON.', questions=dict(decision=dict(
            type='choice', instructions='Select the option matching the switch state exactly.',
            criteria=dict(zip('12345', ('OFF','UNKNOWN','ON','BROKEN','UNPLUGGED')))))))]
    else:
        image = image_bank()
        _, assets, _ = image.inputs()
        cases = image.probes()
    for index, q in enumerate(cases, 1):
        body = payload(q, kind, assets)
        choices = set(body['questions']['decision']['criteria'])
        signature = d.digest(body)
        for attempt in (1, 2):
            target = out / f'probe_{index}_attempt_{attempt}.json'
            dispatch = out / f'probe_{index}_dispatch_{attempt}.json'
            if not target.exists():
                assert not dispatch.exists(), 'Unresolved probe dispatch; do not replay'
                d.save_bound(dispatch, dict(payload_sha256=signature, started=d.timestamps()))
                response = send(d.canonical(body))
                d.save_bound(target, dict(payload_sha256=signature, response=response,
                    parsed=parse(response, choices)))
            saved = json.loads(target.read_text())
            assert saved['payload_sha256'] == signature
            row = parse(saved['response'], choices)
            if row != saved['parsed']:
                # Retain the original unscored rejection, explicitly review it,
                # and reparse the same receipt. Never resend a successful probe.
                assert saved['parsed']['status'] == 'identity_mismatch' and row['status'] == 'ok'
                assert saved['response']['raw_response']['model'] == 'glide_v2'
                d.save_bound(out / f'probe_{index}_parser_review_{attempt}.json', dict(
                    receipt_sha256=file_hash(target), original=saved['parsed'], reviewed=row,
                    reason='Authenticated catalog describes one-pass GLiDE v2.2; successful native response identifies glide_v2. Pin this exact returned identity before scored calls.'))
            print(json.dumps(dict(bank=kind, probe=index, attempt=attempt, **row,
                http_status=saved['response']['http_status'], latency_ms=saved['response']['latency_ms'],
                error=saved['response']['error'], response_headers=saved['response']['response_headers'])), flush=True)
            if row['status'] == 'ok':
                if kind == 'text':
                    assert row['choice'] == '3', 'Native choice compatibility control failed'
                break
            if attempt == 1 and transient(saved['response']):
                time.sleep(60 if saved['response']['http_status'] == 425 else max(1, d.retry_wait(saved['response'])))
                continue
            raise RuntimeError('Native '+kind+' compatibility probe failed; no benchmark calls dispatched')


def prepare(kind, out):
    assets = {}
    if kind == 'text':
        questions, old = text_bank.prepare()
        order = [p['item_id'] for p in old]
        bank_hash = text_bank.BANK_HASH
    else:
        image = image_bank()
        questions, assets, order = image.inputs()
        bank_hash = image.QUESTION_HASH
    plan = []
    for index, item in enumerate(order, 1):
        q = questions[item]
        body = payload(q, kind, assets)
        row = dict(request_index=index, wave=(index-1)//(2 if kind == 'text' else 1)+1,
            item_id=item, family_id=q['family_id'], model_id='fastino_glide', model_requested=MODEL,
            request_payload_sha256=d.digest(body), request_body_bytes=len(d.canonical(body)))
        if kind == 'text':
            row['native_input_sha256'] = q['native_input_sha256']
        else:
            row.update(candidate_id=item, image_sha256=[assets[a]['sha256'] for a in q['asset_ids']],
                       image_count=len(q['asset_ids']))
        plan.append(row)
    out.mkdir(parents=True, exist_ok=True)
    d.save_bound(out/'manifest.json', dict(version='fastino-native-20261023-v1', bank=kind,
        model=MODEL, endpoint='https://'+HOST+'/v1/systemone', bank_sha256=bank_hash,
        planned_cases=len(plan), request_plan=plan, sources=SOURCES,
        input='Frozen native questions/options/order and exact original image bytes; model/store only added',
        timing='Fresh HTTPS connect through complete body; encoding, queue, pacing and retry waits excluded; 90s full-body deadline',
        concurrency='Two requests per barrier wave' if kind == 'text' else 'One serial request',
        speed_screen='Stop when cumulative first-attempt median >2000ms at/after20, at wave boundary',
        retry='One transport/408/425/429/5xx recovery maximum. No answer-dependent retries or provider fallback',
        scoring='First attempts, including errors and invalid outputs; probes separate and unranked',
        privacy='store:false on all requests; no credentials or answer key in ledgers',
        cost='API receipts where present, otherwise reported input_tokens * $0.04/M. Missing usage/cost remains unknown. Output tariff $0.',
        soft_spend_guard_usd=str(GUARD)))
    software = {str(p.relative_to(ROOT)): file_hash(p) for p in (
        Path(__file__), ROOT/'scripts/test_fastino_glide_2026_10_23.py', ROOT/'scripts/decision_refresh.py', ROOT/'scripts/frontier_reference.py',
        ROOT/'scripts/text_models.py')}
    if kind == 'image':
        software.update({'visual/'+n: file_hash(VISUAL/n) for n in ('image_models_2026_10_20.py', 'benchmark.py')})
    d.save_bound(out/'software.json', software)
    return questions, assets, plan


def validate(kind, out):
    qs, assets, plan = prepare(kind, out)
    attempts, results, dispatches = (d.rows(out/n) for n in ('attempts.jsonl','results.jsonl','dispatches.jsonl'))
    done = d.reconcile(dispatches, attempts, results, plan)
    indexed = {p['request_index']: p for p in plan}
    for row in attempts + results + dispatches:
        assert all(row.get(k) == v for k, v in indexed[row['request_index']].items()), 'Request plan drift'
    for row in attempts:
        choices = set(payload(qs[row['item_id']], kind, assets)['questions']['decision']['criteria'])
        assert all(row.get(k) == v for k, v in parse(row, choices).items()), 'Parser drift'
    first, last = stats.first_and_eventual(attempts)
    for row in results:
        index = row['request_index']
        assert row['attempts'] == last[index]['attempt']
        assert row['first_status'] == first[index]['status'] and row['eventual_status'] == last[index]['status']
    if (out/'completion.json').exists():
        assert len(done) == len(plan)
        seal = json.loads((out/'completion.json').read_text())
        assert all(file_hash(out/n) == h for n, h in seal['files_sha256'].items())
    return attempts, results, done


def execute(kind, out, limit=0):
    with lock(out):
        probe(kind, out)
        questions, assets, plan = prepare(kind, out)
        attempts, results, done = validate(kind, out)
        if (out/'completion.json').exists():
            return
        if (out/'stop.json').exists():
            raise RuntimeError('Existing stop condition; inspect, do not automatically resume')
        guard = threading.Lock()
        halt = threading.Event()
        def one(task):
            body = payload(questions[task['item_id']], kind, assets)
            assert d.digest(body) == task['request_payload_sha256']
            wire = d.canonical(body)
            choices = set(body['questions']['decision']['criteria'])
            collected = []
            for attempt in (1, 2):
                with guard:
                    if halt.is_set():
                        break
                    d.append(out/'dispatches.jsonl', dict(task, attempt=attempt, dispatch=d.timestamps()))
                response = send(wire)
                row = dict(task, attempt=attempt, **response, **parse(response, choices))
                with guard:
                    d.append(out/'attempts.jsonl', row)
                    attempts.append(row)
                collected.append(row)
                if row['status'] in ('identity_mismatch','unexpected_reasoning') or row['http_status'] in (400,401,402,403,404,413,422):
                    halt.set()
                if attempt == 1 and transient(row) and not halt.is_set():
                    delay = 60 if row['http_status'] == 425 else max(1, d.retry_wait(row))
                    with guard:
                        d.append(out/'retry_waits.jsonl', dict(request_index=task['request_index'], seconds=delay))
                    if not halt.wait(delay):
                        continue
                break
            if collected:
                with guard:
                    result = dict(task, attempts=len(collected), first_status=collected[0]['status'],
                                  eventual_status=collected[-1]['status'])
                    d.append(out/'results.jsonl', result)
                    results.append(result)
        remaining = [p for p in plan if p['request_index'] not in done]
        if limit:
            remaining = remaining[:limit]
        with ThreadPoolExecutor(max_workers=2 if kind == 'text' else 1) as pool:
            for wave in sorted({p['wave'] for p in remaining}):
                futures = [pool.submit(one, p) for p in remaining if p['wave'] == wave]
                for future in futures:
                    future.result()
                first = [r for r in attempts if r['attempt'] == 1]
                progress = dict(bank=kind, n=len(first), planned=len(plan),
                    latency=stats.quantiles([r['latency_ms'] for r in first]),
                    statuses=dict(Counter(r['status'] for r in first)), time=d.timestamps())
                d.append(out/'progress.jsonl', progress)
                budget = sum(Decimal(str(r['accounted_cost_usd'])) if r['accounted_cost_usd'] is not None
                             else Decimal('.003') for r in attempts)
                reason = 'fatal_response' if halt.is_set() else 'median_over_2s' if speed_stop(attempts) else 'spend_guard' if budget >= GUARD else None
                if len(first) % 20 == 0 or reason:
                    print(json.dumps(progress), flush=True)
                if reason:
                    d.save_bound(out/'stop.json', dict(progress, reason=reason))
                    return
        if len(results) == len(plan):
            names = ['manifest.json','software.json','model_metadata.json','dispatches.jsonl','attempts.jsonl','results.jsonl']
            names += [p.name for p in out.glob('probe*.json')]
            if (out/'retry_waits.jsonl').exists():
                names.append('retry_waits.jsonl')
            d.save_bound(out/'completion.json', dict(status='COMPLETE', n=len(plan), completed=d.timestamps(),
                files_sha256={n: file_hash(out/n) for n in names}))
            validate(kind, out)
            print('COMPLETE '+kind+' '+str(len(plan)), flush=True)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--bank', choices=('text','image'), required=True)
    modes = p.add_mutually_exclusive_group()
    modes.add_argument('--execute', action='store_true')
    modes.add_argument('--probe', action='store_true')
    modes.add_argument('--validate', action='store_true')
    p.add_argument('--limit', type=int, default=0)
    args = p.parse_args()
    out = OUT/args.bank
    if args.execute:
        execute(args.bank, out, args.limit)
    elif args.probe:
        with lock(out):
            probe(args.bank, out)
    elif args.validate:
        a, _, done = validate(args.bank, out)
        print(json.dumps(dict(bank=args.bank, cases=len(done), attempts=len(a))))
    else:
        _, _, plan = prepare(args.bank, out)
        print(json.dumps(dict(bank=args.bank, planned=len(plan), inference_calls=0)))


if __name__ == '__main__':
    main()
