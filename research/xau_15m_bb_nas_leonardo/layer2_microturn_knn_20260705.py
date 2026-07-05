#!/usr/bin/env python3
"""LAYER 2 — MICRO-VIRADA kNN: a forma barra-a-barra do V (2026-07-05).
Família da memória nunca testada contra o rótulo: micro-forma/sequência da reversão. Escala da
VIRADA (não do contexto): 12 barras conhecidas no cj = 8 pré-flush + flush + 3 pós (cj=flush+3).
Canais por barra (causais): corpo/ATR · pavio-sup/ATR · pavio-inf/ATR · retorno close/ATR → 48 dims.
REFERÊNCIAS: candidatos ESTRITAMENTE casados aos fundos GT (|flush−flo|<=1 ATR, ±8h) — recall
estrito desde a definição. Score = −dist média aos k=3 vizinhos GT (LOO nos próprios).
AVALIAÇÃO: precision@head (25/50/100/200) em rótulo-estrito E hit-3R/NET; null de permutação
(300×, pipeline inteiro). Ex-CASCEX. Se a cabeça concentrar >= 3× base com hit>=40%, há engine."""
import json, bisect, hashlib
import numpy as np
from pathlib import Path
HERE = Path(__file__).resolve().parent
src = (HERE / "macro_leg_position_veto_20260705.py").read_text()
exec(src.split("VETOS = {")[0])
GT = HERE / "results" / "ground_truth_bottoms_20260705.json"
assert hashlib.sha256(GT.read_bytes()).hexdigest() == (HERE / "results" / "ground_truth_bottoms_20260705.sha256").read_text().split()[0]
gt = json.load(open(GT))

O = np.array([b["o"] for b in S]); H = np.array([b["h"] for b in S])
L = np.array([b["l"] for b in S]); C = np.array([b["c"] for b in S])
ATR = np.array([float(b.get("atr") or 5.0) for b in S])

def micro_tensor(u):
    fi = bisect.bisect_right(TS, u["t"]) - 1
    if fi < 8 or fi + 3 >= len(S):
        return None
    sl = slice(fi - 8, fi + 4)   # 12 barras, todas <= cj (= fi+3)
    atr = max(0.01, ATR[fi])
    body = (C[sl] - O[sl]) / atr
    upw = (H[sl] - np.maximum(O[sl], C[sl])) / atr
    lww = (np.minimum(O[sl], C[sl]) - L[sl]) / atr
    ret = np.diff(C[fi - 9:fi + 4]) / atr
    return np.concatenate([body, upw, lww, ret])

# rótulo estrito
for u in U:
    u["_gt"] = 0
USORT = sorted([u for u in U if u["cj_t"] in R3], key=lambda x: x["cj_t"])
TT = [u["cj_t"] for u in USORT]
for g in gt:
    j = bisect.bisect_left(TT, g["flush_t"] - 8 * 3600); best = None
    while j < len(TT) and TT[j] <= g["flush_t"] + 8 * 3600:
        u = USORT[j]
        flo_u = u["g_sl"] + 0.1 * u["g_atr"]
        if abs(flo_u - g["flush_low"]) <= (u.get("g_atr") or 5.0):
            if best is None or abs(u["cj_t"] - g["flush_t"]) < abs(best["cj_t"] - g["flush_t"]):
                best = u
        j += 1
    if best is not None:
        best["_gt"] = 1

def is_cascex_member(u):
    if cascade(u["cj_t"]) < 4:
        return False
    if not (fv(u, "reclaim_atr", 0) >= 1.5 and (fv(u, "in_demand", 0) == 1 or fv(u, "dist_demand_atr", 9) <= 0.5)
            and fv(u, "h1_rsi", 99) <= 42):
        return False
    ml = macro_leg(u["cj_t"])
    return ml["vel"] < 0.10 and ml["recent_frac"] < 0.5

keep, X = [], []
for u in USORT:
    if is_cascex_member(u):
        continue
    m = micro_tensor(u)
    if m is None:
        continue
    keep.append(u); X.append(m)
X = np.array(X)
med = np.median(X, axis=0, keepdims=True)
iqr = np.quantile(X, 0.75, axis=0, keepdims=True) - np.quantile(X, 0.25, axis=0, keepdims=True)
XN = (X - med) / np.maximum(iqr, 1e-6)
lab = np.array([u["_gt"] for u in keep], dtype=bool)
N = len(keep); NPOS = int(lab.sum())
print(f"amostra ex-CASCEX: N{N} · GT-estritos {NPOS}")

def knn(ref_mask, k=3):
    R = XN[ref_mask]
    d = np.sqrt(((XN[:, None, :] - R[None, :, :]) ** 2).sum(-1))
    sc = -np.sort(d, axis=1)[:, :k].mean(axis=1)
    for r, gi in enumerate(np.where(ref_mask)[0]):
        sc[gi] = -np.sort(np.delete(d[gi], r))[:k].mean()
    return sc

sc = knn(lab)
order = np.argsort(-sc)
rng = np.random.default_rng(41)
nulls = {kk: [] for kk in (25, 50, 100, 200)}
for _ in range(300):
    pm = np.zeros(N, dtype=bool); pm[rng.choice(N, NPOS, replace=False)] = True
    o = np.argsort(-knn(pm))
    for kk in nulls:
        nulls[kk].append(int(pm[o[:kk]].sum()))
print(f"base GT-rate: {100*NPOS/N:.2f}%")
for kk in (25, 50, 100, 200):
    idx = order[:kk]; nc = int(lab[idx].sum())
    h3 = net = 0
    for ii in idx:
        r3 = R3[keep[ii]["cj_t"]]
        h3 += r3["R3"] >= 3; net += r3["net3"]
    q95 = float(np.quantile(nulls[kk], 0.95)); p = float((np.array(nulls[kk]) >= nc).mean())
    print(f"  top{kk:>4}: GT {nc:>2} (prec {100*nc/kk:>5.1f}%) hit3R {100*h3/kk:>5.1f}% NET {net:>+7.1f} "
          f"| null q95 {q95:.0f} P {p:.3f}")
json.dump({"n": N, "pos": NPOS,
           "heads": {str(kk): {"gt": int(lab[order[:kk]].sum())} for kk in (25, 50, 100, 200)}},
          open(HERE / "results" / "layer2_microturn_knn_20260705.json", "w"), indent=1)
print("OK → results/layer2_microturn_knn_20260705.json")
