#!/usr/bin/env python3
"""Leitor reprodutível dos perfis A/E/B/D por horizonte do l1_exit_review_v2_result.json (read-only)."""
import json
from pathlib import Path
HERE=Path(__file__).resolve().parent
d=json.load(open(HERE/"l1_exit_review_v2_result.json"))
for sn in ['FINAL-24','SCANNER-31-V1','ESTUDO-34']:
    o=d['sets'][sn]; print(f'\n=== {sn} N={o["N"]} ===')
    print(f'{"rule@H":>8} {"sumR":>6} {"WR":>4} {"maxDD":>6} {"strk":>4} {"revW":>4} {"monR":>6} {"bars":>5} {"rcr":>5}')
    for rule in ['A','E','B','D']:
        for H in ['60','150','300','FULL']:
            p=o['by_horizon'][H][rule]
            print(f'{rule+"@"+H:>8} {p["sumR"]:>6} {p["WR"]:>4} {p["maxDD_R"]:>6} {p["streak"]:>4} {p["base_winners_reverted"]:>4} {p["monumental_sumR"]:>6} {p["avg_bars"]:>5} {str(p.get("runner_capture_ratio")):>5}')
        print()
