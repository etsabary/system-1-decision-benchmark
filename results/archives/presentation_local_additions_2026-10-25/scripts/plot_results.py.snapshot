#!/usr/bin/env python3
"""Publication graphics with shared scales, denominators, snapshots and dates."""
from repo_layout import repo_file
import json
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
s=json.loads((repo_file("analysis/summary.json", root=ROOT)).read_text())
models=["jev113","jev114","luna"]
colors={"jev113":"#087f8c","jev114":"#d1731a","luna":"#7353ba"}
plt.rcParams.update({"font.family":"DejaVu Sans","font.size":10,"svg.fonttype":"none","svg.hashsalt":"jev-three-model-reference"})


def save(fig,name):
    for suffix in ["png","svg"]:
        target=repo_file("figures", root=ROOT)/f"{name}.{suffix}"
        kwargs={"metadata":{"Date":None}} if suffix=="svg" else {}
        fig.savefig(target,dpi=180,facecolor=fig.get_facecolor(),**kwargs)
        if suffix=="svg":target.write_text("\n".join(x.rstrip() for x in target.read_text().splitlines())+"\n")


families=s["by_family"]
fig=plt.figure(figsize=(14,16),facecolor="#f7f9fc")
ax=fig.add_axes([.34,.14,.61,.70])
v=np.array([[100*f[m]["accuracy_attempted"] for m in models] for f in families])
ax.imshow(v,vmin=0,vmax=100,cmap="YlGnBu",aspect="auto")
ax.set_yticks(range(25),[f["family"] for f in families],fontsize=10)
ax.set_xticks(range(3),["Jev 1.13\n80.1% overall","Jev 1.14\n82.0% overall","GPT-6 Luna Decisions\n60.5% overall"],fontsize=11,fontweight="bold")
ax.xaxis.tick_top();ax.tick_params(axis="both",length=0,pad=12)
for i,f in enumerate(families):
    for j,m in enumerate(models):
        r=f[m]
        ax.text(j,i,f"{r['correct']}/{r['attempted']}  ·  {100*r['accuracy_attempted']:.0f}%",ha="center",va="center",fontsize=10,fontweight="bold",color="white" if v[i,j]>=62 else "#14283f")
ax.set_xticks(np.arange(-.5,3,1),minor=True);ax.set_yticks(np.arange(-.5,25,1),minor=True)
ax.grid(which="minor",color="white",linewidth=2);ax.tick_params(which="minor",length=0)
for spine in ax.spines.values():spine.set_visible(False)
fig.text(.045,.955,"What changed with Jev 1.14",fontsize=24,fontweight="bold",color="#12263a")
fig.text(.045,.925,"The same 1,136 text questions · correct / all attempted · 25 reasoning families",fontsize=13,color="#415569")
fig.text(.045,.895,"Jev 1.13: Sep 22 + Oct 14, 2026   |   Jev 1.14: Oct 14–15, 2026   |   Luna: Oct 10 + 14, 2026",fontsize=10.5,color="#415569")
fig.text(.045,.078,"Jev 1.14 gained 22 correct answers overall: 56 gains and 34 losses, including two provider errors.\nLargest gains: spatial tracking (+8) and assignments (+7). Exact counting and object swaps did not improve.\nSnapshots: Jev 1.13.0 / 1.13-20260917 (256 historical alias-only records); Jev 1.14-20261014; Luna Decisions 20261006.\nErrors and refusals stay in denominators. Related variants are dependent; task counts are shown. Existing key, independent audit pending.",fontsize=10,color="#415569",linespacing=1.6)
save(fig,"ability_profile")

fig=plt.figure(figsize=(16,8),facecolor="#f7f9fc")
gs=fig.add_gridspec(1,2,left=.19,right=.96,bottom=.24,top=.77,wspace=.38,width_ratios=[1.05,1])
a=fig.add_subplot(gs[0]);b=fig.add_subplot(gs[1])
diagnostics=[("Core questions",640,lambda m:next(r for r in s["by_role"] if r["role"]=="core")[m]["correct"]),
    ("All five rotations\ncorrect",25,lambda m:s["panels"][m]["rotation"]["all_correct"]),
    ("Both changed-fact\nanswers correct",25,lambda m:s["panels"][m]["contrast"]["both_correct"]),
    ("Candidate checks\ncorrect",80,lambda m:s["panels"][m]["candidate_checks"]["correct"])]
for j,m in enumerate(models):
    values=[100*fn(m)/n for _,n,fn in diagnostics]
    bars=a.barh(np.arange(4)+(j-1)*.24,values,height=.21,color=colors[m],label=s["labels"][m])
    for bar,(_,n,fn) in zip(bars,diagnostics):a.text(bar.get_width()+1,bar.get_y()+bar.get_height()/2,f"{fn(m)}/{n}",va="center",fontsize=8)
a.set_yticks(range(4),[x[0] for x in diagnostics],fontsize=10);a.invert_yaxis();a.set_xlim(0,112)
a.set_xticks([0,25,50,75,100]);a.set_xlabel("Correct / all planned cases (%)")
a.set_title("Capability and matched tests",loc="left",pad=18,fontweight="bold")
a.grid(axis="x",alpha=.18);a.set_axisbelow(True);a.spines[["top","right","left"]].set_visible(False)
for m in models:
    rows=[r for r in s["confidence"][m] if r["threshold"] in [.8,.9,.95]]
    x=[100*r["attempted"]/1136 for r in rows];y=[100*r["accuracy_attempted"] for r in rows]
    b.plot(x,y,"o-",color=colors[m],label=s["labels"][m],linewidth=2)
    for xx,yy,r in zip(x,y,rows):
        if r['threshold']==.95:
            offset=(-8,12) if m=="jev113" else (6,-16) if m=="jev114" else (5,12)
            b.annotate("≥0.95",(xx,yy),xytext=offset,textcoords="offset points",fontsize=8,color=colors[m],ha="right" if m=="jev113" else "left")
b.set_xlim(0,70);b.set_ylim(97.4,100.4);b.set_xlabel("Questions retained (% of all 1,136)");b.set_ylabel("Correct within retained subset (%)")
b.set_title("High confidence: accuracy and coverage",loc="left",pad=18,fontweight="bold");b.grid(alpha=.18);b.spines[["top","right"]].set_visible(False)
b.text(.04,.04,"Each curve: cutoffs 0.8, 0.9 and 0.95",transform=b.transAxes,fontsize=9,color="#415569")
fig.legend(*a.get_legend_handles_labels(),loc="lower center",bbox_to_anchor=(.57,.13),ncol=3,frameon=False,fontsize=10)
fig.text(.045,.93,"Improvement does not mean uniform reliability",fontsize=23,fontweight="bold",color="#12263a")
fig.text(.045,.87,"At confidence ≥0.95: Jev 1.13 = 543/544; Jev 1.14 = 602/603; Luna = 96/96.",fontsize=13,color="#415569")
fig.text(.045,.067,"Jev 1.14 retains 53.1% at ≥0.95, versus 47.9% for Jev 1.13 and 8.5% for Luna. Each Jev subset contains one error.\nZero observed Luna errors do not establish zero future error. Cutoffs are exploratory; retained sets differ.\nSnapshots and Toronto test dates match the ability profile. Source: analysis/summary.json.",fontsize=10,color="#415569",linespacing=1.6)
save(fig,"reliability_profile")
print("Rendered two PNG and two SVG comparison graphics")
