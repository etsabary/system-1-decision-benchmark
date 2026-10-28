# Image input: October 23 update

Fastino GLiDE completed 200 native-image decisions: 158 correct (79.0%), 359 ms median. The catalog image flag was false; documented image parts and successful single/multiple-image probes established actual acceptance, followed by the unchanged full bank. The [visual report](https://etsabary.github.io/visual-decision-benchmark/report.html) ranks it second, not first.

The text cohort now has 27 specialized decision models. Capability declarations and measured vision results remain distinct.

## Previous dated reviews

# Image input: October 21 additions

Mammoth-1 and Elephant-1 are text-only on the tested Baseten/OpenRouter catalog routes. Drex Max documents text and image input through its [direct Nace API](https://console.nace.ai/docs/drex/guides/drex-max); its tested OpenRouter route currently advertises text only. No new image inference was performed in this update.

These additions bring the specialized text cohort to 26 models, 17 with declared image input on at least one documented route. Declared support does not establish a measured image score. The [separate visual benchmark](https://github.com/etsabary/visual-decision-benchmark) remains a separate comparison.

## Previous dated capability review

# Image input among the text-benchmarked models

Documentation review: October 20, 2026. **16 of 23 specialized decision models declare image input.** This is a capability review, not a new image benchmark. No image inference was performed for this review.

| Model | Type | Image input | Evidence |
| --- | --- | --- | --- |
| Respan Span-02 | Decision model | Yes — documented | [Source](https://openrouter.ai/api/v1/models/respan/span-02/endpoints) |
| Perplexity Decider v1.2 | Decision model | Yes — documented | [Source](https://openrouter.ai/api/v1/models/perplexity/pplx-decider-v1.2/endpoints) |
| Nimble v4 Max | Decision model | No — current documented route | [Source](https://docs.bespokelabs.ai/api-reference/openapi.yaml) |
| d3-turbo | Decision model | Yes — documented | [Source](https://decision.vllm-sr.ai/api/info) |
| Liquid d1-ultra | Decision model | Yes — documented | [Source](https://openrouter.ai/api/v1/models/liquid/d1-ultra/endpoints) |
| Amos 1 Large | Decision model | Yes — documented | [Source](https://huggingface.co/mukaddamzaid/amos-1-large/raw/main/README.md) |
| kettei-fat | Decision model | Yes — documented | [Source](https://docs.sqwish.ai/guides/models-and-fallback.md) |
| Jev 1.14 | Decision model | Yes — documented | [Source](https://openrouter.ai/api/v1/models/typesafe/jev-1.14/endpoints) |
| Jev 1.13 | Decision model | Yes — documented | [Source](https://openrouter.ai/api/v1/models/typesafe/jev-1.13/endpoints) |
| Mercury Decide | Decision model | Yes — documented | [Source](https://openrouter.ai/api/v1/models/inception/mercury-decide/endpoints) |
| Liquid d1 | Decision model | Yes — documented | [Source](https://openrouter.ai/api/v1/models/liquid/d1/endpoints) |
| Cloudflare Clef | Decision model | Yes — documented | [Source](https://openrouter.ai/api/v1/models/cloudflare/clef/endpoints) |
| Perplexity Decider Flash v1.2 | Decision model | Yes — documented | [Source](https://openrouter.ai/api/v1/models/perplexity/pplx-decider-flash-v1.2/endpoints) |
| Microsoft-Decision-1 | Decision model | No — current documented route | [Source](https://openrouter.ai/api/v1/models/microsoft/microsoft-decision-1/endpoints) |
| Drex v2.0 | Decision model | No — current documented route | [Source](https://openrouter.ai/api/v1/models/nace-ai/drex-v2.0/endpoints) |
| Cloudflare Clef Flash | Decision model | Yes — documented | [Source](https://openrouter.ai/api/v1/models/cloudflare/clef-flash/endpoints) |
| Cloudflare Clef Omni | Decision model | Yes — documented | [Source](https://openrouter.ai/api/v1/models/cloudflare/clef-omni/endpoints) |
| Drex v1.5 | Decision model | No — current documented route | [Source](https://openrouter.ai/api/v1/models/nace-ai/drex-v1.5/endpoints) |
| Kev 4B | Decision model | No — current documented route | [Source](https://openrouter.ai/api/v1/models/jaredpalmer/kev-4b/endpoints) |
| Luna 6 Decisions | Decision model | Yes — documented | [Source](https://openrouter.ai/api/v1/models/openai/gpt-6-luna-decisions/endpoints) |
| Tev1 4B experimental (OpenRouter native adapter) | Decision model | No — current documented route | [Source](https://openrouter.ai/api/v1/models/togethercomputer/tev1-4b-experimental/endpoints) |
| ScaleDown Classify-1 | Decision model | Yes — documented | [Source](https://openrouter.ai/api/v1/models/scaledown/classify-1/endpoints) |
| Solar Decide Flash | Decision model | No — current documented route | [Source](https://openrouter.ai/api/v1/models/upstage/solar-decide-flash/endpoints) |
| GPT-6 Sol — no reasoning | LLM reference | Yes — documented | [Source](https://openrouter.ai/api/v1/models/openai/gpt-6-sol/endpoints) |
| Sonnet 5.5 — no thinking, JSON-choice | LLM reference | Yes — documented | [Source](https://openrouter.ai/api/v1/models/anthropic/claude-sonnet-5.5/endpoints) |
| Qwen3.8-Max — none, Hyper Charm | LLM reference | Yes — documented | [Source](https://hyper.charm.land/v1/models) |

The existing [200-question image benchmark](https://github.com/etsabary/visual-decision-benchmark) covers Jev 1.14, Luna Decisions and its separately labelled regular-LLM references. The other decision models above have not been assigned image scores here. Jev 1.13 is declared image-capable but was not part of that image comparison.

The ordinary LLM references (Sol, Sonnet and Qwen) also accept images; their rows here remain text-only scores. [Official OpenAI model documentation](https://developers.openai.com/api/docs/models/gpt-6-sol) confirms Sol image input. Hyper Charm explicitly declares vision for the exact Qwen model used.

Native support means actual image decoding, not OCR or a caption substituted into a text prompt. Nimble’s documented JSON state is read as text; sending an image-shaped JSON object and receiving HTTP 200 does not establish vision. Sqwish fat reads images; its core size is a different, text-only model. Image encoding and availability can depend on the route. No text score, text latency or text cost is repurposed as an image result.

The dated [machine-readable review](../results/releases/direct_additions_2026-10-20/image_capabilities.json) records source URLs and response hashes. [Current text benchmark](../README.md).
