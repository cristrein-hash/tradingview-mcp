#!/usr/bin/env python3
"""Grupo F = BEAR \\ conv<=1 (7 trades que regime BEAR cortaria mas a CONVERGENCIA preserva). Plota CANONICO
(long_position estrutural SL_CONTEXTUAL + target +3R + 20-bar) com label AMARELO (#f9a825) trazendo R + as VOZES
VIVAS apesar do BEAR (responde: o que estava vivo ali?). NAO apaga nada (canon §6). Verified 2026-06-25.
Pre: pause flag + daemon XAU off."""
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
ALLV = {"regime", "snap", "sweep", "bubble"}

grpF = sorted([b for b, r in TAB.items() if r["rm_bear"] == "1" and r["rm_conv"] == "0"],
              key=lambda b: (-int(TAB[b]["runner"]), OUT[b]["datetime"]))
assert len(grpF) == 7, f"esperado 7, obtido {len(grpF)}"
for b in grpF:
    off = set(TAB[b]["why_low"].split("|")) if TAB[b]["why_low"] else set()
    on = ALLV - off
    print(f"  #{b} {TAB[b]['dt']} realR={TAB[b]['realR']} mfe={TAB[b]['mfe']} runner={TAB[b]['runner']} VIVAS={'+'.join(sorted(on))}")

if not PAUSE_FLAG.exists(): print("ERRO pause flag"); sys.exit(1)
cli = MCPClient(); cli.start()
st = cli.call_tool("chart_get_state"); print(f"chart: {st.get('symbol')} {st.get('resolution')}")
if st.get("symbol") != SYMBOL: cli.call_tool("chart_set_symbol", {"symbol": SYMBOL}); time.sleep(1)
if str(st.get("resolution")) != TIMEFRAME: cli.call_tool("chart_set_timeframe", {"timeframe": TIMEFRAME}); time.sleep(1)
drawn = 0
for b in grpF:
    et = int(F[b]["ts_epoch"]); entry = float(F[b]["close"]); atr = float(OUT[b]["risk_atr"])
    sl = entry - SLCTX[b] * atr; tgt = entry + TR * SLCTX[b] * atr
    assert entry > sl and tgt > entry
    r1 = cli.call_tool("draw_shape", {"shape": "long_position",
        "point": {"time": et, "price": entry}, "point2": {"time": et + WIDTH * BAR, "price": tgt},
        "overrides": json.dumps({"stopLevel": price_to_ticks_offset(entry, sl),
                                 "profitLevel": price_to_ticks_offset(entry, tgt)})})
    if r1.get("success"): drawn += 1
    else: print(f"  #{b} long_position falhou: {r1}")
    off = set(TAB[b]["why_low"].split("|")) if TAB[b]["why_low"] else set()
    on = "+".join(sorted((ALLV - off) - {"regime"}))  # vozes vivas alem do regime
    realR = float(TAB[b]["realR"])
    cli.call_tool("draw_shape", {"shape": "text",
        "point": {"time": et, "price": entry + 0.5 * SLCTX[b] * atr},
        "text": f"#{b} {'+' if realR > 0 else ''}{realR:.1f}R [{on}]",
        "overrides": json.dumps({"color": "#f9a825", "bold": True, "fontsize": 12})})
print(f"Grupo F plotado: {drawn} long_position + 7 labels AMARELOS (vozes vivas no texto); chart NAO restaurado")
cli.stop()
