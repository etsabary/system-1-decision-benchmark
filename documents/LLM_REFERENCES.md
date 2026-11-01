# V2 reasoning-disabled LLM references

Only GPT-6 Sol, Claude Opus 5 and Claude Sonnet 5.5 are current LLM references. Qwen is historical and has no v2 score.

| Reference | Correct /1934 | Accuracy | Median | Control |
| --- | --- | --- | --- | --- |
| GPT-6 Sol · no reasoning | 1597 | 82.57% | 999 ms | reasoning none; verified no reasoning output |
| Opus 5 · no thinking | 1417 | 73.27% | 1547 ms | thinking disabled; JSON-choice;185 declared refusals |
| Sonnet 5.5 · no thinking | 1465 | 75.75% | 1454 ms | between_tools no-thinking control; no tools; zero thinking verified |


Strict accuracy retains refusals and service failures. These configurations do not measure the same models with reasoning enabled. Fastino leads Sol by six answers overall; paired exact p=.768 does not establish an accuracy advantage. Sol leads the equal-category and practical-addition scores. [Full methods](../results/releases/system1_v2_2026-11-01/analysis.md).
