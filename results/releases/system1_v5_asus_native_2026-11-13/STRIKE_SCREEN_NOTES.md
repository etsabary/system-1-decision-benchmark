# Strike 1: incomplete free-tier screen

Strike 1 answered **57 of 100 questions correctly**. All 100 responses were usable. On the same inputs, SubQ Snap 1.1 answered **77/100** correctly and Levanto Sage 2 answered **74/100** correctly. These are paired, answer-blind results on the first 100 questions of a seeded shuffle of the frozen v4 bank; the sample is not stratified. It is a partial screen, not a 2,157-question result or a 62% cutoff classification. The user's instruction was to stop after these 100 questions.

The median client-observed response time was **626.22 ms**, with a **1,423.54 ms p95**. All 100 responses reported a zero EUR charge; they used 105,360 input tokens. Responses were collected sequentially through Strike's direct API. The compared models were tested in different sessions and conditions, so the timings are not a controlled head-to-head measurement.

At the start, the provider's catalogue identified `strike-1` as revision `v20261102`; responses identified `strike-1` without an independently verifiable weights hash. After the screen, a read-only catalogue request returned HTTP 402 and `payment_required` with a no-credits message. This observation does not establish whether the advertised free allowance will reset. No extra model answers were requested after the screen.

The full bank has known question-selection and source-key limitations described in the main report. Aggregate screen information is in [partial_models.json](partial_models.json).
