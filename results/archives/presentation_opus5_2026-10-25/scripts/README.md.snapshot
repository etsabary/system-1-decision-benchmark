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
python3 scripts/validate_repository_layout.py
python3 -m unittest discover -s scripts -p 'test_*.py'
```

The full evidence workflow uses Python 3.10 to match captured floating-point
calculations. The original-evidence workflow also checks its focused suite on
Python 3.12. These checks do not make inference calls or need API credentials.

## Finding the implementation

| Task | Main files |
| --- | --- |
| Current report and category tables | `publish_opus5_reference.py`, `build_readable_report.py` |
| Current report checks | `validate_opus5_release.py` |
| Most recent OpenRouter and Baseten runs | `decision_additions_2026_10_21.py`, `baseten_decisions_2026_10_21.py` |
| Direct-provider runs | `direct_decisions_2026_10_20.py` |
| No-reasoning LLM references | `frontier_reference.py`, `sonnet55_schema_reference.py`, `hyper_reference.py`, `opus5_schema_reference.py` |
| Earlier evidence checks | `validate.py`, the other `validate_*` files and `test_*` files |
| Source-layout migration checks | `repo_layout.py`, `validate_repository_layout.py`, `layout_manifest.json` |

Live runners retain their explicit execution/probe flags and spending controls.
Moving the source does not authorize another paid run. Existing run-resume
software checks remain current-source-only by default.

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
