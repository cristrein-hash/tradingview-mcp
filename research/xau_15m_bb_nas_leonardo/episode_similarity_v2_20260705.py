#!/usr/bin/env python3
"""SIMILARIDADE EPISÓDICA v2 — cabeça do score, ablação e contrastivo (2026-07-05).
v1 provou: trajetória 6-canais ordena Cris-ness (decis monotónicos 19→0, P<0,002 pipeline-null).
v2, DECLARADO EM BLOCO (3 painéis, todos reportados, nenhum threshold escolhido depois):
  A) precision@k na cabeça (k=25/50/100/200) com banda null (500 perms) — onde a similaridade
     concentra; hit-3R e NET3 de cada cabeça (objetivo lucro junto com objetivo rótulo).
  B) ablação de canais: score refeito removendo 1 canal de cada vez (LOO de canal) — quem carrega.
  C) score CONTRASTIVO: −d(k5 Cris) + d(k5 não-Cris vizinhos) — perto dos teus E longe dos sósias;
     mesma avaliação A.
Design herdado congelado de v1 (6 canais, 96→24, escala robusta, k=5, LOO)."""
import json, bisect, glob, hashlib
import numpy as np
from pathlib import Path
HERE = Path(__file__).resolve().parent

GT = HERE / "results" / "ground_truth_bottoms_20260705.json"
sha = hashlib.sha256(GT.read_bytes()).hexdigest()
assert sha == (HERE / "results" / "ground_truth_bottoms_20260705.sha256").read_text().split()[0]
gt = json.load(open(GT)); assert len(gt) == 60
U = [json.loads(l) for l in open(HERE / "results" / "lab_g_candidates.jsonl")]
R3 = {json.loads(l)["cj_t"]: json.loads(l) for l in open(HERE / "results" / "r3_target_universe_20260704.jsonl")}
series = {}
for p in sorted(glob.glob(str(HERE / "primitives" / "*.primitives.json"))):
    for b in json.load(open(p))["series"]:
        series.setdefault(b["t"], b)
S = sorted(series.values(), key=lambda b: b["t"]); TS = [b["t"] for b in S]
C = np.array([b["c"] for b in S]); H = np.array([b["h"] for b in S]); L = np.array([b["l"] for b in S])
V = np.array([float(b.get("v") or 0) for b in S]); RSI = np.array([float(b.get("rsi") or 50) for b in S])
ATR = np.array([float(b.get("atr") or 5.0) for b in S]); EMA = np.array([float(b.get("ema21") or c) for c, b in zip(C, S)])
for u in U:
    u["is_cris60"] = 0
UT = sorted(range(len(U)), key=lambda k: U[k]["t"]); T = [U[k]["t"] for k in UT]
for g in gt:
    j = bisect.bisect_left(T, g["flush_t"] - 7200); best = None
    while j < len(T) and T[j] <= g["flush_t"] + 7200:
        u = U[UT[j]]
        if best is None or abs(u["t"] - g["flush_t"]) < abs(best["t"] - g["flush_t"]):
            best = u
        j += 1
    if best:
        best["is_cris60"] = 1
W, P = 96, 24
CH = ["ema_dist", "rsi", "vol", "v_shape", "range", "speed"]

def episode_tensor(cj_t):
    i = bisect.bisect_right(TS, cj_t) - 1
    if i < W:
        return None
    sl = slice(i - W + 1, i + 1)
    atr = np.maximum(ATR[sl], 0.01)
    vmed = np.median(V[sl]) or 1.0
    M = np.stack([(C[sl] - EMA[sl]) / atr, RSI[sl] / 100.0, V[sl] / vmed,
                  (C[sl] - np.minimum.accumulate(L[sl])) / atr, (H[sl] - L[sl]) / atr,
                  np.diff(C[max(0, i - W):i + 1])[-W:] / atr])
    return M.reshape(6, P, W // P).mean(axis=2)

keep = []; X = []
for u in U:
    m = episode_tensor(u["cj_t"])
    if m is not None:
        keep.append(u); X.append(m)
X = np.array(X)
med = np.median(X, axis=(0, 2), keepdims=True)
iqr = np.quantile(X, 0.75, axis=(0, 2), keepdims=True) - np.quantile(X, 0.25, axis=(0, 2), keepdims=True)
XN = (X - med) / np.maximum(iqr, 1e-6)               # N×6×24 (mantém eixo canal p/ ablação)
lab = np.array([u["is_cris60"] for u in keep], dtype=bool)
N = len(keep); NPOS = int(lab.sum())

def scores(Xn_flat, ref_mask, k=5):
    R = Xn_flat[ref_mask]
    d = np.sqrt(((Xn_flat[:, None, :] - R[None, :, :]) ** 2).sum(-1))
    sc = -np.sort(d, axis=1)[:, :k].mean(axis=1)
    for r, gi in enumerate(np.where(ref_mask)[0]):
        sc[gi] = -np.sort(np.delete(d[gi], r))[:k].mean()
    return sc

def head_panel(sc, tag, nulls=None):
    order = np.argsort(-sc)
    print(f"  {tag}")
    out = {}
    for k in (25, 50, 100, 200):
        idx = order[:k]; nc = int(lab[idx].sum())
        h3 = net = cnt = 0
        for ii in idx:
            r3 = R3.get(keep[ii]["cj_t"])
            if r3:
                cnt += 1; h3 += r3["R3"] >= 3; net += r3["net3"]
        nb = ""
        if nulls is not None:
            q95 = np.quantile(nulls[k], 0.95); pv = float((nulls[k] >= nc).mean())
            nb = f" | null q95 {q95:.0f} P {pv:.3f}"
        print(f"    top{k:>4}: cris {nc:>2} (prec {100*nc/k:>5.1f}%) hit3R {100*h3/max(1,cnt):>5.1f}% "
              f"NET3 {net:>+7.1f}{nb}")
        out[k] = {"cris": nc, "prec": nc / k, "hit3r": h3 / max(1, cnt), "net3": round(float(net), 1)}
    return out

# ---- A) cabeça com null ----
rng = np.random.default_rng(7)
Xf = XN.reshape(N, -1)
print("A) CABEÇA DO SCORE (kNN Cris, v1)")
nulls = {k: [] for k in (25, 50, 100, 200)}
for _ in range(500):
    pm = np.zeros(N, dtype=bool); pm[rng.choice(N, NPOS, replace=False)] = True
    sc = scores(Xf, pm)
    o = np.argsort(-sc)
    for k in nulls:
        nulls[k].append(int(pm[o[:k]].sum()))
nulls = {k: np.array(v) for k, v in nulls.items()}
sc1 = scores(Xf, lab)
resA = head_panel(sc1, "score v1 (−d kNN Cris)", nulls)

# ---- B) ablação de canal ----
print("\nB) ABLAÇÃO (remove 1 canal; cris@top100)")
resB = {}
for ci, nm in enumerate(CH):
    Xa = np.delete(XN, ci, axis=1).reshape(N, -1)
    sca = scores(Xa, lab)
    nc = int(lab[np.argsort(-sca)[:100]].sum())
    resB[nm] = nc
    print(f"    sem {nm:<9}: cris@100 = {nc}")
print(f"    (completo: {resA[100]['cris']})")

# ---- C) contrastivo ----
print("\nC) CONTRASTIVO (−d kNN Cris + d kNN sósias)")
Rn = Xf[~lab]
dn = np.sqrt(((Xf[:, None, :] - Rn[None, ::8, :]) ** 2).sum(-1))   # subamostra 1/8 dos negativos (custo)
dneg = np.sort(dn, axis=1)[:, 1:6].mean(axis=1)                    # exclui self (d=0) p/ negativos
sc2 = sc1 + dneg
resC = head_panel(sc2, "score contrastivo", nulls)

json.dump({"A_head": resA, "B_ablation": resB, "C_contrastive": resC},
          open(HERE / "results" / "episode_similarity_v2_20260705.json", "w"), indent=1)
print("\nOK → results/episode_similarity_v2_20260705.json")
