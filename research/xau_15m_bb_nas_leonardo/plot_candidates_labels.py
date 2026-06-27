#!/usr/bin/env python3
"""Plotagem SIMPLES dos candidatos Stage-B (a pedido de Cris): labels de TEXTO apenas — VERDE=LONG, VERMELHO=SHORT,
com NUMERAÇÃO do candidato (ordem temporal 1..N). SHORT acima / LONG abaixo do preço de entrada. Chart
PEPPERSTONE:XAUUSD / 15. NÃO long_position (override consciente p/ revisão visual de N candidatos). NÃO apaga
desenhos. NÃO Telegram/broker. NÃO screenshot. Verified 2026-06-26."""
import sys, csv, json
from pathlib import Path
HERE = Path(__file__).parent
REPO = Path("/Users/cristrein/tradingview-mcp")
sys.path.insert(0, str(REPO / "my-strategy/core"))
from tv_read_adapter import _MCP
WANT_SYMBOL, WANT_TF = "PEPPERSTONE:XAUUSD", "15"
GREEN, RED = "#26a69a", "#ef5350"
rows = list(csv.DictReader(open(HERE / "candidates_stageB.csv")))
rows.sort(key=lambda r: int(r["entry_t"]))
# limite opcional via arg (ex.: faixa) — default: todos
lo = int(sys.argv[1]) if len(sys.argv) > 1 else 0
hi = int(sys.argv[2]) if len(sys.argv) > 2 else len(rows)
sub = rows[lo:hi]
c = _MCP(); c.start(); drawn = 0; fails = []; chart = {}
try:
    st = c.call("chart_get_state"); chart["before"] = {"symbol": st.get("symbol"), "tf": str(st.get("resolution"))}
    if st.get("symbol") != WANT_SYMBOL: c.call("chart_set_symbol", {"symbol": WANT_SYMBOL})
    if str(st.get("resolution")) != WANT_TF: c.call("chart_set_timeframe", {"timeframe": WANT_TF})
    chk = c.call("chart_get_state"); sym, res = chk.get("symbol"), str(chk.get("resolution"))
    if not (str(sym).endswith("XAUUSD") and res == WANT_TF):
        c.stop(); print(json.dumps({"HARD_STOP": f"chart não confirmou 15: {sym}/{res}"})); sys.exit(1)
    chart["used"] = {"symbol": sym, "tf": res}
    for i, r in enumerate(sub, start=lo + 1):
        d = r["dir"]; price = float(r["entry_close"]); t = int(r["entry_t"])
        off = price * 0.0008
        ppt = price + off if d == "SHORT" else price - off
        r1 = c.call("draw_shape", {"shape": "text", "point": {"time": t, "price": round(ppt, 2)},
                                    "text": str(i),
                                    "overrides": json.dumps({"color": RED if d == "SHORT" else GREEN, "bold": True, "fontsize": 9})})
        if r1.get("success"): drawn += 1
        else: fails.append({"n": i, "t": t, "err": str(r1)[:120]})
finally:
    try: c.stop()
    except Exception: pass
res = {"candidatos_no_csv": len(rows), "faixa": [lo, hi], "tentados": len(sub), "desenhados": drawn,
       "falhas": len(fails), "falhas_amostra": fails[:5], "chart": chart}
(HERE / "plot_candidates_result.json").write_text(json.dumps(res, indent=2, ensure_ascii=False))
print(json.dumps({k: res[k] for k in ["candidatos_no_csv", "faixa", "tentados", "desenhados", "falhas", "chart"]}, indent=2, ensure_ascii=False))
