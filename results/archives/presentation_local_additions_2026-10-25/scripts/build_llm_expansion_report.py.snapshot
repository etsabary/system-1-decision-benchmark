"""Build the current overall analysis from the sealed forty-model aggregate."""
from repo_layout import repo_file
import json
from pathlib import Path

from build_october18_report import speed_band, cost_band

ROOT = Path(__file__).resolve().parents[1]
SOURCE = repo_file('overall_llm_expanded_2026-10-18', root=ROOT)


def table(header, rows):
    return '\n'.join(['| ' + ' | '.join(header) + ' |',
                      '| ' + ' | '.join(['---'] * len(header)) + ' |'] +
                     ['| ' + ' | '.join(map(str, row)) + ' |' for row in rows])


def main():
    s = json.loads((SOURCE / 'summary.json').read_text())
    assert s['model_count'] == 40 and s['publication']['ranked_model_count'] == 37 and not s['pending_model_ids']
    models = s['models']
    added = set(s['native_added_october_18_model_ids']) | set(s['llm_added_october_18_model_ids'])
    order = sorted(s['publication']['eligible_model_ids'], key=lambda m: -models[m]['primary']['correct'])
    rows = []
    for m in order:
        v = models[m]
        cost = v['cost_all_attempts']
        price = f"${v['known_usd_per_1000_questions']:.5f} {cost_band(v['known_usd_per_1000_questions'])}"
        if cost.get('sources', {}).get('usage_times_published_tariff'):
            price = '~' + price
        if cost['missing_attempts']:
            price += ' + ?'
        med = v['latency_first_all']['median_ms']
        rows.append([v['label'] + (' *' if m in added else ''), v['primary']['correct'],
                     f"{100*v['primary']['accuracy_attempted']:.1f}%", f"{v['by_role']['core']['correct']}/640",
                     f'{med:.0f} ms {speed_band(med)}', f"{v['latency_first_all']['p95_ms']:.0f} ms", price,
                     ', '.join(sorted(v['dates_toronto']))])
    ranking = table(['Model', 'Correct / 1,136', 'Accuracy', 'Core correct', 'Median', 'p95', 'Cost per 1,000', 'Test date'], rows)
    new_rows = []
    for m in sorted(s['llm_added_october_18_model_ids'], key=lambda m: -models[m]['primary']['correct']):
        v, c = models[m], s['output_compliance'][m]
        new_rows.append([v['label'], v['primary']['correct'], v['eventual']['correct'],
                         c['usable_first_answers'], c['model_output_failures'], c['provider_transport_failures'],
                         f"${v['cost_all_attempts']['known_usd']:.8f}", v['cost_all_attempts']['missing_attempts']])
    generative = table(['Added model', 'First correct', 'Eventual correct', 'Usable first', 'Output failures',
                        'Provider failures', 'Actual 1,136 cost', 'Unknown charges'], new_rows)
    stops = []
    for m, r in s['partial_samples'].items():
        p, c = r['primary_on_completed_only'], r['output_compliance_completed']
        stops.append([r['label'], f"{p['correct']}/{p['attempted']}",
                      f"{r['latency_completed_first']['median_ms']:.0f} ms", c['model_output_failures'],
                      c['provider_transport_failures'], '; '.join(r['stop_reasons']).replace('_', ' ')])
    stopped = table(['Stopped diagnostic', 'Correct / evaluated', 'Median', 'Output failures', 'Provider failures', 'Stop trigger'], stops)
    totals = s['llm_october_18_experiment_costs']
    all_cost = s['publication']['ranked_accounted_cost']
    native_cost = s['native_october_18_cost']
    native_probes = s['native_october_18_compatibility_probes']
    notes = (repo_file('native_expansion_notes.md', root=ROOT)).read_text().strip()
    # Keep the older local-review source untouched while the current published
    # narrative follows the precise saved values and documented error classes.
    notes = notes.replace('**262 ms p95**',
                          f"**{models['liquid_ultra']['latency_first_all']['p95_ms']:.0f} ms p95**")
    notes = notes.replace('31 first-attempt provider rate limits',
                          '31 first-attempt HTTP 429 provider failures')
    report = f'''# 37 models on the same 1136 text decisions

I started this benchmark because Jev interested me, but I could not place its intelligence relative to the LLMs I use. Could a service that returns a typed decision rather than a paragraph make better quick decisions than Luna? On this bank, Jev was substantially stronger. Expanding the comparison has since found models that exceed Jev, and a regular LLM that comes close.

**Respan Span-02 scored 1,011/1,136 (89.0%), Perplexity Decider v1.2 scored 1,010 (88.9%), and Nimble Max scored 997 (87.8%).** Jev 1.14 scored 929 (81.8%), Jev 1.13 scored 919 (80.9%), regular Luna scored 727 (64.0%) and Luna Decisions scored 677 (59.6%). The strongest regular LLM under the same short-output contract is now **Gemma 4 31B: 902/1,136 (79.4%)**.

These are **System 1-style decisions**: one answer from supplied information, without an explicit thinking budget, tools or an agentic feedback loop. They matter for systems routing many requests under time and cost constraints. This does not compare unrestricted reasoning, writing or agentic ability.

**Updated October 18, 2026.** The main comparison contains **37 complete routes × 1,136 questions = 42,032 model-question cases**. There are 40 complete runs in the saved record, or 45,440 cases; three output-noncompliant runs remain outside the ranking. The October 18 release adds 14 complete native-decision routes, three regular LLMs and the decision-specialized generative Tev1. Five stopped LLM samples, the stopped Solar Decide sample and two failed interface probes are separate diagnostics, not additional full-bank results. The previous release ranked 19 models from 22 complete runs (24,992 model-question cases); those saved results, costs and response times are unchanged.

The bank has **640 core questions plus 496 related variants, contrasts and candidate checks across 25 families**. Related items are not independent observations. The [function tables and examples](FUNCTIONS.md) explain the abilities. The [image benchmark](https://github.com/etsabary/visual-decision-benchmark) remains separate. A harder future bank is also a separate project; no new questions enter this release.

![Overall and core accuracy across all 37 included routes](overall_llm_expanded_2026-10-18/figures/overall_accuracy.png)

## Full bank results with cost and speed scales

Every score uses the first attempt on all 1,136 questions. Failed requests, refusals, invalid output and truncations remain unsuccessful. Median and p95 include **all 1,136 timed first attempts**, including failures. p95 is the response time at or below which roughly 95% of requests completed. A lower median can coexist with a long slow tail.

The labels use fixed descriptive bands for this workload, not universal definitions. Speed: 🟩 Fastest ≤250 ms; 🟨 Fast >250–500 ms; 🟧 Moderate >500–1,000 ms; 🟥 Slow >1,000 ms. Cost per 1,000: 🟩 Lowest ≤$0.01; 🟨 Low >$0.01–$0.025; 🟧 Mid >$0.025–$0.05; 🟥 Highest >$0.05. Both the label and the numerical value remain visible, so color is not required to read the comparison.

Costs per 1,000 normalize the actual 1,136-question run, including eligible recoveries: run cost ÷ 1,136 × 1,000. **`+ ?` means some charges are unknown**, so that color band describes the known lower bound and may understate the final cost. `~` marks token usage multiplied by a captured published tariff instead of a returned dollar charge. Dates are Toronto dates. * marks an October 18 addition.

{ranking}

The 37 included runs account for **${all_cost['known_usd']:.8f}** in known charges or tariff calculations, with **{all_cost['missing_attempts']} attempt charges unreported**. These are not independently reconciled invoices. Compatibility calls and stopped samples are excluded from ranked-run totals. Promotions and later tariff changes are not applied retroactively.

Within that ranked-run total, the 14 complete October 18 native-decision additions reported **${native_cost['known_usd']:.9f}**, with **{native_cost['missing_attempts']} attempt charges unknown**. The **{native_probes['count']} native-route compatibility calls**, including the stopped route's probe, reported **${native_probes['known_usd']:.8f}** separately, with **{native_probes['unknown_charge_attempts']} unknown charges**. The stopped native Solar sample is accounted for separately below; it is not part of the 14 full runs.

Nimble Max's saved cost uses its October 16 tariff of $0.09 per million input tokens. Its [documented tariff checked October 18](https://docs.bespokelabs.ai/nimble/pricing.md) is $0.04. At that price, the saved 373,997 input tokens would cost $0.01495988 for 1,136 questions, or $0.013169 per 1,000. This is a price-only calculation, not a new run. The deprecated `nimble-v4` name now redirects to Max: its dated row does not imply a separate current checkpoint.

{notes}

## Gemma is the strongest regular LLM tested under this contract

Gemma 4 31B scored **902/1,136 (79.4%)**, 175 more correct answers than regular Luna and 225 more than Luna Decisions. It finished 27 questions behind Jev 1.14. Its core-only result was 522/640 (81.6%), compared with Jev's 538/640 and regular Luna's 431/640. The same 902 total as the saved Nimble v4 result does not imply that they answer the same questions correctly.

Its **491 ms median** was shorter than regular Luna's 942 ms, but longer than Jev's 182 ms or Nimble Max's 236 ms. Known full-run cost was **$0.04693176**, above regular Luna's $0.03431990. Forty attempt charges were unreported. Gemma had 47 model-output failures (4.1%) and 28 first-attempt provider failures. It stays below the agreed 5% output-failure cutoff, but all 75 unsuccessful first attempts remain in the score. Recovery improved its eventual result to 915; the ranking retains 902.

Gemma was strong on necessary conditions and contraposition (44/46), one-to-one assignments (54/61), belief tracking (42/44), priority rules (48/52) and causal intervention (38/44). Belief tracking asks whose knowledge changes after an event, given what each person witnessed. Causal intervention changes a variable by instruction and asks which downstream effects follow; it is not merely observing that variable. Gemma exceeded Jev on these sampled belief, priority and causal questions, despite scoring lower overall.

Its weaknesses remained substantial: scheduling 41/69, exact truth counting 27/65, truth-teller consistency 27/62, swaps 24/46 and procedures 9/42. A model that can handle many implications can still fail when it must maintain an updated state or make several constraints hold simultaneously.

## Qwen is near regular Mercury and Nex is a cheaper lower scoring option

Qwen3 235B A22B Instruct 2507 scored **706/1,136 (62.1%)**, with all first answers usable, a **556 ms median**, a 1,667 ms p95 and **$0.03013258** reported cost. It scored 142 questions above the smaller Qwen3-30B-A3B Instruct 2507 configuration, but only four above regular Mercury 2.5. Mercury's saved median was 534 ms and its cost $0.01321493 at the captured promotional price. A larger hosted model did not produce a substantial aggregate gain over that cheaper alternative.

Qwen scored 37/37 on lookup and source authority, 44/45 on preference ordering and 42/46 on counterexamples. It was much weaker on forward conditionals (14/39), exact truth counting (10/65), procedures (8/42) and causal intervention (22/44). Its swap score of 27/46 matched Jev 1.14 and exceeded Span's 25/46, without making either result dependable.

Nex N2.5 Mini scored **651/1,136 (57.3%)**, with all first answers usable, a **500 ms median**, a 1,215 ms p95 and **$0.008746245** reported cost. It was the cheapest completed new regular LLM, but did not improve on regular Luna, Luna Decisions or the leading native routes. Its better families included transitive comparisons (34/34), reachability (37/37), source authority (37/37) and set relations (38/43). Belief tracking was 24/44, causal intervention 15/44, swaps 14/46 and procedures 10/42. Span's native route was cheaper and more accurate overall in these captured runs.

## Tev is a small generative decision model with a different interface

Tev1 4B experimental scored **676/1,136 (59.5%)**, one fewer correct answer than Luna Decisions, with all first answers usable. Its **202 ms median**, **254 ms p95** and **$0.01714902** reported full-run cost offer a useful speed and cost comparison with Luna Decisions' 261 ms, 533 ms and $0.03941610, respectively. Luna's total also has 61 unreported attempt charges. These close accuracy counts are descriptive results, not proof of statistical equivalence.

Tev scored 37/37 on lookup, 44/45 on preference ordering and 37/44 on fault diagnosis. Necessary conditions were 27/46, scheduling 25/69, swaps 18/46 and procedures 11/42. It did not approach the leading overall accuracy scores.

Tev's [documented architecture](https://huggingface.co/togethercomputer/Tev1-4B-experimental) generates an option through a language-model head. OpenRouter rejected its chat/completions call with HTTP 400 and required the native decisions endpoint. The complete run therefore uses a **decision-specialized generative model through OpenRouter's native adapter**, not a claimed non-generative architecture. The failed chat probe is preserved separately; it is not scored as an incorrect decision.

![Accuracy, full response times and normalized costs of the four generative additions and six reference routes](overall_llm_expanded_2026-10-18/figures/generative_accuracy_cost_speed.png)

## Output compliance and the stopped LLM samples

The existing main-table rule excludes complete runs with at least 5% model-output failures. That author-requested, post-hoc rule still excludes the earlier Haiku, DeepSeek and Phi-4 runs; their [complete diagnostics](OUTPUT_COMPLIANCE.md) are preserved. Provider failures are counted separately and do not count toward the format cutoff.

For the new LLMs, the agreed operational screen stops a route after the first 100 questions, or at a subsequent cumulative 100-question check, if accuracy falls below 50%, model-output failures reach 5%, or the median exceeds two seconds. A final check covers all 1,136. This is practical outcome-based selection of useful additions, not a representative survey or a pre-registered superiority study. The first 100 questions cover all families unevenly and include related variants. Partial accuracy is not extrapolated to the full bank, and this new stopping policy is not retroactively used to remove older completed low-scoring rows.

{generative}

The four complete additions reported **${totals['selected_full_runs']['known_usd']:.9f}**, with 40 unknown charges. Stopped samples reported **${totals['stopped_samples']['known_usd']:.11f}**, with 147 unknown charges. Eleven compatibility probes reported **${totals['compatibility_probes']['known_usd']:.9f}**, with two charges unknown. The entire new generative-route experiment therefore reported **${totals['total_new_experiment']['known_usd']:.11f}**, with 189 unknown attempt charges. None of the partial or probe costs is silently assigned to a completed model's normalized score.

The five stopped LLM samples are listed with their actual denominators in the [separate diagnostics](OUTPUT_COMPLIANCE.md#october-18-stopped-samples), outside the main ranking, cost scale and function charts. Their small, selected prefixes cannot establish a full-bank model ranking.

Mistral Small 4's 18/100 reflects 68 first-attempt provider failures; among its 32 usable first decisions, 18 were correct. That is a route-availability problem as well as a low delivered score, not evidence that an available Mistral model would score 18% overall. Solar Pro4 passed earlier screens and reached exactly 40 output failures in 800 questions, the 5% stopping threshold. DeepSeek's October 17 checkpoint returned 62 correct answers in 100 but seven unusable model outputs. Ling failed all three screens. Laguna failed the accuracy and format screens.

Xing4's free route returned HTTP 429 in its unscored compatibility probe. It has no measured benchmark accuracy. Tev's rejected chat route was replaced only by a separately bound native-adapter run; its full result is reported above.

The other stopped configuration, **Solar Decide**, returned 311/347 correct completed decisions (89.6%) but had a **4.58-second median and 12.95-second p95**. It was stopped at the author's request. On exactly those same 347 items, Span scored 316, Perplexity 310 and Nimble Max 309. One of 348 dispatches has no recorded response, so its result and charge remain unknown. It is not replayed and it receives no full-bank score. Its 347 recorded responses reported $0.01015205, separate from the generative experiment totals above.

## What the scores support

The top full-bank routes have different profiles. Span improves sequential execution and scheduling, while Perplexity and Nimble are stronger on some direct rule and belief questions. Jev remains substantially above both Luna configurations, and its 182 ms median remains among the shortest tested. Gemma narrows the regular-LLM accuracy gap, at a higher known cost and with some unusable outputs. Very cheap regular LLMs can be useful for simple families without matching the best specialized routes overall.

Regular Luna still outscored Luna Decisions, 727 versus 677, while taking a longer median, 942 versus 261 ms. Jev 1.14's ten-answer total improvement over 1.13 is modest, not a general intelligence jump. One-to-one assignments improved from 50/61 to 56/61, while other families changed little or moved in the other direction. Feature claims such as languages or image support are not established by these English text scores; the separate visual benchmark measures actual image decisions.

![Family-level correct counts and accuracy](overall_llm_expanded_2026-10-18/figures/generative_family_accuracy.png)

The [37-model family CSV](overall_llm_expanded_2026-10-18/family_comparison.csv) and [function tables](FUNCTIONS.md) show the complete profile. A perfect sampled family is not a reliability guarantee. The dependent variants help expose option-position sensitivity and inconsistency, but do not create extra independent scenarios. The overall score alone does not establish safe deployment on an unfamiliar workload.

## Measurement conditions and reproducible evidence

All additions receive the unchanged question facts, instructions and five options in the original order. Ordinary LLMs use the original numeric-only suffix, a 16-token output cap and reasoning disabled, or a natively nonthinking checkpoint. Native APIs serialize the same content as state and five criteria; Tev uses that native wire format. Providers are pinned and fallback is disabled. Captured [model and endpoint snapshots](llm_additions_2026-10-18) retain the requested model, returned identities, tariff, promotion and settings. Aliases alone do not independently attest fixed model weights.

There are two concurrent requests per model, with a barrier after each pair. Each attempt opens a fresh HTTPS connection; the monotonic timer starts before connecting and stops after reading the complete body. Local queueing and retry waits are outside that response timer. Up to five native models or four regular LLMs were active in their respective batches, with Tev controlled separately. Dates, providers and aggregate load differ, so these are end-to-end hosted-route measurements, not isolated architecture or local-hardware comparisons.

Only transport failures and actual HTTP 408, 429 or 5xx allow one recovery. Wrong valid answers, malformed model outputs and HTTP-200 provider-error envelopes are not retried. The ranking never substitutes a recovered answer for the first attempt. Reported absence of a reasoning trace is not an independent audit of hidden internal computation.

The [40-model aggregate](overall_llm_expanded_2026-10-18/summary.json), [new generative ledgers](llm_additions_2026-10-18), [native addition ledgers](native_additions_2026-10-18), [prior 22-model snapshot](overall_expanded_2026-10-16/summary.json) and [unchanged question bank](data/questions_1136.csv) preserve the evidence. The answer key, credentials, account metadata and individual correctness records are not published. The inference executors never read the key. A separate offline controller reads it only to release or stop subsequent unchanged batches; no correct answer or item-level feedback is sent to the models.

Offline integrity checks send no requests. Use Python 3.10, matching the capture runtime, to reproduce the frozen probability-validity checks:

```sh
python3 native_expansion_analysis.py
python3 llm_expansion_analysis_2026_10_18.py
```

With the frozen private key supplied externally, all complete scores, stopped-sample scores, family scores and screening decisions can be independently reproduced offline:

```sh
python3 llm_expansion_analysis_2026_10_18.py --answer-key /path/to/answer_key_PRIVATE.csv
```

The [original three-model reference](THREE_MODEL_REFERENCE.md) remains available, with its saved inputs and measurements intact.
'''
    # Preserve the user's earlier wording preference and frozen original latency labels.
    assert 'historical' not in report.lower()
    report = report.replace('>250–500', '>250 to 500').replace('>500–1,000', '>500 to 1,000')
    report = report.replace('>$0.01–$0.025', '>$0.01 to $0.025').replace('>$0.025–$0.05', '>$0.025 to $0.05')
    (repo_file('LLM_EXPANSION.md', root=ROOT)).write_text(report)
    print('Built current 37-route overall analysis; publication builder can now render it')


if __name__ == '__main__':
    main()
