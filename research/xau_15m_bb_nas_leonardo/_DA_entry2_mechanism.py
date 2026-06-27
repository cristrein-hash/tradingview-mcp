#!/usr/bin/env python3
"""DA Engine2 — MECHANISM reconciliation (why label-precision real but R dead).
Reads _DA_entry2_routcome.json and prints the chain that settles the contradiction:
 universe avgR vs combo avgR vs matched-MF avgR vs NONE avgR. The combo avgR is BELOW universe & random,
 so the killzone+reclaim filter selects a SUB-average slice even though it enriches MON+FORTE labels.
Pure restatement of saved JSON for reproducibility (no new compute). -> stdout."""
import json
from pathlib import Path
HERE=Path(__file__).parent
r=json.load(open(HERE/"_DA_entry2_routcome.json"))
print("UNIVERSE all 4502 : avgR",r['all']['avgR'],"sumR",r['all']['sumR'],"WR",r['all']['WR'])
print("matched MF (58)   : avgR",r['matched_mf']['avgR'],"WR",r['matched_mf']['WR'])
print("matched MEDFRACO  : avgR",r['matched_medfraco']['avgR'])
print("NONE (4305)       : avgR",r['none']['avgR'])
print("ALL bottoms (197) : avgR",r['all_bottoms']['avgR'],"sumR",r['all_bottoms']['sumR'])
print()
for name,c in r['combos'].items():
    o=c['overall']
    print(f"{name}: n{o['n']} avgR {o['avgR']} sumR {o['sumR']} WR {o['WR']} | nullavg {c['null_avgR_mean']} p_sumR {c['p_sumR']}")
print("\nCHAIN: combo avgR (~0.02) < universe avgR (0.105) = random-same-n mean. The label-precision filter")
print("strips the high-R tail. Selecting Engine-2's TAKEN set is WORSE than taking everything or random.")
