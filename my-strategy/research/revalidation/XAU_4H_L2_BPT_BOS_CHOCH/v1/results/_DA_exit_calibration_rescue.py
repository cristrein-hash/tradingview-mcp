#!/usr/bin/env python3
"""RESGATE — dump completo das tabelas de calibracao de EXIT e SL ja produzidas (exit_calibration_full276,
sl_structural_performance, prior_layers_under_exit_target) p/ decidir o melhor exit/SL SEM re-simular. Verified 2026-06-25."""
import csv
from pathlib import Path
V1 = Path(__file__).resolve().parents[1]

print("=== EXIT CALIBRATION (l2_bpt_exit_calibration_full276.csv) — qual exit ganha? ===")
rows = list(csv.DictReader(open(V1 / "results/l2_bpt_exit_calibration_full276.csv")))
hdr = ["policy", "scope", "cost", "n", "sumR", "avgR", "WR", "PF", "maxDD", "Lstreak", "runner_cap", "giveback", "big_pres"]
print(" | ".join(h[:9].rjust(9) for h in hdr))
for r in rows:
    print(" | ".join(str(r.get(h, ""))[:9].rjust(9) for h in hdr))

print("\n=== SL MODELS PERFORMANCE (l2_bpt_sl_structural_performance.csv) ===")
rows = list(csv.DictReader(open(V1 / "results/l2_bpt_sl_structural_performance.csv")))
hdr = ["model", "n", "WR", "avgR", "sumR", "PF", "maxDD", "streak", "scratch", "stop", "runner", "slATRmed", "sl_gt4ATR"]
print(" | ".join(h[:9].rjust(9) for h in hdr))
for r in rows:
    print(" | ".join(str(r.get(h, ""))[:9].rjust(9) for h in hdr))

print("\n=== PRIOR LAYERS UNDER EXIT TARGET (l2_bpt_prior_layers_under_exit_target_276.csv) ===")
rows = list(csv.DictReader(open(V1 / "results/l2_bpt_prior_layers_under_exit_target_276.csv")))
for r in rows:
    print(f"  {r['layer']:>28}: runners_cut={r['runners_cut']}({r['runners_cut_pct']}%) losers_cut={r['losers_cut']}({r['losers_cut_pct']}%) lift={r['lift_loser_over_runner']} net={r['net_score']} status={r['status']}")
