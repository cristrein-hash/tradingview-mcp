#!/usr/bin/env python3
"""Plota os 31 trades CORTADOS por conv≤1 ∪ bear_leg_refined (a camada de skip) com LABEL VERMELHO, canônico
(long_position 20-bar + SL_CONTEXT estrutural real + target +3R). Texto = #id + letrun_struct R (régua oficial) p/
review visual ANTES de aprovar. Chart já limpo pelo Cris (não chama draw_clear, canon §6). Verified 2026-06-25."""
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

cut = sorted([b for b, t in TAB.items() if (t["rm_conv"] == "1" or t["rm_blr"] == "1") and b in REG])
assert len(cut) == 31, f"esperado 31, obtido {len(cut)}"
nW = sum(1 for b in cut if float(REG[b]["letrun_struct"]) > 0)
print(f"camada de skip conv≤1 ∪ bear_leg_refined: {len(cut)} cortes | dos quais {nW} positivos sob let-run (winners cortados)")

if not PAUSE_FLAG.exists(): print("ERRO pause flag"); sys.exit(1)
cli = MCPClient(); cli.start()
st = cli.call_tool("chart_get_state"); print(f"chart: {st.get('symbol')} {st.get('resolution')}")
if st.get("symbol") != SYMBOL: cli.call_tool("chart_set_symbol", {"symbol": SYMBOL}); time.sleep(1)
if str(st.get("resolution")) != TIMEFRAME: cli.call_tool("chart_set_timeframe", {"timeframe": TIMEFRAME}); time.sleep(1)
drawn = 0
for b in cut:
    r = REG[b]; entry = float(r["entry"]); sl = float(r["sl"]); risk = float(r["risk"])
    tgt = entry + 3 * risk; et = int(F[b]["ts_epoch"]); lr = float(r["letrun_struct"])
    assert entry > sl and tgt > entry
    r1 = cli.call_tool("draw_shape", {"shape": "long_position",
        "point": {"time": et, "price": entry}, "point2": {"time": et + WIDTH * BAR, "price": tgt},
        "overrides": json.dumps({"stopLevel": price_to_ticks_offset(entry, sl),
                                 "profitLevel": price_to_ticks_offset(entry, tgt)})})
    if r1.get("success"): drawn += 1
    else: print(f"  #{b} long_position falhou: {r1}")
    cli.call_tool("draw_shape", {"shape": "text",
        "point": {"time": et, "price": entry + 0.5 * risk},
        "text": f"#{b} {'+' if lr > 0 else ''}{lr:.1f}R",
        "overrides": json.dumps({"color": "#cc0000", "bold": True, "fontsize": 12})})
print(f"desenhados: {drawn} long_position + 31 labels VERMELHOS (cortes da camada de skip); chart NAO restaurado")
cli.stop()
