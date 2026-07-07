#!/usr/bin/env python3
"""LEITURA CONTEXTUAL da FASE de exaustao-topo (2026-07-07) — ler, nao filtrar feature isolada.
Cris: #79/#83/#84/#85 = topos de exaustao a cortar; 19 winners cortados a recuperar; ler a FASE macro
real (nao feature causal isolada). Descrevo, CAUSALMENTE (barras<=j), a fase macro de cada trade com
MULTIPLOS cues integrados que caracterizam 'distribuicao/topo esticado' vs 'perna fresca jovem':
  - failed_high: ultimo swing-high confirmado e LOWER-high vs o anterior (falhou novo maximo = topo).
  - choch_down: preco fechou ABAIXO do ultimo higher-low confirmado (estrutura quebrou p/ baixo).
  - bars_since_newHigh: barras desde novo maximo de 192b (grande = estagnado no topo).
  - overlap_top: fracao das ultimas 48 barras no terco SUPERIOR do range recente (distribuicao no topo).
  - leg_pushes: nº de higher-highs confirmados desde o ultimo swing-low grande (idade da perna em empurroes).
  - dist_major_low: (preco - min low 480b)/ATR-dia (quanto a perna macro ja subiu).
Imprime lado-a-lado os 4 topos-exaustao, os winners cortados pelo ER, e medianas W vs L — para LER.
SANITY_PROBE: leitura contextual multi-fatorial da FASE macro (nao feature isolada); cues integrados;
trajetoria multi-barra; causal barras<=j; markup master; dois objetivos (cortar topo + manter winner)."""
import json, glob, bisect, sys
import datetime as dt
import statistics as st
sys.path.insert(0,"/Users/cristrein/tradingview-mcp/research/xau_15m_bb_nas_leonardo")
from agent_ctx_kit import S,TS,HI,LO,CL,ATR,EMA,N,ENTRIES,causal_swings_upto
BARD=96
def daily_atr_at(j):
    # ATR-dia aprox = ATR 15M * sqrt? nao; uso range dos ultimos ~5 dias / 5
    seg=[HI[k]-LO[k] for k in range(max(0,j-5*BARD),j+1)]
    return (max(HI[max(0,j-BARD):j+1])-min(LO[max(0,j-BARD):j+1])) or (ATR[j] or 5)
def phase(j):
    a=ATR[j] or 5; px=CL[j]
    sw=causal_swings_upto(j,6)
    highs=[pr for tp,i,pr,ci in sw if tp=="H"]; lows=[(i,pr) for tp,i,pr,ci in sw if tp=="L"]
    failed_high=1 if len(highs)>=2 and highs[-1]<highs[-2] else 0
    # choch_down: fechou abaixo do ultimo higher-low confirmado
    hl=None
    if len(lows)>=2:
        for m in range(len(lows)-1,0,-1):
            if lows[m][1]>lows[m-1][1]: hl=lows[m][1]; break
    choch_down=1 if (hl is not None and px<hl-0.1*a) else 0
    # bars since new 192b high
    hi_idx=max(range(max(0,j-192),j+1), key=lambda k:HI[k]); bars_since_newHigh=j-hi_idx
    # overlap no topo: fracao das ultimas 48 barras no terco superior do range de 48b
    seg_hi=max(HI[max(0,j-48):j+1]); seg_lo=min(LO[max(0,j-48):j+1]); rng=(seg_hi-seg_lo) or 1
    top3=sum(1 for k in range(max(0,j-48),j+1) if (CL[k]-seg_lo)/rng>=0.66)/min(49,j+1)
    # leg pushes: higher-highs consecutivos confirmados
    pushes=0
    for m in range(len(highs)-1,0,-1):
        if highs[m]>highs[m-1]: pushes+=1
        else: break
    lo480=min(LO[max(0,j-480):j+1]); dist_major_low=(px-lo480)/a
    return {"failed_high":failed_high,"choch_down":choch_down,"bars_since_newHigh":bars_since_newHigh,
            "overlap_top":round(top3,2),"leg_pushes":pushes,"dist_major_low":round(dist_major_low,1)}
by_n={e["n"]:e for e in ENTRIES}
def ds(t): return dt.datetime.utcfromtimestamp(int(t)).strftime("%Y-%m-%d")
for e in ENTRIES: e.update(phase(e["j"]))
EXH=[79,83,84,85]
CUT_W=[11,29,44,45,82]  # winners conhecidos cortados pelo ER
print("=== 4 TOPOS DE EXAUSTAO (cortar) ===")
for n in EXH:
    e=by_n.get(n)
    if e: print(f"  #{n} {ds(e['t'])} out={e['out']} failed_high={e['failed_high']} choch_down={e['choch_down']} since_newHi={e['bars_since_newHigh']} overlap_top={e['overlap_top']} pushes={e['leg_pushes']} dist_low={e['dist_major_low']}")
print("=== WINNERS DE MARKUP cortados pelo ER (recuperar) ===")
for n in CUT_W:
    e=by_n.get(n)
    if e: print(f"  #{n} {ds(e['t'])} out={e['out']} failed_high={e['failed_high']} choch_down={e['choch_down']} since_newHi={e['bars_since_newHigh']} overlap_top={e['overlap_top']} pushes={e['leg_pushes']} dist_low={e['dist_major_low']}")
W=[e for e in ENTRIES if e["out"]==1]; L=[e for e in ENTRIES if e["out"]==0]
print("\n=== medianas WINNER vs LOSER (todos 96) ===")
for k in ("failed_high","choch_down","bars_since_newHigh","overlap_top","leg_pushes","dist_major_low"):
    print(f"  {k:<18} WIN {st.median([e[k] for e in W]):.2f}  LOSE {st.median([e[k] for e in L]):.2f}")
json.dump([{k:e[k] for k in ('n','t','out','failed_high','choch_down','bars_since_newHigh','overlap_top','leg_pushes','dist_major_low')} for e in ENTRIES],
          open("/Users/cristrein/tradingview-mcp/research/xau_15m_bb_nas_leonardo/results/exhaustion_phase_20260707.json","w"),indent=1)
print("\nsaved · OK")
