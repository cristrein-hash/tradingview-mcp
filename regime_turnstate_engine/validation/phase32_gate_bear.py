#!/usr/bin/env python3
"""Cris (2026-07-01, luz verde): GATE-BEAR = não abrir long em BEAR-macro sustentado (regime causal phase10 no bar de entrada),
PRESERVANDO a capitulação-fundo. Objetivo = VIABILIDADE (cortar a metade-bear da streak de 11), NÃO R.
Guarda central = capitulação profunda causal: f7_cascade ≤ −3 (memória: bolsão winner-rico n9/WR78%, quality bottom comprável).
3 cenários no book L2/BPT 2023+: baseline · gate-bear-TOTAL (mata capitulação=tecto) · gate-bear-KEEP-CAPIT (preserva).
Painel de viabilidade: WR·sumR·DD·MAX-loss-streak·runs≥5·%meses-verdes·pior-mês. Só análise. let-run canónico, custo 0.35."""
import json,csv,io,contextlib,sys,datetime as dt
from pathlib import Path
from collections import defaultdict,Counter
COST=0.35
VAL=Path("/Users/cristrein/tradingview-mcp/regime_turnstate_engine/validation");sys.path.insert(0,str(VAL))
with contextlib.redirect_stdout(io.StringIO()): import phase10_hybrid_regime as P
reg=P.run(0.03,1.15,0.88);T=P.T
D=Path("/Users/cristrein/tradingview-mcp/my-strategy/research/revalidation/XAU_4H_L2_BPT_BOS_CHOCH/v1/results")
path={int(r["bar_idx"]):r for r in csv.DictReader(open(D/"l2_bpt_dspa_path_features_276.csv"))}
def num(v):
    try: return float(v)
    except: return None
rows=[]
for r in csv.DictReader(open(D/"l2_bpt_regua_structural.csv")):
    bi=int(r["bar_idx"]);t=T[bi];y=dt.datetime.utcfromtimestamp(t).year
    if y<2023: continue
    casc=num((path.get(bi) or {}).get("f7_cascade_now"))
    rows.append({"bi":bi,"date":dt.datetime.utcfromtimestamp(t).strftime("%Y-%m-%d"),
                 "ym":dt.datetime.utcfromtimestamp(t).strftime("%Y-%m"),"reg":reg[bi],
                 "R":round(float(r["letrun_struct"])-COST,2),"casc":casc})
rows.sort(key=lambda x:x["bi"])
print("distribuição de regime (bar de entrada):",dict(Counter(x["reg"] for x in rows)))
CAP=lambda x: x["casc"] is not None and x["casc"]<=-3   # capitulação profunda causal
def panel(keepfn,label):
    kept=[x for x in rows if keepfn(x)];rs=[x["R"] for x in kept];n=len(rs)
    if not n: print(f"  {label:34} N=0");return
    w=sum(1 for v in rs if v>0);s=sum(rs);cum=peak=dd=0;streak=mx=0;runs=[]
    for v in rs:
        cum+=v;peak=max(peak,cum);dd=min(dd,cum-peak)
        if v<=0: streak+=1;mx=max(mx,streak)
        else:
            if streak: runs.append(streak)
            streak=0
    if streak: runs.append(streak)
    r5=sum(1 for q in runs if q>=5)
    mth=defaultdict(float)
    for x in kept: mth[x["ym"]]+=x["R"]
    posm=sum(1 for v in mth.values() if v>0);tot=len(mth);worst=min(mth.values())
    print(f"  {label:34} N={n:3} WR={100*w/n:3.0f}% sumR={s:+6.1f} DD={dd:6.1f} | MAXstreak={mx:2} runs>=5:{r5} | meses {posm}/{tot} ({100*posm/tot:.0f}%+) pior{worst:+5.1f}")
print(f"\nBOOK L2/BPT 2023+ = {len(rows)} trades. GATE-BEAR (guarda=capitulação f7_cascade<=-3):")
panel(lambda x:True,"BASELINE (todas)")
panel(lambda x:x["reg"]!="BEAR","GATE-BEAR TOTAL (mata capit)")
panel(lambda x:x["reg"]!="BEAR" or CAP(x),"GATE-BEAR KEEP-CAPIT")
# o que o gate corta e o que preserva
bear=[x for x in rows if x["reg"]=="BEAR"]
bw=[x for x in bear if x["R"]>0]
print(f"\n### trades em BEAR: {len(bear)} (sumR {sum(x['R'] for x in bear):+.1f}, winners {len(bw)}) ###")
print("  -- BEAR winners (a capitulação que o gate-total mataria; casc = proxy) --")
for x in sorted(bw,key=lambda z:-z["R"]):
    print(f"    {x['date']} R{x['R']:+5.1f} casc={x['casc']}  {'<= CAPTURADO por casc<=-3' if CAP(x) else 'NAO capturado'}")
print("  -- trades BEAR que a guarda-capitulação preserva (casc<=-3) --")
for x in sorted([z for z in bear if CAP(z)],key=lambda z:z["bi"]):
    print(f"    {x['date']} R{x['R']:+5.1f} casc={x['casc']} {'WIN' if x['R']>0 else 'loss'}")
# streak: quanto da streak-11 do baseline é BEAR? (localizar)
print("\n### a pior streak do baseline — composição por regime ###")
best=[];cur=[]
for x in rows:
    if x["R"]<=0: cur.append(x)
    else:
        if len(cur)>len(best): best=cur[:]
        cur=[]
if len(cur)>len(best): best=cur[:]
print(f"  pior run = {len(best)} losses: {best[0]['date']} -> {best[-1]['date']} | regimes: {dict(Counter(z['reg'] for z in best))}")
