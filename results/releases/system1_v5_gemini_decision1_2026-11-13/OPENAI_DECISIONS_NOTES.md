# OpenAI update and benchmark scope · November 6, 2026

The [official Decisions guide](https://developers.openai.com/api/docs/guides/decisions) now documents general availability, prompt caching, JSON input, question-specific images, hosted images and up to 400 questions per request. Those are API feature changes; they do not establish improved model weights. GPT-6 Luna is still its only supported model. The native OpenRouter catalogue and live readiness response both identified `openai/gpt-6-luna-decisions-20261006`, matching the earlier test.

A direct request to OpenAI’s `/v1/decisions` was rejected with HTTP 401 by the stored credential. The prior native OpenRouter Decisions route remained accessible and was used, pinned to OpenAI with no provider fallback. This is typed Decisions inference, not chat generation.

## Luna Decisions · partial expansion

**GPT-6 Luna Decisions — incomplete expansion test:** 82/181 (45.30%) on new inputs only, 180 usable; stopped below 50%. Median 283 ms, p95 546 ms. New-run reported cost $0.0126638 plus one unknown charge. Terra scored 159/181 on the exact same inputs. The unchanged 1,342 baseline remains 758 correct (56.48%); this partial expansion is not a full-v4 score or ranked 62% classification. [API changes, scope and costs](OPENAI_DECISIONS_NOTES.md).

The historical 1,342 primaries were checked against the exact current request payload hashes and retained, including their 42 unsuccessful requests. Only the 815 added inputs were eligible for new inference. The new shuffle seed was fixed before responses. The stop was set after 180 new primaries; one already-running request settled, producing 181 total. One new HTTP 502 reported a provider refusal and is retained. There were no scored retries. Costs above cover the new partial session only; historical charges were not rebilled or included in that new subtotal. A missing charge is not assigned zero. The separate unscored native readiness request cost $0.000012 and is outside the benchmark counts and subtotal. This partial sample is not the full 815 additions or the 2,157-question v4 bank, and category coverage is unstratified.

## GPT-6.1 Terra · full-bank reference

GPT-6.1 Terra was run with reasoning disabled on all 2,157 inputs. All 2,155 successful responses reported zero reasoning tokens and no reasoning text. Its API-reported charges total $0.98025050; 2 client DNS failures have no charge telemetry. Those unsuccessful primaries remain in the denominator and timing distribution; they were never retried or replaced. Only the unattempted inputs resumed after connectivity recovered. The checkpoint is October 26, 2026, using OpenAI standard service through OpenRouter. Existing GPT-6 Sol results remain unchanged.

GPT-6.1 Terra is a regular LLM reference using the same one-option generation contract as the earlier Sol reference. It supports reasoning `none`; GPT-6.1 Sol does not. The [official model guide](https://developers.openai.com/api/docs/guides/latest-model) distinguishes these modes. Terra uses two concurrent requests and fresh HTTPS connections; timing includes connection and full-response overhead. The pooled median and p95 are recomputed from individual selected primaries.

All prior complete-model measurements, frozen v4 questions, source rights and selection limitations remain unchanged. Historical dated releases remain available.
