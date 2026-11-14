# D3 Flash9B: two-computer local result

D3 Flash9B Q4_K_M scored **704/1,456 (48.35%)**, with 1,455 usable responses, median 576.68 ms and p95 6,616.03 ms. It meets the fixed 45% cutoff and ranks 25th among 30 active configurations. All 36 previous complete measurements are preserved. Rose names/bars identify the same distributed-local deployment class as SingVL; numerical speed/cost bands keep their usual meaning.

The result adds 6 correct answers (0.41 percentage points) over SingVL, at 1.68 times its median latency. It adds 26 over StartLux Instant 4B Q8. Routing 19/31 versus SingVL 8/31 and temporal intervals 17/25 versus 9/25 are relative gains; conversational intention 14/33 versus 24/33 and quantitative reasoning 84/200 versus 93/200 are weaker. All 43 category results and matched comparisons are downloadable.

The older Artemis IQ3_M configuration remains archival below the cutoff, with 631 correct / 1,292 usable. Among 1,292 commonly usable inputs new D3 got 641 versus 631, plus 63 correct where old responses were unusable. These are different serving/precision configurations; checkpoint equivalence is unestablished and the gain does not isolate quantization.

## Configuration and hardware

The server declares native d3-flash, 8,953,803,264 parameters, GGUF Q4_K_M, 6,592,055,296 model bytes, 4,096 context and llama.cpp b12301-956591f45. A separate 1,635-token synthetic readiness succeeded; 4,295 tokens were explicitly rejected because they exceeded physical batch 4,096. No client truncation occurred.

Hardware is user-reported: ASUS TUF Ryzen 7 and Lenovo Legion Intel Core i7, each RTX 2060 with 6 GB VRAM, using llama.cpp CUDA/RPC over Ethernet. Nominal total VRAM is 12 GB across separate devices. Exact CPU SKUs, actual GPU placement, hidden weight identity and conversion fidelity were not independently attested. Hardware/electricity costs are unmetered, not zero.

## Collection record

Attempt 744, EXT-F31-018, received no HTTP response within 30 seconds. It remains an unsuccessful primary in the score/timing denominator. The cause is unconfirmed; this record does not establish a model-specific cause. Only unattempted inputs 745–1,456 resumed after same-configuration health/identity and synthetic readiness checks. Those 712 responses were all usable and used 1.6 seconds minimum between request starts. All 744 original records remain unchanged. No scored input was replayed or replaced.

Request latency includes the slow responses and retained timeout. Overall median/p95 are pooled from all 1,456 individual selected primaries, not averages of phase percentiles. Client idle gaps are excluded, so latency is not sustained throughput. Initial 744 median/p95: 568.88/6,684.11 ms; paced 712: 590.22/6,233.39 ms. Phase metadata preserves these operating conditions without attributing an unconfirmed cause.

All 1,455 usable responses report 0 output tokens with no generated reasoning text observed; the timeout has no usage telemetry. This does not independently attest forward-pass implementation. Twenty-five configuration snapshots and final health matched. Independent raw scoring, all 43 categories, source/raw/record/phase hashes, the original 744 digest and observed minimum 1.600638-second continuation spacing passed. The frozen bank and third-party rights are unchanged. Later catalogue-router switching checks were unscored and outside this bank run.
