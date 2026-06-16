"""Regime Classifier B v3 — Hybrid with MACRO_BROKEN state machine.

Builds on v2. Adds an overlay:
- Enter MACRO_BROKEN when: drawdown from 13-week high > 10% OR 3+ consecutive BEAR days
- In MACRO_BROKEN mode: any BULL signal downgrades to TRANSITION
- Exit MACRO_BROKEN via MACRO_REPAIR:
  - Weekly new high (close > 8-week high) OR
  - 5+ consecutive sustained BULL days from v2

This captures Cris's intuition: after macro breaks, don't return to BULL
during counter-trend pullbacks until structure REPAIRS.
"""
import json
from datetime import datetime, timedelta

# Load v2 classifications
with open("/tmp/regime_B_v2_classifications.jsonl") as f:
    bars = [json.loads(l) for l in f]
print(f"Loaded {len(bars)} v2 bars")

# Load daily for prices and high/low
with open("/tmp/xau_daily_with_features.jsonl") as f:
    daily = [json.loads(l) for l in f]
daily_by_ts = {b["ts"]: b for b in daily}
daily_sorted = sorted(daily, key=lambda b: b["ts"])
daily_idx = {b["ts"]: i for i, b in enumerate(daily_sorted)}

# Pre-compute 13-week (91 day) rolling high
N = len(daily_sorted)
rolling_high_91 = [None] * N
for i in range(N):
    start = max(0, i - 90)
    rolling_high_91[i] = max(daily_sorted[j]["high"] for j in range(start, i+1))

# Pre-compute 8-week (56 day) rolling high
rolling_high_56 = [None] * N
for i in range(N):
    start = max(0, i - 55)
    rolling_high_56[i] = max(daily_sorted[j]["high"] for j in range(start, i+1))

# Pre-compute drawdown from 13-week high
drawdown_pct_13w = [None] * N
for i in range(N):
    c = daily_sorted[i]["close"]
    h = rolling_high_91[i]
    drawdown_pct_13w[i] = (h - c) / h * 100 if h else 0

# === Apply MACRO_BROKEN state machine ===
bars_sorted = sorted(bars, key=lambda b: b["ts"])

macro_broken = False
macro_broken_start = None
consecutive_bear = 0
consecutive_bull = 0

for b in bars_sorted:
    ts = b["ts"]
    v2_state = b.get("v2_state_final", b.get("state"))
    i = daily_idx.get(ts)
    if i is None:
        b["v3_state"] = v2_state
        b["macro_broken"] = macro_broken
        continue

    # Count consecutive states from v2
    if v2_state == "BEAR":
        consecutive_bear += 1
        consecutive_bull = 0
    elif v2_state == "BULL":
        consecutive_bull += 1
        consecutive_bear = 0
    else:
        # TRANSITION: neutral, keep counters but don't increment
        pass

    dd = drawdown_pct_13w[i] or 0

    # Enter MACRO_BROKEN
    if not macro_broken:
        if dd > 10.0 or consecutive_bear >= 3:
            macro_broken = True
            macro_broken_start = ts

    # Exit MACRO_BROKEN — MACRO_REPAIR (strict: requires real structural recovery)
    if macro_broken:
        # Repair condition 1: close within 3% of 13-week high (return to peak structure)
        c = daily_sorted[i]["close"]
        h13w = rolling_high_91[i]
        near_peak = h13w and c >= h13w * 0.97
        # Repair condition 2: new 13-week high (definitive repair)
        is_new_13w_high = h13w and c >= h13w - 0.001
        if near_peak or is_new_13w_high:
            macro_broken = False
            macro_broken_start = None

    # Final v3 state
    if macro_broken and v2_state == "BULL":
        v3_state = "TRANSITION"  # downgrade BULL to TRANSITION
    else:
        v3_state = v2_state

    b["v3_state"] = v3_state
    b["macro_broken"] = macro_broken
    b["drawdown_pct_13w"] = dd

# Save
with open("/tmp/regime_B_v3_classifications.jsonl", "w") as f:
    for b in bars_sorted:
        f.write(json.dumps(b) + "\n")
print(f"Saved /tmp/regime_B_v3_classifications.jsonl")

# Compare distributions
from collections import Counter
v2_dist = Counter(b.get("v2_state_final", "?") for b in bars_sorted)
v3_dist = Counter(b.get("v3_state", "?") for b in bars_sorted)
print(f"\nState distribution:")
print(f"  v2: {dict(v2_dist)}")
print(f"  v3: {dict(v3_dist)}")

# Diffs
diffs = [(b["ts"], b.get("v2_state_final","?"), b.get("v3_state","?")) for b in bars_sorted
         if b.get("v2_state_final") != b.get("v3_state")]
print(f"v2 → v3 diffs: {len(diffs)}")

# Group runs >= 2024
filtered = [b for b in bars_sorted if b["ts"] >= "2024-01-01"]
runs = []
if filtered:
    cur = {"state": filtered[0]["v3_state"], "start": filtered[0]["ts"], "end": filtered[0]["ts"], "days": 1}
    for b in filtered[1:]:
        if b["v3_state"] == cur["state"]:
            cur["end"] = b["ts"]
            cur["days"] += 1
        else:
            runs.append(cur)
            cur = {"state": b["v3_state"], "start": b["ts"], "end": b["ts"], "days": 1}
    runs.append(cur)

with open("/tmp/regime_B_v3_runs_2024plus.jsonl", "w") as f:
    for r in runs:
        f.write(json.dumps(r) + "\n")
print(f"\n2024+ v3 runs: {len(runs)} → /tmp/regime_B_v3_runs_2024plus.jsonl")

# Track macro_broken periods
mb_runs = []
cur_mb = None
for b in filtered:
    if b.get("macro_broken"):
        if cur_mb is None:
            cur_mb = {"start": b["ts"], "end": b["ts"]}
        else:
            cur_mb["end"] = b["ts"]
    else:
        if cur_mb:
            mb_runs.append(cur_mb)
            cur_mb = None
if cur_mb:
    mb_runs.append(cur_mb)
print(f"\nMACRO_BROKEN periods (2024+): {len(mb_runs)}")
for m in mb_runs:
    print(f"  {m['start']} → {m['end']}")

print("\n=== 2024+ v3 runs ===")
for r in runs:
    print(f"  {r['state']:<12} {r['start']} → {r['end']} ({r['days']}d)")
