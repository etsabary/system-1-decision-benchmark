"""Build a presentation-only successor to the frozen v3 release."""
import argparse,csv,hashlib,html,json,math,shutil,sys,textwrap
from decimal import Decimal
from pathlib import Path
REPO=Path(__file__).resolve().parents[1]
SOURCE=None
NAME='system1_v4_hosted_2026-11-02'
parser=argparse.ArgumentParser()
parser.add_argument('--source',type=Path,required=True)
parser.add_argument('--output',type=Path,required=True,help='New, empty destination outside the frozen v3 release')
args=parser.parse_args()
SOURCE=args.source.resolve()
OUT=args.output.resolve()
if OUT==SOURCE.resolve() or SOURCE.resolve() in OUT.parents or OUT.exists():
 raise SystemExit('Refusing to overwrite an existing destination or the frozen v3 release')
shutil.copytree(SOURCE,OUT)
sys.path.insert(0,str(REPO/'scripts'))
import publish_system1_v2_presentation as style
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import numpy as np

s=json.loads((OUT/'statistics.json').read_text());models=s['models'];mids=s['ranked_model_ids'];guide=json.loads((OUT/'category_guide.json').read_text());cost=json.loads((OUT/'cost_statistics.json').read_text())['models']
with (OUT/'all_category_scores.csv').open(newline='') as f:cats=list(csv.DictReader(f))
lookup={(x['model_id'],x['family_id']):x for x in cats};assert len(mids)>0 and len(lookup)==len(models)*43
cost_floor=min([.001]+[float(cost[mid]['known_usd_per_1000'])*.5 for mid in mids if cost[mid]['known_usd_per_1000'] is not None and Decimal(cost[mid]['known_usd_per_1000'])>0])
groups=style.GROUPS+[('numerical','IQ sequences and admissions-style mathematics',['F32','F33'])]
style.GROUPS=groups
esc=lambda x:html.escape(str(x),quote=True)
def cv(mid):
 c=cost[mid]
 if c['local_unmeasured_count']:return 'Unmetered local', 'Hardware and electricity unmeasured'
 if c['known_usd_per_1000'] is None:return 'Unknown',f"{c['unknown_count']} charges unknown"
 value=Decimal(c['known_usd_per_1000']);suffix=' + ?' if c['unknown_count'] else ''
 basis=f"{c['reported_count']} reported; {c['tariff_estimate_count']} estimates; {c['free_access_tariff_count']} free-access; {c['unknown_count']} unknown"
 if not value and c['free_access_tariff_count'] and c['unknown_count']:return 'Free access + ?',basis
 return '$'+f'{value:.5f}'+suffix,basis

def total_cost(mid):
 c=cost[mid]
 if c['local_unmeasured_count']:return 'Unmetered local'
 if c['known_subtotal_usd'] is None:return 'Unknown'
 value=Decimal(c['known_subtotal_usd'])
 if not value and c['free_access_tariff_count'] and c['unknown_count']:return 'Free access + ?'
 if not value and c['free_access_tariff_count'] and not c['reported_count'] and not c['tariff_estimate_count']:return 'Free access*'
 return '$'+f'{value:.5f}'+(' + ?' if c['unknown_count'] else '')

def cost_band(mid):
 c=cost[mid];value=c['known_usd_per_1000']
 if c['local_unmeasured_count'] or value is None:return None
 if Decimal(value)==0 and c['free_access_tariff_count'] and not c['reported_count'] and not c['tariff_estimate_count']:return None
 return style.cost_band(Decimal(value))

def cost_cell(mid, total=False, verbose=True):
 value,basis=cv(mid);value=total_cost(mid) if total else value;band=cost_band(mid)
 bg=style.GRAY if band is None else style.BANDS[band]
 label='Unmetered / unknown' if band is None else style.BAND_NAMES[band]
 if verbose:detail=label+' · '+basis
 else:
  c=cost[mid]
  evidence='reported + estimated' if c['reported_count'] and c['tariff_estimate_count'] else 'estimate' if c['tariff_estimate_count'] else 'reported' if c['reported_count'] else 'access terms' if c['free_access_tariff_count'] else 'unmeasured'
  detail=label+' · '+evidence+(' · missing charges' if c['unknown_count'] else '')
 return f'<td class="cost {"incomplete" if cost[mid]["unknown_count"] else ""}" style="background:{bg}" data-cost-band="{band if band is not None else "unknown"}">{esc(value)}<small>{esc(detail)}</small></td>'

def cost_mark(mid):
 band=cost_band(mid)
 return '⬜' if band is None else ['🟩','🟨','🟧','🟥'][band]

def speed_mark(ms):return ['🟩','🟨','🟧','🟥'][style.speed_band(ms)]

plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'svg.hashsalt':'system1-v4-2026-11-02'})
def save(fig,name):
 fig.savefig(OUT/(name+'.png'),dpi=150,bbox_inches='tight',metadata={'Description':json.dumps({'model_ids':mids,'minimum_overall_accuracy':.62})})
 fig.savefig(OUT/(name+'.svg'),bbox_inches='tight',metadata={'Date':None,'Description':json.dumps({'model_ids':mids,'minimum_overall_accuracy':.62})})
 plt.close(fig)
 svg=OUT/(name+'.svg');svg.write_text('\n'.join(line.rstrip() for line in svg.read_text().splitlines())+'\n')

fig,axes=plt.subplots(1,3,figsize=(21,13),sharey=True,gridspec_kw={'width_ratios':[1.1,1.15,1.15]});a,b,c=axes;y=np.arange(len(mids))
colors=[style.ROLE_COLORS[models[mid]['role']] for mid in mids];a.barh(y,[100*models[mid]['accuracy'] for mid in mids],color=colors,height=.64);a.set_yticks(y,[models[mid]['label'] for mid in mids]);a.invert_yaxis();a.set_xlim(0,105)
for lab,mid in zip(a.get_yticklabels(),mids):lab.set_color(style.ROLE_COLORS[models[mid]['role']]);lab.set_fontweight('bold')
for iy,mid in enumerate(mids):
 m=models[mid];a.text(100*m['accuracy']+.7,iy,f"{m['accuracy']:.2%}",va='center',fontsize=9)
 b.plot([m['median_ms'],m['p95_ms']],[iy,iy],color='#9ca7b0',lw=1)
 for v,mark in [(m['median_ms'],'o'),(m['p95_ms'],'D')]:b.scatter(v,iy,marker=mark,s=48,facecolor=style.BANDS[style.speed_band(v)],edgecolor='#263d48',linewidth=.5,zorder=3)
 b.text(1.02,iy,f"{m['median_ms']:,.0f} / {m['p95_ms']:,.0f}",transform=b.get_yaxis_transform(),va='center',fontsize=8)
 val,_=cv(mid);cs=cost[mid];amount=cs['known_usd_per_1000']
 if amount is None or float(amount)==0:c.text(.02,iy,val,transform=c.get_yaxis_transform(),va='center',fontsize=8)
 else:
  k=float(amount);c.scatter(k,iy,marker='D' if cs['tariff_estimate_count'] else 'o',s=48,facecolor=style.BANDS[style.cost_band(k)],edgecolor='#263d48',linewidth=.5)
  c.annotate(val,(k,iy),xytext=(5,0),textcoords='offset points',va='center',fontsize=8,color='#8e440c' if cs['unknown_count'] else '#17212c')
a.set_title('ACCURACY',loc='left',fontweight='bold');a.set_xlabel('Correct / 2,157 · operational accuracy (%)')
b.set_title('COMPLETE RESPONSE',loc='left',fontweight='bold');b.set_xscale('log');b.set_xlabel('Milliseconds · ● median / ◆ p95')
c.set_title('COST / 1,000 QUESTIONS',loc='left',fontweight='bold');c.set_xscale('log');c.set_xlim(cost_floor,35);c.set_xlabel('USD · ● reported / ◆ estimated')
for ax in axes:ax.spines[['top','right','left']].set_visible(False);ax.grid(axis='x',alpha=.16);ax.set_axisbelow(True);ax.tick_params(axis='y',length=0)
fig.subplots_adjust(left=.24,right=.97,top=.91,bottom=.11,wspace=.55);fig.suptitle('System 1 Decision Benchmark v4',x=.04,y=.98,ha='left',fontsize=24,fontweight='bold');fig.text(.04,.945,'2,157 questions · 43 categories · qualifying configurations above the 62% cutoff',fontsize=13)
fig.text(.04,.045,'Teal: hosted   Purple: local   Gold: reasoning-disabled LLM references. Timing and cost colours use fixed bands.',fontsize=10)
fig.text(.04,.023,'+ ? = known subtotal with unknown charges; unmetered local excludes hardware/electricity. Quantitative items were selected from model misses; these scores are selection-biased.',fontsize=10)
save(fig,'overview')

# A single three-column image shrinks labels on the GitHub page and phones.
# These three full-width companions keep the same ordering and colour bands.
for kind,title in [('accuracy','Accuracy'),('latency','Response time'),('cost','Cost per 1,000 questions')]:
 fig,ax=plt.subplots(figsize=(11.5,14.8));yy=np.arange(len(mids))
 ax.set_yticks(yy,[models[mid]['label'] for mid in mids],fontsize=13);ax.invert_yaxis()
 for lab,mid in zip(ax.get_yticklabels(),mids):lab.set_color(style.ROLE_COLORS[models[mid]['role']]);lab.set_fontweight('bold')
 if kind=='accuracy':
  ax.barh(yy,[100*models[mid]['accuracy'] for mid in mids],color=[style.ROLE_COLORS[models[mid]['role']] for mid in mids],height=.66)
  ax.set_xlim(0,110);ax.set_xlabel('Correct / 2,157 · operational accuracy (%)',fontsize=13)
  for iy,mid in enumerate(mids):ax.text(100*models[mid]['accuracy']+1,iy,f"{models[mid]['accuracy']:.2%}",va='center',fontsize=12)
 elif kind=='latency':
  ax.set_xscale('log');ax.set_xlabel('Milliseconds · ● median / ◆ p95',fontsize=13)
  for iy,mid in enumerate(mids):
   m=models[mid];ax.plot([m['median_ms'],m['p95_ms']],[iy,iy],color='#7b8e98',lw=1.5)
   for value,marker in [(m['median_ms'],'o'),(m['p95_ms'],'D')]:ax.scatter(value,iy,marker=marker,s=65,facecolor=style.BANDS[style.speed_band(value)],edgecolor='#263d48',linewidth=.8,zorder=3)
   ax.text(1.02,iy,f"{m['median_ms']:,.0f} / {m['p95_ms']:,.0f}",transform=ax.get_yaxis_transform(),va='center',fontsize=11)
  ax.set_xlim(min(models[mid]['median_ms'] for mid in mids)*.75,max(models[mid]['p95_ms'] for mid in mids)*1.2)
 else:
  ax.set_xscale('log');ax.set_xlim(cost_floor,35);ax.set_xlabel('USD / 1,000 · ● reported / ◆ tariff estimate',fontsize=13)
  for iy,mid in enumerate(mids):
   value,_=cv(mid);c=cost[mid];known=c['known_usd_per_1000'];band=cost_band(mid)
   if known is None or Decimal(known)==0:ax.text(.02,iy,value,transform=ax.get_yaxis_transform(),va='center',fontsize=11)
   else:
    v=float(known);ax.scatter(v,iy,marker='D' if c['tariff_estimate_count'] else 'o',s=65,facecolor=style.GRAY if band is None else style.BANDS[band],edgecolor='#263d48',linewidth=.8)
    ax.annotate(value,(v,iy),xytext=(6,0),textcoords='offset points',va='center',fontsize=11,color='#8e440c' if c['unknown_count'] else '#17212c')
 ax.spines[['top','right','left']].set_visible(False);ax.grid(axis='x',alpha=.16);ax.set_axisbelow(True);ax.tick_params(axis='y',length=0);ax.tick_params(axis='x',labelsize=11)
 fig.subplots_adjust(left=.41,right=.87 if kind=='latency' else .94,top=.91,bottom=.10)
 fig.suptitle(title,x=.04,y=.975,ha='left',fontsize=22,fontweight='bold');fig.text(.04,.945,'System 1 v4 · 2,157 questions · qualifying configurations above the 62% cutoff',fontsize=12)
 fig.text(.04,.035,'Teal: hosted · Purple: local · Gold: reasoning-disabled LLMs. Colour bands and cost qualifications appear in the table.',fontsize=10)
 fig.text(.04,.016,'Quantitative items were selected from model misses; these scores are selection-biased.',fontsize=10)
 save(fig,'comparison_'+kind)

for slug,title,fids in groups:
 a=np.array([[float(lookup[mid,fid]['accuracy']) for fid in fids] for mid in mids]);best=a.max(axis=0)
 fig,ax=plt.subplots(figsize=(13,15));im=ax.imshow(a,vmin=0,vmax=1,cmap='YlGnBu',aspect='auto');ax.set_yticks(range(len(mids)),[models[mid]['label'] for mid in mids],fontsize=12)
 for label,mid in zip(ax.get_yticklabels(),mids):label.set_color(style.ROLE_COLORS[models[mid]['role']]);label.set_fontweight('bold')
 names=[fid+'\n'+'\n'.join(textwrap.wrap(guide[fid]['display_name'],16))+f"\nn = {guide[fid]['questions']}" for fid in fids];ax.set_xticks(range(len(fids)),names,fontsize=11);ax.tick_params(top=True,labeltop=True,bottom=False,labelbottom=False,length=0,pad=10)
 ax.set_xticks(np.arange(-.5,len(fids)),minor=True);ax.set_yticks(np.arange(-.5,len(mids)),minor=True);ax.grid(which='minor',color='white',linewidth=1);ax.tick_params(which='minor',bottom=False,left=False)
 for iy,mid in enumerate(mids):
  for ix,fid in enumerate(fids):
   row=lookup[mid,fid];_,fg=style.accuracy_colors(a[iy,ix]);lead=a[iy,ix]==best[ix]
   ax.text(ix,iy,f"{row['correct']}/{row['n']}"+(' ★' if lead else '')+f"\n{a[iy,ix]:.1%}",ha='center',va='center',fontsize=12,color=fg)
   if lead:ax.add_patch(Rectangle((ix-.46,iy-.45),.92,.90,fill=False,edgecolor=fg,linewidth=1.1))
 bar=fig.colorbar(im,ax=ax,orientation='horizontal',fraction=.025,pad=.025,ticks=[0,.2,.4,.6,.8,1]);bar.ax.set_xticklabels(['0%','20%','40%','60%','80%','100%']);bar.set_label('Absolute accuracy · fixed scale across every group · ★ tied leaders')
 fig.suptitle(title,x=.02,y=.995,fontsize=19,fontweight='bold',ha='left');fig.text(.02,.008,'Same overall model order. The 62% cutoff applies to overall accuracy, not category scores.',fontsize=10);fig.subplots_adjust(left=.37,top=.86,bottom=.065,right=.985);save(fig,'categories_'+slug)
style.legend_graphic(OUT)

overall=[];more_rows=[];mobile_cards=[];costrows=[]
for mid in mids:
 m=models[mid];value,basis=cv(mid);coverage=f"{m['valid']}/{m['n']} ({m['coverage']:.2%})";detail=f"{m['accuracy']:.2%}"+(f"–{m['accuracy_upper_if_all_unusable_correct']:.2%} possible" if m['valid']<m['n'] else '')
 overall.append('<tr data-overall-model="'+esc(mid)+'"><td>'+style.model_name(mid,models)+'</td><td>'+f"{m['correct']:,}/{m['n']:,}<small>{detail}</small></td>"+style.speed_cell(m['median_ms'])+style.speed_cell(m['p95_ms'])+cost_cell(mid,True,False)+cost_cell(mid,False,False)+f"<td>{coverage}</td></tr>")
 more_rows.append('<tr data-overall-model="'+esc(mid)+'"><td>'+style.model_name(mid,models)+f"</td><td>{m['added_correct']}/140</td><td>{m['macro_category_accuracy']:.2%}</td><td>{m['answer_accuracy_among_usable']:.2%}</td><td>{coverage}</td></tr>")
 med=style.BANDS[style.speed_band(m['median_ms'])];tail=style.BANDS[style.speed_band(m['p95_ms'])];band=cost_band(mid);moneybg=style.GRAY if band is None else style.BANDS[band]
 medband=style.speed_band(m['median_ms']);tailband=style.speed_band(m['p95_ms']);costlabel='Unmetered / unknown' if band is None else style.BAND_NAMES[band]
 mobile_cards.append('<article class="mobile-card" data-overall-model="'+esc(mid)+'"><h3>'+style.model_name(mid,models)+'</h3><div class="mobile-grid"><div><strong>'+f"{m['accuracy']:.2%}</strong><span>Accuracy · {m['correct']:,}/{m['n']:,}</span></div>"+f'<div><strong>{m["valid"]:,}/{m["n"]:,}</strong><span>Usable responses</span></div><div style="background:{med}" data-mobile-speed-band="{medband}"><strong>{m["median_ms"]:,.0f} ms</strong><span>Median · {style.BAND_NAMES[medband]}</span></div><div style="background:{tail}" data-mobile-speed-band="{tailband}"><strong>{m["p95_ms"]:,.0f} ms</strong><span>p95 · {style.BAND_NAMES[tailband]}</span></div><div style="background:{moneybg}" data-mobile-cost-band="{band if band is not None else "unknown"}"><strong>{esc(total_cost(mid))}</strong><span>Total known cost · {costlabel}</span></div><div style="background:{moneybg}" data-mobile-cost-band="{band if band is not None else "unknown"}"><strong>{esc(value)}</strong><span>Cost per 1,000 · {costlabel}</span></div></div><p>'+esc(basis)+'</p></article>')
for mid in sorted(models,key=lambda x:(-models[x]['accuracy'],x)):
 cs=cost[mid];value,basis=cv(mid);costrows.append('<tr><td>'+style.model_name(mid,models)+'</td>'+cost_cell(mid)+cost_cell(mid,True)+'<td>'+esc(basis)+'</td></tr>')
def table(head,rows):return '<div class="scroll"><table><thead><tr>'+''.join('<th>'+esc(x)+'</th>' for x in head)+'</tr></thead><tbody>'+''.join(rows)+'</tbody></table></div>'
group_html,rank_html=style.category_html(s,guide,lookup,'')
catalog=''.join(f"<li>{esc(models[mid]['label'])}: {models[mid]['correct']}/2,157 ({models[mid]['accuracy']:.2%}); coverage {models[mid]['coverage']:.2%}.</li>" for mid in s['below_cutoff'])
legend='''<ul><li>Teal, purple and gold model names indicate hosted decision, local and reasoning-disabled LLM configurations.</li><li>Category cells use one fixed pale-yellow to dark-blue 0–100% scale. Each shows correct/total and percentage; ★ marks all tied leaders.</li><li>Speed and known cost use fixed green / yellow / orange / red bands: median or p95 ≤250 / ≤500 / ≤1,000 / &gt;1,000 ms; cost ≤$0.010 / ≤$0.025 / ≤$0.050 / &gt;$0.050 per 1,000 questions.</li><li>Cost markers ● / ◆ mean reported amounts / captured tariff estimates. “+ ?” means charges are missing; local costs are unmetered.</li></ul>'''
notes='''<p class="note"><strong>Selection bias:</strong> the original 60 quantitative items were selected because Fastino and D3 Artemis missed them. The 140 new items were selected because at least one of Fastino, Mammoth, GPT-6 Sol without reasoning, D3 Ultra and Drex Max missed them. This distributes but does not eliminate bias. Public questions may appear in model training data.</p><p class="note"><strong>Rights caveat:</strong> MAIQ declares MIT, but the original rights holders of its 23 IQ-test questions are unknown. The owner chose inclusion with that caveat. AQuA declares Apache-2.0 and describes crowdsourced admissions-style mathematics, not verified official exam questions. <a href="SOURCE_AND_LICENSES.md">Full provenance and terms</a> · <a href="source_metadata_2157.jsonl">Question-level metadata</a>.</p>'''
body='<p class="eyebrow">An empirical map of fast, structured decisions · November 2, 2026</p><h1>System 1 Decision Benchmark v4</h1><p class="lead">A 2,157-question, 43-category comparison of decision accuracy, speed, coverage and available cost evidence.</p>'+notes
body+='<nav><a href="#overview">Accuracy, speed &amp; cost</a><a href="#legend">Colour key</a><a href="#categories">Category matrices</a><a href="#rankings">Individual rankings</a><a href="#cost">Cost evidence</a><a href="#method">Method and downloads</a></nav>'
body+='<section id="overview"><h2>Accuracy, speed and cost together</h2><p>Every row includes the known total cost and cost per 1,000 questions. Coloured bands use the thresholds in the key below; + ? marks missing charges.</p><label>Find a model <input id="model-search" type="search" placeholder="Model or deployment"></label><p id="model-empty" role="status" hidden>No models match this search.</p>'
body+='<div class="comparison-table">'+table(['Configuration','Correct / tested · possible range','Median','p95','Total known USD','USD / 1,000','Usable'],overall)+'</div><div class="mobile-cards">'+''.join(mobile_cards)+'</div>'
body+='<details><summary>Additional accuracy and coverage measures</summary>'+table(['Configuration','140 additions','Equal-category','Accuracy among usable','Usable'],more_rows)+'</details>'
body+='<p class="figure-caption">Larger individual graphs keep labels readable. Open the SVG for full resolution.</p>'
for kind,title in [('accuracy','Accuracy'),('latency','Response time'),('cost','Cost per 1,000 questions')]:
 body+=f'<h3>{title}</h3><div class="chart-scroll"><a href="comparison_{kind}.svg"><img src="comparison_{kind}.png" alt="{title} for the qualifying configurations, with the same model order"></a></div>'
body+='<p><a href="overview.svg">Download the combined overview (SVG)</a></p>'
body+='<p>Operational accuracy uses all 2,157 questions as the denominator; an unusable response is not credited as correct. Coverage identifies those responses. The possible-range upper endpoint assumes every unusable response would have been correct; it is a bound, not an estimate. An unusable response is not evidence that the model would have chosen incorrectly. Timings pool individual primary records, include failed calls and network time, and use linear-interpolated p95. Collection dates, hardware and routes differ.</p><h3>Below the 62% cutoff</h3><p>These configurations were measured on v4 and are retained in all data downloads.</p><ul>'+catalog+'</ul></section>'
body+='<section id="legend"><h2>How to read the colours</h2><img class="legend-graphic" src="accuracy_legend.png" alt="Fixed zero to 100 percent category accuracy scale">'+legend+'</section>'
body+='<section id="categories"><h2>43 categories: a visible map of strengths</h2><p>The same model order and 0–100% accuracy scale are used in each matrix. The numeric categories have 23 and 200 questions respectively; the model cohort is selected once by overall accuracy.</p>'+group_html+'</section>'
body+='<section id="rankings"><h2>Rankings within each category</h2><p>Accuracy ties share a competition rank; timings do not break the tie.</p><label>Choose a category <select id="category-select"><option value="">All categories</option>'+''.join(f'<option value="{esc(fid)}">{esc(fid)} · {esc(guide[fid]["display_name"])}</option>' for fid in sorted(guide))+'</select></label>'+rank_html+'</section>'
body+='<section id="cost"><h2>Cost evidence and missing charges</h2><p>Costs are per selected primary record, combining API-reported charges, contemporaneous tariff estimates, free-access records, unknown charges and unmetered locals. Values per 1,000 use the known subtotal divided by 2,157 and are not a complete price when records are unknown. We do not extrapolate historical tariffs to the new questions.</p>'+table(['Configuration','Known USD / 1,000','Known subtotal USD','Evidence counts'],costrows)+'</section>'
partial=json.loads((OUT/'partial_models.json').read_text())
if partial:
 body+='<section id="partial"><h2>Incomplete exploratory tests</h2><p>These partial, unstratified samples are not included in the full-bank rankings or cutoff.</p><ul>'
 for x in partial:
  body+=f'<li>{esc(x["model"])}: {x["sample_correct"]}/{x["sample_n"]} correct on a seeded subset; SubQ scored {x["subq_correct_on_same_inputs"]}/{x["sample_n"]} on those exact inputs. The provider marked {x["provider_extrapolated_count"]} inputs beyond its stated training length. Its usage window stopped the run; this is not a full-bank score.</li>'
 body+='</ul><p><a href="partial_models.json">Partial test details</a></p></section>'
body+='<section id="method"><h2>Method, provenance and downloads</h2><p>All 2,017 v3 inputs and selected primary responses are retained. The 140 additions use new first responses or matching earlier exact-input screening responses; answers are never selected by correctness. Where Drex 2.0 initially returned HTTP 429 without a model answer, the first subsequently returned answer was retained. Timing and cost for those items cover the selected answer, not preceding failed attempts; recovery evidence is available below. Source-key agreement and two reviews support the additions but do not prove uniqueness or guarantee an error-free key. Kimi was asked for maximum reasoning but did not report its effective effort.</p><p>V4 contains 23 number sequences and 200 quantitative items. V3 and v2 remain available unchanged; the separate 120 companion diagnostics are excluded from the 2,157 denominator. Newly added decision models use separate full-bank direct-API sessions and do not replace prior responses. The three language-model references have reasoning disabled.</p><h3>Configuration and collection notes</h3><p>Provider model declarations are not independent attestations of hidden weights. Latency pools individual responses collected in different sessions, routes and worker concurrency; differences in load limit direct speed comparisons.</p><div class="scroll"><table><thead><tr><th>Configuration</th><th>Recorded setting</th><th>Collection dates, Toronto</th><th>Limits</th></tr></thead><tbody>'
for mid in sorted(models,key=lambda x:(-models[x]['accuracy'],x)):
 m=models[mid];dates=', '.join(f'{day}: {count}' for day,count in sorted(m['collection_dates_toronto'].items()))
 body+='<tr><td>'+style.model_name(mid,models)+'</td><td>'+esc(m['configuration'])+'</td><td>'+esc(dates)+'</td><td>'+esc(m['identity_limit'])+' '+esc(m['new_collection_limit'])+'</td></tr>'
body+='</tbody></table></div><ul>'
for name,label in [('questions_2157.jsonl','Answer-free questions'),('source_metadata_2157.jsonl','Question-level origin and license metadata'),('SOURCE_AND_LICENSES.md','Source and license notes'),('statistics.json','All model summaries'),('all_category_scores.csv','All models by 43 categories'),('timing_evidence.csv.gz','Answer-free timing and status evidence'),('cost_evidence.csv.gz','Per-question cost evidence'),('cost_statistics.json','Cost summaries'),('category_guide.json','Category guide'),('transport_recoveries.json','Prior no-answer HTTP 429 recovery evidence'),('model_collection_recoveries.json','New-model recovery evidence'),('model_context_diagnostics.json','New-model context diagnostics'),('partial_models.json','Incomplete exploratory model results'),('audit_receipt.json','Audit receipt'),('manifest.json','Release checksums')]:body+=f'<li><a href="{name}">{esc(label)}</a></li>'
body+='</ul></section>'
js="document.getElementById('model-search').addEventListener('input',function(){const q=this.value.toLowerCase();document.querySelectorAll('[data-overall-model]').forEach(r=>r.hidden=!r.textContent.toLowerCase().includes(q));document.getElementById('model-empty').hidden=[...document.querySelectorAll('.mobile-card')].some(r=>!r.hidden);});document.getElementById('category-select').addEventListener('change',function(){document.querySelectorAll('.category').forEach(r=>{r.hidden=!!this.value&&r.dataset.family!==this.value;if(this.value&&r.dataset.family===this.value)r.open=true;});});"
responsive_css='''.comparison-table table{font-size:14px}.comparison-table .cost{min-width:145px}.mobile-cards{display:none}.chart-scroll{overflow-x:auto}.chart-scroll img{width:100%;max-width:1100px}.mobile-card[hidden]{display:none!important}@media(max-width:700px){.comparison-table{display:none}.mobile-cards{display:grid;gap:14px}.mobile-card{border:1px solid #b9c9ce;background:#fff;padding:14px}.mobile-card h3{margin:0 0 12px;font-size:17px}.mobile-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:6px}.mobile-grid>div{padding:10px;border:1px solid #d7e1e4;min-height:50px}.mobile-grid strong,.mobile-grid span{display:block}.mobile-grid span{font-size:12px}.mobile-card p{margin:10px 0 0;font-size:12px}.chart-scroll img{min-width:750px}}'''
page='<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="description" content="2,157 decision questions, 43 categories, and qualifying configurations with cost and coverage evidence."><title>System 1 Decision Benchmark v4</title><style>'+style.CSS+responsive_css+'</style></head><body><main>'+body+'</main><script>'+js+'</script></body></html>'
(OUT/'report.html').write_text(page)

readme='# System 1 Decision Benchmark v4\n\n'
readme+='This benchmark compares accuracy, latency, coverage and cost for fixed-option decision tasks. V4 contains **2,157 questions across 43 categories**: the unchanged 2,017-question v3 bank plus 140 source-key-supported AQuA questions. The 23 numerical-pattern and 200 quantitative questions are borrowed; the earlier project bank is predominantly project-developed. The previously measured 26 configurations remain in the downloads; newly measured models are added on the same full bank. Main comparisons use a 62% operational-accuracy cutoff.\n\n'
readme+='**Selection bias:** the original 60 quantitative questions were selected for Fastino and D3 Artemis errors; the 140 new questions were selected for an error by at least one of Fastino, Mammoth, GPT-6 Sol without reasoning, D3 Ultra and Drex Max. This distributes, but does not remove, selection bias.\n\n'
readme+='**Source and rights:** AQuA-RAT is crowdsourced admissions-style mathematics under its repository’s Apache-2.0 terms; it is not a set of authenticated official GRE or SAT questions. MAIQ’s repository declares MIT, but its authors collected questions from human IQ tests and the original rights holders for these 23 sequences are not established. The owner elected to include the sequences with that qualification. The project MIT license does not supersede these sources’ terms. [Detailed provenance and notices](results/releases/'+NAME+'/SOURCE_AND_LICENSES.md).\n\n'
readme+='[Interactive v4 report](https://etsabary.github.io/system-1-decision-benchmark/v4/report.html) · [Category rankings](https://etsabary.github.io/system-1-decision-benchmark/v4/report.html#rankings) · [Cost evidence](https://etsabary.github.io/system-1-decision-benchmark/v4/report.html#cost)\n\n'
readme+='## Reading the comparison\n\nTeal, purple and gold denote hosted decision, local and reasoning-disabled LLM configurations. The category scale is fixed from 0–100%; each cell shows correct/total, and ★ marks all tied leaders. Speed and cost use 🟩 green / 🟨 yellow / 🟧 orange / 🟥 red bands: median or p95 ≤250 / ≤500 / ≤1,000 / >1,000 ms; cost ≤$0.010 / ≤$0.025 / ≤$0.050 / >$0.050 per 1,000 questions. ⬜ means the cost is unmetered or unknown. “+ ?” denotes missing charges; known totals may include tariff estimates rather than receipts.\n\n## Main comparison\n\n| Configuration | Correct / 2,157 | Accuracy | Median | p95 | Total known cost | Cost / 1,000 | Usable | Cost evidence |\n|---|---:|---:|---:|---:|---:|---:|---:|---|\n'
for mid in mids:
 m=models[mid];value,basis=cv(mid);mark=cost_mark(mid);readme+=f"| {m['label']} | {m['correct']}/2,157 | {m['accuracy']:.2%} | {speed_mark(m['median_ms'])} {m['median_ms']:,.0f} ms | {speed_mark(m['p95_ms'])} {m['p95_ms']:,.0f} ms | {mark} {total_cost(mid)} | {mark} {value} | {m['valid']}/2,157 | {basis} |\n"
readme+='\nOperational accuracy counts unusable requests as not correct; it does not establish what answer a model would have given. The report shows coverage and results among usable responses. Timings pool individual primary records and include failed requests and network time. Data were collected on different dates and routes. A coloured known cost with + ? is only a subtotal.\n\n## Comparison graphs\n\nEach graph uses the same overall ordering and is shown separately so its labels remain readable.\n\n'
for kind,title in [('accuracy','Accuracy'),('latency','Response time'),('cost','Cost per 1,000 questions')]:
 readme+=f"### {title}\n\n![{title} comparison for the qualifying models](results/releases/{NAME}/comparison_{kind}.png)\n\n"
readme+='## Category results\n\n![Fixed accuracy scale](results/releases/'+NAME+'/accuracy_legend.png)\n\n'
for slug,title,fids in groups:
 readme+='### '+title+'\n\n'+('; '.join(fid+' '+guide[fid]['display_name'] for fid in fids))+'.\n\n!['+title+' accuracy with counts and tied leaders](results/releases/'+NAME+'/categories_'+slug+'.png)\n\n'
readme+='## Below the cutoff\n\n'
for mid in s['below_cutoff']:
 m=models[mid];readme+=f"- {m['label']}: {m['correct']}/2,157 ({m['accuracy']:.2%}); coverage {m['coverage']:.2%}.\n"
readme+='\n## Download and reproducibility\n\n'
for name,label in [('questions_2157.jsonl','Answer-free questions'),('source_metadata_2157.jsonl','Question-level origins and terms'),('SOURCE_AND_LICENSES.md','Source and license notes'),('statistics.json','All model summaries'),('all_category_scores.csv','All model/category scores'),('timing_evidence.csv.gz','Timing and status evidence'),('cost_evidence.csv.gz','Cost evidence'),('cost_statistics.json','Cost summaries'),('category_guide.json','Category guide'),('transport_recoveries.json','Prior no-answer HTTP 429 recovery evidence'),('model_collection_recoveries.json','New-model recovery evidence'),('model_context_diagnostics.json','New-model context diagnostics'),('partial_models.json','Incomplete exploratory model results'),('audit_receipt.json','Audit receipt'),('manifest.json','Release checksums')]:readme+=f'- [{label}](results/releases/{NAME}/{name})\n'
if partial:
 readme+='\n## Incomplete exploratory tests\n\n'
 for x in partial:readme+=f'- {x["model"]}: {x["sample_correct"]}/{x["sample_n"]} correct on a seeded incomplete subset; SubQ scored {x["subq_correct_on_same_inputs"]}/{x["sample_n"]} on the same inputs. This partial result is not included in the full-bank ranking.\n'
readme+='\nThe original [v4 release](results/releases/system1_v4_2026-11-02/report.html), [v3 release](results/releases/system1_v3_presentation_2026-11-01/report.html) and [v2 release](results/releases/system1_v2_presentation_2026-11-01/report.html) remain unchanged. The separate 120 companion diagnostics are not included. Model choices and the scoring key remain private. Public questions may occur in training data; scores are not human IQ norms.\n\nThe [scripts/](scripts/README.md) support offline validation without model credentials:\n\n```sh\npython3 scripts/validate_system1_v4_hosted.py results/releases/'+NAME+' results/releases/system1_v4_2026-11-02\npython3 scripts/validate_october21_release.py\n```\n'
(OUT/'README_V4.md').write_text(readme)
unchanged=['questions_2157.jsonl','source_metadata_2157.jsonl','statistics.json','all_category_scores.csv','category_guide.json','timing_evidence.csv.gz','cost_evidence.csv.gz','cost_statistics.json','audit_receipt.json','SOURCE_AND_LICENSES.md','PROJECT_LICENSE_MIT.txt']
unchanged += [str(x.relative_to(SOURCE)) for x in sorted((SOURCE/'third_party_licenses').iterdir()) if x.is_file()]
for name in unchanged:assert (OUT/name).read_bytes()==(SOURCE/name).read_bytes(),name
def filehash(p):return hashlib.sha256(p.read_bytes()).hexdigest()
files={str(p.relative_to(OUT)):filehash(p) for p in sorted(OUT.rglob('*')) if p.is_file() and p.name!='manifest.json'}
manifest={'version':'v4','questions':2157,'categories':43,'measured_models':len(models),'main_models':len(mids),'minimum_overall_accuracy':.62,'frozen_v3_manifest_sha256':filehash(REPO/'results/releases/system1_v3_presentation_2026-11-01/manifest.json'),'frozen_v4_manifest_sha256':filehash(REPO/'results/releases/system1_v4_2026-11-02/manifest.json'),'unchanged_files_sha256':{name:filehash(SOURCE/name) for name in unchanged},'files_sha256':files}
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n')
print(json.dumps({'groups':len(groups),'categories':len(guide),'main_models':len(mids),'all_models':len(models),'unchanged_data_files':len(unchanged),'report':'report.html'}))
