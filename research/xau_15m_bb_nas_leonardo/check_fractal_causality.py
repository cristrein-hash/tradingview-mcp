#!/usr/bin/env python3
"""Checa look-ahead do fractal: a mínima fractal exige L[i]==min(L[i-4:i+5]) → só confirmável em i+4.
Entrada 8ATR no bar cj. Se cj < i+4, a entrada usou barras futuras (i+1..i+4) p/ saber que i é fundo = LOOK-AHEAD.
Conta quantos trades têm bars_to_8atr (=cj-i) < 4. dataset_8atr.jsonl tem bars_to_8atr."""
import json
from pathlib import Path
HERE=Path(__file__).parent
rows=[json.loads(l) for l in (HERE/"dataset_8atr.jsonl").read_text().splitlines()]
bt=[r["bars_to_8atr"] for r in rows]
lt4=sum(1 for x in bt if x<4); lt5=sum(1 for x in bt if x<5)
print(f"trades 8ATR: {len(rows)}")
print(f"bars_to_8atr <4 (fractal NÃO confirmável na entrada = LOOK-AHEAD): {lt4} ({100*lt4/len(rows):.1f}%)")
print(f"bars_to_8atr <5: {lt5} ({100*lt5/len(rows):.1f}%)")
import statistics as st
print(f"bars_to_8atr: min={min(bt)} mediana={st.median(bt):.0f} p10={sorted(bt)[len(bt)//10]}")
# se houver look-ahead, recomputa WR do stack final excluindo cj-i<4
def R_B(r): return (r.get("absorption")==1 and r.get("sell_decel")==0)  # placeholder; R_B precisa de dataset_r2refine
print("\n(distribuição mostra se o look-ahead do fractal é material; se <4 ~0%, entrada é causal)")
