"""Figures for the October 18 native expansion; previous figures stay unchanged."""
from repo_layout import logical_relative, repo_file
from hashlib import sha256
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
SOURCE=repo_file('overall_expanded_2026-10-18', root=ROOT)
DEST=SOURCE/'figures'


def save(fig,name):
    for suffix in ('png','svg'):
        target=DEST/(name+'.'+suffix)
        fig.savefig(target,dpi=170,bbox_inches='tight',facecolor='white')
        if suffix=='svg':target.write_text('\n'.join(line.rstrip() for line in target.read_text().splitlines())+'\n')
    plt.close(fig)


def main():
    s=json.loads((SOURCE/'summary.json').read_text())
    assert not s['pending_model_ids'] and len(s['native_added_october_18_model_ids'])==14
    ids=s['publication']['eligible_model_ids']
    models={m:s['models'][m] for m in ids}
    new=set(s['native_added_october_18_model_ids'])
    native={'jev113','jev114','luna_decisions'}|set(s['native_added_model_ids'])|new
    labels={m:models[m]['label']+(' *' if m in new else '') for m in ids}
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,
                         'axes.spines.top':False,'axes.spines.right':False,'axes.titleweight':'bold'})
    DEST.mkdir(parents=True,exist_ok=True)
    order=sorted(ids,key=lambda m:models[m]['primary']['correct'])
    height=max(9,len(order)*.4+2)
    fig,ax=plt.subplots(figsize=(14,height))
    y=np.arange(len(order))
    values=[100*models[m]['primary']['accuracy_attempted'] for m in order]
    bars=ax.barh(y-.1,values,height=.48,color=['#e18a29' if m in new else '#214b70' if m in native else '#21867d' for m in order])
    core=[100*models[m]['by_role']['core']['accuracy_attempted'] for m in order]
    ax.scatter(core,y+.23,marker='D',s=14,color='#1b2630',label='640 core items',zorder=4)
    for i,m in enumerate(order): ax.text(values[i]+.8,i-.1,f"{values[i]:.1f}%  ({models[m]['primary']['correct']}/1,136)",va='center',fontsize=9)
    ax.set_yticks(y,[labels[m] for m in order])
    ax.set_xlim(0,111);ax.set_xticks([0,20,40,60,80,100])
    ax.set_xlabel('Correct / all 1,136 planned first attempts (%)')
    ax.set_title(f'{len(order)} decision and reasoning-off routes on the same text bank',loc='left',fontsize=18,pad=35)
    ax.text(0,1.025,'Orange: 14 completed native additions, October 18. Navy: prior native routes. Teal: prior regular LLMs.',transform=ax.transAxes,fontsize=10)
    ax.legend(frameon=False,loc='lower right');ax.grid(axis='x',alpha=.18);ax.set_axisbelow(True)
    fig.text(.23,.025,'* Added October 18, 2026 (Toronto). Prior results: October 15/16, unchanged. Failures count as unsuccessful.\nHaiku, DeepSeek and Phi-4 remain outside the main ranking under the existing 5% output-failure rule.\nThe 496 variants/checks are dependent on core cases; this is a descriptive bank result.',fontsize=9,color='#475761')
    fig.subplots_adjust(left=.25,bottom=.11,top=.92)
    save(fig,'overall_accuracy')

    focus=list(new|{'nimble_v4_max','jev114','luna_decisions','openai/gpt-6-luna'})
    focus=[m for m in focus if m in models]
    focus=sorted(focus,key=lambda m:-models[m]['primary']['correct'])
    fig,axes=plt.subplots(1,3,figsize=(18,11),sharey=True,gridspec_kw={'width_ratios':[1,1.25,1.1]})
    y=np.arange(len(focus));colors=['#e18a29' if m in new else '#214b70' for m in focus]
    accuracy=[100*models[m]['primary']['accuracy_attempted'] for m in focus]
    axes[0].barh(y,accuracy,color=colors,height=.6)
    for i,v in enumerate(accuracy):axes[0].text(v+1,i,f'{v:.1f}%',va='center')
    axes[0].set_xlim(0,110);axes[0].set_xlabel('Correct / planned (%)');axes[0].set_title('First-attempt accuracy',loc='left')
    medians=[models[m]['latency_first_all']['median_ms'] for m in focus]
    p95=[models[m]['latency_first_all']['p95_ms'] for m in focus]
    axes[1].hlines(y,medians,p95,color='#91a9ba',linewidth=2)
    axes[1].scatter(medians,y,color=colors,s=32,label='Median',zorder=3)
    axes[1].scatter(p95,y,color='#214b70',s=20,marker='D',label='p95',zorder=3)
    for i,v in enumerate(medians):axes[1].text(v*1.04,i+.2,f'{v:.0f}',fontsize=9,va='top')
    axes[1].set_xscale('log');axes[1].set_xlabel('Full-response milliseconds (log scale)');axes[1].set_title('All 1,136 first attempts',loc='left');axes[1].legend(frameon=False,loc='lower right')
    costs=[models[m]['known_usd_per_1000_questions']*100 for m in focus]
    axes[2].barh(y,costs,color=colors,height=.6)
    for i,m in enumerate(focus):
        cost=models[m]['cost_all_attempts']
        text=f'{costs[i]:.2f}c'+(' + ?' if cost['missing_attempts'] else '')
        if cost.get('sources',{}).get('usage_times_published_tariff'):text='~'+text
        axes[2].text(costs[i]+.08,i,text,va='center',fontsize=9)
    axes[2].set_xlim(0,max(costs)*1.4);axes[2].set_xlabel('US cents per 1,000 questions');axes[2].set_title('Normalized cost, recoveries included',loc='left')
    axes[0].set_yticks(y,[labels[m] for m in focus]);axes[0].invert_yaxis()
    for ax in axes:ax.grid(axis='x',alpha=.16);ax.set_axisbelow(True)
    fig.suptitle('14 completed native additions and four reference routes',x=.04,ha='left',fontsize=20,fontweight='bold')
    fig.text(.04,.025,'New tests: October 18, 2026. References: October 15/16 (Toronto). Orange marks new native decision routes.\nPer-model concurrency: 2. Connect through full response, new HTTPS connection per attempt. Backend and load differ.\nCosts normalize each actual 1,136-question run to 1,000 questions. + ? indicates unreported error charges.\n~ Nimble cost calculated using its captured October 16 tariff; promotions and later tariff changes are not retroactive.',fontsize=10,color='#475761')
    fig.subplots_adjust(left=.21,bottom=.15,top=.91,wspace=.25)
    save(fig,'native_accuracy_cost_speed')

    data=np.array([[100*f['models'][m]['accuracy_attempted'] for m in focus] for f in s['by_family']])
    fig,ax=plt.subplots(figsize=(21,13))
    im=ax.imshow(data,vmin=0,vmax=100,cmap='YlGnBu',aspect='auto')
    ax.set_xticks(range(len(focus)),[labels[m] for m in focus],rotation=50,ha='right')
    ax.set_yticks(range(25),[f"{f['family_id']}  {f['family']} (n={f['n']})" for f in s['by_family']])
    for i,f in enumerate(s['by_family']):
        for j,m in enumerate(focus):ax.text(j,i,str(f['models'][m]['correct']),ha='center',va='center',fontsize=9,color='white' if data[i,j]>=64 else '#163149')
    ax.set_title('Where the native additions succeed and fail',loc='left',fontsize=19,pad=30)
    ax.text(0,1.02,'Numbers: correct count in each family. Color: percentage of planned questions. * Tested October 18.',transform=ax.transAxes)
    fig.colorbar(im,ax=ax,shrink=.6,pad=.02).set_label('Correct / planned (%)')
    fig.text(.25,.018,'14 completed additions plus four references; unchanged inputs and scoring. October 15/16/18, 2026 (Toronto).\nSolar Decide stopped for latency and excluded from full-bank plots. Family counts include dependent variants.',fontsize=10,color='#475761')
    fig.subplots_adjust(left=.27,bottom=.23,top=.93,right=.95)
    save(fig,'native_family_accuracy')
    write=dict(plotter_sha256=sha256(Path(__file__).read_bytes()).hexdigest(),matplotlib_version=matplotlib.__version__,
               source_summary_sha256=sha256((SOURCE/'summary.json').read_bytes()).hexdigest(),
               files_sha256={logical_relative(p, root=ROOT).as_posix():sha256(p.read_bytes()).hexdigest() for p in sorted(DEST.iterdir())})
    (SOURCE/'graphics_integrity.json').write_text(json.dumps(write,indent=2)+'\n')
    print('Built three October 18 comparison figures; prior figures unchanged')


if __name__=='__main__':main()
