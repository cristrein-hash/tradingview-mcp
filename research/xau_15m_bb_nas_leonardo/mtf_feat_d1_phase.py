#!/usr/bin/env python3
"""FASE 1D — familia de features FRACTAIS da estrutura DIARIA no entry XAU 15M.

Le a fase da perna DIARIA no instante do entry usando SO dias FECHADOS
(htf_closed_upto('1D',t) exclui o dia corrente => anti-lookahead).

Features (escala RELATIVA a propria perna, nao direcao absoluta=calendario):
  d1_trend       : slope continuo da EMA-dia normalizado por ATR-dia (contexto direcional suave)
  d1_leg_age     : dias FECHADOS desde a origem da perna diaria corrente (maturidade)
  d1_pos_in_leg  : posicao do close no range da perna corrente [0=origem .. 1=extremo] (maturidade relativa)
  d1_dist_to_high: room (em ATR) do close ao maximo diario recente (20d)

Salva feature_file JSON (lista de 96 dicts na ordem de ENTRIES) e corre oof_mining_null.
"""
import sys, json
sys.path.insert(0, "/Users/cristrein/tradingview-mcp/research/xau_15m_bb_nas_leonardo")
from mtf_kit import htf_closed_upto, htf_swings, ENTRIES, oof_mining_null
import numpy as np

FEATS = ["d1_trend", "d1_leg_age", "d1_pos_in_leg", "d1_dist_to_high"]

def ema(vals, span):
    a = 2.0 / (span + 1.0)
    e = vals[0]
    for v in vals[1:]:
        e = a * v + (1 - a) * e
    return e

def ema_series(vals, span):
    a = 2.0 / (span + 1.0)
    out = [vals[0]]
    for v in vals[1:]:
        out.append(a * v + (1 - a) * out[-1])
    return out

def d1_features(bars):
    """bars = dias FECHADOS (end<=t). Devolve dict de features causais."""
    n = len(bars)
    C = [b["c"] for b in bars]
    H = [b["h"] for b in bars]
    L = [b["l"] for b in bars]
    piv, _H, _L, _C, A = htf_swings(bars, r=2.0)
    atr = (A[-1] if A else (H[-1] - L[-1])) or 1e-9

    # d1_trend: slope da EMA20-dia sobre 5 dias, em unidades de ATR
    es = ema_series(C, 20)
    k = 5
    d1_trend = (es[-1] - es[-1 - k]) / (k * atr) if n > k else 0.0

    # perna corrente = do ultimo pivot confirmado ate ao ultimo dia fechado
    if piv:
        ptype, pidx, pprice = piv[-1]
    else:
        # fallback: perna desde o inicio da janela
        ptype, pidx, pprice = ("L" if C[-1] >= C[0] else "H"), 0, (L[0] if C[-1] >= C[0] else H[0])

    d1_leg_age = float((n - 1) - pidx)  # dias fechados desde a origem da perna

    seg_hi = max(H[pidx:])
    seg_lo = min(L[pidx:])
    rng = (seg_hi - seg_lo) or 1e-9
    if ptype == "L":  # up-leg: origem=low, extremo=high => maturo quando close perto do high
        d1_pos_in_leg = (C[-1] - seg_lo) / rng
    else:             # down-leg: origem=high, extremo=low => maturo quando close perto do low
        d1_pos_in_leg = (seg_hi - C[-1]) / rng
    d1_pos_in_leg = float(min(1.0, max(0.0, d1_pos_in_leg)))

    # room ao maximo diario recente (ultimos 20 dias fechados), em ATR
    look = min(20, n)
    recent_hi = max(H[-look:])
    d1_dist_to_high = float((recent_hi - C[-1]) / atr)

    return {"d1_trend": float(d1_trend), "d1_leg_age": d1_leg_age,
            "d1_pos_in_leg": d1_pos_in_leg, "d1_dist_to_high": d1_dist_to_high}, bars[-1]["end"]

# ---- computa para cada entry + prova de causalidade ----
rows = []
causal_ok = True
worst_gap = None  # menor gap (t - end) para confirmar end<=t sempre
for e in ENTRIES:
    t = e["t"]
    bars = htf_closed_upto("1D", t)
    assert bars, f"sem barras 1D para entry {e['n']}"
    last_end = bars[-1]["end"]
    assert last_end <= t, f"LOOKAHEAD entry {e['n']}: last_end {last_end} > t {t}"
    gap = t - last_end
    if worst_gap is None or gap < worst_gap:
        worst_gap = gap
    feats, used_end = d1_features(bars)
    assert used_end <= t
    row = {"n": e["n"]}
    row.update(feats)
    rows.append(row)

# ---- VERIFICA que disparam (variancia/min/max) ----
print("=== VARIANCIA DAS FEATURES (disparam?) ===")
arr = {f: np.array([r[f] for r in rows], dtype=float) for f in FEATS}
for f in FEATS:
    a = arr[f]
    print(f"  {f:16s} min={a.min():+.4f} max={a.max():+.4f} mean={a.mean():+.4f} std={a.std():.4f} nuniq={len(np.unique(np.round(a,6)))}")
    if a.std() < 1e-6:
        print(f"  !!! {f} CONSTANTE — DEBUGGA")

print(f"\n=== CAUSALIDADE ===")
print(f"  96/96 entries: ultima barra 1D usada tem end<=t. menor gap(t-end)={worst_gap}s ({worst_gap/3600:.1f}h) => sempre >0, barra corrente EXCLUIDA.")

# ---- salva feature_file ----
FEATURE_FILE = "/Users/cristrein/tradingview-mcp/research/xau_15m_bb_nas_leonardo/mtf_feat_d1_phase.json"
with open(FEATURE_FILE, "w") as fh:
    json.dump(rows, fh, indent=0)
print(f"\nfeature_file salvo: {FEATURE_FILE} ({len(rows)} dicts)")

# ---- matriz X (96 x k) na ordem de ENTRIES + oof_mining_null ----
X = np.column_stack([arr[f] for f in FEATS])
print(f"\n=== OOF MINING NULL (X shape {X.shape}) ===")
res = oof_mining_null(X)
print(json.dumps(res, indent=2))
print("\nRESULT_JSON_BEGIN")
print(json.dumps(res))
print("RESULT_JSON_END")
