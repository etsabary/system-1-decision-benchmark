# Two incomplete local model screens

These sequential GPU screens use the first questions of the same seeded, answer-blind shuffle of the frozen v4 bank. The samples are not stratified, and the runs stopped early under the predetermined reliability or performance rules. They are not full-bank scores or 62% cutoff classifications. SubQ and Sage results below use precisely the same questions, but were collected in different sessions and conditions.

| Model and local precision | Attempts | Usable | Correct | Median usable latency | SubQ / Sage correct on same inputs |
|---|---:|---:|---:|---:|---:|
| Hindsight HS-Decide-1 Flash, FP16 | 100 | 100 | 29 | 273 ms | 77 / 74 |
| Lumma FEV 4B v2, NF4 | 799 | 798 | 452 | 549 ms | 625 / 566 |

Hindsight stopped at the 100-question screen because fewer than half were correct. Lumma stopped at 799 attempts when the predetermined Wilson upper-bound rule was met. One Lumma request was unavailable after a server disconnection; it was retained as an unsuccessful attempt and was not replayed. The remaining 798 usable answers were collected across two sessions using the same recorded model digest and configuration.

All times are client-observed and cover usable answers after warm-up; p95 was 460 ms for Hindsight, 1,262 ms for Lumma. Local compute and electricity costs were not metered. The local adapter's reported confidence differs from its top returned probability on all 100 Hindsight responses, 791 of 798 Lumma responses. The selected option matched the highest returned probability for all usable responses; this observation concerns the local adapter and does not establish upstream model behavior.

The full bank has the question-selection and source-key limitations described in the report. Digests, local precision and audit aggregates are in [partial_models.json](partial_models.json).
