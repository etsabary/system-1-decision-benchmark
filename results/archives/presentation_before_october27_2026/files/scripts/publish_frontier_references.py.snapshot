"""Add three complete, answer-key-free LLM references to the readable report.

Consumes sealed offline summaries, never calls a model or loads correct keys.
The original twenty decision-model aggregates and earlier release seals stay
unchanged. A separate publication seal covers this new presentation.
"""
from repo_layout import logical_relative, repo_file
import argparse
from collections import Counter
from copy import deepcopy
import csv
from hashlib import sha256
from html import escape
import io
import json
from pathlib import Path
import re
import shutil

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import numpy as np

import archive_frontier_presentation as archive
import build_readable_report as readable
from build_october18_report import format_speed,format_cost,legend_markdown,PALETTES
from publish_consolidated_report import table

ROOT=Path(__file__).resolve().parents[1]
NAME='llm_references_2026-10-19'
DEST=repo_file(NAME, root=ROOT)
SITE='https://etsabary.github.io/jev-1.14-comparison-benchmark/'+NAME+'/report.html'
BANK_HASH='2db8cf8353f12b609d4df5330d94f53390c9c2919677dc793df4bb2d3cff7076'
REFERENCE_IDS={'openai/gpt-6-sol':'reference_sol','anthropic/claude-sonnet-5.5':'reference_sonnet',
               'qwen3.8-max':'reference_qwen'}
LABELS={'reference_sol':'GPT-6 Sol — no reasoning','reference_sonnet':'Sonnet 5.5 — no thinking, JSON-choice',
        'reference_qwen':'Qwen3.8-Max — none, Hyper Charm'}
ACTIVE_FILES=('README.md','FUNCTIONS.md','OUTPUT_COMPLIANCE.md','LLM_EXPANSION.md','LLM_REFERENCES.md',
              'docs/index.html','docs/functions.html','docs/output_compliance.html',
              'archive_frontier_presentation.py','publish_frontier_references.py','validate_frontier_release.py',
              'test_frontier_publication.py','build_readable_report.py','validate_readable_report.py',
              'validate_consolidated_release.py','test_consolidated_publication.py','test_readable_report.py',
              '.github/workflows/october18-validate.yml','frontier_reference.py','bounded_reference_runner.py',
              'sonnet55_reference.py','sonnet55_schema_reference.py','hyper_reference.py',
              'analyze_frontier_reference.py',
              'resume_hyper_reference.py','test_hyper_resume_controls.py')


def digest(path):return sha256(Path(path).read_bytes()).hexdigest()


def write(path,text):
    if path.suffix in ('.md','.txt','.html'):
        text=re.sub(r'\b(on|with|all|All|Same|same|per|and|of|October|Span|Sol|Sonnet|scored|answered|added|cover|covers|complete|earlier|Earlier|are|has|from|to|only|across|first|concurrency)(?=\d)',r'\1 ',text)
        text=re.sub(r'(October \d{1,2}),(\d{4})',r'\1, \2',text)
        text=re.sub(r'(?<=[A-Za-z]),(?=\d)',', ',text)
        text=re.sub(r'·(?=[A-Za-z0-9])','· ',text)
        text=re.sub(r'(?<=\d)ms\b',' ms',text)
        text='\n'.join(line.rstrip() for line in text.splitlines()).rstrip()+'\n'
    path.parent.mkdir(parents=True,exist_ok=True);path.write_text(text,encoding='utf-8')


def normalize(report):
    mid=REFERENCE_IDS[report['model']];v=deepcopy(report['statistics'])
    assert v['n']==1342 and sum(c['n'] for c in v['families'].values())==1342
    provider_fail=sum(v['statuses'].get(k,0) for k in ('transport_failure','http_failure','provider_error'))
    c=v['cost_all_attempts'];known=c['known_usd'];missing=c['missing_attempts']
    v.update(model_id=mid,label=LABELS[mid],route=report['route_description'],
             median_ms=v['latency_first_all']['median_ms'],p95_ms=v['latency_first_all']['p95_ms'],
             accuracy_among_usable=v['correct']/v['answered'] if v['answered'] else None,
             first_statuses=v['statuses'],provider_failures=provider_fail,
             model_output_failures=v['failed']-provider_fail,
             cost={'known_usd':known,'known_decimal':c['exact_usd'],'unknown_attempts':missing,
                   'exact_usd':None if missing else known,'known_usd_per_1000':known/1342*1000,
                   'scope':'USD-equivalent prepaid quota valuation, not cash invoice' if mid=='reference_qwen' else 'API-reported USD charge'},
             reasoning_setting=report['reasoning_description'],reasoning_verification=report['reasoning_verification_note'],
             compatibility_known_usd=report['compatibility_probe_cost_usd'],
             compatibility_unknown_attempts=report.get('compatibility_probe_unknown_attempts',0))
    return mid,v


def load(reports):
    native,guide=readable.load();s=deepcopy(native);refs={};bindings={}
    for path in reports:
        report=json.loads(path.read_text());seal=json.loads((path.parent/'checksums.json').read_text())
        assert digest(path)==seal['summary.json'] and report['status']=='COMPLETE_FRONTIER_REFERENCE_1342'
        assert report['bank_sha256']==BANK_HASH
        mid,value=normalize(report);assert mid not in refs
        refs[mid]=value;bindings[mid]={'source_summary_sha256':digest(path),
             'completion_sha256':report['completion_sha256'],'private_source_scoring_bindings':sorted(report['gold_source_bindings'].values()),
             'operational_evidence':report.get('operational_evidence',{})}
    assert set(refs)==set(LABELS),'All three complete references are required; no extrapolated partials'
    s['models'].update(refs)
    s['ranked_model_ids']=sorted(s['models'],key=lambda mid:(-s['models'][mid]['correct'],mid))
    s.update(status='COMPLETE_20_DECISION_PLUS_SELECTED_LLM_REFERENCES_1342',model_count=20+len(refs),
             primary_cases=(20+len(refs))*1342,reference_model_ids=list(refs),
             tested_llm_reference_count=3,all_tested_primary_cases=23*1342,
             decision_model_ids=native['ranked_model_ids'],
             model_kinds={mid:'LLM reference' if mid in refs else 'Decision model' for mid in s['models']},
             source_native_statistics_sha256=digest(repo_file('consolidated_2026-10-19/statistics.json', root=ROOT)),
             reference_evidence_bindings=bindings,question_bank_sha256=BANK_HASH)
    # Native-only combined totals/family caches must not masquerade as totals for23.
    for key in ('families','cost','attempts','recoveries'):s.pop(key,None)
    assert all(s['models'][mid]==native['models'][mid] for mid in native['models'])
    return s,guide


def verify_private_sources(paths):
    import frontier_reference as sol
    import sonnet55_schema_reference as sonnet
    import hyper_reference as qwen
    modules={v.MODEL:v for v in (sol,sonnet,qwen)}
    for path in paths:
        report=json.loads(path.read_text());module=modules[report['model']];out=module.OUT
        assert path.resolve().is_relative_to((out/'analysis').resolve())
        rows,results=module.validate(out,complete=True);stats=report['statistics']
        assert len(results)==1342 and len(rows)==stats['attempts']
        assert module.file_hash(out/'completion.json')==report['completion_sha256']
        first={r['request_index']:r for r in rows if r['attempt']==1}
        assert len(first)==1342 and dict(Counter(r['status'] for r in first.values()))==stats['statuses']
        assert module.chat.quantiles([r['latency_ms'] for r in first.values()])==stats['latency_first_all']
        money=module.chat.money(rows)
        assert all(money[k]==stats['cost_all_attempts'][k] for k in money)
        for name,value in report.get('operational_evidence',{}).items():assert module.file_hash(out/name)==value


def trial_findings():
    import frontier_reference as capture
    result=[]
    for label,folder in [('Sonnet5.5 bare-ID','sonnet55_no_thinking_2026-10-19')]:
        out=repo_file('runs', root=ROOT)/folder;rows=capture.d.rows(out/'attempts.jsonl');first=[r for r in rows if r['attempt']==1]
        result.append({'trial':label,'status':'STOPPED_PARTIAL_NOT_RANKED','questions_attempted':len(first),'attempts':len(rows),
             'first_statuses':dict(Counter(r['status'] for r in first)),'cost':capture.chat.money(rows),
             'raw_attempts_sha256':digest(out/'attempts.jsonl')})
    return {'stopped_trials':result,
            'policy':'All stopped trials/probes are separate from complete scored runs; unknown charges are not zero. Routes were selected without a benchmark answer key.'}


def all_rows(s):
    rows=[]
    for mid in s['ranked_model_ids']:
        m=s['models'][mid];c=m['cost']
        rows.append([m['label'],s['model_kinds'][mid],f"{m['correct']}/1342",f"{m['accuracy']:.1%}",
                     format_speed(m['median_ms']),f"{m['p95_ms']:.0f} ms",
                     ('~' if mid=='nimble_v4_max' else '')+format_cost(c['known_usd_per_1000'],c['unknown_attempts']),
                     f"${c['known_usd']:.6f}"+(' + ?' if c['unknown_attempts'] else '')+(' quota' if mid=='reference_qwen' else '')])
    return rows


def summary_html(s):
    rows=[]
    for mid in s['ranked_model_ids']:
        m=s['models'][mid];c=m['cost'];sb=next((i for i,v in enumerate((250,500,1000)) if m['median_ms']<=v),3)
        cb=next((i for i,v in enumerate((.01,.025,.05)) if c['known_usd_per_1000']<=v),3)
        pb=next((i for i,v in enumerate((250,500,1000)) if m['p95_ms']<=v),3)
        kind=s['model_kinds'][mid];unknown=' + ?' if c['unknown_attempts'] else ''
        approximate='~' if mid=='nimble_v4_max' else ''
        rows.append(f'<tr data-summary-model="{mid}"><th scope="row">{escape(m["label"])}</th><td>{kind}</td><td>{m["correct"]}/1342<br>{m["accuracy"]:.1%}</td>'
          f'<td style="background:{PALETTES[sb]}">{m["median_ms"]:.0f} ms</td><td style="background:{PALETTES[pb]}">{m["p95_ms"]:.0f} ms</td>'
          f'<td style="background:{PALETTES[cb]}">{approximate}${c["known_usd_per_1000"]:.6f}{unknown}</td><td>{approximate}${c["known_usd"]:.6f}{unknown}'+(' quota' if mid=='reference_qwen' else '')+'</td></tr>')
    return '<div class="scroll"><table><thead><tr><th>Model</th><th>Type</th><th>Correct / questions</th><th>Median</th><th>p95</th><th>Cost / 1,000</th><th>Actual 1,342-question cost</th></tr></thead><tbody>'+''.join(rows)+'</tbody></table></div>'


def legend_html():
    cells=[]
    for i,(name,speed,cost) in enumerate(zip(('Green','Yellow','Orange','Red'),('≤250 ms','>250–500 ms','>500–1,000 ms','>1,000 ms'),('≤$0.010','>$0.010–0.025','>$0.025–0.050','>$0.050'))):
        cells.append(f'<tr><th style="background:{PALETTES[i]}">{name}</th><td>{speed}</td><td>{cost}</td></tr>')
    return '<details><summary>Fixed speed and cost color bands</summary><table><thead><tr><th>Band</th><th>Response time</th><th>Known cost per1,000</th></tr></thead><tbody>'+''.join(cells)+'</tbody></table><p>Thresholds use unrounded values. Incomplete costs describe a known lower bound. The median, not p95, is the speed-screening measure.</p></details>'


def refresh_native_context(text,s):
    replacements={
        'The full comparison is 20 routes × 1,342 questions = 26,840 first attempts.':f'The full comparison is {s["model_count"]} routes × 1,342 questions = {s["primary_cases"]:,} first attempts. Within the unchanged 20-decision-model cohort, there are 26,840 first attempts.',
        'Actual selected HTTP attempts total 26,983, including 143 permitted recoveries.':'That original cohort has 26,983 selected HTTP attempts, including 143 permitted recoveries. New LLM attempt and recovery totals appear in the aggregate statistics and quality table.',
        'No new calls were made for this consolidation.':'The 20 decision-model measurements are unchanged; the three complete LLM reference runs were added on October 19.',
        'Nimble uses Bespoke directly; the other routes use OpenRouter with pinned providers and no fallback.':'Among the 20 decision-model routes, Nimble uses Bespoke directly; the others use OpenRouter with pinned providers and no fallback. The new Qwen reference uses Hyper Charm directly.',
        'Known cost across the cohort is':'Known cost across the original 20-decision-model cohort is',
        'Sixteen regular-LLM configurations have only the earlier 1,136-question coverage. They remain in that reference report and are not assigned an expanded score, extrapolated, or ranked here.':'Sixteen earlier regular-LLM configurations have only 1,136-question coverage and are not extrapolated here. The three separately labelled LLM references above each cover all 1,342 questions.',
        'No new inference was performed for this consolidation.':'The decision-model evidence was not rerun; the three new LLM references use fresh inference on the same complete bank.',
        'The overall leader is not strongest in every function':'The decision-model leader is not strongest in every function'}
    for old,new in replacements.items():text=text.replace(old,new)
    return text


def analysis_text(s):
    m=s['models'];span=m['respan02'];sol=m['reference_sol'];sonnet=m['reference_sonnet'];qwen=m['reference_qwen']
    qcat=lambda fid: f"{qwen['families'][fid]['correct']}/{qwen['families'][fid]['n']}"
    best=max((m[i] for i in s['reference_model_ids']),key=lambda v:v['correct'])
    paragraphs=[('Decision models alongside high-end LLMs',
      f"Respan Span-02 scored {span['correct']}/1342 ({span['accuracy']:.1%}). The highest-scoring LLM reference was {best['label']}: {best['correct']}/1342 ({best['accuracy']:.1%}), a gap of {best['correct']-span['correct']} decisions. These are the same questions, facts and option order, with no tools or iterative repair. This measures System 1-style decision performance, not unrestricted reasoning or general intelligence."),
      ('Sol and Span are close overall, with different strengths',
       f"Sol scored {sol['correct']}/1342 ({sol['accuracy']:.1%}), versus Span’s {span['correct']} ({span['accuracy']:.1%}). On the original 1136 questions, Sol scored {sol['matched_original_1136']['correct']} and Span1011; on the added206, Sol scored {sol['added_206']['correct']} and Span116. Sol answered45/46 forward conditionals and52/52 necessary-condition questions; Span answered32/46 and44/52. Span answered33/48 sequential procedures and55/74 truth-teller questions, versus Sol18/48 and38/74."),
      ('Speed and cost separate otherwise nearby scores',
       f"Sol’s median was {sol['median_ms']:.0f}ms, versus Span’s {span['median_ms']:.0f}ms: {sol['median_ms']/span['median_ms']:.1f} times longer. Their recorded full-bank costs were ${sol['cost']['known_usd']:.6f} and ${span['cost']['known_usd']:.8f}, a {sol['cost']['known_usd']/span['cost']['known_usd']:.0f}-fold difference. Span’s p95 was {span['p95_ms']:.0f}ms, versus Sol’s {sol['p95_ms']:.0f}ms; the median advantage did not extend to that tail measure. These are route measurements, not controlled hardware comparisons."),
      ('Sonnet needs a constrained decision format',
       f"Sonnet’s JSON-choice run scored {sonnet['correct']}/1342 ({sonnet['accuracy']:.1%}), at a {sonnet['median_ms']:.0f}ms median and ${sonnet['cost']['known_usd']:.6f} for the bank. All1342 outputs were valid and reported zero thinking tokens. In the separate bare-ID trial,84 of110 outputs were unusable explanations or truncated text. That trial is not pooled into this score. Sonnet scored45/46 forward conditionals,15/48 sequential procedures and30/71 exact truth-counting questions."),
      ('Qwen: decision accuracy and account limits',
       f"Qwen3.8-Max delivered {qwen['correct']}/1342 ({qwen['accuracy']:.1%}); {qwen['answered']} first attempts returned usable decisions, with {qwen['correct']/qwen['answered']:.1%} accuracy among those responses. There were {qwen['provider_failures']} first-attempt provider/transport failures, retained in the primary score. It scored {qcat('F02')} on following if-then rules, {qcat('F13')} on step-by-step procedures and {qcat('F10')} on truth-teller consistency. Its median was {qwen['median_ms']:.0f} ms and p95 {qwen['p95_ms']:.0f} ms. Hyper Charm’s hourly limit produced some rejected requests; those are not labelled wrong model choices. Its cost is a prepaid-quota valuation, not additional cash billing. The requested none setting is documented in Hyper’s catalog, but the route does not report reasoning-token counts."),
      ('What the comparison supports',
       'Span’s 84.0% sits between Sol’s 85.2% and Sonnet’s 79.7% on these immediate decisions, with much lower recorded cost and a shorter median response. The Qwen row adds a further reference point. Scores and error profiles differ by category. This is a selected reference group, not an exhaustive ranking of every LLM that can disable reasoning. Models that require thinking are outside this comparison. New eight-question categories remain coarse diagnostic samples, not reliability guarantees.')]
    return [(title,re.sub(r'\b(Span|Sol|Sonnet|all|All|the|added|scored|answered|of|and|versus)(?=\d)',r'\1 ',text)) for title,text in paragraphs]


def reference_section(s):
    parts=['<section id="llm-references"><h2>High-end LLM references, reasoning off</h2>']
    parts += ['<h3>'+escape(title)+'</h3><p>'+escape(text)+'</p>' for title,text in analysis_text(s)]
    parts.append('<p>Sol: OpenRouter → OpenAI, standard. Sonnet: OpenRouter → Anthropic, between-tools mode with no tools, JSON-choice schema. Qwen: Hyper Charm, reasoning_effort=none. All use the same 16-token output cap; Sonnet’s JSON structure consumes more output tokens than a bare numeric ID. Sol and Sonnet responses are checked for explicit zero reasoning tokens. Qwen’s missing telemetry is not counted as zero.</p>')
    parts.append('<p>Reasoning-off eligibility: <a href="https://developers.openai.com/api/docs/models/gpt-6-sol">OpenAI</a> · <a href="https://platform.claude.com/docs/en/build-with-claude/thinking-troubleshooting">Anthropic</a> · <a href="https://hyper.charm.land/v1/models">Hyper Charm catalog</a>.</p></section>')
    return ''.join(parts)


def overview_chart(s):
    ids=s['ranked_model_ids'];models=[s['models'][i] for i in ids];y=np.arange(len(ids))
    with plt.rc_context({'font.family':'DejaVu Sans','svg.fonttype':'none','svg.hashsalt':'frontier-reference-1342-v1'}):
        fig,axs=plt.subplots(1,3,figsize=(15,max(11,.48*len(ids)+2)),sharey=True,gridspec_kw={'width_ratios':[1.2,1.1,1.1]})
        colors=[(0.95,0.83,0.42,0.60) if i in s['reference_model_ids'] else '#16728c' for i in ids]
        bars=axs[0].barh(y,[100*m['accuracy'] for m in models],color=colors)
        for bar,mid in zip(bars,ids):
            if mid in s['reference_model_ids']:
                bar.set_edgecolor('#9c761c');bar.set_linewidth(1.1)
        axs[0].set_yticks(y,[m['label'].replace(' — ','\n') if i in s['reference_model_ids'] else readable.short(m['label']) for i,m in zip(ids,models)],fontsize=10.5)
        axs[0].set_xlim(0,112);axs[0].set_xlabel('Correct first decisions (%)')
        for yy,m in zip(y,models):axs[0].text(100*m['accuracy']+1,yy,f"{m['accuracy']:.1%}",va='center',fontsize=10)
        for yy,m in zip(y,models):
            band=next((i for i,b in enumerate((250,500,1000)) if m['median_ms']<=b),3)
            axs[1].plot([m['median_ms'],m['p95_ms']],[yy,yy],color='#8a99a5',lw=1.3)
            axs[1].scatter(m['median_ms'],yy,color=PALETTES[band],edgecolor='#364c60',s=70,zorder=3)
            axs[1].scatter(m['p95_ms'],yy,color='#35424d',marker='d',s=20,zorder=3)
            c=m['cost'];band=next((i for i,b in enumerate((.01,.025,.05)) if c['known_usd_per_1000']<=b),3)
            axs[2].scatter(c['known_usd_per_1000'],yy,color=PALETTES[band],edgecolor='#364c60',s=70)
            if c['unknown_attempts']:axs[2].text(c['known_usd_per_1000']*1.15,yy,'+ ?',va='center',fontsize=9)
        axs[1].set_xscale('log');axs[1].set_xlabel('Response time (ms, log scale)\nCircle: median · diamond: p95')
        axs[2].set_xscale('log');axs[2].set_xlabel('Known cost per 1,000 questions\nUSD, log scale; + ? = incomplete')
        axs[0].invert_yaxis()
        for ax,title in zip(axs,('Accuracy','Speed','Cost')):
            ax.set_title(title,fontsize=14,pad=18);ax.grid(axis='x',alpha=.2);ax.set_axisbelow(True)
            for spine in ax.spines.values():spine.set_visible(False)
        fig.suptitle(f'20 decision models and {len(s["reference_model_ids"])} high-end LLM references · 1,342 questions',fontsize=17,y=.98)
        fig.legend(handles=[Patch(facecolor='#16728c',label='Accuracy bars: decision models'),
                            Patch(facecolor=(0.95,0.83,0.42,0.60),edgecolor='#9c761c',label='Accuracy bars: LLM reference points')],
                   loc='upper center',bbox_to_anchor=(.5,.957),ncol=2,frameon=False,fontsize=10.5)
        fig.text(.03,.025,'Blue bars: decision models · translucent pale yellow: LLM references. All first attempts; failures remain in the denominator.\nQwen cost is a prepaid-quota valuation, not a cash invoice. Fixed speed/cost bands match the tables. Different providers, dates and concurrency are not controlled away.\nTests: October 15–19, 2026. New LLM references: October 19, 2026.',fontsize=10)
        fig.subplots_adjust(left=.29,right=.98,top=.90,bottom=.13,wspace=.35)
        for suffix in ('png','svg'):fig.savefig(DEST/('accuracy_speed_cost.'+suffix),dpi=160,metadata={'Date':None} if suffix=='svg' else {})
        plt.close(fig)


def quality(s):
    rows=[[s['models'][mid]['label'],s['models'][mid]['answered'],s['models'][mid]['wrong_valid'],s['models'][mid]['provider_failures'],s['models'][mid]['model_output_failures'],s['models'][mid]['recoveries'],s['models'][mid]['eventual']['correct']] for mid in s['ranked_model_ids']]
    return table(['Model','Usable first','Wrong valid','Provider failures','Output failures','Recoveries','Eventual correct'],rows)


def hashes():
    from repo_identity import historical_path
    paths={repo_file(n, root=ROOT) for n in ACTIVE_FILES}
    for folder in (DEST,repo_file('docs', root=ROOT)/NAME,archive.ARCHIVE):paths.update(p for p in folder.rglob('*') if p.is_file() and p.name!='release_checksums.json')
    return {str(logical_relative(p, root=ROOT)):digest(historical_path(p)) for p in sorted(paths)}


def build(reports):
    assert not (DEST/'release_checksums.json').exists(),'Do not overwrite a sealed publication'
    archive.archive();verify_private_sources(reports);s,guide=load(reports);DEST.mkdir(exist_ok=True)
    count=s['model_count'];reference_count=len(s['reference_model_ids'])
    write(DEST/'statistics.json',json.dumps(s,indent=2)+'\n')
    write(DEST/'compatibility_findings.json',json.dumps(trial_findings(),indent=2)+'\n')
    overview_chart(s)
    original_dest=readable.DEST;readable.DEST=DEST
    try:
        for group in readable.GROUPS:readable.plot(s,group)
    finally:readable.DEST=original_dest
    buf=io.StringIO(newline='');writer=csv.writer(buf)
    writer.writerow(['category_id','category','questions']+[s['models'][mid]['label'] for mid in s['ranked_model_ids']])
    for fid in sorted(readable.LABELS):writer.writerow([fid,readable.LABELS[fid],guide[fid]['questions']]+[readable.score(s['models'][mid]['families'][fid]) for mid in s['ranked_model_ids']])
    write(DEST/'category_scores.csv',buf.getvalue());write(DEST/'category_guide.json',json.dumps(guide,indent=2)+'\n')
    buf=io.StringIO(newline='');writer=csv.writer(buf)
    writer.writerow(['model_id','model','type','questions','correct','accuracy','median_ms','p95_ms',
                     'known_cost_usd','known_cost_per_1000_usd','unknown_cost_attempts','cost_scope','route','test_dates_toronto'])
    for mid in s['ranked_model_ids']:
        m=s['models'][mid];c=m['cost']
        writer.writerow([mid,m['label'],s['model_kinds'][mid],m['n'],m['correct'],m['accuracy'],m['median_ms'],m['p95_ms'],
                         c['known_usd'],c['known_usd_per_1000'],c['unknown_attempts'],
                         c.get('scope','Captured API charges or usage times recorded tariffs; see original evidence'),
                         m['route'],'; '.join(sorted(m['dates_toronto']))])
    write(DEST/'model_statistics.csv',buf.getvalue())
    overview='<section id="overview"><h2>All 23 routes: accuracy, speed and cost</h2><p>Twenty specialized decision models and three selected high-end LLM reference configurations. Each row covers all1342 first attempts. Provider failures remain unsuccessful; valid wrong answers are not retried.</p><div class="figure"><a href="accuracy_speed_cost.svg"><img src="accuracy_speed_cost.png" alt="Accuracy, median and p95 latency, and cost for all23 routes on the same1342 questions"></a></div>'+summary_html(s)+'<p>Costs /1000 are normalized from each1342-question run; actual run totals are also shown. Qwen’s amount is provider-reported prepaid-quota usage, not additional out-of-pocket billing. + ? retains unreported charges. Permitted recovery charges are included, probes are separate. Green/yellow/orange/red use the existing fixed bands; they are not relative ranks or significance tests.</p></section>'
    html=(repo_file('readable_2026-10-19/report.html', root=ROOT)).read_text()
    html=re.sub(r'<section id="overview">.*?(?=<section id="analysis">)',overview+reference_section(s),html,flags=re.S)
    html=html.replace(reference_section(s),legend_html()+reference_section(s),1)
    html=html.replace('content="readable-category-tables"','content="decision-models-with-llm-reference-points"',1)
    functions=readable.clarity_section(s,guide).replace('All 20 models',f'All {count} routes').replace('all 20 models',f'all {count} routes')
    html=re.sub(r'<section id="functions">.*?(?=<section id="quality">)',functions,html,flags=re.S)
    # Render the exact same quality data as Markdown without introducing an HTML library.
    qrows=[]
    for mid in s['ranked_model_ids']:
        m=s['models'][mid];qrows.append('<tr><th>'+escape(m['label'])+'</th>'+''.join('<td>'+str(m[k])+'</td>' for k in ('answered','wrong_valid','provider_failures','model_output_failures','recoveries'))+f'<td>{m["eventual"]["correct"]}</td></tr>')
    quality_html='<section id="quality"><h2>Valid decisions and failed requests</h2><div class="scroll"><table><thead><tr><th>Model</th><th>Usable first</th><th>Wrong valid</th><th>Provider failures</th><th>Output failures</th><th>Recoveries</th><th>Eventual correct</th></tr></thead><tbody>'+''.join(qrows)+'</tbody></table></div><p>Sonnet’s stopped bare-ID trial:26/110 usable;84 unusable explanatory/truncated outputs. Its separate complete JSON-choice run above has1342 usable outputs. Hyper Charm hourly-limit rejections remain in Qwen’s primary denominator and are not called wrong model choices.</p></section>'
    html=re.sub(r'<section id="quality">.*?(?=<section id="method">)',quality_html,html,flags=re.S)
    html=html.replace('Twenty complete decision routes, with one score, pooled response times and captured inference costs per route.','Twenty decision models, with three high-end LLM references tested without reasoning. Same1,342 questions,31 categories and one first decision per question.')
    html=html.replace('1,342 questions, 20 routes','1,342 questions, 23 routes').replace('<nav><a href="#overview">','<nav><a href="#llm-references">LLM reference points</a><a href="#overview">',1)
    best=max((s['models'][mid] for mid in s['reference_model_ids']),key=lambda v:v['correct'])
    cards=f'<div class="cards"><div class="card"><div class="label">Leading decision model</div><div class="big">84.0%</div><div class="small">Respan Span-02 ·1127/1342</div></div><div class="card"><div class="label">Highest LLM reference score</div><div class="big">{best["accuracy"]:.1%}</div><div class="small">{escape(best["label"])} ·{best["correct"]}/1342</div></div><div class="card"><div class="label">Same complete bank</div><div class="big">23 routes</div><div class="small">30,866 first attempts ·31 categories</div></div><div class="card"><div class="label">Span median / cost per1000</div><div class="big">206 ms</div><div class="small">$0.00354 per1000 · p95 2157 ms</div></div></div>'
    html=re.sub(r'<div class="cards">.*?(?=<section id="overview">)',cards,html,count=1,flags=re.S)
    html=html.replace('Regular LLMs lack the complete expanded coverage and are not ranked here.','The earlier LLM cohort lacks expanded coverage; the three new reference configurations above cover all1,342 questions.')
    html=html.replace('<section id="analysis"><h2>What the results show</h2>','<section id="analysis"><h2>What the 20 decision models show</h2>')
    html=refresh_native_context(html,s)
    html=html.replace('../consolidated_2026-10-19/model_statistics.csv','model_statistics.csv').replace('../consolidated_2026-10-19/family_statistics.csv','category_scores.csv').replace('../consolidated_2026-10-19/statistics.json','statistics.json')
    html=html.replace('<section id="method">','<section id="method"><p>The LLM references use the same fresh-HTTPS connect-to-complete-response timer, not time to first token. Sol and Sonnet use concurrency2; Hyper Charm Qwen is sequential and resumed after a provider-requested cooldown. Different protocols, providers, dates and account conditions remain confounds. Sonnet alone needs a JSON-choice grammar; its result is labelled accordingly. All output caps are16 tokens. Compatibility probes and stopped trials are separate from the scored full-bank runs.</p>',1)
    html=html.replace('<h2>Download the consolidated statistics</h2>','<h2>Download the consolidated statistics</h2><p><a href="statistics.json">All23 aggregate model statistics</a> · <a href="category_scores.csv">All23 named-category scores</a> · <a href="audit_receipt.json">Sanitized reference audit receipt</a>. Earlier linked20-model exports remain unchanged.</p>')
    html=html.replace('23 routes',f'{count} routes').replace('all23',f'all{count}').replace('All23',f'All{count}').replace('three selected high-end',f'{reference_count} selected high-end').replace('three high-end LLM references',f'{reference_count} high-end LLM references').replace('30,866 first attempts',f'{s["primary_cases"]:,} first attempts')
    write(DEST/'report.html',html)
    narrative='\n\n'.join(title.upper()+'\n'+text for title,text in analysis_text(s))
    write(DEST/'report.txt',narrative+'\n\n'+table(['Model','Type','Correct','Accuracy','Median','p95','Cost/1000','Actual run cost'],all_rows(s))+'\n')
    old=archive.historical_path(repo_file('README.md', root=ROOT)).read_text();start=old.index('## What this measures');end=old.index('## Category scores and explanations')
    native_text=old[start:end].replace('## Span leads the combined bank','## Span leads the decision models').replace('Regular LLMs lack the complete expanded coverage and are not ranked here.','The earlier LLM cohort lacks expanded coverage; the new reference group has complete matched coverage.')
    group_md=readable.markdown_groups(s,guide).replace(readable.NAME,NAME).replace('All 20 models',f'All {count} routes').replace('all 20 models',f'all {count} routes')
    readme=f'# 20 decision models and {reference_count} high-end LLM references on1,342 text questions\n\nUpdated October19,2026. Three LLM configurations were tested October19; decision-model measurements are unchanged.\n\n'
    readme+='**Respan Span-02 leads the specialized decision models with1127/1342 (84.0%). The LLM reference scores, speed and cost below use the same complete bank with reasoning disabled.**\n\n[Interactive report]('+SITE+') · [LLM reference findings]('+SITE+'#llm-references) · [Named, color-coded categories]('+SITE+'#functions).\n\n![All23 routes: accuracy, speed and cost]('+NAME+'/accuracy_speed_cost.png)\n\n## Results, speed and cost\n\nEvery row covers1342 first attempts. Costs per1000 are normalized; actual full-bank totals appear separately. Qwen’s cost is a Hyper Charm quota valuation, not a cash invoice. + ? means additional unreported charges.\n\n'
    readme+=table(['Model','Type','Correct /1342','Accuracy','Median','p95','Cost per1000','Actual1342-question cost'],all_rows(s))+'\n\n'
    readme+=legend_markdown().replace('each actual 1,136-question run','each actual 1,342-question run')+'\n'
    refs_md='\n\n'.join('## '+title+'\n\n'+text for title,text in analysis_text(s))+'\n\n'
    readme+=refs_md+native_text+group_md+old[old.index('## Questions and statistics'):]
    readme=readme.replace('Sixteen regular LLM configurations have no complete expanded coverage, so they are not assigned a 1,342-question score or mixed into this ranking.','Sixteen earlier regular LLM configurations lack complete expanded coverage and are not extrapolated. The four new, separately labelled references above cover all1,342 questions.')
    readme=readme.replace('Run `python3 validate_readable_report.py`','Run `python3 validate_frontier_release.py` and `python3 validate_readable_report.py`')
    readme=readme.replace('](readable_2026-10-19/report.txt)',']('+NAME+'/report.txt)')
    readme=refresh_native_context(readme,s)
    for old,new in (('model_statistics.csv','model_statistics.csv'),('family_statistics.csv','category_scores.csv'),('statistics.json','statistics.json')):
        readme=readme.replace('](consolidated_2026-10-19/'+old+')',']('+NAME+'/'+new+')')
    readme=readme.replace('[plot data]','[earlier decision-model plot data]').replace('[release manifest]','[original decision-model release manifest]').replace('[sanitized audit receipt]','[original decision-model audit receipt]')
    readme+='\n[Current 23-route model statistics CSV]('+NAME+'/model_statistics.csv) · [Current named-category scores CSV]('+NAME+'/category_scores.csv).\n'
    readme=readme.replace('No new inference was performed for this consolidation.','The decision-model evidence was not rerun; three new LLM references use fresh inference on the same complete bank.')
    readme=readme.replace('`build_readable_report.py` builds this presentation from the unchanged, sealed key-free statistics.','`publish_frontier_references.py` builds the current presentation from sealed summaries, preserving the earlier decision-model evidence and report seals.')
    readme=readme.replace('All23',f'All{count}').replace('four new, separately labelled references',f'{reference_count} new, separately labelled qualified references')
    write(repo_file('README.md', root=ROOT),readme);write(repo_file('LLM_REFERENCES.md', root=ROOT),'# High-end LLM reference points\n\n'+refs_md+'[Interactive methods and category results]('+SITE+'#llm-references).\n')
    detailed=readable.markdown_groups(s,guide,details=True).replace(readable.NAME,NAME).replace('All 20 models',f'All {count} routes').replace('all 20 models',f'all {count} routes')
    write(repo_file('FUNCTIONS.md', root=ROOT),f'# All 31 categories: 20 decision models and {reference_count} LLM references\n\nSame1342 questions; first-attempt results. [Color-coded tables]('+SITE+'#functions).\n\n'+detailed)
    quality_note=re.search(r'<p>(.*?)</p>',quality_html).group(1)
    write(repo_file('OUTPUT_COMPLIANCE.md', root=ROOT),'# Delivered decisions and request failures\n\n'+quality(s)+'\n\n'+quality_note+'\n')
    write(repo_file('LLM_EXPANSION.md', root=ROOT),f'# LLM reference coverage\n\n{reference_count} LLM configurations completed all 1342 questions and appear in the reference comparison. [Findings and configuration notes](LLM_REFERENCES.md). Earlier 1136-question LLM runs remain separate and are not extrapolated.\n')
    receipt={'status':'VERIFIED_PRIVATE_REFERENCE_EVIDENCE','question_count':1342,'tested_reference_count':3,'qualified_reference_count':reference_count,'category_count':31,
             'bank_sha256':BANK_HASH,'reference_bindings':s['reference_evidence_bindings'],
             'published_content':'Aggregate counts, latency quantiles, usage and costs only; no answer keys, individual correctness or private verifier material',
             'primary_policy':'All first attempts, including provider failures; no answer-dependent retries',
             'limits':['Exploratory development bank, not pristine held-out evaluation;37 permanent author-development exclusions remain in separate1305 diagnostic.',
                       'Qwen reasoning-token telemetry unavailable; no verified-zero claim.',
                       'Hyper quota valuation is not cash billing. Unknown rejected-request costs are not zero.',
                       'Sonnet constrained JSON-choice run separate from stopped bare-ID trial.']}
    write(DEST/'audit_receipt.json',json.dumps(receipt,indent=2)+'\n')
    manifest={'version':'decision-models-with-llm-reference-publication-v1','question_count':1342,'model_count':count,'decision_model_count':20,'llm_reference_count':reference_count,'tested_llm_count':3,'category_count':31,
              'bank_sha256':BANK_HASH,'native_statistics_sha256':s['source_native_statistics_sha256'],
              'artifacts':{p.name:digest(p) for p in sorted(DEST.iterdir()) if p.is_file() and p.name not in ('manifest.json','release_checksums.json')}}
    write(DEST/'manifest.json',json.dumps(manifest,indent=2)+'\n')
    pages=repo_file('docs', root=ROOT)/NAME;pages.mkdir(parents=True,exist_ok=True)
    for p in DEST.iterdir():
        if p.is_file() and p.name!='release_checksums.json':shutil.copyfile(p,pages/p.name)
    for name,anchor in (('index.html',''),('functions.html','#functions'),('output_compliance.html','#quality')):
        target=NAME+'/report.html'+anchor
        write(repo_file('docs', root=ROOT)/name,'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="benchmark-cohort" content="october19-consolidated-1342"><meta http-equiv="refresh" content="0;url='+target+'"><title>Decision models and reasoning-off LLM references</title></head><body><a href="'+target+'">Open the current benchmark</a></body></html>\n')
    print(f'Built {count} complete ranked routes,{count*31} exact category cells; twenty decision-model aggregates unchanged. No inference or Git operation.')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--summary',type=Path,action='append',default=[]);p.add_argument('--seal',action='store_true');args=p.parse_args()
    if args.seal:
        from validate_frontier_release import validate
        validate();assert not (DEST/'release_checksums.json').exists();write(DEST/'release_checksums.json',json.dumps(hashes(),indent=2)+'\n')
    else:build(args.summary)
