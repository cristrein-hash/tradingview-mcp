#!/usr/bin/env python3
"""CLUSTERS bubbles+NAS sobre a BASE CORRIGIDA (zigzag fix). Controle decisivo = TRUE (perto de pivô confirmado M8)
vs TRAP (mínima/máxima fractal longe de pivô confirmado). Mede confluência causal na janela (t-PRE,t]:
  fração da cor-tese (SELL p/ fundo / BUY p/ topo, ponderada por tamanho S1/M2/L3), %NAS-dir, intensidade, COMBO.
Pergunta: confluência DISCRIMINA true de trap? E PRECISÃO: entre candidatos com COMBO, % que é true vs base-rate?
Reporta SÓ o veredito (mecânico vs real). RAW-causal. 2026-06-26."""
import json,bisect,statistics as st
from pathlib import Path
HERE=Path(__file__).parent
PRIM={p.name.split(".")[0].replace("XAUUSD_15m_replay_",""):json.loads(p.read_text()) for p in sorted((HERE/"primitives").glob("*.primitives.json"))}
SZ={"S":1,"M":2,"L":3}; PRE=16*900; K=4; M=8; REGION=24
BUB={k:sorted([json.loads(l) for l in (HERE/"bubbles"/f"{k}.bubbles.jsonl").read_text().splitlines() if l],key=lambda x:x["t"]) for k in PRIM}
NAS={k:sorted([e for e in PRIM[k]["nas_events"] if e.get("t") and e.get("dir")],key=lambda x:x["t"]) for k in PRIM}
def zigzag(s,M):
    n=len(s); start=0
    while start<n and not s[start]["atr"]: start+=1
    if start>=n: return []
    piv=[]; d=0; hi=s[start]["h"]; hi_i=start; lo=s[start]["l"]; lo_i=start
    for i in range(start+1,n):
        a=s[i]["atr"]
        if not a: continue
        thr=M*a
        if s[i]["h"]>hi: hi=s[i]["h"]; hi_i=i
        if s[i]["l"]<lo: lo=s[i]["l"]; lo_i=i
        if d>=0 and (hi-s[i]["l"])>=thr: piv.append((hi_i,"TOP")); d=-1; lo=s[i]["l"]; lo_i=i
        elif d<=0 and (s[i]["h"]-lo)>=thr: piv.append((lo_i,"BOT")); d=1; hi=s[i]["h"]; hi_i=i
    return piv
def win(key,t,low=True):
    bb=BUB[key]; ts=[x["t"] for x in bb]; a=bisect.bisect_left(ts,t-PRE); b=bisect.bisect_right(ts,t)
    sw=bw=0
    for x in bb[a:b]:
        w=SZ[x["size"]]; sw+=w if x["side"]=="SELL" else 0; bw+=w if x["side"]=="BUY" else 0
    cor=(sw/(sw+bw)) if (sw+bw)>0 else None
    if not low and cor is not None: cor=1-cor
    ne=NAS[key]; nt=[x["t"] for x in ne]; c=bisect.bisect_left(nt,t-PRE); e=bisect.bisect_right(nt,t)
    nl=sum(1 for x in ne[c:e] if x["dir"]=="LONG"); ns=sum(1 for x in ne[c:e] if x["dir"]=="SHORT")
    return cor,(sw+bw),(nl if low else ns)
def fractal(s,low=True):
    H=[x["h"] for x in s]; L=[x["l"] for x in s]
    return [p for p in range(K,len(s)-K) if (low and L[p]==min(L[p-K:p+K+1])) or ((not low) and H[p]==max(H[p-K:p+K+1]))]
def analyze(low=True):
    name="FUNDOS" if low else "TOPOS"
    blk_med={}
    for k in PRIM:
        s=PRIM[k]["series"]; v=[win(k,s[i]["t"],low)[1] for i in range(60,len(s),50)]; v=[x for x in v if x>0]
        blk_med[k]=st.median(v) if v else 1
    true=[]; trap=[]
    for k,pr in PRIM.items():
        s=pr["series"]; conf=set(i for i,kind in zigzag(s,M) if kind==("BOT" if low else "TOP"))
        for p in fractal(s,low):
            cor,tot,ndir=win(k,s[p]["t"],low)
            rec={"cor":cor,"ndir":ndir,"intens":tot/blk_med[k]}
            is_true=any(abs(p-c)<=REGION for c in conf)
            (true if is_true else trap).append(rec)
    def combo(v): return [x for x in v if x["cor"] is not None and x["cor"]>0.5 and x["ndir"]>=1 and x["intens"]>=1.0]
    def m(v,f): vals=[f(x) for x in v if f(x) is not None]; return st.mean(vals) if vals else 0
    ct=[x for x in true if x["cor"] is not None]; cr=[x for x in trap if x["cor"] is not None]
    print(f"\n=== {name} (base CORRIGIDA): TRUE={len(true)} (perto pivô M8) vs TRAP={len(trap)} ===")
    print(f"  cor-tese fração: true={m(ct,lambda x:x['cor']):.2f} trap={m(cr,lambda x:x['cor']):.2f} | Δ={m(ct,lambda x:x['cor'])-m(cr,lambda x:x['cor']):+.2f}")
    print(f"  %NAS-dir>=1:     true={100*sum(1 for x in true if x['ndir']>=1)/len(true):.0f} trap={100*sum(1 for x in trap if x['ndir']>=1)/len(trap):.0f}")
    print(f"  %COMBO:          true={100*len(combo(true))/len(true):.0f} trap={100*len(combo(trap))/len(trap):.0f}")
    # PRECISÃO: entre candidatos com COMBO, % true vs base-rate
    allc=true+trap; base=100*len(true)/len(allc)
    cb=combo(allc); prec=100*sum(1 for x in cb if x in true)/len(cb) if cb else 0
    # (recomputa is_true por identidade não confiável; refaço precisão por flag)
    print(f"  → veredito: Δ≈0 e %COMBO_true≈%COMBO_trap = MECÂNICO; Δ>0 e combo concentra em true = REAL")
# precisão correta com flag
def precision(low=True):
    blk_med={}
    for k in PRIM:
        s=PRIM[k]["series"]; v=[win(k,s[i]["t"],low)[1] for i in range(60,len(s),50)]; v=[x for x in v if x>0]; blk_med[k]=st.median(v) if v else 1
    rows=[]
    for k,pr in PRIM.items():
        s=pr["series"]; conf=set(i for i,kind in zigzag(s,M) if kind==("BOT" if low else "TOP"))
        for p in fractal(s,low):
            cor,tot,ndir=win(k,s[p]["t"],low)
            is_true=any(abs(p-c)<=REGION for c in conf)
            has_combo=(cor is not None and cor>0.5 and ndir>=1 and tot/blk_med[k]>=1.0)
            rows.append((is_true,has_combo))
    base=100*sum(1 for t,_ in rows if t)/len(rows)
    cb=[r for r in rows if r[1]]; prec=100*sum(1 for t,_ in cb if t)/len(cb) if cb else 0
    nm="FUNDOS" if low else "TOPOS"
    print(f"  [{nm}] PRECISÃO: P(true)|base={base:.0f}% → P(true|COMBO)={prec:.0f}% (n_combo={len(cb)}) | lift={prec/base:.2f}x")
for low in (True,False):
    analyze(low); precision(low)
