#!/usr/bin/env python3
"""Reproduce the three-model comparison using an external, unpublished gold key."""
from repo_layout import repo_file
import argparse
from collections import Counter
import csv
from datetime import datetime
import hashlib
import json
from pathlib import Path
from zoneinfo import ZoneInfo

from analysis_core import normalize,valid,correct,metrics,panels,panel_summary
from run_benchmark import read_csv,digest,packet

ROOT=Path(__file__).resolve().parents[1]
MODELS=["jev113","jev114","luna"]
LABELS={"jev113":"Jev 1.13","jev114":"Jev 1.14","luna":"GPT-6 Luna Decisions"}


def file_hash(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def write_json(path,value):path.write_text(json.dumps(value,indent=2,ensure_ascii=False)+"\n")
def write_csv(path,rows):
    with path.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=list(dict.fromkeys(k for r in rows for k in r)));w.writeheader();w.writerows(rows)


def quantiles(values):
    v=sorted(float(x) for x in values if x not in ("",None))
    def q(p):
        at=(len(v)-1)*p;i=int(at)
        return v[i]+(v[min(i+1,len(v)-1)]-v[i])*(at-i)
    return {"n":len(v),"median_ms":q(.5),"p95_ms":q(.95)} if v else None


def analyze(key_path):
    keys={r["item_id"]:r for r in read_csv(key_path)}
    questions=read_csv(repo_file("data/questions_1136.csv", root=ROOT))
    ids={q["item_id"] for q in questions}
    assert len(ids)==len(questions)==1136 and ids<=set(keys)
    baseline=json.loads((repo_file("data/baseline_reference_manifest.json", root=ROOT)).read_text())
    assert baseline["questions_sha256"]==file_hash(repo_file("data/questions_1136.csv", root=ROOT))
    assert baseline["key_sha256"]==file_hash(key_path)
    assert baseline["jev_decisions_sha256"]==file_hash(repo_file("data/results_jev113.csv", root=ROOT))
    assert baseline["luna_decisions_sha256"]==file_hash(repo_file("data/results_luna.csv", root=ROOT))
    rows={m:[normalize(r) for r in read_csv(repo_file(f"data/results_{m}.csv", root=ROOT))] for m in MODELS}
    for m,rs in rows.items():
        assert len(rs)==len({r["item_id"] for r in rs})==1136
        assert {r["item_id"] for r in rs}==ids
    selection=json.loads((repo_file("data/selection_manifest.json", root=ROOT)).read_text())
    p={m:panels(rs,keys,selection) for m,rs in rows.items()}
    summary={"labels":LABELS,"key_sha256":file_hash(key_path),"questions_sha256":baseline["questions_sha256"],
        "question_count":1136,"primary":{m:metrics(rs,keys) for m,rs in rows.items()},
        "test_dates_toronto":{m:dict(sorted(Counter(datetime.fromisoformat(r["timestamp_utc"].replace('Z','+00:00')).astimezone(ZoneInfo('America/Toronto')).date().isoformat() for r in rs).items())) for m,rs in rows.items()},
        "versions":{m:dict(Counter(r["model_returned"] or "unreported (error)" for r in rs)) for m,rs in rows.items()},
        "panels":{m:panel_summary(group) for m,group in p.items()}}
    for field in ["family","level","role"]:
        values=sorted({keys[i][field] for i in ids})
        summary["by_"+field]=[{field:value,**({"family_id":next(keys[i]["family_id"] for i in ids if keys[i][field]==value)} if field=="family" else {}),
            **{m:metrics([r for r in rs if keys[r["item_id"]][field]==value],keys) for m,rs in rows.items()}} for value in values]
    summary["by_family"].sort(key=lambda x:x["family_id"])
    summary["confidence"]={m:[{"threshold":t,**metrics([r for r in rs if valid(r) and r["normalized_confidence"] is not None and float(r["normalized_confidence"])>=t],keys)} for t in [0,.5,.6,.7,.8,.9,.95,.99]] for m,rs in rows.items()}
    indexed={m:{r["item_id"]:r for r in rs} for m,rs in rows.items()}
    summary["pairwise"]={}
    for old,new in [("jev113","jev114"),("luna","jev114"),("luna","jev113")]:
        transitions=Counter((correct(indexed[old][i],keys),correct(indexed[new][i],keys)) for i in ids)
        shared=[i for i in ids if valid(indexed[old][i]) and valid(indexed[new][i])]
        summary["pairwise"][old+"_to_"+new]={"n":1136,"both_correct":transitions[True,True],"both_unsuccessful":transitions[False,False],
            "fixed":transitions[False,True],"regressed":transitions[True,False],
            "same_choice":sum(indexed[old][i]["normalized_choice"]==indexed[new][i]["normalized_choice"] for i in ids),
            "paired_answered":len(shared),"old_correct_on_paired":sum(correct(indexed[old][i],keys) for i in shared),
            "new_correct_on_paired":sum(correct(indexed[new][i],keys) for i in shared),
            "regressions_due_to_new_unanswered":sum(correct(indexed[old][i],keys) and not valid(indexed[new][i]) for i in ids)}
    summary["common_answered_panels"]={}
    for name in ["rotation","contrast","candidate_checks"]:
        chosen=[i for i in range(len(p["jev113"][name])) if all(p[m][name][i]["complete"] for m in MODELS)]
        summary["common_answered_panels"][name]={"n":len(chosen),**{m:panel_summary({n:[p[m][n][i] for i in chosen] if n==name else [] for n in p[m]})[name] for m in MODELS}}
    ext_ids={r["item_id"] for r in selection["selected_items"]}
    summary["same_subset_body_latency"]={m:quantiles(r["latency_ms"] for r in rs if r["item_id"] in ext_ids and valid(r)) for m,rs in rows.items()}
    attempts=[json.loads(x) for x in (repo_file("data/attempts_jev114.jsonl", root=ROOT)).read_text().splitlines()]
    summary["jev114_execution"]={"http_attempts":len(attempts),"attempts_with_cost":sum(a["provider_cost_usd"] is not None for a in attempts),
        "reported_cost_usd":sum(a["provider_cost_usd"] or 0 for a in attempts),
        "input_tokens":sum(int(r["input_tokens"] or 0) for r in rows["jev114"]),"output_tokens":sum(int(r["output_tokens"] or 0) for r in rows["jev114"]),
        "body_latency":quantiles(r["latency_ms"] for r in rows["jev114"] if valid(r)),
        "errors":dict(Counter(r["http_status"] for r in rows["jev114"] if not valid(r)))}
    metadata=[{k:keys[q["item_id"]][k] for k in ["item_id","base_id","family_id","family","role","level","variant","split"]}|{"prompt_sha256":q["prompt_sha256"]} for q in questions]
    write_csv(repo_file("data/item_metadata.csv", root=ROOT),metadata)
    write_csv(repo_file("data/decisions_jev114.csv", root=ROOT),rows["jev114"])
    write_json(repo_file("analysis/summary.json", root=ROOT),summary)
    family_rows=[]
    for f in summary["by_family"]:
        family_rows.append({"family_id":f["family_id"],"family":f["family"],"n":f["jev113"]["attempted"],
            **{m+"_correct":f[m]["correct"] for m in MODELS},"jev114_minus_jev113":f["jev114"]["correct"]-f["jev113"]["correct"],
            **{m+"_unanswered":f[m]["unanswered"] for m in MODELS}})
    write_csv(repo_file("analysis/family_comparison.csv", root=ROOT),family_rows)
    write_csv(repo_file("analysis/confidence_comparison.csv", root=ROOT),[{"model":m,**r} for m in MODELS for r in summary["confidence"][m]])
    changes=[]
    for i in sorted(ids):
        a,b=indexed["jev113"][i],indexed["jev114"][i]
        if a["normalized_choice"]!=b["normalized_choice"]:
            changes.append({"item_id":i,"family":keys[i]["family"],"role":keys[i]["role"],"level":keys[i]["level"],
                "jev113_choice":a["normalized_choice"],"jev114_choice":b["normalized_choice"],
                "jev113_confidence":a["normalized_confidence"],"jev114_confidence":b["normalized_confidence"]})
    write_csv(repo_file("analysis/changed_choices.csv", root=ROOT),changes)
    # Individual gold/correctness labels stay local for a later answer-key audit.
    private=repo_file("runs", root=ROOT);private.mkdir(exist_ok=True)
    review=[{"item_id":i,"family":keys[i]["family"],"gold_option":keys[i]["gold_option"],
        **{m+"_choice":indexed[m][i]["normalized_choice"] for m in MODELS}} for i in sorted(ids) if any(not correct(indexed[m][i],keys) for m in MODELS)]
    write_csv(private/"answers_for_audit_PRIVATE.csv",review)
    print(json.dumps({"primary":summary["primary"],"change":summary["pairwise"]["jev113_to_jev114"],"execution":summary["jev114_execution"]},indent=2))


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--answer-key",type=Path,required=True)
    analyze(p.parse_args().answer_key)
