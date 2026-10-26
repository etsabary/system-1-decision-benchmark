#!/usr/bin/env python3
"""Public evidence validation. This checks consistency, not the private gold key."""
from repo_layout import repo_file
from collections import Counter
import json
from pathlib import Path
from analyze import ROOT,file_hash
from analysis_core import normalize
from run_benchmark import read_csv,prepare_tasks


def validate():
    tasks=prepare_tasks(repo_file("data/questions_1136.csv", root=ROOT),repo_file("data/results_jev113.csv", root=ROOT),"typesafe/jev-1.14")
    assert len(tasks)==1136
    indexed={t["item_id"]:t for t in tasks}
    baseline=json.loads((repo_file("data/baseline_reference_manifest.json", root=ROOT)).read_text())
    assert baseline["questions_sha256"]==file_hash(repo_file("data/questions_1136.csv", root=ROOT))
    assert baseline["jev_decisions_sha256"]==file_hash(repo_file("data/results_jev113.csv", root=ROOT))
    assert baseline["luna_decisions_sha256"]==file_hash(repo_file("data/results_luna.csv", root=ROOT))
    summary=json.loads((repo_file("analysis/summary.json", root=ROOT)).read_text())
    assert summary["key_sha256"]==baseline["key_sha256"]
    attempts=[json.loads(x) for x in (repo_file("data/attempts_jev114.jsonl", root=ROOT)).read_text().splitlines()]
    counts=Counter(a["item_id"] for a in attempts)
    for model in ["jev113","jev114","luna"]:
        rows=read_csv(repo_file(f"data/results_{model}.csv", root=ROOT))
        assert len(rows)==len({r["item_id"] for r in rows})==1136
        assert {r["item_id"] for r in rows}==set(indexed)
        normalized=[normalize(r) for r in rows]
        m=summary["primary"][model]
        assert m["answered"]==sum(r["normalized_status"]=="ok" for r in normalized)
        assert m["attempted"]==m["answered"]+m["unanswered"]==1136
        assert m["answered"]==m["correct"]+m["wrong"]
        for field in ["family","level","role"]:
            for metric in ["attempted","answered","correct","wrong","unanswered"]:
                assert sum(r[model][metric] for r in summary["by_"+field])==m[metric]
        if model=="jev114":
            saved={r["item_id"]:r for r in read_csv(repo_file("data/decisions_jev114.csv", root=ROOT))}
            for raw,derived in zip(rows,normalized):
                i=raw["item_id"]
                assert raw["model_requested"]=="typesafe/jev-1.14"
                assert raw["request_payload_sha256"]==indexed[i]["request_payload_sha256"]
                assert raw["prompt_sha256"]==indexed[i]["prompt_sha256"]
                assert int(raw["attempt_count"])==counts[i]==1
                if raw["http_status"]=="200":assert raw["model_returned"]=="typesafe/jev-1.14-20261014"
                else:assert raw["http_status"]=="499" and "internal_error" in raw["error_message"]
                assert saved[i]["raw_response_json"]==raw["raw_response_json"]
                assert saved[i]["normalized_choice"]==derived["normalized_choice"]
    for p in summary["pairwise"].values():
        assert p["n"]==sum(p[k] for k in ["both_correct","both_unsuccessful","fixed","regressed"])
    assert summary["pairwise"]["jev113_to_jev114"]["fixed"]-summary["pairwise"]["jev113_to_jev114"]["regressed"]==summary["primary"]["jev114"]["correct"]-summary["primary"]["jev113"]["correct"]
    u=summary["jev114_execution"]
    assert u["http_attempts"]==len(attempts)==1136
    assert abs(u["reported_cost_usd"]-sum(a["provider_cost_usd"] or 0 for a in attempts))<1e-12
    forbidden={"gold_option","gold_canonical","gold_text","explanation"}
    for p in (repo_file("data", root=ROOT)).glob("*.csv"):assert not forbidden.intersection(read_csv(p)[0]),p
    for name,digest in json.loads((repo_file("data/checksums.json", root=ROOT)).read_text()).items():assert file_hash(repo_file(name, root=ROOT))==digest,name
    for image in (repo_file("figures", root=ROOT)).glob("*"):assert image.read_bytes()==(repo_file("docs/figures", root=ROOT)/image.name).read_bytes()
    print("PASS: 1,136 identical inputs; unchanged baseline bytes; pinned 1.14 snapshot; all attempts; choice normalization; aggregate arithmetic; figure parity; checksums; no public gold fields")


if __name__=="__main__":validate()
