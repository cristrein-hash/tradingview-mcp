#!/usr/bin/env python3
"""FASE 7 — robustez do universo reparado + filtro. per-quarter · jackknife top winners/losers ·
null de cortes aleatórios matched-by-regime (o corte 22L/0W do filtro é sorte?) · boundary px_vs_ema
(sensitivity only) · slippage/delay · sessão. Output: xau_15m_live_fireable_n83_robustness_result.json."""
import json, sys, csv, random
import datetime as dt
from pathlib import Path
HERE=Path(__file__).resolve().parent; sys.path.insert(0,str(HERE))
import xau_15m_n83_sl_exit_lib as L
random.seed(20260709)
rows=list(csv.DictReader(open(HERE/"xau_15m_live_fireable_candidates.csv")))
for r in rows:
    for k in ("i","j","t","out"): r[k]=int(float(r[k]))
    for k in ("ent","sl","risk"): r[k]=float(r[k])
    r["px_vs_ema_1d"]=float(r["px_vs_ema_1d"]) if r["px_vs_ema_1d"] else None
def R_of(r): return 3.0 if r["out"]==1 else -1.0
skip=[r for r in rows if r["regime"]=="BEAR" and r["px_vs_ema_1d"] is not None and r["px_vs_ema_1d"]>=0]
keep=[r for r in rows if r not in skip]
res={}
# per-quarter (kept)
q={}
for r in keep:
    qk=r["d"][:4]+"Q"+str((int(r["d"][5:7])-1)//3+1); q.setdefault(qk,[]).append(R_of(r))
res["kept_per_quarter"]={k:{"n":len(v),"sumR":round(sum(v),1)} for k,v in sorted(q.items())}
res["neg_quarters"]=sum(1 for v in q.values() if sum(v)<0)
# jackknife
Rs=[R_of(r) for r in keep]; s=sum(Rs)
res["jack_drop_top_winner"]=round(s-3.0,1)
res["jack_drop_top3_winners"]=round(s-9.0,1)
# null: cortes aleatórios de 22 trades DENTRO do BEAR (matched by regime) — o 22L/0W é sorte?
bear=[r for r in rows if r["regime"]=="BEAR"]; TRI=2000; wins_cut=[]
for _ in range(TRI):
    cut=random.sample(bear,22)
    wins_cut.append(sum(1 for r in cut if r["out"]==1))
p0=sum(1 for w in wins_cut if w==0)/TRI
res["null_random_bear_cuts"]={"trials":TRI,"P_cut22_zero_winners":round(p0,4),
    "mean_winners_cut":round(sum(wins_cut)/TRI,2),
    "obs":"filtro cortou 22 com 0 winners"}
# boundary sensitivity (não muda filtro)
bnd={}
for thr in (-0.5,-0.25,0.0,0.25,0.5):
    sk=[r for r in rows if r["regime"]=="BEAR" and r["px_vs_ema_1d"] is not None and r["px_vs_ema_1d"]>=thr]
    kp=[r for r in rows if r not in sk]
    bnd[str(thr)]={"n_kept":len(kp),"sumR":round(sum(R_of(r) for r in kp),1),
                   "winners_cut":sum(1 for r in sk if r["out"]==1)}
res["boundary_px_vs_ema"]=bnd
res["boundary_population_near_0"]=sum(1 for r in bear if r["px_vs_ema_1d"] is not None and -0.5<r["px_vs_ema_1d"]<0.5)
# slippage (entry+SL fill 0.05/0.10 ATR pior) — recomputar R executável
def R_slip(r,sa):
    a=L.ATR[r["j"]] or 5
    ent=r["ent"]+sa*a; risk=ent-r["sl"]
    if risk<=0: return None
    tgt=ent+3*risk
    sim=L.simulate(r["j"],ent,r["sl"],tgt)
    if sim["oc"]=="SL": return (r["sl"]-sa*a-ent)/risk
    if sim["oc"]=="TGT": return 3.0
    return sim["R"]
for tag,sa in (("slip_0.05",0.05),("slip_0.10",0.10)):
    v=[R_slip(r,sa) for r in keep]; v=[x for x in v if x is not None]
    res[tag]={"sumR":round(sum(v),1),"WR":round(100*sum(1 for x in v if x>0)/len(v),1)}
# delay 1 bar
dv=[]
for r in keep:
    j2=r["j"]+1
    if j2>=L.N: continue
    ent2=L.CL[j2]; risk2=ent2-r["sl"]
    if risk2<=0: continue
    sim=L.simulate(j2,ent2,r["sl"],ent2+3*risk2)
    dv.append(3.0 if sim["oc"]=="TGT" else (-1.0 if sim["oc"]=="SL" else sim["R"]))
res["delay_1bar"]={"n":len(dv),"sumR":round(sum(dv),1),"WR":round(100*sum(1 for x in dv if x>0)/len(dv),1)}
# sessão (UTC hora do entry)
ses={}
for r in keep:
    h=dt.datetime.utcfromtimestamp(r["t"]).hour
    b="asia(0-7)" if h<8 else ("eu(8-15)" if h<16 else "us(16-23)")
    ses.setdefault(b,[]).append(R_of(r))
res["session_split"]={k:{"n":len(v),"sumR":round(sum(v),1)} for k,v in sorted(ses.items())}
(HERE/"xau_15m_live_fireable_n83_robustness_result.json").write_text(json.dumps(res,indent=2,ensure_ascii=False))
print(json.dumps(res,indent=2,ensure_ascii=False))
