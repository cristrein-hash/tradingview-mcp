#!/usr/bin/env python3
"""Re-verificacao DIRETA dos melhores candidatos do engine de filtro long (synth agents erram metrica).
Extrai robust/synth do output do workflow + roda candidatos e combos no harness unico. by_year incluso.
Objetivo: max WR + min DD mantendo sumR (cortar winner curto OK; nao perder R>=3). RAW-causal."""
import json
from pathlib import Path
from filter_harness import run, by_splits, BASE

OUT="/private/tmp/claude-501/-Users-cristrein-tradingview-mcp/b3051da4-3014-4915-9b74-e74977852ecf/tasks/wzlak5rv6.output"
try:
    d=json.load(open(OUT)).get("result",{})
    print("=== ROBUST (verify-aprovados pelo engine) ===")
    for r in d.get("robust",[]):
        print(f"  [{r.get('verdict')}/{r.get('overfit_risk')}] {r.get('expr')}  (yr_ok={r.get('by_year_ok')} blk_ok={r.get('by_block_ok')})")
    print("\n=== SYNTH (texto do engine) ===")
    print((d.get("synth","") or "")[:1800])
except Exception as e:
    print("no workflow output:",e)

CANDS = {
 "BASE (keep all)": "True",
 # range / chop
 "R: h1_eff>=0.15": "r['h1_eff']>=0.15",
 "R: h1_eff>=0.14": "r['h1_eff']>=0.14",
 "R: h1_eff>=0.15 & atr_regime<=1.77": "r['h1_eff']>=0.15 and r['atr_regime']<=1.77",
 "R: h1_eff>=0.15 OR path_eff>=0.6": "r['h1_eff']>=0.15 or r['path_eff']>=0.6",
 # bubble/NAS (Cris)
 "B: buy_leg<=sell_leg+10": "(r.get('buy_bub_w_leg') or 0)<=(r.get('sell_bub_w_leg') or 0)+10",
 "B: buy_leg<=3*sell_leg+5": "(r.get('buy_bub_w_leg') or 0)<=3*(r.get('sell_bub_w_leg') or 0)+5",
 "B: buy_leg<=2*sell_leg+5 & nas_short_w24<2": "(r.get('buy_bub_w_leg') or 0)<=2*(r.get('sell_bub_w_leg') or 0)+5 and (r.get('nas_short_w24') or 0)<2",
 "B: nas_short_w24<2": "(r.get('nas_short_w24') or 0)<2",
 # extended (A)
 "E: rsi>50": "r['rsi']>50",
 "E: vpnode>0.6 & rsi>50": "((r.get('vpnode_dist_atr') is None) or abs(r['vpnode_dist_atr'])>0.6) and r['rsi']>50",
 # COMBOS cross-family (re-verificacao propria)
 "C: range & bubnas": "r['h1_eff']>=0.15 and (r.get('buy_bub_w_leg') or 0)<=3*(r.get('sell_bub_w_leg') or 0)+5",
 "C: range & rsi>50": "r['h1_eff']>=0.15 and r['rsi']>50",
 "C: range & nas_short_w24<2": "r['h1_eff']>=0.15 and (r.get('nas_short_w24') or 0)<2",
 "C: range14 & rsi>50 & nas<2": "r['h1_eff']>=0.14 and r['rsi']>50 and (r.get('nas_short_w24') or 0)<2",
 "C: range & bubnas & rsi>50": "r['h1_eff']>=0.15 and (r.get('buy_bub_w_leg') or 0)<=3*(r.get('sell_bub_w_leg') or 0)+5 and r['rsi']>50",
 "C: (range OR path) & bubnas": "(r['h1_eff']>=0.15 or r['path_eff']>=0.6) and (r.get('buy_bub_w_leg') or 0)<=3*(r.get('sell_bub_w_leg') or 0)+5",
 "C: range14 & bubnas": "r['h1_eff']>=0.14 and (r.get('buy_bub_w_leg') or 0)<=3*(r.get('sell_bub_w_leg') or 0)+5",
}

print("\n=== RE-VERIFICACAO DIRETA (harness unico) ===")
print(f"{'filtro':<38} {'N':>4} {'WR':>5} {'sumR':>6} {'DD':>5} {'stk':>3} {'big':>3} {'maxR':>4} | {'dWR':>4} {'dDD':>4} {'dSumR':>5} {'cut':>3} {'wl':>3} {'bwl':>3} | yr24/25/26")
rows=[]
for name,expr in CANDS.items():
    s,taken=run(eval("lambda r: ("+expr+")"))
    yr,_=by_splits(taken)
    yrs="/".join(f"{yr[y][1]:.0f}" if y in yr else "-" for y in (2024,2025,2026))
    print(f"{name:<38} {s['n']:>4} {s['wr']:>5} {s['sumr']:>6} {s['dd']:>5} {s['streak']:>3} {s['bigwin']:>3} {s['maxR']:>4} | {s['dWR']:>+4} {s['dDD']:>+4} {s['dSumR']:>+5} {s['losers_cut']:>3} {s['winners_lost']:>3} {s['big_winners_lost']:>3} | {yrs}")
    rows.append((name,expr,s))
