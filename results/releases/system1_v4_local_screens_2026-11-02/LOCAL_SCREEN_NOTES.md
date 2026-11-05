# Local model screens: incomplete results

Both models were tested sequentially on the same frozen System 1 v4 inputs, in an answer-blind seeded shuffle. The first returned model answer was retained. One non-benchmark readiness call warmed each model; the reported times include the LAN and client overhead. GPU use is local and electricity and hardware cost were not measured. These partial, unstratified screens are not 2,157-question results or 62% cutoff classifications.

## THIS/THAT 1.2

The local `this-that:1.2` deployment used FP16 (source BF16), a CUDA GPU and a 2,048-token input limit. It answered 32 of the first 100 questions correctly, with all 100 responses usable and a 281.88 ms median. SubQ answered 77/100 on those identical inputs; Sage 2 answered 74/100. The screen stopped at 100 because its accuracy was below the requested 50% threshold. Local model digest and source revision are recorded in `partial_models.json`.

## GLiNER2.5-Decide

The local `gliner2.5:decide` deployment used FP32, a CUDA GPU and a 512-token server limit. Among the first 20 attempts, 14 produced usable answers and 4 were correct. Six requests returned HTTP 422 because their full rendered inputs exceeded 512 tokens; their stated lengths were 723, 821, 930, 959, 1,129 and 1,999 tokens. The screen stopped at 20 because 30% of requests were unusable, exceeding the 5% stopping rule. SubQ answered 15/20 and Sage 2 14/20 on the same 20 inputs. Its median was 115.63 ms across the 14 usable answers only; this is not an all-input latency measure.

No rejected input was shortened or retried, and no partial result was put into the full-bank leaderboard. A future run with a different input limit must identify that configuration separately. `partial_models.json` records the local model identifiers, precision, revisions, digests and stopping reasons.
