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


## Method

Every main configuration has 1,934 selected primary responses across 41 categories. Strict accuracy counts a wrong usable answer and an unsuccessful response as unsuccessful in the same fixed denominator. Input limits, declared refusals, rate/service failures and other errors are shown separately. They do not establish what an unserved model would have answered.

The 1,342 original inputs remain exact. Six existing categories (F26–F31) gain 32 questions each, growing from 8 to 40. Ten practical categories (P01–P10) add 40 questions each. The 120 companion diagnostics remain separate. The downloadable native JSONL preserves all original envelopes, including 206 legacy packets; use native_input verbatim for faithful replay. Category IDs are authoritative. P07 and P10 retain older wording aliases in source metadata; question membership is unchanged.

This is a post-measurement presentation cutoff: unrounded correct/n must be at least 62%. The same 26 model set appears in every main graph, category table, leader list and relative-profile analysis. Individual category scores below 62% remain visible. All 38v2 measurements remain in all_statistics.json. Kev 4B and H2O Lightning Nemotron are explicitly retired from the main selection; AutoThink is an adaptive archival reference. Qwen, plain H2O and older Jev remain historical; only Jev 1.14 is current. Models tested only on the older bank have no inferred v2 score.

For unchanged configurations, recorded exact baseline and expansion inputs are reused, including 304Microsoft development responses. Upgraded defaults use the authorized full-bank runs; Fastino's current catalog-declared v2.3 BF16 replaces the earlier v2.2 NVFP4 measurement. Returned identities and source fingerprints are recorded in model_metadata.json; aliases and captured metadata are not independent attestation of hidden weights. Trio's native request alias resolved to the same returned dated version. No failed question was shortened, and no scored retry or best-of selection replaced a primary response. Busy-service backoff applied only before unattempted Drex/Clef inputs; all first failures remain recorded.

Timing distributions pool individual primary complete-response client times; phase/category medians and p95s are never averaged. Network is included; preparation, loading, warmups, queueing and cooldowns are excluded. Providers, precision, concurrency, routes and dates differ. Retained baseline and new timings can span sessions. Quick failures can reduce all-primary latency; usable-only medians are exported separately. These are service measurements, not isolated architecture-speed comparisons.

Native closed-choice counters vary by provider and are not uniformly generated reasoning tokens. Trio does not report this counter. Sol used reasoning none; Opus 5 used thinking disabled with JSON choices; Sonnet 5.5 used its verified no-thinking between_tools configuration with no tools supplied. These are the only three main LLM references. The adaptive AutoThink result is preserved outside the main System 1 view.

The local deployment was selected as an accessible older setup. Owner records identify an RTX 2060 with 6GB VRAM; current API evidence attests CUDA, allocation and model digests without independently identifying the physical GPU product. Context and quantization belong to each measured configuration. Local hardware/electricity cost is unmeasured. A complete 1,934-call monetary cost ledger has not been consolidated; older 1,342-call tariffs are not scaled into a new v2 bank price.

The bank includes related generated variants and model-guided development, including Jev and retained Microsoft/Drex feedback. It is a development benchmark, not an independently sampled intelligence or deployment-safety test. Fresh held-out items and repeatability measurements are needed for broader generalization. The public export contains answer-free questions, aggregate correctness and per-input timing/status/hash evidence. The scoring key, model choices, probabilities and per-question correctness remain private under the established release policy. Offline public checks reproduce coverage, timing and aggregate consistency; they cannot independently rescore hidden answers.
