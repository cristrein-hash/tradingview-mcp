#!/usr/bin/env python3
"""FILTRO MACRO-CONTEXTUAL CAUSAL — ESTADO DE ESTRUTURA HTF (BOS/CHoCH) para XAU 15M LONG 3R.

HIPOTESE: usando SO swings CONFIRMADOS ate a barra de decisao j (causal_swings_upto(j)),
constroi a maquina de estado de market-structure. BULL enquanto a estrutura confirma
higher-highs/higher-lows (ultimo evento de rompimento foi de um swing-high); BEAR ao romper
um swing-low. MANTEM entries em estrutura BULL confirmada -> ataca direcao HTF (item b).

CAUSALIDADE: causal_swings_upto(j,r) SO devolve swings com conf_bar<=j. Toda comparacao de
precos de pivo usa esses pivos ja confirmados. Nenhuma barra > j entra na decisao. O outcome
e['out'] NUNCA entra na feature — so no score().

ESTRUTURAL (nao snapshot): o estado e resultado de uma SEQUENCIA de pivos (a maquina caminha
pivo a pivo, atualizando bias por HH/LL). Nao e um valor isolado na barra j.
"""
import sys
sys.path.insert(0, "/Users/cristrein/tradingview-mcp/research/xau_15m_bb_nas_leonardo")
from agent_ctx_kit import ENTRIES, score, causal_swings_upto


def structure_state(j, r):
    """Maquina de estado de market-structure CAUSAL ate a barra j (escala zigzag r).

    Caminha pelos pivos confirmados (conf_bar<=j) em ordem. Mantem lastH/lastL.
    - Novo swing-high > lastH  => rompimento bullish (HH)   -> state='bull'
    - Novo swing-low  < lastL  => rompimento bearish (LL)   -> state='bear'
    O estado e o do ULTIMO evento de rompimento confirmado. None se estrutura insuficiente.
    """
    sw = causal_swings_upto(j, r)
    state = None
    lastH = lastL = None
    for tp, i, pr, ci in sw:
        if tp == "H":
            if lastH is not None and pr > lastH:
                state = "bull"        # higher-high confirmado = BOS/CHoCH bull
            lastH = pr
        else:  # "L"
            if lastL is not None and pr < lastL:
                state = "bear"        # lower-low confirmado = BOS/CHoCH bear
            lastL = pr
    return state


def eval_variant(r):
    keep = [e["n"] for e in ENTRIES if structure_state(e["j"], r) == "bull"]
    sc = score(keep)
    return keep, sc


print("BASE:", score([e["n"] for e in ENTRIES]))
print()
best = None
for r in (6, 9, 12):
    keep, sc = eval_variant(r)
    print(f"--- r={r}  BULL-structure  N_kept={sc['N_kept']}")
    print("   ", sc)
    # criterio: engine 3R -> "ano positivo" = net R > 0 (breakeven hit-3R = 25%).
    y25w = int(sc["y2025"].split("/")[0]); y25n = int(sc["y2025"].split("/")[1])
    y26w = int(sc["y2026"].split("/")[0]); y26n = int(sc["y2026"].split("/")[1])
    netR25 = 3 * y25w - (y25n - y25w)
    netR26 = 3 * y26w - (y26n - y26w)
    netR = 3 * sc["winners_kept"] - sc["losers_kept"]
    both_pos = netR25 > 0 and netR26 > 0
    ok = sc["hit3r_kept"] > 0.542 and sc["poison_ratio"] < 0.9 and both_pos and sc["N_kept"] >= 20
    print(f"    netR_total={netR:+d}  netR_2025={netR25:+d}  netR_2026={netR26:+d}  "
          f"both_years_R+={both_pos}  passes_gate={ok}")
    cand = (sc["hit3r_kept"], -sc["poison_ratio"], sc["N_kept"], r, keep, sc, ok)
    if best is None or cand[:3] > best[:3]:
        best = cand

print()
r = best[3]; keep = best[4]; sc = best[5]
print(f"=== BEST VARIANT: r={r} ===")
print("score:", sc)
print("keep_ns:", sorted(keep))
