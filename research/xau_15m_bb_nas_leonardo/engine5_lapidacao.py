#!/usr/bin/env python3
"""LAPIDAÇÃO (Cris 2026-06-28): empilha TODAS as lentes pedidas + gate anti-faca; mostra a FRONTIER
quantos trades dariam × quantos MON+FORTE pegamos (recall) em cada nível de convergência k-de-N. Determinístico, R realizado."""
import json,statistics as st
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
# campos disponíveis?
keys=set(ROWS[0].keys())
need=["reclaim_atr","swept_prior_low","buy_bub_w","atr_regime","h1n_trend","sell_bub_w","downleg_eff","h1_pos","killzone","rsi_min8","h1_rsi","atr_compression_pre","legpos90","dist_demand_atr"]
print("campos ausentes:",[k for k in need if k not in keys] or "nenhum")
for r in ROWS:
    pr=PRIMK.get(r["block"]); s=pr["series"]; tmap={b["t"]:i for i,b in enumerate(s)}
    p=tmap.get(r["t"]); cj=tmap.get(r["cj_t"]); r["R"]=None
    if p is None or cj is None or cj+2>=len(s): continue
    atr=s[p]["atr"] or s[cj]["atr"]
    if atr:
        entry=s[cj]["c"]; sl=min(x["l"] for x in s[p:cj+1])-0.1*atr; r["R"]=letrun(s,cj,entry,sl,atr)
G=[r for r in ROWS if r["R"] is not None]
MF=sum(r["is_monforte"] for r in G)
# gate anti-faca (M1: NÃO 4H-bear-sem-demanda)
def antiknife(r): return not (f(r,"h4n_trend")==-1 and f(r,"h4n_in_demand")==0)
# 14 predicados (lentes pedidas), direção -> MON+FORTE
def preds(r):
    return [
      f(r,"reclaim_atr",0)>=1.0,            # reclamou da mínima
      f(r,"swept_prior_low",0)==1,          # sweep+reclaim
      f(r,"buy_bub_w",9)<=2,                # sem buy-bubble exaustão
      f(r,"atr_regime",1)<1.0,              # vol baixa (inverso)
      f(r,"h1n_trend",0)==1,                # 1D up
      f(r,"sell_bub_w",9)<=2,               # sell-bubble fraca
      f(r,"downleg_eff",1)<0.30,            # perna grind
      f(r,"h1_pos",0)>=0.10,                # h1_pos
      f(r,"killzone",1)==0,                 # off-killzone
      f(r,"rsi_min8",0)>=35,                # não-capitulado
      f(r,"h1_rsi",0)>=50,                  # 1H não-fraco
      f(r,"atr_compression_pre",0)>1.0,     # coiled-spring
      f(r,"legpos90",0)>=0.5,               # pullback raso
      f(r,"dist_demand_atr",99)<=1.0,       # perto de demanda
    ]
NP=14
gated=[r for r in G if antiknife(r)]
for r in gated: r["conv"]=sum(1 for x in preds(r) if x)
print(f"\nuniverso R-ok={len(G)} | MON+FORTE={MF} | pós anti-faca={len(gated)} (MF {sum(r['is_monforte'] for r in gated)})")
print(f"\n=== FRONTIER: empilhar as 14 lentes (anti-faca aplicado). conv = nº de lentes a favor ===")
print(f"{'conv>=':<7}{'n_trades':>9}{'MONFORTE':>9}{'recall':>7}{'MED/FRC':>8}{'NONE':>6}{'prec%':>6}{'avgR':>7}{'sumR':>7}{'DD':>7}  yr24/25/26")
for k in range(0,NP+1):
    sel=[r for r in gated if r["conv"]>=k]
    if not sel: continue
    n=len(sel); mf=sum(r["is_monforte"] for r in sel); mfr=sum(r["is_medfraco"] for r in sel); non=sum(1 for r in sel if r["label"]=="NONE")
    rs=[r["R"] for r in sel]; sm=sum(rs); eq=pk=dd=0
    for x in rs: eq+=x; pk=max(pk,eq); dd=min(dd,eq-pk)
    py={y:round(st.mean([r["R"] for r in sel if r["yr"]==y]),2) if [r for r in sel if r["yr"]==y] else None for y in (2024,2025,2026)}
    print(f"{k:<7}{n:>9}{mf:>9}{round(mf/MF,2):>7}{mfr:>8}{non:>6}{round(100*mf/n,1):>6}{round(sm/n,3):>7}{round(sm,1):>7}{round(dd,1):>7}  {py[2024]}/{py[2025]}/{py[2026]}")
print(f"\n(recall = MON+FORTE pegos / {MF}. 'pegamos' = o próprio candidato MON+FORTE dispara a regra.)")
