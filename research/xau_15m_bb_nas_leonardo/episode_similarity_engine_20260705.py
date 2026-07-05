#!/usr/bin/env python3
"""ENGINE DE SIMILARIDADE EPISÓDICA — leitura contextual case-based vs rótulo Cris-60 (2026-07-05).
MUDANÇA DE PARADIGMA (pedido do Cris): sair de thresholds binários/ternários sobre snapshots.
Cada candidato = TRAJETÓRIA multi-canal das 96 barras até à confirmação (cj). A pergunta deixa de
ser "que corte em que feature?" e passa a ser "este episódio DESENROLA-SE como um episódio do Cris?"
— k-NN sobre a forma completa do episódio (case-based reasoning), família nunca testada no projeto.

DESIGN CONGELADO ANTES DE VER RESULTADOS (zero tuning pós-hoc):
  canais (todos causais, janela = 96 barras terminando na barra cj inclusive):
    c1 (close−ema21)/atr      posição vs média (contexto de tendência local)
    c2 rsi/100                exaustão/momentum
    c3 vol/mediana96          participação
    c4 (close−minlow_run)/atr altura acima do low corrente do episódio (forma do V)
    c5 (high−low)/atr         expansão/compressão de range
    c6 (close−close_prev)/atr velocidade barra-a-barra
  pooling: 96 barras → 24 pontos (média de blocos de 4) → vetor 144-dim por episódio.
  normalização: por canal, escala global robusta (mediana/IQR do universo) — preserva amplitude
  relativa entre episódios (a profundidade IMPORTA), remove só diferença de unidade entre canais.
  score(candidato) = −distância euclidiana média aos k=5 vizinhos mais próximos entre os 59 do
  Cris (LOO: um positivo nunca se vê a si próprio).
AVALIAÇÃO (dois objetivos): enriquecimento is_cris60 por decil de score (prec/recall) E hit-3R/NET3
do pocket top-decil. Null: permutação do rótulo 500× recomputando o enriquecimento do top-decil
(as distâncias não mudam, só quem são as referências — null honesto do pipeline inteiro)."""
import json, bisect, glob, hashlib, random
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

# label
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

W, P = 96, 24  # janela, pontos pós-pooling

def episode_tensor(cj_t):
    i = bisect.bisect_right(TS, cj_t) - 1
    if i < W:
        return None
    sl = slice(i - W + 1, i + 1)
    atr = np.maximum(ATR[sl], 0.01)
    c1 = (C[sl] - EMA[sl]) / atr
    c2 = RSI[sl] / 100.0
    vmed = np.median(V[sl]) or 1.0
    c3 = V[sl] / vmed
    c4 = (C[sl] - np.minimum.accumulate(L[sl])) / atr
    c5 = (H[sl] - L[sl]) / atr
    c6 = np.diff(C[max(0, i - W):i + 1])[-W:] / atr
    M = np.stack([c1, c2, c3, c4, c5, c6])          # 6×96
    return M.reshape(6, P, W // P).mean(axis=2)      # 6×24 (mean-pool)

keep = []; X = []
for u in U:
    m = episode_tensor(u["cj_t"])
    if m is not None:
        keep.append(u); X.append(m)
X = np.array(X)                                      # N×6×24
# escala robusta global por canal
med = np.median(X, axis=(0, 2), keepdims=True)
iqr = np.quantile(X, 0.75, axis=(0, 2), keepdims=True) - np.quantile(X, 0.25, axis=(0, 2), keepdims=True)
Xn = ((X - med) / np.maximum(iqr, 1e-6)).reshape(len(keep), -1)   # N×144
lab = np.array([u["is_cris60"] for u in keep], dtype=bool)
print(f"episódios com tensor: {len(keep)} (de {len(U)}) · positivos {lab.sum()}")

def knn_scores(ref_mask, k=5):
    R = Xn[ref_mask]
    d = np.sqrt(((Xn[:, None, :] - R[None, :, :]) ** 2).sum(-1))   # N×nref
    d_sorted = np.sort(d, axis=1)
    sc = -d_sorted[:, :k].mean(axis=1)
    # LOO: positivos de referência não se veem (distância 0 a si) → usar k vizinhos EXCLUINDO self
    self_idx = np.where(ref_mask)[0]
    for r, gi in enumerate(self_idx):
        dr = np.delete(d[gi], r)
        sc[gi] = -np.sort(dr)[:k].mean()
    return sc

score = knn_scores(lab)
order = np.argsort(-score)
N = len(keep); dec = N // 10
print(f"\n{'decil':>5} {'N':>5} {'cris':>4} {'prec%':>6} {'lift':>5} {'hit3R%':>7} {'NET3':>8} {'rec':>5}")
base = lab.mean()
top_stats = None
for d10 in range(10):
    idx = order[d10 * dec:(d10 + 1) * dec]
    nc = int(lab[idx].sum())
    h3 = net = cnt = 0
    for ii in idx:
        r3 = R3.get(keep[ii]["cj_t"])
        if r3:
            cnt += 1; h3 += r3["R3"] >= 3; net += r3["net3"]
    prec = nc / len(idx)
    print(f"D{d10+1:>4} {len(idx):>5} {nc:>4} {100*prec:>5.1f}% {prec/base:>5.2f} "
          f"{100*h3/max(1,cnt):>6.1f}% {net:>+8.1f} {nc}/{int(lab.sum())}")
    if d10 == 0:
        top_stats = (len(idx), nc, h3, cnt, net)

# null: permutar rótulo 500× (pipeline inteiro re-scored)
random.seed(7); rng = np.random.default_rng(7)
obs_top = top_stats[1]
ge = 0; NPOS = int(lab.sum())
for _ in range(500):
    perm = np.zeros(N, dtype=bool); perm[rng.choice(N, NPOS, replace=False)] = True
    sc = knn_scores(perm)
    o = np.argsort(-sc)[:dec]
    if int(perm[o].sum()) >= obs_top:
        ge += 1
print(f"\nNULL top-decil (500 perms do pipeline inteiro): P(null>=obs {obs_top}) = {ge/500:.3f}")
json.dump({"n": N, "pos": NPOS, "top_decile": {"n": top_stats[0], "cris": top_stats[1],
           "hit3r": round(top_stats[2] / max(1, top_stats[3]), 3), "net3": round(top_stats[4], 1)},
           "p_null": ge / 500},
          open(HERE / "results" / "episode_similarity_engine_20260705.json", "w"), indent=1)
print("OK → results/episode_similarity_engine_20260705.json")
