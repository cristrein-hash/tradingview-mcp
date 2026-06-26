#!/usr/bin/env python3
"""
_engine_macro_regime.py — Macro 4H/regime lens entry-trigger miner.

Universe: 3519 fractal-low RECLAIM entries (close above low+0.25ATR), let-run, structural SL.
Target: R_reclaim (avgR), WR, runner(R>=5), per-year stability.
HARD RULES:
  - features are causal (at reclaim bar). Do NOT use near_M8/R_reclaim/R_8atr/held8/runner as FEATURE.
  - report n, WR, avgR, avgR per year (24/25/26).
  - robust = avgR>base in all 3 years AND n>=30 AND not carried by top-2 trades.
Lens: macro_bull, macro_bear, macro_drop_atr (leg depth), macro_retr (retracement), atr_regime.
Hypothesis: shallow-pullback-in-uptrend vs knife-in-deep-leg.
"""
import json
from collections import defaultdict

BASE = 0.727
ROWS = [json.loads(l) for l in open('entry_dataset.jsonl')]
for r in ROWS:
    r['R'] = r['R_reclaim']

def stats(rows):
    R = [r['R'] for r in rows]
    n = len(R)
    if n == 0:
        return None
    avg = sum(R)/n
    wr = sum(1 for x in R if x > 0)/n
    runner = sum(1 for x in R if x >= 5)/n
    by = {}
    for yr in (2024, 2025, 2026):
        Ry = [r['R'] for r in rows if r['yr'] == yr]
        by[yr] = (len(Ry), round(sum(Ry)/len(Ry), 3) if Ry else None,
                  round(sum(1 for x in Ry if x > 0)/len(Ry), 3) if Ry else None)
    # ex-top2 check
    Rs = sorted(R, reverse=True)
    ex2 = (sum(Rs[2:])/(n-2)) if n > 2 else avg
    return dict(n=n, wr=round(wr, 3), avg=round(avg, 3), runner=round(runner, 3),
                by=by, ex2=round(ex2, 3))

def report(name, rows):
    s = stats(rows)
    if s is None:
        print(f"\n## {name}\n  EMPTY")
        return
    yrs = s['by']
    sig3 = all(yrs[y][1] is not None and yrs[y][1] > BASE for y in (2024, 2025, 2026))
    n30 = s['n'] >= 30
    nall = all(yrs[y][0] >= 8 for y in (2024, 2025, 2026))  # enough per year
    not_carried = s['ex2'] > BASE
    robust = sig3 and n30 and not_carried and nall
    print(f"\n## {name}")
    print(f"  n={s['n']} WR={s['wr']} avgR={s['avg']} runner={s['runner']} lift={round(s['avg']-BASE,3)} ex2={s['ex2']}")
    print(f"  y24={yrs[2024]} y25={yrs[2025]} y26={yrs[2026]}")
    print(f"  sig3yr={sig3} n>=30={n30} not_carried={not_carried} perYr>=8={nall} ROBUST={robust}")
    return dict(name=name, s=s, robust=robust, sig3=sig3)


print("=== BASE ===")
report("ALL (base)", ROWS)

# ---- Single-feature regime cuts ----
print("\n\n=== MACRO REGIME SINGLE CUTS ===")
report("macro_bull==1", [r for r in ROWS if r['macro_bull'] == 1])
report("macro_bear==1", [r for r in ROWS if r['macro_bear'] == 1])
report("macro_bull==0 & macro_bear==0 (neutral)", [r for r in ROWS if r['macro_bull'] == 0 and r['macro_bear'] == 0])

# macro_drop_atr: leg depth. shallow vs deep
print("\n=== LEG DEPTH (macro_drop_atr) ===")
for thr in (2, 3, 4, 5, 6, 8):
    report(f"macro_drop_atr<{thr}", [r for r in ROWS if r['macro_drop_atr'] < thr])
    report(f"macro_drop_atr>={thr}", [r for r in ROWS if r['macro_drop_atr'] >= thr])

# macro_retr: retracement of the leg. shallow pullback = low retr
print("\n=== RETRACEMENT (macro_retr) ===")
for lo, hi in [(0, 0.382), (0, 0.5), (0.382, 0.618), (0.5, 0.786), (0.618, 1.0), (0, 0.618)]:
    report(f"macro_retr in [{lo},{hi})", [r for r in ROWS if lo <= r['macro_retr'] < hi])

# atr_regime
print("\n=== ATR REGIME ===")
for thr in (0.8, 1.0, 1.2):
    report(f"atr_regime<{thr}", [r for r in ROWS if r['atr_regime'] < thr])
    report(f"atr_regime>={thr}", [r for r in ROWS if r['atr_regime'] >= thr])

# ---- HYPOTHESIS: shallow pullback in uptrend vs knife in deep leg ----
print("\n\n=== HYPOTHESIS: shallow pullback in uptrend ===")
# uptrend = macro_bull; shallow = macro_retr low; not-deep leg
report("bull & retr<0.5", [r for r in ROWS if r['macro_bull'] == 1 and r['macro_retr'] < 0.5])
report("bull & retr<0.618", [r for r in ROWS if r['macro_bull'] == 1 and r['macro_retr'] < 0.618])
report("bull & retr>=0.618 (deep pull in up)", [r for r in ROWS if r['macro_bull'] == 1 and r['macro_retr'] >= 0.618])
report("NOT bear & retr<0.5", [r for r in ROWS if r['macro_bear'] == 0 and r['macro_retr'] < 0.5])
report("NOT bear & retr<0.618", [r for r in ROWS if r['macro_bear'] == 0 and r['macro_retr'] < 0.618])

print("\n=== KNIFE: deep leg + bear ===")
report("bear & drop>=4", [r for r in ROWS if r['macro_bear'] == 1 and r['macro_drop_atr'] >= 4])
report("drop>=5 (deep leg any)", [r for r in ROWS if r['macro_drop_atr'] >= 5])
report("bear & retr<0.5 (catch knife)", [r for r in ROWS if r['macro_bear'] == 1 and r['macro_retr'] < 0.5])
