"""Offline publication of the completed GLiDE capture. Never calls a provider.

Prior dated releases and all 29 earlier model records remain unchanged.
The private aggregate was scored before publication; no answer key is loaded here.
"""
import argparse
from collections import Counter
from copy import deepcopy
from decimal import Decimal
from hashlib import sha256
from html import escape
import json
from pathlib import Path
import re
import shutil

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import numpy as np

import decision_refresh as d
import fastino_glide_2026_10_23 as run
import publish_october21_additions as prior
import build_readable_report as readable
from build_october18_report import PALETTES, legend_markdown
from publish_consolidated_report import table
from repo_layout import repo_file

ROOT = run.ROOT
NAME = 'fastino_2026-10-23'
DEST = ROOT/'results/releases'/NAME
PRIVATE = run.OUT/'analysis/94a8a3cda795c060/statistics.json'
SITE = 'https://etsabary.github.io/system-1-decision-benchmark/report.html'
LABEL = 'Fastino GLiDE'
MID = 'fastino_glide'
PREVIOUS_DEST = prior.DEST
ORIGINAL_PRICE = prior.price


def digest(path):
    return sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(value.rstrip()+'\n',encoding='utf-8')


def capture_sources():
    """Preserve exact executed revisions before portability/layout-only edits."""
    for kind in ('text','image'):
        out = run.OUT/kind
        for name,h in json.loads((out/'software.json').read_text()).items():
            source = run.VISUAL/name[7:] if name.startswith('visual/') else ROOT/name
            target = out/'software_capture'/(name+'.snapshot')
            if target.exists():
                assert digest(target)==h,name
            else:
                assert digest(source)==h,name
                target.parent.mkdir(parents=True,exist_ok=True)
                shutil.copyfile(source,target)
    archive = ROOT/'scripts/legacy_layout'
    manifest = ROOT/'scripts/layout_manifest.json'
    layout = json.loads(manifest.read_text())
    for name in ('docs/report.html','docs/index.html','docs/functions.html','docs/output_compliance.html'):
        entry = layout['preserved_sources'].get(name)
        if entry:
            assert digest(ROOT/entry['archive_path'])==entry['sha256']
            continue
        source = ROOT/name
        target = archive/(name+'.snapshot')
        assert not target.exists()
        target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(source,target)
        layout['preserved_sources'][name]=dict(archive_path=target.relative_to(ROOT).as_posix(),sha256=digest(source))
    # Updating a generated source-location registry is mechanical, not a new seal.
    write(manifest,json.dumps(layout,indent=2))


def verify_capture(kind):
    out = run.OUT/kind
    seal = json.loads((out/'completion.json').read_text())
    assert seal['status']=='COMPLETE'
    for name,h in seal['files_sha256'].items():
        assert digest(out/name)==h,name
    for name,h in json.loads((out/'software.json').read_text()).items():
        assert digest(out/'software_capture'/(name+'.snapshot'))==h,name
    manifest = json.loads((out/'manifest.json').read_text())
    rows = d.rows(out/'attempts.jsonl')
    results = d.rows(out/'results.jsonl')
    done = d.reconcile(d.rows(out/'dispatches.jsonl'),rows,results,manifest['request_plan'])
    assert len(done)==(1342 if kind=='text' else 200)
    assert len(rows)==len(results)==len(done)
    assert all(r['attempt']==1 and r['status']=='ok' and r['model_returned']=='glide_v2' for r in rows)
    assert all(r['usage']['output_tokens']==0 and r['response_headers']['x-fastino-data-retention']=='not-stored' for r in rows)
    assert all(r['probabilities_valid'] for r in rows)
    # Current semantic reconstruction is checked against the captured wire bytes;
    # source relocation cannot silently change a question or image.
    if kind=='text':
        qs,_ = run.text_bank.prepare()
        assets = {}
    else:
        qs,assets,_ = run.image_bank().inputs()
    indexed = {p['request_index']:p for p in manifest['request_plan']}
    for row in rows:
        assert all(row[k]==v for k,v in indexed[row['request_index']].items())
        body = run.payload(qs[row['item_id']],kind,assets)
        assert d.digest(body)==row['request_payload_sha256']
        assert len(d.canonical(body))==row['request_body_bytes']
        assert all(row[k]==v for k,v in run.parse(row,set(body['questions']['decision']['criteria'])).items())
    return rows


def load():
    private = json.loads(PRIVATE.read_text())
    records = {kind:verify_capture(kind) for kind in ('text','image')}
    for kind,rows in records.items():
        s = private['groups'][kind]
        assert s['complete'] and s['n']==len(rows)
        assert private['ledger_sha256'][kind]==digest(run.OUT/kind/'attempts.jsonl')
        assert run.stats.quantiles([r['latency_ms'] for r in rows])['median_ms']==s['median_ms']
        assert run.stats.quantiles([r['latency_ms'] for r in rows])['p95_ms']==s['p95_ms']
        amount = sum((Decimal(r['usage']['input_tokens'])*run.RATE for r in rows),Decimal(0))
        assert amount==Decimal(s['cost']['exact_decimal'])
    old = json.loads((prior.DEST/'statistics.json').read_text())
    s = deepcopy(old)
    v = private['groups']['text']
    c = dict(v['cost'],known_decimal=v['cost']['exact_decimal'],exact_usd=v['cost']['known_usd'],
        known_usd_per_1000=v['cost']['known_usd']/1342*1000,public_free_access=False,
        scope='Reported input-token usage times captured $0.04/M tariff; not API-reported monetary receipts',
        source='usage_times_published_tariff',api_reported_usd=None,api_missing_receipts=1342)
    model = dict(model_id=MID,label=LABEL,n=1342,correct=v['correct'],answered=1342,wrong_valid=1342-v['correct'],
        failed=0,accuracy=v['accuracy'],accuracy_among_usable=v['accuracy'],mean_response_ms=v['mean_ms'],
        median_ms=v['median_ms'],p95_ms=v['p95_ms'],attempts=1342,recoveries=0,first_statuses={'ok':1342},
        provider_failures=0,model_output_failures=0,probability_warnings=0,eventual=v['eventual'],cost=c,
        families=v['families'],dates_toronto=v['dates_toronto'],returned_identities=v['returned_identities'],
        providers={'Fastino direct':1342},route='Direct → Fastino → fastino/GLiDE → glide_v2',
        output_token_values=v['output_token_values'],input_tokens=v['input_tokens'],new_domains=v['new_domains'],
        release_exclusion_diagnostic=v['release_exclusion_diagnostic'],original_1136=v['original_1136'],added_206=v['added_206'],
        catalog_description=v['metadata']['model']['description'],version_limit=private['version_note'],
        compatibility=v['probe'],macro_family_accuracy=sum(f['accuracy'] for f in v['families'].values())/31)
    s['models'][MID]=model
    s['model_kinds'][MID]='Decision model'
    s['ranked_model_ids']=sorted(s['models'],key=lambda mid:(-s['models'][mid]['correct'],mid))
    s['decision_model_ids']=[m for m in s['ranked_model_ids'] if m not in s['reference_model_ids']]
    s.update(status='COMPLETE_27_DECISION_PLUS_3_LLM_REFERENCES_1342',model_count=30,decision_model_count=27,
        primary_cases=40260,all_tested_primary_cases=40260,updated_date_toronto='2026-10-23',added_model_ids=[MID],
        prior_statistics_sha256=digest(prior.DEST/'statistics.json'),
        total_http_attempts=sum(m['attempts'] for m in s['models'].values()),
        total_recoveries=sum(m['recoveries'] for m in s['models'].values()))
    assert all(s['models'][mid]==m for mid,m in old['models'].items())
    guide = json.loads((prior.DEST/'category_guide.json').read_text())
    return s,guide,private,records


def price(mid,m,normalized=True):
    value = ORIGINAL_PRICE(mid,m,normalized)
    return '~'+value if mid==MID else value


def findings(s):
    m=s['models'];f=m[MID];sol=m['reference_sol'];span=m['respan02']
    return [
        ('Fastino has the highest observed text score, not the highest image score',
         'Fastino GLiDE answered 1154/1342 correctly (86.0%), ahead of GPT-6 Sol without reasoning at 1143 (85.2%), Mammoth-1 at 1139 (84.9%), and Span-02 and Drex Max at 1127 each (84.0%). The gaps are 11 and 15 answers against Sol and Mammoth. These scores describe this developing bank and do not establish a reliable universal intelligence ordering. On the separate image bank, GLiDE scored 158/200 (79.0%): second, one answer behind Amos at 159/200. Text and image percentages are not combined.'),
        ('A short response time and a metered price below the Sol reference',
         f"GLiDE’s mean / median / p95 text response was 343/213/802 ms. Sol’s median was 1023 ms: {sol['median_ms']/f['median_ms']:.1f} times GLiDE’s measured median. GLiDE’s usage-based cost was $0.01739196 for the complete bank, or $0.01296 per 1000 questions; Sol’s API-reported total was $0.84829450, about {sol['cost']['known_usd']/f['cost']['known_usd']:.1f} times as much. Span’s median was slightly shorter at 206 ms, and its recorded cost was lower at $0.00474628. GLiDE is not the cheapest or fastest entry. These are different dated routes, not controlled hardware measurements. Fastino cost is calculated from reported input tokens and the captured tariff, not a returned monetary receipt."),
        ('Truth-tellers separate GLiDE from the nearby leaders',
         'GLiDE scored 59/74 on truth-tellers and liars: deciding which assignments of truth and falsehood make all the supplied statements consistent. Span scored 55/74, Mammoth 48/74 and Sol 38/74. On exact truth counting—how many supplied claims are true—GLiDE scored 45/71, versus Span 46/71 and Sol 51/71. These are distinct operations: being better at assigning truth-tellers does not make GLiDE best at counting true claims.'),
        ('Strong rules and evidence, with a specific state-update weakness',
         'GLiDE answered all 52 rule-counterexample questions correctly, 51/52 required-condition questions, 45/46 if-then questions and 41/42 interval comparisons. Required-condition questions ask whether every prerequisite holds; counterexamples ask which case breaks a stated rule. Its one-to-one assignments score was 63/67, versus Mammoth’s 64/67 and Drex Max’s 65/67. Ordered procedures remained 18/48 (37.5%), the same as Mammoth and Sol and below Span’s 33/48. Those questions require applying each edit to the current state in order, not recognizing a plausible end state. Tracking swaps gave GLiDE 31/52.'),
        ('The new categories do not follow the overall ranking',
         'Across the six eight-question categories covering risk, information value, worst-case choice, strategic response, concurrent operations and information leaks, GLiDE scored 29/48. Sol scored 36/48, Span 34/48 and Mammoth 30/48. GLiDE scored 3/8 on whether extra information is worth paying for, and 4/8 on worst-case choices without supplied probabilities; Span scored 8/8 on the latter. Each category has only eight questions, so one answer changes its score by 12.5 percentage points. The category profiles identify different useful routes rather than one uniformly best model.'),
        ('The harder additions remain harder for GLiDE',
         'GLiDE scored 1028/1136 (90.5%) on the original portion and 126/206 (61.2%) on the additions. These are descriptive slices of the same unweighted 1342-question score, not separate leaderboards. All existing questions, options, audits and category weights are unchanged. No older model was rerun or re-scored for this addition.'),
        ('The served version and image support were checked, not assumed',
         'The request model is fastino/GLiDE. The authenticated live catalog described a one-pass GLiDE v2.2 deployment; every scored response identified glide_v2. This is a hosted alias, not an immutable-weight attestation, and it must not be labelled v1.2. The catalog image flag was false while the documentation described image parts; real single-image and three-image probes succeeded, followed by the full 200-image run. No OCR or captions replaced pixels. All 1542 scored calls returned usable typed decisions, with no retries, valid probability distributions, zero reported output tokens and not-stored retention headers. That telemetry does not independently reveal undisclosed internal computation.'),
        ('Earlier model profiles and price qualifications remain available',
         'Mammoth remains the next-highest specialized text model at 1139/1342. Drex Max and Span tie at 1127, but Drex’s one-to-one assignments score is 65/67 and Span’s procedure score is 33/48. Elephant’s 1004/1342 remains below Jev 1.14’s 1030/1342. Baseten’s captured promotional free access and Amos/d3 public-free access are not API-reported metered prices of zero. The 29 earlier model records and their dated release seals are preserved exactly; their tests were not repeated to create this update.'),
    ]


def methods():
    return [
        '30 full-bank routes: 27 specialized decision models and three selected no-reasoning LLM references. Each has 1342 questions across 31 categories: 40,260 first attempts. Fastino was measured October 23, 2026 (America/Toronto); earlier rows retain their own test dates, routes and raw measurements.',
        'Same frozen answer-free question bank, original options, native input and seed 2026101906. Every first attempt remains in the accuracy and latency denominator. One recovery is permitted only for transport failures or HTTP 408/429/5xx; Fastino additionally prespecified the documented HTTP 425 warming condition. No recovery was needed. No answer-dependent retries, batching of independent cases or provider fallback.',
        'Fastino used two text requests per barrier wave and serial image requests. The text and image streams overlapped, with up to three Fastino calls globally. Timing starts before a fresh HTTPS connection and ends after the complete response body; encoding, queue, pacing and retry waits are excluded. The predeclared cumulative median cutoff is above 2000 ms after at least 20 questions. Provider hardware, load, dates and account limits remain confounds; these are observed route response times, not isolated inference throughput.',
        'Fastino returned no monetary receipts. Its $0.04 per million input-token and $0 output tariff was captured from the authenticated catalog and documentation. Core text cost is $0.01739196; its separate text admission probe cost $0.00000364. Image core cost is $0.00767264 and two image probes cost $0.00010484. The combined usage-based cost including all probes was $0.02517308. Per-1000 values normalize actual bank totals; no extra 1000-question runs were made. Earlier missing charges remain unknown, not zero.',
        'Native Fastino requests used store:false; all scored receipts reported not-stored retention. The response identity glide_v2 and catalog v2.2 description are recorded. Internal execution and immutable weights are not independently attested. LLM references retain their original protocol labels: Sol explicit reasoning off, Sonnet constrained JSON choice after a separate failed bare-ID trial, and Qwen none with missing reasoning-token telemetry not called zero.',
        'This is a developing benchmark with uneven category sizes and dependent variants, not 1342 independent observations or a pristine held-out evaluation. The 37 permanent author-development exclusions retain their separate 1305-case diagnostic. Two audited ambiguous originals were replaced before these runs. The additions retain their verification evidence; the original bank received a targeted difficult-item audit rather than independent external verification of every original answer.',
        'Answer keys, per-item correctness, raw account state and credentials stay outside public exports. Private frozen-key scoring, input reconstruction, full-ledger reconciliation, quantiles and exact-decimal cost sums were checked before publication. Public aggregate checks cannot independently reproduce answer correctness without the external reference key. Text and image banks remain separate.'
    ]


def overview(s):
    ids=s['ranked_model_ids'];models=[s['models'][m] for m in ids];y=np.arange(len(ids))
    band=lambda v,limits:next((i for i,b in enumerate(limits) if v<=b),3)
    with plt.rc_context({'font.family':'DejaVu Sans','svg.fonttype':'none','svg.hashsalt':'fastino-1342-20261023'}):
        fig,axes=plt.subplots(1,3,figsize=(16,17.2),sharey=True,gridspec_kw={'width_ratios':[1.2,1.1,1.1]})
        colors=[(.95,.83,.42,.60) if mid in s['reference_model_ids'] else '#16728c' for mid in ids]
        bars=axes[0].barh(y,[m['accuracy']*100 for m in models],color=colors)
        for bar,mid in zip(bars,ids):
            if mid in s['reference_model_ids']:bar.set_edgecolor('#9c761c')
        axes[0].set_yticks(y,[readable.short(m['label']) for m in models],fontsize=11)
        axes[0].set_xlim(0,112);axes[0].invert_yaxis();axes[0].set_xlabel('Correct first decisions (%)')
        for yy,mid,m in zip(y,ids,models):
            axes[0].text(100*m['accuracy']+1,yy,f"{m['accuracy']:.1%}",va='center',fontsize=10)
            axes[1].plot([m['median_ms'],m['p95_ms']],[yy,yy],color='#8999a5')
            axes[1].scatter(m['median_ms'],yy,color=PALETTES[band(m['median_ms'],(250,500,1000))],s=65,edgecolor='#364c60')
            axes[1].scatter(m['p95_ms'],yy,color='#35424d',marker='d',s=20)
            c=m['cost']
            if c.get('public_free_access'):
                axes[2].text(.03,yy,'Promotional free*' if mid in ('mammoth1','elephant1') else 'Free public access*',
                    transform=axes[2].get_yaxis_transform(),va='center',fontsize=10,bbox=dict(facecolor='#edf1f5',edgecolor='none',pad=3))
            else:
                axes[2].scatter(c['known_usd_per_1000'],yy,color=PALETTES[band(c['known_usd_per_1000'],(.01,.025,.05))],s=65,edgecolor='#364c60')
                if c['unknown_attempts']:axes[2].text(c['known_usd_per_1000']*1.15,yy,'+ ?',va='center')
        axes[1].set_xscale('log');axes[2].set_xscale('log')
        axes[1].set_xlabel('Response time (ms, log scale)\nCircle: median · diamond: p95')
        axes[2].set_xlabel('Metered/accounted cost per 1,000\nUSD, log scale; + ? = incomplete')
        for ax,title in zip(axes,('Accuracy','Speed','Cost')):
            ax.set_title(title,fontsize=14,pad=18);ax.grid(axis='x',alpha=.2);ax.set_axisbelow(True)
            for spine in ax.spines.values():spine.set_visible(False)
        fig.suptitle('27 decision models and 3 high-end LLM references · 1,342 questions',fontsize=17,y=.98)
        fig.legend(handles=[Patch(facecolor='#16728c',label='Decision models'),Patch(facecolor=(.95,.83,.42,.60),edgecolor='#9c761c',label='No-reasoning LLM references')],loc='upper center',bbox_to_anchor=(.5,.957),ncol=2,frameon=False)
        fig.text(.02,.025,'All first attempts; fixed speed/cost bands. Fastino: October 23, 2026; earlier measurements unchanged.\nFastino cost is usage × captured tariff, not monetary receipts. Free access is not a metered production price.\nDifferent dates, providers and loads remain confounds. Small accuracy gaps do not establish a reliable general ordering.',fontsize=10)
        fig.subplots_adjust(left=.30,right=.98,top=.91,bottom=.12,wspace=.36)
        for suffix in ('png','svg'):fig.savefig(DEST/('accuracy_speed_cost.'+suffix),dpi=160,metadata={'Date':None} if suffix=='svg' else {})
        plt.close(fig)


def categories(s,guide,details=False):
    value=readable.markdown_groups(s,guide,details)
    value=value.replace('All 20 models','All 30 routes').replace('all 20 models','all 30 routes')
    value=value.replace(readable.NAME,NAME)
    value=re.sub(r'https://etsabary.github.io/jev-1.14-comparison-benchmark/[^)# ]+/report.html',SITE,value)
    return value


def html(s,guide):
    old=(PREVIOUS_DEST/'report.html').read_text();head=old[:old.index('<body>')+6]
    head=re.sub(r'<title>.*?</title>','<title>System 1 decisions: 30 routes, 1,342 questions</title>',head)
    head=head.replace('october21-additions-1342','fastino-october23-1342')
    body='<main><h1>System 1 Decision Benchmark</h1><p>27 specialized decision models and 3 high-end LLM references. Same 1,342 text questions, 31 categories. Updated October 23, 2026.</p>'
    body+='<nav><a href="#overview">Overall results</a><a href="#new-additions">Fastino findings</a><a href="#llm-references">LLM references</a><a href="#functions">Named categories</a><a href="#method">Method</a></nav>'
    body+='<div class="cards"><div class="card"><div class="label">Highest observed text score</div><div class="big">86.0%</div><div class="small">Fastino GLiDE · 1154/1342</div></div><div class="card"><div class="label">Highest LLM reference</div><div class="big">85.2%</div><div class="small">GPT-6 Sol, reasoning off · 1143/1342</div></div><div class="card"><div class="label">Matched question coverage</div><div class="big">30 routes</div><div class="small">40,260 first attempts · 31 categories</div></div><div class="card"><div class="label">Fastino: separate image bank</div><div class="big">79.0%</div><div class="small">Second · 158/200; Amos 159/200</div></div></div>'
    body+='<section id="overview"><h2>Accuracy, speed and cost: all 30 routes</h2><p>Blue bars: decision models. Pale yellow: no-reasoning LLM references. Every row covers 1,342 first attempts. ~ marks Fastino’s usage-based tariff calculation, not monetary receipts.</p><div class="figure"><a href="accuracy_speed_cost.svg"><img src="accuracy_speed_cost.png" alt="30 routes: accuracy, speed and cost; Fastino leads measured text accuracy"></a></div>'+prior.summary_html(s)+prior.prior.prior.legend_html()+'</section>'
    body+='<section id="new-additions"><h2>October 23: Fastino GLiDE</h2><p>Catalog: one-pass GLiDE v2.2. Request: fastino/GLiDE. Returned identity: glide_v2. Hosted alias, not immutable weights. All 1,342 text decisions were usable; zero retries.</p>'
    body+=''.join('<h3>'+escape(title)+'</h3><p>'+escape(text)+'</p>' for title,text in findings(s))+'</section>'
    body+='<section id="llm-references"><h2>High-end LLM references, reasoning off</h2><p>These three selected routes demonstrate the measured level of immediate decisions alongside generative models; they are not an exhaustive LLM ranking. Sol uses explicit reasoning off. Sonnet uses a separately constrained JSON-choice schema; its earlier failed bare-ID trial is not pooled. Qwen uses none, but missing reasoning-token telemetry is not called zero. Original failures remain unsuccessful first deliveries.</p></section>'
    body+=readable.clarity_section(s,guide).replace('All 20 models','All 30 routes').replace('all 20 models','all 30 routes')
    body+='<section id="quality"><h2>Delivered decisions and failures</h2>'+prior.markdown.markdown(prior.prior.prior.quality(s),extensions=['tables'])+'</section>'
    body+='<section id="image-support"><h2>Image decisions remain a separate comparison</h2><p>GLiDE completed all 200 native-image questions at 79.0%. It ranks second behind Amos’s 79.5%, not first in both banks. <a href="https://etsabary.github.io/visual-decision-benchmark/report.html">Image report, named categories and costs</a>.</p></section>'
    body+='<section id="method"><h2>Method, cost and measurement limits</h2>'+''.join('<p>'+escape(p)+'</p>' for p in methods())+'</section>'
    body+='<section id="downloads"><h2>Questions, data and audit</h2><p><a href="statistics.json">30-route aggregate JSON</a> · <a href="model_statistics.csv">Model CSV</a> · <a href="category_scores.csv">Category CSV</a> · <a href="audit_receipt.json">Audit receipt</a> · <a href="manifest.json">Release manifest</a> · <a href="report.txt">Plain-text findings</a>.</p><p>Unchanged questions: <a href="../consolidated_2026-10-19/questions_1342.csv">CSV</a> · <a href="../consolidated_2026-10-19/questions_1342.jsonl">Native JSONL</a> · <a href="../consolidated_2026-10-19/questions_1342.txt">Readable text</a>.</p></section></main></body></html>'
    return head+body


def build():
    assert not (DEST/'manifest.json').exists(),'Use a new release for changed published evidence'
    s,guide,private,records=load();DEST.mkdir(parents=True,exist_ok=True)
    original=(prior.DEST,prior.NAME,prior.NEW,prior.price)
    try:
        # Presentation helpers only; no dated artifact or source is rewritten.
        prior.DEST,prior.NAME,prior.NEW,prior.price=DEST,NAME,(MID,),price
        prior.exports(s,guide);overview(s);page=html(s,guide)
        rows=prior.rows(s)
    finally:
        prior.DEST,prior.NAME,prior.NEW,prior.price=original
    for path in DEST.glob('*.svg'):
        write(path,'\n'.join(line.rstrip() for line in path.read_text().splitlines()))
    write(DEST/'report.html',page)
    narrative='\n\n'.join('## '+title+'\n\n'+text for title,text in findings(s))
    write(DEST/'report.txt',narrative+'\n\n'+'\n\n'.join(methods()))
    intro='# System 1 Decision Benchmark\n\n27 specialized decision models and 3 high-end LLM references on the same **1,342 text questions across 31 categories**. Updated October 23, 2026.\n\n'
    intro+='**Fastino GLiDE has the highest observed text score: 1,154/1,342 (86.0%), with a 213 ms median. Sol without reasoning scored 1,143 (85.2%); Mammoth scored 1,139 (84.9%). On the separate image bank, Fastino is second at 158/200, one behind Amos.**\n\n'
    intro+='[Interactive report]('+SITE+') · [Fastino findings]('+SITE+'#new-additions) · [Named, color-coded categories]('+SITE+'#functions).\n\n'
    intro+='![30 routes: accuracy, speed and cost](results/releases/'+NAME+'/accuracy_speed_cost.png)\n\n## Results, speed and cost\n\nEvery row has 1,342 first attempts. Per-1,000 costs normalize actual bank totals. Pale-yellow bars are no-reasoning LLM references; blue bars are decision models. ~ means Fastino cost is calculated from reported token usage and the captured tariff, not returned monetary receipts.\n\n'
    intro+=table(['Model','Type','Correct / 1342','Accuracy','Median','p95','Cost / 1000','Actual 1342 cost'],rows)+'\n\n'
    intro+='Free public or promotional access is not a metered production price. Missing charges remain unknown; Qwen is prepaid-quota valuation.\n\n'+legend_markdown()+'\n\n'
    cat=categories(s,guide).replace(']('+NAME+'/','](results/releases/'+NAME+'/')
    end='## Questions, exports and verification\n\nUnchanged answer-free bank: [CSV](results/releases/consolidated_2026-10-19/questions_1342.csv), [native JSONL](results/releases/consolidated_2026-10-19/questions_1342.jsonl), [readable text](results/releases/consolidated_2026-10-19/questions_1342.txt).\n\n'
    end+='Current exports: [aggregate JSON](results/releases/'+NAME+'/statistics.json), [model CSV](results/releases/'+NAME+'/model_statistics.csv), [category CSV](results/releases/'+NAME+'/category_scores.csv), [audit](results/releases/'+NAME+'/audit_receipt.json).\n\n'
    end+='\n\n'.join(methods())+'\n\nImplementation: [scripts/](scripts/README.md). Current checks: `python3 scripts/validate_fastino_2026_10_23.py`; prior release: `python3 scripts/validate_october21_release.py`. Older dated evidence and seals remain unchanged.\n'
    write(ROOT/'README.md',intro+narrative+'\n\n'+cat+end)
    function_text=categories(s,guide,True).replace(']('+NAME+'/','](../results/releases/'+NAME+'/')
    write(repo_file('FUNCTIONS.md'),'# All 31 categories: 30 full-bank routes\n\n27 decision models and 3 no-reasoning LLM references. [Color-coded tables]('+SITE+'#functions).\n\n'+function_text)
    write(repo_file('OUTPUT_COMPLIANCE.md'),'# Delivered decisions and failures\n\nAll 30 routes retain the 1342-question first-attempt denominator. Fastino returned 1342 usable decisions with no retries. Wrong choices are not formatting failures.\n\n'+prior.prior.prior.quality(s)+'\n\nThe stopped Sonnet bare-ID trial is not pooled into its separately constrained complete reference.\n')
    old_cap=repo_file('IMAGE_CAPABILITIES.md').read_text()
    write(repo_file('IMAGE_CAPABILITIES.md'),'# Image input: October 23 update\n\nFastino GLiDE completed 200 native-image decisions: 158 correct (79.0%), 359 ms median. The catalog image flag was false; documented image parts and successful single/multiple-image probes established actual acceptance, followed by the unchanged full bank. The [visual report](https://etsabary.github.io/visual-decision-benchmark/report.html) ranks it second, not first.\n\nThe text cohort now has 27 specialized decision models. Capability declarations and measured vision results remain distinct.\n\n## Previous dated reviews\n\n'+old_cap)
    out=run.OUT/'text'
    receipt=dict(status='VERIFIED_COMPLETE_FASTINO_1342',question_count=1342,correct=1154,primary_attempts=1342,
        recoveries=0,unusable=0,bank_sha256=run.text_bank.BANK_HASH,private_aggregate_sha256=digest(PRIVATE),
        evidence_sha256=json.loads((out/'completion.json').read_text())['files_sha256'],
        model_requested=run.MODEL,model_returned='glide_v2',catalog_version_description=private['groups']['text']['metadata']['model']['description'],
        usage_cost_usd='0.01739196',api_reported_monetary_receipts=0,probe_cost_usd='0.00000364',
        earlier_29_records_unchanged=True,public_scoring_limit='Aggregate reconciliation, not independent private-key re-scoring',
        privacy='No answer keys, per-item correctness, raw account state or credentials in this packet',
        sources=run.SOURCES)
    write(DEST/'audit_receipt.json',json.dumps(receipt,indent=2))
    write(DEST/'model_metadata.json',json.dumps(private['groups']['text']['metadata'],indent=2))
    manifest=dict(version='fastino-text-20261023-v1',models=30,decision_models=27,llm_references=3,questions_each=1342,
        first_attempts=40260,bank_sha256=run.text_bank.BANK_HASH,prior_statistics_sha256=digest(ROOT/'results/releases/native_additions_2026-10-21/statistics.json'),
        artifacts={p.name:digest(p) for p in DEST.iterdir() if p.is_file()})
    write(DEST/'manifest.json',json.dumps(manifest,indent=2))
    pages=ROOT/'docs'/NAME;pages.mkdir(exist_ok=True)
    for path in DEST.iterdir():
        if path.is_file():shutil.copyfile(path,pages/path.name)
    write(ROOT/'docs/report.html',prior.prior.rebase(page,NAME))
    for name,anchor in (('index.html',''),('functions.html','#functions'),('output_compliance.html','#quality')):
        write(ROOT/'docs'/name,'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="benchmark-cohort" content="fastino-october23-1342"><meta http-equiv="refresh" content="0;url=report.html'+anchor+'"><title>System 1 Decision Benchmark</title></head><body><a href="report.html'+anchor+'">Current 30-route benchmark</a></body></html>')
    print('Built Fastino text publication: 30 routes, 930 category cells; no inference.')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--capture-sources',action='store_true')
    args=p.parse_args()
    if args.capture_sources:capture_sources()
    else:build()
