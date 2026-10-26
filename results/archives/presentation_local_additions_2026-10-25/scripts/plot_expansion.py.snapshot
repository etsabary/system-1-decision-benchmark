"""Rebuild publication graphics from the eleven-model aggregate evidence."""
from repo_layout import repo_file
from hashlib import sha256
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np

HERE = Path(__file__).resolve().parents[1]
SOURCE = repo_file('expansion_2026-10-15', root=HERE)
DEST = repo_file('figures', root=HERE)
SHORT = {'jev113': 'Jev 1.13', 'jev114': 'Jev 1.14', 'luna_decisions': 'Luna Decisions',
         'openai/gpt-6-luna': 'Luna regular', 'openai/gpt-5.4-nano': 'GPT-5.4 nano',
         'google/gemini-2.5-flash-lite': 'Gemini 2.5 Flash-Lite',
         'ibm-granite/granite-4.2-8b': 'Granite 4.2 8B',
         'qwen/qwen3-30b-a3b-instruct-2507': 'Qwen3-30B-A3B Instruct',
         'microsoft/phi-4': 'Phi-4 14B', 'mistralai/mistral-nemo': 'Mistral NeMo 12B',
         'inception/mercury-2.5': 'Mercury 2.5'}


def save(fig, name):
    fig.savefig(DEST/('eleven_'+name+'.png'), dpi=170, bbox_inches='tight', facecolor='white')
    svg = DEST/('eleven_'+name+'.svg')
    fig.savefig(svg, bbox_inches='tight', facecolor='white')
    svg.write_text('\n'.join(line.rstrip() for line in svg.read_text().splitlines())+'\n')
    plt.close(fig)


def main():
    s = json.loads((SOURCE/'summary.json').read_text())
    assert s['status'] == 'COMPLETE_ELEVEN_MODELS_1136_EACH'
    models = s['models']
    order = sorted(models, key=lambda m: models[m]['primary']['correct'])
    historical = {'jev113', 'jev114', 'luna_decisions'}
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10,
                         'axes.spines.top': False, 'axes.spines.right': False,
                         'axes.titleweight': 'bold'})
    fig, ax = plt.subplots(figsize=(12, 8))
    y = np.arange(len(order))
    colors = ['#163e65' if m in historical else '#18867d' for m in order]
    full = [100*models[m]['primary']['accuracy_attempted'] for m in order]
    core = [100*models[m]['by_role']['core']['accuracy_attempted'] for m in order]
    ax.barh(y-.10, full, height=.48, color=colors)
    ax.scatter(core, y+.23, marker='D', s=36, color='#efb83d', edgecolors='#6b511a', zorder=3, label='Core-only accuracy (640 questions)')
    for i, m in enumerate(order):
        ax.text(full[i]+1, i-.10, f"{full[i]:.1f}%  ({models[m]['primary']['correct']}/1,136)", va='center', fontsize=10)
    ax.set_yticks(y, [SHORT[m] for m in order]); ax.set_xlim(0, 112)
    ax.set_xticks([0, 20, 40, 60, 80, 100]); ax.set_xlabel('Correct / all planned questions (%)')
    ax.grid(axis='x', alpha=.17); ax.set_axisbelow(True)
    ax.set_title('Eleven models on the same text decision bank', loc='left', fontsize=17, pad=38)
    ax.text(0, 1.035, 'Bars: all 1,136 questions. Navy: preserved Decisions references. Teal: new reasoning-off LLM runs.', transform=ax.transAxes, fontsize=10)
    ax.legend(loc='lower right', frameon=False)
    fig.text(.125, .015, 'LLMs tested October 15, 2026 (Toronto). Historical references: September 22 to October 15.\nStrict numeric-ID outputs; errors and format failures unsuccessful. Related variants are not independent observations.', fontsize=9, color='#45535c')
    fig.subplots_adjust(bottom=.13)
    save(fig, 'overall_accuracy')

    columns = sorted(models, key=lambda m: -models[m]['primary']['correct'])
    data = np.array([[100*f['models'][m]['accuracy_attempted'] for m in columns] for f in s['by_family']])
    fig, ax = plt.subplots(figsize=(16, 14))
    im = ax.imshow(data, vmin=0, vmax=100, cmap='YlGnBu', aspect='auto')
    ax.set_xticks(range(len(columns)), [SHORT[m] for m in columns], rotation=40, ha='right')
    ax.set_yticks(range(25), [f"{f['family_id']}  {f['family']} (n={f['n']})" for f in s['by_family']])
    for i, f in enumerate(s['by_family']):
        for j, m in enumerate(columns):
            ax.text(j, i, str(f['models'][m]['correct']), ha='center', va='center', fontsize=9,
                    color='white' if data[i, j] >= 63 else '#162d42')
    ax.set_title('Which functions hold up, and which do not?', loc='left', fontsize=18, pad=28)
    ax.text(0, 1.018, 'Cell labels: correct count. Color: accuracy within each family. Columns sorted by overall strict accuracy.', transform=ax.transAxes, fontsize=10)
    colorbar = fig.colorbar(im, ax=ax, shrink=.6, pad=.02)
    colorbar.set_label('Correct / planned (%)')
    fig.text(.32, .015, 'Same 1,136 questions; 25 families. New LLMs: reasoning off, 16-token cap, October 15, 2026.\nThe three Decisions columns preserve their historical runs. One observed bank, not a universal capability ranking.', fontsize=9, color='#45535c')
    fig.subplots_adjust(left=.32, bottom=.17, top=.94, right=.95)
    save(fig, 'family_accuracy')

    new = [m for m in models if m not in historical]
    new.sort(key=lambda m: models[m]['latency_first_all']['median_ms'])
    fig, axes = plt.subplots(1, 2, figsize=(14, 6), sharey=True)
    y = np.arange(len(new))
    costs = [100*models[m]['cost_all_attempts']['known_usd'] for m in new]
    med = [models[m]['latency_first_all']['median_ms']/1000 for m in new]
    p95 = [models[m]['latency_first_all']['p95_ms']/1000 for m in new]
    axes[0].barh(y, costs, color='#18867d', height=.6)
    for i, value in enumerate(costs):
        missing = models[new[i]]['cost_all_attempts']['missing_attempts']
        axes[0].text(value+.06, i, f'{value:.2f}¢'+(f' + {missing} unknown' if missing else ''), va='center', fontsize=9)
    axes[0].set_xlim(0, max(costs)*1.43); axes[0].set_xlabel('Known reported US cents / actual 1,136-question run')
    axes[0].set_title('Cost, including recovery attempts', loc='left')
    axes[0].set_yticks(y, [SHORT[m] for m in new])
    axes[1].barh(y, med, color='#163e65', height=.6, label='Median')
    axes[1].scatter(p95, y, color='#c37c25', marker='D', s=35, label='p95')
    for i, value in enumerate(med):
        axes[1].text(value-.025, i, f'{value:.3f} s', ha='right', va='center', fontsize=9, color='white')
    axes[1].set_xlabel('First-attempt connect-to-full-response seconds')
    axes[1].set_xlim(0, max(p95)*1.18)
    axes[1].set_title('Response time, same new-run setup', loc='left')
    axes[1].legend(frameon=False, loc='upper right')
    for ax in axes:
        ax.grid(axis='x', alpha=.17); ax.set_axisbelow(True)
    axes[0].invert_yaxis()
    fig.suptitle('Eight regular LLMs through OpenRouter', x=.08, ha='left', fontsize=18, fontweight='bold')
    fig.text(.08, .025, 'October 15, 2026. Provider pinned; fallback off; new HTTPS connection per attempt. Two requests/model per wave.\nBackend providers and quantizations differ. No historical Decisions speed bars: their old timer boundaries differ.\nMercury uses the currently discounted tariff. Missing cost remains unknown. Short-output latency is not tokens/second.', fontsize=9, color='#45535c')
    fig.subplots_adjust(left=.2, top=.88, bottom=.19, wspace=.18)
    save(fig, 'cost_and_speed')
    history = s['historical_speeds']
    hh = ['jev113', 'jev114', 'luna_decisions']
    fig, axes = plt.subplots(1, 2, figsize=(14, 5.4), sharey=True)
    for ax, field, title in zip(axes,
            ['full_bank_saved_latency_all_outcomes', 'shared_136_extension_saved_latency'],
            ['Full bank: all 1,136 outcomes', 'Shared extension: successful outcomes']):
        medians = [history[m][field]['median_ms'] for m in hh]
        tails = [history[m][field]['p95_ms'] for m in hh]
        ax.barh(range(3), medians, height=.5, color='#163e65', label='Median')
        ax.scatter(tails, range(3), marker='D', color='#c37c25', label='p95')
        for i, m in enumerate(hh):
            ax.text(medians[i]+18, i+.23, f"{medians[i]:.0f} ms (n={history[m][field]['n']})", va='top', fontsize=10)
        ax.set_xlim(0, max(tails)*1.28)
        ax.set_title(title, loc='left')
        ax.set_xlabel('Historical recorded latency_ms')
        ax.grid(axis='x', alpha=.15); ax.set_axisbelow(True)
    axes[0].set_yticks(range(3), [SHORT[m] for m in hh]); axes[0].invert_yaxis()
    axes[0].legend(loc='lower right', frameon=False)
    fig.suptitle('Historical decision-model speeds are retained', x=.08, ha='left', fontsize=18, fontweight='bold')
    fig.text(.08, .025, 'September 22 to October 15, 2026. Full bank includes timed failures; extension panel includes successful outcomes only.\nJev 1.13 combines older header-only timings across three routes with the later body-timed cohort. Other historical records use body timings.\nPreserved values, not new measurements. Different dates and boundaries prevent a controlled ranking against the new LLMs.', fontsize=9, color='#45535c')
    fig.subplots_adjust(left=.15, top=.83, bottom=.22, wspace=.18)
    save(fig, 'historical_speed')
    paths = sorted(p for p in DEST.glob('eleven_*') if p.suffix in {'.png', '.svg'})
    (SOURCE/'graphics_integrity.json').write_text(json.dumps({'plotter_sha256': sha256(Path(__file__).read_bytes()).hexdigest(),
            'matplotlib_version': matplotlib.__version__, 'source_summary_sha256': sha256((SOURCE/'summary.json').read_bytes()).hexdigest(),
            'files_sha256': {p.name: sha256(p.read_bytes()).hexdigest() for p in paths}}, indent=2)+'\n')
    print(json.dumps({'figures': [p.name for p in paths]}))


if __name__ == '__main__':
    main()
