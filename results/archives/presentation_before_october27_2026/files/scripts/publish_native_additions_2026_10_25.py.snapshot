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

import native_additions_publication_history as archive
import build_readable_report as readable
from build_october18_report import PALETTES, legend_markdown
import publish_opus5_reference as prior
from publish_consolidated_report import table
from repo_layout import repo_file

ROOT = Path(__file__).resolve().parents[1]
NAME = 'native_additions_2026-10-25'
DEST = ROOT / 'results/releases' / NAME
SITE = 'https://etsabary.github.io/system-1-decision-benchmark/report.html'
PREVIOUS = ROOT / 'results/releases/local_additions_2026-10-25'
PURPLE, HOSTED, YELLOW = '#7c3aed', '#16728c', (.95, .83, .42, .60)



def digest(path):
    return sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(value.rstrip() + '\n' if isinstance(value, str) else json.dumps(value, indent=2) + '\n')


def mid(name):
    return 'local_' + name.replace(':', '_').replace('-', '_').replace('.', '_')


def capture():
    from native_additions_evidence import capture as reconcile
    reconcile()


def load():
    old=json.loads((PREVIOUS/'statistics.json').read_text())
    new=json.loads((DEST/'new_models.json').read_text())
    local=json.loads((DEST/'local_models.json').read_text())
    assert len(new)==3 and len(local)==20
    s=deepcopy(old);s['models'].update(new)
    assert set(new).isdisjoint(old['models'])
    assert all(s['models'][mid]==value for mid,value in old['models'].items())
    s['local_model_ids']=sorted(local,key=lambda m:(-local[m]['correct'],m))
    s['hosted_model_ids']=[*old['hosted_model_ids'],'celeris11_decision']
    for mid in new:s['model_kinds'][mid]='Decision / classifier'
    s['ranked_model_ids']=sorted(s['models'],key=lambda m:(-s['models'][m]['correct'],m))
    s['decision_model_ids']=[m for m in s['ranked_model_ids'] if m not in s['reference_model_ids']]
    s.update(status='COMPLETE_52_ROUTES_20_LOCAL_1342',model_count=52,decision_model_count=48,
        hosted_decision_model_count=28,local_model_count=20,primary_cases=69784,all_tested_primary_cases=69784,
        added_model_ids=sorted(new),updated_date_toronto='2026-10-25',
        prior_statistics_sha256=digest(PREVIOUS/'statistics.json'),
        total_http_attempts=sum(m['attempts'] for m in s['models'].values()),
        total_recoveries=sum(m['recoveries'] for m in s['models'].values()))
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
        title='20 local models · RTX 2060 6 GB · 1,342 questions' if local_only else '52 routes · 28 hosted decision models · 20 local models · 4 LLM references'
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
      ('Celeris joins at 76.1%, while Fastino remains highest overall',
       'Celeris 1.1 Decision answered 1,021/1,342 correctly (76.1%), with 155 / 138 / 170 ms mean / median / p95. That is 26 more correct answers than local D3 Flash Artemis at 995 (74.1%), and 129 fewer than hosted Fastino GLiDE at 1,154 (86.0%). GPT-6 Sol without reasoning retains 1,143 (85.2%) and Mammoth-1 1,139 (84.9%). All earlier 49 model records retain their exact scores, durations, costs and dates. The 52-route comparison is an observed result on this developing bank, not a universal model ranking.'),
      ('KnowLine is close to Perplexity, with a longer median than D3',
       'KnowLine 4B Gen5.5 scored 966/1,342 (72.0%), five fewer than local Perplexity Flash mixed4 at 971 (72.4%) and 29 fewer than D3 at 995. Its mean / median / p95 was 848 / 812 / 1,281 ms, compared with Perplexity 875 / 798 / 1,526 ms and D3 441 / 408 / 701 ms. D3 remains the highest-scoring of 20 completed local configurations. KnowLine scored 38/40 on comparisons, 40/43 on lookup/filtering and 48/52 on rule counterexamples; sequential procedures were 8/48, exact truth counting 30/71 and truth-teller consistency 35/74.'),
      ('The Nemotron configuration trails the earlier Qwen-based H2O',
       'H2O Lightning Nemotron 4B scored 823/1,342 (61.3%), with 596 / 574 / 810 ms mean / median / p95. The earlier H2O-Lightning 4B route scored 892 (66.5%) with a 259 ms median: 69 more correct answers and a shorter median on the same user-reported GPU. Fovea scored 841 (62.7%) with a 558 ms median. Nemotron scored 40/43 on lookup/filtering and directed paths, 39/43 on current authoritative records and 46/51 on explicit preferences; sequential procedures were 12/48 and reference binding 16/50. Weights, precision and serving implementations differ, so the comparison does not isolate the backbone.'),
      ('Celeris has strong lookup and path scores, with weaker state updates',
       'Celeris scored 41/43 on directed paths, 40/43 on lookup/filtering, 39/42 on temporal intervals and 46/50 on fault diagnosis. Sequential procedures scored 14/48, object swaps 24/52, truth-teller consistency 36/74 and exact truth counting 35/71. A high overall score can conceal weaknesses on repeated state updates. Every model retains the complete named category matrix. Six categories have eight questions each, so one answer changes their score by 12.5 percentage points.'),
      ('Celeris cost is a tariff estimate, with all latency spikes retained',
       'The 481,334 reported input tokens at the captured USD 0.04/million tariff give an estimated $0.01925336 for 1,342 questions, or about $0.01434677 per 1,000. This is usage times tariff, not monetary receipts. Two admission probes cost an estimated $0.00001048 separately. Fresh HTTPS calls were serial, at least 0.25 seconds apart at dispatch; idle pacing is excluded from response durations. Four scored calls exceeded two seconds, with a maximum of 3,195 ms; all remain in the timing distribution. The cumulative median remained below the existing two-second gate.'),
      ('The two new local models report one native label token',
       'Nemotron and KnowLine both returned typed choices and five-choice probability distributions without generated explanations. Their runtime reports one output token, retained as observed native label telemetry. Earlier 18 local configurations retain their recorded zero-token evidence. Nemotron also reports native probabilities, one fast pass and matching input/processed-input counts. KnowLine reports no truncation but no separate processed-input count. Its earlier admission block is preserved as history and resolved by the completed model-specific compatibility audit. Reported counters do not attest to all internal computation.'),
      ('Matched questions, qualified precision and route-specific timing',
       'The two additions ran on the home LAN using Ollaya 0.17.0, cuda:0 and a user-reported RTX 2060 with 6 GB VRAM, deliberately chosen as an older, more accessible hardware setup. Nemotron used NF4 / FP16 compute / FP32 head; KnowLine used NF4 / FP16 compute / FP32 readout. KnowLine Gen5.5 upstream documentation describes Gen5 weights with read-twice input serving. Loading and four synthetic warm-ups per model are excluded. Start/end serving digests were stable; immutable upstream weight revisions were not reported. Hardware, software, quantization, dates and network paths limit causal speed comparisons.'),
      ('Every new first attempt was usable; prior failures remain counted',
       'All 4,026 new text decisions were usable, with no scored retries, shortened inputs or accuracy-only stop. Across 20 local configurations there are 26,820 usable decisions and 20 unsuccessful first attempts. The existing six truncations and 14 HTTP failures remain in their original 1,342-question denominators. Coba, NLI and Julia remain separate partial or blocked routes outside the full-bank ranking. No completed run was repeated for publication.'),
      ('Colors and cost boundaries retain their meaning',
       'Purple identifies local RTX 2060 runs, blue hosted decision models and pale yellow the four no-reasoning LLM references. Cell colors encode accuracy; the original green-to-red speed/cost bands are fixed. Local hardware, electricity and depreciation were not measured, so no zero-dollar operating cost is invented. Celeris and Fastino estimates are marked with a tilde. API identities and serving digests are provenance, not independent weight attestations.')]


def methods():
    return [
      '52 full-bank routes: 28 hosted decision models, 20 local decision/classifier configurations and four no-reasoning LLM references. Same 1,342 questions across 31 categories: 69,784 first attempts. All earlier 49 model records and the frozen bank/options remain unchanged.',
      'The two new local routes were measured October 25, 2026 (America/Toronto), sequentially on a user-reported NVIDIA RTX 2060 with 6 GB VRAM using Ollaya 0.17.0 and server-reported cuda:0. This older, more accessible hardware was chosen deliberately. CPU, system RAM, driver version and independent hardware identity were not captured. One model/request ran at a time over LAN HTTP. Four synthetic warm-ups per model and cold loading are separate; all 1,342 scored durations per route remain pooled. No proxy measurements are mixed into the full-bank results.',
      'Celeris used the direct native SystemOne endpoint with exact requested and returned model celeris-1.1-decision and x_celeris.explain=false. Catalogs captured before and after execution were identical. One fresh HTTPS request ran at a time, with at least 0.25 seconds between dispatch starts. Idle pacing is excluded; full request-to-response duration is included. All 1,342 responses reported zero output tokens and no explanations. Per-item processed input, truncation and hidden internal computation were not independently attested.',
      'The existing screen stops after at least 20 cases if cumulative median exceeds 2,000 ms, or pauses at 5% unusable output. All three new routes passed and completed; no accuracy-only stopping or scored retries. All first-attempt failures from earlier releases remain counted. Three partial/blocked local routes remain outside the complete ranking; KnowLine’s historical admission issue is now resolved and separately preserved.',
      'Nemotron and KnowLine report one output label token in native typed responses, with no generated explanations. Nemotron adds native probability/one-fast-pass and processed-input evidence; KnowLine does not report those same counters. The earlier zero-token local telemetry is unchanged. Sol, Sonnet, Opus and Qwen retain their exact reasoning settings, output contracts and verification limits. The task measures immediate five-choice decisions without tools or agentic iteration, not reasoning-enabled LLM performance.',
      'Celeris primary cost is reported input usage multiplied by the captured USD 0.04/million tariff, not an API monetary receipt. The two synthetic probes are separate. Local electricity/hardware costs remain unmeasured. Dates, precision, software, provider hardware/load and local/cloud network paths limit latency and architecture comparisons. No newer-GPU timing is inferred.',
      'Public answer-free timing and status evidence reproduces coverage, mean, median and p95. The three new scores and 31 category totals were reconciled offline against the existing private revision-bound key, with payload, source, identity and seal checks. Public aggregates cannot independently reproduce private-key scoring. No key, model-choice ledger, per-item correctness, credential or LAN address is exported.',
      'This is a developing bank with uneven category sizes and dependent variants. Six categories contain eight questions each. Existing audit qualifications and the separate 1,305-case author-development diagnostic retain their scope; no claim is made that every original item received independent external verification.']


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
    value=readable.markdown_groups(s,guide,details).replace('All 20 models','All 52 routes').replace('all 20 models','all 52 routes').replace(readable.NAME,NAME)
    import re
    return re.sub(r'https://etsabary.github.io/jev-1.14-comparison-benchmark/[^)# ]+/report.html',SITE,value)


def html(s,guide):
    import re
    old=(prior.DEST/'report.html').read_text();head=old[:old.index('<body>')+6]
    head=re.sub(r'<title>.*?</title>','<title>System 1 decisions: 52 routes, 20 local GPU models</title>',head)
    head=re.sub(r'content="opus5-october23-1342"', 'content="native-additions-october25-1342"',head)
    head=head.replace('</head>','<meta name="description" content="Compare 52 text decision routes on 1,342 questions: 28 hosted decision models, 20 local RTX 2060 configurations and four reasoning-off LLMs. Accuracy, latency, cost and 31 category profiles."><link rel="canonical" href="'+SITE+'"><style>'+CSS+'</style></head>')
    body='<main><h1>System 1 Decision Benchmark</h1><p>28 hosted decision models, 20 local decision/classifier models and four no-reasoning LLM references. Same 1,342 questions, 31 categories. Updated October 25, 2026.</p>'
    body+='<nav><a href="#overview">All 52 routes</a><a href="#local-results">Local GPU results</a><a href="#new-additions">Findings</a><a href="#functions">Named categories</a><a href="#method">Method and setup</a></nav>'
    body+='<div class="cards"><div class="card"><div class="label">Highest overall</div><div class="big">86.0%</div><div class="small">Fastino GLiDE · 1154/1342</div></div><div class="card"><div class="label">Highest local score</div><div class="big">74.1%</div><div class="small">D3 Flash Artemis 9B · 408 ms median</div></div><div class="card"><div class="label">Deliberate older-GPU setup</div><div class="big">6 GB</div><div class="small">RTX 2060 · CUDA · Ollaya 0.17.0</div></div><div class="card"><div class="label">Full matched coverage</div><div class="big">52 routes</div><div class="small">69,784 first attempts · 31 categories</div></div></div>'
    body+='<div class="route-legend"><span><i class="swatch" style="background:#16728c"></i>Hosted decision models</span><span><i class="swatch" style="background:#7c3aed"></i>Local · RTX 2060 · 6 GB</span><span><i class="swatch" style="background:#f4df9a"></i>LLM references, reasoning off</span></div>'
    body+='<section id="overview"><h2>All 52 routes: accuracy, speed and cost</h2><p>Every row covers 1,342 first attempts. Purple identifies local runs; it does not change the green-to-red speed/cost bands or the accuracy heatmap. The dashed accuracy line marks 20% uniform guessing. Mean is blank where earlier evidence did not export it.</p><div class="figure"><a href="accuracy_speed_cost.svg"><img src="accuracy_speed_cost.png" alt="52 routes, with 20 local GPU models in purple and LLM references in pale yellow"></a></div>'+summary_html(s)+prior.tables.prior.prior.legend_html()+'</section>'
    body+='<section id="local-results"><h2>Local GPU results and profiles</h2><p class="local-note">The RTX 2060 with 6 GB VRAM was chosen deliberately as an older, more accessible setup. Ollaya 0.17.0; server-reported CUDA execution; sequential LAN calls. Loading and warm-ups excluded. Precision varies by model. Hardware identity was supplied by the user; CPU, system RAM and driver version were not captured. No newer-GPU speed or local operating cost has been measured.</p><div class="figure"><a href="local_models.svg"><img src="local_models.png" alt="All 20 completed local models: accuracy and median/p95 latency on RTX 2060"></a></div>'+local_profiles(s)+'</section>'
    body+='<section id="new-additions"><h2>What the expanded comparison shows</h2>'+''.join('<h3>'+escape(title)+'</h3><p>'+escape(text)+'</p>' for title,text in findings(s))+'</section>'
    body+='<section id="llm-references"><h2>Selected no-reasoning LLM references</h2><p>The four existing LLM references retain their settings and measurements. Sol uses explicit reasoning off; Sonnet and Opus use separately labelled constrained JSON choice. Opus refusals and missing telemetry remain in the record. Qwen uses the requested none setting with its existing telemetry qualification. Their full findings remain in the <a href="../opus5_reference_2026-10-23/report.html">October 23 report</a>.</p></section>'
    clarity=readable.clarity_section(s,guide).replace('All 20 models','All 52 routes').replace('all 20 models','all 52 routes')
    body+=mark_names(clarity,s)
    body+='<section id="quality"><h2>Delivered decisions and failures</h2><p>All 1,342 first attempts remain in every ranked score. Twenty local responses were unsuccessful: six truncations and 14 HTTP failures. The three new configurations delivered all 4,026 decisions. Earlier failures remain unchanged, including three input-size rejections each for Perplexity and D3, and seven for Jebadiah 9B. The frozen questions were not shortened or retried. There were no scored retries.</p><div class="scroll">'+prior.tables.markdown.markdown(quality(s),extensions=['tables'])+'</div></section>'
    body+='<section id="screened"><h2>Partial and blocked routes</h2><p>Coba and NLI stopped at 20 cases after input truncation. Julia’s serving batch limit caused HTTP failures. These three remain outside the 52-route full-bank ranking. KnowLine completed after model-specific native-label compatibility review; its earlier admission record is retained in <a href="historical_admission_resolutions.json">resolved admission history</a>. <a href="screened_routes.json">Screen details</a>.</p></section>'
    body+='<section id="method"><h2>Method, setup and interpretation</h2>'+''.join('<p>'+escape(p)+'</p>' for p in methods())+'</section>'
    body+='<section id="downloads"><h2>Data and verification</h2><p><a href="statistics.json">52-route aggregate JSON</a> · <a href="model_statistics.csv">Model CSV</a> · <a href="category_scores.csv">Category CSV</a> · <a href="local_timing_evidence.csv">26,840 answer-free timing rows</a> · <a href="hosted_addition_timing_evidence.csv">Celeris answer-free timing/usage</a> · <a href="local_model_metadata.json">Local setup and model metadata</a> · <a href="audit_receipt.json">Audit</a> · <a href="manifest.json">Manifest</a>.</p><p>Unchanged questions: <a href="../consolidated_2026-10-19/questions_1342.csv">CSV</a> · <a href="../consolidated_2026-10-19/questions_1342.jsonl">Native JSONL</a> · <a href="../consolidated_2026-10-19/questions_1342.txt">Readable text</a>. <a href="https://etsabary.github.io/visual-decision-benchmark/report.html">Separate image benchmark</a>; no image scores changed.</p></section></main></body></html>'
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
    intro='# System 1 Decision Benchmark\n\n28 hosted decision models, **20 local decision/classifier models** and four no-reasoning LLM references on the same **1,342 text questions across 31 categories**. Updated October 25, 2026.\n\n'
    intro+='**Fastino GLiDE remains highest overall at 86.0%. D3 Flash Artemis 9B leads the local batch at 74.1%, with a 408 ms median on an RTX 2060 with 6 GB VRAM.**\n\n'
    intro+='[Interactive report]('+SITE+') · [Local GPU profiles]('+SITE+'#local-results) · [Named, color-coded categories]('+SITE+'#functions)\n\n'
    intro+='![52 routes: local models in purple](results/releases/'+NAME+'/accuracy_speed_cost.png)\n\n'
    intro+='Purple marks **Local · RTX 2060 · 6 GB**. Blue marks hosted decision models; pale yellow marks LLM references. Accuracy cell colors and speed/cost bands keep their existing meaning. Every ranked row contains 1,342 first attempts. Local loading/warm-up calls are excluded; hosted timing paths and dates remain unchanged. Local hardware/electricity cost is unmeasured, rather than plotted as $0.\n\n'
    intro+='**The local tests deliberately use an older RTX 2060 with 6 GB VRAM, chosen to represent a more accessible hardware setup that readers may already have.** D3 leads all 20 tested local configurations; its measured latency is specific to this setup.\n\n'
    intro+='## Complete comparison\n\n'+table(['Model','Setting','Correct / 1342','Accuracy','Mean','Median','p95','Cost / 1000','Bank cost / basis'],rows)+'\n\n'
    intro+=legend_markdown().replace('1,136-question','1,342-question')+'\n\n'
    end='## Categories, questions and evidence\n\n'+category_markdown(s,guide).replace(']('+NAME+'/','](results/releases/'+NAME+'/')
    end+='\n\nCurrent data: [aggregate JSON](results/releases/'+NAME+'/statistics.json), [model CSV](results/releases/'+NAME+'/model_statistics.csv), [category CSV](results/releases/'+NAME+'/category_scores.csv), [answer-free timing evidence](results/releases/'+NAME+'/local_timing_evidence.csv), [setup metadata](results/releases/'+NAME+'/local_model_metadata.json), [audit](results/releases/'+NAME+'/audit_receipt.json).\n\n'
    end+='Unchanged question bank: [native JSONL](results/releases/consolidated_2026-10-19/questions_1342.jsonl), [CSV](results/releases/consolidated_2026-10-19/questions_1342.csv), [readable text](results/releases/consolidated_2026-10-19/questions_1342.txt).\n\n'
    end+='Implementation: [scripts/](scripts/README.md). Current check: `python3 scripts/validate_native_additions_2026_10_25.py`. Historical checks include `python3 scripts/validate_opus5_release.py` and `python3 scripts/validate_october21_release.py`. All earlier releases remain unchanged.\n'
    write(ROOT/'README.md',intro+narrative+'\n\n'+end)
    write(repo_file('FUNCTIONS.md'),'# All 31 categories: 52 full-bank routes\n\n[Color-coded, named tables]('+SITE+'#functions). Purple model-name badges identify local RTX 2060 runs; cell colors always encode accuracy.\n\n'+category_markdown(s,guide,True).replace(']('+NAME+'/','](../results/releases/'+NAME+'/'))
    write(repo_file('OUTPUT_COMPLIANCE.md'),'# Delivered decisions and failures\n\n52 routes retain the 1,342-question first-attempt denominator. The local batch contains 26,820 usable decisions and 20 unsuccessful responses; no scored retries. Partial or blocked routes are documented separately and not ranked.\n\n'+quality(s))
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
    write(DEST/'manifest.json',dict(version='native-additions-20261025-v1', models=52, local_models=20,
        hosted_decision_models=28,llm_references=4,questions_each=1342,first_attempts=69784,
        bank_sha256=s['question_bank_sha256'],prior_statistics_sha256=digest(PREVIOUS/'statistics.json'),
        artifacts={p.name:digest(p) for p in sorted(DEST.iterdir()) if p.is_file() and p.name!='manifest.json'}))
    pages=ROOT/'docs'/NAME;pages.mkdir(parents=True,exist_ok=True)
    for path in DEST.iterdir():
        if path.is_file():shutil.copyfile(path,pages/path.name)
    write(ROOT/'docs/report.html',prior.tables.prior.rebase(page,NAME))
    for name,anchor in [('index.html',''),('functions.html','#functions'),('output_compliance.html','#quality')]:
        write(ROOT/'docs'/name,'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="benchmark-cohort" content="native-additions-october25-1342"><meta http-equiv="refresh" content="0;url=report.html'+anchor+'"><title>System 1 Decision Benchmark</title></head><body><a href="report.html'+anchor+'">Current 52-route comparison</a></body></html>')
    write(ROOT/'docs/sitemap.xml','<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url><loc>'+SITE+'</loc><lastmod>2026-10-25</lastmod></url></urlset>')
    print('Built 52 full-bank routes, including 20 local configurations; no inference.')


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
