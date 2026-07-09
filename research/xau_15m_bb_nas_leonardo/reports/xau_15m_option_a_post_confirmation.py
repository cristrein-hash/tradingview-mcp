#!/usr/bin/env python3
"""OPÇÃO A — entries PÓS-CONFIRMAÇÃO (conforme prereg congelado). Candidato = pivô L CONFIRMADO
(zz r=6 emite no bar conf); janela reclaim = 24 barras A PARTIR de conf_i (inclusive); trigger idêntico
(close>EMA21 & close>prev); kind MARKUP no momento da confirmação (prevL conhecido causalmente);
SL V1 = pivot_low - 0.1*ATR[pivot]; 3R first-touch SL-first h1440; filtro capitulation inalterado
(regime v5 hour-causal + 1D_px_vs_ema /ATR_15M[j]). 100% conhecível live (nada antes de conf).
Output: xau_15m_option_a_result.json + xau_15m_option_a_candidates.csv."""
import json, sys, csv, bisect
import datetime as dt
from pathlib import Path
HERE=Path(__file__).resolve().parent; sys.path.insert(0,str(HERE)); RD=HERE.parent
import xau_15m_n83_sl_exit_lib as L
HI,LO,CL,ATR,EMA,TS,N=L.HI,L.LO,L.CL,L.ATR,L.EMA,L.TS,L.N
W0=dt.datetime(2025,8,1).timestamp(); W1=dt.datetime(2026,7,4).timestamp()
SRC=RD/"engine_substrate4_v5_hourcausal.py"
ns={"__file__":str(SRC)}; exec("\n".join(open(SRC).read().splitlines()[:73]),ns)
regime_hourcausal=ns["regime_hourcausal"]
D1=[b for b in json.load(open(RD/"htf_primitives/htf_1D.primitives.json"))["series"] if b.get("ema21") is not None]
D1T=[b["t"] for b in D1]
def px1d(t,px,a15):
    k=bisect.bisect_right(D1T,t-86400)-1
    return (px-D1[k]["ema21"])/(a15 or 5) if k>=0 else None

# pivôs com conf (zz r=6) + prevL na emissão (causal: prevL = L anterior já confirmado)
piv=L.zz(6); rows=[]
prevL=None; lastH=None
for tp,i,pr,ci in piv:
    if tp=="H": lastH=pr; continue
    # pivô L confirmado em ci
    kind_markup=(prevL is None or pr>prevL)
    if lastH is not None and kind_markup and W0<=TS[i]<=W1:
        # janela de reclaim: ci .. ci+24 (inclusive; trigger no close)
        j=None
        for k in range(ci,min(N,ci+25)):
            if EMA[k] is not None and CL[k]>EMA[k] and CL[k]>CL[k-1]: j=k; break
        if j is not None:
            a=ATR[i] or 5; ent=CL[j]; sl=pr-0.1*a; risk=ent-sl
            if risk>0.05*a:
                tgt=ent+3*risk
                sim=L.simulate(j,ent,sl,tgt)
                rows.append({"i":i,"conf_i":ci,"j":j,"t":TS[j],"d":L.dstr(TS[j]),
                    "ent":round(ent,2),"sl":round(sl,2),"risk":round(risk,2),
                    "risk_atr":round(risk/(ATR[j] or 5),2),
                    "oc":sim["oc"],"out":1 if sim["oc"]=="TGT" else 0,"bars":sim["bars"],
                    "regime":regime_hourcausal(TS[j]),
                    "px_vs_ema_1d":(lambda v: round(v,3) if v is not None else None)(px1d(TS[j],ent,ATR[j])),
                    "entry_lag_from_low":j-i,"conf_lag":ci-i})
    prevL=pr
def R_of(r): return 3.0 if r["out"]==1 else -1.0
def panel(rs): return L.panel([R_of(r) for r in rs])
skip=[r for r in rows if r["regime"]=="BEAR" and r["px_vs_ema_1d"] is not None and r["px_vs_ema_1d"]>=0]
keep=[r for r in rows if r not in skip]
def seg(rs,key):
    o={}
    for r in rs: o.setdefault(key(r),[]).append(R_of(r))
    return {k:L.panel(v) for k,v in sorted(o.items())}
res={"design":"prereg Opção A congelado (entries só de conf_i; janela 24 de conf_i)",
     "n_universe":len(rows),
     "risk_atr_median":sorted(r["risk_atr"] for r in rows)[len(rows)//2] if rows else None,
     "universe_panel":panel(rows),
     "filter":{"n_skip":len(skip),"losers_cut":sum(1 for r in skip if r["out"]==0),
               "winners_cut":sum(1 for r in skip if r["out"]==1)},
     "kept_panel":panel(keep),
     "kept_per_year":seg(keep,lambda r:r["d"][:4]),
     "kept_per_regime":seg(keep,lambda r:r["regime"]),
     "timeouts":sum(1 for r in rows if r["oc"]=="TIME"),
     "comparison_option_b":{"kept":"n144 WR31.9 +40R(marginal) DD-15 stk15"}}
with open(HERE/"xau_15m_option_a_candidates.csv","w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0].keys())); w.writeheader()
    for r in rows: w.writerow(r)
(HERE/"xau_15m_option_a_result.json").write_text(json.dumps(res,indent=2,ensure_ascii=False))
print(json.dumps(res,indent=2,ensure_ascii=False))
