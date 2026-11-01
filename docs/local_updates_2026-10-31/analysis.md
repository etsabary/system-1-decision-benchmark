## Cerno 4B approaches the stronger local configurations

Cerno 4B scored **983/1,342 (73.2%)** on the deliberately older RTX 2060 with 6 GB VRAM. D3 Flash Artemis retains **995 (74.1%)** and StartLux Instant **988 (73.6%)**. Cerno's **690 ms median** was longer than D3's 408 ms and Instant's 282 ms. Its mean / median / p95 were **725 / 690 / 1,112 ms**.

Cerno answered every comparison question (**40/40**), **50/52** rule-counterexample questions and **41/43** lookup questions correctly. These ask it to combine stated orderings, find a case that disproves a rule, or filter records by their conditions. Sequential procedures, applying each edit to the updated state, scored **11/48**. Truth-teller consistency scored **36/74**, and exact truth counting **35/71**. Its local NF4 conversion may differ from the upstream weights; this result applies to the recorded build.

## Jue is the fastest completed run in the new batch

Jue 2.5B scored **801/1,342 (59.7%)**, with **175 / 162 / 314 ms** mean / median / p95. It uses FP16 weights with FP32 LoRA, rather than a local low-bit conversion. Its cybersecurity specialization was not specifically evaluated by this general decision bank.

Jue selected records correctly in **40/43** lookup questions and found the governing source despite conflicting stale records in **39/43**. Sequential procedures scored **12/48**, object swaps **16/52**, and exact truth counting **24/71**. It answered 47 more questions correctly than Cox, with approximately one fifth Cox's 822 ms median latency.

## Dexy, Cox and Iota add distinct measured routes

Dexy 9B, a local NF4 conversion with INT8 embeddings, scored **833/1,342 (62.1%)** at **696 / 670 / 1,012 ms** mean / median / p95. Lookup and following directed paths each scored **39/43**; sequential procedures scored **10/48**. Cox's provider INT8 build scored **754 (56.2%)**, with **876 / 822 / 1,029 ms**. Iota's original joint-schema Q8_0 release scored **738 (55.0%)**, with **315 / 288 / 535 ms**. It is a different release from iota-decide-4b-v0.4.

Cox includes one lost connection. Jue, Cerno 4B and Dexy each include one context-limit failure; Iota returned usable decisions throughout. Every failure remains unsuccessful in the full denominator. No failed question was shortened or retried. The Cerno 9B and MiMo local builds stopped during context-limit screening and have no full-bank score; the [screening record](screened_routes.json) preserves their sample sizes and reasons.

## The main comparison now requires at least 50% overall

This is a reporting selection requested after measurement. It applies to the overall score, including failed first attempts, for every setting and model format. Exactly 50% qualifies. The same qualifying set appears in the overview, named-category tables, category leaders and narrative. Complete measured records remain available in [all statistics](all_statistics.json); [the separate below-50% catalogue](below_50.html) includes earlier LLM formats and short screens with their original sample sizes.

## October 30: Joey-1 and an extraction-model comparison

Joey-1 scored **773/1,342 (57.6%)**, with a **179 ms mean, 163 ms median and 256 ms p95**. All first attempts returned usable native decisions. OpenRouter reported **$0.00484453** for the full bank, or **$0.00360993 per 1,000 questions**. The reported output-token counter was one per decision; the native endpoint returned no prose or reasoning trace.

The larger Baseten models remain substantially more accurate: **Mammoth-1 84.9%** and **Elephant-1 74.8%**. Their recorded medians were 240 and 139 ms. Those October 21 runs used Baseten directly; Joey used OpenRouter on October 30. Dates and routes remain visible, so these speeds do not isolate model size. The earlier promotional access is not a permanent production price.

Joey was strong on comparisons (**38/40**) and forward conditionals (**42/46**). One-to-one assignments, such as matching people to roles under constraints, fell to **24/67**, versus Mammoth's 64 and Elephant's 60. Sequential procedures scored **11/48**. Its lower cost did not approach the leading models' accuracy on this bank.

**Clairic is reported separately as an extraction adapter.** It returned an integer option ID through OpenRouter's Extractions API and scored **729/1,342 (54.3%)**, with **293 / 263 / 444 ms mean / median / p95** and **$0.05851030** reported cost. Six returned numbers outside the supplied option IDs and count as unsuccessful. Directed reachability, following one-way paths, scored **40/43**; Boolean scope **13/54**, sequential procedures **12/48** and exact truth counting **21/71**. This measures the adapted interface, not a native choice endpoint.

The leaders and their earlier measurements are unchanged. [Clairic's labelled results and category scores](clairic.html) are outside the native decision ranking.

## The overall leaders remain unchanged

Fastino GLiDE leads at **1,154/1,342 (86.0%)**, followed by GPT-6 Sol without reasoning at **1,143 (85.2%)** and Mammoth-1 at **1,139 (84.9%)**. Turion Jev 31B adds **1,121 (83.5%)**: one answer above Perplexity Decider v1.2, three below D3 Ultra, and six below both Respan Span-02 and Drex Max. These are results on this bank, with their original test dates and routes retained.

**D3 Flash Artemis remains the highest-scoring immediate local configuration at 995/1,342 (74.1%)** on the deliberately older RTX 2060 with 6 GB VRAM. StartLux AutoThink reaches 1,005 (74.9%) with adaptive generation, shown in the same local purple with a gold frame. StartLux Instant reaches 988 (73.6%) with a shorter 282 ms median. The StartLux API confirmed CUDA execution but did not identify the precise GPU model, so its badge records CUDA and Q8 rather than assigning unverified hardware.

## Turion handles combined rules better than multi-step procedures

Turion answered **53/54** questions about Boolean scope, **51/52** rule counterexamples and **64/67** one-to-one assignments correctly. Boolean scope asks whether conditions must hold together or whether either is enough. A rule counterexample asks which case disproves a stated claim. One-to-one assignment asks how to match people or objects when each can be used once.

It scored **10/48** on sequential procedures, **41/74** on truth-teller consistency and **30/52** on object swaps. Following a sequence of updates remains a different ability from applying a well-specified logical rule. Its mean / median / p95 were **567 / 502 / 1,006 ms**. All 1,342 responses were usable. Monetary charges were not returned, so the cost is recorded as unknown.

## Trio-Spark is fast and inexpensive, with a lower overall score

Trio-Spark scored **915/1,342 (68.2%)**, with **411 / 407 / 451 ms** mean / median / p95. Its strongest results include following directed links **42/43**, comparisons **39/40**, and lookup **40/43**. Object swaps scored **19/52**, truth-teller consistency **31/74**, and sequential procedures **10/48**.

The requested v1.3 alias returned `trio-spark-2026-10-28`; MachineFi identifies that served release as v1.4. One HTTP 429 and one context-length HTTP 413 remain unsuccessful first attempts. No scored questions were retried or shortened. The recorded charge was **$0.013644162 for the bank**, including 99 free trial calls; normalized to 1,000 questions, **$0.01016704**. At the listed tariff, the same recorded input-token total before the trial allowance is $0.01478757.

## AutoThink keeps the immediate path and sometimes adds generation

The [StartLux implementation](https://github.com/StartLuxLabs/StartLux-Decision) describes a probability gate: an AutoThink model can return an immediate decision when sufficiently sure, or generate a thought and read the answer again. This creates an adaptive route between immediate decisions and deliberation. The exact gate used by this local adapter was not exposed.

In these text calls, **750/1,342 (55.9%) reported zero generated tokens**, with a **306 ms median**. **592 (44.1%) reported generation**, with a **13.12 s median**. AutoThink remains in the main comparison because it retains an immediate decision path, with its adaptive status visible on every view. Generation occurred often enough here that “occasional boost” needs the measured proportion alongside it.

Its overall **483 ms median** hides a long tail: **5,767 ms mean** and **13,652 ms p95**. Its mean was **19.7 times Instant's**. The API reported 288,706 output tokens; 491 calls reported exactly the native 512-token budget. It did not expose the thought or a budget-exhaustion flag. Counts alone do not show the content of the reasoning or whether a thought was unfinished.

## The adaptive variant changes which tasks succeed

AutoThink scored **33/48** on sequential procedures, compared with Instant's **10/48**. These questions require applying instructions through successive changes—for example, updating counters in order when a later action depends on the new value. Scheduling rose **39/76 → 49/76**, object swaps **25/52 → 34/52**, and spatial tracking **26/49 → 33/49**.

There were reversals: choosing which authorised record governs fell **42/43 → 21/43**, reference binding **40/50 → 33/50**, and truth-teller consistency **46/74 → 40/74**. AutoThink uniquely answered 122 questions correctly, Instant uniquely answered 105, both answered 883 correctly, and both missed 232. The net gain is **17 answers, or 1.27 percentage points**.

AutoThink's procedure score ties **Respan's 33/48**, the highest observed here. Respan reached that score without reported generation. The result supports investigating selective extra computation, but does not establish that generation is necessary for these tasks. Instant and AutoThink are different released weights with different prompt attention; this is a comparison of the two served variants, rather than a controlled reasoning toggle on identical weights.

## Images are relevant as a separate matched subset

Trio-Spark and both local StartLux routes accept one image per request. They completed the same **177 single-image questions**; **23 multi-image questions** were unsupported. Trio scored **106/177 (59.9%)**, Instant **101 (57.1%)**, and AutoThink **108 (61.0%)**. AutoThink's image median was **8.36 s**, compared with Instant's **387 ms**, and it reported generation on 99/177 calls. Its image run completed under the explicit adaptive-research speed exception.

On those same 177 items, earlier Amos scored **138 (78.0%)**, Fastino **136 (76.8%)**, and D3 Turbo **132 (74.6%)**, recomputed from their existing records. These subset results appear in the [image report](https://etsabary.github.io/visual-decision-benchmark/report.html#single-image-subset), alongside the separate full 200-question ranking. Turion failed the image-binding probes on the tested endpoint and received no image score.


## Recorded results below 50%

These rows are separate from the main comparison. Full-bank runs, earlier 1,136-question runs and short screens retain their own denominators and interfaces. Format-failure scores measure the tested output contract as well as answer quality. A later qualifying format of the same model remains in the main comparison.

### Full runs removed from the current comparison

| Model / trial | Setting / format | Scope | Correct / tested | Accuracy | Reason |
| --- | --- | --- | --- | --- | --- |
| Snap 2B | local · Native choice | Current full 1,342 | 574/1342 | 42.8% | Overall below 50% |
| ScaleDown Classify-1 | hosted · Native choice | Current full 1,342 | 550/1342 | 41.0% | Overall below 50% |
| Mapika Decider 2B | local · Native choice | Current full 1,342 | 547/1342 | 40.8% | Overall below 50% |
| Solar Decide Flash | hosted · Native choice | Current full 1,342 | 538/1342 | 40.1% | Overall below 50% |
| Sura 2B | local · Native choice | Current full 1,342 | 428/1342 | 31.9% | Overall below 50% |
| GLiClass | local · Native choice | Current full 1,342 | 393/1342 | 29.3% | Overall below 50% |
| Von | local · Native choice | Current full 1,342 | 331/1342 | 24.7% | Overall below 50% |
| Laya Typed Decisions | local · Native choice | Current full 1,342 | 322/1342 | 24.0% | Overall below 50% |
| Decima Agent | local · Native choice | Current full 1,342 | 313/1342 | 23.3% | Overall below 50% |
| CLM 8B | local · Native choice | Current full 1,342 | 304/1342 | 22.7% | Overall below 50% |


### Earlier full-bank trials

| Model / trial | Setting / format | Scope | Correct / tested | Accuracy | Reason |
| --- | --- | --- | --- | --- | --- |
| GPT-5.4 nano: bare ID | hosted · LLM bare option ID (16-token cap) | Full corrected 1,136 | 464/1136 | 40.8% | Complete corrected 1,136 bank only; no comparable 1,342 record located; below 50% even among usable answers |
| Granite 4.2 8B: bare ID | hosted · LLM bare option ID (16-token cap) | Full corrected 1,136 | 478/1136 | 42.1% | Complete corrected 1,136 bank only; no comparable 1,342 record located; below 50% even among usable answers |
| Qwen3-30B-A3B Instruct 2507: bare ID | hosted · LLM bare option ID (16-token cap) | Full corrected 1,136 | 564/1136 | 49.6% | Complete corrected 1,136 bank only; no comparable 1,342 record located; below 50% even among usable answers |
| Mistral NeMo 12B: bare ID | hosted · LLM bare option ID (16-token cap) | Full corrected 1,136 | 421/1136 | 37.1% | Complete corrected 1,136 bank only; no comparable 1,342 record located; below 50% even among usable answers |
| Nemotron 3.5 Lightning: bare ID | hosted · LLM bare option ID (16-token cap) | Full corrected 1,136 | 378/1136 | 33.3% | Complete corrected 1,136 bank only; no comparable 1,342 record located; below 50% even among usable answers |
| GLM 4.7 Flash: bare ID | hosted · LLM bare option ID (16-token cap) | Full corrected 1,136 | 334/1136 | 29.4% | Complete corrected 1,136 bank only; no comparable 1,342 record located; below 50% even among usable answers |
| Phi-4 14B: original bare ID | hosted · LLM bare option ID (16-token cap) | Original 1,136, format diagnostic | 428/1136 | 37.7% | Original bank; 327 invalid outputs. Corrected complete run unavailable. |
| Claude Haiku 5.5: original bare ID | hosted · LLM bare option ID (16-token cap) | Original 1,136, format diagnostic | 337/1136 | 29.7% | Original bank; 781 invalid outputs. Corrected complete run unavailable. |
| MiniMax M3 (no thinking, SambaNova) | hosted · LLM bare option ID (16-token cap) | Earlier full 1,342 | 602/1342 | 44.9% | Separate pinned SambaNova route; do not merge with other MiniMax providers |


### Stopped screens and output-format trials

| Model / trial | Setting / format | Scope | Correct / tested | Accuracy | Reason |
| --- | --- | --- | --- | --- | --- |
| ADM-1 NF4 | local · Native choice | Partial screen | 17/100 | 17.0% | Below 50% on the first 100 questions |
| DeepSeek V4 Pro0813: reasoning none | hosted · LLM bare option ID (16-token cap) | Partial screen | 45/100 | 45.0% | 100 usable first attempts; accuracy cutoff stopped this partial run. |
| Ling 3.1 Flash: bare ID | hosted · LLM bare option ID (16-token cap) | Partial screen | 12/100 | 12.0% | 86 output-format failures; 12/14 usable choices correct. |
| Laguna S2.1: bare ID | hosted · LLM bare option ID (16-token cap) | Partial screen | 42/100 | 42.0% | 23 output-format and 11 transport failures; 42/66 usable choices correct. |
| Claude Sonnet 5.5: bare ID | hosted · LLM bare option ID (16-token cap) | Partial screen | 26/110 | 23.6% | 84 invalid outputs; all 26 usable choices correct. Later JSON-choice trial qualifies. |
| Coba 1B: local GPU screen | local · Native choice | Partial screen | 8/20 | 40.0% | 20-case screen; one truncated/unverified input and 19 usable choices. |
| Cribl Decision 2 Mini (0.8B) | local · Native choice (PyTorch) | Partial screen | 145/331 | 43.8% | 331 usable first attempts on Apple M2; stopped screen. Excluded from main graphs. |
| Mistral Small 4: availability failure screen | hosted · LLM bare option ID (16-token cap) | Partial screen | 18/100 | 18.0% | Availability screen: 68 transport failures. Counts do not isolate logical accuracy. |




## Method

The main display contains 56 configurations with at least 50% overall accuracy. All 66 complete 1,342-question model records remain in the full evidence export, with every earlier score, timing, cost and test date unchanged. The ten removed full-bank rows and other below 50 trials are listed separately. Short screens never enter the full-bank ranking.

The October 31 additions use the same frozen 1,342 native states, instructions and five choices, seed 2026101906. Five complete runs and three partial screens account for 6,850 first attempts. Only one local model and request ran at a time. Direct wired LAN was used throughout. Loading, synthetic admission and warmups are outside the connection-to-complete-response timer. All first attempts, including failures, remain in the denominator and timing distribution. No scored retry or question truncation.

The normal screen stops a model after at least 20 calls if cumulative median exceeds 2,000 ms or unusable responses reach 5%. The user additionally authorized stopping below 50% on exactly the first 100. Two local builds stopped for context limits, and one stopped on accuracy. Those partial results do not measure a complete-bank accuracy. Other prior output-format and speed exclusions remain preserved in their dated diagnostics.

The owner identifies this deliberately accessible local setup as an RTX 2060 with 6 GB VRAM. Live metadata confirms CUDA execution, allocated VRAM, precision, alias and stable source revisions, but does not independently attest the hardware product or weights. Cox INT8, ADM NF4 and Iota Q8_0 are provider-supplied representations. Jue uses FP16 + FP32 LoRA. Cerno, Dexy and MiMo use locally quantized builds, labelled in metadata. Compact native responses omit explicit truncation and load-duration fields; oversized synthetic inputs reject. Some llama.cpp context rejections use a structured HTTP 500 with an explicit oversized token count, rather than 4xx. Ordinary 500 errors remain failures. Native typed-index counters 0/1 do not expose reasoning.

All prior adaptive StartLux, Apple M2, hosted-provider and reasoning-off LLM settings remain attached to their original rows. Purple marks local CUDA, magenta Apple M2, blue hosted decisions and pale yellow LLM references. AutoThink retains its thick gold frame, dot pattern and generation proportions. Its authorized adaptive research exception is unchanged. Colors encode accuracy and speed/cost using the same fixed scales. Provider load, hardware, interfaces and dates differ; these are measured service timings, not isolated architectural speed comparisons. Local hardware and electricity costs are unmeasured.

Offline audits bound the private answer key, checked unique first attempts, native/wire request and response hashes, model revisions, CUDA placement, coverage, category sums and timing. Public artifacts contain aggregate correctness and answer-free timing/status/hash evidence. They do not include private keys, model choices, per-item correctness or private network details. Public checks reproduce coverage, timing and aggregate arithmetic; private-key accuracy cannot be independently rescored from public aggregates. Unequal category sizes and dependent variants remain qualifications of the developing bank.
