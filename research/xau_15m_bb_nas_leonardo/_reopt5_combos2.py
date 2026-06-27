"""
_reopt5_combos2.py — expanded combo search: FLOW-exhaustion lens (R_B) + structural
trend/path/regime context that the streak diagnostic flagged.

Streak signature (no-dedup): h1_trend=0 (chop), regime_age_h young, path_eff low.
=> add predicates that demand an established/efficient leg, and re-derive R_B exhaustion
   only inside that context.

RAW-causal. win=R>0. Forbidden as feature: R,win,cj,low_idx,low_t,yr,block.
Robustness gate identical to harness.
"""
import itertools
from _reopt5_harness import (ROWS, evaluate, report, BASE_WR)
SENT=-10000000.0
def nz(v): return v is not None and v!=SENT

# CUT predicates (loser-dense). match -> drop.
CUTS = {
    'cut_skew_up':    lambda r: nz(r['sell_skew_mig']) and r['sell_skew_mig'] >= 1,
    'cut_chop':       lambda r: r['h1_trend']==0,                                   # no 15m/1h trend (streak signature)
    'cut_loweff':     lambda r: nz(r['path_eff']) and r['path_eff'] < 0.12,         # choppy leg
    'cut_regime_old': lambda r: nz(r['regime_age_h']) and r['regime_age_h'] > 100,
    'cut_brate6':     lambda r: nz(r['buy_sell_ratio4']) and r['buy_sell_ratio4'] >= 6,
    'cut_far_demand': lambda r: nz(r['dist_demand_atr']) and r['dist_demand_atr'] > 1.0,  # too far above demand
}
# KEEP predicates (winner-dense / overheating-exhaustion / structural)
KEEPS = {
    'keep_rsi60':       lambda r: nz(r['rsi']) and r['rsi'] >= 60,
    'keep_trend_up':    lambda r: r['h1_trend']==1,
    'keep_regime_y100': lambda r: nz(r['regime_age_h']) and r['regime_age_h'] <= 100,
    'keep_sells_stale': lambda r: nz(r['bars_since_sell']) and r['bars_since_sell'] >= 10,
    'keep_flow_ok':     lambda r: nz(r['flow_accel']) and r['flow_accel'] >= -10,
    'keep_eff':         lambda r: nz(r['path_eff']) and r['path_eff'] >= 0.12,
}

def make(kc,cc):
    kp=[KEEPS[k] for k in kc]; cp=[CUTS[c] for c in cc]
    def fn(r):
        for p in kp:
            if not p(r): return False
        for p in cp:
            if p(r): return False
        return True
    return fn

results=[]; seen=set()
kk=list(KEEPS); ck=list(CUTS)
for nk in range(0,3):
  for nc in range(0,4):
    if not (1<=nk+nc<=3): continue
    for kc in itertools.combinations(kk,nk):
      for cc in itertools.combinations(ck,nc):
        name='+'.join(list(kc)+list(cc))
        if name in seen: continue
        seen.add(name)
        res=evaluate(make(kc,cc),name)
        if res and res['winners_kept_pct']>=85.0:
            results.append(res)

results.sort(key=lambda r:(not r['robust'], r['streak_keep'], -r['wr_keep']))
print(f"BASE WR {BASE_WR:.2f}  cand(winners>=85%)={len(results)}")
rob=[r for r in results if r['robust']]
print(f"ROBUST=True count={len(rob)}\n")
print("=== ROBUST ===")
for r in sorted(rob,key=lambda r:(r['streak_keep'],-r['wr_keep'])):
    report(r); print()
print("=== TOP 12 overall (by streak then wr) ===")
for r in results[:12]:
    report(r); print()
