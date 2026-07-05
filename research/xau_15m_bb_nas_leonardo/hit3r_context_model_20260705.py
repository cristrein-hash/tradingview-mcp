#!/usr/bin/env python3
"""MODELO CONTEXTUAL DIRETO NO LUCRO — logístico L2 sobre trajetória+snapshot vs hit-3R (2026-07-05).
Reformulação do Cris: o alvo é FILTRAR FUNDOS QUE GERAM 3R, não imitar rótulo. Primeira vez no
projeto que features são usadas EM CONTEXTO por um modelo multivariado (até hoje só thresholds).

DESIGN CONGELADO:
  X = trajetória 6-canais×24 pontos (144d, engine v1) + 12 snapshot causais do lab_g
      (legpos60, pullback_depth, rsi_low, g_ema21_dist, g_ema50_dist, g_sweep_depth, g_box96,
       reclaim_atr, g_rec_speed, atr_regime, h1_pos, n_supply_overhead) → 156d, z-score do TREINO.
  y = hit-3R (R3>=3, alvo canónico).
  Modelo: logístico ridge (lambda=1,0 fixo), gradiente 400 iters — sem grid de hiperparâmetros.
  VALIDAÇÃO POR SUB-JANELAS (canon: dentro dos dados, walk-forward):
    fold1 treina ate 2025-06-30, avalia 2025-07-01..2025-12-31
    fold2 treina ate 2025-12-31, avalia 2026-01-01..fim
  Métrica: hit-3R e NET3 do top-decil do score NO PERÍODO DE AVALIAÇÃO vs base do período
  (modelo útil = top-decil >> base fora do treino). Null: permutação de y no treino, 200×."""
import json, bisect, glob, hashlib
import datetime as dt
import numpy as np
from pathlib import Path
HERE = Path(__file__).resolve().parent

GT = HERE / "results" / "ground_truth_bottoms_20260705.json"
sha = hashlib.sha256(GT.read_bytes()).hexdigest()
assert sha == (HERE / "results" / "ground_truth_bottoms_20260705.sha256").read_text().split()[0]
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
W, P = 96, 24

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
    return M.reshape(6, P, W // P).mean(axis=2).reshape(-1)

SNAP = ["legpos60", "pullback_depth", "rsi_low", "g_ema21_dist", "g_ema50_dist", "g_sweep_depth",
        "g_box96", "reclaim_atr", "g_rec_speed", "atr_regime", "h1_pos", "n_supply_overhead"]

def fv(u, k):
    v = u.get(k)
    return float(v) if isinstance(v, (int, float)) and not isinstance(v, bool) else 0.0

keep, X, y, nets, ts = [], [], [], [], []
for u in U:
    r3 = R3.get(u["cj_t"])
    if not r3:
        continue
    m = episode_tensor(u["cj_t"])
    if m is None:
        continue
    keep.append(u)
    X.append(np.concatenate([m, [fv(u, k) for k in SNAP]]))
    y.append(1.0 if r3["R3"] >= 3 else 0.0)
    nets.append(r3["net3"]); ts.append(u["cj_t"])
X = np.array(X); y = np.array(y); nets = np.array(nets); ts = np.array(ts)
print(f"amostra: N{len(X)} · dims {X.shape[1]} · hit-3R base {100*y.mean():.1f}%")

def fit_logistic(Xtr, ytr, lam=1.0, iters=400, lr=0.1):
    mu, sd = Xtr.mean(0), Xtr.std(0) + 1e-9
    Z = (Xtr - mu) / sd
    w = np.zeros(Z.shape[1]); b = 0.0
    for _ in range(iters):
        p = 1 / (1 + np.exp(-(Z @ w + b)))
        g = Z.T @ (p - ytr) / len(ytr) + lam * w / len(ytr)
        w -= lr * g; b -= lr * (p - ytr).mean()
    return w, b, mu, sd

def score(Xe, w, b, mu, sd):
    return ((Xe - mu) / sd) @ w + b

FOLDS = [("fold1 (treino→2025-06 · avalia 2025H2)", dt.datetime(2025, 7, 1), dt.datetime(2026, 1, 1)),
         ("fold2 (treino→2025-12 · avalia 2026)", dt.datetime(2026, 1, 1), dt.datetime(2027, 1, 1))]
rng = np.random.default_rng(11)
out = {}
for tag, ev0, ev1 in FOLDS:
    t0, t1 = ev0.replace(tzinfo=dt.timezone.utc).timestamp(), ev1.replace(tzinfo=dt.timezone.utc).timestamp()
    tr = ts < t0; ev = (ts >= t0) & (ts < t1)
    if ev.sum() < 50:
        print(f"{tag}: avaliação com N{ev.sum()} <50 — inconclusivo por construção"); continue
    w, b, mu, sd = fit_logistic(X[tr], y[tr])
    sc = score(X[ev], w, b, mu, sd)
    k = max(10, int(ev.sum() * 0.10))
    top = np.argsort(-sc)[:k]
    hit_top = y[ev][top].mean(); net_top = nets[ev][top].sum()
    base_ev = y[ev].mean(); net_ev = nets[ev].sum()
    # null: permuta y do treino 200×, re-treina, mesmo top-k
    ge = 0
    for _ in range(200):
        yp = y[tr].copy(); rng.shuffle(yp)
        wp, bp, mup, sdp = fit_logistic(X[tr], yp, iters=150)
        scp = score(X[ev], wp, bp, mup, sdp)
        if y[ev][np.argsort(-scp)[:k]].mean() >= hit_top:
            ge += 1
    print(f"{tag}")
    print(f"  treino N{tr.sum()} (hit {100*y[tr].mean():.1f}%) · avaliação N{ev.sum()} (base hit {100*base_ev:.1f}%, NET {net_ev:+.1f})")
    print(f"  TOP-DECIL fora-do-treino: N{k} · hit-3R {100*hit_top:.1f}% · NET3 {net_top:+.1f} · P(null) {ge/200:.3f}")
    out[tag] = {"k": int(k), "hit_top": round(float(hit_top), 3), "net_top": round(float(net_top), 1),
                "base": round(float(base_ev), 3), "p_null": ge / 200}
    # pesos mais fortes (interpretabilidade)
    idx = np.argsort(-np.abs(w))[:8]
    names = [f"traj[{i//24}:{CHN}]" if (i := int(j)) < 144 else SNAP[i - 144]
             for j in idx for CHN in [["ema", "rsi", "vol", "vshape", "rng", "spd"][int(j) // 24] if j < 144 else ""]][:8]
    print(f"  pesos topo: {[(names[q], round(float(w[idx[q]]), 3)) for q in range(len(idx))]}")
json.dump(out, open(HERE / "results" / "hit3r_context_model_20260705.json", "w"), indent=1)
print("OK → results/hit3r_context_model_20260705.json")
