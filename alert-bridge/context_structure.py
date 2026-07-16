#!/usr/bin/env python3
"""Estrutura de mercado DETERMINISTICA close-only causal (P3/E0) — funcoes PURAS transferidas fielmente
de macro_structural_v3.py (fractal_pivots/atr/CHoCH) + logica de leg. Operam sobre listas H/L/C (nao
importam datasets; sem efeitos colaterais). Usadas pelo context_engine p/ montar o dossie MTF por TF.
NUNCA repinta: um pivot so e usavel quando confirm_bar <= i (causal). py3.9.
Selftest: python3 context_structure.py --selftest
"""
from typing import List, Optional


def atr(H, L, C, i, n=14):
    if i - n + 1 < 1:
        return None
    s = 0.0
    for k in range(i - n + 1, i + 1):
        s += max(H[k] - L[k], abs(H[k] - C[k - 1]), abs(L[k] - C[k - 1]))
    return s / n


def fractal_pivots(H, L, m=3):
    """Pivots fractais causais (transferido de macro_structural_v3.fractal_pivots).
    swing-high em k confirmado em k+m se H[k] domina m barras de cada lado; idem low.
    Devolve (confirm_bar, tipo, pivot_bar, preco) ordenados por confirm_bar."""
    N = len(H); ev = []
    for k in range(m, N - m):
        if all(H[k] > H[k - j] for j in range(1, m + 1)) and all(H[k] >= H[k + j] for j in range(1, m + 1)):
            ev.append((k + m, "H", k, H[k]))
        if all(L[k] < L[k - j] for j in range(1, m + 1)) and all(L[k] <= L[k + j] for j in range(1, m + 1)):
            ev.append((k + m, "L", k, L[k]))
    ev.sort()
    return ev


def _pv(e):
    return {"bar": e[2], "price": e[3], "confirm_bar": e[0]} if e else None


def structure(H, L, C, i=None, m=3, atr_n=14):
    """Dossie estrutural causal ate a barra i (default = ultima). Close-only, sem repintar."""
    N = len(C)
    if i is None:
        i = N - 1
    piv = [e for e in fractal_pivots(H, L, m) if e[0] <= i]      # so pivots confirmados <= i (causal)
    highs = [e for e in piv if e[1] == "H"]
    lows = [e for e in piv if e[1] == "L"]
    last_high = highs[-1] if highs else None
    last_low = lows[-1] if lows else None
    prev_high = highs[-2] if len(highs) >= 2 else None
    prev_low = lows[-2] if len(lows) >= 2 else None
    a = atr(H, L, C, i, atr_n)

    prot_low = last_low[3] if last_low else None                # higher-low imediato
    prot_high = last_high[3] if last_high else None             # lower-high imediato
    choch_dn = prot_low is not None and C[i] < prot_low         # rompe o higher-low
    choch_up = prot_high is not None and C[i] > prot_high       # rompe o lower-high

    # trend por sequencia HH/HL vs LH/LL
    trend = "RANGE"
    if last_high and prev_high and last_low and prev_low:
        hh = last_high[3] > prev_high[3]; hl = last_low[3] > prev_low[3]
        lh = last_high[3] < prev_high[3]; ll = last_low[3] < prev_low[3]
        if hh and hl:
            trend = "UP"
        elif lh and ll:
            trend = "DOWN"

    # leg entre o ultimo swing low e high confirmados: magnitude/ATR + posicao (0=fundo,1=topo)
    leg = None
    if last_high and last_low and a:
        lo, hi = last_low[3], last_high[3]
        if hi > lo:
            leg = {"low": round(lo, 3), "high": round(hi, 3),
                   "mag_atr": round((hi - lo) / a, 2),
                   "pos_in_leg": round(max(0.0, min(1.0, (C[i] - lo) / (hi - lo))), 2),
                   "dir": "up" if last_low[0] < last_high[0] else "down"}

    return {
        "i": i, "close": round(C[i], 3), "atr14": round(a, 4) if a else None, "trend": trend,
        "swings": {"last_high": _pv(last_high), "last_low": _pv(last_low),
                   "prev_high": _pv(prev_high), "prev_low": _pv(prev_low)},
        "choch": {"up": bool(choch_up), "dn": bool(choch_dn)},
        "leg": leg,
    }


def _mk(P):
    return [p + 1.0 for p in P], [p - 1.0 for p in P], list(P)


def _selftest():
    # UPTREND zigzag: peaks 120/130/140/150 (HH), troughs 106/116/126/136 (HL)
    up = [100, 110, 108, 106, 120, 118, 116, 130, 128, 126, 140, 138, 136, 150, 148, 146]
    H, L, C = _mk(up)
    s = structure(H, L, C, m=2)
    print(f"UPTREND: trend={s['trend']} (esp UP) leg={s['leg']}")
    ok_up = s["trend"] == "UP"

    # DOWNTREND zigzag: peaks 140/130/120/110 (LH), troughs 130/120/110/100 (LL)
    dn = [150, 140, 142, 144, 130, 132, 134, 120, 122, 124, 110, 112, 114, 100, 102, 104]
    H, L, C = _mk(dn)
    s2 = structure(H, L, C, m=2)
    print(f"DOWNTREND: trend={s2['trend']} (esp DOWN)")
    ok_dn = s2["trend"] == "DOWN"

    # CHoCH down: uptrend com higher-lows, depois close rompe o ultimo higher-low
    ch = [100, 110, 108, 106, 120, 118, 116, 130, 128, 126, 140, 138, 100]  # HL@126(bar9) confirma, close 100 rompe-o
    H, L, C = _mk(ch)
    s3 = structure(H, L, C, m=2)
    print(f"CHoCH: dn={s3['choch']['dn']} (esp True) up={s3['choch']['up']} | last_low={s3['swings']['last_low']}")
    ok_choch = s3["choch"]["dn"] is True

    # causalidade: pivots so confirmados <= i (confirm_bar > pivot_bar sempre)
    piv = fractal_pivots(H, L, m=2)
    ok_causal = all(e[0] > e[2] for e in piv)
    print(f"causalidade (confirm_bar>pivot_bar): {ok_causal}")

    allok = ok_up and ok_dn and ok_choch and ok_causal
    print("RESULTADO:", "PASS" if allok else "FALHA", f"(up={ok_up} dn={ok_dn} choch={ok_choch} causal={ok_causal})")
    return 0 if allok else 1


if __name__ == "__main__":
    import sys
    if "--selftest" in sys.argv:
        sys.exit(_selftest())
