# SingVL: two-computer local inference

SingVL S1 4B Q4_K_M completed the frozen v5 bank with 698/1,456 correct (47.94%), all 1,456 usable, median 344.23 ms and p95 1,163.74 ms. It meets the exact 45% cutoff and adds a 29th active configuration. All 35 previous configurations remain unchanged.

Rose model names and bars mark this distributed local deployment. The user reports an ASUS TUF with an AMD Ryzen 7 and a Lenovo Legion with an Intel Core i7, each with one RTX 2060 and 6 GB VRAM. The ASUS is the main host; the Lenovo is the worker. llama.cpp CUDA/RPC connects them over the LAN. Each GPU retains its own memory; tensors are distributed between devices. Nominal total VRAM is 12 GB across two computers. Exact CPU SKUs, network throughput, GPU utilization and actual layer placement were not independently captured by this API. The hardware description is user-reported.

This differs from the purple single-computer local configurations and teal hosted native services. Numerical speed/cost background colors keep their existing meaning. The measured 344 ms median includes network and adapter overhead; it does not isolate GPU compute. Hardware and electricity cost are unmetered, not zero.

The backend declares SingVL S1 4B GGUF Q4_K_M, llama.cpp b12301-956591f45 and a 4,096-token context. The native adapter accepts 4,096 input tokens. A 1,597-token synthetic question succeeded; a 4,257-token request was rejected rather than truncated. No client truncation, scored retries or answer replacement occurred. The older 1,024-context 20-question screen is preserved privately and excluded from this result. The user explicitly requested full completion regardless of accuracy.

All responses returned typed choices and valid probability distributions and reported zero output tokens; no generated reasoning text was observed. The original full-precision Transformers runtime, conversion correctness, hidden weight identity and zero-generation internals were not independently attested. This result applies to the recorded quantized compatibility runtime.

The new score exceeds StartLux Instant 4B Q8 by 20 correct answers (1.37 percentage points). It ranks 25th among the 28 previously published active configurations plus this candidate. Necessary conditions 26/32 and forward conditionals 17/22 are relative strengths. Robust decisions without a prior 3/39 and value of information 10/40 are weaknesses. Small category scores are descriptive; no single category establishes general superiority. Full category measurements and cross-model comparisons remain downloadable.

Against StartLux, quantitative reasoning is 93/200 versus 75/200, scheduling 27/54 versus 17/54, and conversational intention 24/33 versus 14/33. StartLux leads routing 19/31 versus 8/31 and value of information 20/40 versus 10/40. The overall 20-answer gap combines offsetting category differences.
