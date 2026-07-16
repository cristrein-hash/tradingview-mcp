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


def _ema(vals, period):
    if len(vals) < period:
        return None
    k = 2 / (period + 1)
    e = sum(vals[:period]) / period
    for v in vals[period:]:
        e = v * k + e * (1 - k)
    return round(e, 3)


def read_micro(count=120):
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


if __name__ == "__main__":
    import json
    print(json.dumps(read_micro(), indent=1, ensure_ascii=False))
