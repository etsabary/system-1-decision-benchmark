"""Answer-blind DeepSeek V4 Pro 0813 reasoning-none reference, 1,342 questions.

OpenRouter -> DeepInfra FP8 is pinned, with no fallback. Hyper Charm's separate
synthetic probe returned reasoning despite both explicit off switches; never pool
it with this route. Dry-run by default. Runtime evidence stays ignored by Git.
"""
from __future__ import annotations

import argparse
from decimal import Decimal
import json
import ssl
import sys
import urllib.request

import bounded_reference_runner as controller
import frontier_reference as base
from deepseek_v41_1017_reference import PROBE

ROOT, BANK_HASH = base.ROOT, base.BANK_HASH
MODEL = 'deepseek/deepseek-v4-pro-0813'
SNAPSHOT = 'deepseek/deepseek-v4-pro-20260813'
OUT = ROOT / 'runs/deepseek_v4_pro_none_2026-10-23/deepinfra'
SPEC = {'host': 'openrouter.ai', 'path': '/api/v1/chat/completions'}
GUARD = Decimal('2.00')
d, chat, file_hash, parse = base.d, base.chat, base.file_hash, base.parse
sanitize = base.hygiene.sanitize_response


def payload(q):
    return {'model': MODEL, 'messages': [{'role': 'user', 'content': base.render(q) + chat.SUFFIX}],
            'max_tokens': 16, 'stream': False, 'usage': {'include': True},
            'reasoning': {'enabled': False, 'effort': 'none'},
            'provider': {'only': ['deepinfra/fp8'], 'allow_fallbacks': False, 'require_parameters': True}}


def prepare():
    questions, old = base.prepare()
    plan = []
    for task in old:
        body = payload(questions[task['item_id']])
        plan.append({**task, 'model_id': 'deepseek_v4_pro_0813_none_deepinfra', 'model_requested': MODEL,
                     'message_sha256': d.digest(body['messages']),
                     'request_payload_sha256': d.digest(body), 'request_body_bytes': len(d.canonical(body))})
    return questions, plan


def check_route(record):
    if record['status'] in ('transport_failure', 'http_failure', 'provider_error'):
        return
    assert record['provider'] == 'DeepInfra', 'Unexpected backend; no silent fallback'
    assert record['model_returned'] in (MODEL, SNAPSHOT), 'Unexpected model/update identity'
    assert record['reported_cost_usd'] is not None, 'Success omitted API-reported charge'
    assert record['reported_reasoning_tokens'] == 0 and not isinstance(record['reported_reasoning_tokens'], bool), 'Reasoning tokens are not explicitly zero'
    assert not record['reasoning_text_present'] and record['status'] != 'unexpected_reasoning', 'No-reasoning contract violated or unverified'


def capture_metadata(out):
    path = out / 'model_metadata.json'
    if not path.exists():
        with urllib.request.urlopen('https://openrouter.ai/api/v1/models/' + MODEL + '/endpoints',
                context=ssl.create_default_context(cafile='/etc/ssl/cert.pem'), timeout=30) as response:
            data = json.load(response)
        d.save_bound(path, {'retrieved': d.timestamps(), **data})
    data = json.loads(path.read_text())['data']
    assert data['id'] == MODEL
    selected = [e for e in data['endpoints'] if e['tag'] == 'deepinfra/fp8' and e['status'] == 0 and not e.get('service_tier')]
    assert len(selected) == 1 and selected[0]['name'] == 'DeepInfra | ' + SNAPSHOT
    assert {'max_tokens', 'reasoning'} <= set(selected[0]['supported_parameters'])
    assert Decimal(selected[0]['pricing']['prompt']) == Decimal('.0000013')
    assert Decimal(selected[0]['pricing']['completion']) == Decimal('.0000026')
    return selected[0]


def probe(out):
    out.mkdir(parents=True, exist_ok=True)
    capture_metadata(out)
    target, dispatch = out / 'compatibility_probe.json', out / 'probe_dispatch.json'
    body = payload(PROBE)
    if not target.exists():
        assert not dispatch.exists(), 'Unresolved probe dispatch; do not replay'
        key = d.api_key(ROOT.parent / 'jev/.env')
        assert key
        d.save_bound(dispatch, {'payload': body, 'request_payload_sha256': d.digest(body), 'dispatch': d.timestamps()})
        response = sanitize(base.transport.send(d.canonical(body), key, SPEC))
        d.save_bound(target, {'payload': body, 'transport': response})
    saved = json.loads(target.read_text())
    record = {**saved['transport'], **parse(saved['transport'])}
    print(json.dumps({k: record.get(k) for k in ('http_status', 'status', 'choice', 'reported_reasoning_tokens',
          'reasoning_text_present', 'reported_cost_usd', 'latency_ms', 'provider', 'model_returned')}, indent=2), flush=True)
    validate_probe(out)


def validate_probe(out):
    saved = json.loads((out / 'compatibility_probe.json').read_text())
    dispatch = json.loads((out / 'probe_dispatch.json').read_text())
    assert saved['payload'] == payload(PROBE) == dispatch['payload']
    assert dispatch['request_payload_sha256'] == d.digest(saved['payload'])
    record = {**saved['transport'], **parse(saved['transport'])}
    check_route(record)
    assert record['status'] == 'ok' and record['choice'] == '3'
    return record


def probe_cost(out):
    return Decimal(str(validate_probe(out)['reported_cost_usd']))


def software():
    names = ('deepseek_v4_pro_reference.py', 'test_deepseek_v4_pro_reference.py',
             'deepseek_v41_1017_reference.py', 'bounded_reference_runner.py', 'frontier_reference.py',
             'added_decisions.py', 'decision_refresh.py', 'text_models.py', 'llm_field_2026_10_18.py',
             'run_benchmark.py', 'repo_layout.py')
    return {name: file_hash(ROOT / 'scripts' / name) for name in names}


def freeze(out, plan):
    out.mkdir(parents=True, exist_ok=True)
    endpoint = capture_metadata(out)
    validate_probe(out)
    d.save_bound(out / 'manifest.json', {
        'version': 'deepseek-v4-pro-0813-reasoning-none-1342-v1', 'model': MODEL,
        'catalog_snapshot': SNAPSHOT, 'route': 'OpenRouter -> DeepInfra FP8', 'captured_endpoint': endpoint,
        'bank_sha256': BANK_HASH, 'question_count': 1342,
        'settings': {k: v for k, v in payload(PROBE).items() if k != 'messages'},
        'prompt': 'Unchanged frozen1342 question text, five choices, numeric-ID-only suffix and seeded Sol order; no tools,16 output tokens',
        'no_reasoning': 'reasoning.enabled=false and effort=none; every successful response must explicitly report0 reasoning tokens and no reasoning content',
        'identity_limit': 'Dated0813 route and provider metadata; returned alias is not immutable-weight attestation',
        'concurrency': {'maximum': 2, 'questions_per_wave': 2, 'barrier': True},
        'timing': 'Unmodified fresh-HTTPS/full-body timer, no local preparation/queue/retry waits',
        'primary': 'All1342 first attempts; unusable responses unsuccessful, no answer-dependent retries',
        'retry': 'At most1 recovery for transport failure or HTTP408/429/5xx; no retries for wrong valid answers, explanations, truncation or refusals',
        'screening': {'initial_questions': 100, 'minimum_accuracy': .5, 'maximum_invalid_fraction': .05, 'maximum_median_ms': 2000,
                      'policy': 'Pause at100 for offline screening; then inspect additional100-question checkpoints for compliance and cumulative speed'},
        'cost': 'API-reported charges including recovery attempts; compatibility probes separate; missing never zero',
        'soft_cost_guard_usd': str(GUARD), 'request_plan': plan,
        'development_policy': 'Same exploratory bank;37 author-development exclusions retained in separate1305 diagnostic',
        'hyper_probe': 'Separate unscored Hyper Charm probe returned60 reasoning tokens despite requested none and thinking disabled; route rejected',
        'sources': ['https://api-docs.deepseek.com/api/create-chat-completion/',
                    'https://openrouter.ai/deepseek/deepseek-v4-pro-0813']})
    d.save_bound(out / 'software.json', software())


def reserve(task):
    return Decimal(task['request_body_bytes'] + 256) * Decimal('.0000013') + Decimal(16) * Decimal('.0000026')


def sealed_files(out):
    names = ['manifest.json', 'software.json', 'model_metadata.json', 'compatibility_probe.json',
             'probe_dispatch.json', 'dispatches.jsonl', 'attempts.jsonl', 'results.jsonl']
    if (out / 'retry_waits.jsonl').exists():
        names.append('retry_waits.jsonl')
    return names


def validate(out, complete=False):
    _, plan = prepare()
    manifest = json.loads((out / 'manifest.json').read_text())
    assert manifest['request_plan'] == plan and manifest['bank_sha256'] == BANK_HASH
    assert json.loads((out / 'software.json').read_text()) == software(), 'Frozen execution software changed'
    validate_probe(out)
    attempts, results, done = controller.ledger_state(sys.modules[__name__], out, plan)
    if complete:
        receipt = json.loads((out / 'completion.json').read_text())
        assert receipt['status'] == 'COMPLETE_1342' and done == set(range(1, 1343))
        assert all(file_hash(out / n) == h for n, h in receipt['files_sha256'].items())
    return attempts, results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group()
    action.add_argument('--probe', action='store_true')
    action.add_argument('--execute', action='store_true')
    action.add_argument('--validate', action='store_true')
    parser.add_argument('--waves', type=int, default=0)
    args = parser.parse_args()
    assert args.waves >= 0
    if args.probe:
        probe(OUT)
    elif args.execute:
        assert args.waves and args.waves <= 50, 'Dispatch at most100 questions before checkpoint review'
        controller.execute(sys.modules[__name__], OUT, args.waves)
    elif args.validate:
        attempts, results = validate(OUT, complete=True)
        print(json.dumps({'validation': 'PASS', 'questions': len(results), 'attempts': len(attempts), 'paid_calls': 0}))
    else:
        print(json.dumps({'mode': 'DRY_RUN', 'model': MODEL, 'questions': len(prepare()[1]), 'paid_calls': 0}))


if __name__ == '__main__':
    main()
