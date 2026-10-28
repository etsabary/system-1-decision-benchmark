"""Offline export and analysis of October 16 regular-LLM additions.

No inference or credentials. Frozen fourteen-model evidence remains unchanged.
Only an external original key may score saved choices; no per-item correctness
or answer key is exported.
"""
from repo_layout import logical_relative, repo_file
from repo_layout import frozen_file
import argparse
from collections import Counter
from copy import deepcopy
from decimal import Decimal
from hashlib import sha256
import csv
import json
from pathlib import Path

from analysis_core import metrics, correct, valid, panels, panel_summary
import matched_analysis as prior
import overall_analysis as native_additions
from score_expansion import load_key, normalized_llm
import text_models as chat

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = repo_file('llm_additions_2026-10-16', root=ROOT)
OVERALL = repo_file('overall_expanded_2026-10-16', root=ROOT)
BASE_SUMMARY = repo_file('overall_2026-10-16/summary.json', root=ROOT)
MODELS = {
    'nemotron35lightning':('Nemotron 3.5 Lightning','nvidia/nemotron-3.5-lightning','coreweave/bf16','CoreWeave',repo_file('runs/nemotron_2026-10-16', root=ROOT)),
    'haiku55':('Claude Haiku 5.5','anthropic/claude-haiku-5.5','anthropic','Anthropic',repo_file('runs/text_field_2026-10-16/haiku55', root=ROOT)),
    'glm47flash':('GLM 4.7 Flash','z-ai/glm-4.7-flash','cloudflare','Cloudflare',repo_file('runs/text_field_2026-10-16/glm47flash', root=ROOT)),
    'deepseek41flash':('DeepSeek V4.1 Flash','deepseek/deepseek-v4.1-flash','deepinfra/fp8','DeepInfra',repo_file('runs/text_field_2026-10-16/deepseek41flash', root=ROOT)),
    'mimo26flash':('MiMo V2.6 Flash','xiaomi/mimo-v2.6-flash','xiaomi/fp8','Xiaomi',repo_file('runs/text_field_2026-10-16/mimo26flash', root=ROOT)),
    'qwen38flash':('Qwen3.8 Flash','qwen/qwen3.8-flash','alibaba/us-east-1','Alibaba',repo_file('runs/text_field_2026-10-16/qwen38flash', root=ROOT)),
    'tencenthy3':('Tencent Hy3','tencent/hy3','tencent/fp8','Tencent',repo_file('runs/text_field_2026-10-16/tencenthy3', root=ROOT)),
    'nemotron35supervl':('Nemotron 3.5 Super VL','nvidia/nemotron-3.5-super-vl','crusoe/bf16','Crusoe',repo_file('runs/text_field_2026-10-16/nemotron35supervl', root=ROOT)),
}
FORMAT_FAILURE_CUTOFF = Decimal('0.05')


def compliance(attempts):
    """Separate model-output failures from HTTP, body-read and error envelopes."""
    def provider_failure(a):
        raw=a.get('raw_response') or {}
        return bool(a.get('transport_failure') or a.get('error') or
                    a.get('http_status')!=200 or raw.get('error'))
    failures=sum(a['status']!='ok' and not provider_failure(a) for a in attempts)
    provider=sum(provider_failure(a) for a in attempts)
    return {'planned':1136,'recorded_first_attempts':len(attempts),
            'usable_first_answers':sum(a['status']=='ok' for a in attempts),
            'model_output_failures':failures,'provider_transport_failures':provider,
            'model_output_failure_fraction':failures/1136,
            'eligible_for_main_comparison':Decimal(failures)/Decimal(1136)<FORMAT_FAILURE_CUTOFF}


def write(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,indent=2,ensure_ascii=False,allow_nan=False)+'\n')


def payload(question,model_id):
    _,model,tag,_,_=MODELS[model_id]
    return {'model':model,'messages':[{'role':'user','content':question['prompt_text']+chat.SUFFIX}],
            'max_tokens':16,'stream':False,'usage':{'include':True},
            'provider':{'only':[tag],'allow_fallbacks':False,'require_parameters':True},
            'reasoning':{'enabled':False}}


def parse(record):
    value=chat.parse(record)
    if value['reasoning_text_present'] or value['reported_reasoning_tokens'] not in (None,0):
        value['status']='unexpected_reasoning'
        value['choice']=None
    return value


def sanitized(raw):
    result={k:raw[k] for k in ('id','model','provider') if k in raw}
    if isinstance(raw.get('choices'),list):
        result['choices']=[]
        for c in raw['choices']:
            message=c.get('message') or {}
            result['choices'].append({**{k:c[k] for k in ('index','finish_reason','native_finish_reason') if k in c},
                'message':{k:message[k] for k in ('role','content','refusal','reasoning','reasoning_content','reasoning_details') if k in message}})
    usage=raw.get('usage')
    if isinstance(usage,dict):
        result['usage']={k:usage[k] for k in ('prompt_tokens','completion_tokens','total_tokens','cost','input_tokens','output_tokens') if k in usage}
        for name,allowed in [('completion_tokens_details',('reasoning_tokens','audio_tokens','accepted_prediction_tokens','rejected_prediction_tokens')),
                             ('prompt_tokens_details',('cached_tokens','audio_tokens'))]:
            if isinstance(usage.get(name),dict):
                result['usage'][name]={k:usage[name][k] for k in allowed if k in usage[name]}
    if isinstance(raw.get('error'),dict):
        err=raw['error']
        result['error']={k:err[k] for k in ('code','message') if k in err}
        md=err.get('metadata') or {}
        result['error']['metadata']={k:md[k] for k in ('provider_name','provider_error_code','limit_source') if k in md}
    return result


def export_probes():
    base=repo_file('runs/text_field_2026-10-16', root=ROOT)
    probes=[]
    for path in sorted(base.glob('*/compatibility_probe*.json')):
        a=json.loads(path.read_text())
        raw=sanitized(a['raw_response'])
        probes.append({'model_id':path.parent.name,'model_requested':a['model_requested'],
                       'item_id':a['item_id'],'request_payload_sha256':a['request_payload_sha256'],
                       'stage':'compatibility_not_scored','retry_probe':path.stem.endswith('_retry'),
                       'http_status':a['http_status'],'status':a['status'],
                       'started':a['started'],'completed':a['completed'],'latency_ms':a['latency_ms'],
                       'reported_cost_usd':a['reported_cost_usd'],'raw_response':raw})
    write(PUBLIC/'compatibility_probes.json',{
        'included_in_scored_benchmark_costs':False,'probe_count':len(probes),
        'known_reported_cost_usd':float(sum((Decimal(str(p['reported_cost_usd'])) for p in probes if p['reported_cost_usd'] is not None),Decimal(0))),
        'unknown_charge_attempts':sum(p['reported_cost_usd'] is None for p in probes),
        'excluded_candidate':{'model':'z-ai/glm-5.3-flash','provider_tag':'deepinfra/fp4',
                              'reason':'HTTP 400: Reasoning is mandatory for this endpoint and cannot be disabled.',
                              'scored_questions':0,'replacement':'GLM 4.7 Flash, approved by benchmark author'},
        'probes':probes})


def export(model_id):
    source=MODELS[model_id][4]
    dest=PUBLIC/model_id
    completion=json.loads((source/'completion.json').read_text())
    assert completion['status']=='COMPLETE_1136'
    for name,expected in completion['files_sha256'].items():
        assert sha256((source/name).read_bytes()).hexdigest()==expected,name
    manifest=json.loads((source/'manifest.json').read_text())
    plan=manifest.pop('request_plan')
    data={'run_manifest.json':json.dumps(manifest,indent=2,ensure_ascii=False)+'\n',
          'request_plan.jsonl':''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in plan)}
    for name in ('software.json','model_metadata.json','dispatches.jsonl','results.jsonl','retry_waits.jsonl'):
        data[name]=(source/name).read_text() if (source/name).exists() else ''
    attempts=[]
    for value in chat.rows(source/'attempts.jsonl'):
        record=deepcopy(value)
        record['raw_response']=sanitized(value['raw_response'])
        record['usage']=record['raw_response'].get('usage') or {}
        attempts.append(record)
    data['attempts.jsonl']=''.join(json.dumps(r,ensure_ascii=False,allow_nan=False)+'\n' for r in attempts)
    software=json.loads(data['software.json'])
    source_map={}
    for name,expected in software.items():
        p=repo_file(name, root=ROOT)
        assert sha256(p.read_bytes()).hexdigest()==expected,name
        if name.startswith('runs/'):
            exported='source/'+name.removeprefix('runs/')
            data[exported]=p.read_text()
            source_map[name]=exported
        else:
            source_map[name]='repository:'+name
    continuation=source/'continuation_receipt.json'
    if continuation.exists():
        receipt=json.loads(continuation.read_text())
        helper=repo_file(receipt['source_path'], root=ROOT)
        assert sha256(helper.read_bytes()).hexdigest()==receipt['source_sha256']
        prefix=(source/'attempts.jsonl').read_bytes()[:receipt['existing_attempts_prefix_bytes']]
        assert sha256(prefix).hexdigest()==receipt['existing_attempts_prefix_sha256']
        data['continuation_receipt.json']=continuation.read_text()
        data['source/resume_envelope_errors.py']=helper.read_text()
    data['source_audit.json']=json.dumps({'completed':completion['completed'],
        'source_run_files_sha256':completion['files_sha256'],'frozen_source_map':source_map,
        'sanitization':'Allowlisted response identity, generated answer, usage and basic errors. Account metadata and credentials removed. No key or per-question correctness.',
        'original_fourteen_summary_sha256':sha256(BASE_SUMMARY.read_bytes()).hexdigest()},indent=2)+'\n'
    dest.mkdir(parents=True,exist_ok=True)
    for name,text in data.items():
        p=dest/name
        if p.exists():
            assert p.read_text()==text,'Do not replace existing public run evidence: '+str(p)
        else:
            p.parent.mkdir(parents=True,exist_ok=True)
            p.write_text(text)
    checksums={name:sha256((dest/name).read_bytes()).hexdigest() for name in sorted(data)}
    if (dest/'checksums.json').exists():
        assert json.loads((dest/'checksums.json').read_text())==checksums
    else:
        write(dest/'checksums.json',checksums)


def validate_model(model_id):
    dest=PUBLIC/model_id
    for name,expected in json.loads((dest/'checksums.json').read_text()).items():
        assert sha256((dest/name).read_bytes()).hexdigest()==expected,name
    audit=json.loads((dest/'source_audit.json').read_text())
    assert audit['original_fourteen_summary_sha256']==sha256(BASE_SUMMARY.read_bytes()).hexdigest()
    for original,expected in json.loads((dest/'software.json').read_text()).items():
        mapped=audit['frozen_source_map'][original]
        path=frozen_file(repo_file(mapped.removeprefix('repository:'), root=ROOT)) if mapped.startswith('repository:') else dest/mapped
        assert sha256(path.read_bytes()).hexdigest()==expected,original
    receipt_path=dest/'continuation_receipt.json'
    if receipt_path.exists():
        receipt=json.loads(receipt_path.read_text())
        assert not receipt['request_or_timer_or_scoring_changes']
        assert sha256((dest/'source/resume_envelope_errors.py').read_bytes()).hexdigest()==receipt['source_sha256']
    manifest=json.loads((dest/'run_manifest.json').read_text())
    assert manifest['questions_sha256']==sha256((repo_file('data/questions_1136.csv', root=ROOT)).read_bytes()).hexdigest()
    qs={r['item_id']:r for r in prior.d.read_csv(repo_file('data/questions_1136.csv', root=ROOT))}
    plan,attempts,results=(chat.rows(dest/name) for name in ('request_plan.jsonl','attempts.jsonl','results.jsonl'))
    assert len(plan)==len(results)==1136
    assert set(p['item_id'] for p in plan)==set(qs)
    prior.d.reconcile(chat.rows(dest/'dispatches.jsonl'),attempts,results,plan)
    indexed={p['request_index']:p for p in plan}
    for p in plan:
        body=payload(qs[p['item_id']],model_id)
        assert p['request_payload_sha256']==prior.d.digest(body)
        assert p['message_sha256']==prior.d.digest(body['messages'])
        assert p['request_body_bytes']==len(prior.d.canonical(body))
    for a in attempts:
        assert all(a[k]==v for k,v in indexed[a['request_index']].items())
        for k,v in parse(a).items():
            assert a[k]==v,k
        raw=a.get('raw_response') or {}
        envelope=(a['http_status']==200 and not raw.get('choices') and isinstance(raw.get('error'),dict)
                  and raw['error'].get('code') in prior.d.TRANSIENT)
        if envelope:
            assert (dest/'continuation_receipt.json').exists()
            assert a['status']!='ok' and a['choice'] is None
        if a['http_status']==200 and not a['error'] and not envelope:
            assert a['provider']==MODELS[model_id][3]
            assert a['model_returned'] in (MODELS[model_id][1],manifest['required_metadata_snapshot'])
            assert a['reported_cost_usd'] is not None
            assert not a['reasoning_text_present'] and a['reported_reasoning_tokens'] in (None,0)
    first,eventual=chat.first_and_eventual(attempts)
    assert len(first)==len(eventual)==1136
    for r in results:
        i=r['request_index']
        assert r['first_status']==first[i]['status'] and r['eventual_status']==eventual[i]['status']
        assert r['attempts']==eventual[i]['attempt']
    return first,eventual,attempts


def analyze(key_path,write_output=False):
    keys=load_key(key_path)
    base=json.loads(BASE_SUMMARY.read_text())
    native_first,_,_=prior.validate_refresh()
    llm_first,_=chat.first_and_eventual(chat.rows(prior.EXPANSION/'attempts.jsonl'))
    model_rows={m:[normalized_llm(a) for a in llm_first.values() if a['model_requested']==m] for m in chat.MODELS}
    output_compliance={m:compliance([a for a in llm_first.values() if a['model_requested']==m]) for m in chat.MODELS}
    for model,spec in prior.d.MODELS.items():
        model_rows[spec[0]]=[prior.normalized_native(a) for a in native_first.values() if a['model_requested']==model]
        output_compliance[spec[0]]=compliance([a for a in native_first.values() if a['model_requested']==model])
    for m in base['added_model_ids']:
        first,_,_=native_additions.validate_model(m)
        model_rows[m]=[prior.normalized_native(a) for a in first.values()]
        output_compliance[m]=compliance(list(first.values()))
    for m,rr in model_rows.items():
        assert metrics(rr,keys)==base['models'][m]['primary']
    summary=deepcopy(base)
    models=summary['models']
    metadata={r['item_id']:r for r in prior.d.read_csv(repo_file('data/item_metadata.csv', root=ROOT))}
    selection=json.loads((repo_file('data/selection_manifest.json', root=ROOT)).read_text())
    added=[m for m in MODELS if (PUBLIC/m/'checksums.json').exists()]
    assert added
    all_new=[]
    for m in added:
        first,eventual,attempts=validate_model(m)
        ff=list(first.values())
        output_compliance[m]=compliance(ff)
        normalized=[normalized_llm(a) for a in ff]
        model_rows[m]=normalized
        spec=MODELS[m]
        cost=chat.money(attempts)
        models[m]={'label':spec[0],'model_requested':spec[1],'provider_tag':spec[2],'provider_name':spec[3],
            'route':'OpenRouter','condition':'regular_llm_reasoning_off_added_october_16',
            'primary':metrics(normalized,keys),'eventual':metrics([normalized_llm(a) for a in eventual.values()],keys),
            'statuses_first':dict(Counter(a['status'] for a in ff)),
            'http_status_first':dict(Counter(str(a['http_status']) for a in ff)),
            'provider_error_envelopes_first':sum(a['http_status']==200 and bool(a['raw_response'].get('error')) and not a['raw_response'].get('choices') for a in ff),
            'recovery_attempts':len(attempts)-1136,'cost_all_attempts':cost,'cost_first_attempts':chat.money(ff),
            'cost_basis':'API-reported','known_usd_per_1000_questions':cost['known_usd']/1136*1000,
            'known_usd_per_primary_correct':cost['known_usd']/metrics(normalized,keys)['correct'] if metrics(normalized,keys)['correct'] else None,
            'latency_first_all':chat.quantiles([a['latency_ms'] for a in ff]),
            'latency_first_usable':chat.quantiles([a['latency_ms'] for a in ff if a['status']=='ok']),
            'latency_first_http200':chat.quantiles([a['latency_ms'] for a in ff if a['http_status']==200]),
            'input_tokens_all_attempts':sum(a['usage'].get('prompt_tokens',0) or 0 for a in attempts),
            'output_tokens_all_attempts':sum(a['usage'].get('completion_tokens',0) or 0 for a in attempts),
            'reasoning_tokens_histogram':dict(Counter(str(a['reported_reasoning_tokens']) for a in ff)),
            'reasoning_text_present_count':sum(a['reasoning_text_present'] for a in ff),
            'finish_reasons':dict(Counter(str(a['finish_reason']) for a in ff)),
            'identities':dict(Counter(a['model_returned'] or 'unreported (error)' for a in ff)),
            'dates_toronto':dict(Counter(a['started']['toronto'][:10] for a in ff)),
            'format_sensitivity_POSTHOC':{'leading_id_correct':sum(chat.leading_id(a)==keys[a['item_id']]['gold_option'] for a in ff)},
            'panels':panel_summary(panels(normalized,keys,selection))}
        for field in ('role','level'):
            models[m]['by_'+field]={v:metrics([r for r in normalized if metadata[r['item_id']][field]==v],keys)
                                   for v in sorted({r[field] for r in metadata.values()})}
        for f in summary['by_family']:
            ids={i for i,r in metadata.items() if r['family_id']==f['family_id']}
            f['models'][m]=metrics([r for r in normalized if r['item_id'] in ids],keys)
        models[m]['macro_family_accuracy']=sum(f['models'][m]['accuracy_attempted'] for f in summary['by_family'])/25
        summary['sessions_utc'][m]={'started':min(a['started']['utc'] for a in attempts),'completed':max(a['completed']['utc'] for a in attempts)}
        all_new.extend(attempts)
    index={m:{r['item_id']:r for r in rr} for m,rr in model_rows.items()}
    summary['model_count']=len(models)
    summary['total_scored_model_questions']=len(models)*1136
    summary['native_added_model_ids']=base['added_model_ids']
    summary['regular_added_model_ids']=added
    summary['added_model_ids']=base['added_model_ids']+added
    summary['pending_model_ids']=[m for m in MODELS if m not in added]
    summary['status']='COMPLETE_1136_PER_TESTED_MODEL_WITH_REGULAR_LLM_ADDITIONS' if not summary['pending_model_ids'] else 'PARTIAL_PUBLIC_EXPORT'
    summary['none_of_tested_models_correct']=sum(not any(correct(index[m][i],keys) for m in models) for i in metadata)
    shared=[i for i in metadata if all(valid(index[m][i]) for m in models)]
    summary['all_tested_models_answered']=len(shared)
    summary['accuracy_on_shared_answered']={m:metrics([r for r in rr if r['item_id'] in shared],keys) for m,rr in model_rows.items()}
    eligible=[m for m in models if output_compliance[m]['eligible_for_main_comparison']]
    excluded=[m for m in models if m not in eligible]
    ranked_cost=sum((Decimal(str(models[m]['cost_all_attempts'].get('exact_usd',models[m]['cost_all_attempts']['known_usd']))) for m in eligible),Decimal(0))
    summary['output_compliance']=output_compliance
    summary['publication']={
        'rule':'Exclude a model from all main rankings, tables and charts when model-output failures are at least 5% of the 1136 planned first attempts. HTTP/transport/upstream error envelopes do not count as model-output failures.',
        'selection':'Post-hoc reporting rule requested by the benchmark author after inspecting output compliance; not preregistered and not a statistical significance test.',
        'format_failure_cutoff':float(FORMAT_FAILURE_CUTOFF),
        'eligible_model_ids':eligible,'excluded_model_ids':excluded,'ranked_model_count':len(eligible),
        'ranked_model_question_cases':len(eligible)*1136,
        'none_of_ranked_models_correct':sum(not any(correct(index[m][i],keys) for m in eligible) for i in metadata),
        'ranked_accounted_cost':{'exact_usd':str(ranked_cost),'known_usd':float(ranked_cost),
                                'missing_attempts':sum(models[m]['cost_all_attempts']['missing_attempts'] for m in eligible)},
        'excluded_runs_preserved':True,'all_tested_scores_preserved':True}
    summary['pairwise']=[{'a':a,'b':b,**prior.pairwise(model_rows[a],model_rows[b],keys)}
                         for pos,a in enumerate(models) for b in list(models)[pos+1:]]
    new_money=chat.money(all_new)
    for field in ('total_selected_reported_cost','total_selected_accounted_cost'):
        value=summary[field]
        total=Decimal(base[field]['exact_usd'])+Decimal(new_money['exact_usd'])
        value['exact_usd']=str(total)
        value['known_usd']=float(total)
        value['missing_attempts']+=new_money['missing_attempts']
        if 'reported_attempts' in value:
            value['reported_attempts']+=new_money['reported_attempts']
    summary['regular_additions_reported_cost']=new_money
    summary['native_addition_cost']=summary.pop('addition_cost')
    summary['total_selected_http_attempts']+=len(all_new)
    summary['limits'] += [
        'Regular LLM additions tested October 16 with original default-temperature chat protocol, reasoning disabled and max_tokens=16; compatibility probes and earlier pilots excluded.',
        'Provider pins and quantization vary by model. Failures and permitted recovery remain separate; no invoice reconciliation.',
        'GLM 5.3 Flash rejected disabled reasoning and is not assigned a fabricated benchmark score.',
    ]
    summary['source_files_sha256']['overall_2026-10-16/summary.json']=sha256(BASE_SUMMARY.read_bytes()).hexdigest()
    probe_path=PUBLIC/'compatibility_probes.json'
    if probe_path.exists():
        summary['source_files_sha256'][str(logical_relative(probe_path, root=ROOT))]=sha256(probe_path.read_bytes()).hexdigest()
    for m in added:
        for p in (PUBLIC/m).rglob('*'):
            if p.is_file():
                summary['source_files_sha256'][str(logical_relative(p, root=ROOT))]=sha256(p.read_bytes()).hexdigest()
    if write_output:
        write(OVERALL/'summary.json',summary)
        with (OVERALL/'family_comparison.csv').open('w',newline='') as f:
            labels={m:models[m]['label'] for m in eligible}
            writer=csv.DictWriter(f,fieldnames=['family_id','family','n',*labels.values()],lineterminator='\n')
            writer.writeheader()
            writer.writerows({'family_id':g['family_id'],'family':g['family'],'n':g['n'],
                             **{label:g['models'][m]['correct'] for m,label in labels.items()}}
                            for g in summary['by_family'])
    else:
        assert summary==json.loads((OVERALL/'summary.json').read_text())
    print(json.dumps({'model_count':len(models),'pending':summary['pending_model_ids'],
        'new_results':{m:{'correct':models[m]['primary']['correct'],'median_ms':models[m]['latency_first_all']['median_ms'],
                          'cost':models[m]['cost_all_attempts']} for m in added}},indent=2))
    return summary


def validate_publication():
    summary=json.loads((OVERALL/'summary.json').read_text())
    old=json.loads(BASE_SUMMARY.read_text())
    for m,value in old['models'].items():
        assert summary['models'][m]==value,m
    for name,expected in summary['source_files_sha256'].items():
        assert sha256(frozen_file(repo_file(name, root=ROOT)).read_bytes()).hexdigest()==expected,name
    attempts=chat.rows(prior.EXPANSION/'attempts.jsonl')
    first,_=chat.first_and_eventual(attempts)
    for m in chat.MODELS:
        assert summary['output_compliance'][m]==compliance([a for a in first.values() if a['model_requested']==m]),m
    for m in summary['regular_added_model_ids']:
        first,_,_=validate_model(m)
        assert summary['output_compliance'][m]==compliance(list(first.values())),m
    eligible=[m for m in summary['models'] if summary['output_compliance'][m]['eligible_for_main_comparison']]
    assert eligible==summary['publication']['eligible_model_ids']
    assert summary['publication']['ranked_model_count']==len(eligible)
    assert len(eligible)*1136==summary['publication']['ranked_model_question_cases']
    print('PASS: unchanged original scores and sources, output/provider failure separation, explicit post-hoc inclusion rule and ranking membership')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--export',choices=MODELS,nargs='+')
    parser.add_argument('--answer-key',type=Path)
    parser.add_argument('--write',action='store_true')
    parser.add_argument('--export-probes',action='store_true')
    args=parser.parse_args()
    if args.export_probes:
        export_probes()
    for model in args.export or []:
        export(model)
    if args.answer_key:
        analyze(args.answer_key,args.write)
    elif PUBLIC.exists():
        for model in MODELS:
            if (PUBLIC/model/'checksums.json').exists():
                validate_model(model)
        if (OVERALL/'summary.json').exists():
            validate_publication()
        print('PASS: regular-LLM additions, exact original messages, source bindings, dispatch ledgers, identities and charges; no API call or key')
