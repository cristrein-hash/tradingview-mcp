"""
_reopt5_flow_scan.py — single-feature WR-lift scan, FLOW-exhaustion lens (R_B for 5ATR).
RAW-causal. win=R>0. Forbidden: R,win,cj,low_idx,low_t,yr,block.
Prints WR in regions for each focus feature so we can pick thresholds that LIFT WR
while keeping >=85% winners. Then we hand-build combos in _reopt5_combos.py.
"""
import statistics
from _reopt5_harness import ROWS, BASE_WR, BASE_WINS
SENT=-10000000.0

def wr(rows):
    return 100*sum(r['win'] for r in rows)/len(rows) if rows else float('nan')

def scan(f, thresholds, direction):
    """direction '>=' keep rows with f>=t ; '<=' keep f<=t."""
    print(f"\n--- {f} (keep {direction} t) base WR {BASE_WR:.2f} ---")
    for t in thresholds:
        if direction=='>=':
            keep=[r for r in ROWS if r[f] is not None and r[f]!=SENT and r[f]>=t]
        else:
            keep=[r for r in ROWS if r[f] is not None and r[f]!=SENT and r[f]<=t]
        wk=sum(r['win'] for r in keep)
        wpct=100*wk/BASE_WINS
        print(f"  t={t:>8}: n_keep={len(keep):5d} WR={wr(keep):5.2f} winners_kept%={wpct:5.1f}")

# FLOW exhaustion lens features
scan('sell_decel', [-1.0,-0.5,0.0,0.3,0.5,0.7,0.9], '>=')   # higher = decelerating sells (exhaustion)
scan('sell_decel', [0.0,0.3,0.5,0.7,0.9], '<=')
scan('flow_accel', [-50,-20,-10,-5,0,5,10,20], '>=')         # positive accel = buy pressure building
scan('flow_accel', [-20,-10,-5,0], '<=')
scan('buy_sell_ratio4', [0,1,2,3,4,5,6], '>=')               # buy dominance recent
scan('buy_sell_ratio4', [0,1,2,3], '<=')
scan('vol_low_vs_med', [0.7,0.9,1.0,1.2,1.5,2.0], '<=')      # low vol = quiet (exhaustion preceding)
scan('vol_low_vs_med', [1.0,1.5,2.0], '>=')
scan('sell_skew_mig', [-2,-1,0,1,2], '>=')
scan('sell_skew_mig', [-1,0,1], '<=')
scan('absorption', [1], '>=')                                # absorption present
scan('regime_age_h', [10,25,50,75,100,150], '<=')           # young regime
scan('regime_age_h', [25,50,75,100], '>=')

# overheating context (R_B = exhaustion-of-selling-in-overheating)
scan('rsi', [60,65,70,75,80], '>=')                          # overbought 15m
scan('rsi', [60,65,70], '<=')
scan('rsi_low', [30,40,50,60], '<=')                          # was oversold (selling exhausted)
scan('rsi_low', [40,50,60], '>=')
scan('low_closepos', [0.2,0.3,0.5,0.7], '<=')               # closed near low of bar
scan('low_closepos', [0.3,0.5,0.7], '>=')
scan('bars_since_sell', [10,20,50,99], '>=')                 # long since last sell signal
scan('bars_since_sell', [20,50], '<=')
