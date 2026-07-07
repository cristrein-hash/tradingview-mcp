#!/usr/bin/env python3
"""FAMILIA FRACTAL HTF — POSICAO E ROOM (2026-07-07).

Classifica a fase de entry XAU 15M pela POSICAO causal do preco de entry dentro da perna/range
das barras HTF FECHADAS (4H, 1D) + o ROOM (distancia ao swing-high HTF confirmado ACIMA).

Tese fractal:
  Fase A (markup)       -> room grande, perna a estender (pos media-baixa, teto longe)
  Fase C (distribuicao) -> encaixotado sob teto HTF (room ~0, pos alta, sem espaco)

REGRAS DURAS:
  - ANTI-LOOKAHEAD: usa SO htf_closed_upto(tf, e['t']) -> barras HTF com END <= t (barra corrente EXCLUIDA).
  - ESCALA RELATIVA: pos = posicao dentro da PROPRIA perna/range HTF (0..1), nao direcao absoluta.
                     room = distancia ao teto / ATR HTF (auto-escala, mata confound de regime/ano).
  - Verifica VARIANCIA das features (nao podem sair constantes).

Features por entry: pos_4h, pos_1d, room_h4, room_d1.
Salva JSON (96 dicts na ordem de ENTRIES) + corre oof_mining_null(X).
"""
import sys, json
sys.path.insert(0, "/Users/cristrein/tradingview-mcp/research/xau_15m_bb_nas_leonardo")
import numpy as np
from mtf_kit import HTF, htf_closed_upto, htf_swings, ENTRIES, PHASE, oof_mining_null

OUT_JSON = "/Users/cristrein/tradingview-mcp/research/xau_15m_bb_nas_leonardo/results/mtf_feat_htf_position_room.json"

WIN = {"4H": 40, "1D": 30}   # janela de barras HTF fechadas p/ definir o range da perna
SWING_R = 2.0                # zigzag HTF p/ swings confirmados


def _pos_and_room(tf, t, ent):
    """Devolve (pos, room, ok, dbg). pos=posicao de ent no range da janela HTF fechada [0..1].
    room=(teto - ent)/ATR_HTF onde teto = swing-high HTF confirmado mais proximo ACIMA de ent;
    se nao ha swing-high acima (ceu-limpo) -> teto = max HIGH da janela; se ent acima disso
    tambem (breakout total) -> room segue negativo/pequeno (extendido). CAUSAL: so barras END<=t."""
    bars = htf_closed_upto(tf, t)
    if len(bars) < 6:
        return None, None, False, {"nbars": len(bars)}
    # anti-lookahead assert: ultima barra fechada tem END <= t
    assert bars[-1]["end"] <= t, f"LOOKAHEAD {tf}: end {bars[-1]['end']} > t {t}"
    win = bars[-WIN[tf]:]
    hi = max(b["h"] for b in win)
    lo = min(b["l"] for b in win)
    rng = hi - lo
    pos = (ent - lo) / rng if rng > 0 else 0.5
    # swings confirmados sobre TODAS as barras fechadas (causal)
    piv, H, L, C, A = htf_swings(bars, SWING_R)
    atr = A[-1] if A and A[-1] else (rng / max(len(win), 1)) or 1.0
    highs_above = [p for (tp, idx, p) in piv if tp == "H" and p > ent]
    if highs_above:
        teto = min(highs_above)           # swing-high confirmado mais proximo ACIMA
    else:
        teto = hi                         # ceu-limpo: usa topo da janela como proxy de resistencia
    room = (teto - ent) / atr
    return pos, room, True, {"pos": pos, "room": room, "teto": teto, "atr": atr,
                             "n_highs_above": len(highs_above), "last_end": bars[-1]["end"]}


def main():
    rows = []
    X4pos, X1pos, R4, R1 = [], [], [], []
    causal_ok = 0
    last_ends = []
    for e in ENTRIES:
        t = e["t"]; ent = e["ent"]
        p4, r4, ok4, d4 = _pos_and_room("4H", t, ent)
        p1, r1, ok1, d1 = _pos_and_room("1D", t, ent)
        # fallbacks defensivos (nunca deve disparar dado len(bars) grande, mas mantem X completa)
        p4 = 0.5 if p4 is None else p4
        r4 = 0.0 if r4 is None else r4
        p1 = 0.5 if p1 is None else p1
        r1 = 0.0 if r1 is None else r1
        if ok4 and ok1:
            causal_ok += 1
            last_ends.append((d4["last_end"], d1["last_end"], t))
        rows.append({"n": e["n"], "pos_4h": round(p4, 4), "pos_1d": round(p1, 4),
                     "room_h4": round(r4, 4), "room_d1": round(r1, 4)})
        X4pos.append(p4); X1pos.append(p1); R4.append(r4); R1.append(r1)

    # ---- salva feature_file ----
    json.dump(rows, open(OUT_JSON, "w"), indent=1)

    # ---- prova de causalidade: cada barra HTF usada tem end <= t ----
    print("=== PROVA DE CAUSALIDADE (anti-lookahead MTF) ===")
    print(f"entries com HTF fechada valida: {causal_ok}/{len(ENTRIES)}")
    viol = [x for x in last_ends if x[0] > x[2] or x[1] > x[2]]
    print(f"violacoes end>t: {len(viol)} (esperado 0)")
    for le4, le1, t in last_ends[:3]:
        print(f"  ex: t={t}  ultima_4H_end={le4} (delta {t-le4}s)  ultima_1D_end={le1} (delta {t-le1}s)  -> ambos <= t")

    # ---- VARIANCIA: features tem de disparar ----
    print("\n=== VARIANCIA DAS FEATURES (tem de disparar, nao constantes) ===")
    for name, arr in [("pos_4h", X4pos), ("pos_1d", X1pos), ("room_h4", R4), ("room_d1", R1)]:
        a = np.array(arr, dtype=float)
        print(f"  {name:8s} min={a.min():+.3f} max={a.max():+.3f} mean={a.mean():+.3f} "
              f"std={a.std():.3f} n_unique={len(np.unique(np.round(a,4)))}")
        if a.std() < 1e-6:
            print(f"    !!! CONSTANTE — feature nao dispara: {name}")

    # ---- fase-diagnostico: pos/room por fase do Cris (sanidade, nao validacao) ----
    print("\n=== POR FASE (labels Cris; sanidade da tese A=room-grande / C=encaixotado) ===")
    by = {}
    for e, r in zip(ENTRIES, rows):
        ph = PHASE.get(e["n"])
        if ph: by.setdefault(ph, []).append(r)
    for ph in sorted(by):
        rs = by[ph]
        mp4 = np.mean([x["pos_4h"] for x in rs]); mr4 = np.mean([x["room_h4"] for x in rs])
        mp1 = np.mean([x["pos_1d"] for x in rs]); mr1 = np.mean([x["room_d1"] for x in rs])
        print(f"  Fase {ph} (n={len(rs):2d}): pos_4h={mp4:.2f} room_h4={mr4:+.2f} | pos_1d={mp1:.2f} room_d1={mr1:+.2f}")

    # ---- matriz X e OOF mining-null ----
    X = np.column_stack([X4pos, X1pos, R4, R1])
    print(f"\n=== OOF MINING-NULL (X shape {X.shape}) ===")
    res = oof_mining_null(X)
    for k, v in res.items():
        print(f"  {k}: {v}")
    print(f"\nfeature_file salvo: {OUT_JSON}")
    return res


if __name__ == "__main__":
    main()
