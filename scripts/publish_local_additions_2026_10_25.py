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

import archive_local_gpu_presentation as archive
import build_readable_report as readable
from build_october18_report import PALETTES, legend_markdown
import publish_opus5_reference as prior
from publish_consolidated_report import table
from repo_layout import repo_file

ROOT = Path(__file__).resolve().parents[1]
NAME = 'local_additions_2026-10-25'
DEST = ROOT / 'results/releases' / NAME
SITE = 'https://etsabary.github.io/system-1-decision-benchmark/report.html'
PREVIOUS = ROOT / 'results/releases/local_gpu_2026-10-25'
PRIVATE = ROOT.parent / 'text-decision-hardening/runs/ollaya_lan_additions_2026-10-25'
PURPLE, HOSTED, YELLOW = '#7c3aed', '#16728c', (.95, .83, .42, .60)
LABELS = {
    'pplx-decider:flash-v1.2-mixed4': 'Perplexity Flash v1.2 mixed4',
    'd3:flash-artemis-iq3_m': 'D3 Flash Artemis 9B',
    'jeb:9b-v2.1-iq4_xs': 'Jebadiah 9B v2.1',
}


def digest(path):
    return sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(value.rstrip() + '\n' if isinstance(value, str) else json.dumps(value, indent=2) + '\n')


def mid(name):
    return 'local_' + name.replace(':', '_').replace('-', '_').replace('.', '_')


def capture():
    """Independently reconcile every scored packet and key-bound category total."""
    assert not (DEST / 'manifest.json').exists(), 'A sealed release must not be recaptured'
    sys.path.insert(0, str(PRIVATE.parent.parent))
    import ollaya_lan_benchmark as executor
    import consolidated_analysis as authority
    from analyze_frontier_reference import load_gold
    questions, order, inventory, _ = executor.prepare(PRIVATE)
    original = authority.CORRECTED
    try:
        authority.CORRECTED = ROOT / 'results/releases/corrected_2026-10-18'
        gold, metadata, _, bindings = load_gold(PRIVATE.parent.parent, questions)
    finally:
        authority.CORRECTED = original
    seals = json.loads((PRIVATE / 'local_additions_checksums.json').read_text())
    models, provenance, timing = {}, {}, []
    for name, label in LABELS.items():
        folder = executor.folder(PRIVATE, name)
        report = json.loads((folder / 'full_report.json').read_text())
        for filename in ('full_report.json', 'attempts.jsonl', 'dispatches.jsonl', 'warmup.jsonl'):
            key = (folder / filename).relative_to(PRIVATE).as_posix()
            assert digest(folder / filename) == seals[key], key
        attempts = executor.rows(folder / 'attempts.jsonl')
        dispatches = executor.rows(folder / 'dispatches.jsonl')
        assert len(attempts) == len(dispatches) == 1342
        assert json.loads((folder / 'state.json').read_text())['state'] == 'complete'
        assert all(v.get('device', '').startswith('cuda') for v in report['devices'])
        md = inventory['metadata'][name]
        for filename in ('metadata_screen.json', 'metadata_screen_end.json',
                         'metadata_continuation.json', 'metadata_continuation_end.json'):
            assert json.loads((folder / filename).read_text())['raw']['digest'] == md['digest']
        for i, (a, d, item_id) in enumerate(zip(attempts, dispatches, order), 1):
            q = questions[item_id]
            assert a['request_index'] == d['request_index'] == i
            assert a['attempt'] == d['attempt'] == 1 and a['item_id'] == d['item_id'] == item_id
            assert a['native_input_sha256'] == q['native_input_sha256']
            body = dict(model=name, **q['native_input'], keep_alive='10m')
            assert a['request_payload_sha256'] == d['request_payload_sha256'] == executor.digest(body)
            assert executor.parse(a['transport'], name, md)['status'] == a['status']
            timing.append(dict(model_id=mid(name), request_index=i, item_id=item_id,
                family_id=q['family_id'], native_input_sha256=q['native_input_sha256'],
                status=a['status'], latency_ms=a['latency_ms'], server_eval_ms=a['server_eval_ms'],
                server_load_ms=a['server_load_ms'], response_sha256=executor.digest(a['transport'].get('raw'))))
        def outcome(ids):
            rr = [a for a in attempts if a['item_id'] in ids]
            hit = sum(a['status'] == 'ok' and a['choice'] == str(gold[a['item_id']]) for a in rr)
            answered = sum(a['status'] == 'ok' for a in rr)
            return dict(n=len(rr), correct=hit, answered=answered, failed=len(rr)-answered,
                        wrong_valid=answered-hit, accuracy=hit/len(rr) if rr else None)
        v = outcome(set(questions))
        assert v['correct'] == report['correct'] and v['n'] == 1342
        quantiles = executor.quantiles([a['latency_ms'] for a in attempts])
        assert quantiles == report['timing']
        families = {fid: outcome({i for i,q in questions.items() if q['family_id'] == fid})
                    for fid in sorted({q['family_id'] for q in questions.values()})}
        assert {f['family_id']:(f['n'], f['correct']) for f in report['families']} == {
            fid:(f['n'], f['correct']) for fid,f in families.items()}
        statuses = dict(Counter(a['status'] for a in attempts))
        dates = dict(Counter(datetime.fromisoformat(a['started_at']).astimezone(ZoneInfo('America/Toronto')).date().isoformat() for a in attempts))
        v.update(model_id=mid(name), label=label, route='Local Ollaya · RTX 2060 6 GB · LAN HTTP',
            execution_location='local', model_requested=name, hardware='NVIDIA RTX 2060', vram_gb=6,
            runtime='Ollaya 0.17.0', precision=(md.get('details') or {}).get('quantization_level', 'unreported'),
            upstream_revision=(md.get('model_info') or {}).get('general.source') or 'Not reported by route',
            serving_digest=md['digest'], mean_response_ms=quantiles['mean_ms'],
            median_ms=quantiles['median_ms'], p95_ms=quantiles['p95_ms'],
            first_statuses=statuses, attempts=1342, recoveries=0,
            provider_failures=sum(a['status'] in ('http_failure','transport_failure','provider_error') for a in attempts),
            model_output_failures=sum(a['status'] not in ('ok','http_failure','transport_failure','provider_error') for a in attempts),
            probability_warnings=0, accuracy_among_usable=v['correct']/v['answered'],
            cost=dict(kind='local_unmetered', known_usd=None, known_decimal=None, exact_usd=None,
                known_usd_per_1000=None, unknown_attempts=0, hardware_electricity_measured=False,
                scope='No metered API invoice; hardware and electricity costs unmeasured'),
            families=families, macro_family_accuracy=sum(f['accuracy'] for f in families.values())/31,
            dates_toronto=dates, returned_identities=dict(Counter(a['model_returned'] for a in attempts)),
            providers={'Local Ollaya':1342},
            original_1136=report['original_1136'], added_206=report['added_206'],
            new_domains=outcome({i for i,q in questions.items() if q['family_id'] >= 'F26'}),
            release_exclusion_diagnostic=outcome({i for i,m in metadata.items() if not m['permanently_unscored_native_development']}),
            highest_scoring_categories=report['highest_scoring_categories'], lowest_scoring_categories=report['lowest_scoring_categories'],
            warmup_calls=report['warmup_calls'], source_summary_sha256=digest(folder/'full_report.json'))
        models[v['model_id']] = v
        provenance[v['model_id']] = dict(model_requested=name, serving_digest=md['digest'],
            details=md.get('details'), capabilities=md.get('capabilities'),
            source_reported=(md.get('model_info') or {}).get('general.source'),
            reported_context={k:value for k,value in (md.get('model_info') or {}).items() if 'context' in k},
            device='cuda:0', gpu='NVIDIA RTX 2060', vram_gb=6, hardware_identity_source='User reported GPU and VRAM; CUDA execution captured',
            runtime='Ollaya 0.17.0', identity_limit='Registry metadata and stable start/end digest; no independent weight attestation',
            source_evidence_sha256={n:digest(folder/n) for n in ('attempts.jsonl','dispatches.jsonl','warmup.jsonl','full_report.json')})
    # The previous published records are copied exactly, never rescored or retimed.
    added_models = models
    models = {**json.loads((PREVIOUS/'local_models.json').read_text()), **models}
    provenance = {**json.loads((PREVIOUS/'local_model_metadata.json').read_text()), **provenance}
    DEST.mkdir(parents=True, exist_ok=True)
    write(DEST/'local_models.json', models)
    write(DEST/'local_model_metadata.json', provenance)
    buffer = io.StringIO(newline=''); writer = csv.DictWriter(buffer, fieldnames=list(timing[0]), lineterminator='\n')
    writer.writeheader(); writer.writerows(timing); write(DEST/'local_timing_evidence.csv', (PREVIOUS/'local_timing_evidence.csv').read_text()+''.join(buffer.getvalue().splitlines(keepends=True)[1:]))
    write(DEST/'screened_routes.json', json.loads((PREVIOUS/'screened_routes.json').read_text()))
    write(DEST/'audit_receipt.json', dict(status='VERIFIED_18_LOCAL_FULL_BANK_ROUTES',
        questions_each=1342, models=18, first_attempts=24156, usable=24136, unusable=20, recoveries=0,
        bank_sha256=executor.BANK_HASH, scoring_authority_sha256=sorted(set(bindings.values())),
        private_capture_sha256=digest(PRIVATE/'inventory_initial.json'),
        captured_execution_source_sha256=digest(PRIVATE/'executor_source.py.snapshot'),
        new_models=3, new_first_attempts=4026, new_usable=4013, new_unusable=13,
        prior_receipt_sha256=digest(PREVIOUS/'audit_receipt.json'),
        prior_statistics_sha256=digest(PREVIOUS/'statistics.json'),
        validation='New packet/input hashes, response parses, private-key scoring, timing and category totals reconciled locally; earlier 46 model records and 20,130 timing rows retained exactly',
        privacy='Aggregate accuracy and answer-free timing/status rows only; no answer keys, model choices, per-item correctness, credentials, private paths or LAN address',
        public_scoring_limit='Public checks reproduce timing/coverage and aggregate arithmetic; private-key accuracy cannot be independently rescored from public artifacts',
        hardware='User reported RTX2060 6GB; every completed route reported cuda:0',
        source_revision_limit='Some custom routes do not report upstream weight revision; quantization and captured serving digest are reported',
        cost='Unmetered local API access is not a measured zero operating cost'))


def load():
    old = json.loads((PREVIOUS/'statistics.json').read_text())
    local = json.loads((DEST/'local_models.json').read_text())
    assert len(local) == 18
    assert all(local[mid] == old['models'][mid] for mid in old['local_model_ids'])
    added_ids = set(local) - set(old['models'])
    assert len(added_ids) == 3
    s = deepcopy(old); s['models'].update(local)
    s['local_model_ids'] = sorted(local, key=lambda m:(-local[m]['correct'],m))
    s['hosted_model_ids'] = list(old['hosted_model_ids'])
    for key in local:s['model_kinds'][key] = 'Decision / classifier'
    s['ranked_model_ids'] = sorted(s['models'], key=lambda m:(-s['models'][m]['correct'],m))
    s['decision_model_ids'] = [m for m in s['ranked_model_ids'] if m not in s['reference_model_ids']]
    s.update(status='COMPLETE_49_ROUTES_18_LOCAL_1342', model_count=49, decision_model_count=45,
        hosted_decision_model_count=27, local_model_count=18, primary_cases=65758, all_tested_primary_cases=65758,
        added_model_ids=sorted(added_ids), updated_date_toronto='2026-10-25',
        prior_statistics_sha256=digest(PREVIOUS/'statistics.json'),
        total_http_attempts=sum(m['attempts'] for m in s['models'].values()),
        total_recoveries=sum(m['recoveries'] for m in s['models'].values()))
    assert all(s['models'][m] == value for m,value in old['models'].items())
    guide = json.loads((PREVIOUS/'category_guide.json').read_text())
    return s, guide


def is_local(s, model):
    return model in s['local_model_ids']


def price(mid, model, normalized=True):
    if model.get('execution_location') == 'local':return 'Local compute cost unmeasured'
    return prior.previous.price(mid, model, normalized)


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
    return '<div class="scroll"><table><thead><tr><th>Model</th><th>Type / setting</th><th>Correct / questions</th><th>Mean</th><th>Median</th><th>p95</th><th>Cost / 1,000</th><th>Actual 1,342 cost</th></tr></thead><tbody>'+''.join(rows)+'</tbody></table></div>'


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
        title='18 local models · RTX 2060 6 GB · 1,342 questions' if local_only else '49 routes · 27 hosted decision models · 18 local models · 4 LLM references'
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
      ('Fastino remains highest overall; D3 leads the local configurations',
       'Fastino GLiDE retains 1,154/1,342 (86.0%), GPT-6 Sol without reasoning 1,143 (85.2%) and Mammoth-1 1,139 (84.9%). D3 Flash Artemis 9B IQ3_M scored 995/1,342 (74.1%), followed locally by Perplexity Flash mixed4 at 971 (72.4%), H2O-Lightning 4B at 892 (66.5%) and Jebadiah 9B v2.1 at 855 (63.7%). All earlier 46 model records retain their original scores, timing and cost fields. D3 answered 24 more questions correctly than the next local configuration, Perplexity, a 1.8 percentage-point lead. Every chart now includes the 49 completed routes.'),
      ('Two configurations move the local accuracy range upward',
       'D3 scored 103 more correct answers than H2O, an increase of 7.7 percentage points, with a 408 ms median versus 259 ms. Perplexity scored 79 more, an increase of 5.9 points, with a 798 ms median. D3 and Jebadiah 9B had similar mean / median / p95 times: 441 / 408 / 701 ms and 440 / 405 / 694 ms. Perplexity measured 875 / 798 / 1,526 ms. The RTX 2060 with 6 GB VRAM was chosen deliberately as an older, more accessible hardware setup: the aim was to measure what these models can do on equipment more readers may already have. These are measured LAN routes; loading and synthetic warm-ups are excluded.'),
      ('D3 combines strong rule application with uneven state tracking',
       'D3 scored 43/46 on following if-then rules, 40/43 on planning an action sequence, 40/43 on directed paths and 48/51 on explicit preference ordering. Its sequential procedures score was 14/48: these questions require applying each edit to the newly updated state. Object swaps scored 24/52 and spatial tracking 22/49. Perplexity scored 39/40 on ordered comparisons, 41/43 on directed paths and 40/43 on choosing authoritative current records, while sequential procedures scored 12/48.'),
      ('The larger Jebadiah improved the overall score by 3.5 points',
       'Jebadiah 9B v2.1 IQ4_XS answered 855/1,342 correctly (63.7%), 47 more than Jebadiah 4B Q8_0 at 808 (60.2%). Its median increased from 270 to 405 ms. Directed paths scored 41/43, explicit preference ordering 47/51 and fault diagnosis 45/50. Sequential procedures scored 10/48 and exact truth counting 23/71. Model size, version and precision all differ, so this comparison does not isolate the cause of the improvement.'),
      ('Overall rank still conceals useful narrower strengths',
       'Fovea selected the authoritative current record over a stale conflicting one in 42/43 cases, matching Fastino and Sol; H2O scored 38/43 and Lev 13/43. JevK5 scored 41/43 on record filtering and directed paths. Sura scored 31.9% overall but 39/50 on tracking what different observers know. The full category tables preserve these differences. The six newest domains contain eight questions each, so one answer changes their score by 12.5 percentage points.'),
      ('A very short response can still be close to guessing',
       'Laya measured a 46 ms median at 24.0% accuracy; Decima Agent 71 ms at 23.3%; Von 77 ms at 24.7%; GLiClass 79 ms at 29.3%. Uniform guessing among five choices averages 20%. Von scored 331 correct, about 63 above the 268 expected from uniform guessing, with 1,011 wrong. Shared templates and dependent questions limit the independent evidence. These configurations showed limited overall success on this logical decision bank; a narrow classification task needs its own validation.'),
      ('Input capacity caused 13 failures in the new runs',
       'Perplexity rejected three inputs above its 1,024-token limit. D3 had three input-size failures with a physical batch limit of 1,024. Jebadiah rejected seven prompts above an effective 896-token read limit, despite a reported 1,024-token context. These are serving/input-capacity failures. They remain unsuccessful first attempts in the same 1,342-case denominator; no prompt was shortened, truncated or retried to fit these variants. Across all 18 local runs, there are 24,136 usable decisions and 20 unsuccessful responses.'),
      ('Precision and provenance belong to the measured configuration',
       'Perplexity used sensitivity-allocated mixed Q2_K–Q6_K weights with an FP32 decision readout; D3 used an Artemis IQ3_M mixed-precision file; Jebadiah 9B used IQ4_XS. Earlier configurations retain their reported Q8_0, Q4_K_M, NF4 and other precision labels. There was no full-precision ablation, so a score difference cannot be assigned to quantization alone. Start/end serving digests were stable; upstream source pins are included where reported. The Perplexity and D3 routes did not report an immutable upstream weight revision.'),
      ('Cost, latency and partial-route limits retain their scope',
       'Local API access had no metered invoice; hardware purchase, electricity and depreciation were not measured. Local rows therefore have no invented zero-dollar operating cost. Hosted routes retain their original dates, network paths, concurrency and cost labels. Purple identifies local RTX 2060 runs, blue hosted decision models and pale yellow no-reasoning LLM references. Coba, NLI, Julia and KnowLine remain separately documented partial or blocked routes outside the full-bank ranking. No speed on newer hardware has been measured or projected.')]


def methods():
    return [
      '49 full-bank routes: 27 hosted decision models, 18 local decision/classifier models and four no-reasoning LLM references. All use the same 1,342 questions and 31 categories: 65,758 first attempts. The question bank, options, weights of categories and earlier 46 model records are unchanged.',
      'The two sequential local batches were measured October 25, 2026 (America/Toronto), using a user-reported NVIDIA RTX 2060 with 6 GB VRAM, Ollaya 0.17.0, and server-reported cuda:0 execution. This older GPU was chosen deliberately to test a more accessible hardware setup rather than require a recent high-end GPU. CPU model, system RAM, driver version and independent hardware identity were not captured. One request and one model ran at a time. The frozen native input packets and five-choice order were unchanged. Fresh LAN HTTP timing runs through the complete response; synthetic compatibility/loading/warm-up calls are excluded and separately recorded. The earlier 20-case CPU screen is not pooled into these GPU measurements.',
      'All 24,156 local first attempts remain in the denominator: 24,136 usable decisions and 20 unsuccessful responses, with no scored retries. Every full-bank median and p95 is pooled from all 1,342 original durations. The speed screen stops a route if cumulative median exceeds two seconds after at least 20 cases; the unusable-output screen pauses at 5%. Four blocked or partial routes remain separately documented.',
      'Same input and scoring support accuracy comparison across routes; latency remains specific to hardware, serving runtime, precision, local/cloud path, warm-up treatment, date and load. Local per-model metadata records quantization and available source pins. Registry digests and returned identities are not independent weight attestations. No claim is made about faster hardware without testing it.',
      'Native routes return typed choices and probability distributions. Local usable responses reported zero output tokens on these completed configurations; reported counters alone do not reveal undisclosed internal computation. Existing Sol, Sonnet, Opus and Qwen settings and qualification limits remain unchanged. This benchmark tests immediate five-choice decisions without tools or agentic iteration, not reasoning-enabled LLM performance.',
      'This remains a developing bank with uneven category sizes and dependent variants. Six categories contain eight questions each. Earlier targeted difficult-item audits, verified additions and the separate 1,305-case author-development diagnostic retain their scope; this update does not claim every original item received independent external verification.',
      'Public timing/status evidence reproduces coverage, means, medians and p95 without credentials or answer keys. Accuracy was checked locally against the existing revision-bound private key. Public aggregates and evidence hashes cannot independently reproduce private-key scoring. No key, model-choice ledger, per-item correctness, private path or LAN address is exported.']


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
    value=readable.markdown_groups(s,guide,details).replace('All 20 models','All 49 routes').replace('all 20 models','all 49 routes').replace(readable.NAME,NAME)
    import re
    return re.sub(r'https://etsabary.github.io/jev-1.14-comparison-benchmark/[^)# ]+/report.html',SITE,value)


def html(s,guide):
    import re
    old=(prior.DEST/'report.html').read_text();head=old[:old.index('<body>')+6]
    head=re.sub(r'<title>.*?</title>','<title>System 1 decisions: 49 routes, 18 local GPU models</title>',head)
    head=re.sub(r'content="opus5-october23-1342"', 'content="local-additions-october25-1342"',head)
    head=head.replace('</head>','<style>'+CSS+'</style></head>')
    body='<main><h1>System 1 Decision Benchmark</h1><p>27 hosted decision models, 18 local decision/classifier models and four no-reasoning LLM references. Same 1,342 questions, 31 categories. Updated October 25, 2026.</p>'
    body+='<nav><a href="#overview">All 49 routes</a><a href="#local-results">Local GPU results</a><a href="#new-additions">Findings</a><a href="#functions">Named categories</a><a href="#method">Method and setup</a></nav>'
    body+='<div class="cards"><div class="card"><div class="label">Highest overall</div><div class="big">86.0%</div><div class="small">Fastino GLiDE · 1154/1342</div></div><div class="card"><div class="label">Highest local score</div><div class="big">74.1%</div><div class="small">D3 Flash Artemis 9B · 408 ms median</div></div><div class="card"><div class="label">Deliberate older-GPU setup</div><div class="big">6 GB</div><div class="small">RTX 2060 · CUDA · Ollaya 0.17.0</div></div><div class="card"><div class="label">Full matched coverage</div><div class="big">49 routes</div><div class="small">65,758 first attempts · 31 categories</div></div></div>'
    body+='<div class="route-legend"><span><i class="swatch" style="background:#16728c"></i>Hosted decision models</span><span><i class="swatch" style="background:#7c3aed"></i>Local · RTX 2060 · 6 GB</span><span><i class="swatch" style="background:#f4df9a"></i>LLM references, reasoning off</span></div>'
    body+='<section id="overview"><h2>All 49 routes: accuracy, speed and cost</h2><p>Every row covers 1,342 first attempts. Purple identifies local runs; it does not change the green-to-red speed/cost bands or the accuracy heatmap. The dashed accuracy line marks 20% uniform guessing. Mean is blank where earlier evidence did not export it.</p><div class="figure"><a href="accuracy_speed_cost.svg"><img src="accuracy_speed_cost.png" alt="49 routes, with 18 local GPU models in purple and LLM references in pale yellow"></a></div>'+summary_html(s)+prior.tables.prior.prior.legend_html()+'</section>'
    body+='<section id="local-results"><h2>Local GPU results and profiles</h2><p class="local-note">The RTX 2060 with 6 GB VRAM was chosen deliberately as an older, more accessible setup. Ollaya 0.17.0; server-reported CUDA execution; sequential LAN calls. Loading and warm-ups excluded. Precision varies by model. Hardware identity was supplied by the user; CPU, system RAM and driver version were not captured. No newer-GPU speed or local operating cost has been measured.</p><div class="figure"><a href="local_models.svg"><img src="local_models.png" alt="All 18 completed local models: accuracy and median/p95 latency on RTX 2060"></a></div>'+local_profiles(s)+'</section>'
    body+='<section id="new-additions"><h2>What the expanded comparison shows</h2>'+''.join('<h3>'+escape(title)+'</h3><p>'+escape(text)+'</p>' for title,text in findings(s))+'</section>'
    body+='<section id="llm-references"><h2>Selected no-reasoning LLM references</h2><p>The four existing LLM references retain their settings and measurements. Sol uses explicit reasoning off; Sonnet and Opus use separately labelled constrained JSON choice. Opus refusals and missing telemetry remain in the record. Qwen uses the requested none setting with its existing telemetry qualification. Their full findings remain in the <a href="../opus5_reference_2026-10-23/report.html">October 23 report</a>.</p></section>'
    clarity=readable.clarity_section(s,guide).replace('All 20 models','All 49 routes').replace('all 20 models','all 49 routes')
    body+=mark_names(clarity,s)
    body+='<section id="quality"><h2>Delivered decisions and failures</h2><p>All 1,342 first attempts remain in every ranked score. Twenty local responses were unsuccessful: six truncations and 14 HTTP failures. The three new configurations account for 13 of those failures: three input-size rejections each for Perplexity and D3, and seven for Jebadiah 9B. The frozen questions were not shortened or retried. There were no scored retries.</p><div class="scroll">'+prior.tables.markdown.markdown(quality(s),extensions=['tables'])+'</div></section>'
    body+='<section id="screened"><h2>Partial and blocked routes</h2><p>Coba and NLI stopped at 20 cases after input truncation. Julia’s serving batch limit caused HTTP failures; KnowLine’s native one-token counter needs adapter review. They are excluded from the 49-route full-bank ranking. <a href="screened_routes.json">Screen details</a>.</p></section>'
    body+='<section id="method"><h2>Method, setup and interpretation</h2>'+''.join('<p>'+escape(p)+'</p>' for p in methods())+'</section>'
    body+='<section id="downloads"><h2>Data and verification</h2><p><a href="statistics.json">49-route aggregate JSON</a> · <a href="model_statistics.csv">Model CSV</a> · <a href="category_scores.csv">Category CSV</a> · <a href="local_timing_evidence.csv">24,156 answer-free timing rows</a> · <a href="local_model_metadata.json">Local setup and model metadata</a> · <a href="audit_receipt.json">Audit</a> · <a href="manifest.json">Manifest</a>.</p><p>Unchanged questions: <a href="../consolidated_2026-10-19/questions_1342.csv">CSV</a> · <a href="../consolidated_2026-10-19/questions_1342.jsonl">Native JSONL</a> · <a href="../consolidated_2026-10-19/questions_1342.txt">Readable text</a>. <a href="https://etsabary.github.io/visual-decision-benchmark/report.html">Separate image benchmark</a>; no image scores changed.</p></section></main></body></html>'
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
    intro='# System 1 Decision Benchmark\n\n27 hosted decision models, **18 local decision/classifier models** and four no-reasoning LLM references on the same **1,342 text questions across 31 categories**. Updated October 25, 2026.\n\n'
    intro+='**Fastino GLiDE remains highest overall at 86.0%. D3 Flash Artemis 9B leads the local batch at 74.1%, with a 408 ms median on an RTX 2060 with 6 GB VRAM.**\n\n'
    intro+='[Interactive report]('+SITE+') · [Local GPU profiles]('+SITE+'#local-results) · [Named, color-coded categories]('+SITE+'#functions)\n\n'
    intro+='![49 routes: local models in purple](results/releases/'+NAME+'/accuracy_speed_cost.png)\n\n'
    intro+='Purple marks **Local · RTX 2060 · 6 GB**. Blue marks hosted decision models; pale yellow marks LLM references. Accuracy cell colors and speed/cost bands keep their existing meaning. Every ranked row contains 1,342 first attempts. Local loading/warm-up calls are excluded; hosted timing paths and dates remain unchanged. Local hardware/electricity cost is unmeasured, rather than plotted as $0.\n\n'
    intro+='**The local tests deliberately use an older RTX 2060 with 6 GB VRAM, chosen to represent a more accessible hardware setup that readers may already have.** D3 leads all 18 tested local configurations; its measured latency is specific to this setup.\n\n'
    intro+='## Complete comparison\n\n'+table(['Model','Setting','Correct / 1342','Accuracy','Mean','Median','p95','Cost / 1000','Actual bank cost'],rows)+'\n\n'
    intro+=legend_markdown().replace('1,136-question','1,342-question')+'\n\n'
    end='## Categories, questions and evidence\n\n'+category_markdown(s,guide).replace(']('+NAME+'/','](results/releases/'+NAME+'/')
    end+='\n\nCurrent data: [aggregate JSON](results/releases/'+NAME+'/statistics.json), [model CSV](results/releases/'+NAME+'/model_statistics.csv), [category CSV](results/releases/'+NAME+'/category_scores.csv), [answer-free timing evidence](results/releases/'+NAME+'/local_timing_evidence.csv), [setup metadata](results/releases/'+NAME+'/local_model_metadata.json), [audit](results/releases/'+NAME+'/audit_receipt.json).\n\n'
    end+='Unchanged question bank: [native JSONL](results/releases/consolidated_2026-10-19/questions_1342.jsonl), [CSV](results/releases/consolidated_2026-10-19/questions_1342.csv), [readable text](results/releases/consolidated_2026-10-19/questions_1342.txt).\n\n'
    end+='Implementation: [scripts/](scripts/README.md). Current check: `python3 scripts/validate_local_additions_2026_10_25.py`. Historical checks include `python3 scripts/validate_opus5_release.py` and `python3 scripts/validate_october21_release.py`. All earlier releases remain unchanged.\n'
    write(ROOT/'README.md',intro+narrative+'\n\n'+end)
    write(repo_file('FUNCTIONS.md'),'# All 31 categories: 49 full-bank routes\n\n[Color-coded, named tables]('+SITE+'#functions). Purple model-name badges identify local RTX 2060 runs; cell colors always encode accuracy.\n\n'+category_markdown(s,guide,True).replace(']('+NAME+'/','](../results/releases/'+NAME+'/'))
    write(repo_file('OUTPUT_COMPLIANCE.md'),'# Delivered decisions and failures\n\n49 routes retain the 1,342-question first-attempt denominator. The local batch contains 24,136 usable decisions and 20 unsuccessful responses; no scored retries. Partial or blocked routes are documented separately and not ranked.\n\n'+quality(s))
    local_doc='# Local GPU runs: setup and model profiles\n\n18 complete runs on the unchanged 1,342-question bank, measured October 25, 2026. [Interactive local results]('+SITE+'#local-results).\n\n'
    local_doc+='**🟣 Local · NVIDIA RTX 2060 · 6 GB VRAM · Ollaya 0.17.0 · CUDA.** Hardware identity was supplied by the user; every completed route reported cuda:0. One request/model at a time over the LAN. Loading and synthetic warm-ups are excluded; the earlier CPU screen is separate. Precision varies by route. CPU, system RAM and driver version were not captured.\n\n'
    local_doc+='The RTX 2060 with 6 GB VRAM was chosen deliberately as an older, more accessible hardware setup. The purpose was to measure what readers can run on equipment they may already have. D3 Flash Artemis 9B is the leader among all 18 tested local configurations at 74.1%, with a 408 ms median.\n\n'
    local_doc+='Local API access was unmetered. Electricity and hardware costs were not measured. No latency on newer hardware is inferred. [Captured metadata](../results/releases/'+NAME+'/local_model_metadata.json) records source pins where available and the server-reported precision and digest. These are serving identities, not independent weight attestations.\n\n'
    local_doc+='Purple bars and model-name badges identify these local configurations. Accuracy heatmap cells retain the same 0–100% blue scale, and speed/cost colors retain their existing thresholds.\n\n'
    for mid in s['local_model_ids']:
        m=s['models'][mid]
        local_doc+='## '+m['label']+'\n\n'+f"{m['correct']}/1342 ({m['accuracy']:.1%}); mean / median / p95 {m['mean_response_ms']:.0f} / {m['median_ms']:.0f} / {m['p95_ms']:.0f} ms. Reported precision: {m['precision']}.\n\n"
        for title,key in [('Higher category scores','highest_scoring_categories'),('Lower category scores','lowest_scoring_categories')]:
            local_doc+=title+': '+ '; '.join(f"{readable.LABELS[c['family_id']]} {c['correct']}/{c['n']}" for c in m[key][:3])+'.\n\n'
    local_doc+='## Partial and blocked routes\n\nCoba 1B and the NLI representative stopped after 20 cases because one response each truncated the input. Julia had 19 HTTP failures in 20 attempts due to its physical batch limit. KnowLine returned a valid typed warm-up choice with output_tokens=1; that counter alone does not establish reasoning, and native adapter review is pending. These routes are documented in [screen details](../results/releases/'+NAME+'/screened_routes.json) and are not ranked as complete runs.\n\n'
    local_doc+='All profiles use observed category accuracy; their higher/lower lists select categories with at least 20 questions. The complete [named category matrix](../results/releases/'+NAME+'/category_scores.csv) also includes the six eight-question domains.\n'
    write(ROOT/'documents/LOCAL_GPU_RUNS.md',local_doc)
    for path in DEST.glob('*.svg'):write(path,'\n'.join(line.rstrip() for line in path.read_text().splitlines()))
    write(DEST/'manifest.json',dict(version='local-additions-20261025-v1', models=49, local_models=18,
        hosted_decision_models=27,llm_references=4,questions_each=1342,first_attempts=65758,
        bank_sha256=s['question_bank_sha256'],prior_statistics_sha256=digest(PREVIOUS/'statistics.json'),
        artifacts={p.name:digest(p) for p in sorted(DEST.iterdir()) if p.is_file() and p.name!='manifest.json'}))
    pages=ROOT/'docs'/NAME;pages.mkdir(parents=True,exist_ok=True)
    for path in DEST.iterdir():
        if path.is_file():shutil.copyfile(path,pages/path.name)
    write(ROOT/'docs/report.html',prior.tables.prior.rebase(page,NAME))
    for name,anchor in [('index.html',''),('functions.html','#functions'),('output_compliance.html','#quality')]:
        write(ROOT/'docs'/name,'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="benchmark-cohort" content="local-additions-october25-1342"><meta http-equiv="refresh" content="0;url=report.html'+anchor+'"><title>System 1 Decision Benchmark</title></head><body><a href="report.html'+anchor+'">Current 49-route comparison</a></body></html>')
    print('Built 49 full-bank routes, including 18 local configurations; no inference.')


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--capture',action='store_true');parser.add_argument('--refresh-unpublished',action='store_true')
    args=parser.parse_args()
    if args.capture:capture()
    build(args.refresh_unpublished)
    prior.bind_layout()
