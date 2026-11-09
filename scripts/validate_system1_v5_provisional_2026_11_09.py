"""Validate the frozen v4-to-provisional-v5 subset without private keys or APIs."""
import argparse
import collections
import csv
import gzip
import hashlib
import html
import json
import math
import re
import statistics
import struct
from decimal import Decimal
from pathlib import Path
from urllib.parse import unquote, urlsplit


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path):
    return json.loads(path.read_text())


def rows(path):
    opener = gzip.open if path.suffix == '.gz' else open
    with opener(path, 'rt', newline='') as handle:
        return list(csv.DictReader(handle))


def jsonlines(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line]


def close(actual, expected):
    assert math.isclose(float(actual), float(expected), rel_tol=1e-12, abs_tol=1e-8), (actual, expected)


def q95(values):
    values = sorted(values)
    index = (len(values) - 1) * .95
    lower, upper = math.floor(index), math.ceil(index)
    return values[lower] + (index - lower) * (values[upper] - values[lower])


def boolean(value):
    assert value.lower() in {'true', 'false'}, value
    return value.lower() == 'true'


def check_manifest(dest):
    manifest = load(dest / 'manifest.json')
    actual = {str(p.relative_to(dest)) for p in dest.rglob('*') if p.is_file() and p.name != 'manifest.json'}
    assert actual == set(manifest['files_sha256']), 'Manifest inventory differs'
    for name, digest in manifest['files_sha256'].items():
        assert sha(dest / name) == digest, name
    return manifest


def check_markdown_links(root):
    checked = 0
    for document in root.rglob('*.md'):
        for target in re.findall(r'!?\[[^\]]*\]\(([^\n)]+)\)', document.read_text()):
            target = target.strip()
            if target.startswith('<'):
                target = target[1:target.index('>')]
            else:
                target = target.split()[0]
            url = urlsplit(html.unescape(target))
            if url.scheme or url.netloc or not url.path:
                continue
            resolved = document.parent / unquote(url.path)
            assert resolved.exists(), ('Broken local Markdown target', document, target)
            checked += 1
    return checked


def band(value, bounds):
    return next((i for i, bound in enumerate(bounds) if Decimal(str(value)) <= Decimal(str(bound))), 3)


def cost_band(cost):
    value = cost['known_usd_per_1000']
    if cost['local_unmeasured_count'] or value is None:
        return None
    if Decimal(value) == 0 and cost['free_access_tariff_count'] and not cost['reported_count'] and not cost['tariff_estimate_count']:
        return None
    return band(value, ['.01', '.025', '.05'])


def cost_label(cost, normalized=False):
    if cost['local_unmeasured_count']:
        return 'Unmetered local'
    field = 'known_usd_per_1000' if normalized else 'known_subtotal_usd'
    if cost[field] is None:
        return 'Unknown'
    value = Decimal(cost[field])
    if not value and cost['free_access_tariff_count'] and cost['unknown_count']:
        return 'Free access + ?'
    if not normalized and not value and cost['free_access_tariff_count'] and not cost['reported_count'] and not cost['tariff_estimate_count']:
        return 'Free access*'
    return '$' + f'{value:.5f}' + (' + ?' if cost['unknown_count'] else '')


def validate(dest, prior, mirror=None):
    check_manifest(prior)
    manifest = check_manifest(dest)
    assert manifest['frozen_v4_manifest_sha256'] == sha(prior / 'manifest.json')
    assert manifest['questions'] == 1456 and manifest['categories'] == 43
    assert 'v5' in manifest['version'].lower()
    old, new = load(prior / 'statistics.json'), load(dest / 'statistics.json')
    assert new['questions'] == 1456 and new['categories'] == 43
    assert set(new['models']) == set(old['models']) and len(new['models']) == 32
    question_rows = jsonlines(dest / 'questions_1456.jsonl')
    old_questions = {q['id']: q for q in jsonlines(prior / 'questions_2157.jsonl')}
    questions = {q['id']: q for q in question_rows}
    assert len(question_rows) == len(questions)
    assert len(old_questions) == 2157 and len(questions) == 1456
    retained = {r['item_id'] for r in rows(dest / 'retained_items.csv')}
    removed = {r['item_id'] for r in rows(dest / 'removed_items.csv')}
    assert len(retained) == 1456 and len(removed) == 701 and not retained & removed
    assert retained | removed == set(old_questions) and retained == set(questions)
    selection = load(dest / 'selection_provenance.json')
    assert selection['source_release'] == prior.name
    assert selection['source_commit'] == '224ee46dc1c16a8ecf2c154a2144b4d2fdc45de1'
    assert selection['source_questions'] == 2157 and selection['retained_questions'] == 1456 and selection['removed_questions'] == 701
    assert set(selection['removed_item_ids']) == removed and set(selection['retained_item_ids']) == retained
    assert selection['removal_cohort_model_ids'] == old['ranked_model_ids']
    assert set(selection['complete_configuration_ids']) == set(old['models'])
    assert selection['new_inference_requests'] == 0 and selection['threshold_percent'] == 45
    receipt = load(dest / 'audit_receipt.json')
    for field, name in [('source_manifest_sha256', 'manifest.json'), ('source_statistics_sha256', 'statistics.json'),
                        ('source_questions_sha256', 'questions_2157.jsonl'), ('source_timing_sha256', 'timing_evidence.csv.gz'),
                        ('source_cost_sha256', 'cost_evidence.csv.gz')]:
        assert receipt[field] == sha(prior / name)
    assert receipt['source_selected_records'] == 32 * 2157 and receipt['retained_selected_records'] == 32 * 1456
    assert receipt['inference_requests'] == 0
    assert all(q == old_questions[item] for item, q in questions.items()), 'Question changed'
    old_sources = {q['id']: q for q in jsonlines(prior / 'source_metadata_2157.jsonl')}
    sources = {q['id']: q for q in jsonlines(dest / 'source_metadata_1456.jsonl')}
    assert set(sources) == retained and all(q == old_sources[item] for item, q in sources.items())
    counts = collections.Counter(q['family_id'] for q in questions.values())
    assert len(counts) == 43 and counts['F32'] == 20 and counts['F33'] == 200
    guide = load(dest / 'category_guide.json')
    assert set(guide) == set(counts)
    for fid, count in counts.items():
        assert guide[fid]['questions'] == count
        assert guide[fid]['example_id'] in retained

    threshold = new['inclusion_threshold']
    assert threshold['percent'] == threshold['numerator'] == 45 and threshold['denominator'] == 100
    assert threshold['n'] == 1456 and threshold['minimum_correct'] == 656
    close(new['minimum_overall_accuracy'], .45)
    assert 655 * 100 < 45 * 1456 <= 656 * 100
    assert old['ranked_model_ids'][-1] == 'super_decider'
    assert new['models']['super_decider']['correct'] == 669
    ranked = sorted((mid for mid, m in new['models'].items() if m['correct'] * 100 >= 45 * m['n']),
                    key=lambda mid: (-new['models'][mid]['correct'], mid))
    assert ranked == new['ranked_model_ids'] == old['ranked_model_ids']
    assert set(new['below_cutoff']) == set(new['models']) - set(ranked)

    correctness = rows(dest / 'correctness_evidence.csv.gz')
    removed_correctness = rows(dest / 'removed_correctness_evidence.csv.gz')
    assert set(correctness[0]) == set(removed_correctness[0]) == {'model_id', 'item_id', 'family_id', 'usable', 'correct'}
    matrix = {(r['model_id'], r['item_id']): r for r in correctness}
    removed_matrix = {(r['model_id'], r['item_id']): r for r in removed_correctness}
    assert len(matrix) == len(correctness) == 32 * 1456
    assert len(removed_matrix) == len(removed_correctness) == 32 * 701
    for mid in new['models']:
        assert {item for model, item in matrix if model == mid} == retained
        assert {item for model, item in removed_matrix if model == mid} == removed
        if mid in ranked:
            assert all(boolean(removed_matrix[mid, item]['correct']) and boolean(removed_matrix[mid, item]['usable']) for item in removed)
            assert new['models'][mid]['correct'] == old['models'][mid]['correct'] - 701
        assert sum(boolean(removed_matrix[mid, item]['correct']) for item in removed) + new['models'][mid]['correct'] == old['models'][mid]['correct']
        assert sum(boolean(removed_matrix[mid, item]['usable']) for item in removed) + new['models'][mid]['valid'] == old['models'][mid]['valid']
    assert not any(all(boolean(matrix[mid, item]['correct']) for mid in ranked) for item in retained)

    ledgers = {}
    for name in ['timing_evidence.csv.gz', 'cost_evidence.csv.gz']:
        expected = [r for r in rows(prior / name) if r['item_id'] in retained]
        actual = rows(dest / name)
        assert actual == expected, name + ' changed a selected primary'
        keyed = {(r['model_id'], r['item_id']): r for r in actual}
        assert len(keyed) == len(actual) == 32 * 1456
        ledgers[name] = keyed
    timing, costs = ledgers['timing_evidence.csv.gz'], ledgers['cost_evidence.csv.gz']
    categories = {(r['model_id'], r['family_id']): r for r in rows(dest / 'all_category_scores.csv')}
    assert len(categories) == 32 * 43
    cost_stats = load(dest / 'cost_statistics.json')['models']
    assert set(cost_stats) == set(new['models'])
    evidence_kinds = ['reported', 'tariff_estimate', 'free_access_tariff', 'unknown', 'local_unmeasured']
    for mid, model in new['models'].items():
        observations = [matrix[mid, item] for item in retained]
        model_times = [timing[mid, item] for item in retained]
        model_costs = [row for (model_id, _), row in costs.items() if model_id == mid]
        correct = sum(boolean(r['correct']) for r in observations)
        usable = sum(boolean(r['usable']) for r in observations)
        assert model['n'] == 1456 and model['correct'] == correct and model['valid'] == usable
        close(model['accuracy'], correct / 1456)
        close(model['coverage'], usable / 1456)
        close(model['answer_accuracy_among_usable'], correct / usable)
        close(model['accuracy_upper_if_all_unusable_correct'], (correct + 1456 - usable) / 1456)
        for r in observations:
            t, c = timing[mid, r['item_id']], costs[mid, r['item_id']]
            assert boolean(r['usable']) == (t['status'] == 'ok')
            assert not boolean(r['correct']) or boolean(r['usable'])
            assert r['family_id'] == questions[r['item_id']]['family_id'] == t['family_id']
            assert t['input_sha256'] == questions[r['item_id']]['native_input_sha256']
            assert all(t[field] == c[field] for field in ['input_sha256', 'source_record_sha256', 'status'])
        dates = dict(collections.Counter(r['collection_date_toronto'] for r in model_times))
        assert model['collection_dates_toronto'] == dates
        values = [float(r['latency_ms']) for r in model_times]
        assert all(math.isfinite(v) and v >= 0 for v in values)
        for field, expected in [('mean_ms', statistics.mean(values)), ('median_ms', statistics.median(values)), ('p95_ms', q95(values))]:
            close(model[field], expected)
        for fid, count in counts.items():
            category = categories[mid, fid]
            group = [r for r in observations if r['family_id'] == fid]
            values = [float(timing[mid, r['item_id']]['latency_ms']) for r in group]
            assert int(category['n']) == count
            assert int(category['correct']) == sum(boolean(r['correct']) for r in group)
            close(category['accuracy'], int(category['correct']) / count)
            for field, expected in [('mean_ms', statistics.mean(values)), ('median_ms', statistics.median(values)), ('p95_ms', q95(values))]:
                close(category[field], expected)
        close(model['macro_category_accuracy'], statistics.mean(float(categories[mid, fid]['accuracy']) for fid in counts))
        cs = cost_stats[mid]
        assert cs['n'] == 1456
        for kind in evidence_kinds:
            assert cs[kind + '_count'] == sum(r['evidence_kind'] == kind for r in model_costs)
        assert sum(cs[kind + '_count'] for kind in evidence_kinds) == 1456
        reported = [Decimal(r['reported_usd']) for r in model_costs if r['reported_usd']]
        estimates = [Decimal(r['tariff_estimate_usd']) for r in model_costs if r['tariff_estimate_usd']]
        for field, amounts in [('reported_subtotal_usd', reported), ('estimate_only_subtotal_usd', estimates), ('known_subtotal_usd', reported + estimates)]:
            if not amounts:
                assert cs[field] is None
            else:
                assert Decimal(cs[field]) == sum(amounts), (mid, field, cs[field], str(sum(amounts)))
        if cs['known_subtotal_usd'] is None:
            assert cs['known_usd_per_1000'] is None
        else:
            assert Decimal(cs['known_usd_per_1000']) == Decimal(cs['known_subtotal_usd']) * Decimal(1000) / Decimal(1456)

    page, readme = (dest / 'report.html').read_text(), (dest / 'README_V5.md').read_text()
    assert 'provisional' in page.lower() and 'provisional' in readme.lower()
    assert page.index('src="comparison_accuracy.png"') < page.index('<div class="comparison-table">')
    assert readme.index('comparison_accuracy.png') < readme.index('| Configuration |')
    for text in ['Selected-record known USD', 'USD / 1,000', 'data-cost-band', 'data-mobile-speed-band', 'mobile-cards', 'selection', '701', '1,456', '669', 'v4']:
        assert text in page, text
    assert 'Selected-record known cost' in readme and 'Cost / 1,000' in readme
    assert 'python3 scripts/validate_system1_v5_provisional_2026_11_09.py' in readme
    assert 'Model-selected choices and the gold scoring key remain private.' in readme
    for match in re.finditer(r'(?<![\d.])62\s*%', page):
        context = page[max(0, match.start() - 180):match.end() + 180].lower()
        assert 'v4' in context or 'historical' in context or 'incomplete' in context, 'Unqualified old 62% cutoff'
    for mid in new['below_cutoff']:
        model = new['models'][mid]
        lines = [line for line in readme.splitlines() if line.startswith('- ') and line[2:].replace('**', '').startswith(model['label'] + ':')]
        assert len(lines) == 1 and f"{model['correct']}/1,456" in lines[0], mid
    primary = {mid: body for mid, body in re.findall(r'<tr data-overall-model="([^"]+)">(.*?)</tr>', page, re.S) if 'data-cost-band=' in body}
    cards = dict(re.findall(r'<article class="mobile-card" data-overall-model="([^"]+)">(.*?)</article>', page, re.S))
    assert set(primary) == set(cards) == set(ranked)
    colors, marks = ['#d8f1e8', '#fff4c2', '#ffe4ca', '#fbdedd'], ['🟩', '🟨', '🟧', '🟥']
    for mid in ranked:
        model, cs = new['models'][mid], cost_stats[mid]
        speeds = [str(band(model[field], [250, 500, 1000])) for field in ['median_ms', 'p95_ms']]
        cb = cost_band(cs)
        color_code = 'unknown' if cb is None else str(cb)
        assert re.findall(r'data-speed-band="([^"]+)"', primary[mid]) == speeds
        assert re.findall(r'data-mobile-speed-band="([^"]+)"', cards[mid]) == speeds
        assert re.findall(r'data-cost-band="([^"]+)"', primary[mid]) == [color_code] * 2
        assert re.findall(r'data-mobile-cost-band="([^"]+)"', cards[mid]) == [color_code] * 2
        assert re.findall(r'<td class="cost [^"]*" style="background:([^"]+)"', primary[mid]) == ['#edf0f2' if cb is None else colors[cb]] * 2
        assert html.escape(cost_label(cs)) in primary[mid] and html.escape(cost_label(cs, True)) in primary[mid]
        line = [line for line in readme.splitlines() if line.startswith('| ' + model['label'] + ' |')]
        assert len(line) == 1
        assert all(marks[int(speed)] in line[0] for speed in speeds)
        mark = '⬜' if cb is None else marks[cb]
        assert mark + ' ' + cost_label(cs) in line[0] and mark + ' ' + cost_label(cs, True) in line[0]
    for kind in ['accuracy', 'latency', 'cost']:
        data = (dest / ('comparison_' + kind + '.png')).read_bytes()
        assert data[:8] == b'\x89PNG\r\n\x1a\n'
        width, height = struct.unpack('>II', data[16:24])
        assert width >= 1300 and height >= 1600
    for name in ['PROJECT_LICENSE_MIT.txt', 'KAI_CASE_NOTE.md', 'STRIKE_SCREEN_NOTES.md', 'LOCAL_SCREEN_NOTES.md', 'NEW_LOCAL_SCREEN_NOTES.md', 'OPENAI_DECISIONS_NOTES.md', 'partial_models.json']:
        assert sha(dest / name) == sha(prior / name), name
    for path in (prior / 'third_party_licenses').iterdir():
        assert sha(dest / 'third_party_licenses' / path.name) == sha(path)
    license_text = (dest / 'SOURCE_AND_LICENSES.md').read_text()
    assert all(term.lower() in license_text.lower() for term in ['Apache', 'MIT', 'MAIQ', 'rights remain unestablished'])
    for path in dest.rglob('*'):
        if path.is_file() and path.suffix in ['.json', '.jsonl', '.csv', '.md', '.html', '.txt']:
            text = path.read_text()
            assert '/Users/' not in text and '/PRIVATE/' not in text, path
    if mirror:
        files = {str(p.relative_to(dest)): sha(p) for p in dest.rglob('*') if p.is_file()}
        mirrored = {str(p.relative_to(mirror)): sha(p) for p in mirror.rglob('*') if p.is_file()}
        assert files == mirrored, 'Published mirror differs'
        check_markdown_links(mirror)
    check_markdown_links(dest)
    print(f'PASS: provisional v5, 1,456 unchanged inputs / 43 categories; exact 45% threshold (656 correct minimum); {len(ranked)} qualifying / 32 complete configurations; 46,592 retained primary records; pooled timings, costs, provenance, colours and v4 archive verified.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('release', type=Path)
    parser.add_argument('prior', type=Path)
    parser.add_argument('--mirror', type=Path)
    args = parser.parse_args()
    validate(args.release, args.prior, args.mirror)
