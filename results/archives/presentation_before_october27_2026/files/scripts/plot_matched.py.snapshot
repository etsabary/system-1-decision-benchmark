"""Plot the eleven selected October 15 runs with matched response timing."""
from repo_layout import repo_file
from hashlib import sha256
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SOURCE = repo_file('matched_2026-10-15', root=ROOT)
DEST = repo_file('figures', root=ROOT)
NATIVE = {'jev113', 'jev114', 'luna_decisions'}
SHORT = {'jev113':'Jev 1.13','jev114':'Jev 1.14','luna_decisions':'Luna Decisions',
         'openai/gpt-6-luna':'Luna regular','openai/gpt-5.4-nano':'GPT-5.4 nano',
         'google/gemini-2.5-flash-lite':'Gemini 2.5 Flash-Lite','ibm-granite/granite-4.2-8b':'Granite 4.2 8B',
         'qwen/qwen3-30b-a3b-instruct-2507':'Qwen3-30B-A3B Instruct','microsoft/phi-4':'Phi-4 14B',
         'mistralai/mistral-nemo':'Mistral NeMo 12B','inception/mercury-2.5':'Mercury 2.5'}


def save(fig, name):
    fig.savefig(DEST/('matched_'+name+'.png'), dpi=170, bbox_inches='tight', facecolor='white')
    svg = DEST/('matched_'+name+'.svg')
    fig.savefig(svg, bbox_inches='tight', facecolor='white')
    svg.write_text('\n'.join(line.rstrip() for line in svg.read_text().splitlines())+'\n')
    plt.close(fig)


def main():
    summary = json.loads((SOURCE/'summary.json').read_text())
    assert summary['status'] == 'COMPLETE_SAME_DAY_ELEVEN_MODELS_1136_EACH'
    models = summary['models']
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,
                         'axes.spines.top':False,'axes.spines.right':False,'axes.titleweight':'bold'})
    order = sorted(models, key=lambda m: models[m]['primary']['correct'])
    fig, ax = plt.subplots(figsize=(12, 8))
    y = np.arange(len(order))
    full = [100*models[m]['primary']['accuracy_attempted'] for m in order]
    core = [100*models[m]['by_role']['core']['accuracy_attempted'] for m in order]
    ax.barh(y-.10, full, height=.48, color=['#163e65' if m in NATIVE else '#18867d' for m in order])
    ax.scatter(core, y+.23, marker='D', s=36, color='#efb83d', edgecolors='#6b511a', zorder=3, label='Core-only accuracy (640 questions)')
    for i, m in enumerate(order):
        ax.text(full[i]+1, i-.10, f"{full[i]:.1f}%  ({models[m]['primary']['correct']}/1,136)", va='center', fontsize=10)
    ax.set_yticks(y, [SHORT[m] for m in order]); ax.set_xlim(0, 112)
    ax.set_xticks([0, 20, 40, 60, 80, 100]); ax.set_xlabel('Correct / all planned questions (%)')
    ax.grid(axis='x', alpha=.17); ax.set_axisbelow(True)
    ax.set_title('Eleven models on the same text decision bank', loc='left', fontsize=17, pad=38)
    ax.text(0, 1.035, 'Bars: all 1,136 questions. Navy: native Decisions. Teal: regular LLMs with switchable reasoning off.', transform=ax.transAxes, fontsize=10)
    ax.legend(loc='lower right', frameon=False)
    fig.text(.125,.015,'All eleven tested October 15, 2026 (Toronto). First attempts only; failures and invalid outputs unsuccessful.\nThree Decisions services rerun; eight LLM runs unchanged. Core and related variants are not independent observations.',fontsize=9,color='#45535c')
    fig.subplots_adjust(bottom=.13)
    save(fig,'overall_accuracy')

    columns = sorted(models, key=lambda m: -models[m]['primary']['correct'])
    data = np.array([[100*f['models'][m]['accuracy_attempted'] for m in columns] for f in summary['by_family']])
    fig, ax = plt.subplots(figsize=(16,14))
    im = ax.imshow(data,vmin=0,vmax=100,cmap='YlGnBu',aspect='auto')
    ax.set_xticks(range(len(columns)),[SHORT[m] for m in columns],rotation=40,ha='right')
    ax.set_yticks(range(25),[f"{f['family_id']}  {f['family']} (n={f['n']})" for f in summary['by_family']])
    for i,f in enumerate(summary['by_family']):
        for j,m in enumerate(columns):
            ax.text(j,i,str(f['models'][m]['correct']),ha='center',va='center',fontsize=9,
                    color='white' if data[i,j]>=63 else '#162d42')
    ax.set_title('Which functions hold up, and which do not?',loc='left',fontsize=18,pad=28)
    ax.text(0,1.018,'Labels: correct count. Color: accuracy within each family. Columns sorted by overall strict accuracy.',transform=ax.transAxes,fontsize=10)
    fig.colorbar(im,ax=ax,shrink=.6,pad=.02).set_label('Correct / planned (%)')
    fig.text(.32,.015,'Same 1,136 questions; 25 families. All services tested October 15, 2026.\nSingle-shot decisions; three refreshed native services and eight unchanged regular LLM runs.',fontsize=9,color='#45535c')
    fig.subplots_adjust(left=.32,bottom=.17,top=.94,right=.95)
    save(fig,'family_accuracy')

    order = sorted(models,key=lambda m:models[m]['latency_first_all']['median_ms'])
    fig,axes = plt.subplots(1,2,figsize=(14,8),sharey=True)
    y = np.arange(len(order))
    costs = [100*models[m]['cost_all_attempts']['known_usd'] for m in order]
    med = [models[m]['latency_first_all']['median_ms']/1000 for m in order]
    p95 = [models[m]['latency_first_all']['p95_ms']/1000 for m in order]
    axes[0].barh(y,costs,color='#18867d',height=.6)
    for i,value in enumerate(costs):
        missing = models[order[i]]['cost_all_attempts']['missing_attempts']
        axes[0].text(value+.06,i,f'{value:.2f}¢'+(f' + {missing} unknown' if missing else ''),va='center',fontsize=9)
    axes[0].set_xlim(0,max(costs)*1.5);axes[0].set_xlabel('Known US cents / actual 1,136-question run')
    axes[0].set_title('Cost, including recovery attempts',loc='left')
    axes[0].set_yticks(y,[SHORT[m] for m in order])
    axes[1].barh(y,med,color='#163e65',height=.6,label='Median')
    axes[1].scatter(p95,y,color='#c37c25',marker='D',s=35,label='p95')
    for i,value in enumerate(med):
        axes[1].text(value+.025,i+.23,f'{value:.3f} s',ha='left',va='top',fontsize=9)
    axes[1].set_xlabel('First-attempt connect-to-full-response seconds')
    axes[1].set_xlim(0,max(p95)*1.2)
    axes[1].set_title('Response time, same client timing method',loc='left')
    axes[1].legend(frameon=False,loc='upper right')
    for ax in axes:
        ax.grid(axis='x',alpha=.17);ax.set_axisbelow(True)
    axes[0].invert_yaxis()
    fig.suptitle('Eleven services through OpenRouter',x=.08,ha='left',fontsize=18,fontweight='bold')
    fig.text(.08,.025,'October 15, 2026, two sessions. New HTTPS connection per attempt; two concurrent requests/model per wave.\nAll 1,136 first attempts per model, including failures. Different native/chat APIs and backend hardware.\nMercury uses its discounted tariff. Missing error charges remain unknown. Latency is not tokens/second.',fontsize=9,color='#45535c')
    fig.subplots_adjust(left=.2,top=.9,bottom=.16,wspace=.18)
    save(fig,'cost_and_speed')
    paths = sorted(DEST.glob('matched_*'))
    (SOURCE/'graphics_integrity.json').write_text(json.dumps({
        'plotter_sha256':sha256(Path(__file__).read_bytes()).hexdigest(),'matplotlib_version':matplotlib.__version__,
        'source_summary_sha256':sha256((SOURCE/'summary.json').read_bytes()).hexdigest(),
        'files_sha256':{p.name:sha256(p.read_bytes()).hexdigest() for p in paths}},indent=2)+'\n')
    print(json.dumps({'figures':[p.name for p in paths]}))


if __name__=='__main__':
    main()
