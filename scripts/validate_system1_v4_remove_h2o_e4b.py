"""Validate the active local-screen exclusion and preserved evidence."""
import hashlib
import json
import sys
from pathlib import Path

dest, source = map(Path, sys.argv[1:])
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
m = json.loads((dest / 'manifest.json').read_text())
assert m['prior_new_local_screens_manifest_sha256'] == sha(source / 'manifest.json')
old = {p.relative_to(source) for p in source.rglob('*') if p.is_file()}
new = {p.relative_to(dest) for p in dest.rglob('*') if p.is_file()}
assert old == new
changed = {Path(n) for n in ('manifest.json', 'report.html', 'README_V4.md', 'partial_models.json', 'NEW_LOCAL_SCREEN_NOTES.md')}
for p in old - changed:
    assert sha(source / p) == sha(dest / p), str(p)
actual = {str(p.relative_to(dest)) for p in dest.rglob('*') if p.is_file() and p.name != 'manifest.json'}
assert actual == set(m['files_sha256'])
for p, digest in m['files_sha256'].items():
    assert sha(dest / p) == digest, p
old_partial = json.loads((source / 'partial_models.json').read_text())
partial = json.loads((dest / 'partial_models.json').read_text())
assert partial == old_partial[:-1] and old_partial[-1]['provider_model_id'] == 'h2o-lightning:e4b-nf4'
assert [(x['sample_n'], x['sample_usable'], x['sample_correct']) for x in partial[-2:]] == [(100, 100, 29), (799, 798, 452)]
for p in ('report.html', 'README_V4.md', 'partial_models.json', 'NEW_LOCAL_SCREEN_NOTES.md'):
    text = (dest / p).read_text().lower()
    assert 'h2o e4b' not in text and 'h2o-lightning:e4b' not in text and 'h2o lightning e4b' not in text
assert len(json.loads((dest / 'statistics.json').read_text())['models']) == 29
print('PASS: local E4B screen excluded; prior partial screens and complete results preserved.')
