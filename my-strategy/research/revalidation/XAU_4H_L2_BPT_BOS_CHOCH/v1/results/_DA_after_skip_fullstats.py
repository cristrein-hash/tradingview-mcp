#!/usr/bin/env python3
"""Foto completa SE aprovar os 31 cortes (conv≤1 ∪ bear_leg_refined) — régua oficial SL_CONTEXT+let-run, custo 0.35R.
Total trades, winners, losers, WR, sumR, avgR, maxDD, streak; baseline vs pós-corte. Calibracao 276. Verified 2026-06-25."""
import csv
from pathlib import Path
V1 = Path(__file__).resolve().parents[1]
COST = 0.35
REG = {int(r["bar_idx"]): r for r in csv.DictReader(open(V1 / "results/l2_bpt_regua_structural.csv"))}
TAB = {int(r["b"]): r for r in csv.DictReader(open(V1 / "results/l2_bpt_conv_bear_overlap_table.csv"))}
rows = []
for b, t in TAB.items():
    if b not in REG: continue
    net = float(REG[b]["letrun_struct"]) - COST
    rows.append({"b": b, "net": net, "letrun": float(REG[b]["letrun_struct"]),
                 "cut": (t["rm_conv"] == "1" or t["rm_blr"] == "1")})

def full(rs, label):
    n = len(rs); W = sum(1 for r in rs if r["net"] > 0); Lz = n - W
    sumR = sum(r["net"] for r in rs)
    cum = peak = mdd = ls = best = 0
    for r in sorted(rs, key=lambda x: x["b"]):
        cum += r["net"]; peak = max(peak, cum); mdd = max(mdd, peak - cum)
        ls = 0 if r["net"] > 0 else ls + 1; best = max(best, ls)
    run = sum(1 for r in rs if r["letrun"] >= 5)
    print(f"{label:>20}: trades={n} | winners={W} losers={Lz} | WR={100*W/n:.1f}% | sumR={sumR:+.1f} avgR={sumR/n:+.3f} | maxDD={mdd:.1f} | maxLossStreak={best} | runners(≥5R)={run}")

full(rows, "BASELINE (245)")
full([r for r in rows if not r["cut"]], "PÓS-CORTE (214)")
cutset = [r for r in rows if r["cut"]]
print(f"\ncortados: {len(cutset)} | winners cortados={sum(1 for r in cutset if r['net']>0)} losers cortados={sum(1 for r in cutset if r['net']<=0)} | sumR removido={sum(r['net'] for r in cutset):+.1f}")
