#!/usr/bin/env python3
"""Cris quer adicionar o TRADE DE CAPITULAÇÃO BEAR (monumental) à V2. Fixar QUAL e medir HONESTO (sem SL inflado).
Região da capitulação de out/2023 (set→nov). Mede o trade de fundo com SL ESTRUTURAL (fundo real − 1 ATR), não o
SL de 5pts que inflou o +26R no V3. Entradas candidatas: (A) V3 BEAR-capit 2023-09-28; (B) fundo confirmado pós-mínimo.
Exits: V2-curto (target+3R/12b) vs let-run HZ120. Dá o R real p/ o Cris escolher — sem fabricar."""
import json,io,contextlib,sys,bisect,datetime as dt
from pathlib import Path
COST=0.35;HZ=120
VAL=Path("/Users/cristrein/tradingview-mcp/regime_turnstate_engine/validation");sys.path.insert(0,str(VAL))
with contextlib.redirect_stdout(io.StringIO()): import phase10_hybrid_regime as P
reg=P.run(0.03,1.15,0.88);T=P.T;H=P.H;L=P.L;C=P.C;n4=len(C)
def atr(i,k=14): return sum(max(H[j]-L[j],abs(H[j]-C[j-1]),abs(L[j]-C[j-1])) for j in range(i-k+1,i+1))/k
def ex_short(bi,entry,sl):
    risk=entry-sl;tgt=entry+3*risk;end=min(bi+12,n4-1)
    for j in range(bi+1,end+1):
        if L[j]<=sl: return -1.0
        if H[j]>=tgt: return 3.0
    return (C[end]-entry)/risk
def ex_letrun(bi,entry,sl,hz=HZ):
    risk=entry-sl;end=min(bi+hz,n4-1)
    for j in range(bi+1,end+1):
        if L[j]<=sl: return -1.0
    return (C[end]-entry)/risk
# janela da capitulação out/2023
lo_win=bisect.bisect_left(T,int(dt.datetime(2023,9,1).timestamp()))
hi_win=bisect.bisect_left(T,int(dt.datetime(2023,11,15).timestamp()))
botj=min(range(lo_win,hi_win),key=lambda j:L[j])  # barra do fundo real
print(f"FUNDO REAL da capitulação out/2023: {dt.datetime.utcfromtimestamp(T[botj]).strftime('%Y-%m-%d')} low={L[botj]:.2f}\n")
# SL estrutural comum = fundo real − 1 ATR(no fundo)
sl_struct=L[botj]-atr(botj)
# entrada A: V3 BEAR-capit 2023-09-28 (entry no toque zona profunda)
jA=bisect.bisect_left(T,int(dt.datetime(2023,9,28).timestamp()))
# entrada B: 1ª barra que FECHA acima do fundo+0.5ATR depois do fundo (fundo confirmado)
jB=next((j for j in range(botj+1,hi_win) if C[j]>L[botj]+0.5*atr(botj)),botj+1)
for tag,j in (("A: BEAR-capit 2023-09-28",jA),("B: fundo-confirmado",jB)):
    entry=C[j];risk=entry-sl_struct
    d=dt.datetime.utcfromtimestamp(T[j]).strftime('%Y-%m-%d')
    if risk<=0: print(f"{tag}: entry {entry:.2f} abaixo do SL — inválido");continue
    rs=round(ex_short(j,entry,sl_struct)-COST,2)
    rl=round(ex_letrun(j,entry,sl_struct)-COST,2)
    rl200=round(ex_letrun(j,entry,sl_struct,200)-COST,2)
    print(f"{tag:26} entry {d} {entry:8.2f} | SL_estrut {sl_struct:.2f} risco {risk:5.1f} | "
          f"R V2-curto {rs:+6.2f} | R let-run120 {rl:+6.2f} | let-run200 {rl200:+6.2f}")
print(f"\nComparar: V3 dava +26.2R nesse fundo MAS com SL 5pts (inflado). Aqui SL estrutural honesto (~{atr(botj):.0f}pts).")
print("Peak pós-fundo:",f"{max(H[botj:botj+200]):.2f}",f"(+{(max(H[botj:botj+200])-L[botj]):.0f} pts do fundo)")
