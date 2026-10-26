"""Local-review figures for screened October 18 generative additions."""
from repo_layout import logical_relative, repo_file
from hashlib import sha256
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SOURCE = repo_file('overall_llm_expanded_2026-10-18', root=ROOT)
DEST = SOURCE / 'figures'


def save(fig, name):
    for suffix in ('png', 'svg'):
        path = DEST / (name + '.' + suffix)
        fig.savefig(path, dpi=170, bbox_inches='tight', facecolor='white')
        if suffix == 'svg':
            path.write_text('\n'.join(line.rstrip() for line in path.read_text().splitlines()) + '\n')
    plt.close(fig)


def main():
    s = json.loads((SOURCE / 'summary.json').read_text())
    assert s['model_count'] == 40 and not s['pending_model_ids']
    new = set(s['llm_added_october_18_model_ids'])
    assert len(new) == 4
    models = s['models']
    refs = {'respan02', 'pplx_decider12', 'nimble_v4_max', 'jev114',
            'openai/gpt-6-luna', 'luna_decisions'}
    focus = sorted(new | refs, key=lambda m: -models[m]['primary']['correct'])
    aliases = {'tev1_4b_native': 'Tev1 4B (native adapter)', 'qwen3_235b': 'Qwen3 235B A22B Instruct'}
    labels = {m: aliases.get(m, models[m]['label']) + (' *' if m in new else '') for m in focus}
    color = {m: '#a0568c' if m == 'tev1_4b_native' else '#e18a29' if m in new else '#214b70' for m in focus}
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10,
                         'axes.spines.top': False, 'axes.spines.right': False})
    DEST.mkdir(parents=True, exist_ok=True)
    ranked = sorted(s['publication']['eligible_model_ids'], key=lambda m: models[m]['primary']['correct'])
    native_new = set(s['native_added_october_18_model_ids'])
    fig, ax = plt.subplots(figsize=(15, 19))
    y = np.arange(len(ranked))
    values = [100 * models[m]['primary']['accuracy_attempted'] for m in ranked]
    ax.barh(y - .1, values, height=.48,
            color=['#a0568c' if m in new else '#e18a29' if m in native_new else '#214b70' for m in ranked])
    ax.scatter([100 * models[m]['by_role']['core']['accuracy_attempted'] for m in ranked],
               y + .23, marker='D', s=14, color='#172833', label='640 core items', zorder=4)
    for i, m in enumerate(ranked):
        ax.text(values[i] + .8, i - .1, f"{values[i]:.1f}% ({models[m]['primary']['correct']}/1,136)",
                va='center', fontsize=9)
    ax.set_yticks(y, [aliases.get(m, models[m]['label']) + (' *' if m in new | native_new else '') for m in ranked])
    ax.set_xlim(0, 111)
    ax.set_xticks([0, 20, 40, 60, 80, 100])
    ax.set_xlabel('Correct / all 1,136 planned first attempts (%)')
    fig.suptitle('37 routes on the same text decision bank', x=.30, y=.98, ha='left', fontsize=20, fontweight='bold')
    fig.text(.30, .953, 'Purple: four generative additions. Orange: 14 native additions. Navy: earlier complete routes.', fontsize=10)
    ax.legend(frameon=False, loc='lower right')
    ax.grid(axis='x', alpha=.18)
    ax.set_axisbelow(True)
    fig.text(.29, .018, '* Added October 18, 2026 (Toronto). Earlier scores, costs and speeds preserved.\n'
             '40 complete runs; 37 included. Three excluded full runs, five stopped LLM samples,\n'
             'Solar Decide partial and two failed interface probes remain outside this ranking.\n'
             'The 496 variants and checks depend on core cases; counts are not independent samples.',
             fontsize=9, color='#475761')
    fig.subplots_adjust(left=.30, bottom=.09, top=.925)
    save(fig, 'overall_accuracy')
    fig, axes = plt.subplots(1, 3, figsize=(18, 8), sharey=True,
                             gridspec_kw={'width_ratios': [1, 1.2, 1.15]})
    y = np.arange(len(focus))
    colors = [color[m] for m in focus]
    accuracy = [100 * models[m]['primary']['accuracy_attempted'] for m in focus]
    axes[0].barh(y, accuracy, color=colors, height=.6)
    for i, value in enumerate(accuracy):
        axes[0].text(value + 1, i, f'{value:.1f}%', va='center')
    axes[0].set_xlim(0, 110)
    axes[0].set_xlabel('Correct / all 1,136 first attempts (%)')
    axes[0].set_title('Accuracy', loc='left', fontweight='bold')
    med = [models[m]['latency_first_all']['median_ms'] for m in focus]
    p95 = [models[m]['latency_first_all']['p95_ms'] for m in focus]
    axes[1].hlines(y, med, p95, color='#9aaebd', linewidth=2)
    axes[1].scatter(med, y, color=colors, s=32, label='Median', zorder=3)
    axes[1].scatter(p95, y, color='#214b70', s=20, marker='D', label='p95', zorder=3)
    for i, value in enumerate(med):
        axes[1].text(value * 1.035, i + .2, f'{value:.0f}', va='top', fontsize=9)
    axes[1].set_xscale('log')
    axes[1].set_xlim(150, 2600)
    axes[1].set_xlabel('Full-response ms, logarithmic scale')
    axes[1].set_title('All 1,136 timed first attempts', loc='left', fontweight='bold')
    axes[1].legend(frameon=False, loc='upper center', bbox_to_anchor=(.5, -.105), ncol=2)
    costs = [100 * models[m]['known_usd_per_1000_questions'] for m in focus]
    axes[2].barh(y, costs, color=colors, height=.6)
    for i, m in enumerate(focus):
        cost = models[m]['cost_all_attempts']
        label = f'{costs[i]:.2f}c' + (' + ?' if cost['missing_attempts'] else '')
        if cost.get('sources', {}).get('usage_times_published_tariff'):
            label = '~' + label
        axes[2].text(costs[i] + .08, i, label, va='center', fontsize=9)
    axes[2].set_xlim(0, max(costs) * 1.45)
    axes[2].set_xlabel('US cents per 1,000 questions')
    axes[2].set_title('Normalized cost, recoveries included', loc='left', fontweight='bold')
    axes[0].set_yticks(y, [labels[m] for m in focus])
    axes[0].invert_yaxis()
    for ax in axes:
        ax.grid(axis='x', alpha=.16)
        ax.set_axisbelow(True)
    fig.suptitle('Four complete generative additions and six reference routes', x=.025,
                 ha='left', fontsize=20, fontweight='bold')
    fig.text(.025, .035,
             '* Tested October 18, 2026 (Toronto). Orange: ordinary LLMs. Purple: decision-specialized generative Tev1. Navy: references.\n'
             'References tested October 15/16/18; saved scores and costs unchanged. Two requests per model, connection through complete response.\n'
             'Costs normalize each actual 1,136-question run to 1,000. + ? means unknown charges. ~ means usage-times-tariff calculation.\n'
             'Nimble Max uses its October 16 tariff here, not its lower current tariff. Failed outputs remain unsuccessful; stopped runs are excluded.',
             fontsize=9, color='#475761')
    fig.subplots_adjust(left=.205, bottom=.2, top=.88, wspace=.26)
    save(fig, 'generative_accuracy_cost_speed')

    heat_ids = sorted(new | {'respan02', 'nimble_v4_max', 'jev114', 'openai/gpt-6-luna', 'luna_decisions'},
                      key=lambda m: -models[m]['primary']['correct'])
    data = np.array([[100 * f['models'][m]['accuracy_attempted'] for m in heat_ids] for f in s['by_family']])
    fig, ax = plt.subplots(figsize=(15, 13))
    im = ax.imshow(data, vmin=0, vmax=100, cmap='YlGnBu', aspect='auto')
    ax.set_xticks(range(len(heat_ids)), [labels[m] for m in heat_ids], rotation=45, ha='right')
    ax.set_yticks(range(25), [f"{f['family_id']}  {f['family']} (n={f['n']})" for f in s['by_family']])
    for i, f in enumerate(s['by_family']):
        for j, m in enumerate(heat_ids):
            ax.text(j, i, str(f['models'][m]['correct']), ha='center', va='center', fontsize=9,
                    color='white' if data[i, j] >= 64 else '#163149')
    ax.set_title('Which functions the additions handle', loc='left', fontsize=19, pad=30, fontweight='bold')
    ax.text(0, 1.02, 'Numbers: correct answers. Color: accuracy on all planned family items. * Added October 18.', transform=ax.transAxes)
    fig.colorbar(im, ax=ax, shrink=.6, pad=.025).set_label('Correct / planned (%)')
    fig.text(.29, .018, 'Four additions plus five reference routes. Tests: October 15/16/18, 2026 (Toronto).\n'
             'Family counts include dependent variants; no stopped sample is presented as a full-bank result.', fontsize=9, color='#475761')
    fig.subplots_adjust(left=.32, bottom=.21, top=.93, right=.95)
    save(fig, 'generative_family_accuracy')
    integrity = {'plotter_sha256': sha256(Path(__file__).read_bytes()).hexdigest(),
                 'source_summary_sha256': sha256((SOURCE / 'summary.json').read_bytes()).hexdigest(),
                 'matplotlib_version': matplotlib.__version__,
                 'files_sha256': {str(logical_relative(p, root=ROOT)): sha256(p.read_bytes()).hexdigest()
                                  for p in sorted(DEST.iterdir())}}
    (SOURCE / 'graphics_integrity.json').write_text(json.dumps(integrity, indent=2) + '\n')
    print('Built overall and two generative comparison figures; prior figures unchanged')


if __name__ == '__main__':
    main()
