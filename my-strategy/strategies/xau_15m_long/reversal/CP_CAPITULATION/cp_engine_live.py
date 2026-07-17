#!/usr/bin/env python3
"""Cp CAPITULATION — motor PURO (lógica VERBATIM do baseline aprovado CP_ENGINE_PREREG_FORWARD_20260716,
tal como corre em cp_plot_window.py / cp_refined.py). Funções puras sobre arrays — SEM I/O, SEM MCP —
para que a MESMA lógica sirva (a) paridade sobre RAW e (b) runtime live. NÃO ALTERAR THRESHOLDS: baseline
congelado; qualquer refino = novo prereg.
Regras: fundo = swing-low fractal M_FRAC=3 · legMag(H[hb..p])/ATR>=15 (hb em p-480..p) · is_leg_bottom
L[p]<=min(192) · confluência auction na perna [hb..p]: buy_dens>=0.25 OU leg_sell>=180 · entry_first =
1º reclaim (C>H[-1] e C>O) em p+3..p+96 sem tocar SL · SL = L[p]-0.1*ATR · target fixo 3R. Alert-only."""
import bisect

M_FRAC, LEGWIN, LEGMIN = 3, 480, 15
ENTRY_HORIZON = 96
BUY = {"plot_0": 1, "plot_2": 2, "plot_4": 3}      # mapeamento validado Cp (8 scripts + context_confluence)
SELL = {"plot_6": 1, "plot_8": 2, "plot_10": 3}


def atr_series(H, L, C):
    N = len(C); ATR = [None] * N; trs = []
    for i in range(N):
        if i > 0:
            trs.append(max(H[i] - L[i], abs(H[i] - C[i - 1]), abs(L[i] - C[i - 1])))
        ATR[i] = sum(trs[-14:]) / 14 if len(trs) >= 14 else None
    return ATR


def swing_lows(H, L, N):
    def is_sl(p):
        return (p - M_FRAC >= 0 and p + M_FRAC < N and
                L[p] == min(L[p - M_FRAC:p + M_FRAC + 1]) and L[p] < min(L[p - M_FRAC:p]))
    return [p for p in range(M_FRAC, N - M_FRAC) if is_sl(p)]


def sz(bubs, ts, t0, t1):
    return sum(bubs[i]["sz"] for i in range(bisect.bisect_left(ts, t0), bisect.bisect_right(ts, t1)))


def fundo_ok(p, T, H, L, ATR, BUYS, BT, SELLS, ST):
    """Gates do fundo (verbatim run()): legMag + is_leg_bottom + confluência auction na perna."""
    hb = max(range(max(0, p - LEGWIN), p + 1), key=lambda k: H[k])
    atr = ATR[p] or 5.0
    dur = max(1, p - hb)
    if (H[hb] - L[p]) / atr < LEGMIN:
        return None
    if not (L[p] <= min(L[max(0, p - 192):p + 1]) + 1e-9):
        return None
    if not (sz(BUYS, BT, T[hb], T[p]) / dur >= 0.25 or sz(SELLS, ST, T[hb], T[p]) >= 180):
        return None
    return {"hb": hb, "atr": atr}


def entry_first(j, T, O, H, L, C, ATR, N):
    """1º reclaim em j+3..j+96 sem tocar SL (verbatim)."""
    atr = ATR[j] or 5.0
    sl = round(L[j] - 0.1 * atr, 2)
    for k in range(j + M_FRAC, min(N, j + ENTRY_HORIZON)):
        if L[k] <= sl:
            return None
        if C[k] > H[k - 1] and C[k] > O[k]:
            ent = round(C[k], 2); r = ent - sl
            if r > 0.05 * atr:
                return {"k": k, "ent": ent, "sl": sl, "tgt": round(ent + 3 * r, 2)}
    return None


def scan(T, O, H, L, C, BUYS, SELLS, t_lo=None, t_hi=None):
    """Corre o engine completo sobre a série: devolve todos os trades (fundo p, entrada k, ent/sl/tgt)."""
    N = len(T)
    ATR = atr_series(H, L, C)
    BT = [x["t"] for x in BUYS]; ST = [x["t"] for x in SELLS]
    out = []
    for p in swing_lows(H, L, N):
        if t_lo is not None and T[p] < t_lo:
            continue
        if t_hi is not None and T[p] > t_hi:
            continue
        if fundo_ok(p, T, H, L, ATR, BUYS, BT, SELLS, ST) is None:
            continue
        e = entry_first(p, T, O, H, L, C, ATR, N)
        if not e:
            continue
        out.append({"p": p, "fundo_t": int(T[p]), "k": e["k"], "etime": int(T[e["k"]]),
                    "ent": e["ent"], "sl": e["sl"], "tgt": e["tgt"]})
    return out


def bubbles_from_pairs(pairs):
    """pairs = iterável de (t, plot) -> (BUYS, SELLS) ordenados, dedup por (t, plot) — como no RAW loader."""
    buyb = {}; sellb = {}
    for t, plot in pairs:
        if t is None:
            continue
        if plot in BUY and (t, plot) not in buyb:
            buyb[(t, plot)] = {"t": t, "sz": BUY[plot]}
        elif plot in SELL and (t, plot) not in sellb:
            sellb[(t, plot)] = {"t": t, "sz": SELL[plot]}
    return (sorted(buyb.values(), key=lambda x: x["t"]), sorted(sellb.values(), key=lambda x: x["t"]))
