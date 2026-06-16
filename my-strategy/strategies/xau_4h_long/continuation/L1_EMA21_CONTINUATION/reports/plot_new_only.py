#!/usr/bin/env python3
"""Plota os 25 NEW_ONLY (regime_l1_v4) no chart 4H para revisão visual manual.
Read-only sobre dados; só DESENHA (vertical_line + label) via MCP. NÃO inventa preço de trade
(usa o close/high real do bar). NÃO apaga desenhos, NÃO Telegram, NÃO broker, NÃO trade mgmt.
Deixa o chart em PEPPERSTONE:XAUUSD/240 (revisão visual exige 240)."""
import sys, csv, json
from pathlib import Path
from datetime import datetime, timezone

HERE = Path(__file__).resolve().parent
L1 = HERE.parent
REPO = L1.parents[4]
sys.path.insert(0, str(L1)); sys.path.insert(0, str(REPO / "my-strategy/core"))
import scanner
from tv_read_adapter import _MCP

CSV = HERE / "l1_old_vs_new_regime_comparison.csv"
WANT_SYMBOL, WANT_TF = "PEPPERSTONE:XAUUSD", "240"

def to_unix(ts):  # ISO UTC naive -> unix (UTC)
    return int(datetime.fromisoformat(ts).replace(tzinfo=timezone.utc).timestamp())

def run():
    rows = [r for r in csv.DictReader(open(CSV)) if r["status"] == "NEW_ONLY"]
    print(f"NEW_ONLY no CSV: {len(rows)}")
    S = scanner.build_series()
    plan, missing = [], []
    for r in rows:
        u = to_unix(r["timestamp"])
        i = S.idx.get(u)
        if i is None:  # nearest dentro de 4h
            cand = [k for k in range(S.N) if abs(S.T[k]-u) <= 4*3600]
            i = min(cand, key=lambda k: abs(S.T[k]-u)) if cand else None
        if i is None:
            missing.append({"id": r["candidate_id"], "ts": r["timestamp"], "reason": "bar não encontrado no RAW"})
            continue
        plan.append({"id": r["candidate_id"], "ts": r["timestamp"], "unix": S.T[i],
                     "close": S.C[i], "high": S.H[i], "low": S.L[i],
                     "old": r["old_regime"], "reason": r["notes"][:40]})
    # MCP: capturar + setar chart 240
    c = _MCP(); c.start()
    chart = {}
    try:
        st = c.call("chart_get_state")
        chart["before"] = {"symbol": st.get("symbol"), "tf": str(st.get("resolution"))}
        if st.get("symbol") != WANT_SYMBOL: c.call("chart_set_symbol", {"symbol": WANT_SYMBOL})
        if str(st.get("resolution")) != WANT_TF: c.call("chart_set_timeframe", {"timeframe": WANT_TF})
        chk = c.call("chart_get_state")
        sym, res = chk.get("symbol"), str(chk.get("resolution"))
        if not (str(sym).endswith("XAUUSD") and res == WANT_TF):
            c.stop(); return {"HARD_STOP": f"chart não confirmou 240: {sym}/{res}"}
        chart["used"] = {"symbol": sym, "tf": res}
        plotted = 0
        for p in plan:
            label = f"NEW_ONLY #{p['id']} L {p['old']}->BULL"
            # marcador vertical no candle (não inventa nível de trade)
            c.call("draw_shape", {"shape": "vertical_line", "point": {"time": p["unix"], "price": p["close"]}})
            # label curto ancorado no high real do bar
            c.call("draw_shape", {"shape": "text", "point": {"time": p["unix"], "price": round(p["high"]*1.004, 2)}, "text": label})
            plotted += 1
        chart["left_on"] = chart["used"]  # NÃO restaura: revisão visual exige 240
    finally:
        try: c.stop()
        except Exception: pass
    res = {"new_only_found": len(rows), "plotted": plotted, "missing": missing,
           "chart": chart, "telegram": "none", "broker": "untouched"}
    (HERE / "l1_new_only_plotting_result.json").write_text(json.dumps(res, indent=2, ensure_ascii=False))
    print(json.dumps(res, indent=2, ensure_ascii=False))
    return res

if __name__ == "__main__":
    run()
