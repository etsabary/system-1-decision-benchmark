# Historical initial v5 selection notes only

The original body below describes the initial 32-configuration, 26-model provisional v5 recalculation and its reuse-only inference scope. This SingVL successor has 36 complete configurations and 29 active graph models. It preserves all earlier sessions and adds a separately audited two-computer local SingVL test. The 1,456-question bank, original removal cohort and 45% cutoff are unchanged. See [DREX_VERSION_NOTES.md](DREX_VERSION_NOTES.md), [prior hosted-session notes](HOSTED_MODEL_NOTES.md) and [current results](statistics.json) for the applicable versions and scopes. The original selection-note body follows as historical provenance.

---

# Provisional v5 selection and interpretation

This result removes 701 questions correctly answered by every configuration in
the previous 26-model main graph, leaving 1,456 questions across 43 categories.
All 32 complete v4 configurations are recomputed from their recorded selected
primaries. There are no new model requests. Historical incomplete screens retain
their original v4 denominators and do not become v5 scores.

The user-set inclusion threshold is exactly 45%. Apply the integer test
correct * 100 >= 45 * 1,456, which requires at least 656 correct answers. The
same 26 configurations qualify; six remain in the separate catalogue. Super
Decider remains the lowest previous main-graph configuration at 669/1,456
(45.9478021978022%); this observation does not define the cutoff. This is a new
reporting policy, replacing the 62% v4 cutoff only for this provisional subset.

The selection is conditional on this cohort and its single recorded responses.
“Universally correct” does not establish triviality, repeatability, or saturation
for other models. Removing identical correct answers cannot change the old
26-model rank order; its percentage-point gaps scale by 2,157/1,456. Category
weights and coverage change unevenly. This is a post-hoc challenge subset, not
an independent fresh test or a demonstration of improved model performance.

Timings pool individual retained records, including failures. Costs filter the
same selected records and distinguish API-reported amounts, captured tariff
estimates, free public access, unknown charges, and unmetered local execution.
Known subtotals are not complete bills when charges are missing. Original blank
historical public source-hash fields remain blank; the private audit binds those
records through frozen normalization-file digests and their raw-record hashes.
No answer choices, gold keys or absolute private paths are included here.

MAIQ rights limitations and AQuA error-selected item bias remain in force; see
SOURCE_AND_LICENSES.md and the retained per-question source metadata.
