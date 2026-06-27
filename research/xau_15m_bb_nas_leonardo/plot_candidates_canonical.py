#!/usr/bin/env python3
"""Plotagem CANÔNICA dos candidatos Stage-B (docs/CANONICAL_TRADE_PLOTTING.md — fonte única).
2 shapes por candidato: long_position (LONG) / short_position (SHORT) + label texto #N.
- entry = entry_close; SL ESTRUTURAL = outro lado da zona Custom OB ∓ 0.1×ATR; TARGET = ±3R (entry±3×risk).
- stopLevel/profitLevel em TICKS (mintick 0.01); point2.time = entry + 20 barras (15M=900s); point2.price = target.
- label #N (índice cronológico), cor VERDE LONG (#1a8917) / VERMELHO SHORT (#cc0000) a pedido de Cris; 0.5R do entry.
- ATR derivado do CSV: atr = (zone_high−zone_low)/zone_width_atr (RAW via primitives). Hard-stop em validação.
- NÃO draw_clear (Cris limpa manual), NÃO screenshot, deixa em PEPPERSTONE:XAUUSD/15. Verified 2026-06-26."""
import sys, csv, json, math
from pathlib import Path
REPO = Path("/Users/cristrein/tradingview-mcp")
sys.path.insert(0, str(REPO / "alert-bridge"))
from draw_xau_4h_trades import MCPClient, price_to_ticks_offset
HERE = Path(__file__).parent
PAUSE = Path("/tmp/claude_recheck.paused")
SYMBOL, TF, BAR_S, WIDTH_BARS = "PEPPERSTONE:XAUUSD", "15", 900, 10  # 10 barras (Cris 2026-06-26: 20 é demais p/ 15M)
GREEN, RED = "#1a8917", "#cc0000"

def build(rows):
    trades = []
    for i, r in enumerate(rows, start=1):
        d = r["dir"]; entry = float(r["entry_close"]); zlo = float(r["zone_low"]); zhi = float(r["zone_high"])
        zwa = float(r["zone_width_atr"]); t = int(r["entry_t"])
        atr = (zhi - zlo) / zwa if zwa > 0 else None
        if not atr or atr <= 0: continue
        if d == "LONG":
            stop = zlo - 0.1 * atr; risk = entry - stop
            if risk <= 0: continue
            target = entry + 3 * risk; shape = "long_position"; ok = stop < entry < target
            label_y = entry + 0.5 * risk
        else:
            stop = zhi + 0.1 * atr; risk = stop - entry
            if risk <= 0: continue
            target = entry - 3 * risk; shape = "short_position"; ok = target < entry < stop
            label_y = entry - 0.5 * risk
        if not ok: continue
        trades.append({"n": i, "dir": d, "shape": shape, "t": t, "exit_t": t + WIDTH_BARS * BAR_S,
                        "entry": round(entry, 2), "stop": round(stop, 2), "target": round(target, 2),
                        "label_y": round(label_y, 2)})
    return trades

def main():
    if not PAUSE.exists(): print("ERRO: pause flag ausente"); return 1
    src = "candidates_annotated.csv" if "--with-macro" in sys.argv else "candidates_stageB.csv"
    rows = list(csv.DictReader(open(HERE / src))); rows.sort(key=lambda r: int(r["entry_t"]))
    trades = build(rows)  # numeração #N cronológica GLOBAL (estável entre janelas, conforme doc canônico)
    if "--with-macro" in sys.argv:   # só continuação a-favor-do-macro (setup_vs_macro==with_macro)
        keep = {int(r["entry_t"]) for r in rows if r.get("setup_vs_macro") == "with_macro"}
        trades = [tr for tr in trades if tr["t"] in keep]
    from datetime import datetime, timezone
    if len(sys.argv) > 1 and "-" in sys.argv[1]:   # filtro por data: só candidatos com entry_t >= AAAA-MM-DD
        cutoff = int(datetime.strptime(sys.argv[1], "%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp())
        sub = [tr for tr in trades if tr["t"] >= cutoff]; faixa = f">= {sys.argv[1]}"
    else:                                          # ou faixa por índice n (lo, hi]
        lo = int(sys.argv[1]) if len(sys.argv) > 1 else 0
        hi = int(sys.argv[2]) if len(sys.argv) > 2 else len(rows)
        sub = [tr for tr in trades if lo < tr["n"] <= hi]; faixa = f"n in ({lo},{hi}]"
    if "--count" in sys.argv:                      # só conta (NÃO toca no chart) — número sem redesenhar
        nl = sum(1 for tr in sub if tr["dir"] == "LONG")
        print(json.dumps({"valid_trades_total": len(trades), "na_faixa": len(sub), "LONG": nl, "SHORT": len(sub) - nl,
                           "faixa": faixa, "n_min": min((tr["n"] for tr in sub), default=None), "n_max": max((tr["n"] for tr in sub), default=None)}))
        return 0
    c = MCPClient(); c.start(); drawn = 0; fails = []; chart = {}
    try:
        st = c.call_tool("chart_get_state"); chart["before"] = {"symbol": st.get("symbol"), "tf": str(st.get("resolution"))}
        if st.get("symbol") != SYMBOL: c.call_tool("chart_set_symbol", {"symbol": SYMBOL})
        if str(st.get("resolution")) != TF: c.call_tool("chart_set_timeframe", {"timeframe": TF})
        chk = c.call_tool("chart_get_state"); sym, res = chk.get("symbol"), str(chk.get("resolution"))
        if not (str(sym).endswith("XAUUSD") and res == TF):
            c.stop(); print(json.dumps({"HARD_STOP": f"chart não confirmou 15: {sym}/{res}"})); return 1
        chart["used"] = {"symbol": sym, "tf": res}
        for tr in sub:
            r1 = c.call_tool("draw_shape", {"shape": tr["shape"],
                "point": {"time": tr["t"], "price": tr["entry"]},
                "point2": {"time": tr["exit_t"], "price": tr["target"]},
                "overrides": json.dumps({"stopLevel": price_to_ticks_offset(tr["entry"], tr["stop"]),
                                          "profitLevel": price_to_ticks_offset(tr["entry"], tr["target"])})})
            if r1.get("success"): drawn += 1
            else: fails.append({"n": tr["n"], "shape": tr["shape"], "err": str(r1)[:160]})
            c.call_tool("draw_shape", {"shape": "text", "point": {"time": tr["t"], "price": tr["label_y"]},
                "text": f"#{tr['n']}", "overrides": json.dumps({"color": GREEN if tr["dir"] == "LONG" else RED, "bold": True, "fontsize": 11})})
        dl = c.call_tool("draw_list")
        chart["draw_list_count"] = dl.get("count") if isinstance(dl, dict) else None
    finally:
        try: c.stop()
        except Exception: pass
    res = {"total_trades": len(trades), "faixa": faixa, "tentados": len(sub), "desenhados_position": drawn,
           "falhas": len(fails), "falhas_amostra": fails[:5], "chart": chart}
    (HERE / "plot_canonical_result.json").write_text(json.dumps(res, indent=2, ensure_ascii=False))
    print(json.dumps({k: res[k] for k in ["total_trades", "faixa", "tentados", "desenhados_position", "falhas", "falhas_amostra", "chart"]}, indent=2, ensure_ascii=False))
    return 0

if __name__ == "__main__":
    sys.exit(main())
