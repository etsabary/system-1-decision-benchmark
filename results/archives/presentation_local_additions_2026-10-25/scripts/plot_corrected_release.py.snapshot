"""Plot only complete configurations on the corrected active question bank."""
from repo_layout import repo_file
from hashlib import sha256
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SOURCE = repo_file('corrected_2026-10-18', root=ROOT)
DEST = SOURCE / 'figures'
ALIASES = {'tev1_4b_native': 'Tev1 4B (native adapter)', 'qwen3_235b': 'Qwen3 235B A22B Instruct'}
NAVY, TEAL, PURPLE = '#214b70', '#22836f', '#995080'


def save(fig, name):
    for suffix in ('png', 'svg'):
        path = DEST / (name + '.' + suffix)
        fig.savefig(path, dpi=170, bbox_inches='tight', facecolor='white')
        if suffix == 'svg':
            path.write_text('\n'.join(line.rstrip() for line in path.read_text().splitlines()) + '\n')
    plt.close(fig)


def main():
    s = json.loads((SOURCE / 'summary.json').read_text())
    assert s['model_count'] == len(s['models']) == 36
    models = s['models']
    label = lambda m: ALIASES.get(m, models[m]['label'])
    rank = sorted(s['publication']['eligible_model_ids'], key=lambda m: models[m]['primary']['correct'])
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10,
                         'axes.spines.top': False, 'axes.spines.right': False})
    DEST.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(15, 18))
    values = [100*models[m]['primary']['accuracy_attempted'] for m in rank]
    ax.barh(np.arange(len(rank))-.08, values, height=.5,
            color=[TEAL if m in ('respan02','pplx_decider12','nimble_v4_max') else NAVY for m in rank])
    ax.scatter([100*models[m]['by_role']['core']['accuracy_attempted'] for m in rank],
               np.arange(len(rank))+.24, marker='D', s=15, color='#172833', label='640 core questions', zorder=4)
    for i,m in enumerate(rank):
        ax.text(values[i]+.8, i-.08, f"{values[i]:.1f}% ({models[m]['primary']['correct']}/1,136)", va='center', fontsize=9)
    ax.set_yticks(np.arange(len(rank)), [label(m) for m in rank])
    ax.set_xlim(0,111);ax.set_xticks(range(0,101,20));ax.set_xlabel('Correct / all 1,136 first attempts (%)')
    ax.grid(axis='x',alpha=.18);ax.set_axisbelow(True);ax.legend(frameon=False,loc='lower right')
    fig.suptitle('36 models on 1,136 text decisions',x=.30,y=.98,ha='left',fontsize=21,fontweight='bold')
    fig.text(.30,.953,'Question audit completed. Two clarified questions retested on October 18, 2026.',fontsize=10)
    fig.text(.30,.018,'Tests: October 15, 16 and 18, 2026 (Toronto). Each row combines 1,134 retained cases + 2 corrected cases.\n'
             'All first-attempt failures remain unsuccessful. Core diamonds use 640 underlying questions.\n'
             'The 496 related variants are dependent. Partial and output-noncompliant runs are outside the ranking.',fontsize=9,color='#475761')
    fig.subplots_adjust(left=.30,bottom=.09,top=.925)
    save(fig,'overall_accuracy')

    focus = sorted(['respan02','pplx_decider12','nimble_v4_max','liquid_ultra','jev114',
                    'mercury_decide','gemma4_31b','openai/gpt-6-luna','luna_decisions','tev1_4b_native'],
                   key=lambda m:-models[m]['primary']['correct'])
    fig,axes=plt.subplots(1,3,figsize=(18,8),sharey=True,gridspec_kw={'width_ratios':[1,1.2,1.2]})
    y=np.arange(len(focus));colors=[PURPLE if m in ('gemma4_31b','openai/gpt-6-luna','tev1_4b_native') else NAVY for m in focus]
    accuracy=[100*models[m]['primary']['accuracy_attempted'] for m in focus]
    axes[0].barh(y,accuracy,color=colors,height=.6)
    for i,v in enumerate(accuracy):axes[0].text(v+1,i,f'{v:.1f}%',va='center')
    axes[0].set_xlim(0,110);axes[0].set_xlabel('Correct / 1,136 (%)');axes[0].set_title('First-attempt accuracy',loc='left',fontweight='bold')
    med=[models[m]['latency_first_all']['median_ms'] for m in focus]
    tail=[models[m]['latency_first_all']['p95_ms'] for m in focus]
    axes[1].hlines(y,med,tail,color='#9aaebd',linewidth=2)
    axes[1].scatter(med,y,color=colors,s=32,label='Median',zorder=3)
    axes[1].scatter(tail,y,color=TEAL,s=23,marker='D',label='p95',zorder=3)
    for i,v in enumerate(med):axes[1].text(v*1.025,i+.2,f'{v:.0f}',va='top',fontsize=9)
    axes[1].set_xscale('log');axes[1].set_xlim(150,2600);axes[1].set_xlabel('Full-response ms (log scale)')
    axes[1].set_title('All 1,136 pooled response times',loc='left',fontweight='bold');axes[1].legend(frameon=False,loc='upper center',bbox_to_anchor=(.5,-.1),ncol=2)
    cents=[100*models[m]['known_usd_per_1000_questions'] for m in focus]
    axes[2].barh(y,cents,color=colors,height=.6)
    for i,m in enumerate(focus):
        v=models[m];text=f'{cents[i]:.2f}c'+(' + ?' if v['cost_all_attempts']['missing_attempts'] else '')
        if v['reported_api_cost_all_attempts']['known_usd']!=v['cost_all_attempts']['known_usd']:text='~'+text
        axes[2].text(cents[i]+.07,i,text,va='center',fontsize=9)
    axes[2].set_xlim(0,max(cents)*1.45);axes[2].set_xlabel('US cents per 1,000 questions')
    axes[2].set_title('Known/accounted normalized cost',loc='left',fontweight='bold')
    axes[0].set_yticks(y,[label(m) for m in focus]);axes[0].invert_yaxis()
    for ax in axes:ax.grid(axis='x',alpha=.16);ax.set_axisbelow(True)
    fig.suptitle('Accuracy, response time and cost on the corrected bank',x=.025,ha='left',fontsize=20,fontweight='bold')
    fig.text(.025,.035,'Test dates: October 15, 16 and 18, 2026 (Toronto). Audit correction: October 18. Each row selects 1,134 original + 2 fresh cases.\n'
             'Cost is actual selected-run cost ÷ 1,136 × 1,000, including permitted recoveries. + ? means unreported charges; ~ means tariff-calculated.\n'
             'Captured prices and promotions remain attached to original calls. Nimble Max uses the lower October 18 tariff only for the two new calls.\n'
             'Purple: generative routes (Tev is decision-specialized). Navy: native decision routes. Full-body timings include failures.',fontsize=9,color='#475761')
    fig.subplots_adjust(left=.205,bottom=.20,top=.88,wspace=.26)
    save(fig,'accuracy_cost_speed')

    data=np.array([[100*f['models'][m]['accuracy_attempted'] for m in focus] for f in s['by_family']])
    fig,ax=plt.subplots(figsize=(16,13))
    im=ax.imshow(data,vmin=0,vmax=100,cmap='YlGnBu',aspect='auto')
    ax.set_xticks(range(len(focus)),[label(m) for m in focus],rotation=45,ha='right')
    ax.set_yticks(range(25),[f"{f['family_id']}  {f['family']} (n={f['n']})" for f in s['by_family']])
    for i,f in enumerate(s['by_family']):
        for j,m in enumerate(focus):ax.text(j,i,str(f['models'][m]['correct']),ha='center',va='center',fontsize=9,color='white' if data[i,j]>=64 else '#163149')
    ax.set_title('Different models lead different decision functions',loc='left',fontsize=19,pad=30,fontweight='bold')
    ax.text(0,1.02,'Numbers: correct answers. Color: accuracy on all planned family questions.',transform=ax.transAxes)
    fig.colorbar(im,ax=ax,shrink=.6,pad=.025).set_label('Correct / planned (%)')
    fig.text(.29,.018,'Tests: October 15, 16 and 18, 2026 (Toronto). Two question replacements tested October 18.\n'
             'All 25 families retain their size. Dependent variants are included. Complete 36-model tables accompany this selected comparison.',fontsize=9,color='#475761')
    fig.subplots_adjust(left=.31,bottom=.23,top=.93,right=.95)
    save(fig,'family_accuracy')
    (SOURCE/'graphics_integrity.json').write_text(json.dumps({'plotter_sha256':sha256(Path(__file__).read_bytes()).hexdigest(),
        'source_summary_sha256':sha256((SOURCE/'summary.json').read_bytes()).hexdigest(),
        'files_sha256':{p.name:sha256(p.read_bytes()).hexdigest() for p in sorted(DEST.iterdir())}},indent=2)+'\n')
    print('Built three corrected36-model figures, each PNG and SVG')


if __name__=='__main__':main()
