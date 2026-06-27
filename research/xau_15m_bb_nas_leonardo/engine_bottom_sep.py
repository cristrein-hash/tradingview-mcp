#!/usr/bin/env python3
"""PHASE 1-2 — Separabilidade determinística dos fundos (Cris 2026-06-27). Fonte ÚNICA de métrica (agente não calcula).
Alvos: STRONG3 = tier∈{MONSTRO,FORTE,MEDIO} vs FRACO (descartar FRACO, usar MÉDIO) ; STRONG2 = {MONSTRO,FORTE} vs resto.
Por feature: AUC (Mann-Whitney) + direção + estabilidade de SINAL por ano (24/25/26) e leave-block (8).
Busca de COMBOS 2-3 (AND com threshold=mediana, direção pelo AUC): maximiza taxa-strong na seleção c/ n>=25,
exige sinal estável (lift>1 em >=2 anos + nenhum bloco inverte forte). Sem promover; só ranquear. -> bottom_sep_report.txt + .json"""
import json,statistics as st
from pathlib import Path
from itertools import combinations
HERE=Path(__file__).parent
ROWS=[json.loads(l) for l in (HERE/"bottom_features.jsonl").read_text().splitlines()]
META={'block','t','yr','tier','tier_clean','leg_atr','power_score','session'}
NUMF=[k for k in ROWS[0] if k not in META and isinstance(ROWS[0][k],(int,float))]
def strong3(r): return 0 if r["tier"]=="FRACO" else 1
def strong2(r): return 1 if r["tier"] in ("MONSTRO","FORTE") else 0
BASE3=sum(strong3(r) for r in ROWS)/len(ROWS); BASE2=sum(strong2(r) for r in ROWS)/len(ROWS)

def auc(rows,feat,tgt):
    vv=[(r[feat],tgt(r)) for r in rows if r.get(feat) is not None]
    pos=[v for v,y in vv if y==1]; neg=[v for v,y in vv if y==0]
    if not pos or not neg: return None,0,0
    allv=sorted(v for v,_ in vv);
    # rank-sum (média de ranks p/ empates)
    rank={}
    i=0; sv=sorted(vv,key=lambda x:x[0])
    vals=[v for v,_ in sv]
    import bisect
    ranks=[0]*len(vals)
    j=0
    while j<len(vals):
        k=j
        while k+1<len(vals) and vals[k+1]==vals[j]: k+=1
        rr=(j+k)/2+1
        for m in range(j,k+1): ranks[m]=rr
        j=k+1
    rsum_pos=sum(ranks[m] for m in range(len(sv)) if sv[m][1]==1)
    n1=len(pos); n0=len(neg)
    U=rsum_pos-n1*(n1+1)/2
    a=U/(n1*n0)
    return round(a,3),n1,n0

def year_sign(feat,tgt,base):
    """lift (taxa-strong acima/abaixo da mediana) por ano, sinal."""
    med=st.median([r[feat] for r in ROWS if r.get(feat) is not None])
    out={}
    for y in (2024,2025,2026):
        g=[r for r in ROWS if r["yr"]==y and r.get(feat) is not None]
        hi=[r for r in g if r[feat]>=med];
        if hi: out[y]=round(sum(tgt(r) for r in hi)/len(hi)-sum(tgt(r) for r in g)/len(g),2)
    return out

# ---- single-feature ranking ----
res=[]
for f in NUMF:
    a3,n1,n0=auc(ROWS,f,strong3); a2,_,_=auc(ROWS,f,strong2)
    if a3 is None: continue
    res.append({"f":f,"auc3":a3,"auc2":a2,"sep3":round(abs(a3-.5),3),"ysign":year_sign(f,strong3,BASE3)})
res.sort(key=lambda x:-x["sep3"])

# leave-block sign stability p/ top features
def lb_stable(feat,tgt):
    med=st.median([r[feat] for r in ROWS if r.get(feat) is not None])
    signs=[]
    for blk in sorted(set(r["block"] for r in ROWS)):
        g=[r for r in ROWS if r["block"]!=blk and r.get(feat) is not None]
        hi=[r for r in g if r[feat]>=med]; lo=[r for r in g if r[feat]<med]
        if hi and lo: signs.append(1 if (sum(tgt(r) for r in hi)/len(hi))>=(sum(tgt(r) for r in lo)/len(lo)) else -1)
    return signs

# ---- combo search 2-3 ----
TOP=[r["f"] for r in res[:14]]
med={f:st.median([r[f] for r in ROWS if r.get(f) is not None]) for f in TOP}
dirn={r["f"]:(1 if r["auc3"]>=.5 else -1) for r in res}
def sel(rows,combo):
    out=[]
    for r in rows:
        ok=True
        for f in combo:
            v=r.get(f)
            if v is None: ok=False; break
            if dirn[f]>0 and v<med[f]: ok=False; break
            if dirn[f]<0 and v>med[f]: ok=False; break
        if ok: out.append(r)
    return out
combos=[]
for sz in (2,3):
    for combo in combinations(TOP,sz):
        s=sel(ROWS,combo); n=len(s)
        if n<25: continue
        rate=sum(strong3(r) for r in s)/n
        yrok=sum(1 for y in (2024,2025,2026) if [r for r in s if r["yr"]==y] and sum(strong3(r) for r in s if r["yr"]==y)/max(1,len([r for r in s if r["yr"]==y]))>BASE3)
        combos.append({"combo":combo,"n":n,"rate3":round(rate,3),"lift":round(rate/BASE3,2),"yrs_above":yrok,
                       "monforte":round(sum(strong2(r) for r in s)/n,2)})
combos.sort(key=lambda x:-x["rate3"])

# ---- report ----
L=[]
L.append(f"N={len(ROWS)} | BASE strong3(not-FRACO)={BASE3:.3f}  strong2(MON+FORTE)={BASE2:.3f}")
L.append(f"\n=== SINGLE FEATURES (top por separação AUC vs strong3) ===")
L.append(f"{'feature':<20}{'auc3':>6}{'auc2':>6}{'sep':>6}  ysign(24/25/26)  lb_sign")
for r in res[:22]:
    lb=lb_stable(r["f"],strong3); lbs=f"{sum(1 for x in lb if x>0)}/{len(lb)}+"
    L.append(f"{r['f']:<20}{r['auc3']:>6}{r['auc2']:>6}{r['sep3']:>6}  {str(r['ysign']):<22}{lbs}")
L.append(f"\n=== COMBOS 2-3 (taxa not-FRACO na seleção; base {BASE3:.2f}) — top 18 ===")
L.append(f"{'combo':<46}{'n':>4}{'rate3':>7}{'lift':>6}{'yrs+':>5}{'monf':>6}")
for c in combos[:18]:
    L.append(f"{'+'.join(x[:14] for x in c['combo']):<46}{c['n']:>4}{c['rate3']:>7}{c['lift']:>6}{c['yrs_above']:>5}{c['monforte']:>6}")
rep="\n".join(L); print(rep)
(HERE/"bottom_sep_report.txt").write_text(rep)
json.dump({"base3":BASE3,"base2":BASE2,"singles":res,"combos":combos[:30]},open(HERE/"bottom_sep.json","w"),indent=1)
print("\n-> bottom_sep_report.txt + bottom_sep.json")
