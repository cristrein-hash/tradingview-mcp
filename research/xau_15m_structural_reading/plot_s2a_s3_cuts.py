#!/usr/bin/env python3
"""PLOT S2a/S3 no chart XAUUSD/15 (ordem Cris 2026-07-10). Retângulos proporcionais (entry→SL,
largura = barras até resolução) + label simples S2a_L/S2a_W/S3_L/S3_W (+#id = ordem temporal na
base). Overlap S2a∩S3 = 1 caixa com label combinado. Losers vermelho, winners verde. Sem clear,
sem screenshot, sem interpretação. Fontes: skip_family_discovery_ledger.csv (flags) + base CSV
(ent/sl/bars). HARD_STOP se chart != XAUUSD/15; exige pause flag."""
import json, csv, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent; REPO = HERE.parents[1]
sys.path.insert(0, str(REPO/"alert-bridge"))
from draw_xau_4h_trades import MCPClient
PAUSE = Path("/tmp/claude_recheck.paused")
SYMBOL, TF = "PEPPERSTONE:XAUUSD", "15"
RED, GREEN = "#cc0000", "#1a8917"

def main():
    assert PAUSE.exists(), "ERRO: pause flag ausente"
    flags = {int(r["t"]): r for r in csv.DictReader(open(HERE/"results/skip_family_discovery_ledger.csv"))}
    base = list(csv.DictReader(open(REPO/"research/xau_15m_bb_nas_leonardo/reports/xau_15m_live_fireable_candidates.csv")))
    base.sort(key=lambda r: int(r["t"]))
    items = []
    for n, r in enumerate(base, 1):
        t = int(r["t"])
        f = flags.get(t)
        if f is None: continue
        s2a, s3 = f["F_S2a"] == "1", f["F_S3"] == "1"
        if not (s2a or s3): continue
        out = int(r["out"])
        tag = "S2a+S3" if (s2a and s3) else ("S2a" if s2a else "S3")
        lab = f"{tag}_{'W' if out else 'L'} #{n}"
        bars = max(int(r["bars"]), 4)
        items.append({"t1": t, "t2": t+bars*900, "lo": float(r["sl"]), "hi": float(r["ent"]),
                      "col": GREEN if out else RED, "label": lab, "s2a": s2a, "s3": s3, "out": out})
    exp = {"S2a_total": sum(1 for i in items if i["s2a"]),
           "S2a_L": sum(1 for i in items if i["s2a"] and not i["out"]),
           "S2a_W": sum(1 for i in items if i["s2a"] and i["out"]),
           "S3_total": sum(1 for i in items if i["s3"]),
           "S3_L": sum(1 for i in items if i["s3"] and not i["out"]),
           "S3_W": sum(1 for i in items if i["s3"] and i["out"]),
           "boxes": len(items)}
    print(json.dumps(exp))
    c = MCPClient(); c.start(); drawn = 0; fails = []
    try:
        st = c.call_tool("chart_get_state")
        sym, res = st.get("symbol"), str(st.get("resolution"))
        if sym != SYMBOL or res != TF:
            print(json.dumps({"HARD_STOP": f"chart {sym}/{res} != {SYMBOL}/{TF}"})); return 1
        for it in items:
            r1 = c.call_tool("draw_shape", {"shape": "rectangle",
                "point": {"time": it["t1"], "price": round(it["lo"], 2)},
                "point2": {"time": it["t2"], "price": round(it["hi"], 2)},
                "overrides": json.dumps({"color": it["col"], "backgroundColor": it["col"],
                                          "transparency": 80, "linewidth": 1})})
            r2 = c.call_tool("draw_shape", {"shape": "text",
                "point": {"time": it["t1"], "price": round(it["hi"]*1.001, 2)},
                "text": it["label"],
                "overrides": json.dumps({"color": it["col"], "fontsize": 11, "bold": True})})
            if r1.get("success") and r2.get("success"): drawn += 1
            else: fails.append(it["label"])
        out = {"summary": exp, "drawn": drawn, "requested": len(items), "fails": fails}
        (HERE/"results/plot_s2a_s3_result.json").write_text(json.dumps(out, indent=2))
        print(json.dumps({"drawn": drawn, "requested": len(items), "fails": fails}))
    finally:
        try: c.stop()
        except Exception: pass
    return 0

if __name__ == "__main__":
    sys.exit(main())
