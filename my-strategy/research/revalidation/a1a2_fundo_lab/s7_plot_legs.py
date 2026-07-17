#!/usr/bin/env python3
"""Plota TODAS as legs do leg_v3 como RETÂNGULOS no chart 15M (tab pinada). Apaga desenhos antes.
Cada leg = segmento de barras 4H consecutivas com o mesmo rótulo; retângulo = [t_ini,t_fim]×[minLow,maxHigh].
Cor por tipo (UP verde · DOWN vermelho · PULLBACK/CORRECAO laranja · ACUMULACAO cinza · outro azul).
--dry = só conta/segmenta (não desenha). py3.9 stdlib.
"""
import os, sys, json, urllib.request, datetime as dt
from pathlib import Path
HERE = Path(__file__).resolve().parent
REV = HERE.parent
sys.path.insert(0, str(REV))
sys.path.insert(0, "/Users/cristrein/tradingview-mcp/alert-bridge")
import leg_v3 as LV
import gt_pivot_structural_harness as R1
from draw_xau_4h_trades import MCPClient

TS4, H4, L4 = R1.TS4, R1.H4, R1.L4
BAR4 = 14400
CDP_LIST = "http://localhost:9222/json/list"
T2IDX = {t: i for i, t in enumerate(TS4)}


def color(leg):
    L = str(leg or "").upper()
    if "UP" in L: return "#26a69a"           # verde
    if "DOWN" in L: return "#ef5350"          # vermelho
    if "PULL" in L or "CORRE" in L: return "#ff9800"   # laranja
    if "ACUM" in L: return "#9e9e9e"          # cinza
    if "WARM" in L: return "#42a5f5"          # azul
    return "#7e57c2"                          # roxo (outro)


def segments():
    v3 = LV.build_leg_v3()
    segs = []
    cur = None
    for r in v3:
        t = r["t"]; leg = r.get("leg", "?")
        i = T2IDX.get(t)
        if i is None:
            continue
        if cur and cur["leg"] == leg:
            cur["i1"] = i
        else:
            if cur:
                segs.append(cur)
            cur = {"leg": leg, "i0": i, "i1": i}
    if cur:
        segs.append(cur)
    for s in segs:
        seg = range(s["i0"], s["i1"] + 1)
        s["t0"] = TS4[s["i0"]]; s["t1"] = TS4[s["i1"]] + BAR4
        s["hi"] = max(H4[j] for j in seg); s["lo"] = min(L4[j] for j in seg)
    return segs


def find_15m():
    with urllib.request.urlopen(CDP_LIST, timeout=8) as r:
        tgs = [t["id"] for t in json.loads(r.read())
               if t.get("type") == "page" and "tradingview.com/chart" in (t.get("url") or "").lower()]
    for tid in tgs:
        os.environ["TVMCP_TARGET_CHART_ID"] = tid
        c = MCPClient(); c.start()
        try:
            if str((c.call_tool("chart_get_state") or {}).get("resolution")) == "15":
                return tid
        finally:
            c.stop()
    return None


WIN_START = int(dt.datetime(2025, 9, 1, tzinfo=dt.timezone.utc).timestamp())


def main():
    dry = "--dry" in sys.argv
    segs = [s for s in segments() if s["t1"] >= WIN_START]   # só Set/2025+ (limite 15M)
    from collections import Counter
    print(f"legs v3: {len(segs)} segmentos · por tipo: {dict(Counter(s['leg'] for s in segs))}")
    d = lambda t: dt.datetime.utcfromtimestamp(int(t)).strftime("%Y-%m-%d")
    print(f"span: {d(segs[0]['t0'])} -> {d(segs[-1]['t1'])}")
    if dry:
        return
    tid = find_15m()
    if not tid:
        print("SEM tab 15M"); return
    os.environ["TVMCP_TARGET_CHART_ID"] = tid
    c = MCPClient(); c.start()
    try:
        print("draw_clear:", (c.call_tool("draw_clear") or {}).get("success"))
        drawn = 0
        for s in segs:
            r = c.call_tool("draw_shape", {"shape": "rectangle",
                            "point": {"time": s["t0"], "price": s["hi"]},
                            "point2": {"time": s["t1"], "price": s["lo"]},
                            "overrides": json.dumps({"color": color(s["leg"]), "backgroundColor": color(s["leg"]),
                                                     "fillBackground": True, "transparency": 80, "linewidth": 1})})
            if isinstance(r, dict) and r.get("success"):
                drawn += 1
        print(f"desenhados {drawn}/{len(segs)} retângulos")
    finally:
        c.stop()


if __name__ == "__main__":
    main()
