"""Choice scoring and matched-panel definitions shared across the three models."""
import json

from run_benchmark import parse_answer


def normalize(row):
    raw=json.loads(row["raw_response_json"])
    answer=raw.get("answers",{}).get("decision",{})
    choice=str(answer.get("choice",""))
    ok=str(row["http_status"])=="200" and choice in {"1","2","3","4","5"}
    warning=""
    if ok:
        try: parse_answer(raw)
        except ValueError as exc: warning=str(exc)
    return {**row,"normalized_status":"ok" if ok else row["status"],
        "normalized_choice":choice if ok else "", "probability_warning":warning,
        "normalized_confidence":answer.get("confidence") if ok else None}


def valid(row): return row["normalized_status"]=="ok"
def correct(row,keys): return valid(row) and row["normalized_choice"]==keys[row["item_id"]]["gold_option"]
def semantic(row,keys): return keys[row["item_id"]][f"option_{row['normalized_choice']}_canonical"]


def metrics(rows,keys):
    n=len(rows);answered=sum(map(valid,rows));good=sum(correct(r,keys) for r in rows)
    return {"attempted":n,"answered":answered,"correct":good,"wrong":answered-good,"unanswered":n-answered,
        "accuracy_attempted":good/n if n else None,"accuracy_answered":good/answered if answered else None,
        "probability_warnings":sum(bool(r["probability_warning"]) for r in rows)}


def panels(rows,keys,selection):
    index={r["item_id"]:r for r in rows}
    rotation=[];contrast=[];checks=[]
    for panel in selection["panels"]["rotations"]:
        group=[index[i] for i in panel["item_ids"]];complete=all(map(valid,group))
        rotation.append({"complete":complete,"all_correct":all(correct(r,keys) for r in group),
            "consistent":complete and len({semantic(r,keys) for r in group})==1})
    for panel in selection["panels"]["contrasts"]:
        a,b=index[panel["base_id"]],index[panel["contrast_id"]]
        contrast.append({"complete":valid(a) and valid(b),"both_correct":correct(a,keys) and correct(b,keys)})
    for panel in selection["panels"]["candidate_checks"]:
        parent=index[panel["base_id"]];group=[index[i] for i in panel["check_ids"]]
        checks.append({"complete":valid(parent) and all(map(valid,group)),
            "parent_correct":correct(parent,keys),"correct":sum(correct(r,keys) for r in group),
            "answered":sum(map(valid,group)),"all_correct":all(correct(r,keys) for r in group)})
    return {"rotation":rotation,"contrast":contrast,"candidate_checks":checks}


def panel_summary(p):
    return {"rotation":{"planned":len(p["rotation"]),"complete":sum(x["complete"] for x in p["rotation"]),
            "all_correct":sum(x["all_correct"] for x in p["rotation"]),"consistent":sum(x["consistent"] for x in p["rotation"])},
        "contrast":{"planned":len(p["contrast"]),"complete":sum(x["complete"] for x in p["contrast"]),
            "both_correct":sum(x["both_correct"] for x in p["contrast"])},
        "candidate_checks":{"parents":len(p["candidate_checks"]),"checks":5*len(p["candidate_checks"]),
            "complete":sum(x["complete"] for x in p["candidate_checks"]),
            "parent_correct":sum(x["parent_correct"] for x in p["candidate_checks"]),
            "correct":sum(x["correct"] for x in p["candidate_checks"]),"answered":sum(x["answered"] for x in p["candidate_checks"]),
            "all_checks_correct":sum(x["all_correct"] for x in p["candidate_checks"])}}
