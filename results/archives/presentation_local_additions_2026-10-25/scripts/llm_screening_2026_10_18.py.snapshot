"""Offline quality gate and authorized orchestration of answer-blind LLM runs.

Only this controller reads the external gold key. It never supplies an answer
or item-specific feedback to the inference executor. Decisions stop a model or
release the next unchanged prefix under the author's approved October18 rule.
"""
from repo_layout import repo_file
from repo_layout import source_file
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys

import llm_field_2026_10_18 as run
import text_additions as older
from score_expansion import load_key, normalized_llm
from analysis_core import metrics

ROOT=run.ROOT
POLICY=dict(accuracy_below=.5,model_output_failures_fraction_at_least=.05,
            median_ms_above=2000,minimum_cases=100,recheck_every_cases=100,
            maximum_active_models=4,approved_by='Benchmark author, October 18, 2026')


def gate(primary, compliance, latency):
    assert primary['attempted']>=POLICY['minimum_cases']
    reasons=[]
    if primary['accuracy_attempted']<POLICY['accuracy_below']:reasons.append('accuracy_below_50_percent')
    n=primary['attempted']
    if compliance['model_output_failures']/n>=POLICY['model_output_failures_fraction_at_least']:
        reasons.append('model_output_failures_at_least_5_percent')
    if latency['median_ms']>POLICY['median_ms_above']:reasons.append('median_above_2000_ms')
    return reasons


def assess(model_id, keys):
    out=run.RUNS/model_id
    run.validate(model_id,out)
    _,plan=run.prepare(model_id)
    attempts,results,_,_=run.ledger_state(out,plan)
    first,eventual=run.chat.first_and_eventual(attempts)
    ff=list(first.values())
    assert len(ff)>=100
    primary=metrics([normalized_llm(a) for a in ff],keys)
    c=older.compliance(ff)
    # The older compliance helper has1136 as its reporting denominator. Use the
    # actual evaluated prefix for this approved operational screening policy.
    c.update(planned=len(ff),model_output_failure_fraction=c['model_output_failures']/len(ff))
    c.pop('eligible_for_main_comparison',None)
    c['passes_output_format_screen']=c['model_output_failures']/len(ff)<.05
    latency=run.chat.quantiles([a['latency_ms'] for a in ff])
    reasons=gate(primary,c,latency)
    value=dict(model_id=model_id,decision='stop' if reasons else 'continue',
        gate_result='fail' if reasons else 'pass',screen_policy=run.SCREEN_POLICY,
        manifest_sha256=run.file_hash(out/'manifest.json'),
        screen_sha256=run.file_hash(out/'screen_100.json'),
        evaluated_first_attempts=len(ff),primary=primary,
        eventual=metrics([normalized_llm(a) for a in eventual.values()],keys),
        compliance=c,first_latency=latency,cost_all_attempts=run.chat.money(attempts),
        cutoffs=POLICY,reasons=reasons,
        authorized_by=POLICY['approved_by'],
        reason='; '.join(reasons) if reasons else 'Passes all three author-approved operational cutoffs on the recorded first-attempt prefix',
        controller_sha256=sha256(Path(__file__).read_bytes()).hexdigest(),
        attempts_prefix=run.bound_prefix(out/'attempts.jsonl'),
        selection_limit='Sequential prefix includes related variants and uneven family coverage; operational selection, not a representative accuracy estimate')
    dest=out/'screening_decisions'/f'after_{len(ff):04d}.json'
    dest.parent.mkdir(exist_ok=True)
    run.d.save_bound(dest,value)
    if reasons:
        run.d.save_bound(out/'STOPPED_SCREEN.json',value)
    return value,dest


def invoke(model_id, *args):
    p=subprocess.run([sys.executable,str(source_file(repo_file('llm_field_2026_10_18.py', root=ROOT))),
                      '--model',model_id,*args],capture_output=True,text=True,cwd=ROOT)
    if p.stdout.strip():print(p.stdout.strip(),flush=True)
    if p.returncode:
        raise RuntimeError('Executor paused for inspection: '+p.stderr[-1600:])


def run_model(model_id, keys):
    out=run.RUNS/model_id
    run.validate_probe(model_id,out)
    if (out/'STOPPED_SCREEN.json').exists():
        value=json.loads((out/'STOPPED_SCREEN.json').read_text())
        return dict(model_id=model_id,status='ALREADY_STOPPED_SCREEN',reasons=value['reasons'])
    if not (out/'screen_100.json').exists():invoke(model_id,'--execute')
    while True:
        value,receipt=assess(model_id,keys)
        print(json.dumps(dict(model_id=model_id,status='SCREEN_ASSESSED',
            completed=value['evaluated_first_attempts'],correct=value['primary']['correct'],
            median_ms=value['first_latency']['median_ms'],decision=value['decision'],reasons=value['reasons'])),flush=True)
        if value['decision']=='stop':return dict(model_id=model_id,status='STOPPED_SCREEN',reasons=value['reasons'])
        if (out/'completion.json').exists():
            return dict(model_id=model_id,status='COMPLETE_1136',correct=value['primary']['correct'])
        # Same first100 receipt remains the immutable release authority. Later
        # rechecks can stop further calls but never alter a question or answer.
        initial=out/'screening_decisions/after_0100.json'
        assert initial.exists()
        invoke(model_id,'--execute','--continue-receipt',str(initial),'--waves','50')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--models',nargs='+',choices=run.MODELS,required=True)
    p.add_argument('--answer-key',type=Path,required=True)
    p.add_argument('--execute',action='store_true',help='Run the approved screen and released unchanged batches')
    args=p.parse_args()
    keys=load_key(args.answer_key)
    errors=[]
    with ThreadPoolExecutor(max_workers=POLICY['maximum_active_models']) as pool:
        futures={pool.submit(run_model if args.execute else assess,m,keys):m for m in args.models}
        for f in as_completed(futures):
            m=futures[f]
            try:
                result=f.result()
                if not args.execute:result=result[0]
                print(json.dumps(result),flush=True)
            except Exception as exc:
                errors.append(m)
                print(json.dumps(dict(model_id=m,status='STOPPED_FOR_INSPECTION',error=type(exc).__name__+': '+str(exc))),flush=True)
    if errors:raise SystemExit('Inspect before resuming: '+','.join(errors))


if __name__=='__main__':main()
