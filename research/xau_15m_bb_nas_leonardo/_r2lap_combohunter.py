#!/usr/bin/env python3
"""R2 lapidacao - COMBO HUNTER v2 (cut-pocket forward-selection, 2-3 combos).
RAW-causal. Only r2_keep==1. win=R>0. Sort by low_t for streak.
Strategy: keeping >=85% winners means cutting FEW rows -> hunt SMALL loser-dense
pockets and UNION them (cut-when A OR B OR C). Each pocket must be loser-dense.
"""
import json, itertools
from collections import defaultdict

ROWS = [json.loads(l) for l in open('dataset_r2refine.jsonl')]
KEPT = [r for r in ROWS if r['r2_keep'] == 1]
KEPT.sort(key=lambda r: r['low_t'])
for i, r in enumerate(KEPT): r['_i'] = i

N = len(KEPT)
W_TOT = sum(r['win'] for r in KEPT)
WR_BASE = 100*W_TOT/N
LOS_TOT = N - W_TOT
SENT = -10000000.0

def year_wr(rows):
    yr = defaultdict(lambda: [0, 0])
    for r in rows:
        yr[r['yr']][0] += 1; yr[r['yr']][1] += r['win']
    return {y: 100*w/n for y, (n, w) in yr.items()}
YBASE = year_wr(KEPT)

def block_stat(rows):
    bl = defaultdict(lambda: [0, 0])
    for r in rows:
        bl[r['block']][0] += 1; bl[r['block']][1] += r['win']
    return {b: (n, 100*w/n) for b, (n, w) in bl.items()}
BBASE = block_stat(KEPT)
BLOCKS = sorted(BBASE.keys())

def streak(rows):
    s = mx = 0
    for r in rows:
        if r['win'] == 0:
            s += 1; mx = max(mx, s)
        else:
            s = 0
    return mx
STREAK_BASE = streak(KEPT)

# CUT-pockets (cut-when True). Curated loser-dense slices from univariate read.
CUTS = {
    'flow_dead':    lambda r: -2 < r['flow_accel'] <= 0,                # dead curvature
    'bsr4_hot':     lambda r: r['buy_sell_ratio4'] > 5,                  # overheated buy ratio
    'bsr4_veryhot': lambda r: r['buy_sell_ratio4'] > 7,
    'absorb':       lambda r: r['absorption'] == 1,
    'vol_spike':    lambda r: r['low_vol_rel'] > 1.37,                   # top-Q vol
    'vol_extreme':  lambda r: r['low_vol_rel'] > 1.6,
    'regime_young': lambda r: r['regime_age_h'] <= 10.5,                # very fresh regime
    'regime_y2':    lambda r: 10.5 < r['regime_age_h'] <= 25.2,         # Q1 = worst (63.2)
    'bsl_fresh':    lambda r: r['bars_since_lowest'] <= 44,             # just made low
    'buyL':         lambda r: r['buy_L_recent'] == 1,
    'closepos_hi':  lambda r: r['low_closepos'] > 0.85,
    'smc_lag_mid':  lambda r: 1 < r['smc_lag_bars'] <= 4,              # Q1 worst (65.6)
    'selldecel_zero': lambda r: r['sell_decel'] == 0.0,                # flat decel Q0 64.9
    'bss_mid':      lambda r: 40 < r['bars_since_sell'] <= 99,         # 63.3 zone
    'flow_strong_neg': lambda r: r['flow_accel'] <= -20,
    'flow_pos_small': lambda r: 0 < r['flow_accel'] < 7,
}

def cut_density(cutfn):
    g = [r for r in KEPT if cutfn(r)]
    if not g: return (0, 0.0, 0)
    w = sum(r['win'] for r in g)
    return (len(g), 100*w/len(g), len(g)-w)

def keep_after(cutfns):
    cut_ids = set()
    for r in KEPT:
        if any(c(r) for c in cutfns):
            cut_ids.add(r['_i'])
    return [r for r in KEPT if r['_i'] not in cut_ids]

def evaluate(keep):
    if not keep: return None
    nk = len(keep)
    wk = sum(r['win'] for r in keep)
    wr = 100*wk/nk
    winners_kept_pct = 100*wk/W_TOT
    los_keep = nk - wk
    losers_cut_pct = 100*(LOS_TOT - los_keep)/LOS_TOT
    yk = year_wr(keep)
    bk = block_stat(keep)
    nw = sum(1 for b in BLOCKS if b in bk and bk[b][1] >= BBASE[b][1] - 1e-9)
    sk = streak(keep)
    robust = (wr > WR_BASE
              and all(y in yk and yk[y] >= YBASE[y] - 1e-9 for y in YBASE)
              and winners_kept_pct >= 85.0
              and nw >= 6
              and sk < STREAK_BASE)
    return dict(nk=nk, wr=wr, streak=sk, winners_kept_pct=winners_kept_pct,
                losers_cut_pct=losers_cut_pct, yk=yk, nw=nw, robust=robust)

def fmt(name, ev):
    yk = ev['yk']
    return (f"{name}: n={ev['nk']} WR={ev['wr']:.2f} strk={ev['streak']} "
            f"winK={ev['winners_kept_pct']:.1f}% losC={ev['losers_cut_pct']:.1f}% "
            f"y24={yk.get(2024,0):.1f} y25={yk.get(2025,0):.1f} y26={yk.get(2026,0):.1f} "
            f"nw={ev['nw']}/8  R={ev['robust']}")

if __name__ == '__main__':
    print(f"BASE n={N} WR={WR_BASE:.2f} streak={STREAK_BASE} "
          f"y24={YBASE[2024]:.2f} y25={YBASE[2025]:.2f} y26={YBASE[2026]:.2f}")
    print("\n=== CUT-POCKET DENSITY (cut-when) ===")
    dens = {}
    for nm, fn in CUTS.items():
        n, w, l = cut_density(fn)
        dens[nm] = (n, w, l)
        print(f"{nm:18s} cut_n={n} cut_WR={w:.1f} losers_in={l}")

    names = list(CUTS.keys())
    print("\n=== SINGLE CUTS (keep complement) ===")
    sing = []
    for nm in names:
        ev = evaluate(keep_after([CUTS[nm]]))
        if ev and ev['winners_kept_pct'] >= 85.0:
            sing.append((nm, ev))
    sing.sort(key=lambda x: (-x[1]['robust'], -x[1]['wr']))
    for nm, ev in sing: print(fmt(nm, ev))

    print("\n=== PAIR CUTS (cut A OR B) winK>=85 & WR>base ===")
    pairs = []
    for a, b in itertools.combinations(names, 2):
        ev = evaluate(keep_after([CUTS[a], CUTS[b]]))
        if ev and ev['wr'] > WR_BASE and ev['winners_kept_pct'] >= 85.0:
            pairs.append((f"cut[{a}|{b}]", ev))
    pairs.sort(key=lambda x: (-x[1]['robust'], -x[1]['wr']))
    for nm, ev in pairs[:30]: print(fmt(nm, ev))

    print("\n=== TRIPLE CUTS (cut A OR B OR C) winK>=85 & WR>base ===")
    trips = []
    for a, b, c in itertools.combinations(names, 3):
        ev = evaluate(keep_after([CUTS[a], CUTS[b], CUTS[c]]))
        if ev and ev['wr'] > WR_BASE and ev['winners_kept_pct'] >= 85.0:
            trips.append((f"cut[{a}|{b}|{c}]", ev))
    trips.sort(key=lambda x: (-x[1]['robust'], -x[1]['wr']))
    for nm, ev in trips[:30]: print(fmt(nm, ev))

    print("\n=== ROBUST=TRUE ===")
    allh = [(nm, ev) for nm, ev in sing + pairs + trips if ev['robust']]
    allh.sort(key=lambda x: -x[1]['wr'])
    for nm, ev in allh: print(fmt(nm, ev))
    print(f"\n#robust={len(allh)}")
