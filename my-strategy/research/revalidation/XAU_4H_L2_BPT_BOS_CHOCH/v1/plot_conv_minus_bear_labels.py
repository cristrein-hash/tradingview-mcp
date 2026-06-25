#!/usr/bin/env python3
"""Marca os 6 trades conv<=1 \\ BEAR (cortes EXTRA em BULL/TRANSITION, alem do regime) com LABEL LARANJA (#f57c00)
abaixo do entry, sobre o plot canonico existente (NAO cria long_position, NAO apaga — canon §6). Texto traz o R p/
responder: sao losers em regime permissivo? Verified 2026-06-25. Pre: pause flag + daemon XAU off."""
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

extra = sorted([b for b, r in TAB.items() if r["rm_conv"] == "1" and r["rm_bear"] == "0"],
               key=lambda b: OUT[b]["datetime"])
assert len(extra) == 6, f"esperado 6, obtido {len(extra)}"
for b in extra:
    print(f"  #{b} {TAB[b]['dt']} realR={TAB[b]['realR']} regime={TAB[b]['regime']} winner={TAB[b]['winner']}")

if not PAUSE_FLAG.exists(): print("ERRO pause flag"); sys.exit(1)
cli = MCPClient(); cli.start()
st = cli.call_tool("chart_get_state"); print(f"chart: {st.get('symbol')} {st.get('resolution')}")
if st.get("symbol") != SYMBOL: cli.call_tool("chart_set_symbol", {"symbol": SYMBOL}); time.sleep(1)
if str(st.get("resolution")) != TIMEFRAME: cli.call_tool("chart_set_timeframe", {"timeframe": TIMEFRAME}); time.sleep(1)
drawn = 0
for b in extra:
    et = int(F[b]["ts_epoch"]); entry = float(F[b]["close"]); Rd = SLCTX[b] * float(OUT[b]["risk_atr"])
    realR = float(TAB[b]["realR"])
    r = cli.call_tool("draw_shape", {"shape": "text",
        "point": {"time": et, "price": entry - 0.5 * Rd},
        "text": f"#{b} \\BEAR {'+' if realR > 0 else ''}{realR:.1f}R",
        "overrides": json.dumps({"color": "#f57c00", "bold": True, "fontsize": 12})})
    if r.get("success"): drawn += 1
    else: print(f"  #{b} label falhou: {r}")
print(f"labels laranja adicionados: {drawn}/6 (conv<=1 \\ BEAR = cortes extra em regime permissivo); chart NAO restaurado")
cli.stop()
