#!/usr/bin/env python3
"""
_engine_novel_triggers.py
Investigative quant miner for CAUSAL entry triggers on the XAU 15M reclaim universe.

Base universe: fractal lows n=3519, entry=RECLAIM (close above low+0.25ATR),
outcome=R_reclaim (let-run, structural SL). Base avgR=+0.73, WR=45.4%, runner(R>=5)=6.5%.

Two parts:
  PART A: mine the existing causal features in entry_dataset.jsonl for subsets
          with higher avgR + WR that are STABLE across 2024/2025/2026, n>=30.
  PART B: INVENTOR lens — compute NOVEL causal features straight from RAW
          primitives/*.json (OHLC) and bubbles/*.jsonl (known_at filtered),
          aligned to the reclaim bar, and test if they discriminate.

RULES:
 - Features are causal (bar of reclaim). NEVER use near_M8/R_reclaim/R_8atr/held8/runner
   as a FEATURE — only as target.
 - Report n, WR, avgR, avgR per year (2024/2025/2026).
 - robust = avgR>base in all 3 years AND n>=30 AND not carried by top-2 trades.
"""
import json, os, glob, statistics as st
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
DS = os.path.join(HERE, 'entry_dataset.jsonl')
BASE = 0.727

def load_rows():
    return [json.loads(l) for l in open(DS)]

def summary(rows, label, mask):
    sel = [r for r in rows if mask(r)]
    n = len(sel)
    if n == 0:
        return None
    R = [r['R_reclaim'] for r in sel]
    avg = sum(R)/n
    wr = 100*sum(1 for x in R if x>0)/n
    runner = 100*sum(1 for x in R if x>=5)/n
    yr = {}
    for y in (2024,2025,2026):
        ys = [r['R_reclaim'] for r in sel if r['yr']==y]
        yr[y] = (len(ys), (sum(ys)/len(ys)) if ys else None)
    # ex-top2 robustness
    Rs = sorted(R, reverse=True)
    extop2 = (sum(Rs[2:])/(n-2)) if n>2 else None
    out = {
        'label': label, 'n': n, 'wr': wr, 'avgR': avg, 'runner': runner,
        'y24': yr[2024], 'y25': yr[2025], 'y26': yr[2026],
        'lift': avg-BASE, 'extop2': extop2,
    }
    return out

def is_robust(o):
    if o is None or o['n'] < 30:
        return False
    for y in ('y24','y25','y26'):
        ny, ay = o[y]
        if ny < 8 or ay is None or ay <= BASE:
            return False
    # not carried by top-2: ex-top2 avgR must still beat base
    if o['extop2'] is None or o['extop2'] <= BASE:
        return False
    return True

def pr(o):
    if o is None:
        print('  (empty)')
        return
    rob = is_robust(o)
    y24,y25,y26 = o['y24'],o['y25'],o['y26']
    print('  %-46s n=%4d WR=%4.1f%% avgR=%+.3f run=%4.1f%% | y24=%+.2f(%d) y25=%+.2f(%d) y26=%+.2f(%d) | lift=%+.3f exT2=%+.3f ROBUST=%s'
          % (o['label'], o['n'], o['wr'], o['avgR'], o['runner'],
             (y24[1] if y24[1] is not None else 0), y24[0],
             (y25[1] if y25[1] is not None else 0), y25[0],
             (y26[1] if y26[1] is not None else 0), y26[0],
             o['lift'], (o['extop2'] or 0), rob))
    return rob

if __name__ == '__main__':
    rows = load_rows()
    print('BASE: n=%d avgR=%.3f WR=%.1f%% runner=%.1f%%' % (
        len(rows), sum(r['R_reclaim'] for r in rows)/len(rows),
        100*sum(1 for r in rows if r['R_reclaim']>0)/len(rows),
        100*sum(1 for r in rows if r['R_reclaim']>=5)/len(rows)))
    print()
    print('=== PART A: single-feature threshold scan (existing causal features) ===')

    # Numeric features to scan with directional thresholds
    numeric = ['rsi','rsi_low','rsi_head','dist_ema_atr','ema_slope_atr',
               'macro_drop_atr','macro_retr','sweep_depth_atr','disp4_atr','disp8_atr',
               'up_closes8','range_exp','leg_ext','room_atr','low_wick','low_closepos',
               'atr_regime','hour','vol_low_vs_med','sell_pol']
    import numpy as np
    results = []
    for f in numeric:
        vals = sorted(set(r[f] for r in rows if r[f] is not None))
        if len(vals) < 4:
            qs = vals
        else:
            qs = [np.quantile([r[f] for r in rows if r[f] is not None], q) for q in (0.2,0.35,0.5,0.65,0.8)]
        for thr in qs:
            for op,opn in ((lambda v,t=thr: v>=t,'>='),(lambda v,t=thr: v<=t,'<=')):
                o = summary(rows, '%s%s%.3f'%(f,opn,thr), lambda r,ff=f,oo=op: r[ff] is not None and oo(r[ff]))
                if o and o['n']>=30:
                    results.append(o)
    results.sort(key=lambda o: o['avgR'], reverse=True)
    print('-- top 20 single-feature by avgR (n>=30) --')
    for o in results[:20]:
        pr(o)
