# Output compliance diagnostics

Haiku 5.5, DeepSeek V4.1 Flash and Phi-4 had substantial difficulty returning only a numeric decision within the 16-token output limit. Their saved runs remain public, but they are excluded from the [main benchmark](../README.md), function tables and comparative charts.

The author requested this separation after reviewing the outputs. The reporting rule excludes a model when at least **5% of the 1,136 planned first attempts** fail the output contract. This is a post-hoc operational cutoff, not a preregistered rule or a statistical significance test. HTTP errors, connection failures, body-read timeouts and upstream error envelopes are counted separately and do not trigger this format exclusion. Lower levels of format failure remain unsuccessful first attempts in the main results.

All models were asked to return only option ID 1, 2, 3, 4 or 5, with reasoning disabled and `max_tokens=16`. No malformed answer was retried. A valid but wrong choice was not retried either. Permitted API recovery attempts and their charges remain separate from the primary first-attempt scores.

## Three unranked runs

The strict full-bank figures below describe success under the tested output contract. They are diagnostic results, not entries in the main accuracy ranking. Accuracy among usable answers is conditional on which questions a model answered directly; it cannot be extrapolated to the unanswered questions.

{{EXCLUDED_RESULTS}}

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
