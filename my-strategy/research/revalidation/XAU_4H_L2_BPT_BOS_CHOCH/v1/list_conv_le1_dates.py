#!/usr/bin/env python3
"""Lista as datas dos 23 trades conv<=1 (removidos) com win/loss, p/ escolher janela de zoom. Verified 2026-06-25."""
import json, collections
from pathlib import Path
V1 = Path(__file__).resolve().parent
SW = json.load(open(V1 / "results/l2_bpt_elimination_sweep.json"))
rem = sorted([r for r in SW if r["conv"] <= 1], key=lambda r: r["dt"])
yr = collections.Counter(r["dt"][:4] for r in rem)
for r in rem:
    print(f"  {'WIN ' if r['realR']>0 else 'LOSS'} #{r['b']:>4} {r['dt'][:16]} conv={r['conv']} bear={r['is_bear']} realR={r['realR']:+.1f} mfe={r['mfe']:.1f}")
print("por ano:", dict(yr))
