"""Publish audited local routes beside unchanged hosted results. Offline only.

--capture reads the owner's private, revision-bound evidence and answer key.
The public release contains aggregate scores, metadata and answer-free timing
rows. Public rebuilds and validation require neither credentials nor the key.
"""
from collections import Counter
from copy import deepcopy
import csv
from datetime import datetime
from hashlib import sha256
from html import escape
import io
import json
import math
from pathlib import Path
import shutil
import subprocess
import sys
from zoneinfo import ZoneInfo

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import numpy as np

import october27_history as archive
import build_readable_report as readable
from build_october18_report import PALETTES, legend_markdown
import publish_opus5_reference as prior
from publish_consolidated_report import table
from repo_layout import repo_file

ROOT = Path(__file__).resolve().parents[1]
NAME = 'native_updates_2026-10-27'
DEST = ROOT / 'results/releases' / NAME
SITE = 'https://etsabary.github.io/system-1-decision-benchmark/report.html'
PREVIOUS = ROOT / 'results/releases/native_additions_2026-10-25'
PURPLE, HOSTED, YELLOW = '#7c3aed', '#16728c', (.95, .83, .42, .60)



def digest(path):
    return sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(value.rstrip() + '\n' if isinstance(value, str) else json.dumps(value, indent=2) + '\n')


def mid(name):
    return 'local_' + name.replace(':', '_').replace('-', '_').replace('.', '_')


def capture():
    from october27_text_evidence import capture as reconcile
    reconcile()



def load():
    s=json.loads((DEST/'statistics.json').read_text())
    old=json.loads((PREVIOUS/'statistics.json').read_text())
    assert s['model_count']==54 and all(s['models'][m]==v for m,v in old['models'].items())
    return s,json.loads((PREVIOUS/'category_guide.json').read_text())



def is_local(s, model):
    return model in s['local_model_ids']


def price(mid, model, normalized=True):
    if model.get('execution_location') == 'local':return 'Local compute cost unmeasured'
    value=prior.previous.price(mid, model, normalized)
    return '~'+value if mid=='celeris11_decision' else value


def badge():
    return '<small class="local-badge">Local · RTX 2060 · 6 GB</small>'


def mark_names(text, s):
    for mid in s['local_model_ids']:
        label=escape(s['models'][mid]['label'])
        text=text.replace('<th scope="row">'+label+'</th>', '<th scope="row" class="local-name">'+label+badge()+'</th>')
    return text


def summary_html(s):
    rows=[]
    for mid in s['ranked_model_ids']:
        m=s['models'][mid]; local=is_local(s,mid); cls='local-model' if local else 'llm-reference' if mid in s['reference_model_ids'] else 'hosted-model'
        mean=m.get('mean_response_ms',m.get('mean_ms'))
        row=f'<tr class="{cls}" data-summary-model="{mid}"><th scope="row">{escape(m["label"])}'+(badge() if local else '')+'</th>'
        row+=f'<td>{"Local decision/classifier" if local else s["model_kinds"][mid]}</td><td>{m["correct"]}/1342<br><b>{m["accuracy"]:.1%}</b></td>'
        row+='<td>'+('—' if mean is None else f'{mean:.0f} ms')+'</td>'
        for key in ('median_ms','p95_ms'):
            band=next((i for i,b in enumerate((250,500,1000)) if m[key]<=b),3)
            row+=f'<td style="background:{PALETTES[band]}">{m[key]:.0f} ms</td>'
        cost=m['cost']; value=price(mid,m)
        if local or cost.get('public_free_access'):shade='#edf1f5'
        else:shade=PALETTES[next((i for i,b in enumerate((.01,.025,.05)) if cost['known_usd_per_1000']<=b),3)]
        row+=f'<td style="background:{shade}">{escape(value)}</td><td>{escape(price(mid,m,False))}</td></tr>'
        rows.append(row)
    return '<div class="scroll"><table><thead><tr><th>Model</th><th>Type / setting</th><th>Correct / questions</th><th>Mean</th><th>Median</th><th>p95</th><th>Cost / 1,000</th><th>1,342 cost / basis</th></tr></thead><tbody>'+''.join(rows)+'</tbody></table></div>'


def overview(s, *, local_only=False):
    ids=s['local_model_ids'] if local_only else s['ranked_model_ids']; models=[s['models'][m] for m in ids]; y=np.arange(len(ids))
    with plt.rc_context({'font.family':'DejaVu Sans','svg.fonttype':'none','svg.hashsalt':'local-20261025-v1'}):
        columns=2 if local_only else 3
        ratios=[1.15,1.1] if local_only else [1.15,1.05,1.12]
        fig,axes=plt.subplots(1,columns,figsize=(14 if local_only else 17,max(10,len(ids)*.49+4)),sharey=True,gridspec_kw={'width_ratios':ratios})
        colors=[PURPLE if is_local(s,m) else YELLOW if m in s['reference_model_ids'] else HOSTED for m in ids]
        axes[0].barh(y,[100*m['accuracy'] for m in models],color=colors)
        axes[0].axvline(20,color='#6b7280',linestyle='--',linewidth=1,label='20% uniform guessing')
        axes[0].set_xlim(0,109);axes[0].set_yticks(y,[readable.short(m['label']) for m in models],fontsize=12);axes[0].invert_yaxis()
        for label,mid in zip(axes[0].get_yticklabels(),ids):
            if is_local(s,mid):label.set_color(PURPLE);label.set_weight('bold')
        for yy,mid,m in zip(y,ids,models):
            axes[0].text(100*m['accuracy']+1,yy,f"{m['accuracy']:.1%}",va='center',fontsize=11)
            axes[1].plot([m['median_ms'],m['p95_ms']],[yy,yy],color='#8896a3')
            band=next((i for i,b in enumerate((250,500,1000)) if m['median_ms']<=b),3)
            axes[1].scatter(m['median_ms'],yy,color=PALETTES[band],edgecolor='#35424d',s=55)
            axes[1].scatter(m['p95_ms'],yy,color='#35424d',marker='d',s=20)
            if local_only:continue
            c=m['cost']
            if is_local(s,mid) or c.get('public_free_access'):
                text='Local compute\nunmeasured' if is_local(s,mid) else 'Promotional free*' if mid in ('mammoth1','elephant1') else 'Free public access*'
                axes[2].text(.03,yy,text,transform=axes[2].get_yaxis_transform(),va='center',fontsize=10,color=PURPLE if is_local(s,mid) else '#35424d')
            else:
                b=next((i for i,v in enumerate((.01,.025,.05)) if c['known_usd_per_1000']<=v),3)
                axes[2].scatter(c['known_usd_per_1000'],yy,color=PALETTES[b],edgecolor='#35424d',s=55)
                if c['unknown_attempts']:axes[2].text(c['known_usd_per_1000']*1.15,yy,'+ ?',va='center',fontsize=10)
        axes[1].set_xscale('log')
        if not local_only:
            axes[2].set_xscale('log');axes[2].set_xlim(.002,7)
        axes[0].set_xlabel('Correct first decisions (%)\nDashed line: 20% uniform guessing')
        axes[1].set_xlabel('Response time (ms, log scale)\nCircle: median · diamond: p95')
        if not local_only:axes[2].set_xlabel('USD / 1,000 (log scale)\nLocal hardware and electricity unmeasured')
        for ax,title in zip(axes,('Accuracy','Speed','Cost')):
            ax.set_title(title,fontsize=15,pad=20);ax.grid(axis='x',alpha=.2);ax.set_axisbelow(True)
            for spine in ax.spines.values():spine.set_visible(False)
        title='20 local models · RTX 2060 6 GB · 1,342 questions' if local_only else '54 routes · 30 hosted decision models · 20 local models · 4 LLM references'
        fig.suptitle(title,fontsize=17,y=.985)
        handles=[Patch(facecolor=PURPLE,label='Local · RTX 2060 · 6 GB')] if local_only else [Patch(facecolor=HOSTED,label='Hosted decision models'),Patch(facecolor=PURPLE,label='Local · RTX 2060 · 6 GB'),Patch(facecolor=YELLOW,edgecolor='#9c761c',label='LLM references, reasoning off')]
        fig.legend(handles=handles,loc='upper center',bbox_to_anchor=(.5,.955 if local_only else .96),ncol=len(handles),frameon=False,fontsize=11 if local_only else 10)
        fig.text(.025,.025,'Local runs: October 25, 2026, Ollaya 0.17.0, CUDA, one request/model at a time; warm-up/loading excluded.\nRTX 2060 6 GB was chosen deliberately as an older, more accessible hardware setup.\nHosted measurements retain their original dates, providers and loads. Latency is route-specific, not controlled hardware speed.\nLocal operating cost is unmeasured. *Free access is not a production tariff; + ? means missing hosted charges.',fontsize=10)
        fig.subplots_adjust(left=.29,right=.98,top=.86 if local_only else .91,bottom=.14 if local_only else .12,wspace=.32)
        stem='local_models' if local_only else 'accuracy_speed_cost'
        for suffix in ('png','svg'):fig.savefig(DEST/(stem+'.'+suffix),dpi=160,metadata={'Date':None} if suffix=='svg' else {})
        plt.close(fig)


def category_plot(s, group):
    import textwrap
    slug,title,fids,_=group; ids=s['ranked_model_ids']; models=[s['models'][m] for m in ids]
    values=np.array([[m['families'][fid]['accuracy'] for fid in fids] for m in models])
    with plt.rc_context({'font.family':'DejaVu Sans','svg.fonttype':'none','svg.hashsalt':'local-categories-20261025'}):
        fig,ax=plt.subplots(figsize=(12.6,len(ids)*.55+5))
        im=ax.imshow(values,vmin=0,vmax=1,cmap='YlGnBu',aspect='auto')
        ax.set_yticks(range(len(ids)),[readable.short(m['label']) for m in models],fontsize=12)
        for label,mid in zip(ax.get_yticklabels(),ids):
            if is_local(s,mid):label.set_color(PURPLE);label.set_weight('bold')
        ax.set_xticks(range(len(fids)),['\n'.join(textwrap.wrap(readable.LABELS[fid],13,break_long_words=False))+f"\n{models[0]['families'][fid]['n']} questions" for fid in fids],fontsize=11)
        ax.tick_params(length=0,labeltop=True,labelbottom=False,pad=8)
        for i,m in enumerate(models):
            for j,fid in enumerate(fids):
                c=m['families'][fid];ax.text(j,i,f"{c['correct']}/{c['n']}\n{c['accuracy']:.1%}",ha='center',va='center',fontsize=12,color=readable.color(c['accuracy'])[1])
        fig.colorbar(im,ax=ax,fraction=.025,pad=.025,shrink=.75).set_label('Accuracy, fixed 0–1 scale')
        fig.text(.025,.975,title,fontsize=19,weight='bold');fig.text(.025,.95,'Purple model names = local RTX 2060 runs. Cell colors always encode accuracy.',fontsize=11)
        fig.text(.025,.03,'Every cell: correct / questions, then percentage. Same overall-score order; 20% uniform guessing.\nSix newest categories have eight questions each; one answer moves a score by 12.5 percentage points.',fontsize=10)
        fig.subplots_adjust(left=.31,right=.95,top=.86,bottom=.09)
        for suffix in ('png','svg'):fig.savefig(DEST/(slug+'.'+suffix),dpi=160,metadata={'Date':None} if suffix=='svg' else {})
        plt.close(fig)


def findings(s):
    return [
      ('D3 Ultra adds 18 correct text decisions; Fastino retains the lead',
       'D3 Ultra scored 1,124/1,342 (83.8%), versus the October 20 D3 Turbo run at 1,106 (82.4%). It ranks sixth among all 54 complete configurations and fifth among the 30 hosted decision models. Fastino GLiDE retains 1,154 (86.0%), GPT-6 Sol without reasoning 1,143 (85.2%) and Mammoth-1 1,139 (84.9%). Drex Max and Respan Span-02 each retain 1,127. All 52 earlier records keep their original scores, timings, costs and dates.'),
      ('D3 gains on causal intervention and object tracking, with weaker procedure execution',
       'D3 Ultra answered 46/46 forward-conditional questions and 52/52 rule-counterexample questions. Causal intervention—working out what follows when a variable is deliberately changed—rose from Turbo’s 38/50 to 45/50. Object swaps rose from 31/52 to 36/52. Sequential procedures fell from 20/48 to 16/48; exact truth counting scored 39/71. The overall gain varies by operation.'),
      ('Liquid d1.1 makes its largest gain in exact truth counting',
       'Liquid d1.1 scored 1,044/1,342 (77.8%), 79 more than the older d1 run at 965 (71.9%). Exact truth counting—choosing the number of statements that are true—rose from 23/71 to 47/71, above D3 Ultra’s 39/71. Necessary conditions rose from 35/52 to 50/52. Boolean scope fell from 50/54 to 44/54, and object swaps from 33/52 to 27/52. Sequential procedures scored 10/48. Liquid d1-ultra retains the stronger overall score at 1,084 (80.8%).'),
      ('The image results differ from the text gains',
       'On the separate frozen 200-question image bank, D3 Ultra scored 148/200 (74.0%), seven fewer than the earlier Turbo’s 155 (77.5%). Liquid d1.1 scored 144/200 (72.0%), nine more than the older d1’s 135 (67.5%). Amos remains at 159 (79.5%) and Fastino at 158 (79.0%). The new image runs used the exact earlier native-provider PNG/JPEG bytes, question wording, options and order. Both supplied 200 usable answers. See the separate image report for 20-category profiles and timing.'),
      ('Both hosted text routes are fast in this measurement',
       'D3 Ultra measured 174 / 148 / 211 ms mean / median / p95, versus Turbo’s 182 / 165 / 298 ms. Liquid d1.1 measured 255 / 212 / 424 ms; older d1’s median / p95 was 206 / 827 ms. Fresh HTTPS requests ran serially within each provider; the two independent providers ran concurrently. All 2,684 new first attempts were usable and reported zero output tokens. No scored retries, shortened questions or tools. Provider hardware, load and dates differ, so these gaps do not isolate architecture.'),
      ('D3 free access and Liquid’s reported cost have different meanings',
       'D3 used its free public API; no monetary receipt or permanent production tariff is inferred. Liquid reported $0.00774762 for 1,342 text questions, or $0.00577319 per 1,000. Two admission probes added $0.00000240 separately. OpenRouter was pinned to Liquid and returned liquid/d1.1-20261027 throughout. The D3 request explicitly used vllm-sr/d3-ultra: the live service now aliases its old Turbo name to Ultra. Earlier Turbo measurements retain their October 20 identity and are not relabelled.'),
      ('The six newer domains separate different abilities',
       'Both new models scored 24/48 across the six eight-question domains. D3 led in worst-case choices without event probabilities (4/8 versus 2/8) and information-flow security (6/8 versus 4/8); Liquid led in known-risk choices (5/8 versus 4/8), buying information before choosing (4/8 versus 3/8), and possible concurrent histories (5/8 versus 3/8). Strategic choices tied at 4/8. One answer moves a domain score by 12.5 percentage points.'),
      ('The deliberately accessible local setup remains visible',
       'All 20 local configurations retain their published results and purple RTX 2060 6 GB badges. This older GPU was chosen deliberately to measure equipment readers may already have. D3 Flash Artemis remains the local accuracy leader at 995/1,342 (74.1%), with a 408 ms median. H2O-Lightning 4B has a lower 66.5% score and a shorter 259 ms median. Local hardware/electricity cost remains unmeasured; no speed on newer GPUs is projected.'),
      ('Scores describe this bank and these execution settings',
       'This is immediate fixed-choice decision making without tools, generated reasoning or agentic iteration. The four selected LLM references preserve their recorded reasoning-off controls and verification limits. Named hosted model identities and native zero-output responses do not attest immutable weights or all internal computation. All earlier failures, partial exclusions, category sizes and the separate author-development diagnostic remain preserved. Blue marks hosted decisions, purple local runs and pale yellow LLM references; cell and speed/cost colors retain fixed scales.')]



def methods():
    return [
      '54 complete routes: 30 hosted decision models, 20 local configurations and four selected no-reasoning LLM references. Every route covers the same 1,342 questions across 31 categories: 72,468 first attempts. All 52 prior model records are unchanged. The developing bank has uneven category sizes and related variants; six categories have eight questions each.',
      'The two new hosted text models were tested October 27, 2026, America/Toronto. Exact frozen native state, instructions and five original choices, in the existing seeded order 2026101906. D3 explicitly requested vllm-sr/d3-ultra; OpenRouter requested liquid/d1.1 with only the Liquid provider, no fallback, returning liquid/d1.1-20261027. Start/end selected identity, provider and tariff were unchanged.',
      'One fresh HTTPS request per provider at a time, two independent hosted providers active concurrently. The unchanged timer spans connection through full response body; local encoding, preparation and pacing are excluded. Two synthetic admission probes per model are separate. Every first attempt is retained; no scored retries. After at least20 requests the cumulative median cutoff is 2,000ms, with a 5% unusable-output gate. Both completed with 1,342 usable native decisions and zero reported output tokens.',
      'D3 public access was free at test time, without monetary receipts or a production-price guarantee. Liquid costs use API-reported charges, with admission separate. Local electricity, hardware and depreciation remain unmeasured. Celeris/Fastino tariff estimates retain their original labels. Model dates, provider hardware/load and network/concurrency qualify speed comparisons.',
      'The 20 local configurations retain their October25 RTX2060 6GB / Ollaya0.17.0 / CUDA provenance and quantization-specific profiles. That older, more accessible setup was chosen deliberately. Loading and warmups are separate; no local run was repeated. All historical failures, three partial/blocked local routes and 26,840 raw local timing rows remain unchanged.',
      'Offline publication reconstructed all 2,684 new payloads, bound the frozen revision-specific private key, checked 31 category totals, native identity, raw timing, cost and sealed owner evidence. Public exports contain aggregates and answer-free timing hashes, not model choices, keys, per-item correctness, credentials or LAN addresses. Public checks reproduce coverage, timing and aggregate arithmetic; they cannot independently recreate private-key scoring.',
      'The separate 1,305-question author-development diagnostic and existing answer-audit qualifications retain their scope. This result does not establish general superiority to frontier LLMs with reasoning enabled. The image report measures the same two named models separately; its scores are not folded into this text denominator.']



def exports(s, guide):
    write(DEST/'statistics.json',s);write(DEST/'category_guide.json',guide)
    buffer=io.StringIO(newline='');writer=csv.writer(buffer,lineterminator='\n')
    writer.writerow(['model_id','model','type','execution_location','hardware','vram_gb','precision','questions','correct','accuracy','mean_ms_if_measured','median_ms','p95_ms','known_cost_usd','known_cost_per1000_usd','cost_kind','route','test_dates_toronto'])
    for mid in s['ranked_model_ids']:
        m=s['models'][mid];c=m['cost'];writer.writerow([mid,m['label'],s['model_kinds'][mid],m.get('execution_location','hosted'),m.get('hardware','Provider hardware unreported'),m.get('vram_gb',''),m.get('precision',''),1342,m['correct'],m['accuracy'],m.get('mean_response_ms',m.get('mean_ms','')),m['median_ms'],m['p95_ms'],c['known_usd'],c['known_usd_per_1000'],c.get('kind','hosted_reported_or_accounted'),m['route'],'; '.join(sorted(m['dates_toronto']))])
    write(DEST/'model_statistics.csv',buffer.getvalue())
    buffer=io.StringIO(newline='');writer=csv.writer(buffer,lineterminator='\n');writer.writerow(['category_id','category','questions']+[s['models'][m]['label'] for m in s['ranked_model_ids']])
    for fid in readable.LABELS:writer.writerow([fid,readable.LABELS[fid],guide[fid]['questions']]+[readable.score(s['models'][m]['families'][fid]) for m in s['ranked_model_ids']])
    write(DEST/'category_scores.csv',buffer.getvalue())


CSS = '''
.local-badge{display:block;color:#5b21b6;background:#ede9fe;border:1px solid #c4b5fd;border-radius:4px;font-size:12px;padding:3px 6px;margin-top:6px;width:max-content;max-width:100%;white-space:normal}.local-model th,.local-name{border-left:5px solid #7c3aed!important}.local-model th{background:#f5f0ff}.route-legend{display:flex;gap:18px;flex-wrap:wrap;margin:18px 0}.swatch{display:inline-block;width:15px;height:15px;margin-right:7px;vertical-align:middle}.local-metadata td{white-space:normal}.local-note{border-left:5px solid #7c3aed;padding:15px 20px;background:#f5f0ff}.local-profiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:16px}.local-profile{padding:16px;border:1px solid #c4b5fd;border-top:4px solid #7c3aed;border-radius:6px;background:white}.local-profile p{font-size:14px}.local-profile h3{margin-top:0}.scroll{max-height:1000px;overflow:auto}.cards{margin-top:22px}.small{line-height:1.5}
'''


def local_profiles(s):
    parts=[]
    for mid in s['local_model_ids']:
        m=s['models'][mid]
        hi='; '.join(f"{readable.LABELS[c['family_id']]} {c['correct']}/{c['n']}" for c in m['highest_scoring_categories'][:3])
        lo='; '.join(f"{readable.LABELS[c['family_id']]} {c['correct']}/{c['n']}" for c in m['lowest_scoring_categories'][:3])
        parts.append('<article class="local-profile"><h3>'+escape(m['label'])+'</h3>'+badge()+f"<p><b>{m['correct']}/1342 · {m['accuracy']:.1%}</b> · {m['median_ms']:.0f} ms median</p><p><b>Reported precision:</b> "+escape(m['precision'])+'</p><p><b>Higher category scores:</b> '+escape(hi)+'</p><p><b>Lower category scores:</b> '+escape(lo)+'</p></article>')
    return '<div class="local-profiles">'+''.join(parts)+'</div>'


def quality(s):
    return table(['Model','Setting','Usable / 1342','Unsuccessful','First-attempt statuses'],[[m['label'],'Local RTX 2060' if is_local(s,mid) else 'Hosted',str(m['answered'])+'/1342',str(m['failed']),'; '.join(f'{k}: {v}' for k,v in m['first_statuses'].items())] for mid in s['ranked_model_ids'] for m in [s['models'][mid]]])


def category_markdown(s,guide,details=False):
    value=readable.markdown_groups(s,guide,details).replace('All 20 models','All 54 routes').replace('all 20 models','all 54 routes').replace(readable.NAME,NAME)
    import re
    return re.sub(r'https://etsabary.github.io/jev-1.14-comparison-benchmark/[^)# ]+/report.html',SITE,value)


def html(s,guide):
    import re
    old=(prior.DEST/'report.html').read_text();head=old[:old.index('<body>')+6]
    head=re.sub(r'<title>.*?</title>','<title>System 1 decisions: 54 routes, 20 local GPU models</title>',head)
    head=re.sub(r'content="opus5-october23-1342"', 'content="native-updates-october27-1342"',head)
    head=head.replace('</head>','<meta name="description" content="Compare 52 text decision routes on 1,342 questions: 30 hosted decision models, 20 local RTX 2060 configurations and four reasoning-off LLMs. Accuracy, latency, cost and 31 category profiles."><link rel="canonical" href="'+SITE+'"><style>'+CSS+'</style></head>')
    body='<main><h1>System 1 Decision Benchmark</h1><p>30 hosted decision models, 20 local decision/classifier models and four no-reasoning LLM references. Same 1,342 questions, 31 categories. Updated October 27, 2026.</p>'
    body+='<nav><a href="#overview">All 54 routes</a><a href="#local-results">Local GPU results</a><a href="#new-additions">Findings</a><a href="#functions">Named categories</a><a href="#method">Method and setup</a></nav>'
    body+='<div class="cards"><div class="card"><div class="label">Highest overall</div><div class="big">86.0%</div><div class="small">Fastino GLiDE · 1154/1342</div></div><div class="card"><div class="label">Highest local score</div><div class="big">74.1%</div><div class="small">D3 Flash Artemis 9B · 408 ms median</div></div><div class="card"><div class="label">Deliberate older-GPU setup</div><div class="big">6 GB</div><div class="small">RTX 2060 · CUDA · Ollaya 0.17.0</div></div><div class="card"><div class="label">Full matched coverage</div><div class="big">54 routes</div><div class="small">72,468 first attempts · 31 categories</div></div></div>'
    body+='<div class="route-legend"><span><i class="swatch" style="background:#16728c"></i>Hosted decision models</span><span><i class="swatch" style="background:#7c3aed"></i>Local · RTX 2060 · 6 GB</span><span><i class="swatch" style="background:#f4df9a"></i>LLM references, reasoning off</span></div>'
    body+='<section id="overview"><h2>All 54 routes: accuracy, speed and cost</h2><p>Every row covers 1,342 first attempts. Purple identifies local runs; it does not change the green-to-red speed/cost bands or the accuracy heatmap. The dashed accuracy line marks 20% uniform guessing. Mean is blank where earlier evidence did not export it.</p><div class="figure"><a href="accuracy_speed_cost.svg"><img src="accuracy_speed_cost.png" alt="54 routes, with 20 local GPU models in purple and LLM references in pale yellow"></a></div>'+summary_html(s)+prior.tables.prior.prior.legend_html()+'</section>'
    body+='<section id="local-results"><h2>Local GPU results and profiles</h2><p class="local-note">The RTX 2060 with 6 GB VRAM was chosen deliberately as an older, more accessible setup. Ollaya 0.17.0; server-reported CUDA execution; sequential LAN calls. Loading and warm-ups excluded. Precision varies by model. Hardware identity was supplied by the user; CPU, system RAM and driver version were not captured. No newer-GPU speed or local operating cost has been measured.</p><div class="figure"><a href="local_models.svg"><img src="local_models.png" alt="All 20 completed local models: accuracy and median/p95 latency on RTX 2060"></a></div>'+local_profiles(s)+'</section>'
    body+='<section id="new-additions"><h2>What the expanded comparison shows</h2>'+''.join('<h3>'+escape(title)+'</h3><p>'+escape(text)+'</p>' for title,text in findings(s))+'</section>'
    body+='<section id="llm-references"><h2>Selected no-reasoning LLM references</h2><p>The four existing LLM references retain their settings and measurements. Sol uses explicit reasoning off; Sonnet and Opus use separately labelled constrained JSON choice. Opus refusals and missing telemetry remain in the record. Qwen uses the requested none setting with its existing telemetry qualification. Their full findings remain in the <a href="../opus5_reference_2026-10-23/report.html">October 23 report</a>.</p></section>'
    clarity=readable.clarity_section(s,guide).replace('All 20 models','All 54 routes').replace('all 20 models','all 54 routes')
    body+=mark_names(clarity,s)
    body+='<section id="quality"><h2>Delivered decisions and failures</h2><p>All 1,342 first attempts remain in every ranked score. Twenty local responses were unsuccessful: six truncations and 14 HTTP failures. The two October 27 hosted additions delivered all 2,684 decisions. Earlier failures remain unchanged, including three input-size rejections each for Perplexity and D3, and seven for Jebadiah 9B. The frozen questions were not shortened or retried. There were no scored retries.</p><div class="scroll">'+prior.tables.markdown.markdown(quality(s),extensions=['tables'])+'</div></section>'
    body+='<section id="screened"><h2>Partial and blocked routes</h2><p>Coba and NLI stopped at 20 cases after input truncation. Julia’s serving batch limit caused HTTP failures. These three remain outside the 54-route full-bank ranking. KnowLine completed after model-specific native-label compatibility review; its earlier admission record is retained in <a href="historical_admission_resolutions.json">resolved admission history</a>. <a href="screened_routes.json">Screen details</a>.</p></section>'
    body+='<section id="method"><h2>Method, setup and interpretation</h2>'+''.join('<p>'+escape(p)+'</p>' for p in methods())+'</section>'
    body+='<section id="downloads"><h2>Data and verification</h2><p><a href="statistics.json">54-route aggregate JSON</a> · <a href="model_statistics.csv">Model CSV</a> · <a href="category_scores.csv">Category CSV</a> · <a href="local_timing_evidence.csv">26,840 answer-free timing rows</a> · <a href="hosted_addition_timing_evidence.csv">Celeris answer-free timing/usage</a> · <a href="local_model_metadata.json">Local setup and model metadata</a> · <a href="audit_receipt.json">Audit</a> · <a href="manifest.json">Manifest</a>.</p><p>Unchanged questions: <a href="../consolidated_2026-10-19/questions_1342.csv">CSV</a> · <a href="../consolidated_2026-10-19/questions_1342.jsonl">Native JSONL</a> · <a href="../consolidated_2026-10-19/questions_1342.txt">Readable text</a>. <a href="https://etsabary.github.io/visual-decision-benchmark/report.html">Separate image benchmark</a>; D3 Ultra and Liquid d1.1 image results are reported separately.</p></section></main></body></html>'
    return head+body


def build(refresh_unpublished=False):
    if (DEST/'manifest.json').exists():
        tracked=subprocess.run(['git','ls-files','--error-unmatch',str((DEST/'manifest.json').relative_to(ROOT))],cwd=ROOT,capture_output=True).returncode==0
        assert refresh_unpublished and not tracked, 'Do not overwrite a published release'
        (DEST/'manifest.json').unlink()
    archive.archive();s,guide=load();exports(s,guide);overview(s);overview(s,local_only=True)
    for group in readable.GROUPS:category_plot(s,group)
    page=html(s,guide);write(DEST/'report.html',page)
    narrative='\n\n'.join('## '+title+'\n\n'+text for title,text in findings(s))
    write(DEST/'report.txt',narrative+'\n\n'+'\n\n'.join(methods()))
    rows=[]
    for mid in s['ranked_model_ids']:
        m=s['models'][mid];mean=m.get('mean_response_ms',m.get('mean_ms'))
        setting='🟣 Local' if is_local(s,mid) else '🟡 LLM reference' if mid in s['reference_model_ids'] else 'Hosted decision'
        rows.append([m['label'],setting,f"{m['correct']}/1342",f"{m['accuracy']:.1%}",'—' if mean is None else f'{mean:.0f} ms',f"{m['median_ms']:.0f} ms",f"{m['p95_ms']:.0f} ms",price(mid,m),price(mid,m,False)])
    intro='# System 1 Decision Benchmark\n\n30 hosted decision models, **20 local decision/classifier models** and four no-reasoning LLM references on the same **1,342 text questions across 31 categories**. Updated October 27, 2026.\n\n'
    intro+='**Fastino GLiDE remains highest overall at 86.0%. D3 Flash Artemis 9B leads the local batch at 74.1%, with a 408 ms median on an RTX 2060 with 6 GB VRAM.**\n\n'
    intro+='[Interactive report]('+SITE+') · [Local GPU profiles]('+SITE+'#local-results) · [Named, color-coded categories]('+SITE+'#functions)\n\n'
    intro+='![54 routes: local models in purple](results/releases/'+NAME+'/accuracy_speed_cost.png)\n\n'
    intro+='Purple marks **Local · RTX 2060 · 6 GB**. Blue marks hosted decision models; pale yellow marks LLM references. Accuracy cell colors and speed/cost bands keep their existing meaning. Every ranked row contains 1,342 first attempts. Local loading/warm-up calls are excluded; hosted timing paths and dates remain unchanged. Local hardware/electricity cost is unmeasured, rather than plotted as $0.\n\n'
    intro+='**The local tests deliberately use an older RTX 2060 with 6 GB VRAM, chosen to represent a more accessible hardware setup that readers may already have.** D3 leads all 20 tested local configurations; its measured latency is specific to this setup.\n\n'
    intro+='## Complete comparison\n\n'+table(['Model','Setting','Correct / 1342','Accuracy','Mean','Median','p95','Cost / 1000','Bank cost / basis'],rows)+'\n\n'
    intro+=legend_markdown().replace('1,136-question','1,342-question')+'\n\n'
    end='## Categories, questions and evidence\n\n'+category_markdown(s,guide).replace(']('+NAME+'/','](results/releases/'+NAME+'/')
    end+='\n\nCurrent data: [aggregate JSON](results/releases/'+NAME+'/statistics.json), [model CSV](results/releases/'+NAME+'/model_statistics.csv), [category CSV](results/releases/'+NAME+'/category_scores.csv), [answer-free timing evidence](results/releases/'+NAME+'/local_timing_evidence.csv), [setup metadata](results/releases/'+NAME+'/local_model_metadata.json), [audit](results/releases/'+NAME+'/audit_receipt.json).\n\n'
    end+='Unchanged question bank: [native JSONL](results/releases/consolidated_2026-10-19/questions_1342.jsonl), [CSV](results/releases/consolidated_2026-10-19/questions_1342.csv), [readable text](results/releases/consolidated_2026-10-19/questions_1342.txt).\n\n'
    end+='Implementation: [scripts/](scripts/README.md). Current check: `python3 scripts/validate_native_updates_2026_10_27.py`. Historical checks include `python3 scripts/validate_opus5_release.py` and `python3 scripts/validate_october21_release.py`. All earlier releases remain unchanged.\n'
    write(ROOT/'README.md',intro+narrative+'\n\n'+end)
    write(repo_file('FUNCTIONS.md'),'# All 31 categories: 54 full-bank routes\n\n[Color-coded, named tables]('+SITE+'#functions). Purple model-name badges identify local RTX 2060 runs; cell colors always encode accuracy.\n\n'+category_markdown(s,guide,True).replace(']('+NAME+'/','](../results/releases/'+NAME+'/'))
    write(repo_file('OUTPUT_COMPLIANCE.md'),'# Delivered decisions and failures\n\n54 routes retain the 1,342-question first-attempt denominator. The local batch contains 26,820 usable decisions and 20 unsuccessful responses; no scored retries. Partial or blocked routes are documented separately and not ranked.\n\n'+quality(s))
    local_doc='# Local GPU runs: setup and model profiles\n\n20 complete runs on the unchanged 1,342-question bank, measured October 25, 2026. [Interactive local results]('+SITE+'#local-results).\n\n'
    local_doc+='**🟣 Local · NVIDIA RTX 2060 · 6 GB VRAM · Ollaya 0.17.0 · CUDA.** Hardware identity was supplied by the user; every completed route reported cuda:0. One request/model at a time over the LAN. Loading and synthetic warm-ups are excluded; the earlier CPU screen is separate. Precision varies by route. CPU, system RAM and driver version were not captured.\n\n'
    local_doc+='The RTX 2060 with 6 GB VRAM was chosen deliberately as an older, more accessible hardware setup. The purpose was to measure what readers can run on equipment they may already have. D3 Flash Artemis 9B is the leader among all 20 tested local configurations at 74.1%, with a 408 ms median.\n\n'
    local_doc+='Local API access was unmetered. Electricity and hardware costs were not measured. No latency on newer hardware is inferred. [Captured metadata](../results/releases/'+NAME+'/local_model_metadata.json) records source pins where available and the server-reported precision and digest. These are serving identities, not independent weight attestations.\n\n'
    local_doc+='Purple bars and model-name badges identify these local configurations. Accuracy heatmap cells retain the same 0–100% blue scale, and speed/cost colors retain their existing thresholds.\n\n'
    for mid in s['local_model_ids']:
        m=s['models'][mid]
        local_doc+='## '+m['label']+'\n\n'+f"{m['correct']}/1342 ({m['accuracy']:.1%}); mean / median / p95 {m['mean_response_ms']:.0f} / {m['median_ms']:.0f} / {m['p95_ms']:.0f} ms. Reported precision: {m['precision']}.\n\n"
        for title,key in [('Higher category scores','highest_scoring_categories'),('Lower category scores','lowest_scoring_categories')]:
            local_doc+=title+': '+ '; '.join(f"{readable.LABELS[c['family_id']]} {c['correct']}/{c['n']}" for c in m[key][:3])+'.\n\n'
    local_doc+='## Partial and blocked routes\n\nCoba 1B and the NLI representative stopped after 20 cases because one response each truncated the input. Julia had 19 HTTP failures in 20 attempts due to its physical batch limit. KnowLine’s earlier native one-label compatibility block was resolved: its complete run is ranked above, with the original admission preserved in [resolution history](../results/releases/native_additions_2026-10-25/historical_admission_resolutions.json). The three remaining partial routes are documented in [screen details](../results/releases/'+NAME+'/screened_routes.json) and are not ranked as complete runs.\n\n'
    local_doc+='All profiles use observed category accuracy; their higher/lower lists select categories with at least 20 questions. The complete [named category matrix](../results/releases/'+NAME+'/category_scores.csv) also includes the six eight-question domains.\n'
    write(ROOT/'documents/LOCAL_GPU_RUNS.md',local_doc)
    for path in DEST.glob('*.svg'):write(path,'\n'.join(line.rstrip() for line in path.read_text().splitlines()))
    write(DEST/'manifest.json',dict(version='native-updates-20261027-v1', models=54, local_models=20,
        hosted_decision_models=30,llm_references=4,questions_each=1342,first_attempts=72468,
        bank_sha256=s['question_bank_sha256'],prior_statistics_sha256=digest(PREVIOUS/'statistics.json'),
        artifacts={p.name:digest(p) for p in sorted(DEST.iterdir()) if p.is_file() and p.name!='manifest.json'}))
    pages=ROOT/'docs'/NAME;pages.mkdir(parents=True,exist_ok=True)
    for path in DEST.iterdir():
        if path.is_file():shutil.copyfile(path,pages/path.name)
    write(ROOT/'docs/report.html',prior.tables.prior.rebase(page,NAME))
    for name,anchor in [('index.html',''),('functions.html','#functions'),('output_compliance.html','#quality')]:
        write(ROOT/'docs'/name,'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="benchmark-cohort" content="native-updates-october27-1342"><meta http-equiv="refresh" content="0;url=report.html'+anchor+'"><title>System 1 Decision Benchmark</title></head><body><a href="report.html'+anchor+'">Current 54-route comparison</a></body></html>')
    write(ROOT/'docs/sitemap.xml','<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url><loc>'+SITE+'</loc><lastmod>2026-10-27</lastmod></url></urlset>')
    print('Built 54 full-bank routes, including 20 local configurations; no inference.')


def bind_layout():
    prior.bind_layout()
    path=ROOT/'scripts/layout_manifest.json'
    value=json.loads(path.read_text())
    value['current_files']['docs/sitemap.xml']=digest(ROOT/'docs/sitemap.xml')
    write(path,value)


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--capture',action='store_true');parser.add_argument('--refresh-unpublished',action='store_true')
    args=parser.parse_args()
    if args.capture:capture()
    build(args.refresh_unpublished)
    bind_layout()
