"""Preserve curated v4 notes and graph ordering for the Prism update."""
import hashlib, json, re, sys
from decimal import Decimal
from pathlib import Path

repo=Path(__file__).resolve().parents[1]
out=Path(sys.argv[1]).resolve()
prior=repo/'results/releases/system1_v4_local_screens_curated_2026-11-04'
name='system1_v4_prism_2026-11-05'
page=(out/'report.html').read_text();old=(prior/'report.html').read_text()
recoveries=json.loads((out/'model_collection_recoveries.json').read_text())
failed=sum(len(x.get('failed_attempts',[])) for x in recoveries if x.get('model_id')=='sarvam_prism')
cost=json.loads((out/'cost_statistics.json').read_text())['models']['sarvam_prism']
inr=Decimal(cost['known_subtotal_usd'])*Decimal(90)
cost_text=(f'Prism’s selected answers used an estimated ₹{inr:.6f} in input-token charges, '
           'using the published ₹4 per million input tokens; USD comparisons use Sarvam’s illustrative ₹90 per USD. '
           f'This is an estimate, excluding tax and charges for failed requests, not a billing receipt. '
           f'{failed} no-answer transient failures preceded selected answers; their latency and retry waits are excluded from response times.')
anchor='<section id="cost"><h2>Cost evidence and missing charges</h2>';assert page.count(anchor)==1
page=page.replace(anchor,anchor+'<p>'+cost_text+'</p>',1)
notes=''.join(re.search(r'<div class="note" data-incomplete-model="'+ident+r'">.*?</div>',old).group() for ident in ('strike-1','hanzo-kai'))
anchor='</ul></section><section id="legend">';assert page.count(anchor)==1
page=page.replace(anchor,'</ul>'+notes+'</section><section id="legend">',1)
local=re.search(r'<section id="local-screens">.*?</section>',old).group()
anchor='<section id="legend">';assert page.count(anchor)==1;page=page.replace(anchor,local+anchor,1)
chart=re.search(r'<h3>Accuracy</h3><div class="chart-scroll">.*?</div>',page).group()
page=page.replace(chart,'',1);anchor='<label>Find a model <input id="model-search"';assert page.count(anchor)==1;page=page.replace(anchor,chart+anchor,1)
selection=re.search(r'<p class="note"><strong>Selection bias:</strong>.*?</p>',page).group()
page=page.replace(selection,'',1);anchor='<section id="method"><h2>Method, provenance and downloads</h2>';assert page.count(anchor)==1;page=page.replace(anchor,anchor+selection,1)
sage=re.search(r'<p><strong>Levanto Sage 2:</strong>.*?</p>',old).group()
anchor='<details><summary>Additional accuracy and coverage measures</summary>';assert page.count(anchor)==1;page=page.replace(anchor,sage+anchor,1)
(out/'report.html').write_text(page)

readme=(out/'README_V4.md').read_text();old=(prior/'README_V4.md').read_text()
anchor='\nOperational accuracy counts unusable requests';assert readme.count(anchor)==1
readme=readme.replace(anchor,'\n**Prism cost and retries:** '+cost_text+'\n\nOperational accuracy counts unusable requests',1)
selection=re.search(r'\*\*Selection bias:\*\*[^\n]+\n\n',readme).group();readme=readme.replace(selection,'',1)
chart=re.search(r'### Accuracy\n\n!\[Accuracy comparison for the qualifying models\]\([^\n]+\)\n\n',readme).group();readme=readme.replace(chart,'',1)
anchor='## Main comparison\n\n';assert readme.count(anchor)==1;readme=readme.replace(anchor,anchor+chart,1)
notes=old[old.index('**Strike 1 — incomplete'):old.index('## Download and reproducibility')].replace(prior.name,name)
anchor='## Download and reproducibility';assert readme.count(anchor)==1;readme=readme.replace(anchor,notes+anchor,1)
sage=re.search(r'\*\*Sage 2 response detail:\*\*[^\n]+',old).group()
anchor='\nOperational accuracy counts unusable requests';assert readme.count(anchor)==1;readme=readme.replace(anchor,'\n'+sage+'\n\nOperational accuracy counts unusable requests',1)
(out/'README_V4.md').write_text(readme)

sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
manifest=json.loads((out/'manifest.json').read_text());manifest['prior_curated_manifest_sha256']=sha(prior/'manifest.json')
manifest['files_sha256']={str(p.relative_to(out)):sha(p) for p in sorted(out.rglob('*')) if p.is_file() and p.name!='manifest.json'}
(out/'manifest.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n')
print('Restored curated partial-screen notes, chart order, and lower-page selection context.')
