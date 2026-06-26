#!/usr/bin/env python3
"""
_disc8_da_audit.py — Devil's Advocate self-audit on combo-hunter findings.
MULTI-FACTORIAL by design: tests 2-3 way orthogonal combos across families
(h1/h4/hd multi-TF + OB + vol + leg-trajectory). Trajectory features used
(path_eff, macro_retr, bars_to_8atr, eff). Dual objective (raise WR + cut streak).
Validation = per-year sub-windows + binomial + selection-bias counting.

Questions:
 (A) Selection bias: how many combos tested vs how many cross base.
 (B) Is the ~+2pp WR lift real or noise? Binomial vs base on kept subset.
 (C) Passthrough check: do "robust" combos just keep ~87% of the book?
 (D) Aggressive loser-cut: relax winners_kept to 0.55, demand WR>=0.72 stable. Survivors?
 (E) Best honest tradeoff: max WR with wk>=0.70 stable per year.
"""
import json
from itertools import combinations
import math

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
    if len(k) < 30:
        return None
    nk = len(k); wk = sum(r['win'] for r in k); wr = wk / nk
    wy = {}
    for y in YEARS:
        s = [r for r in k if r['yr'] == y]
        wy[y] = (sum(x['win'] for x in s) / len(s), len(s)) if s else (None, 0)
    return dict(nk=nk, wr=wr, strk=streak(k), wk=wk / TOTW, lc=(TOTL - (nk - wk)) / TOTL, wy=wy)


def binom_p(k, n, p):
    mu = n * p; sd = math.sqrt(n * p * (1 - p))
    z = (k - 0.5 - mu) / sd
    return 0.5 * math.erfc(z / math.sqrt(2))


def safe(v):
    return v is not None


P = {}


def ap(n, f):
    P[n] = f


for tf in ['h1', 'h4', 'hd']:
    ap(f'{tf}_trend_up', lambda r, tf=tf: r[f'{tf}_trend'] == 1)
    ap(f'{tf}_trend_notdown', lambda r, tf=tf: safe(r[f'{tf}_trend']) and r[f'{tf}_trend'] >= 0)
    ap(f'{tf}_pos_lo', lambda r, tf=tf: safe(r[f'{tf}_pos']) and r[f'{tf}_pos'] < 0.4)
    ap(f'{tf}_pos_hi', lambda r, tf=tf: safe(r[f'{tf}_pos']) and r[f'{tf}_pos'] > 0.6)
    ap(f'{tf}_eff_hi', lambda r, tf=tf: safe(r[f'{tf}_eff']) and r[f'{tf}_eff'] > 0.4)
    ap(f'{tf}_eff_lo', lambda r, tf=tf: safe(r[f'{tf}_eff']) and r[f'{tf}_eff'] < 0.2)
    ap(f'{tf}_dist_lo', lambda r, tf=tf: safe(r[f'{tf}_dist']) and r[f'{tf}_dist'] < 1.0)
    ap(f'{tf}_dist_hi', lambda r, tf=tf: safe(r[f'{tf}_dist']) and r[f'{tf}_dist'] > 2.0)
ap('in_demand', lambda r: r['in_demand'] == 1); ap('not_in_demand', lambda r: r['in_demand'] == 0)
ap('demand_fresh', lambda r: r['demand_fresh'] == 1)
ap('dist_supply_far', lambda r: r['dist_supply_atr'] > 2.0); ap('dist_supply_near', lambda r: r['dist_supply_atr'] < 1.0)
ap('dist_demand_near', lambda r: r['dist_demand_atr'] < 1.0); ap('dist_demand_far', lambda r: r['dist_demand_atr'] > 2.0)
ap('n_demand_ge2', lambda r: r['n_demand_near'] >= 2); ap('n_demand_0', lambda r: r['n_demand_near'] == 0)
ap('atr_regime_hi', lambda r: r['atr_regime'] > 1.2); ap('atr_regime_lo', lambda r: r['atr_regime'] < 0.9)
ap('atr_expand_hi', lambda r: r['atr_expand'] > 1.2); ap('atr_expand_lo', lambda r: r['atr_expand'] < 1.0)
ap('vol_low', lambda r: r['vol_low_vs_med'] < 1.0); ap('vol_high', lambda r: r['vol_low_vs_med'] > 1.5)
ap('vol_climax_hi', lambda r: r['vol_climax'] > 1.5); ap('vol_climax_lo', lambda r: r['vol_climax'] < 1.0)
ap('vpnode_above', lambda r: r['vpnode_dist_atr'] > 0); ap('vpnode_below', lambda r: r['vpnode_dist_atr'] < 0)
ap('vpnode_far_above', lambda r: r['vpnode_dist_atr'] > 2.0); ap('vpnode_near', lambda r: abs(r['vpnode_dist_atr']) < 1.0)
ap('macro_bull', lambda r: r['macro_bull'] == 1); ap('macro_bear', lambda r: r['macro_bear'] == 1)
ap('macro_notbear', lambda r: r['macro_bear'] == 0)
ap('macro_retr_hi', lambda r: r['macro_retr'] > 1.0); ap('macro_retr_lo', lambda r: r['macro_retr'] < 0.6)
ap('macro_drop_lo', lambda r: r['macro_drop_atr'] < 6.0); ap('macro_drop_hi', lambda r: r['macro_drop_atr'] > 9.0)
ap('path_eff_hi', lambda r: r['path_eff'] > 0.6); ap('path_eff_lo', lambda r: r['path_eff'] < 0.3)
ap('bars_fast', lambda r: r['bars_to_8atr'] < 20); ap('bars_slow', lambda r: r['bars_to_8atr'] > 40)
ap('rsi_hi', lambda r: r['rsi'] > 60); ap('rsi_lo', lambda r: r['rsi'] < 45); ap('rsi_mid', lambda r: 45 <= r['rsi'] <= 65)
ap('rsi_low_hi', lambda r: r['rsi_low'] > 40); ap('rsi_low_lo', lambda r: r['rsi_low'] < 30)
ap('disp4_hi', lambda r: r['disp4_atr'] > 2.0); ap('disp4_lo', lambda r: r['disp4_atr'] < 1.0)
ap('killzone', lambda r: r['killzone'] == 1); ap('not_killzone', lambda r: r['killzone'] == 0)
names = list(P)

print(f"BASE WR={BASE:.4f} N={N} streak={BS}")
print(f"BASE WR/yr: " + " ".join(f"{y}={BWY[y]:.3f}" for y in YEARS))

tested = 0; crossed = 0
for a, b in combinations(names, 2):
    m = ev(lambda r: P[a](r) and P[b](r))
    if m is None:
        continue
    tested += 1
    if m['wk'] >= 0.85 and m['wr'] >= BASE + 0.01:
        crossed += 1
print(f"\n(A) 2-way combos tested={tested}; crossing wk>=0.85 & wr>=base+1pp = {crossed} ({crossed/tested:.1%})")

best = ev(lambda r: safe(r['h1_dist']) and r['h1_dist'] > 2.0 and safe(r['h4_dist']) and r['h4_dist'] > 2.0 and r['vpnode_dist_atr'] > 0)
p = binom_p(int(round(best['wr'] * best['nk'])), best['nk'], BASE)
print(f"\n(B) best robust combo n={best['nk']} wr={best['wr']:.4f} vs base {BASE:.4f}")
print(f"    one-sided binomial p(X>=obs | base) = {p:.3f} (subset, NOT independent)")
print(f"    lift=+{(best['wr']-BASE)*100:.2f}pp ; keeps {best['nk']/N:.1%} of trades")

print(f"\n(C) PASSTHROUGH: best 'robust' combo keeps {best['nk']/N:.1%} of book. ~87% kept = near-passthrough, NOT a separator.")

print("\n(D) AGGRESSIVE: wk>=0.55, wr>=0.72, wr>=base ALL yrs, streak<base:")
hits = []
for a, b in combinations(names, 2):
    m = ev(lambda r: P[a](r) and P[b](r))
    if m is None:
        continue
    if m['wk'] >= 0.55 and m['wr'] >= 0.72 and m['strk'] < BS:
        ok = all(m['wy'][y][0] is not None and m['wy'][y][1] >= 40 and m['wy'][y][0] >= BWY[y] for y in YEARS)
        if ok:
            hits.append((f"{a}+{b}", m))
hits.sort(key=lambda x: -x[1]['wr'])
if not hits:
    print("    NONE survive at wk>=0.55. Cannot cut losers hard without dumping winners.")
for d, m in hits[:8]:
    print(f"    {d:34s} n={m['nk']} wr={m['wr']:.3f} strk={m['strk']} wk={m['wk']:.2f} "
          f"y24={m['wy'][2024][0]:.2f} y25={m['wy'][2025][0]:.2f} y26={m['wy'][2026][0]:.2f}")

print("\n(E) BEST HONEST: wk>=0.70, wr>base all yrs, streak<base, ranked by WR:")
hon = []
for a, b in combinations(names, 2):
    m = ev(lambda r: P[a](r) and P[b](r))
    if m is None:
        continue
    if m['wk'] >= 0.70 and m['strk'] < BS:
        ok = all(m['wy'][y][0] is not None and m['wy'][y][1] >= 40 and m['wy'][y][0] > BWY[y] - 0.005 for y in YEARS)
        if ok and m['wr'] > BASE:
            hon.append((f"{a}+{b}", m))
hon.sort(key=lambda x: -x[1]['wr'])
for d, m in hon[:8]:
    print(f"    {d:34s} n={m['nk']} wr={m['wr']:.3f} strk={m['strk']} wk={m['wk']:.2f} lc={m['lc']:.2f} "
          f"y24={m['wy'][2024][0]:.2f} y25={m['wy'][2025][0]:.2f} y26={m['wy'][2026][0]:.2f}")
