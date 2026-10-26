# High-end LLM reference points

## Decision models alongside high-end LLMs

Respan Span-02 scored 1127/1342 (84.0%). The highest-scoring LLM reference was GPT-6 Sol — no reasoning: 1143/1342 (85.2%), a gap of 16 decisions. These are the same questions, facts and option order, with no tools or iterative repair. This measures System 1-style decision performance, not unrestricted reasoning or general intelligence.

## Sol and Span are close overall, with different strengths

Sol scored 1143/1342 (85.2%), versus Span’s 1127 (84.0%). On the original 1136 questions, Sol scored 1014 and Span 1011; on the added 206, Sol scored 129 and Span 116. Sol answered 45/46 forward conditionals and 52/52 necessary-condition questions; Span answered 32/46 and 44/52. Span answered 33/48 sequential procedures and 55/74 truth-teller questions, versus Sol 18/48 and 38/74.

## Speed and cost separate otherwise nearby scores

Sol’s median was 1023 ms, versus Span’s 206 ms: 5.0 times longer. Their recorded full-bank costs were $0.848294 and $0.00474628, a 179-fold difference. Span’s p95 was 2157 ms, versus Sol’s 1546 ms; the median advantage did not extend to that tail measure. These are route measurements, not controlled hardware comparisons.

## Sonnet needs a constrained decision format

Sonnet’s JSON-choice run scored 1070/1342 (79.7%), at a 1506 ms median and $1.923908 for the bank. All 1342 outputs were valid and reported zero thinking tokens. In the separate bare-ID trial, 84 of 110 outputs were unusable explanations or truncated text. That trial is not pooled into this score. Sonnet scored 45/46 forward conditionals, 15/48 sequential procedures and 30/71 exact truth-counting questions.

## Qwen: decision accuracy and account limits

Qwen3.8-Max delivered 967/1342 (72.1%); 1317 first attempts returned usable decisions, with 73.4% accuracy among those responses. There were 25 first-attempt provider/transport failures, retained in the primary score. It scored 38/46 on following if-then rules, 11/48 on step-by-step procedures and 30/74 on truth-teller consistency. Its median was 1191 ms and p95 1731 ms. Hyper Charm’s hourly limit produced some rejected requests; those are not labelled wrong model choices. Its cost is a prepaid-quota valuation, not additional cash billing. The requested none setting is documented in Hyper’s catalog, but the route does not report reasoning-token counts.

## What the comparison supports

Span’s 84.0% sits between Sol’s 85.2% and Sonnet’s 79.7% on these immediate decisions, with much lower recorded cost and a shorter median response. The Qwen row adds a further reference point. Scores and error profiles differ by category. This is a selected reference group, not an exhaustive ranking of every LLM that can disable reasoning. Models that require thinking are outside this comparison. New eight-question categories remain coarse diagnostic samples, not reliability guarantees.

[Interactive methods and category results](https://etsabary.github.io/system-1-decision-benchmark/report.html#llm-references).
