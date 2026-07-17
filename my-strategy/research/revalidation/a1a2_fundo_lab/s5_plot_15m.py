#!/usr/bin/env python3
"""A1A2_FUNDO_LAB · plot canónico dos 7 trades do detetor (região+reclaim+depth) no 15M.
long_position (entry/SL/target em TICKS) + label #n. Pina a tab 15M (TVMCP_TARGET_CHART_ID).
Ajusta a visible-range para a janela dos trades, plota, verifica por draw_list, e RESTAURA a
visible-range a realtime (a tab 15M alimenta o E0/E1/E2 — não deixar em Nov/2025). NÃO limpa desenhos
existentes. Pausa dos daemons = feita pelo wrapper. py3.9 stdlib.
"""
import os, sys, json, urllib.request, bisect, datetime as dt
from pathlib import Path
HERE = Path(__file__).resolve().parent
REV = HERE.parent
sys.path.insert(0, str(REV)); sys.path.insert(0, str(HERE))
sys.path.insert(0, "/Users/cristrein/tradingview-mcp/alert-bridge")
from a1_causal_entry import load_series, _is_swinglow, M_FRAC, causal_entry
from s2b_seq_features import feats, blocks, BUCKET
from s3b_zigzag_region import zzleg_region
from draw_xau_4h_trades import MCPClient, price_to_ticks_offset
import statistics as st, csv

WIN_START = int(dt.datetime(2025, 9, 1, tzinfo=dt.timezone.utc).timestamp())
BOX_BARS, BAR_S = 20, 900
CDP_LIST = "http://localhost:9222/json/list"


def region_trades():
    S = load_series(blocks()); T, L, N = S["T"], S["L"], S["N"]
    tab = {}
    with open(HERE / "results" / "a1a2_bucket_table.csv") as fh:
        for r in csv.DictReader(fh):
            tab[int(r["t"])] = (r["kind"], r["family_label"])
    gr = []; gd = []
    for p in range(M_FRAC, N - M_FRAC):
        if _is_swinglow(L, p, M_FRAC) and tab.get(T[p], ("", ""))[0] in ("GT_A1", "GT_A2"):
            fv = feats(S, {}, p, "fix48")
            if fv: gr.append(fv["reclaim"]); gd.append(fv["depth"])
    mrc, mdp = st.median(gr), st.median(gd)
    out = []
    for p in range(M_FRAC, N - M_FRAC):
        if T[p] < WIN_START or not _is_swinglow(L, p, M_FRAC):
            continue
        info = tab.get(T[p])
        if not info or info[1] not in BUCKET:
            continue
        fv = feats(S, {}, p, "fix48")
        if not fv or fv["reclaim"] < mrc or fv["depth"] < mdp:
            continue
        reg, _ = zzleg_region(int(T[p]), L[p])
        if reg not in ("BOTTOM", "MIDDLE"):
            continue
        e = causal_entry(S, p + M_FRAC, "MB3")   # DA-fix: entry só a partir da confirmação p+3
        if not e:
            continue
        out.append({"etime": int(T[e["ei"]]), "entry": e["ent"], "sl": e["sl"], "tgt": e["tgt"],
                    "kind": info[0], "out": e["o"]})
    return out


def find_15m_tab():
    with urllib.request.urlopen(CDP_LIST, timeout=8) as r:
        targets = [t["id"] for t in json.loads(r.read())
                   if t.get("type") == "page" and "tradingview.com/chart" in (t.get("url") or "").lower()]
    for tid in targets:
        os.environ["TVMCP_TARGET_CHART_ID"] = tid
        c = MCPClient(); c.start()
        try:
            st_ = c.call_tool("chart_get_state") or {}
            if str(st_.get("resolution")) == "15":
                return tid
        finally:
            c.stop()
    return None


def main():
    trades = region_trades()
    print(f"{len(trades)} trades do detetor-região para plotar")
    tid = find_15m_tab()
    if not tid:
        print("SEM tab 15M — aborta"); return
    os.environ["TVMCP_TARGET_CHART_ID"] = tid
    c = MCPClient(); c.start()
    try:
        st_ = c.call_tool("chart_get_state") or {}
        print("tab 15M:", st_.get("symbol"), st_.get("resolution"))
        tmin = min(t["etime"] for t in trades); tmax = max(t["etime"] for t in trades)
        # visible-range cobrindo a janela (margem 2 dias)
        c.call_tool("chart_set_visible_range", {"from": tmin - 2 * 86400, "to": tmax + 3 * 86400})
        drawn = 0
        for k, s in enumerate(trades, 1):
            r = c.call_tool("draw_shape", {
                "shape": "long_position", "point": {"time": s["etime"], "price": s["entry"]},
                "point2": {"time": s["etime"] + BOX_BARS * BAR_S, "price": s["tgt"]},
                "overrides": json.dumps({"stopLevel": price_to_ticks_offset(s["entry"], s["sl"]),
                                         "profitLevel": price_to_ticks_offset(s["entry"], s["tgt"])})})
            if r.get("success"):
                drawn += 1
                Rd = abs(s["entry"] - s["sl"])
                c.call_tool("draw_shape", {"shape": "text",
                            "point": {"time": s["etime"], "price": s["entry"] + 0.5 * Rd},
                            "text": f"#{k} {s['out']}", "overrides": json.dumps({"color": "#1565c0", "bold": True, "fontsize": 12})})
            else:
                print(f"  falhou #{k} @{s['etime']}: {r}")
        print(f"desenhados {drawn}/{len(trades)}")
        dl = c.call_tool("draw_list") or {}
        n_draw = len(dl.get("drawings", dl.get("shapes", [])))
        print(f"draw_list: {n_draw} desenhos no chart")
        # RESTAURAR realtime (a tab alimenta o E0/E1/E2)
        import time as _t
        now = int(_t.time())
        c.call_tool("chart_set_visible_range", {"from": now - 200 * BAR_S, "to": now + 20 * BAR_S})
        st2 = c.call_tool("chart_get_state") or {}
        print("chart restaurado (visible-range -> realtime):", str(st2.get("resolution")))
    finally:
        c.stop()


if __name__ == "__main__":
    main()
