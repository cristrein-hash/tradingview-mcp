#!/usr/bin/env python3
"""DIAGNÓSTICO: preço diário + EMAs + label-Cris vs label-detector(v3) em torno das 6 fronteiras de regime.
Mostra onde divergem e se o PREÇO justifica (causal) ou se é marcação a-partir-do-topo (hindsight)."""
import json,datetime as dt
from pathlib import Path
HERE=Path(__file__).parent
Z=json.loads((HERE/"regime_zones_cris.json").read_text())
PRIM=[json.loads(p.read_text()) for p in sorted((HERE/"primitives").glob("*.primitives.json"))]
bars={}
for pr in PRIM:
    for b in pr["series"]: bars.setdefault(b["t"],b)
T15=sorted(bars); days={}
for t in T15:
    b=bars[t]; k=t//86400; g=days.setdefault(k,{"o":b["o"],"h":b["h"],"l":b["l"],"c":b["c"]})
    g["h"]=max(g["h"],b["h"]); g["l"]=min(g["l"],b["l"]); g["c"]=b["c"]
DK=sorted(days); DC=[days[k]["c"] for k in DK]; DH=[days[k]["h"] for k in DK]; DL=[days[k]["l"] for k in DK]
def ema_at(i,n):
    c=DC[max(0,i-3*n):i+1]; k=2/(n+1); e=c[0]
    for v in c[1:]: e=v*k+e*(1-k)
    return e
E20=[ema_at(i,20) for i in range(len(DK))]; E50=[ema_at(i,50) for i in range(len(DK))]; E100=[ema_at(i,100) for i in range(len(DK))]
def cris_at(t):
    for z in Z:
        if z["t_start"]<=t<=z["t_end"]: return z["type"]
    return "-"
def d(k): return dt.datetime.utcfromtimestamp(k*86400).strftime("%Y-%m-%d")
# imprime ±8 dias em torno de cada fronteira (t_start das zonas 2..6)
print("data        close   E20    E50    E100   |Cris")
for z in Z[1:]:
    bi=min(range(len(DK)),key=lambda i:abs(DK[i]*86400+43200-z["t_start"]))
    print(f"--- fronteira p/ {z['type']} em {z['start'][:10]} ---")
    for i in range(max(0,bi-6),min(len(DK),bi+7)):
        t=DK[i]*86400+43200
        print(f"{d(DK[i])}  {DC[i]:>7.0f} {E20[i]:>6.0f} {E50[i]:>6.0f} {E100[i]:>6.0f}  |{cris_at(t)}")
