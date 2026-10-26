"""Publish sanitized native-image compatibility evidence in both benchmarks.

Compatibility probes are separate from scored cases and their cost totals.
Only the already-authorized three probes are read; no inference calls occur.
"""
import argparse
from decimal import Decimal
from hashlib import sha256
import json
from pathlib import Path
import ssl
import urllib.request

import added_decisions as a
from overall_analysis import write, OVERALL


def main(image_repo):
    source_url = 'https://docs.bespokelabs.ai/api-reference/openapi.yaml'
    context = ssl.create_default_context(cafile='/etc/ssl/cert.pem')
    schema = urllib.request.urlopen(source_url, context=context, timeout=30).read()
    assert b'Nimble reads a JSON state as JSON text.' in schema
    records = [json.loads((a.RUNS / 'image_compatibility' / model / 'response.json').read_text()) for model in a.MODELS]
    by_id = {r['model_id']: r for r in records}
    assert by_id['microsoft_decision']['http_status'] == 400
    assert 'does not accept' in by_id['microsoft_decision']['raw_response']['error']['message']
    assert all(by_id[m]['http_status'] == 200 for m in ('nimble_v4', 'nimble_v4_max'))
    known_cost = sum((Decimal(str(r['accounted_cost_usd'])) for r in records if r['accounted_cost_usd'] is not None), Decimal(0))
    capability = {
        'review_date_toronto': '2026-10-16', 'checked': a.d.timestamps(),
        'scope': 'Current tested hosted routes and documented API contracts; not a claim about every base-model capability or future endpoint',
        'scored_image_questions_added': 0, 'native_image_compatibility_requests': 3,
        'image_score_policy': 'Not eligible for a native-image bank through these APIs; no zero score, image accuracy, image benchmark latency or 200-question cost assigned',
        'no_substitution': 'No OCR, captions, image modification or text-only substitute was used',
        'text_benchmark': 'https://github.com/etsabary/jev-1.14-comparison-benchmark',
        'nimble_contract': {
            'source': source_url, 'source_sha256': sha256(schema).hexdigest(),
            'documentation': 'https://docs.bespokelabs.ai/api-reference/systemone',
            'state_description_excerpt': 'Nimble reads a JSON state as JSON text.',
            'interpretation': 'The accepted image_url array is JSON text, not a documented image-decoding modality. HTTP 200 is not evidence of vision.',
            'identity_limit': 'The response model field repeats the requested model name; it does not independently attest a hidden checkpoint',
        },
        'models': {
            'microsoft_decision': {'label': 'Microsoft-Decision-1', 'route': 'OpenRouter/Azure',
                'image_status': 'native_image_input_rejected', 'probe_http_status': 400,
                'source': 'https://openrouter.ai/api/v1/models/microsoft/microsoft-decision-1/endpoints',
                'declared_input_modalities': ['text'], 'probe_error': by_id['microsoft_decision']['raw_response']['error']['message'],
                'accuracy': None, 'scheduled_image_cases': 0},
            **{model: {'label': a.MODELS[model]['label'], 'route': 'Bespoke direct',
                'image_status': 'image_shaped_json_read_as_text_by_documented_contract', 'probe_http_status': 200,
                'probe_input_tokens': by_id[model]['usage']['input_tokens'],
                'probe_confidence': by_id[model]['confidence'], 'source': source_url,
                'accuracy': None, 'scheduled_image_cases': 0} for model in ('nimble_v4', 'nimble_v4_max')},
        },
        'probe_cost': {'known_tariff_usd': str(known_cost),
                       'missing_charge_records': sum(r['accounted_cost_usd'] is None for r in records),
                       'included_in_scored_benchmark_costs': False},
    }
    write(OVERALL / 'image_capabilities.json', capability)
    write(image_repo / 'data/october_16_capabilities.json', capability)
    text = ''.join(json.dumps(r, ensure_ascii=False, allow_nan=False) + '\n' for r in records)
    (OVERALL / 'image_compatibility_probes.jsonl').write_text(text)
    (image_repo / 'data/october_16_compatibility_probes.jsonl').write_text(text)
    print(json.dumps({'models': 3, 'scored_image_cases_added': 0, 'probe_cost': capability['probe_cost']}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--image-repo', type=Path, required=True)
    main(parser.parse_args().image_repo)
