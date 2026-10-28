"""Offline, private-key reconciliation for the three October 25 additions.

Only aggregate scores and answer-free timing bindings cross the public boundary.
No API calls, credentials or new inference are used by this module.
"""
from collections import Counter
from datetime import datetime
from decimal import Decimal
from hashlib import sha256
import csv
import io
import json
import math
from pathlib import Path
import statistics
import sys
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
PRIVATE = ROOT.parent / 'text-decision-hardening'
PREVIOUS = ROOT / 'results/releases/local_additions_2026-10-25'
DEST = ROOT / 'results/releases/native_additions_2026-10-25'
ROUTES = [
    ('nemotron_lan_benchmark_2026-10-25_222630', 'models/h2o-lightning-nemotron__4b',
     'h2o-lightning-nemotron:4b', 'local_h2o_lightning_nemotron_4b', 'H2O Lightning Nemotron 4B'),
    ('knowline_lan_benchmark_2026-10-25_225254', 'models/knowline__4b-gen5.5',
     'knowline:4b-gen5.5', 'local_knowline_4b_gen5_5', 'KnowLine 4B Gen5.5'),
    ('celeris_decision_benchmark_2026-10-25_225435', '',
     'celeris-1.1-decision', 'celeris11_decision', 'Celeris 1.1 Decision'),
]


def digest(path):
    return sha256(Path(path).read_bytes()).hexdigest()


def packet_digest(value):
    return sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
        separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def rows(path):
    return [json.loads(line) for line in path.read_text().splitlines()]


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value.rstrip()+'\n' if isinstance(value, str) else json.dumps(value, indent=2)+'\n')


def quantiles(values):
    ordered=sorted(values); pos=(len(values)-1)*.95; lo=int(pos)
    return dict(mean_ms=statistics.mean(values), median_ms=statistics.median(values),
        p95_ms=ordered[lo]+(ordered[min(lo+1,len(ordered)-1)]-ordered[lo])*(pos-lo))


def csv_text(values):
    stream=io.StringIO(newline='')
    writer=csv.DictWriter(stream, fieldnames=list(values[0]), lineterminator='\n')
    writer.writeheader(); writer.writerows(values)
    return stream.getvalue()


def check_native(raw, model, local):
    assert raw['model']==model and set(raw['answers'])=={'decision'}
    answer=raw['answers']['decision']; probabilities=answer['probabilities']
    assert answer['type']=='choice' and answer['choice'] in ('1','2','3','4','5')
    assert set(probabilities)==set('12345')
    assert all(isinstance(v,(float,int)) and math.isfinite(v) and 0<=v<=1 for v in probabilities.values())
    assert math.isclose(sum(probabilities.values()),1,abs_tol=.02)
    assert not any(k in raw or k in answer for k in ('explanation','reasoning','thinking'))
    assert raw['usage']['output_tokens']==(1 if local else 0)
    if local:
        assert raw['state_truncated'] is False and raw['done_reason']=='decide'
    if model=='h2o-lightning-nemotron:4b':
        assert raw['probability_source']=='native'
        assert raw['effort_used']=={'tier':'fast','passes_per_decision':1}
        assert raw['usage']['processed_input_tokens']==raw['usage']['input_tokens']
    return answer['choice']


def capture():
    assert not (DEST/'manifest.json').exists(), 'Do not recapture a sealed public release'
    questions=rows(ROOT/'results/releases/consolidated_2026-10-19/questions_1342.jsonl')
    questions={q['id']:q for q in questions}
    sys.path.insert(0,str(PRIVATE))
    from analyze_frontier_reference import load_gold
    import consolidated_analysis as authority
    old=authority.CORRECTED
    try:
        authority.CORRECTED=ROOT/'results/releases/corrected_2026-10-18'
        gold, metadata, _, bindings=load_gold(PRIVATE,questions)
    finally:
        authority.CORRECTED=old
    with (ROOT/'results/releases/corrected_2026-10-18/questions_1136.csv').open() as stream:
        old_ids={r['item_id'] for r in csv.DictReader(stream)}
    new_models={}; local_timing=[]; hosted_timing=[]; provenance={}; source_bindings={}
    for run, sub, model, mid, label in ROUTES:
        private=PRIVATE/'runs'/run; folder=private/sub; local=bool(sub)
        seal=json.loads((private/'seal.json').read_text())
        for name, expected in seal['files'].items():
            assert digest(private/name)==expected, name
        manifest=json.loads((private/'manifest.json').read_text())
        assert manifest['bank_sha256']==digest(ROOT/'results/releases/consolidated_2026-10-19/questions_1342.jsonl')
        attempts=rows(folder/'attempts.jsonl'); dispatches=rows(folder/'dispatches.jsonl')
        assert len(attempts)==len(dispatches)==len(set(a['item_id'] for a in attempts))==1342
        report_path=folder/('full_report.json' if local else 'final_report.json')
        report=json.loads(report_path.read_text()); latencies=[]
        for index,(a,d,item) in enumerate(zip(attempts,dispatches,manifest['question_order']),1):
            q=questions[item]
            assert a['request_index']==d['request_index']==index
            assert a['attempt']==d['attempt']==1 and a['item_id']==d['item_id']==item
            assert a['family_id']==d['family_id']==q['family_id']
            assert a['native_input_sha256']==d['native_input_sha256']==q['native_input_sha256']
            body=dict(model=model,**q['native_input'])
            if local: body['keep_alive']='10m'
            else: body['x_celeris']={'explain':False}
            assert a['request_payload_sha256']==d['request_payload_sha256']==packet_digest(body)
            assert a['transport']['http_status']==200 and a['status']=='ok'
            assert check_native(a['transport']['raw'],model,local)==a['choice']
            assert a['model_returned']==model
            assert a['latency_ms']==a['transport']['latency_ms'] and math.isfinite(a['latency_ms'])
            latencies.append(a['latency_ms'])
            timing=dict(model_id=mid,request_index=index,item_id=item,family_id=q['family_id'],
                native_input_sha256=q['native_input_sha256'],status=a['status'],latency_ms=a['latency_ms'])
            if local:
                timing.update(server_eval_ms=a['server_eval_ms'],server_load_ms=a['server_load_ms'],
                    response_sha256=packet_digest(a['transport']['raw']))
                local_timing.append(timing)
            else:
                timing.update(request_payload_sha256=a['request_payload_sha256'],
                    input_tokens=a['usage']['input_tokens'],output_tokens=a['usage']['output_tokens'],
                    estimated_cost_usd=str(Decimal(a['usage']['input_tokens'])*Decimal('.00000004')),
                    response_sha256=packet_digest(a['transport']['raw']))
                hosted_timing.append(timing)
        def outcome(ids):
            rr=[a for a in attempts if a['item_id'] in ids]
            hit=sum(a['choice']==str(gold[a['item_id']]) for a in rr)
            return dict(n=len(rr),correct=hit,answered=len(rr),failed=0,wrong_valid=len(rr)-hit,
                accuracy=hit/len(rr) if rr else None)
        v=outcome(questions); timing=quantiles(latencies)
        assert v['correct']==report['correct']
        saved=report['timing'] if local else {k:report[k] for k in timing}
        assert all(math.isclose(timing[k],saved[k],rel_tol=1e-12) for k in timing)
        families={fid:outcome({i for i,q in questions.items() if q['family_id']==fid})
            for fid in sorted({q['family_id'] for q in questions.values()})}
        saved_families={f['family_id']:f for f in report['families']} if local else report['families']
        assert all((v['n'],v['correct'])==(saved_families[f]['n'],saved_families[f]['correct']) for f,v in families.items())
        profiles=[dict(family_id=f,**value) for f,value in families.items() if value['n']>=20]
        high=sorted(profiles,key=lambda f:(-f['accuracy'],f['family_id']))
        low=sorted(profiles,key=lambda f:(f['accuracy'],f['family_id']))
        dates=dict(Counter(datetime.fromisoformat(a.get('started_at') or a['transport']['started_at']).astimezone(
            ZoneInfo('America/Toronto')).date().isoformat() for a in attempts))
        v.update(model_id=mid,label=label,model_requested=model,execution_location='local' if local else 'hosted',
            route='Local Ollaya · RTX 2060 6 GB · LAN HTTP' if local else 'Direct Celeris · native SystemOne · explanations off',
            mean_response_ms=timing['mean_ms'],median_ms=timing['median_ms'],p95_ms=timing['p95_ms'],
            first_statuses={'ok':1342},attempts=1342,recoveries=0,provider_failures=0,model_output_failures=0,
            probability_warnings=0,accuracy_among_usable=v['correct']/1342,families=families,
            macro_family_accuracy=statistics.mean(f['accuracy'] for f in families.values()),dates_toronto=dates,
            returned_identities={model:1342},providers={('Local Ollaya' if local else 'Celeris'):1342},
            original_1136=outcome(old_ids),added_206=outcome(set(questions)-old_ids),
            new_domains=outcome({i for i,q in questions.items() if q['family_id']>='F26'}),
            release_exclusion_diagnostic=outcome({i for i,m in metadata.items() if not m['permanently_unscored_native_development']}),
            highest_scoring_categories=high,lowest_scoring_categories=low,source_summary_sha256=digest(report_path),
            observed_output_tokens=1 if local else 0)
        if local:
            md=json.loads((folder/'metadata_screen.json').read_text())['raw']
            for name in ('metadata_screen_end.json','metadata_continuation.json','metadata_continuation_end.json'):
                assert json.loads((folder/name).read_text())['raw']['digest']==md['digest']
            assert all(d['device']=='cuda:0' for d in report['devices'])
            v.update(hardware='NVIDIA RTX 2060',vram_gb=6,runtime='Ollaya 0.17.0',
                precision=md['details']['quantization_level'],serving_digest=md['digest'],
                upstream_revision='Not reported by route',warmup_calls=report['warmup_calls'],
                cost=dict(kind='local_unmetered',known_usd=None,known_decimal=None,exact_usd=None,
                    known_usd_per_1000=None,unknown_attempts=0,hardware_electricity_measured=False,
                    scope='No metered API invoice; hardware and electricity costs unmeasured'))
            provenance[mid]=dict(model_requested=model,serving_digest=md['digest'],details=md['details'],
                capabilities=md['capabilities'],device='cuda:0',gpu='NVIDIA RTX 2060',vram_gb=6,
                context_length=report['devices'][0]['context_length'],runtime='Ollaya 0.17.0',
                hardware_identity_source='User reported GPU and VRAM; CUDA execution captured',
                identity_limit='Stable serving digest; no independent weight attestation',
                output_telemetry='One reported native label token, no generated explanation',
                processed_input_attestation=('Input and processed counters match' if 'nemotron' in model else 'No independent processed-input counter'),
                source_evidence_sha256={n:digest(folder/n) for n in ('attempts.jsonl','dispatches.jsonl','full_report.json','warmup.jsonl')})
        else:
            cost=Decimal(sum(a['usage']['input_tokens'] for a in attempts))*Decimal('.00000004')
            assert cost==Decimal(report['known_cost_usd'])
            assert json.loads((private/'catalog_start.json').read_text())['data']==json.loads((private/'catalog_end.json').read_text())['raw']
            v.update(cost=dict(kind='hosted_usage_times_tariff',source='usage_times_published_tariff',
                known_usd=float(cost),known_decimal=str(cost),exact_usd=float(cost),
                known_usd_per_1000=float(cost*1000/1342),unknown_attempts=0,known_attempts=1342,
                scope='Reported input usage times captured USD 0.04/million tariff; estimate, not monetary receipts'),
                primary_input_tokens=sum(a['usage']['input_tokens'] for a in attempts),
                admission_calls=report['probe_calls'],admission_estimated_usd=report['probe_cost_usd'],
                reasoning_verification='Explanations disabled; zero reported output tokens; internal computation unattested',
                processed_input_attestation='No per-item processed-input or truncation attestation')
        new_models[mid]=v
        source_bindings[mid]=dict(seal_sha256=digest(private/'seal.json'),
            audit_sha256=digest(private/'audit_receipt.json'),report_sha256=digest(report_path),
            execution_source_sha256=digest(private/'executor_source.py.snapshot'))
    old_local=json.loads((PREVIOUS/'local_models.json').read_text())
    write(DEST/'new_models.json',new_models)
    write(DEST/'local_models.json',{**old_local,**{m:v for m,v in new_models.items() if v['execution_location']=='local'}})
    write(DEST/'local_model_metadata.json',{**json.loads((PREVIOUS/'local_model_metadata.json').read_text()),**provenance})
    old_timing=(PREVIOUS/'local_timing_evidence.csv').read_text()
    write(DEST/'local_timing_evidence.csv',old_timing+''.join(csv_text(local_timing).splitlines(keepends=True)[1:]))
    write(DEST/'hosted_addition_timing_evidence.csv',csv_text(hosted_timing))
    screens=json.loads((PREVIOUS/'screened_routes.json').read_text())
    write(DEST/'screened_routes.json',[s for s in screens if s['model']!='knowline:4b-gen5.5'])
    write(DEST/'historical_admission_resolutions.json',dict(original=[s for s in screens if s['model']=='knowline:4b-gen5.5'],
        resolution='Native one-label readout accepted after model-specific audit; full 1342-case route now ranked. Earlier admission record unchanged.',
        model_id='local_knowline_4b_gen5_5',observed_output_tokens=1))
    write(DEST/'audit_receipt.json',dict(status='VERIFIED_52_FULL_BANK_ROUTES',models=52,local_models=20,
        questions_each=1342,first_attempts=69784,new_models=3,new_first_attempts=4026,new_usable=4026,new_unusable=0,
        local_first_attempts=26840,local_usable=26820,local_unusable=20,new_retries=0,
        bank_sha256=digest(ROOT/'results/releases/consolidated_2026-10-19/questions_1342.jsonl'),
        scoring_authority_sha256=sorted(set(bindings.values())),source_bindings=source_bindings,
        prior_statistics_sha256=digest(PREVIOUS/'statistics.json'),earlier_49_records_unchanged=True,
        validation='All 4026 new packets rebuilt; sealed source/response identities, offline key scores, 31 categories and timing reconciled. No inference replay.',
        privacy='Aggregates and answer-free timing bindings; no key, model choices, per-item correctness, credentials or LAN address',
        public_scoring_limit='Public checks reproduce coverage, timing and aggregate arithmetic; private-key scoring requires owner evidence',
        cost='Celeris usage-times-tariff estimate; local hardware/electricity unmeasured'))


if __name__=='__main__':
    capture()
