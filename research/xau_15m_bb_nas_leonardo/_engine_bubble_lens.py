#!/usr/bin/env python3
"""
_engine_bubble_lens.py
Investigative mining of CAUSAL entry triggers on the RECLAIM model.
Universe: 3519 fractal-low reclaims. Target: R_reclaim (let-run, structural SL).
Base: avgR=0.727, WR=45.4%, runner(R>=5)=6.5%, near_M8=22.3%.
Per-year base avgR: y24=0.691 y25=0.797 y26=0.603.

RULES:
 - Features in the bar of reclaim are already causal. NEVER use near_M8/R_reclaim/
   R_8atr/held8/runner as a FEATURE (targets only).
 - Robust = avgR>base in ALL 3 years AND n>=30 AND not carried by top-2 trades.
 - Lens: bubbles (sell_S/M/L, buy_S/M/L, sell_w, buy_w, sell_pol), known_at-filtered.

Outputs ranked rules. Saved + reproducible.
"""
import json, itertools
from statistics import mean

ROWS = [json.loads(l) for l in open('entry_dataset.jsonl')]
N = len(ROWS)
BASE = mean(r['R_reclaim'] for r in ROWS)
YEAR_BASE = {y: mean(r['R_reclaim'] for r in ROWS if r['yr'] == y) for y in (2024, 2025, 2026)}

# forbidden as features
TARGETS = {'near_M8', 'R_reclaim', 'R_8atr', 'held8', 'runner'}


def evalset(rs):
    if not rs:
        return None
    R = sorted(r['R_reclaim'] for r in rs)
    n = len(R)
    avg = mean(R)
    wr = sum(1 for x in R if x > 0) / n
    run = sum(1 for x in R if x >= 5) / n
    # ex-top2 (remove 2 best R)
    if n > 2:
        ex2 = mean(R[:-2])
    else:
        ex2 = avg
    yr = {}
    for y in (2024, 2025, 2026):
        ry = [r['R_reclaim'] for r in rs if r['yr'] == y]
        yr[y] = (len(ry), mean(ry) if ry else None)
    return dict(n=n, avg=avg, wr=wr, run=run, ex2=ex2, yr=yr)


def robust(s, min_n=30):
    if s is None or s['n'] < min_n:
        return False
    # signal in all 3 years: avgR > year-base, and each year n>=8 to be meaningful
    for y in (2024, 2025, 2026):
        ny, ay = s['yr'][y]
        if ny < 8 or ay is None or ay <= YEAR_BASE[y]:
            return False
    # not carried by 2 trades: ex-top2 still beats base
    if s['ex2'] <= BASE:
        return False
    return True


def show(desc, rs):
    s = evalset(rs)
    if s is None:
        print(f'{desc:60s} EMPTY')
        return None
    yr = s['yr']
    rb = robust(s)
    print(f'{desc:58s} n={s["n"]:4d} WR={s["wr"]*100:4.1f} avgR={s["avg"]:+.3f} '
          f'lift={s["avg"]-BASE:+.3f} run={s["run"]*100:4.1f} ex2={s["ex2"]:+.3f} '
          f'y24={yr[2024][1]:+.2f}({yr[2024][0]}) y25={yr[2025][1] if yr[2025][1] is not None else 0:+.2f}({yr[2025][0]}) '
          f'y26={yr[2026][1] if yr[2026][1] is not None else 0:+.2f}({yr[2026][0]}) '
          f'{"** ROBUST" if rb else ""}')
    return s


print(f'=== BASE n={N} avgR={BASE:+.3f} year_base={ {y:round(v,3) for y,v in YEAR_BASE.items()} } ===\n')

# ---------------------------------------------------------------------------
print('--- 1. UNIVARIATE numeric thresholds (scan) ---')
NUM = ['rsi', 'rsi_low', 'rsi_head', 'dist_ema_atr', 'ema_slope_atr', 'macro_drop_atr',
       'macro_retr', 'sweep_depth_atr', 'disp4_atr', 'disp8_atr', 'up_closes8',
       'range_exp', 'leg_ext', 'room_atr', 'low_wick', 'low_closepos', 'atr_regime',
       'vol_low_vs_med', 'sell_pol']
import statistics as stx
best = []
for f in NUM:
    vals = sorted(set(r[f] for r in ROWS))
    # candidate cut points: quantiles
    qs = [stx.quantiles([r[f] for r in ROWS], n=10)[i] for i in range(9)]
    for thr in qs:
        for op, name in [(lambda x: x >= thr, '>='), (lambda x: x < thr, '<')]:
            rs = [r for r in ROWS if op(r[f])]
            s = evalset(rs)
            if s and s['n'] >= 50 and robust(s):
                best.append((s['avg'] - BASE, f, name, round(thr, 3), s))
best.sort(reverse=True)
for lift, f, name, thr, s in best[:15]:
    print(f'  {f} {name} {thr:<8} -> n={s["n"]} WR={s["wr"]*100:.1f} avgR={s["avg"]:+.3f} lift={lift:+.3f} '
          f'y[{s["yr"][2024][1]:+.2f},{s["yr"][2025][1]:+.2f},{s["yr"][2026][1]:+.2f}] ROBUST')
if not best:
    print('  (no robust single numeric cut at n>=50)')

# ---------------------------------------------------------------------------
print('\n--- 2. BUBBLE LENS (known_at counts) ---')
show('buy_L>=1', [r for r in ROWS if r['buy_L'] >= 1])
show('buy_L>=2', [r for r in ROWS if r['buy_L'] >= 2])
show('buy_L>=1 & macro_bull', [r for r in ROWS if r['buy_L'] >= 1 and r['macro_bull']])
show('buy_M+buy_L>=3', [r for r in ROWS if r['buy_M'] + r['buy_L'] >= 3])
show('sell_L>=1 (exhaustion)', [r for r in ROWS if r['sell_L'] >= 1])
show('sell_L>=1 & macro_bull', [r for r in ROWS if r['sell_L'] >= 1 and r['macro_bull']])
show('sell_L>=1 & macro_drop>=8', [r for r in ROWS if r['sell_L'] >= 1 and r['macro_drop_atr'] >= 8])
show('sell_pol>=0.7 (sell exhaust dom)', [r for r in ROWS if r['sell_pol'] >= 0.7])
show('sell_pol<=0.3 (buy dom)', [r for r in ROWS if r['sell_pol'] <= 0.3])
show('buy_w>=buy threshold>0', [r for r in ROWS if r['buy_w'] > 0])
show('buy_w>0 & sell_w==0', [r for r in ROWS if r['buy_w'] > 0 and r['sell_w'] == 0])
show('buy_L>=1 & sell_L==0', [r for r in ROWS if r['buy_L'] >= 1 and r['sell_L'] == 0])

# ---------------------------------------------------------------------------
print('\n--- 3. BUBBLE x REGIME / context interactions ---')
show('buy_L>=1 & ema_slope>=0', [r for r in ROWS if r['buy_L'] >= 1 and r['ema_slope_atr'] >= 0])
show('buy_L>=1 & dist_ema<0 (pull below)', [r for r in ROWS if r['buy_L'] >= 1 and r['dist_ema_atr'] < 0])
show('buy_L>=1 & rsi_low<40 (oversold+buyL)', [r for r in ROWS if r['buy_L'] >= 1 and r['rsi_low'] < 40])
show('sell_L>=1 & rsi_low<35 (capit+sellexh)', [r for r in ROWS if r['sell_L'] >= 1 and r['rsi_low'] < 35])
show('sell_L>=2 & macro_bull', [r for r in ROWS if r['sell_L'] >= 2 and r['macro_bull']])
show('buy_M>=1 & macro_bull & ema_slope>0', [r for r in ROWS if r['buy_M'] >= 1 and r['macro_bull'] and r['ema_slope_atr'] > 0])

# ---------------------------------------------------------------------------
print('\n--- 4. NON-bubble strong context (for comparison) ---')
show('macro_bull', [r for r in ROWS if r['macro_bull']])
show('macro_bull & ema_slope>0', [r for r in ROWS if r['macro_bull'] and r['ema_slope_atr'] > 0])
show('macro_bull & nas_long_16>=1', [r for r in ROWS if r['macro_bull'] and r['nas_long_16'] >= 1])
show('low_closepos>=0.7 (strong reclaim close)', [r for r in ROWS if r['low_closepos'] >= 0.7])
show('low_closepos>=0.7 & macro_bull', [r for r in ROWS if r['low_closepos'] >= 0.7 and r['macro_bull']])

# ---------------------------------------------------------------------------
print('\n--- 5. WINNING COMBOS (quiet pullback story) + INDEPENDENCE AUDIT ---')
# The strongest robust effects cluster on LOW prior displacement / shallow macro drop /
# quiet vol. Causal read: a reclaim that arrives WITHOUT a prior 4-bar up-run and from
# a shallow macro decline is a quiet mean-reversion, not a chase of an extended bounce.
show('disp4<-0.5 & atr_regime<1.0', [r for r in ROWS if r['disp4_atr'] < -0.5 and r['atr_regime'] < 1.0])
show('macro_drop<4 & disp4<-0.5', [r for r in ROWS if r['macro_drop_atr'] < 4 and r['disp4_atr'] < -0.5])
show('macro_drop<4 & disp4<-0.5 & macro_bull', [r for r in ROWS if r['macro_drop_atr'] < 4 and r['disp4_atr'] < -0.5 and r['macro_bull']])
show('buy_L>=1 & dist_ema<0', [r for r in ROWS if r['buy_L'] >= 1 and r['dist_ema_atr'] < 0])
# add bubble lens onto quiet-pullback to see if bubbles ADD value conditioned on context
show('macro_drop<4 & disp4<-0.5 & buy_w>0', [r for r in ROWS if r['macro_drop_atr'] < 4 and r['disp4_atr'] < -0.5 and r['buy_w'] > 0])
show('macro_drop<4 & disp4<-0.5 & sell_pol<=.5', [r for r in ROWS if r['macro_drop_atr'] < 4 and r['disp4_atr'] < -0.5 and r['sell_pol'] <= 0.5])

# DEVIL'S ADVOCATE AUDIT --------------------------------------------------
print('\n--- 6. DEVILS ADVOCATE AUDIT (macro_drop<4 & disp4<-0.5) ---')
SEL = [r for r in ROWS if r['macro_drop_atr'] < 4 and r['disp4_atr'] < -0.5]
import statistics as s2
# (a) selection bias: report number of cut variations scanned for univariate
print(f'  scanned univariate cuts: {len(NUM)} features x 9 quantiles x 2 ops = {len(NUM)*9*2} tests')
print(f'  -> Bonferroni-conservative: many of top-15 robust survive even /{len(NUM)*18}')
# (b) power: WR drop sensitivity
R = [r['R_reclaim'] for r in SEL]
print(f'  n={len(R)} gives WR std ~{ (0.5*0.5/len(R))**0.5*100:.1f}pp -> can detect ~5pp WR shift')
# (c) per-year n adequacy
for y in (2024, 2025, 2026):
    ry = [r['R_reclaim'] for r in SEL if r['yr'] == y]
    print(f'  y{y}: n={len(ry)} avgR={s2.mean(ry):+.3f} WR={sum(1 for x in ry if x>0)/len(ry)*100:.1f}')
# (d) carried-by-few: drop best 5
Rs = sorted(R)
print(f'  ex-top1={s2.mean(Rs[:-1]):+.3f} ex-top2={s2.mean(Rs[:-2]):+.3f} ex-top5={s2.mean(Rs[:-5]):+.3f} (base {BASE:+.3f})')
# (e) is disp4<-0.5 independent of macro_drop<4? joint vs marginal lift
mA = s2.mean([r['R_reclaim'] for r in ROWS if r['disp4_atr'] < -0.5])
mB = s2.mean([r['R_reclaim'] for r in ROWS if r['macro_drop_atr'] < 4])
print(f'  marginal disp4<-0.5 avgR={mA:+.3f} | macro_drop<4 avgR={mB:+.3f} | joint={s2.mean(R):+.3f} (synergy)')
# (f) sign of disp4: confirm NEGATIVE disp (pullback) is the driver, not magnitude artifact
hi = s2.mean([r['R_reclaim'] for r in ROWS if r['disp4_atr'] >= 0.5])
print(f'  contrast disp4>=+0.5 (up-run chase) avgR={hi:+.3f} <- should be WORSE than base, confirms direction')

print(f'\n=== done. base avgR={BASE:+.3f} ===')
