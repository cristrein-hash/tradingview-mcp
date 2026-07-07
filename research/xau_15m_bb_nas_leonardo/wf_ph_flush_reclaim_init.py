#!/usr/bin/env python3
"""FASE B — INICIACAO por FLUSH + VARREDURA + RECLAIM (classificador de fase do ciclo).

Hipotese: uma entrada boa (Fase B = iniciacao fresca) nasce quando a DEMANDA (low i) foi
um FLUSH GENUINO — uma perna de queda real ATE ao low — que VARREU liquidez (fez minimo
abaixo do minimo recente = sweep) e foi RECLAIMED RAPIDO (o mercado absorveu e voltou depressa
= CHoCH-up). Pullbacks rasos/drift e flush-outs profundos que ficam a arrastar (distribuicao-topo
/ bear-ativo) NAO tem esta assinatura -> CUT.

TODAS as features usam SO barras indice<=j (CAUSAL). O sweep/flush olham a perna que TERMINA
no low i (i<=j sempre). O reclaim_lag=j-i ja e causal. NUNCA se usa e['out'] nem os n-alvo.
"""
import sys; sys.path.insert(0,"/Users/cristrein/tradingview-mcp/research/xau_15m_bb_nas_leonardo")
from agent_ctx_kit import S,TS,HI,LO,CL,ATR,EMA,RSI,N,ENTRIES,score,causal_swings_upto

def feats(e):
    """Features CAUSAIS da assinatura de iniciacao. So barras <= j (o low i<=j)."""
    i=e['i']; j=e['j']; lo=e['demand_low']; a=ATR[i] or 5.0
    # FLUSH: perna de queda que termina no low i. Max high nas ultimas K barras ate i, drop ate lo.
    K=8
    seg=range(max(0,i-K),i+1)
    mh=max(HI[k] for k in seg)
    mhi=max(seg,key=lambda k:HI[k])
    drop_atr=(mh-lo)/a          # profundidade da perna de flush em ATR
    span=i-mhi                  # quao rapido caiu (barras do topo local ao low) -> velocidade
    # VARREDURA (sweep): low i fez minimo abaixo do minimo das M barras anteriores
    M=12
    prior=[LO[k] for k in range(max(0,i-M),i)]
    priormin=min(prior) if prior else lo
    swept = lo < priormin
    sweep_depth=(priormin-lo)/a  # quao fundo varreu; fundo demais = flush-out bear (mau)
    # RECLAIM: velocidade da recuperacao ate o gatilho j (CHoCH-up rapido)
    rl=e['reclaim_lag']
    # CONTEXTO DE FASE (causal, swings confirmados <=j): distribuicao-topo / bear vs iniciacao
    sw=causal_swings_upto(j)
    Hs=[pr for tp,idx,pr,ci in sw if tp=='H']; Ls=[pr for tp,idx,pr,ci in sw if tp=='L']
    slope=(EMA[j]-EMA[j-6])/a if (EMA[j] is not None and j>=6 and EMA[j-6] is not None) else 0.0
    rngpos=0.5
    if Hs and Ls and Hs[-1]>Ls[-1]: rngpos=(CL[j]-Ls[-1])/(Hs[-1]-Ls[-1])
    return dict(drop_atr=drop_atr, span=span, swept=swept, sweep_depth=sweep_depth, rl=rl,
                slope=slope, rngpos=rngpos)

F={e['n']:feats(e) for e in ENTRIES}

def classify(DR, RL, SDmax, SDmin, require_swept, speed_max, veto_slope, veto_rngpos):
    """KEEP = assinatura de iniciacao fresca:
       flush real (drop>=DR ATR) + varreu (opcional) + sweep CONTROLADO (SDmin<=depth<=SDmax)
       + reclaim RAPIDO (rl<=RL) + queda razoavelmente rapida (span<=speed_max).
       VETO DISTRIBUICAO/BEAR: corta se EMA a descer forte (slope<=veto_slope) E preco a fazer
       chase perto do topo do range causal (rngpos>=veto_rngpos) = markup exausto / bear-ativo,
       NAO iniciacao fresca. (reclaim rapido rl<=2 = iniciacao inequivoca, isento do veto.)"""
    keep=set()
    for e in ENTRIES:
        f=F[e['n']]
        if f['drop_atr'] < DR: continue
        if require_swept and not f['swept']: continue
        if not (SDmin <= f['sweep_depth'] <= SDmax): continue
        if f['rl'] > RL: continue
        if f['span'] > speed_max: continue
        if f['rl'] > 2 and f['slope'] <= veto_slope and f['rngpos'] >= veto_rngpos: continue
        keep.add(e['n'])
    return keep

if __name__=="__main__":
    grid=[]
    for DR in [0.0,1.5,2.0,2.5]:
        for RL in [3,4,5,6]:
            for SDmax in [0.6,0.9,9.9]:
                for SDmin in [-9.9]:
                    for req in [False]:
                        for spd in [99]:
                            for vsl in [99.0,-0.4,-0.55,-0.7]:      # 99=veto off
                                for vrp in [0.6,0.65,0.7,0.75]:
                                    keep=classify(DR,RL,SDmax,SDmin,req,spd,vsl,vrp)
                                    if len(keep)<20: continue
                                    sc=score(keep)
                                    y25=[int(x) for x in sc['y2025'].split('/')]
                                    y26=[int(x) for x in sc['y2026'].split('/')]
                                    posyrs = y25[0] > (y25[1]-y25[0]) and y26[0] > (y26[1]-y26[0])
                                    grid.append((sc['hit3r_kept'],sc['poison_ratio'],sc['N_kept'],posyrs,
                                                 DR,RL,SDmax,SDmin,req,spd,sc,vsl,vrp))
    # filter valid: poison<0.9, both years +, N>=20
    valid=[g for g in grid if g[1]<0.9 and g[3] and g[2]>=20]
    # SELECAO ROBUSTA: entre as que passam os gates, escolhe a de melhor hit3r_kept
    # DENTRO das que cortam losers com folga (poison<=0.82). Isto favorece separacao real,
    # nao winner's-curse de hit3r com poison colado em 0.9. (nenhum n-alvo entra nesta escolha.)
    strong=[g for g in valid if g[1]<=0.82]
    pool=strong if strong else valid
    pool.sort(key=lambda g:(g[0], g[2]), reverse=True)
    print("=== TOP VALID (poison<0.9, ambos anos+, N>=20) — pool de selecao robusta poison<=0.82 ===")
    for g in pool[:10]:
        print(f"hit3r={g[0]:.3f} poison={g[1]:.2f} N={g[2]} | DR={g[4]} RL={g[5]} SDmax={g[6]} vrng={g[12]} | {g[10]['y2025']} {g[10]['y2026']}")
    b=pool[0]
    best=classify(b[4],b[5],b[6],b[7],b[8],b[9],b[11],b[12])
    print(f"\n=== BEST CONFIG === DR={b[4]} RL={b[5]} SDmax={b[6]} SDmin={b[7]} req_swept={b[8]} spd={b[9]} veto_slope={b[11]} veto_rngpos={b[12]}")
    print("=== BEST SCORE ===", score(best))
    loser_targets=[21,23,31,49,50,55,56,57,59,60,65,66,67,68,69,79,83,84,85,89,93,94]
    winners_key=[1,11,12,13,14,26,28,29,30,44,45,61,62,63,71,72,73,74,75,82,95,96]
    lt_cut=[n for n in loser_targets if n not in best]
    wk_keep=[n for n in winners_key if n in best]
    print(f"SANITY loser-targets CAIDOS: {len(lt_cut)}/{len(loser_targets)} -> {sorted(lt_cut)}")
    print(f"SANITY winners-chave MANTIDOS: {len(wk_keep)}/{len(winners_key)} -> {sorted(wk_keep)}")
    print("KEEP_NS=",sorted(best))
