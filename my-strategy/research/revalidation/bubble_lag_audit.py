#!/usr/bin/env python3
"""AUDITORIA do LAG das bubbles (ordem Cris 2026-07-14): "bubbles 15M aparecem ao fecho da barra
concluída" — verificar se o meu known_at está certo vs a extração canónica que funcionou.
Compara: lag medido do OPEN (known_at−t) vs do FECHO (known_at−(t+900)) em barras 15M.
Fonte canónica = research/xau_15m_bb_nas_leonardo/bubbles/*.bubbles.jsonl (extração que os engines
de sucesso usaram). Sem lookahead, só medição. Reprodutível."""
import json, statistics
from collections import Counter
from pathlib import Path
BUB = Path("/Users/cristrein/tradingview-mcp/research/xau_15m_bb_nas_leonardo/bubbles")
BAR = 900
files = sorted(BUB.glob("*.bubbles.jsonl"))
lag_open, lag_close = [], []
n = 0
for f in files:
    for line in f.read_text().splitlines():
        if not line.strip(): continue
        b = json.loads(line)
        t, ka = b.get("t"), b.get("known_at")
        if t is None or ka is None: continue
        n += 1
        lag_open.append((ka - t) / BAR)
        lag_close.append((ka - (t + BAR)) / BAR)

def dist(name, arr):
    c = Counter(round(x) for x in arr)
    med = statistics.median(arr)
    print(f"  {name}: mediana {med:.2f} barras · min {min(arr):.2f} max {max(arr):.2f}")
    print(f"      histograma (barras→%): " + " · ".join(f"{k}b:{100*v/len(arr):.0f}%" for k, v in sorted(c.items())[:8]))

print(f"BUBBLES canónicas auditadas: {n} (de {len(files)} blocos)")
print("\nLAG do OPEN da barra-âncora (known_at − t):")
dist("lag_open", lag_open)
print("\nLAG do FECHO da barra-âncora (known_at − (t+900)):  ← o que importa causalmente")
dist("lag_close", lag_close)
# quantos aparecem EXATAMENTE ao fecho da própria barra (lag_close≈0) vs 1 barra depois
c0 = sum(1 for x in lag_close if abs(x) < 0.5)
c1 = sum(1 for x in lag_close if 0.5 <= x < 1.5)
print(f"\nVEREDITO: aparecem ao FECHO da própria barra (lag_close≈0): {100*c0/n:.0f}% · "
      f"1 barra depois: {100*c1/n:.0f}% · resto {100*(n-c0-c1)/n:.0f}%")
