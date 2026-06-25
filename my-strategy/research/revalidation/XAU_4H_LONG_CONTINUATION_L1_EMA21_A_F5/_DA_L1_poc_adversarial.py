#!/usr/bin/env python3
"""DEVIL'S ADVOCATE — adversarial audit of dist_poc<=0.35 loser-cut on L1 EMA21 (n=34).
Tests: (1) full dist_poc distribution by win/loss, (2) threshold fragility +/-20%,
(3) the critical boundary winner that breaks the cut, (4) the 'edge of cliff' structure,
(5) the 2 winners sitting AT the loser median to test the 'WALL' rationale.
Reads l1_contrastive_features.json. Verified 2026-06-25."""
import json, statistics as st
from pathlib import Path
T = json.load(open(Path(__file__).parent / "l1_contrastive_features.json"))
for t in T:
    t["dist_poc"] = float(t["dist_poc"]) if t["dist_poc"] not in (None, "None", "") else None
    t["R"] = float(t["R"]); t["mfe"] = float(t["mfe"]) if t["mfe"] not in (None,"None","") else None
    t["win"] = (t["win"] in (True, "True")); t["runner"] = (t["runner"] in (True, "True"))

W = sorted([t["dist_poc"] for t in T if t["win"] and t["dist_poc"] is not None])
Lz = sorted([t["dist_poc"] for t in T if not t["win"] and t["dist_poc"] is not None])
print("N total", len(T), "with poc", sum(1 for t in T if t["dist_poc"] is not None))
print("WINNER dist_poc:", [round(x, 3) for x in W])
print("LOSER  dist_poc:", [round(x, 3) for x in Lz])
print(f"winner med {st.median(W):.3f}  loser med {st.median(Lz):.3f}")

print("\n=== THRESHOLD FRAGILITY (+/-20% around 0.354 = 0.283..0.425) ===")
for thr in [0.28, 0.30, 0.32, 0.354, 0.373, 0.38, 0.40, 0.42]:
    cut = [t for t in T if t["dist_poc"] is not None and t["dist_poc"] <= thr]
    lc = sum(1 for t in cut if not t["win"]); wc = sum(1 for t in cut if t["win"]); rc = sum(1 for t in cut if t["runner"])
    print(f"  thr<={thr:.3f}: cut {len(cut):2d} = {lc}L/{wc}W/{rc}run")

print("\n=== CLIFF EDGE: nearest winner above the cut boundary ===")
lowest_winner = min(W)
print(f"  lowest-dist_poc WINNER = {lowest_winner:.3f}")
print(f"  highest loser still inside cut (<=0.354) = {max(x for x in Lz if x<=0.354):.3f}")
print(f"  gap to first winner = {lowest_winner - max(x for x in Lz if x<=0.354):.4f} ATR")
print(f"  -> a +6% threshold move (0.354->0.375) already eats winner #{lowest_winner:.3f}")

print("\n=== 'WALL' RATIONALE STRESS: winners that sit BELOW the loser median (0.41) ===")
below_med_w = [t for t in T if t["win"] and t["dist_poc"] is not None and t["dist_poc"] < 0.50]
print(f"  winners with dist_poc<0.50 ATR (near-POC, should be 'WALL' per rationale): {len(below_med_w)}")
for t in sorted(below_med_w, key=lambda x: x["dist_poc"]):
    print(f"    {t['ts'][:10]} dist_poc={t['dist_poc']:.3f} R={t['R']:+.2f} mfe={t['mfe']}")

print("\n=== LOSERS NOT CUT (survive the filter): residual losers ===")
surv_los = [t for t in T if not t["win"] and t["dist_poc"] is not None and t["dist_poc"] > 0.354]
print(f"  {len(surv_los)} losers survive (dist_poc>0.354) -> filter leaves half the losers")
for t in sorted(surv_los, key=lambda x: x["dist_poc"]):
    print(f"    {t['ts'][:10]} dist_poc={t['dist_poc']:.3f} R={t['R']:+.2f}")

print("\nIn-sample n=34. Calibration, not validation. P(null>=real)~0.05 for BEST of thousands.")
