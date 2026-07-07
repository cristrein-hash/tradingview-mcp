#!/usr/bin/env python3
"""ADVERSARIAL VERIFY — HTF-STRUCTURE-STATE (BOS/CHoCH causal, r=9 BULL).

Objetivo: re-implementar a feature de forma ESTRITAMENTE causal e independente, sem
confiar cegamente no candidato. Reconstruo os swings confirmados eu mesmo (conf_bar<=j),
comparo com o helper causal_swings_upto, e recorro a maquina de estado. Depois testo
sensibilidade: (a) ci<=j (usado pelo autor), (b) ci<j (ainda mais estrito), e r={6,9,12}.
"""
import sys
sys.path.insert(0, "/Users/cristrein/tradingview-mcp/research/xau_15m_bb_nas_leonardo")
from agent_ctx_kit import (ENTRIES, score, causal_swings_upto,
                           HI, LO, ATR, N)


# --- Reconstrucao INDEPENDENTE do zigzag com conf_bar explicito (espelha _zz do kit) ---
def zz_full(r):
    piv = []; d = 0; ehi = elo = 0
    for i in range(1, N):
        a = ATR[i]
        if HI[i] > HI[ehi]: ehi = i
        if LO[i] < LO[elo]: elo = i
        if d <= 0 and HI[i] - LO[elo] >= r * a and elo < i:
            piv.append(("L", elo, LO[elo], i)); d = 1
            ehi = max(range(elo, i + 1), key=lambda k: HI[k])
        elif d >= 0 and HI[ehi] - LO[i] >= r * a and ehi < i:
            piv.append(("H", ehi, HI[ehi], i)); d = -1
            elo = min(range(ehi, i + 1), key=lambda k: LO[k])
    return piv


def my_causal_swings(j, r, strict_lt=False):
    """swings confirmados; strict_lt=False => ci<=j (autor); True => ci<j."""
    return [(tp, i, pr, ci) for tp, i, pr, ci in zz_full(r)
            if (ci < j if strict_lt else ci <= j)]


def structure_state(swings):
    state = None; lastH = lastL = None
    for tp, i, pr, ci in swings:
        if tp == "H":
            if lastH is not None and pr > lastH: state = "bull"
            lastH = pr
        else:
            if lastL is not None and pr < lastL: state = "bear"
            lastL = pr
    return state


# --- 0) sanity: meu zigzag == helper do kit (para conf_bar<=j) ---
mismatch = 0
for e in ENTRIES[:20]:
    j = e["j"]
    a = my_causal_swings(j, 9)
    b = causal_swings_upto(j, 9)
    if a != b: mismatch += 1
print(f"[sanity] my_causal_swings vs kit causal_swings_upto (r=9, primeiros 20 j): mismatches={mismatch}")
print()

# --- 1) reproduz o candidato via helper (ci<=j) ---
print("=== VIA HELPER causal_swings_upto (ci<=j) — deve bater com o candidato ===")
for r in (6, 9, 12):
    keep = [e["n"] for e in ENTRIES if structure_state(causal_swings_upto(e["j"], r)) == "bull"]
    sc = score(keep)
    print(f" r={r:>2}: N={sc['N_kept']:>2} hit={sc['hit3r_kept']:.3f} poison={sc['poison_ratio']:.2f} "
          f"wc={sc['winners_cut']} lc={sc['losers_cut']} y25={sc['y2025']} y26={sc['y2026']}")
print()

# --- 2) STRICT: reconstrucao independente, ci<=j ---
print("=== STRICT INDEP (my_causal_swings, ci<=j) ===")
strict_sc_by_r = {}
for r in (6, 9, 12):
    keep = [e["n"] for e in ENTRIES if structure_state(my_causal_swings(e["j"], r)) == "bull"]
    sc = score(keep)
    strict_sc_by_r[r] = sc
    print(f" r={r:>2}: N={sc['N_kept']:>2} hit={sc['hit3r_kept']:.3f} poison={sc['poison_ratio']:.2f} "
          f"wc={sc['winners_cut']} lc={sc['losers_cut']} y25={sc['y2025']} y26={sc['y2026']}")
print()

# --- 3) EXTRA-STRICT: ci<j (confirmacao estritamente antes da barra de decisao) ---
print("=== EXTRA-STRICT (ci<j) ===")
for r in (6, 9, 12):
    keep = [e["n"] for e in ENTRIES if structure_state(my_causal_swings(e["j"], r, strict_lt=True)) == "bull"]
    sc = score(keep)
    print(f" r={r:>2}: N={sc['N_kept']:>2} hit={sc['hit3r_kept']:.3f} poison={sc['poison_ratio']:.2f} "
          f"wc={sc['winners_cut']} lc={sc['losers_cut']} y25={sc['y2025']} y26={sc['y2026']}")
print()

# strict metrics for r=9 (author's chosen scale)
import json
print("STRICT_METRICS_R9 =", json.dumps(strict_sc_by_r[9]))
