#!/usr/bin/env python3
"""Diagnostico do funil do gatilho P3: por caso, conta pools SSL e onde cada um morre
(status/escala/sem-alvo-BSL/r-fora). Materializado. py3 stdlib."""
import json, sys, datetime as dt
from pathlib import Path
REPO=Path("/Users/cristrein/tradingview-mcp"); HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(REPO/"my-strategy/core")); sys.path.insert(0,str(REPO/"alert-bridge"))
import raw_reader as RR, lm_pools as LP, liquidity_map as LM
def jl(p):
    try: return [json.loads(l) for l in open(p) if l.strip()]
    except: return []
raw=RR.series_flat(RR.resolve_gz("XAUUSD","15M"))
rows=[dict(t=t,o=v[0],h=v[1],l=v[2],c=v[3]) for t,v in sorted(raw.items())]
raw_end=rows[-1]["t"]
store=sorted(jl(REPO/"my-strategy/core/bar_store/store/bars_15m.jsonl"),key=lambda x:x["t"])
cases=jl(HERE/"ground_truth_cases.jsonl")
dated=[c for c in cases if c.get("t") and c.get("entry")]
seen={}
for c in sorted(dated,key=lambda x:x["t"]):
    k=(round(c["entry"],1),dt.datetime.fromtimestamp(c["t"],dt.timezone.utc).date())
    if k not in seen: seen[k]=c
longs=[c for c in seen.values() if c["dir"]=="LONG"][:12]   # amostra p/ diagnostico
from collections import Counter
tot=Counter()
for c in longs:
    t=c["t"]; src=rows if t<=raw_end else store
    upto=[b for b in src if b["t"]<=t][-450:]
    if len(upto)<120: continue
    atr=LM._atr(upto[-400:])
    ssl=LP.pools_asof(upto,side="SSL"); bsl=LP.pools_asof(upto,side="BSL")
    bsl_intact=[b for b in bsl if b["status"]=="INTACT"]
    print(f"{c['src']}:{str(c['name'])[:8]:<9} SSL={len(ssl)} (INTACT/SWEPT={sum(1 for p in ssl if p['status'] in ('INTACT','SWEPT'))}) BSL={len(bsl)} (INTACT={len(bsl_intact)})")
    for p in ssl:
        if p["status"] not in ("INTACT","SWEPT"): tot["status_consumed"]+=1; continue
        limit=p["hi"]; sl=p["lo"]-0.1*atr; risk=limit-sl
        if risk<=0.05*atr or risk>2.5*atr: tot["escala"]+=1; continue
        above=[b for b in bsl_intact if b["lo"]>limit]
        if not above: tot["sem_alvo_BSL_intact"]+=1; continue
        r=(min(x["lo"] for x in above)-limit)/risk
        if r>5.0: tot["r>5"]+=1
        elif r<1.0: tot["r<1"]+=1
        else: tot["NASCE"]+=1
print("\nfunil agregado (12 casos):",dict(tot))
