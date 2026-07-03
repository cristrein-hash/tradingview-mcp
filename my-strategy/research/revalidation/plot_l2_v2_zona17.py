#!/usr/bin/env python3
"""Plota os 17 trades APROVADOS da L2/BPT XAU 4H LONG · RTSE V2 zona-pura no chart 4H.

Fonte dos trades: docs/L2_BPT_XAU_4H_LONG_V2_STRATEGY_CONFIRMATION_SHEET.md §7 (OK FINAL Cris
2026-07-02) — tabela embutida abaixo (bar_idx, date, entry, SL, R let-run real com custo −0,35R).
entry_time resolvido do frozen RAW (repro_recovery/raw_features_2020_2026.jsonl) por bar_idx,
com ASSERT de data (sheet vs RAW) e ASSERT do painel (N17, sumR≈+36,2, WR 9/17).

Canon (PLOTTING_CANON_MASTER + skills/plotting-canon):
  long_position + label #id (fontsize 12), width 20 barras 4H, ticks mintick 0.01,
  color_mode = OUTCOME (verde winner / vermelho loser), exit_policy = FONTE
  (let-run R realizado; exit = entry + R*risk — convenção do l2_plot_4h.py aprovado).

Remoção prévia SELETIVA (autorização Cris 2026-07-03): remove TODOS os desenhos EXCETO
retângulos (= zonas do regime detector, preservadas). NUNCA draw_clear.
Sem screenshot; verificação por draw_list. Requer pause flag. Autorizado por Cris.
"""
import sys, json
from pathlib import Path

REPO = Path("/Users/cristrein/tradingview-mcp")
V1 = REPO / "my-strategy/research/revalidation/XAU_4H_L2_BPT_BOS_CHOCH/v1"
sys.path.insert(0, str(REPO / "alert-bridge"))
from draw_xau_4h_trades import MCPClient, price_to_ticks_offset  # helper canônico

PAUSE = Path("/tmp/claude_recheck.paused")
SYMBOL, TF, BAR_S, WIDTH = "PEPPERSTONE:XAUUSD", "240", 14400, 20
GREEN, RED = "#1a8917", "#cc0000"
KEEP_TYPES = {"rectangle"}  # zonas do regime detector — PRESERVAR

# (bar_idx, date, entry, sl, R) — confirmation sheet §7, verbatim
TRADES17 = [
    (4918, "2023-03-08", 1820.4, 1804.0, 11.98),
    (4926, "2023-03-09", 1830.7, 1811.0,  8.62),
    (5016, "2023-03-30", 1980.2, 1954.0, -1.35),
    (5103, "2023-04-21", 1986.1, 1968.0, -1.35),
    (5826, "2023-10-06", 1831.6, 1812.0,  7.99),
    (5875, "2023-10-18", 1948.2, 1911.0, -0.01),
    (6376, "2024-02-15", 2004.5, 1983.0,  7.02),
    (6791, "2024-05-23", 2328.4, 2305.0, -1.35),
    (7149, "2024-08-15", 2444.5, 2422.0,  4.19),
    (7549, "2024-11-18", 2585.9, 2553.0,  1.68),
    (8133, "2025-04-04", 3025.7, 2996.0, -1.35),
    (8216, "2025-04-25", 3280.9, 3256.0, -1.35),
    (8236, "2025-04-30", 3288.6, 3191.0, -1.35),
    (8893, "2025-10-01", 3872.9, 3790.0,  1.34),
    (8905, "2025-10-03", 3882.6, 3817.0,  1.68),
    (8978, "2025-10-21", 4111.2, 3938.0, -1.35),
    (9007, "2025-10-28", 3938.7, 3814.0,  1.15),
]

# ---- resolver entry_time por bar_idx no frozen RAW + validar datas ----
frozen = [json.loads(l) for l in open(V1 / "repro_recovery/raw_features_2020_2026.jsonl")]
trades = []
for bi, date, entry, sl, R in TRADES17:
    r = frozen[bi]
    raw_date = str(r.get("datetime") or "")[:10]
    if raw_date and raw_date != date:
        sys.exit(f"ABORT: bar_idx {bi} data RAW={raw_date} != sheet={date}")
    risk = entry - sl
    if risk <= 0:
        sys.exit(f"ABORT: risco inválido no bar {bi}")
    trades.append({"t": int(r["ts_epoch"]), "date": date, "entry": entry, "sl": sl,
                   "exit": round(entry + R * risk, 2), "R": R, "win": R > 0})

# ---- painel de sanidade (validate-before-presenting) ----
n = len(trades); wn = sum(1 for t in trades if t["win"]); sm = sum(t["R"] for t in trades)
assert n == 17, n
assert wn == 9, wn
assert abs(sm - 36.2) < 0.5, sm
print(f"PANEL OK: N={n} WR={100*wn/n:.0f}% sumR={sm:+.1f} ({trades[0]['date']} -> {trades[-1]['date']})")

if "--prepare-only" in sys.argv:
    print("prepare-only: sem MCP/chart."); sys.exit(0)
if not PAUSE.exists():
    sys.exit("ERRO: pause flag ausente. Rode: touch /tmp/claude_recheck.paused")

c = MCPClient(); c.start()
report = {"removed": 0, "kept_rectangles": 0, "posicoes": 0, "labels": 0, "falhas": []}
try:
    st = c.call_tool("chart_get_state")
    sym, res = st.get("symbol"), str(st.get("resolution"))
    if not str(sym).endswith("XAUUSD"):
        c.stop(); sys.exit(f"HARD_STOP: chart={sym} (esperado XAUUSD)")
    report["chart_inicial"] = f"{sym}/{res}"

    # ---- 1) remoção SELETIVA: apagar tudo EXCETO retângulos (regime detector) ----
    # draw_list retorna {success, count, shapes:[{id, name}]} (formato sondado 2026-07-03)
    dl0 = c.call_tool("draw_list")
    entities = dl0.get("shapes") or []
    report["before"] = dl0.get("count")
    if report["before"] and not entities:
        c.stop(); sys.exit("ABORT: draw_list com count>0 mas sem lista 'shapes' — formato inesperado, nada removido")
    for e in entities:
        eid = e.get("id")
        etype = str(e.get("name") or "").lower()
        if not eid:
            continue
        if any(k in etype for k in KEEP_TYPES):
            report["kept_rectangles"] += 1
            continue
        rr = c.call_tool("draw_remove_one", {"entity_id": eid})
        if isinstance(rr, dict) and rr.get("success"):
            report["removed"] += 1
        else:
            report["falhas"].append(f"remove {eid} ({etype}): {str(rr)[:60]}")

    # GATE: se qualquer remoção falhou, NAO plotar (evita duplicar sets no chart)
    if report["falhas"]:
        print(json.dumps(report, indent=2, ensure_ascii=False))
        c.stop(); sys.exit("ABORT: remocao seletiva incompleta — plot cancelado para nao duplicar")

    # ---- 2) garantir 4H ----
    if res != TF:
        c.call_tool("chart_set_timeframe", {"timeframe": TF})
        import time as _t; _t.sleep(1.5)

    # ---- 3) plot canônico dos 17 ----
    for i, t in enumerate(trades, 1):
        entry, sl, ex, tt, win = t["entry"], t["sl"], t["exit"], t["t"], t["win"]
        risk = entry - sl
        r1 = c.call_tool("draw_shape", {"shape": "long_position",
            "point": {"time": tt, "price": entry},
            "point2": {"time": tt + WIDTH * BAR_S, "price": ex},
            "overrides": json.dumps({
                "stopLevel": price_to_ticks_offset(entry, sl),
                "profitLevel": price_to_ticks_offset(entry, ex)})})
        if isinstance(r1, dict) and r1.get("success"): report["posicoes"] += 1
        else: report["falhas"].append(f"pos #{i}: {str(r1)[:60]}")
        r2 = c.call_tool("draw_shape", {"shape": "text",
            "point": {"time": tt, "price": round(entry + 0.5 * risk, 2)},
            "text": f"#{i}",
            "overrides": json.dumps({"color": GREEN if win else RED, "bold": True, "fontsize": 12})})
        if isinstance(r2, dict) and r2.get("success"): report["labels"] += 1

    dl = c.call_tool("draw_list")
    report["after"] = dl.get("count")
finally:
    try: c.stop()
    except Exception: pass

print(json.dumps(report, indent=2, ensure_ascii=False))
