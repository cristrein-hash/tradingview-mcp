#!/usr/bin/env python3
"""
_engine_combo_hunter.py
Combo-hunter for XAU 15M reclaim entries.
Lens: COMBOS of 2-3 features across families that jointly separate winners
(avgR/runner) with stability across 2024/2025/2026.

RULES:
 - Features are causal (bar of reclaim). NEVER use near_M8/R_reclaim/R_8atr/held8/runner as feature.
 - Report n, WR, avgR, avgR per year (y24/y25/y26), lift, robust.
 - robust = avgR>base in all 3 years AND n>=30 AND not carried by ex-top2.
 - Distrust rules carried by 1-2 trades (check ex-top2).
"""
import json, itertools
from collections import defaultdict

ROWS = [json.loads(l) for l in open('entry_dataset.jsonl')]
N = len(ROWS)
TARGET = 'R_reclaim'
BASE = sum(r[TARGET] for r in ROWS) / N
RESULT_KEYS = {'R_reclaim','held8','runner','R_8atr','near_M8'}
META_KEYS = {'block','low_t','yr','low_idx','reclaim_idx'}
FEATKEYS = [k for k in ROWS[0] if k not in RESULT_KEYS and k not in META_KEYS]

def stats(sub):
    if not sub:
        return None
    n = len(sub)
    R = [r[TARGET] for r in sub]
    avg = sum(R)/n
    wr = sum(1 for x in R if x>0)/n*100
    run = sum(1 for x in R if x>=5)
    d = {}
    for y in (2024,2025,2026):
        ys = [r[TARGET] for r in sub if r['yr']==y]
        d[y] = (len(ys), sum(ys)/len(ys) if ys else None)
    # ex-top2 by R
    Rs = sorted(R, reverse=True)
    extop2 = (sum(Rs[2:])/(n-2)) if n>2 else None
    return dict(n=n, wr=wr, avg=avg, run=run, runpct=run/n*100, yr=d, extop2=extop2)

def robust(s, base=BASE):
    if s is None or s['n'] < 30:
        return False
    for y in (2024,2025,2026):
        ny, ay = s['yr'][y]
        if ny < 5 or ay is None or ay <= base:
            return False
    # not carried by ex-top2
    if s['extop2'] is None or s['extop2'] <= base:
        return False
    return True

def fmt(name, s):
    if s is None:
        return f"{name}: EMPTY"
    yr = s['yr']
    ystr = " ".join(f"{y}:{(yr[y][1] if yr[y][1] is not None else float('nan')):+.2f}(n{yr[y][0]})" for y in (2024,2025,2026))
    rb = "ROBUST" if robust(s) else "weak"
    return (f"{name}: n={s['n']} WR={s['wr']:.0f}% avgR={s['avg']:+.3f} "
            f"lift={s['avg']-BASE:+.3f} run={s['run']}({s['runpct']:.0f}%) "
            f"exT2={s['extop2']:+.3f} | {ystr} [{rb}]")

# ---- candidate predicates per family (causal features only) ----
# We build named boolean predicates. Use a grid of thresholds informed by distributions.
import numpy as np
def col(k): return np.array([r[k] for r in ROWS], float)
def q(k, ps):
    a = col(k); return [round(float(np.nanquantile(a,p)),3) for p in ps]

# print distributions for threshold picking
DIST = {}
for k in FEATKEYS:
    a = col(k)
    DIST[k] = [round(float(np.nanquantile(a,p)),3) for p in (0.1,0.25,0.5,0.75,0.9)]

PRED = {}
# RSI family (oversold reclaim = mean-reversion fuel)
PRED['rsi_low<35'] = lambda r: r['rsi_low'] < 35
PRED['rsi_low<30'] = lambda r: r['rsi_low'] < 30
PRED['rsi<45'] = lambda r: r['rsi'] < 45
PRED['rsi_head>0.5'] = lambda r: r['rsi_head'] > 0.5   # rsi recovered from low
PRED['rsi_head>1.0'] = lambda r: r['rsi_head'] > 1.0
# EMA / location family (discount)
PRED['dist_ema<-0.5'] = lambda r: r['dist_ema_atr'] < -0.5  # below ema = discount
PRED['dist_ema<0'] = lambda r: r['dist_ema_atr'] < 0
PRED['dist_ema>0'] = lambda r: r['dist_ema_atr'] > 0  # above ema = momentum
PRED['ema_slope>0'] = lambda r: r['ema_slope_atr'] > 0
PRED['ema_slope<0'] = lambda r: r['ema_slope_atr'] < 0
# macro regime
PRED['macro_bull'] = lambda r: r['macro_bull']==1
PRED['not_bear'] = lambda r: r['macro_bear']==0
PRED['macro_bear'] = lambda r: r['macro_bear']==1
PRED['macro_drop>3'] = lambda r: r['macro_drop_atr']>3   # deep drop = stretched
PRED['macro_retr<0.5'] = lambda r: r['macro_retr']<0.5
PRED['macro_retr>0.7'] = lambda r: r['macro_retr']>0.7
# sweep / liquidity
PRED['sweep>0.5'] = lambda r: r['sweep_depth_atr']>0.5
PRED['sweep>1'] = lambda r: r['sweep_depth_atr']>1
PRED['sweep<0.3'] = lambda r: r['sweep_depth_atr']<0.3
PRED['fast_reclaim'] = lambda r: r['reclaim_speed']<=2
# displacement / momentum at reclaim
PRED['disp4>1'] = lambda r: r['disp4_atr']>1
PRED['disp8>1.5'] = lambda r: r['disp8_atr']>1.5
PRED['up_closes>=5'] = lambda r: r['up_closes8']>=5
PRED['up_closes>=6'] = lambda r: r['up_closes8']>=6
PRED['range_exp>1.5'] = lambda r: r['range_exp']>1.5
# leg/room (space to run)
PRED['leg_ext<0.5'] = lambda r: r['leg_ext']<0.5
PRED['room>2'] = lambda r: r['room_atr']>2
PRED['room>3'] = lambda r: r['room_atr']>3
# candle quality
PRED['wick>0.3'] = lambda r: r['low_wick']>0.3
PRED['closepos>0.6'] = lambda r: r['low_closepos']>0.6
PRED['closepos>0.7'] = lambda r: r['low_closepos']>0.7
# volatility/session
PRED['atr_reg>1'] = lambda r: r['atr_regime']>1
PRED['atr_reg<1'] = lambda r: r['atr_regime']<1
PRED['killzone'] = lambda r: r['killzone']==1
PRED['vol_low'] = lambda r: r['vol_low_vs_med']<1
# NAS / SMC / bubbles
PRED['nas_long16'] = lambda r: r['nas_long_16']==1
PRED['nas_long48'] = lambda r: r['nas_long_48']==1
PRED['no_nas_short'] = lambda r: r['nas_short_16']==0
PRED['choch'] = lambda r: r['smc_choch']==1
PRED['bos'] = lambda r: r['smc_bos']==1
PRED['buy_bubble'] = lambda r: (r['buy_S']+r['buy_M']+r['buy_L'])>0
PRED['buy_ML'] = lambda r: (r['buy_M']+r['buy_L'])>0
PRED['no_sell_bubble'] = lambda r: (r['sell_S']+r['sell_M']+r['sell_L'])==0
PRED['sell_pol_lo'] = lambda r: r['sell_pol']<0.4

def apply(pred): return [r for r in ROWS if pred(r)]

def main():
    print(f"BASE: n={N} avgR={BASE:+.3f} WR={sum(1 for r in ROWS if r[TARGET]>0)/N*100:.1f}% "
          f"runner={sum(1 for r in ROWS if r[TARGET]>=5)}({sum(1 for r in ROWS if r[TARGET]>=5)/N*100:.1f}%)")
    print("="*100)

    # ---- SINGLES ----
    print("\n### SINGLES (avgR>base, n>=50, sorted by lift) ###")
    singles = []
    for name, p in PRED.items():
        s = stats(apply(p))
        if s and s['n']>=50:
            singles.append((name, p, s))
    singles.sort(key=lambda x: -x[2]['avg'])
    keep_singles = []
    for name, p, s in singles:
        if s['avg'] > BASE:
            print(fmt(name, s))
            keep_singles.append((name, p, s))

    # ---- PAIRS (forward from promising singles) ----
    print("\n### PAIRS (n>=30, robust first) ###")
    names = list(PRED.items())
    pairs = []
    for (n1,p1),(n2,p2) in itertools.combinations(names,2):
        sub = [r for r in ROWS if p1(r) and p2(r)]
        s = stats(sub)
        if s and s['n']>=30 and s['avg']>BASE+0.15:
            pairs.append((f"{n1} & {n2}", s))
    pairs.sort(key=lambda x:(not robust(x[1]), -x[1]['avg']))
    for name, s in pairs[:40]:
        print(fmt(name, s))

    # ---- TRIPLES (forward from top robust pairs) ----
    print("\n### TRIPLES (n>=30, robust, sorted by avgR) ###")
    triples = []
    for (n1,p1),(n2,p2),(n3,p3) in itertools.combinations(names,3):
        sub = [r for r in ROWS if p1(r) and p2(r) and p3(r)]
        s = stats(sub)
        if s and s['n']>=30 and robust(s):
            triples.append((f"{n1} & {n2} & {n3}", s))
    triples.sort(key=lambda x:-x[1]['avg'])
    for name, s in triples[:40]:
        print(fmt(name, s))
    print(f"\n[triples robust total: {len(triples)}]")

if __name__=='__main__':
    main()
