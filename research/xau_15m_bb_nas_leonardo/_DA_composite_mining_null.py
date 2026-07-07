#!/usr/bin/env python3
"""DA ATTACK 1: MINING-NULL COMPOSTO (best-of-6 familias sob outcomes permutados).
Re-corre a SELECAO INTEIRA sob ruido: para cada shuffle de y, corre LOO das 6 familias,
pega o MELHOR oof_hit, e ve a distribuicao do best-of-6. P(best6_null >= 0.647)?
"""
import sys, json, glob, os
sys.path.insert(0, "/Users/cristrein/tradingview-mcp/research/xau_15m_bb_nas_leonardo")
import numpy as np
from mtf_kit import _loo
from agent_ctx_kit import ENTRIES

HERE = "/Users/cristrein/tradingview-mcp/research/xau_15m_bb_nas_leonardo"
NS = [e["n"] for e in ENTRIES]
y = np.array([e["out"] for e in ENTRIES], dtype=float)

# localiza os 6 feature files (root ou results/)
FAMILIES = {
    "h4_phase":            f"{HERE}/results/mtf_feat_h4_phase.json",
    "d1_phase":            f"{HERE}/mtf_feat_d1_phase.json",
    "leg_maturity_nested": f"{HERE}/results/mtf_feat_leg_maturity_nested.json",
    "htf_demand_retest":   f"{HERE}/results/mtf_feat_htf_demand_retest.json",
    "fractal_alignment":   f"{HERE}/mtf_feat_fractal_alignment.json",
    "htf_position_room":   f"{HERE}/results/mtf_feat_htf_position_room.json",
}

def load_X(path):
    rows = json.load(open(path))
    by_n = {r["n"]: r for r in rows}
    keys = [k for k in rows[0].keys() if k != "n"]
    X = np.array([[by_n[n][k] for k in keys] for n in NS], dtype=float)
    X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)
    mu = X.mean(0); sd = X.std(0) + 1e-9
    return (X - mu) / sd, keys

Xs = {}; KEYS = {}
for k, p in FAMILIES.items():
    if not os.path.exists(p):
        print(f"[MISSING] {k}: {p}"); continue
    Xs[k], KEYS[k] = load_X(p)
    print(f"loaded {k:22s} shape={Xs[k].shape}")

# --- observado: oof_hit real de cada familia (= y[keep].mean(), consistente com o null) ---
print("\n=== OBSERVADO (LOO com y real) ===")
obs = {}
for k in Xs:
    P = _loo(Xs[k], y); keep = P > 0.5
    obs[k] = float(y[keep].mean()) if keep.sum() else float("nan")
    print(f"  {k:22s} oof_hit={obs[k]:.3f}  N_keep={int(keep.sum())}")
best_obs = max(obs.values())
best_fam = max(obs, key=obs.get)
print(f"  BEST-OF-6 observado = {best_obs:.3f} ({best_fam})")

# --- mining-null COMPOSTO: shuffle partilhado, best-of-6 por iteracao ---
NPERM = 200
rng = np.random.default_rng(7)
best_null = []
per_fam_null = {k: [] for k in Xs}
for it in range(NPERM):
    yp = rng.permutation(y)
    vals = []
    for k in Xs:
        Pp = _loo(Xs[k], yp); kp = Pp > 0.5
        v = float(yp[kp].mean()) if kp.sum() else float("nan")
        per_fam_null[k].append(v)
        if not np.isnan(v): vals.append(v)
    best_null.append(max(vals) if vals else float("nan"))
    if (it+1) % 50 == 0: print(f"  ...perm {it+1}/{NPERM}")

best_null = np.array([v for v in best_null if not np.isnan(v)])
TARGET = 0.647
p_target = float((best_null >= TARGET).mean())
p_best = float((best_null >= best_obs).mean())
print("\n=== RESULTADO MINING-NULL COMPOSTO (best-of-6) ===")
print(f"  N perms validas          = {len(best_null)}")
print(f"  best6_null mediana        = {np.median(best_null):.3f}")
print(f"  best6_null q90            = {np.quantile(best_null,0.90):.3f}")
print(f"  best6_null q95            = {np.quantile(best_null,0.95):.3f}")
print(f"  best6_null max            = {best_null.max():.3f}")
print(f"  P(best6_null >= 0.647)    = {p_target:.3f}")
print(f"  P(best6_null >= best_obs) = {p_best:.3f}")

# comparacao: null MARGINAL do htf_demand_retest sozinho (o que o kit reporta)
marg = np.array([v for v in per_fam_null["htf_demand_retest"] if not np.isnan(v)])
print(f"\n  [ref] null MARGINAL htf_demand_retest: mediana={np.median(marg):.3f} "
      f"P(>=0.647)={float((marg>=0.647).mean()):.3f}")

json.dump({"obs": obs, "best_obs": best_obs, "best_fam": best_fam,
           "p_best6_ge_0647": p_target, "p_best6_ge_bestobs": p_best,
           "best6_median": float(np.median(best_null)), "best6_q95": float(np.quantile(best_null,0.95)),
           "marginal_p": float((marg>=0.647).mean())},
          open(f"{HERE}/results/_DA_composite_mining_null_OUT.json","w"), indent=1)
print("\nsaved results/_DA_composite_mining_null_OUT.json")
