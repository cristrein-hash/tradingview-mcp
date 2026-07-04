#!/usr/bin/env python3
"""DA — offset da âncora dos 35 trades do Cris (materialização do check inline, reprodutível).
Pergunta: o preço de entry desenhado corresponde a QUANDO no passado? Para cada trade, a última
barra <= t0 cujo range contém o entry. Resultado: mediana 16 barras ANTES da âncora (cluster
13-19b = o flush-low anterior); trades 2026 (#27-#35) = 0-1b (dentro da barra-âncora).
Conclusão: o entry desenhado ≈ preço do FUNDO do flush já passado → fill retroativo por construção."""
import json, bisect
from pathlib import Path
import statistics

HERE = Path(__file__).resolve().parent
ns = {"__name__": "e", "__file__": str(HERE / "engine_substrate4_v5_hourcausal.py")}
exec(compile((HERE / "engine_substrate4_v5_hourcausal.py").read_text(), "e", "exec"), ns)
PRIMK = ns["PRIMK"]

raw = json.load(open(HERE / "results" / "cris_manual_trades_20260704.json"))
print(f"metadata: {raw['chart']} extraído {raw['extracted_at']}")
tr = sorted([{"t": s["props"]["points"][0]["time"], "entry": s["props"]["points"][0]["price"]}
             for s in raw["shapes"] if s.get("name") == "long_position"], key=lambda x: x["t"])

def find_block(t):
    for k, pr in PRIMK.items():
        s = pr["series"]
        if s[0]["t"] <= t <= s[-1]["t"]: return k, s
    return None, None

out = []
for i, x in enumerate(tr, 1):
    bk, s = find_block(x["t"]); ts = [b["t"] for b in s]
    j0 = bisect.bisect_right(ts, x["t"]) - 1
    last = None
    for k in range(j0, -1, -1):
        if s[k]["l"] <= x["entry"] <= s[k]["h"]: last = j0 - k; break
    out.append((i, last))
print("último toque do entry ANTES de t0 (barras antes):")
print(out)
ds = [d for _, d in out if d is not None]
print(f"entry tocado nas 24 barras antes de t0: {sum(1 for d in ds if d <= 24)}/35 · nunca antes no bloco: {35 - len(ds)}")
print(f"mediana barras-antes: {statistics.median(ds)} · max: {max(ds)}")
