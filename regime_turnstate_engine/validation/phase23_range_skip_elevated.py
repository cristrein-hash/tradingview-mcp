#!/usr/bin/env python3
"""RECONCILIAÇÃO CRUA + filtro (Cris): por BOX RANGE do detector, cada trade ordenado por entry, distância acima da
DEMANDA-FUNDO do box, e R tal como PLOTADO (letrun raw, fonte da cor das long_positions). Sem métrica derivada.
Achado: no range 2025 a estratégia entrou TODAS no meio (>37% do range) = chasing = 13/15 losers; nunca na demanda.
Testa filtro SKIP-ELEVADO: descarta entradas acima de thr% do range. Mede losers cortados vs winners perdidos vs net.
box = segmento RANGE do phase10 (=o que foi plotado). CAVEAT: box_hi/lo é do segmento inteiro (demanda forma-se cedo=causal;
topo pode ser hindsight — por isso reporto tb dist em ATR vs running-min-so-far, que é 100% causal). R plotado = raw; net oficial −0.35."""
import json,bisect,io,contextlib,sys,datetime as dt
from pathlib import Path
VAL=Path("/Users/cristrein/tradingview-mcp/regime_turnstate_engine/validation");sys.path.insert(0,str(VAL))
with contextlib.redirect_stdout(io.StringIO()): import phase10_hybrid_regime as P
T=P.T;L=P.L;H=P.H;C=P.C
def atr(i,k=14): return sum(max(H[j]-L[j],abs(H[j]-C[j-1]),abs(L[j]-C[j-1])) for j in range(i-k+1,i+1))/k
segs=[s for s in json.load(open("/tmp/causal_segments_v10.json")) if s["regime"]=="RANGE"]
tp=json.load(open("/tmp/l2_base_trades_2023.json"))   # entry_time, entry, R (letrun raw, como plotado)
def enrich(t):
    box=None
    for s in segs:
        if s['start']<=t['entry_time']<=s['end']: box=s;break
    if not box: return None
    bi=bisect.bisect_right(T,t['entry_time'])-1
    i0=bisect.bisect_left(T,box['start']);rmin=min(L[i0:bi+1]);a=atr(bi)
    return {**t,"box":(box['d0'],box['d1']),"lo":box['lo'],"hi":box['hi'],
            "pct":100*(t['entry']-box['lo'])/(box['hi']-box['lo']),
            "dist_atr":(t['entry']-rmin)/a,"win":t['R']>0}
tr=[x for x in (enrich(t) for t in tp) if x]
print("="*88);print("FILTRO SKIP-ELEVADO — descarta entradas acima de thr% do range (mantém near-demanda)");print("="*88)
base_w=sum(1 for x in tr if x['win']);base_R=sum(x['R'] for x in tr)
print(f"  BASE (todos {len(tr)} range-trades): {base_w} win / {len(tr)-base_w} loss | sumR_plot {base_R:+.1f}")
print(f"  {'skip se %range >':>18}{'trades_mantidos':>16}{'losers_cortados':>16}{'winners_perdidos':>17}{'net_R_mantido':>14}")
for thr in [30,35,40,45,50]:
    keep=[x for x in tr if x['pct']<=thr];cut=[x for x in tr if x['pct']>thr]
    lc=sum(1 for x in cut if not x['win']);wl=sum(1 for x in cut if x['win'])
    print(f"  {thr:>16}%{len(keep):>16}{lc:>16}{wl:>17}{sum(x['R'] for x in keep):>+14.1f}")
print("\n  mesma coisa por DIST-ATR (causal, vs running-min-so-far):")
print(f"  {'skip se dist >':>18}{'trades_mantidos':>16}{'losers_cortados':>16}{'winners_perdidos':>17}{'net_R_mantido':>14}")
for thr in [2,3,4,5]:
    keep=[x for x in tr if x['dist_atr']<=thr];cut=[x for x in tr if x['dist_atr']>thr]
    lc=sum(1 for x in cut if not x['win']);wl=sum(1 for x in cut if x['win'])
    print(f"  {str(thr)+'ATR':>17}{len(keep):>16}{lc:>16}{wl:>17}{sum(x['R'] for x in keep):>+14.1f}")
print("\n-- os WINNERS que o filtro-de-posição mata (win mas pct alto) = os BREAKOUTS do fim do range --")
for x in sorted([z for z in tr if z['win']],key=lambda z:-z['pct'])[:8]:
    print(f"    {dt.datetime.utcfromtimestamp(x['entry_time']).strftime('%Y-%m-%d')} pct {x['pct']:.0f}% dist {x['dist_atr']:.1f}ATR R {x['R']:+.1f}")
# BOS-up: o close rompeu o topo do range estabelecido ANTES (breakout)? (causal)
def bos_up(t):
    bi=bisect.bisect_right(T,t['entry_time'])-1
    box=next(s for s in segs if s['start']<=t['entry_time']<=s['end']);i0=bisect.bisect_left(T,box['start'])
    if bi-3<=i0: return False
    prior_high=max(H[i0:bi-2])           # topo do range formado antes das últimas 3 barras
    return C[bi]>prior_high              # fechou acima = rompeu (breakout)
for x in tr: x['bos']=bos_up(x)
print("\n"+"="*88);print("FILTRO COMBINADO: skip se ELEVADO (pct>40) E SEM rompimento (BOS-up)");print("="*88)
def report(keep,cut,nm):
    kw=sum(1 for x in keep if x['win']);cw=sum(1 for x in cut if x['win']);cl=sum(1 for x in cut if not x['win'])
    print(f"  {nm:34} mantém N={len(keep)} ({kw}W/{len(keep)-kw}L) sumR={sum(x['R'] for x in keep):+6.1f} | corta {len(cut)} ({cl}L+{cw}W)")
report(tr,[],"BASE")
for thr in [35,40,45]:
    cut=[x for x in tr if x['pct']>thr and not x['bos']];keep=[x for x in tr if not (x['pct']>thr and not x['bos'])]
    report(keep,cut,f"skip pct>{thr}% & !BOS")
print("\n-- separação: elevado(pct>40) COM-BOS vs SEM-BOS --")
elev=[x for x in tr if x['pct']>40]
wb=[x for x in elev if x['bos']];nb=[x for x in elev if not x['bos']]
print(f"  elevado COM BOS-up (breakout): N={len(wb)} WR={100*sum(1 for x in wb if x['win'])/len(wb) if wb else 0:.0f}% sumR={sum(x['R'] for x in wb):+.1f}")
print(f"  elevado SEM BOS-up (chasing):  N={len(nb)} WR={100*sum(1 for x in nb if x['win'])/len(nb) if nb else 0:.0f}% sumR={sum(x['R'] for x in nb):+.1f}")
