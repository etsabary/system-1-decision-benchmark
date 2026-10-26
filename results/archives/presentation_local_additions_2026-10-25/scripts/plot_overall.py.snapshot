"""Plot the combined comparison, explicitly marking October 16 additions."""
from repo_layout import repo_file
from hashlib import sha256
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import ScalarFormatter
import numpy as np

from plot_matched import SHORT as ORIGINAL_SHORT

ROOT = Path(__file__).resolve().parents[1]
SOURCE = repo_file('overall_expanded_2026-10-16', root=ROOT)
DEST = repo_file('figures', root=ROOT)
SHORT = {**ORIGINAL_SHORT, 'microsoft_decision': 'Microsoft-Decision-1',
         'nimble_v4': 'Nimble v4', 'nimble_v4_max': 'Nimble v4 Max',
         'nemotron35lightning':'Nemotron 3.5 Lightning','haiku55':'Haiku 5.5',
         'glm47flash':'GLM 4.7 Flash','deepseek41flash':'DeepSeek V4.1 Flash',
         'mimo26flash':'MiMo V2.6 Flash','qwen38flash':'Qwen3.8 Flash',
         'tencenthy3':'Tencent Hy3','nemotron35supervl':'Nemotron 3.5 Super VL'}


def save(fig, name):
    for extension in ('png', 'svg'):
        target = DEST / ('expanded_' + name + '.' + extension)
        fig.savefig(target, dpi=170,
                    bbox_inches='tight', facecolor='white')
        if extension == 'svg':
            target.write_text('\n'.join(line.rstrip() for line in target.read_text().splitlines()) + '\n')
    plt.close(fig)


def main():
    summary = json.loads((SOURCE / 'summary.json').read_text())
    assert not summary['pending_model_ids'], 'Do not publish an unfinished model expansion'
    models = {m:summary['models'][m] for m in summary['publication']['eligible_model_ids']}
    added = set(summary['added_model_ids'])
    native = {'jev113', 'jev114', 'luna_decisions'} | set(summary['native_added_model_ids'])
    names = {m: SHORT[m] + (' *' if m in added else '') for m in models}
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10,
                         'axes.spines.top': False, 'axes.spines.right': False,
                         'axes.titleweight': 'bold'})
    order = sorted(models, key=lambda m: models[m]['primary']['correct'])
    height = max(8, len(order) * .55 + 2)
    fig, ax = plt.subplots(figsize=(13, height))
    y = np.arange(len(order))
    full = [100 * models[m]['primary']['accuracy_attempted'] for m in order]
    core = [100 * models[m]['by_role']['core']['accuracy_attempted'] for m in order]
    bars = ax.barh(y - .1, full, height=.48,
                   color=['#163e65' if m in native else '#18867d' for m in order])
    for m, bar in zip(order, bars):
        if m in added:
            bar.set_hatch('//')
            bar.set_edgecolor('#7599ba')
    ax.scatter(core, y + .22, marker='D', s=30, color='#efb83d',
               edgecolors='#6b511a', zorder=3, label='640 core questions')
    for i, model in enumerate(order):
        ax.text(full[i] + 1, i - .1, f"{full[i]:.1f}% ({models[model]['primary']['correct']}/1,136)", va='center')
    ax.set_yticks(y, [names[m] for m in order])
    ax.set_xlim(0, 111)
    ax.set_xticks([0, 20, 40, 60, 80, 100])
    ax.set_xlabel('Correct / all 1,136 planned questions (%)')
    ax.set_title(f'{len(models)} models on the same text decision bank', loc='left', fontsize=18, pad=30)
    ax.text(0, 1.025, 'Navy: native Decisions. Teal: regular LLMs, switchable reasoning off. * Added October 16.', transform=ax.transAxes)
    ax.legend(frameon=False, loc='lower right')
    ax.grid(axis='x', alpha=.17)
    ax.set_axisbelow(True)
    fig.text(.18, .025, 'Tests: October 15 and 16, 2026 (Toronto). First attempts only; failures unsuccessful.\nHaiku, DeepSeek and Phi-4 excluded for ≥5% output-format failures (post-hoc inclusion rule).\nSame frozen questions and options; related variants are not independent observations.', fontsize=9, color='#45535c')
    fig.subplots_adjust(left=.24, bottom=.13, top=.9)
    save(fig, 'accuracy')

    columns = sorted(models, key=lambda m: -models[m]['primary']['correct'])
    data = np.array([[100 * f['models'][m]['accuracy_attempted'] for m in columns] for f in summary['by_family']])
    fig, ax = plt.subplots(figsize=(max(17, len(columns) * .9 + 5), 14))
    im = ax.imshow(data, vmin=0, vmax=100, cmap='YlGnBu', aspect='auto')
    ax.set_xticks(range(len(columns)), [names[m] for m in columns], rotation=43, ha='right')
    ax.set_yticks(range(25), [f"{f['family_id']}  {f['family']} (n={f['n']})" for f in summary['by_family']])
    for i, f in enumerate(summary['by_family']):
        for j, m in enumerate(columns):
            ax.text(j, i, str(f['models'][m]['correct']), ha='center', va='center', fontsize=9,
                    color='white' if data[i, j] >= 63 else '#162d42')
    ax.set_title('Accuracy across 25 text decision functions', loc='left', fontsize=18, pad=28)
    ax.text(0, 1.018, 'Labels: correct count. Color: family accuracy. * Added October 16; all other runs October 15.', transform=ax.transAxes)
    fig.colorbar(im, ax=ax, shrink=.6, pad=.02).set_label('Correct / planned (%)')
    fig.text(.30, .018, 'Same 1,136 text questions across 25 families. Dates: October 15 and 16, 2026 (Toronto).\nHaiku, DeepSeek and Phi-4 excluded for ≥5% format failures; inclusion rule chosen after testing.\nSingle-shot decisions; no tools, answer feedback or explicit reasoning trace.', fontsize=9, color='#45535c')
    fig.subplots_adjust(left=.30, bottom=.19, top=.94, right=.95)
    save(fig, 'family_accuracy')

    order = sorted(models, key=lambda m: models[m]['latency_first_all']['median_ms'])
    y = np.arange(len(order))
    fig, axes = plt.subplots(1, 2, figsize=(15, height), sharey=True)
    costs = [100 * models[m]['cost_all_attempts']['known_usd'] for m in order]
    medians = [models[m]['latency_first_all']['median_ms'] / 1000 for m in order]
    p95 = [models[m]['latency_first_all']['p95_ms'] / 1000 for m in order]
    axes[0].barh(y, costs, color='#18867d', height=.6)
    for i, m in enumerate(order):
        cost = models[m]['cost_all_attempts']
        calculated = cost.get('sources', {}).get('usage_times_published_tariff', 0)
        text = ('~' if calculated else '') + f'{costs[i]:.2f}c'
        if cost['missing_attempts']:
            text += f" + {cost['missing_attempts']} unknown"
        axes[0].text(costs[i] + .06, i, text, va='center', fontsize=9)
    axes[0].set_xlim(0, max(costs) * 1.55)
    axes[0].set_xlabel('US cents / actual 1,136-question run, including retries')
    axes[0].set_title('Cost: returned charges or labelled calculation', loc='left')
    axes[0].set_yticks(y, [names[m] for m in order])
    axes[1].hlines(y, medians, p95, color='#7599ba', linewidth=2, alpha=.65)
    axes[1].scatter(medians, y, color='#163e65', s=35, label='Median', zorder=3)
    axes[1].scatter(p95, y, color='#c37c25', marker='D', s=30, label='p95')
    for i, value in enumerate(medians):
        axes[1].text(value * 1.04, i + .18, f'{value:.3f} s', va='top', fontsize=9)
    axes[1].set_xscale('log')
    axes[1].set_xlim(min(medians)*.7, max(p95)*1.3)
    axes[1].set_xticks([v for v in (.1,.2,.5,1,2,5,10,20,50) if min(medians)*.7<=v<=max(p95)*1.3])
    axes[1].xaxis.set_major_formatter(ScalarFormatter())
    axes[1].set_xlabel('Connect-to-full-response seconds (log scale)')
    axes[1].set_title('Same full-response timer; different services/dates', loc='left')
    axes[1].legend(frameon=False)
    axes[0].invert_yaxis()
    for ax in axes:
        ax.grid(axis='x', alpha=.17)
        ax.set_axisbelow(True)
    fig.suptitle(f'{len(models)} services: cost and speed for 1,136 text decisions', x=.07, ha='left', fontsize=18, fontweight='bold')
    fig.text(.07, .025, '* Added October 16, 2026; other runs October 15 (Toronto). Microsoft: OpenRouter/Azure; Nimble: Bespoke direct.\nAll 1,136 first attempts/model, including failures. Same full-response timer; at most two concurrent requests/model.\n~ Nimble cost calculated from token usage and tariff. Missing charges unknown. Mercury promotional tariff.\nHaiku, DeepSeek and Phi-4 excluded for ≥5% format failures (post-hoc inclusion rule).', fontsize=9, color='#45535c')
    fig.subplots_adjust(left=.23, top=.9, bottom=.15, wspace=.18)
    save(fig, 'cost_and_speed')
    paths = sorted(DEST.glob('expanded_*'))
    (SOURCE / 'graphics_integrity.json').write_text(json.dumps({
        'plotter_sha256': sha256(Path(__file__).read_bytes()).hexdigest(),
        'matplotlib_version': matplotlib.__version__,
        'source_summary_sha256': sha256((SOURCE / 'summary.json').read_bytes()).hexdigest(),
        'files_sha256': {p.name: sha256(p.read_bytes()).hexdigest() for p in paths}}, indent=2) + '\n')
    print('Built combined accuracy, family and cost/speed figures')


if __name__ == '__main__':
    main()
