"""Publish three sealed direct-provider runs beside the unchanged 23 routes.

Offline only: no inference, credentials, answer keys or item-level correctness.
Earlier releases and their seals are retained; this presentation gets a new seal.
"""
from repo_layout import logical_relative, repo_file
from repo_layout import source_file
import argparse
from collections import Counter
from copy import deepcopy
import csv
from decimal import Decimal
from hashlib import sha256
from html import escape
import io
import json
from pathlib import Path
import posixpath
import re
import shutil
from urllib.parse import urlsplit,urlunsplit

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import numpy as np

import archive_direct_presentation as archive
import build_readable_report as readable
from build_october18_report import format_speed,format_cost,legend_markdown,PALETTES
import publish_frontier_references as prior
from publication_history import previous_path
from publish_consolidated_report import table

ROOT=Path(__file__).resolve().parents[1]
NAME='direct_additions_2026-10-20'
DEST=repo_file(NAME, root=ROOT)
BASE=repo_file('llm_references_2026-10-19', root=ROOT)
PRIVATE=repo_file('runs/direct_decisions_2026-10-20', root=ROOT)
SITE='https://etsabary.github.io/system-1-decision-benchmark/report.html'
NEW_IDS=('d3_turbo','amos_large','kettei_fat')
ACTIVE=('README.md','FUNCTIONS.md','OUTPUT_COMPLIANCE.md','IMAGE_CAPABILITIES.md',
        'docs/report.html','docs/index.html','docs/functions.html','docs/output_compliance.html',
        'publish_direct_decisions.py','validate_direct_release.py','test_direct_publication.py',
        'capture_image_capabilities_2026_10_20.py','publication_history.py','archive_direct_presentation.py',
        'repo_identity.py','validate_frontier_release.py','validate_consolidated_release.py',
        '.github/workflows/october18-validate.yml')


def digest(path):return sha256(Path(path).read_bytes()).hexdigest()


def write(path,text):
    if path.suffix in ('.md','.txt','.html'):
        text=re.sub(r'(?<=\d)ms\b',' ms',text)
        text=re.sub(r'(?<=[A-Za-z]),(?=\d)',', ',text)
        text='\n'.join(line.rstrip() for line in text.splitlines()).rstrip()+'\n'
    path.parent.mkdir(parents=True,exist_ok=True);path.write_text(text,encoding='utf-8')


def normalize(mid,source):
    import direct_decisions_2026_10_20 as run
    assert source['complete'];v=source['statistics'];cfg=run.MODELS[mid]
    assert v['n']==1342 and len(v['families'])==31
    assert v['first_statuses']=={'ok':1342} and v['recoveries']==0
    assert v['returned_identities']=={cfg['model']:1342} and v['output_token_values']=={'0':1342}
    free=mid!='kettei_fat';c=v['cost'];reported=v['api_reported_cost']
    cost=dict(known_usd=None if free else reported['known_usd'],
        known_decimal=None if free else reported['exact_decimal'],
        known_usd_per_1000=None if free else reported['known_usd']/1342*1000,
        unknown_attempts=reported['unknown_attempts'],exact_usd=None if free else reported['known_usd'],
        public_free_access=free,accounted_access_cost_usd=c['known_usd'],
        scope='Currently free public endpoint; no API-reported monetary charge and no production-price guarantee' if free else 'API-reported USD charges; starter credit is payment credit, not a zero price')
    return dict(model_id=mid,label=source['label'],n=v['n'],correct=v['correct'],answered=v['answered'],
        wrong_valid=v['wrong_valid'],failed=v['failed'],accuracy=v['accuracy'],accuracy_among_usable=v['accuracy'],
        mean_response_ms=v['mean_response_ms'],median_ms=v['latency']['median_ms'],p95_ms=v['latency']['p95_ms'],
        attempts=v['attempts'],recoveries=v['recoveries'],first_statuses=v['first_statuses'],
        provider_failures=0,model_output_failures=0,probability_warnings=v['probabilities_warning_count'],
        eventual=v['eventual'],cost=cost,families=v['families'],dates_toronto=v['dates_toronto'],
        returned_identities=v['returned_identities'],providers={'direct':1342},
        route='Direct → https://'+cfg['host']+'/v1/systemone → '+cfg['model'],
        output_token_values=v['output_token_values'],input_tokens=v['input_tokens'],
        macro_family_accuracy=sum(x['accuracy'] for x in v['families'].values())/31,
        new_domains=v['new_domains'],release_exclusion_diagnostic=v['release_exclusion_diagnostic'],
        compatibility=source['compatibility'])


def verify_private(source):
    """Reconcile sealed HTTP ledgers/timing/charges without opening any key."""
    import direct_decisions_2026_10_20 as run
    assert source['status']=='COMPLETE_THREE_DIRECT_1342' and source['bank_sha256']==prior.BANK_HASH
    seal=json.loads((PRIVATE/'analysis/checksums.json').read_text())
    for name,h in seal.items():assert digest(PRIVATE/'analysis'/name)==h,name
    for name,h in source['analysis_source_sha256'].items():assert digest(repo_file(name, root=ROOT))==h,name
    for mid in NEW_IDS:
        rows,results,_=run.validate(mid,PRIVATE/mid,True);v=source['models'][mid]['statistics']
        assert len(rows)==len(results)==1342 and all(r['status']=='ok' for r in rows)
        assert run.chat.quantiles([r['latency_ms'] for r in rows])==v['latency']
        assert abs(sum(r['latency_ms'] for r in rows)/1342-v['mean_response_ms'])<1e-8
        assert sum(Decimal(str(r['accounted_cost_usd'])) for r in rows)==Decimal(v['cost']['exact_decimal'])
        for name,h in source['models'][mid]['evidence_sha256'].items():assert digest(PRIVATE/mid/name)==h,name
    amendment=source['models']['kettei_fat']['account_rate_amendment']
    assert amendment['observed_limits']==dict(rpm=30,concurrency=1)
    assert amendment['controller_sha256']==digest(source_file(repo_file('continue_sqwish_2026_10_20.py', root=ROOT)))


def load():
    source=json.loads((PRIVATE/'analysis/summary.json').read_text());verify_private(source)
    s=deepcopy(json.loads((BASE/'statistics.json').read_text()))
    old=deepcopy(s['models'])
    for mid in NEW_IDS:s['models'][mid]=normalize(mid,source['models'][mid])
    s['ranked_model_ids']=sorted(s['models'],key=lambda mid:(-s['models'][mid]['correct'],mid))
    s['decision_model_ids']=[mid for mid in s['ranked_model_ids'] if mid not in s['reference_model_ids']]
    s['model_kinds'].update({mid:'Decision model' for mid in NEW_IDS})
    s.update(status='COMPLETE_23_DECISION_PLUS_3_LLM_REFERENCES_1342',model_count=26,
        decision_model_count=23,primary_cases=26*1342,all_tested_primary_cases=26*1342,
        added_model_ids=list(NEW_IDS),updated_date_toronto='2026-10-20',
        prior_statistics_sha256=digest(BASE/'statistics.json'),
        direct_evidence_bindings={mid:source['models'][mid]['evidence_sha256'] for mid in NEW_IDS},
        direct_source_summary_sha256=digest(PRIVATE/'analysis/summary.json'),
        direct_scoring_authority_sha256=sorted(source['gold_source_bindings'].values()),
        direct_analysis_source_sha256=source['analysis_source_sha256'],
        total_http_attempts=sum(m['attempts'] for m in s['models'].values()),
        total_recoveries=sum(m['recoveries'] for m in s['models'].values()))
    assert all(s['models'][mid]==v for mid,v in old.items())
    guide=json.loads((BASE/'category_guide.json').read_text())
    return s,guide


def price(mid,m,normalized=True,styled=True):
    c=m['cost']
    if c.get('public_free_access'):return 'Free public access*'
    if normalized:
        return ('~' if mid=='nimble_v4_max' else '')+format_cost(c['known_usd_per_1000'],c['unknown_attempts']) if styled else f"${c['known_usd_per_1000']:.6f}"+(' + ?' if c['unknown_attempts'] else '')
    return ('~' if mid=='nimble_v4_max' else '')+f"${c['known_usd']:.6f}"+(' + ?' if c['unknown_attempts'] else '')+(' quota' if mid=='reference_qwen' else '')


def all_rows(s):
    return [[m['label'],s['model_kinds'][mid],f"{m['correct']}/1342",f"{m['accuracy']:.1%}",
        format_speed(m['median_ms']),f"{m['p95_ms']:.0f} ms",price(mid,m),price(mid,m,False)]
        for mid in s['ranked_model_ids'] for m in [s['models'][mid]]]


def summary_html(s):
    rows=[]
    band=lambda value,limits:next((i for i,b in enumerate(limits) if value<=b),3)
    for mid in s['ranked_model_ids']:
        m=s['models'][mid];c=m['cost'];free=c.get('public_free_access')
        cb='#edf1f5' if free else PALETTES[band(c['known_usd_per_1000'],(.01,.025,.05))]
        cls='llm-reference' if mid in s['reference_model_ids'] else 'native-addition' if mid in NEW_IDS else ''
        rows.append(f'<tr class="{cls}" data-summary-model="{mid}"><th scope="row">{escape(m["label"])}</th>'
            f'<td>{s["model_kinds"][mid]}</td><td>{m["correct"]}/1342<br>{m["accuracy"]:.1%}</td>'
            f'<td style="background:{PALETTES[band(m["median_ms"],(250,500,1000))]}">{m["median_ms"]:.0f} ms</td>'
            f'<td style="background:{PALETTES[band(m["p95_ms"],(250,500,1000))]}">{m["p95_ms"]:.0f} ms</td>'
            f'<td class="{"cost-incomplete" if c["unknown_attempts"] and not free else ""}" style="background:{cb}">{escape(price(mid,m,styled=False))}</td>'
            f'<td>{escape(price(mid,m,False))}</td></tr>')
    return '<div class="scroll"><table><thead><tr><th>Model</th><th>Type</th><th>Correct / questions</th><th>Median</th><th>p95</th><th>Cost / 1,000</th><th>Actual 1,342-question cost</th></tr></thead><tbody>'+''.join(rows)+'</tbody></table></div>'


def findings(s):
    m=s['models'];d=m['d3_turbo'];a=m['amos_large'];k=m['kettei_fat'];span=m['respan02']
    rank=lambda mid:s['decision_model_ids'].index(mid)+1
    value=lambda mid,fid:f"{m[mid]['families'][fid]['correct']}/{m[mid]['families'][fid]['n']}"
    return [
      ('Three additions, the same leading group',
       f"d3-turbo scored {d['correct']}/1342 ({d['accuracy']:.1%}), fourth among the 23 specialized decision models. Span remains first at 1127, followed by Perplexity Decider at 1120 and Nimble Max at 1115. Amos Large scored {a['correct']} ({a['accuracy']:.1%}), sixth; kettei-fat scored {k['correct']} ({k['accuracy']:.1%}), seventh. These are observed scores on this developing bank, not a general intelligence ordering."),
      ('Strong rule following does not imply strong state tracking',
       f"d3-turbo and kettei-fat each answered all 46 if-then questions correctly; Amos answered 44. Checking required conditions produced 51/52, 49/52 and 50/52 respectively. On step-by-step procedures—applying each ordered edit to the current state—the scores were 20/48, 16/48 and 16/48. Span scored 33/48. All three newcomers returned valid decisions; their unsuccessful procedure answers were wrong choices, not formatting failures."),
      ('Knowledge tracking and exact counting separate the newcomers',
       f"On tracking what others know, d3-turbo scored 47/50, Amos 46/50 and kettei-fat 43/50, versus Span 41/50. These tasks ask, for example, where an observer will look after an object moved while they were absent. Exact truth counting—how many supplied claims are true—gave d3-turbo 35/71, Amos 37/71 and kettei-fat 19/71, versus Span 46/71. A similar overall score can conceal a large difference on one operation."),
      ('kettei-fat has a different profile from its neighboring scores',
       f"kettei-fat scored {value('kettei_fat','F18')} on causal intervention, which asks what changes when a specified cause is forced to a new value; d3-turbo scored {value('d3_turbo','F18')} and Amos {value('amos_large','F18')}. It also scored 56/58 on exceptions and priority rules and 43/43 on choosing authoritative current records. Its 19/71 exact truth-counting score is 26.8%, against a 20% random-choice baseline. The category profile is more useful than treating its 79.4% overall as one uniform ability."),
      ('Scores near the Sonnet reference, at shorter response times',
       f"Sonnet's separately constrained, no-thinking reference scored 1070/1342 (79.7%). d3-turbo answered 36 more correctly, Amos four more and kettei-fat four fewer. Their medians were {d['median_ms']:.0f}, {a['median_ms']:.0f} and {k['median_ms']:.0f} ms, versus Sonnet's 1506 ms. These small Amos/Sonnet/kettei score gaps do not establish a reliable ordering. Sol remains the highest-scoring LLM reference at 1143/1342 (85.2%)."),
      ('Fast responses, separate public-access and metered prices',
       f"The October 20 mean / median / p95 times were d3-turbo 182/165/298 ms, Amos 306/311/360 ms and kettei-fat 179/174/214 ms. All 4026 first attempts returned usable decisions, with no recoveries or probability-format warnings. d3-turbo and Amos used currently free public endpoints; no monetary charge was reported, so they are not plotted as a metered production price of zero. Sqwish reported ${k['cost']['known_usd']:.8f} for all 1342 questions (${k['cost']['known_usd_per_1000']:.5f} per 1000). Its 30-request/minute starter limit stretched batch duration, not the measured response time. Different providers, dates, hardware and admission limits remain confounds."),
      ('New image-capable candidates, not new image scores',
       'Current catalogs or author documentation declare image input for 16 of the 23 decision models, including Span-02, both Perplexity Deciders, both Liquid models and all three newcomers. The separate image benchmark has not changed. Text accuracy and latency do not establish image accuracy or image cost; the capability review records sources and distinguishes declared support from tested performance.'),
    ]


def overview_chart(s):
    ids=s['ranked_model_ids'];models=[s['models'][i] for i in ids];y=np.arange(len(ids))
    with plt.rc_context({'font.family':'DejaVu Sans','svg.fonttype':'none','svg.hashsalt':'direct-native-1342-20261020'}):
        fig,axs=plt.subplots(1,3,figsize=(16,15.3),sharey=True,gridspec_kw={'width_ratios':[1.2,1.1,1.1]})
        colors=[(0.95,0.83,0.42,.60) if mid in s['reference_model_ids'] else '#16728c' for mid in ids]
        bars=axs[0].barh(y,[100*m['accuracy'] for m in models],color=colors)
        for bar,mid in zip(bars,ids):
            if mid in s['reference_model_ids']:bar.set_edgecolor('#9c761c');bar.set_linewidth(1.1)
        axs[0].set_yticks(y,[readable.short(m['label']) for m in models],fontsize=11)
        axs[0].set_xlim(0,112);axs[0].set_xlabel('Correct first decisions (%)')
        for yy,m in zip(y,models):
            axs[0].text(100*m['accuracy']+1,yy,f"{m['accuracy']:.1%}",va='center',fontsize=10)
            sb=next((i for i,b in enumerate((250,500,1000)) if m['median_ms']<=b),3)
            axs[1].plot([m['median_ms'],m['p95_ms']],[yy,yy],color='#8a99a5',lw=1.3)
            axs[1].scatter(m['median_ms'],yy,color=PALETTES[sb],edgecolor='#364c60',s=70,zorder=3)
            axs[1].scatter(m['p95_ms'],yy,color='#35424d',marker='d',s=20,zorder=3)
            c=m['cost']
            if c.get('public_free_access'):
                axs[2].text(.04,yy,'Free public access*',transform=axs[2].get_yaxis_transform(),va='center',fontsize=10,
                    bbox=dict(facecolor='#edf1f5',edgecolor='none',pad=3))
            else:
                cb=next((i for i,b in enumerate((.01,.025,.05)) if c['known_usd_per_1000']<=b),3)
                axs[2].scatter(c['known_usd_per_1000'],yy,color=PALETTES[cb],edgecolor='#364c60',s=70)
                if c['unknown_attempts']:axs[2].text(c['known_usd_per_1000']*1.15,yy,'+ ?',va='center',fontsize=9)
        axs[1].set_xscale('log');axs[1].set_xlabel('Response time (ms, log scale)\nCircle: median · diamond: p95')
        axs[2].set_xscale('log');axs[2].set_xlabel('Metered/accounted cost per 1,000\nUSD, log scale; + ? = incomplete')
        axs[0].invert_yaxis()
        for ax,title in zip(axs,('Accuracy','Speed','Cost')):
            ax.set_title(title,fontsize=14,pad=18);ax.grid(axis='x',alpha=.2);ax.set_axisbelow(True)
            for spine in ax.spines.values():spine.set_visible(False)
        fig.suptitle('23 decision models and 3 high-end LLM references · 1,342 questions',fontsize=17,y=.98)
        fig.legend(handles=[Patch(facecolor='#16728c',label='Decision models'),
            Patch(facecolor=(.95,.83,.42,.60),edgecolor='#9c761c',label='No-reasoning LLM references')],
            loc='upper center',bbox_to_anchor=(.5,.957),ncol=2,frameon=False,fontsize=11)
        fig.text(.02,.023,'All first attempts. Fixed speed/cost bands; failures stay in the denominator. Qwen uses a prepaid-quota valuation, not cash billing.\n*Free public access is not a metered $0 price or a promise of production capacity. New direct routes: October 20, 2026; earlier measurements unchanged.\nDifferent providers, dates and account limits remain confounds. Rate/admission waits are excluded from response latency.',fontsize=10)
        fig.subplots_adjust(left=.30,right=.98,top=.91,bottom=.125,wspace=.36)
        for suffix in ('png','svg'):fig.savefig(DEST/('accuracy_speed_cost.'+suffix),dpi=160,metadata={'Date':None} if suffix=='svg' else {})
        plt.close(fig)


def categories_markdown(s,guide,details=False):
    text=readable.markdown_groups(s,guide,details)
    text=text.replace(readable.NAME,NAME).replace('All 20 models','All 26 routes').replace('all 20 models','all 26 routes')
    text=text.replace('https://etsabary.github.io/jev-1.14-comparison-benchmark/'+NAME+'/report.html',SITE)
    return text


def rebase(text,prefix):
    def link(match):
        attr,target=match.groups();u=urlsplit(target)
        if u.scheme or u.netloc or not u.path or u.path.startswith('/'):return match.group(0)
        path=posixpath.normpath(posixpath.join(prefix,u.path));assert not path.startswith('../')
        return attr+'="'+urlunsplit(('','',path,u.query,u.fragment))+'"'
    return re.sub(r'\b(href|src)="([^"]+)"',link,text)


def capability_markdown(s):
    c=json.loads((DEST/'image_capabilities.json').read_text())
    native=s['decision_model_ids'];refs=s['reference_model_ids']
    yes=sum(c['models'][mid]['image_input'] for mid in native)
    text=f'# Image input among the text-benchmarked models\n\nDocumentation review: October 20, 2026. **{yes} of {len(native)} specialized decision models declare image input.** This is a capability review, not a new image benchmark. No image inference was performed for this review.\n\n'
    rows=[]
    for mid in native+refs:
        v=c['models'][mid];status='Yes — documented' if v['image_input'] else 'No — current documented route'
        rows.append([s['models'][mid]['label'],s['model_kinds'][mid],status,f'[Source]({v["source"]})'])
    text+=table(['Model','Type','Image input','Evidence'],rows)
    text+='\nThe existing [200-question image benchmark](https://github.com/etsabary/visual-decision-benchmark) covers Jev 1.14, Luna Decisions and its separately labelled regular-LLM references. The other decision models above have not been assigned image scores here. Jev 1.13 is declared image-capable but was not part of that image comparison.\n\n'
    text+='The ordinary LLM references (Sol, Sonnet and Qwen) also accept images; their rows here remain text-only scores. [Official OpenAI model documentation](https://developers.openai.com/api/docs/models/gpt-6-sol) confirms Sol image input. Hyper Charm explicitly declares vision for the exact Qwen model used.\n\n'
    text+='Native support means actual image decoding, not OCR or a caption substituted into a text prompt. Nimble’s documented JSON state is read as text; sending an image-shaped JSON object and receiving HTTP 200 does not establish vision. Sqwish fat reads images; its core size is a different, text-only model. Image encoding and availability can depend on the route. No text score, text latency or text cost is repurposed as an image result.\n\n'
    text+='The dated [machine-readable review]('+NAME+'/image_capabilities.json) records source URLs and response hashes. [Current text benchmark](README.md).\n'
    return text


def exports(s,guide):
    write(DEST/'statistics.json',json.dumps(s,indent=2)+'\n')
    write(DEST/'category_guide.json',json.dumps(guide,indent=2)+'\n')
    out=io.StringIO(newline='');w=csv.writer(out)
    w.writerow(['category_id','category','questions']+[s['models'][mid]['label'] for mid in s['ranked_model_ids']])
    for fid in readable.LABELS:w.writerow([fid,readable.LABELS[fid],guide[fid]['questions']]+[readable.score(s['models'][mid]['families'][fid]) for mid in s['ranked_model_ids']])
    write(DEST/'category_scores.csv',out.getvalue())
    out=io.StringIO(newline='');w=csv.writer(out)
    w.writerow(['model_id','model','type','questions','correct','accuracy','mean_ms_if_measured',
        'median_ms','p95_ms','known_metered_or_accounted_cost_usd','known_cost_per_1000_usd',
        'unreported_charge_attempts','public_free_access','cost_scope','route','test_dates_toronto'])
    for mid in s['ranked_model_ids']:
        m=s['models'][mid];c=m['cost']
        w.writerow([mid,m['label'],s['model_kinds'][mid],m['n'],m['correct'],m['accuracy'],m.get('mean_response_ms',''),
            m['median_ms'],m['p95_ms'],c['known_usd'],c['known_usd_per_1000'],c['unknown_attempts'],bool(c.get('public_free_access')),
            c.get('scope','Captured charges or usage times captured tariff; see the unchanged prior evidence.'),
            m['route'],'; '.join(sorted(m['dates_toronto']))])
    write(DEST/'model_statistics.csv',out.getvalue())
    for group in readable.GROUPS:
        old_dest=readable.DEST;readable.DEST=DEST
        try:readable.plot(s,group)
        finally:readable.DEST=old_dest


def additions_table(s):
    return table(['October 20 addition','Correct /1342','Average (mean)','Median','p95','Actual 1342-question cost'],
        [[m['label'],f"{m['correct']}/1342 ({m['accuracy']:.1%})",f"{m['mean_response_ms']:.0f} ms",
          f"{m['median_ms']:.0f} ms",f"{m['p95_ms']:.0f} ms",price(mid,m,False)] for mid in NEW_IDS for m in [s['models'][mid]]])


def method(s):
    return [
      f"The full comparison covers 26 routes × 1342 questions = {26*1342:,} first attempts: 23 specialized decision models and three separately labelled high-end LLM references. The same 1342 inputs, facts and five choices retain their tested order. No existing model was rerun or removed for this update. There are {s['total_http_attempts']:,} selected HTTP attempts, including {s['total_recoveries']} permitted recoveries; the three October 20 runs account for 4026 first attempts and zero recoveries.",
      'Primary scores and latency use all first attempts. A valid wrong choice is never retried. One recovery is permitted only for transport failures or HTTP 408/429/5xx; its cost is included and its response cannot replace the first attempt in the ranking. Provider failures are unsuccessful delivered decisions, not classified as wrong reasoning choices.',
      'Median and p95 are computed from individual first-attempt times, never averages of stage medians. Timing runs from a fresh HTTPS connection through the complete response body, not time to first token. Deliberate admission, rate-limit and retry waits are excluded. The mean is also available for the three new runs. p95 is an interpolated 95th percentile, not the mean of the slowest 5%.',
      'The October 20 additions use direct provider APIs. Amos was paced below its public 60-request/minute cap. Sqwish starter access used one active request and 2.1-second start spacing after an account-limit amendment; the first 54 successful attempts remain included. Its response latency is not batch throughput. d3-turbo used up to two in flight. Previous routes, dates, loads and quantiles are unchanged. Different protocols, hosting hardware and account conditions are not controlled away.',
      'Among the earlier 20 decision routes, Nimble uses Bespoke directly and the others use OpenRouter with pinned providers and no fallback. Sol and Sonnet use OpenRouter; Qwen uses Hyper Charm. Sonnet requires the separately labelled JSON-choice grammar; its stopped bare-ID trial remains outside the scored comparison. Qwen requests reasoning_effort=none but has no reasoning-token telemetry. Tev1 is a decision-specialized generative model using a native adapter, not a claimed nongenerative architecture.',
      'All three new responses named the requested model and reported zero output tokens. The hosted names do not attest immutable weights or reveal internal implementation. No explanation generation, tool use, agentic iteration or answer-dependent repair was requested. This measures System 1-style choices, not unrestricted reasoning or general intelligence.',
      'Costs per 1000 are actual selected-run costs divided by 1342 and multiplied by 1000. Probe charges are separate. Sqwish charges come from every returned receipt and match the captured $0.06 per million input tokens; its exact full-bank charge is $0.02071056. d3-turbo and Amos used currently free public access, with no API-reported monetary charge; their metered price fields are null, not fabricated zeros. They have no cost-axis numeric point. Starter credit does not make Sqwish free.',
      'Earlier captured charges and usage-times-tariff accounting remain unchanged. + ? means additional unreported charges, not zero. Nimble retains its recorded mixed tariffs; Hyper Charm Qwen is a prepaid-quota valuation, not a cash invoice. Verification subscriptions are outside model-inference accounting. The total is not an independently reconciled financial invoice.',
      'This is a developing benchmark with dependent variants and uneven category sizes, not 1342 independent observations or a pristine held-out evaluation. The 37 author-development cases retain their permanent exclusion from a future held-out scored release and their separate 1305-case diagnostic. The complete developmental ranking remains 1342 questions for every route. Small score gaps do not establish a general intelligence ordering.',
      'The construction combines the corrected 1136-question bank, 200 verified expansion questions and six additional truth-teller questions into one score. The 31 categories and their question weights are unchanged. Each of F26–F31 has eight questions, so one answer changes a category score by 12.5 percentage points. Display groups are reading aids, not additional scored categories.',
      'All 206 expansion questions have current-revision blind Sol xhigh and different-model Opus or Argon checks, supplemented by exact computational evidence. The original bank received a targeted difficult-item audit, not independent external verification of every original question. Two retired ambiguous procedure questions are absent; their verified replacements appear once.',
      'All question inputs remain available without answer keys. Aggregate scores, categories, usage and costs are published; answer keys, item-level correctness, certificates, verifier responses, raw account data and credentials are not. Publication validators check consistency and privacy; public aggregates cannot reproduce private-key scoring or raw-latency pooling. The dated audit receipt binds the private evidence checks.',
      'Sixteen earlier regular-LLM configurations have only 1136-question coverage and are not extrapolated. Solar Decide remains excluded for latency; the distinct Solar Decide Flash remains included. No older published row was removed. The separate image benchmark is unchanged; documented image support is not an image score.'
    ]


def build_html(s,guide):
    old=(BASE/'report.html').read_text()
    head=old[:old.index('<body>')+6]
    head=head.replace('decision-models-with-llm-reference-points','october20-direct-additions-1342')
    head=re.sub(r'<title>.*?</title>','<title>System 1 Decision Benchmark: 26 routes, 1342 questions</title>',head)
    extra='.llm-reference>th{background:#fff6d5}.native-addition>th{border-left:4px solid #1684ac}.free-note{background:#edf1f5;padding:16px;border-radius:6px}.addition-note{background:#eaf5fb;padding:20px;border-radius:8px}.cost-incomplete{text-decoration:underline;text-decoration-color:#b7770b;text-underline-offset:4px}'
    head=head.replace('</style>',extra+'</style>',1)
    nav='<nav><a href="#overview">Overall results</a><a href="#new-additions">October 20 additions</a><a href="#llm-references">LLM references</a><a href="#functions">Named categories</a><a href="#image-support">Image input</a><a href="#method">Method</a></nav>'
    body='<main><h1>System 1 Decision Benchmark</h1><p>23 specialized decision models and 3 high-end LLM references on the same 1342 text questions across 31 categories. Updated October 20, 2026.</p>'+nav
    body+='<div class="cards"><div class="card"><div class="label">Leading decision model</div><div class="big">84.0%</div><div class="small">Respan Span-02 · 1127/1342</div></div><div class="card"><div class="label">Highest LLM reference score</div><div class="big">85.2%</div><div class="small">GPT-6 Sol, reasoning off · 1143/1342</div></div><div class="card"><div class="label">Complete matched coverage</div><div class="big">26 routes</div><div class="small">34,892 first attempts · 31 categories</div></div><div class="card"><div class="label">New direct providers</div><div class="big">3 additions</div><div class="small">d3-turbo · Amos Large · kettei-fat</div></div></div>'
    body+='<section id="overview"><h2>Accuracy, speed and cost: all 26 routes</h2><p>Every row covers 1342 first decisions. Blue accuracy bars are specialized decision models; translucent pale yellow bars are no-reasoning LLM reference points.</p><div class="figure"><a href="accuracy_speed_cost.svg"><img src="accuracy_speed_cost.png" alt="All 26 routes: full-bank accuracy, median and p95 response latency, and metered cost"></a></div>'+summary_html(s)
    body+='<p class="free-note">*Free public access is not an API-reported $0 monetary charge or a guarantee of free production capacity. d3-turbo and Amos have a labelled free-access entry, not a numeric point on the logarithmic price axis. For metered routes, per-1000 costs are normalized from the actual 1342-question run; + ? preserves unreported charges. Qwen is a prepaid-quota valuation, not additional out-of-pocket billing.</p>'+prior.legend_html()+'</section>'
    body+='<section id="new-additions"><h2>October 20 additions: d3-turbo, Amos and kettei-fat</h2><div class="addition-note"><p>All 4026 first attempts returned valid decisions. No retries, refusals, probability-format warnings or provider failures occurred.</p><div class="scroll"><table><thead><tr><th>Model</th><th>Correct / questions</th><th>Average (mean)</th><th>Median</th><th>p95</th><th>Actual run cost</th></tr></thead><tbody>'
    for mid in NEW_IDS:
        m=s['models'][mid];body+=f'<tr data-addition-model="{mid}"><th>{escape(m["label"])}</th><td>{m["correct"]}/1342 · {m["accuracy"]:.1%}</td><td>{m["mean_response_ms"]:.1f} ms</td><td>{m["median_ms"]:.1f} ms</td><td>{m["p95_ms"]:.1f} ms</td><td>{escape(price(mid,m,False))}</td></tr>'
    body+='</tbody></table></div><p>New tests: October 20, 2026 (America/Toronto). Earlier 23-route measurements are unchanged. Response times exclude deliberate rate-limit waits.</p></div>'
    body+=''.join('<h3>'+escape(t)+'</h3><p>'+escape(v)+'</p>' for t,v in findings(s))+'</section>'
    body+=prior.reference_section(s)
    native=re.search(r'<section id="analysis">.*?(?=<section id="functions">)',old,re.S).group()
    native=native.replace('What the 20 decision models show','Earlier decision-model findings, unchanged measurements')
    native=native.replace('Span has the lowest cost among routes with complete cost reporting.','Span has the lowest metered cost among routes with complete charge accounting. The two new free public endpoints are a separate access category.')
    body+=native
    body+=readable.clarity_section(s,guide).replace('All 20 models','All 26 routes').replace('all 20 models','all 26 routes')
    qrows=[]
    for mid in s['ranked_model_ids']:
        m=s['models'][mid];qrows.append('<tr><th>'+escape(m['label'])+'</th>'+''.join('<td>'+str(m[k])+'</td>' for k in ('answered','wrong_valid','provider_failures','model_output_failures','recoveries'))+f'<td>{m["eventual"]["correct"]}</td></tr>')
    body+='<section id="quality"><h2>Delivered decisions and failures</h2><div class="scroll"><table><thead><tr><th>Model</th><th>Usable first</th><th>Wrong valid</th><th>Provider failures</th><th>Output failures</th><th>Recoveries</th><th>Eventual correct</th></tr></thead><tbody>'+''.join(qrows)+'</tbody></table></div><p>Sonnet’s stopped bare-ID trial remains separate: 26/110 usable, 84 unusable. Its complete JSON-choice run is the ranked row. Qwen quota rejections remain unsuccessful deliveries in its primary denominator.</p></section>'
    body+='<section id="image-support"><h2>Which decision models accept images?</h2><p>Current documentation declares image input for <b>16 of the 23 decision models</b>, including all three new additions. This text report assigns no image accuracy, latency or cost to them. The existing image benchmark is unchanged.</p><p><a href="../IMAGE_CAPABILITIES.md">Full model-by-model capability list and sources</a> · <a href="image_capabilities.json">Dated source review (JSON)</a> · <a href="https://github.com/etsabary/visual-decision-benchmark">Separate image benchmark</a></p></section>'
    body+='<section id="method"><h2>Method, accounting and limits</h2>'+''.join('<p>'+escape(p)+'</p>' for p in method(s))+'</section>'
    body+='<section id="downloads"><h2>Questions, statistics and audit</h2><p><a href="statistics.json">26-route aggregate statistics</a> · <a href="model_statistics.csv">Model CSV</a> · <a href="category_scores.csv">Named-category CSV</a> · <a href="audit_receipt.json">Sanitized audit receipt</a> · <a href="manifest.json">Release manifest</a> · <a href="report.txt">Plain-text findings</a></p><p>Unchanged, answer-free question bank: <a href="../consolidated_2026-10-19/questions_1342.csv">CSV</a> · <a href="../consolidated_2026-10-19/questions_1342.jsonl">Exact native inputs (JSONL)</a> · <a href="../consolidated_2026-10-19/questions_1342.txt">Readable text</a>.</p></section></main></body></html>\n'
    html=head+body
    # Markdown is offered as a normal repository link, not a missing Pages file.
    html=html.replace('href="../IMAGE_CAPABILITIES.md"','href="https://github.com/etsabary/system-1-decision-benchmark/blob/main/IMAGE_CAPABILITIES.md"')
    return html


def build():
    assert not (DEST/'release_checksums.json').exists(),'Never overwrite a sealed publication'
    archive.archive();s,guide=load();DEST.mkdir(exist_ok=True)
    capabilities=json.loads((DEST/'image_capabilities.json').read_text())
    assert set(capabilities['models'])==set(s['models'])
    assert sum(capabilities['models'][mid]['image_input'] for mid in s['decision_model_ids'])==16
    exports(s,guide);overview_chart(s)
    write(repo_file('IMAGE_CAPABILITIES.md', root=ROOT),capability_markdown(s))
    write(DEST/'report.html',build_html(s,guide))
    native=previous_path(repo_file('README.md', root=ROOT)).read_text()
    native=native[native.index('## What this measures'):native.index('## Category scores and explanations')]
    native=native.replace('Span has the lowest cost among routes with complete cost reporting.','Span has the lowest metered cost among routes with complete charge accounting. The new free public endpoints are a separate access category.')
    intro='# System 1 Decision Benchmark\n\n23 specialized decision models and 3 high-end LLM references on 1,342 text questions.\n\nUpdated October 20, 2026. Added complete d3-turbo, Amos Large and Sqwish kettei-fat runs; all earlier measurements are unchanged.\n\n'
    intro+='**Respan Span-02 remains the leading specialized decision model at 1127/1342 (84.0%). Newcomer d3-turbo is fourth at 1106/1342 (82.4%); Amos Large and kettei-fat score 80.0% and 79.4%.**\n\n'
    intro+='[Interactive report]('+SITE+') · [New findings]('+SITE+'#new-additions) · [Named, color-coded categories]('+SITE+'#functions) · [Which models read images?](IMAGE_CAPABILITIES.md).\n\n![All 26 routes: accuracy, speed and cost]('+NAME+'/accuracy_speed_cost.png)\n\n'
    intro+='## Results, speed and cost\n\nEvery row covers 1342 first attempts. Per-1000 costs are normalized; actual 1342-question totals are separate. Free public access is not a metered production price of zero. Qwen’s amount is a prepaid-quota valuation, not a cash invoice. + ? means additional unreported charges.\n\n'
    intro+=table(['Model','Type','Correct /1342','Accuracy','Median','p95','Cost per 1000','Actual 1342-question cost'],all_rows(s))+'\n'
    intro+='*d3-turbo and Amos currently provide free public access. No monetary charge was reported; their metered cost fields are null and no numeric price point is plotted. This is not a guarantee of free production capacity.*\n\n'
    intro+=legend_markdown().replace('each actual 1,136-question run','each actual 1,342-question run')+'\n'
    intro+='## October 20 additions\n\n'+additions_table(s)+'\nAll three completed 1342 first attempts, without failures, recoveries or probability warnings. Rate-limit waits are excluded from response times.\n\n'
    narrative='\n\n'.join('## '+t+'\n\n'+v for t,v in findings(s))+'\n\n'
    refs='\n\n'.join('## '+t+'\n\n'+v for t,v in prior.analysis_text(s))+'\n\n'
    end='## Questions, statistics and method\n\nAll 1342 question inputs are unchanged and remain available without answers: [CSV](consolidated_2026-10-19/questions_1342.csv), [exact native JSONL](consolidated_2026-10-19/questions_1342.jsonl), [readable text](consolidated_2026-10-19/questions_1342.txt).\n\n'
    end+='Current exports: [model CSV]('+NAME+'/model_statistics.csv), [named-category CSV]('+NAME+'/category_scores.csv), [aggregate JSON]('+NAME+'/statistics.json), [sanitized audit receipt]('+NAME+'/audit_receipt.json), [manifest]('+NAME+'/manifest.json), [plain-text findings]('+NAME+'/report.txt).\n\n'
    end+='[Request failures and output compliance](OUTPUT_COMPLIANCE.md) · [Image capability review](IMAGE_CAPABILITIES.md) · [Earlier 1136-question comparison](REFERENCE_1136.md) · [Separate image benchmark](https://github.com/etsabary/visual-decision-benchmark).\n\n'
    end+='\n\n'.join(method(s))+'\n\n## Offline publication checks\n\nRun `python3 validate_direct_release.py`, `python3 repo_identity.py` and `python3 -m unittest discover -p "test_*.py"` with `requirements-reports.txt` and `python-dotenv` installed. These checks make no inference calls. Earlier dated releases and seals remain available unchanged.\n'
    write(repo_file('README.md', root=ROOT),intro+narrative+refs+native+categories_markdown(s,guide)+end)
    write(repo_file('FUNCTIONS.md', root=ROOT),'# All 31 categories: 23 decision models and 3 LLM references\n\nSame 1342 questions, first-attempt scores. [Color-coded tables]('+SITE+'#functions).\n\n'+categories_markdown(s,guide,True))
    write(repo_file('OUTPUT_COMPLIANCE.md', root=ROOT),'# Delivered decisions and request failures\n\nAll 26 routes retain the complete 1342 first-attempt denominator. Wrong valid choices are distinct from provider and output failures. No answer-dependent retries.\n\n'+prior.quality(s)+'\n\nThe October 20 additions returned 4026 usable first decisions with zero recoveries and zero probability-format warnings. Sonnet’s separate bare-ID trial is not pooled into its complete constrained-format score. Qwen’s first-attempt quota/transport failures remain in the ranking.\n')
    write(DEST/'report.txt','\n\n'.join(t.upper()+'\n'+v for t,v in findings(s))+'\n\n'+table(['Model','Type','Correct','Accuracy','Median','p95','Cost/1000','Actual run cost'],all_rows(s))+'\n\nMETHOD\n'+'\n\n'.join(method(s))+'\n')
    receipt=dict(status='VERIFIED_COMPLETE_DIRECT_1342',question_count=1342,added_model_count=3,
        primary_attempts=4026,recoveries=0,unusable_responses=0,probability_warnings=0,
        bank_sha256=prior.BANK_HASH,source_summary_sha256=s['direct_source_summary_sha256'],
        evidence_sha256=s['direct_evidence_bindings'],scoring_binding_sha256=s['direct_scoring_authority_sha256'],
        source_analysis_sha256=s['direct_analysis_source_sha256'],
        private_check='Reconciled dispatch, attempt and result journals; software seals, returned model IDs, zero output tokens, raw timing quantiles and charge sums match the sealed analysis. Private answer-key scoring is not reproduced by this public export.',
        new_input='Same frozen question bank and five options; no new inference for publication.',
        cost_policy='Free public access is separately labelled; no invented API-reported zero. Sqwish charges are provider-reported.',
        privacy='Aggregate results and hashes only; no answer keys, item-level correctness, raw account data or credentials.')
    write(DEST/'audit_receipt.json',json.dumps(receipt,indent=2)+'\n')
    manifest=dict(version='october20-direct-decisions-publication-v1',question_count=1342,model_count=26,
        decision_model_count=23,llm_reference_count=3,category_count=31,bank_sha256=prior.BANK_HASH,
        prior_statistics_sha256=s['prior_statistics_sha256'],prior_release_seal_sha256=digest(BASE/'release_checksums.json'),
        added_models=list(NEW_IDS),earlier_models_unchanged=True,
        artifacts={p.name:digest(p) for p in sorted(DEST.iterdir()) if p.is_file() and p.name not in ('manifest.json','release_checksums.json')})
    write(DEST/'manifest.json',json.dumps(manifest,indent=2)+'\n')
    pages=repo_file('docs', root=ROOT)/NAME;pages.mkdir(parents=True,exist_ok=True)
    for p in DEST.iterdir():
        if p.is_file() and p.name!='release_checksums.json':shutil.copyfile(p,pages/p.name)
    write(repo_file('docs/report.html', root=ROOT),rebase((DEST/'report.html').read_text(),NAME))
    for name,anchor in (('index.html',''),('functions.html','#functions'),('output_compliance.html','#quality')):
        write(repo_file('docs', root=ROOT)/name,'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="benchmark-cohort" content="october20-direct-additions-1342"><meta http-equiv="refresh" content="0;url=report.html'+anchor+'"><title>System 1 Decision Benchmark</title></head><body><a href="report.html'+anchor+'">Current 26-route benchmark</a></body></html>\n')
    print('Built 26 full-bank rows and 806 category cells; earlier 23 measurements unchanged; no inference or Git operation.')


def hashes():
    from archive_october21_presentation import previous
    paths={repo_file(n, root=ROOT) for n in ACTIVE}
    for folder in (DEST,repo_file('docs', root=ROOT)/NAME,archive.ARCHIVE):
        paths.update(p for p in folder.rglob('*') if p.is_file() and p.name!='release_checksums.json')
    return {str(logical_relative(p, root=ROOT)):digest(previous(p)) for p in sorted(paths)}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--seal',action='store_true');args=parser.parse_args()
    if args.seal:
        from validate_direct_release import validate
        validate();assert not (DEST/'release_checksums.json').exists()
        write(DEST/'release_checksums.json',json.dumps(hashes(),indent=2)+'\n')
    else:build()
