#!/usr/bin/env python3
"""Compara filtro de regime DIARIO B v3 (multi-TF state machine) vs macro 4H (ema50+swing) no 15M (Cris 2026-06-27).
Mapeia cada entrada ao v3_state do DIA ANTERIOR ja fechado (causal/conservador, sem look-ahead).
Cenarios sobre base A2+h1_eff>=0.15: 4H macro!=BEAR (atual) | B v3!=BEAR | B v3==BULL | AMBOS (corta se qualquer um=BEAR). RAW-causal."""
import json, bisect, datetime as dt
from pathlib import Path
from filter_harness import ROWS, dedup, stats
BV3=Path("/Users/cristrein/tradingview-mcp/my-strategy/strategies/candidates/regime_classifier_v3/regime_B_v3_classifications.jsonl")
cls=[json.loads(l) for l in BV3.read_text().splitlines() if l.strip()]
days=sorted((dt.date.fromisoformat(r["ts"]), r["v3_state"]) for r in cls)
DD=[d for d,_ in days]
def bv3_asof(t):
    ed=dt.datetime.utcfromtimestamp(t).date()
    k=bisect.bisect_left(DD,ed)-1  # ultimo dia com ts < data-da-entrada (dia anterior fechado)
    return days[k][1] if k>=0 else "WARMUP"
for r in ROWS: r["bv3"]=bv3_asof(r["t"])

base=dedup([r for r in ROWS if r['h1_eff'] is not None and r['h1_eff']>=0.15])
# distribuicao bv3 dos 211 + overlap com 4H BEAR
import collections
cb=collections.Counter(c["bv3"] for c in base)
print("v3_state (diario) dos 211:",dict(cb))
print("  4H BEAR nos 211:",sum(1 for c in base if c['macro_bear']==1),"| B v3 BEAR nos 211:",sum(1 for c in base if c['bv3']=='BEAR'),
      "| ambos BEAR:",sum(1 for c in base if c['macro_bear']==1 and c['bv3']=='BEAR'))
for st in ("BULL","TRANSITION","BEAR"):
    g=[c for c in base if c["bv3"]==st]
    if g: print(f"  B v3 {st:<10} n={len(g):>3} WR={100*sum(x['win'] for x in g)/len(g):.1f}% sumR={sum(x['R'] for x in g):+.1f}")
B=stats(base)

def yrstr(taken):
    yr={}
    for c in taken: yr.setdefault(c["yr"],[0,0]); yr[c["yr"]][0]+=1; yr[c["yr"]][1]+=c["win"]
    return "/".join(f"{100*yr[y][1]/yr[y][0]:.0f}" if y in yr else "-" for y in (2024,2025,2026))

H="r['h1_eff'] is not None and r['h1_eff']>=0.15"
CEN={
 "BASE A2+h1_eff (sem regime)": "True",
 "4H macro!=BEAR (ATUAL)": "r['macro_bear']==0",
 "B v3 != BEAR (diario)": "r['bv3']!='BEAR'",
 "B v3 == BULL so": "r['bv3']=='BULL'",
 "AMBOS (4H!=BEAR & Bv3!=BEAR)": "r['macro_bear']==0 and r['bv3']!='BEAR'",
}
print(f"\n{'cenario (+ h1_eff>=0.15)':<34} {'N':>4} {'WR':>5} {'sumR':>6} {'DD':>5} {'stk':>3} {'maxR':>4} | {'dWR':>5} {'dSumR':>6} {'dDD':>5} | yr24/25/26")
print(f"{'BASE211':<34} {B['n']:>4} {B['wr']:>5} {B['sumr']:>6} {B['dd']:>5} {B['streak']:>3} {B['maxR']:>4} | {'+0.0':>5} {'+0.0':>6} {'+0.0':>5} | {yrstr(base)}")
for name,cond in CEN.items():
    if cond=="True": continue
    fn=eval("lambda r:("+H+") and ("+cond+")")
    taken=dedup([r for r in ROWS if fn(r)]); s=stats(taken)
    print(f"{name:<34} {s['n']:>4} {s['wr']:>5} {s['sumr']:>6} {s['dd']:>5} {s['streak']:>3} {s['maxR']:>4} | {s['wr']-B['wr']:>+5.1f} {s['sumr']-B['sumr']:>+6.1f} {s['dd']-B['dd']:>+5.1f} | {yrstr(taken)}")
