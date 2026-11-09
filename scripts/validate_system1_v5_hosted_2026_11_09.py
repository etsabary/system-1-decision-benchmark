"""Validate new hosted results against the immutable provisional v5 bank."""
import argparse
import collections
import gzip
import html
import json
import re
import statistics
import xml.etree.ElementTree as ET
from decimal import Decimal
from pathlib import Path
from urllib.parse import unquote, urlsplit

import validate_system1_v5_provisional_2026_11_09 as base


NEW_MODELS = {'morph_reflex', 'reax_1_3'}


def indexed(path, fields):
    records = base.rows(path)
    result = {tuple(r[f] for f in fields): r for r in records}
    assert len(result) == len(records), ('Duplicate records', path)
    return records, result


def validate(dest, prior, mirror=None):
    repo = Path(__file__).resolve().parents[1]
    base.validate(prior, repo / 'results/releases/system1_v4_openai_2026-11-06')
    manifest = base.check_manifest(dest)
    assert manifest['frozen_v5_manifest_sha256'] == base.sha(prior / 'manifest.json')
    old, new = base.load(prior / 'statistics.json'), base.load(dest / 'statistics.json')
    old_cost = base.load(prior / 'cost_statistics.json')['models']
    costs = base.load(dest / 'cost_statistics.json')['models']
    assert set(new['models']) == set(old['models']) | NEW_MODELS
    assert len(new['models']) == 34 and set(costs) == set(new['models'])
    assert new['questions'] == 1456 and new['categories'] == 43
    assert new['minimum_overall_accuracy'] == .45
    assert new['inclusion_threshold'] == old['inclusion_threshold']
    assert all(new['models'][m] == old['models'][m] and costs[m] == old_cost[m] for m in old['models'])
    unchanged = ['questions_1456.jsonl', 'source_metadata_1456.jsonl', 'category_guide.json',
                 'selection_provenance.json', 'removed_items.csv', 'retained_items.csv',
                 'removed_correctness_evidence.csv.gz', 'SOURCE_AND_LICENSES.md', 'PROJECT_LICENSE_MIT.txt']
    for name in unchanged:
        assert (dest / name).read_bytes() == (prior / name).read_bytes(), name
    assert (dest / 'baseline_v5_audit_receipt.json').read_bytes() == (prior / 'audit_receipt.json').read_bytes()
    receipt = base.load(dest / 'audit_receipt.json')
    assert receipt['source_manifest_sha256'] == base.sha(prior / 'manifest.json')
    questions = {q['id']: q for q in base.jsonlines(dest / 'questions_1456.jsonl')}
    assert len(questions) == 1456
    families = collections.Counter(q['family_id'] for q in questions.values())
    assert len(families) == 43 and min(families.values()) > 0
    ledger_names = ['timing_evidence.csv.gz', 'cost_evidence.csv.gz', 'correctness_evidence.csv.gz', 'all_category_scores.csv']
    ledgers = {}
    for name in ledger_names:
        before = gzip.decompress((prior / name).read_bytes()) if name.endswith('.gz') else (prior / name).read_bytes()
        after = gzip.decompress((dest / name).read_bytes()) if name.endswith('.gz') else (dest / name).read_bytes()
        assert after.startswith(before), ('Historical CSV records changed', name)
        fields = ('model_id', 'family_id') if name == 'all_category_scores.csv' else ('model_id', 'item_id')
        rr, index = indexed(dest / name, fields)
        expected = 34 * (43 if name == 'all_category_scores.csv' else 1456)
        assert len(rr) == len(index) == expected, name
        ledgers[name] = (rr, index)
    timing = ledgers['timing_evidence.csv.gz'][1]
    cost_rows, cost_index = ledgers['cost_evidence.csv.gz']
    flags = ledgers['correctness_evidence.csv.gz'][1]
    category = ledgers['all_category_scores.csv'][1]
    audits = base.load(dest / 'hosted_model_audits.json')
    assert set(audits) == NEW_MODELS
    for mid in NEW_MODELS:
        m, audit = new['models'][mid], audits[mid]
        assert m['n'] == audit['n'] == 1456 and audit['complete'] and not audit['pending']
        assert audit['output_tokens'] == 0
        rr = [flags[mid, item] for item in questions]
        correct = sum(base.boolean(r['correct']) for r in rr)
        usable = sum(base.boolean(r['usable']) for r in rr)
        assert correct == m['correct'] == audit['correct'] and usable == m['valid'] == audit['valid']
        base.close(m['accuracy'], correct / 1456)
        base.close(m['coverage'], usable / 1456)
        base.close(m['answer_accuracy_among_usable'], correct / usable)
        base.close(m['accuracy_upper_if_all_unusable_correct'], (correct + 1456 - usable) / 1456)
        all_latencies = []
        for item, q in questions.items():
            t, c, f = timing[mid, item], cost_index[mid, item], flags[mid, item]
            assert t['family_id'] == c['family_id'] == f['family_id'] == q['family_id']
            assert t['input_sha256'] == c['input_sha256'] == q['native_input_sha256']
            assert t['source_record_sha256'] == c['source_record_sha256']
            assert re.fullmatch('[0-9a-f]{64}', t['source_record_sha256'])
            assert t['status'] == c['status']
            assert base.boolean(f['usable']) == (t['status'] == 'ok')
            assert not base.boolean(f['correct']) or base.boolean(f['usable'])
            assert t['output_counter'] in ('', '0')
            latency = float(t['latency_ms'])
            assert latency >= 0
            all_latencies.append(latency)
        for field, expected in [('mean_ms', statistics.mean(all_latencies)), ('median_ms', statistics.median(all_latencies)), ('p95_ms', base.q95(all_latencies))]:
            base.close(m[field], expected)
            base.close(audit[field], expected)
        for fid, total in families.items():
            ids = [item for item, q in questions.items() if q['family_id'] == fid]
            row = category[mid, fid]
            n_correct = sum(base.boolean(flags[mid, item]['correct']) for item in ids)
            assert int(row['n']) == total and int(row['correct']) == n_correct
            base.close(row['accuracy'], n_correct / total)
            values = [float(timing[mid, item]['latency_ms']) for item in ids]
            for field, expected in [('mean_ms', statistics.mean(values)), ('median_ms', statistics.median(values)), ('p95_ms', base.q95(values))]:
                base.close(row[field], expected)
        base.close(m['macro_category_accuracy'], statistics.mean(float(category[mid, fid]['accuracy']) for fid in families))
    ranked = sorted((mid for mid, m in new['models'].items() if m['correct'] * 100 >= 45 * 1456), key=lambda mid: (-new['models'][mid]['correct'], mid))
    assert ranked == new['ranked_model_ids'] and len(ranked) == 28
    assert [m for m in ranked if m in old['ranked_model_ids']] == old['ranked_model_ids']
    assert set(new['below_cutoff']) == set(new['models']) - set(ranked)
    assert len(new['below_cutoff']) == 6
    morph_rows = [r for r in cost_rows if r['model_id'] == 'morph_reflex']
    morph = costs['morph_reflex']
    assert all(r['evidence_kind'] == 'reported' and r['reported_usd'] and not r['tariff_estimate_usd'] for r in morph_rows)
    morph_total = sum((Decimal(r['reported_usd']) for r in morph_rows), Decimal(0))
    assert Decimal(morph['reported_subtotal_usd']) == Decimal(morph['known_subtotal_usd']) == morph_total
    assert morph['reported_count'] == morph['n'] == 1456 and morph['unknown_count'] == 0
    assert Decimal(morph['known_usd_per_1000']) == morph_total * 1000 / 1456
    native_rows, native = indexed(dest / 'native_currency_cost_evidence.csv.gz', ('model_id', 'item_id'))
    assert len(native_rows) == 1456 and {r['model_id'] for r in native_rows} == {'reax_1_3'}
    fx = base.load(dest / 'fx_receipt.json')
    assert fx['date'] == '2026-11-09' and fx['rate_usd_per_eur'] == '1.1193'
    xml = dest / fx['xml_filename']
    assert base.sha(xml) == fx['xml_sha256']
    xml_root = ET.fromstring(xml.read_bytes())
    assert any(x.attrib.get('time') == fx['date'] for x in xml_root.iter())
    assert any(x.attrib.get('currency') == 'USD' and x.attrib.get('rate') == fx['rate_usd_per_eur'] for x in xml_root.iter())
    rate = Decimal(fx['rate_usd_per_eur'])
    nanos, fx_total, converted = 0, Decimal(0), 0
    for row in native_rows:
        key = row['model_id'], row['item_id']
        c, t = cost_index[key], timing[key]
        assert all(row[f] == c[f] == t[f] for f in ['input_sha256', 'source_record_sha256', 'status'])
        assert row['reported_currency'] == 'EUR'
        assert row['fx_rate_usd_per_eur'] == fx['rate_usd_per_eur'] and row['fx_date'] == fx['date']
        assert row['fx_receipt_sha256'] == base.sha(dest / 'fx_receipt.json')
        assert not c['reported_usd'] and not c['tariff_estimate_usd']
        if row['reported_amount_nanos']:
            amount = int(row['reported_amount_nanos'])
            assert amount >= 0
            eur = Decimal(amount) / Decimal(1000000000)
            usd = eur * rate
            assert Decimal(row['reported_amount_eur']) == eur and Decimal(row['fx_estimate_usd']) == usd
            assert c['evidence_kind'] == row['evidence_kind'] == 'fx_conversion_estimate'
            nanos += amount
            fx_total += usd
            converted += 1
        else:
            assert c['evidence_kind'] == row['evidence_kind'] == 'unknown'
    reax = costs['reax_1_3']
    assert reax['fx_estimate_count'] == reax['native_reported_count'] == converted
    assert reax['unknown_count'] == 1456 - converted
    assert reax['reported_count'] == reax['tariff_estimate_count'] == 0
    assert reax['native_reported_currency'] == 'EUR'
    assert int(reax['native_reported_subtotal_nanos']) == nanos
    assert Decimal(reax['native_reported_subtotal']) == Decimal(nanos) / Decimal(1000000000)
    assert reax['cost_basis'] == 'fx_conversion_estimate'
    assert Decimal(reax['fx_estimate_subtotal_usd']) == Decimal(reax['known_subtotal_usd']) == Decimal(reax['estimate_only_subtotal_usd']) == fx_total
    assert Decimal(reax['known_usd_per_1000']) == fx_total * 1000 / 1456
    page, readme = (dest / 'report.html').read_text(), (dest / 'README_V5.md').read_text()
    assert '45%' in page and '1,456' in page and 'FX est.' in page and 'FX est.' in readme
    assert 'reported' in page and 'EUR' in page and 'Terra' in page
    assert page.index('comparison_accuracy.png') < page.index('class="comparison-table"')
    desktop = re.search(r'<div class="comparison-table">.*?</table>', page, re.S).group()
    desktop_ids = re.findall(r'data-overall-model="([^"]+)"', desktop)
    mobile_ids = re.findall(r'<article class="mobile-card" data-overall-model="([^"]+)"', page)
    assert desktop_ids == mobile_ids == ranked
    assert 'Model-selected choices and the gold scoring key remain private.' in readme
    assert 'validate_system1_v5_hosted_2026_11_09.py' in readme
    scope_note = (dest / 'V5_SELECTION_NOTES.md').read_text()[:1000]
    assert scope_note.lower().startswith('# historical initial v5 selection notes only')
    assert '34' in scope_note and '28' in scope_note and 'HOSTED_MODEL_NOTES.md' in scope_note
    for mid in ranked:
        match = re.search(r'<tr[^>]*data-overall-model="' + re.escape(mid) + r'"[^>]*>(.*?)</tr>', page, re.S)
        assert match, mid
        row = match.group(1)
        assert f'{new["models"][mid]["accuracy"]:.2%}' in row
        assert row.count('data-cost-band=') == 2 and row.count('data-speed-band=') == 2
    for document in dest.rglob('*'):
        if document.suffix in {'.json', '.jsonl', '.md', '.csv', '.html'}:
            text = document.read_text()
            assert '/Users/' not in text and '"expected_answer"' not in text and '"gold_answer"' not in text, document
    for target in re.findall(r'(?:href|src)="([^"]+)"', page):
        path = urlsplit(html.unescape(target))
        if not path.scheme and not path.netloc and path.path:
            assert (dest / unquote(path.path)).exists(), target
    base.check_markdown_links(dest)
    if mirror:
        assert {str(p.relative_to(mirror)) for p in mirror.rglob('*') if p.is_file()} == {str(p.relative_to(dest)) for p in dest.rglob('*') if p.is_file()}
        for p in dest.rglob('*'):
            if p.is_file():
                assert p.read_bytes() == (mirror / p.relative_to(dest)).read_bytes(), p
        base.check_markdown_links(mirror)
    print('PASS: hosted provisional v5; 34 complete / 28 qualifying; frozen 1,456 inputs; 49,504 records; original32 unchanged; EUR receipts and USD FX estimates distinct; source, timing, costs, links and mirror verified.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('release', type=Path)
    parser.add_argument('prior', type=Path)
    parser.add_argument('--mirror', type=Path)
    args = parser.parse_args()
    validate(args.release.resolve(), args.prior.resolve(), args.mirror.resolve() if args.mirror else None)
