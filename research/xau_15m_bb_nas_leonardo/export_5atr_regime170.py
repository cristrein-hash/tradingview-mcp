#!/usr/bin/env python3
"""Exporta os 170 trades: A2 5ATR + h1_eff>=0.15 + (4H macro!=BEAR) + (B v3 diario != BEAR). (Cris escolheu 2026-06-27)
SL=A (flush-0.1ATR), EXIT let-run, dedup uma-posicao. bv3 as-of dia-anterior fechado (causal).
exit price = entry + R*(entry-sl). -> strategy_5atr_regime170_trades.csv p/ plot canonico. RAW-causal."""
import json, bisect, csv, datetime as dt
from pathlib import Path
from filter_harness import ROWS, dedup
HERE=Path(__file__).parent
BV3=Path("/Users/cristrein/tradingview-mcp/my-strategy/strategies/candidates/regime_classifier_v3/regime_B_v3_classifications.jsonl")
days=sorted((dt.date.fromisoformat(json.loads(l)["ts"]), json.loads(l)["v3_state"]) for l in BV3.read_text().splitlines() if l.strip())
DD=[d for d,_ in days]
def bv3_asof(t):
    ed=dt.datetime.utcfromtimestamp(t).date(); k=bisect.bisect_left(DD,ed)-1
    return days[k][1] if k>=0 else "WARMUP"
kept=[r for r in ROWS if r['h1_eff'] is not None and r['h1_eff']>=0.15 and r['macro_bear']==0 and bv3_asof(r['t'])!='BEAR']
taken=dedup(kept); taken.sort(key=lambda x:x["t"])
for n,c in enumerate(taken,1): c["num"]=n
with open(HERE/"strategy_5atr_regime170_trades.csv","w",newline="") as f:
    w=csv.writer(f); w.writerow(["num","entry_t","entry","sl","exit","R","win","yr"])
    for c in taken:
        risk=c["entry"]-c["sl"]; exit_px=c["entry"]+c["R"]*risk
        w.writerow([c["num"],c["t"],round(c["entry"],2),round(c["sl"],2),round(exit_px,2),round(c["R"],2),c["win"],c["yr"]])
n=len(taken); wn=sum(c["win"] for c in taken)
print(f"strategy_5atr_regime170_trades.csv: N={n} winners={wn} losers={n-wn} WR={100*wn/n:.1f}% sumR={sum(c['R'] for c in taken):+.1f}")
