#!/usr/bin/env python3
"""SM probe 1 — read-only: SMC event texts (CHoCH direction?), series fields,
full lifts table (15M lenses), 35 t0s span, primitives coverage span."""
import json, collections
from pathlib import Path

HERE = Path(__file__).resolve().parent

# 1. SMC event text vocabulary in one 15M block
d = json.load(open(HERE / "primitives" / "XAUUSD_15m_replay_2025-08-25_to_2025-11-25.primitives.json"))
print("primitives top-level keys:", list(d.keys()))
b0 = d["series"][500]
print("series bar fields:", sorted(b0.keys()))
print("sample bar:", {k: b0[k] for k in sorted(b0.keys())})
texts = collections.Counter(str(e.get("text", "")) for e in d["smc_events"])
print("\nSMC texts:", dict(texts))
e0 = d["smc_events"][0]
print("smc event fields:", sorted(e0.keys()), "sample:", e0)
print("nas event sample:", d["nas_events"][0] if d["nas_events"] else None)

# 2. full lifts (15M rows) from repriced map
rep = json.load(open(HERE / "results" / "cris_repriced_map_20260704.json"))
print("\n15M lifts (cov_cris / cov_ctrl / lift):")
for k, v in rep["lifts"].items():
    if k.endswith("|15M"):
        print(f"  {k:<28} {100*v[0]:>4.0f}% / {100*v[1]:>4.0f}%  {v[2]:.2f}x")
print("\n30M+1H survivors of interest:")
for k in ("quiet4_le1|30M", "rsi_40_60|1H", "no_initiative|1H", "absorb_sellML|1H",
          "dipleg_sell_dom|15M", "dipleg_sell_dom|30M", "dipleg_sell_dom|1H", "nas_LONG_rec24|30M"):
    v = rep["lifts"].get(k)
    if v: print(f"  {k:<28} {100*v[0]:>4.0f}% / {100*v[1]:>4.0f}%  {v[2]:.2f}x")

# 3. 35 t0s
AN = json.load(open(HERE / "results" / "cris_trades_analysis_20260704.json"))
import datetime as dt
ts = sorted(r["t"] for r in AN)
print(f"\n35 trades: n={len(ts)}  span {dt.datetime.utcfromtimestamp(ts[0])} -> {dt.datetime.utcfromtimestamp(ts[-1])}")
print("fields of one record:", sorted(AN[0].keys()))

# 4. primitives coverage span (all 9 blocks)
import glob
tot = []
for p in sorted(glob.glob(str(HERE / "primitives" / "*.primitives.json"))):
    dd = json.load(open(p))
    S = dd["series"]
    tot.append((Path(p).name, len(S), S[0]["t"], S[-1]["t"]))
for name, n, a, b in tot:
    print(f"  {name}: {n} bars  {dt.datetime.utcfromtimestamp(a):%Y-%m-%d} -> {dt.datetime.utcfromtimestamp(b):%Y-%m-%d}")
