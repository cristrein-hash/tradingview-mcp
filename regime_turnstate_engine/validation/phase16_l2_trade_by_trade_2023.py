#!/usr/bin/env python3
"""Relatório TRADE-A-TRADE (DESCRITIVO) da base canónica L2/BPT (universo 276 + SL_CONTEXT + let-run) de 2023+, por REGIME phase10.
Merge: regua_structural (entry/sl/risk/letrun/mfe) + sl_context_policy (sl_atr/exit_type) + regime causal phase10.
R = letrun pós-custo 0.35. MFE = teto forward (NÃO bankable). Flags: MONSTRO(mfe>=10R) / BIG-LOSER(R<=-1). Não é promoção."""
import csv,io,contextlib,sys,datetime as dt
from pathlib import Path
COST=0.35;VAL=Path("/Users/cristrein/tradingview-mcp/regime_turnstate_engine/validation");sys.path.insert(0,str(VAL))
with contextlib.redirect_stdout(io.StringIO()): import phase10_hybrid_regime as P
reg=P.run(0.03,1.15,0.88);T=P.T
D=Path("/Users/cristrein/tradingview-mcp/my-strategy/research/revalidation/XAU_4H_L2_BPT_BOS_CHOCH/v1/results")
slx={int(r["i"]):r for r in csv.DictReader(open(D/"l2_bpt_sl_context_policy_results.csv"))}
rows=[]
for r in csv.DictReader(open(D/"l2_bpt_regua_structural.csv")):
    bi=int(r["bar_idx"]);t=T[bi];y=dt.datetime.utcfromtimestamp(t).year
    if y<2023: continue
    R=round(float(r["letrun_struct"])-COST,2);mfe=float(r["mfe_struct"])
    sx=slx.get(bi,{});rows.append({"bi":bi,"date":dt.datetime.utcfromtimestamp(t).strftime("%Y-%m-%d"),
        "regime":reg[bi],"entry":float(r["entry"]),"sl_atr":float(sx.get("sl_atr",0) or 0),
        "R":R,"mfe":mfe,"exit":sx.get("exit_type",""),"win":R>0,"yr":y})
def block(rg):
    g=sorted([x for x in rows if x["regime"]==rg],key=lambda x:x["bi"])
    s=sum(x["R"] for x in g);w=sum(1 for x in g if x["win"])
    print(f"\n{'='*92}\n### REGIME {rg} — N={len(g)} | WR={100*w/len(g):.0f}% | sumR={s:+.1f} | avgR={s/len(g):+.2f} ###\n{'='*92}")
    print(f"{'#':>3} {'data':10} {'entry':>8} {'SLatr':>5} {'R':>6} {'MFE':>6} {'cap%':>5} flag")
    for i,x in enumerate(g,1):
        cap=int(100*x['R']/x['mfe']) if x['mfe']>0 and x['R']>0 else 0
        fl="MONSTRO" if x['mfe']>=10 else ("BIG-LOSS" if x['R']<=-1 else "")
        print(f"{i:>3} {x['date']:10} {x['entry']:>8.1f} {x['sl_atr']:>5.1f} {x['R']:>+6.2f} {x['mfe']:>6.1f} {cap:>4}% {fl}")
print("RELATORIO TRADE-A-TRADE — L2/BPT base canonica 2023+ (let-run pos-custo, regime phase10)")
print(f"total trades: {len(rows)} | win {sum(1 for x in rows if x['win'])} | sumR {sum(x['R'] for x in rows):+.1f}")
for rg in ["BULL","RANGE","BEAR"]: block(rg)
from collections import defaultdict
print(f"\n{'='*60}\nRESUMO ANO x REGIME (sumR pos-custo)\n{'='*60}")
agg=defaultdict(float);cnt=defaultdict(int)
for x in rows: agg[(x['yr'],x['regime'])]+=x['R'];cnt[(x['yr'],x['regime'])]+=1
for y in sorted(set(x['yr'] for x in rows)):
    parts=[f"{rg} {agg[(y,rg)]:+.1f}(n{cnt[(y,rg)]})" for rg in ['BULL','RANGE','BEAR'] if cnt[(y,rg)]]
    print(f"  {y}: "+" | ".join(parts))
