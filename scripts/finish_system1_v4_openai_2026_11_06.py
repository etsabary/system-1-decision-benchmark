"""Preserve curated v4 notes and add the OpenAI reference and native screen."""
import hashlib,html,json,re,sys
from pathlib import Path
repo=Path(__file__).resolve().parents[1];out=Path(sys.argv[1]).resolve()
prior=repo/'results/releases/system1_v4_super_decider_2026-11-05';name='system1_v4_openai_2026-11-06'
page=(out/'report.html').read_text();old=(prior/'report.html').read_text();stats=json.loads((out/'statistics.json').read_text());cost=json.loads((out/'cost_statistics.json').read_text())['models']['reference_terra61'];terra=stats['models']['reference_terra61'];luna=next(x for x in json.loads((out/'partial_models.json').read_text()) if x.get('provider_model_id')=='openai/gpt-6-luna-decisions')
notes=''.join(re.search(r'<div class="note" data-incomplete-model="'+ident+r'">.*?</div>',old).group() for ident in ('strike-1','hanzo-kai'))
native=(f'<div class="note" data-incomplete-model="luna-decisions-20261106"><strong>GPT-6 Luna Decisions — incomplete expansion test:</strong> '
        f'{luna["sample_correct"]}/{luna["sample_n"]} correct ({luna["sample_accuracy"]:.2%}) on new inputs only; {luna["sample_usable"]} usable. '
        f'The unchanged 1,342-question baseline remains 758 correct (56.48%). Of 815 added inputs, {luna["sample_n"]} were attempted before the below-50% stopping rule; {luna["unattempted_expansion_inputs"]} remain untested. '
        f'Median {luna["median_ms"]:.0f} ms; p95 {luna["p95_ms"]:.0f} ms. New-request charges total ${luna["reported_charge_usd"]} reported plus one unknown charge. '
        f'GPT-6.1 Terra answered {luna["terra_correct_on_same_inputs"]}/{luna["sample_n"]} of these exact inputs correctly. '
        'This is not a full-v4 score or a 62% classification. The native route and October 6 checkpoint match the original run; no scored retries. '
        '<a href="OPENAI_DECISIONS_NOTES.md">API changes, scope and costs</a>.</div>')
anchor='</ul></section><section id="legend">';assert page.count(anchor)==1;page=page.replace(anchor,'</ul>'+notes+native+'</section><section id="legend">',1)
local=re.search(r'<section id="local-screens">.*?</section>',old).group();page=page.replace('<section id="legend">',local+'<section id="legend">',1)
chart=re.search(r'<h3>Accuracy</h3><div class="chart-scroll">.*?</div>',page).group();page=page.replace(chart,'',1);page=page.replace('<label>Find a model <input id="model-search"',chart+'<label>Find a model <input id="model-search"',1)
selection=re.search(r'<p class="note"><strong>Selection bias:</strong>.*?</p>',page).group();page=page.replace(selection,'',1);anchor='<section id="method"><h2>Method, provenance and downloads</h2>';page=page.replace(anchor,anchor+selection,1)
sage=re.search(r'<p><strong>Levanto Sage 2:</strong>.*?</p>',old).group();page=page.replace('<details><summary>Additional accuracy and coverage measures</summary>',sage+'<details><summary>Additional accuracy and coverage measures</summary>',1)
oldcost=''.join(re.search(pattern,old).group() for pattern in [r'<p>Prism’s selected answers.*?</p>',r'<p>Super Decider’s selected answers.*?</p>'])
terranote=(f'GPT-6.1 Terra was run with reasoning disabled on all 2,157 inputs. All {terra["valid"]:,} successful responses reported zero reasoning tokens and no reasoning text. '
           f'Its API-reported charges total ${cost["reported_subtotal_usd"]}; {cost["unknown_count"]} client DNS failures have no charge telemetry. '
           'Those unsuccessful primaries remain in the denominator and timing distribution; they were never retried or replaced. Only the unattempted inputs resumed after connectivity recovered. '
           'The checkpoint is October 26, 2026, using OpenAI standard service through OpenRouter. Existing GPT-6 Sol results remain unchanged.')
anchor='<section id="cost"><h2>Cost evidence and missing charges</h2>';page=page.replace(anchor,anchor+oldcost+'<p><strong>GPT-6.1 Terra:</strong> '+html.escape(terranote)+'</p>',1)
page=page.replace('<p>Provider model declarations are not independent attestations of hidden weights.','<p><a href="OPENAI_DECISIONS_NOTES.md">OpenAI native Decisions update and test scope</a>; <a href="luna_partial_timing.csv.gz">Luna partial timing</a>; <a href="luna_partial_cost.csv.gz">Luna partial cost</a>; <a href="luna_partial_category_scores.csv">Luna partial categories</a>.</p><p>Provider model declarations are not independent attestations of hidden weights.',1)
(out/'report.html').write_text(page)

readme=(out/'README_V4.md').read_text();oldmd=(prior/'README_V4.md').read_text();selection=re.search(r'\*\*Selection bias:\*\*[^\n]+\n\n',readme).group();readme=readme.replace(selection,'',1)
chart=re.search(r'### Accuracy\n\n!\[Accuracy comparison for the qualifying models\]\([^\n]+\)\n\n',readme).group();readme=readme.replace(chart,'',1);readme=readme.replace('## Main comparison\n\n','## Main comparison\n\n'+chart,1)
oldnotes=oldmd[oldmd.index('**Strike 1 — incomplete'):oldmd.index('## Download and reproducibility')].replace(prior.name,name)
native_md=(f'**GPT-6 Luna Decisions — incomplete expansion test:** {luna["sample_correct"]}/{luna["sample_n"]} ({luna["sample_accuracy"]:.2%}) on new inputs only, {luna["sample_usable"]} usable; stopped below 50%. '
           f'Median {luna["median_ms"]:.0f} ms, p95 {luna["p95_ms"]:.0f} ms. New-run reported cost ${luna["reported_charge_usd"]} plus one unknown charge. '
           f'Terra scored {luna["terra_correct_on_same_inputs"]}/{luna["sample_n"]} on the exact same inputs. '
           'The unchanged 1,342 baseline remains 758 correct (56.48%); this partial expansion is not a full-v4 score or ranked 62% classification. '
           f'[API changes, scope and costs](results/releases/{name}/OPENAI_DECISIONS_NOTES.md).\n\n')
anchor='## Download and reproducibility';readme=readme.replace(anchor,oldnotes+native_md+'## Method and limitations\n\n'+selection+anchor,1)
details='\n\n'.join(re.search(pattern,oldmd).group() for pattern in [r'\*\*Sage 2 response detail:\*\*[^\n]+',r'\*\*Prism cost and retries:\*\*[^\n]+',r'\*\*Super Decider cost and configuration:\*\*[^\n]+'])
readme=readme.replace('\nOperational accuracy counts unusable requests','\n'+details+'\n\n**GPT-6.1 Terra cost and configuration:** '+terranote+'\n\nOperational accuracy counts unusable requests',1)
readme=readme.replace('python3 scripts/validate_system1_v4_hosted.py results/releases/'+name+' results/releases/system1_v4_2026-11-02','python3 scripts/validate_system1_v4_openai_2026_11_06.py results/releases/'+name+' results/releases/'+prior.name)
(out/'README_V4.md').write_text(readme)
import csv
with (out/'all_category_scores.csv').open(newline='') as f:category_rows=list(csv.DictReader(f))
cat={(x['model_id'],x['family_id']):x for x in category_rows};sol=stats['models']['reference_sol'];deltas=[]
for fid in sorted({x['family_id'] for x in category_rows}):
 a=cat['reference_terra61',fid];b=cat['reference_sol',fid]
 deltas.append({'family_id':fid,'family':a['family'],'n':int(a['n']),'terra_correct':int(a['correct']),'sol_correct':int(b['correct']),'difference_correct':int(a['correct'])-int(b['correct']),'difference_percentage_points':100*(float(a['accuracy'])-float(b['accuracy']))})
comparison={'terra':{'correct':terra['correct'],'n':2157,'accuracy':terra['accuracy'],'median_ms':terra['median_ms'],'p95_ms':terra['p95_ms'],'reported_subtotal_usd':cost['reported_subtotal_usd'],'unknown_charges':cost['unknown_count']},'sol':{'correct':sol['correct'],'n':2157,'accuracy':sol['accuracy'],'median_ms':sol['median_ms'],'p95_ms':sol['p95_ms']},'difference_percentage_points':100*(terra['accuracy']-sol['accuracy']),'categories':deltas,'limits':'Descriptive same-bank comparison; configurations and collection dates differ. Category counts include dependent variants. Luna has a separate partial expansion denominator.'}
(out/'openai_comparison.json').write_text(json.dumps(comparison,indent=2,ensure_ascii=False)+'\n')
gains=sorted(deltas,key=lambda x:(-x['difference_percentage_points'],x['family_id']))[:3];losses=sorted(deltas,key=lambda x:(x['difference_percentage_points'],x['family_id']))[:3]
brief=(f'GPT-6.1 Terra scored {terra["correct"]}/2,157 ({terra["accuracy"]:.2%}), {comparison["difference_percentage_points"]:+.2f} percentage points relative to GPT-6 Sol’s {sol["accuracy"]:.2%}. '
       f'Median response time was {terra["median_ms"]:.0f} ms versus Sol’s {sol["median_ms"]:.0f} ms. These are descriptive results from separate collection sessions.')
def line(x):return f'{x["family"]}: Terra {x["terra_correct"]}/{x["n"]}, Sol {x["sol_correct"]}/{x["n"]} ({x["difference_percentage_points"]:+.1f} points)'
detail='<section id="openai-update"><h2>OpenAI reference comparison</h2><p>'+html.escape(brief)+'</p><p><strong>Largest category gains:</strong> '+html.escape('; '.join(map(line,gains)))+'.</p><p><strong>Smallest changes / largest deficits:</strong> '+html.escape('; '.join(map(line,losses)))+'.</p><p><a href="openai_comparison.json">All 43 category differences</a>. Luna Decisions is the separate incomplete native screen above.</p></section>'
page=page.replace('<section id="legend">',detail+'<section id="legend">',1);(out/'report.html').write_text(page)
readme=readme.replace('## Method and limitations\n\n','## OpenAI reference comparison\n\n'+brief+'\n\nLargest category gains: '+'; '.join(map(line,gains))+'.\n\nSmallest changes / largest deficits: '+'; '.join(map(line,losses))+f'. [All category differences](results/releases/{name}/openai_comparison.json).\n\n## Method and limitations\n\n',1);(out/'README_V4.md').write_text(readme)
text=(f'# OpenAI update and benchmark scope · November 6, 2026\n\n'
      'The [official Decisions guide](https://developers.openai.com/api/docs/guides/decisions) now documents general availability, prompt caching, JSON input, question-specific images, hosted images and up to 400 questions per request. Those are API feature changes; they do not establish improved model weights. GPT-6 Luna is still its only supported model. The native OpenRouter catalogue and live readiness response both identified `openai/gpt-6-luna-decisions-20261006`, matching the earlier test.\n\n'
      'A direct request to OpenAI’s `/v1/decisions` was rejected with HTTP 401 by the stored credential. The prior native OpenRouter Decisions route remained accessible and was used, pinned to OpenAI with no provider fallback. This is typed Decisions inference, not chat generation.\n\n'
      '## Luna Decisions · partial expansion\n\n'+native_md+
      'The historical 1,342 primaries were checked against the exact current request payload hashes and retained, including their 42 unsuccessful requests. Only the 815 added inputs were eligible for new inference. The new shuffle seed was fixed before responses. The stop was set after 180 new primaries; one already-running request settled, producing 181 total. One new HTTP 502 reported a provider refusal and is retained. There were no scored retries. Costs above cover the new partial session only; historical charges were not rebilled or included in that new subtotal. A missing charge is not assigned zero. The separate unscored native readiness request cost $0.000012 and is outside the benchmark counts and subtotal. This partial sample is not the full 815 additions or the 2,157-question v4 bank, and category coverage is unstratified.\n\n'
      '## GPT-6.1 Terra · full-bank reference\n\n'+terranote+'\n\n'
      'GPT-6.1 Terra is a regular LLM reference using the same one-option generation contract as the earlier Sol reference. It supports reasoning `none`; GPT-6.1 Sol does not. The [official model guide](https://developers.openai.com/api/docs/guides/latest-model) distinguishes these modes. Terra uses two concurrent requests and fresh HTTPS connections; timing includes connection and full-response overhead. The pooled median and p95 are recomputed from individual selected primaries.\n\n'
      'All prior complete-model measurements, frozen v4 questions, source rights and selection limitations remain unchanged. Historical dated releases remain available.\n')
(out/'OPENAI_DECISIONS_NOTES.md').write_text(text.replace('results/releases/'+name+'/',''))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();manifest=json.loads((out/'manifest.json').read_text());manifest['prior_super_decider_manifest_sha256']=sha(prior/'manifest.json');manifest['files_sha256']={str(p.relative_to(out)):sha(p) for p in sorted(out.rglob('*')) if p.is_file() and p.name!='manifest.json'};(out/'manifest.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n')
print('Preserved graph order, costs, historical notes and the separate native Decisions screen.')
