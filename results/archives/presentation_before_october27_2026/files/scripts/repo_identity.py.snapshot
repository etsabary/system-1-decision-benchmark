"""Publish neutral repository links without rewriting frozen benchmark evidence."""
from repo_layout import logical_relative, repo_file
import argparse
from hashlib import sha256
from html.parser import HTMLParser
import json
from pathlib import Path
import posixpath
import re
import subprocess
from urllib.parse import urlsplit, urlunsplit

ROOT = Path(__file__).resolve().parents[1]
DEST = repo_file('repo_identity_2026-10-19', root=ROOT)
ARCHIVE = DEST / 'archive'
OLD = 'jev-1.14-comparison-benchmark'
NEW = 'system-1-decision-benchmark'
SITE = 'https://etsabary.github.io/' + NEW
PRIOR = repo_file('llm_references_2026-10-19', root=ROOT)
SAVED = ('README.md', 'FUNCTIONS.md', 'LLM_REFERENCES.md',
         'docs/index.html', 'docs/functions.html', 'docs/output_compliance.html',
         'publish_frontier_references.py', '.github/workflows/october18-validate.yml')
CURRENT = SAVED + ('docs/report.html', 'repo_identity.py', 'test_repo_identity.py')


def digest(path):
    return sha256(Path(path).read_bytes()).hexdigest()


def historical_path(path):
    path = Path(path)
    manifest = ARCHIVE / 'manifest.json'
    entries = json.loads(manifest.read_text())['files'] if manifest.exists() else {}
    entry = entries.get(str(logical_relative(path, root=ROOT)))
    if entry is None:
        from publication_history import previous_path
        return previous_path(path)
    saved = ARCHIVE / entry['path']
    assert digest(saved) == entry['sha256']
    return saved


def archive():
    manifest = ARCHIVE / 'manifest.json'
    if manifest.exists():
        for name in SAVED:
            historical_path(repo_file(name, root=ROOT))
        return
    commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    entries = {}
    for name in SAVED:
        data = subprocess.check_output(['git', 'show', commit + ':' + name], cwd=ROOT)
        assert data == (repo_file(name, root=ROOT)).read_bytes(), 'Overlapping changes: ' + name
        path = ARCHIVE / (name + '.snapshot')
        assert not path.exists()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        entries[name] = {'path': name + '.snapshot', 'sha256': digest(path)}
    manifest.write_text(json.dumps({'commit': commit, 'files': entries}, indent=2) + '\n')


def neutral_links(text):
    text = text.replace('https://etsabary.github.io/' + OLD, SITE)
    text = text.replace('https://github.com/etsabary/' + OLD,
                        'https://github.com/etsabary/' + NEW)
    return text.replace(SITE + '/llm_references_2026-10-19/report.html', SITE + '/report.html')


def root_report(text):
    text = neutral_links(text)
    def link(match):
        attr, target = match.groups()
        u = urlsplit(target)
        if u.scheme or u.netloc or not u.path or u.path.startswith('/'):
            return match.group(0)
        path = posixpath.normpath(posixpath.join('llm_references_2026-10-19', u.path))
        assert not path.startswith('../')
        return attr + '="' + urlunsplit(('', '', path, u.query, u.fragment)) + '"'
    text = re.sub(r'\b(href|src)="([^"]+)"', link, text)
    return text.replace('<title>Text decision benchmark:', '<title>System 1 Decision Benchmark:')


def build():
    assert not (DEST / 'manifest.json').exists(), 'Do not overwrite a sealed identity migration'
    archive()
    for name in ('README.md', 'FUNCTIONS.md', 'LLM_REFERENCES.md'):
        text = neutral_links(historical_path(repo_file(name, root=ROOT)).read_text())
        if name == 'README.md':
            text = re.sub(r'^# .+\n', '# System 1 Decision Benchmark\n\n20 specialized decision models and 3 high-end LLM references on 1,342 text questions.\n', text, count=1)
        (repo_file(name, root=ROOT)).write_text(text)
    (repo_file('docs/report.html', root=ROOT)).write_text(root_report((PRIOR / 'report.html').read_text()))
    for name in ('index.html', 'functions.html', 'output_compliance.html'):
        text = historical_path(repo_file('docs', root=ROOT) / name).read_text()
        text = neutral_links(text).replace('llm_references_2026-10-19/report.html', 'report.html')
        (repo_file('docs', root=ROOT) / name).write_text(text)
    files = {name: digest(repo_file(name, root=ROOT)) for name in CURRENT}
    files.update({str(logical_relative(p, root=ROOT)): digest(p) for p in ARCHIVE.rglob('*') if p.is_file()})
    (DEST / 'manifest.json').write_text(json.dumps({
        'name': NEW, 'old_name': OLD, 'site': SITE + '/report.html',
        'scope': 'Repository identity, current links and presentation entry point only; no new inference or changed measurements.',
        'prior_release_seal_sha256': digest(PRIOR / 'release_checksums.json'),
        'statistics_sha256': digest(PRIOR / 'statistics.json'),
        'files': files}, indent=2) + '\n')


class Page(HTMLParser):
    def __init__(self):
        super().__init__(); self.links = []; self.cells = []; self.models = []
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        self.links += [v for k, v in attrs.items() if k in ('src', 'href')]
        if 'data-category' in attrs:
            self.cells.append(attrs)
        if 'data-summary-model' in attrs:
            self.models.append(attrs['data-summary-model'])


def validate():
    from publication_history import previous_path
    from validate_frontier_release import validate as previous
    from validate_consolidated_release import privacy
    manifest = json.loads((DEST / 'manifest.json').read_text())
    assert all(digest(previous_path(repo_file(name, root=ROOT))) == h for name, h in manifest['files'].items())
    assert digest(PRIOR / 'release_checksums.json') == manifest['prior_release_seal_sha256']
    assert digest(PRIOR / 'statistics.json') == manifest['statistics_sha256']
    a = Page(); a.feed((PRIOR / 'report.html').read_text())
    b = Page(); text = previous_path(repo_file('docs/report.html', root=ROOT)).read_text(); b.feed(text)
    assert a.models == b.models and a.cells == b.cells
    assert len(b.models) == 23 and len(b.cells) == 713
    for name in ('README.md', 'FUNCTIONS.md', 'LLM_REFERENCES.md', 'docs/report.html'):
        text = previous_path(repo_file(name, root=ROOT)).read_text(); privacy(text)
        assert OLD not in text
    for path in (repo_file('docs', root=ROOT)).glob('*.html'):
        page = Page(); page.feed(previous_path(path).read_text())
        for target in page.links:
            u = urlsplit(target)
            if not u.scheme and not u.netloc and u.path:
                assert (path.parent / u.path).exists(), (path, target)
    previous()
    print('PASS: neutral repository identity, valid current report links, unchanged 23 routes and 713 category cells; all previous seals preserved.')


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--archive', action='store_true')
    p.add_argument('--build', action='store_true')
    args = p.parse_args()
    if args.archive:
        archive()
    elif args.build:
        build(); validate()
    else:
        validate()
