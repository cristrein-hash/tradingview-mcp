#!/usr/bin/env python3
"""Diagnóstico dos 197 mismatches OHLC entre run-1 e run-2 da extensão: magnitude por campo,
qual campo diverge, adjacência a soluços (dup/hole), e comparação das 2 barras de overlap
com o 8º bloco (árbitro independente)."""
import json, datetime as dt
from pathlib import Path
BT = Path("/Users/cristrein/tradingview-mcp/alert-bridge/logs/backtests")
HERE = Path(__file__).parent

def load(p):
    recs = {}
    for l in open(p, "rb"):
        r = json.loads(l); recs[r["ohlcv"][-1]["time"]] = r["ohlcv"][-1]
    return recs
r2 = load(BT / "XAUUSD_15m_replay_2026-05-25_to_2026-07-04.normalized.jsonl")
r1 = load(BT / "forensics_20260704_run1" / "XAUUSD_15m_replay_2026-05-25_to_2026-07-04.normalized.jsonl")
common = sorted(set(r2) & set(r1))
diffs = []
for t in common:
    a, b = r2[t], r1[t]
    d = {k: abs(a[k] - b[k]) for k in ("open", "high", "low", "close")}
    if max(d.values()) > 1e-9: diffs.append((t, d, a, b))
print(f"mismatches: {len(diffs)}/{len(common)}")
import statistics as st
for k in ("open", "high", "low", "close"):
    v = [d[1][k] for d in diffs if d[1][k] > 1e-9]
    if v: print(f"  {k}: n={len(v)} med={st.median(v):.3f} max={max(v):.2f}")
big = [d for d in diffs if max(d[1].values()) > 1.0]
print(f"  diffs > $1: {len(big)}")
for t, d, a, b in big[:8]:
    print(f"    {dt.datetime.utcfromtimestamp(t)} r2={a['open']}/{a['high']}/{a['low']}/{a['close']} r1={b['open']}/{b['high']}/{b['low']}/{b['close']}")
# árbitro: 2 barras de overlap vs primitives do 8º bloco
prim = json.load(open(HERE / "primitives" / "XAUUSD_15m_replay_2026-02-25_to_2026-05-25_rerun_customOBbaseline.primitives.json"))["series"]
p8 = {b["t"]: b for b in prim}
for t in [x for x in common if x in p8]:
    e = p8[t]
    m2 = max(abs(r2[t][k] - e[k[0]]) for k in ("open", "high", "low", "close"))
    m1 = max(abs(r1[t][k] - e[k[0]]) for k in ("open", "high", "low", "close"))
    print(f"  árbitro 8º bloco t={dt.datetime.utcfromtimestamp(t)}: |r2-8º|max={m2:.3f} |r1-8º|max={m1:.3f}")
# volume também difere?
vd = [abs((r2[t].get('volume') or 0)-(r1[t].get('volume') or 0)) for t in common]
print(f"  volume: barras com diff {sum(1 for x in vd if x>0)}, max {max(vd)}")
