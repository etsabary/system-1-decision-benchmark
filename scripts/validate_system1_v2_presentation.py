"""Validate the visual successor and reconcile every public cost ledger row."""
import collections
import csv
from decimal import Decimal
import gzip
from html.parser import HTMLParser
import json
import re
from urllib.parse import unquote, urlsplit
import xml.etree.ElementTree as ET

import publish_system1_v2_presentation as b


class Page(HTMLParser):
    def __init__(self):
        super().__init__(); self.cells = []; self.ranks = []; self.overall = []; self.ids = []; self.links = []; self.speeds = []
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if 'id' in a: self.ids.append(a['id'])
        if 'data-overall-model' in a: self.overall.append(a['data-overall-model'])
        if 'data-correct' in a: self.cells.append(a)
        if 'data-rank-correct' in a: self.ranks.append(a)
        if 'data-speed-band' in a: self.speeds.append(a)
        for key in ['href', 'src']:
            if key in a: self.links.append(a[key])


def ledger_rows(path):
    with gzip.open(path, 'rt', newline='') as f: return list(csv.DictReader(f))


def validate_costs(d):
    rows = ledger_rows(d / 'cost_evidence.csv.gz')
    timing = ledger_rows(d / 'timing_evidence.csv.gz')
    assert len(rows) == len(timing) == 73492
    models = b.load(d / 'cost_statistics.json')['models']
    all_s = b.load(d / 'all_statistics.json')['models']
    assert set(models) == set(all_s) and len(models) == 38
    csvmodels = b.frozen.csvrows(d / 'cost_statistics.csv')
    assert len(csvmodels) == len({r['model_id'] for r in csvmodels}) == 38
    for r in csvmodels:
        c = models[r['model_id']]
        assert all(v == ('' if c[k] is None else str(c[k])) for k, v in r.items())
    assert not {'correct', 'choice', 'probabilities', 'expected_answer', 'correct_option_id'} & rows[0].keys()
    grouped = collections.defaultdict(list)
    for r, t in zip(rows, timing):
        for field in ['model_id', 'item_id', 'family_id', 'component', 'input_sha256', 'status', 'collection_date_toronto', 'source_record_sha256']:
            assert r[field] == t[field], (field, r['model_id'], r['item_id'])
        assert r['evidence_kind'] in ['reported', 'tariff_estimate', 'free_access_tariff', 'unknown', 'local_unmeasured']
        reported, estimate = r['reported_usd'], r['tariff_estimate_usd']
        assert not (reported and estimate)
        for amount in [reported, estimate]:
            if amount: assert Decimal(amount).is_finite() and Decimal(amount) >= 0
        assert bool(reported) == (r['evidence_kind'] == 'reported')
        assert bool(estimate) == (r['evidence_kind'] in ['tariff_estimate', 'free_access_tariff'])
        if r['evidence_kind'] == 'free_access_tariff':
            assert Decimal(estimate) == 0 and any(x in r['evidence_basis'] for x in ['free', 'promotional'])
        assert r['evidence_basis']
        if r['model_id'].startswith('local_'): assert r['evidence_kind'] == 'local_unmeasured'
        grouped[r['model_id']].append(r)
    for mid, c in models.items():
        rr = grouped[mid]; assert len(rr) == len({r['item_id'] for r in rr}) == 1934
        kinds = collections.Counter(r['evidence_kind'] for r in rr)
        for kind in ['reported', 'tariff_estimate', 'free_access_tariff', 'unknown', 'local_unmeasured']:
            assert c[kind + '_count'] == kinds[kind], (mid, kind)
        rep = sum((Decimal(r['reported_usd']) for r in rr if r['reported_usd']), Decimal(0))
        est = sum((Decimal(r['tariff_estimate_usd']) for r in rr if r['tariff_estimate_usd']), Decimal(0))
        assert rep == Decimal(c['reported_subtotal_usd'] or 0) and est == Decimal(c['estimate_only_subtotal_usd'] or 0)
        known = kinds['reported'] + kinds['tariff_estimate'] + kinds['free_access_tariff']
        assert known == c['known_evidence_count']
        assert c['receipt_coverage'] == kinds['reported']/1934 and c['evidence_coverage'] == known/1934
        assert c['basis_counts'] == dict(collections.Counter(r['evidence_basis'] for r in rr))
        assert c['component_evidence_counts'] == {component: dict(collections.Counter(r['evidence_kind'] for r in rr if r['component'] == component)) for component in ['original1342', 'logical192', 'practical400']}
        if known:
            assert Decimal(c['known_subtotal_usd']) == rep + est
            assert Decimal(c['known_usd_per_1000']) == (rep + est)/Decimal(1934)*1000
        else: assert c['known_subtotal_usd'] is None and c['known_usd_per_1000'] is None
    # Independent capture-audit checkpoints, including receipt gaps and changed tariff/access phases.
    expected = {'reference_sol': ('1.8969510', 1934, 0), 'reference_sonnet': ('3.725226', 1934, 0), 'reference_opus5': ('7.998020', 1751, 183), 'fastino_glide_v23_bf16': ('.03772244', 0, 0), 'celeris11_decision': ('.04073156', 0, 0), 'mammoth1': ('.052865', 0, 1), 'elephant1': ('.018556020', 0, 0), 'nimble_v4_max': ('.05783746', 0, 1), 'trio_spark14': ('.025050018', 1772, 162)}
    for mid, (amount, receipts, unknown) in expected.items():
        c = models[mid]
        assert abs(Decimal(c['known_subtotal_usd']) - Decimal(amount)) <= Decimal('1e-12')
        assert c['reported_count'] == receipts and c['unknown_count'] == unknown
    assert models['reference_opus5']['unknown_count'] == 183 and all_s['reference_opus5']['failure_counts']['declared refusal'] == 185
    for mid in ['mammoth1', 'elephant1']:
        assert models[mid]['free_access_tariff_count'] == 1342 and Decimal(models[mid]['estimate_only_subtotal_usd']) > 0
    for mid in ['d3_ultra', 'amos_large']:
        assert models[mid]['evidence_kind'] == 'free_access_tariff' and models[mid]['reported_count'] == 0
    assert models['turion_jev31b']['known_subtotal_usd'] is None
    return models


def validate_page(path, s, cats):
    page = Page(); content = path.read_text(); page.feed(content)
    assert page.overall == s['ranked_model_ids']
    assert len(page.cells) == len(page.ranks) == 1066 and len(page.ids) == len(set(page.ids))
    assert len({(c['data-model'], c['data-category']) for c in page.cells}) == 1066
    for c in page.cells + page.ranks:
        mid, fid = c['data-model'], c['data-category']; expected = cats[mid, fid]
        key = 'data-correct' if 'data-correct' in c else 'data-rank-correct'
        assert c[key] == expected['correct'] and c['data-n'] == expected['n']
        bg, fg = b.accuracy_colors(expected['accuracy'])
        assert f'background:{bg};color:{fg}' in c['style']
        best = max(int(cats[m, fid]['correct']) for m in s['ranked_model_ids'])
        assert ('leader' in c['class']) == (int(expected['correct']) == best)
    # Ranking order: descending accuracy, stable overall-order ties. Rank numbers use competition ranks.
    for fid in sorted({k[1] for k in cats}):
        rendered = [c['data-model'] for c in page.ranks if c['data-category'] == fid]
        expected = sorted(s['ranked_model_ids'], key=lambda m: -int(cats[m, fid]['correct']))
        assert rendered == expected
        fragment = re.search(r'id="category-' + fid + r'".*?</details>', content, re.S).group(0)
        rankvalues = [int(v) for v in re.findall(r'data-category-rank="(\d+)"', fragment)]
        assert rankvalues == [1 + sum(int(cats[m, fid]['correct']) > int(cats[mid, fid]['correct']) for m in expected) for mid in expected]
    assert len(page.speeds) == 26*2 + 1066*2
    for link in page.links:
        u = urlsplit(link)
        if not u.scheme and not u.netloc:
            if u.path: assert (path.parent / unquote(u.path)).is_file(), (path, link)
            elif u.fragment: assert u.fragment in page.ids, (path, link)
    for phrase in ['How to read the colours', 'cost_evidence.csv.gz', '1,934', '62%', '1,751', '183', '185', 'USD / 1,000']:
        assert phrase in content
    assert 'has not been consolidated' not in content


def validate():
    d = b.SOURCE; seal = b.load(d / 'manifest.json')
    assert seal['frozen_release_manifest_sha256'] == b.sha(b.frozen.SOURCE / 'manifest.json')
    for name, value in seal['artifacts'].items(): assert b.sha(d / name) == value, name
    for name, value in seal['source_files_sha256'].items(): assert b.sha(b.ROOT / name) == value, name
    for name, value in seal['preserved_inputs_sha256'].items():
        assert b.sha(d / name) == b.sha(b.frozen.SOURCE / name) == value, name
    for name in ['statistics.json', 'model_statistics.csv', 'category_scores.csv', 'model_profiles.csv', 'category_leaders.csv']:
        assert (d / name).read_bytes() == (b.frozen.SOURCE / name).read_bytes()
    costs = validate_costs(d)
    s = b.load(d / 'statistics.json'); cats = {(r['model_id'], r['family_id']): r for r in b.frozen.csvrows(d / 'category_scores.csv')}
    assert sorted(fid for _, _, fids in b.GROUPS for fid in fids) == sorted(b.load(d / 'category_guide.json'))
    for name in ['overview'] + ['categories_' + slug for slug, _, _ in b.GROUPS]:
        root = ET.parse(d / (name + '.svg')).getroot()
        description = json.loads(root.find('.//{http://purl.org/dc/elements/1.1/}description').text)
        assert description['model_ids'] == s['ranked_model_ids'] and description['minimum_overall_accuracy'] == .62
        if name.startswith('categories_'):
            assert description['accuracy_scale'] == [0, 1]
            assert description['family_ids'] == next(f for slug, _, f in b.GROUPS if name == 'categories_' + slug)
    for path in [d / 'report.html', b.ROOT / 'docs/report.html']: validate_page(path, s, cats)
    readme = (b.ROOT / 'README.md').read_text()
    assert len(re.findall(r'!\[', readme)) >= 9
    for match in re.finditer(r'!?\[[^\]]*\]\(([^)]+)\)', readme):
        u = urlsplit(match[1])
        if not u.scheme and not u.netloc and u.path: assert (b.ROOT / unquote(u.path)).is_file(), match[1]
    for p in d.iterdir():
        if not p.is_file(): continue
        assert p.read_bytes() == (b.ROOT / 'docs' / b.NAME / p.name).read_bytes()
        if p.suffix in ['.json', '.jsonl', '.csv', '.md', '.txt', '.html', '.svg']:
            text = p.read_text()
            assert all(x not in text for x in ['/Users/', '192.168.1.', 'API_KEY=', 'Bearer sk-', '"expected_answer":', '"correct_option_id":', '"probabilities":']), p
    for entry in b.load(b.ARCHIVE / 'manifest.json')['files'].values(): assert b.sha(b.ARCHIVE / entry['path']) == entry['sha256']
    print('PASS: unchanged v2 measurements; 73,492 cost/timing joins; 38 cost summaries; 26 main models; 1,066 coloured cells + 1,066 sorted rankings; seven annotated matrices; legends, privacy, links and seals.')


if __name__ == '__main__': validate()
