"""Publish the combined October18 report without rewriting archived evidence.

The hand-written/current analysis is LLM_EXPANSION.md. Only the active README,
FUNCTIONS, OUTPUT_COMPLIANCE and their three HTML pages are generated. Original
three-model pages and figures remain byte-preserved. New cohort figures are
copied below docs/figures/october18, never into the old root figures directory.
"""
from __future__ import annotations
from repo_layout import logical_relative, repo_file
from repo_layout import frozen_file

from hashlib import sha256
from html import escape, unescape
import json
import math
from pathlib import Path
import re
import shutil
from urllib.parse import quote, urlsplit, urlunsplit

import markdown
import build_report as old

ROOT = Path(__file__).resolve().parents[1]
SOURCE = repo_file('overall_llm_expanded_2026-10-18/summary.json', root=ROOT)
REPORT = repo_file('LLM_EXPANSION.md', root=ROOT)
REPO = old.REPO
LEGEND_HEADING = '## Reading the speed and cost colors'
COHORT_MARKER = '<meta name="benchmark-cohort" content="october18-combined">'
SPEED_LABELS = ('🟩 Fastest', '🟨 Fast', '🟧 Moderate', '🟥 Slow')
COST_LABELS = ('🟩 Lowest', '🟨 Low', '🟧 Mid', '🟥 Highest')
UNKNOWN = '⬜ Unknown'
PALETTES = ('#d8f1e8', '#fff4c2', '#ffe4ca', '#fbdedd')
TEXT_COLOR = '#193047'
TABLE_CSS = '''
.metric-cell{font-weight:600;white-space:nowrap;color:#193047}
.band-1{background:#d8f1e8}.band-2{background:#fff4c2}
.band-3{background:#ffe4ca}.band-4{background:#fbdedd}
.metric-unknown{background:#e7eaee;color:#193047}
.cost-incomplete{text-decoration-line:underline;text-decoration-style:dotted;text-decoration-color:#9a6700;text-underline-offset:.25em;border-bottom:2px solid #bd820c}
.legend-note{font-size:.9rem}main{min-width:0}table{overscroll-behavior-x:contain}
@media(max-width:640px){body{padding:18px 12px 56px}h1{font-size:1.8rem}th,td{padding:8px}table{font-size:.8rem}nav{gap:10px}}
'''


def numeric(value):
    if value is None or isinstance(value, bool):
        return None
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) and result >= 0 else None


def band(value, bounds, labels):
    value = numeric(value)
    if value is None:
        return UNKNOWN
    return labels[next((i for i, bound in enumerate(bounds) if value <= bound), len(bounds))]


def speed_band(ms):
    """Author-requested fixed thresholds, classified on unrounded milliseconds."""
    return band(ms, (250, 500, 1000), SPEED_LABELS)


def cost_band(usd_per1000):
    """Classify known/accounted USD per1000, not actual run dollars or a tariff."""
    return band(usd_per1000, (.01, .025, .05), COST_LABELS)


def format_speed(ms):
    return UNKNOWN if numeric(ms) is None else f'{float(ms):.0f} ms {speed_band(ms)}'


def format_cost(usd_per1000, missing_attempts=0, precision=5):
    text = UNKNOWN if numeric(usd_per1000) is None else f'${float(usd_per1000):.{precision}f} {cost_band(usd_per1000)}'
    return text + (' + ?' if missing_attempts else '')


def legend_markdown():
    return f'''{LEGEND_HEADING}

The squares and labels use fixed descriptive bands, not relative ranks or statistical significance. Speed uses the full-bank first-attempt median. Cost uses known or accounted dollars per 1,000 questions, normalized from each actual 1,136-question run including permitted recoveries.

| Band | Median response time | Known/accounted cost per 1,000 |
|---|---|---|
| Green | 🟩 Fastest: ≤250 ms | 🟩 Lowest: ≤$0.010 |
| Yellow | 🟨 Fast: >250 to ≤500 ms | 🟨 Low: >$0.010 to ≤$0.025 |
| Orange | 🟧 Moderate: >500 to ≤1,000 ms | 🟧 Mid: >$0.025 to ≤$0.050 |
| Red | 🟥 Slow: >1,000 ms | 🟥 Highest: >$0.050 |
| Gray | {UNKNOWN}: unavailable | {UNKNOWN}: unavailable |

Bands use unrounded measurements; displayed numbers can round to a boundary. `+ ?` means additional charges were not reported. In those cells, the cost band describes only the known lower bound, not a complete cost or a guaranteed price advantage. The website also underlines these incomplete costs in amber. Text labels remain visible without color.
'''


def annotate_metric_cells(body):
    """Labels survive GitHub Markdown; HTML adds accessible cell backgrounds."""
    def annotate(match):
        content = match.group(2)
        visible = unescape(re.sub(r'<[^>]+>', '', content))
        classes = []
        for labels, kind in ((SPEED_LABELS, 'speed'), (COST_LABELS, 'cost')):
            for index, label in enumerate(labels, 1):
                # Word boundary prevents Fast matching Fastest and Low matching
                # Lowest. Both the square and the word must match the label.
                if re.search(re.escape(label) + r'\b', visible):
                    classes += ['metric-cell', 'band-' + str(index), 'metric-' + kind]
                    break
        if UNKNOWN in visible:
            classes += ['metric-cell', 'metric-unknown']
        incomplete = bool(re.search(r'\+\s*\?', visible))
        if incomplete:
            classes.append('cost-incomplete')
        if not classes:
            return match.group(0)
        attributes = match.group(1)
        if 'class=' in attributes:
            attributes = re.sub(r'class="([^"]*)"', lambda m: 'class="' + m[1] + ' ' + ' '.join(dict.fromkeys(classes)) + '"', attributes)
        else:
            attributes += ' class="' + ' '.join(dict.fromkeys(classes)) + '"'
        if incomplete:
            attributes += ' title="Known cost only; additional charges unreported"'
        return '<td' + attributes + '>' + content + '</td>'
    return re.sub(r'<td([^>]*)>(.*?)</td>', annotate, body, flags=re.S)


def figure_mapping():
    mapping = {}
    folders = [('overall_llm_expanded_2026-10-18/figures', 'figures/october18'),
               ('overall_expanded_2026-10-18/figures', 'figures/october18/native')]
    for source, dest in folders:
        for path in sorted((repo_file(source, root=ROOT)).glob('*')):
            if path.is_file():
                mapping[str(logical_relative(path, root=ROOT))] = dest + '/' + path.name
    return mapping


def target_url(target, image_map=None, image=False):
    image_map = figure_mapping() if image_map is None else image_map
    parts = urlsplit(unescape(target))
    if parts.scheme or parts.netloc or target.startswith('#'):
        return unescape(target)
    path = parts.path.removeprefix('./')
    if path in image_map:
        return urlunsplit(('', '', image_map[path], parts.query, parts.fragment))
    pages = {'README.md': 'index.html', 'LLM_EXPANSION.md': 'index.html',
             'FUNCTIONS.md': 'functions.html', 'OUTPUT_COMPLIANCE.md': 'output_compliance.html',
             'THREE_MODEL_REFERENCE.md': 'three_model_reference.html'}
    if path in pages:
        return urlunsplit(('', '', pages[path], parts.query, parts.fragment))
    if image and path.startswith('figures/'):
        return target
    if image:
        return 'https://raw.githubusercontent.com/etsabary/jev-1.14-comparison-benchmark/main/' + quote(path, safe='/')
    kind = 'tree' if (repo_file(path, root=ROOT)).is_dir() else 'blob'
    return REPO + '/' + kind + '/main/' + quote(path, safe='/') + ('?' + parts.query if parts.query else '') + ('#' + parts.fragment if parts.fragment else '')


def render(text, title, image_map=None):
    body = markdown.markdown(text, extensions=['tables', 'fenced_code', 'toc'])
    body = re.sub(r'href="([^"]+)"', lambda m: 'href="' + escape(target_url(m[1], image_map), quote=True) + '"', body)
    body = re.sub(r'src="([^"]+)"', lambda m: 'src="' + escape(target_url(m[1], image_map, image=True), quote=True) + '"', body)
    body = annotate_metric_cells(body)
    # Reuse the established responsive page shell, not its outdated report
    # generation or relative-link mapper. The replacement body is already mapped.
    shell = old.render('', title)
    shell = shell.replace('<title>', COHORT_MARKER + '<title>', 1)
    shell = shell.replace('</style>', TABLE_CSS + '</style>', 1)
    shell = shell.replace('<main></main>', '<main>' + body + '</main>')
    shell = shell.replace('<a href="functions.html">Functions and load</a>',
                          '<a href="functions.html">Functions and load</a><a href="output_compliance.html">Output diagnostics</a>')
    return shell


def functions_markdown(summary):
    models = summary['models']
    order = sorted(summary['publication']['eligible_model_ids'], key=lambda m: -models[m]['primary']['correct'])
    text = (f'# Results by function and load level\n\n'
            f'The [main report](README.md) compares {len(order)} eligible configurations on the unchanged 1,136-question bank, tested October 15, 16 and 18, 2026. '
            'Every cell uses strict first-attempt results. Unranked full runs, stopped samples and failed interfaces remain in the [output diagnostics](OUTPUT_COMPLIANCE.md), not these tables. '
            'The 640 core scenarios and 496 dependent variants are not 1,136 independent observations.\n\n'
            + (repo_file('task_examples.md', root=ROOT)).read_text() + '\n## All 25 functions\n\n')
    text += old.table(['Function', 'n'] + [models[m]['label'] for m in order], [
        [f['family'], f['n']] + [f"{f['models'][m]['correct']} ({old.pct(f['models'][m]['correct'], f['n'])})" for m in order]
        for f in summary['by_family']])
    for field, heading in [('by_role', 'Core and related item types'), ('by_level', 'Engineered load levels')]:
        groups = list(models[order[0]][field])
        assert all(set(models[m][field]) == set(groups) for m in order)
        text += '## ' + heading + '\n\n' + old.table(['Group', 'n'] + [models[m]['label'] for m in order], [
            [group, models[order[0]][field][group]['attempted']] + [
                f"{models[m][field][group]['correct']} ({old.pct(models[m][field][group]['correct'], models[m][field][group]['attempted'])})" for m in order]
            for group in groups])
    return text.rstrip() + '\n'


def diagnostics_markdown(summary):
    models = summary['models']
    excluded = summary['publication']['excluded_model_ids']
    old_diagnostics = old.expand((repo_file('output_compliance_layout.md', root=ROOT)).read_text(), {
        'EXCLUDED_RESULTS': old.table(['Unranked diagnostic', 'Usable / 1,136', 'Model-output failures', 'Provider failures',
                                      'Correct among usable', 'Strict full-bank result', 'Median', 'Known run cost'], [
            [models[m]['label'], models[m]['primary']['answered'], summary['output_compliance'][m]['model_output_failures'],
             summary['output_compliance'][m]['provider_transport_failures'],
             f"{models[m]['primary']['correct']}/{models[m]['primary']['answered']} ({old.pct(models[m]['primary']['correct'], models[m]['primary']['answered'])})",
             f"{models[m]['primary']['correct']}/1,136 ({old.pct(models[m]['primary']['correct'], 1136)})",
             f"{models[m]['latency_first_all']['median_ms']:.0f} ms", f"${models[m]['cost_all_attempts']['known_usd']:.8f}"] for m in excluded])})
    text = old_diagnostics.rstrip() + '\n\n## October 18 stopped samples\n\n'
    text += ('The new generative candidates were screened after the fixed first 100 questions and rechecked cumulatively after each further 100. '
             'The author approved a hold for accuracy below 50%, model-output failures at least 5%, or median response time above 2,000 ms. '
             'The prefix has uneven family coverage and dependent variants; these are operational selection rules, not a representative full-bank accuracy estimate. '
             'Provider failures are distinct from explanations, refusals and malformed output. No stopped sample is extrapolated to 1,136 or included in the main ranking.\n\n')
    def money(cost):
        return f"${cost['known_usd']:.8f}" + (' + ?' if cost['missing_attempts'] else '')
    text += old.table(['Stopped configuration', 'Completed', 'Correct on completed', 'Model-output failures', 'Provider/transport failures',
                       'Sample median', 'Known actual sample cost', 'Unknown charges', 'Stop reasons'], [
        [v['label'], v['completed_first_attempts'],
         f"{v['primary_on_completed_only']['correct']}/{v['completed_first_attempts']}",
         v['output_compliance_completed']['model_output_failures'],
         v['output_compliance_completed']['provider_transport_failures'],
         format_speed(v['latency_completed_first']['median_ms']), money(v['cost_recorded_attempts']),
         v['cost_recorded_attempts']['missing_attempts'], ', '.join(v['stop_reasons'])]
        for v in summary['partial_samples'].values()])
    text += ('Sample costs above are actual recorded costs, not normalized per-1,000 prices. Their median bands describe only their observed sample. '
             '[Bound screening receipts and unchanged attempt ledgers](llm_additions_2026-10-18) retain the progression and the approved cutoffs.\n\n')
    solar = summary['partial_runs']['solar_decide']
    score = solar['primary_on_completed_only']
    text += (f"The separate native Solar Decide route was stopped for latency after {solar['completed_first_attempts']} recorded responses: "
             f"{score['correct']}/{score['attempted']} correct, with a {solar['latency_completed_first']['median_ms']:.0f} ms sample median. "
             f"It had {solar['additional_unresolved_charge_attempts']} unresolved dispatch whose result and charge remain unknown. "
             'It is not the Solar Pro 4 chat model in the table. Its [stop receipt and original partial evidence](native_additions_2026-10-18/solar_decide_partial) remain unchanged and are not replayed.\n\n')
    text += '## Compatibility-only interfaces\n\n'
    text += old.table(['Interface', 'Probe HTTP status', 'Recorded error', 'Known probe charge'], [
        [v['label'] + (' chat interface' if m == 'tev1_4b' else ''), v['http_status'], v['error_message'],
         'Unknown' if v['reported_probe_cost_usd'] is None else f"${v['reported_probe_cost_usd']:.8f}"]
        for m, v in summary['compatibility_only'].items()])
    text += ('These are unscored compatibility calls, not zero-accuracy benchmark runs. Tev subsequently completed all 1,136 questions through OpenRouter\'s native adapter; '
             'it remains a decision-specialized generative model, not an architectural non-generative control. Xing\'s free route returned a rate-limit error; this does not establish its decision accuracy.\n\n')
    cost = summary['llm_october_18_experiment_costs']
    text += ('## Separate experimental costs\n\n' + old.table(['Cost bucket', 'Known actual cost', 'Attempts with unknown charges'], [
        [label, money(cost[field]), cost[field]['missing_attempts']]
        for label, field in [('Four selected complete runs', 'selected_full_runs'),
                             ('Stopped samples', 'stopped_samples'), ('Compatibility probes', 'compatibility_probes'),
                             ('All new experimental calls', 'total_new_experiment')]])
        + '\nMissing charges are not zero. Only the four selected complete runs contribute to current full-bank model costs; '
          'stopped-sample and compatibility charges are separate and none of these totals is an independently reconciled invoice. '
          'The [current aggregate](overall_llm_expanded_2026-10-18/summary.json) retains exact amounts and counts.\n')
    return text


def reference_hashes():
    expected = json.loads((repo_file('expansion_2026-10-15/source_audit.json', root=ROOT)).read_text())['preserved_reference_reports']
    for name, digest in expected.items():
        assert sha256(frozen_file(repo_file(name, root=ROOT)).read_bytes()).hexdigest() == digest, 'Original reference report changed'
    return expected


def build():
    summary = json.loads(SOURCE.read_text())
    assert summary['model_count'] == 40 and summary['publication']['ranked_model_count'] == 37
    assert not summary['pending_model_ids'], 'Do not publish an unfinished expansion'
    references = reference_hashes()
    text = REPORT.read_text()
    assert 'hardening_2026-10-18' not in text and 'WORKED_EXAMPLES.md' not in text, 'Later hardening project is outside this publication'
    assert '{{' not in text, 'Unexpanded report field'
    if LEGEND_HEADING not in text:
        text = text.rstrip() + '\n\n' + legend_markdown()
    mapping = figure_mapping()
    required = ['overall_llm_expanded_2026-10-18/figures/' + name + '.png'
                for name in ('overall_accuracy', 'generative_accuracy_cost_speed', 'generative_family_accuracy')]
    assert all(name in mapping for name in required), 'Build all three new figures before replacing active reports'
    functions, diagnostics = functions_markdown(summary), diagnostics_markdown(summary)
    for name, content in [('README.md', text), ('FUNCTIONS.md', functions), ('OUTPUT_COMPLIANCE.md', diagnostics)]:
        (repo_file(name, root=ROOT)).write_text(content.rstrip() + '\n')
    docs = repo_file('docs', root=ROOT)
    (docs / 'figures').mkdir(parents=True, exist_ok=True)
    for path in sorted((repo_file('figures', root=ROOT)).iterdir()):
        assert path.is_file(), 'New figure directories must not enter the legacy root figures folder'
        dest = docs / 'figures' / path.name
        if not dest.exists() or dest.read_bytes() != path.read_bytes():
            shutil.copyfile(path, dest)
    for source, destination in mapping.items():
        dest = docs / destination
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(repo_file(source, root=ROOT), dest)
    for name, content, title in [('index.html', text, '37 models on 1,136 text decisions'),
                                  ('functions.html', functions, 'Text decisions by function and load'),
                                  ('output_compliance.html', diagnostics, 'Decision output diagnostics')]:
        (docs / name).write_text(render(content, title, mapping))
    assert reference_hashes() == references
    print('Built current40-complete/37-ranked README, function tables, diagnostics and Pages; original reference evidence preserved')


if __name__ == '__main__':
    build()
