#!/usr/bin/env python3
"""Plota no 15M as operações que TERIAM SIDO SINALIZADAS hoje = candidatos que (1) passam materialidade E1,
(2) sobrevivem ao anti-spam E1 (cooldown/dedup = sinais DISTINTOS), (3) sobrevivem aos vetos E2 Sub-fase A.
Long/short_position canónico + label (regra + confluência). Pausa os daemons antes de tocar o chart.
Uso: python3 plot_today_signals.py [--dry]   (--dry = só imprime, não plota)"""
import os, sys, json, time
from pathlib import Path
BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))
import e1_replay, e1_detector as e1, e2_quality as e2
from draw_xau_4h_trades import MCPClient, price_to_ticks_offset

TF15 = "8DD9A79D11F923AFDC772375FD18DD88"   # descoberto dinamicamente abaixo se mudar
BOX_BARS = 20; BAR_S = 900   # canon §2: largura 20 barras


def survivors():
    data = e1_replay.capture()
    d15 = data["15"]; N = len(d15["C"]); start = max(45, N - 120)
    T = d15["T"]
    state = {"cooldown": {}, "dedup": {}}; prev = None; out = []
    for i in range(start, N):
        dsr = e1_replay.synth(data, i)
        t = dsr["_meta"]["cycle_ts"]
        for c in e1.detect(dsr, prev):
            atr = e1.atr_of((dsr["axes"]["mtf"].get(c["tf"], {}) or {}).get("leg") or {})
            c["materiality"] = e1.materiality(c, dsr, atr); c["cycle_ts"] = t; c["bar_time"] = t
            if not e2.is_material(c):
                continue
            if e1.anti_spam(c, state, t):          # anti-spam E1 (sinais distintos)
                continue
            grade, vs, hard, soft = e2.evaluate_vetos(c, dsr, 0)
            if grade != "survivor":
                continue
            state["cooldown"][f"{c['rule']}:{c['tf']}:{c['direction']}"] = t
            state["dedup"][e1.cand_hash(c)] = t
            out.append(c)
        prev = dsr
    return data, out


def find_tf15():
    import urllib.request
    try:
        with urllib.request.urlopen("http://localhost:9222/json/list", timeout=8) as r:
            for tt in json.loads(r.read()):
                if tt.get("type") == "page" and "tradingview.com/chart" in (tt.get("url") or "").lower():
                    os.environ["TVMCP_TARGET_CHART_ID"] = tt["id"]
                    c = MCPClient(); c.start()
                    res = str((c.call_tool("chart_get_state") or {}).get("resolution")); c.stop()
                    if res == "15":
                        return tt["id"]
    except Exception:
        pass
    return TF15


def main():
    dry = "--dry" in sys.argv
    data, surv = survivors()
    print(f"=== {len(surv)} sinais distintos (materiais+anti-spam+vetos E2) na queda de hoje ===")
    for c in surv:
        print(f"  {c['direction']} {c['rule']}/{c['tf']} @{c['bar_time']} | entry {c['entry']} SL {c['sl']} "
              f"tgt {c['target']} RR {c['rr']} conf {c['materiality']['confluence']}")
    if dry or not surv:
        return
    tid = find_tf15()
    os.environ["TVMCP_TARGET_CHART_ID"] = tid
    c = MCPClient(); c.start()
    drawn = 0
    try:
        st = c.call_tool("chart_get_state") or {}
        print("plotando na tab", str(st.get("resolution")), "...")
        for k, s in enumerate(surv):
            shape = "long_position" if s["direction"] == "LONG" else "short_position"
            t0 = int(s["bar_time"])
            # canon §0: overrides em TICKS-offset (price_to_ticks_offset = abs); §2: point2 no target, 20 barras
            r = c.call_tool("draw_shape", {
                "shape": shape, "point": {"time": t0, "price": s["entry"]},
                "point2": {"time": t0 + BOX_BARS * BAR_S, "price": s["target"]},
                "overrides": json.dumps({"stopLevel": price_to_ticks_offset(s["entry"], s["sl"]),
                                         "profitLevel": price_to_ticks_offset(s["entry"], s["target"])})})
            if r.get("success"):
                drawn += 1
                # canon §3: label = #número cronológico; candidatos SEM outcome = cor neutra azul #1565c0; 0.5R do entry
                Rd = abs(s["entry"] - s["sl"])
                label_y = s["entry"] + (0.5 * Rd if s["direction"] == "LONG" else -0.5 * Rd)
                c.call_tool("draw_shape", {"shape": "text",
                            "point": {"time": t0, "price": label_y}, "text": f"#{k + 1}",
                            "overrides": json.dumps({"color": "#1565c0", "bold": True, "fontsize": 12})})
            else:
                print(f"  falhou {s['direction']} @{t0}: {r}")
        print(f"desenhados {drawn}/{len(surv)} sinais no 15M")
    finally:
        c.stop()


if __name__ == "__main__":
    main()
