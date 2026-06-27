"""
DA probe for feature 'session_birth_pedigree':
1. Does 15M tick-volume show a session-of-day pattern (confound: born_vol_ratio
   would mechanically score Asia-born zones low REGARDLESS of zone quality)?
2. Is born_vol_ratio computable causally from RAW (born_t + pre-birth v window)?
3. How concentrated is zone birth across sessions (sample sufficiency per cell)?
RAW exclusive, causal. No look-ahead.
"""
import json, statistics, datetime, glob
from collections import defaultdict

files = sorted(glob.glob("primitives/*.primitives.json"))

# --- 1. volume by UTC hour, pooled across all blocks ---
byh = defaultdict(list)
all_series = []
for f in files:
    d = json.load(open(f))
    for b in d["series"]:
        if b.get("v") is None:
            continue
        h = datetime.datetime.utcfromtimestamp(b["t"]).hour
        byh[h].append(b["v"])
        all_series.append(b)

print("=== median tick-volume by UTC hour (pooled, all blocks) ===")
for h in range(24):
    if byh[h]:
        print(f"{h:02d}h  med={statistics.median(byh[h]):7.0f}  n={len(byh[h])}")

def sess(h):
    if 22 <= h or h < 6: return "ASIA"
    if 6 <= h < 12: return "LONDON"
    if 12 <= h < 16: return "NY_AM"
    return "NY_PM"

bys = defaultdict(list)
for h in range(24):
    for v in byh[h]:
        bys[sess(h)].append(v)
print("\n=== median tick-volume by SESSION ===")
for s in ["ASIA","LONDON","NY_AM","NY_PM"]:
    print(f"{s:8s} med={statistics.median(bys[s]):7.0f}  n={len(bys[s])}")

# --- 2 & 3. zone birth: session distribution + born_vol_ratio computability ---
# build per-block sorted series for causal pre-birth window lookup
print("\n=== zone birth session distribution + born_vol_ratio feasibility ===")
birth_sess = defaultdict(int)
ratios = []
computable = 0
uncomputable = 0
for f in files:
    d = json.load(open(f))
    s = d["series"]
    s = [b for b in s if b.get("v") is not None]
    s.sort(key=lambda b: b["t"])
    times = [b["t"] for b in s]
    import bisect
    for z in d.get("zones", []):
        bt = z.get("born_t")
        if bt is None:
            continue
        h = datetime.datetime.utcfromtimestamp(bt).hour
        birth_sess[sess(h)] += 1
        # index of birth bar
        idx = bisect.bisect_left(times, bt)
        if idx >= len(times) or times[idx] != bt:
            # birth_t not exactly a bar -> snap to last bar < bt
            idx = bisect.bisect_right(times, bt) - 1
        if idx < 0:
            uncomputable += 1
            continue
        # birth window [born_t-2 .. born_t] = idx-2..idx
        bw = s[max(0, idx-2): idx+1]
        # pre-birth baseline: 96 bars strictly before born_t -> idx-96..idx-1
        pb = s[max(0, idx-96): idx]
        if len(bw) < 1 or len(pb) < 20:
            uncomputable += 1
            continue
        birth_vol = statistics.mean([b["v"] for b in bw])
        base = statistics.median([b["v"] for b in pb])
        if base == 0:
            uncomputable += 1
            continue
        ratios.append(birth_vol / base)
        computable += 1

print("birth session counts:", dict(birth_sess))
print(f"born_vol_ratio computable={computable}  uncomputable={uncomputable}")
if ratios:
    ratios.sort()
    print(f"born_vol_ratio  min={ratios[0]:.2f} median={statistics.median(ratios):.2f} "
          f"p90={ratios[int(0.9*len(ratios))]:.2f} max={ratios[-1]:.2f}")
