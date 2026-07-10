#!/usr/bin/env python3
"""PLOT CANÓNICO — resultado A2 vs 42 VELA DE FUNDO (ordem Cris 2026-07-10; desenhos anteriores
removidos por ele). Cada marca GT plotada como long_position sintética (entry=preço da marca,
SL=entry−1·ATR15, alvo=+3R) SÓ para visualização do verdict A2. Labels: A2_COVERED (verde) ·
A2_NEAR (laranja) · A2_LATE (cinza) · A2_MISS (vermelho), com #n temporal e idade da região quando
coberta. Sem clear, sem screenshot, sem interpretação. HARD_STOP se chart != XAUUSD/15."""
import json, sys, bisect
from pathlib import Path
HERE = Path(__file__).resolve().parent; REPO = HERE.parents[1]
sys.path.insert(0, str(REPO/"alert-bridge"))
sys.path.insert(0, str(REPO/"research/xau_15m_structural_leg_engine"))
from draw_xau_4h_trades import MCPClient, price_to_ticks_offset
from f1_structural_leg_machine import Data
PAUSE = Path("/tmp/claude_recheck.paused")
SYMBOL, TF, BAR_S = "PEPPERSTONE:XAUUSD", "15", 900
COL = {"COVERED": "#1a8917", "NEAR": "#e8a33d", "LATE": "#787b86", "MISS": "#cc0000"}

def klass(v):
    if v.startswith("COVERED"): return "COVERED"
    if v == "NEAR_MISS": return "NEAR"
    if v == "LATE_ONLY": return "LATE"
    return "MISS"

def main():
    assert PAUSE.exists(), "ERRO: pause flag ausente"
    gate = json.load(open(REPO/"research/xau_15m_structural_leg_engine/results/a2_anchor_gt_gate_result.json"))
    rows = gate["fundos_42"]["rows"]
    cat = json.load(open(REPO/"research/xau_15m_bb_nas_leonardo/results/catalog_manual_tags_20260707.json"))
    tmap = {x["date"]: x["t"] for x in cat["notes"]["FUNDO"]}
    D = Data()
    items = []
    rows_sorted = sorted(rows, key=lambda r: tmap[r["date"]])
    for n, r in enumerate(rows_sorted, 1):
        t = tmap[r["date"]]; px = float(r["px"])
        i = bisect.bisect_right(D.TS, t)-1
        a = D.ATR[i] or 5.0
        sl = px-1.0*a; tgt = px+3.0*a
        k = klass(r["verdict"])
        lab = f"A2_{k} #{n}"
        if k == "COVERED" and r.get("bottom_age_h") is not None:
            lab += f" ({r['bottom_age_h']}h)"
        items.append({"t": t, "ent": px, "sl": sl, "tgt": tgt, "ly": px+0.5*a,
                      "col": COL[k], "label": lab, "k": k})
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
        summ = {k: sum(1 for i2 in items if i2["k"] == k) for k in COL}
        out = {"counts": summ, "drawn": drawn, "requested": len(items), "fails": fails}
        (HERE/"results/plot_a2_gt42_result.json").write_text(json.dumps(out, indent=2))
        print(json.dumps(out))
    finally:
        try: c.stop()
        except Exception: pass
    return 0

if __name__ == "__main__":
    sys.exit(main())
