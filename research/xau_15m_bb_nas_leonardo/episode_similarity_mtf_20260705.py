#!/usr/bin/env python3
"""SIMILARIDADE EPISÓDICA MULTI-ESCALA — campo de visão 24h→16 dias (2026-07-05).
PONTO CEGO identificado: TODAS as leituras de hoje (72 snapshot, convergência, kNN 6ch, contrastivo,
modelo hit-3R) usavam contexto ≤24h (96 barras 15M). Os fundos do Cris são fins de ondas de
capitulação MULTI-DIA; os sósias são dips de ruído em contexto HTF plano. Hipótese: a separação
está na trajetória de escala superior, invisível a 24h.

DESIGN CONGELADO (extensão direta do v1, mesmas regras):
  3 escalas, mesmos 6 canais (ema_dist, rsi, vol, v_shape, range, speed), cada uma 96 unidades →
  pool 24 pontos:
    esc-15M: 96 barras 15M (24h)   — como v1
    esc-1H : 96 horas (4 dias)     — barras 1H agregadas de 15M (close-only causal, hora fechada)
    esc-4H : 96 blocos 4H (16 dias)— idem
  RSI/EMA/ATR recomputados NA escala (Wilder 14 / EMA 21 / ATR 14 sobre barras agregadas).
  Vetor final 3×6×24 = 432d, escala robusta global. kNN k=5 LOO vs rótulo Cris-60 (o rótulo é o
  alvo de detecção; lucro já provado dentro dele). Painéis: cabeça (25/50/100/200) com null 300×,
  decis, e ablação POR ESCALA (só-15M / só-1H / só-4H / pares) — onde mora a separação."""
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
S15 = sorted(series.values(), key=lambda b: b["t"])

def aggregate(bars, step_s):
    out = []; cur = None
    for b in bars:
        k = b["t"] - (b["t"] % step_s)
        if cur is None or cur["t"] != k:
            if cur: out.append(cur)
            cur = {"t": k, "o": b["o"], "h": b["h"], "l": b["l"], "c": b["c"], "v": float(b.get("v") or 0)}
        else:
            cur["h"] = max(cur["h"], b["h"]); cur["l"] = min(cur["l"], b["l"])
            cur["c"] = b["c"]; cur["v"] += float(b.get("v") or 0)
    if cur: out.append(cur)
    return out

def indicators(bars):
    n = len(bars)
    c = np.array([b["c"] for b in bars]); h = np.array([b["h"] for b in bars]); l = np.array([b["l"] for b in bars])
    v = np.array([b["v"] for b in bars])
    ema = np.copy(c); a = 2 / 22
    for i in range(1, n):
        ema[i] = a * c[i] + (1 - a) * ema[i - 1]
    tr = np.maximum(h - l, np.maximum(abs(h - np.roll(c, 1)), abs(l - np.roll(c, 1)))); tr[0] = h[0] - l[0]
    atr = np.copy(tr)
    for i in range(1, n):
        atr[i] = (atr[i - 1] * 13 + tr[i]) / 14
    d = np.diff(c, prepend=c[0]); up = np.where(d > 0, d, 0.0); dn = np.where(d < 0, -d, 0.0)
    au = np.copy(up); ad = np.copy(dn)
    for i in range(1, n):
        au[i] = (au[i - 1] * 13 + up[i]) / 14; ad[i] = (ad[i - 1] * 13 + dn[i]) / 14
    rsi = 100 - 100 / (1 + au / np.maximum(ad, 1e-9))
    return c, h, l, v, ema, np.maximum(atr, 0.01), rsi

SCALES = {}
for nm, step in (("15M", 900), ("1H", 3600), ("4H", 14400)):
    bars = S15 if nm == "15M" else aggregate(S15, step)
    c, h, l, v, ema, atr, rsi = indicators(bars)
    SCALES[nm] = {"t": [b["t"] for b in bars], "c": c, "h": h, "l": l, "v": v, "ema": ema, "atr": atr,
                  "rsi": rsi, "step": step}
W, P = 96, 24

def tensor_at(nm, cj_t):
    sc = SCALES[nm]
    # causal: última barra FECHADA da escala antes/na cj_t
    i = bisect.bisect_right(sc["t"], cj_t - sc["step"])   # barra cujo fecho <= cj_t
    i -= 1
    if nm == "15M":
        i = bisect.bisect_right(sc["t"], cj_t) - 1        # 15M: a barra cj é conhecida ao close
    if i < W:
        return None
    sl = slice(i - W + 1, i + 1)
    atr = sc["atr"][sl]; c = sc["c"][sl]
    vmed = np.median(sc["v"][sl]) or 1.0
    M = np.stack([(c - sc["ema"][sl]) / atr, sc["rsi"][sl] / 100.0, sc["v"][sl] / vmed,
                  (c - np.minimum.accumulate(sc["l"][sl])) / atr, (sc["h"][sl] - sc["l"][sl]) / atr,
                  np.diff(sc["c"][max(0, i - W):i + 1])[-W:] / atr])
    return M.reshape(6, P, W // P).mean(axis=2)

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

keep, TX = [], []
for u in U:
    ms = [tensor_at(nm, u["cj_t"]) for nm in ("15M", "1H", "4H")]
    if any(m is None for m in ms):
        continue
    keep.append(u); TX.append(np.stack(ms))          # 3×6×24
TX = np.array(TX)
med = np.median(TX, axis=(0, 3), keepdims=True)
iqr = np.quantile(TX, 0.75, axis=(0, 3), keepdims=True) - np.quantile(TX, 0.25, axis=(0, 3), keepdims=True)
XN = (TX - med) / np.maximum(iqr, 1e-6)
lab = np.array([u["is_cris60"] for u in keep], dtype=bool)
N = len(keep); NPOS = int(lab.sum())
print(f"episódios: {N} · positivos {NPOS} (perdidos por histórico HTF: {len(U)-N})")

def knn(Xf, ref_mask, k=5):
    R = Xf[ref_mask]
    d = np.sqrt(((Xf[:, None, :] - R[None, :, :]) ** 2).sum(-1))
    sc = -np.sort(d, axis=1)[:, :k].mean(axis=1)
    for r, gi in enumerate(np.where(ref_mask)[0]):
        sc[gi] = -np.sort(np.delete(d[gi], r))[:k].mean()
    return sc

def head(sc, tag, nulls=None):
    order = np.argsort(-sc); out = {}
    for k in (25, 50, 100, 200):
        idx = order[:k]; nc = int(lab[idx].sum())
        h3 = net = cnt = 0
        for ii in idx:
            r3 = R3.get(keep[ii]["cj_t"])
            if r3:
                cnt += 1; h3 += r3["R3"] >= 3; net += r3["net3"]
        nb = ""
        if nulls is not None:
            nb = f" | null q95 {np.quantile(nulls[k],0.95):.0f} P {float((nulls[k]>=nc).mean()):.3f}"
        print(f"    top{k:>4}: cris {nc:>2} (prec {100*nc/k:>5.1f}%) hit3R {100*h3/max(1,cnt):>5.1f}% NET3 {net:>+7.1f}{nb}")
        out[k] = {"cris": nc, "hit3r": round(h3 / max(1, cnt), 3), "net3": round(float(net), 1)}
    return out

COMBOS = {"3-escalas (15M+1H+4H)": (0, 1, 2), "só-15M": (0,), "só-1H": (1,), "só-4H": (2,),
          "1H+4H (só HTF)": (1, 2), "15M+1H": (0, 1)}
rng = np.random.default_rng(3)
res = {}
for tag, dims in COMBOS.items():
    Xf = XN[:, list(dims)].reshape(N, -1)
    sc = knn(Xf, lab)
    nulls = {k: [] for k in (25, 50, 100, 200)}
    for _ in range(300):
        pm = np.zeros(N, dtype=bool); pm[rng.choice(N, NPOS, replace=False)] = True
        o = np.argsort(-knn(Xf, pm))
        for k in nulls:
            nulls[k].append(int(pm[o[:k]].sum()))
    nulls = {k: np.array(v) for k, v in nulls.items()}
    print(f"\n  {tag}")
    res[tag] = head(sc, tag, nulls)
json.dump(res, open(HERE / "results" / "episode_similarity_mtf_20260705.json", "w"), indent=1)
print("\nOK → results/episode_similarity_mtf_20260705.json")
