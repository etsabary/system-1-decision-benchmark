## New local Liquid models on Apple M2

Liquid d1-2B scored **795/1,342 (59.2%)**, with a **898 ms median** and **1,848 ms p95**. Liquid d1-Omni-2B scored **814/1,342 (60.7%)**, with a **717 ms median** and **1,406 ms p95**. Omni answered 19 more correctly. Both completed every text question with usable decisions and zero reported output tokens.

Both scored 37/40 on ordering by comparisons and 39/43 on following directed connections. d1-2B scored 46/51 on ranking with tie-break rules and 44/50 on fault diagnosis. Omni scored 39/43 on lookup and 48/58 on exceptions and priority rules. Sequential procedures were difficult: 10/48 and 13/48 respectively. Counting exactly true claims scored 27/71 and 28/71; truth-teller consistency 33/74 and 31/74.

The runs used an Apple M2 Mac with 16 GB unified memory, Ollama 0.40.12 and MLX/Metal, BF16, one model and request at a time. Loading and separate probes are excluded. RTX 2060 measurements use a different machine, runtime, precision and date. Hardware and electricity cost are unmeasured for local runs.

On images, d1-2B answered 9/20 with a 4.71 s median; Omni answered 13/20 with a 3.32 s median. Both image screens stopped after 20 because their medians exceeded the two-second limit. These small samples are not 200-question image benchmark scores.

## D3 Ultra adds 18 correct text decisions; Fastino retains the lead

D3 Ultra scored 1,124/1,342 (83.8%), versus the October 20 D3 Turbo run at 1,106 (82.4%). It ranked sixth among the previous 54 complete configurations and fifth among the 30 hosted decision models. Fastino GLiDE retains 1,154 (86.0%), GPT-6 Sol without reasoning 1,143 (85.2%) and Mammoth-1 1,139 (84.9%). Drex Max and Respan Span-02 each retain 1,127. All 52 earlier records kept their original scores, timings, costs and dates.

## D3 gains on causal intervention and object tracking, with weaker procedure execution

D3 Ultra answered 46/46 forward-conditional questions and 52/52 rule-counterexample questions. Causal intervention—working out what follows when a variable is deliberately changed—rose from Turbo’s 38/50 to 45/50. Object swaps rose from 31/52 to 36/52. Sequential procedures fell from 20/48 to 16/48; exact truth counting scored 39/71. The overall gain varies by operation.

## Liquid d1.1 makes its largest gain in exact truth counting

Liquid d1.1 scored 1,044/1,342 (77.8%), 79 more than the older d1 run at 965 (71.9%). Exact truth counting—choosing the number of statements that are true—rose from 23/71 to 47/71, above D3 Ultra’s 39/71. Necessary conditions rose from 35/52 to 50/52. Boolean scope fell from 50/54 to 44/54, and object swaps from 33/52 to 27/52. Sequential procedures scored 10/48. Liquid d1-ultra retains the stronger overall score at 1,084 (80.8%).

## The image results differ from the text gains

On the separate frozen 200-question image bank, D3 Ultra scored 148/200 (74.0%), seven fewer than the earlier Turbo’s 155 (77.5%). Liquid d1.1 scored 144/200 (72.0%), nine more than the older d1’s 135 (67.5%). Amos remains at 159 (79.5%) and Fastino at 158 (79.0%). The new image runs used the exact earlier native-provider PNG/JPEG bytes, question wording, options and order. Both supplied 200 usable answers. See the separate image report for 20-category profiles and timing.

## Both hosted text routes are fast in this measurement

D3 Ultra measured 174 / 148 / 211 ms mean / median / p95, versus Turbo’s 182 / 165 / 298 ms. Liquid d1.1 measured 255 / 212 / 424 ms; older d1’s median / p95 was 206 / 827 ms. Fresh HTTPS requests ran serially within each provider; the two independent providers ran concurrently. All 2,684 new first attempts were usable and reported zero output tokens. No scored retries, shortened questions or tools. Provider hardware, load and dates differ, so these gaps do not isolate architecture.

## D3 free access and Liquid’s reported cost have different meanings

D3 used its free public API; no monetary receipt or permanent production tariff is inferred. Liquid reported $0.00774762 for 1,342 text questions, or $0.00577319 per 1,000. Two admission probes added $0.00000240 separately. OpenRouter was pinned to Liquid and returned liquid/d1.1-20261027 throughout. The D3 request explicitly used vllm-sr/d3-ultra: the live service now aliases its old Turbo name to Ultra. Earlier Turbo measurements retain their October 20 identity and are not relabelled.

## The six newer domains separate different abilities

Both new models scored 24/48 across the six eight-question domains. D3 led in worst-case choices without event probabilities (4/8 versus 2/8) and information-flow security (6/8 versus 4/8); Liquid led in known-risk choices (5/8 versus 4/8), buying information before choosing (4/8 versus 3/8), and possible concurrent histories (5/8 versus 3/8). Strategic choices tied at 4/8. One answer moves a domain score by 12.5 percentage points.

## The deliberately accessible local setup remains visible

All 20 RTX 2060 local configurations retain their published results and purple RTX 2060 6 GB badges. This older GPU was chosen deliberately to measure equipment readers may already have. D3 Flash Artemis remains the local accuracy leader at 995/1,342 (74.1%), with a 408 ms median. H2O-Lightning 4B has a lower 66.5% score and a shorter 259 ms median. Local hardware/electricity cost remains unmeasured; no speed on newer GPUs is projected.

## Scores describe this bank and these execution settings

This is immediate fixed-choice decision making without tools, generated reasoning or agentic iteration. The four selected LLM references preserve their recorded reasoning-off controls and verification limits. Named hosted model identities and native zero-output responses do not attest immutable weights or all internal computation. All earlier failures, partial exclusions, category sizes and the separate author-development diagnostic remain preserved. Blue marks hosted decisions, purple RTX 2060 runs, magenta Apple M2 runs and pale yellow LLM references; cell and speed/cost colors retain fixed scales.
