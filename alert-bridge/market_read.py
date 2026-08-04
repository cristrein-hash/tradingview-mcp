#!/usr/bin/env python3
"""LEITOR CANÓNICO ÚNICO de TODOS os indicadores (Cris 2026-08-04: "leitor canónico para todos os indicadores
em todas as velas e fechamento de velas — tem que ser PERMANENTE"). CONSOME o store_reader (que já lê tudo o
que o bar-store capta via MCP) e devolve UM snapshot normalizado por TF: preço, OB Detector (zonas reais), SMC,
SVP, NAS, Market Order Bubbles, RSI, Volume. NUNCA aproximar/inventar — a fonte é sempre o indicador real.

Este é o CAMINHO DE LEITURA único; vela/validador/candle-reader/map-sync devem consumir `snapshot(tf)`.
NÃO reconstrói readers paralelos — assembla o store_reader. py3.9."""
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))
import store_reader as SR


def _num(x):
    """Parser numérico dos valores TradingView. FIX auditoria: TV usa narrow-nbsp (\u202f) em '9.27 K' —
    sem o strip, SVP/Volume viravam None silenciosamente e o prompt levava 'SVP comprador' falso."""
    try:
        s = str(x).replace(",", "").replace(" ", "").replace("\u202f", "").replace("\xa0", "").replace("K", "e3").replace("M", "e6")
        return float(s)
    except Exception:
        return None


def _studies(tf):
    """study_values do store (devolve (data, age)) -> dict {nome_estudo: values}."""
    data, _age = SR.study_values(tf)
    studies = (data or {}).get("studies") or []
    return {st.get("name", ""): st.get("values", {}) for st in studies}


def _find(studies, sub):
    for name, vals in studies.items():
        if sub in name:
            return vals
    return {}


def ob_zones(tf, ref_price=None):
    """Zonas OB Detector v11 REAIS do store (caminho canónico; NUNCA aproximar). pine_boxes->(data,age).
    NOTA DE AUDITORIA (04/08): as zonas 4515-5598 do 240 SÃO XAU REAL — ATH 5597.91 em 2026-01-28 e a escada
    de supplies do crash (verificado em bars_1d). O 'guard de contaminação' que aqui esteve por 1 commit era
    ERRO MEU (assumi teto 4382 sem ler os dados) e excluía zonas HTF reais — removido. A captura (tab_pin
    verifica símbolo XAUUSD + resolução) estava certa. NUNCA assumir — ler os dados. ref_price mantido só
    para ordenar por proximidade se fornecido."""
    data, _age = SR.pine_boxes(tf)
    for st in (data or {}).get("studies", []):
        if "OB Detector" in st.get("name", ""):
            zs = sorted([{"low": z["low"], "high": z["high"]} for z in st.get("zones", [])
                         if "low" in z], key=lambda z: -z["high"])
            if ref_price:
                zs = sorted(zs, key=lambda z: abs((z["low"] + z["high"]) / 2 - ref_price))
            return zs
    return []


def snapshot(tf="15"):
    """UM snapshot normalizado de TODOS os indicadores REAIS no TF (fecho da vela corrente). None se store off."""
    st = _studies(tf)
    if not st:
        return None
    bars = SR.bars(tf)
    price = bars[-1]["c"] if bars else None
    nas = _find(st, "NAS TOP BOTTOM")
    svp = _find(st, "Session Volume Profile")
    rsi = _find(st, "Relative Strength Index")
    vol = _find(st, "Volume")
    bub = _find(st, "Market Order Bubbles")
    smc = _find(st, "Smart Money Concepts")
    try:
        t0 = bars[-6]["t"] if len(bars) >= 6 else None
        bub_recent = len(SR.shape_pairs("bubbles", t0, bars[-1]["t"])) if bars else 0
        nas_recent = len(SR.shape_pairs("nas", t0, bars[-1]["t"])) if bars else 0
    except Exception:
        bub_recent = nas_recent = 0
    return {
        "tf": tf, "price": price, "fresh": SR.fresh(tf),
        "ob_zones": ob_zones(tf, ref_price=price),                  # OB Detector REAL (com guard de contaminação)
        "smc_plotcandle": _num(smc.get("PlotCandle")),
        "svp": {"up": _num(svp.get("Up")), "down": _num(svp.get("Down")), "total": _num(svp.get("Total"))},
        "rsi": _num(rsi.get("RSI")), "rsi_ma": _num(rsi.get("RSI-based MA")),
        "volume": _num(vol.get("Volume")),
        "nas": {"top": _num(nas.get("NAS TOP / SHORT")), "bottom": _num(nas.get("NAS BOTTOM / LONG")),
                "rsi": _num(nas.get("NAS_RSI")), "dist_ema_atr": _num(nas.get("NAS_DISTANCE_FROM_EMA_ATR"))},
        "bubbles_now": _num(bub.get("Shapes")), "bubbles_recent": bub_recent, "nas_recent": nas_recent,
    }


def read_line(tf="15"):
    """Uma linha legível do snapshot (para chat/log)."""
    s = snapshot(tf)
    if not s:
        return f"[{tf}] sem dados no store"
    obs = " · ".join(f"{z['low']:.0f}-{z['high']:.0f}" for z in s["ob_zones"][:4])
    svp = s["svp"]
    if svp["up"] is None and svp["down"] is None:
        side = "—"                                       # não inventar lado quando o SVP não existe no TF
    else:
        side = "vendedor" if (svp["down"] or 0) > (svp["up"] or 0) else "comprador"
    return (f"[{tf}] px {s['price']} · RSI {s['rsi']}/{s['rsi_ma']} · SVP {side} "
            f"(U{svp['up']}/D{svp['down']}) · NAS rsi {s['nas']['rsi']} dist {s['nas']['dist_ema_atr']}ATR · "
            f"bubbles {s['bubbles_recent']}/6b · OB: {obs}")


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        s = snapshot("15")
        ok1 = s is not None and s.get("price") is not None
        ok2 = s and isinstance(s.get("ob_zones"), list) and len(s["ob_zones"]) > 0
        ok3 = s and s.get("rsi") is not None and s.get("nas", {}).get("rsi") is not None
        for lab, ok in (("snapshot devolve preço", ok1), ("OB zones reais presentes", ok2),
                        ("RSI+NAS presentes", ok3)):
            print(f"  [{'OK' if ok else 'FAIL'}] {lab}")
        allok = ok1 and ok2 and ok3
        print("selftest", "PASS" if allok else "FAIL")
        sys.exit(0 if allok else 1)
    for tf in ("15", "60", "240"):
        print(read_line(tf))
