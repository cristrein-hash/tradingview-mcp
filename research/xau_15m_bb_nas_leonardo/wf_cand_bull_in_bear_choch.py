#!/usr/bin/env python3
"""FILTRO MACRO-CONTEXTUAL CAUSAL: BULL GENUINO DENTRO DE BEAR (causal CHoCH-up).

Hipotese (pedido nº1 do Cris):
  - Contexto BEAR = swings CONFIRMADOS (conf_bar<=j) a fazer lower-highs / lower-lows ate j.
  - Dentro do bear, deteta MUDANCA DE CARATER bullish CAUSAL = o preco FECHOU acima do
    ultimo LOWER-HIGH CONFIRMADO (tudo <= j) => "bull genuino".
  - MANTEM entries bear SO com choch-up confirmado; REJEITA bear sem choch-up.
  - Entries NAO-bear (bull/range) sao mantidos (nao sao alvo da rejeicao).

CAUSALIDADE: usa APENAS causal_swings_upto(j) (swings com conf_bar<=j, ja confirmados
por movimento PASSADO) e closes CL[k] com k<=j. Nenhuma janela ultrapassa j; nenhum
last_t de zona; nenhum uso de e['out'] na decisao.
"""
import sys
sys.path.insert(0, "/Users/cristrein/tradingview-mcp/research/xau_15m_bb_nas_leonardo")
from agent_ctx_kit import CL, ENTRIES, score, causal_swings_upto


def bear_and_choch(j, min_highs=2, min_lows=2):
    """Devolve (is_bear, choch_up) usando SO barras <=j.
    is_bear: ultimos highs confirmados descendentes (lower-highs) e ultimos lows descendentes (lower-lows).
    choch_up: apos o ultimo LOWER-HIGH confirmado, existe um close (k<=j) acima do preco desse LH."""
    sw = causal_swings_upto(j)
    highs = [(idx, pr, ci) for tp, idx, pr, ci in sw if tp == "H"]
    lows = [(idx, pr, ci) for tp, idx, pr, ci in sw if tp == "L"]
    if len(highs) < min_highs or len(lows) < min_lows:
        return (False, False)
    # lower-highs: ultimos min_highs highs estritamente descendentes
    lh = all(highs[-k][1] < highs[-k-1][1] for k in range(1, min_highs))
    # lower-lows: ultimos min_lows lows estritamente descendentes
    ll = all(lows[-k][1] < lows[-k-1][1] for k in range(1, min_lows))
    is_bear = lh and ll
    if not is_bear:
        return (False, False)
    # CHoCH-up: ultimo lower-high confirmado
    last_lh_idx, last_lh_pr, last_lh_ci = highs[-1]
    # existe close acima do LH entre a confirmacao do LH e j (multi-barra, causal)
    choch = any(CL[k] > last_lh_pr for k in range(last_lh_ci, j + 1))
    return (True, choch)


def build_keep(min_highs=2, min_lows=2):
    keep = []
    diag = {"bear_choch": 0, "bear_nochoch": 0, "notbear": 0}
    for e in ENTRIES:
        is_bear, choch = bear_and_choch(e["j"], min_highs, min_lows)
        if is_bear and not choch:
            diag["bear_nochoch"] += 1  # REJEITADO
            continue
        if is_bear and choch:
            diag["bear_choch"] += 1
        else:
            diag["notbear"] += 1
        keep.append(e["n"])
    return keep, diag


if __name__ == "__main__":
    print("BASE:", score([e["n"] for e in ENTRIES]))
    print()
    best = None
    for mh in (2, 3):
        for ml in (1, 2):
            keep, diag = build_keep(mh, ml)
            sc = score(keep)
            print(f"min_highs={mh} min_lows={ml}  diag={diag}")
            print("   ", sc)
            # criterio: poison<0.9, ambos anos+, N>=20
            y25w = int(sc["y2025"].split("/")[0]); y26w = int(sc["y2026"].split("/")[0])
            ok = sc["poison_ratio"] < 0.9 and sc["N_kept"] >= 20 and y25w > 0 and y26w > 0
            print(f"    -> criterio_ok={ok}")
            if ok and (best is None or sc["hit3r_kept"] > best[1]["hit3r_kept"]):
                best = (f"mh={mh},ml={ml}", sc, keep, diag)
            print()
    print("=" * 60)
    if best:
        print("MELHOR variante:", best[0])
        print("score:", best[1])
        print("diag:", best[3])
        print("keep_ns:", sorted(best[2]))
    else:
        print("NENHUMA variante atinge o criterio (poison<0.9 & ambos anos+ & N>=20).")
        # imprime a de menor poison para reporte honesto
        cands = []
        for mh in (2, 3):
            for ml in (1, 2):
                keep, diag = build_keep(mh, ml)
                sc = score(keep)
                cands.append((f"mh={mh},ml={ml}", sc, keep, diag))
        cands.sort(key=lambda c: (c[1]["poison_ratio"], -c[1]["hit3r_kept"]))
        b = cands[0]
        print("Menor-poison p/ reporte honesto:", b[0])
        print("score:", b[1])
        print("diag:", b[3])
        print("keep_ns:", sorted(b[2]))
