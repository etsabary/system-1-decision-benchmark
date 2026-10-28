"""Offline 29-route presentation; prior measurements and release seals retained."""
from repo_layout import logical_relative, repo_file
from repo_layout import frozen_file
import argparse
from copy import deepcopy
import csv
from hashlib import sha256
from html import escape
import io
import json
from pathlib import Path
import re
import shutil
import markdown

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import numpy as np

import analyze_decision_additions_2026_10_21 as analysis
import archive_october21_presentation as archive
import build_readable_report as readable
import publish_direct_decisions as prior
from build_october18_report import PALETTES,format_speed,legend_markdown
from publish_consolidated_report import table

ROOT = Path(__file__).resolve().parents[1]
NAME = 'native_additions_2026-10-21'
DEST = repo_file(NAME, root=ROOT)
PRIVATE = analysis.OUT/'complete'
NEW = tuple(analysis.RUNS)
SITE = 'https://etsabary.github.io/system-1-decision-benchmark/report.html'
ACTIVE = ('README.md','FUNCTIONS.md','OUTPUT_COMPLIANCE.md','IMAGE_CAPABILITIES.md',
          'docs/report.html','docs/index.html','docs/functions.html','docs/output_compliance.html',
          'publish_october21_additions.py','validate_october21_release.py','test_october21_publication.py',
          'archive_october21_presentation.py','publish_direct_decisions.py','validate_direct_release.py',
          'decision_additions_2026_10_21.py','baseten_decisions_2026_10_21.py',
          'analyze_decision_additions_2026_10_21.py','test_decision_additions_2026_10_21.py',
          'test_baseten_decisions_2026_10_21.py','test_analyze_decision_additions_2026_10_21.py',
          '.github/workflows/october18-validate.yml')


def digest(path):
    return sha256(Path(path).read_bytes()).hexdigest()


def write(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(value.rstrip()+'\n',encoding='utf-8')


def load():
    sealed = json.loads((PRIVATE/'checksums.json').read_text())
    for name,h in sealed.items():
        assert digest(PRIVATE/name)==h
    report = json.loads((PRIVATE/'summary.json').read_text())
    assert analysis.analyze(False)==report,'Private scoring/evidence reconciliation changed'
    s = analysis.combined(report)
    assert s==json.loads((PRIVATE/'statistics.json').read_text())
    guide = json.loads((prior.DEST/'category_guide.json').read_text())
    return s,guide,report


def price(mid,m,normalized=True):
    if mid in ('mammoth1','elephant1'):
        return 'Promotional free access*'
    return prior.price(mid,m,normalized,styled=False)


def findings(s):
    m = s['models']
    cell = lambda mid,fid: f"{m[mid]['families'][fid]['correct']}/{m[mid]['families'][fid]['n']}"
    return [
        ('Mammoth-1 leads the decision-model sample',
         'Mammoth-1 answered 1139/1342 correctly (84.9%), twelve more than Span-02 and Drex Max, which tied at 1127/1342 (84.0%). GPT-6 Sol without reasoning answered 1143 correctly (85.2%), four more than Mammoth. The four-answer gap does not establish a reliable general ordering. Mammoth’s median response was 240 ms and Sol’s was 1023 ms: about 4.3 times longer for Sol on these measured routes. Sonnet’s separately constrained, no-thinking reference remains 1070/1342 (79.7%).'),
        ('The leader still has specific weak operations',
         'Mammoth scored 64/67 on one-to-one assignments—matching each person or object to exactly one available slot—and 57/58 on exceptions and priority rules. Tracking what others know gave 47/50. These tasks can ask where someone will search after an object moved while they were absent. Counting exactly true claims gave 44/71, truth-tellers and liars 48/74, and ordered procedures only 18/48. Procedures require applying each edit to the current state, not merely recognizing a plausible final answer. Span scored 33/48 there, despite its lower overall total. Mammoth also scored 38/52 on tracking swaps, versus Span’s 28/52.'),
        ('Drex Max ties Span overall, with different strengths',
         'Drex Max scored 65/67 on one-to-one assignments and 45/46 on if-then rules, versus Span’s 63/67 and 32/46. On procedures, Drex scored 18/48 and Span 33/48; on worst-case choices without supplied probabilities, Drex scored 5/8 and Span 8/8. Equal overall totals do not mean the same decisions will be correct. Drex’s median/p95 was 286/445 ms, versus Span’s previously measured 206/2157 ms: Span had the shorter median, Drex the shorter tail. Drex’s complete API-reported cost was $0.02842302, normalized to $0.02118 per 1000 questions. Span’s recorded $0.00474628 total was about six times lower.'),
        ('Elephant-1 is fast, but not a uniform improvement over Jev',
         'Elephant-1 scored 1004/1342 (74.8%), below Jev 1.14’s 1030/1342 (76.8%). Its 139 ms median was shorter than Jev’s 179 ms. Elephant still scored 60/67 on one-to-one assignments and 46/50 on knowledge tracking, versus Jev’s 57/67 and 44/50. Comparing time intervals gave Elephant 25/42 and Jev 40/42; checking required conditions gave 38/52 and 48/52. A newer release is not automatically stronger across this bank.'),
        ('The added questions expose more separation',
         'On the original 1136 questions, Mammoth scored 1019/1136 (89.7%), Drex Max 1004/1136 (88.4%) and Elephant 902/1136 (79.4%). On the 206 additions their scores were 120/206 (58.3%), 123/206 (59.7%) and 102/206 (49.5%). This is a descriptive split, not a second leaderboard or a change in weighting. Across the six new categories, Mammoth scored 30/48, Drex 29/48 and Elephant 22/48. Each new category contains only eight questions; one answer moves its score by 12.5 percentage points.'),
        ('Jev’s position is a measured result, not an explanation of its roadmap',
         'Mammoth answered 109 more questions correctly than Jev 1.14; Drex Max answered 97 more. Jev still answered all 46 if-then questions correctly, versus 45 each for Mammoth and Drex. This bank measures supplied-fact, five-choice decisions without tools or agentic iteration; it does not test broad knowledge, multilingual coverage or product integration. It cannot establish why a developer has or has not improved a model.'),
        ('Free launch access is separate from a production price',
         'Mammoth and Elephant used Baseten’s direct API at the captured promotional zero tariff. Their responses did not contain monetary receipts, so the report does not invent an API-reported $0 price or plot one on the logarithmic cost axis. Baseten advertises a one-week launch promotion; availability and later prices may change. Their 20-question OpenRouter controls agreed with the direct route on all 20 choices for each model. Those controls are not pooled into the full-bank scores or latency measurements.'),
    ]


def method(s):
    return [
        f"The comparison contains 26 specialized decision models and three no-reasoning LLM reference routes: 29 × 1342 = {29*1342:,} first attempts. All earlier26 model records are preserved exactly. New full-bank runs: October21,2026, America/Toronto; Mammoth and Elephant direct through Baseten, Drex Max through OpenRouter’s pinned DeepInfra endpoint.",
        'Same frozen 1342-question bank, seed2026101906, original five choices and native inputs. Every first attempt remains in the accuracy and latency denominator, including failures. One recovery is allowed only for transport failures or HTTP408/429/5xx; no answer-dependent retries. All4026 new first attempts returned usable decisions, with zero recoveries and zero probability-format warnings. After at least20 questions, a cumulative median above2000 ms stops a route; none of the three reached that threshold.',
        'Response timing starts before a fresh HTTPS connection and ends after the full response body. Preparation, deliberate pacing, queue waits and recovery delays are outside the response timer. Two requests per model run in barrier waves, with up to three models active. Provider hardware, dates, loads and routes are not controlled away; latency is not batch throughput or an isolated inference-speed measurement.',
        'Baseten’s catalog and returned latest serving aliases identify Mammoth-1 and Elephant-1, not immutable weights. Drex returned nace-ai/drex-max-20261016 from DeepInfra. Baseten’s official technical report describes one-pass option-logit decisions. These native requests ask for neither reasoning nor explanations. Reported native output-token counters are retained; a nonzero counter alone is not evidence of thinking. Undisclosed internal execution cannot be independently verified from an API envelope.',
        'Drex uses reported usage.cost for every attempt. Baseten promotional access is labelled separately from metered receipts. Separate compatibility probes and the two20-case OpenRouter controls are excluded from the4026 ranked first attempts. Missing charges remain unknown, not zero. Existing Nimble price estimates and Qwen prepaid-quota valuations retain their original labels.',
        'This is a developing benchmark with uneven category sizes and dependent variants, not1342 independent observations or a pristine held-out evaluation. The37 permanent author-development exclusions retain their separate1305-case diagnostic. Two audited ambiguous original items were already replaced before these runs. All206 additions retain their existing independent verification and computational evidence; the original bank received a targeted difficult-item audit, not independent external verification of every original question.',
        'Public exports contain unchanged answer-free question inputs, aggregate category scores and sanitized evidence hashes—not answer keys, per-item correctness, private verifier outputs, raw account state or credentials. Public checks verify consistency but cannot reproduce private-key scoring or raw-latency pooling. REAX1 is not included: a hosted API for that exact fine-tune has not been confirmed.',
    ]


def overview(s):
    ids = s['ranked_model_ids']
    models = [s['models'][mid] for mid in ids]
    y = np.arange(len(ids))
    band = lambda v,limits:next((i for i,b in enumerate(limits) if v<=b),3)
    with plt.rc_context({'font.family':'DejaVu Sans','svg.fonttype':'none','svg.hashsalt':'oct21-native-1342'}):
        fig,axes = plt.subplots(1,3,figsize=(16,16.7),sharey=True,gridspec_kw={'width_ratios':[1.2,1.1,1.1]})
        bars = axes[0].barh(y,[100*m['accuracy'] for m in models],color=[(.95,.83,.42,.60) if mid in s['reference_model_ids'] else '#16728c' for mid in ids])
        for bar,mid in zip(bars,ids):
            if mid in s['reference_model_ids']:
                bar.set_edgecolor('#9c761c')
        axes[0].set_yticks(y,[readable.short(m['label']) for m in models],fontsize=11)
        axes[0].set_xlim(0,112)
        axes[0].set_xlabel('Correct first decisions (%)')
        for yy,mid,m in zip(y,ids,models):
            axes[0].text(100*m['accuracy']+1,yy,f"{m['accuracy']:.1%}",va='center',fontsize=10)
            axes[1].plot([m['median_ms'],m['p95_ms']],[yy,yy],color='#8999a5')
            axes[1].scatter(m['median_ms'],yy,color=PALETTES[band(m['median_ms'],(250,500,1000))],edgecolor='#364c60',s=65,zorder=3)
            axes[1].scatter(m['p95_ms'],yy,color='#35424d',marker='d',s=20,zorder=3)
            c = m['cost']
            if c.get('public_free_access'):
                label = 'Promotional free*' if mid in ('mammoth1','elephant1') else 'Free public access*'
                axes[2].text(.03,yy,label,transform=axes[2].get_yaxis_transform(),va='center',fontsize=10,
                             bbox=dict(facecolor='#edf1f5',edgecolor='none',pad=3))
            else:
                axes[2].scatter(c['known_usd_per_1000'],yy,color=PALETTES[band(c['known_usd_per_1000'],(.01,.025,.05))],edgecolor='#364c60',s=65)
                if c['unknown_attempts']:
                    axes[2].text(c['known_usd_per_1000']*1.15,yy,'+ ?',va='center',fontsize=9)
        axes[0].invert_yaxis()
        axes[1].set_xscale('log');axes[2].set_xscale('log')
        axes[1].set_xlabel('Response time (ms, log scale)\nCircle: median · diamond: p95')
        axes[2].set_xlabel('Metered/accounted cost per 1000\nUSD, log scale; + ? = incomplete')
        for ax,title in zip(axes,('Accuracy','Speed','Cost')):
            ax.set_title(title,fontsize=14,pad=18);ax.grid(axis='x',alpha=.2);ax.set_axisbelow(True)
            for spine in ax.spines.values():
                spine.set_visible(False)
        fig.suptitle('26 decision models and 3 high-end LLM references · 1,342 questions',fontsize=17,y=.98)
        fig.legend(handles=[Patch(facecolor='#16728c',label='Decision models'),
            Patch(facecolor=(.95,.83,.42,.60),edgecolor='#9c761c',label='No-reasoning LLM references')],
            loc='upper center',bbox_to_anchor=(.5,.957),ncol=2,frameon=False)
        fig.text(.02,.025,'All first attempts; fixed speed/cost bands. *Free access is not a metered production price. Baseten: launch promotion.\nNew full runs: October 21, 2026; earlier measurements unchanged. Different providers, dates and account limits remain confounds.\nFresh HTTPS through full response; rate/admission waits excluded. Qwen is prepaid-quota valuation, not cash billing.',fontsize=10)
        fig.subplots_adjust(left=.30,right=.98,top=.91,bottom=.12,wspace=.36)
        for suffix in ('png','svg'):
            fig.savefig(DEST/('accuracy_speed_cost.'+suffix),dpi=160,metadata={'Date':None} if suffix=='svg' else {})
        plt.close(fig)


def rows(s):
    return [[m['label'],s['model_kinds'][mid],f"{m['correct']}/1342",f"{m['accuracy']:.1%}",
             format_speed(m['median_ms']),f"{m['p95_ms']:.0f} ms",price(mid,m),price(mid,m,False)]
            for mid in s['ranked_model_ids'] for m in [s['models'][mid]]]


def summary_html(s):
    body = []
    band = lambda v,limits:next((i for i,b in enumerate(limits) if v<=b),3)
    for mid in s['ranked_model_ids']:
        m = s['models'][mid]
        css = 'llm-reference' if mid in s['reference_model_ids'] else 'native-addition' if mid in NEW else ''
        c = m['cost']
        shade = '#edf1f5' if c.get('public_free_access') else PALETTES[band(c['known_usd_per_1000'],(.01,.025,.05))]
        body.append(f'<tr class="{css}" data-summary-model="{mid}"><th scope="row">{escape(m["label"])}</th>'
            f'<td>{s["model_kinds"][mid]}</td><td>{m["correct"]}/1342<br>{m["accuracy"]:.1%}</td>'
            f'<td style="background:{PALETTES[band(m["median_ms"],(250,500,1000))]}">{m["median_ms"]:.0f} ms</td>'
            f'<td style="background:{PALETTES[band(m["p95_ms"],(250,500,1000))]}">{m["p95_ms"]:.0f} ms</td>'
            f'<td style="background:{shade}">{escape(price(mid,m))}</td><td>{escape(price(mid,m,False))}</td></tr>')
    return '<div class="scroll"><table><thead><tr><th>Model</th><th>Type</th><th>Correct / questions</th><th>Median</th><th>p95</th><th>Cost per1000</th><th>Actual1342-question cost</th></tr></thead><tbody>'+''.join(body)+'</tbody></table></div>'


def exports(s,guide):
    write(DEST/'statistics.json',json.dumps(s,indent=2)+'\n')
    write(DEST/'category_guide.json',json.dumps(guide,indent=2)+'\n')
    text = io.StringIO(newline='');writer = csv.writer(text,lineterminator='\n')
    writer.writerow(['category_id','category','questions']+[s['models'][mid]['label'] for mid in s['ranked_model_ids']])
    for fid in readable.LABELS:
        writer.writerow([fid,readable.LABELS[fid],guide[fid]['questions']]+[readable.score(s['models'][mid]['families'][fid]) for mid in s['ranked_model_ids']])
    write(DEST/'category_scores.csv',text.getvalue())
    text = io.StringIO(newline='');writer = csv.writer(text,lineterminator='\n')
    writer.writerow(['model_id','model','type','questions','correct','accuracy','mean_ms_if_measured','median_ms','p95_ms',
        'known_cost_usd','known_cost_per1000_usd','unreported_charge_attempts','free_access','route','test_dates_toronto'])
    for mid in s['ranked_model_ids']:
        m=s['models'][mid];c=m['cost']
        writer.writerow([mid,m['label'],s['model_kinds'][mid],m['n'],m['correct'],m['accuracy'],m.get('mean_response_ms',''),
            m['median_ms'],m['p95_ms'],c['known_usd'],c['known_usd_per_1000'],c['unknown_attempts'],
            c.get('public_free_access',False),m['route'],'; '.join(sorted(m['dates_toronto']))])
    write(DEST/'model_statistics.csv',text.getvalue())
    previous = readable.DEST
    try:
        readable.DEST = DEST
        for group in readable.GROUPS:
            readable.plot(s,group)
    finally:
        readable.DEST = previous


def category_markdown(s,guide,details=False):
    text = readable.markdown_groups(s,guide,details).replace('All20 models','All29 routes').replace('All 20 models','All29 routes').replace('all 20 models','all29 routes')
    text = text.replace(readable.NAME,NAME).replace('https://etsabary.github.io/jev-1.14-comparison-benchmark/'+NAME+'/report.html',SITE)
    return text


def html(s,guide):
    old = (prior.DEST/'report.html').read_text()
    head = old[:old.index('<body>')+6]
    head = re.sub(r'<title>.*?</title>','<title>System1 Decision Benchmark:29 routes,1342 questions</title>',head)
    head = head.replace('october20-direct-additions-1342','october21-additions-1342')
    body = '<main><h1>System1 Decision Benchmark</h1><p>26 specialized decision models and3 high-end LLM references. Same1342 text questions,31 categories. Updated October21,2026.</p>'
    body += '<nav><a href="#overview">Overall results</a><a href="#new-additions">October21 findings</a><a href="#llm-references">LLM references</a><a href="#functions">Named categories</a><a href="#method">Method</a></nav>'
    body += '<div class="cards"><div class="card"><div class="label">Leading decision-model score</div><div class="big">84.9%</div><div class="small">Mammoth-1 ·1139/1342</div></div><div class="card"><div class="label">Highest LLM reference score</div><div class="big">85.2%</div><div class="small">GPT-6 Sol, reasoning off ·1143/1342</div></div><div class="card"><div class="label">Complete matched coverage</div><div class="big">29 routes</div><div class="small">38,918 first attempts ·31 categories</div></div><div class="card"><div class="label">Tied decision-model scores</div><div class="big">84.0%</div><div class="small">Span-02 and Drex Max ·1127 each</div></div></div>'
    body += '<section id="overview"><h2>Accuracy, speed and cost: all29 routes</h2><p>Blue bars: decision models. Pale yellow: separately labelled, no-reasoning LLM references. Every row covers1342 first attempts.</p><div class="figure"><a href="accuracy_speed_cost.svg"><img src="accuracy_speed_cost.png" alt="All29 routes: accuracy, median and p95 response, and cost"></a></div>'+summary_html(s)
    body += '<p class="free-note">*Free public or promotional access is not an API-reported $0 receipt or a permanent production price. No numeric free-price point is plotted. Baseten’s launch promotion is temporary. Costs per1000 are normalized from actual1342-question totals; + ? preserves unreported charges. Qwen is a prepaid-quota valuation.</p>'+prior.prior.legend_html()+'</section>'
    body += '<section id="new-additions"><h2>October21: Mammoth-1, Elephant-1 and Drex Max</h2><div class="scroll"><table><thead><tr><th>Model</th><th>Correct /1342</th><th>Average (mean)</th><th>Median</th><th>p95</th><th>Actual run cost / access</th><th>Route</th></tr></thead><tbody>'
    for mid in NEW:
        m=s['models'][mid]
        body += f'<tr data-addition-model="{mid}"><th>{escape(m["label"])}</th><td>{m["correct"]}/1342 ·{m["accuracy"]:.1%}</td><td>{m["mean_response_ms"]:.1f} ms</td><td>{m["median_ms"]:.1f} ms</td><td>{m["p95_ms"]:.1f} ms</td><td>{escape(price(mid,m,False))}</td><td>{escape(m["route"])}</td></tr>'
    body += '</tbody></table></div><p>All4026 new first attempts were usable, without recoveries or probability-format warnings. Neither partial OpenRouter control is ranked. Earlier26 model records are unchanged.</p>'
    body += ''.join('<h3>'+escape(title)+'</h3><p>'+escape(text)+'</p>' for title,text in findings(s))+'</section>'
    body += '<section id="llm-references"><h2>High-end LLM references, reasoning off</h2><p>These three selected reference routes show the level of immediate decision performance alongside generative models. They are not an exhaustive ranking of every LLM that can disable reasoning. No tools or iterative repair;16 output tokens maximum.</p><p>Sol: OpenRouter → OpenAI, explicit reasoning off. Sonnet: OpenRouter → Anthropic, no tools, constrained JSON-choice schema. Both complete runs report zero reasoning/thinking tokens. Sonnet’s separate bare-ID trial produced84 unusable outputs among110 and is not pooled into its complete score. Qwen: Hyper Charm, reasoning_effort=none; the route does not report reasoning-token counts, so missing telemetry is not called zero. Its original delivery failures remain in the denominator.</p></section>'
    body += readable.clarity_section(s,guide).replace('All 20 models','All29 routes').replace('all 20 models','all29 routes')
    body += '<section id="quality"><h2>Delivered decisions and failures</h2>'+markdown.markdown(prior.prior.quality(s),extensions=['tables'])+'</section>'
    body += '<section id="image-support"><h2>Image input is a separate test</h2><p>Mammoth-1 and Elephant-1 are text-only on the tested catalog routes. Drex Max documents image input through its direct Nace API; no image score is inferred here. The <a href="https://github.com/etsabary/visual-decision-benchmark">separate image benchmark</a> and its measured results are unchanged.</p></section>'
    body += '<section id="method"><h2>Method, cost and measurement limits</h2>'+''.join('<p>'+escape(text)+'</p>' for text in method(s))+'</section>'
    body += '<section id="downloads"><h2>Questions, data and audit</h2><p><a href="statistics.json">29-route aggregate JSON</a> ·<a href="model_statistics.csv">Model CSV</a> ·<a href="category_scores.csv">Named-category CSV</a> ·<a href="audit_receipt.json">Sanitized audit receipt</a> ·<a href="manifest.json">Release manifest</a> ·<a href="report.txt">Plain-text findings</a></p><p>Unchanged answer-free questions: <a href="../consolidated_2026-10-19/questions_1342.csv">CSV</a> ·<a href="../consolidated_2026-10-19/questions_1342.jsonl">Exact native JSONL</a> ·<a href="../consolidated_2026-10-19/questions_1342.txt">Readable text</a>.</p></section></main></body></html>\n'
    return head+body


def clean(text):
    # Normalize prose whitespace only; never touch JSON, CSV, prompts or scores.
    text = re.sub(r'(?<=[A-Za-z])(?=\d)', ' ', text)
    text = re.sub(r'(?<=\d)(?=[A-Za-z])', ' ', text)
    return text


def build():
    assert not (DEST/'release_checksums.json').exists(),'Never overwrite a sealed release'
    archive.archive()
    s,guide,report = load()
    DEST.mkdir(exist_ok=True)
    exports(s,guide);overview(s)
    write(DEST/'report.html',html(s,guide))
    narrative = '\n\n'.join('## '+title+'\n\n'+text for title,text in findings(s))
    categories = category_markdown(s,guide)
    intro = '# System1 Decision Benchmark\n\n26 specialized decision models and3 high-end LLM references on the same1,342 text questions across31 categories. Updated October21,2026.\n\n'
    intro += '**Mammoth-1 leads the tested decision models at1139/1342 (84.9%). GPT-6 Sol without reasoning scored1143/1342 (85.2%); their median responses were240 ms and1023 ms. Drex Max and Span-02 tie at1127/1342 (84.0%).**\n\n'
    intro += '[Interactive report]('+SITE+') ·[October21 findings]('+SITE+'#new-additions) ·[Named, color-coded categories]('+SITE+'#functions).\n\n![All29 routes: accuracy, speed and cost]('+NAME+'/accuracy_speed_cost.png)\n\n'
    intro += '## Results, speed and cost\n\nEvery row contains1342 first attempts. Costs per1000 are normalized; actual run totals appear separately. Free access is not a metered production price. Pale-yellow graph bars distinguish no-reasoning LLM references; blue bars are decision models.\n\n'
    intro += table(['Model','Type','Correct /1342','Accuracy','Median','p95','Cost per1000','Actual1342-question cost'],rows(s))+'\n\n'
    intro += '*Baseten’s free launch promotion is temporary. d3-turbo and Amos have separate public-free access. These endpoints omit monetary receipts; their numeric metered-price fields remain null. Qwen’s amount is prepaid-quota valuation; + ? means unreported charges.*\n\n'
    intro += legend_markdown().replace('1,136','1,342')+'\n\n'
    end = '## Questions, statistics and method\n\nUnchanged answer-free questions: [CSV](consolidated_2026-10-19/questions_1342.csv), [exact native JSONL](consolidated_2026-10-19/questions_1342.jsonl), [readable text](consolidated_2026-10-19/questions_1342.txt).\n\n'
    end += 'Current exports: [model CSV]('+NAME+'/model_statistics.csv), [category CSV]('+NAME+'/category_scores.csv), [aggregate JSON]('+NAME+'/statistics.json), [audit receipt]('+NAME+'/audit_receipt.json), [manifest]('+NAME+'/manifest.json).\n\n'
    end += '\n\n'.join(method(s))+'\n\nOffline checks: `python3 validate_october21_release.py` and `python3 -m unittest discover -p "test_*.py"`. Earlier dated releases and their seals remain available unchanged.\n'
    write(repo_file('README.md', root=ROOT),intro+narrative+'\n\n'+categories+end)
    write(repo_file('FUNCTIONS.md', root=ROOT),'# All31 categories:26 decision models and3 LLM references\n\nSame1342 questions. [Color-coded tables]('+SITE+'#functions).\n\n'+category_markdown(s,guide,True))
    write(repo_file('OUTPUT_COMPLIANCE.md', root=ROOT),'# Delivered decisions and request failures\n\nAll29 routes retain the full1342-question first-attempt denominator. Wrong valid decisions are separate from unusable outputs or provider failures. All4026 new first attempts were usable, with zero recoveries.\n\n'+prior.prior.quality(s)+'\n\nThe separate stopped Sonnet bare-ID trial is not pooled into its complete constrained JSON-choice reference. Qwen’s original quota and transport failures remain unsuccessful first deliveries.\n')
    oldcaps = archive.previous(repo_file('IMAGE_CAPABILITIES.md', root=ROOT)).read_text()
    write(repo_file('IMAGE_CAPABILITIES.md', root=ROOT),'# Image input: October21 additions\n\nMammoth-1 and Elephant-1 are text-only on the tested Baseten/OpenRouter catalog routes. Drex Max documents text and image input through its [direct Nace API](https://console.nace.ai/docs/drex/guides/drex-max); its tested OpenRouter route currently advertises text only. No new image inference was performed in this update.\n\nThese additions bring the specialized text cohort to26 models,17 with declared image input on at least one documented route. Declared support does not establish a measured image score. The [separate visual benchmark](https://github.com/etsabary/visual-decision-benchmark) remains a separate comparison.\n\n## Previous dated capability review\n\n'+oldcaps)
    write(DEST/'report.txt',narrative+'\n\n'+table(['Model','Type','Correct','Accuracy','Median','p95','Cost/1000','Actual cost'],rows(s))+'\n\n'+'\n\n'.join(method(s))+'\n')
    receipt = dict(status='VERIFIED_COMPLETE_THREE_1342',question_count=1342,added_model_count=3,
        primary_attempts=4026,recoveries=0,unusable_responses=0,bank_sha256=analysis.router.bank.BANK_HASH,
        source_summary_sha256=digest(PRIVATE/'summary.json'),
        evidence_sha256={mid:m['evidence_sha256'] for mid,m in report['models'].items()},
        scoring_authority_sha256=sorted(report['gold_source_bindings'].values()),
        analysis_source_sha256=report['analysis_source_sha256'],
        controls=report['openrouter_controls'],
        verification='Reconciled dispatches, attempts, results, software seals and every payload hash; private revision-bound scoring, raw first-attempt latency quantiles and charge sums verified. No route pooling.',
        privacy='Aggregate evidence and hashes only; no correct answer keys, per-item correctness, credentials or account records')
    write(DEST/'audit_receipt.json',json.dumps(receipt,indent=2)+'\n')
    # Repair compact human prose from authoring without altering attributes/IDs.
    # Explicit replacements keep model IDs, anchor names and machine data intact.
    replacements={'System1':'System 1','and3':'and 3','same1,342':'same 1,342','across31':'across 31','October21':'October 21',
        'at1139':'at 1139','scored1143':'scored 1143','were240':'were 240','and1023':'and 1023','at1127':'at 1127',
        'All29':'All 29','all29':'all 29','all31':'all 31','All31':'All 31','contains1342':'contains 1342',
        'per1000':'per 1000','Actual1342':'Actual 1342','same1342':'same 1342','questions,31':'questions, 31',
        'models and3':'models and 3','·1139':'· 1139','·1143':'· 1143','·1127':'· 1127','·31':'· 31',
        'covers1342':'covers 1342','All4026':'All 4026','all4026':'all 4026','Earlier26':'Earlier 26',
        'earlier26':'earlier 26','two20':'two 20','the4026':'the 4026','bank to26':'bank to 26','cohort to26':'cohort to 26',
        'models,17':'models, 17','26 models and3':'26 models and 3','categories:26':'categories: 26',
        'full1342':'full 1342','least20':'least 20','above2000':'above 2000','not1342':'not 1342',
        'The37':'The 37','separate1305':'separate 1305','All206':'All 206','REAX1':'REAX 1',
        'HTTP408':'HTTP 408','produced84':'produced 84','among110':'among 110','repair;16':'repair; 16',
        'Same1342':'Same 1342','actual1342':'actual 1342','seed2026101906':'seed 2026101906',
        'per1,000':'per 1,000','October21,2026':'October 21, 2026','October 21,2026':'October 21, 2026'}
    paths=[repo_file(n, root=ROOT) for n in ('README.md','FUNCTIONS.md','OUTPUT_COMPLIANCE.md','IMAGE_CAPABILITIES.md')]+[DEST/'report.html',DEST/'report.txt']
    for path in paths:
        text=path.read_text()
        for before,after in replacements.items():text=text.replace(before,after)
        write(path,text)
    manifest = dict(version='october21-native-additions-v1',question_count=1342,model_count=29,
        decision_model_count=26,llm_reference_count=3,category_count=31,primary_attempts=38918,
        bank_sha256=analysis.router.bank.BANK_HASH,added_models=list(NEW),earlier_models_unchanged=True,
        prior_statistics_sha256=digest(prior.DEST/'statistics.json'),
        artifacts={p.name:digest(p) for p in sorted(DEST.iterdir()) if p.is_file() and p.name not in ('manifest.json','release_checksums.json')})
    write(DEST/'manifest.json',json.dumps(manifest,indent=2)+'\n')
    pages = repo_file('docs', root=ROOT)/NAME
    pages.mkdir(parents=True,exist_ok=True)
    for path in DEST.iterdir():
        if path.is_file() and path.name!='release_checksums.json':shutil.copyfile(path,pages/path.name)
    write(repo_file('docs/report.html', root=ROOT),prior.rebase((DEST/'report.html').read_text(),NAME))
    for name,anchor in (('index.html',''),('functions.html','#functions'),('output_compliance.html','#quality')):
        write(repo_file('docs', root=ROOT)/name,'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="benchmark-cohort" content="october21-additions-1342"><meta http-equiv="refresh" content="0;url=report.html'+anchor+'"><title>System1 Decision Benchmark</title></head><body><a href="report.html'+anchor+'">Current29-route benchmark</a></body></html>\n')
    print('Built29 complete routes and899 exact category cells. No inference or Git operation.')


def hashes():
    paths={repo_file(name, root=ROOT) for name in ACTIVE}
    for folder in (DEST,repo_file('docs', root=ROOT)/NAME,archive.ARCHIVE):
        paths.update(p for p in folder.rglob('*') if p.is_file() and p.name!='release_checksums.json')
    return {str(logical_relative(path, root=ROOT)):digest(frozen_file(path)) for path in sorted(paths)}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--seal',action='store_true');args=p.parse_args()
    if args.seal:
        from validate_october21_release import validate
        validate();assert not (DEST/'release_checksums.json').exists()
        write(DEST/'release_checksums.json',json.dumps(hashes(),indent=2)+'\n')
    else:
        build()
