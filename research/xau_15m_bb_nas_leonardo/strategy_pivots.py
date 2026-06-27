#!/usr/bin/env python3
"""ESTRATÉGIA dos pivôs M8: LONG em cada fundo / SHORT em cada topo, na EXATA barra do pivô (mesma da plotagem).
Entry=close do bar do pivô; SL estrutural=extremo ∓0.1ATR; let-run trailing estrutural. R capado.
⚠️ NÃO-CAUSAL: entra no pivô confirmado-em-retrospecto = TETO com timing perfeito (o zigzag só confirma M8 depois).
RAW. 2026-06-26."""
import json,csv,datetime as dt,statistics as st
from pathlib import Path
HERE=Path(__file__).parent
PRIM={p.name.split(".")[0].replace("XAUUSD_15m_replay_",""):json.loads(p.read_text()) for p in sorted((HERE/"primitives").glob("*.primitives.json"))}
RCAP=20.0; HMAX=480
def cf_low(s,i):
    L=[b["l"] for b in s]; lo=max(2,i-120); bst=None
    for p in range(lo,i-1):
        if L[p]==min(L[p-2:p+3]): bst=L[p]
    return bst
def cf_high(s,i):
    H=[b["h"] for b in s]; lo=max(2,i-120); bst=None
    for p in range(lo,i-1):
        if H[p]==max(H[p-2:p+3]): bst=H[p]
    return bst
def letrun(s,ei,entry,sl,long,atr):
    risk=(entry-sl) if long else (sl-entry)
    if risk<=0: return None
    trail=sl; r1=False; ex=None; end=min(ei+HMAX,len(s)-1)
    for i in range(ei+1,end+1):
        if long:
            if s[i]["l"]<=trail: ex=trail; break
            if (s[i]["h"]-entry)/risk>=1: r1=True
            if r1:
                sw=cf_low(s,i)
                if sw: trail=max(trail,sw-0.1*atr)
        else:
            if s[i]["h"]>=trail: ex=trail; break
            if (entry-s[i]["l"])/risk>=1: r1=True
            if r1:
                sh=cf_high(s,i)
                if sh: trail=min(trail,sh+0.1*atr)
    if ex is None: ex=s[end]["c"]
    return max(-1.0,min(RCAP,((ex-entry) if long else (entry-ex))/risk))
# index t->bar por bloco
IDX={k:{b["t"]:j for j,b in enumerate(pr["series"])} for k,pr in PRIM.items()}
def blk(t):
    for k,pr in PRIM.items():
        s=pr["series"]
        if s[0]["t"]<=t<=s[-1]["t"]: return k
    return None
rows=list(csv.DictReader(open(HERE/"true_reversals_M8.csv")))
res={"LONG":[],"SHORT":[]}
for r in rows:
    t=int(r["t"]); k=blk(t)
    if not k or t not in IDX[k]: continue
    s=PRIM[k]["series"]; i=IDX[k][t]; atr=s[i]["atr"] or 1.0
    if i+2>=len(s): continue
    entry=s[i]["c"]
    if r["kind"]=="BOT":
        R=letrun(s,i,entry,s[i]["l"]-0.1*atr,True,atr); side="LONG"
    else:
        R=letrun(s,i,entry,s[i]["h"]+0.1*atr,False,atr); side="SHORT"
    if R is None: continue
    res[side].append({"R":R,"yr":dt.datetime.utcfromtimestamp(t).year,"t":t})
def rep(v,lab):
    if not v: print(f"  {lab}: vazio"); return
    n=len(v); sm=sum(x["R"] for x in v); wr=100*sum(1 for x in v if x["R"]>0)/n
    ts=sorted(v,key=lambda x:x["t"]); eq=pk=dd=0; stk=mstk=0
    for x in ts:
        eq+=x["R"];pk=max(pk,eq);dd=min(dd,eq-pk)
        if x["R"]<=0:stk+=1;mstk=max(mstk,stk)
        else:stk=0
    run=sum(1 for x in v if x["R"]>=5)
    print(f"  {lab}: n={n} WR={wr:.0f}% avgR={sm/n:+.2f} sumR={sm:+.0f} maxDD={dd:.0f}R streakL={mstk} runners(>=5R)={run}")
print("⚠️ TETO com timing perfeito (não-causal: entra no pivô confirmado em retrospecto)")
print("\nLONG nos fundos:"); rep(res["LONG"],"todos")
for y in (2024,2025,2026): rep([x for x in res["LONG"] if x["yr"]==y],f"  {y}")
print("\nSHORT nos topos:"); rep(res["SHORT"],"todos")
for y in (2024,2025,2026): rep([x for x in res["SHORT"] if x["yr"]==y],f"  {y}")
print("\nLONG+SHORT combinado:"); rep(res["LONG"]+res["SHORT"],"todos")
