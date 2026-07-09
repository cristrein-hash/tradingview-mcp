#!/usr/bin/env python3
"""PLOT CANÓNICO S2a/S3 (ordem Cris 2026-07-10; anterior apagado por ele). Canon: long_position +
label · width 10 barras (900s) · stopLevel/profitLevel em TICKS (mintick 0.01) · outcome-mode
VERDE #1a8917 winner / VERMELHO #cc0000 loser · label em entry+0.5*risk · sem clear · sem
screenshot. HARD_STOP se chart != XAUUSD/15; exige pause flag."""
import json, csv, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent; REPO = HERE.parents[1]
sys.path.insert(0, str(REPO/"alert-bridge"))
from draw_xau_4h_trades import MCPClient, price_to_ticks_offset
PAUSE = Path("/tmp/claude_recheck.paused")
SYMBOL, TF, BAR_S = "PEPPERSTONE:XAUUSD", "15", 900
GREEN, RED = "#1a8917", "#cc0000"

def main():
    assert PAUSE.exists(), "ERRO: pause flag ausente"
    flags = {int(r["t"]): r for r in csv.DictReader(open(HERE/"results/skip_family_discovery_ledger.csv"))}
    base = list(csv.DictReader(open(REPO/"research/xau_15m_bb_nas_leonardo/reports/xau_15m_live_fireable_candidates.csv")))
    base.sort(key=lambda r: int(r["t"]))
    items = []
    for n, r in enumerate(base, 1):
        t = int(r["t"]); f = flags.get(t)
        if f is None: continue
        s2a, s3 = f["F_S2a"] == "1", f["F_S3"] == "1"
        if not (s2a or s3): continue
        out = int(r["out"]); ent = float(r["ent"]); sl = float(r["sl"])
        risk = ent-sl; tgt = ent+3*risk
        tag = "S2a+S3" if (s2a and s3) else ("S2a" if s2a else "S3")
        items.append({"t": t, "ent": ent, "sl": sl, "tgt": tgt, "ly": ent+0.5*risk,
                      "col": GREEN if out else RED,
                      "label": f"{tag}_{'W' if out else 'L'} #{n}",
                      "s2a": s2a, "s3": s3, "out": out})
    c = MCPClient(); c.start(); drawn = 0; fails = []
    try:
        st = c.call_tool("chart_get_state")
        sym, res = st.get("symbol"), str(st.get("resolution"))
        if sym != SYMBOL or res != TF:
            print(json.dumps({"HARD_STOP": f"chart {sym}/{res} != {SYMBOL}/{TF}"})); return 1
        for it in items:
            r1 = c.call_tool("draw_shape", {"shape": "long_position",
                "point": {"time": it["t"], "price": round(it["ent"], 2)},
                "point2": {"time": it["t"]+10*BAR_S, "price": round(it["tgt"], 2)},
                "overrides": json.dumps({"stopLevel": price_to_ticks_offset(it["ent"], it["sl"]),
                                          "profitLevel": price_to_ticks_offset(it["ent"], it["tgt"])})})
            r2 = c.call_tool("draw_shape", {"shape": "text",
                "point": {"time": it["t"], "price": round(it["ly"], 2)},
                "text": it["label"],
                "overrides": json.dumps({"color": it["col"], "fontsize": 11, "bold": True})})
            if r1.get("success") and r2.get("success"): drawn += 1
            else: fails.append(it["label"])
        summ = {"S2a": {"L": sum(1 for i in items if i["s2a"] and not i["out"]),
                        "W": sum(1 for i in items if i["s2a"] and i["out"])},
                "S3": {"L": sum(1 for i in items if i["s3"] and not i["out"]),
                       "W": sum(1 for i in items if i["s3"] and i["out"])},
                "drawn": drawn, "requested": len(items), "fails": fails}
        (HERE/"results/plot_s2a_s3_canonical_result.json").write_text(json.dumps(summ, indent=2))
        print(json.dumps(summ))
    finally:
        try: c.stop()
        except Exception: pass
    return 0

if __name__ == "__main__":
    sys.exit(main())
