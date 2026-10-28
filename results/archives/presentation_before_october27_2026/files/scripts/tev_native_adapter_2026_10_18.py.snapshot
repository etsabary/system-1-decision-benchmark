"""Tev1 through OpenRouter's native adapter, with the approved100-case screen.

Tev1 is a decision-specialized GENERATIVE model. Its own documentation describes
a next-token label head, while OpenRouter rejects its chat-completions route and
requires /api/alpha/decisions. This runner tests that provider adapter using the
unchanged native benchmark state/question/five criteria. It does not reclassify
the underlying architecture as non-generative or claim a hidden-reasoning audit.

The frozen chat runner is loaded in an isolated namespace. Its tested dispatch,
screen, retry and continuation machinery is reused without modifying its source
or the module state of any independently running ordinary-LLM process. No paid
call occurs without --probe or --execute; the answer key is never loaded here.
"""
from __future__ import annotations
from repo_layout import repo_file
from repo_layout import source_file

from hashlib import sha256
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location('_tev_native_screen_engine_20261018',
                                              source_file(repo_file('llm_field_2026_10_18.py', root=ROOT)))
engine = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(engine)
_base_source_hashes = engine.source_hashes
_base_sanitize = engine.sanitize_response
_base_validate_probe = engine.validate_probe

MODEL_ID = 'tev1_4b_native'
RUNS = repo_file('runs/tev_native_adapter_2026-10-18', root=ROOT)
MODELS = {MODEL_ID: {**engine.MODELS['tev1_4b'],
                    'label': 'Tev1 4B experimental (OpenRouter native adapter)',
                    'kind': 'decision_specialized_generative_native_adapter',
                    'path': '/api/alpha/decisions', 'max_tokens': None,
                    'architecture': 'Decision-specialized generative model with next-token label head',
                    'compatibility_limit': 'Native adapter selected after OpenRouter explicitly rejected chat endpoint'}}
d = engine.d
old = engine.old
chat = engine.chat
SCREEN_POLICY = engine.SCREEN_POLICY
SCREEN_SIZE = engine.SCREEN_SIZE
file_hash = engine.file_hash
bound_prefix = engine.bound_prefix
verify_prefixes = engine.verify_prefixes


def source_hashes():
    return {**_base_source_hashes(),
            Path(__file__).name: file_hash(Path(__file__)),
            'test_tev_native_adapter_2026_10_18.py': file_hash(source_file(repo_file('test_tev_native_adapter_2026_10_18.py', root=ROOT)))}


def payload(question, model_id=MODEL_ID):
    cfg = MODELS[model_id]
    return {'model': cfg['model'], **d.packet(question),
            'provider': {'only': [cfg['provider_tag']], 'allow_fallbacks': False,
                         'require_parameters': True}}


def prepare(model_id=MODEL_ID):
    cfg = MODELS[model_id]
    bank = repo_file('data/questions_1136.csv', root=ROOT)
    baseline = json.loads((repo_file('data/baseline_reference_manifest.json', root=ROOT)).read_text())
    assert file_hash(bank) == baseline['questions_sha256'], 'Frozen bank changed'
    questions = {q['item_id']: q for q in d.read_csv(bank)}
    order = list(dict.fromkeys(r['item_id'] for r in d.rows(repo_file('expansion_2026-10-15/request_plan.jsonl', root=ROOT))))
    assert len(questions) == len(order) == 1136 and set(order) == set(questions)
    plan = []
    for position, item_id in enumerate(order):
        q = questions[item_id]
        original = {k: q[k] for k in ('instructions', 'context', 'question')}
        original['options'] = [q[f'option_{i}'] for i in range(1, 6)]
        assert d.digest(original) == q['prompt_sha256']
        body = payload(q, model_id)
        plan.append({'request_index': position + 1, 'wave': position // 2 + 1,
                     'item_id': item_id, 'model_id': model_id, 'model_requested': cfg['model'],
                     'prompt_sha256': q['prompt_sha256'], 'native_input_sha256': d.digest(d.packet(q)),
                     'request_payload_sha256': d.digest(body),
                     'request_body_bytes': len(d.canonical(body))})
    return questions, plan


def freeze(model_id, out, plan):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    cfg = MODELS[model_id]
    d.save_bound(out / 'manifest.json', {
        'version': 'october-18-tev-generative-native-adapter-screen-v1',
        'model_id': model_id, 'model': cfg, 'question_count': 1136,
        'screen_question_count': SCREEN_SIZE,
        'questions_sha256': file_hash(repo_file('data/questions_1136.csv', root=ROOT)),
        'reference_order_sha256': file_hash(repo_file('expansion_2026-10-15/request_plan.jsonl', root=ROOT)),
        'endpoint': 'https://openrouter.ai/api/alpha/decisions',
        'classification': 'Decision-specialized generative model via OpenRouter native adapter',
        'architecture_limit': 'A typed native response does not prove a non-generative underlying model or audit hidden internal processing',
        'prompt': 'Exact original native state, instructions, question and five criteria; only model/provider routing added',
        'question_order': 'Exact saved eight-LLM bank order; first100 fixed sequential items, not an independent balanced sample',
        'max_tokens': None,
        'output_cap_limit': 'No chat max_tokens field is sent to the native API; endpoint metadata advertises max_completion_tokens8',
        'reasoning': 'No chain of thought requested; native API returns typed decision fields, not a verified internal-reasoning toggle',
        'temperature': 'Native API; no chat temperature parameter',
        'concurrency': {'maximum_per_model': 2, 'questions_per_wave': 2,
                        'barrier': 'Both cases settle before the next independent wave'},
        'timing': 'Unmodified added_decisions.send; fresh HTTPS connection, monotonic connect through complete body; preparation/queue/retry wait excluded',
        'connect_timeout_seconds': 10, 'total_response_timeout_seconds': 90,
        'retry': 'At most one recovery for transport failure or actualHTTP408/429/5xx; no retries of invalid answers, incorrect valid answers or HTTP200 provider envelopes',
        'primary': 'First attempts; full1136 denominator only after completion; stopped screens labelled partial',
        'probe': 'Separate unscored native compatibility call; failed chat probe remains separate original evidence',
        'screen_policy': {'id': SCREEN_POLICY, 'fixed_cases': SCREEN_SIZE,
                          'hold_if_accuracy_below': .5,
                          'hold_if_model_output_failures_fraction_at_least': .05,
                          'hold_if_first_attempt_median_ms_above': 2000,
                          'accuracy_evaluation': 'Separate offline controller only, never this executor',
                          'continuation': 'External checksum-bound receipt required for remaining1036'},
        'choice_parser': 'Strict native choice1-5; probability rounding/confidence warnings retained without invalidating a valid choice',
        'identity_limit': 'Pinned Together endpoint and captured dated metadata; returned aliases do not independently attest weights',
        'cost': 'API-reported only; missing charges unknown; compatibility and primary/recovery separated',
        'known_spend_guard_usd': str(engine.GUARD),
        'guard_limit': 'Soft pre-dispatch guard, not a hard billing cap with unknown/in-flight charges',
        'request_plan': plan,
    })
    d.save_bound(out / 'software.json', source_hashes())


def validate_metadata(data, model_id=MODEL_ID):
    cfg = MODELS[model_id]
    endpoints = [e for e in data.get('endpoints', [])
                 if e.get('tag') == cfg['provider_tag'] and e.get('status') == 0
                 and not e.get('service_tier')]
    assert len(endpoints) == 1, 'Expected exactly one pinned active Together endpoint'
    endpoint = endpoints[0]
    assert endpoint['name'] == 'Together | ' + cfg['snapshot']
    assert endpoint['provider_name'] == 'Together'
    assert engine.Decimal(endpoint['pricing']['prompt']) * 10**6 == engine.Decimal('0.042')
    assert engine.Decimal(endpoint['pricing']['completion']) == 0
    assert 'text' in data['architecture']['input_modalities']
    assert 'decisions' in data['architecture']['output_modalities']
    return endpoint


def sanitize_response(response):
    clean = _base_sanitize(response)
    original = response.get('raw_response')
    original = original if isinstance(original, dict) else {}
    raw = clean['raw_response']
    answers = original.get('answers')
    if isinstance(answers, dict):
        decision = answers.get('decision')
        if isinstance(decision, dict):
            raw['answers'] = {'decision': {k: decision[k] for k in ('choice', 'confidence', 'probabilities') if k in decision}}
        else:
            raw['answers'] = {'decision': None}
    for field in ('reasoning', 'reasoning_content'):
        if original.get(field):
            raw[field] = original[field]
    if original.get('reasoning_details'):
        raw['reasoning_details'] = [{'type': 'present_redacted'}]
    usage = original.get('usage')
    if isinstance(usage, dict):
        raw.setdefault('usage', {}).update({k: usage[k] for k in ('input_tokens', 'output_tokens') if k in usage})
    return clean


def parse(response, model_id=MODEL_ID):
    raw = response.get('raw_response')
    raw = raw if isinstance(raw, dict) else {}
    # The frozen native parser tolerates probability rounding; normalize malformed
    # envelope shapes before invoking it rather than inferring an answer.
    normalized = {**response, 'raw_response': raw}
    parsed = d.parse(normalized)
    usage = parsed['usage']
    details = usage.get('completion_tokens_details')
    details = details if isinstance(details, dict) else {}
    reasoning_tokens = details.get('reasoning_tokens')
    reasoning_text = bool(raw.get('reasoning') or raw.get('reasoning_content') or raw.get('reasoning_details'))
    provider_failure = bool(response.get('transport_failure') or response.get('error') or
                            response.get('http_status') != 200 or raw.get('error'))
    if provider_failure:
        parsed.update(status='transport_failure' if response.get('transport_failure') else
                      'http_failure' if response.get('http_status') != 200 else 'provider_error', choice=None)
    elif reasoning_text or (reasoning_tokens is not None and
                            (isinstance(reasoning_tokens, bool) or reasoning_tokens != 0)):
        parsed.update(status='unexpected_reasoning', choice=None)
    cost = parsed['reported_cost_usd']
    return {**parsed, 'accounted_cost_usd': cost,
            'cost_source': 'api_reported' if cost is not None else 'unreported',
            'finish_reason': None, 'output_text': None,
            'reasoning_text_present': reasoning_text, 'reported_reasoning_tokens': reasoning_tokens,
            'model_output_failure': not provider_failure and parsed['status'] != 'ok'}


def validate_probe(model_id, out, require_compatible=True):
    record = _base_validate_probe(model_id, out, require_compatible=False)
    if require_compatible:
        assert record['status'] in ('ok', 'invalid_answer'), 'Native adapter compatibility failed'
        engine.check_identity(record)
    return record


engine.MODELS = MODELS
engine.RUNS = RUNS
engine.payload = payload
engine.prepare = prepare
engine.freeze = freeze
engine.source_hashes = source_hashes
engine.validate_metadata = validate_metadata
engine.sanitize_response = sanitize_response
engine.parse = parse
engine.validate_probe = validate_probe

# Stable surface for the separate offline controller. Its invoke function must
# target this adapter script, not the frozen ordinary-chat script.
capture_metadata = engine.capture_metadata
check_identity = engine.check_identity
retryable = engine.retryable
ledger_state = engine.ledger_state
write_screen = engine.write_screen
authorize_continuation = engine.authorize_continuation
probe = engine.probe
validate = engine.validate
execute = engine.execute


if __name__ == '__main__':
    engine.main()
