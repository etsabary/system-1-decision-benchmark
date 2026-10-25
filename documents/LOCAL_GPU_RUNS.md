# Local GPU runs: setup and model profiles

15 complete runs on the unchanged 1,342-question bank, measured October 25, 2026. [Interactive local results](https://etsabary.github.io/system-1-decision-benchmark/report.html#local-results).

**🟣 Local · NVIDIA RTX 2060 · 6 GB VRAM · Ollaya 0.17.0 · CUDA.** Hardware identity was supplied by the user; every completed route reported cuda:0. One request/model at a time over the LAN. Loading and synthetic warm-ups are excluded; the earlier CPU screen is separate. Precision varies by route. CPU, system RAM and driver version were not captured.

Local API access was unmetered. Electricity and hardware costs were not measured. No latency on newer hardware is inferred. [Captured metadata](../results/releases/local_gpu_2026-10-25/local_model_metadata.json) records source pins where available and the server-reported precision and digest. These are serving identities, not independent weight attestations.

Purple bars and model-name badges identify these local configurations. Accuracy heatmap cells retain the same 0–100% blue scale, and speed/cost colors retain their existing thresholds.

## H2O-Lightning 4B

892/1342 (66.5%); mean / median / p95 289 / 259 / 459 ms. Reported precision: Q8_0.

Higher category scores: Following directed connections 41/43; Lookup and filtering 40/43; Ranking with tie-break rules 46/51.

Lower category scores: Following step-by-step procedures 8/48; Counting exactly true claims 20/71; Resolving names and references 25/50.

## Fovea 4B

841/1342 (62.7%); mean / median / p95 588 / 558 / 779 ms. Reported precision: NF4 / FP16 compute / FP32 readout.

Higher category scores: Choosing authoritative current records 42/43; Lookup and filtering 40/43; Following directed connections 40/43.

Lower category scores: Following step-by-step procedures 10/48; Counting exactly true claims 20/71; Tracking swaps 18/52.

## Jebadiah 4B

808/1342 (60.2%); mean / median / p95 298 / 270 / 479 ms. Reported precision: Q8_0.

Higher category scores: Lookup and filtering 40/43; Following directed connections 39/43; Ranking with tie-break rules 45/51.

Lower category scores: Counting exactly true claims 15/71; Following step-by-step procedures 11/48; Resolving names and references 19/50.

## JevK5 4B

780/1342 (58.1%); mean / median / p95 323 / 296 / 525 ms. Reported precision: Q8_0.

Higher category scores: Lookup and filtering 41/43; Following directed connections 41/43; Ordering by comparisons 33/40.

Lower category scores: Following step-by-step procedures 14/48; Changing a cause 15/50; Counting exactly true claims 22/71.

## Lev 4B

749/1342 (55.8%); mean / median / p95 570 / 532 / 914 ms. Reported precision: Q8_0.

Higher category scores: Following directed connections 39/43; Ordering by comparisons 34/40; Ranking with tie-break rules 43/51.

Lower category scores: Counting exactly true claims 13/71; Following step-by-step procedures 9/48; Choosing authoritative current records 13/43.

## Credence E4B

741/1342 (55.2%); mean / median / p95 315 / 284 / 464 ms. Reported precision: Q4_K_M.

Higher category scores: Following directed connections 39/43; Choosing authoritative current records 38/43; Ordering by comparisons 35/40.

Lower category scores: Truth-tellers and liars 20/74; Counting exactly true claims 20/71; Tracking position and direction 16/49.

## Strands Decider 2B

710/1342 (52.9%); mean / median / p95 435 / 403 / 703 ms. Reported precision: F32.

Higher category scores: Choosing authoritative current records 39/43; Lookup and filtering 38/43; Exceptions and priority rules 49/58.

Lower category scores: Truth-tellers and liars 14/74; Checking required conditions 10/52; Following step-by-step procedures 11/48.

## Snap 2B

574/1342 (42.8%); mean / median / p95 157 / 136 / 229 ms. Reported precision: Q8_0.

Higher category scores: Lookup and filtering 39/43; Choosing authoritative current records 37/43; Ordering by comparisons 32/40.

Lower category scores: Following step-by-step procedures 8/48; Checking required conditions 10/52; Counting exactly true claims 15/71.

## Mapika Decider 2B

547/1342 (40.8%); mean / median / p95 381 / 371 / 613 ms. Reported precision: F32.

Higher category scores: Ordering by comparisons 34/40; Ranking with tie-break rules 40/51; Lookup and filtering 33/43.

Lower category scores: Following step-by-step procedures 8/48; Checking required conditions 9/52; Tracking position and direction 9/49.

## Sura 2B

428/1342 (31.9%); mean / median / p95 436 / 425 / 672 ms. Reported precision: F32.

Higher category scores: Choosing authoritative current records 34/43; Tracking what others know 39/50; Ordering by comparisons 30/40.

Lower category scores: Tracking position and direction 3/49; Changing a cause 5/50; Following step-by-step procedures 5/48.

## GLiClass

393/1342 (29.3%); mean / median / p95 92 / 79 / 178 ms. Reported precision: F32.

Higher category scores: Ordering by comparisons 19/40; One-to-one assignments 30/67; All, some, none and sets 20/49.

Lower category scores: Diagnosing faults from evidence 5/50; Following step-by-step procedures 9/48; Combining AND, OR and NOT 11/54.

## Von

331/1342 (24.7%); mean / median / p95 96 / 77 / 174 ms. Reported precision: F32.

Higher category scores: Exceptions and priority rules 30/58; Ordering by comparisons 17/40; All, some, none and sets 18/49.

Lower category scores: Diagnosing faults from evidence 3/50; Checking required conditions 8/52; Resolving names and references 8/50.

## Laya Typed Decisions

322/1342 (24.0%); mean / median / p95 53 / 46 / 95 ms. Reported precision: F16/F32.

Higher category scores: Ordering by comparisons 28/40; Exceptions and priority rules 28/58; Following directed connections 19/43.

Lower category scores: Ranking with tie-break rules 2/51; Checking required conditions 4/52; Following step-by-step procedures 4/48.

## Decima Agent

313/1342 (23.3%); mean / median / p95 81 / 71 / 138 ms. Reported precision: F32.

Higher category scores: Resolving names and references 19/50; Ordering by comparisons 15/40; One-to-one assignments 25/67.

Lower category scores: Ranking with tie-break rules 3/51; Finding rule violations 5/52; Enough evidence or a conflict? 4/41.

## CLM 8B

304/1342 (22.7%); mean / median / p95 324 / 282 / 726 ms. Reported precision: Q4_K_M.

Higher category scores: Lookup and filtering 19/43; Diagnosing faults from evidence 19/50; Following if-then rules 17/46.

Lower category scores: Ordering by comparisons 3/40; Combining AND, OR and NOT 5/54; Scheduling under constraints 9/76.

## Partial and blocked routes

Coba 1B and the NLI representative stopped after 20 cases because one response each truncated the input. Julia had 19 HTTP failures in 20 attempts due to its physical batch limit. KnowLine returned a valid typed warm-up choice with output_tokens=1; that counter alone does not establish reasoning, and native adapter review is pending. These routes are documented in [screen details](../results/releases/local_gpu_2026-10-25/screened_routes.json) and are not ranked as complete runs.

All profiles use observed category accuracy; their higher/lower lists select categories with at least 20 questions. The complete [named category matrix](../results/releases/local_gpu_2026-10-25/category_scores.csv) also includes the six eight-question domains.
