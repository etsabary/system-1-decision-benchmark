"""Reconcile saved native text decisions offline; export aggregates, never keys."""
from collections import Counter
from copy import deepcopy
from decimal import Decimal
from hashlib import sha256
import csv,io,json,math,random,statistics,sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PRIVATE=ROOT.parent/'text-decision-hardening'
CAPTURE=PRIVATE/'runs/d3_ultra_liquid11_2026-10-27_222502'
OLD=ROOT/'results/releases/native_additions_2026-10-25'
DEST=ROOT/'results/releases/native_updates_2026-10-27'
MODELS={'d3_ultra':('d3_ultra','D3 Ultra','vllm-sr/d3-ultra'),
        'liquid11':('liquid11_decision','Liquid d1.1','liquid/d1.1')}

def digest(p):return sha256(Path(p).read_bytes()).hexdigest()
def canonical(v):return json.dumps(v,sort_keys=True,ensure_ascii=False,separators=(',',':'),allow_nan=False).encode()
def packet(v):return sha256(canonical(v)).hexdigest()
def rows(p):return [json.loads(s) for s in Path(p).read_text().splitlines()]
def write(p,v):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(v.rstrip()+'\n' if isinstance(v,str) else json.dumps(v,indent=2)+'\n')

def payload(q,mid):
    b=dict(model=MODELS[mid][2],**q['native_input'])
    if mid=='liquid11':b['provider']=dict(only=['liquid'],allow_fallbacks=False,require_parameters=True)
    return b

def capture():
    assert not (DEST/'manifest.json').exists(),'Never overwrite a sealed release'
    seal=json.loads((CAPTURE/'seal.json').read_text())
    for name,h in seal['files_sha256'].items():assert digest(CAPTURE/name)==h,name
    qs=rows(ROOT/'results/releases/consolidated_2026-10-19/questions_1342.jsonl');qq={q['id']:q for q in qs}
    order=list(qq);random.Random(2026101906).shuffle(order)
    sys.path.insert(0,str(PRIVATE))
    from analyze_frontier_reference import load_gold
    import consolidated_analysis as authority
    previous=authority.CORRECTED
    try:
        authority.CORRECTED=ROOT/'results/releases/corrected_2026-10-18'
        gold,metadata,names,bindings=load_gold(PRIVATE,qq)
    finally:authority.CORRECTED=previous
    originals={r['item_id'] for r in csv.DictReader((ROOT/'results/releases/corrected_2026-10-18/questions_1136.csv').open())}
    new={};timings=[];provenance={}
    for folder,(mid,label,model) in MODELS.items():
        p=CAPTURE/folder;report=json.loads((p/'final_report.json').read_text());audit=json.loads((p/'audit_receipt.json').read_text())
        manifest=json.loads((p/'manifest.json').read_text());aa=rows(p/'attempts.jsonl');dd=rows(p/'dispatches.jsonl')
        assert audit['status']=='PASS' and report['state']=='complete'
        assert len(aa)==len(dd)==len({a['item_id'] for a in aa})==1342
        assert [a['item_id'] for a in aa]==manifest['order']==order
        for i,(a,d) in enumerate(zip(aa,dd),1):
            q=qq[a['item_id']];raw=a['transport']['raw_response'];answer=raw['answers']['decision']
            assert a['attempt']==d['attempt']==1 and a['request_index']==d['request_index']==i
            assert a['request_payload_sha256']==d['request_payload_sha256']==packet(payload(q,folder))
            assert a['native_input_sha256']==q['native_input_sha256'] and a['family_id']==q['family_id']
            assert a['status']=='ok' and a['transport']['http_status']==200 and answer['type']=='choice'
            assert answer['choice']==a['choice'] and a['choice'] in set('12345')
            assert raw['usage']['output_tokens']==0 and not any(raw.get(k) or answer.get(k) for k in ('reasoning','reasoning_content','explanation','text','content'))
            assert raw['model'] in ([model] if folder=='d3_ultra' else ['liquid/d1.1','liquid/d1.1-20261027'])
            if folder=='liquid11':assert raw['provider']=='Liquid' and a['reported_cost_usd'] is not None
            assert a['latency_ms']==a['transport']['latency_ms']
            timings.append(dict(model_id=mid,request_index=i,item_id=a['item_id'],family_id=q['family_id'],native_input_sha256=q['native_input_sha256'],
                request_payload_sha256=a['request_payload_sha256'],model_returned=a['model_returned'],status=a['status'],attempt=1,
                latency_ms=a['latency_ms'],input_tokens=a['usage']['input_tokens'],output_tokens=0,
                reported_cost_usd=a['reported_cost_usd'],cost_source=a['cost_source'],response_sha256=packet(raw)))
        def outcome(ids):
            rr=[a for a in aa if a['item_id'] in ids];hit=sum(a['choice']==str(gold[a['item_id']]) for a in rr)
            return dict(n=len(rr),correct=hit,answered=len(rr),failed=0,wrong_valid=len(rr)-hit,accuracy=hit/len(rr) if rr else None)
        v=outcome(qq);assert v['correct']==report['correct']
        families={f:outcome({i for i,q in qq.items() if q['family_id']==f}) for f in sorted(names)}
        assert all((f['n'],f['correct'])==(report['families'][fid]['n'],report['families'][fid]['correct']) for fid,f in families.items())
        xs=sorted(a['latency_ms'] for a in aa);pos=(len(xs)-1)*.95;lo=int(pos)
        timing=dict(mean_response_ms=statistics.mean(xs),median_ms=statistics.median(xs),p95_ms=xs[lo]+(xs[lo+1]-xs[lo])*(pos-lo))
        assert all(math.isclose(timing[k],report['mean_ms' if k=='mean_response_ms' else k],rel_tol=1e-12) for k in timing)
        for i in range(20,1343):assert statistics.median(a['latency_ms'] for a in aa[:i])<=2000
        profiles=[dict(family_id=f,**value) for f,value in families.items() if value['n']>=20]
        v.update(model_id=mid,label=label,model_requested=model,execution_location='hosted',
            route='Direct D3 native SystemOne; explicit Ultra identity' if folder=='d3_ultra' else 'OpenRouter native Decisions; pinned Liquid provider',
            **timing,first_statuses={'ok':1342},attempts=1342,recoveries=0,provider_failures=0,model_output_failures=0,
            probability_warnings=report['probability_warnings'],accuracy_among_usable=v['accuracy'],families=families,
            macro_family_accuracy=statistics.mean(f['accuracy'] for f in families.values()),dates_toronto=report['dates_toronto'],
            returned_identities=report['returned_identities'],providers=report['providers'],observed_output_tokens=0,
            original_1136=outcome(originals),added_206=outcome(set(qq)-originals),new_domains=outcome({i for i,q in qq.items() if q['family_id']>='F26'}),
            release_exclusion_diagnostic=outcome({i for i,m in metadata.items() if not m['permanently_unscored_native_development']}),
            highest_scoring_categories=sorted(profiles,key=lambda f:(-f['accuracy'],f['family_id'])),
            lowest_scoring_categories=sorted(profiles,key=lambda f:(f['accuracy'],f['family_id'])),admission_calls=2,admission_cost_usd=report['admission_cost_usd'])
        if folder=='d3_ultra':
            v['cost']=dict(known_usd=None,known_decimal=None,known_usd_per_1000=None,exact_usd=None,unknown_attempts=1342,
                public_free_access=True,accounted_access_cost_usd=0.0,scope='Free public API access at test time; no monetary receipts or permanent production tariff')
        else:
            cost=sum((Decimal(str(a['reported_cost_usd'])) for a in aa),Decimal(0));assert cost==Decimal(report['cost_known_usd'])
            v['cost']=dict(known_usd=float(cost),known_decimal=str(cost),exact_usd=float(cost),known_usd_per_1000=float(cost*1000/1342),
                known_attempts=1342,unknown_attempts=0,source='api_reported',scope='API-reported USD charges; admission probes separate')
        new[mid]=v
        provenance[mid]=dict(requested_model=model,returned_identities=v['returned_identities'],selected_catalog=manifest['selected_catalog'],
            selected_catalog_unchanged=True,input='Exact frozen 1342 native packets',concurrency=1,scored_retries=0,
            source_evidence_sha256={n:digest(p/n) for n in ('manifest.json','attempts.jsonl','dispatches.jsonl','admission.jsonl','final_report.json','audit_receipt.json','catalog_start.json','catalog_end.json','executor_source.py.snapshot')},
            private_seal_sha256=digest(CAPTURE/'seal.json'),identity_limit='Named/dated route metadata, not immutable hosted-weight attestation')
    s=deepcopy(json.loads((OLD/'statistics.json').read_text()));prior=deepcopy(s['models']);s['models'].update(new)
    s['hosted_model_ids']+=list(new)
    for m in new:s['model_kinds'][m]='Decision model'
    s['ranked_model_ids']=sorted(s['models'],key=lambda m:(-s['models'][m]['correct'],m))
    s['decision_model_ids']=[m for m in s['ranked_model_ids'] if m not in s['reference_model_ids']]
    s.update(status='COMPLETE_54_ROUTES_20_LOCAL_1342',model_count=54,decision_model_count=50,hosted_decision_model_count=30,
        primary_cases=72468,all_tested_primary_cases=72468,added_model_ids=list(new),updated_date_toronto='2026-10-27',
        prior_statistics_sha256=digest(OLD/'statistics.json'),total_http_attempts=sum(m['attempts'] for m in s['models'].values()),
        total_recoveries=sum(m['recoveries'] for m in s['models'].values()))
    assert all(s['models'][mid]==v for mid,v in prior.items())
    write(DEST/'statistics.json',s);write(DEST/'new_models.json',new);write(DEST/'october27_model_metadata.json',provenance)
    stream=io.StringIO(newline='');w=csv.DictWriter(stream,fieldnames=list(timings[0]),lineterminator='\n');w.writeheader();w.writerows(timings)
    write(DEST/'october27_timing_evidence.csv',stream.getvalue())
    write(DEST/'audit_receipt.json',dict(status='VERIFIED_54_ROUTES',models=54,first_attempts=72468,new_models=2,new_first_attempts=2684,
        new_usable=2684,new_unusable=0,retries=0,earlier_52_records_unchanged=True,private_seal_sha256=digest(CAPTURE/'seal.json'),
        scoring_authority_sha256=sorted(set(bindings.values())),bank_sha256=s['question_bank_sha256'],
        privacy='Aggregates and answer-free timing only; no model choices, keys, per-item correctness, credentials or LAN addresses',
        scoring_limit='Owner reconciled revision-bound private scoring offline; public exports verify timing, coverage and arithmetic'))
    import shutil
    for name in ['local_models.json','local_model_metadata.json','local_timing_evidence.csv','screened_routes.json','historical_admission_resolutions.json','hosted_addition_timing_evidence.csv']:
        shutil.copyfile(OLD/name,DEST/name)
    print('Captured 2684 native text decisions offline; 52 earlier records exact')

if __name__=='__main__':capture()
