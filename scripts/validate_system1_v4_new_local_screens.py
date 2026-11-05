"""Verify the local-screen successor preserves the previous release."""
import hashlib
import json
import sys
from pathlib import Path

dest, source = map(Path, sys.argv[1:])
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
manifest = json.loads((dest / 'manifest.json').read_text())
assert manifest['prior_strike_screen_manifest_sha256'] == sha(source / 'manifest.json')
old = {p.relative_to(source) for p in source.rglob('*') if p.is_file()}
new = {p.relative_to(dest) for p in dest.rglob('*') if p.is_file()}
assert new == old | {Path('NEW_LOCAL_SCREEN_NOTES.md')}
changed = {Path('manifest.json'), Path('report.html'), Path('README_V4.md'), Path('partial_models.json')}
for name in old - changed:
    assert sha(source / name) == sha(dest / name), str(name)
actual = {str(p.relative_to(dest)) for p in dest.rglob('*') if p.is_file() and p.name != 'manifest.json'}
assert actual == set(manifest['files_sha256'])
for name, expected in manifest['files_sha256'].items():
    assert sha(dest / name) == expected, name
partial = json.loads((dest / 'partial_models.json').read_text())
assert partial[:4] == json.loads((source / 'partial_models.json').read_text())
assert len(partial) == 7
assert [(x['sample_n'], x['sample_usable'], x['sample_correct']) for x in partial[4:]] == [(100, 100, 29), (799, 798, 452), (20, 16, 6)]
assert all(x['status'] == 'incomplete_not_in_full_bank_rankings' and len(x['records_digest_sha256']) == 64 for x in partial[4:])
assert len(json.loads((dest / 'statistics.json').read_text())['models']) == 29
page, readme = (dest / 'report.html').read_text(), (dest / 'README_V4.md').read_text()
section = page[page.index('<section id="local-screens">'):page.index('<section id="legend">')]
for fragment in ('29/100', '452/799', '6/16', '4/20', 'not full-bank scores or cutoff classifications'):
    assert fragment in section and fragment in readme
assert page.index('src="comparison_accuracy.png"') < page.index('<div class="comparison-table">')
assert readme.index('comparison_accuracy.png') < readme.index('| Configuration |')
print('PASS: three incomplete local screens added; previous results and graphics preserved.')
