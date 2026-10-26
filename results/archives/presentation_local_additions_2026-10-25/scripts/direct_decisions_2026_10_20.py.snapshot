"""Answer-blind, resumable native-provider runs on the frozen 1,342 bank.

No gold keys, no provider fallback, no correctness-dependent retries. Runtime
evidence stays in ignored runs/. Explicit --execute is required for inference.
"""
from repo_layout import repo_file
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from contextlib import contextmanager
from decimal import Decimal
import fcntl
from hashlib import sha256
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
import frontier_reference as bank
import text_models as chat

ROOT = Path(__file__).resolve().parents[1]
OUT = repo_file('runs/direct_decisions_2026-10-20', root=ROOT)
ENV = Path('/Users/etsabary/Documents/repos/the village 14947/.env')
MODELS = {
    'd3_turbo': dict(label='d3-turbo', model='vllm-sr/d3-turbo', host='decision.vllm-sr.ai',
                     key='D3-TURBO_API_KEY', catalog='/api/info', interval=.15, tariff='0'),
    'amos_large': dict(label='Amos 1 Large', model='amos-1-large', host='api.amos.scira.ai',
                      key=None, catalog='/v1/models', interval=1.1, tariff='0'),
    'kettei_fat': dict(label='kettei-fat', model='kettei-fat', host='api.sqwish.ai',
                      key='SQWISH_API_KEY', catalog='/v1/models', interval=1.1, tariff='.06'),
}
SOFTWARE = ('direct_decisions_2026_10_20.py', 'test_direct_decisions_2026_10_20.py',
            'frontier_reference.py', 'decision_refresh.py', 'run_benchmark.py', 'text_models.py')


def credentials(mid):
    name = MODELS[mid]['key']
    if name is None:
        return ''
    value = str(os.environ.get(name) or dotenv_values(ENV).get(name) or '').strip()
    assert value, name + ' is not configured'
    return value


def payload(q, mid):
    return {'model': MODELS[mid]['model'], **q['native_input']}


def send(body, key, mid, operation):
    """Fresh HTTPS connect through full body; same timing boundary as prior runs.

    Sqwish retries reuse one operation key. Queue/rate waits are outside timer.
    Amos receives no Authorization header. No process-wide client state changes.
    """
    cfg = MODELS[mid]
    ctx = ssl.create_default_context(cafile='/etc/ssl/cert.pem')
    conn = http.client.HTTPSConnection(cfg['host'], timeout=10, context=ctx)
    result = dict(http_status=0, raw_response={}, error='', response_headers={},
                  transport_failure=False, headers_latency_ms=None, started=d.timestamps())
    headers = {'Content-Type':'application/json', 'Accept':'application/json'}
    if key:
        headers['Authorization'] = 'Bearer ' + key
    if mid == 'kettei_fat':
        headers['Idempotency-Key'] = operation
    start = time.perf_counter()
    try:
        conn.connect()
        conn.sock.settimeout(max(.001, 90 - (time.perf_counter()-start)))
        conn.request('POST', '/v1/systemone', body=body, headers=headers)
        conn.sock.settimeout(max(.001, 90 - (time.perf_counter()-start)))
        response = conn.getresponse()
        result.update(http_status=response.status, headers_latency_ms=(time.perf_counter()-start)*1000,
            response_headers={k.lower():v for k,v in response.getheaders() if k.lower() in
                {'retry-after','x-request-id','date','content-type','idempotency-replayed'}})
        chunks, size = [], 0
        while True:
            left = 90 - (time.perf_counter()-start)
            if left <= 0:
                raise TimeoutError('90-second total response deadline')
            conn.sock.settimeout(left)
            chunk = response.read1(65536)
            if not chunk:
                break
            size += len(chunk)
            assert size <= 4*1024**2, 'Oversized decision response'
            chunks.append(chunk)
        text = b''.join(chunks).decode('utf-8')
        if key:
            text = text.replace(key, '[REDACTED_API_KEY]')
        try:
            result['raw_response'] = json.loads(text)
        except ValueError:
            result['error'] = 'Non-JSON response: ' + text[:300]
        if response.status != 200:
            result['error'] = 'HTTP ' + str(response.status)
    except Exception as exc:
        message = type(exc).__name__ + ': ' + str(exc)
        result['error'] = message.replace(key, '[REDACTED_API_KEY]') if key else message
        result['transport_failure'] = isinstance(exc, (OSError,http.client.HTTPException))
    finally:
        result.update(latency_ms=(time.perf_counter()-start)*1000, completed=d.timestamps())
        conn.close()
    return result


def parse(response, mid):
    result = d.parse(response)
    raw = response.get('raw_response') or {}
    if not isinstance(raw, dict):
        raw = {}
    if raw.get('error'):
        result.update(status='provider_error', choice=None)
    if response.get('transport_failure'):
        result.update(status='transport_failure', choice=None)
    if result['status'] == 'ok':
        if result['model_returned'] != MODELS[mid]['model']:
            result.update(status='identity_mismatch', choice=None)
        elif result['usage'].get('output_tokens') != 0:
            result.update(status='unverified_zero_generation', choice=None)
    cost, source = None, 'unreported'
    amount = (raw.get('charge') or {}).get('amount_usd')
    if mid == 'kettei_fat' and amount is not None:
        value = Decimal(str(amount))
        assert value.is_finite() and value >= 0
        cost, source = float(value), 'api_reported_charge'
    elif MODELS[mid]['tariff'] == '0':
        cost, source = 0.0, 'public_free_endpoint_not_api_reported'
    elif isinstance(result['usage'].get('input_tokens'), int):
        cost = float(Decimal(result['usage']['input_tokens']) * Decimal(MODELS[mid]['tariff']) / 10**6)
        source = 'usage_times_captured_tariff'
    return {**result, 'accounted_cost_usd':cost, 'cost_source':source,
            'reported_cost_usd':float(Decimal(str(amount))) if mid == 'kettei_fat' and amount is not None else None,
            'returned_version':raw.get('version')}


def prepare(mid, out):
    questions, order = bank.prepare()
    plan = []
    for item in order:
        q = questions[item['item_id']]
        plan.append({k:item[k] for k in ('request_index','wave','item_id','family_id','native_input_sha256')})
        plan[-1].update(model_id=mid, model_requested=MODELS[mid]['model'],
            request_payload_sha256=d.digest(payload(q,mid)), request_body_bytes=len(d.canonical(payload(q,mid))))
    out.mkdir(parents=True, exist_ok=True)
    d.save_bound(out/'manifest.json', dict(version='direct-native-1342-20261020-v1', model=MODELS[mid],
        bank_sha256=bank.BANK_HASH, planned_cases=1342, request_plan=plan,
        endpoint='https://'+MODELS[mid]['host']+'/v1/systemone',
        input='Exact frozen native state, instructions, question and five original criteria; only model identity added',
        order='Same seed/order as Sol1342: 2026101906; no gold key read by executor',
        timing='Fresh HTTPS connect through full response body, monotonic; excludes preparation/queue/rate/retry waits',
        concurrency='Two in-flight maximum per model; two-question waves with barrier',
        rate_interval_seconds=MODELS[mid]['interval'],
        retry='One transport/HTTP408/429/5xx recovery maximum; same Sqwish idempotency key. No answer-dependent retries',
        scoring='First attempt over every scored question, failures unsuccessful; recovery evidence separate',
        speed_screen='Pause after at least20 cases when first-attempt median exceeds2000ms, per existing operator rule',
        cost='API charge for Sqwish, otherwise usage-times-captured tariff if charge absent. Free services labelled public-free, never API-reported zero',
        soft_cost_guard_usd='.50', identity_limit='Returned named model checked; hosted alias is not immutable-weight attestation',
        privacy='Only public benchmark questions sent; providers may retain requests; no Village conversation data',
        sources=['https://decision.vllm-sr.ai/api/info','https://huggingface.co/vllm-sr/d3-turbo',
                 'https://amos.scira.ai/docs/','https://docs.sqwish.ai/guides/jev-migration',
                 'https://docs.sqwish.ai/guides/pricing']))
    d.save_bound(out/'software.json', {n:bank.file_hash(repo_file(n, root=ROOT)) for n in SOFTWARE})
    return questions, plan


def capture_metadata(mid, out):
    path=out/'model_metadata.json'
    if path.exists():
        return
    cfg=MODELS[mid]; key=credentials(mid)
    url='https://'+cfg['host']+cfg['catalog']
    headers={'Accept':'application/json'}
    if key:
        headers['Authorization']='Bearer '+key
    with urllib.request.urlopen(urllib.request.Request(url,headers=headers),
            context=ssl.create_default_context(cafile='/etc/ssl/cert.pem'),timeout=25) as response:
        data=json.load(response)
    rows=data.get('models') or data.get('data') or []
    selected=[r for r in rows if r.get('id',r.get('name'))==cfg['model']]
    assert len(selected)==1, 'Exact model absent from catalog'
    if mid=='d3_turbo':
        assert selected[0]['ready']
    if mid=='kettei_fat':
        assert selected[0]['status']=='ready' and selected[0]['decision_price_nano']=='60'
    d.save_bound(path,dict(retrieved=d.timestamps(),source=url,selected=selected[0],
                          public_free=mid!='kettei_fat',limits=data.get('limits')))


def probe(mid, out):
    path=out/'compatibility_probe.json'
    if not path.exists():
        q={'native_input':{'state':'The switch is ON.','questions':{'decision':{'type':'choice',
            'instructions':'Select the option matching the switch state exactly.',
            'criteria':dict(zip('12345',('OFF','UNKNOWN','ON','BROKEN','UNPLUGGED')))}}}}
        body=payload(q,mid)
        assert not (out/'probe_dispatch.json').exists(), 'Unresolved compatibility dispatch; inspect before replay'
        d.save_bound(out/'probe_dispatch.json',dict(payload=body,sha256=d.digest(body),started=d.timestamps()))
        d.save_bound(path,dict(payload=body,transport=send(d.canonical(body),credentials(mid),mid,'direct-20261020-'+mid+'-probe')))
    value=json.loads(path.read_text()); parsed=parse(value['transport'],mid)
    assert value['payload']==json.loads((out/'probe_dispatch.json').read_text())['payload']
    assert parsed['status']=='ok' and parsed['choice']=='3', 'Compatibility probe failed: '+parsed['status']
    return parsed


@contextmanager
def model_lock(out):
    with (out/'.execution.lock').open('a') as stream:
        fcntl.flock(stream,fcntl.LOCK_EX|fcntl.LOCK_NB)
        try:
            yield
        finally:
            fcntl.flock(stream,fcntl.LOCK_UN)


def validate(mid,out,complete=False):
    _,plan=prepare(mid,out)
    attempts,results,dispatches=(d.rows(out/n) for n in ('attempts.jsonl','results.jsonl','dispatches.jsonl'))
    done=d.reconcile(dispatches,attempts,results,plan)
    indexed={r['request_index']:r for r in plan}
    for row in attempts+results+dispatches:
        assert all(row[k]==v for k,v in indexed[row['request_index']].items())
    for row in attempts:
        assert all(row[k]==v for k,v in parse(row,mid).items()), 'Parser drift'
    if complete:
        assert len(done)==1342
        for name,value in json.loads((out/'completion.json').read_text())['files_sha256'].items():
            assert bank.file_hash(out/name)==value
    return attempts,results,done


def execute(mid,out,limit=0):
    questions,plan=prepare(mid,out);capture_metadata(mid,out);probe(mid,out)
    with model_lock(out):
        attempts,results,done=validate(mid,out)
        if (out/'completion.json').exists():
            validate(mid,out,True);return
        if (out/'speed_screen_pause.json').exists():
            print(json.dumps({'model':mid,'status':'PAUSED_SPEED_SCREEN'}),flush=True);return
        key=credentials(mid);lock=threading.Lock(); halt=threading.Event(); rate=threading.Lock(); last=[0.0]
        def one(task):
            body=d.canonical(payload(questions[task['item_id']],mid)); collected=[]; began=time.perf_counter()
            for attempt in (1,2):
                with rate:
                    delay=max(0,MODELS[mid]['interval']-(time.monotonic()-last[0]))
                    if halt.wait(delay):return
                    last[0]=time.monotonic()
                with lock:
                    if halt.is_set():return
                    known=sum(Decimal(str(a['accounted_cost_usd'])) if a['accounted_cost_usd'] is not None
                              else Decimal(a['request_body_bytes'])*Decimal('.00000006') for a in attempts)
                    assert known < Decimal('.50'), 'Soft cost guard'
                    d.append(out/'dispatches.jsonl',{**task,'attempt':attempt,'dispatch':d.timestamps()})
                response=send(body,key,mid,'direct-20261020-'+mid+'-'+task['request_payload_sha256'])
                row={**task,'attempt':attempt,**response,**parse(response,mid)}
                with lock:
                    d.append(out/'attempts.jsonl',row);attempts.append(row)
                collected.append(row)
                if row['status'] in ('identity_mismatch','unverified_zero_generation') or row['http_status'] in (400,401,402,403,404,413,422):
                    halt.set();break
                if attempt==1 and (row['transport_failure'] or row['http_status'] in d.TRANSIENT):
                    wait=min(60,max(1,d.retry_wait(row)))
                    with lock:d.append(out/'retry_waits.jsonl',dict(request_index=task['request_index'],seconds=wait))
                    if halt.wait(wait):break
                    continue
                break
            if collected:
                result={**task,'attempts':len(collected),'first_status':collected[0]['status'],
                        'eventual_status':collected[-1]['status'],'item_elapsed_ms':(time.perf_counter()-began)*1000}
                with lock:d.append(out/'results.jsonl',result);results.append(result)
        remaining=[p for p in plan if p['request_index'] not in done]
        if limit:remaining=remaining[:limit]
        with ThreadPoolExecutor(max_workers=2) as pool:
            for wave in sorted({p['wave'] for p in remaining}):
                for future in as_completed([pool.submit(one,p) for p in remaining if p['wave']==wave]):future.result()
                first=[a for a in attempts if a['attempt']==1]
                stats=chat.quantiles([a['latency_ms'] for a in first])
                progress=dict(model=mid,n=len(results),planned=1342,statuses=dict(Counter(a['status'] for a in first)),
                              latency=stats,cost_known_usd=sum(a['accounted_cost_usd'] or 0 for a in attempts),time=d.timestamps())
                d.append(out/'progress.jsonl',progress)
                if len(results)%20==0 or halt.is_set():print(json.dumps(progress),flush=True)
                if halt.is_set():
                    d.save_bound(out/('halt_'+str(len(results))+'.json'),progress);return
                if len(first)>=20 and stats['median_ms']>2000:
                    d.save_bound(out/'speed_screen_pause.json',progress);print('PAUSED_SPEED_SCREEN '+mid,flush=True);return
        if len(results)==1342:
            files=('manifest.json','software.json','model_metadata.json','compatibility_probe.json','probe_dispatch.json',
                   'attempts.jsonl','results.jsonl','dispatches.jsonl')
            if (out/'retry_waits.jsonl').exists():files+=('retry_waits.jsonl',)
            d.save_bound(out/'completion.json',dict(status='COMPLETE_1342',completed=d.timestamps(),
                files_sha256={n:bank.file_hash(out/n) for n in files}))
            validate(mid,out,True);print('COMPLETE_1342 '+mid,flush=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--model',choices=MODELS,required=True)
    parser.add_argument('--execute',action='store_true')
    parser.add_argument('--validate',action='store_true')
    parser.add_argument('--limit',type=int,default=0)
    args=parser.parse_args();out=OUT/args.model
    if args.validate:
        rows,results,done=validate(args.model,out,(out/'completion.json').exists())
        print(json.dumps({'model':args.model,'validated':len(done),'attempts':len(rows)}));return
    if args.execute:execute(args.model,out,args.limit)
    else:
        _,plan=prepare(args.model,out);print(json.dumps({'mode':'DRY_RUN','requests':len(plan),'inference_calls':0}))


if __name__=='__main__':main()
