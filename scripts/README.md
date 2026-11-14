# Current presentation build

The v4 Kai-note successor places the user's stopped, incomplete Hanzo sample beside the below-cutoff catalogue and documents its usage limits, without changing the full-bank results or graphs. Validate that presentation-only successor with:

```sh
python3 scripts/validate_system1_v4_kai_note.py results/releases/system1_v4_kai_note_2026-11-02 results/releases/system1_v4_hosted_2026-11-02
```

The v4 hosted-model successor adds completed SubQ and meraGPT runs without changing the frozen v4 bank or earlier model evidence. Its companion validator checks that every earlier result, category score, timing and cost record is preserved:

```sh
python3 scripts/validate_system1_v4_hosted.py results/releases/system1_v4_hosted_2026-11-02 results/releases/system1_v4_2026-11-02
```

The v4 release retains the v3 selected records and adds 140 quantitative items. Its offline validators check the question bank, unchanged v3 evidence, category and overall statistics, timing and cost ledgers, and the readable colour-coded presentation:

```sh
python3 scripts/validate_system1_v4.py results/releases/system1_v4_2026-11-02 results/releases/system1_v3_presentation_2026-11-01
python3 scripts/validate_system1_v4_presentation.py results/releases/system1_v4_2026-11-02
```

`publish_system1_v4.py` renders a new presentation into an empty `--output` directory from a complete `--source` release; it does not run inference.

`publish_system1_v2_presentation.py` restores annotated category matrices, coloured individual ranks and reconciled cost evidence without changing frozen measurements. `validate_system1_v2_presentation.py` checks the ledger joins, totals, colours, ranks, privacy and immutable inputs. Use `--output` to rebuild offline in a new directory. The initial v2 builder below reproduces its original dated presentation.

# Benchmark scripts

## Current v2 publication

`publish_system1_v2.py` rebuilds the 26-model,1,934-question public report offline from sanitized captures. `validate_system1_v2.py` checks exact inputs,73,492 timing records, aggregate/category totals,62% selection, privacy, links and seals. `test_system1_v2.py` checks cutoff boundaries and exclusions. `system1_v2_history.py` resolves pre-v2 presentation snapshots for old validators. No inference or credentials are required.

```sh
python3 scripts/validate_system1_v2.py
python3 -m unittest discover -s scripts -p "test_system1_v2.py"
python3 scripts/publish_system1_v2.py --output /tmp/system1-v2-rebuild
```

## Historical scripts and releases

# Benchmark scripts

All 110 Python files previously in the repository root are grouped here: live
benchmark runners, analysis and plotting tools, report builders, validators and
their tests. Documents are in `documents/`; dated outputs and evidence are in
`results/`. The published website stays in `docs/`, at the same public URLs.
No benchmark measurements changed in this cleanup.

Run commands from the repository root. For an earlier command such as
`python3 validate.py`, use `python3 scripts/validate.py` instead. Imports between
these scripts remain local to this folder.

## Offline checks

Install the report dependencies in your preferred virtual environment:

```sh
python3 -m pip install -r scripts/requirements-reports.txt python-dotenv
python3 scripts/validate_october21_release.py
python3 scripts/validate_opus5_release.py
python3 scripts/validate_local_additions_2026_10_25.py
python3 scripts/validate_repository_layout.py
python3 -m unittest discover -s scripts -p 'test_*.py'
```

The full evidence workflow uses Python 3.10 to match captured floating-point
calculations. The original-evidence workflow also checks its focused suite on
Python 3.12. These checks do not make inference calls or need API credentials.

## Finding the implementation

| Task | Main files |
| --- | --- |
| Current report and category tables | `publish_local_updates_2026_10_31.py`, shared `publish_october29_decisions.py` and `build_readable_report.py` |
| Current report checks | `validate_local_updates_2026_10_31.py`, `test_local_updates_2026_10_31.py` |
| Local GPU evidence and model profiles | `publish_local_additions_2026_10_25.py` (`--capture` is owner-only, offline private-key reconciliation) |
| Most recent OpenRouter and Baseten runs | `decision_additions_2026_10_21.py`, `baseten_decisions_2026_10_21.py` |
| Direct-provider runs | `direct_decisions_2026_10_20.py` |
| No-reasoning LLM references | `frontier_reference.py`, `sonnet55_schema_reference.py`, `hyper_reference.py`, `opus5_schema_reference.py` |
| Earlier evidence checks | `validate.py`, the other `validate_*` files and `test_*` files |
| Source-layout migration checks | `repo_layout.py`, `validate_repository_layout.py`, `layout_manifest.json` |

Live runners retain their explicit execution/probe flags and spending controls.
Moving the source does not authorize another paid run. Existing run-resume
software checks remain current-source-only by default.

The latest October 25 release adds two local configurations (Nemotron and
KnowLine) and hosted Celeris 1.1 to the previous 49 routes, for 52 complete
routes and 20 local configurations. `native_additions_evidence.py` reconciles
sealed owner evidence offline; it does not run inference. `publish_native_additions_2026_10_25.py`
builds the presentation, and `validate_native_additions_2026_10_25.py` checks
coverage, timing, cost estimates and all 1,612 category cells. The historical
49-route validator resolves the exact archived presentation with
`native_additions_publication_history.py`.

Earlier model records and timing rows remain exact. Accuracy is bound to the
owner's private key and is not independently reproducible from public aggregates.
Private endpoint addresses and raw choices are not exported. Rebuilding an
unsealed local presentation from its sanitized capture uses
`python3 scripts/publish_native_additions_2026_10_25.py --refresh-unpublished`.

## Historical source provenance

[`legacy_layout/`](legacy_layout/) contains exact `.snapshot` copies of the
previous root-level sources and superseded README/workflow entry points, from
commit `495d01d929dc42e238fdcc7dc699e009f9f952e5`. They are evidence, not active
scripts. Earlier dated release manifests retain their original paths and hashes;
offline checks resolve those paths to the matching preserved bytes.

`layout_manifest.json` separately binds the active relocated sources and the
unchanged published artifacts. This distinguishes a source reorganization from
a new experiment and detects changes to either current code or archived evidence.

The high-level folder map is recorded in the same manifest. `repo_file()` resolves
the original logical evidence names to their current physical locations;
`logical_relative()` retains those names when validating dated checksums. These
helpers do not weaken live-run software checks or rewrite sealed evidence.

[Repository overview](../README.md) · [Results index](../results/README.md)

## October 27 additions

`publish_native_updates_2026_10_27.py` publishes the two audited hosted additions offline. `validate_native_updates_2026_10_27.py` verifies 54 routes,2684 new timing rows,1674 category cells and exact preservation of 52 prior records. `october27_history.py` resolves the prior active presentation for historical checks.

## October 31 main-report selection

`publish_local_updates_2026_10_31.py` adds five complete local runs and three
stopped screens. `statistics.json` contains the 56 configurations with at least
50% overall; `all_statistics.json` retains all 66 complete records. Every main
figure, category table and category leader uses the same qualifying set. The
separate below-50% catalogue retains older banks, formats and screen sizes.

`--capture --capture-only` is an owner-only offline reconciliation, not inference.
A normal build uses the captured public aggregates. The earlier 61-configuration
active presentation is preserved with exact hashes under the October 31 archive;
its validator still checks the original counts and values.

```sh
python3 scripts/publish_local_updates_2026_10_31.py
python3 scripts/validate_local_updates_2026_10_31.py
python3 -m unittest discover -s scripts -p 'test_local_updates_2026_10_31.py'
```

## Provisional v5 · November 9, 2026

`publish_system1_v5_provisional_2026_11_09.py` renders the separately audited
1,456-question subset without inference. The exact inclusion cutoff is 45%,
requiring at least 656 correct answers. `validate_system1_v5_provisional_2026_11_09.py`
checks the retained inputs, 701 removed IDs, all 32 configurations, individual
timing/cost evidence, source rights, graph membership and provisional selection
provenance against the frozen v4 release. Original v4 scores and the 62% cutoff
remain historical; v5 has its own denominator and threshold.

```sh
python3 scripts/validate_system1_v5_provisional_2026_11_09.py results/releases/system1_v5_provisional_2026-11-09 results/releases/system1_v4_openai_2026-11-06
```

## Provisional v5 hosted additions · November 9, 2026

`publish_system1_v5_hosted_2026_11_09.py` adds the two audited hosted runs to
the frozen 1,456-input bank. The validator preserves all prior 32 summaries and
their exact individual evidence rows, verifies both new runs, and keeps native
EUR receipts separate from USD currency-conversion estimates. The initial v5
and all earlier dated releases remain immutable.

```sh
python3 scripts/validate_system1_v5_hosted_2026_11_09.py results/releases/system1_v5_hosted_2026-11-09 results/releases/system1_v5_provisional_2026-11-09
```

## Drex Max v1.1 successor · November 9, 2026

`publish_system1_v5_drex_2026_11_09.py` renders the independently audited native
Nace update. The active graph can supersede older Drex Max only after an
explicit replacement decision; its original measurements stay archival, separate
from models below the cutoff. The validator preserves the prior 34 results,
checks new usage-based cost estimates and native counters, and verifies all
transport phases and the unchanged 1,456-question bank.

```sh
python3 scripts/validate_system1_v5_drex_2026_11_09.py results/releases/system1_v5_drex_2026-11-09 results/releases/system1_v5_hosted_2026-11-09
```

Dated-release commands intentionally omit an active-mirror argument so they
continue to work after later publications. The v5 CI workflow additionally
checks `--mirror docs/v5` for its current successor only.

## SingVL distributed-local successor · November 11, 2026

`publish_system1_v5_singvl_2026_11_11.py` retains the existing layout and adds a
rose deployment color for SingVL on two user-reported RTX2060 6GB computers.
The role extension is local to the new renderer; historical renderer sources
and dated releases remain unchanged. Cost and speed bands keep their original
meaning, and all 35 previous model/cost objects and 50,960 ledger prefixes are preserved.

```sh
python3 scripts/validate_system1_v5_singvl_2026_11_11.py results/releases/system1_v5_singvl_2026-11-11 results/releases/system1_v5_drex_2026-11-09
```

The current CI also checks the exact docs/v5 mirror. Hardware metadata is
user-reported; the serving API does not independently attest actual GPU placement.

## D3 Flash distributed-local successor · November 11, 2026

`publish_system1_v5_d3_flash_2026_11_11.py` reuses the current layout and rose
deployment color for the separately tested D3 Flash9B Q4_K_M configuration.
All 36 previous model/cost objects and 52,416 ledger prefixes remain unchanged.
The frozen bank stays 1,456 questions / 43 categories with an exact 45% cutoff.
The collection record retains one timeout and two pacing phases, with cause
unconfirmed. Local hardware and electricity are unmetered, not zero.

```sh
python3 scripts/validate_system1_v5_d3_flash_2026_11_11.py results/releases/system1_v5_d3_flash_2026-11-11 results/releases/system1_v5_singvl_2026-11-11
```

CI also validates the exact docs/v5 mirror. Historical renderers and releases
are unchanged; the latest report retains readable matrices and cost/speed bands.

## Native Gemini Decision 1 successor · November 13, 2026

`publish_system1_v5_gemini_decision1_2026_11_13.py` renders the audited native
Google AI Studio configuration served through OpenRouter. It adds 1,456 first
primaries while preserving all 37 preceding model/cost objects and 53,872-row
ledger prefixes. The new ledgers contain 55,328 records each. The frozen bank
stays 1,456 questions / 43 categories with an exact 45% inclusion cutoff.
Precision is unknown. API-reported USD 0.0797482 excludes readiness; output
counters are zero without independent generation-implementation attestation.

```sh
python3 scripts/validate_system1_v5_gemini_decision1_2026_11_13.py results/releases/system1_v5_gemini_decision1_2026-11-13 results/releases/system1_v5_d3_flash_2026-11-11 --mirror docs/v5
```

CI checks the exact current mirror. Older dated releases and their bound
scripts stay unchanged; the current report updates all cohort ranks and
retains readable matrices, complete costs and fixed speed/cost bands.

## Four-model native hosted successor · November 13, 2026

`publish_system1_v5_hosted_refresh_2026_11_13.py` renders native Perplexity
Decider v1.3 and Flash v1.3 plus HeyGen Decision 1 and Turbo preview. It preserves
all 38 prior model/cost objects and 55,328-row ledger prefixes, appending 5,824
first primaries. All three main ledgers contain 61,152 records. The fixed bank
stays 1,456 questions / 43 categories with the exact 45% cutoff (656 correct).
There are 42 complete configurations, 34 active, six below cutoff, two
superseded. Perplexity v1.3 replaces v1.2 under the standing current-version
policy; older evidence remains unchanged, separate from the below-cutoff list.

Perplexity estimates cover all primaries, with actual API monetary charges
unreported; the native output-accounting token per question is retained.
HeyGen costs are API-reported; Turbo is a preview native decision model.
Precision and generation implementation are not independently attested.
Readiness remains excluded; timing pools individual primaries, not phase
medians or sustained dispatch throughput.

```sh
python3 scripts/validate_system1_v5_hosted_refresh_2026_11_13.py results/releases/system1_v5_hosted_refresh_2026-11-13 results/releases/system1_v5_gemini_decision1_2026-11-13 --mirror docs/v5
```

The validator checks exact preserved objects/prefixes, unique complete item
sets, correctness and usability, joined usage/source hashes, native counters,
Decimal cost subtotals and absent actual-charge telemetry, pooled timings,
category denominators, replacement, ranks, colours, links, privacy and mirror.
Earlier dated releases and their bound scripts remain immutable.

## ASUS native partial-screen presentation · November 13, 2026

`publish_system1_v5_asus_native_2026_11_13.py` copies the frozen hosted-refresh
release without rerendering any graph or changing any full-bank data. It adds
three separate 100-question local screens (QEV 0.5B, QEV 1.3B and GS1 0.8B)
with 300 rows per partial timing/cost/correctness/usage ledger and their declared
resident native FP32 runtime profiles. All 42 full results, 34 active ranks,
61,152-row main ledgers, cost objects, category views, graphs and historical
partial files remain byte-identical. There are no new full-bank configurations.

The fixed shuffled prefix is unstratified. Wilson upper bounds implement a
screening heuristic, not a formal repeated-look guarantee or full-bank cutoff
classification. Local hardware/electricity is unmetered. Typed choices remain
scored when a server also flags abstention (five QEV 0.5B and two QEV 1.3B
responses); raw flags and zero output counters are retained. Server GPU,
precision, reuse and source declarations are not independent attestation.

```sh
python3 scripts/validate_system1_v5_asus_native_2026_11_13.py results/releases/system1_v5_asus_native_2026-11-13 results/releases/system1_v5_hosted_refresh_2026-11-13 --mirror docs/v5
```

The validator checks exact full-parent files and recovered parent HTML,
separate denominators and null full scores/ranks/classifications, complete
unique fixed-prefix item joins, correctness, pooled timing, unmetered costs,
source/profile/review hashes, usage, abstention flags, links and privacy.
