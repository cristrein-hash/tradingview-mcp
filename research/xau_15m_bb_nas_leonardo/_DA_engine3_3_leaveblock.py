#!/usr/bin/env python3
"""DA ATTACK 3 — LEAVE-BLOCK robustness of the standout combo. (Cris 2026-06-28)
Recompute the combo's avgR/sumR dropping each of the 8 blocks. min/max avgR. Stable or 1-block-carried?
Also per-block standalone metrics to locate concentration."""
from _DA_engine3_core import G, passes, metr, STANDOUT
from collections import Counter

full = [r for r in G if passes(r, STANDOUT)]
blocks = sorted(set(r["block"] for r in G))
print(f"standout combo: {'+'.join(STANDOUT)}  n={len(full)}")
m_all = metr(full)
print(f"ALL-blocks: {m_all}\n")

print("=== PER-BLOCK standalone ===")
print(f"{'block':>12}{'n':>5}{'mf':>4}{'WR':>7}{'sumR':>8}{'avgR':>8}")
for b in blocks:
    sel = [r for r in full if r["block"] == b]
    m = metr(sel); mf = sum(r["is_monforte"] for r in sel)
    if m:
        print(f"{b:>12}{m['n']:>5}{mf:>4}{m['WR']:>7}{m['sumR']:>8}{m['avgR']:>8}")
    else:
        print(f"{b:>12}{'0':>5}")

print("\n=== LEAVE-ONE-BLOCK-OUT (drop block, recompute) ===")
print(f"{'dropped':>12}{'n':>5}{'sumR':>8}{'avgR':>8}{'maxDD':>8}")
avgs = []
for b in blocks:
    sel = [r for r in full if r["block"] != b]
    m = metr(sel); avgs.append((b, m["avgR"], m["sumR"]))
    print(f"{b:>12}{m['n']:>5}{m['sumR']:>8}{m['avgR']:>8}{m['maxDD']:>8}")
mn = min(avgs, key=lambda x: x[1]); mx = max(avgs, key=lambda x: x[1])
print(f"\navgR range across LOBO: min={mn[1]:+.3f} (drop {mn[0]})  max={mx[1]:+.3f} (drop {mx[0]})")
print(f"spread={mx[1]-mn[1]:.3f}  (full avgR={m_all['avgR']:+.3f})")
print("\nVERDICT 3: stable iff dropping ANY single block keeps avgR clearly >0 and near full; "
      "1-block-carried iff min avgR collapses toward 0 / below take-all 0.105.")
