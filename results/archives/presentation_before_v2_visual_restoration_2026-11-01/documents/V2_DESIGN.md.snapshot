# System 1 Decision Benchmark v2: design and selection

The frozen core contains 1,934 questions, 41 categories and no replacement of the original 1,342 native inputs. Six existing categories (F26–F31) grow 8→40 by adding 32 each; ten new practical categories (P01–P10) add 40 each. The 120 diagnostics are separate.

The exact native JSONL is the authoritative replay format; 206 legacy envelopes remain unchanged. CSV and TXT support inspection. The public key is intentionally omitted under the established benchmark policy.

## Practical categories

| ID | Category | Questions | Decision being tested |
| --- | --- | --- | --- |
| P01 | Understanding requests and routing | 40 | Identify the governing request and route it under explicit priority and exception rules. |
| P02 | Recognizing multiple requested actions | 40 | Recognize all currently requested actions, including cancellations and scoped revisions. |
| P03 | Tracking current conversational intention | 40 | Track the current intention after conversational corrections and changes of scope. |
| P04 | Selecting a tool or requesting clarification | 40 | Choose a tool or ask for necessary clarification using the stated prerequisites. |
| P05 | Checking authorization and scope | 40 | Apply authorization boundaries, revocations, delegated scope and external constraints. |
| P06 | Making decisions with untrusted content | 40 | Keep instructions in untrusted documents separate from the authorized task. |
| P07 | Applying a contextual content policy | 40 | Apply an explicit contextual content-policy rubric to the facts provided. |
| P08 | Extracting and normalizing facts | 40 | Extract facts and normalize aliases, units or representations under explicit rules. |
| P09 | Checking claims against supplied evidence | 40 | Check whether supplied evidence supports, contradicts or leaves a claim unresolved. |
| P10 | Assigning severity or priority from a rubric | 40 | Assign severity or priority using the supplied rubric and precedence rules. |


## Inclusion

The final 62% cutoff uses unrounded correct/n, including unsuccessful responses. A 1,934-question model needs at least 1,200 correct. The same 26 configuration set is used for graphs, category scores, category leaders and relative profiles. Kev 4B, Nemotron and adaptive AutoThink are explicitly outside this set. Qwen, plain H2O and Jev 1.13 remain historical. The three LLM references are Sol, Opus 5 and Sonnet 5.5 with reasoning disabled. All 38v2 records remain public separately. Older 1,342-only scores are not converted or mixed into v2 rankings.

## Validity limits

The new questions were hardened and reviewed during model-guided development. Jev and retained Microsoft/Drex feedback are development exposure. Related variants, selected model feedback and a single recorded primary response per input limit independent generalization. Category specialties are descriptive and exploratory. Fixed-bank counts are exact; paired resampling explores hypothetical bank mixtures and does not measure inference repeatability. Full scoring-key and answer audits remain owner-side; public checks cover input hashes, coverage, timing and aggregate consistency.
