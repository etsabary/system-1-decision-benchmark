"""Restore curated notes and graph order for the Super Decider addition."""
import hashlib,json,re,sys
from decimal import Decimal
from pathlib import Path

repo=Path(__file__).resolve().parents[1];out=Path(sys.argv[1]).resolve()
prior=repo/'results/releases/system1_v4_prism_2026-11-05';name='system1_v4_super_decider_2026-11-05'
page=(out/'report.html').read_text();old=(prior/'report.html').read_text()
notes=''.join(re.search(r'<div class="note" data-incomplete-model="'+ident+r'">.*?</div>',old).group() for ident in ('strike-1','hanzo-kai'))
anchor='</ul></section><section id="legend">';assert page.count(anchor)==1
page=page.replace(anchor,'</ul>'+notes+'</section><section id="legend">',1)
local=re.search(r'<section id="local-screens">.*?</section>',old).group();anchor='<section id="legend">';assert page.count(anchor)==1;page=page.replace(anchor,local+anchor,1)
chart=re.search(r'<h3>Accuracy</h3><div class="chart-scroll">.*?</div>',page).group();page=page.replace(chart,'',1)
anchor='<label>Find a model <input id="model-search"';assert page.count(anchor)==1;page=page.replace(anchor,chart+anchor,1)
selection=re.search(r'<p class="note"><strong>Selection bias:</strong>.*?</p>',page).group();page=page.replace(selection,'',1)
anchor='<section id="method"><h2>Method, provenance and downloads</h2>';assert page.count(anchor)==1;page=page.replace(anchor,anchor+selection,1)
sage=re.search(r'<p><strong>Levanto Sage 2:</strong>.*?</p>',old).group();anchor='<details><summary>Additional accuracy and coverage measures</summary>';assert page.count(anchor)==1;page=page.replace(anchor,sage+anchor,1)
prism=re.search(r'<p>Prism’s selected answers.*?</p>',old).group()
cost=json.loads((out/'cost_statistics.json').read_text())['models']['super_decider']
value=Decimal(cost['known_subtotal_usd'])
new=(f'Super Decider’s selected answers have an estimated ${value:.6f} input-token cost at the product page’s $0.03 per million input tokens. '
     'The account catalogue labelled this model Free; the actual charge was not reported, so that estimate may not apply. '
     'Thinking off was requested, but the response does not independently attest the effective setting. '
     'Selected-answer timings exclude any failed requests and retry waits.')
anchor='<section id="cost"><h2>Cost evidence and missing charges</h2>';assert page.count(anchor)==1;page=page.replace(anchor,anchor+prism+'<p>'+new+'</p>',1)
(out/'report.html').write_text(page)

readme=(out/'README_V4.md').read_text();old=(prior/'README_V4.md').read_text()
selection=re.search(r'\*\*Selection bias:\*\*[^\n]+\n\n',readme).group();readme=readme.replace(selection,'',1)
chart=re.search(r'### Accuracy\n\n!\[Accuracy comparison for the qualifying models\]\([^\n]+\)\n\n',readme).group();readme=readme.replace(chart,'',1)
anchor='## Main comparison\n\n';assert readme.count(anchor)==1;readme=readme.replace(anchor,anchor+chart,1)
notes=old[old.index('**Strike 1 — incomplete'):old.index('## Download and reproducibility')].replace(prior.name,name)
anchor='## Download and reproducibility';assert readme.count(anchor)==1;readme=readme.replace(anchor,notes+anchor,1)
sage=re.search(r'\*\*Sage 2 response detail:\*\*[^\n]+',old).group();prism=re.search(r'\*\*Prism cost and retries:\*\*[^\n]+',old).group()
anchor='\nOperational accuracy counts unusable requests';assert readme.count(anchor)==1
readme=readme.replace(anchor,'\n'+sage+'\n\n'+prism+'\n\n**Super Decider cost and configuration:** '+new+'\n\nOperational accuracy counts unusable requests',1)
(out/'README_V4.md').write_text(readme)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
manifest=json.loads((out/'manifest.json').read_text());manifest['prior_prism_manifest_sha256']=sha(prior/'manifest.json')
manifest['files_sha256']={str(p.relative_to(out)):sha(p) for p in sorted(out.rglob('*')) if p.is_file() and p.name!='manifest.json'}
(out/'manifest.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n')
print('Restored curated notes and cost qualifications.')
