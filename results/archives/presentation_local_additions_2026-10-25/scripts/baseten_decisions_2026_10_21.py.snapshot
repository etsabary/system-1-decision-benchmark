"""Direct Baseten full-bank runs, separate from the OpenRouter free samples."""
from repo_layout import repo_file
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
import http.client
import json
import os
from pathlib import Path
import ssl
import threading
import time
import urllib.request

from dotenv import dotenv_values
import decision_refresh as d
import decision_additions_2026_10_21 as screen
import direct_decisions_2026_10_20 as direct
import frontier_reference as bank
import text_models as stats

ROOT = Path(__file__).resolve().parents[1]
OUT = repo_file('runs/baseten_decisions_2026-10-21', root=ROOT)
MODELS = {
    'mammoth1':dict(label='Mammoth-1',model='decision-models/baseten-mammoth-27b-latest',name='mammoth-1'),
    'elephant1':dict(label='Elephant-1',model='decision-models/baseten-elephant-9b-latest',name='elephant-1'),
}
SOFTWARE = ('baseten_decisions_2026_10_21.py','test_baseten_decisions_2026_10_21.py',
            'decision_additions_2026_10_21.py','direct_decisions_2026_10_20.py',
            'frontier_reference.py','decision_refresh.py','text_models.py','run_benchmark.py')


def key():
    value = str(os.environ.get('BASETEN_API_KEY') or dotenv_values(screen.ENV).get('BASETEN_API_KEY') or '').strip()
    assert value, 'BASETEN_API_KEY missing'
    return value


def payload(q,mid):
    return dict(model=MODELS[mid]['model'], **q['native_input'])


def send(body):
    secret = key()
    connection = http.client.HTTPSConnection('inference.baseten.co',timeout=10,
        context=ssl.create_default_context(cafile='/etc/ssl/cert.pem'))
    value = dict(http_status=0,raw_response={},error='',response_headers={},
                 headers_latency_ms=None,transport_failure=False,started=d.timestamps())
    began = time.perf_counter()
    try:
        connection.connect()
        connection.sock.settimeout(max(.001,90-(time.perf_counter()-began)))
        connection.request('POST','/v1/systemone',body=body,headers={
            'Authorization':'Api-Key '+secret,'Content-Type':'application/json','Accept':'application/json'})
        response = connection.getresponse()
        value.update(http_status=response.status,headers_latency_ms=(time.perf_counter()-began)*1000,
            response_headers={k.lower():v for k,v in response.getheaders() if k.lower() in
                ('date','retry-after','x-request-id','content-type')})
        chunks,size = [],0
        while True:
            left = 90-(time.perf_counter()-began)
            if left <= 0:
                raise TimeoutError('90-second full-response deadline')
            connection.sock.settimeout(left)
            chunk = response.read1(65536)
            if not chunk:
                break
            size += len(chunk)
            assert size <= 4*1024**2
            chunks.append(chunk)
        text = b''.join(chunks).decode().replace(secret,'[REDACTED_API_KEY]')
        try:
            value['raw_response'] = json.loads(text)
        except ValueError:
            value['error'] = 'Non-JSON response: '+text[:300]
        if response.status != 200:
            value['error'] = 'HTTP '+str(response.status)
    except Exception as exc:
        value.update(error=(type(exc).__name__+': '+str(exc)).replace(secret,'[REDACTED_API_KEY]'),
                     transport_failure=isinstance(exc,(OSError,http.client.HTTPException)))
    finally:
        value.update(latency_ms=(time.perf_counter()-began)*1000,completed=d.timestamps())
        connection.close()
    return value


def parse(response,mid):
    value = d.parse(response)
    raw = response.get('raw_response') or {}
    if raw.get('error'):
        value.update(status='provider_error',choice=None)
    if response.get('transport_failure'):
        value.update(status='transport_failure',choice=None)
    if value['status'] == 'ok' and value['model_returned'] not in (
            MODELS[mid]['model'],MODELS[mid]['name'],'baseten/'+MODELS[mid]['name'],
            'baseten/'+MODELS[mid]['name']+'-20261021'):
        value.update(status='identity_mismatch',choice=None)
    if raw.get('reasoning') or raw.get('thinking') or value['usage'].get('reasoning_tokens'):
        value.update(status='unexpected_reasoning',choice=None)
    return dict(value,accounted_cost_usd=value['reported_cost_usd'] if value['reported_cost_usd'] is not None else 0.,
        cost_source='api_reported' if value['reported_cost_usd'] is not None else 'captured_promotional_zero_tariff_not_receipt',
        returned_version=raw.get('version'))


def prepare(mid,out):
    qs,original = bank.prepare()
    plan = []
    for task in original:
        body = payload(qs[task['item_id']],mid)
        plan.append(dict({k:task[k] for k in ('request_index','wave','item_id','family_id','native_input_sha256')},
            model_id=mid,model_requested=MODELS[mid]['model'],request_payload_sha256=d.digest(body),
            request_body_bytes=len(d.canonical(body))))
    out.mkdir(parents=True,exist_ok=True)
    d.save_bound(out/'manifest.json',dict(version='baseten-native-1342-20261021-v1',model=MODELS[mid],
        bank_sha256=bank.BANK_HASH,planned_cases=1342,request_plan=plan,
        endpoint='https://inference.baseten.co/v1/systemone',order_seed=bank.SEED,
        input='Unchanged frozen native input; model identity only added; executor does not load answer key',
        timing='Fresh HTTPS connect through complete body, same monotonic boundary; pacing/queue/retry waits excluded',
        concurrency='Two in-flight maximum per model, two-case barrier waves; two models active',
        speed_screen='Cumulative first-attempt median over2000ms at/after20 stops after the current two-case wave',
        retries='One transport/HTTP408/429/5xx recovery maximum; never answer-dependent',
        scoring='First attempts including failures. OpenRouter sample never pooled into direct-run score or timings',
        cost='Catalog currently zero promotional price, independently labelled from returned usage.cost; absent receipts remain unreported',
        identity_limit='Catalog name mammoth-1/elephant-1 behind latest serving aliases; returned identity checked but no immutable-weight attestation',
        generation_limit='Official native single-forward-pass option-logit architecture, no explanation or reasoning requested; internal execution not independently attested',
        sources=['https://www.baseten.co/library/'+MODELS[mid]['name']+'/',
                 'https://labs.baseten.co/articles/mammoth-1-and-elephant-1-frontier-decision-models']))
    d.save_bound(out/'software.json',{name:bank.file_hash(repo_file(name, root=ROOT)) for name in SOFTWARE})
    return qs,plan


def capture_catalog(mid,out):
    target = out/'model_metadata.json'
    if target.exists():
        return
    url = 'https://inference.baseten.co/v1/models'
    request = urllib.request.Request(url,headers={'Authorization':'Api-Key '+key()})
    with urllib.request.urlopen(request,context=ssl.create_default_context(cafile='/etc/ssl/cert.pem'),timeout=25) as response:
        data = json.load(response)
    selected = [v for v in data['data'] if v['id'] == MODELS[mid]['model']]
    assert len(selected) == 1 and selected[0]['name'] == MODELS[mid]['name']
    assert all(float(selected[0]['pricing'][k]) == 0 for k in ('prompt','completion','request'))
    assert selected[0]['input_modalities'] == ['text']
    d.save_bound(target,dict(retrieved=d.timestamps(),source=url,selected=selected[0]))


def probe(mid,out):
    target = out/'compatibility_probe.json'
    if not target.exists():
        body = payload(dict(native_input=dict(state='The switch is ON.',questions=dict(decision=dict(
            type='choice',instructions='Select the option matching the switch state exactly.',
            criteria=dict(zip('12345',('OFF','UNKNOWN','ON','BROKEN','UNPLUGGED'))))))),mid)
        assert not (out/'probe_dispatch.json').exists(), 'Unresolved probe dispatch'
        d.save_bound(out/'probe_dispatch.json',dict(payload=body,started=d.timestamps()))
        d.save_bound(target,dict(payload=body,transport=send(d.canonical(body))))
    value = json.loads(target.read_text())
    parsed = parse(value['transport'],mid)
    assert value['payload'] == json.loads((out/'probe_dispatch.json').read_text())['payload']
    assert parsed['status'] == 'ok' and parsed['choice'] == '3', 'Compatibility failed: '+parsed['status']
    return parsed


def validate(mid,out,complete=False):
    _,plan = prepare(mid,out)
    attempts,results,dispatches = (d.rows(out/n) for n in ('attempts.jsonl','results.jsonl','dispatches.jsonl'))
    done = d.reconcile(dispatches,attempts,results,plan)
    indexed = {p['request_index']:p for p in plan}
    for row in attempts+results+dispatches:
        assert all(row[k] == v for k,v in indexed[row['request_index']].items())
    for row in attempts:
        assert all(row[k] == v for k,v in parse(row,mid).items()), 'Parser drift'
    first,last = stats.first_and_eventual(attempts)
    for row in results:
        i = row['request_index']
        assert row['attempts'] == last[i]['attempt'] and row['first_status'] == first[i]['status']
        assert row['eventual_status'] == last[i]['status']
    if complete:
        assert len(done) == 1342
        for name,h in json.loads((out/'completion.json').read_text())['files_sha256'].items():
            assert bank.file_hash(out/name) == h
    return attempts,results,done


def execute(mid,limit=0):
    out = OUT/mid
    qs,plan = prepare(mid,out)
    with direct.model_lock(out):
        capture_catalog(mid,out)
        parsed = probe(mid,out)
        print(json.dumps(dict(model=mid,route='direct_baseten',probe=parsed['status'],returned=parsed['model_returned'])),flush=True)
        attempts,results,done = validate(mid,out)
        if (out/'completion.json').exists():
            validate(mid,out,True)
            return
        if (out/'speed_screen_pause.json').exists() or screen.speed_stop(attempts):
            print('PAUSED_SPEED_SCREEN '+mid,flush=True)
            return
        halt,lock = threading.Event(),threading.Lock()
        def one(task):
            body = d.canonical(payload(qs[task['item_id']],mid))
            assert d.digest(json.loads(body)) == task['request_payload_sha256']
            collected = []
            began = time.perf_counter()
            for attempt in (1,2):
                with lock:
                    if halt.is_set():
                        return
                    d.append(out/'dispatches.jsonl',dict(task,attempt=attempt,dispatch=d.timestamps()))
                response = send(body)
                row = dict(task,attempt=attempt,**response,**parse(response,mid))
                with lock:
                    d.append(out/'attempts.jsonl',row)
                    attempts.append(row)
                collected.append(row)
                if row['status'] in ('identity_mismatch','unexpected_reasoning') or row['http_status'] in (400,401,402,403,404,413,422):
                    halt.set()
                    break
                if attempt == 1 and (row['transport_failure'] or row['http_status'] in d.TRANSIENT):
                    delay = max(1,d.retry_wait(row))
                    with lock:
                        d.append(out/'retry_waits.jsonl',dict(request_index=task['request_index'],seconds=delay))
                    if halt.wait(delay):
                        break
                    continue
                break
            if collected:
                with lock:
                    result = dict(task,attempts=len(collected),first_status=collected[0]['status'],
                        eventual_status=collected[-1]['status'],item_elapsed_ms=(time.perf_counter()-began)*1000)
                    d.append(out/'results.jsonl',result)
                    results.append(result)
        remaining = [p for p in plan if p['request_index'] not in done]
        if limit:
            remaining = remaining[:limit]
        with ThreadPoolExecutor(max_workers=2) as pool:
            for wave in sorted({p['wave'] for p in remaining}):
                for future in as_completed([pool.submit(one,p) for p in remaining if p['wave'] == wave]):
                    future.result()
                first = [r for r in attempts if r['attempt'] == 1]
                progress = dict(model=mid,n=len(first),route='direct_baseten',planned=1342,
                    latency=stats.quantiles([r['latency_ms'] for r in first]),
                    statuses=dict(Counter(r['status'] for r in first)),time=d.timestamps())
                d.append(out/'progress.jsonl',progress)
                if len(first)%50 == 0 or halt.is_set():
                    print(json.dumps(progress),flush=True)
                if halt.is_set():
                    d.save_bound(out/('halt_'+str(len(first))+'.json'),progress)
                    return
                if screen.speed_stop(attempts):
                    d.save_bound(out/'speed_screen_pause.json',progress)
                    print('PAUSED_SPEED_SCREEN '+mid,flush=True)
                    return
        if len(results) == 1342:
            files = ['manifest.json','software.json','model_metadata.json','compatibility_probe.json',
                     'probe_dispatch.json','attempts.jsonl','results.jsonl','dispatches.jsonl']
            if (out/'retry_waits.jsonl').exists():
                files.append('retry_waits.jsonl')
            d.save_bound(out/'completion.json',dict(status='COMPLETE_1342',completed=d.timestamps(),
                files_sha256={name:bank.file_hash(out/name) for name in files}))
            validate(mid,out,True)
            print('COMPLETE_1342 '+mid,flush=True)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--models',nargs='+',choices=MODELS,default=list(MODELS))
    p.add_argument('--execute',action='store_true')
    p.add_argument('--validate',action='store_true')
    p.add_argument('--limit',type=int,default=0)
    args = p.parse_args()
    if not args.execute:
        for mid in args.models:
            if args.validate:
                a,r,done = validate(mid,OUT/mid,(OUT/mid/'completion.json').exists())
                print(json.dumps(dict(model=mid,validated=len(done),attempts=len(a))))
            else:
                _,plan = prepare(mid,OUT/mid)
                print(json.dumps(dict(model=mid,dry_run=True,requests=len(plan),inference_calls=0)))
        return
    with ThreadPoolExecutor(max_workers=len(args.models)) as pool:
        jobs = {pool.submit(execute,mid,args.limit):mid for mid in args.models}
        for future in as_completed(jobs):
            future.result()


if __name__ == '__main__':
    main()
