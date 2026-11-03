"""Preserve v4 notes and put the accuracy graph before the comparison table."""
import hashlib, json, re, sys
from pathlib import Path

repo = Path(__file__).resolve().parents[1]
out = Path(sys.argv[1]).resolve()
prior = repo / 'results/releases/system1_v4_kai_note_2026-11-02'
name = 'system1_v4_sage_2026-11-02'

page = (out / 'report.html').read_text()
old_page = (prior / 'report.html').read_text()
note = re.search(r'<div class="note" data-incomplete-model="hanzo-kai">.*?</div>', old_page).group()
page, n = re.subn(r'<section id="partial">.*?</section>', '', page, count=1)
assert n == 1
anchor = page.index('<h3>Below the 62% cutoff</h3>')
end = page.index('</ul></section>', anchor) + len('</ul>')
page = page[:end] + note + page[end:]
chart = re.search(r'<h3>Accuracy</h3><div class="chart-scroll">.*?</div>', page).group()
page = page.replace(chart, '', 1)
anchor = '<label>Find a model <input id="model-search"'
assert page.count(anchor) == 1
page = page.replace(anchor, chart + anchor, 1)
sage_note = ('<p><strong>Levanto Sage 2:</strong> two returned choices differed from the highest '
             'probability in the same response. The returned choices were scored as received; '
             'both were incorrect. Substituting the highest probabilities would add two correct '
             'answers, but is not the reported score.</p>')
anchor = '<details><summary>Additional accuracy and coverage measures</summary>'
assert page.count(anchor) == 1
page = page.replace(anchor, sage_note + anchor, 1)
(out / 'report.html').write_text(page)

readme = (out / 'README_V4.md').read_text()
selection = ('**Selection bias:** the original 60 quantitative questions were selected for Fastino and D3 Artemis errors; '
             'the 140 new questions were selected for an error by at least one of Fastino, Mammoth, GPT-6 Sol without '
             'reasoning, D3 Ultra and Drex Max. This distributes, but does not remove, selection bias.\n\n')
assert readme.count(selection) == 1
readme = readme.replace(selection, '')
chart_md = re.search(r'### Accuracy\n\n!\[Accuracy comparison for the qualifying models\]\([^\n]+\)\n\n', readme).group()
readme = readme.replace(chart_md, '', 1)
anchor = '## Main comparison\n\n'
assert readme.count(anchor) == 1
readme = readme.replace(anchor, anchor + chart_md, 1)
old = (prior / 'README_V4.md').read_text()
kai = re.search(r'\*\*Hanzo Kai 1\.9 — stopped partial test:\*\*[^\n]+', old).group()
kai = kai.replace('results/releases/system1_v4_kai_note_2026-11-02/', 'results/releases/' + name + '/')
readme, n = re.subn(r'## Incomplete exploratory tests\n\n- Hanzo Kai 1\.9:[^\n]+\n\n', '', readme)
assert n == 1
question_selection = ("## Question selection\n\nThe quantitative category includes 60 questions selected for errors by Fastino and D3 Artemis "
                      "and 140 selected for errors by at least one of Fastino, Mammoth, GPT-6 Sol without reasoning, D3 Ultra and Drex Max. "
                      "Selection using these models' answers can affect comparisons involving them; using several models distributes, "
                      "but does not eliminate, this selection bias.\n\n")
anchor = '## Download and reproducibility\n\n'
assert readme.count(anchor) == 1
readme = readme.replace(anchor, kai + '\n\n' + question_selection + anchor, 1)
anchor = '\nOperational accuracy counts unusable requests'
assert readme.count(anchor) == 1
readme = readme.replace(anchor, '\n**Sage 2 response detail:** Two returned choices disagreed with the highest probability in the same response; both returned choices were incorrect and were scored as received. Substituting the highest probabilities would add two correct answers.\n\nOperational accuracy counts unusable requests', 1)
(out / 'README_V4.md').write_text(readme)

manifest = json.loads((out / 'manifest.json').read_text())
manifest['prior_hosted_successor_manifest_sha256'] = hashlib.sha256((prior / 'manifest.json').read_bytes()).hexdigest()
manifest['files_sha256'] = {str(p.relative_to(out)): hashlib.sha256(p.read_bytes()).hexdigest()
                            for p in sorted(out.rglob('*')) if p.is_file() and p.name != 'manifest.json'}
(out / 'manifest.json').write_text(json.dumps(manifest, indent=2, sort_keys=True) + '\n')
print('Preserved Kai and question-selection notes; moved accuracy chart before tables.')
