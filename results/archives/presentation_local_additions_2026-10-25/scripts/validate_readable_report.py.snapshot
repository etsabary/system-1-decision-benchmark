"""Check clarity, score-cell fidelity, local links, privacy and presentation hashes."""
from repo_layout import repo_file
from collections import Counter
import csv
from html.parser import HTMLParser
import json
from pathlib import Path
import re

import build_readable_report as b


class Page(HTMLParser):
    def __init__(self):
        super().__init__(); self.cells = []; self.targets = []; self.ids = []; self.text = []
        self.headings = []; self.in_heading = False
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'td' and 'data-category' in a:
            self.cells.append(a)
        self.targets += [v for k, v in attrs if k in ('src', 'href')]
        if 'id' in a:
            self.ids.append(a['id'])
        if tag in ('h3', 'h4'):
            self.in_heading = True
    def handle_endtag(self, tag):
        if tag in ('h3', 'h4'):
            self.in_heading = False
    def handle_data(self, data):
        self.text.append(data)
        if self.in_heading:
            self.headings.append(data)


def validate():
    from archive_frontier_presentation import historical_path
    s, guide = b.load()
    manifest = json.loads((b.DEST / 'manifest.json').read_text())
    assert manifest['source_statistics_sha256'] == b.digest(b.SOURCE / 'statistics.json')
    assert manifest['source_questions_sha256'] == b.digest(b.SOURCE / 'questions_1342.jsonl')
    assert manifest['numerical_results_changed'] is False and manifest['new_inference_calls'] == 0
    assert (manifest['question_count'], manifest['model_count'], manifest['category_count']) == (1342, 20, 31)
    assert sorted(fid for _, _, fids, _ in b.GROUPS for fid in fids) == list(b.LABELS)
    for name, expected in manifest['artifacts'].items():
        assert b.digest(b.DEST / name) == expected, name
    html = (b.DEST / 'report.html').read_text()
    page = Page(); page.feed(html)
    assert len(page.ids) == len(set(page.ids)), 'Duplicate anchors'
    assert len(page.cells) == 620
    assert Counter(c['data-category'] for c in page.cells) == {fid: 20 for fid in b.LABELS}
    assert Counter(c['data-model'] for c in page.cells) == {mid: 31 for mid in s['ranked_model_ids']}
    for cell in page.cells:
        value = s['models'][cell['data-model']]['families'][cell['data-category']]
        assert int(cell['data-correct']) == value['correct'] and int(cell['data-n']) == value['n']
        assert b.color(value['accuracy'])[0] in cell['style']
    visible = ' '.join(page.text)
    assert 'without a prior' not in visible.lower()
    assert 'prior what' not in visible.lower()
    assert '12.5 percentage points' in visible and '20%' in visible
    assert 'not additional scored questions' in visible
    for fid, name in b.LABELS.items():
        assert name in page.headings, name
        assert guide[fid]['what_it_tests'] in visible and guide[fid]['illustration'] in visible
    for path in [b.DEST / 'report.html', repo_file('docs', root=b.ROOT) / b.NAME / 'report.html', *(repo_file('docs', root=b.ROOT)).glob('*.html')]:
        parsed = Page(); parsed.feed(historical_path(path).read_text())
        for target in parsed.targets:
            if re.match(r'^(https?:|mailto:|data:)', target):
                continue
            relative, _, fragment = target.partition('#')
            if relative:
                assert (path.parent / relative).exists(), (path, target)
            elif fragment:
                assert fragment in parsed.ids, (path, target)
    with (b.DEST / 'category_scores.csv').open(newline='') as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) == 31
    for row in rows:
        fid = row['category_id']
        assert row['category'] == b.LABELS[fid]
        assert int(row['questions']) == s['models'][s['ranked_model_ids'][0]]['families'][fid]['n']
        for mid in s['ranked_model_ids']:
            m = s['models'][mid]
            assert row[m['label']] == b.score(m['families'][fid])
    for path in b.DEST.iterdir():
        if path.name == 'release_checksums.json':
            continue
        assert path.read_bytes() == (repo_file('docs', root=b.ROOT) / b.NAME / path.name).read_bytes()
        if path.suffix != '.png':
            text = path.read_text()
            assert '/Users/' not in text
            assert not re.search(r'\bsk-(?:or-v1-)?[A-Za-z0-9_-]{24,}', text)
    from validate_consolidated_release import hashes
    assert hashes() == json.loads((b.SOURCE / 'release_checksums.json').read_text()), 'Prior release seal changed'
    readme = historical_path(repo_file('README.md', root=b.ROOT)).read_text()
    functions = historical_path(repo_file('FUNCTIONS.md', root=b.ROOT)).read_text()
    for text in (readme, functions):
        assert 'without a prior' not in text.lower()
        assert '![All 31 function profiles]' not in text
        for slug, _, fids, _ in b.GROUPS:
            assert f']({b.NAME}/{slug}.png)' in text
            for fid in fids:
                assert b.LABELS[fid] in text
        for target in re.findall(r'\]\(([^)]+)\)', text):
            if not re.match(r'^(https?:|mailto:|#)', target):
                assert (repo_file(target.split('#')[0], root=b.ROOT)).exists(), target
    seal = b.DEST / 'release_checksums.json'
    if seal.exists():
        assert b.seal_hashes() == json.loads(seal.read_text()), 'Sealed readable presentation changed'
    print('PASS: five named groups, 31 explained categories, 620 exact colored cells, unchanged statistics/questions and earlier seal')
    return s


if __name__ == '__main__':
    validate()
