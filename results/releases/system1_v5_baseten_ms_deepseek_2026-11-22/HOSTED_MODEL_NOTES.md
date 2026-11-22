# New hosted v5 configurations and cost evidence

Morph Reflex uses native Decisions through OpenRouter, pinned to Morph and
provider-declared BF16 with fallback disabled; returned checkpoint is
morph/reflex-20261103. REAX 1.3 uses its native direct SystemOne API, EU tier,
with provider-returned model and version reax-1.3. Provider declarations do not
independently attest hidden model weights. These are separate model routes.

Both use the same frozen 1,456-question v5 bank and answer-blind shuffled order.
Each scored input has exactly one retained first attempt. No scored retries,
warmups, readiness requests or correctness-based answer selection enter scores.
Returned choices are scored even when they differ from the reported probability
argmax. Failed primaries remain unsuccessful; partial stopped screens retain
their own denominators and never become full-bank scores or cutoff labels.

Morph's USD charges are API-reported. REAX's actual API-reported charges are EUR
integer nanos, preserved per request in native_currency_cost_evidence.csv.gz.
Comparison USD is an FX conversion estimate at ECB EUR1 = USD1.1193 dated
November 9, 2026. It is not API-reported USD and may differ from the account's
bank/card settlement. The XML and receipt accompany this release. REAX's main
cost-ledger USD columns stay empty; the explicit fx_conversion_estimate kind
joins to the native-currency sidecar. Its cost summary includes native EUR and
separately labelled estimated USD. Captured advertised USD tariffs are not used
as a substitute for actual EUR charges. Readiness charges are excluded.

Historical v5 configuration summaries and selected primary ledger records are
unchanged. Timings pool individual selected records, including failures. Costs
retain distinctions among reported USD, tariff estimates, free public access,
unknown charges, unmetered local execution, and new EUR-to-USD FX estimates.
The fixed 45% full-bank reporting cutoff remains unchanged. The original v5
selection, AQuA bias and MAIQ rights limitations continue to apply.
