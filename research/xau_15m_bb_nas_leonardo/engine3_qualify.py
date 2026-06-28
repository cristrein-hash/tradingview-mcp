#!/usr/bin/env python3
"""ENGINE 3 — Fase 2: QUALIFICAÇÃO-PRIMEIRO. Objetivo (Cris): capturar TODOS MONSTER+FORTE com MÍNIMO de trades.
Métrica = recall_MONFORTE alto + n pequeno (qualidade, não quantidade). Knife pré-gateado. Fonte única de métrica.
AUC is_monforte sobre TODAS features (15M+HTF). Combos 2-3 sobre top features; ranqueia FRONTIER por F(score)=
precisão-mf * recall (favorece pegar os fortes com pouco trade). Reporta n/recall/MF/MEDFRACO/NONE/per-ano/leave-block."""
import json,statistics as st
from pathlib import Path
from itertools import combinations
HERE=Path(__file__).parent
ROWS=[json.loads(l) for l in (HERE/"entry_candidates_htf.jsonl").read_text().splitlines()]
# normaliza HTF None->faltante; numéricos
META={'block','t','cj_t','yr','label','is_monforte','is_medfraco','is_bottom'}
def isnum(v): return isinstance(v,(int,float)) and not isinstance(v,bool)
NUMF=[k for k in ROWS[0] if k not in META and isnum(ROWS[0].get(k))]
MFtot=sum(r["is_monforte"] for r in ROWS); N=len(ROWS); base=MFtot/N
print(f"N={N} MON+FORTE={MFtot} base={100*base:.2f}% | features={len(NUMF)} (15M+HTF)")
def auc(feat):
    vv=[(r[feat],r["is_monforte"]) for r in ROWS if isnum(r.get(feat))]
    pos=[v for v,y in vv if y]; neg=[v for v,y in vv if not y]
    if not pos or not neg: return .5
    sv=sorted(vv,key=lambda x:x[0]); vals=[v for v,_ in sv]; ranks=[0]*len(vals); j=0
    while j<len(vals):
        k=j
        while k+1<len(vals) and vals[k+1]==vals[j]: k+=1
        rr=(j+k)/2+1
        for m in range(j,k+1): ranks[m]=rr
        j=k+1
    rsp=sum(ranks[m] for m in range(len(sv)) if sv[m][1]==1)
    return (rsp-len(pos)*(len(pos)+1)/2)/(len(pos)*len(neg))
aucs=sorted(((f,auc(f)) for f in NUMF),key=lambda x:-abs(x[1]-.5))
print("\n=== AUC is_monforte (15M+HTF, top 18) ===")
for f,a in aucs[:18]: print(f"  {f:<22}{a:.3f} {'+' if a>=.5 else '-'}")
# KNIFE pre-gate
G=[r for r in ROWS if r.get("falling_knife",0)==0]
print(f"\npós gate anti-faca: {len(G)} cand | MON+FORTE {sum(r['is_monforte'] for r in G)}/{MFtot}")
TOP=[f for f,a in aucs[:14] if f!="falling_knife"]
dirn={f:(1 if a>=.5 else -1) for f,a in aucs}
def thr(f,q):
    vals=sorted(r[f] for r in ROWS if isnum(r.get(f))); return vals[int(q*len(vals))]
# thresholds mais APERTADOS (q0.80 / q0.20) p/ seleção tight
TH={f:(thr(f,0.80) if dirn[f]>0 else thr(f,0.20)) for f in TOP}
def passes(r,cc):
    for f in cc:
        v=r.get(f)
        if not isnum(v): return False
        if dirn[f]>0 and v<TH[f]: return False
        if dirn[f]<0 and v>TH[f]: return False
    return True
def ev(cc):
    sel=[r for r in G if passes(r,cc)]; n=len(sel)
    if n<8: return None
    mf=sum(r["is_monforte"] for r in sel); mfr=sum(r["is_medfraco"] for r in sel); non=sum(1 for r in sel if r["label"]=="NONE")
    return {"combo":cc,"n":n,"mf":mf,"recall":round(mf/MFtot,3),"prec":round(mf/n,3),"medfraco":mfr,"none":non,"lift":round((mf/n)/base,1)}
res=[]
for sz in (2,3):
    for cc in combinations(TOP,sz):
        m=ev(cc)
        if m and m["mf"]>=10: res.append(m)
# score qualidade: recall alto com n pequeno -> precisão*recall
for m in res: m["score"]=round(m["prec"]*m["recall"],4)
res.sort(key=lambda x:-x["score"])
def peryear(cc):
    return {y:f"{sum(r['is_monforte'] for r in G if r['yr']==y and passes(r,cc))}/{sum(1 for r in G if r['yr']==y and passes(r,cc))}" for y in (2024,2025,2026)}
print(f"\n=== FRONTIER (qualidade=prec*recall; knife-gated; thresholds tight q80/20) — top 14 ===")
print(f"{'combo':<50}{'n':>4}{'mf':>4}{'rec':>5}{'prec':>6}{'lift':>5}{'mfrc':>5}{'none':>5}")
for m in res[:14]:
    print(f"{'+'.join(x[:15] for x in m['combo']):<50}{m['n']:>4}{m['mf']:>4}{m['recall']:>5}{m['prec']:>6}{m['lift']:>5}{m['medfraco']:>5}{m['none']:>5}")
if res:
    b=res[0]; print(f"\ntop por ano: {peryear(b['combo'])}  combo={b['combo']}")
json.dump({"base":base,"MFtot":MFtot,"aucs":[(f,a) for f,a in aucs],"frontier":[{k:(v if k!='combo' else list(v)) for k,v in m.items()} for m in res[:40]]},open(HERE/"engine3_qualify.json","w"),indent=1)
print("-> engine3_qualify.json")
