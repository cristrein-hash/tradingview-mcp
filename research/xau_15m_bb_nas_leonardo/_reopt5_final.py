"""
_reopt5_final.py — final candidate filters for 5ATR (non-degenerate), full metrics.
Includes: (A) structural winners (disp4/dist_supply/h1_pos) found by brute force;
          (B) FLOW-exhaustion R_B re-derivation for 5ATR (my lens) for honest comparison.
RAW-causal. win=R>0. Forbidden: R,win,cj,low_idx,low_t,yr,block.
"""
from _reopt5_harness import ROWS, evaluate, report, BASE_WR, BASE_WINS
SENT=-10000000.0
def nz(v): return v is not None and v!=SENT

CANDS={
 # A. structural (brute-force robust core)
 'A1 disp4>=0.78 & dist_supply>=-0.28':
    lambda r: nz(r['disp4_atr']) and r['disp4_atr']>=0.78 and nz(r['dist_supply_atr']) and r['dist_supply_atr']>=-0.28,
 'A2 h1_pos>=0.65 & disp4>=0.78':
    lambda r: nz(r['h1_pos']) and r['h1_pos']>=0.65 and nz(r['disp4_atr']) and r['disp4_atr']>=0.78,
 'A3 disp4>=0.78 & dist_supply>=-0.28 & macro_bear==0':
    lambda r: nz(r['disp4_atr']) and r['disp4_atr']>=0.78 and nz(r['dist_supply_atr']) and r['dist_supply_atr']>=-0.28 and r['macro_bear']==0,
 'A4 disp4>=0.78 & h1_pos>=0.65 & macro_bear==0':
    lambda r: nz(r['disp4_atr']) and r['disp4_atr']>=0.78 and nz(r['h1_pos']) and r['h1_pos']>=0.65 and r['macro_bear']==0,
 # singles for reference
 'S1 dist_supply>=-0.25':       lambda r: nz(r['dist_supply_atr']) and r['dist_supply_atr']>=-0.25,
 'S2 disp4>=0.78':              lambda r: nz(r['disp4_atr']) and r['disp4_atr']>=0.78,
 'S3 h1_pos>=0.65':             lambda r: nz(r['h1_pos']) and r['h1_pos']>=0.65,
 'S4 macro_bear==0':           lambda r: r['macro_bear']==0,
 # B. FLOW-exhaustion R_B re-derivation for 5ATR (my lens): overheating + selling exhausted
 'B_RB v1 rsi>=60 & flow_accel>=-10 & cut_skew_up':
    lambda r: nz(r['rsi']) and r['rsi']>=60 and nz(r['flow_accel']) and r['flow_accel']>=-10 and not(nz(r['sell_skew_mig']) and r['sell_skew_mig']>=1),
 'B_RB v2 rsi>=60 & bars_since_sell>=20 & cut_skew_up':
    lambda r: nz(r['rsi']) and r['rsi']>=60 and nz(r['bars_since_sell']) and r['bars_since_sell']>=20 and not(nz(r['sell_skew_mig']) and r['sell_skew_mig']>=1),
 'B_RB v3 disp4>=0.78 & flow_accel>=-10':
    lambda r: nz(r['disp4_atr']) and r['disp4_atr']>=0.78 and nz(r['flow_accel']) and r['flow_accel']>=-10,
}
out=[]
for name,fn in CANDS.items():
    res=evaluate(fn,name); out.append(res)
    report(res); print()
