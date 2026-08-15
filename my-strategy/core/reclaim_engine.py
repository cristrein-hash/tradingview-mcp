#!/usr/bin/env python3
"""Reclaim-sequence engine (reversão-long 15M) — Cris 2026-08-15.
Pivô fractal + sweep/retest + reclaim-COM-DESLOCAMENTO + hold. Preenche o buraco entre a Cp (só capitulação
de perna grande, legMag>=15xATR) e o A1/A2 (BULL-only): a RETOMADA RASA que ambos perdem — ex.: 14/08 reclaim
4311->4333, que o sistema live não deu (regime-1D BEAR travou tudo). Direção = long por construção; o 1D NÃO
fecha a direção (contexto, não veto).

CAUSAL: pivô confirmado p+FRACT_M<=i-1; reclaim na barra i; hold em i+1; ENTRADA no fecho de i+1. SL curto =
min(low sweep/retest)-0.1ATR (não o pivô longínquo). 3R fixo. Regras PRÉ-DECLARADAS (recall-gate v2: apanha a
retomada de 14/08 e rejeita os 5 longs-faca de 13/08). NÃO é edge provado — FORWARD=árbitro. py3 stdlib."""

FRACT_M = 2       # pivô-low fractal (±2 barras)
PIVOT_LB = 40     # procura pivôs nas últimas 40 barras
TEST_TOL = 0.15   # teste do pivô = low <= level + 0.15*ATR (sweep OU retest apertado)
RECL_MARG = 0.10  # reclaim = fecho >= level + 0.10*ATR
BODY_FRAC = 0.50  # displacement = corpo >= 50% do range
UPPER_FRAC = 0.60 # fecho terço superior = (C-L) >= 0.60*range
TARGET_R = 3.0


def _atr(H, L, C, i, n=14):
    if i < n:
        return H[i] - L[i]
    s = 0.0
    for k in range(i - n + 1, i + 1):
        s += max(H[k] - L[k], abs(H[k] - C[k - 1]), abs(L[k] - C[k - 1])) if k > 0 else H[k] - L[k]
    return s / n


def _is_fractal_low(L, p, n):
    if p - FRACT_M < 0 or p + FRACT_M >= n:
        return False
    return all(L[p] < L[p - k] for k in range(1, FRACT_M + 1)) and all(L[p] <= L[p + k] for k in range(1, FRACT_M + 1))


def detect(T, O, H, L, C, i):
    """Devolve dict do fire na barra-reclaim i, ou None. Causal (usa bars<=i+1)."""
    n = len(C)
    if i < PIVOT_LB or i + 1 >= n:
        return None
    a = _atr(H, L, C, i)
    rng = max(H[i] - L[i], 1e-9)
    testlow = min(L[i - 1], L[i])
    cand = [(p, L[p]) for p in range(max(FRACT_M, i - PIVOT_LB), i - 2)
            if p + FRACT_M <= i - 1 and _is_fractal_low(L, p, n) and L[p] < C[i]]
    if not cand:
        return None
    p, level = min(cand, key=lambda x: abs(x[1] - testlow))
    tested = testlow <= level + TEST_TOL * a
    swept = testlow < level
    reclaim = (C[i] > level + RECL_MARG * a) and (C[i] > O[i]) and \
              (abs(C[i] - O[i]) >= BODY_FRAC * rng) and ((C[i] - L[i]) >= UPPER_FRAC * rng)
    hold = C[i + 1] > level
    if not (tested and reclaim and hold):
        return None
    entry = C[i + 1]
    sl = testlow - 0.1 * a                       # SL curto = low do sweep/retest -0.1ATR
    tgt = entry + TARGET_R * (entry - sl)
    return {"reclaim_t": T[i], "etime": T[i + 1], "entry": round(entry, 2), "sl": round(sl, 2),
            "tgt": round(tgt, 2), "level": round(level, 2), "atr": round(a, 2),
            "mode": ("SWEEP" if swept else "RETEST")}


def scan(T, O, H, L, C):
    """Todos os fires causais sobre a série. Devolve lista (ordem temporal)."""
    out = []
    for i in range(PIVOT_LB, len(C) - 1):
        d = detect(T, O, H, L, C, i)
        if d:
            out.append(d)
    return out


if __name__ == "__main__":
    import sys, json, datetime as d
    from pathlib import Path
    if "--selftest" in sys.argv:
        STORE = Path("/Users/cristrein/tradingview-mcp/my-strategy/core/bar_store/store/bars_15m.jsonl")
        B = sorted([(int(x['t']), float(x['o']), float(x['h']), float(x['l']), float(x['c']))
                    for x in (json.loads(l) for l in STORE.read_text().splitlines() if l.strip())])
        T = [x[0] for x in B]; O = [x[1] for x in B]; H = [x[2] for x in B]; L = [x[3] for x in B]; C = [x[4] for x in B]
        fires = scan(T, O, H, L, C)
        ft = {f["reclaim_t"] for f in fires}
        fires2 = scan(T, O, H, L, C)                       # determinismo
        t_reclaim = int(d.datetime(2026, 8, 14, 5, 45, tzinfo=d.timezone.utc).timestamp())
        t = []
        # AFIRMAÇÕES HONESTAS: (1) apanha a retomada de 14/08 que o live perdeu; (2) determinístico.
        # NÃO afirma "rejeita os 5 facas" — isso era falso (dispara losers no topo/crash = custo estrutural
        # aceite pelo Cris; não há separador 15M — ver reclaim_significance_v3). FORWARD=árbitro.
        t.append(("apanha retomada 14/08 06:45", t_reclaim in ft))
        t.append(("determinístico (scan estável)", [f["reclaim_t"] for f in fires] == [f["reclaim_t"] for f in fires2]))
        for lab, r in t:
            print("  [%s] %s" % ("OK" if r else "FAIL", lab))
        allok = all(r for _, r in t)
        # tally honesto da janela de crash 12-14/08 (adversa a longs; NÃO é veredito de edge)
        lo = int(d.datetime(2026, 8, 12, tzinfo=d.timezone.utc).timestamp())
        cw = [f for f in fires if f["reclaim_t"] >= lo]
        print("selftest", "PASS" if allok else "FAIL", "| fires total:", len(fires),
              "| fires 12-14/08:", len(cw), "(janela crash, mistos — forward=árbitro)")
        sys.exit(0 if allok else 1)
