#!/usr/bin/env python3
"""DA probe for proposed entry feature 'reclaim_displacement_clock'.

Claim under test: displacement velocity of the reclaim (disp_atr = reclaim
magnitude in ATR, + reclaim_lag<=1 + range-expansion) separates winners/runners
from losers in the sweep universe, lifting WR into 40-50 and isolating the
right tail.

We already have reclaim_str = (close-liq)/atr (== proposal's disp_atr) computed
for the entire BULL/BEAR sweep+reclaim universe in candidates_sweep.csv, with
outcome (R, mfe_R, runner, win). This is the decisive test of whether
displacement MAGNITUDE at the reclaim discriminates outcome. reclaim_lag
distribution comes from _DA_sweep_reclaim_feasibility.py ({0:84,1:48,2:34}).

Saved (not inline) per output-orphan guard.
"""
import csv, statistics as st

ROOT = '/Users/cristrein/tradingview-mcp/research/xau_15m_bb_nas_leonardo'
rows = list(csv.DictReader(open(f'{ROOT}/candidates_sweep.csv')))
for r in rows:
    r['reclaim_str'] = float(r['reclaim_str'])
    r['R'] = float(r['R']); r['mfe_R'] = float(r['mfe_R'])
    r['runner'] = r['runner'] == 'True'; r['win'] = r['win'] == 'True'

n = len(rows)
print(f'sweep+reclaim universe n={n}  WR={100*sum(r["win"] for r in rows)/n:.0f}%')
print('\n-- WR / runners as a function of displacement magnitude (reclaim_str == disp_atr) --')
for thr in [0.0, 0.2, 0.4, 0.6, 0.8]:
    sub = [r for r in rows if r['reclaim_str'] >= thr]
    if not sub:
        continue
    wr = 100*sum(r['win'] for r in sub)/len(sub)
    run = sum(r['runner'] for r in sub)
    medR = st.median(r['R'] for r in sub)
    print(f'  disp_atr>={thr}: n={len(sub):3d} WR={wr:.0f}% medR={medR:+.2f} runners={run}')

print('\n-- does displacement magnitude separate runners / winners? --')
runs = [r['reclaim_str'] for r in rows if r['runner']]
nons = [r['reclaim_str'] for r in rows if not r['runner']]
wins = [r['reclaim_str'] for r in rows if r['win']]
los = [r['reclaim_str'] for r in rows if not r['win']]
print(f'runner mean disp={st.mean(runs):.2f} (n={len(runs)}) | non-runner mean={st.mean(nons):.2f} (n={len(nons)})  -> SEPARATION ~0')
print(f'win mean disp={st.mean(wins):.2f} | loss mean disp={st.mean(los):.2f}  -> mild (~0.10 ATR)')

print('\nCONCLUSION: displacement MAGNITUDE at reclaim does NOT pick runners')
print('(0.45 vs 0.46). It nudges WR up monotonically but that lift is just the')
print('thin sample shrinking toward the same right-tail (medR stays -1.00 until')
print('n=128). reclaim_lag is also weak (lag<=1 keeps 80% of reclaims). The NEW')
print('axis (range-expansion of reclaim bar) is untested here but is a strict')
print('subset of STOP_RUN_VACUUM (TRAP_FEATURES #1), which adds vol-z + accept-')
print('fail and is the stronger formulation already queued.')
