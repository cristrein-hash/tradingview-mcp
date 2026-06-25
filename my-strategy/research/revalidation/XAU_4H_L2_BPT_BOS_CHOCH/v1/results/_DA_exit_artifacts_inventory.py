#!/usr/bin/env python3
"""INVENTARIO — o que cada artefato de SL/exit ja tem POR-TRADE (R sob qual SL/exit?), p/ resgatar e comparar SEM
re-simular. So lista header+n+amostra. Verified 2026-06-25."""
import csv
from pathlib import Path
V1 = Path(__file__).resolve().parents[1]
FILES = ["results/l2_bpt_sl_context_policy_results.csv", "results/l2_bpt_exit_calibration_full276.csv",
         "results/l2_bpt_outcome_exit_inventory.csv", "results/l2_bpt_prior_layers_under_exit_target_276.csv",
         "results/l2_bpt_sl_structural_performance.csv", "results/l2_bpt_real_outcome_sl_validation.csv",
         "results/l2_bpt_sl_structural_models.csv", "results/l2_bpt_exit_vs_reading_decomposition_276.csv"]
for f in FILES:
    p = V1 / f
    if not p.exists(): print(f"[MISSING] {f}\n"); continue
    rows = list(csv.DictReader(open(p)))
    cols = [c for c in rows[0].keys() if c] if rows else []
    print(f"[{Path(f).name}] n={len(rows)}")
    print("  cols:", cols)
    if rows: print("  row0:", {k: rows[0][k] for k in list(cols)[:8]})
    print()
