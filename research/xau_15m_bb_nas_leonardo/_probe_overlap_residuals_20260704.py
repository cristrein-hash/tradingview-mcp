#!/usr/bin/env python3
"""Resíduos da validação v2: (1) qual barra de overlap diverge do 8º bloco e quanto;
(2) confirmação de que a última barra (2026-07-03 16:30) é flat por fim-de-replay (descartável
segundo o plano §6 'partial candle'). Nota: engines usam setdefault → bloco antigo é autoritativo
no overlap; divergência ali não contamina downstream."""
import json, datetime as dt
from pathlib import Path
HERE = Path(__file__).parent
BT = Path("/Users/cristrein/tradingview-mcp/alert-bridge/logs/backtests")

def builder_bars(path):
    bars = {}
    for raw in open(path, "rb"):
        r = json.loads(raw)
        if not r.get("replay_current_dt"): continue
        for b in (r.get("ohlcv") or []):
            if isinstance(b, dict) and b.get("time") is not None:
                bars[b["time"]] = {"o": b["open"], "h": b["high"], "l": b["low"], "c": b["close"]}
    return bars
B2 = builder_bars(BT / "XAUUSD_15m_replay_2026-05-25_to_2026-07-04.normalized.jsonl")
p8 = {b["t"]: b for b in json.load(open(HERE / "primitives" / "XAUUSD_15m_replay_2026-02-25_to_2026-05-25_rerun_customOBbaseline.primitives.json"))["series"]}
for t in sorted(x for x in B2 if x <= 1779667200):
    if t in p8:
        e, b = p8[t], B2[t]
        d = {k: abs(b[k] - e[k]) for k in ("o", "h", "l", "c")}
        print(dt.datetime.utcfromtimestamp(t).isoformat(), "ext:", b, "| 8º:", {k: e[k] for k in ("o","h","l","c")}, "| maxdiff", round(max(d.values()), 3))
lb = max(B2)
print("última barra:", dt.datetime.utcfromtimestamp(lb).isoformat(), B2[lb])
