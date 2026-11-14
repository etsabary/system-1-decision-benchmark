# REAX 1.3 and GPT-6.1 Terra on the complete v5 bank

Both figures cover the same 1,456 frozen inputs. REAX scored 1077/1,456
(73.97%); reasoning-disabled Terra scored 1188/1,456
(81.59%). REAX's score difference is -111
answers (-7.62 percentage points).

REAX median latency was 946.36 ms versus Terra's 1160.22 ms;
p95 was 1540.64 ms versus 1728.75 ms. These distributions pool
individual selected primary records, including failures.

REAX's actual API-reported total was EUR 1.0204992.
At the captured ECB November 9 rate of EUR1 = USD1.1193, this is an estimated
USD 1.14224475456. Terra's known API-reported subtotal was
USD 0.75732600, with 2 charges unknown.
The REAX converted estimate is 1.508 times (+50.83%) Terra's
known subtotal. That ratio uses Terra's known subtotal; its complete bill and
an exact full-cost ratio remain unavailable. REAX's converted USD is an estimate,
not API-reported USD or a bank/card settlement amount.

REAX remains a native zero-generation two-model ensemble in the hosted decision
category. Its observed cost and response time are LLM-like in scale in this
comparison with a reasoning-disabled LLM reference. Terra used the OpenAI
standard route through OpenRouter on November 6; REAX used its direct EU route
on November 9. Different providers, dates and execution paths make this a
descriptive recorded comparison, not a controlled production equivalence.
The zero-output-token native protocol does not by itself imply lower cost or
latency than a short-output LLM reference.
