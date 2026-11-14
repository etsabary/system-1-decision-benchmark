# ASUS native resident 4,096-context partial screens

These are separate 100-question screens on the fixed answer-blind shuffled v5 prefix, with unstratified category counts. They are not 1,456-question scores, full-bank rankings or classifications against the 45% cutoff. All 42 complete configurations, 34 active rankings, six below-cutoff results, two superseded versions, 61,152-record main ledgers, category tables and graphs remain byte-identical to the preceding hosted release. The same 100 inputs were used for each screen. No score was extrapolated to the unattempted 1,356 questions per model.

| Configuration | Correct / screen | Usable | Median | p95 | Wilson 95% upper | Continuation | Cost |
|---|---:|---:|---:|---:|---:|---|---|
| QEV 0.5B · native FP32 text/readout | 19/100 (19.00%, sample only) | 100/100 | 🟩 169.74 ms | 🟨 454.82 ms | 27.78% | Stopped; no full-bank classification | ⬜ Unmetered hardware / electricity |
| QEV 1.3B · native FP32 text/readout | 22/100 (22.00%, sample only) | 100/100 | 🟨 263.78 ms | 🟧 891.50 ms | 31.07% | Stopped; no full-bank classification | ⬜ Unmetered hardware / electricity |
| GS1 0.8B · native PyTorch FP32 eager resident | 27/100 (27.00%, sample only) | 100/100 | 🟥 1111.32 ms | 🟥 1442.01 ms | 36.43% | Stopped; no full-bank classification | ⬜ Unmetered hardware / electricity |

Each screen stopped at the predefined 100-question check because its Wilson 95% upper bound was below 45%. This is a sequential screening heuristic, not a formal repeated-look guarantee or a full-bank inclusion decision. All attempted answers were usable first primaries; there were no scored retries, errors, truncation or runtime-condition changes. All reported output counters were zero, with no generated reasoning text observed and no independent zero-generation attestation. QEV 0.5B reported abstained=true on five responses and QEV 1.3B on two, while returning valid typed choices; those choices are scored normally and the flags remain in the usage ledger. Local hardware and electricity are unmetered, not zero cost. Pooled individual latencies exclude idle pacing and do not measure sustained throughput.

The user confirmed one ASUS RTX 2060 running the publisher’s native PyTorch implementation with 4,096-token context and one resident model at a time. Server replies declared CUDA, reuse and stable runtime profiles. These declarations do not independently attest GPU execution, exact installed weights or source/conversion fidelity. QEV text/readout was declared FP32 with repeated-KV CUDA SDPA; unused vision weights retained BF16 storage. GS1 used its declared FP32 CUDA eager-reference runtime; its replies did not declare a backbone/version checkpoint, so none is inferred. These samples describe the ASUS-served FP32 configurations; the original BF16 runtime was not measured. The compact QEV 0.5B and 1.3B packages legitimately declare parent QEV 0.8B and 2B backbones; parent names are not a precision or installed-weight attestation. This is a separate native single-GPU configuration from earlier distributed GGUF/llama.cpp/RPC measurements.

Initial model loading, synthetic readiness and oversize checks, earlier 2,048-context per-request preflight, pre-score 4,096-context readiness cycles and the unscored monitor diagnostic are excluded. An unscored control test found that GET /props unloaded native weights; monitoring was changed to catalogue-only before any scored primary. Those earlier records remain separately archived. Source rights, frozen cohort-conditioned question selection, AQuA error-selection dependence and the unresolved original MAIQ item-rights caveat remain unchanged; the 120 companion diagnostics retain separate denominators.

- [Screen method, stops and runtime limitations](ASUS_NATIVE_SCREEN_NOTES.md)
- [Separate 100-question screen summaries](asus_native_screen_statistics.json)
- [Server-declared runtime profiles and source hashes](asus_native_screen_profiles.json)
- [Partial-screen individual timing evidence](asus_native_screen_timing.csv.gz)
- [Partial-screen unmetered cost evidence](asus_native_screen_cost.csv.gz)
- [Partial-screen correctness and usability booleans](asus_native_screen_correctness.csv.gz)
- [Partial-screen native usage and record hashes](asus_native_screen_usage.csv.gz)
- [Partial-screen audit and review provenance](asus_native_screen_audit.json)
- [Frozen full-bank parent manifest](parent_hosted_refresh_manifest.json)



Runtime and process fields are server claims. The public usage ledger retains their per-request hashes and declared reuse fields; raw selected choices and gold scoring values remain private.
