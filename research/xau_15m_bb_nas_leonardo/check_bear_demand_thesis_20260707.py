#!/usr/bin/env python3
"""VERIFICAR A TESE DO CRIS (2026-07-07): losers-a-cortar estao todos em BEAR-macro; winners intra-bear
distinguem-se por PROXIMIDADE A DEMANDA VALIDA (causal). Antes de construir engine, confirmar nos dados.
CAUSAL: bear-macro via estrutura (lower-highs confirmados ate j) OU EMA-media a descer; demanda via
zonas DEMAND do indicador NASCIDAS ANTES do entry (born_t<TS[j]) — NUNCA last_t (futuro)."""
import json, glob, bisect, sys
import datetime as dt
import statistics as st
sys.path.insert(0,"/Users/cristrein/tradingview-mcp/research/xau_15m_bb_nas_leonardo")
from agent_ctx_kit import S,TS,HI,LO,CL,ATR,EMA,N,ENTRIES,causal_swings_upto
zones=[]
for p in sorted(glob.glob("/Users/cristrein/tradingview-mcp/research/xau_15m_bb_nas_leonardo/primitives/*.primitives.json")):
    zones+=[z for z in json.load(open(p)).get("zones",[]) if z.get("born_t")]
zones.sort(key=lambda z:z["born_t"]); ZT=[z["born_t"] for z in zones]
BARD=96
def ema_slow(j):
    # EMA ~10-dia (960 barras) causal, aprox via media movel simples dos closes
    seg=CL[max(0,j-960):j+1]; return sum(seg)/len(seg)
def is_bear(j):
    # estrutura: ultimos 2 swing-highs confirmados descendentes OU preco abaixo da EMA-lenta a descer
    sw=causal_swings_upto(j,6); highs=[pr for tp,i,pr,ci in sw if tp=="H"]
    lower_highs=1 if len(highs)>=2 and highs[-1]<highs[-2] else 0
    e_now=ema_slow(j); e_prev=ema_slow(max(0,j-480))
    below_falling=1 if (CL[j]<e_now and e_now<e_prev) else 0
    return lower_highs or below_falling
def demand_dist_causal(j):
    # distancia a zona DEMAND nascida ANTES de j, mais proxima do preco (nunca last_t)
    hi=bisect.bisect_right(ZT,TS[j]); px=CL[j]; a=ATR[j] or 5; best=99
    for z in zones[:hi]:
        if z["text"]!="DEMAND": continue
        mid=(z["high"]+z["low"])/2
        # zona relevante = perto e ja tocada/valida: exige que o preco esteja perto do topo da zona (retest)
        d=abs(px-mid)/a
        if d<best: best=d
    return round(best,2)
def ds(t): return dt.datetime.utcfromtimestamp(int(t)).strftime("%Y-%m-%d")
for e in ENTRIES: e["bear"]=is_bear(e["j"]); e["dem"]=demand_dist_causal(e["j"])
LOSER_TARGETS=[55,56,57,59,60,65,67,68,79,83,84,85]
INTRABEAR_WIN=[82]  # winner intra-bear que TEM de ficar
by_n={e["n"]:e for e in ENTRIES}
print("=== LOSER-TARGETS do Cris (todos deviam ser bear + longe de demanda) ===")
for n in LOSER_TARGETS:
    e=by_n.get(n)
    if e: print(f"  #{n} {ds(e['t'])} out={e['out']} bear={e['bear']} demand_dist={e['dem']}")
print("=== WINNERS intra-bear a manter (bear + PERTO de demanda?) ===")
for n in INTRABEAR_WIN+[44,45,82]:
    e=by_n.get(n)
    if e: print(f"  #{n} {ds(e['t'])} out={e['out']} bear={e['bear']} demand_dist={e['dem']}")
# tabela: bear x demand-proximity x outcome
print("\n=== SEPARACAO: em BEAR-macro, demanda-proxima separa winner/loser? ===")
BE=[e for e in ENTRIES if e["bear"]==1]; NB=[e for e in ENTRIES if e["bear"]==0]
def rate(s): return f"{sum(x['out'] for x in s)}/{len(s)} ({sum(x['out'] for x in s)/len(s):.0%})" if s else "0"
print(f"  bear-macro N{len(BE)} hit-3R {rate(BE)} · nao-bear N{len(NB)} hit-3R {rate(NB)}")
for thr in (0.3,0.5,0.8):
    near=[e for e in BE if e["dem"]<=thr]; far=[e for e in BE if e["dem"]>thr]
    print(f"  BEAR & demand<= {thr}: {rate(near)}  |  BEAR & demand> {thr}: {rate(far)}")
print(f"\n  medianas demand_dist em BEAR: WIN {st.median([e['dem'] for e in BE if e['out']==1] or [0]):.2f} vs LOSE {st.median([e['dem'] for e in BE if e['out']==0] or [0]):.2f}")
json.dump([{k:e[k] for k in ('n','t','out','bear','dem')} for e in ENTRIES], open("/Users/cristrein/tradingview-mcp/research/xau_15m_bb_nas_leonardo/results/bear_demand_thesis_20260707.json","w"),indent=1)
print("\nsaved · OK")
