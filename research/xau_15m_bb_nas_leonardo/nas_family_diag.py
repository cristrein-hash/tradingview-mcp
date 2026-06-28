#!/usr/bin/env python3
"""Reproducible diagnostic for the NAS-family flow engine on SUBSTRATE #4.

Why this exists: the task asked whether NAS-recent (and one combined flow axis)
can cut LOSERS while preserving RUNNERS with null_p<0.02. This script materializes
the per-group R-stats that explain WHY the NAS family fails, so the conclusion is
reproducible (no orphan inline analysis). Scoring of any candidate combo is done
through score_flow.py (single source of truth); see run_nas_combos.py.

Run: python3 nas_family_diag.py
"""
import json
from pathlib import Path

HERE = Path(__file__).parent
RECS = [json.loads(l) for l in (HERE / "substrate4_flow.jsonl").read_text().splitlines()]


def stats(rows):
    R = [r["R"] for r in rows]
    if not R:
        return "n=0"
    los = sum(1 for x in R if x <= 0)
    run = sum(1 for x in R if x >= 3)
    return (f"n={len(R):3d} avgR={sum(R)/len(R):+.3f} los={los:3d} "
            f"run={run:2d} sumR={sum(R):+.1f}")


def main():
    print("BASE:", stats(RECS))
    print()
    print("--- NAS family: recent-NAS is WRONG-SIGNED + sparse ---")
    for ft in ["nas_long_16", "nas_any_rec", "h4n_nas_long_rec", "h1n_nas_long_rec"]:
        present = [r for r in RECS if r["flow"].get(ft, 0) >= 1]
        absent = [r for r in RECS if r["flow"].get(ft, 0) == 0]
        print(f"{ft:20s} present>=1: {stats(present)}")
        print(f"{ft:20s} absent ==0: {stats(absent)}")
    print()
    print("--- CHoCH: recent-CHoCH is a regime CONCENTRATOR, not a loser-cut ---")
    for ft in ["choch_any_rec", "h1n_choch_up_rec", "h4n_choch_up_rec"]:
        print(f"{ft:18s} ==1: {stats([r for r in RECS if r['flow'].get(ft) == 1])}")
        print(f"{ft:18s} ==0: {stats([r for r in RECS if r['flow'].get(ft) == 0])}")
    print()
    print("VERDICT: NAS-recent absence cuts only ~9 losers/1 runner (null_p~0.22-0.28,")
    print("not better than random). CHoCH-recent==1 has higher avgR but keeps only ~84")
    print("rows, dropping ~41 of 53 runners (runners_cut/losers_cut ~0.20 >> 0.15) and")
    print("collapsing 2026 to ~0. No NAS-family combo passes the gate. Returning empty.")


if __name__ == "__main__":
    main()
