#!/usr/bin/env python3
"""E1 ACCEPTANCE / REPLAY harness (P4) — prova de recall do short perdido de hoje. Captura OHLCV NATIVO
por TF (15M/1H/4H/1D, sem resamplear), sintetiza a sequência de dossiês barra-a-barra (structure() = a
MESMA que o E0 usa, causal), e corre o E1 detect()+materiality sobre a janela da queda. PASS = E1 emite
candidato SHORT durante o break bearish. Offline após a captura. py3.9. Uso: python3 e1_replay.py
"""
import os, sys, bisect
from pathlib import Path
BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))
from draw_xau_4h_trades import MCPClient
from context_mtf import list_chart_targets
import context_structure as cs
import e1_detector as e1

TFS = ("15", "60", "240", "1D")


def capture():
    """Captura OHLCV nativo de cada TF (pin por tab). Devolve {tf: {H,L,C,T}}."""
    data = {}
    saved = os.environ.get("TVMCP_TARGET_CHART_ID")
    try:
        for tid in list_chart_targets():
            os.environ["TVMCP_TARGET_CHART_ID"] = tid
            c = MCPClient()
            try:
                c.start()
                st = c.call_tool("chart_get_state") or {}
                res = str(st.get("resolution"))
                if res not in TFS or res in data:
                    continue
                oh = c.call_tool("data_get_ohlcv", {"count": 400}) or {}
                bars = oh.get("bars") or oh.get("ohlcv") or []
                data[res] = {"H": [b["high"] for b in bars], "L": [b["low"] for b in bars],
                             "C": [b["close"] for b in bars], "T": [b["time"] for b in bars]}
            finally:
                try: c.stop()
                except Exception: pass
    finally:
        if saved is None: os.environ.pop("TVMCP_TARGET_CHART_ID", None)
        else: os.environ["TVMCP_TARGET_CHART_ID"] = saved
    return data


def _rsi(C, i, n=14):
    if i < n: return None
    g = l = 0.0
    for k in range(i - n + 1, i + 1):
        d = C[k] - C[k - 1]
        g += max(d, 0); l += max(-d, 0)
    rs = g / l if l else 999
    return round(100 - 100 / (1 + rs), 2)


def _ema(C, i, p):
    if i + 1 < p: return None
    k = 2 / (p + 1); e = sum(C[:p]) / p
    for v in C[p:i + 1]: e = v * k + e * (1 - k)
    return round(e, 3)


def synth(data, i15):
    """Sintetiza o dossiê no fecho da barra 15M i15 (causal), com HTF dos bares nativos no mesmo instante."""
    d15 = data["15"]; t = d15["T"][i15]
    mtf = {}
    for tf in TFS:
        dd = data.get(tf)
        if not dd: continue
        j = bisect.bisect_right(dd["T"], t) - 1        # última barra HTF <= t (causal, nativo)
        if j < 40: continue
        stru = cs.structure(dd["H"][:j + 1], dd["L"][:j + 1], dd["C"][:j + 1])
        mtf[tf] = {"trend": stru["trend"], "leg": stru["leg"], "choch": stru["choch"],
                   "swings": stru["swings"], "zones": None, "svp": {"pressure": None}}
    close = d15["C"][i15]
    micro = {"close": close, "bar_time": t, "ema": {"ema21": _ema(d15["C"], i15, 21)},
             "rsi": _rsi(d15["C"], i15), "rsi_ma": _rsi(d15["C"], i15 - 1),
             "dmi": {"plus_di": None, "minus_di": None}, "nas": {}}
    return {"_meta": {"cycle_ts": t, "price_ref": close},
            "source_health": {"mtf": {"status": "fresh"}, "micro_15m": {"status": "fresh"}},
            "axes": {"mtf": mtf, "micro_15m": micro,
                     "macro": {"risk_level": "normal", "news_gate": {"session": "ny", "high_impact_now": False}},
                     "confluence": {"15": {}}}}


def main():
    print("A capturar OHLCV nativo (15M/1H/4H/1D)...")
    data = capture()
    print("TFs capturados:", {tf: len(data[tf]["C"]) for tf in data})
    d15 = data["15"]; C, T = d15["C"], d15["T"]
    N = len(C)
    # janela: apanhar o pico do dia e a queda (últimas ~120 barras 15M = ~30h)
    start = max(45, N - 120)
    peak_i = max(range(start, N), key=lambda k: C[k])
    peak = C[peak_i]
    print(f"pico da janela: {peak} @ barra {peak_i} | close final: {C[-1]} | queda: {round(C[-1]-peak,1)}")
    shorts = []; prev = None
    for i in range(start, N):
        d = synth(data, i)
        cands = e1.detect(d, prev)
        for c in cands:
            atr = e1.atr_of((d["axes"]["mtf"].get(c["tf"], {}) or {}).get("leg") or {})
            c["materiality"] = e1.materiality(c, d, atr)
            if c["direction"] == "SHORT":
                shorts.append((i, C[i], c))
        prev = d
    # SHORTs durante a queda (após o pico)
    post = [(i, px, c) for (i, px, c) in shorts if i >= peak_i]
    passed = [(i, px, c) for (i, px, c) in post if c["materiality"]["pass"]]
    print(f"\n=== SHORT candidatos na queda (após pico @ barra {peak_i}): {len(post)} (materiais: {len(passed)}) ===")
    from collections import Counter
    rc = Counter(c["rule"] for (_i, _px, c) in post)
    print("  por regra:", dict(rc))
    _bc = [(i, px, c) for (i, px, c) in post if c["rule"] == "bos_continuation"]
    if _bc:
        print(f"  bos_continuation ({len(_bc)}):")
        for i, px, c in _bc[:8]:
            print(f"    barra {i} px {px} | {c['tf']} entry {c['entry']} SL {c['sl']} tgt {c['target']} RR {c['rr']} pass {c['materiality']['pass']}")
    for i, px, c in post[:12]:
        print(f"  barra {i} px {px} | {c['rule']} {c['tf']} entry {c['entry']} SL {c['sl']} tgt {c['target']} "
              f"RR {c['rr']} conf {c['materiality']['confluence']} pass {c['materiality']['pass']}")
    ok = len(passed) >= 1
    print(f"\nACEITAÇÃO: {'PASS' if ok else 'FALHA'} — E1 {'gerou' if ok else 'NÃO gerou'} SHORT material durante a queda de hoje")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
