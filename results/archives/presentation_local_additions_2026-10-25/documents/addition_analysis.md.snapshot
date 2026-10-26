## Nimble v4 Max changes the overall leader

**Added October 16, 2026.** Nimble v4 Max scored **997/1,136 (87.8%)**, ahead of Jev 1.14's 929/1,136 (81.8%). Its advantage is 68 correct answers, or 6.0 percentage points. The core-only comparison has the same direction: 573/640 (89.5%) versus 538/640 (84.1%). The new result changes the overall conclusion: Jev remains substantially stronger than both Luna services on these questions, but no longer leads this expanded text comparison.

Max improved on Jev 1.14 in 16 families, tied it in eight and scored one question lower on sufficiency and inconsistency (29/35 versus 30/35). It was correct on 98 questions Jev 1.14 missed, while Jev was correct on 30 that Max missed. That is a substantial overall gain without making either service a universal replacement for the other.

The clearest gains are truth-teller consistency (46/62 versus 31/62), exact truth counting (37/65 versus 26/65), and sequential procedures (14/42 versus 4/42). Truth-teller consistency means finding an account in which people's claims about who is truthful fit together. Exact truth counting asks how many supplied statements hold under the same facts. Sequential procedures require updating a state after each prescribed operation. Max improves those functions, but 37/65 on counting and 14/42 on procedures remain poor bases for unattended decisions. Its 47/69 scheduling and 32/46 swap-tracking scores also leave substantial weaknesses.

Max answered every sampled question correctly in 15 families, including necessary conditions, Boolean scope, temporal intervals, belief tracking, exceptions and priority rules. Those are observations on this generated bank, not reliability guarantees. At a returned confidence cutoff of 0.9 it retained 742 questions, all correct in this run (65.3% coverage). The cutoff was examined on the same bank and has not been validated on a new workload.

Its median complete response was **236 ms**, compared with 182 ms for Jev 1.14, and its calculated tariff cost was **$0.03365973** for the full bank, compared with Jev's reported $0.02723011. Max buys higher observed accuracy at somewhat greater cost and latency. Nimble used Bespoke directly, while Jev used OpenRouter, on different days; these timings describe the tested services, not an isolated architecture comparison.

## Nimble v4 offers a different price and quality trade-off

The smaller Nimble v4 scored **902/1,136 (79.4%)**, 27 questions below Jev 1.14 and 175 above regular Luna. Its calculated tariff cost was **$0.01495988**, about 45% below Jev 1.14's reported cost. Its median was **214 ms**, with a 260 ms p95. It did not improve on Jev's overall score or median latency, but its lower cost makes it a useful alternative on tasks where its particular strengths fit.

Nimble v4 scored 44/44 on belief tracking, 37/37 on planning with preconditions and 46/46 on rule verification, compared with Jev 1.14's 39/44, 36/37 and 45/46. It also reached 38/65 on exact truth counting, slightly above Max and well above Jev, although still far from dependable. Its weaker areas include swap tracking (21/46), sequential procedures (8/42), scheduling (39/69) and spatial tracking (24/43). The lower total is not a formatting penalty: all 1,136 first answers were usable typed choices.

## Microsoft improves the low-cost comparison

Microsoft-Decision-1 scored **841/1,136 (74.0%)**, with all first answers usable, a **288 ms** median and a 574 ms p95. Its **$0.013277124 API-reported cost** is almost the same as Mercury's $0.01321493 promotional run cost, while it answered 139 more questions correctly. It also had a shorter observed median than Mercury's 534 ms. Both used OpenRouter, but their dates and backends differ.

Microsoft was perfect on the sampled lookup, transitive-comparison, reachability, source-authority and fault-diagnosis questions. It was also strong on belief tracking (40/44) and exceptions (48/52). Exact truth counting was 37/65, ahead of Jev 1.14's 26/65, but necessary conditions and contraposition were only 22/46, swap tracking 24/46 and sequential procedures 6/42. It is a stronger inexpensive text-decision result than the regular LLMs in this bank, not the strongest model overall.

## The three native additions completed without a failed first attempt

All three services completed 1,136 first attempts without a transport failure, invalid choice or recovery request. Their 3,408 cases are preserved in the [fourteen-model snapshot](../results/releases/overall_2026-10-16/summary.json). The later regular-LLM runs extend that evidence without replacing any original response. The current ranking applies the output-compliance inclusion rule to old and new models alike.

Microsoft reports a dollar charge in each response. Nimble reports input-token usage but no dollar charge, so its displayed costs are usage multiplied by the captured published prices: $0.04 per million input tokens for v4 and $0.09 for Max, with free output. These are tariff calculations, not independently reconciled invoices. Similar per-token prices do not imply identical per-question costs because services count different prompt overheads and tokens.
