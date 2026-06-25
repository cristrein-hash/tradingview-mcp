#!/usr/bin/env python3
"""Confere cobertura do SL ESTRUTURAL por-trade p/ os 23 conv<=1, de 3 fontes, p/ re-plotar fiel (canon §4 SL=demand
low -0.1ATR, target +3R). NAO plota — so diagnostico de cobertura/distancias. Verified 2026-06-25."""
import json, csv
from pathlib import Path
V1 = Path(__file__).resolve().parent
SW = json.load(open(V1 / "results/l2_bpt_elimination_sweep.json"))
OUT = {int(r["bar_idx"]): r for r in csv.DictReader(open(V1 / "results/l2_bpt_uncapped_or_proxy_outcomes_276.csv"))}
F = [json.loads(l) for l in open(V1 / "repro_recovery/raw_features_2020_2026.jsonl")]
rem = sorted([r for r in SW if r["conv"] <= 1], key=lambda r: r["dt"])
ids = [r["b"] for r in rem]

def load(path):
    p = V1 / path
    if not p.exists(): return {}
    rows = list(csv.DictReader(open(p)))
    key = "bar_idx" if rows and "bar_idx" in rows[0] else (rows[0] and list(rows[0])[0])
    out = {}
    for r in rows:
        try: out[int(float(r[key]))] = r
        except Exception: pass
    return out

QUAL = load("results/l2_bpt_trade_qualification_matrix.csv")
SLCTX = load("results/l2_bpt_sl_context_policy_results.csv")
BACK = {int(json.loads(l)["bar_idx"]): json.loads(l) for l in open(V1 / "results/l2_bpt_raw_backbone_episodes.jsonl")}
print(f"cobertura nos {len(ids)} trades conv<=1:")
print(f"  qualification_matrix (dist_4h_demand_low_atr/sl_atr): {sum(1 for b in ids if b in QUAL)}/{len(ids)}")
print(f"  sl_context_policy (sl_atr): {sum(1 for b in ids if b in SLCTX)}/{len(ids)}")
print(f"  backbone (dist_demand_atr): {sum(1 for b in ids if b in BACK)}/{len(ids)}")
print()
print(f"{'#':>5} {'date':>11} {'entry':>9} {'qual.dist_dem':>13} {'qual.sl_atr':>11} {'slctx.sl_atr':>12} {'back.dist_dem':>13}")
for r in rem:
    b = r["b"]; entry = float(F[b]["close"])
    q = QUAL.get(b, {}); s = SLCTX.get(b, {}); bk = BACK.get(b, {}).get("supply_demand_raw_mapped", {})
    dd = q.get("dist_4h_demand_low_atr", ""); qsl = q.get("sl_atr", ""); ssl = s.get("sl_atr", ""); bdd = bk.get("dist_demand_atr", "")
    print(f"{b:>5} {r['dt'][:11]:>11} {entry:>9.2f} {str(dd)[:13]:>13} {str(qsl)[:11]:>11} {str(ssl)[:12]:>12} {str(bdd)[:13]:>13}")
