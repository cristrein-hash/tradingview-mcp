#!/usr/bin/env python3
"""
_engine_nas_smc.py — Investigative mining of CAUSAL entry triggers under the
NAS/SMC lens for the XAU 15m BigBeluga+NAS (Leonardo) RECLAIM model.

Universe: fractal lows n=3519, entry=RECLAIM, outcome=R_reclaim (let-run, structural SL).
Base: avgR=+0.727, WR=45.4%, runner(R>=5)=6.5%.

Lens: nas_long_16/48, nas_short_16, nas_last_long, smc_choch, smc_bos.
NAS-LONG cluster/timing + CHoCH/BOS recency as structural confirmation.

HARD RULES enforced here:
  - Features are causal (bar of reclaim). NEVER use near_M8/R_reclaim/R_8atr/held8/runner as a FEATURE.
  - Report n, WR, avgR, and avgR per year (2024/2025/2026).
  - robust = avgR>base in ALL 3 years AND n>=30 AND not carried by top-2 trades
    (ex-top2 avgR must still beat base).
"""
import json
import itertools

BASE = 0.727
PATH = "entry_dataset.jsonl"
ROWS = [json.loads(l) for l in open(PATH)]


def stats(rs):
    n = len(rs)
    if n == 0:
        return None
    R = [r["R_reclaim"] for r in rs]
    wr = sum(1 for x in R if x > 0) / n
    avg = sum(R) / n
    run = sum(1 for x in R if x >= 5) / n
    by = {}
    for y in (2024, 2025, 2026):
        sub = [r["R_reclaim"] for r in rs if r["yr"] == y]
        by[y] = (len(sub), round(sum(sub) / len(sub), 3) if sub else None)
    # ex-top2
    Rs = sorted(R, reverse=True)
    extop2 = (sum(Rs[2:]) / (n - 2)) if n > 2 else None
    return {
        "n": n, "wr": round(wr, 3), "avg": round(avg, 3), "run": round(run, 3),
        "y24": by[2024], "y25": by[2025], "y26": by[2026],
        "extop2": round(extop2, 3) if extop2 is not None else None,
    }


def robust(s):
    if s is None or s["n"] < 30:
        return False
    for y in ("y24", "y25", "y26"):
        ny, ay = s[y]
        if ny < 5 or ay is None or ay <= BASE:
            return False
    if s["extop2"] is None or s["extop2"] <= BASE:
        return False
    return True


def show(desc, rs):
    s = stats(rs)
    if s is None:
        print(f"{desc}: EMPTY")
        return None
    r = robust(s)
    print(f"{desc}\n  n={s['n']} WR={s['wr']} avgR={s['avg']} lift={round(s['avg']-BASE,3)} "
          f"run={s['run']} | y24={s['y24']} y25={s['y25']} y26={s['y26']} | exTop2={s['extop2']} "
          f"| ROBUST={r}")
    return s, r


print("=" * 90)
print("BASELINE")
show("ALL", ROWS)

print("=" * 90)
print("SINGLE-FEATURE SCANS (NAS/SMC lens)")

# nas_long thresholds
for thr in (1, 2, 3, 4):
    show(f"nas_long_16 >= {thr}", [r for r in ROWS if r["nas_long_16"] >= thr])
for thr in (1, 2, 3, 4, 5, 6):
    show(f"nas_long_48 >= {thr}", [r for r in ROWS if r["nas_long_48"] >= thr])
show("nas_last_long == 1", [r for r in ROWS if r["nas_last_long"] == 1])
show("nas_last_long == 0", [r for r in ROWS if r["nas_last_long"] == 0])

# nas_short as a NEGATIVE filter (avoid recent short cluster)
for thr in (1, 2, 3):
    show(f"nas_short_16 == 0 (none) baseline-ref", [r for r in ROWS if r["nas_short_16"] == 0]) if thr == 1 else None
    show(f"nas_short_16 <= {thr-1}", [r for r in ROWS if r["nas_short_16"] <= thr - 1])

# smc recency
for v in (1, 2, 3):
    show(f"smc_choch == {v} (recency bucket)", [r for r in ROWS if r["smc_choch"] == v])
for v in (1, 2, 3):
    show(f"smc_bos == {v}", [r for r in ROWS if r["smc_bos"] == v])
show("smc_choch in (1,2) recent CHoCH", [r for r in ROWS if r["smc_choch"] in (1, 2)])
show("smc_bos in (1,2) recent BOS", [r for r in ROWS if r["smc_bos"] in (1, 2)])

print("=" * 90)
print("COMBOS: NAS-LONG cluster + structural confirmation")

# NAS long present + recent CHoCH
show("nas_long_16>=1 AND smc_choch in(1,2)",
     [r for r in ROWS if r["nas_long_16"] >= 1 and r["smc_choch"] in (1, 2)])
show("nas_long_16>=2 AND smc_choch in(1,2)",
     [r for r in ROWS if r["nas_long_16"] >= 2 and r["smc_choch"] in (1, 2)])
show("nas_long_48>=2 AND smc_choch in(1,2)",
     [r for r in ROWS if r["nas_long_48"] >= 2 and r["smc_choch"] in (1, 2)])
show("nas_long_48>=3 AND smc_choch in(1,2)",
     [r for r in ROWS if r["nas_long_48"] >= 3 and r["smc_choch"] in (1, 2)])

# NAS long + recent BOS (continuation structure)
show("nas_long_16>=1 AND smc_bos in(1,2)",
     [r for r in ROWS if r["nas_long_16"] >= 1 and r["smc_bos"] in (1, 2)])
show("nas_long_48>=2 AND smc_bos in(1,2)",
     [r for r in ROWS if r["nas_long_48"] >= 2 and r["smc_bos"] in (1, 2)])

# NAS long + last signal long (timing freshness)
show("nas_last_long==1 AND nas_long_16>=1",
     [r for r in ROWS if r["nas_last_long"] == 1 and r["nas_long_16"] >= 1])
show("nas_last_long==1 AND nas_long_48>=2",
     [r for r in ROWS if r["nas_last_long"] == 1 and r["nas_long_48"] >= 2])
show("nas_last_long==1 AND nas_long_48>=3",
     [r for r in ROWS if r["nas_last_long"] == 1 and r["nas_long_48"] >= 3])

# NAS long + NO recent short cluster (clean directional)
show("nas_long_16>=1 AND nas_short_16==0",
     [r for r in ROWS if r["nas_long_16"] >= 1 and r["nas_short_16"] == 0])
show("nas_long_48>=2 AND nas_short_16==0",
     [r for r in ROWS if r["nas_long_48"] >= 2 and r["nas_short_16"] == 0])

# Triple: nas cluster + choch + clean
show("nas_long_48>=2 AND smc_choch in(1,2) AND nas_short_16==0",
     [r for r in ROWS if r["nas_long_48"] >= 2 and r["smc_choch"] in (1, 2) and r["nas_short_16"] == 0])
show("nas_last_long==1 AND smc_choch in(1,2) AND nas_long_48>=2",
     [r for r in ROWS if r["nas_last_long"] == 1 and r["smc_choch"] in (1, 2) and r["nas_long_48"] >= 2])

print("=" * 90)
print("INTERACTION with macro/structure context (still NAS-anchored)")
show("nas_long_48>=2 AND macro_bull==1",
     [r for r in ROWS if r["nas_long_48"] >= 2 and r["macro_bull"] == 1])
show("nas_long_16>=1 AND macro_bear==0",
     [r for r in ROWS if r["nas_long_16"] >= 1 and r["macro_bear"] == 0])
show("nas_long_48>=2 AND smc_bos in(1,2) AND nas_short_16==0",
     [r for r in ROWS if r["nas_long_48"] >= 2 and r["smc_bos"] in (1, 2) and r["nas_short_16"] == 0])
