"""OB-detector lens exploration: supply/demand geometry vs win/loss.
Look for the CONTEXTUAL combo, not single-feature separation.
Hypothesis: loser when 8ATR reached near SUPPLY above (ceiling) or far from demand;
winner exiting fresh demand with supply distant. Combine with regime/TF.
"""
import json
from _disc8_lib import load

rows = load()
W = [r for r in rows if r["win"] == 1]
L = [r for r in rows if r["win"] == 0]


def stat(name, sel=lambda r: True):
    ws = [r[name] for r in W if sel(r) and r[name] is not None]
    ls = [r[name] for r in L if sel(r) and r[name] is not None]
    if not ws or not ls:
        return
    import statistics as st
    mw, ml = st.mean(ws), st.mean(ls)
    print(f"  {name:18s} W_mean={mw:7.3f} L_mean={ml:7.3f}  diff={mw-ml:+.3f}  nW={len(ws)} nL={len(ls)}")


print("=== OB features W vs L (full) ===")
for k in ["dist_demand_atr", "dist_supply_atr", "in_demand", "n_demand_near",
          "demand_fresh", "vpnode_dist_atr", "macro_retr", "macro_drop_atr",
          "path_eff", "rsi", "rsi_low", "disp4_atr", "atr_regime", "atr_expand",
          "vol_low_vs_med", "vol_climax", "bars_to_8atr"]:
    stat(k)

print("\n=== ratio supply/demand idea: is supply the ceiling? ===")
# define 'room above' = dist_supply - dist_demand (how much more space to supply vs demand behind)
for r in rows:
    r["_room"] = r["dist_supply_atr"] - r["dist_demand_atr"]
    dd = r["dist_demand_atr"] if r["dist_demand_atr"] not in (None,) else 0.0
    r["_sd_ratio"] = r["dist_supply_atr"] / (abs(dd) + 0.1)
stat("_room")
stat("_sd_ratio")

print("\n=== WR by dist_supply_atr quartiles ===")
import numpy as np
ds = sorted(r["dist_supply_atr"] for r in rows)
qs = [np.percentile(ds, p) for p in (25, 50, 75)]
print("supply quartile cuts", [round(q, 2) for q in qs])
for lo, hi, lab in [(-1e9, qs[0], "Q1 near"), (qs[0], qs[1], "Q2"), (qs[1], qs[2], "Q3"), (qs[2], 1e9, "Q4 far")]:
    sel = [r for r in rows if lo <= r["dist_supply_atr"] < hi]
    if sel:
        print(f"  {lab:8s} n={len(sel):4d} WR={sum(s['win'] for s in sel)/len(sel):.3f}")

print("\n=== WR by dist_demand_atr quartiles ===")
dd = sorted(r["dist_demand_atr"] for r in rows)
qs2 = [np.percentile(dd, p) for p in (25, 50, 75)]
print("demand quartile cuts", [round(q, 2) for q in qs2])
for lo, hi, lab in [(-1e9, qs2[0], "Q1 close"), (qs2[0], qs2[1], "Q2"), (qs2[1], qs2[2], "Q3"), (qs2[2], 1e9, "Q4 far")]:
    sel = [r for r in rows if lo <= r["dist_demand_atr"] < hi]
    if sel:
        print(f"  {lab:8s} n={len(sel):4d} WR={sum(s['win'] for s in sel)/len(sel):.3f}")

print("\n=== WR by _room (supply-demand) terciles ===")
rm = sorted(r["_room"] for r in rows)
qr = [np.percentile(rm, p) for p in (33, 66)]
print("room cuts", [round(q, 2) for q in qr])
for lo, hi, lab in [(-1e9, qr[0], "T1 supply<=demand"), (qr[0], qr[1], "T2"), (qr[1], 1e9, "T3 supply far above")]:
    sel = [r for r in rows if lo <= r["_room"] < hi]
    if sel:
        print(f"  {lab:22s} n={len(sel):4d} WR={sum(s['win'] for s in sel)/len(sel):.3f}")
