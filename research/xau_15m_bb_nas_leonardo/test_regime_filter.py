#!/usr/bin/env python3
"""Filtro final de MACRO-REGIME (Cris 2026-06-27): cortar BEAR, manter BULL+TRANSITION(NEUTRAL),
sobre a base aprovada A2+h1_eff>=0.15. Compara features de regime CAUSAIS que temos (macro_bull/bear as-of 4H,
h1_trend, h4_trend, h4_pos, macro_retr, macro_drop_atr, regime_age_h) p/ achar a mais eficiente. RAW-causal.
Tudo aplicado PRE-dedup (harness re-deduma). Mostra metricas completas + por ano."""
from filter_harness import run, by_splits, BASE, ROWS

H="r['h1_eff']>=0.15"  # filtro base ja fixado
# diagnostico: quantos dos 211 (taken) sao BEAR/BULL/NEUTRAL as-of
_,base211=run(eval("lambda r: ("+H+")"))
import collections
reg=collections.Counter()
for c in base211:
    reg["BULL" if c.get("macro_bull") else ("BEAR" if c.get("macro_bear") else "NEUTRAL")]+=1
print("Regime as-of dos 211 (base A2+h1_eff):",dict(reg))
for k in ("BULL","BEAR","NEUTRAL"):
    g=[c for c in base211 if (k=="BULL" and c.get("macro_bull")) or (k=="BEAR" and c.get("macro_bear")) or (k=="NEUTRAL" and not c.get("macro_bull") and not c.get("macro_bear"))]
    if g: print(f"  {k}: n={len(g)} WR={100*sum(x['win'] for x in g)/len(g):.1f}% sumR={sum(x['R'] for x in g):+.1f}")

CANDS={
 "BASE A2+h1_eff (211)": H,
 # pedido direto do Cris:
 "+ cortar BEAR (macro!=BEAR)": f"{H} and r['macro_bear']==0",
 "+ so BULL (macro_bull==1)": f"{H} and r['macro_bull']==1",
 # outras features de regime causais:
 "+ h1_trend>=0": f"{H} and (r.get('h1_trend') or 0)>=0",
 "+ h4_trend>=0 (None=keep)": f"{H} and ((r.get('h4_trend') is None) or r['h4_trend']>=0)",
 "+ h4_pos>=0.3 (None=keep)": f"{H} and ((r.get('h4_pos') is None) or r['h4_pos']>=0.3)",
 "+ macro_retr>=0.4": f"{H} and (r.get('macro_retr') or 0)>=0.4",
 "+ macro_drop_atr<=8": f"{H} and (r.get('macro_drop_atr') or 0)<=8",
 "+ regime_age_h>=24": f"{H} and (r.get('regime_age_h') or 0)>=24",
 # combos do regime macro + estrutura de tendencia
 "+ macro!=BEAR & h4_trend>=0": f"{H} and r['macro_bear']==0 and ((r.get('h4_trend') is None) or r['h4_trend']>=0)",
 "+ macro!=BEAR & h1_trend>=0": f"{H} and r['macro_bear']==0 and (r.get('h1_trend') or 0)>=0",
}
print(f"\n{'filtro':<40} {'N':>4} {'WR':>5} {'sumR':>6} {'DD':>5} {'stk':>3} {'maxR':>4} | {'dWR':>4} {'dDD':>4} {'dSumR':>5} {'cut':>3} {'bwl':>3} | yr24/25/26")
for name,expr in CANDS.items():
    s,taken=run(eval("lambda r: ("+expr+")"))
    yr,_=by_splits(taken)
    yrs="/".join(f"{yr[y][1]:.0f}" if y in yr else "-" for y in (2024,2025,2026))
    print(f"{name:<40} {s['n']:>4} {s['wr']:>5} {s['sumr']:>6} {s['dd']:>5} {s['streak']:>3} {s['maxR']:>4} | {s['dWR']:>+4} {s['dDD']:>+4} {s['dSumR']:>+5} {s['losers_cut']:>3} {s['big_winners_lost']:>3} | {yrs}")
