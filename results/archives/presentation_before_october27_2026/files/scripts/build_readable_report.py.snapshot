"""Readable presentation of sealed statistics. No calls, rescoring or question edits."""
from repo_layout import logical_relative, repo_file
import argparse
import csv
from hashlib import sha256
from html import escape
import io
import json
from pathlib import Path
import re
import shutil
import subprocess
import textwrap

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import to_hex
from matplotlib.ticker import PercentFormatter
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SOURCE = repo_file('consolidated_2026-10-19', root=ROOT)
NAME = 'readable_2026-10-19'
DEST = repo_file(NAME, root=ROOT)
ARCHIVE = repo_file('presentation_archive_2026-10-19', root=ROOT)
COMMIT = '629343132e8da1bb4cf9b10c953a2ecdacac3439'
CHANGED = ('README.md', 'FUNCTIONS.md', 'docs/index.html', 'docs/functions.html',
           'docs/output_compliance.html', 'validate_consolidated_release.py',
           'test_consolidated_publication.py', '.github/workflows/october18-validate.yml')

LABELS = {
    'F01': 'Lookup and filtering', 'F02': 'Following if-then rules',
    'F03': 'Checking required conditions', 'F04': 'Combining AND, OR and NOT',
    'F05': 'All, some, none and sets', 'F06': 'Ordering by comparisons',
    'F07': 'Scheduling under constraints', 'F08': 'One-to-one assignments',
    'F09': 'Counting exactly true claims', 'F10': 'Truth-tellers and liars',
    'F11': 'Enough evidence or a conflict?', 'F12': 'Tracking swaps',
    'F13': 'Following step-by-step procedures', 'F14': 'Comparing time intervals',
    'F15': 'Tracking position and direction', 'F16': 'Resolving names and references',
    'F17': 'Tracking what others know', 'F18': 'Changing a cause',
    'F19': 'Exceptions and priority rules', 'F20': 'Planning valid action sequences',
    'F21': 'Following directed connections', 'F22': 'Ranking with tie-break rules',
    'F23': 'Finding rule violations', 'F24': 'Choosing authoritative current records',
    'F25': 'Diagnosing faults from evidence', 'F26': 'Risk with supplied probabilities',
    'F27': 'Is extra information worth its cost?',
    'F28': 'Worst-case choices without probabilities',
    'F29': 'Anticipating another decision-maker',
    'F30': 'Checking overlapping operations', 'F31': 'Detecting secret-information leaks',
}
GROUPS = (
    ('rules', 'Rules and evidence', ['F01', 'F02', 'F03', 'F04', 'F05', 'F11'],
     'Which facts meet a rule, which conclusions follow, and when is the evidence insufficient?'),
    ('ordering', 'Ordering, schedules and assignments', ['F06', 'F07', 'F08', 'F14', 'F22'],
     'Can the model combine comparisons, fit a schedule, assign unique partners and apply tie-break rules?'),
    ('state', 'Claims, changing state and perspectives', ['F09', 'F10', 'F12', 'F13', 'F15', 'F16', 'F17'],
     'Can the model count true statements, update a changing situation and separate what different observers know?'),
    ('causes', 'Causes, plans and exceptions', ['F18', 'F19', 'F20', 'F21', 'F23', 'F24', 'F25'],
     'Which actions work, which consequences change, and which rule or source controls when information conflicts?'),
    ('uncertainty', 'Risk, strategy and system behavior', ['F26', 'F27', 'F28', 'F29', 'F30', 'F31'],
     'These decisions involve uncertain outcomes, another actor, overlapping operations or possible information leaks.'),
)
SOURCES = ('README.md', 'FUNCTIONS.md', 'docs/index.html', 'docs/functions.html',
           'docs/output_compliance.html', 'build_readable_report.py', 'validate_readable_report.py',
           'test_readable_report.py', 'validate_consolidated_release.py',
           'test_consolidated_publication.py', '.github/workflows/october18-validate.yml')


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8')


def archive():
    seal = json.loads((SOURCE / 'release_checksums.json').read_text())
    files = {}
    for name in CHANGED:
        data = subprocess.check_output(['git', 'show', COMMIT + ':' + name], cwd=ROOT)
        h = sha256(data).hexdigest()
        assert h == seal[name], name
        target = ARCHIVE / (name + '.snapshot')
        if target.exists():
            assert target.read_bytes() == data
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        files[name] = {'archive_path': name + '.snapshot', 'sha256': h}
    data = json.dumps({'source_commit': COMMIT, 'files': files,
                       'purpose': 'Exact previous presentation and validation sources; numerical exports and questions are unchanged.'}, indent=2) + '\n'
    path = ARCHIVE / 'manifest.json'
    if path.exists():
        assert path.read_text() == data
    else:
        write(path, data)


def load():
    s = json.loads((SOURCE / 'statistics.json').read_text())
    with (SOURCE / 'function_guide.csv').open(newline='') as f:
        guide = {r['family_id']: r for r in csv.DictReader(f)}
    for fid, label in LABELS.items():
        guide[fid]['display_name'] = label
    guide['F26']['what_it_tests'] = 'Choose the action with the lowest probability-weighted cost, using the supplied likelihoods and costs.'
    guide['F28']['what_it_tests'] = 'Follow the stated worst-case rule when likelihoods are not supplied. Minimize either the largest possible loss or the largest regret (extra loss compared with the best action for each situation), as the question specifies. Do not invent probabilities.'
    guide['F28']['illustration'] = 'A route costs 4 in either situation; another costs 1 or 9. With no probabilities and a smallest-worst-case-cost rule, which route should be chosen?'
    guide['F27']['what_it_tests'] = 'Decide whether paying for a test before choosing an action reduces the probability-weighted cost enough to cover the test price.'
    guide['F27']['illustration'] = 'Should you buy a sensor reading before choosing an action, or is acting without the extra information cheaper overall?'
    guide['F29']['what_it_tests'] = 'Choose an action while accounting for the specified choices or payoff-maximizing response of another decision-maker.'
    guide['F29']['illustration'] = 'Which first move gives the best result after the other player chooses their own best reply?'
    guide['F30']['what_it_tests'] = 'Decide whether overlapping operations and their reported results can fit a permitted one-at-a-time order that respects the specified timing and object rules.'
    guide['F30']['illustration'] = 'Two processes read and change the same stored value. Could their reported results fit an allowed one-at-a-time order?'
    guide['F31']['what_it_tests'] = 'Check whether changing a protected secret can change an observable result in a way the stated policy forbids.'
    guide['F31']['illustration'] = 'If public inputs stay the same, could public output distinguish two secret values that the policy says must remain indistinguishable?'
    return s, guide


def short(label):
    for prefix,compact in (('GPT-6 Sol —','GPT-6 Sol (LLM, none)'),
                           ('Sonnet 5.5 —','Sonnet 5.5 (LLM, JSON)'),
                           ('Qwen3.8-Max —','Qwen3.8-Max (LLM, none)')):
        if label.startswith(prefix):
            return compact
    return label.replace('experimental (OpenRouter native adapter)', '(native adapter)').replace('Perplexity Decider Flash v1.2', 'Perplexity Flash v1.2')


def color(value):
    # Matplotlib treats integer 1 as palette index 1, not the 100% endpoint.
    rgba = plt.get_cmap('YlGnBu')(float(value))
    rgb = rgba[:3]
    def linear(x):
        return x / 12.92 if x <= .04045 else ((x + .055) / 1.055) ** 2.4
    lum = sum(a * linear(b) for a, b in zip((.2126, .7152, .0722), rgb))
    foreground = '#ffffff' if 1.05 / (lum + .05) >= (lum + .05) / .05 else '#000000'
    return to_hex(rgba), foreground


def score(cell):
    return f"{cell['correct']}/{cell['n']} ({cell['accuracy']:.1%})"


def leaders(s, fid):
    maximum = max(m['families'][fid]['correct'] for m in s['models'].values())
    names = [short(s['models'][mid]['label']) for mid in s['ranked_model_ids'] if s['models'][mid]['families'][fid]['correct'] == maximum]
    n = s['models'][s['ranked_model_ids'][0]]['families'][fid]['n']
    return ', '.join(names) + f' · {maximum}/{n} ({maximum/n:.1%})'


def plot(s, group):
    slug, title, fids, _ = group
    models = [s['models'][mid] for mid in s['ranked_model_ids']]
    values = np.array([[m['families'][fid]['accuracy'] for fid in fids] for m in models])
    with plt.rc_context({'font.family': 'DejaVu Sans', 'svg.fonttype': 'none', 'svg.hashsalt': 'readable-1342-v1'}):
        fig, ax = plt.subplots(figsize=(11.6, max(12.8, len(models)*.64)))
        im = ax.imshow(values, vmin=0, vmax=1, cmap='YlGnBu', aspect='auto')
        ax.set_yticks(range(len(models)), [short(m['label']) for m in models], fontsize=13)
        headers = ['\n'.join(textwrap.wrap(LABELS[fid], 12, break_long_words=False)) + f"\n{models[0]['families'][fid]['n']} questions" for fid in fids]
        ax.set_xticks(range(len(fids)), headers, fontsize=12)
        ax.tick_params(length=0, labeltop=True, labelbottom=False, pad=9)
        ax.set_xticks(np.arange(-.5, len(fids), 1), minor=True)
        ax.set_yticks(np.arange(-.5, len(models), 1), minor=True)
        ax.grid(which='minor', color='white', linewidth=1.1)
        ax.tick_params(which='minor', length=0)
        for i, m in enumerate(models):
            for j, fid in enumerate(fids):
                c = m['families'][fid]
                ax.text(j, i, f"{c['correct']}/{c['n']}\n{c['accuracy']:.1%}", ha='center', va='center',
                        fontsize=13, linespacing=1.1, color=color(c['accuracy'])[1])
        for spine in ax.spines.values():
            spine.set_visible(False)
        cb = fig.colorbar(im, ax=ax, fraction=.025, pad=.025, shrink=.8)
        cb.ax.yaxis.set_major_formatter(PercentFormatter(xmax=1))
        cb.ax.tick_params(labelsize=11)
        cb.set_label('Correct first decisions', fontsize=12)
        fig.text(.025, .975, title, ha='left', va='top', fontsize=20, weight='bold')
        fig.text(.025, .938, f'Each cell: correct / questions, then percentage. All {len(models)} routes, in overall-score order.', fontsize=11)
        fig.text(.025, .055, 'Darker blue = higher accuracy. Fixed 0-100% scale; random guessing = 20%.\nPercentages are rounded; counts are exact. All first attempts, including failures, remain in the denominator.', fontsize=10.5, linespacing=1.6)
        if slug == 'uncertainty':
            fig.text(.025, .017, 'Eight questions per category: one answer changes the score by 12.5 percentage points.', fontsize=10.5)
        fig.subplots_adjust(left=.315, right=.94, top=.79, bottom=.11)
        # Check rendered bounds rather than guessing that character wraps fit.
        # Only header type shrinks, within a fixed readable lower bound.
        for header_size in (12, 11.5, 11, 10.5):
            for label in ax.get_xticklabels():
                label.set_fontsize(header_size)
            fig.canvas.draw()
            renderer = fig.canvas.get_renderer()
            boxes = [label.get_window_extent(renderer) for label in ax.get_xticklabels()]
            if all(a.x1 + 3 < b.x0 for a, b in zip(boxes, boxes[1:])):
                break
        else:
            raise AssertionError('Category chart headers overlap: ' + slug)
        for suffix in ('png', 'svg'):
            fig.savefig(DEST / (slug + '.' + suffix), dpi=160, metadata={'Date': None} if suffix == 'svg' else {})
        plt.close(fig)


def matrix(s, fids):
    th = '<thead><tr><th scope="col">Model</th>' + ''.join(f'<th scope="col"><a href="#category-{fid}">{escape(LABELS[fid])}</a><small>{s["models"][s["ranked_model_ids"][0]]["families"][fid]["n"]} questions</small></th>' for fid in fids) + '</tr></thead>'
    rows = []
    for mid in s['ranked_model_ids']:
        m = s['models'][mid]
        cells = []
        for fid in fids:
            c = m['families'][fid]; bg, fg = color(c['accuracy'])
            cells.append(f'<td data-model="{mid}" data-category="{fid}" data-correct="{c["correct"]}" data-n="{c["n"]}" style="background:{bg};color:{fg}"><strong>{c["correct"]}/{c["n"]}</strong><span>{c["accuracy"]:.1%}</span></td>')
        rows.append('<tr><th scope="row">' + escape(m['label']) + '</th>' + ''.join(cells) + '</tr>')
    return '<div class="category-matrix" tabindex="0" role="region" aria-label="Category scores; scroll horizontally on narrow screens"><table>' + th + '<tbody>' + ''.join(rows) + '</tbody></table></div>'


def cards(s, guide, fids):
    result = []
    for fid in fids:
        g = guide[fid]
        rankings = sorted(s['ranked_model_ids'], key=lambda mid: -s['models'][mid]['families'][fid]['correct'])
        rows = []
        for mid in rankings:
            m = s['models'][mid]; c = m['families'][fid]
            bg, fg = color(c['accuracy'])
            rows.append('<tr><th scope="row">' + escape(m['label']) + f'</th><td style="background:{bg};color:{fg}">' + escape(score(c)) + '</td></tr>')
        result.append(f'<article class="category-card" id="category-{fid}"><h4>{escape(g["display_name"])}</h4><p class="category-meta">{fid} · {g["questions"]} questions</p><p>{escape(g["what_it_tests"])}</p><p class="example"><b>Example:</b> {escape(g["illustration"])}</p><p><b>Highest observed:</b> {escape(leaders(s, fid))}</p><details><summary>All 20 models in this category</summary><div class="ranked-category"><table><thead><tr><th>Model</th><th>Correct / questions (%)</th></tr></thead><tbody>{"".join(rows)}</tbody></table></div></details></article>')
    return '<div class="category-cards">' + ''.join(result) + '</div>'


CSS = '''
main{max-width:1280px}.category-section{margin:44px 0 60px;scroll-margin-top:20px}.category-section>h3{font-size:1.65rem;margin-bottom:10px}.category-nav{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px;margin:20px 0}.category-nav a{background:white;border:1px solid #cbdce5;padding:16px;border-radius:8px;line-height:1.4}.category-guide{background:#e9f2f6;padding:20px 24px;border-radius:8px}.category-guide li{margin:8px 0}.accuracy-legend{display:flex;gap:6px;flex-wrap:wrap;margin:16px 0}.accuracy-legend span{padding:6px 13px;border:1px solid #bacbd4;border-radius:4px}.category-matrix{overflow:auto;max-height:950px;border:1px solid #b7ccd8;border-radius:8px;background:white;margin:24px 0;isolation:isolate}.category-matrix table{width:100%;table-layout:fixed;font-size:16px;min-width:930px}.category-matrix th,.category-matrix td{padding:13px 10px;white-space:normal;text-align:center;vertical-align:middle}.category-matrix thead th{top:0;background:#e8f0f5;z-index:3;line-height:1.4;font-weight:650}.category-matrix thead small{display:block;font-size:13px;margin-top:8px;color:#405b6d}.category-matrix th:first-child{position:sticky;left:0;width:230px;text-align:left;background:#f0f5f8;z-index:2;border-right:2px solid #b7ccd8;overflow-wrap:anywhere}.category-matrix thead th:first-child{z-index:4}.category-matrix tbody th{font-weight:600;font-size:15px}.category-matrix td strong,.category-matrix td span{display:block}.category-matrix td strong{font-size:18px}.category-matrix td span{font-size:14px;margin-top:3px}.category-cards{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px;margin:25px 0}.category-card{background:white;border:1px solid #cedee8;border-top:4px solid #307d9c;border-radius:8px;padding:20px;scroll-margin-top:20px;min-width:0}.category-card h4{font-size:1.15rem;margin:0 0 8px}.category-card p{margin:10px 0}.category-meta{color:#536b7e;font-size:.9rem}.example{background:#f2f6f8;padding:12px;border-radius:4px}.category-card details{padding:12px;margin:15px 0 0}.ranked-category{overflow:auto}.ranked-category table{font-size:14px}.ranked-category th{white-space:normal;position:static}.ranked-category td{white-space:nowrap}.category-chart img{width:100%;max-width:1000px;display:block;margin:auto}.category-section>details{padding:14px 20px}.category-section>details summary{margin-bottom:10px}.category-section>p{max-width:1050px}@media(max-width:700px){.category-cards{grid-template-columns:1fr}.category-guide{padding:15px}.category-matrix th:first-child{width:170px}.category-matrix table{min-width:900px}.category-matrix tbody th{font-size:14px}.category-nav{grid-template-columns:1fr}.category-section>h3{font-size:1.35rem}.category-card{padding:16px}.category-section{margin:32px 0}.category-chart{overflow:auto}.category-chart img{min-width:830px}}
'''


def clarity_section(s, guide):
    parts = ['<section id="functions"><h2>Category scores: what each task means</h2>',
        '<p>All 31 categories are arranged into five reading groups. These groups organize the display only; they do not change the benchmark, its weighting or any score.</p>',
        '<div class="category-guide"><h3>How to read these results</h3><ul><li>Read a row to compare one model across the named tasks. Read a column to compare models on one task.</li><li>Each cell gives <b>correct answers / questions</b>, followed by the percentage. For example, <b>6/8 · 75%</b> means six correct first decisions out of eight, not a confidence rating.</li><li>Darker blue means higher accuracy on the same fixed 0-100% scale throughout. Random guessing among five choices averages 20%. Percentages help compare differently sized categories; counts show the size of the evidence.</li><li>The model names stay visible when you scroll sideways. On a narrow screen, each explanation card also has an <b>All 20 models</b> list with no wide matrix to decode.</li><li>Small categories are coarse: one answer changes an eight-question category by 12.5 percentage points. A perfect sampled score is not a reliability guarantee.</li></ul></div>']
    parts.append('<nav class="category-nav" aria-label="Category groups">' + ''.join(f'<a href="#group-{slug}">{escape(title)}<small> · {len(fids)} categories</small></a>' for slug, title, fids, _ in GROUPS) + '</nav>')
    parts.append('<div class="accuracy-legend" aria-label="Fixed accuracy color scale">' + ''.join(f'<span style="background:{color(v)[0]};color:{color(v)[1]}">{v:.0%}</span>' for v in (0, .2, .4, .6, .8, 1)) + '</div>')
    for slug, title, fids, intro in GROUPS:
        if slug == 'uncertainty':
            parts.append('<div id="domains"></div>')
        parts.append(f'<section class="category-section" id="group-{slug}"><h3>{escape(title)}</h3><p>{escape(intro)}</p>')
        if slug == 'uncertainty':
            parts.append('<p><b>“Without probabilities” means exactly that:</b> the question gives possible situations and their costs, but does not say how likely each situation is. The model must use the specified worst-case loss or regret rule, rather than inventing an average.</p>')
        parts.append(matrix(s, fids))
        parts.append('<p class="small">Rows keep the same overall-score order in every group. This is not a category-specific ranking. Expand a category card below for its own ranking.</p>')
        parts.append(cards(s, guide, fids))
        parts.append(f'<details><summary>View or download the full-size chart for this group</summary><div class="category-chart"><a href="{slug}.svg"><img src="{slug}.png" alt="All 20 models: {escape(title)}; full category names, exact correct counts and percentages"></a></div><p><a href="{slug}.png">PNG</a> · <a href="{slug}.svg">SVG</a></p></details></section>')
    parts.append('<p><a href="category_scores.csv">Download the full named-category score matrix (CSV)</a>. Display names use plain language; stable category IDs and the tested data are unchanged. Examples explain the task types; they are illustrations, not additional scored questions.</p></section>')
    return ''.join(parts)


def plain(text):
    return text.replace('robust decision-making without a prior', 'worst-case choices without supplied probabilities').replace('Robust decisions without a prior', LABELS['F28'])


def markdown_groups(s, guide, details=False):
    from publish_consolidated_report import table
    text = '## Category scores and explanations\n\n'
    text += 'The 31 categories are grouped below so the labels and values remain readable. These are reading groups, not new scored categories. All 20 models remain in overall-score order. Every cell shows **correct / questions and percentage**. Darker blue means higher accuracy on a fixed 0-100% scale; uniform random guessing averages 20%. Different category sizes mean that percentages alone do not show how much evidence is available.\n\n'
    text += '[Open the color-coded, selectable tables](https://etsabary.github.io/jev-1.14-comparison-benchmark/readable_2026-10-19/report.html#functions), with a pinned model-name column and individual category rankings.\n\n'
    for slug, title, fids, intro in GROUPS:
        text += '### ' + title + '\n\n' + intro + '\n\n'
        if slug == 'uncertainty':
            text += '**Worst-case choices without probabilities** means choosing under a specified worst-case loss or regret rule when the likelihoods of possible situations are not supplied. There is no probability distribution to average over. Each of these six categories has eight questions, so one answer changes its score by 12.5 percentage points.\n\n'
        text += table(['Category', 'Questions', 'What it tests and a simple example'],
                      [[g['display_name'] + ' (' + fid + ')', g['questions'], g['what_it_tests'] + ' Example: ' + g['illustration']] for fid in fids for g in [guide[fid]]]) + '\n'
        text += f'![{title}: all 20 models, named categories, correct counts and percentages]({NAME}/{slug}.png)\n\n'
        text += f'[Full-size SVG]({NAME}/{slug}.svg) · [Color-coded table and category rankings](https://etsabary.github.io/jev-1.14-comparison-benchmark/{NAME}/report.html#group-{slug})\n\n'
        if details:
            text += table(['Model'] + [LABELS[fid] for fid in fids],
                          [[s['models'][mid]['label']] + [score(s['models'][mid]['families'][fid]) for fid in fids] for mid in s['ranked_model_ids']]) + '\n'
    text += 'Counts are exact; displayed percentages are rounded. A perfect result on a small sample is not a reliability guarantee. [Download the full category matrix](' + NAME + '/category_scores.csv).\n\n'
    return text


def seal_hashes():
    from archive_frontier_presentation import historical_path
    paths = {repo_file(name, root=ROOT) for name in SOURCES}
    for folder in (DEST, repo_file('docs', root=ROOT) / NAME, ARCHIVE):
        paths.update(p for p in folder.rglob('*') if p.is_file() and p.name != 'release_checksums.json')
    return {str(logical_relative(p, root=ROOT)): digest(historical_path(p)) for p in sorted(paths)}


def build():
    assert not (DEST / 'release_checksums.json').exists(), 'Never overwrite a sealed presentation; make a later version'
    archive()
    s, guide = load()
    DEST.mkdir(exist_ok=True)
    for group in GROUPS:
        plot(s, group)
    buf = io.StringIO(newline=''); out = csv.writer(buf)
    out.writerow(['category_id', 'category', 'questions'] + [s['models'][mid]['label'] for mid in s['ranked_model_ids']])
    for fid in sorted(LABELS):
        out.writerow([fid, LABELS[fid], guide[fid]['questions']] + [score(s['models'][mid]['families'][fid]) for mid in s['ranked_model_ids']])
    write(DEST / 'category_scores.csv', buf.getvalue())
    write(DEST / 'category_guide.json', json.dumps(guide, indent=2) + '\n')
    base = (SOURCE / 'report.html').read_text()
    base = re.sub(r'((?:href|src)=")([^"#:]+)(")', lambda m: m.group() if m[2].startswith(('https:', 'http:', 'mailto:', 'data:')) else m[1] + '../consolidated_2026-10-19/' + m[2] + m[3], base)
    base, count = re.subn(r'<section id="functions">.*?(?=<section id="quality">)', clarity_section(s, guide), base, flags=re.S)
    assert count == 1
    base = plain(base).replace('</style>', CSS + '</style>', 1)
    base = base.replace('href="../consolidated_2026-10-19/report.txt"', 'href="report.txt"')
    base = base.replace('<head>', '<head><meta name="benchmark-presentation" content="readable-category-tables">', 1)
    write(DEST / 'report.html', base)
    text = plain((SOURCE / 'report.txt').read_text()) + '\n\nCATEGORY EXPLANATIONS AND EXACT VALUES\n'
    for slug, title, fids, intro in GROUPS:
        text += '\n' + title.upper() + '\n' + intro + '\n'
        for fid in fids:
            g = guide[fid]
            text += '\n' + g['display_name'] + f" ({fid}, {g['questions']} questions)\n" + g['what_it_tests'] + '\nIllustration: ' + g['illustration'] + '\n'
            text += '\n'.join(s['models'][mid]['label'] + ': ' + score(s['models'][mid]['families'][fid]) for mid in s['ranked_model_ids']) + '\n'
    text += '\nIllustrations explain task types; they are not additional scored questions. Display labels and grouping changed; all measurements and tested question inputs are unchanged.\n'
    write(DEST / 'report.txt', text)
    old_readme = (ARCHIVE / 'README.md.snapshot').read_text()
    old_readme = plain(old_readme)
    a = old_readme.index('![All 31 function profiles]')
    b = old_readme.index('## Questions and statistics', a)
    readme = old_readme[:a] + markdown_groups(s, guide) + old_readme[b:]
    readme = readme.replace('Run `python3 validate_consolidated_release.py`', 'Run `python3 validate_readable_report.py`')
    readme = readme.replace('](consolidated_2026-10-19/report.txt)', '](' + NAME + '/report.txt)')
    readme = readme.replace('`publish_consolidated_report.py` rebuilds the presentation from the imported key-free bundle.', '`build_readable_report.py` builds this presentation from the unchanged, sealed key-free statistics. Sealed presentation artifacts are not overwritten.')
    write(repo_file('README.md', root=ROOT), readme)
    functions = '# The 31 decision categories: meanings and results\n\nAll scores below use the same 1,342 questions and 20 models as the [overall comparison](README.md). This page gives named categories, examples and exact values. [Use the color-coded tables](https://etsabary.github.io/jev-1.14-comparison-benchmark/readable_2026-10-19/report.html#functions) for comparison without decoding category IDs.\n\n' + markdown_groups(s, guide, details=True)
    write(repo_file('FUNCTIONS.md', root=ROOT), functions.rstrip() + '\n')
    for name, anchor in (('index.html', ''), ('functions.html', '#functions'), ('output_compliance.html', '#quality')):
        target = NAME + '/report.html' + anchor
        write(repo_file('docs', root=ROOT) / name, '<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="benchmark-cohort" content="october19-consolidated-1342"><meta http-equiv="refresh" content="0;url=' + target + '"><title>1,342 text decisions: readable category results</title></head><body><a href="' + target + '">Open the current benchmark</a></body></html>\n')
    payload = {'question_count': 1342, 'model_count': 20, 'category_count': 31,
               'source_statistics_sha256': digest(SOURCE / 'statistics.json'),
               'source_questions_sha256': digest(SOURCE / 'questions_1342.jsonl'),
               'numerical_results_changed': False, 'new_inference_calls': 0,
               'groups': [{'id': slug, 'title': title, 'category_ids': fids} for slug, title, fids, _ in GROUPS],
               'artifacts': {p.name: digest(p) for p in sorted(DEST.iterdir()) if p.is_file() and p.name != 'manifest.json'}}
    write(DEST / 'manifest.json', json.dumps(payload, indent=2) + '\n')
    pages = repo_file('docs', root=ROOT) / NAME
    pages.mkdir(parents=True, exist_ok=True)
    for path in DEST.iterdir():
        if path.is_file():
            shutil.copyfile(path, pages / path.name)
    print('Built five readable groups, 31 category explanations and 620 color-coded exact scores. No numerical changes.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seal', action='store_true')
    args = parser.parse_args()
    if args.seal:
        from validate_readable_report import validate
        validate()
        path = DEST / 'release_checksums.json'
        assert not path.exists(), 'Immutable presentation seal already exists'
        write(path, json.dumps(seal_hashes(), indent=2) + '\n')
    else:
        build()
