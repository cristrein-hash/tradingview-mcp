#!/usr/bin/env python3
"""FASE 3 — UNIVERSO LIVE-FIREABLE (Opção B do base repair). Walk online do zz(6) (mesma ordem de
update; pivôs só existem a partir da confirmação); candidato = running low da down-leg confirmada;
entry = reclaim EMA21 (<=24 barras do candidato); kind MARKUP live = higher-low vs último L CONFIRMADO;
1 entry por candidato; janela ago/2025→2026-07-04; SL V1 (low−0.1ATR[cand]); 3R first-touch SL-first
horizon 1440. Enriquecido com: macro_regime v5 hour-causal (código VERBATIM), 1D_px_vs_ema (último
bar 1D FECHADO, htf_1D nativo) + sanity vs cut CSV original. PROIBIDO: conf_i futuro / lower-low
futuro / outcome como seletor. Outputs: ..._result.json + xau_15m_live_fireable_candidates.csv."""
import json, sys, csv
import datetime as dt
from pathlib import Path
HERE=Path(__file__).resolve().parent; sys.path.insert(0,str(HERE)); RD=HERE.parent
import xau_15m_n83_sl_exit_lib as L
HI,LO,CL,ATR,EMA,TS,N=L.HI,L.LO,L.CL,L.ATR,L.EMA,L.TS,L.N
W0=dt.datetime(2025,8,1).timestamp(); W1=dt.datetime(2026,7,4).timestamp()
R6=6; WIN=24

# ---- regime v5 hour-causal VERBATIM (mesma técnica do n96_causal_regime_recross.py) ----
SRC=RD/"engine_substrate4_v5_hourcausal.py"
core="\n".join(open(SRC).read().splitlines()[:73])
ns={"__file__":str(SRC)}
exec(core,ns)
regime_hourcausal=ns["regime_hourcausal"]

# ---- 1D feature (último bar 1D FECHADO antes do entry) ----
D1=json.load(open(RD/"htf_primitives/htf_1D.primitives.json"))["series"]
D1=[b for b in D1 if b.get("ema21") is not None and b.get("atr")]
D1T=[b["t"] for b in D1]
import bisect
def px_vs_ema_1d(entry_t, entry_px, atr15):
    """(px - EMA21_1D_último_bar_FECHADO)/ATR_15M — normalização IDÊNTICA ao original
    (n96_exhaustive_mtf_discrimination.py linha 38: a=ATR[e['j']] do 15M; bars_upto: t_bar+86400<=t)."""
    k=bisect.bisect_right(D1T, entry_t-86400)-1
    if k<0: return None
    return (entry_px-D1[k]["ema21"])/(atr15 or 5)

# ---- walk online (candidatos live) ----
d=0; ehi=elo=0; prevL=None; lastH=None
entered=set(); rows=[]
open_window=None
for k in range(1,N):
    a=ATR[k]
    if HI[k]>HI[ehi]: ehi=k
    if LO[k]<LO[elo]: elo=k
    if d<=0 and HI[k]-LO[elo]>=R6*a and elo<k:
        open_window=(elo,min(N-1,elo+WIN))
        prevL=LO[elo]; d=1; ehi=max(range(elo,k+1),key=lambda q:HI[q])
    elif d>=0 and HI[ehi]-LO[k]>=R6*a and ehi<k:
        lastH=HI[ehi]; d=-1; elo=min(range(ehi,k+1),key=lambda q:LO[q]); open_window=None
    cand=None
    if d==-1 and lastH is not None and elo<k and (k-elo)<=WIN: cand=elo
    elif open_window and open_window[0]<k<=open_window[1]: cand=open_window[0]
    if cand is None or cand in entered: continue
    lo=LO[cand]
    kind_markup=(prevL is None or lo>prevL)
    if not (W0<=TS[cand]<=W1):
        continue
    if EMA[k] is not None and CL[k]>EMA[k] and CL[k]>CL[k-1]:
        entered.add(cand)                       # consome o candidato (1 entry por candidato)
        if not kind_markup: continue            # só MARKUP live
        aa=ATR[cand] or 5
        ent=CL[k]; sl=lo-0.1*aa; risk=ent-sl
        if risk<=0.05*aa: continue
        tgt=ent+3*risk
        sim=L.simulate(k,ent,sl,tgt)
        rows.append({"i":cand,"j":k,"t":TS[k],"d":L.dstr(TS[k]),"ent":round(ent,2),"sl":round(sl,2),
            "tgt":round(tgt,2),"risk":round(risk,2),"oc":sim["oc"],"out":1 if sim["oc"]=="TGT" else 0,
            "bars":sim["bars"],
            "regime":regime_hourcausal(TS[k]),
            "px_vs_ema_1d":(lambda v: round(v,3) if v is not None else None)(px_vs_ema_1d(TS[k],ent,ATR[k])),
            "leg_state":"MARKUP_CANDIDATE_LIVE"})

# ---- match vs N96 contaminado (referência apenas) ----
base=L.reproduce_base(); bk={(tr["i"],tr["j"]):tr["trade_id"] for tr in base}
for r in rows:
    r["matched_n96"]=bk.get((r["i"],r["j"]))
matched=[r for r in rows if r["matched_n96"]]; extra=[r for r in rows if not r["matched_n96"]]
# sanity 1D: comparar px_vs_ema_1d com o cut CSV original nos matched
orig={}
with open(RD/"results/n96_intra_bear_cut_trades.csv") as f:
    for rr in csv.DictReader(f):
        try: orig[int(rr["trade"].lstrip("#"))]=float(rr["1D_px_vs_ema"])
        except Exception: pass
san=[]
for r in matched:
    n=r["matched_n96"]
    if n in orig and r["px_vs_ema_1d"] is not None:
        san.append({"n":n,"mine":r["px_vs_ema_1d"],"orig":orig[n],"diff":round(abs(r["px_vs_ema_1d"]-orig[n]),3)})
# dupes
tset={}; dupes=0
for r in rows:
    if r["t"] in tset: dupes+=1
    tset[r["t"]]=1
res={"n_live_fireable":len(rows),
     "expected_approx":173,
     "matched_n96":len(matched),"extra":len(extra),
     "outcomes":{"TGT":sum(1 for r in rows if r["oc"]=="TGT"),"SL":sum(1 for r in rows if r["oc"]=="SL"),
                 "TIME":sum(1 for r in rows if r["oc"]=="TIME")},
     "WR_resolved_pct":round(100*sum(r["out"] for r in rows if r["oc"]!="TIME")/max(1,sum(1 for r in rows if r["oc"]!="TIME")),1),
     "sumR_3R_model":round(sum(3.0 if r["out"]==1 else -1.0 for r in rows if r["oc"]!="TIME"),1),
     "regime_coverage":{reg:sum(1 for r in rows if r["regime"]==reg) for reg in ("BULL","BEAR","RANGE")},
     "px1d_available":sum(1 for r in rows if r["px_vs_ema_1d"] is not None),
     "duplicate_bars":dupes,
     "sanity_1d_vs_cut_csv":{"n":len(san),"max_abs_diff":max((s["diff"] for s in san),default=None),
                              "sample":san[:5]},
     "family_label":"não disponível ex-ante p/ candidatos novos (rótulo pós-hoc de losers) — declarado"}
with open(HERE/"xau_15m_live_fireable_candidates.csv","w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0].keys())); w.writeheader()
    for r in rows: w.writerow(r)
(HERE/"xau_15m_live_fireable_universe_result.json").write_text(json.dumps(res,indent=2,ensure_ascii=False))
print(json.dumps(res,indent=2,ensure_ascii=False))
