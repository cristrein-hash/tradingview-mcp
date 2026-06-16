"""Regime Classifier B v2 — Cascade + Volatility + STALL + SHARP_DROP + DIST_ALARM.

Three new signals added based on visual feedback:
1. STALL: no new 26-week high in N+ days → push to TRANSITION (catches accumulation/distribution)
2. SHARP_DROP: drawdown >K ATR from 4-week high in <M days → push to BEAR (catches sharp sell-offs before cascade confirms)
3. DIST_ALARM: distribution event from classifier D within last 12 weeks → push BEAR earlier
"""
import json
from datetime import datetime

# Load data
print("Loading data...")
with open("/tmp/regime_B_classifications.jsonl") as f:
    bars_b = [json.loads(l) for l in f]
print(f"  B classifications: {len(bars_b)}")

with open("/tmp/xau_daily_with_features.jsonl") as f:
    daily = [json.loads(l) for l in f]
print(f"  Daily bars: {len(daily)}")

# Index daily by ts
daily_by_ts = {b["ts"]: b for b in daily}

# Load distribution events from classifier D
try:
    with open("/tmp/regime_D_distribution_events.jsonl") as f:
        dist_events = [json.loads(l) for l in f]
    print(f"  Distribution events: {len(dist_events)}")
except FileNotFoundError:
    dist_events = []
    print(f"  WARNING: no distribution events file — proceeding without DIST_ALARM")

dist_dates = set()
for e in dist_events:
    # Each event has a date; we'll consider 12-week window after
    dist_dates.add(e.get("ts", e.get("date", "")))

# Build daily look-back for STALL and SHARP_DROP
# Need rolling 26-week (182 days) high and 4-week (28 days) high
daily_sorted = sorted(daily, key=lambda b: b["ts"])
N = len(daily_sorted)

# Pre-compute rolling 182-day high (26 weeks)
rolling_high_182 = [None] * N
for i in range(N):
    start = max(0, i - 181)
    rolling_high_182[i] = max(daily_sorted[j]["high"] for j in range(start, i+1))

# Pre-compute rolling 28-day high (4 weeks)
rolling_high_28 = [None] * N
for i in range(N):
    start = max(0, i - 27)
    rolling_high_28[i] = max(daily_sorted[j]["high"] for j in range(start, i+1))

# Pre-compute days since last 26-week new high
days_since_new_high = [None] * N
last_new_high_idx = 0
for i in range(N):
    h = daily_sorted[i]["high"]
    # Was a new high made within last 1 day? (i.e., today's high == rolling 26w high)
    if h >= rolling_high_182[i] - 0.001:
        last_new_high_idx = i
    days_since_new_high[i] = i - last_new_high_idx

# Pre-compute drawdown from 4-week high in last 10 days
sharp_drop_signal = [False] * N
for i in range(N):
    if i < 10: continue
    atr = daily_sorted[i].get("atr_14")
    if not atr: continue
    # Max high in last 28 days
    h4w = rolling_high_28[i]
    # Current close
    c = daily_sorted[i]["close"]
    # Drawdown
    dd = h4w - c
    # Days since 4w high reached
    days_since_4w_high = 0
    for j in range(i, max(0, i-28), -1):
        if daily_sorted[j]["high"] >= h4w - 0.001:
            days_since_4w_high = i - j
            break
    # Fire if dd > 2.5 ATR AND drop happened in <10 days
    if dd > 2.5 * atr and 0 < days_since_4w_high <= 10:
        sharp_drop_signal[i] = True

# Pre-compute STALL signal: days_since_new_high >= 30
stall_signal = [days_since_new_high[i] >= 30 for i in range(N)]

# Pre-compute DIST_ALARM: any distribution event in last 84 days (12 weeks)
def dist_alarm_at(ts):
    ts_date = ts
    for d in dist_dates:
        if d <= ts_date:
            # Calculate days diff
            from datetime import datetime
            try:
                d1 = datetime.fromisoformat(d[:10])
                d2 = datetime.fromisoformat(ts_date[:10])
                diff = (d2 - d1).days
                if 0 <= diff <= 84:
                    return True
            except:
                pass
    return False

dist_alarm_signal = [dist_alarm_at(b["ts"]) for b in daily_sorted]

# Index for lookup
daily_idx = {b["ts"]: i for i, b in enumerate(daily_sorted)}

# === Re-classify using v1 B + new signals ===
output = []
for b in bars_b:
    ts = b["ts"]
    if ts not in daily_idx:
        # Use original state
        new_state = b["state"]
        b["v2_state"] = new_state
        b["stall"] = False
        b["sharp_drop"] = False
        b["dist_alarm"] = False
        b["v2_score_modifier"] = 0
        output.append(b)
        continue

    i = daily_idx[ts]
    stall = stall_signal[i]
    sd = sharp_drop_signal[i]
    da = dist_alarm_signal[i]

    # Compute score modifier
    # STALL: push BULL state toward TRANSITION (-1)
    # SHARP_DROP: push toward BEAR (-2)
    # DIST_ALARM: push toward BEAR (-1)
    modifier = 0
    if stall: modifier -= 1
    if sd: modifier -= 2
    if da: modifier -= 1

    # Combine with original combined_score
    orig_score = b.get("combined_score", 0)
    new_score = orig_score + modifier

    # Re-classify with same threshold logic
    if new_score >= 2:
        v2_state = "BULL"
    elif new_score <= -2:
        v2_state = "BEAR"
    else:
        v2_state = "TRANSITION"

    # Apply hysteresis: only flip if state different for 2+ consecutive days
    # For simplicity, just emit instantaneous; hysteresis handled in run-grouping
    b["v2_state"] = v2_state
    b["stall"] = stall
    b["sharp_drop"] = sd
    b["dist_alarm"] = da
    b["v2_score_modifier"] = modifier
    output.append(b)

# Apply 2-day hysteresis on v2_state: state only flips if 2 consecutive days agree
def hysteresis(states, k=2):
    if not states: return []
    out = list(states)
    cur = out[0]
    pending = None
    pending_count = 0
    for i in range(1, len(out)):
        if out[i] == cur:
            pending = None
            pending_count = 0
        else:
            if pending == out[i]:
                pending_count += 1
                if pending_count >= k:
                    cur = out[i]
                    pending = None
                    pending_count = 0
            else:
                pending = out[i]
                pending_count = 1
            out[i] = cur
    return out

v2_states_raw = [b["v2_state"] for b in output]
v2_states = hysteresis(v2_states_raw, k=2)
for b, s in zip(output, v2_states):
    b["v2_state_final"] = s

# Save v2 classifications
with open("/tmp/regime_B_v2_classifications.jsonl", "w") as f:
    for b in output:
        f.write(json.dumps(b) + "\n")
print(f"\nSaved {len(output)} v2 classifications → /tmp/regime_B_v2_classifications.jsonl")

# Compare v1 vs v2 state distribution
from collections import Counter
v1_dist = Counter(b["state"] for b in output)
v2_dist = Counter(b["v2_state_final"] for b in output)
print(f"\nState distribution comparison:")
print(f"  v1: {dict(v1_dist)}")
print(f"  v2: {dict(v2_dist)}")

# Find where they differ
diffs = [(b["ts"], b["state"], b["v2_state_final"]) for b in output if b["state"] != b["v2_state_final"]]
print(f"\nDiffs v1→v2: {len(diffs)} days changed state")

# Group consecutive v2 runs >= 2024
filtered = [b for b in output if b["ts"] >= "2024-01-01"]
runs = []
if filtered:
    cur = {"state": filtered[0]["v2_state_final"], "start": filtered[0]["ts"], "end": filtered[0]["ts"], "days": 1}
    for b in filtered[1:]:
        if b["v2_state_final"] == cur["state"]:
            cur["end"] = b["ts"]
            cur["days"] += 1
        else:
            runs.append(cur)
            cur = {"state": b["v2_state_final"], "start": b["ts"], "end": b["ts"], "days": 1}
    runs.append(cur)

print(f"\n2024+ v2 runs: {len(runs)}")
for r in runs:
    print(f"  {r['state']:<12} {r['start']} → {r['end']} ({r['days']} days)")

# Save runs
with open("/tmp/regime_B_v2_runs_2024plus.jsonl", "w") as f:
    for r in runs:
        f.write(json.dumps(r) + "\n")
print(f"\nSaved runs → /tmp/regime_B_v2_runs_2024plus.jsonl")
