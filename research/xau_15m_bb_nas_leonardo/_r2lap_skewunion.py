#!/usr/bin/env python3
"""R2 lapidacao - SKEW-EXHAUSTION UNION builder (contextual combos).
RAW-causal. Only r2_keep==1. win=R>0. Sort by low_t.
Key finding (from purepocket): sell_skew_mig>0 (SELL thinning = exhaustion) is NEUTRAL
alone but loser-dense when conditioned on overheating/vol/young-regime. Build a CUT-when
UNION of these contextual loser-pockets, optimize WR lift + streak while keeping >=85%
winners. Forward-greedy + exhaustive small unions over a CURATED candidate set.
"""
import json, itertools
from collections import defaultdict

ROWS = [json.loads(l) for l in open('dataset_r2refine.jsonl')]
KEPT = [r for r in ROWS if r['r2_keep'] == 1]
KEPT.sort(key=lambda r: r['low_t'])
for i, r in enumerate(KEPT): r['_i'] = i
N = len(KEPT); W_TOT = sum(r['win'] for r in KEPT); WR_BASE = 100*W_TOT/N
LOS_TOT = N - W_TOT; SENT = -10000000.0

def year_wr(rows):
    yr = defaultdict(lambda: [0,0])
    for r in rows: yr[r['yr']][0]+=1; yr[r['yr']][1]+=r['win']
    return {y:100*w/n for y,(n,w) in yr.items()}
YBASE = year_wr(KEPT)
def block_stat(rows):
    bl = defaultdict(lambda: [0,0])
    for r in rows: bl[r['block']][0]+=1; bl[r['block']][1]+=r['win']
    return {b:(n,100*w/n) for b,(n,w) in bl.items()}
BBASE = block_stat(KEPT); BLOCKS = sorted(BBASE)
def streak(rows):
    s=mx=0
    for r in rows:
        if r['win']==0: s+=1; mx=max(mx,s)
        else: s=0
    return mx
STREAK_BASE = streak(KEPT)

A = {
    'flow_dead':   lambda r: -2 < r['flow_accel'] <= 0,
    'flow_zero':   lambda r: r['flow_accel'] == 0,
    'flow_neg':    lambda r: r['flow_accel'] < 0,
    'bsr4_hot':    lambda r: r['buy_sell_ratio4'] > 5,
    'bsr4_vhot':   lambda r: r['buy_sell_ratio4'] > 7,
    'absorb':      lambda r: r['absorption'] == 1,
    'vol_hi':      lambda r: r['low_vol_rel'] > 1.37,
    'vol_xhi':     lambda r: r['low_vol_rel'] > 1.6,
    'reg_young':   lambda r: r['regime_age_h'] <= 25.2,
    'bsl_fresh':   lambda r: r['bars_since_lowest'] <= 44,
    'buyL':        lambda r: r['buy_L_recent'] == 1,
    'closepos_hi': lambda r: r['low_closepos'] > 0.85,
    'sd_zero':     lambda r: r['sell_decel'] == 0.0,
    'skew_pos':    lambda r: r['sell_skew_mig'] > 0,
    'ny_ovl':      lambda r: r['is_ny_overlap'] == 1,
}
def AND(*ks):
    fns = [A[k] for k in ks]
    return lambda r: all(f(r) for f in fns)

# CURATED contextual cut-pockets (the loser-dense interactions found)
POCKETS = {
    'vol_xhi&skew':      AND('vol_xhi','skew_pos'),      # 43.1
    'bsr4_vhot&skew':    AND('bsr4_vhot','skew_pos'),    # 47.8
    'bsr4_hot&skew':     AND('bsr4_hot','skew_pos'),     # 50.6
    'absorb&sd_zero':    AND('absorb','sd_zero'),        # 54.0
    'bsr4_vhot&vol_hi':  AND('bsr4_vhot','vol_hi'),      # 54.4
    'bss_mid&skew':      AND('bsr4_hot','skew_pos'),     # (alias-ish, keep distinct below)
    'vol_hi&sd_zero':    AND('vol_hi','sd_zero'),        # 54.7
    'reg_young&skew':    AND('reg_young','skew_pos'),    # 54.9
    'vol_hi&bsl_fresh':  AND('vol_hi','bsl_fresh'),      # 55.0
    'flow_zero&vol_hi':  AND('flow_zero','vol_hi'),      # 55.3
    'buyL&skew':         AND('buyL','skew_pos'),         # 55.5
    'flow_dead&vol_hi':  AND('flow_dead','vol_hi'),      # 56.4
    'absorb&bsl_fresh':  AND('absorb','bsl_fresh'),      # 56.7
    'flow_dead&absorb':  AND('flow_dead','absorb'),      # 56.9
    'absorb&skew':       AND('absorb','skew_pos'),       # 57.3
    'vol_xhi&sd_zero':   AND('vol_xhi','sd_zero'),       # 57.9
    'bsr4_vhot&absorb':  AND('bsr4_vhot','absorb'),
}
del POCKETS['bss_mid&skew']  # dup

def keep_after(fns):
    cut = set()
    for r in KEPT:
        if any(f(r) for f in fns): cut.add(r['_i'])
    return [r for r in KEPT if r['_i'] not in cut]

def evaluate(keep):
    nk=len(keep); wk=sum(r['win'] for r in keep); wr=100*wk/nk
    winK=100*wk/W_TOT; losC=100*(LOS_TOT-(nk-wk))/LOS_TOT
    yk=year_wr(keep); bk=block_stat(keep)
    nw=sum(1 for b in BLOCKS if b in bk and bk[b][1]>=BBASE[b][1]-1e-9)
    sk=streak(keep)
    robust=(wr>WR_BASE and all(y in yk and yk[y]>=YBASE[y]-1e-9 for y in YBASE)
            and winK>=85.0 and nw>=6 and sk<STREAK_BASE)
    return dict(nk=nk,wr=wr,streak=sk,winK=winK,losC=losC,yk=yk,nw=nw,robust=robust)

def fmt(nm, ev):
    yk=ev['yk']
    return (f"{nm}\n   n={ev['nk']} WR={ev['wr']:.2f} strk={ev['streak']} winK={ev['winK']:.1f}% "
            f"losC={ev['losC']:.1f}% | y24={yk.get(2024,0):.1f}(b{YBASE[2024]:.1f}) "
            f"y25={yk.get(2025,0):.1f}(b{YBASE[2025]:.1f}) y26={yk.get(2026,0):.1f}(b{YBASE[2026]:.1f}) "
            f"nw={ev['nw']}/8 R={ev['robust']}")

names = list(POCKETS)
print(f"BASE n={N} WR={WR_BASE:.2f} strk={STREAK_BASE} y24={YBASE[2024]:.1f} y25={YBASE[2025]:.1f} y26={YBASE[2026]:.1f}")

results = []
for k in (1,2,3):
    for combo in itertools.combinations(names, k):
        fns = [POCKETS[c] for c in combo]
        ev = evaluate(keep_after(fns))
        if ev['wr'] > WR_BASE and ev['winK'] >= 85.0:
            results.append(("cut[" + " | ".join(combo) + "]", ev, k))

# rank: robust first, then highest WR, then lowest streak
results.sort(key=lambda x: (-x[1]['robust'], -x[1]['wr'], x[1]['streak']))
print(f"\n=== {len(results)} combos with WR>base & winK>=85 (top 30) ===")
for nm, ev, k in results[:30]:
    print(fmt(nm, ev))

robs = [(nm,ev) for nm,ev,k in results if ev['robust']]
print(f"\n=== ROBUST=TRUE ({len(robs)}) ===")
for nm, ev in sorted(robs, key=lambda x:(x[1]['streak'], -x[1]['wr'])):
    print(fmt(nm, ev))
