# Hanzo Kai: stopped partial evaluation

The user stopped this evaluation after 244 of the 2,157 v4 questions. Kai answered **46/244 correctly (18.85%)**. On those exact questions, SubQ Snap 1.1 answered **190/244 correctly (77.87%)**. Uniform guessing over the supplied option counts would have yielded about 49 correct answers on average. The questions were selected by an answer-blind seeded shuffle, but the incomplete sample is not stratified.

**This is a partial result, not a 2,157-question score or a determination that Kai would fall below the 62% full-bank cutoff.** It is shown beside the below-cutoff catalogue at the user's request and is excluded from the full-bank statistics, graphs and ranks. The benchmark has known question-selection and source-key limitations described in the main report.

The Hanzo API initially allowed 50 answers before returning a free-plan daily limit. After the user purchased prepaid credits, testing resumed; after 244 valid answers in total, the API reported that an eight-hour usage window was exhausted. The account's reported tier remained Free and the provider indicated a reset at 3:00 a.m. Toronto time on November 2, 2026. The user then directed that testing stop. The top-up purchased credit; this does not establish that the entire purchase was consumed by these requests.

The model catalogue labeled the alias Kai 1.7, while the actual responses identified checkpoint **kai-1.9** and a consistent weights hash and calibration. The API marked **31 of the 244 inputs** as exceeding the model's stated training length; this signal does not by itself establish truncation. Request timing came from sessions with different concurrency, so the partial sample is not a controlled speed comparison.

The original first answers and no-answer errors remain in the private run evidence; no further Kai inference was performed after the user's instruction. Aggregate sample data is in [partial_models.json](partial_models.json).
