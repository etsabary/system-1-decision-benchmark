"""Render the audited four-model hosted successor without changing historical measurements."""
import argparse,csv,hashlib,html,json,math,shutil,sys,textwrap
from decimal import Decimal
from pathlib import Path
REPO=Path(__file__).resolve().parents[1]
SOURCE=None
NAME='system1_v5_hosted_refresh_2026-11-13'
parser=argparse.ArgumentParser()
parser.add_argument('--source',type=Path,required=True)
parser.add_argument('--output',type=Path,required=True,help='New, empty destination outside the frozen earlier release')
args=parser.parse_args()
SOURCE=args.source.resolve()
OUT=args.output.resolve()
if OUT==SOURCE.resolve() or SOURCE.resolve() in OUT.parents or OUT.exists():
 raise SystemExit('Refusing to overwrite an existing destination or the frozen earlier release')
shutil.copytree(SOURCE,OUT)
sys.path.insert(0,str(REPO/'scripts'))
import publish_system1_v2_presentation as style
style.ROLE_COLORS = {**style.ROLE_COLORS, "Local distributed": "#b2364b"}
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import numpy as np

s=json.loads((OUT/'statistics.json').read_text());models=s['models'];mids=s['ranked_model_ids'];guide=json.loads((OUT/'category_guide.json').read_text());cost=json.loads((OUT/'cost_statistics.json').read_text())['models']
with (OUT/'all_category_scores.csv').open(newline='') as f:cats=list(csv.DictReader(f))
lookup={(x['model_id'],x['family_id']):x for x in cats};assert len(mids)>0 and len(lookup)==len(models)*43
threshold=s['inclusion_threshold'];cutoff=threshold['numerator']/threshold['denominator']
assert s['questions']==1456 and threshold['percent']==45 and threshold['minimum_correct']==656
threshold_label='45% (at least 656/1,456 correct)'
provenance=json.loads((OUT/'selection_provenance.json').read_text())
v4=json.loads((REPO/'results/releases/system1_v4_openai_2026-11-06/statistics.json').read_text())
baseline=json.loads((REPO/'results/releases/system1_v5_gemini_decision1_2026-11-13/statistics.json').read_text())
new_ids={'pplx_decider13_native_20261112','pplx_decider_flash13_native_20261112','heygen_decision1_openrouter_20261112','heygen_decision1_turbo_openrouter_20261112'}
assert set(models)-set(baseline['models'])==new_ids
assert all(models[mid]==value for mid,value in baseline['models'].items())
baseline_cost=json.loads((REPO/'results/releases/system1_v5_gemini_decision1_2026-11-13/cost_statistics.json').read_text())['models']
assert all(cost[mid]==value for mid,value in baseline_cost.items())
assert models['drex_max_v11']['n']==1456
comparison=json.loads((OUT/'drex_comparison.json').read_text())
superseded=s.get('superseded_model_ids',[])
assert set(models)==set(mids)|set(s['below_cutoff'])|set(superseded)
assert not set(superseded)&(set(mids)|set(s['below_cutoff']))
replacement=comparison['replacement_decision']
assert replacement in ['supersede_old_active_configuration','retain_both_configurations']
assert ('drex_max' in superseded)==(replacement=='supersede_old_active_configuration')
assert models['morph_reflex']['n']==models['reax_1_3']['n']==1456
selection_note=OUT/'V5_SELECTION_NOTES.md'
initial_selection_body=selection_note.read_text()
if initial_selection_body.startswith('# Historical initial v5 selection notes only'):
 initial_selection_body=initial_selection_body.split('\n\n---\n\n',1)[1]
selection_note.write_text('# Historical initial v5 selection notes only\n\n'
 'The original body below describes the initial 32-configuration, 26-model provisional v5 '
 'recalculation and its reuse-only inference scope. This four-model hosted successor has '
 f'{len(models)} complete configurations and {len(mids)} active graph models. It preserves '
 'all earlier sessions and adds four separately audited native hosted tests. '
 'The 1,456-question bank, original removal cohort and 45% cutoff are unchanged. '
 'See [DREX_VERSION_NOTES.md](DREX_VERSION_NOTES.md), '
 '[prior hosted-session notes](HOSTED_MODEL_NOTES.md) and '
 '[current results](statistics.json) for the applicable versions and scopes. '
 'The original selection-note body follows as historical provenance.\n\n---\n\n'
 +initial_selection_body)
cost_floor=min([.001]+[float(cost[mid]['known_usd_per_1000'])*.5 for mid in mids if cost[mid]['known_usd_per_1000'] is not None and Decimal(cost[mid]['known_usd_per_1000'])>0])
groups=style.GROUPS+[('numerical','IQ sequences and admissions-style mathematics',['F32','F33'])]
style.GROUPS=groups
esc=lambda x:html.escape(str(x),quote=True)
def ordinal(n):return str(n)+('th' if 10<=n%100<=20 else {1:'st',2:'nd',3:'rd'}.get(n%10,'th'))
def has_estimate(c):return bool(c['tariff_estimate_count'] or c.get('fx_estimate_count',0))

def cv(mid):
 c=cost[mid]
 if c['local_unmeasured_count']:return 'Unmetered local', 'Hardware and electricity unmeasured'
 if c['known_usd_per_1000'] is None:return 'Unknown',f"{c['unknown_count']} charges unknown"
 value=Decimal(c['known_usd_per_1000']);suffix=' + ?' if c['unknown_count'] else ''
 basis=f"{c['reported_count']} reported; {c['tariff_estimate_count']} estimates; {c['free_access_tariff_count']} free-access; {c['unknown_count']} no-price/usage"
 if c.get('actual_charge_telemetry')=='unreported':basis+='; actual API charges unreported' 
 if c.get('fx_estimate_count',0):
  basis=f"EUR {c['native_reported_subtotal']} reported ({c['native_reported_count']} records); {c['fx_estimate_count']} USD FX estimates; {c['unknown_count']} unknown"
  return '$'+f'{value:.5f}'+' FX est.'+suffix,basis
 if not value and c['free_access_tariff_count'] and c['unknown_count']:return 'Free access + ?',basis
 return '$'+f'{value:.5f}'+suffix,basis

def total_cost(mid):
 c=cost[mid]
 if c['local_unmeasured_count']:return 'Unmetered local'
 if c['known_subtotal_usd'] is None:return 'Unknown'
 value=Decimal(c['known_subtotal_usd'])
 if c.get('fx_estimate_count',0):return '$'+f'{value:.5f}'+' FX est.'+(' + ?' if c['unknown_count'] else '')
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
  if c.get('fx_estimate_count',0):evidence=f"FX estimate · EUR {c['native_reported_subtotal']} reported"
  detail=label+' · '+evidence+(' · actual API charges unreported' if c.get('actual_charge_telemetry')=='unreported' else '')+(' · missing charges' if c['unknown_count'] else '')
 return f'<td class="cost {"incomplete" if cost[mid]["unknown_count"] else ""}" style="background:{bg}" data-cost-band="{band if band is not None else "unknown"}">{esc(value)}<small>{esc(detail)}</small></td>'

def cost_mark(mid):
 band=cost_band(mid)
 return '⬜' if band is None else ['🟩','🟨','🟧','🟥'][band]

def speed_mark(ms):return ['🟩','🟨','🟧','🟥'][style.speed_band(ms)]

plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'svg.hashsalt':'system1-v5-hosted-refresh-2026-11-13'})
def save(fig,name):
 fig.savefig(OUT/(name+'.png'),dpi=150,bbox_inches='tight',metadata={'Description':json.dumps({'model_ids':mids,'minimum_overall_accuracy':cutoff,'inclusion_threshold':threshold,'version':'v5-provisional-hosted-refresh'})})
 fig.savefig(OUT/(name+'.svg'),bbox_inches='tight',metadata={'Date':None,'Description':json.dumps({'model_ids':mids,'minimum_overall_accuracy':cutoff,'inclusion_threshold':threshold,'version':'v5-provisional-hosted-refresh'})})
 plt.close(fig)
 svg=OUT/(name+'.svg');svg.write_text('\n'.join(line.rstrip() for line in svg.read_text().splitlines())+'\n')

fig,axes=plt.subplots(1,3,figsize=(21,13*len(mids)/26),sharey=True,gridspec_kw={'width_ratios':[1.1,1.15,1.15]});a,b,c=axes;y=np.arange(len(mids))
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
  k=float(amount);c.scatter(k,iy,marker='D' if has_estimate(cs) else 'o',s=48,facecolor=style.BANDS[style.cost_band(k)],edgecolor='#263d48',linewidth=.5)
  c.annotate(val,(k,iy),xytext=(5,0),textcoords='offset points',va='center',fontsize=8,color='#8e440c' if cs['unknown_count'] else '#17212c')
a.set_title('ACCURACY',loc='left',fontweight='bold');a.set_xlabel('Correct / 1,456 · operational accuracy (%)')
b.set_title('COMPLETE RESPONSE',loc='left',fontweight='bold');b.set_xscale('log');b.set_xlabel('Milliseconds · ● median / ◆ p95')
c.set_title('COST / 1,000 QUESTIONS',loc='left',fontweight='bold');c.set_xscale('log');c.set_xlim(cost_floor,35);c.set_xlabel('USD · ● reported / ◆ estimated')
for ax in axes:ax.spines[['top','right','left']].set_visible(False);ax.grid(axis='x',alpha=.16);ax.set_axisbelow(True);ax.tick_params(axis='y',length=0)
fig.subplots_adjust(left=.24,right=.97,top=.91,bottom=.11,wspace=.55);fig.suptitle('System 1 Decision Benchmark · provisional v5',x=.04,y=.98,ha='left',fontsize=24,fontweight='bold');fig.text(.04,.945,f'1,456 questions · 43 categories · inclusion ≥{threshold_label}',fontsize=13)
fig.text(.04,.045,'Names: teal hosted · purple local · rose two-computer local · gold LLM references. Speed/cost colours retain fixed bands.',fontsize=10)
fig.text(.04,.023,'+ ? = known subtotal with unknown charges; unmetered local excludes hardware/electricity. Fixed subset of retained v4 records; cohort-conditioned selection. Full v4 remains archived.',fontsize=10)
save(fig,'overview')

# A single three-column image shrinks labels on the GitHub page and phones.
# These three full-width companions keep the same ordering and colour bands.
for kind,title in [('accuracy','Accuracy'),('latency','Response time'),('cost','Cost per 1,000 questions')]:
 fig,ax=plt.subplots(figsize=(11.5,14.8*len(mids)/26));yy=np.arange(len(mids))
 ax.set_yticks(yy,[models[mid]['label'] for mid in mids],fontsize=13);ax.invert_yaxis()
 for lab,mid in zip(ax.get_yticklabels(),mids):lab.set_color(style.ROLE_COLORS[models[mid]['role']]);lab.set_fontweight('bold')
 if kind=='accuracy':
  ax.barh(yy,[100*models[mid]['accuracy'] for mid in mids],color=[style.ROLE_COLORS[models[mid]['role']] for mid in mids],height=.66)
  ax.set_xlim(0,110);ax.set_xlabel('Correct / 1,456 · operational accuracy (%)',fontsize=13)
  for iy,mid in enumerate(mids):ax.text(100*models[mid]['accuracy']+1,iy,f"{models[mid]['accuracy']:.2%}",va='center',fontsize=12)
 elif kind=='latency':
  ax.set_xscale('log');ax.set_xlabel('Milliseconds · ● median / ◆ p95',fontsize=13)
  for iy,mid in enumerate(mids):
   m=models[mid];ax.plot([m['median_ms'],m['p95_ms']],[iy,iy],color='#7b8e98',lw=1.5)
   for value,marker in [(m['median_ms'],'o'),(m['p95_ms'],'D')]:ax.scatter(value,iy,marker=marker,s=65,facecolor=style.BANDS[style.speed_band(value)],edgecolor='#263d48',linewidth=.8,zorder=3)
   ax.text(1.02,iy,f"{m['median_ms']:,.0f} / {m['p95_ms']:,.0f}",transform=ax.get_yaxis_transform(),va='center',fontsize=11)
  ax.set_xlim(min(models[mid]['median_ms'] for mid in mids)*.75,max(models[mid]['p95_ms'] for mid in mids)*1.2)
 else:
  ax.set_xscale('log');ax.set_xlim(cost_floor,35);ax.set_xlabel('USD / 1,000 · ● reported / ◆ USD estimate',fontsize=13)
  for iy,mid in enumerate(mids):
   value,_=cv(mid);c=cost[mid];known=c['known_usd_per_1000'];band=cost_band(mid)
   if known is None or Decimal(known)==0:ax.text(.02,iy,value,transform=ax.get_yaxis_transform(),va='center',fontsize=11)
   else:
    v=float(known);ax.scatter(v,iy,marker='D' if has_estimate(c) else 'o',s=65,facecolor=style.GRAY if band is None else style.BANDS[band],edgecolor='#263d48',linewidth=.8)
    ax.annotate(value,(v,iy),xytext=(6,0),textcoords='offset points',va='center',fontsize=11,color='#8e440c' if c['unknown_count'] else '#17212c')
 ax.spines[['top','right','left']].set_visible(False);ax.grid(axis='x',alpha=.16);ax.set_axisbelow(True);ax.tick_params(axis='y',length=0);ax.tick_params(axis='x',labelsize=11)
 fig.subplots_adjust(left=.41,right=.87 if kind=='latency' else .94,top=.91,bottom=.10)
 fig.suptitle(title,x=.04,y=.975,ha='left',fontsize=22,fontweight='bold');fig.text(.04,.945,f'Provisional v5 · 1,456 questions · inclusion ≥{threshold_label}',fontsize=12)
 fig.text(.04,.035,'Names: teal hosted · purple local · rose two-computer local · gold LLM references.',fontsize=10)
 save(fig,'comparison_'+kind)

for slug,title,fids in groups:
 a=np.array([[float(lookup[mid,fid]['accuracy']) for fid in fids] for mid in mids]);best=a.max(axis=0)
 fig,ax=plt.subplots(figsize=(13,15*len(mids)/26));im=ax.imshow(a,vmin=0,vmax=1,cmap='YlGnBu',aspect='auto');ax.set_yticks(range(len(mids)),[models[mid]['label'] for mid in mids],fontsize=12)
 for label,mid in zip(ax.get_yticklabels(),mids):label.set_color(style.ROLE_COLORS[models[mid]['role']]);label.set_fontweight('bold')
 names=[fid+'\n'+'\n'.join(textwrap.wrap(guide[fid]['display_name'],16))+f"\nn = {guide[fid]['questions']}" for fid in fids];ax.set_xticks(range(len(fids)),names,fontsize=11);ax.tick_params(top=True,labeltop=True,bottom=False,labelbottom=False,length=0,pad=10)
 ax.set_xticks(np.arange(-.5,len(fids)),minor=True);ax.set_yticks(np.arange(-.5,len(mids)),minor=True);ax.grid(which='minor',color='white',linewidth=1);ax.tick_params(which='minor',bottom=False,left=False)
 for iy,mid in enumerate(mids):
  for ix,fid in enumerate(fids):
   row=lookup[mid,fid];_,fg=style.accuracy_colors(a[iy,ix]);lead=a[iy,ix]==best[ix]
   ax.text(ix,iy,f"{row['correct']}/{row['n']}"+(' ★' if lead else '')+f"\n{a[iy,ix]:.1%}",ha='center',va='center',fontsize=12,color=fg)
   if lead:ax.add_patch(Rectangle((ix-.46,iy-.45),.92,.90,fill=False,edgecolor=fg,linewidth=1.1))
 bar=fig.colorbar(im,ax=ax,orientation='horizontal',fraction=.025,pad=.025,ticks=[0,.2,.4,.6,.8,1]);bar.ax.set_xticklabels(['0%','20%','40%','60%','80%','100%']);bar.set_label('Absolute accuracy · fixed scale across every group · ★ tied leaders')
 fig.text(.02,.024,'Names: teal hosted · purple local · rose two-computer local · gold LLM references.',fontsize=10)
 fig.suptitle(title,x=.02,y=.995,fontsize=19,fontweight='bold',ha='left');fig.text(.02,.008,f'Same overall model order. Inclusion ≥{threshold_label} overall; category counts vary.',fontsize=10);fig.subplots_adjust(left=.37,top=.86,bottom=.065,right=.985);save(fig,'categories_'+slug)
style.legend_graphic(OUT)

overall=[];more_rows=[];mobile_cards=[];costrows=[]
for mid in mids:
 m=models[mid];value,basis=cv(mid);coverage=f"{m['valid']}/{m['n']} ({m['coverage']:.2%})"
 detail=f"{m['accuracy']:.2%}"+(f"–{m['accuracy_upper_if_all_unusable_correct']:.2%} possible" if m['valid']<m['n'] else '')
 overall.append('<tr data-overall-model="'+esc(mid)+'"><td>'+style.model_name(mid,models)+'</td><td>'+f"{m['correct']:,}/{m['n']:,}<small>{detail}</small></td>"+style.speed_cell(m['median_ms'])+style.speed_cell(m['p95_ms'])+cost_cell(mid,True,False)+cost_cell(mid,False,False)+f"<td>{coverage}</td></tr>")
 more_rows.append('<tr data-overall-model="'+esc(mid)+'"><td>'+style.model_name(mid,models)+f"</td><td>{m['macro_category_accuracy']:.2%}</td><td>{m['answer_accuracy_among_usable']:.2%}</td><td>{coverage}</td></tr>")
 medband=style.speed_band(m['median_ms']);tailband=style.speed_band(m['p95_ms']);band=cost_band(mid)
 med=style.BANDS[medband];tail=style.BANDS[tailband];moneybg=style.GRAY if band is None else style.BANDS[band]
 costlabel='Unmetered / unknown' if band is None else style.BAND_NAMES[band]
 mobile_cards.append('<article class="mobile-card" data-overall-model="'+esc(mid)+'"><h3>'+style.model_name(mid,models)+'</h3><div class="mobile-grid"><div><strong>'+f"{m['accuracy']:.2%}</strong><span>Accuracy · {m['correct']:,}/{m['n']:,}</span></div>"+f'<div><strong>{m["valid"]:,}/{m["n"]:,}</strong><span>Usable responses</span></div><div style="background:{med}" data-mobile-speed-band="{medband}"><strong>{m["median_ms"]:,.0f} ms</strong><span>Median · {style.BAND_NAMES[medband]}</span></div><div style="background:{tail}" data-mobile-speed-band="{tailband}"><strong>{m["p95_ms"]:,.0f} ms</strong><span>p95 · {style.BAND_NAMES[tailband]}</span></div><div style="background:{moneybg}" data-mobile-cost-band="{band if band is not None else "unknown"}"><strong>{esc(total_cost(mid))}</strong><span>Selected-record cost · {costlabel}</span></div><div style="background:{moneybg}" data-mobile-cost-band="{band if band is not None else "unknown"}"><strong>{esc(value)}</strong><span>Cost per 1,000 · {costlabel}</span></div></div><p>'+esc(basis)+'</p></article>')
for mid in sorted(models,key=lambda x:(-models[x]['accuracy'],x)):
 cs=cost[mid];value,basis=cv(mid)
 costrows.append('<tr><td>'+style.model_name(mid,models)+'</td>'+cost_cell(mid)+cost_cell(mid,True)+'<td>'+esc(basis)+'</td></tr>')
def table(head,rows):
 return '<div class="scroll"><table><thead><tr>'+''.join('<th>'+esc(x)+'</th>' for x in head)+'</tr></thead><tbody>'+''.join(rows)+'</tbody></table></div>'

group_html,rank_html=style.category_html(s,guide,lookup,'')
catalog=''
for mid in s['below_cutoff']:
 m=models[mid];archived=''
 if mid in v4['models']:
  old=v4['models'][mid];archived=f" Historical v4: {old['correct']}/2,157 ({old['accuracy']:.2%}), below its former 62% cutoff."
 catalog+=f"<li>{esc(m['label'])}: <strong>v5 {m['correct']}/1,456 ({m['accuracy']:.2%})</strong>; coverage {m['coverage']:.2%}.{archived}</li>"
legend='''<ul><li>Teal model names indicate hosted native decisions; purple indicates local baselines; rose (#b2364b) identifies the two-computer local D3 and SingVL deployments; gold indicates reasoning-disabled LLM references.</li><li>Category cells use one fixed pale-yellow to dark-blue 0–100% scale. Each shows correct/total and percentage; ★ marks all tied leaders.</li><li>Speed and known cost use fixed green / yellow / orange / red bands: median or p95 ≤250 / ≤500 / ≤1,000 / &gt;1,000 ms; cost ≤$0.010 / ≤$0.025 / ≤$0.050 / &gt;$0.050 per 1,000 questions.</li><li>Cost markers ● / ◆ mean API-reported USD / USD estimates from captured tariffs or foreign exchange. REAX reports EUR; its USD values are labelled FX estimates. “+ ?” means charges are missing; local costs are unmetered.</li></ul>'''
reax=models['reax_1_3'];terra=models['reference_terra61']
reax_usd=Decimal(cost['reax_1_3']['known_subtotal_usd']);terra_usd=Decimal(cost['reference_terra61']['known_subtotal_usd'])
cost_difference=100*(reax_usd/terra_usd-1)
latency_difference=100*(reax['median_ms']/terra['median_ms']-1)
tradeoff=(f"The provider describes REAX 1.3 as a large two-model native decision ensemble: it returns probabilities with zero generated answer tokens. "
          f"In this full-bank test its cost and latency are closer to the LLM references than to the fastest inexpensive decision specialists. "
          f"It scored {reax['correct']}/1,456 ({reax['accuracy']:.2%}), versus Terra’s {terra['correct']}/1,456 ({terra['accuracy']:.2%}); "
          f"its median was {reax['median_ms']:,.0f} ms versus Terra’s {terra['median_ms']:,.0f} ms ({abs(latency_difference):.1f}% {'slower' if latency_difference>=0 else 'faster'}). "
          f"REAX’s FX-estimated USD cost is {abs(cost_difference):.1f}% {'higher' if cost_difference>=0 else 'lower'} than Terra’s known USD subtotal on the same 1,456 inputs. "
          f"Terra has {cost['reference_terra61']['unknown_count']} unknown charges, so this compares available subtotals rather than complete final bills.")
specialist_tradeoff=(f"REAX’s FX-estimated selected-record USD cost is {reax_usd/Decimal(cost['fastino_glide_v23_bf16']['known_subtotal_usd']):.1f}× Fastino’s tariff-estimated cost and "
                    f"{reax_usd/Decimal(cost['morph_reflex']['known_subtotal_usd']):.1f}× Morph Reflex’s API-reported cost. "
                    "These ratios describe the recorded sessions and conversion rate, not guaranteed future prices. Its accuracy qualifies it for the graph; the ensemble’s resource trade-off remains visible.")
drex=models['drex_max_v11'];old_drex=models['drex_max'];dcost=cost['drex_max_v11'];old_dcost=cost['drex_max']
decision_text=('Native Drex Max v1.1 replaces the older Drex Max in the active graph under the user’s conditional replacement instruction. The older result remains a superseded reference, with every score and recorded response preserved. It is above the 45% cutoff and is not classified as below cutoff.'
               if 'drex_max' in superseded else
               'Both Drex configurations remain separately measured. The explicit replacement decision retains both configurations; each enters the active graph only if its full-bank score meets the 45% cutoff.')
drex_comparison_text=(f"The new native Nace API declares Drex Max v1.1, released October 28, whereas the earlier DeepInfra/OpenRouter configuration returned an October 16 checkpoint. "
                      f"The new version scored {drex['correct']}/1,456 ({drex['accuracy']:.2%}), versus {old_drex['correct']}/1,456 ({old_drex['accuracy']:.2%}) previously: "
                      f"{comparison['correct_difference']:+d} correct answers ({comparison['accuracy_difference_percentage_points']:+.2f} percentage points). "
                      f"New median/p95 response times are {drex['median_ms']:,.0f}/{drex['p95_ms']:,.0f} ms, versus {old_drex['median_ms']:,.0f}/{old_drex['p95_ms']:,.0f} ms. "
                      f"The paired outcomes include {comparison['new_only_correct']} new-only correct and {comparison['old_only_correct']} old-only correct answers. "
                      "These are distinct versions, routes and collection sessions; the comparison does not isolate a weight-only effect.")
drex_cost_text=(f"New Drex has no monetary API charge telemetry. Its captured-tariff estimate is USD {dcost['known_subtotal_usd']} at $0.03 per million reported input tokens, "
                f"with {dcost['unknown_count']} no-usage primary costs unknown. The previous known API-reported subtotal is USD {old_dcost['known_subtotal_usd']} plus {old_dcost['unknown_count']} unknown charges. "
                f"The new estimate is {Decimal(comparison['new_estimate_to_old_known_reported_cost_ratio']):.3f}× that older known subtotal; this comparison does not establish actual billing savings. "
                "The retained no-answer HTTP 429 primaries were never replayed or assigned zero cost. Only unattempted inputs resumed after the rate-limit pause. "
                "Collection moved from two workers to sequential pacing; waits are outside request timers, so pooled latency is not uniform-throughput evidence. "
                "The provider documents 120 requests/minute for free access and 600 for paid access; applicable limits and phases are recorded separately.")
drex_counter_text=(f"Native Drex returns typed choices and probabilities. Raw output-token counters are nonzero in {drex['nonzero_output_counter_responses']} responses and sum to {drex['raw_output_tokens']}. "
                   "Those counters are preserved under the existing native-choice scoring policy. No generated reasoning text was observed; zero generation is not independently attested and is not claimed. "
                   "Only the captured input-token tariff enters the cost estimate; output is not billed by that tariff.")
superseded_catalog=''.join(f"<li>{esc(models[mid]['label'])}: {models[mid]['correct']}/1,456 ({models[mid]['accuracy']:.2%}); median/p95 {models[mid]['median_ms']:,.0f}/{models[mid]['p95_ms']:,.0f} ms; known cost {esc(total_cost(mid))}. Superseded by a separately tested version, not below the cutoff. Full records remain downloadable.</li>" for mid in superseded)
selection='''<p><strong>Provisional subset:</strong> V5 removes the exact 701 questions that every one of the 26 configurations in the preceding v4 main graph answered correctly. The selection includes the four reasoning-disabled LLM references. All 1,456 retained question inputs and all previously recorded primary answers are unchanged. All 38 preceding complete configurations retain their recorded answers. Four native hosted configurations add full-bank sessions on the same frozen inputs. This is a cohort-conditioned subset, not independent evidence of general difficulty. The original 26 configurations retain their relative score order; newly tested models can interleave and superseded versions are archived separately; removing their shared successes rescales their percentages. Category sizes change unevenly, and equal-category accuracy is a separate diagnostic.</p>'''
selection+=f'<p><strong>Frozen inclusion threshold:</strong> ≥{threshold_label}, set by the user after reviewing the lowest retained main-graph score, Super Decider at 669/1,456 (45.95%). Qualification uses the exact integer rule <code>correct ×100 ≥45 ×1,456</code>, equivalent to at least 656 correct, including ties; displayed rounded percentages do not determine inclusion. This fixed threshold applies to future configurations on the unchanged provisional v5 bank. All {len(models)} complete configurations are retained in the downloads; the active graph has {len(mids)} configurations after the threshold and explicit version-selection decision, with {len(superseded)} superseded reference(s).</p>'
selection+='''<p>The original quantitative selection also remains relevant: 60 AQuA items were selected for errors by Fastino and D3 Artemis, and 140 for errors by at least one of Fastino, Mammoth, GPT-6 Sol, D3 Ultra and Drex Max. Selection across multiple models distributes that dependence without eliminating it. Public questions may occur in training data.</p>'''
rights='''<p><strong>Question origins and rights:</strong> The retained bank contains 1,236 questions from the project development bank, 20 MAIQ number sequences and 200 AQuA quantitative questions. AQuA-RAT declares Apache-2.0 and contains crowdsourced admissions-style mathematics, not authenticated official GRE or SAT exam questions. MAIQ declares MIT, but its original human-test item rights are not established. The development lineage does not fully establish individual authorship or possible external influences for every project-bank item. The project MIT license does not supersede third-party terms. The two noncommercial LogiQA items remain outside this bank. <a href="SOURCE_AND_LICENSES.md">Full source and license notices</a> · <a href="source_metadata_1456.jsonl">Per-question provenance</a>.</p>'''
body='<p class="eyebrow">Fast, structured decisions · provisional v5 · November 13, 2026</p><h1>System 1 Decision Benchmark · provisional v5</h1><p class="lead">1,456 questions across 43 categories, including native Perplexity v1.3 and HeyGen Decision 1 variants, Gemini Decision 1, and D3 Flash and SingVL two-computer local results.</p>'
body+=f'<p>The inclusion threshold is <strong>{threshold_label}</strong>, set by the user. <a href="https://github.com/etsabary/system-1-decision-benchmark/blob/main/results/releases/system1_v5_provisional_2026-11-09/report.html">The initial 1,456-question v5 release remains archived</a>; <a href="https://etsabary.github.io/system-1-decision-benchmark/v4/report.html">the complete 2,157-question v4 report remains unchanged.</a></p>'
body+='<nav><a href="#overview">Accuracy, speed &amp; cost</a><a href="#hosted-refresh">Perplexity and HeyGen</a><a href="#gemini-update">Gemini Decision 1</a><a href="#d3-flash-update">D3 Flash local result</a><a href="#singvl-update">Two-computer SingVL</a><a href="#drex-update">Drex version update</a><a href="#hosted-update">REAX trade-off</a><a href="#legend">Colour key</a><a href="#categories">Category matrices</a><a href="#rankings">Individual rankings</a><a href="#cost">Cost evidence</a><a href="#history">Historical screens</a><a href="#method">Method and downloads</a></nav>'
body+='<section id="overview"><h2>Accuracy, speed and cost</h2><p>Accuracy uses all 1,456 retained questions. Costs and response times are recomputed from those same selected records.</p><div class="chart-scroll"><a href="comparison_accuracy.svg"><img src="comparison_accuracy.png" alt="Accuracy of the qualifying configurations on provisional v5, ordered by score"></a></div><label>Find a model <input id="model-search" type="search" placeholder="Model or deployment"></label><p id="model-empty" role="status" hidden>No models match this search.</p>'
body+='<div class="comparison-table">'+table(['Configuration','Correct / tested · possible range','Median','p95','Selected-record known USD','USD / 1,000','Usable'],overall)+'</div><div class="mobile-cards">'+''.join(mobile_cards)+'</div>'
body+='<details><summary>Additional accuracy and coverage measures</summary>'+table(['Configuration','Equal-category accuracy','Accuracy among usable','Usable'],more_rows)+'</details>'
for kind,title in [('latency','Response time'),('cost','Cost per 1,000 questions')]:
 body+=f'<h3>{title}</h3><div class="chart-scroll"><a href="comparison_{kind}.svg"><img src="comparison_{kind}.png" alt="{title} on the retained v5 records, with the same model order"></a></div>'
body+='<p><a href="overview.svg">Combined accuracy, speed and cost overview (SVG)</a></p><p>Operational accuracy counts an unusable response as not correct. The possible upper endpoint assumes every unusable answer would have been correct; it is a bound, not an estimate. Timings pool the retained individual primary records, include failed calls and network time, and use linear-interpolated p95. Collection dates, hardware and routes differ.</p></section>'
singvl=models['singvl_s1_4b_q4km_llamacpp_ctx4096_lan']
singvl_text=("SingVL S1 4B Q4_K_M scored 698/1,456 (47.94%), with all 1,456 responses usable. Median/p95 complete-response latency was 344/1,164 ms. "
             "Rose model names and bars identify this two-computer local setup. The user reports an ASUS TUF with AMD Ryzen 7 and a Lenovo Legion with Intel Core i7, each with an RTX 2060 and 6 GB VRAM. "
             "The ASUS coordinates llama.cpp CUDA/RPC inference with the Lenovo worker over the LAN. Each GPU retains its own memory; the nominal total is 12 GB across the two computers. "
             "This is a different deployment from the purple local baselines. Hardware and electricity are unmetered, not zero; latency includes LAN and adapter overhead.")
singvl_limits=("The serving API declares Q4_K_M weights, llama.cpp b12301-956591f45 and 4,096-token backend context and input allowance. The original 1,024-context 20-question screen is excluded. "
               "The hardware description is user-reported; actual GPU placement, weight-file identity, conversion correctness and zero-generation internals were not independently attested through the API. "
               "This score applies to the quantized compatibility runtime, not the original full-precision Transformers implementation. All responses returned valid typed decisions and reported zero output tokens, with no generated reasoning text observed.")
singvl_analysis=(f"The result meets the fixed 45% cutoff and now ranks {ordinal(mids.index('singvl_s1_4b_q4km_llamacpp_ctx4096_lan')+1)} among the {len(mids)} active configurations. It exceeds StartLux Instant 4B Q8 by 20 correct answers (1.37 percentage points). "
                 "Necessary conditions (26/32) and forward conditionals (17/22) are relative strengths; robust decisions without a prior (3/39) and value of information (10/40) are weaknesses. "
                 "Quantitative reasoning is 93/200 versus StartLux’s 75/200; scheduling is 27/54 versus 17/54, and conversational intention is 24/33 versus 14/33. "
                 "StartLux leads request routing (19/31 versus 8/31) and value of information (20/40 versus 10/40). The overall lead masks different task profiles. "
                 "The category figures are descriptive and do not establish a general advantage from adding a second GPU.")
d3_text=(f"D3 Flash 9B Q4_K_M scored 704/1,456 (48.35%), ranking {ordinal(mids.index('d3_flash_9b_q4km_llamacpp_ctx4096_lan')+1)} among {len(mids)} qualifying configurations. "
         "Median/p95 response latency was 577/6,616 ms, with 1,455 usable responses. Rose names and bars identify this two-computer local setup alongside SingVL.")
d3_analysis=("It adds six correct answers over SingVL (0.41 percentage points), at 1.68 times its median latency, and 26 over StartLux Instant 4B Q8. "
             "Request routing is 19/31 versus SingVL’s 8/31, and temporal intervals 17/25 versus 9/25. SingVL leads conversational intention (24/33 versus 14/33), "
             "quantitative reasoning (93/200 versus 84/200) and reference binding (22/35 versus 15/35). The small overall difference masks distinct task profiles.")
d3_limits=("The user reports the same ASUS TUF Ryzen 7 and Lenovo Legion Intel Core i7 deployment, each with an RTX 2060 and 6 GB VRAM, using llama.cpp CUDA/RPC over Ethernet. "
           "The API declares native D3 Flash Q4_K_M and 4,096 context. Exact weight identity, equivalence to the older Artemis checkpoint, conversion fidelity and actual GPU placement are not independently attested. "
           "Hardware and electricity costs are unmetered. Full configuration and collection details accompany the downloadable evidence.")
gemini_text=(f"Gemini Decision 1 scored 798/1,456 (54.81%), with all 1,456 responses usable, ranking {ordinal(mids.index('gemini_decision1_openrouter_20261111')+1)} among {len(mids)} active configurations. "
             "Median/p95 complete-response latency was 372.08/495.57 ms. API-reported charges total USD 0.0797482, with no missing charges; the separate USD 0.0000116 readiness charge is excluded.")
gemini_limits=("This is OpenRouter’s native Decisions route pinned to Google AI Studio, requested as google/gemini-decision-1 and returned as google/gemini-decision-1-20261111. "
               "Precision is unknown. The fixed full-bank collection on November 12 used first attempts only, with no request errors, scored retries or client truncation and 18 matching metadata snapshots. "
               "All responses reported zero output tokens with no generated reasoning text observed; hidden weights and zero-generation internals were not independently attested.")
gemini_analysis=("Gemini adds 12 correct answers over Jev 1.14 (786/1,456) at 2.15 times its median latency. Morph Reflex scored 841/1,456 at a 354.45 ms median. "
                 "It adds 120 correct answers over StartLux Instant 4B Q8, 100 over SingVL and 94 over D3 Flash Q4_K_M. The measurements retain their different routes, dates, precision and hardware.")
refresh=json.loads((OUT/'hosted_refresh_model_audits.json').read_text())
refresh_text=("Four full-bank native hosted sessions add 5,824 first attempts, all usable, with no errors, scored retries or client truncation. "
              "The frozen 1,456-question/43-category bank and exact 45% cutoff are unchanged. There are 42 complete configurations, 34 active, six below cutoff and two superseded versions. "
              "Perplexity Decider v1.3 replaces v1.2 in the active comparison under the standing current-version policy; all older measurements and primary records remain unchanged. "
              "The new direct route/version/date and cost basis remain separately labelled.")
refresh_comparison=("Perplexity Decider v1.3 scored 984/1,456 (67.58%), versus v1.2’s 949; median response time was 215.68 ms versus 245.84 ms. "
                    "Flash v1.3 scored 667/1,456 (45.81%) at a 124.87 ms median. HeyGen Decision 1 scored 937/1,456 (64.35%) at 340.16 ms, "
                    "and Turbo preview 959/1,456 (65.87%) at 270.98 ms. Turbo adds 22 correct answers with lower measured median and API-reported cost. "
                    "The paired HeyGen outcomes were 863 both correct, 74 standard-only, 96 Turbo-only and 423 neither. Both remain distinct native decision models; Turbo is preview, not an ordinary generative LLM reference.")
refresh_cost=("Perplexity’s native input tariffs of USD 0.02/M (Decider) and 0.01/M (Flash) yield captured estimates of USD 0.01534610 and 0.00767305. "
              "All 1,456 primaries per model have estimates, but actual API monetary charges are unreported for all 1,456; they are not reported zero charges. "
              "Separate readiness estimates of USD 0.00000194 and 0.00000097 are excluded. HeyGen API-reported charges total USD 0.16275784 standard and 0.13255038 Turbo, with no missing charges; "
              "their separate USD 0.00001666 and 0.00001071 readiness charges are excluded. These are session subtotals and captured tariffs, not future price guarantees.")
refresh_limits=("Both Perplexity native /v1/decisions requests named explicit v1.3 versions; returned model fields echo those versions without independently attesting immutable weights. "
                "HeyGen used OpenRouter’s native Decisions API pinned to HeyGen, declaring November 12 snapshots. Precision is unknown for all four, and each retained 17 matching metadata checks. "
                "Perplexity reports one raw output-accounting token per question (1,456 per model), retained without a zero-counter requirement. HeyGen reports zero output tokens. "
                "No generated reasoning text was observed, and hidden weights and generation implementation were not independently attested. "
                "Per-request timing pools individual primaries and excludes idle dispatch pacing; it is not sustained throughput. HeyGen dispatch gaps met the one-second floor; transport starts after TLS setup are a different timestamp and can be closer together.")
refresh_ranks='Current active ranks: '+', '.join(models[mid]['label']+' '+str(mids.index(mid)+1)+'/'+str(len(mids)) for mid in sorted(new_ids,key=lambda x:mids.index(x)))+'.'
body+='<section id="hosted-refresh"><h2>Perplexity v1.3 and HeyGen Decision 1</h2>'+''.join('<p>'+esc(x)+'</p>' for x in [refresh_text,refresh_comparison,refresh_ranks,refresh_cost,refresh_limits])+'<p><a href="HOSTED_REFRESH_NOTES.md">Configuration, replacement and billing notes</a> · <a href="hosted_refresh_analysis.json">All categories and matched comparisons</a> · <a href="hosted_refresh_usage_evidence.csv.gz">Per-primary native usage and charge evidence</a></p></section>'
body+='<section id="gemini-update"><h2>Gemini Decision 1: native hosted decisions</h2><p>'+esc(gemini_text)+'</p><p>'+esc(gemini_analysis)+'</p><p>'+esc(gemini_limits)+'</p><p><a href="GEMINI_DECISION1_NOTES.md">Configuration and collection notes</a> · <a href="gemini_decision1_analysis.json">All category and paired comparisons</a> · <a href="gemini_decision1_usage_evidence.csv.gz">Usage and reported charges</a></p></section>'
body+='<section id="d3-flash-update"><h2>D3 Flash 9B: a local comparison</h2><p>'+esc(d3_text)+'</p><p>'+esc(d3_analysis)+'</p><p>'+esc(d3_limits)+'</p><p><a href="D3_FLASH_NOTES.md">Historical D3 collection record</a> · <a href="d3_flash_analysis.json">D3 release-time category and paired comparisons</a> · <a href="d3_flash_hardware.json">Hardware provenance</a></p></section>'
body+='<section id="singvl-update"><h2>SingVL: two computers, two local GPUs</h2><p>'+esc(singvl_text)+'</p><p>'+esc(singvl_analysis)+'</p><p>'+esc(singvl_limits)+'</p><p><a href="SINGVL_DISTRIBUTED_NOTES.md">Configuration and collection notes</a> · <a href="singvl_hardware.json">Hardware provenance</a> · <a href="singvl_analysis.json">SingVL release-time category results</a></p></section>'
body+='<section id="drex-update"><h2>Drex Max v1.1: a separately tested native version</h2><p>'+esc(decision_text)+'</p><p>'+esc(drex_comparison_text)+'</p><p>'+esc(drex_cost_text)+'</p><p>'+esc(drex_counter_text)+'</p><p><a href="DREX_VERSION_NOTES.md">Version, scoring and collection notes</a> · <a href="drex_comparison.json">Paired outcome and performance comparison</a> · <a href="drex_counter_policy.json">Raw-counter interpretation</a> · <a href="drex_transport_phases.json">Transport phases</a></p></section>'
body+='<section id="hosted-update"><h2>REAX: accuracy with an ensemble cost and latency trade-off</h2><p>'+esc(tradeoff)+'</p><p>'+esc(specialist_tradeoff)+'</p><p><a href="HOSTED_MODEL_NOTES.md">Model identity, zero-generation interface and collection details</a></p></section>'
body+='<section id="legend"><h2>How to read the colours</h2><img class="legend-graphic" src="accuracy_legend.png" alt="Fixed zero to 100 percent category accuracy scale">'+legend+'</section>'
body+='<section id="categories"><h2>43 categories: a map of strengths</h2><p>Each matrix uses the same overall model order and fixed 0–100% accuracy scale. Retained category counts vary; every cell shows its own denominator. Numerical patterns contain 20 questions and quantitative reasoning contains 200.</p>'+group_html+'</section>'
body+='<section id="rankings"><h2>Rankings within each category</h2><p>Accuracy ties share a competition rank; response times do not break the tie. Inclusion is determined once by overall accuracy.</p><label>Choose a category <select id="category-select"><option value="">All categories</option>'+''.join(f'<option value="{esc(fid)}">{esc(fid)} · {esc(guide[fid]["display_name"])}</option>' for fid in sorted(guide))+'</select></label>'+rank_html+'</section>'
reaxcost=cost['reax_1_3'];morphcost=cost['morph_reflex']
hosted_cost_note=(f"Morph Reflex’s selected 1,456 primaries have API-reported USD charges of ${morphcost['reported_subtotal_usd']}. "
                 f"REAX 1.3 reports EUR {reaxcost['native_reported_subtotal']} across {reaxcost['native_reported_count']} selected primaries. "
                 f"Its USD ${reaxcost['fx_estimate_subtotal_usd']} comparison is an FX estimate, using EUR 1 = USD {reaxcost['fx_rate_usd_per_eur']} from the ECB reference rate dated {reaxcost['fx_date']}. "
                 "The converted USD amount was not reported by the provider. Exact native EUR nanos, conversion records and the captured rate receipt are downloadable. Readiness calls and other unscored requests remain outside these totals.")
body+='<section id="cost"><h2>Cost evidence and missing charges</h2><p>Costs are attributable to selected primary records on the same 1,456 questions. The prior 38 configurations preserve their historical cost records. HeyGen adds API-reported USD charges; Perplexity adds captured input-tariff estimates with actual monetary charges unreported. Readiness remains excluded. These amounts do not promise future prices. Costs preserve API-reported USD, captured tariff estimates, EUR-to-USD FX estimates, free-access records, unknown charges and unmetered local compute as distinct cases. The per-1,000 value divides the known subtotal by 1,456 and multiplies by 1,000; + ? means the subtotal is incomplete. No historical tariff was extrapolated to missing records. Probes, preceding failed recovery attempts, setup and model reviews remain outside the selected-record cost totals.</p><p>'+esc(hosted_cost_note)+'</p><p><a href="HOSTED_MODEL_NOTES.md">New-model configurations and cost scope</a> · <a href="native_currency_cost_evidence.csv.gz">Native EUR and FX evidence</a> · <a href="fx_receipt.json">FX receipt</a> · <a href="ecb_eurofxref_2026-11-09.xml">Captured ECB rates</a></p>'+table(['Configuration','Known USD / 1,000','Known subtotal USD','Evidence counts'],costrows)+'</section>'
body+='<section id="history"><h2>Historical v4 exploratory screens</h2><p>The following stopped or incomplete screens retain their original v4 samples and denominators. They are historical evidence, not provisional v5 scores or classifications against the new threshold. No stopped test was resumed.</p><ul>'
history=[('Strike 1','57/100 correct; free-tier screen stopped after 100 requests.','STRIKE_SCREEN_NOTES.md'),('Hanzo Kai 1.9','46/244 correct; the free daily cap was followed by a separate eight-hour plan window after credits were purchased. The user stopped the test.','KAI_CASE_NOTE.md'),('THIS/THAT 1.2 and GLiNER2.5-Decide','THIS/THAT: 32/100 correct. GLiNER: 4/14 usable answers, plus 6 input-length rejections in 20 attempts.','LOCAL_SCREEN_NOTES.md'),('Hindsight and Lumma','Hindsight: 29/100 correct. Lumma: 452/799 attempts correct, including an unavailable request.','NEW_LOCAL_SCREEN_NOTES.md'),('GPT-6 Luna Decisions','82/181 correct on the separately attempted additions; historical baseline 758/1,342. The expansion stopped below its recorded 50% rule.','OPENAI_DECISIONS_NOTES.md')]
for label,text,name in history:
 body+=f'<li><strong>{esc(label)}:</strong> {esc(text)} <a href="{name}">Historical method and limits</a>.</li>'
body+='</ul><p><a href="partial_models.json">Original partial-result records</a> · <a href="https://etsabary.github.io/system-1-decision-benchmark/v4/report.html">Unchanged v4 report and scores</a></p></section>'
body+=f'<section id="below-cutoff"><h2>Below the 45% cutoff</h2><p>These complete configurations were rescored on the same 1,456 retained questions and fall below {threshold_label}. Their full results remain downloadable. Archived v4 scores retain the original 2,157-question denominator and former 62% cutoff.</p><ul>'+catalog+'</ul></section>'
if superseded:
 body+='<section id="superseded"><h2>Superseded versions retained for reference</h2><p>Version replacement is separate from the accuracy cutoff. These measurements remain in all-model evidence and their dated archives.</p><ul>'+superseded_catalog+'</ul></section>'
body+='<section id="method"><h2>Method, provenance and downloads</h2>'+selection+rights+'<h3>Records and collection</h3><p>Recorded first primary responses and previously approved exact-input reuse are preserved. A response was not replaced because it was incorrect. Historical HTTP 429 recoveries retain the previously selected first returned answer, with prior no-answer attempts disclosed separately. Costs and timings cover those selected answers. Provider identities, precision, routes and collection dates retain their original provenance; model declarations do not independently attest hidden weights. The 120 companion diagnostics remain separate.</p><p>Comparisons with archived v4 percentages require their different denominators and category weights to be stated. Category scores on very small retained sets are descriptive and can move substantially with one answer. The smaller bank reduces future request count by 701 of 2,157 (32.5%); token charges need not fall by the same fraction.</p><div class="scroll"><table><thead><tr><th>Configuration</th><th>Recorded setting</th><th>Retained collection dates, Toronto</th><th>Limits</th></tr></thead><tbody>'
for mid in sorted(models,key=lambda x:(-models[x]['accuracy'],x)):
 m=models[mid];dates=', '.join(f'{day}: {count}' for day,count in sorted(m['collection_dates_toronto'].items()))
 body+='<tr><td>'+style.model_name(mid,models)+'</td><td>'+esc(m['configuration'])+'</td><td>'+esc(dates)+'</td><td>'+esc(m['identity_limit'])+' '+esc(m['new_collection_limit'])+'</td></tr>'
downloads=[('questions_1456.jsonl','Answer-free provisional v5 questions'),('source_metadata_1456.jsonl','Question-level origin and license metadata'),('SOURCE_AND_LICENSES.md','Source and license notes'),('statistics.json','All model summaries'),('all_category_scores.csv','All models by 43 categories'),('timing_evidence.csv.gz','Retained timing and status evidence'),('cost_evidence.csv.gz','Retained cost evidence'),('cost_statistics.json','Retained cost summaries'),('category_guide.json','Category guide'),('removed_items.csv','701 removed question IDs and categories'),('retained_items.csv','1,456 retained question IDs and categories'),('selection_provenance.json','Fixed selection cohort and subset provenance'),('correctness_evidence.csv.gz','Retained correctness and usability booleans'),('removed_correctness_evidence.csv.gz','Removed-item correctness and usability booleans'),('transport_recoveries.json','Historical no-answer recovery evidence'),('model_collection_recoveries.json','Historical collection recovery evidence'),('model_context_diagnostics.json','Historical context diagnostics'),('audit_receipt.json','Subset audit receipt'),('manifest.json','Release checksums')]
downloads += [('HOSTED_MODEL_NOTES.md','Morph and REAX configuration, collection and billing notes'),('hosted_model_audits.json','Independent new-model audit summaries'),('hosted_cost_summaries.json','New-model cost summaries'),('new_model_comparison.json','Full-bank REAX, Terra, Fastino and Morph comparisons'),('REAX_TERRA_COMPARISON.md','REAX ensemble accuracy, speed and cost trade-off'),('native_currency_cost_evidence.csv.gz','Native EUR charges and separately estimated USD conversion'),('fx_receipt.json','Captured ECB rate receipt'),('ecb_eurofxref_2026-11-09.xml','Captured ECB exchange-rate XML'),('baseline_v5_audit_receipt.json','Frozen initial v5 audit receipt')]
downloads += [('DREX_VERSION_NOTES.md','Drex native version, replacement and collection notes'),('drex_comparison.json','Drex old/new paired comparison and replacement decision'),('drex_model_audit.json','Drex first-primary audit'),('drex_usage_evidence.csv.gz','Drex per-primary input usage and retained raw output counters'),('drex_counter_policy.json','Drex raw output-counter interpretation'),('drex_version_provenance.json','Drex version and provider provenance'),('drex_transport_phases.json','Drex concurrency and rate-limit collection phases'),('parent_hosted_audit_receipt.json','Frozen preceding hosted-release audit receipt')]
downloads += [('SINGVL_DISTRIBUTED_NOTES.md','SingVL distributed deployment and collection notes'),('singvl_hardware.json','User-reported hardware and captured serving configuration'),('singvl_model_audit.json','Independent SingVL first-primary audit'),('singvl_usage_evidence.csv.gz','Per-primary native usage and source hashes'),('singvl_analysis.json','Historical SingVL release-time category analysis'),('parent_drex_audit_receipt.json','Previous Drex-release audit receipt')]
downloads += [('D3_FLASH_NOTES.md','D3 Flash configuration and neutral collection record'),('d3_flash_hardware.json','D3 user-reported deployment and serving configuration'),('d3_flash_model_audit.json','Independent D3 first-primary audit'),('d3_flash_usage_evidence.csv.gz','D3 native usage and retained missing telemetry'),('d3_flash_transport_phases.json','D3 request pacing and retained timeout evidence'),('d3_flash_analysis.json','Historical D3 release-time category and paired analysis'),('d3_flash_category_comparison.csv','D3 against every preceding model by category'),('parent_singvl_audit_receipt.json','Frozen preceding SingVL audit receipt')]
downloads += [('GEMINI_DECISION1_NOTES.md','Gemini native configuration and collection notes'),('gemini_decision1_model_audit.json','Independent Gemini first-primary audit'),('gemini_decision1_usage_evidence.csv.gz','Gemini per-primary usage, declared snapshot and API-reported USD'),('gemini_decision1_analysis.json','Gemini release-time categories and paired comparisons'),('gemini_decision1_category_comparison.csv','Gemini against all 37 preceding models by category'),('parent_d3_flash_audit_receipt.json','Frozen preceding D3 audit receipt')]
downloads += [('HOSTED_REFRESH_NOTES.md','Perplexity/HeyGen configuration, version replacement and cost qualifications'),('hosted_refresh_model_audits.json','Four native hosted first-primary audits'),('hosted_refresh_usage_evidence.csv.gz','Four native hosted usage and cost records'),('hosted_refresh_analysis.json','Current-release full category and paired analyses'),('hosted_refresh_category_comparison.csv','Four models against every other measured configuration by category'),('pplx_version_comparison.json','Perplexity native version replacement decision'),('parent_gemini_audit_receipt.json','Frozen preceding Gemini-release audit receipt')]
body+='</tbody></table></div><p>Ranks in archived collection notes and release-time analysis files describe their original dated cohort. Current cohort ranks appear in the main comparison and current model sections above.</p><ul>'+''.join(f'<li><a href="{name}">{esc(label)}</a></li>' for name,label in downloads)+'</ul></section>'
js="document.getElementById('model-search').addEventListener('input',function(){const q=this.value.toLowerCase();document.querySelectorAll('[data-overall-model]').forEach(r=>r.hidden=!r.textContent.toLowerCase().includes(q));document.getElementById('model-empty').hidden=[...document.querySelectorAll('.mobile-card')].some(r=>!r.hidden);});document.getElementById('category-select').addEventListener('change',function(){document.querySelectorAll('.category').forEach(r=>{r.hidden=!!this.value&&r.dataset.family!==this.value;if(this.value&&r.dataset.family===this.value)r.open=true;});});"
responsive_css='''.comparison-table table{font-size:14px}.comparison-table .cost{min-width:145px}.mobile-cards{display:none}.chart-scroll{overflow-x:auto}.chart-scroll img{width:100%;max-width:1100px}.mobile-card[hidden]{display:none!important}@media(max-width:700px){.comparison-table{display:none}.mobile-cards{display:grid;gap:14px}.mobile-card{border:1px solid #b9c9ce;background:#fff;padding:14px}.mobile-card h3{margin:0 0 12px;font-size:17px}.mobile-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:6px}.mobile-grid>div{padding:10px;border:1px solid #d7e1e4;min-height:50px}.mobile-grid strong,.mobile-grid span{display:block}.mobile-grid span{font-size:12px}.mobile-card p{margin:10px 0 0;font-size:12px}.chart-scroll img{min-width:750px}}'''
page='<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="description" content="Provisional v5: 1,456 retained decision questions, 43 categories, exact 45% inclusion threshold, readable coloured accuracy, speed and cost evidence."><title>System 1 Decision Benchmark · provisional v5</title><style>'+style.CSS+responsive_css+'</style></head><body><main>'+body+'</main><script>'+js+'</script></body></html>'
(OUT/'report.html').write_text(page)

readme='# System 1 Decision Benchmark · provisional v5\n\n'
readme+='This provisional successor contains **1,456 questions across 43 categories**. It removes the exact 701 questions answered correctly by all 26 configurations in the original v4 main graph, while retaining every remaining question and recorded primary response. All 38 preceding complete configurations retain their recorded answers. Four native hosted configurations add full-bank sessions on the same frozen inputs. The complete v4 bank and reports remain unchanged.\n\n'
readme+=f'**Inclusion threshold: {threshold_label}.** The user set this cutoff after reviewing Super Decider’s 669/1,456 (45.95%), the lowest score among the preceding graph models. Inclusion uses the exact rule **correct ×100 ≥45 ×1,456**, requiring at least **656 correct**, including ties. All 38 preceding complete configurations are preserved and four native hosted configurations are added; {len(mids)} configurations appear in the active graph after the threshold and explicit version-selection decision, with {len(superseded)} superseded reference(s).\n\n'
readme+='[Interactive provisional v5 report](https://etsabary.github.io/system-1-decision-benchmark/v5/report.html) · [Category rankings](https://etsabary.github.io/system-1-decision-benchmark/v5/report.html#rankings) · [Cost evidence](https://etsabary.github.io/system-1-decision-benchmark/v5/report.html#cost) · [Archived full v4](https://etsabary.github.io/system-1-decision-benchmark/v4/report.html)\n\n'
readme+='## Main comparison\n\n![Accuracy on the 1,456 retained questions](results/releases/'+NAME+'/comparison_accuracy.png)\n\n'
readme+='| Configuration | Correct / 1,456 | Accuracy | Median | p95 | Selected-record known cost | Cost / 1,000 | Usable | Cost evidence |\n|---|---:|---:|---:|---:|---:|---:|---:|---|\n'
for mid in mids:
 m=models[mid];value,basis=cv(mid);mark=cost_mark(mid)
 readme+=f"| {m['label']} | {m['correct']}/1,456 | {m['accuracy']:.2%} | {speed_mark(m['median_ms'])} {m['median_ms']:,.0f} ms | {speed_mark(m['p95_ms'])} {m['p95_ms']:,.0f} ms | {mark} {total_cost(mid)} | {mark} {value} | {m['valid']}/1,456 | {basis} |\n"
readme+='\n## Perplexity v1.3 and HeyGen Decision 1\n\n'+refresh_text+'\n\n'+refresh_comparison+'\n\n'+refresh_ranks+'\n\n'+refresh_cost+'\n\n'+refresh_limits+'\n\n'
readme+='\n## Gemini Decision 1: native hosted decisions\n\n'+gemini_text+'\n\n'+gemini_analysis+'\n\n'+gemini_limits+'\n\n'
readme+='\n## D3 Flash 9B: a local comparison\n\n'+d3_text+'\n\n'+d3_analysis+'\n\n'+d3_limits+'\n\n'
readme+='\n## SingVL: two-computer local inference\n\n'+singvl_text+'\n\n'+singvl_analysis+'\n\n'+singvl_limits+'\n\n'
readme+='\n## Drex Max v1.1: a separately tested native version\n\n'+decision_text+'\n\n'+drex_comparison_text+'\n\n'+drex_cost_text+'\n\n'+drex_counter_text+'\n\n'
readme+='\n## REAX: accuracy with an ensemble cost and latency trade-off\n\n'+tradeoff+'\n\n'+specialist_tradeoff+'\n\n'
readme+='\nTeal model names indicate hosted decisions, purple local baselines, rose the two-computer local D3 and SingVL deployments, and gold reasoning-disabled LLM references. Speed and cost use 🟩 green / 🟨 yellow / 🟧 orange / 🟥 red bands: ≤250 / ≤500 / ≤1,000 / >1,000 ms; ≤$0.010 / ≤$0.025 / ≤$0.050 / >$0.050 per 1,000 questions. ⬜ denotes unmetered or unknown cost. “+ ?” marks missing charges. API-reported USD, tariff estimates, EUR-to-USD FX estimates and free access remain distinct.\n\n'
readme+='## Response time and cost\n\nTimings and costs use individual selected primary records. All 38 preceding configurations are unchanged; four native hosted configurations add separately measured sessions. Morph Reflex and REAX 1.3 retain their preceding full-bank sessions. Median and p95 include selected unsuccessful requests; they are never averages of category medians. Monetary amounts are selected-record charges or estimates, not guaranteed future prices.\n\n'+hosted_cost_note+'\n\n'
for kind,title in [('latency','Response time'),('cost','Cost per 1,000 questions')]:
 readme+=f'### {title}\n\n![{title} for provisional v5](results/releases/{NAME}/comparison_{kind}.png)\n\n'
readme+='## Category results\n\nThe category scale is fixed at 0–100%. Each cell shows correct/retained total and percentage; ★ marks all tied leaders. Category sizes vary after removal.\n\n![Fixed accuracy scale](results/releases/'+NAME+'/accuracy_legend.png)\n\n'
for slug,title,fids in groups:
 readme+='### '+title+'\n\n'+('; '.join(fid+' '+guide[fid]['display_name']+f" (n={guide[fid]['questions']})" for fid in fids))+'.\n\n!['+title+' accuracy with retained counts and tied leaders](results/releases/'+NAME+'/categories_'+slug+'.png)\n\n'
readme+='## Below the 45% cutoff\n\nV5 uses the retained 1,456-question bank and 45% cutoff. Historical v4 scores below use its original 2,157 questions and former 62% cutoff.\n\n'
for mid in s['below_cutoff']:
 m=models[mid];archived=''
 if mid in v4['models']:
  old=v4['models'][mid];archived=f" Historical v4: {old['correct']}/2,157 ({old['accuracy']:.2%})."
 readme+=f"- **{m['label']}: v5 {m['correct']}/1,456 ({m['accuracy']:.2%})**; coverage {m['coverage']:.2%}.{archived}\n"
if superseded:
 readme+='\n## Superseded versions retained for reference\n\nVersion replacement is separate from the 45% cutoff. All measurements and recorded responses remain available.\n\n'
 for mid in superseded:
  m=models[mid];readme+=f"- **{m['label']}: {m['correct']}/1,456 ({m['accuracy']:.2%})**; median/p95 {m['median_ms']:,.0f}/{m['p95_ms']:,.0f} ms; known cost {total_cost(mid)}. Superseded by the separately tested native version, not below cutoff.\n"
readme+='\n## Historical v4 exploratory screens\n\nThese are unchanged historical samples with their original denominators, not v5 scores or classifications against its threshold. No stopped test was resumed.\n\n'
for label,text,name in history:
 readme+=f'- **{label}:** {text} [Historical method and limits](results/releases/{NAME}/{name}).\n'
readme+='\n## Selection, scope and limitations\n\nThe removed set was chosen using the exact recorded answers of the original 26-model v4 main graph, including four reasoning-disabled LLM references. This cohort-conditioned selection leaves the original cohort’s relative overall order unchanged and changes category weights unevenly. It is not an independent demonstration of general difficulty. Future configurations use the frozen 1,456 inputs and exact 45% threshold.\n\n'
readme+='The quantitative category retains 60 questions selected for Fastino/D3 Artemis errors and 140 selected for an error by at least one of Fastino, Mammoth, GPT-6 Sol, D3 Ultra or Drex Max. Multiple selection models distribute that dependence without removing it. Public questions may appear in training data; these scores are not human IQ norms. The separate 120 companion diagnostics remain excluded.\n\n'
readme+='The smaller bank reduces future requests by **701/2,157 (32.5%)**. Token charges need not fall by the same proportion. Costs and response times preserve differences in dates, routes, model settings, precision and hardware.\n\n'
readme+='## Question origins and licenses\n\nThe retained bank has **1,236 questions from the project development bank, 20 MAIQ number sequences and 200 AQuA quantitative questions**. AQuA-RAT declares Apache-2.0 and contains crowdsourced admissions-style mathematics, not authenticated official GRE or SAT questions. MAIQ’s repository declares MIT, but original human-test item rights remain unestablished; inclusion retains that caveat. The development lineage does not fully establish individual authorship or possible external influences for every project-bank item. The project MIT license does not supersede third-party rights. The two noncommercial LogiQA items remain outside the bank. [Full source and license notices](results/releases/'+NAME+'/SOURCE_AND_LICENSES.md).\n\n'
readme+='## Download and reproducibility\n\nRanks in archived collection notes and release-time analysis files describe their original dated cohort. Current cohort ranks appear in the main comparison and current model sections above.\n\n'
for name,label in downloads:readme+=f'- [{label}](results/releases/{NAME}/{name})\n'
readme+='\nThe [scripts/](scripts/README.md) support offline validation without credentials. The [preceding hosted v5 report](results/releases/system1_v5_hosted_2026-11-09/report.html), [initial v5 report](results/releases/system1_v5_provisional_2026-11-09/report.html), [full v4 report](results/releases/system1_v4_openai_2026-11-06/report.html), [v3](results/releases/system1_v3_presentation_2026-11-01/report.html) and [v2](results/releases/system1_v2_presentation_2026-11-01/report.html) remain unchanged. Model-selected choices and the gold scoring key remain private.\n\n```sh\npython3 scripts/validate_system1_v5_hosted_refresh_2026_11_13.py results/releases/'+NAME+' results/releases/system1_v5_gemini_decision1_2026-11-13\npython3 scripts/validate_october21_release.py\n```\n'
# This file is distributed inside both a dated release and docs/v5.
# Its own assets are siblings; cross-release and script links use stable URLs.
readme=readme.replace('results/releases/'+NAME+'/','')
for prefix in ('results/releases/','scripts/'):
 readme=readme.replace(']('+prefix,'](https://github.com/etsabary/system-1-decision-benchmark/blob/main/'+prefix)
(OUT/'README_V5.md').write_text(readme)

unchanged=['questions_1456.jsonl','source_metadata_1456.jsonl','statistics.json','all_category_scores.csv','category_guide.json','timing_evidence.csv.gz','cost_evidence.csv.gz','cost_statistics.json','audit_receipt.json','SOURCE_AND_LICENSES.md','PROJECT_LICENSE_MIT.txt','selection_provenance.json','removed_items.csv','retained_items.csv','correctness_evidence.csv.gz','removed_correctness_evidence.csv.gz']
unchanged += ['HOSTED_MODEL_NOTES.md','hosted_model_audits.json','hosted_cost_summaries.json','new_model_comparison.json','REAX_TERRA_COMPARISON.md','native_currency_cost_evidence.csv.gz','fx_receipt.json','ecb_eurofxref_2026-11-09.xml','baseline_v5_audit_receipt.json']
unchanged += ['SINGVL_DISTRIBUTED_NOTES.md','singvl_hardware.json','singvl_model_audit.json','singvl_usage_evidence.csv.gz','singvl_analysis.json','parent_drex_audit_receipt.json']
unchanged += ['D3_FLASH_NOTES.md','d3_flash_hardware.json','d3_flash_model_audit.json','d3_flash_usage_evidence.csv.gz','d3_flash_transport_phases.json','d3_flash_analysis.json','d3_flash_category_comparison.csv','parent_singvl_audit_receipt.json']
unchanged += ['DREX_VERSION_NOTES.md','drex_comparison.json','drex_model_audit.json','drex_usage_evidence.csv.gz','drex_counter_policy.json','drex_version_provenance.json','drex_transport_phases.json','parent_hosted_audit_receipt.json']
unchanged += ['GEMINI_DECISION1_NOTES.md','gemini_decision1_model_audit.json','gemini_decision1_usage_evidence.csv.gz','gemini_decision1_analysis.json','gemini_decision1_category_comparison.csv','parent_d3_flash_audit_receipt.json']
unchanged += ['HOSTED_REFRESH_NOTES.md','hosted_refresh_model_audits.json','hosted_refresh_usage_evidence.csv.gz','hosted_refresh_analysis.json','hosted_refresh_category_comparison.csv','pplx_version_comparison.json','parent_gemini_audit_receipt.json']
unchanged += [str(x.relative_to(SOURCE)) for x in sorted((SOURCE/'third_party_licenses').iterdir()) if x.is_file()]
for name in unchanged:assert (OUT/name).read_bytes()==(SOURCE/name).read_bytes(),name
def filehash(p):return hashlib.sha256(p.read_bytes()).hexdigest()
files={str(p.relative_to(OUT)):filehash(p) for p in sorted(OUT.rglob('*')) if p.is_file() and p.name!='manifest.json'}
manifest={'version':'v5-provisional-hosted-refresh','questions':1456,'categories':43,'measured_models':len(models),'main_models':len(mids),'superseded_model_ids':superseded,'replacement_decision':replacement,'minimum_overall_accuracy':cutoff,'inclusion_threshold':threshold,'frozen_gemini_v5_manifest_sha256':filehash(REPO/'results/releases/system1_v5_gemini_decision1_2026-11-13/manifest.json'),'pplx_replacement_decision':json.loads((OUT/'pplx_version_comparison.json').read_text())['replacement_decision'],'frozen_d3_flash_v5_manifest_sha256':filehash(REPO/'results/releases/system1_v5_d3_flash_2026-11-11/manifest.json'),'frozen_singvl_v5_manifest_sha256':filehash(REPO/'results/releases/system1_v5_singvl_2026-11-11/manifest.json'),'frozen_drex_v5_manifest_sha256':filehash(REPO/'results/releases/system1_v5_drex_2026-11-09/manifest.json'),'source_files_sha256':{name:filehash(REPO/name) for name in ['scripts/publish_system1_v5_hosted_refresh_2026_11_13.py','scripts/validate_system1_v5_hosted_refresh_2026_11_13.py']},'frozen_v4_manifest_sha256':filehash(REPO/'results/releases/system1_v4_openai_2026-11-06/manifest.json'),'frozen_v5_manifest_sha256':filehash(REPO/'results/releases/system1_v5_provisional_2026-11-09/manifest.json'),'frozen_hosted_v5_manifest_sha256':filehash(REPO/'results/releases/system1_v5_hosted_2026-11-09/manifest.json'),'unchanged_files_sha256':{name:filehash(SOURCE/name) for name in unchanged},'files_sha256':files}
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n')
print(json.dumps({'groups':len(groups),'categories':len(guide),'main_models':len(mids),'all_models':len(models),'unchanged_data_files':len(unchanged),'report':'report.html','threshold':threshold_label}))
