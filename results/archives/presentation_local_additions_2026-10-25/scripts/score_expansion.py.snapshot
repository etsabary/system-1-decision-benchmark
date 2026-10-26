"""Reproduce eleven-model accuracy with an external gold key, offline.

Only aggregate comparisons are returned. This script never publishes a key or
per-question correctness record, and never sends model requests.
"""
from repo_layout import repo_file
import argparse
from hashlib import sha256
import json
from pathlib import Path

from analysis_core import normalize, metrics, panels, panel_summary
from text_models import ROOT, EXPANSION, MODELS, HISTORICAL, rows, first_and_eventual, leading_id, read_csv


def normalized_llm(record):
    return {**record, 'normalized_status': record['status'], 'normalized_choice': record['choice'] or '',
            'normalized_confidence': None, 'probability_warning': ''}


def load_key(path):
    expected = json.loads((repo_file('data/baseline_reference_manifest.json', root=ROOT)).read_text())['key_sha256']
    if sha256(Path(path).read_bytes()).hexdigest() != expected:
        raise ValueError('Gold-key version does not match this frozen benchmark')
    records = read_csv(path)
    keys = {r['item_id']: r for r in records}
    if len(keys) != len(records):
        raise ValueError('Duplicate key item IDs')
    return keys


def score(key_path):
    keys = load_key(key_path)
    saved = json.loads((EXPANSION/'summary.json').read_text())
    metadata = {r['item_id']: r for r in read_csv(repo_file('data/item_metadata.csv', root=ROOT))}
    selection = json.loads((repo_file('data/selection_manifest.json', root=ROOT)).read_text())
    first, eventual = first_and_eventual(rows(EXPANSION/'attempts.jsonl'))
    records = {m: [normalize(r) for r in read_csv(repo_file('data', root=ROOT)/name)] for m, name in HISTORICAL.items()}
    records |= {m: [normalized_llm(r) for r in first.values() if r['model_requested'] == m] for m in MODELS}
    for m, rr in records.items():
        assert len(rr) == len({r['item_id'] for r in rr}) == 1136
        assert metrics(rr, keys) == saved['models'][m]['primary'], m
        assert panel_summary(panels(rr, keys, selection)) == saved['models'][m]['panels'], m
        for field in ('role', 'level'):
            for value, expected in saved['models'][m]['by_'+field].items():
                assert metrics([r for r in rr if metadata[r['item_id']][field] == value], keys) == expected
        for family in saved['by_family']:
            group = [r for r in rr if metadata[r['item_id']]['family_id'] == family['family_id']]
            assert metrics(group, keys) == family['models'][m], (m, family['family_id'])
        if m in MODELS:
            final = [normalized_llm(r) for r in eventual.values() if r['model_requested'] == m]
            assert metrics(final, keys) == saved['models'][m]['eventual']
            leading = sum(leading_id(r) == keys[r['item_id']]['gold_option'] for r in rr)
            assert leading == saved['models'][m]['format_sensitivity_POSTHOC']['leading_id_correct']
    print('PASS: external-key reproduction of all eleven primary scores, 25 families, roles, levels, matched panels, LLM recovery scores and post-hoc leading-ID scores; no API calls or per-item output')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--answer-key', type=Path, required=True)
    score(parser.parse_args().answer_key)
