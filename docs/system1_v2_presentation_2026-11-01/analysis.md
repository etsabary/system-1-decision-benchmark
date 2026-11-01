## What the larger bank shows

Fastino GLiDE v2.3 has the highest observed full-bank score: **1603/1,934 (82.89%)**, compared with GPT-6 Sol's **1597 (82.57%)**. The six-answer gap is small: 147 questions favor Fastino and 141 favor Sol; the paired exact test gives **p=0.768**. A 95% paired item-resampling interval for the accuracy gap spans -1.40 to +2.02 percentage points. The category-mixture interval is wider, from -2.67 to +3.68 points. These intervals describe hypothetical bank mixtures, not inference repeatability or independent template sampling. This is not evidence of a general intelligence advantage.

Equal-weight category accuracy reverses the narrow lead: **Sol 82.83%**, Fastino **82.52%**. On the 192 logical additions both score 129; on the 400 practical additions Sol scores 325 and Fastino 312. Fastino's clearer measured advantage is latency: **216 ms median versus 999 ms**, about 4.6 times faster under these collection conditions.

**D3 Ultra leads the 592 additions with 460/592 (77.70%)**, including 138/192 logical additions. It reaches 81.90% overall with a 164 ms median. Neither the overall ranking nor practical-only scores fully describe this profile.

**StartLux Instant leads the eight measured local configurations on the full bank:** 1290/1,934 (66.70%), 310 ms median, and usable responses on all 1,934 inputs. It ties for the planning lead at 40/43. Among Artemis's 1,765 usable inputs, Instant scores 1,226 and Artemis 1,223. On the 1,699 inputs without a context rejection from any of the eight locals, Artemis scores 1,190 and Instant 1,187. These selected subsets show a near-tie; Instant's full-bank lead also reflects broader input coverage. Untested local models cannot be ranked from this run.

### Distinct observed specialties

| Model | Strong category | Limitation or weaker category |
| --- | --- | --- |
| Fastino | Truth-teller consistency 61/74, versus Sol 38/74 | Robust decisions without a prior 16/40; tool/clarification selection 19/40 |
| Sol, no reasoning | Practical additions 325/400; contextual policy 39/40 | Sequential procedures 18/48; truth-teller consistency 38/74 |
| D3 Ultra | Information-flow security 37/40; contextual policy 40/40 | Sequential procedures 16/48 |
| Respan Span-02 | Sequential procedures 33/48, ahead of the next observed 24/48 | Fact extraction/normalization 13/40; severity rubric 14/40 |
| Turion Jev 31B | Exact truth counting 53/71 | Sequential procedures 10/48 |
| Kettei-fat | Request routing 39/40; source authority 43/43 | Exact truth counting 19/71 |
| Opus 5, no thinking | Authorization/scope 32/40; one-to-one assignments 66/67 |185 declared refusals affect full-bank coverage |

Category specialties are exploratory across many comparisons, generally based on 40–76 questions. Narrow leads do not establish general expertise. All leader/tie tables use the same 26 qualifying configurations.

The additions retain headroom: the best observed score is 19/40 for robust decisions without a prior and 23/40 for fact extraction/normalization. Low accuracy alone is not a validation of question quality; these are the frozen, previously reviewed tasks used for this evaluation.


## Cost evidence

Costs now use the selected primary calls on the same 1,934 inputs as the scores. The answer-free cost ledger joins to all 73,492 timing records by model, item, native-input hash and source-record hash. Warmups, probes, recovery attempts, model reviews and account balances are excluded. USD per 1,000 is the known run subtotal divided by 1,934 and multiplied by 1,000; it is not the bill for a separate 1,000-call run.

**Reported charges and estimates are different evidence.** Reported charges retain the provider's recorded monetary amount, including cache accounting where supplied. Estimates use captured per-call usage and tariffs at collection, including tariff changes between baseline and additions. They are not recalculated at today's prices. Recorded zero-dollar receipts, when present, remain receipts; a public or promotional free endpoint without a receipt is labelled free access instead.

**Missing charges stay missing.** Opus has 1,751 monetary records and 183 missing charges; its displayed $4.13548 per 1,000 is only the known subtotal, followed by + ?. This is separate from its 185 declared refusals. Fastino and Celeris use tariff estimates. Mammoth and Elephant mix a promotional free baseline with priced additions and therefore have positive estimated totals. D3 Ultra and Amos used free public access, not metered receipts. Turion has no supported monetary total. Local hardware and electricity were not measured and are never shown as $0 inference.

The comparison describes these captured routes, input lengths, collection dates and access terms. It does not promise future tariffs or equivalent production bills. Cost-status records are available for all 38 measured configurations; the main cost chart and table retain the same 26-model selection as the accuracy comparison. Identity/telemetry metadata preserves the initial v2 capture unchanged; its original “cost not consolidated” note is superseded by these separate cost summaries and ledger.
