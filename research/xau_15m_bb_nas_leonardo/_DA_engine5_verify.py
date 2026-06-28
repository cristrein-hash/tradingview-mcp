#!/usr/bin/env python3
"""DA VERIFY of Engine 5 transversal-convergence claim (Cris 2026-06-28).
Adversarial reproduction of engine5_eval.py + 5 targeted checks:
Q1 null-of-max validity + R-sim parity. Q2 conv>=6 K=2000 / ex-2025 / ex-top5 / per-year.
Q3 LABEL-lift vs R-lift (does conv select higher-R, or just lower-DD smaller-n?).
Q4 specificity vs NONE noise (4305), not just MED/FRACO control.
Q5 overlap with E4 beta/quiet filter (h1n_trend up + atr_regime<1 + killzone==0).
In-sample, RAW-causal, NO OOS. Calibration on full universe, not the curated 61/144."""
import json,statistics as st,random
from pathlib import Path
HERE=Path(__file__).parent
PRIM={p.name.split(".")[0].replace("XAUUSD_15m_replay_",""):json.loads(p.read_text()) for p in sorted((HERE/"primitives").glob("*.primitives.json"))}
PRIMK={k[:10]:v for k,v in PRIM.items()}
ROWS=[json.loads(l) for l in (HERE/"entry_candidates_htf.jsonl").read_text().splitlines()]
HMAX=480; RCAP=20.0
def cf_low(s,i):
    L=[b["l"] for b in s]; lo=max(2,i-120); bst=None
    for p in range(lo,i-1):
        if L[p]==min(L[p-2:p+3]): bst=L[p]
    return bst
def letrun(s,cj,entry,sl,atr):
    risk=entry-sl
    if risk<=0: return None
    trail=sl; r1=False; ex=None; end=min(cj+HMAX,len(s)-1)
    for k in range(cj+1,end+1):
        if s[k]["l"]<=trail: ex=trail; break
        if (s[k]["h"]-entry)/risk>=1: r1=True
        if r1:
            sw=cf_low(s,k)
            if sw: trail=max(trail,sw-0.1*atr)
    if ex is None: ex=s[end]["c"]
    return max(-1.0,min(RCAP,(ex-entry)/risk))
def f(r,k,d=None):
    v=r.get(k); return v if isinstance(v,(int,float)) and not isinstance(v,bool) else d
for r in ROWS:
    pr=PRIMK.get(r["block"]); s=pr["series"]; tmap={b["t"]:i for i,b in enumerate(s)}
    p=tmap.get(r["t"]); cj=tmap.get(r["cj_t"]); r["R"]=None
    if p is None or cj is None or cj+2>=len(s): continue
    atr=s[p]["atr"] or s[cj]["atr"]
    if atr:
        entry=s[cj]["c"]; sl=min(x["l"] for x in s[p:cj+1])-0.1*atr; r["R"]=letrun(s,cj,entry,sl,atr)
    P=[f(r,"atr_regime",1)<1.0, f(r,"h1n_trend",0)==1, f(r,"sell_bub_w",9)<=2,
       f(r,"downleg_eff",1)<0.30, f(r,"h1_pos",0)>=0.10, f(r,"killzone",1)==0]
    r["conv"]=sum(1 for x in P if x); r["P"]=P
G=[r for r in ROWS if r["R"] is not None]
MF=sum(r["is_monforte"] for r in G); base=MF/len(G); baseavg=st.mean([r["R"] for r in G])
print(f"universo R-ok={len(G)} | MON+FORTE={MF} (base {100*base:.2f}%) | base avgR={baseavg:.3f}")
print(f"NONE noise={sum(1 for r in G if r['label']=='NONE')} | MED/FRACO control={sum(r['is_medfraco'] for r in G)}")

def cell(sel,name):
    rs=[r["R"] for r in sel]; sm=sum(rs); n=len(sel)
    w=sum(1 for x in rs if x>0); mf=sum(r["is_monforte"] for r in sel)
    eq=pk=dd=0
    for x in rs: eq+=x; pk=max(pk,eq); dd=min(dd,eq-pk)
    print(f"  {name:<24} n={n:>4} avgR={sm/n:+.3f} WR={100*w/n:4.1f} sumR={sm:+6.1f} DD={dd:6.1f} MFprec={100*mf/n:.2f}% precLift={(mf/n)/base:.2f}")

print("\n=== Q1 null-of-max validity: shuffle R within full universe, fixed masks (correct conditional-mean null) ===")
print("  The null tests: given these subset SIZES, is the observed mean separable from random R assignment? Valid for R-edge.")
print("  (Note: it does NOT test MON+FORTE selection — that's the LABEL question, handled in Q3/Q4.)")

print("\n=== Q3 LABEL-lift vs R-lift: does higher conv select higher-R trades? ===")
for k in (0,3,4,5,6):
    sel=[r for r in G if r["conv"]>=k] if k else G
    cell(sel,f"conv>={k}" if k else "TAKE-ALL")
print("  -> if avgR rises but precLift(R for MON+FORTE) stays ~1 and DD shrinks with n: beta-quiet filter, not R-selection.")

print("\n=== Q4 specificity vs NONE noise (4305) not just MED/FRACO ===")
for k in (4,5,6):
    sel=[r for r in G if r["conv"]>=k]
    n=len(sel); mf=sum(r["is_monforte"] for r in sel)
    none=sum(1 for r in sel if r["label"]=="NONE"); mfr=sum(r["is_medfraco"] for r in sel)
    # recall of NONE vs recall of MON+FORTE
    NONE_tot=sum(1 for r in G if r["label"]=="NONE")
    print(f"  conv>={k}: captures {mf}/{MF} MON+FORTE (rec {100*mf/MF:.0f}%) AND {none}/{NONE_tot} NONE (rec {100*none/NONE_tot:.0f}%) -> NONE recall ~= MF recall? then no isolation")

print("\n=== Q5 overlap with E4 beta/quiet filter (h1n_trend==1 & atr_regime<1 & killzone==0) ===")
def e4q(r): return f(r,"h1n_trend",0)==1 and f(r,"atr_regime",1)<1.0 and f(r,"killzone",1)==0
E4=[r for r in G if e4q(r)]
cell(E4,"E4-quiet(3 preds)")
for k in (4,5,6):
    c=[r for r in G if r["conv"]>=k]
    inter=[r for r in c if e4q(r)]
    print(f"  conv>={k}: n={len(c)} | overlap w/ E4-quiet = {len(inter)}/{len(c)} = {100*len(inter)/len(c):.0f}%")
print("  -> high overlap => convergence is re-expressing the same quiet-uptrend beta filter.")

print("\n=== Q2 conv>=6 robustness (ex-2025, ex-top5, ex-both) ===")
c6=[r for r in G if r["conv"]>=6]; rs=[r["R"] for r in c6]; sm=sum(rs)
cell(c6,"conv>=6 full")
ex25=[r for r in c6 if r["yr"]!=2025]; cell(ex25,"conv>=6 ex-2025")
ex5=sorted(c6,key=lambda r:r["R"],reverse=True)[5:]; cell(ex5,"conv>=6 ex-top5")
exboth=sorted(ex25,key=lambda r:r["R"],reverse=True)[5:]; cell(exboth,"conv>=6 ex-2025 ex-top5")
for y in (2024,2025,2026):
    cell([r for r in c6 if r["yr"]==y],f"conv>=6 {y}")
top5=sorted(rs,reverse=True)[:5]
print(f"  top5={[round(x,1) for x in top5]} = {100*sum(top5)/sm:.0f}% of sumR | are top5 MON+FORTE? {[r['is_monforte'] for r in sorted(c6,key=lambda r:r['R'],reverse=True)[:5]]}")

print("\n=== Q2b tighter null-of-max K=2000 ===")
rules={f"conv>={k}":(lambda r,k=k:r["conv"]>=k) for k in (3,4,5,6)}
rules["R1"]=lambda r:r["P"][0] and r["P"][1] and r["P"][4]
rules["R3"]=lambda r:r["P"][0] and r["P"][2] and r["P"][3]
allrules=list(rules.items())
obs=[st.mean([r["R"] for r in G if fn(r)]) if any(fn(r) for r in G) else -9 for _,fn in allrules]
masks=[[fn(r) for r in G] for _,fn in allrules]
Rs=[r["R"] for r in G]; K=2000; cnt=[0]*len(allrules); random.seed(13)
for _ in range(K):
    random.shuffle(Rs)
    sh=[]
    for m in masks:
        sel=[Rs[i] for i in range(len(G)) if m[i]]
        sh.append(sum(sel)/len(sel) if sel else -9)
    mx=max(sh)
    for j in range(len(allrules)):
        if mx>=obs[j]: cnt[j]+=1
for (name,_),c in zip(allrules,cnt):
    print(f"  {name}: nullmax_p={c/K:.4f}")
