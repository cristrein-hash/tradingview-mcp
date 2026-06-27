#!/usr/bin/env python3
"""
_reopt5_ob.py — OB-lens (Order Block zones) re-optimization for 5ATR candidates.

LENS: OB zones — loser near supply / far from demand; winner exiting FRESH demand.
Features: dist_demand_atr, dist_supply_atr, in_demand, demand_fresh.
Strategy = CUT-when-loser-dense stacks that remove loser pockets while keeping
>=85% winners and improving per-year + per-block stability + max-losing-streak.

Also tests cross-lens combos with the strongest loser-dense single cuts found by scan:
  dist_supply_atr (near/into supply), macro_bear, h1_dist (compressed h1),
  vpnode_dist_atr (at node), disp4_atr (no displacement), rsi (weak momentum).

RAW-causal. PROHIBITED: R,win,cj,low_idx.
"""
from _reopt5_harness import evaluate, report, ROWS, BASE_WR, BASE_STREAK, BASE_YR

def g(r,k,default=None):
    v=r.get(k)
    return default if v is None else v

# ---- CUT predicates: True = this row is a LOSER-DENSE pocket -> CUT it ----
# OB-lens cuts
CUTS = {
    # near or beyond supply (price ran into overhead supply) -> loser
    'into_supply'   : lambda r: g(r,'dist_supply_atr', 99) < -0.28,
    'near_supply'   : lambda r: g(r,'dist_supply_atr', 99) < 0.5,
    'far_demand'    : lambda r: g(r,'dist_demand_atr', 0) >  3.0,   # very far above demand origin
    'not_fresh'     : lambda r: g(r,'demand_fresh', 1) == 0,
    'not_in_demand' : lambda r: g(r,'in_demand', 1) == 0,
    # cross-lens loser-dense (from scan)
    'macro_bear'    : lambda r: g(r,'macro_bear',0) >= 1,
    'h1_compress'   : lambda r: g(r,'h1_dist', 99) < 1.43,
    'at_node'       : lambda r: g(r,'vpnode_dist_atr', 99) < 1.07,
    'no_disp'       : lambda r: g(r,'disp4_atr', 99) < 0.78,
    'rsi_weak'      : lambda r: g(r,'rsi', 99) < 55.9,
    'h1_down'       : lambda r: g(r,'h1_trend', 0) < 0,
    'london_open'   : lambda r: g(r,'is_london_open',0) >= 1,
}

def keep_not(*names):
    """KEEP if NOT any of the named cut predicates fire."""
    preds=[CUTS[n] for n in names]
    return lambda r: not any(p(r) for p in preds)

print(f"BASE WR={BASE_WR:.2f} streak={BASE_STREAK}\n")

print("=== SINGLE OB-lens cuts ===")
for n in ['into_supply','near_supply','far_demand','not_fresh','not_in_demand']:
    report(evaluate(keep_not(n), f"CUT {n}"))

print("\n=== SINGLE cross-lens cuts ===")
for n in ['macro_bear','h1_compress','at_node','no_disp','rsi_weak','h1_down','london_open']:
    report(evaluate(keep_not(n), f"CUT {n}"))

print("\n=== 2-CUT combos (OB + cross) ===")
import itertools
all_names=list(CUTS.keys())
res2=[]
for a,b in itertools.combinations(all_names,2):
    m=evaluate(keep_not(a,b), f"CUT {a}+{b}")
    if m: res2.append(m)
# sort: robust first, then by wr_keep
res2.sort(key=lambda m:(not m['robust'], -m['wr_keep']))
for m in res2[:12]:
    report(m)

print("\n=== 3-CUT combos ===")
res3=[]
for a,b,c in itertools.combinations(all_names,3):
    m=evaluate(keep_not(a,b,c), f"CUT {a}+{b}+{c}")
    if m: res3.append(m)
res3.sort(key=lambda m:(not m['robust'], -m['wr_keep']))
for m in res3[:12]:
    report(m)

print("\n=== ROBUST=True (any combo size) ===")
robusts=[m for m in res2+res3 if m['robust']]
robusts.sort(key=lambda m:(-m['wr_keep'], m['streak_keep']))
for m in robusts[:20]:
    report(m)
print(f"\nTotal robust combos found: {len(robusts)}")
