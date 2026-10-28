"""Build the local-review October 18 report without replacing published pages."""
from repo_layout import repo_file
from decimal import Decimal
from hashlib import sha256
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SOURCE=repo_file('overall_expanded_2026-10-18', root=ROOT)


def table(header,rows):
    return '\n'.join(['| '+' | '.join(header)+' |','| '+' | '.join(['---']*len(header))+' |']+
                     ['| '+' | '.join(map(str,row))+' |' for row in rows])


def main():
    s=json.loads((SOURCE/'summary.json').read_text())
    assert s['model_count']==36 and not s['pending_model_ids']
    new=s['native_added_october_18_model_ids']
    ranked=s['publication']['eligible_model_ids']
    order=sorted(ranked,key=lambda m:-s['models'][m]['primary']['correct'])
    result_rows=[]
    for m in order:
        v=s['models'][m];cost=v['cost_all_attempts']
        label=v['label']+(' *' if m in new else '')
        dates=', '.join(d.removeprefix('2026-') for d in sorted(v['dates_toronto']))
        price=('~' if cost.get('sources',{}).get('usage_times_published_tariff') else '')+f"${v['known_usd_per_1000_questions']:.5f}"
        if cost['missing_attempts']:price+=' + ?'
        result_rows.append([label,f"{v['primary']['correct']}/1,136",f"{100*v['primary']['accuracy_attempted']:.1f}%",
            f"{v['by_role']['core']['correct']}/640",f"{v['latency_first_all']['median_ms']:.0f}",
            f"{v['latency_first_all']['p95_ms']:.0f}",price,dates])
    results=table(['Model','Correct','Accuracy','Core correct','Median ms','p95 ms','Cost per 1,000','Test date'],result_rows)
    reliability_rows=[]
    for m in sorted(new,key=lambda m:-s['models'][m]['primary']['correct']):
        v=s['models'][m];c=s['output_compliance'][m];money=v['cost_all_attempts']
        reliability_rows.append([v['label'],c['usable_first_answers'],c['model_output_failures'],c['provider_transport_failures'],
            v['recovery_attempts'],v['eventual']['correct'],f"${money['known_usd']:.8f}",money['missing_attempts']])
    reliability=table(['New model','Usable first','Output failures','Provider or transport failures','Recovery calls',
                       'Eventual correct','Actual 1,136 run cost','Unknown charges'],reliability_rows)
    panels_rows=[]
    for m in sorted(new,key=lambda m:-s['models'][m]['primary']['correct']):
        p=s['models'][m]['panels'];r=p['rotation'];c=p['contrast'];k=p['candidate_checks']
        panels_rows.append([s['models'][m]['label'],f"{r['all_correct']}/{r['planned']}",
            f"{r['consistent']}/{r['complete']}",f"{c['both_correct']}/{c['planned']}",f"{k['correct']}/{k['checks']}"])
    panels_table=table(['New model','All rotations correct','Semantically consistent complete panels','Both contrast answers correct','Candidate checks correct'],panels_rows)
    routes=[]
    for m in new:
        v=s['models'][m]
        data=json.loads((repo_file('native_additions_2026-10-18', root=ROOT)/m/'model_metadata.json').read_text())
        endpoint=data['selected_endpoint'];price=Decimal(endpoint['pricing']['prompt'])*10**6
        identities=', '.join(k for k in v['identities'] if not k.startswith('unreported'))
        routes.append([v['label'],v['provider_tag'],identities,f'${price.normalize()}'])
    route_table=table(['New model','Pinned provider tag','Returned model name','Captured input price per million'],routes)
    total=s['native_october_18_cost'];probes=s['native_october_18_compatibility_probes']
    partial=s['partial_runs']['solar_decide'];partscore=partial['primary_on_completed_only'];parttime=partial['latency_completed_first']
    warnings=[(s['models'][m]['label'],s['models'][m]['primary']['probability_warnings']) for m in new if s['models'][m]['primary']['probability_warnings']]
    warning_text='; '.join(f'{name}: {n}' for name,n in warnings) or 'None'
    notes=(repo_file('native_expansion_notes.md', root=ROOT)).read_text().strip()
    text=f'''# Native decision models on the full text bank

I tested 15 new native decision routes on October 18, 2026. Fourteen completed the same 1,136 English text questions used for Jev, Nimble and Luna; I stopped Solar Decide because its latency was impractical for fast decisions. The complete runs add 15,904 scored model-question cases. The combined record now contains 36 complete model runs; 33 qualify for the main comparison under the existing output-compliance rule. All 22 earlier results and their original costs and timings are unchanged.

This is a local review before choosing the next regular-LLM runs. The published GitHub pages have not been replaced. The image bank has not been run on these additions.

{notes}

![Accuracy across the 33 included routes](overall_expanded_2026-10-18/figures/overall_accuracy.png)

## Results on the unchanged question bank

Every row uses the first attempt on all 1,136 questions. A failed request is unsuccessful, but is distinguished from a wrong valid answer in the reliability table. The core column uses the 640 underlying questions. The other 496 cases are related rotations, contrasts and candidate checks, so the overall denominator is not 1,136 independent observations.

* marks a new October 18 run. All dates are in Toronto in 2026. Costs per 1,000 are normalized from each actual 1,136-question run, including permitted recoveries. `+ ?` indicates unreported charges; `~` indicates a usage-times-tariff calculation rather than a returned dollar charge.

{results}

Haiku 5.5, DeepSeek V4.1 Flash and Phi-4 remain outside this main table under the existing post-hoc cutoff of at least 5% model-output failures. Their original runs remain in the [output diagnostics](OUTPUT_COMPLIANCE.md). Provider failures do not count toward that format cutoff, and none is removed from an eligible model's score.

## Cost and route reliability of the additions

The 14 new full runs reported **${total['known_usd']:.8f}** in known charges, with **{total['missing_attempts']} attempts whose charges were not returned**. The 15 compatibility calls are separate and cost **${probes['known_usd']:.8f}** in reported charges. Missing charges are not treated as zero, and these totals have not been reconciled against an invoice.

{reliability}

The eventual column includes at most one recovery for a transport failure or HTTP 408, 429 or 5xx. Wrong valid answers, malformed answers and HTTP-200 provider-error envelopes are not retried. The primary ranking never substitutes an eventual answer for the first response.

### Solar Decide was stopped for latency

Solar Decide returned {partscore['correct']}/{partscore['attempted']} correct completed answers ({100*partscore['accuracy_attempted']:.1f}%), with a {parttime['median_ms']/1000:.2f}-second median and {parttime['p95_ms']/1000:.2f}-second p95. On exactly those {partscore['attempted']} items, Span-02 scored {partial['same_completed_subset']['respan02']['correct']}, Perplexity Decider {partial['same_completed_subset']['pplx_decider12']['correct']} and Nimble Max {partial['same_completed_subset']['nimble_v4_max']['correct']}. These are matched partial-subset comparisons, not full-bank scores. The route was accurate on this subset but too slow for the intended latency-sensitive use.

Its 347 recorded responses reported $0.01015205. One of the 348 dispatched requests had no recorded response when the process was stopped; its outcome and charge remain unknown. The [stop receipt and partial ledger](native_additions_2026-10-18/solar_decide_partial) preserve that request without replay. Solar Decide is outside every full-bank table and chart.

Nimble Max's table cost retains the October 16 tariff of $0.09 per million input tokens. Its [current documented tariff](https://docs.bespokelabs.ai/nimble/pricing.md), checked October 18, is $0.04. Applying that tariff to its saved 373,997 input tokens gives $0.01495988 for the full bank, or $0.013169 per 1,000 questions. That is a price-only calculation, not a new benchmark run. The deprecated `nimble-v4` name now points to Max, so the two historical Nimble rows do not imply two distinct current services.

![Accuracy, timing and normalized cost of the 14 complete additions and four references](overall_expanded_2026-10-18/figures/native_accuracy_cost_speed.png)

## Functions and dependent diagnostic panels

The [family CSV](overall_expanded_2026-10-18/family_comparison.csv) preserves correct counts and denominators for all 25 functions and 33 included models. The [task examples](task_examples.md) explain what each function means without adding scored questions.

![Correct counts and accuracy across 25 functions](overall_expanded_2026-10-18/figures/native_family_accuracy.png)

Rotation panels put the same semantic options in different positions. A model can be semantically consistent and consistently wrong, so all-correct panels are separate. Contrast panels change evidence and require the right decision on both versions. Candidate checks ask whether a proposed answer meets the original rules. Planned panel denominators retain missing answers.

{panels_table}

Probability-distribution warnings do not discard usable choices, matching the original scoring policy. New warnings: {warning_text}. Clef's recorded warning examples arise from rounded probabilities summing to 0.9999 or 1.0001 rather than exactly one. The raw responses preserve the distributions. Returned confidence values are not calibrated on a common cross-model scale; threshold results in the aggregate data are exploratory on this same bank.

## Measurement conditions and model names

All 15 new routes use OpenRouter's `/api/alpha/decisions` endpoint. They receive the unchanged native state, original instructions and question, and the original five criteria in the same order. There are two concurrent requests per model, with a barrier after each pair, and at most five active native models. Each attempt opens a fresh HTTPS connection. The monotonic timer starts before connecting and ends after reading the complete response. Local queueing and retry waits are outside that response timer. The table below lists the 14 completed routes; the stopped route's snapshot is in its partial ledger.

Median and p95 include all 1,136 timed first attempts per model, including failures. p95 is the response time at or below which roughly 95% of those requests completed. The earlier routes use the same timing boundary and per-model concurrency, but were tested on October 15/16 with different aggregate load and services. These measurements describe end-to-end routes, not isolated model inference.

Every provider is pinned and fallback is disabled. The two PrimeIntellect Clef routes were chosen at their captured lower tariffs, not silently switched to the more expensive Cloudflare or DeepInfra routes. Returned names are checked against captured endpoint metadata; names alone do not independently attest fixed weights. Clef and Clef Flash return undated model names.

{route_table}

The captured endpoint snapshots retain promotions and listed modalities. Only text was tested. Image acceptance and visual decision quality require separate verification. [Tev1's documented interface](https://huggingface.co/togethercomputer/Tev1-4B-experimental) uses a standard language-model head and generates an option letter through chat completions; it is reserved for the later generative-model comparison, rather than classified as one of these 15 native routes.

## Saved evidence and reproduction

The [combined summary](overall_expanded_2026-10-18/summary.json), [new sanitized attempt ledgers](native_additions_2026-10-18), [unchanged 22-model summary](overall_expanded_2026-10-16/summary.json) and [question bank](data/questions_1136.csv) preserve the comparison. The answer key, account metadata, credentials and individual correctness records are not exported. Scoring happens offline after each model's full run, using the original key's frozen hash; the live executor never reads the key.

Offline integrity and protocol checks require no API credentials:

```sh
python3 native_expansion_analysis.py
python3 -m unittest test_native_field_2026_10_18 test_native_expansion_analysis
```

With the original private key supplied externally, all 36 complete aggregate scores, family scores, panel results and the stopped route's partial score can be reproduced without sending requests:

```sh
python3 native_expansion_analysis.py --answer-key /path/to/answer_key_PRIVATE.csv
```

The bank measures single-shot choice decisions from supplied facts, without an explicit thinking budget, tools or answer feedback. It does not measure unrestricted reasoning, writing, multilingual performance or agentic iteration.
'''
    (repo_file('NATIVE_DECISION_EXPANSION.md', root=ROOT)).write_text(text)
    print('Built local-review report; existing README and published HTML unchanged')


if __name__=='__main__':main()
