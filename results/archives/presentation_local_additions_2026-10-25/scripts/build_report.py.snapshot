"""Build the current overall comparison, retaining the original selected runs."""
from repo_layout import repo_file
import json
from pathlib import Path
import re
import shutil
from datetime import datetime
from zoneinfo import ZoneInfo

import markdown

ROOT = Path(__file__).resolve().parents[1]
REPO = 'https://github.com/etsabary/jev-1.14-comparison-benchmark'
NATIVE = ('jev113', 'jev114', 'luna_decisions')


def table(headers, rows):
    return '| '+' | '.join(headers)+' |\n|'+'|'.join(['---']+['---:']*(len(headers)-1))+'|\n'+''.join('| '+' | '.join(str(v) for v in row)+' |\n' for row in rows)+'\n'


def pct(n, total):
    return f'{100*n/total:.1f}%' if total else 'n/a'


def render(text, title):
    body = markdown.markdown(text, extensions=['tables', 'fenced_code', 'toc'])
    pages = {'THREE_MODEL_REFERENCE.md': 'three_model_reference.html', 'FUNCTIONS.md': 'functions.html', 'README.md': 'index.html', 'OUTPUT_COMPLIANCE.md':'output_compliance.html'}
    body = re.sub(r'href="(?!https?://|#)([^"]+)"', lambda m: 'href="'+pages.get(m[1], REPO+'/blob/main/'+m[1])+'"', body)
    return '''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'''+title+'''</title><style>body{max-width:1260px;margin:auto;padding:32px 24px 80px;background:#f8fafc;color:#193047;font:17px/1.65 system-ui,sans-serif}h1{font-size:2.35rem;line-height:1.2}h2{margin-top:2.3rem;line-height:1.3}a{color:#087f8c}img{max-width:100%;height:auto;background:white;border-radius:10px}table{display:block;overflow-x:auto;max-width:100%;border-collapse:collapse;font-size:.86rem;margin:20px 0}th,td{border-bottom:1px solid #d5dfe9;padding:9px 11px;text-align:left;vertical-align:top}th{background:#e6eef5}code{font-size:.85em;overflow-wrap:anywhere}pre{overflow:auto;background:#e6eef5;padding:16px}nav{display:flex;gap:18px;flex-wrap:wrap;border-bottom:1px solid #d5dfe9;padding-bottom:16px;font-size:.9rem}p{max-width:100ch}</style></head><body><nav><a href="index.html">Overall comparison</a><a href="functions.html">Functions and load</a><a href="three_model_reference.html">Original three-model reference</a><a href="'''+REPO+'">Repository and evidence</a></nav><main>'+body+'</main></body></html>\n'


def expand(text, parts):
    for _ in range(4):
        if '{{' not in text:
            return text
        text = re.sub(r'\{\{([A-Z_]+)\}\}', lambda m: parts[m[1]].rstrip(), text)
    assert '{{' not in text, 'Unexpanded report field'
    return text


def build():
    source = repo_file('overall_expanded_2026-10-16/summary.json', root=ROOT)
    assert source.exists(), 'Build the combined October 16 analysis first'
    s = json.loads(source.read_text())
    assert not s['pending_model_ids'], 'Do not publish an unfinished model expansion'
    assert s['model_count']==22 and s['publication']['ranked_model_count']==19
    all_models = s['models']
    publication = s['publication']
    models = {m:all_models[m] for m in publication['eligible_model_ids']}
    order = sorted(models, key=lambda m: -models[m]['primary']['correct'])
    added = [m for m in s['added_model_ids'] if m in models]
    native = NATIVE + tuple(s['native_added_model_ids'])
    families = {f['family_id']: f for f in s['by_family']}
    parts = {}
    parts['MODEL_COUNT'] = str(len(models))
    parts['TEST_CONTEXT'] = (f"The main comparison contains **{len(models)} services × 1,136 questions = {len(models)*1136:,} scored model-question cases**. "
        +f"{len(all_models)} services were tested in total ({len(all_models)*1136:,} cases). Haiku, DeepSeek and Phi-4 are retained in the [output-compliance diagnostics](OUTPUT_COMPLIANCE.md), outside the main ranking because at least 5% of their first outputs failed the decision-only contract. "
        +f"**Added October 16, 2026:** {', '.join(models[m]['label'] for m in added)}. These results are included in the main ranking, function tables and graphics, not isolated as a separate pilot. "
        +"The original eleven services were tested on October 15 and their saved results are unchanged. "
        +"Microsoft uses OpenRouter/Azure; Nimble uses Bespoke's direct API; the regular LLM additions use separately pinned OpenRouter backends. Different dates, routes and provider load limit speed comparisons, even with the same client timer.")
    def count(model, fid):
        f = families[fid]
        return f"{f['models'][model]['correct']}/{f['n']}"
    def pair(a, b):
        p = next(p for p in s['pairwise'] if {p['a'], p['b']} == {a, b})
        return p
    j13, j14, ld, lr = (models[m] for m in (*NATIVE, 'openai/gpt-6-luna'))
    best = models[order[0]]
    regular_order = [m for m in order if m not in native]
    best_regular = models[regular_order[0]]
    parts['LEAD_RESULTS'] = (f"**{best['label']} now leads the expanded comparison at {best['primary']['correct']}/1,136 ({pct(best['primary']['correct'],1136)})**. "
        f"Jev 1.14 scored **{j14['primary']['correct']} ({pct(j14['primary']['correct'],1136)})**, Jev 1.13 **{j13['primary']['correct']} ({pct(j13['primary']['correct'],1136)})**, "
        +f"and Luna Decisions **{ld['primary']['correct']} ({pct(ld['primary']['correct'],1136)})**. "
        +f"The strongest regular LLM under this decision-only contract was **{best_regular['label']}: {best_regular['primary']['correct']} ({pct(best_regular['primary']['correct'],1136)})**. "
        +"The tables separate correct choices, wrong choices and outputs that could not be used as decisions.")
    parts['RESULTS'] = table(['Model', 'Correct / 1,136', 'Accuracy', 'Core correct', 'Wrong valid', 'Unanswered', 'Full-bank median', 'p95', 'Test date'], [
        [models[m]['label'], models[m]['primary']['correct'], pct(models[m]['primary']['correct'],1136),
         f"{models[m]['by_role']['core']['correct']}/640", models[m]['primary']['wrong'], models[m]['primary']['unanswered'],
         f"{models[m]['latency_first_all']['median_ms']:.0f} ms", f"{models[m]['latency_first_all']['p95_ms']:.0f} ms", ', '.join(models[m]['dates_toronto'])] for m in order])
    parts['COSTS'] = table(['Model', 'Cost for 1,136', 'Normalized cost per 1,000', 'Attempts missing cost', 'Cost basis'], [
        [models[m]['label'], f"${models[m]['cost_all_attempts']['known_usd']:.8f}", f"${models[m]['known_usd_per_1000_questions']:.8f}",
         models[m]['cost_all_attempts']['missing_attempts'],'Token usage × tariff' if models[m].get('cost_basis','').startswith('Usage') else 'API-reported'] for m in order])
    cost = publication['ranked_accounted_cost']
    parts['COST_CONTEXT'] = (f"The selected {len(models)} runs account for **${cost['known_usd']:.9f} combined**. "
        f"{cost['missing_attempts']} attempts have unknown charges. API-returned charges and calculations from input-token usage and a published tariff are distinguished; neither is a statement of an independently reconciled invoice. "
        f"All {len(all_models)} tested runs, including the three unranked diagnostics, account for ${s['total_selected_accounted_cost']['known_usd']:.9f} in known charges or tariff calculations. "
        "Mercury's captured tariff had an 80% promotional discount. Its cost advantage is specific to that price.")
    parts['ADDITIONS_ANALYSIS'] = (repo_file('addition_analysis.md', root=ROOT)).read_text()+'\n'+(repo_file('regular_additions_analysis.md', root=ROOT)).read_text()
    p = pair('openai/gpt-6-luna', 'luna_decisions')
    parts['LUNA_COMPARISON'] = (f"Regular Luna answered **727/1,136** correctly, compared with **{ld['primary']['correct']}/1,136** for Luna Decisions. "
        f"Its core score was 431/640, compared with {ld['by_role']['core']['correct']}/640. "
        f"They agreed on {p['same_choice_on_both_answered']} of the {p['both_answered']} questions both answered "
        f"({pct(p['same_choice_on_both_answered'],p['both_answered'])}). Similar aggregate scores do not mean they made the same decisions.\n\n"
        f"The speed trade-off matters. The full-bank median was **{ld['latency_first_all']['median_ms']:.0f} ms for Luna Decisions**, "
        "compared with 942 ms for regular Luna and 534 ms for Mercury. All three were tested on October 15 with the same response-body timing method, "
        "although Decisions was measured in a later session and uses a different request interface. "
        f"Regular Luna also cost less in reported charges: $0.03431990 versus ${ld['cost_all_attempts']['known_usd']:.8f} for Decisions, "
        f"whose {ld['cost_all_attempts']['missing_attempts']} failed attempts omitted charges. Mercury scored 25 more questions correctly than Decisions, "
        "with roughly twice its median response time in this short-output test, but about one-third of its known reported cost.")
    parts['LUNA_FUNCTIONS'] = ("The direction of the difference depends on the function. Regular Luna versus Luna Decisions scored "
        +', '.join(f"{count('openai/gpt-6-luna',f)} versus {count('luna_decisions',f)} on {name}" for f,name in [
            ('F02','forward implications'),('F04','Boolean scope'),('F23','rule verification'),('F24','source authority')])+'. '
        +f"On belief tracking, Luna Decisions scored {count('luna_decisions','F17')} versus regular Luna's {count('openai/gpt-6-luna','F17')}; "
        +f"on supplied-candidate checks, {ld['panels']['candidate_checks']['correct']}/80 versus {lr['panels']['candidate_checks']['correct']}/80. "
        +"These services expose different identities and request interfaces, so differences cannot be attributed to the interface alone.")
    parts['COMMON_HARD'] = (f"No model is dependable on sequential procedure execution: the best strict result is "
        f"{max(families['F13']['models'][m]['correct'] for m in models)}/42. "
        f"The best exact truth-counting result is {max(families['F09']['models'][m]['correct'] for m in models)}/65. "
        "Object tracking through repeated swaps and truth-teller consistency also remain substantial weaknesses. "
        "A typed answer, a short response or a low price does not remove the need to check exact state transitions and counts.\n\n"
        f"Jev 1.14 scored {count('jev114','F08')} on assignments, {count('jev114','F17')} on belief tracking, "
        f"and {count('jev114','F20')} on planning with preconditions. "
        +f"It answered every sampled question correctly in {sum(f['models']['jev114']['correct']==f['n'] for f in s['by_family'])} families: "
        +', '.join(f['family'].lower() for f in s['by_family'] if f['models']['jev114']['correct']==f['n'])+'. '
        +f"Its {count('jev114','F07')} scheduling result "
        f"and {count('jev114','F13')} procedural result show why its bounded-deduction strengths should not be described as general reliability.\n\n"
        f"There are {publication['none_of_ranked_models_correct']} questions that none of the {len(models)} ranked models answered correctly under the strict primary rules. "
        "Their IDs remain private for a possible later key and wording audit. This count does not establish that their reference answers are wrong; the original key is unchanged.")
    comparison = pair('jev113','jev114')
    corrected = comparison['only_b_correct'] if comparison['a']=='jev113' else comparison['only_a_correct']
    lost = comparison['only_a_correct'] if comparison['a']=='jev113' else comparison['only_b_correct']
    parts['VERSION_RESULTS'] = (f"The overall text difference is **{j14['primary']['correct']-j13['primary']['correct']:+d} correct answers**, "
        f"from {pct(j13['primary']['correct'],1136)} to {pct(j14['primary']['correct'],1136)}. "
        +"The clearest gains remain assignments and spatial tracking, but the new run no longer shows a scheduling gain.\n\n"
        +table(['Function','Jev 1.13','Jev 1.14','Change in correct answers'], [[name,count('jev113',fid),count('jev114',fid),f"{families[fid]['models']['jev114']['correct']-families[fid]['models']['jev113']['correct']:+d}"] for fid,name in [
            ('F08','One-to-one assignments'),('F15','Verbal spatial tracking'),('F07','Scheduling'),('F09','Exact truth counting'),
            ('F13','Sequential procedures'),('F12','Object tracking through swaps'),('F17','Belief tracking')]])+'\n'
        +f"Across individual questions, 1.14 corrected {corrected} cases that 1.13 did not answer correctly, and lost {lost} cases that 1.13 answered correctly. "
        +"Improvement is not uniform. "+'; '.join(f"{name}: {count('jev113',fid)} versus {count('jev114',fid)}" for fid,name in [
            ('F19','Exceptions and priority rules'),('F14','temporal intervals')])+'. '
        +f"On changed-evidence pairs, the counts with both answers correct were {j13['panels']['contrast']['both_correct']}/25 and {j14['panels']['contrast']['both_correct']}/25. "
        +"A version upgrade should therefore be checked against the tasks an application actually uses.")
    parts['PROCEDURE_CROSSOVER'] = (f"The text bank also shows why totals do not describe every function: Qwen answered 11/42 procedural questions correctly, "
        f"versus Jev 1.14's {count('jev114','F13')}. Neither result is dependable.")
    parts['PANELS'] = table(['Model','All rotations correct','Consistent / complete panels','Both evidence answers correct','Candidate checks correct','All five checks correct'], [
        [models[m]['label'],f"{models[m]['panels']['rotation']['all_correct']}/25",f"{models[m]['panels']['rotation']['consistent']}/{models[m]['panels']['rotation']['complete']}",
         f"{models[m]['panels']['contrast']['both_correct']}/25",f"{models[m]['panels']['candidate_checks']['correct']}/80",f"{models[m]['panels']['candidate_checks']['all_checks_correct']}/16"] for m in order])
    parts['FORMAT'] = table(['Model','Strict correct','Leading-ID correct','Invalid first output','First provider/transport failures','Recovery attempts','Eventual correct'], [
        [models[m]['label'],models[m]['primary']['correct'],models[m]['format_sensitivity_POSTHOC']['leading_id_correct'],s['output_compliance'][m]['model_output_failures'],
         s['output_compliance'][m]['provider_transport_failures'],models[m]['recovery_attempts'],models[m]['eventual']['correct']] for m in order if m not in native])
    parts['NATIVE_OUTCOMES'] = table(['Decisions service','Usable first choices','First transport/HTTP failures','Probability warnings','Recovery attempts','Eventual correct'], [
        [models[m]['label'],models[m]['primary']['answered'],models[m]['statuses_first'].get('http_failure',0),models[m]['primary']['probability_warnings'],
         models[m]['recovery_attempts'],models[m]['eventual']['correct']] for m in native])
    parts['CONFIDENCE'] = table(['Confidence cutoff']+[models[m]['label'] for m in native], [
        [f'≥{cutoff:g}']+[f"{next(x for x in models[m]['confidence'] if x['threshold']==cutoff)['correct']}/{next(x for x in models[m]['confidence'] if x['threshold']==cutoff)['attempted']} "
          f"({pct(next(x for x in models[m]['confidence'] if x['threshold']==cutoff)['attempted'],1136)} coverage)" for m in native] for cutoff in (.8,.9,.95)])
    parts['REPEAT'] = table(['Service','Previous correct / 1,136','Fresh correct / 1,136','Previously unsuccessful now correct','Previously correct now unsuccessful'], [
        [models[m]['label'],s['repeat_comparison'][m]['previous_primary']['correct'],models[m]['primary']['correct'],
         s['repeat_comparison'][m]['old_to_new']['only_b_correct'],s['repeat_comparison'][m]['old_to_new']['only_a_correct']] for m in NATIVE])
    parts['REPEAT_ANALYSIS'] = ("The ranking is unchanged, but Jev 1.14's margin over 1.13 narrowed from 22 to 10 correct answers "
        "(about 0.9 percentage points in the fresh run). The version improvement is therefore smaller than the first comparison suggested. "
        "Assignments and spatial tracking still improve; scheduling is now tied, while sequential procedure execution is worse.\n\n"
        f"Luna Decisions fell from 687 to {ld['primary']['correct']} correct, with 33 first-attempt HTTP failures versus 23 unanswered cases in the previous selected results. "
        "Both views contain 426 wrong valid choices, but individual answers changed in both directions. Earlier retry rules also differed, "
        "so the lower total is not an isolated measurement of model intelligence. Five of the 33 failed first attempts recovered on the permitted retry; "
        "the eventual score was 680/1,136. The main comparison keeps the stricter 677/1,136 first-attempt result, as it does for every ranked model.")
    parts['SESSIONS'] = table(['Session','Toronto start','Toronto finish'], [
        [label]+[datetime.fromisoformat(s['sessions_utc'][key][field]).astimezone(ZoneInfo('America/Toronto')).strftime('%Y-%m-%d %H:%M:%S') for field in ('started','completed')]
        for key,label in [('eight_regular_llms','Eight regular LLMs'),('three_decisions','Original three Decisions services')]+[(m,models[m]['label']) for m in added]])
    parts['IDENTITIES'] = table(['Service','Returned identities and counts','Backend tag','Toronto dates'], [
        [models[m]['label'],'; '.join('`'+k+'` ('+str(v)+')' for k,v in models[m]['identities'].items()),models[m]['provider_tag'],', '.join(models[m]['dates_toronto'])] for m in order])
    companion = json.loads((repo_file('expansion_2026-10-15/companion_images.json', root=ROOT)).read_text())
    names = {'typesafe/jev-1.14':'Jev 1.14','openai/gpt-6-luna-decisions':'Luna Decisions','openai/gpt-6-luna':'Luna regular','openai/gpt-5.4-nano':'GPT-5.4 nano','google/gemini-2.5-flash-lite':'Gemini 2.5 Flash-Lite'}
    parts['IMAGES'] = table(['Image configuration','Correct / 200','Accuracy','Median full reply','Known actual 200-question cost'], [
        [names[m],v['correct_first'],pct(v['correct_first'],200),f"{v['latency_first_all_ms']['median']:.0f} ms",f"${v['core_cost']['reported_usd']:.8f}"+('*' if v['core_cost']['missing_records'] else '')] for m,v in companion['models'].items()])+'\nAn asterisk marks missing error charges. These are actual 200-question costs; the image repo’s per-1,000 chart remains a separately labelled normalization.\n'
    parts['ANALYSIS'] = (repo_file('report_sections.md', root=ROOT)).read_text()
    text = expand((repo_file('report_layout.md', root=ROOT)).read_text(), parts)
    assert 'historical' not in text.lower()
    (repo_file('README.md', root=ROOT)).write_text(text)
    functions = f'# Results by function and load level\n\nThe [main report](README.md) compares {len(models)} eligible services tested October 15 and 16. All cells below use strict first-attempt results. The same output-compliance inclusion rule applies to every table; the three excluded runs remain in the [diagnostics](OUTPUT_COMPLIANCE.md).\n\n'+(repo_file('task_examples.md', root=ROOT)).read_text()+'\n## All 25 functions\n\n'
    functions += table(['Function','n']+[models[m]['label'] for m in order], [[f['family'],f['n']]+[f"{f['models'][m]['correct']} ({pct(f['models'][m]['correct'],f['n'])})" for m in order] for f in s['by_family']])
    for field,heading in [('by_role','Core and related item types'),('by_level','Engineered load levels')]:
        functions += '## '+heading+'\n\n'+table(['Group','n']+[models[m]['label'] for m in order], [
            [v,models[order[0]][field][v]['attempted']]+[f"{models[m][field][v]['correct']} ({pct(models[m][field][v]['correct'],models[m][field][v]['attempted'])})" for m in order] for v in models[order[0]][field]])
    (repo_file('FUNCTIONS.md', root=ROOT)).write_text(functions.rstrip()+'\n')
    diagnostics = expand((repo_file('output_compliance_layout.md', root=ROOT)).read_text(),{
        'EXCLUDED_RESULTS':table(['Unranked diagnostic','Usable / 1,136','Model-output failures','Provider failures','Correct among usable','Strict full-bank result','Median','Known run cost'],[
            [all_models[m]['label'],all_models[m]['primary']['answered'],s['output_compliance'][m]['model_output_failures'],
             s['output_compliance'][m]['provider_transport_failures'],
             f"{all_models[m]['primary']['correct']}/{all_models[m]['primary']['answered']} ({pct(all_models[m]['primary']['correct'],all_models[m]['primary']['answered'])})",
             f"{all_models[m]['primary']['correct']}/1,136 ({pct(all_models[m]['primary']['correct'],1136)})",
             f"{all_models[m]['latency_first_all']['median_ms']:.0f} ms",f"${all_models[m]['cost_all_attempts']['known_usd']:.8f}"] for m in publication['excluded_model_ids']])})
    (repo_file('OUTPUT_COMPLIANCE.md', root=ROOT)).write_text(diagnostics)
    for path in (repo_file('figures', root=ROOT)).iterdir():
        shutil.copyfile(path, repo_file('docs/figures', root=ROOT)/path.name)
    (repo_file('docs/index.html', root=ROOT)).write_text(render(text,f'{len(models)} models on 1136 text decisions'))
    (repo_file('docs/functions.html', root=ROOT)).write_text(render(functions,'Text decision results by function and load'))
    (repo_file('docs/output_compliance.html', root=ROOT)).write_text(render(diagnostics,'Output compliance diagnostics'))
    print('Built overall README, function tables and Pages; original evidence preserved')


if __name__ == '__main__':
    build()
