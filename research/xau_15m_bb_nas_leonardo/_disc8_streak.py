#!/usr/bin/env python3
"""
_disc8_streak.py — focused angle: can ANY combo cut the max-losing-streak
meaningfully (<=20) while keeping >=85% winners AND wr>=base every year?
The base streak=28 is the killer for a 66%-WR system. Search combos ranked
by streak reduction subject to winners_kept>=0.85.
Multi-factorial: 2-3 way across families. Validation = per-year stability.
"""
import json
from itertools import combinations

ROWS = [json.loads(l) for l in open('dataset_8atr.jsonl')]
ROWS.sort(key=lambda r: r['low_t'])
N = len(ROWS); TOTW = sum(r['win'] for r in ROWS); TOTL = N - TOTW
BASE = TOTW / N; YEARS = [2024, 2025, 2026]
BWY = {y: (lambda s: sum(x['win'] for x in s) / len(s))([r for r in ROWS if r['yr'] == y]) for y in YEARS}


def streak(rows):
    mx = cur = 0
    for r in rows:
        if r['win'] == 0:
            cur += 1; mx = max(mx, cur)
        else:
            cur = 0
    return mx


BS = streak(ROWS)


def ev(fn):
    k = [r for r in ROWS if fn(r)]
    if len(k) < 100:
        return None
    nk = len(k); wk = sum(r['win'] for r in k); wr = wk / nk
    wy = {}
    for y in YEARS:
        s = [r for r in k if r['yr'] == y]
        wy[y] = (sum(x['win'] for x in s) / len(s), len(s)) if s else (None, 0)
    return dict(nk=nk, wr=wr, strk=streak(k), wk=wk / TOTW, lc=(TOTL - (nk - wk)) / TOTL, wy=wy)


def safe(v):
    return v is not None


P = {}


def ap(n, f):
    P[n] = f


for tf in ['h1', 'h4', 'hd']:
    ap(f'{tf}_trend_up', lambda r, tf=tf: r[f'{tf}_trend'] == 1)
    ap(f'{tf}_trend_notdown', lambda r, tf=tf: safe(r[f'{tf}_trend']) and r[f'{tf}_trend'] >= 0)
    ap(f'{tf}_pos_hi', lambda r, tf=tf: safe(r[f'{tf}_pos']) and r[f'{tf}_pos'] > 0.6)
    ap(f'{tf}_eff_hi', lambda r, tf=tf: safe(r[f'{tf}_eff']) and r[f'{tf}_eff'] > 0.4)
    ap(f'{tf}_dist_hi', lambda r, tf=tf: safe(r[f'{tf}_dist']) and r[f'{tf}_dist'] > 2.0)
ap('in_demand', lambda r: r['in_demand'] == 1)
ap('demand_fresh', lambda r: r['demand_fresh'] == 1)
ap('dist_supply_far', lambda r: r['dist_supply_atr'] > 2.0)
ap('atr_regime_lo', lambda r: r['atr_regime'] < 0.9)
ap('atr_expand_lo', lambda r: r['atr_expand'] < 1.0)
ap('vol_low', lambda r: r['vol_low_vs_med'] < 1.0)
ap('vpnode_above', lambda r: r['vpnode_dist_atr'] > 0)
ap('vpnode_far_above', lambda r: r['vpnode_dist_atr'] > 2.0)
ap('macro_notbear', lambda r: r['macro_bear'] == 0)
ap('macro_retr_hi', lambda r: r['macro_retr'] > 1.0)
ap('path_eff_lo', lambda r: r['path_eff'] < 0.3)
ap('bars_slow', lambda r: r['bars_to_8atr'] > 40)
ap('rsi_hi', lambda r: r['rsi'] > 60)
ap('rsi_mid', lambda r: 45 <= r['rsi'] <= 65)
ap('not_killzone', lambda r: r['killzone'] == 0)
names = list(P)

print(f"BASE WR={BASE:.4f} streak={BS}  BASE/yr " + " ".join(f"{y}={BWY[y]:.3f}" for y in YEARS))

print("\n=== Streak-cut combos: wk>=0.85, streak<=20, wr>=base all yrs ===")
res = []
combos = [(a,) for a in names] + list(combinations(names, 2)) + list(combinations(names, 3))
for cb in combos:
    fns = [P[x] for x in cb]
    m = ev(lambda r, fns=fns: all(f(r) for f in fns))
    if m is None:
        continue
    if m['wk'] >= 0.85 and m['strk'] <= 20:
        ok = all(m['wy'][y][0] is not None and m['wy'][y][0] >= BWY[y] - 0.005 for y in YEARS)
        if ok and m['wr'] >= BASE:
            res.append(('+'.join(cb), m))
res.sort(key=lambda x: (x[1]['strk'], -x[1]['wr']))
if not res:
    print("  NONE: cannot get streak<=20 while keeping >=85% winners + per-yr stable.")
for d, m in res[:15]:
    print(f"  {d:42s} n={m['nk']} wr={m['wr']:.3f} strk={m['strk']} wk={m['wk']:.2f} lc={m['lc']:.2f} "
          f"y24={m['wy'][2024][0]:.2f} y25={m['wy'][2025][0]:.2f} y26={m['wy'][2026][0]:.2f}")

print("\n=== Relaxed: wk>=0.80, streak<=22, wr>=base all yrs ===")
res2 = []
for cb in combos:
    fns = [P[x] for x in cb]
    m = ev(lambda r, fns=fns: all(f(r) for f in fns))
    if m is None:
        continue
    if m['wk'] >= 0.80 and m['strk'] <= 22:
        ok = all(m['wy'][y][0] is not None and m['wy'][y][0] >= BWY[y] - 0.005 for y in YEARS)
        if ok and m['wr'] >= BASE:
            res2.append(('+'.join(cb), m))
res2.sort(key=lambda x: (x[1]['strk'], -x[1]['wr']))
for d, m in res2[:15]:
    print(f"  {d:42s} n={m['nk']} wr={m['wr']:.3f} strk={m['strk']} wk={m['wk']:.2f} lc={m['lc']:.2f} "
          f"y24={m['wy'][2024][0]:.2f} y25={m['wy'][2025][0]:.2f} y26={m['wy'][2026][0]:.2f}")
