# Colours, ranks and comparison bands

The colours answer different questions; their scales stay fixed across every model and category.

| Encoding | Meaning and rationale |
| --- | --- |
| Teal model names / bars | Hosted native decision models |
| Purple model names / bars | Local CUDA decision configurations |
| Gold model names / pale gold bars | Reasoning-disabled LLM reference configurations |
| Pale yellow → green → dark blue cells | Absolute category accuracy, fixed 0–100%. Each cell also prints correct / tested and percentage. Darker blue means more correct answers. Black or white text follows contrast. A border and ★ mark all tied leaders. |
| Blue → white → red in the relative-profile figure | Below → near → above the score expected after removing model and category averages. Fixed −30 to +30 percentage points. This shows descriptive specialties; it is a different scale from absolute accuracy. |
| Green / yellow / orange / red timing | ≤250 / ≤500 / ≤1,000 / >1,000 ms. Median and p95 are classified separately. |
| Green / yellow / orange / red cost | ≤$0.010 / ≤$0.025 / ≤$0.050 / >$0.050 per 1,000 questions. Uses the unrounded known subtotal / 1,934 × 1,000. |
| ● / ◆ cost marks | API-reported charges / captured tariff estimates. Free-access and local costs are labelled separately. |
| + ? / grey | Additional charges missing / no comparable monetary measurement. A partial cost is a known subtotal, not a complete price. |

These speed and cost bands restore the earlier fixed thresholds. They make slow tails and expensive configurations easy to find; they are descriptive bands, not statistical outlier tests or significance claims. Displayed numbers can round to a boundary. Role colours identify deployment, not quality; only accuracy cells encode correctness. Category leaders share a rank when their counts tie.
