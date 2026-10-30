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


## Method

The October 30 addition uses the unchanged frozen 1,342 questions through OpenRouter, pinned to BaseTen for Joey. All 1,342 first attempts are usable. Clairic uses a separately labelled integer extraction field; six out-of-range IDs count as unsuccessful. Raw responses, request hashes, identity, coverage and category totals were reconciled offline with the frozen private key. The new answer-free timing export includes both models; no scored calls were retried.

Every full text row contains the same 1,342 first attempts across 31 categories. All 56 earlier model records retain their exact scores, timings, costs and dates. The question bank and scoring rules are unchanged. Categories have unequal sizes; the six newest have eight questions each. Related variants and author-development qualifications remain in the earlier releases.

The October 29 runs used the frozen native state, instructions and five original options, in the existing seeded order. One request at a time within each route; local models ran sequentially over direct wired LAN. Timers span request transfer through the complete response; preparation, pacing, loading and warm-ups are excluded. All dispatches were resolved. No tools, scored retries or agentic iteration. AutoThink's internal generation is explicitly included and labelled. Turion and Instant reported zero output tokens. Trio returned native typed decisions without explanatory text; its text endpoint did not return an output-token counter.

The normal two-second cumulative-median speed screen after at least 20 calls remained in effect for immediate-decision routes. AutoThink completed under a user-authorized research exception; its full accuracy, mean, median and p95 remain visible even when deliberation is slow. The native local budget was 512 tokens, with an advertised maximum of 1,024; it was not tuned during the test. Token counters are observations, not visible reasoning traces.

StartLux ran through Ollaya 0.17.0, CUDA, Q8_0, with 2,048-token context. Instant used bidirectional prompt attention; AutoThink used causal attention. Precise GPU model, driver and system RAM were not returned by this route. Previous RTX 2060 measurements retain their original confirmed user-supplied hardware label, chosen deliberately as an older accessible setup; Apple M2 measurements retain their separate magenta label. Sharing a purple local-CUDA color does not assert identical hardware. No projected speed on newer hardware is included. Local hardware and electricity costs are unmeasured.

Trio's cost is the API-reported charge including the trial allowance. Turion's monetary charge is unknown. Earlier free-access and tariff-estimate qualifications remain attached to each model. Provider load, deployment, precision, dates and network paths vary, so latency differences do not isolate model architecture. Selected LLM references retain their earlier reasoning-off settings and limitations.

Private offline audits bound the frozen answer key, reconstructed requests and reconciled category totals. Public exports supply aggregates and answer-free timing and request/response hashes, with no keys or per-item model choices. Public checks reproduce coverage, timing, token counts, cost arithmetic and category sums; they cannot independently rescore private answers. The question bank remains publicly downloadable without the scoring key.
