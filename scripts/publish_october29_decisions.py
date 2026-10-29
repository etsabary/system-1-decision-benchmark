"""Publish audited October 29 decisions and adaptive-generation research. Offline only.

--capture reconciles private owner records with the frozen key once. Normal builds
and public validation use sanitized aggregates and answer-free evidence only.
"""
from collections import Counter
from copy import deepcopy
import csv, hashlib, io, json, math, re, shutil, statistics, sys
from pathlib import Path
from html import escape
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Patch, Rectangle
import numpy as np
from markdown import markdown
import build_readable_report as read
import publish_native_updates_2026_10_27 as previous
from publish_consolidated_report import table
from build_october18_report import PALETTES
ROOT=Path(__file__).resolve().parents[1]
NAME='adaptive_additions_2026-10-29'; DEST=ROOT/'results/releases'/NAME
OLD=ROOT/'results/releases/local_m2_2026-10-28'
H=ROOT.parent/'text-decision-hardening'; RUN=H/'runs/startlux_lan_2026-10-29'; HOST=H/'runs/turion_triospark_2026-10-29'
IDS=['turion_jev31b','trio_spark14','local_startlux_instant4b','local_startlux_autothink4b']; AUTO=IDS[3]
PURPLE='#7c3aed'; GOLD='#d97706'; BLUE='#16728c'; M2='#a21caf'; YELLOW=(.95,.83,.42,.60)
SITE='https://etsabary.github.io/system-1-decision-benchmark/report.html'
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def hashval(v):return hashlib.sha256(json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def rows(p):return [json.loads(x) for x in Path(p).read_text().splitlines() if x.strip()]
def load(p):return json.loads(Path(p).read_text())
def write(p,v):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text((v.rstrip() if isinstance(v,str) else json.dumps(v,indent=2,ensure_ascii=False))+'\n')
def quant(t):
 t=sorted(t);pos=(len(t)-1)*.95;lo=math.floor(pos);hi=math.ceil(pos)
 return dict(mean_ms=statistics.mean(t),median_ms=statistics.median(t),p95_ms=t[lo]+(t[hi]-t[lo])*(pos-lo))
def capture():
 assert not (DEST/'manifest.json').exists(), 'Never overwrite a published release'
 sys.path.insert(0,str(H))
 import consolidated_analysis as authority
 from analyze_frontier_reference import load_gold
 qs={q['id']:q for q in rows(ROOT/'results/releases/consolidated_2026-10-19/questions_1342.jsonl')}
 saved=authority.CORRECTED;authority.CORRECTED=ROOT/'results/releases/corrected_2026-10-18'
 try:gold,meta,names,_=load_gold(H,qs)
 finally:authority.CORRECTED=saved
 agg=load(RUN/'aggregate.json');prior=load(OLD/'statistics.json');s=deepcopy(prior)
 original={r['item_id'] for r in csv.DictReader((ROOT/'results/releases/corrected_2026-10-18/questions_1136.csv').open())}
 configs=[(IDS[0],'Turion Jev 31B','turion','turion-jev-31b'),(IDS[1],'Trio-Spark v1.4','trio_spark14','trio-spark-v1.3'),(IDS[2],'StartLux v1.1 4B Instant','startlux_instant','startlux:4b-v1.1-instant'),(AUTO,'StartLux v1.1 4B AutoThink','startlux_autothink','startlux:4b-v1.1-autothink')]
 evidence=[];protocols={}
 for mid,label,key,model in configs:
  local=mid.startswith('local_');src=RUN/'models'/model.replace(':','__') if local else HOST
  aa=rows(src/'attempts.jsonl') if local else rows(src/('trio_attempts.jsonl' if key=='trio_spark14' else 'turion_attempts.jsonl'))
  dd=rows(src/'dispatches.jsonl') if local else rows(src/('trio_dispatch.jsonl' if key=='trio_spark14' else 'turion_dispatch.jsonl'))
  assert len(aa)==len(dd)==len({a.get('item_id',a.get('id')) for a in aa})==1342
  byid={a.get('item_id',a.get('id')):a for a in aa}
  for a,d in zip(aa,dd):
   iid=a.get('item_id',a.get('id'));q=qs[iid];assert iid==d.get('item_id',d.get('id'))
   req=a.get('request_payload_sha256',a.get('sha256'));assert req==d.get('request_payload_sha256',d.get('sha256'))
   raw=a['transport']['raw'] if local else a.get('response',{})
   if local:assert a['native_input_sha256']==q['native_input_sha256'] and a['attempt']==1
   else:
    ni=q['native_input'];dec=ni['questions']['decision'];payload={'model':model,**ni} if key=='turion' else {'model':model,'state':ni['state'],'task':dec['instructions'],'choices':[{'id':k,'description':v} for k,v in dec['criteria'].items()]}
    assert req==hashval(payload)
   evidence.append(dict(model_id=mid,item_id=iid,family_id=q['family_id'],index=a.get('request_index',a.get('index')),attempt=1,native_input_sha256=q['native_input_sha256'],request_sha256=req,response_sha256=hashval(raw),status=a['status'],latency_ms=a.get('latency_ms',a.get('ms')),input_tokens=(a.get('usage') or {}).get('input_tokens',(a.get('usage') or {}).get('billed_input_tokens')),output_tokens=(a.get('usage') or {}).get('output_tokens') if a['status']=='ok' else None,reported_cost_usd=(int(a['billing']['amount_nano_usd'])/1e9 if a.get('billing') else None)))
  def outcome(items):
   z=[byid[i] for i in items];n=len(z);valid=sum(a['status']=='ok' for a in z);c=sum(a['status']=='ok' and a['choice']==str(gold[a.get('item_id',a.get('id'))]) for a in z)
   return dict(n=n,correct=c,answered=valid,failed=n-valid,wrong_valid=valid-c,accuracy=c/n if n else None)
  m=outcome(qs);expected=agg['text'][key];assert m['correct']==expected['correct'] and m['n']==expected['n']
  fam={fid:outcome({i for i,q in qs.items() if q['family_id']==fid}) for fid in sorted(names)}
  assert all((v['n'],v['correct'])==(expected['families'][f]['n'],expected['families'][f]['correct']) for f,v in fam.items())
  timing=quant([a.get('latency_ms',a.get('ms')) for a in aa]);assert all(math.isclose(timing[k],expected[k],rel_tol=1e-12) for k in timing)
  profile=[dict(family_id=f,**v) for f,v in fam.items() if v['n']>=20]
  cost=dict(known_usd=None,known_usd_per_1000=None,unknown_attempts=1342,kind='local_unmeasured' if local else 'charge_unknown',scope='Local hardware and electricity unmeasured' if local else 'No per-request monetary charge returned; not assumed free')
  if key=='trio_spark14':
   total=sum(int(a['billing']['amount_nano_usd']) for a in aa if a.get('billing'))/1e9;assert total==.013644162
   cost.update(known_usd=total,known_usd_per_1000=total/1342*1000,unknown_attempts=0,kind='api_reported_including_trial',scope='Actual recorded charge, including 99 free trial calls; two unsuccessful first attempts',before_trial_tariff_usd=.01478757)
  m.update(model_id=mid,label=label,model_requested=model,execution_location='local' if local else 'hosted',hardware='CUDA GPU; precise model unreported' if local else 'Provider hardware unreported',precision='Q8_0' if local else 'Unreported',runtime='Ollaya 0.17.0 · CUDA' if local else 'Native hosted decision API',route='Direct wired LAN · Ollaya /api/decide' if local else 'Turion direct /v1/systemone' if key=='turion' else 'MachineFi direct /api/spark/v1/decisions',mean_response_ms=timing['mean_ms'],median_ms=timing['median_ms'],p95_ms=timing['p95_ms'],first_statuses=dict(Counter(a['status'] for a in aa)),attempts=1342,recoveries=0,provider_failures=m['failed'],model_output_failures=0,probability_warnings=0,accuracy_among_usable=m['correct']/m['answered'],families=fam,macro_family_accuracy=statistics.mean(v['accuracy'] for v in fam.values()),dates_toronto={'2026-10-29':1342},returned_identities=dict(Counter(a.get('model_returned') or a.get('model_version') or ('turion-jev-31b' if key=='turion' else 'unavailable on failed response') for a in aa)),providers={'Local Ollaya' if local else 'Turion' if key=='turion' else 'MachineFi':1342},observed_output_tokens=sum((a.get('usage') or {}).get('output_tokens',0) for a in aa),original_1136=outcome(original),added_206=outcome(set(qs)-original),new_domains=outcome({i for i in qs if qs[i]['family_id']>='F26'}),release_exclusion_diagnostic=outcome({i for i in qs if not meta[i]['permanently_unscored_native_development']}),highest_scoring_categories=sorted(profile,key=lambda v:(-v['accuracy'],v['family_id'])),lowest_scoring_categories=sorted(profile,key=lambda v:(v['accuracy'],v['family_id'])),cost=cost)
  if key=='trio_spark14':
   m['observed_output_tokens']=None
   m['output_token_telemetry']='Not returned by text endpoint; native typed decisions, no explanatory text'
  protocol=dict(date='2026-10-29',questions=1342,scored_retries=0,first_attempt_failures_in_denominator=True,question_bank_sha256=s['question_bank_sha256'],single_request_in_flight=True,load_warmup_excluded=local,mode='Adaptive decision; sometimes generates' if mid==AUTO else 'Native immediate decision')
  if local:
   md=load(src/'metadata_screen.json')['raw'];mi=md['model_info']
   protocol.update(model_digest=md['digest'],precision='Q8_0',source_commit=mi['startlux.source_commit'],tokenizer_revision=mi['startlux.tokenizer_revision'],prompt_attention=mi['startlux.prompt_attention'],context_length=2048,max_images=1,max_processed_pixels_advertised=262144,device_observed='cuda:0',gpu_model='Not reported by API',runtime='Ollaya 0.17.0',warmup_calls=4)
  if mid==AUTO:
   protocol.update(native_think_budget=512,max_think_budget=1024,speed_policy='User-authorized adaptive research exception; complete despite long tails',thought_text_exposed=False,explicit_budget_exhaustion_flag=False)
   m['adaptive_generation']=deepcopy(agg['paired_text']);m['adaptive_generation'].pop('at',None)
  protocols[mid]=protocol;s['models'][mid]=m;s['model_kinds'][mid]='Adaptive decision · sometimes thinks' if mid==AUTO else 'Decision model'
  (s['local_model_ids'] if local else s['hosted_model_ids']).append(mid)
 s['ranked_model_ids']=sorted(s['models'],key=lambda mid:(-s['models'][mid]['correct'],mid))
 s['decision_model_ids']=[mid for mid in s['ranked_model_ids'] if mid not in s['reference_model_ids']]
 s.update(model_count=60,decision_model_count=56,hosted_decision_model_count=32,local_model_count=24,primary_cases=80520,all_tested_primary_cases=80520,updated_date_toronto='2026-10-29',added_model_ids=IDS,adaptive_model_ids=[AUTO],single_pass_decision_ids=[mid for mid in s['decision_model_ids'] if mid!=AUTO],prior_statistics_sha256=digest(OLD/'statistics.json'),status='COMPLETE_60_ROUTES_WITH_ONE_ADAPTIVE_RESEARCH_REFERENCE')
 assert all(s['models'][k]==v for k,v in prior['models'].items())
 write(DEST/'statistics.json',s);write(DEST/'category_guide.json',load(OLD/'category_guide.json'));write(DEST/'execution_protocol.json',protocols)
 buf=io.StringIO(newline='');w=csv.DictWriter(buf,fieldnames=list(evidence[0]),lineterminator='\n');w.writeheader();w.writerows(evidence);write(DEST/'october29_timing_evidence.csv',buf.getvalue())
 write(DEST/'audit_receipt.json',dict(status='PASS',new_full_text_runs=4,new_first_attempts=5368,previous_56_model_records_unchanged=True,bank_sha256=s['question_bank_sha256'],private_key_reconciled=True,category_totals_reconciled=True,all_dispatches_resolved=True,scored_retries=0,public_scope='Aggregates and answer-free timings/hashes; no keys, choices or per-item correctness'))

def color(mid,s):return M2 if mid.startswith('local_m2') else PURPLE if mid in s['local_model_ids'] else YELLOW if mid in s['reference_model_ids'] else BLUE
def badge(mid,s):
 if mid==AUTO:return '<small class="local-badge adaptive-badge">✦ Local · CUDA · sometimes thinks</small>'
 if mid in IDS[2:]:return '<small class="local-badge">Local · CUDA · Q8</small>'
 if mid.startswith('local_m2'):return '<small class="local-badge m2-badge">Local · Apple M2 · 16 GB</small>'
 if mid in s['local_model_ids']:return '<small class="local-badge">Local · RTX 2060 · 6 GB</small>'
 return ''
def price(mid,m,norm=True):
 if mid==IDS[0]:return 'Unknown monetary charge'
 if mid==IDS[1]:return f"${m['cost']['known_usd_per_1000' if norm else 'known_usd']:.8f}"+('' if norm else ' · trial included')
 return previous.price(mid,m,norm)
def band(v,limits):return next((i for i,x in enumerate(limits) if v<=x),3)
def mark_names(html,s):
 for mid in s['ranked_model_ids']:
  label=escape(s['models'][mid]['label']);cls='adaptive-name' if mid==AUTO else 'local-name' if mid in s['local_model_ids'] else 'reference-name' if mid in s['reference_model_ids'] else ''
  html=html.replace('<th scope="row">'+label+'</th>','<th scope="row" class="'+cls+'">'+label+badge(mid,s)+'</th>')
 return html.replace('All 20 models','All 60 routes').replace('all 20 models','all 60 routes')
def overview(s):
 mids=s['ranked_model_ids'];y=np.arange(len(mids));fig,axes=plt.subplots(1,3,figsize=(17,len(mids)*.49+4),sharey=True,gridspec_kw={'width_ratios':[1.15,1.05,1.12]})
 bars=axes[0].barh(y,[100*s['models'][mid]['accuracy'] for mid in mids],color=[color(mid,s) for mid in mids]);axes[0].set_yticks(y,[s['models'][mid]['label']+(' [sometimes thinks]' if mid==AUTO else '') for mid in mids],fontsize=10);axes[0].invert_yaxis();axes[0].set_xlim(0,109);axes[0].axvline(20,color='#6b7280',ls='--')
 for lab,mid in zip(axes[0].get_yticklabels(),mids):
  if mid in s['local_model_ids']:lab.set_color(color(mid,s));lab.set_weight('bold')
 for yy,mid,bar in zip(y,mids,bars):
  m=s['models'][mid];axes[0].text(m['accuracy']*100+1,yy,f"{m['accuracy']:.1%}",va='center',fontsize=10)
  axes[1].plot([m['median_ms'],m['p95_ms']],[yy,yy],color='#8896a3');axes[1].scatter(m['median_ms'],yy,color=PALETTES[band(m['median_ms'],(250,500,1000))],edgecolor='#35424d',s=44);axes[1].scatter(m['p95_ms'],yy,color='#35424d',marker='d',s=18)
  if mid==AUTO:
   bar.set_edgecolor(GOLD);bar.set_linewidth(5);bar.set_hatch('..');axes[1].scatter(m['mean_response_ms'],yy,marker='*',color=GOLD,s=90,zorder=4)
   for ax in axes:ax.axhspan(yy-.47,yy+.47,facecolor='none',edgecolor=GOLD,lw=3.5,zorder=5)
  c=m['cost'];v=c['known_usd_per_1000']
  if v is None:
   msg='Local cost unmeasured' if mid in s['local_model_ids'] else 'Free public access*' if c.get('public_free_access') else 'Charge unknown'
   axes[2].text(.03,yy,msg,transform=axes[2].get_yaxis_transform(),va='center',fontsize=9,color=PURPLE if mid in s['local_model_ids'] else '#35424d')
  else:axes[2].scatter(v,yy,color=PALETTES[band(v,(.01,.025,.05))],edgecolor='#35424d',s=44)
 axes[1].set_xscale('log');axes[2].set_xscale('log');axes[2].set_xlim(.002,7)
 for ax,title in zip(axes,['Accuracy','Speed: median to p95','Cost']):ax.set_title(title);ax.grid(axis='x',alpha=.2);ax.set_axisbelow(True)
 axes[0].set_xlabel('Correct first decisions (%)');axes[1].set_xlabel('Response time (ms, log scale)');axes[2].set_xlabel('USD / 1,000 questions')
 fig.suptitle('60 routes · 1,342 questions each · includes one adaptive research configuration',fontsize=16,y=.985)
 fig.legend(handles=[Patch(facecolor=BLUE,label='Hosted decision'),Patch(facecolor=PURPLE,label='Local CUDA'),Patch(facecolor=M2,label='Local Apple M2'),Patch(facecolor=YELLOW,label='LLM reference'),Patch(facecolor=PURPLE,edgecolor=GOLD,lw=2,hatch='..',label='Local AutoThink · sometimes thinks')],loc='upper center',bbox_to_anchor=(.5,.965),ncol=3,frameon=False)
 fig.text(.03,.02,'Purple connects local CUDA runs. Gold frame marks adaptive AutoThink; gold star shows its mean (5,767 ms).\nAutoThink: median 483 ms, p95 13,652 ms; generation reported on 44.1% of text calls. Other rows retain original dates/settings.\nLocal hardware/electricity costs are unmeasured. StartLux GPU model was not returned by the API.',fontsize=9)
 fig.subplots_adjust(left=.30,right=.98,top=.91,bottom=.09,wspace=.32)
 for ext in ['png','svg']:fig.savefig(DEST/('accuracy_speed_cost.'+ext),dpi=150,metadata={'Date':None} if ext=='svg' else {})
 plt.close(fig)
def category_plots(s):
 import textwrap
 for slug,title,fids,_ in read.GROUPS:
  mids=s['ranked_model_ids'];fig,ax=plt.subplots(figsize=(12.6,len(mids)*.55+5));values=np.array([[s['models'][m]['families'][f]['accuracy'] for f in fids] for m in mids]);im=ax.imshow(values,vmin=0,vmax=1,cmap='YlGnBu',aspect='auto');ax.set_yticks(range(len(mids)),[read.short(s['models'][m]['label'])+(' [sometimes thinks]' if m==AUTO else '') for m in mids],fontsize=10)
  for lab,mid in zip(ax.get_yticklabels(),mids):
   if mid in s['local_model_ids']:lab.set_color(color(mid,s));lab.set_weight('bold')
  ai=mids.index(AUTO);ax.add_patch(Rectangle((-.49,ai-.49),len(fids)-.02,.98,fill=False,edgecolor=GOLD,lw=3.5))
  ax.set_xticks(range(len(fids)),['\n'.join(textwrap.wrap(read.LABELS[f],13,break_long_words=False))+f"\n{s['models'][mids[0]]['families'][f]['n']} questions" for f in fids],fontsize=10);ax.tick_params(length=0,labeltop=True,labelbottom=False,pad=8)
  for i,mid in enumerate(mids):
   for j,f in enumerate(fids):
    v=s['models'][mid]['families'][f];ax.text(j,i,f"{v['correct']}/{v['n']}\n{v['accuracy']:.1%}",ha='center',va='center',fontsize=10,color=read.color(v['accuracy'])[1])
  fig.colorbar(im,ax=ax,fraction=.025,pad=.025,shrink=.75).set_label('Accuracy, fixed 0–1 scale');fig.text(.025,.975,title,fontsize=18,weight='bold');fig.text(.025,.95,'Purple: local CUDA. Magenta: Apple M2. Gold frame: adaptive AutoThink. Cells encode accuracy.',fontsize=10);fig.subplots_adjust(left=.31,right=.95,top=.86,bottom=.09)
  for ext in ['png','svg']:fig.savefig(DEST/(slug+'.'+ext),dpi=150,metadata={'Date':None} if ext=='svg' else {})
  plt.close(fig)
def adaptive_plot(s):
 a=s['models'][AUTO];i=s['models'][IDS[2]];pair=a['adaptive_generation'];fig,axes=plt.subplots(1,2,figsize=(14,6.2),gridspec_kw={'width_ratios':[1,1.25]})
 times=[pair['latency_by_reported_generation']['reported_zero_generation']['median_ms'],pair['latency_by_reported_generation']['reported_generation']['median_ms']]
 bars=axes[0].barh([1,0],times,color=PURPLE,edgecolor=GOLD,lw=2);axes[0].set_yticks([1,0],['Zero generated tokens\n750 calls · 55.9%','Generated tokens\n592 calls · 44.1%']);axes[0].set_xscale('log');axes[0].set_xlim(100,30000)
 for b,t in zip(bars,times):axes[0].text(t*1.08,b.get_y()+b.get_height()/2,f'{t/1000:.2f} s',va='center')
 axes[0].set_xlabel('Median client response (ms, log scale)');axes[0].set_title('AutoThink text: two observed response groups')
 import textwrap
 fids=['F13','F07','F12','F24','F16','F10'];yy=np.arange(len(fids));axes[1].barh(yy-.17,[100*i['families'][f]['accuracy'] for f in fids],height=.32,color=PURPLE,alpha=.4,label='Instant');axes[1].barh(yy+.17,[100*a['families'][f]['accuracy'] for f in fids],height=.32,color=PURPLE,edgecolor=GOLD,lw=1.8,label='AutoThink');axes[1].set_yticks(yy,['\n'.join(textwrap.wrap(read.LABELS[f],23)) for f in fids],fontsize=9);axes[1].invert_yaxis();axes[1].set_xlim(0,110);axes[1].set_xlabel('Correct decisions (%)');axes[1].set_title('Large gains and reversals by task');axes[1].legend(loc='lower right')
 fig.suptitle('StartLux 4B: an adaptive boost with a longer response tail',fontsize=15);fig.text(.03,.02,'Different released weights and attention settings: this is not a controlled reasoning on/off experiment. Native budget: 512 tokens.\nOutput counters group the calls; the API did not expose thoughts. Text first attempts on October 29, 2026.',fontsize=9);fig.subplots_adjust(left=.17,right=.97,top=.82,bottom=.22,wspace=.85)
 for ext in ['png','svg']:fig.savefig(DEST/('adaptive_behavior.'+ext),dpi=160,metadata={'Date':None} if ext=='svg' else {})
 plt.close(fig)

FINDINGS='''## The overall leaders remain unchanged

Fastino GLiDE leads at **1,154/1,342 (86.0%)**, followed by GPT-6 Sol without reasoning at **1,143 (85.2%)** and Mammoth-1 at **1,139 (84.9%)**. Turion Jev 31B adds **1,121 (83.5%)**: one answer above Perplexity Decider v1.2, three below D3 Ultra, and six below both Respan Span-02 and Drex Max. These are results on this bank, with their original test dates and routes retained.

**D3 Flash Artemis remains the highest-scoring immediate local configuration at 995/1,342 (74.1%)** on the deliberately older RTX 2060 with 6 GB VRAM. StartLux AutoThink reaches 1,005 (74.9%) with adaptive generation, shown in the same local purple with a gold frame. StartLux Instant reaches 988 (73.6%) with a shorter 282 ms median. The StartLux API confirmed CUDA execution but did not identify the precise GPU model, so its badge records CUDA and Q8 rather than assigning unverified hardware.

## Turion handles combined rules better than multi-step procedures

Turion answered **53/54** questions about Boolean scope, **51/52** rule counterexamples and **64/67** one-to-one assignments correctly. Boolean scope asks whether conditions must hold together or whether either is enough. A rule counterexample asks which case disproves a stated claim. One-to-one assignment asks how to match people or objects when each can be used once.

It scored **10/48** on sequential procedures, **41/74** on truth-teller consistency and **30/52** on object swaps. Following a sequence of updates remains a different ability from applying a well-specified logical rule. Its mean / median / p95 were **567 / 502 / 1,006 ms**. All 1,342 responses were usable. Monetary charges were not returned, so the cost is recorded as unknown.

## Trio-Spark is fast and inexpensive, with a lower overall score

Trio-Spark scored **915/1,342 (68.2%)**, with **411 / 407 / 451 ms** mean / median / p95. Its strongest results include following directed links **42/43**, comparisons **39/40**, and lookup **40/43**. Object swaps scored **19/52**, truth-teller consistency **31/74**, and sequential procedures **10/48**.

The requested v1.3 alias returned `trio-spark-2026-10-28`; MachineFi identifies that served release as v1.4. One HTTP 429 and one context-length HTTP 413 remain unsuccessful first attempts. No scored questions were retried or shortened. The recorded charge was **$0.013644162 for the bank**, including 99 free trial calls; normalized to 1,000 questions, **$0.01016704**. At the listed tariff, the same recorded input-token total before the trial allowance is $0.01478757.

## AutoThink keeps the immediate path and sometimes adds generation

The [StartLux implementation](https://github.com/StartLuxLabs/StartLux-Decision) describes a probability gate: an AutoThink model can return an immediate decision when sufficiently sure, or generate a thought and read the answer again. This creates an adaptive route between immediate decisions and deliberation. The exact gate used by this local adapter was not exposed.

In these text calls, **750/1,342 (55.9%) reported zero generated tokens**, with a **306 ms median**. **592 (44.1%) reported generation**, with a **13.12 s median**. AutoThink remains in the main comparison because it retains an immediate decision path, with its adaptive status visible on every view. Generation occurred often enough here that “occasional boost” needs the measured proportion alongside it.

Its overall **483 ms median** hides a long tail: **5,767 ms mean** and **13,652 ms p95**. Its mean was **19.7 times Instant's**. The API reported 288,706 output tokens; 491 calls reported exactly the native 512-token budget. It did not expose the thought or a budget-exhaustion flag. Counts alone do not show the content of the reasoning or whether a thought was unfinished.

## The adaptive variant changes which tasks succeed

AutoThink scored **33/48** on sequential procedures, compared with Instant's **10/48**. These questions require applying instructions through successive changes—for example, updating counters in order when a later action depends on the new value. Scheduling rose **39/76 → 49/76**, object swaps **25/52 → 34/52**, and spatial tracking **26/49 → 33/49**.

There were reversals: choosing which authorised record governs fell **42/43 → 21/43**, reference binding **40/50 → 33/50**, and truth-teller consistency **46/74 → 40/74**. AutoThink uniquely answered 122 questions correctly, Instant uniquely answered 105, both answered 883 correctly, and both missed 232. The net gain is **17 answers, or 1.27 percentage points**.

AutoThink's procedure score ties **Respan's 33/48**, the highest observed here. Respan reached that score without reported generation. The result supports investigating selective extra computation, but does not establish that generation is necessary for these tasks. Instant and AutoThink are different released weights with different prompt attention; this is a comparison of the two served variants, rather than a controlled reasoning toggle on identical weights.

## Images are relevant as a separate matched subset

Trio-Spark and both local StartLux routes accept one image per request. They completed the same **177 single-image questions**; **23 multi-image questions** were unsupported. Trio scored **106/177 (59.9%)**, Instant **101 (57.1%)**, and AutoThink **108 (61.0%)**. AutoThink's image median was **8.36 s**, compared with Instant's **387 ms**, and it reported generation on 99/177 calls. Its image run completed under the explicit adaptive-research speed exception.

On those same 177 items, earlier Amos scored **138 (78.0%)**, Fastino **136 (76.8%)**, and D3 Turbo **132 (74.6%)**, recomputed from their existing records. These subset results appear in the [image report](https://etsabary.github.io/visual-decision-benchmark/report.html#single-image-subset), alongside the separate full 200-question ranking. Turion failed the image-binding probes on the tested endpoint and received no image score.
'''
METHOD='''Every full text row contains the same 1,342 first attempts across 31 categories. All 56 earlier model records retain their exact scores, timings, costs and dates. The question bank and scoring rules are unchanged. Categories have unequal sizes; the six newest have eight questions each. Related variants and author-development qualifications remain in the earlier releases.

The October 29 runs used the frozen native state, instructions and five original options, in the existing seeded order. One request at a time within each route; local models ran sequentially over direct wired LAN. Timers span request transfer through the complete response; preparation, pacing, loading and warm-ups are excluded. All dispatches were resolved. No tools, scored retries or agentic iteration. AutoThink's internal generation is explicitly included and labelled. Turion and Instant reported zero output tokens. Trio returned native typed decisions without explanatory text; its text endpoint did not return an output-token counter.

The normal two-second cumulative-median speed screen after at least 20 calls remained in effect for immediate-decision routes. AutoThink completed under a user-authorized research exception; its full accuracy, mean, median and p95 remain visible even when deliberation is slow. The native local budget was 512 tokens, with an advertised maximum of 1,024; it was not tuned during the test. Token counters are observations, not visible reasoning traces.

StartLux ran through Ollaya 0.17.0, CUDA, Q8_0, with 2,048-token context. Instant used bidirectional prompt attention; AutoThink used causal attention. Precise GPU model, driver and system RAM were not returned by this route. Previous RTX 2060 measurements retain their original confirmed user-supplied hardware label, chosen deliberately as an older accessible setup; Apple M2 measurements retain their separate magenta label. Sharing a purple local-CUDA color does not assert identical hardware. No projected speed on newer hardware is included. Local hardware and electricity costs are unmeasured.

Trio's cost is the API-reported charge including the trial allowance. Turion's monetary charge is unknown. Earlier free-access and tariff-estimate qualifications remain attached to each model. Provider load, deployment, precision, dates and network paths vary, so latency differences do not isolate model architecture. Selected LLM references retain their earlier reasoning-off settings and limitations.

Private offline audits bound the frozen answer key, reconstructed requests and reconciled category totals. Public exports supply aggregates and answer-free timing and request/response hashes, with no keys or per-item model choices. Public checks reproduce coverage, timing, token counts, cost arithmetic and category sums; they cannot independently rescore private answers. The question bank remains publicly downloadable without the scoring key.'''
CSS='''
.adaptive-card{border:6px solid #d97706;border-radius:14px;padding:24px;background:#f5f0ff;box-shadow:0 0 0 4px #ede9fe;margin:28px 0}.adaptive-card h2{color:#5b21b6;margin-top:0}.adaptive-badge{background:#ede9fe;color:#5b21b6;border:2px solid #d97706}.adaptive-name{border:2px solid #d97706!important;border-left:6px solid #7c3aed!important;background:#f5f0ff!important}.adaptive-model td{border-top:3px solid #d97706;border-bottom:3px solid #d97706}.adaptive-model th{border:4px solid #d97706!important;border-left:6px solid #7c3aed!important;background:#f5f0ff}.m2-badge{color:#86198f;background:#fdf4ff;border-color:#e879f9}.m2-model th{border-left:5px solid #a21caf!important;background:#fdf4ff}.reference-name{background:#fff8df!important}.split-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:16px}.split-grid>div{padding:16px;background:white;border:1px solid #c4b5fd;border-radius:9px}.split-grid strong{font-size:1.8rem;display:block;color:#5b21b6}.split-grid small{display:block;margin-top:10px}.figure img{width:100%}.summary-table th:first-child{min-width:235px}.cost-note{white-space:normal;min-width:170px}.adaptive-legend{border:2px solid #d97706;background:#ede9fe;color:#5b21b6;padding:4px 8px;border-radius:5px}.new-note{padding:20px;border-left:5px solid #16728c;background:#edf6f8}td{font-variant-numeric:tabular-nums}
'''
def summary(s):
 md=[];html=[]
 for mid in s['ranked_model_ids']:
  m=s['models'][mid];local=mid in s['local_model_ids'];ref=mid in s['reference_model_ids'];setting='✦ Local CUDA · adaptive' if mid==AUTO else '🟣 Local CUDA · Q8' if mid in IDS[2:] else '🟣 Apple M2' if mid.startswith('local_m2') else '🟣 RTX 2060' if local else '🟡 LLM reference' if ref else 'Hosted decision'
  mean=m.get('mean_response_ms',m.get('mean_ms'));meanstr='—' if mean is None else f'{mean:,.0f} ms'
  md.append([m['label'],setting,f"{m['correct']}/1342",f"{m['accuracy']:.1%}",meanstr,f"{m['median_ms']:,.0f} ms",f"{m['p95_ms']:,.0f} ms",price(mid,m),price(mid,m,False)])
  cls='adaptive-model' if mid==AUTO else 'm2-model' if mid.startswith('local_m2') else 'local-model' if local else 'llm-reference' if ref else 'hosted-model'
  row=f'<tr class="{cls}" data-summary-model="{mid}"><th scope="row">{escape(m["label"])}{badge(mid,s)}</th><td>{escape(setting)}</td><td>{m["correct"]}/1342 · {m["accuracy"]:.1%}</td><td>{meanstr}</td>'
  for k in ['median_ms','p95_ms']:row+=f'<td style="background:{PALETTES[band(m[k],(250,500,1000))]}">{m[k]:,.0f} ms</td>'
  c=m['cost'];shade='#edf1f5' if c['known_usd_per_1000'] is None else PALETTES[band(c['known_usd_per_1000'],(.01,.025,.05))]
  row+=f'<td style="background:{shade}" class="cost-note">{escape(price(mid,m))}</td><td class="cost-note">{escape(price(mid,m,False))}</td></tr>';html.append(row)
 return table(['Model','Setting','Correct / 1342','Accuracy','Mean','Median','p95','Cost / 1000','Bank cost / basis'],md),'<div class="scroll"><table class="summary-table"><thead><tr><th>Model</th><th>Setting</th><th>Correct / 1342</th><th>Mean</th><th>Median</th><th>p95</th><th>Cost / 1000</th><th>Bank cost / basis</th></tr></thead><tbody>'+''.join(html)+'</tbody></table></div>'
def build():
 s=load(DEST/'statistics.json');s['total_http_attempts']=sum(m.get('attempts',m['n']) for m in s['models'].values());s['total_recoveries']=sum(m.get('recoveries',0) for m in s['models'].values());guide=load(DEST/'category_guide.json');previous.DEST=DEST;previous.exports(s,guide);overview(s);category_plots(s);adaptive_plot(s)
 mdtable,htmltable=summary(s)
 intro='# System 1 Decision Benchmark\n\n**60 configurations on the same 1,342 text questions across 31 categories:** 32 hosted decision models, 23 immediate local configurations, one adaptive local AutoThink model, and four selected no-reasoning LLM references. Updated October 29, 2026.\n\n**Fastino GLiDE leads overall at 86.0%. D3 Flash Artemis leads the immediate local configurations at 74.1%. StartLux AutoThink reaches 74.9% with generation on 44.1% of text calls.**\n\n[Interactive report]('+SITE+') · [AutoThink: immediate decisions and adaptive generation]('+SITE+'#adaptive) · [Named categories]('+SITE+'#functions)\n\n![60 configurations: local CUDA purple, adaptive AutoThink framed in gold](results/releases/'+NAME+'/accuracy_speed_cost.png)\n\nPurple connects the local CUDA runs; magenta identifies Apple M2; blue identifies hosted decisions; pale yellow identifies LLM references. **The purple AutoThink bar has a gold frame and dot pattern because it sometimes generates.** Speed/cost bands and accuracy colors retain their fixed meanings. Hardware, routes and dates stay labelled.\n\n## Complete comparison\n\n'+mdtable+'\n\nMedian is the midpoint response time. p95 is the time within which 95% of measured responses completed; it exposes slower responses that a median can hide. The plot uses a gold star for AutoThink’s mean. Local compute costs are unmeasured; unknown charges are not treated as zero.\n\n'
 groups=read.markdown_groups(s,guide).replace('All 20 models','All 60 routes').replace('all 20 models','all 60 routes').replace(read.NAME,'results/releases/'+NAME)
 groups=re.sub(r'https://etsabary.github.io/jev-1.14-comparison-benchmark/[^)# ]+/report.html',SITE,groups)
 adaptive_md='\n\n![AutoThink timing split and category tradeoffs](results/releases/'+NAME+'/adaptive_behavior.png)\n\n'
 end='\n\n## Method and evidence\n\n'+METHOD+'\n\n[Aggregate statistics](results/releases/'+NAME+'/statistics.json) · [Model CSV](results/releases/'+NAME+'/model_statistics.csv) · [Category CSV](results/releases/'+NAME+'/category_scores.csv) · [New answer-free timing evidence](results/releases/'+NAME+'/october29_timing_evidence.csv) · [Execution settings](results/releases/'+NAME+'/execution_protocol.json) · [Audit receipt](results/releases/'+NAME+'/audit_receipt.json).\n\n[Previous 56-route analysis](results/releases/local_m2_2026-10-28/analysis.md) · [Question bank](results/releases/consolidated_2026-10-19/questions_1342.csv) · [scripts/](scripts/README.md). Historical check: `python3 scripts/validate_october21_release.py`.\n'
 write(ROOT/'README.md',intro+FINDINGS+adaptive_md+groups+end)
 base=(OLD/'report.html').read_text();head=base[:base.index('<body>')+6];head=re.sub(r'<title>.*?</title>','<title>System 1 Decision Benchmark · 60 configurations</title>',head);head=re.sub(r'<meta name="description"[^>]+>','<meta name="description" content="60 configurations on 1,342 text decisions. Compare accuracy, speed, costs and 31 named categories. Includes local StartLux adaptive AutoThink.">',head);head=head.replace('</head>','<style>'+CSS+'</style></head>')
 adaptive='<section id="adaptive" class="adaptive-card"><h2>✦ StartLux AutoThink: local decisions, sometimes with a boost</h2><p>The purple fill connects it to local CUDA models. Its gold frame identifies adaptive generation. All 1,342 answers count in its 74.9% score.</p><div class="split-grid"><div><strong>55.9%</strong>750 calls · zero generated tokens<small>306 ms median in this group</small></div><div><strong>44.1%</strong>592 calls · generated tokens reported<small>13.12 s median in this group</small></div><div><strong>33/48</strong>Sequential procedures<small>Instant: 10/48 · Respan: 33/48</small></div><div><strong>5.77 s</strong>Mean across all text calls<small>483 ms median · 13.65 s p95</small></div></div><p>Counts show the observed response split. The API does not expose thoughts. The local adapter kept its native 512-token budget. The image run generated on 99/177 calls and had an 8.36 s median.</p><div class="figure"><a href="adaptive_behavior.svg"><img src="adaptive_behavior.png" alt="AutoThink purple bars with gold frame: latency split and procedure gains alongside category reversals"></a></div></section>'
 leader='<div class="cards"><div class="card"><div class="label">Highest overall</div><div class="big">86.0%</div><div class="small">Fastino GLiDE · 1,154/1,342</div></div><div class="card"><div class="label">Highest immediate local score</div><div class="big">74.1%</div><div class="small">D3 Flash Artemis · RTX 2060 · 6 GB</div></div><div class="card"><div class="label">Adaptive local configuration</div><div class="big">✦ 74.9%</div><div class="small">AutoThink · generation on 44.1% of text calls</div></div></div>'
 body='<main><h1>System 1 Decision Benchmark</h1><p>60 configurations on the same 1,342 questions across 31 categories: 32 hosted decisions, 23 immediate local configurations, one adaptive local configuration and four LLM references. Updated October 29, 2026.</p><nav><a href="#overview">All 60 configurations</a> · <a href="#adaptive">✦ AutoThink</a> · <a href="#findings">Findings</a> · <a href="#functions">Named categories</a> · <a href="#method">Method</a></nav>'+leader+'<div class="route-legend"><span><i class="swatch" style="background:#16728c"></i>Hosted decisions</span><span><i class="swatch" style="background:#7c3aed"></i>Local CUDA</span><span><i class="swatch" style="background:#a21caf"></i>Local Apple M2</span><span><i class="swatch" style="background:#f4df9a"></i>LLM references</span><span class="adaptive-legend">✦ Purple + gold frame: local, sometimes thinks</span></div><section id="overview"><h2>Accuracy, speed and cost</h2><p>Every row covers all 1,342 first attempts. Accuracy and speed/cost colors keep their fixed scales. Median shows the midpoint; p95 shows the slower response tail. A gold star marks AutoThink’s mean. Read the exact values in the scrollable table below.</p><div class="figure"><a href="accuracy_speed_cost.svg"><img src="accuracy_speed_cost.png" alt="60 configurations; local CUDA in purple, adaptive AutoThink in purple with gold frame"></a></div>'+htmltable+previous.prior.tables.prior.prior.legend_html()+'</section>'+adaptive+'<section id="findings">'+markdown(FINDINGS,extensions=['tables'])+'</section>'+mark_names(read.clarity_section(s,guide),s)+'<section id="method"><h2>Method and evidence</h2>'+markdown(METHOD)+'<p><a href="statistics.json">Aggregates</a> · <a href="model_statistics.csv">Model CSV</a> · <a href="category_scores.csv">Category CSV</a> · <a href="october29_timing_evidence.csv">New answer-free timing evidence</a> · <a href="execution_protocol.json">Settings</a> · <a href="audit_receipt.json">Audit</a> · <a href="../consolidated_2026-10-19/questions_1342.csv">Questions</a> · <a href="../local_m2_2026-10-28/report.html">Previous report and setup details</a> · <a href="https://etsabary.github.io/visual-decision-benchmark/report.html">Image report</a></p></section></main></body></html>'
 page=head+body;write(DEST/'report.html',page);write(DEST/'analysis.md',FINDINGS+'\n\n## Method\n\n'+METHOD)
 for p in DEST.glob('*.svg'):write(p,'\n'.join(x.rstrip() for x in p.read_text().splitlines()))
 write(DEST/'manifest.json',dict(version='adaptive-october29-1342-v1',models=60,questions_each=1342,adaptive_model_ids=[AUTO],prior_statistics_sha256=digest(OLD/'statistics.json'),artifacts={p.name:digest(p) for p in sorted(DEST.iterdir()) if p.is_file() and p.name!='manifest.json'}))
 shutil.copytree(DEST,ROOT/'docs'/NAME,dirs_exist_ok=True);write(ROOT/'docs/report.html',previous.prior.tables.prior.rebase(page,NAME))
 for name,anchor in [('index.html',''),('functions.html','#functions'),('output_compliance.html','#method')]:write(ROOT/'docs'/name,'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta http-equiv="refresh" content="0;url=report.html'+anchor+'"><title>System 1 Decision Benchmark</title></head><body><a href="report.html'+anchor+'">Current 60-configuration comparison</a></body></html>')
 write(ROOT/'docs/sitemap.xml','<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url><loc>'+SITE+'</loc><lastmod>2026-10-29</lastmod></url></urlset>');previous.bind_layout()
 print('Built 60 configurations, including one framed purple adaptive model; 56 earlier records unchanged; no inference.')
if __name__=='__main__':
 if '--capture' in sys.argv:capture()
 build()
