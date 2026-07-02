#!/usr/bin/env python3
"""Análise detalhada do B10 (2026-01-12) com os SL/TP ajustados manualmente pelo Cris (extraídos via MCP).
Compara SL original (zona) vs SL Cris; TP original vs TP Cris. Mostra o que o preço fez desde a entrada
(min low, max high, close atual, data do último bar), se/quando stopa, R mark-to-market, MAE/MFE, e o swing-low
do reteste (p/ julgar se o SL do Cris é estrutural ou colado ao wick)."""
import json,io,contextlib,sys,bisect,datetime as dt
from pathlib import Path
MT=0.01;COST=0.35
VAL=Path("/Users/cristrein/tradingview-mcp/regime_turnstate_engine/validation");sys.path.insert(0,str(VAL))
with contextlib.redirect_stdout(io.StringIO()): import phase10_hybrid_regime as P
reg=P.run(0.03,1.15,0.88);T=P.T;H=P.H;L=P.L;C=P.C;n4=len(C)
def atr(i,k=14): return sum(max(H[j]-L[j],abs(H[j]-C[j-1]),abs(L[j]-C[j-1])) for j in range(i-k+1,i+1))/k
et=1768230000;entry=4610.77
bi=bisect.bisect_left(T,et)
a=atr(bi)
sl_orig=entry-13573*MT   # original plotado (zona-bottom−0.5ATR)
sl_cris=entry-11576*MT   # ajuste manual Cris
tp_orig=entry+6787*MT
tp_cris=entry+94880*MT
swing=min(L[bi-4:bi+1])  # swing-low do reteste (janela recente)
print(f"B10 entry {dt.datetime.utcfromtimestamp(T[bi]).strftime('%Y-%m-%d %Hh')}  bar_idx={bi}  ATR={a:.1f}")
print(f"  último bar dos dados: {dt.datetime.utcfromtimestamp(T[n4-1]).strftime('%Y-%m-%d')}  (bar {n4-1}, {n4-1-bi} barras após entry)\n")
print(f"  SL original (zona)  {sl_orig:8.2f}  risk {entry-sl_orig:6.2f} ({100*(entry-sl_orig)/entry:.2f}%)")
print(f"  SL Cris (ajuste)    {sl_cris:8.2f}  risk {entry-sl_cris:6.2f} ({100*(entry-sl_cris)/entry:.2f}%)  -> {'APERTOU' if sl_cris>sl_orig else 'ALARGOU'} {abs(sl_cris-sl_orig):.1f}pts")
print(f"  swing-low reteste   {swing:8.2f}  (SL Cris está {sl_cris-swing:+.1f}pts vs swing-low)")
print(f"  TP original         {tp_orig:8.2f}  ({6787/13573:.1f}R)")
print(f"  TP Cris             {tp_cris:8.2f}  ({94880/11576:.1f}R)  -> alvo +{tp_cris-entry:.0f}pts (+{100*(tp_cris-entry)/entry:.1f}%)\n")
# o que o preço fez
end=n4-1;risk=entry-sl_cris
lows=[L[j] for j in range(bi+1,end+1)];highs=[H[j] for j in range(bi+1,end+1)]
minlo=min(lows);maxhi=max(highs);jmin=bi+1+lows.index(minlo);jmax=bi+1+highs.index(maxhi)
stop_cris=next((j for j in range(bi+1,end+1) if L[j]<=sl_cris),None)
stop_orig=next((j for j in range(bi+1,end+1) if L[j]<=sl_orig),None)
hit_tp=next((j for j in range(bi+1,end+1) if H[j]>=tp_cris),None)
print(f"  desde a entrada até hoje:")
print(f"    min low  {minlo:8.2f} em {dt.datetime.utcfromtimestamp(T[jmin]).strftime('%Y-%m-%d')}  (MAE {(minlo-entry)/risk:+.2f}R)")
print(f"    max high {maxhi:8.2f} em {dt.datetime.utcfromtimestamp(T[jmax]).strftime('%Y-%m-%d')}  (MFE {(maxhi-entry)/risk:+.2f}R)")
print(f"    close atual {C[end]:8.2f}  (R mark-to-market {(C[end]-entry)/risk-COST:+.2f}R, NÃO realizado)")
print(f"    SL Cris tocado? {'SIM em '+dt.datetime.utcfromtimestamp(T[stop_cris]).strftime('%Y-%m-%d') if stop_cris else 'NÃO'}")
print(f"    SL orig tocado? {'SIM em '+dt.datetime.utcfromtimestamp(T[stop_orig]).strftime('%Y-%m-%d') if stop_orig else 'NÃO'}")
print(f"    TP Cris (5559) atingido? {'SIM' if hit_tp else 'NÃO — falta '+f'{tp_cris-maxhi:.0f}pts'}")
print(f"\n  margem SL Cris vs min-low real: {minlo-sl_cris:+.1f}pts (se pequena e positiva = SL colado ao fundo que já aconteceu=hindsight)")
