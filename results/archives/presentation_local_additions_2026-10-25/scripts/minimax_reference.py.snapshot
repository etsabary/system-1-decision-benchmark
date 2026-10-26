"""MiniMax M3 no-thinking reference; fixed OpenRouter -> DeepInfra FP8 route.

Hyper Charm's catalog exposes only low/medium/high for M3, not an off mode.
This separate route requires explicit zero reasoning-token telemetry. No tools,
answer-dependent retries, hidden fallbacks or changes to the frozen bank.
"""
from repo_layout import repo_file
import argparse
from decimal import Decimal
import json
import sys

import bounded_reference_runner as controller
import frontier_reference as base

ROOT, BANK_HASH = base.ROOT, base.BANK_HASH
OUT = repo_file('runs/minimax_m3_none_deepinfra_1342_2026-10-19', root=ROOT)
MODEL = 'minimax/minimax-m3'
SNAPSHOT = 'minimax/minimax-m3-20260531'
SPEC = base.SPEC
GUARD = Decimal('1.00')
d, chat, file_hash = base.d, base.chat, base.file_hash
sanitize, parse = base.hygiene.sanitize_response, base.parse


def payload(q):
    return {'model': MODEL, 'messages': [{'role': 'user', 'content': base.render(q) + chat.SUFFIX}],
            'max_tokens': 16, 'stream': False, 'usage': {'include': True},
            'reasoning': {'enabled': False},
            'provider': {'only': ['deepinfra/fp8'], 'allow_fallbacks': False, 'require_parameters': True}}


def prepare():
    questions, old = base.prepare()
    plan = []
    for t in old:
        body = payload(questions[t['item_id']])
        plan.append({**t, 'model_id': 'minimax_m3_none', 'model_requested': MODEL,
                     'request_payload_sha256': d.digest(body), 'request_body_bytes': len(d.canonical(body))})
    return questions, plan


def reserve(task):
    return Decimal(task['request_body_bytes'] + 256) * Decimal('.00000028') + Decimal(16) * Decimal('.0000011')


def check_route(record):
    if record['status'] in ('transport_failure', 'http_failure', 'provider_error'):
        return
    assert record['provider'] == 'DeepInfra', 'Unexpected provider; no fallback'
    assert record['model_returned'] in (MODEL, SNAPSHOT), 'Unexpected model identity'
    assert record['reported_cost_usd'] is not None, 'Missing reported cost'
    assert record['reported_reasoning_tokens'] == 0 and not isinstance(record['reported_reasoning_tokens'], bool)
    assert not record['reasoning_text_present'] and record['status'] != 'unexpected_reasoning', 'No-thinking not verified'


def validate_probe(out):
    probe = json.loads((out / 'compatibility_probe.json').read_text())
    dispatch = json.loads((out / 'probe_dispatch.json').read_text())
    assert probe['payload'] == dispatch['payload'] and d.digest(probe['payload']) == dispatch['request_payload_sha256']
    expected = payload({'instructions': '', 'context': '', 'question': '', 'options': [''] * 5})
    assert {k:v for k,v in probe['payload'].items() if k != 'messages'} == {k:v for k,v in expected.items() if k != 'messages'}
    record = {**probe['transport'], **parse(probe['transport'])}
    check_route(record)
    assert record['status'] == 'ok' and record['choice'] == '3'
    return record


def probe_cost(out):
    validate_probe(out)
    probes=json.loads((out/'route_selection_probes.json').read_text())
    assert len(probes)==3
    assert all(parse(p['transport'])['reported_cost_usd'] is not None for p in probes)
    return sum((Decimal(str(parse(p['transport'])['reported_cost_usd'])) for p in probes),Decimal(0))


def software():
    return {**base.software(), **{n:file_hash(repo_file(n, root=ROOT)) for n in ('bounded_reference_runner.py', 'minimax_reference.py', 'test_minimax_reference.py')}}


def freeze(out, plan):
    metadata = json.loads((out/'model_metadata.json').read_text())['data']
    selected = [e for e in metadata['endpoints'] if e['tag'] == 'deepinfra/fp8' and e['status'] == 0]
    assert len(selected) == 1 and selected[0]['name'] == 'DeepInfra | ' + SNAPSHOT
    assert Decimal(selected[0]['pricing']['prompt']) == Decimal('.00000028')
    assert Decimal(selected[0]['pricing']['completion']) == Decimal('.0000011')
    assert {'reasoning','max_tokens'} <= set(selected[0]['supported_parameters'])
    validate_probe(out)
    settings = payload({'instructions': '', 'context': '', 'question': '', 'options': ['']*5})
    d.save_bound(out/'manifest.json', {'version':'minimax-m3-no-thinking-1342-v1',
        'model':MODEL, 'catalog_snapshot':SNAPSHOT, 'question_count':1342, 'bank_sha256':BANK_HASH,
        'endpoint':'https://'+SPEC['host']+SPEC['path'], 'settings':{k:v for k,v in settings.items() if k != 'messages'},
        'request_plan':plan, 'prompt':'Same questions, option order, numeric-only suffix and fixed shuffle as Sol; no answer keys',
        'concurrency':{'maximum':2,'questions_per_wave':2,'barrier':'Both calls settle before next wave'},
        'timing':'Unmodified fresh-HTTPS full-response monotonic timer from added_decisions.send',
        'retry':'One recovery for transport or HTTP408/429/5xx; never explanations, invalid decisions or wrong answers',
        'primary':'All 1342 first attempts, including failures; recovery outcomes supplementary',
        'reasoning':'reasoning.enabled=false; require explicit zero reasoning tokens and no reasoning content',
        'identity_limit':'Dated endpoint catalog and returned model, not immutable-weight attestation; FP8 route',
        'cost':'API-reported charges including recoveries; compatibility probe separate; unknown never zero',
        'soft_guard_usd':str(GUARD), 'guard_limit':'Local conservative byte-based guard, not a vendor spending cap',
        'development_policy':'Exploratory bank; retain 37 permanent author-development exclusions in separate diagnostic',
        'hyper_route_selection':'Hyper catalog supports low/medium/high only; no documented off mode. Three simple compatibility probes preceded the scored bank; choose DeepInfra FP8 by latency, never correctness on benchmark questions. Minimax and SambaNova probes retained separately, no silent fallback.',
        'sources':['https://platform.minimax.io/docs/api-reference/text-openai-api',
                   'https://openrouter.ai/api/v1/models/minimax/minimax-m3/endpoints']})
    d.save_bound(out/'software.json',software())


def sealed_files(out):
    return ['manifest.json','software.json','model_metadata.json','compatibility_probe.json','probe_dispatch.json','route_selection_probes.json',
            'dispatches.jsonl','attempts.jsonl','results.jsonl'] + (['retry_waits.jsonl'] if (out/'retry_waits.jsonl').exists() else [])


def validate(out, complete=False):
    _,plan = prepare()
    manifest = json.loads((out/'manifest.json').read_text())
    assert manifest['request_plan'] == plan and manifest['bank_sha256'] == BANK_HASH
    assert json.loads((out/'software.json').read_text()) == software()
    validate_probe(out)
    attempts,results,done = controller.ledger_state(sys.modules[__name__],out,plan)
    if complete:
        receipt=json.loads((out/'completion.json').read_text())
        assert receipt['status']=='COMPLETE_1342' and done==set(range(1,1343))
        assert all(file_hash(out/n)==h for n,h in receipt['files_sha256'].items())
    return attempts,results


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--execute',action='store_true');p.add_argument('--validate',action='store_true')
    args=p.parse_args();assert not (args.execute and args.validate)
    if args.execute:
        controller.execute(sys.modules[__name__],OUT)
    elif args.validate:
        a,r=validate(OUT,complete=True)
        print(json.dumps({'validation':'PASS','questions':len(r),'attempts':len(a),'paid_calls':0}))
    else:
        print(json.dumps({'mode':'DRY_RUN','model':MODEL,'questions':len(prepare()[1]),'paid_calls':0}))


if __name__=='__main__':
    main()
