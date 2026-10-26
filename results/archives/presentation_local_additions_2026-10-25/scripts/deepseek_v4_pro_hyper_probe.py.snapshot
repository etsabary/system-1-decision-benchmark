"""One journaled Hyper Charm V4 Pro non-thinking compatibility probe.

No scored questions, purchases, setting changes or retries. The Hyper catalog
does not advertise 'none' for this model: successful text alone cannot prove it.
"""
import json
import ssl
import urllib.request

import frontier_reference as base
import hyper_reference as hyper
from deepseek_v41_1017_reference import PROBE

MODEL = 'deepseek-v4-pro-0813'
OUT = base.ROOT / 'runs/deepseek_v4_pro_none_2026-10-23/hyper_probe'
SPEC = {'host': 'hyper.charm.land', 'path': '/v1/chat/completions'}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    metadata = OUT / 'model_metadata.json'
    if not metadata.exists():
        with urllib.request.urlopen('https://hyper.charm.land/v1/models',
                context=ssl.create_default_context(cafile='/etc/ssl/cert.pem'), timeout=30) as response:
            data = json.load(response)
        base.d.save_bound(metadata, {'retrieved': base.d.timestamps(), **data})
    model = [m for m in json.loads(metadata.read_text())['data'] if m['id'] == MODEL]
    assert len(model) == 1
    body = {'model': MODEL,
            'messages': [{'role': 'user', 'content': base.render(PROBE) + base.chat.SUFFIX}],
            'max_tokens': 16, 'stream': False, 'reasoning_effort': 'none',
            'thinking': {'type': 'disabled'}}
    target, dispatch = OUT / 'compatibility_probe.json', OUT / 'probe_dispatch.json'
    if not target.exists():
        assert not dispatch.exists(), 'Unresolved dispatch, do not replay'
        key = hyper.credentials(base.ROOT.parent.parent / 'the village 14947/.env')
        assert key, 'Hyper Charm credential not configured'
        base.d.save_bound(dispatch, {'payload': body, 'request_payload_sha256': base.d.digest(body),
                                   'dispatch': base.d.timestamps()})
        response = hyper.sanitize(base.transport.send(base.d.canonical(body), key, SPEC))
        base.d.save_bound(target, {'payload': body, 'transport': response})
    saved = json.loads(target.read_text())
    assert saved['payload'] == body
    record = hyper.parse(saved['transport'])
    print(json.dumps({'model': MODEL, 'catalog_reasoning': model[0].get('reasoning'),
                     'http_status': saved['transport']['http_status'],
                     'status': record['status'], 'choice': record['choice'],
                     'reasoning_tokens': record['reported_reasoning_tokens'],
                     'reasoning_text_present': record['reasoning_text_present'],
                     'latency_ms': saved['transport']['latency_ms'],
                     'cost_usd_equivalent': record['reported_cost_usd'],
                     'hypercredits': record['reported_hypercredits'],
                     'error': saved['transport']['raw_response'].get('error')}, indent=2))


if __name__ == '__main__':
    main()
