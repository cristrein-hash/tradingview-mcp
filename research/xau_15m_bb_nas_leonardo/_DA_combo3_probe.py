#!/usr/bin/env python3
"""combo3 family: probe feature distributions on losers vs winners to pick sensible thresholds.
Reproducible. Reads filter_dataset.jsonl directly (same source as filter_harness)."""
import json
from pathlib import Path
HERE = Path(__file__).parent
ROWS = [json.loads(l) for l in (HERE/"filter_dataset.jsonl").read_text().splitlines()]

# dedup like harness to get the BASE taken set
def dedup(cands):
    byblk = {}
    for c in cands: byblk.setdefault(c["block"], []).append(c)
    taken = []
    for blk, cs in byblk.items():
        cs.sort(key=lambda x: x["cj"]); busy = -10**9
        for c in cs:
            if c["cj"] <= busy: continue
            busy = c["exi"]; taken.append(c)
    taken.sort(key=lambda x: x["t"]); return taken

TAKEN = dedup(ROWS)
win = [c for c in TAKEN if c["win"]]
los = [c for c in TAKEN if not c["win"]]
big = [c for c in TAKEN if c["R"] >= 3]
print(f"taken={len(TAKEN)} win={len(win)} los={len(los)} big={len(big)}")

FEATS = ["buy_bub_w_leg","buy_bub_L_leg","buy_bub_w_w24","nas_short_leg","nas_short_w24",
         "dist_ema_atr","leg_ext_atr","room_above_atr","rsi","h1_pos","h1_dist","disp4_atr",
         "dist_supply_atr","vpnode_dist_atr","macro_retr","path_eff","h1_eff","h4_eff",
         "atr_regime","h4_pos","dist_demand_atr","regime_age_h","buy_sell_ratio4"]

import statistics as st
def summ(vals):
    vals = [v for v in vals if v is not None]
    if not vals: return "all-None"
    vals.sort()
    q = lambda p: vals[min(len(vals)-1, int(p*len(vals)))]
    return f"n={len(vals)} min={vals[0]:.2f} q25={q(.25):.2f} med={q(.5):.2f} q75={q(.75):.2f} q90={q(.9):.2f} max={vals[-1]:.2f}"

for f in FEATS:
    wv = [c.get(f) for c in win]
    lv = [c.get(f) for c in los]
    print(f"\n== {f} ==")
    print(f"  WIN: {summ(wv)}")
    print(f"  LOS: {summ(lv)}")
