#!/usr/bin/env python3
"""DA ATTACK 5 — CONCENTRATION of the standout combo's +79.4R. (Cris 2026-06-28)
Is sumR driven by a few big winners (RCAP20 let-run tail)? Top-5 trades' R share. Remove them -> avgR/sumR.
Also full R distribution + Gini-ish tail diagnostics. A let-run strategy LIVES on the tail; if removing 5 of 386
trades kills the edge, it's tail-dependent (fragile for prop-firm with strict DD)."""
from _DA_engine3_core import G, passes, R_of, metr, R_list, STANDOUT

full = [r for r in G if passes(r, STANDOUT)]
rs = sorted(R_list(full), reverse=True)
n = len(rs); sm = sum(rs)
print(f"standout combo n={n} sumR={sm:+.1f} avgR={sm/n:+.3f}")
print(f"\nR distribution: max={rs[0]:+.1f} top5={[round(x,1) for x in rs[:5]]} "
      f"min={rs[-1]:+.1f}  #winners={sum(1 for x in rs if x>0)} #at-RCAP20={sum(1 for x in rs if x>=19.9)}")

for k in (1, 3, 5, 10):
    rem = rs[k:]; share = sum(rs[:k]) / sm * 100
    print(f"\n  remove top-{k}: top{k} R-share={share:.1f}%  -> n={len(rem)} sumR={sum(rem):+.1f} "
          f"avgR={sum(rem)/len(rem):+.3f}")

# how many trades to cover the whole sumR (concentration)
cum = 0; need = 0
for x in rs:
    cum += x; need += 1
    if cum >= sm: break
print(f"\ntop {need} trades ({100*need/n:.1f}% of n) already account for 100% of net sumR "
      f"(rest net <=0).")

# WR if we strip the tail
print("\nVERDICT 5: edge is broad iff removing top-5 keeps avgR meaningfully >0 (> take-all 0.105). "
      "Tail-dependent iff avgR collapses to ~0 or below take-all after stripping a handful.")
