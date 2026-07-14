#!/usr/bin/env python3
"""PLOT dos 61 fundos como OPERAÇÕES LONG no 1H XAUUSD (ordem Cris 2026-07-14; re-plot v2).
Correção: tempo de cada fundo ALINHADO à barra 1H (floor à hora) — os 14 fundos com timestamp 15M
fracionário (círculo-only) rendiam torto no 1H. Remove SÓ os meus (long_position + labels '#n cls');
preserva todos os outros desenhos. long_position canónico + label da classe. Pausa. Sem screenshot.
Stop/target NOMINAIS (mecânica de entry não desenhada) — vale a localização+classe."""
import json, re, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
REPO = Path("/Users/cristrein/tradingview-mcp")
sys.path.insert(0, str(REPO / "alert-bridge"))
from draw_xau_4h_trades import MCPClient, price_to_ticks_offset
PAUSE = Path("/tmp/claude_recheck.paused")
GT = json.load(open(HERE / "results" / "REGIME_GT_FUNDOS_UNIFIED_20260714.json"))
BAR_1H = 3600; BOX_BARS = 20; STOP_PCT = 0.005
LABEL_RE = re.compile(r"^#\d+\s+(A1|A2|B|Cp|Cg|Cs)$")
CLS = {
    "A1_pullback_fundo": ("A1", "#2e7d32"), "A2_pullback_raso": ("A2", "#66bb6a"),
    "B_range": ("B", "#ef6c00"), "C_PANIC_aguda": ("Cp", "#c62828"),
    "C_GRIND_profundo": ("Cg", "#6a1b9a"), "C_shallow_bounce": ("Cs", "#757575"),
}

def main():
    assert PAUSE.exists(), "pause flag ausente"
    c = MCPClient(); c.start()
    out = {"removed_mine": 0, "kept": 0, "drawn": 0, "labels": 0, "fails": 0}
    try:
        st = c.call_tool("chart_get_state")
        if st.get("symbol") != "PEPPERSTONE:XAUUSD":
            print(json.dumps({"HARD_STOP_symbol": st.get("symbol")})); return 1
        if str(st.get("resolution")) not in ("60", "1H"):
            c.call_tool("chart_set_timeframe", {"timeframe": "60"})
        # remover SÓ os meus: long_position + text com padrão '#n classe'
        for it in c.call_tool("draw_list").get("shapes", []):
            nm = it.get("name")
            if nm == "long_position":
                if c.call_tool("draw_remove_one", {"entity_id": it["id"]}).get("success"): out["removed_mine"] += 1
            elif nm == "text":
                p = c.call_tool("draw_get_properties", {"entity_id": it["id"]})
                txt = (p.get("properties") or {}).get("text") or p.get("text") or ""
                if LABEL_RE.match(txt.strip()):
                    if c.call_tool("draw_remove_one", {"entity_id": it["id"]}).get("success"): out["removed_mine"] += 1
                else: out["kept"] += 1
            else: out["kept"] += 1
        # re-plotar alinhado a 1H
        for k, f in enumerate(sorted(GT["fundos"], key=lambda x: x["t"]), 1):
            t = int(f["t"]) - (int(f["t"]) % BAR_1H)     # floor à barra 1H
            entry = float(f["price"]); tag, col = CLS.get(f.get("subclasse", "?"), ("?", "#455a64"))
            stop = entry * (1 - STOP_PCT); R = entry - stop; target = entry + 3 * R
            r1 = c.call_tool("draw_shape", {
                "shape": "long_position",
                "point": {"time": t, "price": round(entry, 2)},
                "point2": {"time": t + BOX_BARS * BAR_1H, "price": round(target, 2)},
                "overrides": json.dumps({"stopLevel": price_to_ticks_offset(entry, stop),
                                          "profitLevel": price_to_ticks_offset(entry, target)})})
            if r1.get("success"): out["drawn"] += 1
            else: out["fails"] += 1
            r2 = c.call_tool("draw_shape", {
                "shape": "text",
                "point": {"time": t, "price": round(entry + 0.5 * R, 2)},
                "text": f"#{k} {tag}",
                "overrides": json.dumps({"color": col, "bold": True, "fontsize": 11})})
            if r2.get("success"): out["labels"] += 1
        c.call_tool("chart_scroll_to_date", {"date": "2025-09-01"})
        print(json.dumps(out))
    finally:
        try: c.stop()
        except Exception: pass
    return 0

if __name__ == "__main__":
    sys.exit(main())
