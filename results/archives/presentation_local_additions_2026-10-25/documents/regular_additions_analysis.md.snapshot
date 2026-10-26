## Tencent Hy3 outscored regular Luna at lower reported cost

Tencent Hy3 scored **790/1,136 (69.5%)**, 63 more correct answers than regular Luna and 113 more than Luna Decisions. Its core-only result was 446/640 (69.7%), versus regular Luna's 431/640. Reported full-run cost was **$0.02774624**, below regular Luna's $0.03431990, but its median response was slower: **1,423 ms versus 942 ms**. One failed attempt omitted a charge. Tencent's captured pricing included a lower-price time window; the reported cost describes the window in which this run occurred.

Hy3 answered every sampled lookup, transitive-comparison, directed-reachability and source-authority question correctly. Belief tracking was 34/44, versus regular Luna's 16/44 and Luna Decisions' 30/44. This family asks whose knowledge should change after an event, given what each person observed. Necessary conditions were also stronger than regular Luna, at 31/46 versus 13/46. Exact truth counting (15/65), sequential procedures (12/42) and repeated swaps (22/46) remained weak.

Hy3 did answer 59 questions that Jev 1.14 missed, while Jev answered 198 that Hy3 missed. Sequential procedures were a family-level crossover, at 12/42 versus Jev's 4/42; neither result supports dependable procedural execution. Microsoft-Decision-1 still scored 51 more questions correctly overall than Hy3, with a 288 ms median and $0.01327712 reported cost. The leading native decision services retain substantial advantages on this tested contract.

## Qwen3.8 Flash improved on the older Qwen configuration

Qwen3.8 Flash scored **763/1,136 (67.2%)**, compared with 564/1,136 (49.6%) for Qwen3-30B-A3B Instruct 2507. These are different model configurations, not a controlled checkpoint upgrade. It also outscored regular Luna by 36 correct answers, with an **862 ms median** versus Luna's 942 ms. Its reported run cost was higher, at **$0.05003065**, with 34 failed attempts omitting charges.

It was strong on directed reachability (37/37), fault diagnosis (43/44), preference ordering (44/45) and transitive comparison (33/34). Necessary conditions improved to 33/46, versus regular Luna's 13/46. Temporal interval reasoning was weaker at 19/36, compared with regular Luna's 24/36 and Tencent's 31/36. Procedures (6/42), exact truth counting (20/65) and causal intervention (16/44) remained poor.

Only three first outputs failed the answer format. Thirty other first attempts failed at the provider or transport level. Permitted recoveries raised the eventual score to 779/1,136, but the ranking retains the first-attempt 763. Its **5,717 ms p95** also shows a much slower tail than its median suggests.

## MiMo finished near Luna Decisions with a slower response

MiMo V2.6 Flash scored **684/1,136 (60.2%)**, seven more correct answers than Luna Decisions but 43 fewer than regular Luna. Its median was **1,429 ms** and p95 **6,032 ms**, with **$0.04312187** in reported charges and five attempts with unknown charges. It did not improve on regular Luna's overall accuracy, median latency or known run cost.

MiMo answered all 37 lookup questions correctly and scored 36/37 on reachability, 42/45 on preference ordering and 40/46 on rule verification. Necessary conditions (18/46), exact truth counting (14/65), causal intervention (18/44) and sequential procedures (5/42) were weaker. It had 35 capped model outputs and five provider or body-read failures. The 3.1% format-failure rate stays below the main comparison's 5% exclusion cutoff; all 40 unsuccessful first attempts remain in its denominator.

## Nemotron 3.5 Super VL scored 62.5 percent

Nemotron 3.5 Super VL answered **710/1,136** questions correctly, compared with regular Luna's 727 and Mercury 2.5's 702. Its median full response was **465 ms**, versus 942 ms for regular Luna and 534 ms for Mercury. Reported charges for the full run were **$0.03381740**, close to regular Luna's $0.03431990 and above Mercury's $0.01321493 promotional run cost. Two provider errors omitted charges. The score includes those unanswered cases.

Nimble v4 Max scored 997/1,136 (87.8%) at a calculated tariff cost of $0.03365973 and a 236 ms median. Its run cost was almost the same as Super VL's reported charge, with 287 more correct first answers and roughly half the median response time. Both were tested on October 16, through different providers and interfaces.

This is a different, larger Nemotron configuration from Lightning. It returned 1,134 valid first answers, all without a reported hidden reasoning trace. One upstream failure arrived as HTTP 502; another arrived inside an HTTP-200 error envelope without a model answer. The second response initially triggered an identity guard. Its recorded attempt was preserved as unsuccessful, and only unattempted questions were resumed. No existing question was replayed or replaced. The [continuation receipt and frozen helper](../results/runs/llm_additions_2026-10-16/nemotron35supervl) document the handling.

Super VL was perfect on sampled lookup and transitive comparisons, and scored 43/46 on rule verification and 40/43 on set relations. Necessary conditions were only 11/46, exact truth counting 17/65 and procedures 8/42. It returned decisions consistently under the short-output instruction; the weak family scores mostly reflect wrong valid choices rather than format failures.

## Nemotron Lightning was fast but scored 33.3 percent

Nemotron 3.5 Lightning answered **378/1,136** questions correctly with a **280 ms median** and **533 ms p95**. Its reported cost was **$0.02323863**, including eligible retries; 82 failed attempts omitted charges. Its first attempts included 67 upstream rate limits and one DNS failure. Recoveries brought the eventual score to 395/1,136, with 14 cases still unanswered. Valid first answers were correct on 378/1,068 cases (35.4%), so transport failures do not account for the low score. Every valid first answer was a complete numeric choice using two output tokens, without reported reasoning tokens.

Lightning's strongest sampled family was transitive comparison, at 27/34: for example, using A before B and B before C to compare A with C. It scored 25/37 on lookup and filtering, but only 5/44 on causal intervention, 7/46 on necessary conditions and 7/43 on verbal spatial tracking. These are results for the tested short-output, reasoning-off configuration.

An earlier, separate 25-question pilot used temperature 0 and scored 15/25. The full run omitted temperature to preserve the original eight-LLM request protocol; it scored 9/25 on those same pilot items, with 24 valid first answers. The two samples used different sampling configurations and are not pooled. The full result does not establish performance under a greedy or reasoning-enabled configuration.

## GLM followed the output instruction but scored 29.4 percent

GLM 4.7 Flash returned **1,134 usable first decisions**, all complete two-token numeric choices with zero reported reasoning tokens. Only **334/1,136 (29.4%)** were correct; 800 were wrong valid choices. The remaining two responses were provider-error envelopes, not model explanations or truncation. GLM stays in the main ranking because it complied with the output contract. Its low accuracy is a different result from Haiku's high unanswered rate.

Transitive comparisons were its strongest sampled family at 30/34. Necessary conditions were 4/46, Boolean scope 6/48, rule verification 8/46 and source authority 8/37. It preserved the same semantic choice across all rotations in only 2/25 complete rotation panels. Returning a valid option ID did not establish consistent interpretation of the choices.

Its median full response was **560 ms**, but p95 was **17,056 ms**. The run cost **$0.02005890** in reported charges, with two unknown error charges. The tested route was OpenRouter/Cloudflare; this is an end-to-end service measurement. The [continuation receipt](../results/runs/llm_additions_2026-10-16/glm47flash/continuation_receipt.json) preserves both upstream failures and documents resuming only unattempted questions after the original identity guard paused the run.
