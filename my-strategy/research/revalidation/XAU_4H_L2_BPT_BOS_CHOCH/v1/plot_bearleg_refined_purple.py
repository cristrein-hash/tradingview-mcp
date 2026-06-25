#!/usr/bin/env python3
"""Plota os 12 cortes do BEAR_LEG_REFINED (aprovado, BLOCK dentro de MACRO_BEAR_LEG) canonico (long_position
estrutural SL_CONTEXTUAL + target +3R + 20-bar) com label ROXO (#6a1b9a). Texto marca '∩conv' nos que tambem sao
conv<=1 (4/12) p/ ver se e a mesma familia. Chart ja limpo pelo Cris. Verified 2026-06-25. Pre: pause flag + daemon off."""
import sys, json, time, csv
from pathlib import Path
V1 = Path(__file__).resolve().parent
ROOT = V1.parents[4]
sys.path.insert(0, str(ROOT / "alert-bridge"))
from draw_xau_4h_trades import MCPClient, price_to_ticks_offset, SYMBOL, TIMEFRAME, PAUSE_FLAG  # noqa: E402

BAR = 14400; WIDTH = 20; TR = 3.0
F = [json.loads(l) for l in open(V1 / "repro_recovery/raw_features_2020_2026.jsonl")]
OUT = {int(r["bar_idx"]): r for r in csv.DictReader(open(V1 / "results/l2_bpt_uncapped_or_proxy_outcomes_276.csv"))}
SLCTX = {}
for r in csv.DictReader(open(V1 / "results/l2_bpt_sl_context_policy_results.csv")):
    k = r.get("bar_idx") or list(r.values())[0]
    try: SLCTX[int(float(k))] = float(r["sl_atr"])
    except Exception: pass
TAB = {int(r["b"]): r for r in csv.DictReader(open(V1 / "results/l2_bpt_conv_bear_overlap_table.csv"))}

blr = sorted([b for b, r in TAB.items() if r["rm_blr"] == "1"], key=lambda b: OUT[b]["datetime"])
assert len(blr) == 12, f"esperado 12, obtido {len(blr)}"
inter = [b for b in blr if TAB[b]["rm_conv"] == "1"]
print(f"bear_leg_refined BLOCK = {len(blr)} | ∩conv<=1 = {len(inter)}: {inter}")
for b in blr:
    print(f"  #{b} {TAB[b]['dt']} realR={TAB[b]['realR']} winner={TAB[b]['winner']} {'∩conv' if TAB[b]['rm_conv']=='1' else ''}")

if not PAUSE_FLAG.exists(): print("ERRO pause flag"); sys.exit(1)
cli = MCPClient(); cli.start()
st = cli.call_tool("chart_get_state"); print(f"chart: {st.get('symbol')} {st.get('resolution')}")
if st.get("symbol") != SYMBOL: cli.call_tool("chart_set_symbol", {"symbol": SYMBOL}); time.sleep(1)
if str(st.get("resolution")) != TIMEFRAME: cli.call_tool("chart_set_timeframe", {"timeframe": TIMEFRAME}); time.sleep(1)
drawn = 0
for b in blr:
    et = int(F[b]["ts_epoch"]); entry = float(F[b]["close"]); atr = float(OUT[b]["risk_atr"])
    sl = entry - SLCTX[b] * atr; tgt = entry + TR * SLCTX[b] * atr
    assert entry > sl and tgt > entry
    r1 = cli.call_tool("draw_shape", {"shape": "long_position",
        "point": {"time": et, "price": entry}, "point2": {"time": et + WIDTH * BAR, "price": tgt},
        "overrides": json.dumps({"stopLevel": price_to_ticks_offset(entry, sl),
                                 "profitLevel": price_to_ticks_offset(entry, tgt)})})
    if r1.get("success"): drawn += 1
    else: print(f"  #{b} long_position falhou: {r1}")
    realR = float(TAB[b]["realR"]); tag = " ∩conv" if TAB[b]["rm_conv"] == "1" else ""
    cli.call_tool("draw_shape", {"shape": "text",
        "point": {"time": et, "price": entry + 0.5 * SLCTX[b] * atr},
        "text": f"#{b} {'+' if realR > 0 else ''}{realR:.1f}R{tag}",
        "overrides": json.dumps({"color": "#6a1b9a", "bold": True, "fontsize": 12})})
print(f"bear_leg_refined plotado: {drawn} long_position + 12 labels ROXOS ({len(inter)} marcados ∩conv); chart NAO restaurado")
cli.stop()
