#!/usr/bin/env python3
"""
_engine_macro_regime2.py — refinement of macro-regime triggers.

Findings from pass 1 (_engine_macro_regime.py):
  - macro_drop_atr<4 ROBUST: n=831 avgR=1.03 lift+0.303 (3yr sig)
  - bull & retr>=0.618 ROBUST: n=790 avgR=0.885 lift+0.158
  - shallow-pullback (bull & retr<0.5) FAILED (lift-0.131)
  - deep leg / bear = knife = worse (confirms knife hypothesis: avoid deep leg)

This pass:
  1. tighten/combine shallow leg-depth
  2. test bull & retr>=0.618 & shallow leg interaction
  3. drop-top-5 robustness (runners carry avgR) + WR/runner reporting
  4. distinguish leg DEPTH (drop_atr) vs leg RETRACE (retr) cleanly
"""
import json

BASE = 0.727
ROWS = [json.loads(l) for l in open('entry_dataset.jsonl')]
for r in ROWS:
    r['R'] = r['R_reclaim']

def stats(rows):
    R = sorted([r['R'] for r in rows], reverse=True)
    n = len(R)
    if n == 0:
        return None
    avg = sum(R)/n
    wr = sum(1 for x in R if x > 0)/n
    runner = sum(1 for x in R if x >= 5)/n
    by = {}
    for yr in (2024, 2025, 2026):
        Ry = [r['R'] for r in rows if r['yr'] == yr]
        by[yr] = (len(Ry), round(sum(Ry)/len(Ry), 3) if Ry else None)
    ex2 = (sum(R[2:])/(n-2)) if n > 2 else avg
    ex5 = (sum(R[5:])/(n-5)) if n > 5 else avg
    return dict(n=n, wr=round(wr, 3), avg=round(avg, 3), runner=round(runner, 3),
                by=by, ex2=round(ex2, 3), ex5=round(ex5, 3), nrun=sum(1 for x in R if x >= 5))

def report(name, rows):
    s = stats(rows)
    if s is None:
        print(f"\n## {name}\n  EMPTY"); return
    yrs = s['by']
    sig3 = all(yrs[y][1] is not None and yrs[y][1] > BASE for y in (2024, 2025, 2026))
    n30 = s['n'] >= 30
    nall = all(yrs[y][0] >= 8 for y in (2024, 2025, 2026))
    not_carried = s['ex5'] > BASE  # stricter: survive dropping top-5
    robust = sig3 and n30 and not_carried and nall
    print(f"\n## {name}")
    print(f"  n={s['n']} WR={s['wr']} avgR={s['avg']} lift={round(s['avg']-BASE,3)} runner={s['runner']}({s['nrun']}) ex2={s['ex2']} ex5={s['ex5']}")
    print(f"  y24={yrs[2024]} y25={yrs[2025]} y26={yrs[2026]}")
    print(f"  sig3yr={sig3} n>=30={n30} survive_ex5={not_carried} ROBUST={robust}")
    return robust

print("=== BASE ===")
report("ALL", ROWS)

print("\n=== TIGHTEN LEG DEPTH ===")
for thr in (2.5, 3, 3.5, 4, 4.5):
    report(f"macro_drop_atr<{thr}", [r for r in ROWS if r['macro_drop_atr'] < thr])

print("\n=== LEG DEPTH x BULL ===")
report("drop<4 & bull", [r for r in ROWS if r['macro_drop_atr'] < 4 and r['macro_bull'] == 1])
report("drop<4 & NOT bear", [r for r in ROWS if r['macro_drop_atr'] < 4 and r['macro_bear'] == 0])
report("drop<4 & bear", [r for r in ROWS if r['macro_drop_atr'] < 4 and r['macro_bear'] == 1])

print("\n=== DEEP-PULL-IN-UPTREND refine (bull & retr>=0.618) ===")
report("bull & retr>=0.618", [r for r in ROWS if r['macro_bull'] == 1 and r['macro_retr'] >= 0.618])
report("bull & retr>=0.786", [r for r in ROWS if r['macro_bull'] == 1 and r['macro_retr'] >= 0.786])
report("NOT bear & retr>=0.618", [r for r in ROWS if r['macro_bear'] == 0 and r['macro_retr'] >= 0.618])
report("bull & retr>=0.618 & drop<6", [r for r in ROWS if r['macro_bull'] == 1 and r['macro_retr'] >= 0.618 and r['macro_drop_atr'] < 6])

print("\n=== UNION / best combos ===")
report("drop<4 OR (bull & retr>=0.618)", [r for r in ROWS if r['macro_drop_atr'] < 4 or (r['macro_bull'] == 1 and r['macro_retr'] >= 0.618)])
# the cleanest single robust rule: drop<4. Add bull tilt
report("drop<4.5 & NOT bear", [r for r in ROWS if r['macro_drop_atr'] < 4.5 and r['macro_bear'] == 0])
report("drop<3 (very shallow)", [r for r in ROWS if r['macro_drop_atr'] < 3])

print("\n=== KNIFE CONFIRM (what to AVOID) ===")
report("drop>=4 & bear (knife)", [r for r in ROWS if r['macro_drop_atr'] >= 4 and r['macro_bear'] == 1])
report("complement of drop<4 (drop>=4)", [r for r in ROWS if r['macro_drop_atr'] >= 4])
