"""Find a TIGHT 'pure chop' cut that preserves >=85% winners.
Strategy: cut-when. Search the loser-dense corner. Need losers_cut high relative
to winners_cut. Profile candidate cut-rules by (winners_cut, losers_cut, lift).
"""
from _r2lap_lib import load, evaluate, report, wr

k = load()
W = sum(r['win'] for r in k); L = len(k) - W
print(f"n={len(k)} winners={W} losers={L}  to keep>=85% winners can cut <= {int(0.15*W)} winners\n")

def profile(name, cut_pred):
    """cut_pred(r)->True means CUT."""
    cut = [r for r in k if cut_pred(r)]
    cw = sum(r['win'] for r in cut); cl = len(cut) - cw
    print(f"{name}: cut_n={len(cut)} cut_win={cw} cut_los={cl} "
          f"cut_WR={100*cw/len(cut) if cut else 0:.1f} (lo group is chop if WR<<68.5)")

# Examine corners. Cut where group WR is LOW => removing losers.
profile("absorption==1", lambda r: r['absorption']==1)
profile("buy_L_recent==1", lambda r: r['buy_L_recent']==1)
profile("buy_sell_ratio4>=7", lambda r: r['buy_sell_ratio4']>=7)
profile("flow_accel flat(-2..0)", lambda r: -2<=r['flow_accel']<=0)
profile("low_vol_rel>1.5", lambda r: r['low_vol_rel']>1.5)
profile("bars_since_lowest<44", lambda r: r['bars_since_lowest']<44)
profile("regime_age_h 0..25 (young, ex-Q3)", lambda r: r['regime_age_h']<25.2)
profile("bsr4>=7 AND flat flow", lambda r: r['buy_sell_ratio4']>=7 and -2<=r['flow_accel']<=0)
profile("bsr4>=7 AND absorption", lambda r: r['buy_sell_ratio4']>=7 and r['absorption']==1)
profile("buy_L_recent AND bsr4>=7", lambda r: r['buy_L_recent']==1 and r['buy_sell_ratio4']>=7)
profile("absorption AND flat flow", lambda r: r['absorption']==1 and -2<=r['flow_accel']<=0)
profile("absorption AND low_vol>1.5", lambda r: r['absorption']==1 and r['low_vol_rel']>1.5)
profile("flat flow AND low_vol>1.5", lambda r: -2<=r['flow_accel']<=0 and r['low_vol_rel']>1.5)
profile("bsr4>=7 AND low_vol>1.5", lambda r: r['buy_sell_ratio4']>=7 and r['low_vol_rel']>1.5)

print("\n-- KEEP-rules (cut complement), require >=85% win kept --")
tests = [
  ("K1 cut absorption&flat-flow", lambda r: not (r['absorption']==1 and -2<=r['flow_accel']<=0)),
  ("K2 cut bsr4>=7 & flat-flow", lambda r: not (r['buy_sell_ratio4']>=7 and -2<=r['flow_accel']<=0)),
  ("K3 cut buy_L_recent & bsr4>=7", lambda r: not (r['buy_L_recent']==1 and r['buy_sell_ratio4']>=7)),
  ("K4 cut absorption & low_vol>1.5", lambda r: not (r['absorption']==1 and r['low_vol_rel']>1.5)),
  ("K5 cut (bsr4>=7&flat) OR (absorption&low_vol>1.5)",
     lambda r: not ((r['buy_sell_ratio4']>=7 and -2<=r['flow_accel']<=0) or (r['absorption']==1 and r['low_vol_rel']>1.5))),
]
for d,f in tests:
    report(evaluate(k,f,d)); print()
