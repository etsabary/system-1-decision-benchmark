"""Offline reconstruction and validation of the eight regular LLM runs.

No network operations, credentials or answer key are used by this module.
The original live execution is described by the frozen run manifest.
"""
from repo_layout import repo_file
from collections import Counter, defaultdict
from datetime import datetime
from decimal import Decimal
from hashlib import sha256
import json
import math
from pathlib import Path
import re

from run_benchmark import canonical_bytes, digest, read_csv

ROOT = Path(__file__).resolve().parents[1]
EXPANSION = repo_file('expansion_2026-10-15', root=ROOT)
MODELS = {
    'openai/gpt-6-luna': ('Luna 6 regular', 'openai', 'OpenAI', 'switchable'),
    'openai/gpt-5.4-nano': ('GPT-5.4 nano', 'openai', 'OpenAI', 'switchable'),
    'google/gemini-2.5-flash-lite': ('Gemini 2.5 Flash-Lite', 'google-ai-studio', 'Google AI Studio', 'switchable'),
    'ibm-granite/granite-4.2-8b': ('Granite 4.2 8B', 'deepinfra/bf16', 'DeepInfra', 'switchable'),
    'qwen/qwen3-30b-a3b-instruct-2507': ('Qwen3-30B-A3B Instruct 2507', 'siliconflow/fp8', 'SiliconFlow', 'nonthinking_checkpoint'),
    'microsoft/phi-4': ('Phi-4 14B', 'deepinfra/bf16', 'DeepInfra', 'ordinary_instruct'),
    'mistralai/mistral-nemo': ('Mistral NeMo 12B', 'deepinfra/fp8', 'DeepInfra', 'ordinary_instruct'),
    'inception/mercury-2.5': ('Mercury 2.5', 'inception', 'Inception', 'switchable'),
}
HISTORICAL = {'jev113': 'results_jev113.csv', 'jev114': 'results_jev114.csv', 'luna_decisions': 'results_luna.csv'}
SUFFIX = '\n\nReturn only the numeric option ID (1, 2, 3, 4 or 5), without explanation.'
ALLOWED = {'1', '2', '3', '4', '5'}
TRANSIENT = {408, 429, *range(500, 600)}


def rows(path):
    return [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]


def payload(question, model):
    label, pin, provider, kind = MODELS[model]
    body = {'model': model, 'messages': [{'role': 'user', 'content': question['prompt_text']+SUFFIX}],
            'max_tokens': 16, 'stream': False, 'usage': {'include': True},
            'provider': {'only': [pin], 'allow_fallbacks': False, 'require_parameters': True}}
    if kind == 'switchable':
        body['reasoning'] = {'enabled': False}
        if model != 'google/gemini-2.5-flash-lite':
            body['reasoning']['effort'] = 'none'
    return body


def number(value):
    return not isinstance(value, bool) and isinstance(value, (int, float)) and math.isfinite(value) and value >= 0


def parse(record):
    body = record.get('raw_response') or {}
    choices = body.get('choices', [])
    answer = choices[0] if isinstance(choices, list) and len(choices) == 1 and isinstance(choices[0], dict) else {}
    message = answer.get('message') or {}
    text = message.get('content')
    choice = text.strip() if isinstance(text, str) else None
    usable = record['http_status'] == 200 and not record['error'] and choice in ALLOWED and answer.get('finish_reason') == 'stop'
    usage = body.get('usage') or {}
    details = usage.get('completion_tokens_details') or {}
    return {'status': 'ok' if usable else 'http_failure' if record['http_status'] != 200 else 'refusal' if message.get('refusal') else 'invalid_output',
            'choice': choice if usable else None, 'output_text': text, 'finish_reason': answer.get('finish_reason'),
            'model_returned': body.get('model'), 'provider': body.get('provider'), 'request_id': body.get('id'),
            'usage': usage, 'reported_cost_usd': usage.get('cost') if number(usage.get('cost')) else None,
            'reported_reasoning_tokens': details.get('reasoning_tokens'),
            'reasoning_text_present': bool(message.get('reasoning') or message.get('reasoning_details'))}


def leading_id(record):
    """Post-hoc format sensitivity, not the primary scoring contract."""
    if record['http_status'] != 200 or record.get('error') or not isinstance(record.get('output_text'), str):
        return None
    match = re.match(r'^\s*([1-5])(?=$|\s|[.):])', record['output_text'])
    return match.group(1) if match else None


def quantiles(values):
    values = sorted(values)
    if not values:
        return {'n': 0, 'median_ms': None, 'p95_ms': None}
    def q(p):
        x = (len(values)-1)*p
        low = int(x)
        return values[low]+(values[min(low+1, len(values)-1)]-values[low])*(x-low)
    return {'n': len(values), 'median_ms': q(.5), 'p95_ms': q(.95)}


def money(records):
    values = [Decimal(str(r['reported_cost_usd'])) for r in records if r['reported_cost_usd'] is not None]
    value = sum(values, Decimal(0))
    return {'known_usd': float(value), 'exact_usd': str(value), 'reported_attempts': len(values),
            'missing_attempts': len(records)-len(values)}


def first_and_eventual(attempts):
    grouped = defaultdict(list)
    for a in attempts:
        grouped[a['request_index']].append(a)
    first, eventual = {}, {}
    for index, group in grouped.items():
        group.sort(key=lambda a: a['attempt'])
        assert [a['attempt'] for a in group] in ([1], [1, 2])
        if len(group) == 2:
            assert group[0]['transport_failure'] or group[0]['http_status'] in TRANSIENT
        first[index], eventual[index] = group[0], group[-1]
    return first, eventual


def historical_speeds():
    original = json.loads((repo_file('analysis/summary.json', root=ROOT)).read_text())
    result = {}
    for model, filename in HISTORICAL.items():
        records = read_csv(repo_file('data', root=ROOT)/filename)
        successful = [r for r in records if r['http_status'] == '200']
        group = 'luna' if model == 'luna_decisions' else model
        result[model] = {
            'full_bank_saved_latency_all_outcomes': quantiles([float(r['latency_ms']) for r in records if r.get('latency_ms') not in ('', None)]),
            'saved_successful_latency_all_records': quantiles([float(r['latency_ms']) for r in successful if r['latency_ms']]),
            'shared_136_extension_saved_latency': original['same_subset_body_latency'][group],
            'dates_toronto': original['test_dates_toronto'][group],
            'basis': 'Recorded historical latency_ms on successful responses, not re-timed or substituted',
            'route_note': 'Mixed TypeSafe direct, Experiential and OpenRouter routes' if model == 'jev113' else 'OpenRouter native Decisions',
            'comparison_limit': 'Different dates and timing boundaries; not a controlled speed ranking against the new LLM run',
        }
        if model != 'jev114':
            old = [r for r in successful if r.get('source_cohort') == 'historical_1000']
            result[model]['original_1000_saved_latency'] = quantiles([float(r['latency_ms']) for r in old])
            if model == 'jev113':
                result[model]['original_1000_openrouter_subset'] = quantiles([float(r['latency_ms']) for r in old if r['provider'] == 'openrouter'])
    return result


def validate():
    manifest = json.loads((EXPANSION/'run_manifest.json').read_text())
    summary = json.loads((EXPANSION/'summary.json').read_text())
    plan = rows(EXPANSION/'request_plan.jsonl')
    attempts = rows(EXPANSION/'attempts.jsonl')
    dispatches = rows(EXPANSION/'dispatches.jsonl')
    results = rows(EXPANSION/'results.jsonl')
    questions = {r['item_id']: r for r in read_csv(repo_file('data/questions_1136.csv', root=ROOT))}
    assert len(plan) == len(results) == 9088
    assert len(attempts) == len(dispatches) == 9096
    assert len({(p['item_id'], p['model_requested']) for p in plan}) == 9088
    assert Counter(p['model_requested'] for p in plan) == Counter({m: 1136 for m in MODELS})
    for name, expected in manifest['original_files_sha256'].items():
        assert sha256((repo_file('data', root=ROOT)/name).read_bytes()).hexdigest() == expected
    signatures = lambda rr: [(r['request_index'], r['attempt']) for r in rr]
    assert len(set(signatures(attempts))) == len(attempts)
    assert len(set(signatures(dispatches))) == len(dispatches)
    assert set(signatures(attempts)) == set(signatures(dispatches))
    assert len({r['request_index'] for r in results}) == 9088
    indexed = {p['request_index']: p for p in plan}
    for p in plan:
        body = payload(questions[p['item_id']], p['model_requested'])
        assert digest(body) == p['request_payload_sha256']
        assert digest(body['messages']) == p['message_sha256']
        assert len(canonical_bytes(body)) == p['request_body_bytes']
    for start in range(0, 9088, 8):
        assert len({p['message_sha256'] for p in plan[start:start+8]}) == 1
    identities = {}
    for a in attempts:
        p = indexed[a['request_index']]
        assert all(a[k] == p[k] for k in p)
        for k, value in parse(a).items():
            assert a[k] == value, k
        assert a['reported_reasoning_tokens'] in (None, 0) and not a['reasoning_text_present']
        if a['http_status'] == 200:
            m = a['model_requested']
            assert a['provider'] == MODELS[m][2]
            assert a['model_returned'] == m or a['model_returned'].startswith(m+'-')
            observed = (a['model_returned'], a['provider'])
            assert m not in identities or identities[m] == observed
            identities[m] = observed
    first, eventual = first_and_eventual(attempts)
    assert len(first) == 9088
    for terminal in results:
        i = terminal['request_index']
        assert terminal['first_status'] == first[i]['status']
        assert terminal['eventual_status'] == eventual[i]['status']
        assert terminal['attempts'] == eventual[i]['attempt']
    assert money(attempts) == summary['new_total_reported_cost']
    for m in MODELS:
        ff = [r for r in first.values() if r['model_requested'] == m]
        aa = [r for r in attempts if r['model_requested'] == m]
        d = summary['models'][m]
        assert money(aa) == d['cost_all_attempts']
        assert quantiles([r['latency_ms'] for r in ff]) == d['latency_first_all']
        assert Counter(r['status'] for r in ff) == d['statuses_first']
        assert sum(r['status'] == 'ok' for r in ff) == d['primary']['answered']
        assert d['primary']['correct']+d['primary']['wrong'] == d['primary']['answered']
        assert sum(f['models'][m]['correct'] for f in summary['by_family']) == d['primary']['correct']
    assert historical_speeds() == summary['historical_speeds']
    assert len(summary['models']) == 11 and summary['total_scored_model_questions'] == 12496
    print('PASS: 9,088 exact reconstructed requests; 9,096 sanitized attempts; first/recovery separation; identical LLM messages; identities; reported costs; new and historical timing arithmetic; no API calls')


if __name__ == '__main__':
    validate()
