"""Check Sage v4 additions, previous records, and requested presentation order."""
import csv, gzip, json, sys
from pathlib import Path

root = Path(sys.argv[1])
previous = Path(sys.argv[2])
stats = json.loads((root / 'statistics.json').read_text())
old = json.loads((previous / 'statistics.json').read_text())
assert len(old['models']) == 28 and len(stats['models']) == 29
assert all(stats['models'][mid] == model for mid, model in old['models'].items())
sage = stats['models']['levanto_sage_2']
assert (sage['correct'], sage['n'], sage['valid']) == (1530, 2157, 2157)
assert 'reasoning off' in sage['configuration']
assert 'Two returned choices' in sage['new_collection_limit']

def rows(path):
    with (gzip.open(path, 'rt', newline='') if path.suffix == '.gz' else path.open(newline='')) as stream:
        return list(csv.DictReader(stream))

for name in ('all_category_scores.csv', 'timing_evidence.csv.gz', 'cost_evidence.csv.gz'):
    assert rows(previous / name) == [x for x in rows(root / name) if x['model_id'] != 'levanto_sage_2'], name
assert (root / 'questions_2157.jsonl').read_bytes() == (previous / 'questions_2157.jsonl').read_bytes()
assert (root / 'KAI_CASE_NOTE.md').read_bytes() == (previous / 'KAI_CASE_NOTE.md').read_bytes()
page = (root / 'report.html').read_text()
readme = (root / 'README_V4.md').read_text()
assert page.index('src="comparison_accuracy.png"') < page.index('<div class="comparison-table">')
assert readme.index('comparison_accuracy.png') < readme.index('| Configuration |')
assert 'data-incomplete-model="hanzo-kai"' in page and '46/244' in readme
assert readme.index('## Question selection') > readme.index('categories_numerical.png')
assert 'two returned choices' in page.lower()
print('PASS: prior 28 model results and evidence retained; Sage, Kai, selection notes and chart order verified.')
