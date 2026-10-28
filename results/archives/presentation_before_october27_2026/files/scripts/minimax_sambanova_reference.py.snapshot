"""Separate MiniMax M3 no-thinking reference, pinned OpenRouter -> SambaNova.

The stopped DeepInfra prefix is not pooled into this run. Together and Novita
compatibility probes produced thinking despite the requested off flag and are
not eligible routes. A new route never silently replaces a scored attempt.
"""
from repo_layout import repo_file
import argparse
from decimal import Decimal
import json
import sys

import minimax_reference as prior

base,controller=prior.base,prior.controller
ROOT,BANK_HASH,MODEL,SNAPSHOT,SPEC=prior.ROOT,prior.BANK_HASH,prior.MODEL,prior.SNAPSHOT,prior.SPEC
OUT=repo_file('runs/minimax_m3_none_sambanova_1342_2026-10-19', root=ROOT)
GUARD=Decimal('2.00')
d,chat,file_hash,sanitize,parse=prior.d,prior.chat,prior.file_hash,prior.sanitize,prior.parse


def payload(q):
    body=prior.payload(q)
    body['provider']['only']=['sambanova']
    return body


def prepare():
    questions,old=base.prepare();plan=[]
    for t in old:
        body=payload(questions[t['item_id']])
        plan.append({**t,'model_id':'minimax_m3_sambanova_none','model_requested':MODEL,
                     'request_payload_sha256':d.digest(body),'request_body_bytes':len(d.canonical(body))})
    return questions,plan


def reserve(task):
    return Decimal(task['request_body_bytes']+256)*Decimal('.0000006')+Decimal(16)*Decimal('.0000024')


def check_route(r):
    if r['status'] in ('transport_failure','http_failure','provider_error'):return
    assert r['provider']=='SambaNova' and r['model_returned'] in (MODEL,SNAPSHOT)
    assert r['reported_cost_usd'] is not None
    assert r['reported_reasoning_tokens']==0 and not isinstance(r['reported_reasoning_tokens'],bool)
    assert not r['reasoning_text_present'] and r['status']!='unexpected_reasoning'


def validate_probe(out):
    p=json.loads((out/'compatibility_probe.json').read_text());v=json.loads((out/'probe_dispatch.json').read_text())
    assert p['payload']==v['payload'] and d.digest(p['payload'])==v['request_payload_sha256']
    expected=payload({'instructions':'','context':'','question':'','options':['']*5})
    assert {k:v for k,v in p['payload'].items() if k!='messages'}=={k:v for k,v in expected.items() if k!='messages'}
    r={**p['transport'],**parse(p['transport'])};check_route(r)
    assert r['status']=='ok' and r['choice']=='3'
    return r


def probe_cost(out):
    validate_probe(out)
    probes=json.loads((out/'route_selection_probes.json').read_text())
    return sum((Decimal(str(p['transport']['raw_response']['usage']['cost']))
                for p in probes if isinstance((p['transport'].get('raw_response') or {}).get('usage',{}).get('cost'),(int,float))),Decimal(0))


def software():
    return {**prior.software(),**{n:file_hash(repo_file(n, root=ROOT)) for n in ('minimax_sambanova_reference.py','test_minimax_sambanova_reference.py')}}


def freeze(out,plan):
    md=json.loads((out/'model_metadata.json').read_text())['data']
    rows=[e for e in md['endpoints'] if e['tag']=='sambanova' and e['status']==0]
    assert len(rows)==1 and rows[0]['name']=='SambaNova | '+SNAPSHOT
    assert Decimal(rows[0]['pricing']['prompt'])==Decimal('.0000006')
    assert Decimal(rows[0]['pricing']['completion'])==Decimal('.0000024')
    validate_probe(out)
    previous=json.loads((prior.OUT/'manifest.json').read_text())
    body=payload({'instructions':'','context':'','question':'','options':['']*5})
    d.save_bound(out/'manifest.json',{**previous,'version':'minimax-m3-sambanova-no-thinking-1342-v1',
        'settings':{k:v for k,v in body.items() if k!='messages'},'request_plan':plan,'soft_guard_usd':str(GUARD),
        'identity_limit':'Dated OpenRouter model catalog and returned model, no immutable-weight or quantization attestation',
        'hyper_route_selection':'Hyper lacks documented off. DeepInfra prefix stopped for repeated429; Together/Novita probes emitted thinking; Parasail rejected with429. SambaNova passed explicit-zero no-thinking probe. All trials retained separately.',
        'compatibility_cost_limit':'All known route-probe charges retained; rejected probes without cost remain unknown, not zero.'})
    d.save_bound(out/'software.json',software())


def sealed_files(out):
    return prior.sealed_files(out)


def validate(out,complete=False):
    _,plan=prepare();m=json.loads((out/'manifest.json').read_text())
    assert m['request_plan']==plan and m['bank_sha256']==BANK_HASH
    assert json.loads((out/'software.json').read_text())==software()
    validate_probe(out);a,r,done=controller.ledger_state(sys.modules[__name__],out,plan)
    if complete:
        seal=json.loads((out/'completion.json').read_text())
        assert seal['status']=='COMPLETE_1342' and done==set(range(1,1343))
        assert all(file_hash(out/n)==h for n,h in seal['files_sha256'].items())
    return a,r


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--execute',action='store_true');p.add_argument('--validate',action='store_true');p.add_argument('--waves',type=int,default=0)
    args=p.parse_args();assert not(args.execute and args.validate)
    if args.execute:controller.execute(sys.modules[__name__],OUT,waves=args.waves)
    elif args.validate:
        a,r=validate(OUT,complete=True);print(json.dumps({'validation':'PASS','questions':len(r),'attempts':len(a),'paid_calls':0}))
    else:print(json.dumps({'mode':'DRY_RUN','questions':len(prepare()[1]),'paid_calls':0}))


if __name__=='__main__':main()
