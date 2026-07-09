#!/usr/bin/env python3
"""FASE 9 — ROBUSTEZ adversarial do SL/exit (N83). Candidatos: C=3R atual (baseline) vs D=4R vs
F=timestop288 (os 2 'melhores' exploratórios). Testes: per-quarter · jackknife-1 (drop melhor trade) ·
slippage/spread stress (entry +0.05ATR pior, SL fill -0.05/-0.10ATR pior) · delay entry 1 bar ·
boundary do filtro (1D_px_vs_ema threshold 0 -> -0.5/+0.5) · null de exposição p/ F (fecho em bar
aleatório <=288 vs timestop fixo). Output: xau_15m_n83_sl_exit_robustness_result.json."""
import json, sys, random, csv
from pathlib import Path
HERE=Path(__file__).resolve().parent; sys.path.insert(0,str(HERE))
import xau_15m_n83_sl_exit_lib as L
random.seed(20260709)
base=L.reproduce_base(); regmap,cut,fam=L.load_context()
n83=[t for t in base if t["trade_id"] not in cut]
def sim_R(tr,mult=None,cap=None,ent_adj=0.0,sl_adj=0.0):
    a=L.ATR[tr["j"]] or 5
    ent=tr["ent"]+ent_adj*a; sl=tr["sl"]+0  # sl nível fica; sl_adj aplica no FILL
    risk=ent-sl
    if risk<=0: return None
    tgt=(ent+mult*risk) if mult else None
    sim=L.simulate(tr["j"],ent,sl,tgt,time_cap=cap)
    if sim["oc"]=="SL":  return (sl - sl_adj*a - ent)/risk
    if sim["oc"]=="TGT": return (tgt-ent)/risk
    return (L.CL[sim["end"]]-ent)/risk
CANDS={"C_3R":dict(mult=3),"D_4R":dict(mult=4),"F_timestop288":dict(cap=288)}
res={"candidates":{}}
for name,kw in CANDS.items():
    Rs=[(tr,sim_R(tr,**kw)) for tr in n83]; Rs=[(t,r) for t,r in Rs if r is not None]
    vals=[r for _,r in Rs]; p=L.panel(vals)
    # per-quarter
    q={}
    for tr,r in Rs:
        d=L.dstr(tr["t"]); qk=d[:4]+"Q"+str((int(d[5:7])-1)//3+1); q.setdefault(qk,[]).append(r)
    p["per_quarter"]={k:{"n":len(v),"sumR":round(sum(v),1)} for k,v in sorted(q.items())}
    p["neg_quarters"]=sum(1 for v in q.values() if sum(v)<0)
    # jackknife-1 (drop melhor)
    p["jack_drop_best"]=round(p["sumR"]-max(vals),1)
    # slippage stress
    for tag,ea,sa in (("slip_light",0.05,0.05),("slip_heavy",0.10,0.10)):
        sv=[sim_R(tr,**kw,ent_adj=ea,sl_adj=sa) for tr in n83]; sv=[x for x in sv if x is not None]
        p[tag]={"sumR":round(sum(sv),1),"WR":round(100*sum(1 for x in sv if x>0)/len(sv),1)}
    # delay 1 bar: entry no close de j+1 (se j+1 existe), mesmo SL nível
    dv=[]
    for tr in n83:
        j2=tr["j"]+1
        if j2>=L.N: continue
        ent2=L.CL[j2]; risk2=ent2-tr["sl"]
        if risk2<=0: continue
        tgt2=(ent2+kw["mult"]*risk2) if kw.get("mult") else None
        s2=L.simulate(j2,ent2,tr["sl"],tgt2,time_cap=kw.get("cap"))
        dv.append(s2["R"])
    pd_=L.panel([x for x in dv if x is not None])
    p["delay_1bar"]={"n":pd_["n"],"sumR":pd_["sumR"],"WR":pd_["WR"]}
    res["candidates"][name]=p
# null de exposição p/ F (o timestop é skill ou beta?): fecho em bar aleatório U[1,288] com SL ativo
TR=1000; nulls=[]
for _ in range(TR):
    tot=0
    for tr in n83:
        kx=random.randint(1,288)
        s=L.simulate(tr["j"],tr["ent"],tr["sl"],None,time_cap=kx)
        tot+=s["R"] if s["R"] is not None else 0
    nulls.append(tot)
obsF=res["candidates"]["F_timestop288"]["sumR"]
nulls.sort()
res["null_exposure_F"]={"obs":obsF,"null_mean":round(sum(nulls)/TR,1),
    "null_p95":round(nulls[int(0.95*TR)],1),"p_null_ge_obs":round(sum(1 for x in nulls if x>=obsF)/TR,3)}
# boundary do filtro: threshold px>=thr, thr em {-0.5,-0.25,0,+0.25,+0.5} (0=oficial)
feats={}
with open(L.RD/"results/n96_exhaustive_mtf_features.csv") as f:
    for row in csv.DictReader(f):
        try: feats[int(row.get("trade") or row.get("id") or row.get("n"))]=float(row["1D_px_vs_ema"])
        except Exception: pass
bnd={}
for thr in (-0.5,-0.25,0.0,0.25,0.5):
    keep=[t for t in base if not (regmap.get(t["trade_id"])=="BEAR" and feats.get(t["trade_id"],-99)>=thr)]
    Rs=[3.0 if t["out"]==1 else -1.0 for t in keep]
    bnd[str(thr)]={"n":len(keep),"sumR":round(sum(Rs),1),"W_cut":sum(1 for t in base if t["out"]==1 and t not in keep)}
res["filter_boundary_3R"]=bnd
(HERE/"xau_15m_n83_sl_exit_robustness_result.json").write_text(json.dumps(res,indent=2,ensure_ascii=False))
for name,p in res["candidates"].items():
    print(f"{name:<15} sumR={p['sumR']:<7} WR={p['WR']:<5} DD={p['maxDD_R']} stk={p['streak']} negQ={p['neg_quarters']} jack={p['jack_drop_best']} slipL={p['slip_light']['sumR']} slipH={p['slip_heavy']['sumR']} delay={p['delay_1bar']['sumR']}")
print("nullF:",res["null_exposure_F"])
print("boundary:",{k:v["sumR"] for k,v in res["filter_boundary_3R"].items()})
