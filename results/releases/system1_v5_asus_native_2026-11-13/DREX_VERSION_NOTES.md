# Drex Max v1.1: versioned native route and active comparison

The complete frozen v5 bank has 1,456 inputs. Native Nace Drex Max v1.1 scored
996/1,456 (68.41%) with 1454 usable first attempts. The historical
DeepInfra October 16 Drex Max measurement remains 952/1,456
(65.38%) with 1447 usable responses. The paired table has
141 new-only correct and 97 old-only correct answers;
the net difference is +44 answers
(+3.02 percentage points).

New median/p95 are 344.59/490.10 ms, versus historical
330.62/1324.09 ms. The new route has a captured
tariff estimate of USD 0.02355297, based on reported input usage at USD0.03/M.
It is not an API-reported bill. 2 no-usage primary costs remain
unknown; all 1,456 actual API charges lack monetary telemetry. The old known
API-reported subtotal is USD 0.04695126 plus nine unknown charges.
The new estimated subtotal divided by that old known subtotal is
0.502; this does not establish actual billing savings.

Replacement decision: supersede_old_active_configuration. All 34 previous configuration
objects and their selected response records remain unchanged. If superseded,
the old Drex Max is listed separately as a superseded reference; it is not
classified as below the 45% cutoff. The exact bank and cutoff remain unchanged.

The catalogue declares an October 28 release for drex-max-v1.1 and a native Nace
route, while the older measurement used the October 16 checkpoint on DeepInfra.
These are distinct captured configurations. Hidden weight identity is not
independently attested.

Native output-token counters are nonzero in 1454 responses and sum
to 238612. The existing Drex native-choice policy accepts these
typed decisions and preserves their raw counters. No generated reasoning text
was observed; zero generation is not independently attested and is not claimed.
The current official answer guide describes output_tokens as what the model
produced and says those tokens are not billed. Only input tokens enter the
captured tariff estimate. See drex_counter_policy.json for source URLs and
capture hashes.

Two HTTP429 no-answer responses were preserved as failed primaries. Only
unattempted inputs resumed after the provider's Retry-After window, with an
explicit sequential pacing amendment. There were no scored retries or
correctness-based replacements. Pacing waits are outside per-request latency;
the changed concurrency/rate means pooled response time is descriptive and
does not establish uniform-throughput performance. Readiness was unscored and
its estimated cost is excluded.

Phase 1 covered sequences 1–322 with two workers. Sequences 323–582 and
583–1,456 used one worker with a 0.65-second global start interval, within the
published free 120 RPM limit. A billing_check pause occurred after sequence 582;
only unattempted inputs resumed at 583. The complete wall-clock span was
1377.78 seconds, including cooldown, deliberate
pacing and the billing_check/human pause. This is not model-only throughput.
See drex_transport_phases.json for boundaries and receipt hashes.
