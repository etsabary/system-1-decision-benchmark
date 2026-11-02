"""Create a presentation-only v4 successor documenting the stopped Kai test."""
import argparse,hashlib,json,re,shutil
from pathlib import Path

REPO=Path(__file__).resolve().parents[1]
SOURCE=REPO/'results/releases/system1_v4_hosted_2026-11-02'
NAME='system1_v4_kai_note_2026-11-02'
parser=argparse.ArgumentParser()
parser.add_argument('--output',type=Path,required=True)
args=parser.parse_args();out=args.output.resolve()
if out.exists() or out==SOURCE.resolve() or SOURCE.resolve() in out.parents:raise SystemExit('Destination must be new and outside the frozen source release')
shutil.copytree(SOURCE,out)
partial=json.loads((out/'partial_models.json').read_text())
assert len(partial)==1
x=partial[0]
assert x['model']=='Hanzo Kai 1.9' and x['sample_n']==244 and x['sample_correct']==46 and x['subq_correct_on_same_inputs']==190 and x['provider_extrapolated_count']==31

case='''# Hanzo Kai: stopped partial evaluation

The user stopped this evaluation after 244 of the 2,157 v4 questions. Kai answered **46/244 correctly (18.85%)**. On those exact questions, SubQ Snap 1.1 answered **190/244 correctly (77.87%)**. Uniform guessing over the supplied option counts would have yielded about 49 correct answers on average. The questions were selected by an answer-blind seeded shuffle, but the incomplete sample is not stratified.

**This is a partial result, not a 2,157-question score or a determination that Kai would fall below the 62% full-bank cutoff.** It is shown beside the below-cutoff catalogue at the user's request and is excluded from the full-bank statistics, graphs and ranks. The benchmark has known question-selection and source-key limitations described in the main report.

The Hanzo API initially allowed 50 answers before returning a free-plan daily limit. After the user purchased prepaid credits, testing resumed; after 244 valid answers in total, the API reported that an eight-hour usage window was exhausted. The account's reported tier remained Free and the provider indicated a reset at 3:00 a.m. Toronto time on November 2, 2026. The user then directed that testing stop. The top-up purchased credit; this does not establish that the entire purchase was consumed by these requests.

The model catalogue labeled the alias Kai 1.7, while the actual responses identified checkpoint **kai-1.9** and a consistent weights hash and calibration. The API marked **31 of the 244 inputs** as exceeding the model's stated training length; this signal does not by itself establish truncation. Request timing came from sessions with different concurrency, so the partial sample is not a controlled speed comparison.

The original first answers and no-answer errors remain in the private run evidence; no further Kai inference was performed after the user's instruction. Aggregate sample data is in [partial_models.json](partial_models.json).
'''
(out/'KAI_CASE_NOTE.md').write_text(case)
html=(out/'report.html').read_text()
start=html.index('<section id="partial">');end=html.index('</section>',start)+len('</section>')
assert '46/244' in html[start:end] and '190/244' in html[start:end]
html=html[:start]+html[end:]
anchor=html.index('<h3>Below the 62% cutoff</h3>');end=html.index('</ul></section>',anchor)+len('</ul>')
note='''<div class="note" data-incomplete-model="hanzo-kai"><strong>Hanzo Kai 1.9 — stopped partial test:</strong> 46/244 correct (18.85%); SubQ scored 190/244 (77.87%) on those same inputs. <strong>This is not a full-bank score or a 62% cutoff classification.</strong> Hanzo first stopped after 50 free answers. After prepaid credits were purchased, it allowed further calls but then imposed an eight-hour usage limit. The user stopped testing. The provider marked 31 inputs beyond its stated training length. <a href="KAI_CASE_NOTE.md">Usage limits, method and result details</a> · <a href="partial_models.json">Partial-test data</a>.</div>'''
html=html[:end]+note+html[end:]
(out/'report.html').write_text(html)

readme=(out/'README_V4.md').read_text()
old='''## Incomplete exploratory tests

- Hanzo Kai 1.9: 46/244 correct on a seeded incomplete subset; SubQ scored 190/244 on the same inputs. This partial result is not included in the full-bank ranking.

'''
assert readme.count(old)==1;readme=readme.replace(old,'')
anchor='\n## Download and reproducibility\n'
assert readme.count(anchor)==1
summary='''
**Hanzo Kai 1.9 — stopped partial test:** 46/244 correct (18.85%); SubQ scored 190/244 (77.87%) on the same inputs. This is an incomplete sample, not a full-bank score or a 62% cutoff classification. Hanzo first limited the free run to 50 answers, then imposed an eight-hour usage window after prepaid credits were purchased. The user stopped testing. The API marked 31 inputs beyond its stated training length. [Usage limits and method](results/releases/'''+NAME+'''/KAI_CASE_NOTE.md).
'''
readme=readme.replace(anchor,'\n'+summary+anchor)
readme=readme.replace('results/releases/system1_v4_hosted_2026-11-02/','results/releases/'+NAME+'/')
(out/'README_V4.md').write_text(readme)

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
manifest=json.loads((SOURCE/'manifest.json').read_text())
manifest['frozen_hosted_manifest_sha256']=digest(SOURCE/'manifest.json')
manifest['presentation_note']='Hanzo Kai partial result placed beside the below-cutoff catalogue; the full-bank data, graphs and model selection remain unchanged.'
manifest['files_sha256']={str(p.relative_to(out)):digest(p) for p in sorted(out.rglob('*')) if p.is_file() and p.name!='manifest.json'}
(out/'manifest.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n')
print(json.dumps({'output':str(out),'note':'KAI_CASE_NOTE.md','sample':'46/244','full_bank_models':manifest['measured_models'],'graphs_unchanged':True}))
