#!/usr/bin/env python3
"""RETOMA ENGINE v1 — XAU 15M LONG · retoma-de-demanda em HIGHER-LOW (a camada órfã do router).
Classe caracterizada em research/cp_char_fresh_bottoms_20260727.py sobre os fundos IDEAIS do Cris
(A 16/07 3969 · B 20/07 3998 · C 24/07 4044 · D 27/07 4065): fundos de RETOMA dentro de recuperação /
range — 3/4 são higher-lows, pernas 11-23×ATR, TODOS com reclaim — que o Cp (capitulação profunda,
baseline CONGELADO, não tocado) corretamente não apanha.

PRINCÍPIOS (declarados ANTES de olhar outcomes — nunca fit ao dia visível):
- COMPLEMENTO DO Cp: candidato = fundo fractal que o Cp NÃO qualifica (fundo_ok==None) — zero overlap
  de alertas por construção; o Cp continua dono da capitulação profunda.
- PERNA SIGNIFICATIVA: legMag >= LEG_FRESH_MIN = 8×ATR — princípio "metade do canónico Cp (15)": queda
  real, não ruído; abaixo disso é micro-oscilação (não é nível re-derivado dos 4 GT).
- ANCORAGEM NA DEMANDA (lição S1 + SLs S2/S4/S5 do Cris): o low ancora numa zona de DEMANDA existente
  (OB/SMC lidas do store — NUNCA inventadas): low dentro da zona ou a <=0.5×ATR da borda superior.
- GATILHO = RECLAIM verbatim do Cp (entry_first, importado — mesma mecânica validada GT 5/5).
- SL ESTRUTURAL = extremo inferior da zona de demanda −0.1×ATR (o padrão dos stops do Cris, 3997.55×3);
  fallback low do fundo −0.1×ATR se o fundo ancorou pela borda. Exit 3R fixo (padrão camadas 15M).
- Leilão (buy_dens/leg_sell) = VOZ medida e reportada, NÃO veto (canon convergência; o read/humano pesa).
Funções puras, sem I/O — paridade research/runtime. py3.9."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "strategies/xau_15m_long/reversal/CP_CAPITULATION"))
import cp_engine_live as cp

LEG_FRESH_MIN = 8.0          # principio: metade do canonico Cp (15) — queda real, nao ruido
ANCHOR_ATR = 0.5             # licao S1: ancora na zona (low dentro ou <=0.5 ATR da borda superior)


def zone_anchor(low, zones):
    """Zona de demanda EXISTENTE que ancora o fundo: low dentro de [zlow,zhigh] ou <=ANCHOR_ATR acima
    da borda. zones = lista [{'low':..,'high':..}] (store/dossiê — nunca inventadas). Devolve a zona
    (a de borda superior mais próxima) ou None."""
    best = None
    for z in zones or []:
        zl, zh = z.get("low"), z.get("high")
        if zl is None or zh is None:
            continue
        if zl <= low <= zh or 0 <= (low - zh):
            d = 0.0 if zl <= low <= zh else (low - zh)
            if best is None or d < best[0]:
                best = (d, z)
    return best


def retoma_scan(T, O, H, L, C, BUYS, SELLS, zones, t_lo=None, t_hi=None):
    """Varre a série 15M: fundos fractais NÃO-Cp com perna >=8×ATR, ancorados em demanda, com reclaim.
    Devolve candidatos {p, fundo_t, k, etime, ent, sl, tgt, legmag, anchored, zona, buy_dens, leg_sell}."""
    N = len(T)
    ATR = cp.atr_series(H, L, C)
    BT = [x["t"] for x in BUYS]; ST = [x["t"] for x in SELLS]
    out = []
    for p in cp.swing_lows(H, L, N):
        if t_lo is not None and T[p] < t_lo:
            continue
        if t_hi is not None and T[p] > t_hi:
            continue
        atr = ATR[p] or 5.0
        hb = max(range(max(0, p - cp.LEGWIN), p + 1), key=lambda k: H[k])
        legmag = (H[hb] - L[p]) / atr
        if legmag < LEG_FRESH_MIN:
            continue                                    # micro-oscilacao
        if cp.fundo_ok(p, T, H, L, ATR, BUYS, BT, SELLS, ST) is not None:
            continue                                    # capitulacao profunda = territorio do Cp
        za = zone_anchor(L[p], zones)
        if za is None or za[0] > ANCHOR_ATR * atr:
            continue                                    # sem ancoragem estrutural = sem candidato (S1)
        e = cp.entry_first(p, T, O, H, L, C, ATR, N)
        if not e:
            continue
        zona = za[1]
        # SL estrutural: extremo inferior da demanda -0.1ATR (padrao Cris); nunca ACIMA do low do fundo
        sl = round(min(zona["low"], L[p]) - 0.1 * atr, 2)
        r = e["ent"] - sl
        if r <= 0.05 * atr:
            continue
        dur = max(1, p - hb)
        out.append({"p": p, "fundo_t": int(T[p]), "low": L[p], "k": e["k"], "etime": int(T[e["k"]]),
                    "ent": e["ent"], "sl": sl, "tgt": round(e["ent"] + 3 * r, 2),
                    "legmag": round(legmag, 1), "anchored": round(za[0], 2),
                    "zona": {"low": zona["low"], "high": zona["high"]},
                    "buy_dens": round(cp.sz(BUYS, BT, T[hb], T[p]) / dur, 2),
                    "leg_sell": cp.sz(SELLS, ST, T[hb], T[p])})
    return out
