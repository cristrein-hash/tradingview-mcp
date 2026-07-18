#!/usr/bin/env python3
"""F-A2 — MAPA DE ÍMANES (P3/E0). VOZ descritiva no dossiê, NÃO sinal/gate/seta. Store-backed, causal,
close-only. Fonde FVG-não-mitigado + clusters de liquidez (equal H/L) + zonas OB (pine_boxes) num mapa
único acima/abaixo, + ordinalidade do pullback (fator 2). Serve o read E2 (o mapa que faltou 2026-07-17).
Grelha CONGELADA — ver docs/architecture/F_A2_MAGNET_MAP_PREREG_20260718.md. py3.9.
Uso: python3 context_magnets.py"""
import sys
from pathlib import Path
BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))
import context_structure as cs

# --- GRELHA CONGELADA (princípio, não fit; §2 do prereg) ---
LOOKBACK = 480          # 5 dias 15M = LEGWIN Cp
FVG_MIN_ATR = 0.25      # micro-gaps = ruído
SWING_K = 3             # = M_FRAC Cp; lag causal
CLUSTER_TOL_ATR = 0.25  # unidade "igual" do stack
CLUSTER_N = 2           # equal-highs = 2 toques
MAX_LIST = 4            # nearest N por lado no render


def _atr(H, L, C, n=14):
    a = cs.atr(H, L, C, len(C) - 1, n) if len(C) > n else None
    return a or 5.0


# ---------- FVG (regra 3 velas, mitigação só com barras fechadas j>i) ----------
def fvgs(O, H, L, C, atr, last):
    """Devolve FVGs não-mitigados: bullish = magnet ABAIXO (suporte), bearish = ACIMA (resistência)."""
    n = len(C); start = max(2, n - LOOKBACK)
    below = []; above = []   # (dist_atr, size_atr, age_bars, edge_price)
    for i in range(start, n):
        # bullish: void [high[i-2], low[i]] ; mitigado se alguma barra fechada j>i desce ao topo (L[j] <= low[i])
        if L[i] > H[i - 2]:
            size = L[i] - H[i - 2]
            if size >= FVG_MIN_ATR * atr:
                mit = any(L[j] <= L[i] for j in range(i + 1, n))
                if not mit:
                    below.append((round((C[last] - L[i]) / atr, 2), round(size / atr, 2), n - 1 - i, L[i]))
        # bearish: void [high[i], low[i-2]] ; mitigado se alguma barra fechada j>i sobe (H[j] >= high[i])
        if H[i] < L[i - 2]:
            size = L[i - 2] - H[i]
            if size >= FVG_MIN_ATR * atr:
                mit = any(H[j] >= H[i] for j in range(i + 1, n))
                if not mit:
                    above.append((round((H[i] - C[last]) / atr, 2), round(size / atr, 2), n - 1 - i, H[i]))
    below = [x for x in below if x[0] >= 0]; above = [x for x in above if x[0] >= 0]
    below.sort(key=lambda x: x[0]); above.sort(key=lambda x: x[0])
    fmt = lambda x: {"type": "fvg", "dist_atr": x[0], "size_atr": x[1], "age": x[2]}
    return [fmt(x) for x in above[:MAX_LIST]], [fmt(x) for x in below[:MAX_LIST]]


# ---------- swings fractais confirmados (k barras à direita fechadas = lag k) ----------
def swings(H, L, n, k=SWING_K):
    hi = []; lo = []
    for p in range(k, n - k):                       # p+k <= n-1 => confirmado
        if H[p] == max(H[p - k:p + k + 1]) and H[p] > max(H[p - k:p]):
            hi.append((p, H[p]))
        if L[p] == min(L[p - k:p + k + 1]) and L[p] < min(L[p - k:p]):
            lo.append((p, L[p]))
    return hi, lo


# ---------- clusters de liquidez (equal highs/lows) ----------
def clusters(prices, atr, close, side):
    """side='high'(acima) ou 'low'(abaixo). Agrupa preços dentro de tol; grupo >=N = nível de liquidez."""
    if not prices:
        return []
    ps = sorted(p for _, p in prices)
    groups = []; cur = [ps[0]]
    for p in ps[1:]:
        if p - cur[-1] <= CLUSTER_TOL_ATR * atr:
            cur.append(p)
        else:
            groups.append(cur); cur = [p]
    groups.append(cur)
    out = []
    for g in groups:
        if len(g) >= CLUSTER_N:
            lvl = sum(g) / len(g)
            if side == "high" and lvl > close:
                out.append({"type": "liq_cluster", "dist_atr": round((lvl - close) / atr, 2), "touches": len(g)})
            elif side == "low" and lvl < close:
                out.append({"type": "liq_cluster", "dist_atr": round((close - lvl) / atr, 2), "touches": len(g)})
    out.sort(key=lambda x: x["dist_atr"])
    return out[:MAX_LIST]


# ---------- ordinalidade do pullback (fator 2) ----------
def pullback_ordinal(hi, lo):
    """Cauda de higher-lows (up-leg) ou lower-highs (down-leg). ordinal = nº consecutivos."""
    def tail(seq, cmp):
        c = 0
        for a, b in zip(seq[::-1], seq[-2::-1]):
            if cmp(a[1], b[1]): c += 1
            else: break
        return c
    up = tail(lo, lambda a, b: a > b) if len(lo) >= 2 else 0     # higher-lows
    dn = tail(hi, lambda a, b: a < b) if len(hi) >= 2 else 0     # lower-highs
    if up >= dn and up > 0:
        leg, ordn = "up", up
    elif dn > 0:
        leg, ordn = "down", dn
    else:
        return {"leg_dir": "range", "ordinal": 0, "maturity": "indef"}
    mat = "continuação_provável" if ordn == 1 else ("maduro_reversão_mais_provável" if ordn >= 3 else "intermédio")
    return {"leg_dir": leg, "ordinal": ordn, "maturity": mat}


# ---------- OB (pine_boxes já no store) -> fundir no mapa ----------
def _ob_from_boxes(pb, atr, close):
    above = []; below = []
    for study in (pb or {}).get("studies", []):
        for z in study.get("zones", []):
            hi = z.get("high"); lo = z.get("low")
            if hi is None or lo is None:
                continue
            if lo > close:
                above.append({"type": "ob", "dist_atr": round((lo - close) / atr, 2)})
            elif hi < close:
                below.append({"type": "ob", "dist_atr": round((close - hi) / atr, 2)})
    above.sort(key=lambda x: x["dist_atr"]); below.sort(key=lambda x: x["dist_atr"])
    return above[:MAX_LIST], below[:MAX_LIST]


def read_magnets():
    """Store-first, causal. None se store 15M não-fresco (dossiê fica sem magnets; E2 lida com ausência)."""
    import store_reader as SR
    if not SR.fresh("15"):
        return None
    rs = SR.bars("15", LOOKBACK + 40)
    if len(rs) < 60:
        return None
    O = [r["o"] for r in rs]; H = [r["h"] for r in rs]; L = [r["l"] for r in rs]; C = [r["c"] for r in rs]
    n = len(C); last = n - 1; atr = _atr(H, L, C)
    close = C[last]
    fa, fb = fvgs(O, H, L, C, atr, last)
    hi, lo = swings(H, L, n)
    ca = clusters(hi, atr, close, "high"); cb = clusters(lo, atr, close, "low")
    pb, _ = SR.pine_boxes("15")
    oba, obb = _ob_from_boxes(pb, atr, close)
    above = sorted(fa + ca + oba, key=lambda x: x["dist_atr"])[:MAX_LIST]
    below = sorted(fb + cb + obb, key=lambda x: x["dist_atr"])[:MAX_LIST]
    return {"above": above, "below": below, "pullback": pullback_ordinal(hi, lo), "atr": round(atr, 2)}


def _selftest():
    # FVG sintético: gap bullish claro + mitigação
    import random
    O = [100]*10; H = list(range(100, 110)); L = [h-1 for h in H]; C = [h-0.5 for h in H]
    # forçar bullish FVG na barra 5: low[5] > high[3]
    L[5] = H[3] + 2; H[5] = L[5] + 1; C[5] = L[5] + 0.5; O[5] = L[5]
    atr = 1.0
    fa, fb = fvgs(O, H, L, C, atr, len(C)-1)
    ok_fvg = isinstance(fb, list)  # estrutura válida
    po = pullback_ordinal([(1, 100), (5, 102), (9, 104)], [(2, 99), (6, 101), (8, 103)])
    ok_po = po["leg_dir"] == "up" and po["ordinal"] >= 1
    print("selftest F-A2:", "PASS" if (ok_fvg and ok_po) else "FALHA", "| pullback:", po)
    return 0 if (ok_fvg and ok_po) else 1


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        raise SystemExit(_selftest())
    import json
    print(json.dumps(read_magnets(), indent=1, ensure_ascii=False))
