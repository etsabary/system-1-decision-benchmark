> Earlier 1,136-question reference, not the current 1,342-question ranking. [Current report](../README.md).

# Scope of the current diagnostics

The [active corrected-bank comparison](REFERENCE_1136.md) includes 36 complete configurations. The three excluded full-run diagnostics below describe the earlier uncorrected bank and were not retested. Stopped samples and interface probes retain their original denominators. They are outside the active ranking.

Original Nimble v4 has 902 correct answers on its 1,134 retained unchanged questions. The original checkpoint is unavailable: its alias now redirects to Max. The two corrected questions remain untested for original v4. It is a partial diagnostic, not a 1,136-question score, and Max responses were not substituted.

# Output compliance diagnostics

Haiku 5.5, DeepSeek V4.1 Flash and Phi-4 had substantial difficulty returning only a numeric decision within the 16-token output limit. Their saved runs remain public, but they are excluded from the [main benchmark](REFERENCE_1136.md), function tables and comparative charts.

The author requested this separation after reviewing the outputs. The reporting rule excludes a model when at least **5% of the 1,136 planned first attempts** fail the output contract. This is a post-hoc operational cutoff, not a preregistered rule or a statistical significance test. HTTP errors, connection failures, body-read timeouts and upstream error envelopes are counted separately and do not trigger this format exclusion. Lower levels of format failure remain unsuccessful first attempts in the main results.

All models were asked to return only option ID 1, 2, 3, 4 or 5, with reasoning disabled and `max_tokens=16`. No malformed answer was retried. A valid but wrong choice was not retried either. Permitted API recovery attempts and their charges remain separate from the primary first-attempt scores.

## Three unranked runs

The strict full-bank figures below describe success under the tested output contract. They are diagnostic results, not entries in the main accuracy ranking. Accuracy among usable answers is conditional on which questions a model answered directly; it cannot be extrapolated to the unanswered questions.

| Unranked diagnostic | Usable / 1,136 | Model-output failures | Provider failures | Correct among usable | Strict full-bank result | Median | Known run cost |
|---|---:|---:|---:|---:|---:|---:|---:|
| Phi-4 14B | 807 | 327 | 2 | 428/807 (53.0%) | 428/1,136 (37.7%) | 365 ms | $0.02329726 |
| Claude Haiku 5.5 | 355 | 781 | 0 | 337/355 (94.9%) | 337/1,136 (29.7%) | 792 ms | $0.05498820 |
| DeepSeek V4.1 Flash | 954 | 181 | 1 | 614/954 (64.4%) | 614/1,136 (54.0%) | 411 ms | $0.04461453 |

Costs include permitted API retries. DeepSeek and Phi-4 each have failed attempts with missing charges; unknown charges are not zero. The complete ledgers and per-model cost records are linked from the [all-tested aggregate](../results/releases/overall_expanded_2026-10-16/summary.json).

## Haiku often began explaining instead of returning an answer

Claude Haiku 5.5 returned 355 usable first decisions, of which **337 were correct (94.9%)**. The remaining 781 outputs all reached the 16-token limit without a complete numeric answer. Its 18 wrong valid choices and 781 unusable outputs are different outcomes. Every API call succeeded.

Saved examples begin with text such as “We need which named flag must be on given the facts.” Disabling hidden reasoning did not prevent the model from explaining in its visible response. A larger output budget or an answer-first prompt could test its decision accuracy more fully, but neither configuration was run here. The 94.9% answered-subset result does not establish full-bank accuracy.

## DeepSeek had 180 capped outputs and one invalid option

DeepSeek V4.1 Flash returned 954 usable first decisions, of which **614 were correct (64.4%)**. On 180 questions the output reached the cap; saved examples begin explaining the solution. One other response was `0`, outside the five allowed options. A separate transport failure accounts for the remaining unanswered case.

Its selected DeepInfra route had a captured 30% discount. The reported run cost and response time describe the short-output configuration, not a larger-budget or reasoning-enabled run.

## Phi-4 frequently added explanation after an answer ID

Phi-4 had **327 first responses** that failed the output format, plus two HTTP failures. Many outputs began with an answer ID and then added explanation, sometimes reaching the cap. A uniform, post-hoc leading-ID parser recovers 536 correct responses from the saved outputs, compared with 428 under the strict parser. This sensitivity check adds no calls and does not replace the strict diagnostic result.

## Evidence remains unchanged

The [original eight-LLM evidence](../results/releases/expansion_2026-10-15) preserves Phi-4's run. The [October 16 regular-LLM ledgers](../results/runs/llm_additions_2026-10-16) preserve Haiku and DeepSeek. The private reference key is unchanged. No answer was discarded, replaced or inferred from an unfinished explanation.

## October 18 stopped samples

The new generative candidates were screened after the fixed first 100 questions and rechecked cumulatively after each further 100. The author approved a hold for accuracy below 50%, model-output failures at least 5%, or median response time above 2,000 ms. The prefix has uneven family coverage and dependent variants; these are operational selection rules, not a representative full-bank accuracy estimate. Provider failures are distinct from explanations, refusals and malformed output. No stopped sample is extrapolated to 1,136 or included in the main ranking.

| Stopped configuration | Completed | Correct on completed | Model-output failures | Provider/transport failures | Sample median | Known actual sample cost | Unknown charges | Stop reasons |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Mistral Small 4 | 100 | 18/100 | 0 | 68 | 292 ms 🟨 Fast | $0.00129714 + ? | 135 | accuracy_below_50_percent |
| Solar Pro 4 | 800 | 424/800 | 40 | 0 | 591 ms 🟧 Moderate | $0.02372823 | 0 | model_output_failures_at_least_5_percent |
| Ling 3.1 Flash | 100 | 12/100 | 86 | 0 | 2647 ms 🟥 Slow | $0.00254607 | 0 | accuracy_below_50_percent, model_output_failures_at_least_5_percent, median_above_2000_ms |
| Laguna S2.1 | 100 | 42/100 | 23 | 11 | 260 ms 🟨 Fast | $0.00238887 + ? | 12 | accuracy_below_50_percent, model_output_failures_at_least_5_percent |
| DeepSeek V4.1 Flash 1017 | 100 | 62/100 | 7 | 0 | 388 ms 🟨 Fast | $0.00273750 | 0 | model_output_failures_at_least_5_percent |

Sample costs above are actual recorded costs, not normalized per-1,000 prices. Their median bands describe only their observed sample. [Bound screening receipts and unchanged attempt ledgers](../results/runs/llm_additions_2026-10-18) retain the progression and the approved cutoffs.

The separate native Solar Decide route was stopped for latency after 347 recorded responses: 311/347 correct, with a 4577 ms sample median. It had 1 unresolved dispatch whose result and charge remain unknown. It is not the Solar Pro 4 chat model in the table. Its [stop receipt and original partial evidence](../results/runs/native_additions_2026-10-18/solar_decide_partial) remain unchanged and are not replayed.

## Compatibility-only interfaces

| Interface | Probe HTTP status | Recorded error | Known probe charge |
|---|---:|---:|---:|
| Xing 4.0 29B A4B free | 429 | Provider returned error | Unknown |
| Tev1 4B experimental chat interface | 400 | togethercomputer/tev1-4b-experimental is a decisions model and cannot be used with the chat/completions endpoint. Use the /api/alpha/decisions endpoint instead. | Unknown |

These are unscored compatibility calls, not zero-accuracy benchmark runs. Tev subsequently completed all 1,136 questions through OpenRouter's native adapter; it remains a decision-specialized generative model, not an architectural non-generative control. Xing's free route returned a rate-limit error; this does not establish its decision accuracy.

## Separate experimental costs

| Cost bucket | Known actual cost | Attempts with unknown charges |
|---|---:|---:|
| Four selected complete runs | $0.10295960 + ? | 40 |
| Stopped samples | $0.03269781 + ? | 147 |
| Compatibility probes | $0.00017619 + ? | 2 |
| All new experimental calls | $0.13583360 + ? | 189 |


Missing charges are not zero. Only the four selected complete runs contribute to current full-bank model costs; stopped-sample and compatibility charges are separate and none of these totals is an independently reconciled invoice. The [current aggregate](../results/releases/overall_llm_expanded_2026-10-18/summary.json) retains exact amounts and counts.
