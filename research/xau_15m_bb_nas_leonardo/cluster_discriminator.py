#!/usr/bin/env python3
"""DISCRIMINADOR: a confluência bubbles-SELL+NAS-LONG distingue FUNDO VERDADEIRO de TRAP (mínima que falhou)?
Senão, é só MECÂNICO (vender precede qualquer mínima). Pega TODAS as mínimas/máximas fractais (candidatas), rotula:
  - VERDADEIRO: excursão favorável >= TRUE_M*ATR antes de perfurar o extremo (BUF*ATR).
  - TRAP: excursão < TRAP_M*ATR (não entregou; foi perfurada cedo).
Mede na MESMA janela causal (t-PRE,t] a fração da cor-tese, NAS-dir e combo. Compara VERDADEIRO vs TRAP. RAW-causal. 2026-06-26."""
import json,statistics as st,bisect
from pathlib import Path
HERE=Path(__file__).parent
PRIM={p.name.split(".")[0].replace("XAUUSD_15m_replay_",""):json.loads(p.read_text()) for p in sorted((HERE/"primitives").glob("*.primitives.json"))}
SZ={"S":1,"M":2,"L":3}; PRE=16*900; K=4; HOR=192; BUF=0.25; TRUE_M=8; TRAP_M=3
BUB={k:sorted([json.loads(l) for l in (HERE/"bubbles"/f"{k}.bubbles.jsonl").read_text().splitlines() if l],key=lambda x:x["t"]) for k in PRIM}
NAS={k:sorted([e for e in PRIM[k]["nas_events"] if e.get("t") and e.get("dir")],key=lambda x:x["t"]) for k in PRIM}
def win_metrics(key,t):
    bb=BUB[key]; ts=[x["t"] for x in bb]; lo=bisect.bisect_left(ts,t-PRE); hi=bisect.bisect_right(ts,t)
    sellw=buyw=0
    for x in bb[lo:hi]:
        w=SZ[x["size"]]; sellw+=w if x["side"]=="SELL" else 0; buyw+=w if x["side"]=="BUY" else 0
    pol=sellw/(sellw+buyw) if (sellw+buyw)>0 else None
    ne=NAS[key]; nts=[x["t"] for x in ne]; a=bisect.bisect_left(nts,t-PRE); b=bisect.bisect_right(nts,t)
    nl=sum(1 for x in ne[a:b] if x["dir"]=="LONG"); ns=sum(1 for x in ne[a:b] if x["dir"]=="SHORT")
    return pol,sellw+buyw,nl,ns
def rev(s,p,low):
    Lp=s[p]["l"] if low else s[p]["h"]; a=s[p]["atr"]
    if not a: return None
    ext=Lp; end=min(p+HOR,len(s)-1)
    for i in range(p+1,end+1):
        if low:
            if s[i]["l"]<Lp-BUF*a: break
            ext=max(ext,s[i]["h"])
        else:
            if s[i]["h"]>Lp+BUF*a: break
            ext=min(ext,s[i]["l"])
    return ((ext-Lp) if low else (Lp-ext))/a
def pivots(s,low):
    H=[x["h"] for x in s]; L=[x["l"] for x in s]
    return [p for p in range(K,len(s)-K) if (low and L[p]==min(L[p-K:p+K+1])) or ((not low) and H[p]==max(H[p-K:p+K+1]))]
def gather(low):
    true=[]; trap=[]
    for k,pr in PRIM.items():
        s=pr["series"]
        for p in pivots(s,low):
            rv=rev(s,p,low)
            if rv is None: continue
            pol,tot,nl,ns=win_metrics(k,s[p]["t"]);
            cor=(pol if low else (1-pol)) if pol is not None else None  # SELL-frac p/ fundo, BUY-frac p/ topo
            ndir=nl if low else ns
            rec={"cor":cor,"ndir":ndir,"intens":tot}
            (true if rv>=TRUE_M else (trap if rv<TRAP_M else [])).append(rec) if rv>=TRUE_M or rv<TRAP_M else None
            if rv>=TRUE_M: true.append(rec)
            elif rv<TRAP_M: trap.append(rec)
    return true,trap
def rep(v,label):
    cors=[x["cor"] for x in v if x["cor"] is not None]
    combo=sum(1 for x in v if x["cor"] is not None and x["cor"]>0.5 and x["ndir"]>=1)
    print(f"   {label:<22} n={len(v):>4} | cor-tese fração méd={st.mean(cors):.2f} %>0.5={100*sum(1 for c in cors if c>0.5)/len(cors):.0f} "
          f"| %NAS-dir>=1={100*sum(1 for x in v if x['ndir']>=1)/len(v):.0f} | COMBO(cor>0.5 & NAS-dir)={100*combo/len(v):.0f}%")
for low,name in [(True,"FUNDOS — cor=SELL, NAS=LONG"),(False,"TOPOS — cor=BUY, NAS=SHORT")]:
    t,tr=gather(low)
    print(f"\n=== {name}  (VERDADEIRO rev>={TRUE_M}ATR  vs  TRAP rev<{TRAP_M}ATR) ===")
    rep(t,"VERDADEIRO"); rep(tr,"TRAP")
    ct=[x["cor"] for x in t if x["cor"] is not None]; cr=[x["cor"] for x in tr if x["cor"] is not None]
    print(f"   Δ cor-tese (verdadeiro − trap) = {st.mean(ct)-st.mean(cr):+.2f}  → se ~0, confluência é MECÂNICA (não discrimina)")