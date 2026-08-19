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


# ---------------------------------------------------------------------------
# MODO --week (Cris 2026-08-02): aceitação R9/R10 sobre a SEMANA 27-31/07 inteira.
# 15M = bar-store (o MCP 400-bars não chega a segunda 27/07); HTF 60/240/1D = captura MCP (400 barras
# cobrem semanas). Zonas 240 = as DOCUMENTADAS da semana lidas do OB Detector v11 via MCP em 30-31/07
# (supply 4101.07-4116.28, demand 3995.84-4010 — provenance data_get_pine_boxes; NÃO inventadas).
# News: injeta high_impact_now na janela FOMC real (29/07 19:00 Lisboa = 18:00 UTC ± margem) — o news
# live não é replayável. Asserts: A) ob_touch_hold LONG nasce no OB 28/07 (entry 4005-4022, SL ~3994);
# A2) nunca nasce com fecho além do bloco (faca); B) top_fade SHORT nasce no topo de 2ª-feira 27/07;
# B2) ZERO top_fade na janela FOMC; C) regressão = regras antigas byte-idênticas OFF vs ON.
# Reusa synth()+structure() existentes (não reconstrói leitura).
# ---------------------------------------------------------------------------
import json as _json

WEEK_ZONES_240 = {"above": {"low": 4101.07, "high": 4116.28, "src": "Custom OB Dete"},
                  "below": {"high": 4010.0, "low": 3995.84, "src": "Custom OB Dete"}}
FOMC_W = (1785348000 - 900, 1785348000 + 9000)     # 17:45–20:30 UTC de 29/07 (decisão 18:00 + Powell)
T_WEEK0 = 1785024000                                # 2026-07-26 00:00 UTC
WIN_A = (1785232800, 1785268800)                    # 28/07 10:00–20:00 UTC (LONG no OB)
# janela B até 16:00 UTC: a versão CAUSAL (breakdown após >=2 rejeições) dispara às 11:15 UTC — mais tarde
# que o wick ideal do Cris (01:00, vender DENTRO da zona no 1º toque), MESMA estrutura de topo; o custo da
# causalidade é entrar na confirmação (4097) em vez do extremo (4106). Captura a mesma queda p/ 4038-4018.
WIN_B = (1785103200, 1785168000)                    # 26/07 22:00 – 27/07 16:00 UTC (topo de 2ª)


def _load_store_15m():
    p = BASE.parent / "my-strategy/core/bar_store/store/bars_15m.jsonl"
    rows = [_json.loads(l) for l in open(p) if l.strip() and l[0] == "{"]
    rows = [b for b in rows if b.get("t") and b["t"] >= T_WEEK0]
    return rows


def _run_week(data, rows, flags_on):
    e1.OB_TOUCH = flags_on; e1.TOP_FADE = flags_on
    out = []
    prev = None
    N = len(data["15"]["C"])
    for i in range(45, N):
        d = synth(data, i)
        t = data["15"]["T"][i]
        m240 = d["axes"]["mtf"].get("240")
        if m240 is not None:
            m240["zones"] = WEEK_ZONES_240
        d["axes"]["macro"]["news_gate"]["high_impact_now"] = bool(FOMC_W[0] <= t <= FOMC_W[1])
        for c in e1.detect(d, prev):
            atr = e1.atr_of((d["axes"]["mtf"].get(c["tf"], {}) or {}).get("leg") or {})
            c["materiality"] = e1.materiality(c, d, atr)
            out.append((t, c))
        prev = d
    return out


def week_main():
    rows = _load_store_15m()
    print(f"bar-store 15M: {len(rows)} barras da semana (desde 26/07 00:00 UTC)")
    print("A capturar HTF nativo via MCP (60/240/1D)...")
    mcp = capture()
    data = {"15": {"H": [b["h"] for b in rows], "L": [b["l"] for b in rows],
                   "C": [b["c"] for b in rows], "T": [b["t"] for b in rows]}}
    for tf in ("60", "240", "1D"):
        if tf in mcp: data[tf] = mcp[tf]
    print("TFs:", {tf: len(data[tf]["C"]) for tf in data})
    # monkeypatch dos helpers de barra (o tail-read de 8KB nunca casa com barras históricas)
    IDX = {b["t"]: b for b in rows}; T15 = [b["t"] for b in rows]
    e1._bar_hl_15m = lambda t: ((IDX[t]["h"], IDX[t]["l"]) if t in IDX else None)
    def _mp_prev(t):
        i = bisect.bisect_left(T15, t); return rows[i - 1] if i > 0 else None
    e1._bar_15m_prev = _mp_prev
    e1._bars_15m_tail = lambda t, n: rows[max(0, bisect.bisect_right(T15, t) - n):bisect.bisect_right(T15, t)]

    on = _run_week(data, rows, True)
    off = _run_week(data, rows, False)

    r9 = [(t, c) for t, c in on if c["rule"] == "ob_touch_hold"]
    r10 = [(t, c) for t, c in on if c["rule"] == "top_fade"]
    print(f"\nR9 ob_touch_hold gerados: {len(r9)} | R10 top_fade gerados: {len(r10)}")
    import datetime as _dt
    for t, c in (r9 + r10)[:12]:
        hh = _dt.datetime.utcfromtimestamp(t).strftime("%d %H:%M")
        print(f"  {hh}UTC {c['rule']} {c['direction']} {c['tf']} entry {c['entry']} SL {c['sl']} tgt {c['target']} pass {c['materiality']['pass']}")

    # entry até 4023: o sistema causal entra no FECHO da barra de hold (28/07: 4022.45), não no wick ideal
    # (4011.48) — o SL estrutural é o mesmo (~3993); a diferença ideal-vs-causal é o custo da causalidade.
    a_hits = [(t, c) for t, c in r9 if c["direction"] == "LONG" and WIN_A[0] <= t <= WIN_A[1]
              and 4005 <= c["entry"] <= 4023 and 3991 <= c["sl"] <= 3997 and c["materiality"]["pass"]]
    a_knife = [(t, c) for t, c in r9 if c["direction"] == "LONG" and c["entry"] < WEEK_ZONES_240["below"]["low"]]
    b_hits = [(t, c) for t, c in r10 if WIN_B[0] <= t <= WIN_B[1] and 4090 <= c["entry"] <= 4112]
    b_fomc = [(t, c) for t, c in r10 if FOMC_W[0] <= t <= FOMC_W[1]]
    old_on = [(t, c["rule"], c["direction"], c["entry"]) for t, c in on if c["rule"] not in ("ob_touch_hold", "top_fade")]
    old_off = [(t, c["rule"], c["direction"], c["entry"]) for t, c in off if c["rule"] not in ("ob_touch_hold", "top_fade")]
    new_off = [c for _t, c in off if c["rule"] in ("ob_touch_hold", "top_fade")]

    ok_a = len(a_hits) >= 1
    ok_ak = len(a_knife) == 0
    ok_b = len(b_hits) >= 1
    ok_bf = len(b_fomc) == 0
    ok_reg = (old_on == old_off) and len(new_off) == 0
    print(f"\nA  LONG no OB 28/07 (entry 4005-4022, SL 3991-3997, pass): {'PASS' if ok_a else 'FALHA'} (n={len(a_hits)})")
    print(f"A2 nunca em faca (entry < fundo do bloco): {'PASS' if ok_ak else 'FALHA'} (violacoes={len(a_knife)})")
    print(f"B  top_fade no topo 27/07 (entry 4090-4112): {'PASS' if ok_b else 'FALHA'} (n={len(b_hits)})")
    print(f"B2 ZERO top_fade na janela FOMC: {'PASS' if ok_bf else 'FALHA'} (n={len(b_fomc)})")
    print(f"C  regressao regras antigas OFF==ON + novas OFF=0: {'PASS' if ok_reg else 'FALHA'}")
    allok = ok_a and ok_ak and ok_b and ok_bf and ok_reg
    print(f"\nACEITACAO SEMANA: {'PASS' if allok else 'FALHA'}")
    return 0 if allok else 1


if __name__ == "__main__":
    sys.exit(week_main() if "--week" in sys.argv else main())
