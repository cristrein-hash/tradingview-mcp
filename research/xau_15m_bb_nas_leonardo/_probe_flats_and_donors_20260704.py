#!/usr/bin/env python3
"""Extensão: (1) run-2 tem barras flat (O=H=L=C — corrida de captura)? (2) as 17 barras-doadoras
da run-1 (buracos da run-2) são flat? Decide splice parcial vs run-2 solo com buracos documentados."""
import json, datetime as dt
from pathlib import Path
BT = Path("/Users/cristrein/tradingview-mcp/alert-bridge/logs/backtests")
def load(p):
    recs = {}
    for l in open(p, "rb"):
        r = json.loads(l); recs[r["ohlcv"][-1]["time"]] = r["ohlcv"][-1]
    return recs
r2 = load(BT / "XAUUSD_15m_replay_2026-05-25_to_2026-07-04.normalized.jsonl")
r1 = load(BT / "forensics_20260704_run1" / "XAUUSD_15m_replay_2026-05-25_to_2026-07-04.normalized.jsonl")
flat = lambda b: b["open"] == b["high"] == b["low"] == b["close"]
f2 = [t for t, b in r2.items() if flat(b)]
print(f"run-2 barras flat: {len(f2)}")
for t in sorted(f2)[:10]: print("  ", dt.datetime.utcfromtimestamp(t))
donors = sorted(set(r1) - set(r2))
print(f"doadoras run-1 (17 buracos): {len(donors)} — flats entre elas:")
for t in donors:
    b = r1[t]
    print(f"  {dt.datetime.utcfromtimestamp(t)} flat={flat(b)} O={b['open']} H={b['high']} L={b['low']} C={b['close']} vol={b.get('volume')}")
