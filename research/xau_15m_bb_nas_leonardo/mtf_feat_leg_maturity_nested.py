#!/usr/bin/env python3
"""FAMILIA: MATURIDADE DE PERNA ANINHADA (nested leg maturity) — escala-relativa, anti-confound.

IDEIA (fractal): para 4H e 1D mede-se, com barras HTF SO FECHADAS antes do entry:
  - mat   = idade da PERNA HTF corrente (nr de barras desde a origem = ultimo pivo major),
            NORMALIZADA pela mediana das pernas anteriores -> RELATIVO A PROPRIA PERNA, nao ao calendario.
            Fase A/B => perna JOVEM (mat baixo); Fase C => perna MADURA/esticada (mat alto).
  - ext   = extensao ja percorrida desde a origem da perna, em ATR-HTF (relativo, mata regime).
  - pushes= nr de sub-swings (pivos finos r=1) DENTRO da perna major corrente (contagem de ondas;
            poucas=jovem, muitas=distribuicao madura).

ANTI-LOOKAHEAD: usa SO htf_closed_upto(tf,e['t']) (barras END<=t; barra corrente EXCLUIDA).
Prova impressa: para todos os entries, end da ultima barra HTF usada <= e['t'].
"""
import sys, json
sys.path.insert(0,"/Users/cristrein/tradingview-mcp/research/xau_15m_bb_nas_leonardo")
from mtf_kit import HTF, htf_closed_upto, htf_swings, ENTRIES, PHASE, oof_mining_null
import numpy as np
from pathlib import Path

HERE = Path("/Users/cristrein/tradingview-mcp/research/xau_15m_bb_nas_leonardo")

def leg_features(tf, t):
    """Features de maturidade de perna aninhada para timeframe tf no instante t (CAUSAL).
    Devolve (mat, ext, pushes, last_end) usando SO barras HTF fechadas (end<=t)."""
    bars = htf_closed_upto(tf, t)
    n = len(bars)
    if n < 6:
        return 0.0, 0.0, 0.0, (bars[-1]["end"] if bars else None)
    piv, H, L, C, A = htf_swings(bars, r=2.0)   # pivos MAJOR da perna
    last_end = bars[-1]["end"]
    last_i = n - 1
    if not piv:
        # sem pivo confirmado: perna = tudo desde o inicio da amostra causal
        origin_idx = 0; origin_px = C[0]
        prior_legs = []
    else:
        tp, origin_idx, origin_px = piv[-1]        # origem da perna corrente = ultimo pivo major
        # comprimentos (em barras) das pernas ANTERIORES ja fechadas -> mediana p/ normalizar (RELATIVO)
        idxs = [p[1] for p in piv]
        prior_legs = [idxs[k]-idxs[k-1] for k in range(1, len(idxs))]
    age_bars = last_i - origin_idx                 # idade da perna corrente em barras HTF
    if prior_legs:
        norm = float(np.median(prior_legs)) or 1.0
    else:
        norm = 10.0 if tf == "4H" else 5.0         # fallback de escala (constante, nao-lookahead)
    mat = age_bars / norm                          # RELATIVO a perna: >1 = mais velha que a mediana
    atr = A[last_i] or 1.0
    ext = abs(C[last_i] - origin_px) / atr         # extensao percorrida em ATR-HTF (relativo)
    # pushes: sub-swings finos (r=1) DENTRO da perna corrente (idx do pivo fino >= origin_idx)
    fpiv, *_ = htf_swings(bars, r=1.0)
    pushes = float(sum(1 for p in fpiv if p[1] >= origin_idx))
    return round(mat,4), round(ext,4), pushes, last_end

# ---- (1) computa features causais p/ cada entry + (causalidade) ----
rows=[]; violations=0
for e in ENTRIES:
    t = e["t"]
    h4m, h4e, h4p, end4 = leg_features("4H", t)
    d1m, d1e, d1p, end1 = leg_features("1D", t)
    if (end4 is not None and end4 > t) or (end1 is not None and end1 > t):
        violations += 1
    rows.append({"n":e["n"],
                 "h4_mat":h4m, "h4_ext":h4e, "h4_pushes":h4p,
                 "d1_mat":d1m, "d1_ext":d1e, "d1_pushes":d1p,
                 "_end4":end4, "_end1":end1, "_t":t})

FEATS = ["h4_mat","h4_ext","h4_pushes","d1_mat","d1_ext","d1_pushes"]

# ---- (2) VERIFICA que disparam (variancia / min / max) ----
print("=== CAUSALIDADE ===")
print(f"entries={len(rows)}  violacoes_lookahead(end>t)={violations}  (tem de ser 0)")
mx4 = max(r["_t"]-r["_end4"] for r in rows if r["_end4"])
mx1 = max(r["_t"]-r["_end1"] for r in rows if r["_end1"])
print(f"min gap (t - end_ultima_barra_HTF): 4H>=0 sempre; menor gap 4H={min(r['_t']-r['_end4'] for r in rows if r['_end4'])}s  1D={min(r['_t']-r['_end1'] for r in rows if r['_end1'])}s")
print("\n=== FEATURES DISPARAM? (var/min/max/nonzero) ===")
for f in FEATS:
    v = np.array([r[f] for r in rows], float)
    print(f"{f:11s} var={v.var():.4f} min={v.min():.3f} max={v.max():.3f} mean={v.mean():.3f} nonzero={int((v!=0).sum())}/96")

# ---- (3) salva feature_file JSON (lista de 96 dicts {n,<feats>} na ordem de ENTRIES) ----
out_rows=[{**{"n":r["n"]}, **{f:r[f] for f in FEATS}} for r in rows]
FEAT_FILE = HERE/"results"/"mtf_feat_leg_maturity_nested.json"
FEAT_FILE.parent.mkdir(exist_ok=True)
json.dump(out_rows, open(FEAT_FILE,"w"), indent=1)
print(f"\nsaved feature_file: {FEAT_FILE}")

# ---- (4) monta X (96 x k) na ordem de ENTRIES e corre oof_mining_null ----
X = np.array([[r[f] for f in FEATS] for r in rows], float)
print(f"\nX shape={X.shape}")
res = oof_mining_null(X)
print("\n=== OOF_MINING_NULL ===")
for k,val in res.items(): print(f"  {k}: {val}")

# phase-label diagnostic (nao entra no classifier; so leitura)
labeled=[(r["n"],PHASE.get(r["n"]),r["h4_mat"],r["d1_mat"],r["h4_pushes"]) for r in rows if r["n"] in PHASE]
print("\n=== leitura por fase (labels Cris, diagnostico) ===")
for ph in "ABCD":
    sub=[x for x in labeled if x[1]==ph]
    if sub:
        h4=np.mean([x[2] for x in sub]); d1=np.mean([x[3] for x in sub]); pu=np.mean([x[4] for x in sub])
        print(f"  fase {ph} (n={len(sub)}): h4_mat={h4:.2f} d1_mat={d1:.2f} h4_pushes={pu:.2f}")

print("\nJSON_RESULT=" + json.dumps(res))
