#!/usr/bin/env python3
"""Precisão: simula B3/B4/B6 com os SL/TP EXATOS do chart (extraídos via MCP) e HORIZONTE LONGO (até TP ou SL, sem cap
de 120 barras) — a tese do Cris é LONG RUN (trades de meses até o TP estrutural). Reporta resultado, R, data de saída,
barras, MFE. custo 0.35."""
import io,contextlib,sys,bisect,datetime as dt
from pathlib import Path
MT=0.01;COST=0.35
VAL=Path("/Users/cristrein/tradingview-mcp/regime_turnstate_engine/validation");sys.path.insert(0,str(VAL))
with contextlib.redirect_stdout(io.StringIO()): import phase10_hybrid_regime as P
reg=P.run(0.03,1.15,0.88);T=P.T;H=P.H;L=P.L;C=P.C;n4=len(C)
# (tag, entry_time, entry, SL_ticks, TP_ticks) — exatos do chart
TR=[
 ("B3",1698141600,1964.48, 4706, 31073),
 ("B4",1712570400,2327.38, 2739,  9233),
 ("B6",1721340000,2426.15,14554,102690),
]
print(f"{'#':4}{'entry':9}{'SL':9}{'TP':9}{'R:R':6}{'result':9}{'Rreal':8}{'saída':12}{'meses':6}{'MFE_R':7}")
for tag,et,entry,slt,tpt in TR:
    bi=bisect.bisect_left(T,et);sl=entry-slt*MT;tp=entry+tpt*MT;risk=entry-sl;rr=tpt/slt
    res=None;rj=None;mfe=0
    for j in range(bi+1,n4):
        mfe=max(mfe,(H[j]-entry)/risk)
        if L[j]<=sl: res="SL";Rr=-1.0;rj=j;break
        if H[j]>=tp: res="TP";Rr=rr;rj=j;break
    if res is None: res="ABERTO";Rr=(C[n4-1]-entry)/risk;rj=n4-1
    d=dt.datetime.utcfromtimestamp(T[rj]).strftime("%Y-%m-%d");mo=(T[rj]-et)/86400/30
    print(f"{tag:4}{entry:9.2f}{sl:9.2f}{tp:9.2f}{rr:6.2f}{res:9}{Rr-COST:+8.2f}{d:12}{mo:5.1f}m{mfe:+7.2f}")
print("\n(horizonte LONGO = deixa o trade correr meses até TP ou SL, como a tese de long-run do Cris. R:R = alvo/risco do setup dele.)")
