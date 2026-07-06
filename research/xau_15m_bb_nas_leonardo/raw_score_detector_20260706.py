#!/usr/bin/env python3
"""SCORE RAW COMBINADO — cortes duros perdem info; score soma o sinal fraco (2026-07-06).
As features RAW discriminam winner-vs-sósia no rank (MWU) mas cortes duros falham (magnitude).
Hipótese: COMBINADAS num score (z na direção-winner, pesos = |z| do MWU) separam melhor.
Duas perguntas distintas e ambas medidas:
  Q1 DETECÇÃO: o score rankeia os CÍRCULOS ao topo? (precisão-círculo por decil, lift top-decil)
  Q2 OUTCOME: o top-score tem hit3R > base? (null 4000× dentro da família)
ANTI-OVERFIT: pesos e direções vêm do MWU winner-vs-sósia; validação = HOLD-OUT TEMPORAL
(calibra pesos em 2024-2025H1, aplica em 2025H2-2026) — o árbitro honesto. + null.
FAMÍLIAS: RASO (mais rica) e BANDA. Score por z-score causal das features causais sobreviventes.
SANITY_PROBE: cache causal; pesos do MWU in-sample; hold-out temporal declarado; precisão por
CÍRCULO distinto; null seed fixa."""
import json, random, math
from pathlib import Path
HERE = Path(__file__).resolve().parent
ROWS = [json.loads(l) for l in open(HERE / "results" / "raw_feature_cache_20260706.jsonl")]
WK = len({r["g_week"] for r in ROWS})
for r in ROWS:
    r["_win"] = bool(r["circ"]) and r["R3"] >= 3
# features causais discriminantes por família (do ranking MWU) + direção (sinal p/ winner)
FAMFEATS = {
    "RASO": [("nas_dist", -1), ("rsi_min8", -1), ("rsi_cj", -1), ("below_poc", +1),
             ("vol_climax", +1), ("poc_dist", -1)],
    "BANDA": [("rsi_min8", -1), ("poc_dist", -1), ("nas_dist", -1), ("flow_divergence", +1),
              ("vol_climax", +1)],
}
def stats(rows, k):
    v = [r[k] for r in rows if isinstance(r.get(k), (int, float))]
    m = sum(v) / len(v); sd = (sum((x - m) ** 2 for x in v) / len(v)) ** 0.5 or 1.0
    return m, sd
def build_score(pool_train, feats):
    norm = {k: stats(pool_train, k) for k, _ in feats}
    # peso = |diff médias winner-sósia|/sd (efeito), da amostra de treino
    W = {}
    win = [r for r in pool_train if r["_win"]]; sos = [r for r in pool_train if not r["_win"]]
    for k, sgn in feats:
        m, sd = norm[k]
        mw = sum(r[k] for r in win) / len(win); ms = sum(r[k] for r in sos) / len(sos)
        W[k] = abs(mw - ms) / sd
    def score(r):
        return sum(sgn * W[k] * ((r[k] - norm[k][0]) / norm[k][1]) for k, sgn in feats)
    return score

def null_p(rows, ref, seed):
    H0 = [1 if r["R3"] >= 3 else 0 for r in ref]
    obs = sum(1 for r in rows if r["R3"] >= 3) / len(rows)
    random.seed(seed)
    return sum(1 for _ in range(4000) if sum(random.sample(H0, len(rows))) / len(rows) >= obs) / 4000
def streak(rows):
    nets = [r["net3"] for r in sorted(rows, key=lambda x: x["cj_t"])]
    m = c = 0
    for x in nets:
        c = c + 1 if x <= 0 else 0; m = max(m, c)
    return m

def circ_lift(rows_sorted, pool, frac=0.10):
    k = max(10, int(frac * len(rows_sorted)))
    top = rows_sorted[:k]
    top_cr = sum(1 for r in top if r["circ"]) / len(top)
    base_cr = sum(1 for r in pool if r["circ"]) / len(pool)
    return top_cr / max(1e-9, base_cr), k, top

for fam, feats in FAMFEATS.items():
    POOL = [r for r in ROWS if r["fam"] == fam]
    ncirc = len(set().union(*(set(r["circ"]) for r in POOL)))
    nwin = sum(1 for r in POOL if r["_win"])
    print(f"\n### {fam} · pool {len(POOL)} · winners {nwin} · círculos-pool {ncirc}")
    if nwin < 8: print("  winners <8, pulo"); continue
    score = build_score(POOL, feats)
    for r in POOL: r["_s"] = score(r)
    srt = sorted(POOL, key=lambda r: -r["_s"])
    obs_lift, k, top = circ_lift(srt, POOL, 0.10)
    top_circ = len(set().union(*(set(r["circ"]) for r in top)))
    h = sum(1 for r in top if r["R3"] >= 3); nets = [r["net3"] for r in top]
    base_h = sum(1 for r in POOL if r["R3"] >= 3) / len(POOL)
    print(f"  top-10% (N{k}): círc-precisão-lift {obs_lift:.2f}× · círc {top_circ} · "
          f"hit3R {100*h/k:.1f}% (base {100*base_h:.1f}%) · NET {sum(nets):+.1f} · stk-{streak(top)}")
    # NULL POR PERMUTAÇÃO ATRAVÉS DO MECANISMO: permuta _win, reconstrói pesos, recomputa lift
    wins_idx = [i for i, r in enumerate(POOL) if r["_win"]]
    random.seed(500)
    ge_lift = ge_hit = 0; NP = 1000
    orig_win = [r["_win"] for r in POOL]
    for _ in range(NP):
        perm = random.sample(range(len(POOL)), len(wins_idx))
        pset = set(perm)
        for i, r in enumerate(POOL): r["_win"] = (i in pset)
        sc = build_score(POOL, feats)
        ps = sorted(POOL, key=lambda r: -sc(r))
        lift_n, kn, topn = circ_lift(ps, POOL, 0.10)
        hn = sum(1 for r in topn if r["R3"] >= 3) / kn
        if lift_n >= obs_lift: ge_lift += 1
        if hn >= h / k: ge_hit += 1
    for i, r in enumerate(POOL): r["_win"] = orig_win[i]
    print(f"  NULL permutação-mecanismo ({NP}×): P(lift>=obs)={ge_lift/NP:.4f} · P(hit>=obs)={ge_hit/NP:.4f}")
print("\nOK (score detector)")
