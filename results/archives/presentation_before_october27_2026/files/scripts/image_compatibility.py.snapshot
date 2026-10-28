"""Small native-image compatibility check, never a scored image benchmark.

Run only after the text measurements finish. Reuses a frozen image/question
without OCR, captions, answer feedback or altered options. Dry-run by default.
"""
import argparse
import base64
from hashlib import sha256
import json
from pathlib import Path

import added_decisions as a
from matched_analysis import sanitize_raw


def execute(args):
    root = args.image_repo
    questions = a.d.rows(root / 'data/questions.jsonl')
    question = next(q for q in questions if q['candidate_id'] == 'VB0001')
    assets = {v['asset_id']: v for v in a.d.rows(root / 'data/assets.jsonl')}
    images = []
    hashes = []
    for asset_id in question['asset_ids']:
        asset = assets[asset_id]
        data = (root / asset['path']).read_bytes()
        assert sha256(data).hexdigest() == asset['sha256']
        hashes.append(asset['sha256'])
        images.append({'type': 'image_url', 'image_url': {
            'url': 'data:' + asset['mime'] + ';base64,' + base64.b64encode(data).decode('ascii')}})
    spec = a.MODELS[args.model]
    body = {'model': spec['model'], 'state': images, 'questions': {'decision': {
        'type': 'choice', 'instructions': question['question'] + '\n\nRules: ' + question['rules'],
        'criteria': {o['id']: o['text'] for o in question['options']}}}}
    if spec['host'] == 'openrouter.ai':
        body['provider'] = {'only': [spec['provider_tag']], 'allow_fallbacks': False, 'require_parameters': True}
    out = a.RUNS / 'image_compatibility' / args.model
    out.mkdir(parents=True, exist_ok=True)
    manifest = {'model_id': args.model, 'model_requested': spec['model'], 'candidate_id': question['candidate_id'],
                'image_sha256': hashes, 'request_payload_sha256': a.d.digest(body),
                'request_body_bytes': len(a.d.canonical(body)), 'purpose': 'Compatibility only, not a scored bank run',
                'format': 'Exact original native image benchmark state/questions, plus fixed route for Microsoft',
                'software_sha256': sha256(Path(__file__).read_bytes()).hexdigest()}
    a.d.save_bound(out / 'manifest.json', manifest)
    if not args.execute:
        print(json.dumps({'mode': 'DRY_RUN', **manifest}))
        return
    assert not (out / 'dispatch.json').exists(), 'Do not repeat a potentially billed probe'
    assert all((a.RUNS / model / 'completion.json').exists() for model in a.MODELS), 'Finish all text measurements first'
    key = a.credentials()[spec['key_name']]
    assert key, 'Required API key missing'
    a.d.save_bound(out / 'dispatch.json', {'started': a.d.timestamps()})
    response = a.send(a.d.canonical(body), key, spec)
    record = {**manifest, **response, **a.parse(response, args.model)}
    record['raw_response'] = sanitize_raw(record['raw_response'])
    record['usage'] = record['raw_response'].get('usage') or {}
    a.d.save_bound(out / 'response.json', record)
    print(json.dumps({k: record[k] for k in ('model_id', 'http_status', 'status', 'model_returned', 'choice',
                      'cost_source', 'accounted_cost_usd', 'raw_response')}, ensure_ascii=False))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--image-repo', type=Path, required=True)
    parser.add_argument('--model', choices=a.MODELS, required=True)
    parser.add_argument('--execute', action='store_true')
    execute(parser.parse_args())
