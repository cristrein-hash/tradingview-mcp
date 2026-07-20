#!/usr/bin/env python3
"""Reader MICRO 15M (P3/E0) — lê o eixo micro na tab 15M dedicada: preço vs EMAs (computadas do OHLCV),
RSI+RSI-MA, DMI (ADX/+DI/-DI), Choppiness, volume de sessão (SVP), NAS. Determinístico. NUNCA toca a tab
do P1 (pina a tab 15M por target). py3.9. Uso: python3 context_micro.py
"""
import os, sys
from pathlib import Path
BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))
from draw_xau_4h_trades import MCPClient
from context_mtf import list_chart_targets
import context_structure as cs


def _ema(vals, period):
    if len(vals) < period:
        return None
    k = 2 / (period + 1)
    e = sum(vals[:period]) / period
    for v in vals[period:]:
        e = v * k + e * (1 - k)
    return round(e, 3)


# ---------- F-A1: iniciativa das velas (fator 1) + vitalidade de sessão (fator 4) ----------
def _tr(H, L, C, i):
    if i <= 0:
        return H[i] - L[i]
    return max(H[i] - L[i], abs(H[i] - C[i - 1]), abs(L[i] - C[i - 1]))


def candle_block(O, H, L, C, atr, W=4):
    """Iniciativa das velas: corpo/range por ATR das últimas W barras, força por lado (F-A1.1). Descritivo
    (o read pondera como voz), causal. Ver docs/architecture/E2_READ_CALIBRATION_DESIGN_20260718 §9."""
    if not atr or atr <= 0 or len(C) < W:
        return None
    bars = []; up_f = dn_f = 0.0
    for i in range(len(C) - W, len(C)):
        body = C[i] - O[i]
        b_atr = round(abs(body) / atr, 2)
        bars.append({"dir": "up" if body > 0 else ("down" if body < 0 else "flat"),
                     "body_atr": b_atr, "range_atr": round((H[i] - L[i]) / atr, 2)})
        if body > 0: up_f += b_atr
        elif body < 0: dn_f += b_atr
    up_f = round(up_f, 2); dn_f = round(dn_f, 2)
    dom = "buy" if up_f > dn_f * 1.3 else ("sell" if dn_f > up_f * 1.3 else "balanced")
    return {"window_bars": W, "up_force_atr": up_f, "dn_force_atr": dn_f, "dominant": dom, "bars": bars}


def vitality_block(H, L, C, atr, k=4):
    """Vitalidade: média do true-range das últimas k barras / ATR (F-A1.2). <0.6 = morna/wind-down."""
    if not atr or atr <= 0 or len(C) < k + 1:
        return None
    ratio = round((sum(_tr(H, L, C, i) for i in range(len(C) - k, len(C))) / k) / atr, 2)
    return {"ratio": ratio, "label": "low" if ratio < 0.6 else ("high" if ratio > 1.3 else "normal"), "k": k}


def _attach_tape(m, O, H, L, C, W=4, k=4):
    """Anexa candles+vitality ao bloco micro (F-A1). Silencioso se dados insuficientes. NÃO altera decisão."""
    if not (m and C and len(C) >= max(W, k) + 15):
        return m
    atr = cs.atr(H, L, C, len(C) - 1, 14)
    if atr:
        cb = candle_block(O, H, L, C, atr, W); vb = vitality_block(H, L, C, atr, k)
        if cb: m["candles"] = cb
        if vb: m["vitality"] = vb
    return m


def _micro_from(g, closes, bar_time):
    """Constrói o bloco micro a partir de study_values agrupados (g) + closes (mesma lógica de sempre)."""
    last = closes[-1] if closes else None
    ema9, ema21, ema50 = _ema(closes, 9), _ema(closes, 21), _ema(closes, 50)
    rsi = g.get("Relative Strength Index", {})
    dmi = g.get("Directional Movement Index", {})
    svp = g.get("Session Volume Profile", {})
    chop = g.get("Choppiness Index", {})
    nas = g.get("NAS TOP BOTTOM DETECTOR", {})
    up, dn = svp.get("Up"), svp.get("Down")

    def num(x):
        try: return float(str(x).replace("K", "e3").replace(" ", ""))
        except Exception: return None
    return {
        "close": last, "bar_time": bar_time,
        "ema": {"ema9": ema9, "ema21": ema21, "ema50": ema50,
                "pos": ("above" if (last and ema21 and last > ema21) else "below") if last and ema21 else None},
        "rsi": rsi.get("RSI"), "rsi_ma": rsi.get("RSI-based MA"),
        "dmi": {"adx": dmi.get("ADX"), "plus_di": dmi.get("+DI"), "minus_di": dmi.get("-DI")},
        "chop": chop.get("Choppiness Index") or (list(chop.values())[0] if chop else None),
        "volume_session": {"up": num(up), "dn": num(dn),
                           "ratio": round(num(up) / num(dn), 2) if num(up) and num(dn) else None},
        "nas": {"bottom": nas.get("NAS_BOTTOM_SIGNAL"), "top": nas.get("NAS_TOP_SIGNAL"),
                "dist_ema_atr": nas.get("NAS_DISTANCE_FROM_EMA_ATR")},
    }


def read_micro_store(count=120):
    """STORE-FIRST (Fase 1, 2026-07-18): micro 15M do bar-store, zero CDP. None se store não-fresco."""
    import store_reader as SR
    if not SR.fresh("15"):
        return None
    sv, _age = SR.study_values("15")
    if sv is None:
        return None
    g = {s.get("name"): s.get("values", {}) for s in (sv or {}).get("studies", [])}
    rs = SR.bars("15", count)
    closes = [r["c"] for r in rs]
    bar_time = rs[-1]["t"] if rs else None
    m = _micro_from(g, closes, bar_time)
    O = [r.get("o") for r in rs]; H = [r.get("h") for r in rs]; L = [r.get("l") for r in rs]
    if all(x is not None for x in O + H + L):
        _attach_tape(m, O, H, L, closes)     # F-A1: velas + vitalidade (store = barras fechadas)
    return m


def read_micro(count=120):
    try:
        st = read_micro_store(count)
        if st is not None:
            return st
    except Exception:
        pass                                              # store doente -> caminho MCP antigo
    try:                                                  # anti-herd (auditoria #5): gate o fallback-MCP
        import store_reader as SR
        if not SR.fallback_ok("micro"):
            return None
    except Exception:
        pass
    saved = os.environ.get("TVMCP_TARGET_CHART_ID")
    try:
        for tid in list_chart_targets():
            os.environ["TVMCP_TARGET_CHART_ID"] = tid
            c = MCPClient()
            try:
                c.start()
                st = c.call_tool("chart_get_state") or {}
                if str(st.get("resolution")) != "15":
                    continue
                sv = c.call_tool("data_get_study_values") or {}
                g = {s.get("name"): s.get("values", {}) for s in sv.get("studies", [])}
                oh = c.call_tool("data_get_ohlcv", {"count": count}) or {}
                bars = oh.get("bars") or oh.get("ohlcv") or []
                closes = [b.get("close") for b in bars if b.get("close") is not None]
                last = closes[-1] if closes else None
                bar_time = bars[-1].get("time") if bars else None
                ema9, ema21, ema50 = _ema(closes, 9), _ema(closes, 21), _ema(closes, 50)
                rsi = g.get("Relative Strength Index", {})
                dmi = g.get("Directional Movement Index", {})
                svp = g.get("Session Volume Profile", {})
                chop = g.get("Choppiness Index", {})
                nas = g.get("NAS TOP BOTTOM DETECTOR", {})
                up, dn = svp.get("Up"), svp.get("Down")

                def num(x):
                    try: return float(str(x).replace("K", "e3").replace(" ", ""))
                    except Exception: return None
                m = {
                    "close": last, "bar_time": bar_time,
                    "ema": {"ema9": ema9, "ema21": ema21, "ema50": ema50,
                            "pos": ("above" if (last and ema21 and last > ema21) else "below") if last and ema21 else None},
                    "rsi": rsi.get("RSI"), "rsi_ma": rsi.get("RSI-based MA"),
                    "dmi": {"adx": dmi.get("ADX"), "plus_di": dmi.get("+DI"), "minus_di": dmi.get("-DI")},
                    "chop": chop.get("Choppiness Index") or (list(chop.values())[0] if chop else None),
                    "volume_session": {"up": num(up), "dn": num(dn),
                                       "ratio": round(num(up) / num(dn), 2) if num(up) and num(dn) else None},
                    "nas": {"bottom": nas.get("NAS_BOTTOM_SIGNAL"), "top": nas.get("NAS_TOP_SIGNAL"),
                            "dist_ema_atr": nas.get("NAS_DISTANCE_FROM_EMA_ATR")},
                }
                Oa = [b.get("open") for b in bars]; Ha = [b.get("high") for b in bars]; La = [b.get("low") for b in bars]
                if all(x is not None for x in Oa + Ha + La) and len(closes) == len(bars):
                    _attach_tape(m, Oa, Ha, La, closes)   # F-A1 (fallback MCP; última barra pode estar em formação)
                return m
            except Exception as e:
                return {"error": f"{type(e).__name__}:{str(e)[:60]}"}
            finally:
                try: c.stop()
                except Exception: pass
    finally:
        if saved is None:
            os.environ.pop("TVMCP_TARGET_CHART_ID", None)
        else:
            os.environ["TVMCP_TARGET_CHART_ID"] = saved
    return {"error": "tab 15M nao encontrada"}


def _selftest():
    n = 40
    C = [100.0 - i for i in range(n)]          # descida
    O = [C[i] + 0.8 for i in range(n)]         # close<open -> velas DOWN com corpo
    H = [O[i] + 0.3 for i in range(n)]; L = [C[i] - 0.3 for i in range(n)]
    atr = cs.atr(H, L, C, n - 1, 14)
    cb = candle_block(O, H, L, C, atr, 4); vb = vitality_block(H, L, C, atr, 4)
    m = {"close": C[-1]}; _attach_tape(m, O, H, L, C)
    r = [("candle dominant=sell", bool(cb) and cb["dominant"] == "sell"),
         ("candle dn_force>0", bool(cb) and cb["dn_force_atr"] > 0),
         ("vitality ratio>0", bool(vb) and vb["ratio"] > 0),
         ("attach_tape adiciona campos", "candles" in m and "vitality" in m),
         ("W insuficiente -> None", candle_block(O, H, L, C, atr, 999) is None)]
    allok = all(ok for _, ok in r)
    for name, ok in r: print(f"  {'OK' if ok else 'FALHA'} {name}")
    print("SELFTEST context_micro:", "PASS" if allok else "FALHA")
    return 0 if allok else 1


if __name__ == "__main__":
    import json
    if "--selftest" in sys.argv:
        sys.exit(_selftest())
    print(json.dumps(read_micro(), indent=1, ensure_ascii=False))
