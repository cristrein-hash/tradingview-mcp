#!/usr/bin/env python3
"""Marca os 17 trades conv<=1 ∩ BEAR (redundantes com regime BEAR) com LABEL AZUL (#1565c0) abaixo do entry, sobre o
plot canonico conv<=1 ja existente (NAO cria long_position, NAO apaga nada — canon §6). So highlight de redundancia.
Verified 2026-06-25. Pre: pause flag + daemon XAU off."""
import sys, json, time, csv
from pathlib import Path
V1 = Path(__file__).resolve().parent
ROOT = V1.parents[4]
sys.path.insert(0, str(ROOT / "alert-bridge"))
from draw_xau_4h_trades import MCPClient, SYMBOL, TIMEFRAME, PAUSE_FLAG  # noqa: E402

F = [json.loads(l) for l in open(V1 / "repro_recovery/raw_features_2020_2026.jsonl")]
OUT = {int(r["bar_idx"]): r for r in csv.DictReader(open(V1 / "results/l2_bpt_uncapped_or_proxy_outcomes_276.csv"))}
SLCTX = {}
for r in csv.DictReader(open(V1 / "results/l2_bpt_sl_context_policy_results.csv")):
    k = r.get("bar_idx") or list(r.values())[0]
    try: SLCTX[int(float(k))] = float(r["sl_atr"])
    except Exception: pass
TAB = {int(r["b"]): r for r in csv.DictReader(open(V1 / "results/l2_bpt_conv_bear_overlap_table.csv"))}

inter = sorted([b for b, r in TAB.items() if r["rm_conv"] == "1" and r["rm_bear"] == "1"],
               key=lambda b: OUT[b]["datetime"])
assert len(inter) == 17, f"esperado 17 ∩, obtido {len(inter)}"
print(f"conv<=1 ∩ BEAR = {len(inter)} trades (azul): {inter}")

if not PAUSE_FLAG.exists(): print("ERRO pause flag"); sys.exit(1)
cli = MCPClient(); cli.start()
st = cli.call_tool("chart_get_state"); print(f"chart: {st.get('symbol')} {st.get('resolution')}")
if st.get("symbol") != SYMBOL: cli.call_tool("chart_set_symbol", {"symbol": SYMBOL}); time.sleep(1)
if str(st.get("resolution")) != TIMEFRAME: cli.call_tool("chart_set_timeframe", {"timeframe": TIMEFRAME}); time.sleep(1)
drawn = 0
for b in inter:
    et = int(F[b]["ts_epoch"]); entry = float(F[b]["close"]); Rd = SLCTX[b] * float(OUT[b]["risk_atr"])
    r = cli.call_tool("draw_shape", {"shape": "text",
        "point": {"time": et, "price": entry - 0.5 * Rd},   # abaixo do entry, nao sobrepoe label verde/vermelho
        "text": f"#{b} ∩BEAR",
        "overrides": json.dumps({"color": "#1565c0", "bold": True, "fontsize": 12})})
    if r.get("success"): drawn += 1
    else: print(f"  #{b} label falhou: {r}")
print(f"labels azuis adicionados: {drawn}/17 (conv<=1 ∩ BEAR = redundantes); chart NAO restaurado")
cli.stop()
