#!/usr/bin/env python3
"""FAMÍLIA mtf_1d_pattern — padrões estruturais do 1D NATIVO (raw_1d_ohlc.jsonl).

Features por dia (causal, sobre closes 1D):
  f1 = sinal(close - EMA_a) · f2 = sinal(EMA_a - EMA_b) · f3 = sinal(slope EMA_a sobre s dias)
=> 8 padrões binários. Mapeamento padrão->rótulo por maioria do GT IN-SAMPLE (t < SPLIT),
congelado nas séries de labels (o cego usa o mapeamento congelado).

CAUSALIDADE: barra 1D com tempo t_d só é usável em t se t_d + 86400 <= t (barra do dia D
usável só a partir do dia D+1). Após o fim dos dados 1D (~2026-05-25) o último padrão
conhecido é mantido (declarado). Warmup (EMA_b/slope indefinidos) -> FALLBACK.

IN-SAMPLE ONLY: métricas só em t < SPLIT=1672531200. Nenhuma métrica t >= SPLIT é calculada.
"""
import sys, json, bisect
from collections import Counter
sys.path.insert(0, "/Users/cristrein/tradingview-mcp/my-strategy/research/revalidation")
import gt_pivot_structural_harness as R1

FAMILY = "mtf_1d_pattern"
SPLIT = 1672531200  # 2023-01-01 UTC
RAW_1D = "/Users/cristrein/tradingview-mcp/my-strategy/research/revalidation/raw_1d_ohlc.jsonl"
OUT = "/Users/cristrein/tradingview-mcp/my-strategy/research/revalidation/results/feat_mtf_1d_pattern_labels.json"

# ===== GRELHA INTERNA FECHADA (declarada antes de qualquer resultado): 4 configs =====
CONFIGS = [
    {"id": "c1", "a": 21, "b": 50, "s": 5},
    {"id": "c2", "a": 21, "b": 50, "s": 10},
    {"id": "c3", "a": 10, "b": 30, "s": 5},
    {"id": "c4", "a": 10, "b": 30, "s": 10},
]
FALLBACK = "RANGE"  # padrão nunca visto in-sample ou warmup EMA
DAY_S = 86400

# ---- carregar 1D nativo ----
D = [json.loads(l) for l in open(RAW_1D) if l.strip()]
D.sort(key=lambda b: b["t"])
D_T = [b["t"] for b in D]
D_C = [b["c"] for b in D]
D_CLOSE_AT = [t + DAY_S for t in D_T]  # barra do dia D conhecida a partir do dia seguinte

def ema_series(vals, n):
    k = 2.0 / (n + 1)
    out, e = [], None
    for v in vals:
        e = v if e is None else e + k * (v - e)
        out.append(e)
    return out

def sgn(x):
    return 1 if x > 0 else 0

def patterns_for(a, b, s):
    """Padrão (0..7) por índice diário; None durante warmup (precisa >= b barras e lag s)."""
    ea, eb = ema_series(D_C, a), ema_series(D_C, b)
    warm = max(b - 1, s)
    pats = []
    for d in range(len(D_C)):
        if d < warm:
            pats.append(None); continue
        f1 = sgn(D_C[d] - ea[d])
        f2 = sgn(ea[d] - eb[d])
        f3 = sgn(ea[d] - ea[d - s])
        pats.append(f1 * 4 + f2 * 2 + f3)
    return pats

TS4 = R1.ENG.TS4
SC_IN = [(t, g) for t, g in R1.SCOPE if t < SPLIT]

def build_config(cfg):
    pats_daily = patterns_for(cfg["a"], cfg["b"], cfg["s"])
    # padrão ativo em cada t de TS4 (última barra 1D FECHADA <= t; mantém último após fim dos dados)
    pat_at = []
    for t in TS4:
        d = bisect.bisect_right(D_CLOSE_AT, t) - 1
        pat_at.append(pats_daily[d] if d >= 0 else None)
    # mapeamento padrão->rótulo por maioria do GT, SÓ t < SPLIT (congelado)
    cnt = {p: Counter() for p in range(8)}
    for t, g in SC_IN:
        p = pat_at[R1.T2I[t]]
        if p is not None:
            cnt[p][g] += 1
    mapping = {p: (cnt[p].most_common(1)[0][0] if cnt[p] else FALLBACK) for p in range(8)}
    # séries de labels para TODOS os TS4 (mapeamento congelado aplica-se ao histórico todo)
    labels = [mapping[p] if p is not None else FALLBACK for p in pat_at]
    return labels, mapping

results = {"family": FAMILY, "configs": []}
report = []
for cfg in CONFIGS:
    labels, mapping = build_config(cfg)
    sc = R1.score_fn(lambda t, _l=labels: _l[R1.T2I[t]], SC_IN)  # IN-SAMPLE ONLY
    results["configs"].append({
        "id": cfg["id"],
        "params": {"a": cfg["a"], "b": cfg["b"], "s": cfg["s"],
                   "mapping_frozen_in_sample": {str(k): v for k, v in mapping.items()}},
        "labels": labels,
    })
    report.append((cfg, sc, mapping))
    print(f"{cfg['id']} a={cfg['a']} b={cfg['b']} s={cfg['s']} | IN bal={sc['bal']} acc={sc['acc']} "
          f"recall B/Be/R={sc['recall']['BULL']}/{sc['recall']['BEAR']}/{sc['recall']['RANGE']} "
          f"| map={mapping}")

json.dump(results, open(OUT, "w"))
print(f"\nOK: {OUT} · n_ts4={len(TS4)} · sc_in n={len(SC_IN)} · 1D termina em {D_T[-1]} (depois disso mantém último padrão)")
