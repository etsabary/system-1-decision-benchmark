"""Build the active report from the independently checked two-item correction.

No calls or answer-key access. Superseded captures and seals remain unchanged.
"""
from repo_layout import repo_file
from pathlib import Path
import json
import shutil

import build_october18_report as web
import build_report as tables

ROOT = Path(__file__).resolve().parents[1]
FOLDER = 'corrected_2026-10-18'
SOURCE = repo_file(FOLDER, root=ROOT)
MARKER = '<meta name="benchmark-cohort" content="october18-corrected-two-items">'


def order(s):
    return sorted(s['publication']['eligible_model_ids'], key=lambda m: -s['models'][m]['primary']['correct'])


def cost_cell(v):
    estimated = v.get('reported_api_cost_all_attempts', {}).get('known_usd') != v['cost_all_attempts']['known_usd']
    return ('~' if estimated else '') + web.format_cost(v['known_usd_per_1000_questions'], v['cost_all_attempts']['missing_attempts'])


def dates(v):
    days = sorted(v['dates_toronto'])
    return ', '.join(days)


def main_report(s):
    m = s['models']
    n = lambda mid: m[mid]['primary']['correct']
    acc = lambda mid: f"{100*m[mid]['primary']['accuracy_attempted']:.1f}%"
    med = lambda mid: f"{m[mid]['latency_first_all']['median_ms']:.0f}"
    p95 = lambda mid: f"{m[mid]['latency_first_all']['p95_ms']:.0f}"
    usd = lambda mid: f"${m[mid]['cost_all_attempts']['known_usd']:.8f}"
    per = lambda mid: f"${m[mid]['known_usd_per_1000_questions']:.5f}"
    by_family = {f['family_id']: f for f in s['by_family']}
    f = lambda fid, mid: by_family[fid]['models'][mid]['correct']
    text = f'''# 36 models on the same 1136 text decisions

I started this benchmark because Jev interested me, but I could not place its intelligence relative to the LLMs I use. Could a service that returns a typed decision rather than a paragraph make better quick decisions than Luna? On this bank, Jev was substantially stronger. Expanding the comparison has since found models that exceed Jev, and a regular LLM that comes close.

**Respan Span-02 scored {n('respan02'):,}/1,136 ({acc('respan02')}), Perplexity Decider v1.2 scored {n('pplx_decider12'):,} ({acc('pplx_decider12')}), and Nimble Max scored {n('nimble_v4_max')} ({acc('nimble_v4_max')}).** Jev 1.14 scored {n('jev114')} ({acc('jev114')}), Jev 1.13 scored {n('jev113')} ({acc('jev113')}), regular Luna scored {n('openai/gpt-6-luna')} ({acc('openai/gpt-6-luna')}) and Luna Decisions scored {n('luna_decisions')} ({acc('luna_decisions')}). **Gemma 4 31B is the strongest regular LLM tested under this short-output contract: {n('gemma4_31b')}/1,136 ({acc('gemma4_31b')}).**

These are **System 1-style decisions**: one answer from supplied information, without an explicit thinking budget, tools or an agentic feedback loop. They matter for systems routing many requests under time and cost constraints. This does not compare unrestricted reasoning, writing or agentic ability.

**Updated October 18, 2026, after the question audit.** The active comparison contains **36 complete configurations × 1,136 questions = 40,896 model-question cases**. Two ambiguous procedure questions have been replaced by clarified versions and tested across all 36 available configurations. Every model retains its other 1,134 responses. The leading order is unchanged. The original Nimble v4 is unavailable as a distinct checkpoint, so its 1,134 retained cases remain a partial diagnostic outside the full-bank ranking. Three earlier output-noncompliant runs, five stopped LLM samples, the stopped Solar Decide sample and two failed interface probes also remain outside the ranking.

The [active question bank]({FOLDER}/questions_1136.csv) contains **640 core questions plus 496 related variants, contrasts and candidate checks across 25 families**. Each question has five options, giving a 20% uniform-random baseline. Related items are not independent observations. The [function tables and examples](FUNCTIONS.md) explain the abilities. The [image benchmark](https://github.com/etsabary/visual-decision-benchmark) remains separate. The harder future benchmark is a separate project.

![Overall and core accuracy across all 36 complete corrected-bank configurations]({FOLDER}/figures/overall_accuracy.png)

## Full bank results with cost and speed scales

Every score uses the first attempt on all 1,136 active questions. Failed requests, refusals, invalid output and truncations remain unsuccessful. Median and p95 pool **all 1,136 timed first attempts**, including failures: 1,134 retained measurements plus the two new measurements. Medians are not averaged. This correction is not a fresh full-bank speed rerun. p95 is the response time at or below which roughly 95% of requests completed.

Costs per 1,000 normalize the selected 1,136-question evidence, including permitted recoveries: selected cost ÷ 1,136 × 1,000. **`+ ?` means additional charges are unknown**, so its cost band describes the known lower bound. `~` marks usage multiplied by a captured tariff rather than an API-returned dollar amount. Original charges retain their captured prices; the new Nimble Max calls use the October 18 tariff. Dates are Toronto dates. * identifies a configuration first added on October 18.

'''
    old = json.loads((repo_file('overall_llm_expanded_2026-10-18/summary.json', root=ROOT)).read_text())
    added = set(old['native_added_october_18_model_ids'] + old['llm_added_october_18_model_ids'])
    text += tables.table(['Model', 'Correct / 1,136', 'Accuracy', 'Core correct', 'Median', 'p95', 'Cost per 1,000', 'Test dates'], [
        [v['label'] + (' *' if mid in added else ''), v['primary']['correct'], acc(mid),
         f"{v['by_role']['core']['correct']}/640", web.format_speed(v['latency_first_all']['median_ms']),
         f"{v['latency_first_all']['p95_ms']:.0f} ms", cost_cell(v), dates(v)]
        for mid in order(s) for v in [m[mid]]])
    text += '\n' + web.legend_markdown()
    text += f'''
The active complete configurations account for **${s['total_selected_accounted_cost']['known_usd']:.8f}** in known charges or tariff calculations, with **{s['total_selected_accounted_cost']['missing_attempts']} attempt charges still unknown**. These are selected-evidence costs, not independently reconciled invoices. Removed original-question attempts, partial runs and compatibility probes are outside these totals. The [correction receipt]({FOLDER}/correction_receipt.json) accounts for removed calls separately.

For **GLM 4.7 Flash**, only the two replacement calls moved from inactive Cloudflare to **Venice**, using the same dated model. For **Nemotron 3.5 Super VL**, those two calls moved from inactive Crusoe to **Together**, again using the same dated model. Each retains 1,134 original-provider results. These are explicitly mixed-provider rows, not 1,136 new calls on the replacement provider. The [route records]({FOLDER}/routes.json) identify both changes.

Nimble Max's retained 1,134 responses use its October 16 tariff of $0.09 per million input tokens. The two fresh calls use the [October 18 tariff of $0.04](https://docs.bespokelabs.ai/nimble/pricing.md). Its active cost therefore combines captured prices rather than repricing the earlier run. The deprecated `nimble-v4` alias now redirects to Max and cannot supply the missing original-v4 measurements.

## Span leads the full bank while Perplexity and Nimble lead the core subset

Span scored **{n('respan02'):,}/1,136**, Perplexity **{n('pplx_decider12'):,}** and Nimble Max **{n('nimble_v4_max')}**. Perplexity and Nimble both scored **573/640 (89.5%)** on the core questions; Span scored **568/640 (88.8%)**. Span's higher total comes from the related variants and checks.

The two-answer gap between Span and Perplexity is too small to establish a general intelligence ordering. Span was correct on 72 questions Perplexity missed; Perplexity was correct on 70 Span missed. One Perplexity first attempt failed at the transport level. Its permitted recovery was correct, bringing its eventual score to 1,010; the primary table retains 1,009.

Span's median was **{med('respan02')} ms**, with **{usd('respan02')}** reported for the selected full bank, or **{per('respan02')} per 1,000 questions**. Every first answer was usable. Perplexity's median was **{med('pplx_decider12')} ms**, with **{usd('pplx_decider12')}** reported and one unknown charge. Its **{p95('pplx_decider12')} ms p95** was much shorter than Span's **{p95('respan02')} ms**. Span combined high accuracy, a short typical response and the lower reported cost; Perplexity had a more consistent response-time tail.

The function profile explains more than the aggregate gap. A sequential procedure can ask you to reverse five cards, swap two positions, move a card, and identify the final occupant of a position. Span scored **{f('F13','respan02')}/42**, versus Perplexity's **{f('F13','pplx_decider12')}/42**, Nimble's **{f('F13','nimble_v4_max')}/42** and Jev 1.14's **{f('F13','jev114')}/42**. Span also led these references on scheduling, **55/69**, versus Perplexity's 53, Nimble's 47 and Jev's 45. These are substantial improvements over Jev in maintaining and updating a state, with many errors remaining.

Exact truth counting asks which candidate makes precisely a specified number of statements true. Span scored **41/65**, Perplexity **39/65**, Nimble **37/65** and Jev **26/65**. This family is improving among the strongest tested routes, while the best score still misses 24 of 65 items.

Span was weaker on forward conditionals, **28/39**, where Perplexity, Nimble and both Jev versions scored 39/39. These ask what follows when facts activate a chain of rules. On belief tracking, which asks what a person knows given what they witnessed, Span scored **38/44**, versus Perplexity and Nimble at **44/44**. Its swap tracking was **25/46**, below Perplexity and Nimble's 32. The overall leader is not the strongest route for every function.

## Jev remains stronger than both Luna configurations

Jev 1.14 scored **929/1,136 (81.8%)**, versus regular Luna's **728 (64.1%)** and Luna Decisions' **677 (59.6%)**. Its **{med('jev114')} ms median** was among the shortest tested. Regular Luna answered 51 more questions correctly than Luna Decisions, while taking a longer median, **{med('openai/gpt-6-luna')} versus {med('luna_decisions')} ms**.

Jev 1.14 improved by ten correct answers over Jev 1.13, **929 versus 919**. One-to-one assignments rose from **50/61 to 56/61**. Such a question might assign five people to five rooms while satisfying several exclusions and one-use constraints. This is a meaningful family improvement within a modest overall gain. Procedures were **4/42 versus 6/42**, and swaps **27/46 versus 28/46**. The new version did not improve every function. Language and image feature claims are not established by these English text scores; actual image decisions have their own benchmark.

Mercury Decide tied Jev 1.14 at **929**, with a **{med('mercury_decide')} ms median** and **{usd('mercury_decide')}** reported cost, or **{per('mercury_decide')} per 1,000** at the captured promotion. It scored **33/46** on swaps, **42/44** on belief tracking and **51/52** on priority rules, versus Jev's 27, 39 and 46. Necessary conditions were weaker at **26/46**, versus Jev's **45/46**. Procedures were **10/42**. These profiles support choosing routes by the decisions a system actually needs to make.

Regular Mercury 2.5 is a separate configuration: **702/1,136 (61.8%)**, a **{med('inception/mercury-2.5')} ms median** and **{usd('inception/mercury-2.5')}** reported cost. The native route performed substantially better under this contract. Different hosted configurations and dates do not isolate the architectural cause of that difference.

## Gemma narrows the regular LLM gap

Gemma 4 31B scored **902/1,136 (79.4%)**, 27 answers behind Jev 1.14 and 174 above regular Luna. Its core result was **522/640 (81.6%)**, versus Jev's 538 and Luna's 431. Its **{med('gemma4_31b')} ms median** was shorter than regular Luna's {med('openai/gpt-6-luna')} ms, but longer than Jev's {med('jev114')} ms. Known selected cost was **{usd('gemma4_31b')}**, plus 40 unreported attempt charges.

Gemma had **47 model-output failures (4.1%)** and **28 first-attempt provider failures**. All 75 unusable first attempts remain unsuccessful. Recovery raised its eventual score to 915; the primary table retains 902. Its output-failure rate remains below the agreed 5% exclusion threshold.

Gemma scored **44/46** on necessary conditions, **54/61** on assignments, **42/44** on belief tracking, **48/52** on priority rules and **38/44** on causal interventions. It exceeded Jev on the latter three sampled families. A causal intervention changes a variable by instruction and asks which downstream effects follow. Its harder families included scheduling **41/69**, exact truth counting **27/65**, truth-teller consistency **27/62**, swaps **24/46** and procedures **9/42**.

Qwen3 235B A22B Instruct 2507 scored **706/1,136 (62.1%)**, with all first answers usable, a **{med('qwen3_235b')} ms median** and **{usd('qwen3_235b')}** reported cost. Its score is only four above regular Mercury 2.5 despite a higher captured cost. Qwen scored 37/37 on lookup and source authority, 44/45 on preference ordering and 42/46 on counterexamples, but only 14/39 on forward conditionals, 10/65 on truth counting and 8/42 on procedures.

Nex N2.5 Mini scored **650/1,136 (57.2%)**, with all first answers usable, a **{med('nex25_mini')} ms median** and **{usd('nex25_mini')}** reported cost. It was the cheapest completed new regular LLM. Span's native route was cheaper and more accurate overall in the captured runs.

Tev1 4B experimental now ties Luna Decisions at **677/1,136 (59.6%)**, with all first answers usable, a **{med('tev1_4b_native')} ms median**, **{p95('tev1_4b_native')} ms p95** and **{usd('tev1_4b_native')}** reported cost. It is a [decision-specialized generative model](https://huggingface.co/togethercomputer/Tev1-4B-experimental) served through OpenRouter's native adapter, not a claimed non-generative architecture. Its chat interface was rejected; that probe is separate from its full native-adapter result.

![Accuracy response time and cost for the leading routes and selected LLMs]({FOLDER}/figures/accuracy_cost_speed.png)

## Direct decision output does not guarantee accurate decisions

Liquid d1-ultra scored **970/1,136 (85.4%)**, with a **{med('liquid_ultra')} ms median** and **{p95('liquid_ultra')} ms p95**. The cheaper Liquid d1 scored **864 (76.1%)**. Clef scored **859**, Clef Flash **793** and Clef Omni **790**. Omni's higher captured text cost did not produce a gain over the cheaper Clef routes. Its non-text capabilities were not tested here.

Drex v2.0 scored **834**, versus v1.5's **791**. v2.0 encountered 31 first-attempt HTTP 429 provider failures. Kev 4B scored **737**, near regular Luna's 728 with a shorter median, **{med('kev4b')} versus {med('openai/gpt-6-luna')} ms**. Its core score, 418/640, was below Luna's 431.

Classify-1 scored **499/1,136 (43.9%)** and Solar Decide Flash **477 (42.0%)**. These low scores mostly reflect wrong valid choices. Perplexity Flash scored **855 (75.3%)**, including 50 first-attempt token-rate-limit failures. Accuracy among only usable responses is diagnostic; the full-denominator score measures delivered decisions.

## The audit and the two replacements

The audit selected **182 difficult questions** that at most 30% of the 37 previously included configurations answered correctly. Each received two independent blind verifications through the Village bridges, using Opus 5.5, Argon and GPT 6.1 Sol (extra-high effort). **181 had two independent verifiers supporting the supplied answer.** One procedure question had ambiguous wording: “after every operation” could ask for the intermediate states, while its options and supplied answer described the final state. A full-bank wording search found one additional instance outside the difficult-item queue.

Both now ask for the position **after all operations have been completed**. Their facts, operations and options are unchanged. Fresh independent Opus and Argon checks, plus exact step-by-step simulation, confirmed each clarified question has one valid supplied answer. The two original prompts and their results are absent from the active bank, accuracy totals, timing pools and selected costs. This targeted audit does not establish independent verification of every one of the 1,136 questions.

There were **72 fresh first attempts: two corrected questions × 36 available configurations**, with no recovery needed. Twenty-five configurations kept their total; seven lost one correct answer and four gained one. Fresh responses can vary, so those changes do not isolate the effect of the wording. The two corrected items are dependent variants, so all 640-question core scores are unchanged. The leading order is unchanged. Span's margin over Perplexity increased from one answer to two; Tev now ties Luna Decisions. The [aggregate correction deltas]({FOLDER}/summary.json) document the changes without publishing the private answer key.

## Output compliance and unfinished routes

Complete runs with at least 5% model-output failures remain outside the main comparison. Earlier Haiku, DeepSeek and Phi-4 runs are previous-version diagnostics, not corrected full-bank results. Provider failures are counted separately from explanations, refusals and malformed model output.

The newer LLM screen paused a model after 100 questions, and at subsequent cumulative 100-question checks, for accuracy below 50%, model-output failures at least 5%, or median response time above 2,000 ms. These are practical outcome-based selection rules for useful additions, not a representative survey. The uneven prefixes include related variants. The five stopped samples retain their actual denominators in the [output diagnostics](OUTPUT_COMPLIANCE.md); no partial score is extrapolated to the full bank. This stopping rule is not retroactively used to delete older completed low-scoring configurations.

The separate Solar Decide route returned **311/347 correct completed responses**, with a **4.58-second median and 12.95-second p95**, and was stopped for latency. One additional dispatch has no recorded response or known charge. It receives no full-bank score and was not replayed. Original Nimble v4 now has **902/1,134 retained correct answers**, with two replacement questions untested because the original checkpoint is unavailable. It also receives no full-bank rank.

![All function scores for selected complete configurations]({FOLDER}/figures/family_accuracy.png)

The [36-model family CSV]({FOLDER}/family_comparison.csv) and [complete function tables](FUNCTIONS.md) show where individual routes are stronger. Perfect scores on a sampled family are not reliability guarantees. Dependent variants expose sensitivity and inconsistency without creating extra independent scenarios.

## Measurement conditions and evidence

Ordinary LLMs receive the same question facts, instructions and five options in the same order, with the original numeric-only suffix, a 16-token output cap and reasoning disabled or a natively nonthinking checkpoint. Native APIs serialize the same content as state and five criteria. Tev uses the native wire format. Providers are pinned and fallback is disabled. Captured metadata records requested and returned model identities. Aliases alone do not independently attest fixed model weights.

Each model runs two requests concurrently with a barrier after each pair. Every attempt opens a fresh HTTPS connection. A monotonic timer starts before connecting and ends after the complete response body is read. Local queueing and retry waits are outside this timer. Original batches had different aggregate loads and dates. The two-question correction ran up to three models concurrently. These are end-to-end hosted-route measurements, not local-hardware speed estimates.

Only transport failures and actual HTTP 408, 429 or 5xx allow one recovery. Wrong valid choices, invalid output and HTTP-200 provider-error envelopes are not retried. Recovered answers never replace first attempts in the primary ranking. Reported absence of reasoning tokens is not an independent audit of hidden internal computation.

The [active aggregate]({FOLDER}/summary.json), [active question bank]({FOLDER}/questions_1136.csv), [replacement attempt evidence]({FOLDER}/replacement_attempts.jsonl), [route records]({FOLDER}/routes.json) and [correction receipt]({FOLDER}/correction_receipt.json) define this version. The selected record is 1,134 retained cases plus two new cases per included configuration. Earlier captures keep their exact seals for provenance and are not the active bank. The answer key, account metadata, credentials and item-level correctness are not published. Inference executors never read the key; scoring occurs offline.

Offline validation sends no model requests:

```sh
python3 -m pip install -r requirements-reports.txt
python3 freeze_october18_release.py --check
python3 validate_corrected_release.py
python3 -m unittest discover -p 'test_*.py'
```

Python 3.10 matches the capture runtime and its frozen floating-point probability checks. [Earlier measurement captures](overall_llm_expanded_2026-10-18) and [output diagnostics](OUTPUT_COMPLIANCE.md) preserve the different denominators and settings.
'''
    return text


def main():
    s = json.loads((SOURCE / 'summary.json').read_text())
    assert s['model_count'] == 36 and len(order(s)) == 36
    text = main_report(s)
    # Check the prose counts from computed deltas instead of relying on memory.
    from collections import Counter
    assert Counter(v['correct_delta'] for v in s['deltas'].values()) == {0:25, -1:7, 1:4}
    for name in ('README.md', 'LLM_EXPANSION.md'):
        (repo_file(name, root=ROOT)).write_text(text)
    functions = web.functions_markdown(s).replace('unchanged 1,136-question bank', 'corrected 1,136-question bank')
    functions = functions.replace('tested October 15, 16 and 18, 2026.',
        'tested October 15, 16 and 18, 2026. Each configuration combines 1,134 retained cases and two freshly tested corrected questions; all core scores are unchanged.')
    (repo_file('FUNCTIONS.md', root=ROOT)).write_text(functions)
    old = json.loads((repo_file('overall_llm_expanded_2026-10-18/summary.json', root=ROOT)).read_text())
    diagnostics = web.diagnostics_markdown(old)
    diagnostics = diagnostics.replace('# Output compliance and stopped routes', '# Output compliance and stopped routes')
    prefix = '''# Scope of the current diagnostics

The [active corrected-bank comparison](README.md) includes 36 complete configurations. The three excluded full-run diagnostics below describe the earlier uncorrected bank and were not retested. Stopped samples and interface probes retain their original denominators. They are outside the active ranking.

Original Nimble v4 has 902 correct answers on its 1,134 retained unchanged questions. The original checkpoint is unavailable: its alias now redirects to Max. The two corrected questions remain untested for original v4. It is a partial diagnostic, not a 1,136-question score, and Max responses were not substituted.

'''
    diagnostics = prefix + diagnostics
    (repo_file('OUTPUT_COMPLIANCE.md', root=ROOT)).write_text(diagnostics)
    mapping = {f'{FOLDER}/figures/{p.name}': f'figures/corrected/{p.name}' for p in (SOURCE / 'figures').iterdir() if p.is_file()}
    dest = repo_file('docs/figures/corrected', root=ROOT)
    dest.mkdir(parents=True, exist_ok=True)
    for p in (SOURCE / 'figures').iterdir():
        if p.is_file(): shutil.copyfile(p, dest / p.name)
    for name, content, title in [('index.html', text, '36 text decision models after the question audit'),
                                  ('functions.html', functions, 'Decision results by function and load'),
                                  ('output_compliance.html', diagnostics, 'Output compliance and partial diagnostics')]:
        (repo_file('docs', root=ROOT) / name).write_text(web.render(content, title, mapping).replace(web.COHORT_MARKER, MARKER))
    print('Built36-model corrected-bank report, function tables and three current HTML pages')


if __name__ == '__main__':
    main()
