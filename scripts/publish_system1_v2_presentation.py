"""Presentation-only successor to the immutable v2 capture. No inference."""
import argparse
import collections
from decimal import Decimal
import html
import json
from pathlib import Path
import re
import shutil
import subprocess
import textwrap

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import colormaps, colors
import numpy as np
from markdown import markdown

import publish_system1_v2 as frozen

ROOT = frozen.ROOT
NAME = 'system1_v2_presentation_2026-11-01'
SOURCE = ROOT / 'results/releases' / NAME
ARCHIVE = ROOT / 'results/archives/presentation_before_v2_visual_restoration_2026-11-01'
PUBLIC_SOURCES = ['scripts/' + n for n in [
    'publish_system1_v2_presentation.py', 'validate_system1_v2_presentation.py',
    'test_system1_v2_presentation.py']]
INPUTS = frozen.INPUTS + ['cost_statistics.json', 'cost_evidence.csv.gz']
ROLE_COLORS = {'Hosted native': '#16728c', 'Local native': '#7c3aed', 'LLM reference': '#806100'}
BANDS = ('#d8f1e8', '#fff4c2', '#ffe4ca', '#fbdedd')
BAND_NAMES = ('Green', 'Yellow', 'Orange', 'Red')
GRAY = '#edf0f2'
GROUPS = [
    ('rules', 'Rules, evidence and logical scope', ['F01', 'F02', 'F03', 'F04', 'F05', 'F11']),
    ('ordering', 'Ordering, schedules and assignments', ['F06', 'F07', 'F08', 'F14', 'F22']),
    ('state', 'State tracking and perspectives', ['F09', 'F10', 'F12', 'F13', 'F15', 'F16', 'F17']),
    ('causes', 'Causes, plans and authoritative evidence', ['F18', 'F19', 'F20', 'F21', 'F23', 'F24', 'F25']),
    ('uncertainty', 'Decisions under uncertainty', ['F26', 'F27', 'F28', 'F29', 'F30', 'F31']),
    ('practical_actions', 'Practical decisions: scope, policy and actions', ['P01', 'P02', 'P03', 'P04', 'P05']),
    ('practical_evidence', 'Practical decisions: evidence, security and quality', ['P06', 'P07', 'P08', 'P09', 'P10']),
]
esc = lambda v: html.escape(str(v), quote=True)
pct = frozen.pct
load, sha, write = frozen.load, frozen.sha, frozen.write


def band(value, bounds):
    if value is None:
        return None
    return next((i for i, limit in enumerate(bounds) if Decimal(str(value)) <= Decimal(str(limit))), 3)


def speed_band(ms):
    return band(ms, (250, 500, 1000))


def cost_band(usd):
    return band(usd, ('.01', '.025', '.05'))


def accuracy_colors(value):
    rgb = colormaps['YlGnBu'](float(value))[:3]
    linear = [v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4 for v in rgb]
    luminance = sum(v * w for v, w in zip(linear, (.2126, .7152, .0722)))
    black = (luminance + .05) / .05
    white = 1.05 / (luminance + .05)
    return colors.to_hex(rgb), '#000000' if black >= white else '#ffffff'


def competition_ranks(rows):
    return {mid: 1 + sum(int(c['correct']) > int(row['correct']) for _, c in rows)
            for mid, row in rows}


def model_name(mid, models):
    m = models[mid]
    return '<span class="model-name" style="color:' + ROLE_COLORS[m['role']] + '">' + esc(m['label']) + '</span>'


def speed_cell(value):
    i = speed_band(value)
    return f'<td style="background:{BANDS[i]}" data-speed-band="{i}">{value:,.0f} ms <small>{BAND_NAMES[i]}</small></td>'


def cost_text(c):
    kind = c['evidence_kind']
    if kind == 'local_unmeasured':
        return 'Unmetered local', 'Hardware and electricity unmeasured; no API charge recorded'
    if kind == 'unknown':
        return 'Unknown', 'No monetary receipt or supported captured tariff'
    if kind == 'free_access_tariff':
        return '$0 access*', 'Public free access at collection; not a monetary receipt or future price promise'
    suffix = ' + ?' if c['unknown_count'] else ''
    value = '$' + f"{Decimal(c['known_usd_per_1000']):.5f}" + suffix
    if c['tariff_estimate_count'] or c['free_access_tariff_count']:
        basis = 'Tariff estimate / access terms'
        if c['free_access_tariff_count']:
            basis += f"; {c['free_access_tariff_count']} promotional free-access calls"
    else:
        basis = 'API-reported charges'
    if c['unknown_count']:
        basis += f"; {c['unknown_count']} charges unknown (known subtotal only)"
    return value, basis


def cost_cell(c):
    value, basis = cost_text(c)
    i = cost_band(c['known_usd_per_1000']) if c['evidence_kind'] not in ['local_unmeasured', 'unknown', 'free_access_tariff'] else None
    bg = GRAY if i is None else BANDS[i]
    return f'<td class="cost {"incomplete" if c["unknown_count"] else ""}" style="background:{bg}" data-cost-kind="{c["evidence_kind"]}">{esc(value)}<small>{esc(basis)}</small></td>'


LEGEND_MD = '''The colours answer different questions; their scales stay fixed across every model and category.

| Encoding | Meaning and rationale |
| --- | --- |
| Teal model names / bars | Hosted native decision models |
| Purple model names / bars | Local CUDA decision configurations |
| Gold model names / pale gold bars | Reasoning-disabled LLM reference configurations |
| Pale yellow → green → dark blue cells | Absolute category accuracy, fixed 0–100%. Each cell also prints correct / tested and percentage. Darker blue means more correct answers. Black or white text follows contrast. A border and ★ mark all tied leaders. |
| Blue → white → red in the relative-profile figure | Below → near → above the score expected after removing model and category averages. Fixed −30 to +30 percentage points. This shows descriptive specialties; it is a different scale from absolute accuracy. |
| Green / yellow / orange / red timing | ≤250 / ≤500 / ≤1,000 / >1,000 ms. Median and p95 are classified separately. |
| Green / yellow / orange / red cost | ≤$0.010 / ≤$0.025 / ≤$0.050 / >$0.050 per 1,000 questions. Uses the unrounded known subtotal / 1,934 × 1,000. |
| ● / ◆ cost marks | API-reported charges / captured tariff estimates. Free-access and local costs are labelled separately. |
| + ? / grey | Additional charges missing / no comparable monetary measurement. A partial cost is a known subtotal, not a complete price. |

These speed and cost bands restore the earlier fixed thresholds. They make slow tails and expensive configurations easy to find; they are descriptive bands, not statistical outlier tests or significance claims. Displayed numbers can round to a boundary. Role colours identify deployment, not quality; only accuracy cells encode correctness. Category leaders share a rank when their counts tie.
'''

COST_MD = '''Costs now use the selected primary calls on the same 1,934 inputs as the scores. The answer-free cost ledger joins to all 73,492 timing records by model, item, native-input hash and source-record hash. Warmups, probes, recovery attempts, model reviews and account balances are excluded. USD per 1,000 is the known run subtotal divided by 1,934 and multiplied by 1,000; it is not the bill for a separate 1,000-call run.

**Reported charges and estimates are different evidence.** Reported charges retain the provider's recorded monetary amount, including cache accounting where supplied. Estimates use captured per-call usage and tariffs at collection, including tariff changes between baseline and additions. They are not recalculated at today's prices. Recorded zero-dollar receipts, when present, remain receipts; a public or promotional free endpoint without a receipt is labelled free access instead.

**Missing charges stay missing.** Opus has 1,751 monetary records and 183 missing charges; its displayed $4.13548 per 1,000 is only the known subtotal, followed by + ?. This is separate from its 185 declared refusals. Fastino and Celeris use tariff estimates. Mammoth and Elephant mix a promotional free baseline with priced additions and therefore have positive estimated totals. D3 Ultra and Amos used free public access, not metered receipts. Turion has no supported monetary total. Local hardware and electricity were not measured and are never shown as $0 inference.

The comparison describes these captured routes, input lengths, collection dates and access terms. It does not promise future tariffs or equivalent production bills. Cost-status records are available for all 38 measured configurations; the main cost chart and table retain the same 26-model selection as the accuracy comparison. Identity/telemetry metadata preserves the initial v2 capture unchanged; its original “cost not consolidated” note is superseded by these separate cost summaries and ledger.
'''

INTRO_MD = '''This benchmark asks a practical question: **how accurately, quickly and cheaply can a model choose the right action from a fixed set of options?** Every model receives the same native decision inputs. The tasks span logical constraints, state tracking, uncertainty, and practical choices about authorization, policy, evidence and tool use. Accuracy is measured alongside complete response time, coverage and cost, so a fast service that rejects hard inputs cannot look stronger simply by leaving them out.

V2 contains **1,934 questions across 41 categories**: the original 1,342 inputs, 192 additions to six existing categories, and 400 questions in ten new practical categories. The six expanded categories now contain 40 questions each; each new category also contains 40. The 120 companion diagnostics remain separate. The expansion provides more resolution and leaves headroom on harder decisions while preserving the earlier bank exactly.

The main comparison shows **26 configurations with at least 62% overall accuracy**: 20 hosted decision models, three local configurations and three reasoning-disabled LLM references. All 38 measurements remain downloadable. Model selection is applied once to overall accuracy; weak individual category results remain visible. These are measured configurations and routes, rather than a claim about every mode of a model family.
'''


def save_figure(fig, dest, name, mids, **extra):
    description = json.dumps(dict(model_ids=mids, minimum_overall_accuracy=.62, **extra), sort_keys=True)
    fig.savefig(dest / (name + '.png'), dpi=150, bbox_inches='tight', metadata={'Description': description})
    fig.savefig(dest / (name + '.svg'), bbox_inches='tight', metadata={'Date': None, 'Description': description})
    plt.close(fig)
    p = dest / (name + '.svg')
    p.write_text('\n'.join(line.rstrip() for line in p.read_text().splitlines()) + '\n')


def plot_overview(dest, s, costs):
    mids, models = s['ranked_model_ids'], s['models']
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10, 'svg.hashsalt': NAME})
    fig, axes = plt.subplots(1, 3, figsize=(21, 13.5), sharey=True,
                             gridspec_kw={'width_ratios': [1.1, 1.15, 1.15]})
    ax, bx, cx = axes
    yy = np.arange(len(mids))
    role_colors = [('#f3df98' if models[m]['role'] == 'LLM reference' else ROLE_COLORS[models[m]['role']]) for m in mids]
    ax.barh(yy, [100 * models[m]['accuracy'] for m in mids], color=role_colors, height=.64)
    ax.set_yticks(yy, [models[m]['label'] for m in mids], fontsize=10)
    ax.invert_yaxis()
    for label, mid in zip(ax.get_yticklabels(), mids):
        label.set_color(ROLE_COLORS[models[mid]['role']]); label.set_fontweight('bold')
    ax.set_xlim(0, 105)
    ax.set_title('ACCURACY', loc='left', fontsize=13, fontweight='bold', pad=18)
    ax.set_xlabel('Correct / 1,934 · strict accuracy (%)')
    for y, mid in enumerate(mids):
        m = models[mid]
        ax.text(100 * m['accuracy'] + .8, y, f"{m['accuracy']:.2%}", va='center', fontsize=9)
        bx.plot([m['median_ms'], m['p95_ms']], [y, y], color='#9ca7b0', lw=1, zorder=1)
        for value, marker, size in [(m['median_ms'], 'o', 65), (m['p95_ms'], 'D', 32)]:
            bx.scatter(value, y, s=size, marker=marker, facecolor=BANDS[speed_band(value)], edgecolor='#263d48', linewidth=.6, zorder=3)
        bx.text(1.02, y, f"{m['median_ms']:,.0f} / {m['p95_ms']:,.0f}", transform=bx.get_yaxis_transform(), va='center', fontsize=8)
        c = costs[mid]
        value, _ = cost_text(c)
        if c['evidence_kind'] in ['unknown', 'local_unmeasured', 'free_access_tariff']:
            cx.text(.01, y, value, transform=cx.get_yaxis_transform(), va='center', fontsize=9, color='#56636a')
        else:
            amount = float(c['known_usd_per_1000'])
            estimated = c['tariff_estimate_count'] + c['free_access_tariff_count'] > 0
            cx.scatter(amount, y, marker='D' if estimated else 'o', s=60,
                       facecolor=BANDS[cost_band(amount)], edgecolor='#263d48', linewidth=.7, zorder=3)
            cx.annotate(value, (amount, y), xytext=(7, 0), textcoords='offset points', va='center', fontsize=9,
                        color='#8e440c' if c['unknown_count'] else '#17212c')
    bx.set_xscale('log'); bx.set_xlim(min(models[m]['median_ms'] for m in mids)*.75, max(models[m]['p95_ms'] for m in mids)*1.15)
    bx.set_title('COMPLETE RESPONSE', loc='left', fontsize=13, fontweight='bold', pad=18)
    bx.set_xlabel('Milliseconds, log scale · ● median / ◆ p95')
    cx.set_xscale('log'); cx.set_xlim(.003, 35)
    cx.set_title('COST / 1,000 QUESTIONS', loc='left', fontsize=13, fontweight='bold', pad=18)
    cx.set_xlabel('USD, log scale · ● reported / ◆ estimated')
    for a in axes:
        a.spines[['top', 'right', 'left']].set_visible(False)
        a.grid(axis='x', alpha=.16); a.set_axisbelow(True); a.tick_params(axis='y', length=0)
    fig.subplots_adjust(left=.24, right=.97, top=.91, bottom=.11, wspace=.53)
    fig.suptitle('System 1 Decision Benchmark v2', x=.04, y=.98, ha='left', fontsize=24, fontweight='bold')
    fig.text(.04, .943, '1,934 questions · 41 categories · the same 26 qualifying configurations in every panel', fontsize=13)
    fig.text(.04, .045, 'Teal: hosted decisions   Purple: local CUDA   Gold: LLM references with reasoning disabled.  Green → yellow → orange → red: fixed speed / cost bands.', fontsize=10)
    fig.text(.04, .022, '+ ? = missing charges; known subtotal only. $0 access* = free endpoint, not receipts. Unmetered local excludes hardware/electricity. See the cost evidence table and legend.', fontsize=10)
    save_figure(fig, dest, 'overview', mids)


def plot_groups(dest, s, guide, lookup):
    mids, models = s['ranked_model_ids'], s['models']
    for slug, title, fids in GROUPS:
        a = np.array([[float(lookup[mid, fid]['accuracy']) for fid in fids] for mid in mids])
        best = a.max(axis=0)
        fig, ax = plt.subplots(figsize=(14.5, 13.5))
        im = ax.imshow(a, vmin=0, vmax=1, cmap='YlGnBu', aspect='auto')
        ax.set_yticks(range(len(mids)), [models[m]['label'] for m in mids], fontsize=9)
        for label, mid in zip(ax.get_yticklabels(), mids):
            label.set_color(ROLE_COLORS[models[mid]['role']]); label.set_fontweight('bold')
        names = [fid + '\n' + '\n'.join(textwrap.wrap(guide[fid]['display_name'], 19)) + f"\nn = {guide[fid]['questions']}" for fid in fids]
        ax.set_xticks(range(len(fids)), names, fontsize=10)
        ax.tick_params(top=True, labeltop=True, bottom=False, labelbottom=False, length=0, pad=10)
        ax.set_xticks(np.arange(-.5, len(fids)), minor=True)
        ax.set_yticks(np.arange(-.5, len(mids)), minor=True)
        ax.grid(which='minor', color='#ffffff', linewidth=1); ax.tick_params(which='minor', bottom=False, left=False)
        for y, mid in enumerate(mids):
            for x, fid in enumerate(fids):
                c = lookup[mid, fid]
                _, fg = accuracy_colors(a[y, x])
                leader = a[y, x] == best[x]
                ax.text(x, y, f"{c['correct']}/{c['n']}" + (' ★' if leader else '') + f"\n{a[y,x]:.1%}", ha='center', va='center', fontsize=9, color=fg)
                if leader:
                    from matplotlib.patches import Rectangle
                    ax.add_patch(Rectangle((x-.46, y-.45), .92, .90, fill=False, edgecolor=fg, linewidth=1.1))
        bar = fig.colorbar(im, ax=ax, orientation='horizontal', fraction=.025, pad=.025, ticks=[0, .2, .4, .6, .8, 1])
        bar.ax.set_xticklabels(['0%', '20%', '40%', '60%', '80%', '100%'])
        bar.set_label('Absolute accuracy · one fixed scale for all seven figures · ★ all tied observed leaders', fontsize=10)
        fig.suptitle(title, x=.02, y=.995, fontsize=19, fontweight='bold', ha='left')
        fig.text(.02, .008, 'Same overall model order throughout. Overall cutoff ≥62%; individual category scores remain visible at every value.', fontsize=10)
        fig.subplots_adjust(left=.30, top=.86, bottom=.065, right=.985)
        save_figure(fig, dest, 'categories_' + slug, mids, family_ids=fids, accuracy_scale=[0, 1])


CSS = frozen.CSS + '''
body{background:#e9eef0;color:#172830}main{max-width:1480px;padding:54px 34px}h1{font-family:Georgia,serif;font-size:54px;letter-spacing:-1.6px;max-width:950px}h2{font-family:Georgia,serif;font-size:32px;border-top:2px solid #173b46;padding-top:22px;margin-top:54px}h3{font-size:22px}p{max-width:1080px}.eyebrow{font:700 12px/1.5 system-ui;letter-spacing:2px;text-transform:uppercase;color:#16728c}.lead{font-size:20px}.model-name{font-weight:700}.score{font-weight:650;text-align:center;min-width:105px;white-space:nowrap}.score.leader{box-shadow:inset 0 0 0 2px currentColor}small{display:block;font-size:11px;line-height:1.35;margin-top:4px;color:inherit}.cost{min-width:160px;max-width:260px}.incomplete{border-bottom:3px solid #b65c0c}table{font-variant-numeric:tabular-nums}th{position:sticky;top:0;background:#e9eef1;z-index:1}.matrix th:first-child,.matrix td:first-child{position:sticky;left:0;background:#fff;z-index:2;min-width:230px}.matrix th:first-child{z-index:3}.matrix th{min-width:105px;white-space:normal;text-align:center}.matrix th:first-child{text-align:left}.matrix td{padding:7px}.legend-graphic{max-width:1100px}.note{background:#edf5f5;border-left:4px solid #16728c;padding:14px 20px}.metrics{display:grid;grid-template-columns:repeat(4,1fr);border-top:1px solid #b7c8cd;border-bottom:1px solid #b7c8cd;margin:28px 0}.metrics div{padding:20px 15px;border-right:1px solid #b7c8cd}.metrics strong{font:700 30px Georgia,serif;display:block}.metrics span{font-size:13px}.group-nav{display:flex;flex-wrap:wrap;gap:8px 20px}.scroll{margin:18px 0}a:focus-visible,summary:focus-visible{outline:3px solid #16728c;outline-offset:3px}summary{font-size:16px}details{border-radius:0}.rank td:nth-child(2){min-width:230px}.rank .score{min-width:120px}.figure-caption{font-size:13px;color:#53616a}nav{border-bottom:1px solid #bbcbd0;padding-bottom:18px}@media(max-width:700px){main{padding:26px 14px}h1{font-size:36px}h2{font-size:27px}.metrics{grid-template-columns:repeat(2,1fr)}.matrix td:first-child,.matrix th:first-child{position:static;min-width:190px}}
'''


CSS += 'input,select{box-sizing:border-box;max-width:100%}label{display:block}code{overflow-wrap:anywhere}'


def legend_graphic(dest):
    fig, ax = plt.subplots(figsize=(12, 2.3))
    gradient = np.linspace(0, 1, 256)[None, :]
    ax.imshow(gradient, cmap='YlGnBu', aspect='auto', extent=[0, 100, 0, 1])
    ax.set_yticks([]); ax.set_xticks([0, 20, 40, 60, 80, 100], ['0%', '20%', '40%', '60%', '80%', '100%'])
    ax.set_title('Category accuracy: fixed 0–100% across every table and figure', loc='left', fontsize=13, fontweight='bold')
    fig.text(.08, .015, 'Teal names = hosted     Purple names = local CUDA     Gold names = LLM reference     ★ = all tied category leaders', fontsize=10)
    fig.subplots_adjust(bottom=.3, top=.68)
    save_figure(fig, dest, 'accuracy_legend', [])


def score_cell(mid, fid, c, best, ranking=False):
    bg, fg = accuracy_colors(c['accuracy'])
    lead = int(c['correct']) == best
    key = 'data-rank-correct' if ranking else 'data-correct'
    return f'<td class="score {"leader" if lead else ""}" style="background:{bg};color:{fg}" data-model="{mid}" data-category="{fid}" {key}="{c["correct"]}" data-n="{c["n"]}">{c["correct"]}/{c["n"]} {"★" if lead else ""}<small>{float(c["accuracy"]):.2%}</small></td>'


def category_html(s, guide, lookup, prefix):
    mids, models = s['ranked_model_ids'], s['models']
    groups, ranks = [], []
    for slug, title, fids in GROUPS:
        best = {fid: max(int(lookup[mid, fid]['correct']) for mid in mids) for fid in fids}
        header = '<th>Configuration · overall order</th>' + ''.join(f'<th>{fid}<br>{esc(guide[fid]["display_name"])}<small>{guide[fid]["questions"]} questions</small></th>' for fid in fids)
        rows = ''.join('<tr><td>' + model_name(mid, models) + '</td>' + ''.join(score_cell(mid, fid, lookup[mid, fid], best[fid]) for fid in fids) + '</tr>' for mid in mids)
        groups.append(f'<h3 id="group-{slug}">{esc(title)}</h3><p class="figure-caption">Every cell prints correct / tested and accuracy. ★ and an inset border mark all tied category leaders.</p><div class="scroll"><table class="matrix"><thead><tr>{header}</tr></thead><tbody>{rows}</tbody></table></div><p><a href="{prefix}categories_{slug}.svg">Download annotated figure (SVG)</a> · <a href="{prefix}categories_{slug}.png">PNG</a></p>')
        for fid in fids:
            g = guide[fid]
            ordered = sorted([(mid, lookup[mid, fid]) for mid in mids], key=lambda row: (-int(row[1]['correct']), mids.index(row[0])))
            cranks = competition_ranks(ordered)
            rankrows = ''.join(f'<tr data-category-rank="{cranks[mid]}"><td>{cranks[mid]}</td><td>{model_name(mid, models)}</td>' + score_cell(mid, fid, c, best[fid], True) + speed_cell(float(c['median_ms'])) + speed_cell(float(c['p95_ms'])) + '</tr>' for mid, c in ordered)
            ranks.append(f'<details class="category" data-family="{fid}" id="category-{fid}"><summary>{fid} · {esc(g["display_name"])} · {g["questions"]} questions</summary><p>{esc(g["what_it_tests"])}</p><blockquote>Illustration: {esc(g["illustration"])}</blockquote><div class="scroll"><table class="rank"><thead><tr><th>Rank</th><th>Configuration</th><th>Correct / tested</th><th>Median</th><th>p95</th></tr></thead><tbody>{rankrows}</tbody></table></div></details>')
    return ''.join(groups), ''.join(ranks)


def markdown_html(text):
    # Let wide prose tables scroll without widening the mobile viewport.
    rendered = markdown(text, extensions=['tables'])
    return re.sub(r'(<table>.*?</table>)', r'<div class="scroll">\1</div>', rendered, flags=re.S)


def render(s, all_s, guide, cats, profiles, leaders, analysis, costs, prefix=''):
    models, mids = s['models'], s['ranked_model_ids']
    lookup = {(r['model_id'], r['family_id']): r for r in cats}
    groups, ranks = category_html(s, guide, lookup, prefix)
    overall, costrows = [], []
    for mid in mids:
        m, c = models[mid], costs[mid]
        bg, fg = accuracy_colors(m['accuracy'])
        overall.append(f'<tr data-overall-model="{mid}"><td>{model_name(mid, models)}<small>{esc(m["role"])}</small></td><td class="score" style="background:{bg};color:{fg}">{m["correct"]}/1,934<small>{m["accuracy"]:.2%}</small></td><td>{m["macro_category_accuracy"]:.2%}</td><td>{m["added_correct"]}/592<small>{m["added_accuracy"]:.2%}</small></td><td>{m["valid"]}/1,934</td>' + speed_cell(m['median_ms']) + speed_cell(m['p95_ms']) + cost_cell(c) + '</tr>')
        costrows.append('<tr><td>' + model_name(mid, models) + '</td>' + cost_cell(c) + '<td>' + (('$' + f"{Decimal(c['known_subtotal_usd']):.8f}") if c['known_subtotal_usd'] is not None else 'Unknown / unmeasured') + (' + ?' if c['unknown_count'] and c['known_subtotal_usd'] is not None else '') + f'</td><td>{c["reported_count"]}/1,934</td><td>{c["tariff_estimate_count"] + c["free_access_tariff_count"]}/1,934</td><td>{c["unknown_count"]}</td></tr>')
    table = lambda headers, rows: '<div class="scroll"><table><thead><tr>' + ''.join('<th>'+h+'</th>' for h in headers) + '</tr></thead><tbody>' + ''.join(rows) + '</tbody></table></div>'
    old = (frozen.SOURCE / 'report.html').read_text()
    # Preserve the already-audited profiles, coverage, exclusions and collection provenance.
    from re import search
    retained = []
    for ident in ['profiles', 'coverage', 'other-models', 'collection-dates', 'method']:
        fragment = search(r'<section id="' + ident + r'">.*?</section>', old, flags=16).group(0)
        if ident == 'method':
            from re import sub
            fragment = sub(r'A complete[^<]*?monetary cost ledger has not been consolidated;[^<]*?v2\s*bank price\.', 'Selected-primary monetary evidence is now reconciled separately in the cost table and downloadable ledger; missing charges and tariff estimates remain explicit.', fragment)
        fragment = fragment.replace('src="', 'src="' + prefix).replace('href="not_in_main.html"', 'href="' + prefix + 'not_in_main.html"')
        for name in INPUTS + ['statistics.json', 'model_statistics.csv', 'category_scores.csv', 'model_profiles.csv', 'manifest.json']:
            fragment = fragment.replace('href="' + name + '"', 'href="' + prefix + name + '"')
        retained.append(fragment)
    opts = ''.join(f'<option value="{fid}">{fid} · {esc(guide[fid]["display_name"])}</option>' for fid in sorted(guide))
    navgroups = ' '.join(f'<a href="#group-{slug}">{esc(title)}</a>' for slug, title, _ in GROUPS)
    body = '<p class="eyebrow">An empirical map of fast, structured decisions · November 1, 2026</p><h1>System 1 Decision Benchmark v2</h1>'
    body += markdown_html(INTRO_MD)
    body += '<nav><a href="#overview">Accuracy, speed & cost</a><a href="#legend">Colour key</a><a href="#findings">What it demonstrates</a><a href="#functions">Category matrices</a><a href="#rankings">Individual rankings</a><a href="#cost">Cost evidence</a><a href="#profiles">Model profiles</a><a href="#method">Test & methods</a></nav>'
    body += '<div class="metrics"><div><strong>82.89%</strong><span>Fastino · highest observed overall</span></div><div><strong>77.70%</strong><span>D3 Ultra · highest on the 592 additions</span></div><div><strong>66.70%</strong><span>StartLux Instant · highest local full bank</span></div><div><strong>26 / 38</strong><span>qualifying / measured configurations</span></div></div>'
    body += f'<section id="overview"><h2>Accuracy, speed and cost together</h2><a href="{prefix}overview.svg"><img src="{prefix}overview.png" alt="26 models: accuracy, coloured median and p95 response time, and reported or estimated costs with missing-charge labels"></a><p class="figure-caption">Every panel uses the same models and row order. Costs with + ? are known subtotals. Free access and unmetered local compute are labelled separately.</p><label>Find a model <input id="model-search" type="search" placeholder="Model or deployment"></label>'
    body += table(['Configuration', 'Correct / tested', 'Equal-category', '592 additions', 'Usable', 'Median', 'p95', 'USD / 1,000 · evidence'], overall)
    body += '<p class="note">Timings pool individual primary responses, including unsuccessful calls. Median and p95 are computed from the combined observations; component medians are never averaged. Network time is included; setup, loading and pacing are excluded. Hardware, precision, routes and dates differ.</p></section>'
    body += f'<section id="legend"><h2>How to read the colours</h2><img class="legend-graphic" src="{prefix}accuracy_legend.png" alt="Fixed category accuracy scale from pale yellow at zero through green to dark blue at 100 percent">' + markdown_html(LEGEND_MD) + '</section>'
    body += '<section id="findings">' + markdown_html(analysis) + f'<img src="{prefix}original_vs_additions.png" alt="Original bank versus the 592 additions, same 26 configurations"><p class="figure-caption">The banks differ in composition; their difference does not isolate a causal effect of difficulty.</p><img src="{prefix}local_coverage.png" alt="Full bank and common context-compatible subset for the three qualifying local configurations"></section>'
    body += '<section id="functions"><h2>41 categories: a visible map of strengths</h2><p>The seven groups make related operations readable without compressing 41 columns into one figure. Counts, percentages and tied leaders remain visible in every cell. Rows keep the overall ranking; individual rankings follow below. The 62% cutoff applies to overall accuracy, not each category.</p><div class="group-nav">' + navgroups + '</div>' + groups + '</section>'
    body += '<section id="rankings"><h2>Rankings within each category</h2><p>Open a category for its definition, illustration, sorted ranking, accuracy and response-time bands. Equal correct counts receive equal competition ranks; timings do not break accuracy ties.</p><label>Choose a category <select id="category-select"><option value="">All categories</option>' + opts + '</select></label>' + ranks + '</section>'
    body += '<section id="cost"><h2>What the cost figures actually measure</h2>' + markdown_html(COST_MD) + table(['Configuration', 'USD / 1,000 · basis', 'Known run subtotal USD', 'Monetary records', 'Tariff / free-access records', 'Unknown charges'], costrows) + f'<p><a href="{prefix}cost_statistics.json">All 38 cost summaries (JSON)</a> · <a href="{prefix}cost_statistics.csv">Cost summaries CSV</a> · <a href="{prefix}cost_evidence.csv.gz">73,492 answer-free cost records</a> · <a href="{prefix}cost_method.md">Cost method</a></p></section>'
    body += ''.join(retained)
    js = "document.getElementById('model-search').addEventListener('input',function(){const q=this.value.toLowerCase();document.querySelectorAll('[data-overall-model]').forEach(r=>r.hidden=!r.textContent.toLowerCase().includes(q));});document.getElementById('category-select').addEventListener('change',function(){document.querySelectorAll('.category').forEach(r=>{r.hidden=!!this.value&&r.dataset.family!==this.value;if(this.value&&r.dataset.family===this.value)r.open=true;});});"
    return '<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="description" content="1,934 decision questions, 41 categories and 26 qualifying configurations. Coloured accuracy rankings, speed, cost and coverage with reproducible evidence."><title>System 1 Decision Benchmark v2 · Accuracy, speed and cost</title><style>' + CSS + '</style></head><body><main>' + body + '</main><script>' + js + '</script></body></html>'


def archive():
    if (ARCHIVE / 'manifest.json').exists():
        for entry in load(ARCHIVE / 'manifest.json')['files'].values():
            assert sha(ARCHIVE / entry['path']) == entry['sha256']
        return
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    files = {}
    for name in frozen.PRESERVE + ['documents/V2_DESIGN.md']:
        raw = subprocess.check_output(['git', 'show', head + ':' + name], cwd=ROOT)
        assert raw == (ROOT / name).read_bytes(), 'Overlapping edit: ' + name
        p = ARCHIVE / (name + '.snapshot'); p.parent.mkdir(parents=True, exist_ok=True); p.write_bytes(raw)
        files[name] = dict(path=name + '.snapshot', sha256=sha(p))
    write(ARCHIVE / 'manifest.json', dict(commit=head, scope='Exact presentation before visual/cost restoration; no measurements changed', files=files))


def readme(s, costs, guide, analysis):
    path = 'results/releases/' + NAME + '/'
    text = '# System 1 Decision Benchmark v2\n\n' + INTRO_MD + '\n[Full interactive report](' + frozen.SITE + 'report.html) · [Individual category rankings](' + frozen.SITE + 'report.html#rankings) · [Cost evidence](' + frozen.SITE + 'report.html#cost)\n\n'
    text += '![Accuracy, coloured median and p95 timing, and cost for the same 26 qualifying models](' + path + 'overview.png)\n\n## How to read the colours\n\n'
    text += '![Fixed absolute category accuracy scale](' + path + 'accuracy_legend.png)\n\n' + LEGEND_MD
    text += '\n## Main comparison\n\n'
    rows = []
    for mid in s['ranked_model_ids']:
        m, c = s['models'][mid], costs[mid]
        money, basis = cost_text(c)
        speed = lambda v: ['🟩', '🟨', '🟧', '🟥'][speed_band(v)] + f' {v:,.0f} ms'
        cb = cost_band(c['known_usd_per_1000']) if c['evidence_kind'] not in ['free_access_tariff', 'unknown', 'local_unmeasured'] else None
        costmark = ['🟩', '🟨', '🟧', '🟥'][cb] if cb is not None else '⬜'
        rows.append((m['label'], f"{m['correct']}/1,934", pct(m['accuracy']), speed(m['median_ms']), speed(m['p95_ms']), costmark + ' ' + money, basis))
    text += frozen.mdtable(['Configuration', 'Correct', 'Accuracy', 'Median', 'p95', 'USD / 1,000', 'Cost basis'], rows)
    text += '\n## What the larger benchmark demonstrates\n\n' + analysis.replace('## What the larger bank shows\n\n', '')
    text += '\n## Category results in detail\n\nEach matrix uses the same overall model order and fixed accuracy scale. Correct / tested and percentage are printed in every cell. The border and ★ mark all tied observed leaders. [Open the sorted, coloured individual rankings](' + frozen.SITE + 'report.html#rankings).\n\n'
    for slug, title, fids in GROUPS:
        text += '### ' + title + '\n\n' + '; '.join(fid + ' ' + guide[fid]['display_name'] for fid in fids) + '.\n\n![' + title + ': counts, percentages and tied category leaders](' + path + 'categories_' + slug + '.png)\n\n'
    text += '## Cost: receipts, estimates and access terms\n\n' + COST_MD + '\n## Timing, coverage and validity\n\n'
    text += 'Medians and p95s pool all 1,934 primary response times, including failures. They are never averages of category or phase medians. Wrong usable answers, context limits, declared refusals and service failures are distinguished. Routes, precision, hardware and collection dates differ; see the report for provenance.\n\n'
    text += 'The bank includes related generated variants and model-guided development, including Jev and retained Microsoft/Drex feedback. It is a development benchmark with limited independent generalization. Category specialties are descriptive, and narrow leads need not be reliable. These reasoning-disabled LLM configurations do not represent the same models with reasoning enabled. Public checks reproduce input hashes, timing, coverage, monetary aggregation and category totals; the scoring key, model choices, probabilities and individual correctness remain private.\n\n'
    text += 'All 38 v2 measurements remain available. The main graphs use the same 26 configurations with at least 62% overall. Eleven measurements score below that cutoff; adaptive AutoThink is archival. Kev 4B, Nemotron, plain H2O, Qwen and older Jev are outside the main selection. [Brief catalogue](' + path + 'not_in_main.html).\n\n'
    text += '## Download the test and evidence\n\n'
    links = [('Exact native questions (JSONL)', 'questions_1934.jsonl'), ('Questions CSV', 'questions_1934.csv'), ('Readable questions', 'questions_1934.txt'), ('Item/category metadata', 'metadata_core.jsonl'), ('Bank manifest', 'bank_manifest.json'), ('Main results', 'statistics.json'), ('All 38 measurements', 'all_statistics.json'), ('Category scores', 'category_scores.csv'), ('Model profiles', 'model_profiles.csv'), ('Timing/status evidence', 'timing_evidence.csv.gz'), ('Cost evidence', 'cost_evidence.csv.gz'), ('Cost summaries', 'cost_statistics.json'), ('Audit receipt', 'audit_receipt.json'), ('Release checksums', 'manifest.json')]
    text += '\n'.join('- [' + title + '](' + path + name + ')' for title, name in links) + '\n\n'
    text += '## Rebuild and validate offline\n\nThe [scripts/](scripts/README.md) use public captures and require no API keys or live inference.\n\n```sh\npython3 -m pip install -r scripts/requirements-reports.txt python-dotenv\npython3 scripts/validate_system1_v2.py\npython3 scripts/validate_system1_v2_presentation.py\npython3 scripts/publish_system1_v2_presentation.py --output /tmp/system1-v2-presentation-rebuild\n```\n\nHistorical check: `python3 scripts/validate_october21_release.py`. This presentation-only release preserves the questions, scores, timings and selection from the [initial v2 capture](results/releases/system1_v2_2026-11-01/report.html). [Previous 1,342-question report](results/releases/local_updates_2026-10-31/report.html). All dated releases retain their original evidence and denominators.\n'
    return text


def build(dest=SOURCE, publish=True):
    if not publish:
        assert dest.resolve() != SOURCE.resolve(), 'Isolated rebuilds require a separate output directory'
    if publish:
        assert subprocess.run(['git', 'cat-file', '-e', 'HEAD:' + str((SOURCE / 'manifest.json').relative_to(ROOT))], cwd=ROOT, capture_output=True).returncode != 0, 'Committed releases are immutable; use --output'
        archive()
        if (SOURCE / 'manifest.json').exists():
            seal = load(SOURCE / 'manifest.json')
            for name in INPUTS:
                assert sha(SOURCE / name) == seal['artifacts'][name], 'Captured input changed: ' + name
    assert dest == SOURCE or not dest.exists(), 'Choose a new rebuild directory'
    dest.mkdir(parents=True, exist_ok=True)
    for name in INPUTS:
        if dest != SOURCE:
            shutil.copyfile(SOURCE / name, dest / name)
    # Reuse already-audited derived captures and supplementary plots verbatim.
    for name in load(frozen.SOURCE / 'manifest.json')['artifacts']:
        if name not in frozen.INPUTS and name not in ['report.html', 'analysis.md']:
            shutil.copyfile(frozen.SOURCE / name, dest / name)
    all_s = load(dest / 'all_statistics.json'); s = frozen.main_view(all_s)
    guide = load(dest / 'category_guide.json'); costs = load(dest / 'cost_statistics.json')['models']
    cost_fields = ['model_id', 'label', 'n', 'evidence_kind', 'reported_count', 'tariff_estimate_count', 'free_access_tariff_count', 'unknown_count', 'local_unmeasured_count', 'known_evidence_count', 'reported_subtotal_usd', 'estimate_only_subtotal_usd', 'known_subtotal_usd', 'known_usd_per_1000']
    frozen.csvwrite(dest / 'cost_statistics.csv', [{k: c[k] for k in cost_fields} for c in costs.values()])
    cats = frozen.csvrows(dest / 'category_scores.csv')
    profiles, leaders, _, _ = frozen.profiles_and_leaders(s, cats, guide)
    lookup = {(r['model_id'], r['family_id']): r for r in cats}
    assert len(s['models']) == 26 and len(lookup) == 1066
    assert sorted(fid for _, _, fids in GROUPS for fid in fids) == sorted(guide)
    analysis = (frozen.SOURCE / 'analysis.md').read_text().split('\n\n## Method')[0]
    plot_overview(dest, s, costs); plot_groups(dest, s, guide, lookup); legend_graphic(dest)
    write(dest / 'analysis.md', analysis + '\n\n## Cost evidence\n\n' + COST_MD)
    write(dest / 'cost_method.md', '# Cost evidence for the frozen v2 bank\n\n' + COST_MD)
    write(dest / 'visual_guide.md', '# Reading the v2 presentation\n\n' + LEGEND_MD)
    write(dest / 'report.html', render(s, all_s, guide, cats, profiles, leaders, analysis, costs))
    if publish:
        write(ROOT / 'README.md', readme(s, costs, guide, analysis))
        write(ROOT / 'docs/report.html', render(s, all_s, guide, cats, profiles, leaders, analysis, costs, NAME + '/'))
        functions = '# The 41 categories: coloured rankings and explanations\n\n[Interactive category matrices](' + frozen.SITE + 'report.html#functions) · [Sorted individual rankings](' + frozen.SITE + 'report.html#rankings). Every category uses the same 26 configurations meeting 62% overall.\n\n' + LEGEND_MD + '\n'
        for slug, title, fids in GROUPS:
            functions += '## ' + title + '\n\n![' + title + '](../results/releases/' + NAME + '/categories_' + slug + '.png)\n\n'
            for fid in fids:
                g = guide[fid]
                functions += f"### {fid} · {g['display_name']}\n\n{g['questions']} questions. {g['what_it_tests']}\n\nIllustration: {g['illustration']}\n\n[Sorted coloured ranking]({frozen.SITE}report.html#category-{fid}).\n\n"
        write(ROOT / 'documents/FUNCTIONS.md', functions)
        write(ROOT / 'documents/COST_METHOD.md', '# V2 cost comparison\n\n' + COST_MD + '\n[Cost table](' + frozen.SITE + 'report.html#cost).\n')
        write(ROOT / 'documents/VISUAL_GUIDE.md', '# Colours, ranks and comparison bands\n\n' + LEGEND_MD)
        for name in ['data/README.md', 'results/README.md', 'documents/README.md', 'scripts/README.md']:
            original = (ARCHIVE / (name + '.snapshot')).read_text()
            original = original.replace(frozen.NAME + '/', NAME + '/')
            if name == 'scripts/README.md':
                original = '# Current presentation build\n\n`publish_system1_v2_presentation.py` restores annotated category matrices, coloured individual ranks and reconciled cost evidence without changing frozen measurements. `validate_system1_v2_presentation.py` checks the ledger joins, totals, colours, ranks, privacy and immutable inputs. Use `--output` to rebuild offline in a new directory. The initial v2 builder below reproduces its original dated presentation.\n\n' + original
            else:
                rel = '' if name == 'documents/README.md' else '../documents/'
                original += '\n\n[Cost evidence](' + rel + 'COST_METHOD.md) · [Visual guide](' + rel + 'VISUAL_GUIDE.md).\n'
            write(ROOT / name, original)
        workflow = ROOT / '.github/workflows/october18-validate.yml'
        raw = (ARCHIVE / '.github/workflows/october18-validate.yml.snapshot').read_text()
        write(workflow, raw.replace('      - run: python3 scripts/validate_system1_v2.py\n', '      - run: python3 scripts/validate_system1_v2.py\n      - run: python3 scripts/validate_system1_v2_presentation.py\n'))
    artifacts = {p.name: sha(p) for p in sorted(dest.iterdir()) if p.is_file() and p.name != 'manifest.json'}
    write(dest / 'manifest.json', dict(version='system-1-decision-v2-presentation', questions=1934, categories=41, main_models=26, measured_models=38, minimum_overall_accuracy=.62, artifacts=artifacts, source_files_sha256={n: sha(ROOT / n) for n in PUBLIC_SOURCES}, frozen_release_manifest_sha256=sha(frozen.SOURCE / 'manifest.json'), preserved_inputs_sha256={n: sha(frozen.SOURCE / n) for n in frozen.INPUTS}, scope='Presentation and selected-primary cost reconciliation only; frozen questions, scores, timings and selection unchanged'))
    if publish:
        shutil.copytree(dest, ROOT / 'docs' / NAME, dirs_exist_ok=True)
        frozen.bind_layout()
        layoutpath = ROOT / 'scripts/layout_manifest.json'; layout = load(layoutpath)
        for name in PUBLIC_SOURCES + ['documents/COST_METHOD.md', 'documents/VISUAL_GUIDE.md']:
            layout['current_files'][name] = sha(ROOT / name)
        write(layoutpath, layout)
    print(json.dumps(dict(status='built', presentation=NAME, models=26, categories=41, output=str(dest))))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--output', type=Path); args = parser.parse_args()
    build(args.output or SOURCE, publish=args.output is None)
