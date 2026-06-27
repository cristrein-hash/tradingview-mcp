#!/usr/bin/env python3
"""ENGINE DE ENTRADA (Cris 2026-06-27): refinar entry mapeando demanda 15M pre-existente, CAUSAL, sem lookahead.
Ideia: no close do sinal 5ATR (barra cj), em vez de comprar no close (entry alto/atrasado), colocar um
LIMIT no TOPO da DEMAND pre-existente mais proxima abaixo (born_t<=tc). Regras causais:
  - se o low tocar o limit ANTES do SL e ANTES de exit -> preenche no limit (entry menor, risco menor) e roda let-run.
  - se bater SL antes -> -1R (mesmo SL estrutural flush-0.1ATR).
  - se NUNCA tocar o limit (preco fugiu pra cima) -> preenche no 5ATR (entry/R original) => NAO perde trade.
SL mantido = flush-0.1ATR (estrutural, mesmo nivel). Compara sumR/WR/DD vs base let-run atual.
Preserva os trades SEM demanda abaixo (ficam 5ATR). RAW-causal. So mede."""
import json, csv, statistics as st
from pathlib import Path
HERE=Path(__file__).parent; HMAX=480; RCAP=20.0
PRIM={p.name.split(".")[0].replace("XAUUSD_15m_replay_",""): json.loads(p.read_text())
      for p in sorted((HERE/"primitives").glob("*.primitives.json"))}
PRIM={k[:10]:v for k,v in PRIM.items()}
FD={r["t"]:r for r in (json.loads(l) for l in (HERE/"filter_dataset.jsonl").read_text().splitlines())}
T170=list(csv.DictReader(open(HERE/"strategy_5atr_regime170_trades.csv")))

def cf_low(s,i):
    L=[b["l"] for b in s]; lo=max(2,i-120); bst=None
    for p in range(lo,i-1):
        if L[p]==min(L[p-2:p+3]): bst=L[p]
    return bst
def letrun(s,start,entry,sl,atr):
    risk=entry-sl
    if risk<=0: return None
    trail=sl; r1=False; ex=None; end=min(start+HMAX,len(s)-1)
    for k in range(start+1,end+1):
        if s[k]["l"]<=trail: ex=trail; break
        if (s[k]["h"]-entry)/risk>=1: r1=True
        if r1:
            sw=cf_low(s,k)
            if sw: trail=max(trail,sw-0.1*atr)
    if ex is None: ex=s[end]["c"]
    return max(-1.0,min(RCAP,(ex-entry)/risk))
def demand_top_below(zones, entry, tc):
    best=None
    for z in zones:
        if z.get("text")!="DEMAND" or z.get("born_t",1e18)>tc: continue
        if z["high"]<=entry-1e-9:   # estritamente abaixo (limit faz sentido)
            d=entry-z["high"]
            if best is None or d<best[0]: best=(d,z["high"])
    return best[1] if best else None

rows=[]
for tr in T170:
    num=int(tr["num"]); t=int(tr["entry_t"]); fd=FD.get(t)
    if not fd: continue
    pr=PRIM[fd["block"]]; s=pr["series"]; z=pr["zones"]
    i=fd["i"]; cj=fd["cj"]; atr=s[i]["atr"]; tc=s[cj]["t"]
    entry0=float(tr["entry"]); sl=float(tr["sl"]); R0=float(tr["R"]); win0=R0>0
    limit=demand_top_below(z,entry0,tc)
    mode="5ATR"; entry_eff=entry0; R=R0; fillk=cj
    if limit is not None and limit>sl:    # limit precisa estar acima do SL p/ fazer sentido
        end=min(cj+HMAX,len(s)-1); filled=None
        for k in range(cj+1,end+1):
            if s[k]["l"]<=sl: break                 # SL antes do limit -> trade perde (-1R), nao preenche melhor
            if s[k]["l"]<=limit: filled=k; break     # tocou limit -> preenche aqui
        if filled is not None:
            entry_eff=limit; mode="LIMIT_demanda"
            R=letrun(s,filled,entry_eff,sl,atr)
            if R is None: R=R0; entry_eff=entry0; mode="5ATR"
        # se nao preencheu (preco fugiu) -> fica 5ATR (R0)
    rows.append({"num":num,"win0":int(win0),"mode":mode,"entry0":round(entry0,2),"entry_eff":round(entry_eff,2),
                 "sl":sl,"R0":round(R0,3),"R":round(R,3),"win":int(R>0),
                 "risk0":round(entry0-sl,2),"risk_eff":round(entry_eff-sl,2)})

def metr(rs,key):
    n=len(rs); sm=sum(r[key] for r in rs); w=sum(1 for r in rs if r[key]>0)
    eq=pk=dd=0
    for r in sorted(rs,key=lambda x:x["num"]):
        eq+=r[key]; pk=max(pk,eq); dd=min(dd,eq-pk)
    return n,round(100*w/n,1),round(sm,1),round(dd,1)
nb,wb,sb,db=metr(rows,"R0"); ne,we,se,de=metr(rows,"R")
lim=[r for r in rows if r["mode"]=="LIMIT_demanda"]
print(f"=== ENGINE ENTRADA — limit em DEMANDA pre-existente (causal) vs 5ATR atual ===")
print(f"  BASE 5ATR (atual):     N={nb} WR={wb}% sumR={sb:+} DD={db}")
print(f"  ENGINE limit-demanda:  N={ne} WR={we}% sumR={se:+} DD={de}")
print(f"  trades que preencheram no LIMIT (entry melhorado): {len(lim)}/170 | resto ficou 5ATR")
if lim:
    dR=[r['R']-r['R0'] for r in lim]
    flipped=sum(1 for r in lim if r['R0']<=0 and r['R']>0)
    worse=sum(1 for r in lim if r['R']<r['R0']-1e-6)
    print(f"    desses: dR medio {st.mean(dR):+.2f} | viraram loser->winner: {flipped} | pioraram: {worse}")
    print(f"    risco medio: 5ATR ${st.mean([r['risk0'] for r in lim]):.1f} -> limit ${st.mean([r['risk_eff'] for r in lim]):.1f}")
with open(HERE/"lab_entry_engine.csv","w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
print("-> lab_entry_engine.csv")
