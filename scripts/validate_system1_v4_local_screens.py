"""Verify incomplete local screens and preserve all prior full-bank evidence."""
import hashlib, json, sys
from pathlib import Path

dest, source = map(Path, sys.argv[1:])
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
manifest = json.loads((dest / 'manifest.json').read_text())
assert manifest['prior_sage_manifest_sha256'] == sha(source / 'manifest.json')
old = {p.relative_to(source) for p in source.rglob('*') if p.is_file()}
new = {p.relative_to(dest) for p in dest.rglob('*') if p.is_file()}
assert new == old | {Path('LOCAL_SCREEN_NOTES.md')}
changed = {Path('manifest.json'), Path('report.html'), Path('README_V4.md'), Path('partial_models.json')}
for name in old - changed:
    assert sha(source / name) == sha(dest / name), str(name)
actual = {str(p.relative_to(dest)) for p in dest.rglob('*') if p.is_file() and p.name != 'manifest.json'}
assert actual == set(manifest['files_sha256'])
for name, digest in manifest['files_sha256'].items():
    assert sha(dest / name) == digest, name
partial = json.loads((dest / 'partial_models.json').read_text())
assert len(partial) == 3 and partial[0] == json.loads((source / 'partial_models.json').read_text())[0]
tt, gl = partial[1:]
assert (tt['sample_n'], tt['sample_usable'], tt['sample_correct'], tt['subq_correct_on_same_inputs']) == (100, 100, 32, 77)
assert (gl['sample_n'], gl['sample_usable'], gl['sample_correct'], gl['server_input_limit_tokens']) == (20, 14, 4, 512)
assert all(x['status'] == 'incomplete_not_in_full_bank_rankings' for x in (tt, gl))
stats = json.loads((dest / 'statistics.json').read_text())
assert len(stats['models']) == 29
assert all('this_that' not in mid and 'gliner' not in mid for mid in stats['models'])
page = (dest / 'report.html').read_text()
readme = (dest / 'README_V4.md').read_text()
assert 'not full-bank scores or cutoff classifications' in page and 'not full-bank scores or cutoff classifications' in readme
assert 'data-incomplete-model="hanzo-kai"' in page and '46/244' in readme
assert page.index('src="comparison_accuracy.png"') < page.index('<div class="comparison-table">')
assert readme.index('comparison_accuracy.png') < readme.index('| Configuration |')
assert readme.index('## Question selection') > readme.index('categories_numerical.png')
print('PASS: both partial screens are separate; previous model data, graphics, Hanzo note and ordering preserved.')
