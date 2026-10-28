#!/usr/bin/env python3
"""Build the archived three-model report; use build_report.py for the expansion."""
from repo_layout import repo_file
import json
from pathlib import Path
import re
import shutil
import markdown

ROOT=Path(__file__).resolve().parents[1]
s=json.loads((repo_file("analysis/summary.json", root=ROOT)).read_text())
models=["jev113","jev114","luna"]
labels=s["labels"]
pct=lambda n,d:f"{100*n/d:.1f}%" if d else "n/a"
pair=s["pairwise"]["jev113_to_jev114"]

text="""# Jev 1.14, Jev 1.13 and GPT-6 Luna Decisions

## The same 1,136 questions, with a fixed reference

Jev 1.14 scored **932/1,136 (82.0%)**, compared with **910/1,136 (80.1%)** for Jev 1.13 and **687/1,136 (60.5%)** for GPT-6 Luna Decisions. The new Jev release gained 22 correct answers overall. It improved some abilities substantially, while leaving several of the original weaknesses almost unchanged.

This is a text-only comparison using the exact same instructions, facts, questions and five answer options in the same order. The original responses remain the reference. A separate 256-item Jev 1.13 recheck is reported in the baseline repository and does not replace them.

![Accuracy by reasoning family, with model snapshots and test dates](figures/ability_profile.png)

## Results and model identities

| Measure | Jev 1.13 | Jev 1.14 | GPT-6 Luna Decisions |
|---|---:|---:|---:|
"""
for label,field in [("Questions attempted","attempted"),("Valid choices","answered"),("Correct","correct"),("Wrong valid choices","wrong"),("Unanswered","unanswered"),("Probability-format warnings","probability_warnings")]:
    text+=f"| {label} | "+" | ".join(str(s["primary"][m][field]) for m in models)+" |\n"
text+="| Correct / all attempted | "+" | ".join(pct(s["primary"][m]["correct"],1136) for m in models)+" |\n"
text+="| Correct / answered | "+" | ".join(pct(s["primary"][m]["correct"],s["primary"][m]["answered"]) for m in models)+" |\n"
core=next(r for r in s["by_role"] if r["role"]=="core")
text+="| Core questions only | "+" | ".join(f"{core[m]['correct']}/{core[m]['attempted']} ({pct(core[m]['correct'],core[m]['attempted'])})" for m in models)+" |\n\n"
text+="""The full reference contains 640 core questions and 496 related variants, contrasts and candidate checks. The combined score is useful for tracking the same bank over time; the related items are not independent observations. The core score and matched tests therefore remain separate views of performance.

| Model | Returned identity | Test dates, Toronto |
|---|---|---|
| Jev 1.13 | `jev-1.13.0` (412), `typesafe/jev-1.13-20260917` (468), historical `jev-latest` (256) | September 22 and October 14, 2026 |
| Jev 1.14 | `typesafe/jev-1.14-20261014` on all 1,134 answered requests | October 14–15, 2026 |
| GPT-6 Luna Decisions | `openai/gpt-6-luna-decisions-20261006` on all 1,113 answered requests | October 10 and 14, 2026 |

The Jev 1.14 release date is October 14. Its run crossed midnight locally. Error responses did not identify a model. The historical Jev alias belongs to the September 22 Jev 1.13 run; those response records preserve the alias rather than an exact snapshot. All new Jev calls explicitly requested their version, and the runner checked the returned snapshot. These dates and identities matter: later calls to a Luna or Jev alias may evaluate another release.

## Where Jev 1.14 improved, and where it did not

The clearest gains were in **verbal spatial tracking**, from 24/43 to 32/43, and **one-to-one assignments**, from 49/61 to 56/61. Scheduling improved from 43/69 to 46/69. Spatial tracking still failed on 11 questions, and scheduling on 23, so the gains do not make either ability dependable without task-specific checking.

Several weak areas barely moved. **Exact truth counting stayed at 24/65**, and **object tracking through swaps stayed at 29/46**. **Sequential procedure execution rose from 5/42 to 6/42**, still only 14.3%. Jev 1.14 therefore provides little evidence of a solution to the state-update and exact-count limitations found in the original benchmark.

The new version also lost ground in some areas. Exceptions and priority rules fell from 48/52 to 45/52, temporal interval relations from 35/36 to 34/36, and correctly answered changed-evidence pairs from 20/25 to 19/25. Improvement is not uniform across functions.

Across individual questions, Jev 1.14 corrected **56** previously unsuccessful cases and lost **34** previously correct cases. Two of those losses were provider errors; the remaining 32 were wrong valid choices. Both versions were correct on 876 questions, and both were unsuccessful on 170. On the 1,134 questions both answered, Jev 1.14 scored 932 and Jev 1.13 scored 908. This is one observed comparison across dates and historical routes, not an isolated measurement of model weights.

## What looks dependable, and what still needs checking

**Bounded decisions from supplied facts are the strongest use case here.** Jev 1.14 answered every sampled record-lookup, forward-implication, contraposition, Boolean-scope, transitive-comparison, preference-ordering, source-authority, reachability and fault-diagnosis question correctly. These are generated, self-contained tasks with explicit rules. The result supports further testing of classification and routing under similarly clear conditions; it does not guarantee correctness on new domains, long real-world contexts or safety-critical decisions.

**Exact counts, repeated state changes and broad candidate verification remain weak.** A caller should not assume Jev 1.14 can reliably maintain a changing state, execute a sequence of edits, count satisfied statements, or certify an arrangement simply because it returns a confident typed choice. Exact arithmetic and state transitions can be checked in code. Richer interpretations need their own domain evaluation and an uncertainty path.

**Luna has clear strengths too.** It answered all 37 lookup and all 37 reachability questions correctly, 44/45 preference questions, and 33/34 transitive comparisons. It exceeded both Jev versions on sequential procedures, with 9/42, although that is still poor absolute performance. It was substantially weaker on contraposition, with 13/46, and on object tracking, with 16/46. Its confidence filter identified a small strong subset, but its overall coverage at high confidence was much lower.

## Confidence: accuracy and coverage together

![Matched tests and confidence accuracy versus coverage](figures/reliability_profile.png)

| Confidence cutoff | Jev 1.13 correct / retained | Jev 1.14 correct / retained | Luna correct / retained |
|---|---:|---:|---:|
"""
for t in [.8,.9,.95]:
    line=[]
    for m in models:
        r=next(r for r in s["confidence"][m] if r["threshold"]==t)
        line.append(f"{r['correct']}/{r['attempted']} ({pct(r['correct'],r['attempted'])}; {pct(r['attempted'],1136)} coverage)")
    text+=f"| ≥{t:g} | "+" | ".join(line)+" |\n"
text+="""
At confidence ≥0.95, Jev 1.14 retained 603 questions and made one error; Jev 1.13 retained 544 and made one error. The new release covers a larger fraction of this bank at roughly the same observed selective accuracy. Luna retained 96 with no observed errors. That smaller error-free subset does not establish a zero future error rate. Confidence is a provider-reported signal, distinct from selected-option probability. The cutoffs are exploratory because they were examined on these results; they are not validated production thresholds.

## Matched diagnostic tests

| Outcome | Jev 1.13 | Jev 1.14 | Luna Decisions |
|---|---:|---:|---:|
"""
for label,group,field,denom in [("All five option rotations correct","rotation","all_correct",25),("Same semantic choice across rotations","rotation","consistent",None),("Both changed-evidence answers correct","contrast","both_correct",25),("Supplied-candidate checks correct","candidate_checks","correct",80),("Original parent puzzles correct","candidate_checks","parent_correct",16),("All five candidate checks correct","candidate_checks","all_checks_correct",16)]:
    cells=[]
    for m in models:
        r=s["panels"][m][group];d=denom if denom else r["complete"]
        cells.append(f"{r[field]}/{d}")
    text+=f"| {label} | "+" | ".join(cells)+" |\n"
text+="""
Luna fully answered 21/25 rotation panels, 22/25 evidence pairs and 12/16 parent-plus-check sets; both Jev versions fully answered every planned panel. Refusals remain unsuccessful in planned-case denominators. On the 21 rotation panels all three fully answered, both Jev versions got all five choices correct in 18 panels, compared with Luna's 14. On the 22 fully answered evidence pairs, the counts were 18 for Jev 1.13, 17 for Jev 1.14 and 13 for Luna. The summary also records the shared-complete candidate checks.

Supplying a candidate improved Jev's verification score from 36/80 to 41/80, compared with Luna's 32/80. The continued errors show that removing solution search does not remove all difficulty in checking or counting constraints. This observation does not establish a particular internal reasoning mechanism. A stable semantic choice across rotations can still be wrong, and changing an answer after an evidence edit is insufficient unless the new answer is correct.

## All reasoning families

| Function | n | Jev 1.13 | Jev 1.14 | Luna Decisions | Jev change, correct answers |
|---|---:|---:|---:|---:|---:|
"""
for f in s["by_family"]:
    line=[f"{f[m]['correct']} ({pct(f[m]['correct'],f[m]['attempted'])})" for m in models]
    delta=f["jev114"]["correct"]-f["jev113"]["correct"]
    text+=f"| {f['family']} | {f['jev113']['attempted']} | "+" | ".join(line)+f" | {delta:+d} |\n"
u=s["jev114_execution"]
text+=f"""
## API outcomes and cost

Jev 1.14 made **{u['http_attempts']} HTTP attempts**. Two returned HTTP 499 with a provider `internal_error` and “Unable to complete this request.” They were retained as unanswered and were not retried because 499 is outside the runner's frozen retry list. They are not demonstrated logical mistakes. Eight other responses contained valid choices but probability distributions failing the strict normalization check; those first choices were scored, and the probability warnings remain visible. This is the same choice/probability separation used for the earlier Jev results.

Successful responses reported **{u['input_tokens']:,} input tokens**, **{u['output_tokens']:,} output tokens**, and **${u['reported_cost_usd']:.8f}** in cost. The two errors omitted usage, so their billed cost is unknown. Median successful response-body latency was {u['body_latency']['median_ms']:.0f} ms, with p95 {u['body_latency']['p95_ms']:.0f} ms. Different dates, historical timer boundaries and provider conditions prevent a controlled speed or total-cost comparison with the older runs.

## Data, reproduction and limits

The [questions](data/questions_1136.csv), [three sets of results](data), [attempt ledger](data/attempts_jev114.jsonl), [model manifest](data/jev114_run_manifest.json), [family comparison](analysis/family_comparison.csv), [changed choices](analysis/changed_choices.csv), [aggregate summary](analysis/summary.json) and [checksums](data/checksums.json) are retained. Changed-choice rows expose recorded model outputs, not gold answers. The answer key remains outside Git.

This bank mixes 25 task templates, engineered load levels and dependent variants. The reference is fixed, but it is not a standardized measure of intelligence or a deployment safety test. Gold answers have computational validation; a fully independent audit of the printed questions is separate work. Shared template or wording defects can affect every model. Future key corrections should be versioned and applied to all three sets of saved responses.

The [original Jev benchmark](https://github.com/etsabary/jev-deterministic-benchmark) and [expanded two-model reference](https://github.com/etsabary/luna-decisions-benchmark/tree/0f10c51/extension_136) remain unchanged. This repository is the separate Jev 1.14 comparison. The new run evaluates the release explicitly listed as [Jev 1.14](https://openrouter.ai/typesafe/jev-1.14), using OpenRouter's native Decisions endpoint. The recorded Luna model is GPT-6 Luna Decisions, snapshot October 6, 2026. There is no multimodal testing in this report.

```bash
# No credentials, private key or API calls needed
python3 validate.py
python3 -m unittest -v test_analysis.py
python3 run_benchmark.py

# Re-score using the external original key
python3 analyze.py --answer-key /path/to/answer_key_PRIVATE.csv

# Rebuild graphics and the report
python3 -m pip install -r requirements-reports.txt
python3 plot_results.py
python3 build_report.py
```
"""
(repo_file("THREE_MODEL_REFERENCE.md", root=ROOT)).write_text(text)
body=markdown.markdown(text,extensions=["tables","fenced_code"])
prefix="https://github.com/etsabary/jev-1.14-comparison-benchmark/blob/main/"
body=re.sub(r'href="(?!https?://|#)([^"]+)"',lambda m:'href="'+prefix+m.group(1)+'"',body)
(repo_file("docs/figures", root=ROOT)).mkdir(exist_ok=True)
for image in (repo_file("figures", root=ROOT)).glob("*"):
    shutil.copy2(image,repo_file("docs/figures", root=ROOT)/image.name)
html="""<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Jev 1.14 vs Jev 1.13 and GPT-6 Luna Decisions: 1,136 questions</title>
<style>body{max-width:1180px;margin:auto;padding:38px 24px 80px;background:#f7f9fc;color:#172c42;font:17px/1.65 system-ui,sans-serif}h1{font-size:2.3rem;line-height:1.2}h2{margin-top:2.3rem;line-height:1.3}a{color:#087f8c}img{width:100%;height:auto;border-radius:12px}table{display:block;overflow-x:auto;max-width:100%;border-collapse:collapse;font-size:.9rem}td,th{border-bottom:1px solid #d5dfe9;padding:10px 12px;text-align:left}th{background:#e7eef5}code{font-size:.86em;overflow-wrap:anywhere}pre{overflow:auto;padding:18px;background:#e7eef5}nav{border-bottom:1px solid #d5dfe9;padding-bottom:18px;margin-bottom:30px;font-size:.9rem}</style>
<nav><a href="https://github.com/etsabary/jev-1.14-comparison-benchmark">Repository and raw evidence</a> · <a href="https://etsabary.github.io/jev-deterministic-benchmark/extension_136.html">Frozen two-model reference</a></nav><main>
"""+body+"</main></html>\n"
(repo_file("docs/three_model_reference.html", root=ROOT)).write_text(html)
print("Built THREE_MODEL_REFERENCE.md and docs/three_model_reference.html")
