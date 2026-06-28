#!/usr/bin/env python3
"""Detecção causal de regime vs zonas do Cris (2026-06-28). Compara o classificador causal existente
macro_regime_4h.json (BULL/BEAR/NEUTRAL, EMA50+swing do 15M, as-of/sem lookahead) com regime_zones_cris.json.
Mede concordância por barra 15M (NEUTRAL≈RANGE) + matriz de confusão + precisão por zona. Só dados."""
import json,bisect
from pathlib import Path
HERE=Path(__file__).parent
MR=json.loads((HERE/"macro_regime_4h.json").read_text())["bars_4h"]; MEND=[b["t_end"] for b in MR]
def macro_at(t):
    k=bisect.bisect_right(MEND,t)-1; return MR[k]["macro"] if k>=0 else None
Z=json.loads((HERE/"regime_zones_cris.json").read_text())
# grade de barras 15M no período coberto (dos primitives)
PRIM=[json.loads(p.read_text()) for p in sorted((HERE/"primitives").glob("*.primitives.json"))]
T=sorted({b["t"] for pr in PRIM for b in pr["series"]})
zmin=min(z["t_start"] for z in Z); zmax=min(max(z["t_end"] for z in Z), T[-1])
grid=[t for t in T if zmin<=t<=zmax]
def cris_at(t):
    for z in Z:
        if z["t_start"]<=t<=z["t_end"]: return z["type"]
    return None
MAP={"BULL":"BULL","BEAR":"BEAR","NEUTRAL":"RANGE","RANGE":"RANGE"}
from collections import Counter,defaultdict
conf=Counter(); per=defaultdict(Counter); tot=0; agree=0
for t in grid:
    c=cris_at(t); m=macro_at(t)
    if c is None or m is None: continue
    md=MAP.get(m,m); tot+=1
    per[c][md]+=1; conf[(c,md)]+=1
    if md==c: agree+=1
print(f"barras 15M comparadas: {tot} | concordância global (NEUTRAL=RANGE): {100*agree/tot:.1f}%")
print(f"\nprecisão por ZONA do Cris (o que o detector causal diz dentro de cada uma):")
print(f"{'zona Cris':<8}{'n':>7}{'BULL%':>7}{'BEAR%':>7}{'RANGE%':>7}{'= match%':>9}")
for c in ("RANGE","BULL","BEAR"):
    n=sum(per[c].values())
    if not n: continue
    print(f"{c:<8}{n:>7}{100*per[c]['BULL']/n:>7.1f}{100*per[c]['BEAR']/n:>7.1f}{100*per[c]['RANGE']/n:>7.1f}{100*per[c][c]/n:>9.1f}")
# por zona individual (as 6) com datas
print(f"\npor zona individual:")
for i,z in enumerate(Z,1):
    g=[t for t in grid if z['t_start']<=t<=z['t_end']]
    cc=Counter(MAP.get(macro_at(t)) for t in g if macro_at(t))
    n=sum(cc.values())
    if not n: continue
    top=cc.most_common(1)[0]
    print(f"  {i} {z['type']:<6} {z['start'][:10]}..{z['end'][:10]}  detector: "+", ".join(f"{k}{100*v/n:.0f}%" for k,v in cc.most_common())+f"  (match {100*cc[z['type']]/n:.0f}%)")
