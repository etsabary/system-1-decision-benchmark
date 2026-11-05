"""Check the partial Strike note and ensure all prior benchmark evidence survives."""
import hashlib, json, sys
from pathlib import Path

dest, source = map(Path, sys.argv[1:])
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
manifest = json.loads((dest / 'manifest.json').read_text())
assert manifest['prior_local_screens_manifest_sha256'] == sha(source / 'manifest.json')
old = {p.relative_to(source) for p in source.rglob('*') if p.is_file()}
new = {p.relative_to(dest) for p in dest.rglob('*') if p.is_file()}
assert new == old | {Path('STRIKE_SCREEN_NOTES.md')}
changed = {Path('manifest.json'), Path('report.html'), Path('README_V4.md'), Path('partial_models.json')}
for name in old - changed:
    assert sha(source / name) == sha(dest / name), str(name)
actual = {str(p.relative_to(dest)) for p in dest.rglob('*') if p.is_file() and p.name != 'manifest.json'}
assert actual == set(manifest['files_sha256'])
for name, expected in manifest['files_sha256'].items():
    assert sha(dest / name) == expected, name
partial = json.loads((dest / 'partial_models.json').read_text())
assert partial[:3] == json.loads((source / 'partial_models.json').read_text())
assert len(partial) == 4
strike = partial[3]
assert strike['status'] == 'incomplete_not_in_full_bank_rankings'
assert (strike['sample_n'], strike['sample_usable'], strike['sample_correct']) == (100, 100, 57)
assert strike['subq_correct_on_same_inputs'] == 77 and strike['sage_correct_on_same_inputs'] == 74
assert strike['reported_charge_count'] == 100 and float(strike['reported_charge_eur']) == 0
assert len(strike['records_digest_sha256']) == 64
stats = json.loads((dest / 'statistics.json').read_text())
assert len(stats['models']) == 29 and all('strike' not in mid.lower() for mid in stats['models'])
page = (dest / 'report.html').read_text()
readme = (dest / 'README_V4.md').read_text()
begin, end = page.index('<h3>Below the 62% cutoff</h3>'), page.index('<section id="legend">')
section = page[begin:end]
assert 'data-incomplete-model="strike-1"' in section and '57/100' in section
assert 'not a full-bank score or a 62% cutoff classification' in section
assert 'data-incomplete-model="hanzo-kai"' in section and 'Incomplete local screens' in section
assert readme.index('## Below the cutoff') < readme.index('**Strike 1 — incomplete 100-question screen:**') < readme.index('## Question selection')
assert 'not a full-bank score or a 62% cutoff classification' in readme
assert page.index('src="comparison_accuracy.png"') < page.index('<div class="comparison-table">')
assert readme.index('comparison_accuracy.png') < readme.index('| Configuration |')
print('PASS: Strike partial screen is beside the cutoff catalogue; prior results, graphics and other partial notes are intact.')
