"""Refine the winning axis: room (supply-demand) x bars_to_8atr (grind vs spike).
Goal honoring the >=85% winners-kept constraint while raising WR & cutting streak.
Two views:
  A) loosest rules that still beat base in all 3 yrs with winners_kept>=0.85
  B) the spike-into-ceiling loser cell isolated (precision of the cut).
RAW-causal.
"""
from _disc8_lib import load, eval_rule, print_rule, base_stats
import numpy as np

rows = load()
n, w, wr, st = base_stats(rows)
for r in rows:
    r["_room"] = r["dist_supply_atr"] - r["dist_demand_atr"]


def g(r, k):
    return r[k] if r[k] is not None else 0


print("=== 2x2 cell WR: room(>=0?) x spike(bars<X?) ===")
for B in (40, 60, 84, 120):
    print(f" bars threshold = {B}")
    for rm_lo, rm_hi, rl in [(-1e9, 0, "ceiling(room<0)"), (0, 1e9, "clearer(room>=0)")]:
        for bl, bh, sl in [(-1e9, B, "spike(fast)"), (B, 1e9, "grind(slow)")]:
            sel = [r for r in rows if rm_lo <= r["_room"] < rm_hi and bl <= r["bars_to_8atr"] < bh]
            if sel:
                print(f"   {rl:18s} {sl:11s} n={len(sel):4d} WR={sum(s['win'] for s in sel)/len(sel):.3f}")

print("\n=== isolate the WORST cell to cut (precision) at bars<60 & room<0 ===")
worst = [r for r in rows if r["_room"] < 0 and r["bars_to_8atr"] < 60]
if worst:
    print(f" worst cell n={len(worst)} WR={sum(s['win'] for s in worst)/len(worst):.3f} (cut these)")

print("\n=== Candidate KEEP rules honoring winners_kept>=0.85 priority ===")
CANDS = {
    # cut only the spike-into-ceiling cell (keep complement)
    "cut[room<0 & bars<60]": lambda r: not (r["_room"] < 0 and r["bars_to_8atr"] < 60),
    "cut[room<0 & bars<84]": lambda r: not (r["_room"] < 0 and r["bars_to_8atr"] < 84),
    "cut[room<0 & bars<40]": lambda r: not (r["_room"] < 0 and r["bars_to_8atr"] < 40),
    "cut[room<-0.2 & bars<84]": lambda r: not (r["_room"] < -0.2 and r["bars_to_8atr"] < 84),
    # add a worst-year context: also cut ceiling spikes only when h4 not up
    "cut[room<0 & bars<60 & h4_trend<1]": lambda r: not (r["_room"] < 0 and r["bars_to_8atr"] < 60 and g(r, "h4_trend") < 1),
    # moderate selective rule
    "room>=0 & grind84": lambda r: r["_room"] >= 0 and r["bars_to_8atr"] >= 84,
    "room>=0 & grind60": lambda r: r["_room"] >= 0 and r["bars_to_8atr"] >= 60,
    "room>=0 & grind40": lambda r: r["_room"] >= 0 and r["bars_to_8atr"] >= 40,
    # room alone variants
    "room>=0": lambda r: r["_room"] >= 0,
    "room>=-0.2": lambda r: r["_room"] >= -0.2,
    "grind60": lambda r: r["bars_to_8atr"] >= 60,
}
res = [eval_rule(rows, fn, d) for d, fn in CANDS.items()]
res = [m for m in res if m]
# split into "winner-safe" (>=0.85 kept) and "aggressive"
print("\n--- WINNER-SAFE (winners_kept>=0.85) ---")
for m in sorted([m for m in res if m["winners_kept_pct"] >= 0.85], key=lambda m: -m["wr_keep"]):
    print_rule(m); print()
print("--- AGGRESSIVE (winners_kept<0.85) ---")
for m in sorted([m for m in res if m["winners_kept_pct"] < 0.85], key=lambda m: -m["wr_keep"]):
    print_rule(m); print()
