"""Publish owner-audited M2 Ollama decisions with no new inference."""
import csv, hashlib, importlib.util, io, json, math, statistics, sys
from copy import deepcopy
from html import escape
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import numpy as np
import build_readable_report as read
import publish_native_updates_2026_10_27 as old
from build_october18_report import PALETTES
from publish_consolidated_report import table
from repo_layout import repo_file
R=Path(__file__).resolve().parents[1]
H=R.parent/'text-decision-hardening'
CAP=H/'runs/m2_liquid_2b_2026-10-28'
OLD=R/'results/releases/native_updates_2026-10-27'
NAME='local_m2_2026-10-28'
DEST=R/'results/releases'/NAME
M2='#a21caf'; RTX='#7c3aed'; BLUE='#16728c'; YELLOW=(.95,.83,.42,.60)
IDS={'d1:2b':'local_m2_d1_2b','d1-omni:2b':'local_m2_d1_omni_2b'}
LABELS={'d1:2b':'Liquid d1-2B · M2','d1-omni:2b':'Liquid d1-Omni-2B · M2'}
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def loadrows(p):return [json.loads(x) for x in Path(p).read_text().splitlines() if x.strip()]
def write(p,v):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text((v.rstrip() if isinstance(v,str) else json.dumps(v,indent=2,ensure_ascii=False))+'\n')
def capture():
 assert not (DEST/'manifest.json').exists()
 sys.path.insert(0,str(H));sys.path.insert(0,str(CAP))
 import consolidated_analysis as auth
 from analyze_frontier_reference import load_gold
 spec=importlib.util.spec_from_file_location('m2executor',CAP/'run.py'); run=importlib.util.module_from_spec(spec);spec.loader.exec_module(run)
 qs={q['id']:q for q in loadrows(run.TEXT)}
 oldcorr=auth.CORRECTED;auth.CORRECTED=repo_file('corrected_2026-10-18')
 try:gold,meta,names,bindings=load_gold(H,qs)
 finally:auth.CORRECTED=oldcorr
 reports=json.loads((CAP/'offline_report.json').read_text());receipt=json.loads((CAP/'audit_receipt.json').read_text());manifest=json.loads((CAP/'manifest.json').read_text())
 assert receipt['status']=='PASS' and digest(CAP/'run.py')==manifest['run_source_sha256']
 attempts=loadrows(CAP/'attempts.jsonl');dispatch=loadrows(CAP/'dispatches.jsonl');assert len(attempts)==len(dispatch)==2724
 for a,d in zip(attempts,dispatch):assert all(a[k]==v for k,v in d.items())
 oldstats=json.loads((OLD/'statistics.json').read_text());s=deepcopy(oldstats); originals={r['item_id'] for r in csv.DictReader((repo_file('corrected_2026-10-18')/'questions_1136.csv').open())}
 evidence=[];screens=[]
 for model,mid in IDS.items():
  aa=[a for a in attempts if a['model']==model and a['phase']=='text'];screen=[a for a in attempts if a['model']==model and a['phase']=='image'];assert len(aa)==1342 and len(screen)==20
  assert [a['item_id'] for a in aa]==manifest['text_order'] and [a['item_id'] for a in screen]==manifest['image_order'][:20]
  for a in aa:
   q=qs[a['item_id']];b=run.text_body(q,model)
   assert a['request_sha256']==run.hashval(b) and a['question_sha256']==run.hashval(q) and a['http']==200 and a['status']=='ok' and a['raw']['model']==model and a['raw']['usage']['output_tokens']==0
   assert run.parse(a,model,list(b['questions']['decision']['criteria']))['choice']==a['choice']
   evidence.append(dict(model_id=mid,item_id=a['item_id'],family_id=a['family_id'],index=a['index'],input_sha256=q['native_input_sha256'],request_sha256=a['request_sha256'],response_sha256=run.hashval(a['raw']),status=a['status'],latency_ms=a['latency_ms'],input_tokens=a['usage']['input_tokens'],output_tokens=0))
  def outcome(ids):
   z=[a for a in aa if a['item_id'] in ids];n=len(z);c=sum(a['choice']==str(gold[a['item_id']]) for a in z)
   return dict(n=n,correct=c,answered=n,failed=0,wrong_valid=n-c,accuracy=c/n if n else None)
  m=outcome(qs);report=reports[model+' text'];assert m['correct']==report['correct'] and m['n']==1342
  fam={f:outcome({i for i in qs if meta[i]['family_id']==f}) for f in sorted(names)}
  assert all((x['n'],x['correct'])==(report['families'][f]['n'],report['families'][f]['correct']) for f,x in fam.items())
  times=[a['latency_ms'] for a in aa];q=run.quant(times);assert all(math.isclose(q[k],report['timing'][k],rel_tol=1e-12) for k in q)
  assert all(statistics.median(times[:i])<=2000 for i in range(20,1343))
  profiles=[dict(family_id=f,**v) for f,v in fam.items() if v['n']>=20]
  m.update(model_id=mid,label=LABELS[model],model_requested=model,execution_location='local',hardware='Apple M2',memory='16 GB unified memory',precision='BF16',runtime='Ollama 0.40.12 · MLX / Metal',route='Local Ollama · Apple M2 16 GB · loopback HTTP',mean_response_ms=q['mean_ms'],median_ms=q['median_ms'],p95_ms=q['p95_ms'],first_statuses={'ok':1342},attempts=1342,recoveries=0,provider_failures=0,model_output_failures=0,probability_warnings=0,accuracy_among_usable=m['accuracy'],families=fam,macro_family_accuracy=statistics.mean(x['accuracy'] for x in fam.values()),dates_toronto={'2026-10-28':1342},returned_identities={model:1342},providers={'Local Ollama':1342},observed_output_tokens=0,original_1136=outcome(originals),added_206=outcome(set(qs)-originals),new_domains=outcome({i for i in qs if meta[i]['family_id']>='F26'}),release_exclusion_diagnostic=outcome({i for i in qs if not meta[i]['permanently_unscored_native_development']}),highest_scoring_categories=sorted(profiles,key=lambda x:(-x['accuracy'],x['family_id'])),lowest_scoring_categories=sorted(profiles,key=lambda x:(x['accuracy'],x['family_id'])),cost=dict(known_usd=None,known_usd_per_1000=None,unknown_attempts=1342,scope='Local hardware and electricity costs unmeasured'))
  s['models'][mid]=m;s['model_kinds'][mid]='Decision model';s['local_model_ids'].append(mid)
  scr=reports[model+' image'];assert scr['n']==20 and scr['timing']['median_ms']>2000
  screens.append(dict(model=LABELS[model],n=20,correct=scr['correct'],accuracy=scr['correct']/20,**scr['timing'],state='stopped_slow',usable=20))
 s['ranked_model_ids']=sorted(s['models'],key=lambda x:(-s['models'][x]['correct'],x));s['decision_model_ids']=[x for x in s['ranked_model_ids'] if x not in s['reference_model_ids']]
 s.update(model_count=56,decision_model_count=52,local_model_count=22,primary_cases=75152,all_tested_primary_cases=75152,updated_date_toronto='2026-10-28',added_model_ids=list(IDS.values()),prior_statistics_sha256=digest(OLD/'statistics.json'),status='COMPLETE_56_ROUTES_22_LOCAL_1342')
 assert all(s['models'][k]==v for k,v in oldstats['models'].items())
 DEST.mkdir(parents=True,exist_ok=True);write(DEST/'statistics.json',s);write(DEST/'category_guide.json',json.loads((OLD/'category_guide.json').read_text()));write(DEST/'image_speed_screens.json',screens)
 out=io.StringIO(newline='');w=csv.DictWriter(out,fieldnames=list(evidence[0]),lineterminator='\n');w.writeheader();w.writerows(evidence);write(DEST/'m2_timing_evidence.csv',out.getvalue())
 write(DEST/'audit_receipt.json',dict(status='PASS',new_text_runs=2,new_text_attempts=2684,new_image_screens=2,previous_54_models_unchanged=True,original_bank_sha256=manifest['text_sha256'],private_audit_sha256=digest(CAP/'audit_receipt.json'),text_keys_reconciled=True,category_counts_reconciled=True,scored_retries=0,privacy='Aggregate scores and answer-free timing, not answer keys or per-item choices',scoring_limit='Correctness reconciled privately; public exports independently verify timing, coverage and aggregates.'))
 return s

def color(mid,s):return M2 if mid in IDS.values() else RTX if mid in s['local_model_ids'] else YELLOW if mid in s['reference_model_ids'] else BLUE
def badge(mid,s):
 if mid in IDS.values():return '<small class="local-badge m2-badge">Local · Apple M2 · 16 GB</small>'
 if mid in s['local_model_ids']:return '<small class="local-badge">Local · RTX 2060 · 6 GB</small>'
 return ''
def plot(s):
 mids=s['ranked_model_ids'];models=[s['models'][i] for i in mids];y=np.arange(len(mids));fig,axes=plt.subplots(1,3,figsize=(17,max(12,len(mids)*.49+4)),sharey=True,gridspec_kw={'width_ratios':[1.15,1.05,1.12]})
 axes[0].barh(y,[100*m['accuracy'] for m in models],color=[color(i,s) for i in mids]);axes[0].set_yticks(y,[m['label'] for m in models],fontsize=10);axes[0].invert_yaxis();axes[0].set_xlim(0,109);axes[0].axvline(20,color='#6b7280',linestyle='--')
 for label,mid in zip(axes[0].get_yticklabels(),mids):
  if mid in s['local_model_ids']:label.set_color(color(mid,s));label.set_weight('bold')
 for yy,mid,m in zip(y,mids,models):
  axes[0].text(100*m['accuracy']+1,yy,f"{m['accuracy']:.1%}",va='center',fontsize=10)
  axes[1].plot([m['median_ms'],m['p95_ms']],[yy,yy],color='#8896a3');band=next((i for i,x in enumerate((250,500,1000)) if m['median_ms']<=x),3);axes[1].scatter(m['median_ms'],yy,color=PALETTES[band],edgecolor='#35424d',s=45);axes[1].scatter(m['p95_ms'],yy,color='#35424d',marker='d',s=18)
  c=m['cost']
  if mid in s['local_model_ids'] or c.get('public_free_access'):axes[2].text(.03,yy,'Local cost unmeasured' if mid in s['local_model_ids'] else 'Free access*',transform=axes[2].get_yaxis_transform(),va='center',fontsize=9,color=color(mid,s) if mid in s['local_model_ids'] else '#35424d')
  else:
   v=c['known_usd_per_1000'];band=next((i for i,x in enumerate((.01,.025,.05)) if v<=x),3);axes[2].scatter(v,yy,color=PALETTES[band],edgecolor='#35424d',s=45)
 axes[1].set_xscale('log');axes[2].set_xscale('log');axes[2].set_xlim(.002,7)
 for ax,title in zip(axes,['Accuracy','Speed','Cost']):ax.set_title(title);ax.grid(axis='x',alpha=.2);ax.set_axisbelow(True)
 axes[0].set_xlabel('Correct first decisions (%)');axes[1].set_xlabel('Response time (ms): median · p95');axes[2].set_xlabel('USD / 1,000 · local costs unmeasured')
 fig.suptitle('56 routes · 30 hosted decisions · 22 local configurations · 4 LLM references',fontsize=16,y=.985)
 fig.legend(handles=[Patch(facecolor=BLUE,label='Hosted decisions'),Patch(facecolor=RTX,label='Local RTX 2060'),Patch(facecolor=M2,label='Local Apple M2'),Patch(facecolor=YELLOW,label='LLM references')],loc='upper center',bbox_to_anchor=(.5,.96),ncol=4,frameon=False)
 fig.text(.03,.02,'Local Apple M2: 16 GB unified memory, Ollama MLX, BF16, October 28. RTX 2060: 6 GB, Ollaya CUDA, October 25.\nDifferent machines, routes, dates and loads; warm-up/loading excluded for local runs.',fontsize=9)
 fig.subplots_adjust(left=.29,right=.98,top=.91,bottom=.09,wspace=.32)
 for ext in ('png','svg'):fig.savefig(DEST/('accuracy_speed_cost.'+ext),dpi=150,metadata={'Date':None} if ext=='svg' else {})
 plt.close(fig)

def build():
 s=capture();guide=json.loads((DEST/'category_guide.json').read_text());plot(s)
 # Existing plots remain available; generate the new full 56-row named-category plots.
 old.DEST=DEST
 for group in read.GROUPS:old.category_plot(s,group)
 # Re-render plots with distinct model label colours using the same accuracy scale.
 for group in read.GROUPS:
  slug,title,fids,_=group;ids=s['ranked_model_ids'];fig,ax=plt.subplots(figsize=(12.6,len(ids)*.55+5));values=np.array([[s['models'][m]['families'][f]['accuracy'] for f in fids] for m in ids]);im=ax.imshow(values,vmin=0,vmax=1,cmap='YlGnBu',aspect='auto');ax.set_yticks(range(len(ids)),[read.short(s['models'][m]['label']) for m in ids],fontsize=11)
  for lab,mid in zip(ax.get_yticklabels(),ids):
   if mid in s['local_model_ids']:lab.set_color(color(mid,s));lab.set_weight('bold')
  import textwrap
  ax.set_xticks(range(len(fids)),['\n'.join(textwrap.wrap(read.LABELS[f],13,break_long_words=False))+f"\n{s['models'][ids[0]]['families'][f]['n']} questions" for f in fids],fontsize=10);ax.tick_params(length=0,labeltop=True,labelbottom=False,pad=8)
  for i,mid in enumerate(ids):
   for j,f in enumerate(fids):
    v=s['models'][mid]['families'][f];ax.text(j,i,f"{v['correct']}/{v['n']}\n{v['accuracy']:.1%}",ha='center',va='center',fontsize=11,color=read.color(v['accuracy'])[1])
  fig.colorbar(im,ax=ax,fraction=.025,pad=.025,shrink=.75).set_label('Accuracy, fixed 0–1 scale');fig.text(.025,.975,title,fontsize=18,weight='bold');fig.text(.025,.95,'Purple: local RTX 2060. Magenta: local Apple M2. Cells encode accuracy.',fontsize=11);fig.subplots_adjust(left=.31,right=.95,top=.86,bottom=.09)
  for ext in ('png','svg'):fig.savefig(DEST/(slug+'.'+ext),dpi=150,metadata={'Date':None} if ext=='svg' else {})
  plt.close(fig)
 buf=io.StringIO(newline='');w=csv.writer(buf,lineterminator='\n');w.writerow(['category_id','category','questions']+[s['models'][m]['label'] for m in s['ranked_model_ids']]);
 for fid in read.LABELS:w.writerow([fid,read.LABELS[fid],guide[fid]['questions']]+[read.score(s['models'][m]['families'][fid]) for m in s['ranked_model_ids']])
 write(DEST/'category_scores.csv',buf.getvalue())
 rows=[];htmlrows=[]
 for mid in s['ranked_model_ids']:
  m=s['models'][mid];loc=mid in s['local_model_ids'];setting=('🟣 Apple M2' if mid in IDS.values() else '🟣 RTX 2060' if loc else '🟡 LLM reference' if mid in s['reference_model_ids'] else 'Hosted decision');price=old.price(mid,m);fullprice=old.price(mid,m,False);mean=m.get('mean_response_ms',m.get('mean_ms'));rows.append([m['label'],setting,f"{m['correct']}/1342",f"{m['accuracy']:.1%}",'—' if mean is None else f'{mean:.0f} ms',f"{m['median_ms']:.0f} ms",f"{m['p95_ms']:.0f} ms",price,fullprice]);cls='m2-model' if mid in IDS.values() else 'local-model' if loc else 'llm-reference' if mid in s['reference_model_ids'] else 'hosted-model'
  cells=[setting,f"{m['correct']}/1342 · {m['accuracy']:.1%}",'—' if mean is None else f'{mean:.0f} ms']
  row=f'<tr class="{cls}" data-summary-model="{mid}"><th scope="row">{escape(m["label"])}{badge(mid,s)}</th>'+''.join('<td>'+escape(x)+'</td>' for x in cells)
  for k in ('median_ms','p95_ms'):
   band=next((i for i,x in enumerate((250,500,1000)) if m[k]<=x),3);row+=f'<td style="background:{PALETTES[band]}">{m[k]:.0f} ms</td>'
  cost=m['cost'];shade='#edf1f5' if loc or cost.get('public_free_access') else PALETTES[next((i for i,x in enumerate((.01,.025,.05)) if cost['known_usd_per_1000']<=x),3)];row+=f'<td style="background:{shade}">{escape(price)}</td><td>{escape(fullprice)}</td></tr>';htmlrows.append(row)
 findings='''## New local Liquid models on Apple M2\n\nLiquid d1-2B scored **795/1,342 (59.2%)**, with a **898 ms median** and **1,848 ms p95**. Liquid d1-Omni-2B scored **814/1,342 (60.7%)**, with a **717 ms median** and **1,406 ms p95**. Omni answered 19 more correctly. Both completed every text question with usable decisions and zero reported output tokens.\n\nBoth scored 37/40 on ordering by comparisons and 39/43 on following directed connections. d1-2B scored 46/51 on ranking with tie-break rules and 44/50 on fault diagnosis. Omni scored 39/43 on lookup and 48/58 on exceptions and priority rules. Sequential procedures were difficult: 10/48 and 13/48 respectively. Counting exactly true claims scored 27/71 and 28/71; truth-teller consistency 33/74 and 31/74.\n\nThe runs used an Apple M2 Mac with 16 GB unified memory, Ollama 0.40.12 and MLX/Metal, BF16, one model and request at a time. Loading and separate probes are excluded. RTX 2060 measurements use a different machine, runtime, precision and date. Hardware and electricity cost are unmeasured for local runs.\n\nOn images, d1-2B answered 9/20 with a 4.71 s median; Omni answered 13/20 with a 3.32 s median. Both image screens stopped after 20 because their medians exceeded the two-second limit. These small samples are not 200-question image benchmark scores.\n'''
 intro='# System 1 Decision Benchmark\n\n30 hosted decision models, **22 local configurations** and four no-reasoning LLM references on the same **1,342 text questions across 31 categories**. Updated October 28, 2026.\n\n**Fastino GLiDE leads overall at 86.0%. D3 Flash Artemis leads the local configurations at 74.1%, tested on an RTX 2060.**\n\n[Interactive report](https://etsabary.github.io/system-1-decision-benchmark/report.html) · [Named categories](https://etsabary.github.io/system-1-decision-benchmark/report.html#functions)\n\n![56 routes, local RTX 2060 in purple and Apple M2 in magenta](results/releases/'+NAME+'/accuracy_speed_cost.png)\n\nBlue: hosted decisions; purple: local RTX 2060; magenta: local Apple M2; pale yellow: LLM references. Accuracy cells and speed/cost colors retain their fixed scales.\n\n## Complete comparison\n\n'+table(['Model','Setting','Correct / 1342','Accuracy','Mean','Median','p95','Cost / 1000','Bank cost / basis'],rows)+'\n\n'
 narrative='\n\n'.join('## '+title+'\n\n'+text for title,text in old.findings(s))
 narrative=narrative.replace('ranks sixth among all 54 complete configurations','ranked sixth among the previous 54 complete configurations').replace('All 52 earlier records keep','All 52 earlier records kept').replace('All 20 local configurations retain','All 20 RTX 2060 local configurations retain').replace('Blue marks hosted decisions, purple local runs and pale yellow LLM references','Blue marks hosted decisions, purple RTX 2060 runs, magenta Apple M2 runs and pale yellow LLM references')
 groups=read.markdown_groups(s,guide).replace('All 20 models','All 56 routes').replace('all 20 models','all 56 routes').replace('all 20 models','all 56 routes').replace(read.NAME,'results/releases/'+NAME)
 import re
 groups=re.sub(r'https://etsabary.github.io/jev-1.14-comparison-benchmark/[^)# ]+/report.html','https://etsabary.github.io/system-1-decision-benchmark/report.html',groups)
 write(R/'README.md',intro+findings+'\n'+narrative+'\n\n'+groups+'\n\n[Aggregate statistics](results/releases/'+NAME+'/statistics.json) · [Category CSV](results/releases/'+NAME+'/category_scores.csv) · [Answer-free timing evidence](results/releases/'+NAME+'/m2_timing_evidence.csv) · [Audit](results/releases/'+NAME+'/audit_receipt.json).\n\n[Question bank](results/releases/consolidated_2026-10-19/questions_1342.csv) · [scripts/](scripts/README.md). Historical check: `python3 scripts/validate_october21_release.py`.')
 base=(OLD/'report.html').read_text();head=base[:base.index('<body>')+6];head=re.sub(r'<title>.*?</title>','<title>System 1 Decision Benchmark · 56 routes</title>',head);head=head.replace('Compare 52 text decision routes on 1,342 questions: 30 hosted decision models, 20 local RTX 2060 configurations and four reasoning-off LLMs.', 'Compare 56 text decision routes on 1,342 questions: 30 hosted decision models, 22 local configurations and four reasoning-off LLMs.');head=head.replace('</head>','<style>.m2-badge{color:#86198f;background:#fdf4ff;border-color:#e879f9}.m2-model th{border-left:5px solid #a21caf!important;background:#fdf4ff}</style></head>')
 summary='<div class="scroll"><table><thead><tr><th>Model</th><th>Setting</th><th>Correct / 1342</th><th>Mean</th><th>Median</th><th>p95</th><th>Cost / 1000</th><th>Bank cost / basis</th></tr></thead><tbody>'+''.join(htmlrows)+'</tbody></table></div>'
 sections=read.clarity_section(s,guide).replace('All 20 models','All 56 routes').replace('all 20 models','all 56 routes')
 for mid in s['local_model_ids']:
  label=escape(s['models'][mid]['label']);sections=sections.replace('<th scope="row">'+label+'</th>','<th scope="row">'+label+badge(mid,s)+'</th>')
 from markdown import markdown
 body='<main><h1>System 1 Decision Benchmark</h1><p>56 routes: 30 hosted decision models, 22 local configurations and four LLM references. Same 1,342 questions across 31 categories. Updated October 28, 2026.</p><nav><a href="#overview">Overview</a> · <a href="#findings">Findings</a> · <a href="#functions">Named categories</a> · <a href="#method">Method</a></nav><p>Blue: hosted · purple: RTX 2060 · magenta: Apple M2 · pale yellow: no-reasoning LLM references. Speed and accuracy cell scales are unchanged.</p><section id="overview"><h2>Accuracy, speed and cost</h2><a href="accuracy_speed_cost.svg"><img style="width:100%" src="accuracy_speed_cost.png" alt="56 routes, with separate colors for Apple M2 and RTX 2060"></a>'+summary+'</section><section id="findings">'+markdown(findings+'\n\n'+narrative,extensions=['tables'])+'</section>'+sections+'<section id="method"><h2>Method and evidence</h2><p>First attempts on a frozen bank; no tools or iterative reasoning. Local Apple M2 uses Ollama 0.40.12, MLX/Metal and BF16, one request at a time. Loading and four image and two text admission probes per model were excluded. RTX 2060 uses Ollaya and CUDA. Host load, runtime and dates differ. Electricity and hardware costs are unmeasured.</p><p><a href="statistics.json">Aggregate statistics</a> · <a href="category_scores.csv">Category CSV</a> · <a href="m2_timing_evidence.csv">M2 answer-free timing evidence</a> · <a href="image_speed_screens.json">Image speed screens</a> · <a href="audit_receipt.json">Audit</a> · <a href="../consolidated_2026-10-19/questions_1342.csv">Questions</a> · <a href="https://etsabary.github.io/visual-decision-benchmark/report.html">Image report</a></p></section></main></body></html>'
 page=head+body;write(DEST/'report.html',page);write(DEST/'analysis.md',findings+'\n'+narrative)
 old.exports(s,guide)
 # Previous export writes statistics unchanged and supplies the full model CSV.
 for path in DEST.glob('*.svg'):write(path,'\n'.join(x.rstrip() for x in path.read_text().splitlines()))
 write(DEST/'manifest.json',dict(version='m2-local-20261028-v1',models=56,local_models=22,questions_each=1342,prior_statistics_sha256=digest(OLD/'statistics.json'),artifacts={p.name:digest(p) for p in sorted(DEST.iterdir()) if p.is_file() and p.name!='manifest.json'}))
 import shutil
 shutil.copytree(DEST,R/'docs'/NAME,dirs_exist_ok=True)
 write(R/'docs/report.html',old.prior.tables.prior.rebase(page,NAME))
 for file,anchor in [('index.html',''),('functions.html','#functions'),('output_compliance.html','#method')]:write(R/'docs'/file,'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta http-equiv="refresh" content="0;url=report.html'+anchor+'"><title>System 1 Decision Benchmark</title></head><body><a href="report.html'+anchor+'">Current 56-route comparison</a></body></html>')
 write(R/'docs/sitemap.xml','<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url><loc>https://etsabary.github.io/system-1-decision-benchmark/report.html</loc><lastmod>2026-10-28</lastmod></url></urlset>')
 # Bind current source and documentation after publication.
 old.bind_layout()
 print('Built 56 routes; all prior scores retained; no inference.')
if __name__=='__main__':build()
