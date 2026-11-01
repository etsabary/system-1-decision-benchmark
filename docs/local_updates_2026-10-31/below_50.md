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
