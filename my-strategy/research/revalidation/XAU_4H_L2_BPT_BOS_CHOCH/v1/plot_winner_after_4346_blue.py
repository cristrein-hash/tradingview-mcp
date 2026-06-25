#!/usr/bin/env python3
"""Plota o PRIMEIRO winner (letrun_struct>0, régua oficial) com bar_idx > 4346, em LABEL AZUL, canônico
(long_position 20-bar + SL_CONTEXT + target +3R). Adiciona sobre o chart atual (não apaga). Verified 2026-06-25."""
import sys, json, time, csv
from pathlib import Path
V1 = Path(__file__).resolve().parent
ROOT = V1.parents[4]
sys.path.insert(0, str(ROOT / "alert-bridge"))
from draw_xau_4h_trades import MCPClient, price_to_ticks_offset, SYMBOL, TIMEFRAME, PAUSE_FLAG  # noqa: E402

BAR = 14400; WIDTH = 20
F = [json.loads(l) for l in open(V1 / "repro_recovery/raw_features_2020_2026.jsonl")]
REG = {int(r["bar_idx"]): r for r in csv.DictReader(open(V1 / "results/l2_bpt_regua_structural.csv"))}
TAB = {int(r["b"]): r for r in csv.DictReader(open(V1 / "results/l2_bpt_conv_bear_overlap_table.csv"))}

after = sorted(b for b in REG if b > 4346 and float(REG[b]["letrun_struct"]) > 0)
b = after[0]; r = REG[b]; t = TAB.get(b, {})
entry = float(r["entry"]); sl = float(r["sl"]); risk = float(r["risk"]); lr = float(r["letrun_struct"])
tgt = entry + 3 * risk; et = int(F[b]["ts_epoch"])
import datetime as dt
print(f"primeiro winner após #4346 = #{b} ({dt.datetime.utcfromtimestamp(et).strftime('%Y-%m-%d %H:%M')}) "
      f"letrun={lr:+.2f}R regime={t.get('regime')} cortado_pela_camada={t.get('rm_conv')=='1' or t.get('rm_blr')=='1'}")

if not PAUSE_FLAG.exists(): print("ERRO pause flag"); sys.exit(1)
cli = MCPClient(); cli.start()
st = cli.call_tool("chart_get_state")
if st.get("symbol") != SYMBOL: cli.call_tool("chart_set_symbol", {"symbol": SYMBOL}); time.sleep(1)
if str(st.get("resolution")) != TIMEFRAME: cli.call_tool("chart_set_timeframe", {"timeframe": TIMEFRAME}); time.sleep(1)
r1 = cli.call_tool("draw_shape", {"shape": "long_position",
    "point": {"time": et, "price": entry}, "point2": {"time": et + WIDTH * BAR, "price": tgt},
    "overrides": json.dumps({"stopLevel": price_to_ticks_offset(entry, sl), "profitLevel": price_to_ticks_offset(entry, tgt)})})
cli.call_tool("draw_shape", {"shape": "text", "point": {"time": et, "price": entry + 0.5 * risk},
    "text": f"#{b} {'+' if lr>0 else ''}{lr:.1f}R", "overrides": json.dumps({"color": "#1565c0", "bold": True, "fontsize": 12})})
print(f"plotado #{b} long_position + label AZUL (success={r1.get('success')}); chart não restaurado")
cli.stop()
