#!/usr/bin/env python3
"""
_disc8_devils_advocate.py — adversarial audit of the top RANGE-vs-TREND combos.

Mandated DA questions:
 1. Look-ahead: hd_/h4_ are HTF closed-bar-only by dataset construction (stated).
    We cannot re-derive here, but we test STRUCTURAL robustness instead:
 2. In-sample tuning: thresholds were chosen on this data -> test threshold
    sensitivity (+/- perturbation) to see if edge is a knife-edge fit.
 3. Selection/Bonferroni: 680 combos tested. Report how many beat base by chance.
 4. Power: per-year n and Wilson lower bound.
 5. Loader check: is the WR carried by a few blocks? Leave-one-block-out.
 6. Robustness: per-block WR full table for the finalist combos.

win=R>0. RAW-causal. Saved + reproducible.
"""
import json, itertools, math

ROWS = [json.loads(l) for l in open('dataset_8atr.jsonl')]
N = len(ROWS)
BASE_WR = sum(r['win'] for r in ROWS) / N
YEARS = [2024, 2025, 2026]
SORTED = sorted(ROWS, key=lambda r: r['low_t'])
TOTAL_WINNERS = sum(r['win'] for r in ROWS)
TOTAL_LOSERS = N - TOTAL_WINNERS


def g(r, k, d):
    v = r.get(k); return d if v is None else v


def wr(rows):
    return sum(r['win'] for r in rows) / len(rows) if rows else 0.0


def max_losing_streak(rows):
    mx = cur = 0
    for r in rows:
        if r['win'] == 0:
            cur += 1; mx = max(mx, cur)
        else:
            cur = 0
    return mx


def wilson_lower(k, n, z=1.96):
    if n == 0: return 0.0
    p = k / n
    d = 1 + z*z/n
    c = p + z*z/(2*n)
    m = z*math.sqrt(p*(1-p)/n + z*z/(4*n*n))
    return (c - m)/d


# ---------- finalist predicates (parametrized for sensitivity) ----------
def make_pred(hd_eff_min, h4_lo, h4_hi):
    return lambda r: (g(r, 'hd_eff', 0) >= hd_eff_min
                      and h4_lo <= g(r, 'h4_eff', 0) <= h4_hi)


FINALISTS = {
    'A_hd.2_h4[.2,.45]': make_pred(0.2, 0.2, 0.45),   # tightest top combo
    'B_hd.1_h4[.2,.45]': make_pred(0.1, 0.2, 0.45),   # broader, more trades
    'C_hd.2_h4[.1,.45]': make_pred(0.2, 0.1, 0.45),   # h4_eff_mid alone w/ hd
}


def report(name, pred):
    kept = [r for r in SORTED if pred(r)]
    n = len(kept); w = sum(r['win'] for r in kept)
    print(f"\n=== {name}  n={n} WR={wr(kept):.4f} "
          f"Wilson95lo={wilson_lower(w,n):.3f} streak={max_losing_streak(kept)} "
          f"winners_kept={w}/{TOTAL_WINNERS}={w/TOTAL_WINNERS:.2f} "
          f"losers_cut={(TOTAL_LOSERS-(n-w))/TOTAL_LOSERS:.2f} ===")
    # per year
    for y in YEARS:
        sub = [r for r in kept if r['yr'] == y]
        k2 = sum(r['win'] for r in sub)
        print(f"   y{y}: n={len(sub):4d} WR={wr(sub):.3f} Wilson95lo={wilson_lower(k2,len(sub)):.3f}")
    # per block
    blocks = {}
    for r in kept:
        blocks.setdefault(r['block'], []).append(r)
    print("   per-block:", {b: (round(wr(v),3), len(v)) for b, v in sorted(blocks.items())})
    # leave-one-block-out: min WR when dropping each block
    allblocks = sorted(set(r['block'] for r in ROWS))
    loo = []
    for drop in allblocks:
        sub = [r for r in kept if r['block'] != drop]
        loo.append((drop, round(wr(sub), 4)))
    print("   leave-one-block-out WR:", loo)
    below = [b for b, v in blocks.items() if len(v) >= 12 and wr(v) < BASE_WR]
    print(f"   blocks(n>=12) below base WR: {below}")


print(f"BASE WR={BASE_WR:.4f} N={N} winners={TOTAL_WINNERS} losers={TOTAL_LOSERS}  base_streak={max_losing_streak(SORTED)}")

for name, pred in FINALISTS.items():
    report(name, pred)

# ---------- DA Q2: threshold sensitivity grid on combo A ----------
print("\n--- THRESHOLD SENSITIVITY (knife-edge check) on hd_eff_min x h4 band ---")
print(f"{'hd_min':6} {'h4_lo':5} {'h4_hi':5} {'n':5} {'WR':6} {'y24':5} {'y25':5} {'y26':5}")
for hd_min in [0.05, 0.1, 0.15, 0.2, 0.25]:
    for h4_lo, h4_hi in [(0.15, 0.45), (0.2, 0.45), (0.2, 0.5), (0.1, 0.4)]:
        pred = make_pred(hd_min, h4_lo, h4_hi)
        kept = [r for r in SORTED if pred(r)]
        if len(kept) < 200: continue
        ys = {}
        for y in YEARS:
            sub = [r for r in kept if r['yr'] == y]; ys[y] = wr(sub)
        print(f"{hd_min:6} {h4_lo:5} {h4_hi:5} {len(kept):5d} {wr(kept):.3f}  "
              f"{ys[2024]:.3f} {ys[2025]:.3f} {ys[2026]:.3f}")

# ---------- DA Q3: selection — null permutation ----------
# How many of 680-ish 2/3-combos beat base purely by chance with this WR margin?
# Quick proxy: shuffle win labels, recount how many combos exceed WR 0.73 at n>=150.
import random
random.seed(7)
P = {
    'hd_eff_hi2': lambda r: g(r,'hd_eff',0)>=0.2, 'hd_eff_hi': lambda r: g(r,'hd_eff',0)>=0.1,
    'h4_eff_mid': lambda r: 0.1<=g(r,'h4_eff',0)<=0.45, 'h4_eff_hi': lambda r: g(r,'h4_eff',0)>=0.2,
    'h1_eff_hi': lambda r: g(r,'h1_eff',0)>=0.2, 'slow_grind': lambda r: g(r,'bars_to_8atr',0)>=25,
    'low_patheff3': lambda r: g(r,'path_eff',1)<=0.3, 'atr_hi': lambda r: g(r,'atr_regime',1)>=1.2,
    'h1_up': lambda r: g(r,'h1_trend',0)==1, 'rsi_not_hot': lambda r: g(r,'rsi',50)<=70,
}
keys = list(P.keys())
combos = list(itertools.combinations(keys,2))+list(itertools.combinations(keys,3))
def count_above(rows, thr=0.73):
    c=0
    for cb in combos:
        fns=[P[k] for k in cb]
        kept=[r for r in rows if all(f(r) for f in fns)]
        if len(kept)>=150 and wr(kept)>=thr: c+=1
    return c
real=count_above(ROWS)
nulls=[]
for _ in range(20):
    perm=[dict(r) for r in ROWS]
    wins=[r['win'] for r in ROWS]; random.shuffle(wins)
    for r,wv in zip(perm,wins): r['win']=wv
    nulls.append(count_above(perm))
print(f"\n--- SELECTION (null permutation) ---")
print(f"real combos with WR>=0.73 @n>=150: {real}")
print(f"null (shuffled win) combos >=0.73: mean={sum(nulls)/len(nulls):.1f} max={max(nulls)} dist={sorted(nulls)}")
