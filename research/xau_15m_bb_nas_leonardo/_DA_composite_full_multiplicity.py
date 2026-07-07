#!/usr/bin/env python3
"""DA ATTACK 1b: multiplicidade COMPLETA = 6 familias + 7 configs de sintese (concatenacoes).
best-of-13 null. P(best13_null >= 0.647)?
"""
import sys, json, os
sys.path.insert(0, "/Users/cristrein/tradingview-mcp/research/xau_15m_bb_nas_leonardo")
import numpy as np
from mtf_kit import _loo
from agent_ctx_kit import ENTRIES

HERE = "/Users/cristrein/tradingview-mcp/research/xau_15m_bb_nas_leonardo"
NS = [e["n"] for e in ENTRIES]
y = np.array([e["out"] for e in ENTRIES], dtype=float)

FAM = {
    "h4_phase":            f"{HERE}/results/mtf_feat_h4_phase.json",
    "d1_phase":            f"{HERE}/mtf_feat_d1_phase.json",
    "leg_maturity_nested": f"{HERE}/results/mtf_feat_leg_maturity_nested.json",
    "htf_demand_retest":   f"{HERE}/results/mtf_feat_htf_demand_retest.json",
    "fractal_alignment":   f"{HERE}/mtf_feat_fractal_alignment.json",
    "htf_position_room":   f"{HERE}/results/mtf_feat_htf_position_room.json",
}
def load_raw(path):
    rows = json.load(open(path)); by_n = {r["n"]: r for r in rows}
    keys = [k for k in rows[0].keys() if k != "n"]
    X = np.array([[by_n[n][k] for k in keys] for n in NS], dtype=float)
    return np.nan_to_num(X)
RAW = {k: load_raw(p) for k, p in FAM.items()}

def std(X):
    mu = X.mean(0); sd = X.std(0) + 1e-9; return (X - mu) / sd

# 13 candidatos: 6 familias singleton + 7 sinteses (concat com a demanda + o all-6)
cands = {k: std(RAW[k]) for k in RAW}
d = "htf_demand_retest"
synth = {
    "S_demand+position":  [d, "htf_position_room"],
    "S_demand+fractal":   [d, "fractal_alignment"],
    "S_demand+h4":        [d, "h4_phase"],
    "S_demand+legmat":    [d, "leg_maturity_nested"],
    "S_demand+d1":        [d, "d1_phase"],
    "S_demand+pos+frac":  [d, "htf_position_room", "fractal_alignment"],
    "S_all6":             list(RAW.keys()),
}
for name, fams in synth.items():
    cands[name] = std(np.concatenate([RAW[f] for f in fams], axis=1))
print(f"candidatos totais: {len(cands)} (6 familias + {len(synth)} sinteses)")

def oof(Xs, yy):
    P = _loo(Xs, yy); keep = P > 0.5
    return float(yy[keep].mean()) if keep.sum() else float("nan")

print("\n=== OBSERVADO por candidato ===")
obs = {}
for k, Xs in cands.items():
    obs[k] = oof(Xs, y); print(f"  {k:22s} oof_hit={obs[k]:.3f}")
best_obs = max(obs.values()); best_k = max(obs, key=obs.get)
print(f"  BEST observado = {best_obs:.3f} ({best_k})")

NPERM = 200
rng = np.random.default_rng(7)
best_null = []
for it in range(NPERM):
    yp = rng.permutation(y)
    vals = [oof(Xs, yp) for Xs in cands.values()]
    vals = [v for v in vals if not np.isnan(v)]
    best_null.append(max(vals))
    if (it+1) % 25 == 0: print(f"  ...perm {it+1}/{NPERM}")
best_null = np.array(best_null)

p647 = float((best_null >= 0.647).mean())
pbo = float((best_null >= best_obs).mean())
out = dict(n_cands=len(cands), best_obs=best_obs, best_k=best_k,
           p_ge_0647=p647, p_ge_bestobs=pbo,
           median=float(np.median(best_null)), q90=float(np.quantile(best_null,.9)),
           q95=float(np.quantile(best_null,.95)), mx=float(best_null.max()))
print("\n=== best-of-13 NULL ===")
for k, v in out.items(): print(f"  {k}: {v}")
json.dump(out, open(f"{HERE}/results/_DA_full_multiplicity_OUT.json","w"), indent=1)
print("saved results/_DA_full_multiplicity_OUT.json")
