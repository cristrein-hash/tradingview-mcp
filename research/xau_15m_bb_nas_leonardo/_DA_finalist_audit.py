#!/usr/bin/env python3
"""DA audit of FINAL pick for XAU 15M LONG-filter engine.
Reproduces every finalist number, runs leave-one-condition-out, threshold nudges (+-15%),
year/block stability, big-winner reshuffle analysis, and dedup new_trades honesty check.
All metrics come from filter_harness.run (single source of truth)."""
import json, importlib.util
from pathlib import Path
HERE = Path(__file__).parent
spec = importlib.util.spec_from_file_location('fh', HERE/'filter_harness.py')
fh = importlib.util.module_from_spec(spec); spec.loader.exec_module(fh)

def m(expr):
    fn = eval('lambda r: ('+expr+')')
    s, taken = fh.run(fn)
    yr, blk = fh.by_splits(taken)
    return s, yr, blk, taken

def line(label, s):
    return (f"{label:<34} N={s['n']:>3} WR={s['wr']:>4} sumR={s['sumr']:>5} DD={s['dd']:>5} "
            f"strk={s['streak']} big={s['bigwin']} bigLost={s['big_winners_lost']} "
            f"new={s['new_trades']} winLost={s['winners_lost']} losCut={s['losers_cut']} "
            f"dWR={s['dWR']} dSumR={s['dSumR']}")

FINALISTS = {
    'BASE(h1_eff only)': "r['h1_eff']>=0.15",
    'A': "r['h1_eff']>=0.15 and r['rsi']>50",
    'B': "r['h1_eff']>=0.15 and (r['buy_bub_w_leg']<=3*r['sell_bub_w_leg']+5) and r['rsi']>50",
    'C': "r['h1_eff']>=0.15 and r['buy_bub_L_w24']<=3 and r['dist_ema_atr']<=4",
}

print('### BASE ###'); print(json.dumps(fh.BASE)); print()
print('### FINALISTS reproduced ###')
for k, e in FINALISTS.items():
    s, yr, blk, _ = m(e)
    print(line(k, s)); print('   by_year', yr); print('   by_block', blk)
print()

print('### POINT 2: LEAVE-ONE-CONDITION-OUT ###')
LOO = {
    'A drop rsi (=h1_eff)':   "r['h1_eff']>=0.15",
    'A drop h1_eff (rsi only)':"r['rsi']>50",
    'B drop bubratio':        "r['h1_eff']>=0.15 and r['rsi']>50",
    'B drop rsi':             "r['h1_eff']>=0.15 and (r['buy_bub_w_leg']<=3*r['sell_bub_w_leg']+5)",
    'B drop h1_eff':          "(r['buy_bub_w_leg']<=3*r['sell_bub_w_leg']+5) and r['rsi']>50",
    'C drop bubL':            "r['h1_eff']>=0.15 and r['dist_ema_atr']<=4",
    'C drop distema':         "r['h1_eff']>=0.15 and r['buy_bub_L_w24']<=3",
    'C drop h1_eff':          "r['buy_bub_L_w24']<=3 and r['dist_ema_atr']<=4",
}
for k, e in LOO.items():
    s, *_ = m(e); print(line(k, s))
print()

print('### POINT 3: THRESHOLD NUDGES +-15% ###')
NUDGE = {
    'h1_eff 0.13':            "r['h1_eff']>=0.13 and r['rsi']>50",
    'h1_eff 0.15(A)':         "r['h1_eff']>=0.15 and r['rsi']>50",
    'h1_eff 0.17':            "r['h1_eff']>=0.17 and r['rsi']>50",
    'rsi 45':                 "r['h1_eff']>=0.15 and r['rsi']>45",
    'rsi 50(A)':              "r['h1_eff']>=0.15 and r['rsi']>50",
    'rsi 55':                 "r['h1_eff']>=0.15 and r['rsi']>55",
    'C bubL<=2':              "r['h1_eff']>=0.15 and r['buy_bub_L_w24']<=2 and r['dist_ema_atr']<=4",
    'C bubL<=3':              "r['h1_eff']>=0.15 and r['buy_bub_L_w24']<=3 and r['dist_ema_atr']<=4",
    'C bubL<=4':              "r['h1_eff']>=0.15 and r['buy_bub_L_w24']<=4 and r['dist_ema_atr']<=4",
    'C distema<=3.4':         "r['h1_eff']>=0.15 and r['buy_bub_L_w24']<=3 and r['dist_ema_atr']<=3.4",
    'C distema<=4.6':         "r['h1_eff']>=0.15 and r['buy_bub_L_w24']<=3 and r['dist_ema_atr']<=4.6",
    'B coef 2.55*+4.25':      "r['h1_eff']>=0.15 and (r['buy_bub_w_leg']<=2.55*r['sell_bub_w_leg']+4.25) and r['rsi']>50",
    'B coef 3.45*+5.75':      "r['h1_eff']>=0.15 and (r['buy_bub_w_leg']<=3.45*r['sell_bub_w_leg']+5.75) and r['rsi']>50",
}
for k, e in NUDGE.items():
    s, *_ = m(e); print(line(k, s))
print()

print('### POINT 5: dedup reshuffle / big-winner identity ###')
print('Raw rows R>=3:', sum(1 for r in fh.ROWS if r['R']>=3), '| BASE dedup big winners:', fh.BASE['bigwin'])
print('BASE big-winner survivors:')
for c in fh.BASE_TAKEN:
    if c['R']>=3:
        print(f"   blk={c['block']} R={c['R']} h1_eff={c['h1_eff']} rsi={c['rsi']}")
for k in ['A','B','C']:
    s, yr, blk, taken = m(FINALISTS[k])
    bigs=[c for c in taken if c['R']>=3]
    new_ids = {(c['block'],c['low_t']) for c in taken} - fh.BASE_IDS
    new_rows=[c for c in taken if (c['block'],c['low_t']) in new_ids]
    new_sumR=round(sum(c['R'] for c in new_rows),1)
    new_win=sum(c['win'] for c in new_rows)
    print(f"{k}: surviving big winners={len(bigs)} | new_trades={len(new_rows)} "
          f"new_sumR={new_sumR} new_WR={round(100*new_win/max(len(new_rows),1),1)}")
