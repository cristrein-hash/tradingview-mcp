#!/usr/bin/env python3
"""ROBUSTEZ do RLAD (trail 1R atrás do pico-R inteiro) — o único trailing que bateu o 3R fixo (143 vs 125).
Lição L1 (knife-edge): testar VIZINHOS da regra (step/lag variantes pré-declaradas), per-quarter,
jackknife-1, slippage no fill do stop, delay-1-bar. Se só a célula exata funciona = frágil.
Variantes: lag1_step1 (original) · lag1_step0.5 · lag1.5_step0.5 · lag2_step1 · ativação só após 2R.
Output: xau_15m_n83_rlad_robustness_result.json."""
import json, sys
from pathlib import Path
HERE=Path(__file__).resolve().parent; sys.path.insert(0,str(HERE))
import xau_15m_n83_sl_exit_lib as L
base=L.reproduce_base(); regmap,cut,fam=L.load_context()
n83=[t for t in base if t["trade_id"] not in cut]
HOR=L.HORIZON
import math
def sim_rlad(tr,lag=1.0,step=1.0,act=0.0,slip_atr=0.0):
    j=tr["j"]; ent=tr["ent"]; sl0=tr["sl"]; risk=ent-sl0
    eff=sl0; maxR=0.0; last=min(L.N-1,j+HOR)
    for m in range(j+1,last+1):
        if maxR>=act and maxR>lag:
            lock=math.floor((maxR-lag)/step)*step
            cand=ent+lock*risk
        else: cand=sl0
        eff=max(eff,cand,sl0)
        if L.LO[m]<=eff:
            a=L.ATR[m-1] or 5
            return (eff-slip_atr*a-ent)/risk, m-j
        maxR=max(maxR,(L.HI[m]-ent)/risk)
    return (L.CL[last]-ent)/risk, last-j
VAR={"lag1_step1_(orig)":dict(lag=1,step=1),
     "lag1_step0.5":dict(lag=1,step=0.5),
     "lag1.5_step0.5":dict(lag=1.5,step=0.5),
     "lag2_step1":dict(lag=2,step=1),
     "act2R_lag1_step1":dict(lag=1,step=1,act=2.0)}
res={"variants":{}}
for name,kw in VAR.items():
    out=[sim_rlad(tr,**kw) for tr in n83]
    Rs=[r for r,_ in out]; p=L.panel(Rs)
    yr={}
    for tr,(r,_) in zip(n83,out): yr.setdefault(L.dstr(tr["t"])[:4],[]).append(r)
    p["per_year"]={y:round(sum(v),1) for y,v in sorted(yr.items())}
    q={}
    for tr,(r,_) in zip(n83,out):
        d=L.dstr(tr["t"]); q.setdefault(d[:4]+"Q"+str((int(d[5:7])-1)//3+1),[]).append(r)
    p["per_quarter"]={k:round(sum(v),1) for k,v in sorted(q.items())}
    p["neg_quarters"]=sum(1 for v in q.values() if sum(v)<0)
    p["jack_drop_best"]=round(p["sumR"]-max(Rs),1)
    res["variants"][name]=p
# slippage + delay no ORIGINAL VERDADEIRO (= act2R_lag1_step1; o RLAD do trailing script ativa a 2R:
# int(maxR)-1>=1 exige maxR>=2). NOTA: a 1ª versão deste stress usou por engano a variante BE-a-1R.
OK=dict(lag=1,step=1,act=2.0)
o_slip=[sim_rlad(tr,**OK,slip_atr=0.05)[0] for tr in n83]; o_slip2=[sim_rlad(tr,**OK,slip_atr=0.10)[0] for tr in n83]
res["orig_slippage"]={"slip0.05_sumR":round(sum(o_slip),1),"slip0.10_sumR":round(sum(o_slip2),1)}
dv=[]
for tr in n83:
    j2=tr["j"]+1
    if j2>=L.N: continue
    ent2=L.CL[j2]; risk2=ent2-tr["sl"]
    if risk2<=0: continue
    tr2=dict(tr); tr2["j"]=j2; tr2["ent"]=ent2
    dv.append(sim_rlad(tr2,**OK)[0])
res["orig_delay_1bar"]={"n":len(dv),"sumR":round(sum(dv),1)}
res["orig_definition"]="lock=floor(maxR)-1 quando maxR>=2 (ativação implícita a +2R; nunca BE-a-1R)"
res["baseline_3R_sumR"]=125.0
(HERE/"xau_15m_n83_rlad_robustness_result.json").write_text(json.dumps(res,indent=2,ensure_ascii=False))
print(f"{'variant':<22} {'sumR':>7} {'WR':>5} {'DD':>6} {'stk':>4} {'negQ':>4} {'jack':>7}  per-year")
for name,p in res["variants"].items():
    yb=" ".join(f"{y}:{v}" for y,v in p["per_year"].items())
    print(f"{name:<22} {p['sumR']:>7} {p['WR']:>5} {p['maxDD_R']:>6} {p['streak']:>4} {p['neg_quarters']:>4} {p['jack_drop_best']:>7}  {yb}")
print("slippage:",res["orig_slippage"]," delay:",res["orig_delay_1bar"])
