"""Present independently reviewed ASUS partial screens without altering full-bank evidence."""
import argparse,hashlib,html,json,re,shutil
from pathlib import Path
REPO=Path(__file__).resolve().parents[1];PRIOR=REPO/'results/releases/system1_v5_hosted_refresh_2026-11-13';NAME='system1_v5_asus_native_2026-11-13'
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();esc=lambda x:html.escape(str(x),quote=True)
p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True,help='Public-safe independently reviewed partial-screen data only');p.add_argument('--output',type=Path,required=True);a=p.parse_args();source=a.source.resolve();out=a.output.resolve();assert not out.exists() and out!=PRIOR and PRIOR not in out.parents and source not in out.parents
screens=read(source/'asus_native_screen_statistics.json');models=screens['models'];profiles=read(source/'asus_native_screen_profiles.json');audit=read(source/'asus_native_screen_audit.json');assert models and set(models)==set(profiles)==set(audit['models'])
assert all(m['n']==m['usable']==100 and m['full_bank_accuracy'] is None and m['full_bank_cutoff_classification'] is None and m['full_bank_rank'] is None and not m['continuation_authorized'] for m in models.values())
shutil.copytree(PRIOR,out)
for q in source.iterdir():
 assert q.is_file() and q.name.startswith('asus_native_screen_');assert not (out/q.name).exists();shutil.copyfile(q,out/q.name)
shutil.copyfile(PRIOR/'manifest.json',out/'parent_hosted_refresh_manifest.json')
intro=('These are separate 100-question screens on the fixed answer-blind shuffled v5 prefix, with unstratified category counts. '
       'They are not 1,456-question scores, full-bank rankings or classifications against the 45% cutoff. '
       'All 42 complete configurations, 34 active rankings, six below-cutoff results, two superseded versions, 61,152-record main ledgers, category tables and graphs remain byte-identical to the preceding hosted release. '
       'The same 100 inputs were used for each screen. No score was extrapolated to the unattempted 1,356 questions per model.')
method=('Each screen stopped at the predefined 100-question check because its Wilson 95% upper bound was below 45%. '
        'This is a sequential screening heuristic, not a formal repeated-look guarantee or a full-bank inclusion decision. '
        'All attempted answers were usable first primaries; there were no scored retries, errors, truncation or runtime-condition changes. '
        'All reported output counters were zero, with no generated reasoning text observed and no independent zero-generation attestation. '
        'QEV 0.5B reported abstained=true on five responses and QEV 1.3B on two, while returning valid typed choices; those choices are scored normally and the flags remain in the usage ledger. '
        'Local hardware and electricity are unmetered, not zero cost. Pooled individual latencies exclude idle pacing and do not measure sustained throughput.')
deployment=('The user confirmed one ASUS RTX 2060 running the publisher’s native PyTorch implementation with 4,096-token context and one resident model at a time. '
            'Server replies declared CUDA, reuse and stable runtime profiles. These declarations do not independently attest GPU execution, exact installed weights or source/conversion fidelity. '
            'QEV text/readout was declared FP32 with repeated-KV CUDA SDPA; unused vision weights retained BF16 storage. '
            'GS1 used its declared FP32 CUDA eager-reference runtime; its replies did not declare a backbone/version checkpoint, so none is inferred. '
            'These samples describe the ASUS-served FP32 configurations; the original BF16 runtime was not measured. '
            'The compact QEV 0.5B and 1.3B packages legitimately declare parent QEV 0.8B and 2B backbones; parent names are not a precision or installed-weight attestation. '
            'This is a separate native single-GPU configuration from earlier distributed GGUF/llama.cpp/RPC measurements.')
excluded=('Initial model loading, synthetic readiness and oversize checks, earlier 2,048-context per-request preflight, pre-score 4,096-context readiness cycles and the unscored monitor diagnostic are excluded. '
          'An unscored control test found that GET /props unloaded native weights; monitoring was changed to catalogue-only before any scored primary. '
          'Those earlier records remain separately archived. Source rights, frozen cohort-conditioned question selection, AQuA error-selection dependence and the unresolved original MAIQ item-rights caveat remain unchanged; the 120 companion diagnostics retain separate denominators.')
links=[('ASUS_NATIVE_SCREEN_NOTES.md','Screen method, stops and runtime limitations'),('asus_native_screen_statistics.json','Separate 100-question screen summaries'),('asus_native_screen_profiles.json','Server-declared runtime profiles and source hashes'),('asus_native_screen_timing.csv.gz','Partial-screen individual timing evidence'),('asus_native_screen_cost.csv.gz','Partial-screen unmetered cost evidence'),('asus_native_screen_correctness.csv.gz','Partial-screen correctness and usability booleans'),('asus_native_screen_usage.csv.gz','Partial-screen native usage and record hashes'),('asus_native_screen_audit.json','Partial-screen audit and review provenance'),('parent_hosted_refresh_manifest.json','Frozen full-bank parent manifest')]
BANDS=('#d8f1e8','#fff4c2','#ffe4ca','#fbdedd');BAND_NAMES=('Green','Yellow','Orange','Red');GRAY='#edf0f2'
def speed_band(ms):return 0 if ms<=250 else 1 if ms<=500 else 2 if ms<=1000 else 3
def speed_td(ms):
 band=speed_band(ms);return f'<td style="background:{BANDS[band]}" data-speed-band="{band}">{ms:.2f} ms<small>{BAND_NAMES[band]}</small></td>'
def metric(label,value,band=None,cost=False):
 bg=GRAY if band is None else BANDS[band];attr=' data-cost-band="unknown"' if cost else f' data-speed-band="{band}"' if band is not None else ''
 return f'<div style="background:{bg}"{attr}><span>{esc(label)}</span><strong>{esc(value)}</strong></div>'
headers=['Configuration','Correct / screen','Usable','Median','p95','Wilson 95% upper','Continuation','Cost']
rows=[];mdrows=[];cards=[]
for mid,m in models.items():
 rows.append('<tr data-asus-screen="'+esc(mid)+'"><td>'+esc(m['label'])+'</td><td>'+str(m['correct'])+'/100<small>'+f"{m['sample_accuracy']:.2%}"+' sample only</small></td><td>100/100</td>'+speed_td(m['median_ms'])+speed_td(m['p95_ms'])+'<td>'+f"{m['wilson95_upper']:.2%}"+'</td><td>Stopped; no full-bank classification</td><td style="background:'+GRAY+'" data-cost-band="unknown">Unmetered hardware / electricity</td></tr>')
 marks=['🟩','🟨','🟧','🟥'];mdrows.append(f"| {m['label']} | {m['correct']}/100 ({m['sample_accuracy']:.2%}, sample only) | 100/100 | {marks[speed_band(m['median_ms'])]} {m['median_ms']:.2f} ms | {marks[speed_band(m['p95_ms'])]} {m['p95_ms']:.2f} ms | {m['wilson95_upper']:.2%} | Stopped; no full-bank classification | ⬜ Unmetered hardware / electricity |")
 grid=metric('Correct / sample',f"{m['correct']}/100 ({m['sample_accuracy']:.2%})")+metric('Usable','100/100')+metric('Median',f"{m['median_ms']:.2f} ms",speed_band(m['median_ms']))+metric('p95',f"{m['p95_ms']:.2f} ms",speed_band(m['p95_ms']))+metric('Cost','Unmetered hardware / electricity',cost=True)+metric('Wilson 95% upper',f"{m['wilson95_upper']:.2%}")
 cards.append('<article class="asus-screen-card" data-asus-screen-card="'+esc(mid)+'"><h3>'+esc(m['label'])+'</h3><div class="asus-screen-grid">'+grid+'</div><p><strong>Stopped at 100; no full-bank score, rank or cutoff classification.</strong> Sample only; 1,356 inputs remain unattempted.</p></article>')
table='<div class="scroll asus-screen-table"><table><thead><tr>'+''.join('<th>'+x+'</th>' for x in headers)+'</tr></thead><tbody>'+''.join(rows)+'</tbody></table></div>'
section='<section id="asus-native-screens"><h2>ASUS native v5 partial screens</h2><p>'+esc(intro)+'</p>'+table+'<div class="asus-screen-cards">'+''.join(cards)+'</div>'+''.join('<p>'+esc(x)+'</p>' for x in [method,deployment,excluded])+'<ul>'+''.join('<li><a href="'+n+'">'+esc(label)+'</a></li>' for n,label in links)+'</ul></section>'
css='/*ASUS_SCREEN_START*/.asus-screen-cards{display:none}.asus-screen-card{border:1px solid #b9c9ce;background:#fff;padding:14px}.asus-screen-card h3{margin:0 0 12px;font-size:17px}.asus-screen-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:6px}.asus-screen-grid>div{padding:10px;border:1px solid #d7e1e4;min-height:50px}.asus-screen-grid strong,.asus-screen-grid span{display:block}.asus-screen-grid span{font-size:12px}.asus-screen-card p{margin:10px 0 0;font-size:12px}@media(max-width:700px){.asus-screen-table{display:none}.asus-screen-cards{display:grid;gap:14px}}/*ASUS_SCREEN_END*/'
page=(PRIOR/'report.html').read_text();needle='<section id="below-cutoff">';assert page.count(needle)==1;page=page.replace(needle,section+needle);page=page.replace('<a href="#history">Historical screens</a>','<a href="#asus-native-screens">ASUS native screens</a><a href="#history">Historical screens</a>');page=page.replace('</style>',css+'</style>');(out/'report.html').write_text(page)
mdsection='## ASUS native v5 partial screens\n\n'+intro+'\n\n'+'| '+' | '.join(headers)+' |\n|---|---:|---:|---:|---:|---:|---|---|\n'+'\n'.join(mdrows)+'\n\n'+'\n\n'.join([method,deployment,excluded])+'\n\n'+'\n'.join('- ['+label+']('+n+')' for n,label in links)+'\n\n'
md=(PRIOR/'README_V5.md').read_text();needle='## Below the 45% cutoff\n';assert md.count(needle)==1;md=md.replace(needle,mdsection+needle);md+='\nValidate the ASUS screen successor and its unchanged full-bank parent:\n\n```sh\npython3 scripts/validate_system1_v5_asus_native_2026_11_13.py results/releases/'+NAME+' results/releases/system1_v5_hosted_refresh_2026-11-13 --mirror docs/v5\n```\n';(out/'README_V5.md').write_text(md)
notes='# ASUS native resident 4,096-context partial screens\n\n'+intro+'\n\n'+mdsection.split('\n\n',2)[2]+'\n\nRuntime and process fields are server claims. The public usage ledger retains their per-request hashes and declared reuse fields; raw selected choices and gold scoring values remain private.\n';(out/'ASUS_NATIVE_SCREEN_NOTES.md').write_text(notes)
unchanged={str(q.relative_to(PRIOR)):sha(q) for q in PRIOR.rglob('*') if q.is_file() and q.name not in ['report.html','README_V5.md','manifest.json']}
for n,h in unchanged.items():assert sha(out/n)==h,n
s=read(out/'statistics.json');assert len(s['models'])==42 and len(s['ranked_model_ids'])==34
manifest=dict(version='v5-provisional-asus-native-screens',questions=1456,categories=43,measured_models=42,main_models=34,partial_screen_models=len(models),partial_screen_ids=list(models),partial_records_per_ledger=100*len(models),superseded_model_ids=s['superseded_model_ids'],minimum_overall_accuracy=s['minimum_overall_accuracy'],inclusion_threshold=s['inclusion_threshold'],frozen_hosted_refresh_manifest_sha256=sha(PRIOR/'manifest.json'),all_full_bank_files_unchanged=True,unchanged_files_sha256=unchanged,source_files_sha256={n:sha(REPO/n) for n in ['scripts/publish_system1_v5_asus_native_2026_11_13.py','scripts/validate_system1_v5_asus_native_2026_11_13.py']},files_sha256={str(q.relative_to(out)):sha(q) for q in sorted(out.rglob('*')) if q.is_file() and q.name!='manifest.json'})
(out/'manifest.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n');print(json.dumps(dict(full_models=42,active=34,partial_screen_models=len(models),main_records_unchanged=61152,prior_files_exact=len(unchanged))))
