# Results and evidence

[Interactive report](https://etsabary.github.io/system-1-decision-benchmark/report.html) · [Repository overview](../README.md)

## Current comparison

The [October 25 release](releases/native_additions_2026-10-25/) contains all 52 routes on 1,342 questions across 31 categories: 28 hosted decision models, 20 local models and four no-reasoning LLM references.

- [Model statistics](releases/native_additions_2026-10-25/model_statistics.csv)
- [Category scores](releases/native_additions_2026-10-25/category_scores.csv)
- [Aggregate JSON](releases/native_additions_2026-10-25/statistics.json)
- [Accuracy, response-time and cost graphic](releases/native_additions_2026-10-25/accuracy_speed_cost.png)
- [Local GPU metadata](releases/native_additions_2026-10-25/local_model_metadata.json) and [answer-free timing rows](releases/native_additions_2026-10-25/local_timing_evidence.csv)
- [Audit receipt](releases/native_additions_2026-10-25/audit_receipt.json) and [release manifest](releases/native_additions_2026-10-25/manifest.json)
- [Full question bank](releases/consolidated_2026-10-19/questions_1342.csv), [exact native JSONL](releases/consolidated_2026-10-19/questions_1342.jsonl) and [readable questions](releases/consolidated_2026-10-19/questions_1342.txt)

Celeris 1.1 adds 76.1% at 138 ms median; the local KnowLine and Nemotron additions score 72.0% and 61.3%. All 49 prior measurement records are unchanged. Celeris costs are usage-times-tariff estimates; local operating cost is unmeasured. [Celeris timing/usage evidence](releases/native_additions_2026-10-25/hosted_addition_timing_evidence.csv).

## Evidence folders

| Folder | Purpose |
| --- | --- |
| [releases](releases/) | Dated comparisons and their manifests; use October 25 for current results |
| [runs](runs/) | Sanitized earlier run exports used to reconstruct the comparisons, not private execution logs |
| [archives](archives/) | Superseded presentation snapshots and provenance needed to verify earlier seals |
| [figures](figures/) | Earlier shared figures; current charts are in the October 25 release |

Question, measurement, figure, website and dated seal bytes are unchanged by the
folder cleanup. Existing manifests retain their original logical file names;
the [layout manifest](../scripts/layout_manifest.json) records their physical
locations, and the offline validators apply that mapping explicitly.

For viewing historical HTML, the published [website](../docs/) retains its
original directory structure and URLs. Use the current interactive report for
the latest comparison.
