#!/usr/bin/env python3
"""R2 lapidacao - PURE-POCKET interaction miner.
RAW-causal. Only r2_keep==1. win=R>0. Sort by low_t.
Hunt INTERACTION cut-pockets: 2-feature conjunctions that are unusually loser-dense
(low WR) yet small (preserve >=85% winners). Contextual reading: a feature weak alone
becomes strong conditioned on another. Then build best UNION rule.
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
    yr = defaultdict(lambda: [0, 0])
    for r in rows: yr[r['yr']][0]+=1; yr[r['yr']][1]+=r['win']
    return {y: 100*w/n for y,(n,w) in yr.items()}
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

# Atomic boolean conditions (each a candidate slice). Contextual building blocks.
ATOMS = {
    'flow_dead':   lambda r: -2 < r['flow_accel'] <= 0,
    'flow_neg':    lambda r: r['flow_accel'] < 0,
    'flow_zero':   lambda r: r['flow_accel'] == 0,
    'bsr4_hot':    lambda r: r['buy_sell_ratio4'] > 5,
    'bsr4_vhot':   lambda r: r['buy_sell_ratio4'] > 7,
    'absorb':      lambda r: r['absorption'] == 1,
    'vol_hi':      lambda r: r['low_vol_rel'] > 1.37,
    'vol_xhi':     lambda r: r['low_vol_rel'] > 1.6,
    'reg_young':   lambda r: r['regime_age_h'] <= 25.2,
    'bsl_fresh':   lambda r: r['bars_since_lowest'] <= 44,
    'buyL':        lambda r: r['buy_L_recent'] == 1,
    'closepos_hi': lambda r: r['low_closepos'] > 0.85,
    'smc_lagmid':  lambda r: 1 < r['smc_lag_bars'] <= 4,
    'sd_zero':     lambda r: r['sell_decel'] == 0.0,
    'sd_sent':     lambda r: r['sell_decel'] == SENT,
    'bss_mid':     lambda r: 40 < r['bars_since_sell'] <= 99,
    'ny_ovl':      lambda r: r['is_ny_overlap'] == 1,
    'london':      lambda r: r['is_london_open'] == 1,
    'deadzone':    lambda r: r['is_deadzone'] == 1,
    'skew_pos':    lambda r: r['sell_skew_mig'] > 0,
    'buyaftersmc': lambda r: r['buy_after_smc'] == 1,
}

def slice_stat(fn):
    g = [r for r in KEPT if fn(r)]
    if not g: return (0, 100.0, 0)
    w = sum(r['win'] for r in g)
    return (len(g), 100*w/len(g), len(g)-w)

names = list(ATOMS)
print(f"BASE n={N} WR={WR_BASE:.2f} strk={STREAK_BASE} y24={YBASE[2024]:.1f} y25={YBASE[2025]:.1f} y26={YBASE[2026]:.1f}")

# 2-way interaction pockets: lowest WR, require min size and loser enrichment
print("\n=== 2-WAY CUT-POCKETS (sorted by WR asc, n>=60) ===")
pk = []
for a, b in itertools.combinations(names, 2):
    fa, fb = ATOMS[a], ATOMS[b]
    fn = lambda r, fa=fa, fb=fb: fa(r) and fb(r)
    n, wr, l = slice_stat(fn)
    if n >= 60:
        pk.append((f"{a}&{b}", n, wr, l, fn))
pk.sort(key=lambda x: x[2])
for nm, n, wr, l, fn in pk[:30]:
    print(f"{nm:28s} n={n} WR={wr:.1f} losers={l} lift={l/n - (LOS_TOT/N):.3f}")

# Build best UNION of up to 3 lowest-WR pockets respecting winners_kept>=85
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
    return (f"{nm}: n={ev['nk']} WR={ev['wr']:.2f} strk={ev['streak']} winK={ev['winK']:.1f}% "
            f"losC={ev['losC']:.1f}% y24={yk.get(2024,0):.1f} y25={yk.get(2025,0):.1f} "
            f"y26={yk.get(2026,0):.1f} nw={ev['nw']}/8 R={ev['robust']}")

# candidate pockets = lowest-WR with WR < 62 (strongly loser-dense)
cand = [(nm, fn) for nm, n, wr, l, fn in pk if wr < 63]
print(f"\n=== {len(cand)} strong pockets (WR<63). UNION search 1-3 ===")
best = []
for k in (1, 2, 3):
    for combo in itertools.combinations(range(len(cand)), k):
        fns = [cand[i][1] for i in combo]
        ev = evaluate(keep_after(fns))
        if ev['wr'] > WR_BASE and ev['winK'] >= 85.0:
            nm = "cut[" + "|".join(cand[i][0] for i in combo) + "]"
            best.append((nm, ev))
best.sort(key=lambda x: (-x[1]['robust'], -x[1]['wr']))
for nm, ev in best[:25]: print(fmt(nm, ev))
print("\n=== ROBUST ===")
for nm, ev in best:
    if ev['robust']: print(fmt(nm, ev))
print(f"#robust={sum(1 for _,e in best if e['robust'])}")
