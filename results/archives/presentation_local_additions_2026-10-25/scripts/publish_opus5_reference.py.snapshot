"""Publish the completed Opus5 reference without changing earlier measurements.

Offline only. No credentials, inference or answer keys in exported artifacts.
Private revision-bound scoring must already have completed and sealed all1342.
"""
from collections import Counter
from copy import deepcopy
from decimal import Decimal
from html import escape
import json
from pathlib import Path
import re
import shutil
import subprocess
import argparse

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import numpy as np

import archive_fastino_presentation as archive
import opus5_schema_reference as run
import publish_fastino_2026_10_23 as previous
import publish_october21_additions as tables
import build_readable_report as readable
from build_october18_report import PALETTES, legend_markdown
from publish_consolidated_report import table
from repo_layout import repo_file

ROOT = run.ROOT
NAME = 'opus5_reference_2026-10-23'
DEST = ROOT / 'results/releases' / NAME
MID = 'reference_opus5'
PRIVATE = run.OUT / 'analysis/63def9936a7c325b/summary.json'
SITE = previous.SITE
digest, write = previous.digest, previous.write


def load():
    records, _ = run.validate(run.OUT, complete=True)
    private = json.loads(PRIVATE.read_text())
    assert private['status'] == 'COMPLETE_1342' and private['bank_sha256'] == run.native.BANK_HASH
    assert private['ledger_sha256'] == digest(run.OUT / 'attempts.jsonl')
    assert private['analyzer_sha256'] == digest(ROOT / 'scripts/analyze_opus5_reference.py')
    v = private['statistics']
    assert v['n'] == len(records) == 1342 and v['correct'] == 1109
    assert v['statuses'] == dict(Counter(r['status'] for r in records)) == {'ok': 1305, 'refusal': 37}
    assert run.chat.quantiles([r['latency_ms'] for r in records]) == v['latency_first_all']
    assert run.chat.money(records) == {k: value for k, value in v['cost_all_attempts'].items() if k != 'known_usd_per_1000'}
    assert all(not r['reasoning_text_present'] for r in records)
    assert all(r['reported_reasoning_tokens'] == 0 for r in records if r['status'] == 'ok')
    old = json.loads((previous.DEST / 'statistics.json').read_text())
    s = deepcopy(old)
    model = deepcopy(v)
    cost = v['cost_all_attempts']
    model.update(model_id=MID, label='Opus 5 — no thinking, JSON-choice',
        route='OpenRouter → Anthropic standard, constrained JSON-choice',
        mean_response_ms=v['mean_ms'], median_ms=v['latency_first_all']['median_ms'], p95_ms=v['latency_first_all']['p95_ms'],
        accuracy_among_usable=v['correct'] / v['answered'], first_statuses=v['statuses'],
        provider_failures=0, model_output_failures=v['failed'], probability_warnings=0,
        cost={'known_usd': cost['known_usd'], 'known_decimal': cost['exact_usd'],
              'exact_usd': cost['known_usd'], 'unknown_attempts': cost['missing_attempts'],
              'known_usd_per_1000': cost['known_usd_per_1000'], 'scope': 'API-reported USD charges;35 missing refusal receipts remain unknown'},
        reasoning_setting='thinking.type=disabled; output_config.effort=high; no tools',
        reasoning_verification='All1305 usable responses explicitly report0 thinking tokens and no thinking blocks;2 refusals also report0 and35 omit telemetry',
        output_contract='Separate constrained JSON choice:string1-5; original questions and numeric-ID suffix unchanged',
        bare_id_trial={'n': 8, 'usable': 5, 'format_failures': 2, 'refusals': 1,
                       'known_cost_usd': .019325, 'unknown_charges': 1, 'pooled': False},
        compatibility_known_usd=float(run.probe_cost(run.OUT) + run.native.probe_cost(run.native.OUT)),
        compatibility_unknown_attempts=1,
        version_limit='Requested claude-opus-5 with dated20260723 endpoint catalog; API identity is not immutable-weight attestation')
    s['models'][MID] = model
    s['model_kinds'][MID] = 'LLM reference'
    s['reference_model_ids'] = [*old['reference_model_ids'], MID]
    s['ranked_model_ids'] = sorted(s['models'], key=lambda mid: (-s['models'][mid]['correct'], mid))
    s['decision_model_ids'] = [mid for mid in s['ranked_model_ids'] if mid not in s['reference_model_ids']]
    s.update(status='COMPLETE_27_DECISION_PLUS_4_LLM_REFERENCES_1342', model_count=31,
        tested_llm_reference_count=4, decision_model_count=27, primary_cases=41602,
        all_tested_primary_cases=41602, added_model_ids=[MID], updated_date_toronto='2026-10-23',
        prior_statistics_sha256=digest(previous.DEST / 'statistics.json'),
        total_http_attempts=sum(m['attempts'] for m in s['models'].values()),
        total_recoveries=sum(m['recoveries'] for m in s['models'].values()))
    s['reference_evidence_bindings'][MID] = {'source_summary_sha256': digest(PRIVATE),
        'execution_evidence_sha256': json.loads((run.OUT / 'completion.json').read_text())['files_sha256']}
    assert all(s['models'][mid] == m for mid, m in old['models'].items())
    guide = json.loads((previous.DEST / 'category_guide.json').read_text())
    return s, guide, private


def findings(s):
    o = s['models'][MID]
    return [
        ('Opus5 without thinking scored82.6%, below Sol and above Sonnet',
         'Opus5 answered1109/1342 correctly (82.6%), versus GPT-6 Sol without reasoning at1143 (85.2%) and Sonnet5.5 in constrained JSON-choice mode at1070 (79.7%). Fastino GLiDE remains highest at1154 (86.0%); Mammoth scored1139 (84.9%) and Span and Drex Max1127 each (84.0%). These are observed results on the same developing bank, not a general intelligence ranking.'),
        ('Near-perfect unique assignments, with weaker exceptions and causal changes',
         'Opus scored66/67 on one-to-one assignments: giving every person or object exactly one partner while satisfying all clues. Sol scored61/67, Fastino63/67 and Drex Max65/67. Opus scored47/74 on truth-tellers and liars, versus Sol38/74 and Fastino59/74. It answered all52 rule-violation questions correctly. On exceptions and priority rules, Opus scored43/58 and Sol57/58; on changing a cause while holding other inputs fixed, Opus scored35/50 and Sol44/50. Ordered procedures remained18/48, the same as Sol and Fastino, versus Span33/48.'),
        ('The larger LLM cost did not buy a higher overall System1 score',
         f"Opus’s mean/median/p95 response was1581/1538/2109 ms. Its API-reported bank cost was$4.641065 plus unreported charges for35 responses, or at least$3.458320 per1000 questions. Sol’s total was$0.84829450 and Sonnet’s$1.923908. The known Opus amount alone is{4.641065/.8482945:.1f} times Sol’s and{4.641065/1.923908:.1f} times Sonnet’s. Fastino’s separately labelled usage-based estimate was$0.01739196, with a213 ms median. Different dates, providers and loads limit timing and price comparisons; missing charges are not zero."),
        ('A constrained answer format, with37 refusals retained as unsuccessful',
         'The full Opus run used thinking.type=disabled, output_config.effort=high, no tools and a16-token cap through OpenRouter’s pinned Anthropic standard route. All1305 usable JSON choices explicitly reported zero thinking tokens and no thinking blocks. There were37 refusals: two reported zero thinking tokens, while35 omitted thinking/cost telemetry. All37 remain unsuccessful first attempts in the1342-question score. There were no retries or malformed JSON choices. A separate eight-question bare-ID trial produced five usable IDs, two malformed/explanatory outputs and one refusal; it is not pooled into this score. Constraining the answer grammar does not make this identical to unconstrained bare-ID delivery.'),
        ('The harder additions separate the references too',
         'Opus scored1001/1136 (88.1%) on the original portion and108/206 (52.4%) on the additions. Across the six newest eight-question categories it scored29/48, versus Sol36/48, Span34/48 and Fastino29/48. The primary score remains one unweighted1342-question total. Existing questions, category weights and all30 earlier model records are unchanged.'),
    ] + previous.findings(s)


def methods():
    original = previous.methods()
    original[0] = ('31 full-bank routes:27 specialized decision models and four selected no-reasoning LLM references. '
        'Each covers1342 questions across31 categories:41,602 first attempts. Opus was measured October23,2026 (America/Toronto); '
        'all30 earlier model records retain their original measurements and dates.')
    return [original[0],
        'Opus used two requests per barrier wave, a16-token output cap, explicit disabled thinking at high effort, no tools, the same frozen question/option order and numeric-only suffix, and an additional JSON-choice output grammar. The dated Anthropic standard endpoint was pinned with no provider fallback. All first attempts, including37 refusals, stay in accuracy and latency denominators. No retries occurred. The mean, median andp95 pool all1342 original response times, not category medians.',
        'Opus API-reported cost totals$4.641065 for1307 receipts;35 refusal charges are unreported. Its separate successful synthetic probes total$0.002610; the disabled-thinking+xhigh negative control was rejected withHTTP400 and omitted cost telemetry. The separate eight-case bare-ID trial cost$0.019325 reported plus one unreported charge. These probes and the stopped trial are not pooled into the ranked bank. The positive high-effort probe returned zero thinking tokens; the negative control confirmed that xhigh is incompatible with disabled thinking on the tested route.',
        'All1305 usable Opus choices reported zero thinking tokens and no thinking blocks;35 refusals omitted telemetry and are unverified, not verified zeros. Sonnet and Opus use separately labelled constrained JSON choice; Sol uses the bare-ID contract. These are selected references, not an exhaustive ranking of the strongest LLMs or a comparison with reasoning enabled.',
        *original[1:]]


def clean(text):
    # Author text uses plain facts and compact numbers; retain normal word spacing.
    text = re.sub(r'(?<![vVpPF])(?<=[A-Za-z])(?=\d)|(?<=\d)(?=[A-Za-z])', ' ', text)
    text = re.sub(r'(?<=\w)(?=\$)|(?<=[:;])(?=\d)', ' ', text)
    return (text.replace('andp95', 'and p95').replace('d 3', 'd3').replace('d 1', 'd1')
            .replace('5 xx', '5xx').replace('withHTTP400', 'with HTTP400').replace(',2026', ', 2026'))


def overview(s):
    ids = s['ranked_model_ids']; models = [s['models'][mid] for mid in ids]; y = np.arange(len(ids))
    band = lambda v, limits: next((i for i, b in enumerate(limits) if v <= b), 3)
    with plt.rc_context({'font.family': 'DejaVu Sans', 'svg.fonttype': 'none', 'svg.hashsalt': 'opus5-1342-20261023'}):
        fig, axes = plt.subplots(1, 3, figsize=(16, 17.8), sharey=True, gridspec_kw={'width_ratios': [1.2, 1.1, 1.1]})
        bars = axes[0].barh(y, [100*m['accuracy'] for m in models], color=[(.95, .83, .42, .60) if mid in s['reference_model_ids'] else '#16728c' for mid in ids])
        for bar, mid in zip(bars, ids):
            if mid in s['reference_model_ids']:
                bar.set_edgecolor('#9c761c')
        axes[0].set_yticks(y, ['Opus 5 (LLM, JSON)' if mid == MID else readable.short(m['label']) for mid,m in zip(ids,models)], fontsize=11)
        axes[0].set_xlim(0, 112); axes[0].invert_yaxis(); axes[0].set_xlabel('Correct first decisions (%)')
        for yy, mid, m in zip(y, ids, models):
            axes[0].text(100*m['accuracy']+1, yy, f"{m['accuracy']:.1%}", va='center', fontsize=10)
            axes[1].plot([m['median_ms'], m['p95_ms']], [yy, yy], color='#8999a5')
            axes[1].scatter(m['median_ms'], yy, color=PALETTES[band(m['median_ms'], (250, 500, 1000))], s=65, edgecolor='#364c60')
            axes[1].scatter(m['p95_ms'], yy, color='#35424d', marker='d', s=20)
            c = m['cost']
            if c.get('public_free_access'):
                axes[2].text(.03, yy, 'Promotional free*' if mid in ('mammoth1', 'elephant1') else 'Free public access*',
                    transform=axes[2].get_yaxis_transform(), va='center', fontsize=10, bbox={'facecolor': '#edf1f5', 'edgecolor': 'none', 'pad': 3})
            else:
                axes[2].scatter(c['known_usd_per_1000'], yy, color=PALETTES[band(c['known_usd_per_1000'], (.01, .025, .05))], s=65, edgecolor='#364c60')
                if c['unknown_attempts']:
                    axes[2].text(c['known_usd_per_1000']*1.15, yy, '+ ?', va='center', fontsize=9)
        axes[1].set_xscale('log'); axes[2].set_xscale('log')
        axes[1].set_xlabel('Response time (ms, log scale)\nCircle: median · diamond: p95')
        axes[2].set_xlabel('Cost per 1,000 (USD, log)\n+ ? = incomplete charges')
        for ax, title in zip(axes, ('Accuracy', 'Speed', 'Cost')):
            ax.set_title(title, fontsize=14, pad=18); ax.grid(axis='x', alpha=.2); ax.set_axisbelow(True)
            for spine in ax.spines.values(): spine.set_visible(False)
        fig.suptitle('27 decision models and 4 no-reasoning LLM references · 1,342 questions', fontsize=17, y=.98)
        fig.legend(handles=[Patch(facecolor='#16728c', label='Decision models'), Patch(facecolor=(.95,.83,.42,.60), edgecolor='#9c761c', label='No-reasoning LLM references')], loc='upper center', bbox_to_anchor=(.5,.957), ncol=2, frameon=False)
        fig.text(.02,.025,'Opus 5: October 23, 2026. Explicit thinking disabled; constrained JSON-choice; 37 refusals included.\nOpus known bank cost $4.641065 + 35 unreported charges. Older measurements unchanged.\nFastino is usage × tariff; free access is not a production tariff. Different dates, providers and loads remain confounds.', fontsize=10)
        fig.subplots_adjust(left=.30, right=.98, top=.91, bottom=.12, wspace=.36)
        for suffix in ('png','svg'):
            fig.savefig(DEST/('accuracy_speed_cost.'+suffix), dpi=160, metadata={'Date':None} if suffix=='svg' else {})
        plt.close(fig)


def categories(s, guide, details=False):
    return previous.categories(s, guide, details).replace(previous.NAME, NAME).replace('30 routes', '31 routes')


def html(s, guide):
    old = (previous.DEST/'report.html').read_text(); head = old[:old.index('<body>')+6]
    head = re.sub(r'<title>.*?</title>', '<title>System1 decisions:31 routes,1342 questions</title>', head)
    head = head.replace('fastino-october23-1342', 'opus5-october23-1342')
    body = '<main><h1>System 1 Decision Benchmark</h1><p>27 specialized decision models and4 no-reasoning LLM references. Same1,342 text questions,31 categories. Updated October23,2026.</p>'
    body += '<nav><a href="#overview">Overall results</a><a href="#new-additions">Opus5 findings</a><a href="#llm-references">LLM references</a><a href="#functions">Named categories</a><a href="#method">Method</a></nav>'
    body += '<div class="cards"><div class="card"><div class="label">Highest observed text score</div><div class="big">86.0%</div><div class="small">Fastino GLiDE ·1154/1342</div></div><div class="card"><div class="label">Highest LLM reference</div><div class="big">85.2%</div><div class="small">GPT-6 Sol, reasoning off ·1143/1342</div></div><div class="card"><div class="label">New Opus5 reference</div><div class="big">82.6%</div><div class="small">1109/1342 ·1538 ms median</div></div><div class="card"><div class="label">Matched question coverage</div><div class="big">31 routes</div><div class="small">41,602 first attempts ·31 categories</div></div></div>'
    body += '<section id="overview"><h2>Accuracy, speed and cost: all31 routes</h2><p>Blue bars: decision models. Pale yellow: no-reasoning LLM references. Every row covers1,342 first attempts. + ? means missing charges; Opus has35. ~ marks Fastino’s usage-based tariff calculation.</p><div class="figure"><a href="accuracy_speed_cost.svg"><img src="accuracy_speed_cost.png" alt="31 routes: accuracy, speed and cost; Opus5 is a pale-yellow LLM reference"></a></div>'+tables.summary_html(s)+tables.prior.prior.legend_html()+'</section>'
    body += '<section id="new-additions"><h2>October23: Opus5 without thinking</h2>'+''.join('<h3>'+escape(clean(title))+'</h3><p>'+escape(clean(text))+'</p>' for title,text in findings(s))+'</section>'
    body += '<section id="llm-references"><h2>Selected LLM references, reasoning off</h2><p>These four routes provide context for immediate decision performance, not an exhaustive LLM ranking. Sol uses explicit reasoning off. Sonnet and Opus use separately constrained JSON-choice grammars after stopped bare-ID trials; those trials are not pooled. Opus uses disabled thinking, high effort and no tools. All usable Opus answers explicitly report zero thinking tokens;35 refusals omit telemetry. Qwen uses none, but unreported reasoning counts are not called zero. Failures remain unsuccessful first deliveries.</p></section>'
    body += readable.clarity_section(s,guide).replace('All 20 models','All 31 routes').replace('all 20 models','all 31 routes')
    body += '<section id="quality"><h2>Delivered decisions and failures</h2>'+tables.markdown.markdown(tables.prior.prior.quality(s),extensions=['tables'])+'</section>'
    body += '<section id="image-support"><h2>Image results remain separate</h2><p>This Opus update is text-only; no Opus image score is inferred. <a href="https://etsabary.github.io/visual-decision-benchmark/report.html">Separate native-image benchmark</a>: Fastino158/200, Amos159/200. No image measurements changed.</p></section>'
    body += '<section id="method"><h2>Method, costs and measurement limits</h2>'+''.join('<p>'+escape(clean(p))+'</p>' for p in methods())+'</section>'
    body += '<section id="downloads"><h2>Questions, data and audit</h2><p><a href="statistics.json">31-route aggregate JSON</a> · <a href="model_statistics.csv">Model CSV</a> · <a href="category_scores.csv">Category CSV</a> · <a href="audit_receipt.json">Audit receipt</a> · <a href="manifest.json">Release manifest</a>.</p><p>Unchanged questions: <a href="../consolidated_2026-10-19/questions_1342.csv">CSV</a> · <a href="../consolidated_2026-10-19/questions_1342.jsonl">Native JSONL</a> · <a href="../consolidated_2026-10-19/questions_1342.txt">Readable text</a>.</p></section></main></body></html>'
    def visible(match):
        text = clean(match[0])
        for model in s['models'].values():
            text = text.replace(clean(model['label']), model['label'])
        return text
    body = re.sub(r'(?<=>)[^<>]+(?=<)', visible, body)
    return head + body


def build(refresh_unpublished=False):
    if (DEST/'manifest.json').exists():
        tracked = subprocess.run(['git','ls-files','--error-unmatch',str((DEST/'manifest.json').relative_to(ROOT))],cwd=ROOT,capture_output=True).returncode == 0
        assert refresh_unpublished and not tracked, 'Use a new release for changed published evidence'
    archive.archive()
    s,guide,private = load(); DEST.mkdir(parents=True,exist_ok=True)
    old = (tables.DEST,tables.NAME,tables.NEW,tables.price)
    try:
        tables.DEST,tables.NAME,tables.NEW,tables.price = DEST,NAME,(MID,),previous.price
        tables.exports(s,guide); overview(s); page = html(s,guide); rows = tables.rows(s)
    finally:
        tables.DEST,tables.NAME,tables.NEW,tables.price = old
    for path in DEST.glob('*.svg'):
        write(path,'\n'.join(line.rstrip() for line in path.read_text().splitlines()))
    write(DEST/'report.html',page)
    narrative = '\n\n'.join('## '+clean(title)+'\n\n'+clean(text) for title,text in findings(s))
    write(DEST/'report.txt', narrative+'\n\n'+'\n\n'.join(clean(p) for p in methods()))
    intro = '# System 1 Decision Benchmark\n\n27 specialized decision models and4 no-reasoning LLM references on the same **1,342 text questions across31 categories**. Updated October23,2026.\n\n'
    intro = clean(intro)
    intro += '**Fastino GLiDE remains highest at1,154/1,342 (86.0%). Sol without reasoning scored1,143 (85.2%); the new Opus5 no-thinking, JSON-choice reference scored1,109 (82.6%), above Sonnet’s1,070 (79.7%).**\n\n'
    intro = clean(intro)
    intro += '[Interactive report]('+SITE+') · [Opus findings]('+SITE+'#new-additions) · [Named, color-coded categories]('+SITE+'#functions).\n\n'
    intro += '![31 routes: accuracy, speed and cost](results/releases/'+NAME+'/accuracy_speed_cost.png)\n\n## Results, speed and cost\n\nEvery row has 1,342 first attempts. Per-1,000 costs normalize actual bank totals. Pale-yellow bars are no-reasoning LLM references; blue bars are decision models. Opus and Sonnet use constrained JSON choice. + ? means missing charges; Opus has 35. ~ marks Fastino’s usage-based estimate, not monetary receipts.\n\n'
    intro += table(['Model','Type','Correct / 1342','Accuracy','Median','p95','Cost / 1000','Actual 1342 cost'],rows)+'\n\n'
    legend = legend_markdown().replace('1,136-question','1,342-question')
    intro += 'Free access is not a production tariff. Missing charges are unknown; Qwen is prepaid-quota valuation.\n\n'+legend+'\n\n'
    cat = categories(s,guide).replace(']('+NAME+'/','](results/releases/'+NAME+'/')
    end = '## Questions, exports and verification\n\nUnchanged answer-free bank: [CSV](results/releases/consolidated_2026-10-19/questions_1342.csv), [native JSONL](results/releases/consolidated_2026-10-19/questions_1342.jsonl), [readable text](results/releases/consolidated_2026-10-19/questions_1342.txt).\n\n'
    end += 'Current exports: [aggregate JSON](results/releases/'+NAME+'/statistics.json), [model CSV](results/releases/'+NAME+'/model_statistics.csv), [category CSV](results/releases/'+NAME+'/category_scores.csv), [audit](results/releases/'+NAME+'/audit_receipt.json).\n\n'
    end += '\n\n'.join(clean(p) for p in methods())+'\n\nImplementation: [scripts/](scripts/README.md). Current checks: `python3 scripts/validate_opus5_release.py`; prior checks: `python3 scripts/validate_fastino_2026_10_23.py` and `python3 scripts/validate_october21_release.py`. Older dated evidence and seals remain unchanged.\n'
    write(ROOT/'README.md',intro+narrative+'\n\n'+cat+end)
    write(repo_file('FUNCTIONS.md'),'# All 31 categories: 31 full-bank routes\n\n27 decision models and 4 no-reasoning LLM references. [Color-coded tables]('+SITE+'#functions).\n\n'+categories(s,guide,True).replace(']('+NAME+'/','](../results/releases/'+NAME+'/'))
    write(repo_file('OUTPUT_COMPLIANCE.md'),'# Delivered decisions and failures\n\nAll 31 routes retain the 1342-question first-attempt denominator. Opus returned 1305 valid JSON choices and 37 refusals, no retries. The separate eight-question bare-ID trial is not pooled; missing telemetry is unverified and missing charges unknown.\n\n'+tables.prior.prior.quality(s))
    seal = json.loads((run.OUT/'completion.json').read_text())
    receipt = {'status':'VERIFIED_COMPLETE_OPUS5_1342','question_count':1342,'correct':1109,
        'primary_attempts':1342,'recoveries':0,'usable':1305,'refusals':37,
        'zero_thinking_usable':1305,'zero_thinking_refusals':2,'unreported_thinking_refusals':35,
        'known_cost_usd':'4.641065','unreported_charge_attempts':35,
        'bank_sha256':run.native.BANK_HASH,'source_summary_sha256':digest(PRIVATE),
        'execution_evidence_sha256':seal['files_sha256'],
        'scoring_authority_sha256':sorted(set(private['scoring_bindings'].values())),
        'earlier_30_records_unchanged':True,'output_grammar':'Constrained JSON choice:string1-5',
        'bare_id_trial':s['models'][MID]['bare_id_trial'],
        'compatibility_known_usd':s['models'][MID]['compatibility_known_usd'],
        'compatibility_unknown_charges':1,
        'privacy':'Aggregate reconciliation and evidence hashes only; no answer keys, per-item correctness or credentials',
        'public_scoring_limit':'Private revision-bound scoring verified locally; public aggregates cannot independently reproduce it'}
    write(DEST/'audit_receipt.json',json.dumps(receipt,indent=2))
    write(DEST/'model_metadata.json',json.dumps(json.loads((run.OUT/'manifest.json').read_text())['captured_endpoint'],indent=2))
    manifest = {'version':'opus5-reference-20261023-v1','models':31,'decision_models':27,'llm_references':4,
        'questions_each':1342,'first_attempts':41602,'bank_sha256':run.native.BANK_HASH,
        'prior_statistics_sha256':digest(previous.DEST/'statistics.json'),
        'artifacts':{p.name:digest(p) for p in sorted(DEST.iterdir()) if p.is_file() and p.name != 'manifest.json'}}
    write(DEST/'manifest.json',json.dumps(manifest,indent=2))
    pages = ROOT/'docs'/NAME; pages.mkdir(exist_ok=True)
    for path in DEST.iterdir():
        if path.is_file(): shutil.copyfile(path,pages/path.name)
    write(ROOT/'docs/report.html',tables.prior.rebase(page,NAME))
    for name,anchor in (('index.html',''),('functions.html','#functions'),('output_compliance.html','#quality')):
        write(ROOT/'docs'/name,'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="benchmark-cohort" content="opus5-october23-1342"><meta http-equiv="refresh" content="0;url=report.html'+anchor+'"><title>System 1 Decision Benchmark</title></head><body><a href="report.html'+anchor+'">Current31-route benchmark</a></body></html>')
    print('Built Opus5 addition:31 complete routes,961 category cells; no inference.')


def bind_layout():
    """Refresh only the generated active-file registry; old snapshots stay sealed."""
    path = ROOT/'scripts/layout_manifest.json'
    value = json.loads(path.read_text())
    names = set(value['current_files']) | {p.relative_to(ROOT).as_posix() for p in (ROOT/'scripts').glob('*.py')}
    value['current_files'] = {name:digest(ROOT/name) for name in sorted(names)}
    write(path,json.dumps(value,indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--refresh-unpublished',action='store_true')
    build(parser.parse_args().refresh_unpublished)
    bind_layout()
