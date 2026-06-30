#!/usr/bin/env python3
"""RTSE — avaliação DIAGNÓSTICA: o detector phase10 (BULL/RANGE/BEAR) agrega benefício à L1 EMA21 LONG 4H?
NÃO é integração; é ver se o regime CAUSAL no bar de entrada separa winners/losers da L1 e se ajuda sobre o loser-cut.
n=34 (tiny) + thresholds calibrados => DIAGNÓSTICO, não validação. Painel completo (N/WR/sumR/avgR/DD/ret-DD/streak/ano)."""
import json,io,contextlib,sys,bisect,datetime as dt
from pathlib import Path
VAL=Path("/Users/cristrein/tradingview-mcp/regime_turnstate_engine/validation");sys.path.insert(0,str(VAL))
with contextlib.redirect_stdout(io.StringIO()):
    import phase10_hybrid_regime as P     # roda no import (suprimido); expõe run(), T
reg=P.run(0.03,1.15,0.88);T=P.T          # regime causal por bar 4H
L1=Path("/Users/cristrein/tradingview-mcp/my-strategy/research/revalidation/XAU_4H_LONG_CONTINUATION_L1_EMA21_A_F5")
trades=json.load(open(L1/"l1_approved34.json"))
cut8=set(json.load(open(L1/"l1_poc_cut8_ts.json")))
def epoch(s): return int(dt.datetime.strptime(s,"%Y-%m-%dT%H:%M").replace(tzinfo=dt.timezone.utc).timestamp())
def regime_at(ts):
    e=epoch(ts);j=bisect.bisect_right(T,e)-1            # último bar <= entrada (causal)
    return reg[j] if 0<=j<len(reg) else None
for t in trades:
    t["regime"]=regime_at(t["ts"]);t["yr"]=t["ts"][:4];t["kept_poc"]=t["ts"] not in cut8
def panel(rows,name):
    if not rows: print(f"  {name:34} n=0");return
    rows=sorted(rows,key=lambda r:r["ts"]);n=len(rows);w=sum(1 for r in rows if r["win"]);sumR=sum(r["R"] for r in rows)
    # DD + streak sobre R cumulativo em ordem
    cum=0;peak=0;dd=0;cs=0;mxls=0
    for r in rows:
        cum+=r["R"];peak=max(peak,cum);dd=min(dd,cum-peak)
        cs=cs+1 if not r["win"] else 0;mxls=max(mxls,cs)
    rdd=sumR/abs(dd) if dd<0 else float('inf')
    print(f"  {name:34} N={n:2} WR={100*w/n:3.0f}% sumR={sumR:+6.1f} avgR={sumR/n:+5.2f} DD={dd:5.1f} ret/DD={rdd if rdd!=float('inf') else 99:5.1f} maxLoseStreak={mxls}")
print("="*70);print("L1 EMA21 LONG 4H — detector phase10 aplicado (causal no bar de entrada)");print("="*70)
from collections import Counter
print("dist regime (34 trades):",dict(Counter(t['regime'] for t in trades)))
print("\n-- POR REGIME (todos os 34) --")
for rg in ["BULL","RANGE","BEAR",None]:
    panel([t for t in trades if t["regime"]==rg],f"regime={rg}")
print("\n-- BASES de comparação --")
panel(trades,"BASE 34 (aprovados)")
panel([t for t in trades if t["kept_poc"]],"POC-cut 26 (versão aprovada)")
print("\n-- GATING por regime do phase10 (agrega benefício?) --")
panel([t for t in trades if t["regime"]=="BULL"],"34 ∩ BULL")
panel([t for t in trades if t["regime"] in("BULL","RANGE")],"34 ∩ (BULL∪RANGE) [exclui BEAR]")
panel([t for t in trades if t["kept_poc"] and t["regime"]=="BULL"],"POC26 ∩ BULL")
panel([t for t in trades if t["kept_poc"] and t["regime"] in("BULL","RANGE")],"POC26 ∩ (BULL∪RANGE)")
print("\n-- o que o regime CORTA vs o loser-cut POC (sobreposição) --")
bear=[t for t in trades if t["regime"]=="BEAR"]
print(f"  trades em BEAR: {len(bear)} | desses, win={sum(1 for t in bear if t['win'])} sumR={sum(t['R'] for t in bear):+.1f}")
print(f"  BEAR já cortados pelo POC-cut: {sum(1 for t in bear if not t['kept_poc'])}/{len(bear)}")
cutters=[t for t in trades if not t['kept_poc']]
print(f"  os 8 do POC-cut: regimes = {dict(Counter(t['regime'] for t in cutters))} | win={sum(1 for t in cutters if t['win'])}/8 sumR={sum(t['R'] for t in cutters):+.1f}")
