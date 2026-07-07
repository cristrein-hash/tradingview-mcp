#!/usr/bin/env python3
"""FAMILIA: RETEST DE DEMANDA HTF (fractal) para classificar fase de entry XAU 15M.

Hipotese: Fase B (iniciacao off-flush) = o entry 15M esta a RETESTAR uma demanda/suporte
de escala 4H ou 1D FRESCA (swing-low HTF confirmado, FECHADO antes do entry). Fase C
(distribuicao) = longe da demanda, no TOPO da perna HTF.

Escala RELATIVA (mata confound de calendario): posicao/maturidade RELATIVA A PROPRIA PERNA
HTF (leg_pos no range da perna, barras desde a origem, distancia a demanda em ATR-HTF),
NAO direcao absoluta.

ANTI-LOOKAHEAD: usa SO htf_closed_upto(tf,e['t']) -> barras HTF com END<=t (a barra HTF que
CONTEM t esta EXCLUIDA). Swings computados so sobre essas barras fechadas.
"""
import sys, json
sys.path.insert(0, "/Users/cristrein/tradingview-mcp/research/xau_15m_bb_nas_leonardo")
from mtf_kit import HTF, htf_closed_upto, htf_swings, ENTRIES, oof_mining_null
import numpy as np

HERE = "/Users/cristrein/tradingview-mcp/research/xau_15m_bb_nas_leonardo"

def _swing_lows(piv):
    """pivots do tipo 'L' -> lista (idx, price) na ordem temporal."""
    return [(idx, price) for (tp, idx, price) in piv if tp == "L"]

def _swing_highs(piv):
    return [(idx, price) for (tp, idx, price) in piv if tp == "H"]

def compute_features(e):
    p = e["ent"]          # preco de entry (conhecido no bar j = known_at entry)
    t = e["t"]
    f = {}
    causal_proof = {}     # ultima barra HTF usada por TF (end<=t)

    for tf, atr_floor in (("4H", 1.0), ("1D", 1.0)):
        bars = htf_closed_upto(tf, t)   # <-- CAUSAL: barras FECHADAS (end<=t)
        pref = tf.lower()
        # prova de causalidade: ultima barra usada tem end<=t
        causal_proof[tf] = (bars[-1]["end"] if bars else None)

        piv, H, L, C, A = htf_swings(bars, r=2.0)
        atr = (A[-1] if A else None) or atr_floor
        lows = _swing_lows(piv)
        highs = _swing_highs(piv)

        if lows:
            last_low_idx, last_low = lows[-1]
            # distancia (signed) a demanda HTF mais RECENTE, em ATR-HTF
            f[f"dist_{pref}_demand"] = (p - last_low) / atr
            # demanda mais PROXIMA ABAIXO do preco (suporte vivo), em ATR
            below = [lp for (_, lp) in lows if lp <= p + 0.25 * atr]
            near_below = max(below) if below else last_low
            f[f"near_{pref}_demand_below"] = (p - near_below) / atr
            # retest flag: preco dentro de 0.5 ATR-HTF de ALGUMA demanda recente
            recent = lows[-4:]
            mind = min(abs(p - lp) / atr for (_, lp) in recent)
            f[f"is_{pref}_retest"] = 1.0 if mind <= 0.5 else 0.0
            f[f"mindist_{pref}_demand"] = mind
            # maturidade da perna: barras HTF desde a origem (ultimo swing-low)
            f[f"{pref}_leg_maturity"] = float(len(bars) - 1 - last_low_idx)
        else:
            f[f"dist_{pref}_demand"] = 0.0
            f[f"near_{pref}_demand_below"] = 0.0
            f[f"is_{pref}_retest"] = 0.0
            f[f"mindist_{pref}_demand"] = 3.0
            f[f"{pref}_leg_maturity"] = 0.0

        # posicao na perna corrente (0=na demanda base, 1=no topo da perna)
        if lows and highs:
            last_low_idx, last_low = lows[-1]
            last_high_idx, last_high = highs[-1]
            rng = last_high - last_low
            if rng > 0:
                f[f"{pref}_leg_pos"] = (p - last_low) / rng
            else:
                f[f"{pref}_leg_pos"] = 0.5
        else:
            f[f"{pref}_leg_pos"] = 0.5

    return f, causal_proof

def main():
    feats = []
    proofs = []
    for e in ENTRIES:
        f, cp = compute_features(e)
        row = {"n": e["n"]}
        row.update({k: round(float(v), 5) for k, v in f.items()})
        feats.append(row)
        proofs.append((e["n"], e["t"], cp))

    keys = [k for k in feats[0].keys() if k != "n"]

    # ---- (2) VERIFICA que disparam: variancia / min / max ----
    print("=== VARIANCIA DAS FEATURES (devem DISPARAR, nao constantes) ===")
    dead = []
    for k in keys:
        col = np.array([r[k] for r in feats], dtype=float)
        v = float(col.var())
        print(f"  {k:26s} var={v:10.4f} min={col.min():8.3f} max={col.max():8.3f} mean={col.mean():8.3f}")
        if v < 1e-9:
            dead.append(k)
    if dead:
        print(f"  [ALERTA] features CONSTANTES (var~0): {dead}")
    else:
        print("  OK: todas as features tem variancia > 0")

    # ---- prova de causalidade: ultima barra HTF end<=t para TODOS os entries ----
    print("\n=== PROVA ANTI-LOOKAHEAD (ultima barra HTF end<=t) ===")
    bad = 0
    for (n, t, cp) in proofs:
        for tf, end in cp.items():
            if end is not None and end > t:
                bad += 1
                print(f"  [VIOLACAO] n={n} tf={tf} end={end} > t={t}")
    ex = proofs[len(proofs)//2]
    print(f"  entries verificados: {len(proofs)} · violacoes end>t: {bad}")
    print(f"  exemplo n={ex[0]}: t={ex[1]} · ultimas barras HTF fechadas: "
          + ", ".join(f"{tf}:end={end}(gap={ex[1]-end}s)" for tf, end in ex[2].items() if end))

    # ---- (3) salva feature_file JSON ----
    fpath = f"{HERE}/results/mtf_feat_htf_demand_retest.json"
    import os
    os.makedirs(f"{HERE}/results", exist_ok=True)
    json.dump(feats, open(fpath, "w"), indent=1)
    print(f"\nfeature_file salvo: {fpath} ({len(feats)} rows, {len(keys)} features)")

    # ---- (4) monta X (96 x k) na ordem de ENTRIES e corre oof_mining_null ----
    X = np.array([[r[k] for k in keys] for r in feats], dtype=float)
    print(f"\nX shape = {X.shape}")
    res = oof_mining_null(X)
    print("\n=== oof_mining_null(X) ===")
    for k, v in res.items():
        print(f"  {k}: {v}")

    # dump resultado para leitura estruturada
    json.dump({"features": keys, "oof": res, "feature_file": fpath},
              open(f"{HERE}/results/mtf_feat_htf_demand_retest_OOF.json", "w"), indent=1)
    print("\n__OOF_JSON__" + json.dumps(res))
    print("__CAUSAL_BAD__" + str(bad) + "__N__" + str(len(proofs)))

if __name__ == "__main__":
    main()
