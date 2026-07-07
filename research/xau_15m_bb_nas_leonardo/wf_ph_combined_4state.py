#!/usr/bin/env python3
"""wf_ph_combined_4state.py — CLASSIFICADOR DE FASE DO CICLO (maquina de 4 estados A/B/C/D)
para o engine 3R XAU 15M LONG.  CAUSAL: cada feature usa SO barras indice <= j (barra de decisao).

LEITURA-ALVO:
  KEEP = A (MARKUP ATIVO: higher-highs, estrutura sobe, entrada FUNDA no pullback, nao chase)
         UNIAO B (INICIACAO: flush fresco a demanda + reclaim RAPIDO = CHoCH-up, nova perna comeca).
  CUT  = C (DISTRIBUICAO-TOPO: reclaim lento/grind na zona, markup sem push, chase perto do topo)
         UNIAO D (BEAR-ATIVO: lower-highs consecutivos / BOS-down).

3 SUB-ESTADOS CAUSAIS integrados por entry (funcao SO da estrutura em j):
  (1) DIRECAO da estrutura   -> highs confirmados via causal_swings_upto(j): lower-highs => D (bear)
  (2) FLUSH-FRESCO/RECLAIM   -> reclaim_lag = barras demanda->CHoCH-up; rapido (<=4) => B (iniciacao)
  (3) PUSH-COUNT + POSICAO   -> higher-highs consecutivos desde a origem + entrada funda vs topo => A

Regra dura: NUNCA usa e['out'] nem os numeros-alvo na LOGICA. score() so LE o resultado.
Variante escolhida por metrica (hit3r alto & poison<0.9 & ambos anos>50% & N>=20), nao por lista-alvo.
"""
import sys; sys.path.insert(0,"/Users/cristrein/tradingview-mcp/research/xau_15m_bb_nas_leonardo")
from agent_ctx_kit import (S,TS,HI,LO,CL,ATR,EMA,RSI,N,ENTRIES,score,causal_swings_upto)
from collections import Counter

# ---------- FEATURES CAUSAIS (so barras <= j) ----------
def causal_feats(e):
    j=e["j"]; i=e["i"]; a=ATR[i] or 5.0
    sw=causal_swings_upto(j)                       # swings confirmados ate j (CAUSAL, conf_bar<=j)
    Hs=[(idx,pr) for tp,idx,pr,ci in sw if tp=="H"]
    Ls=[(idx,pr) for tp,idx,pr,ci in sw if tp=="L"]
    f={}
    # (1) DIRECAO: dois lower-highs consecutivos = bear ativo
    f["lh2"]=1 if (len(Hs)>=3 and Hs[-1][1]<Hs[-2][1]<Hs[-3][1]) else 0
    # (3) PUSH-COUNT: higher-highs consecutivos desde o ultimo desvio (markup vivo)
    push=0
    for k in range(len(Hs)-1,0,-1):
        if Hs[k][1]>Hs[k-1][1]: push+=1
        else: break
    f["push"]=push
    # POSICAO da entrada vs ultimo high confirmado: funda (<<0) = pullback real, nao chase de topo
    f["ent_vs_H"]=(e["ent"]-Hs[-1][1])/a if Hs else 0.0
    # (2) FLUSH-FRESCO: rapidez do reclaim (demanda -> CHoCH-up). Curto = V-flush genuina.
    f["reclaim"]=e["reclaim_lag"]
    # profundidade do pullback (contexto do flush)
    f["depth"]=(e["leg_top"]-e["demand_low"])/a
    return f

FE={e["n"]:causal_feats(e) for e in ENTRIES}

# ---------- MAQUINA DE 4 ESTADOS (atribuicao por PRIORIDADE) ----------
# Parametros da variante selecionada por metrica:
P=dict(b_reclaim=4, a_push=2, a_entpos=-4.0)

def classify(e):
    f=FE[e["n"]]
    # B  INICIACAO: flush fresco + reclaim rapido (CHoCH-up). Populacao mais limpa de winners.
    if f["reclaim"] <= P["b_reclaim"]:
        return "B"
    # D  BEAR-ATIVO: lower-highs consecutivos (so relevante quando NAO houve V-flush recente).
    if f["lh2"] == 1:
        return "D"
    # A  MARKUP ATIVO: >=2 higher-highs consecutivos E entrada FUNDA (nao chase de topo).
    if f["push"] >= P["a_push"] and f["ent_vs_H"] < P["a_entpos"]:
        return "A"
    # C  DISTRIBUICAO-TOPO: reclaim lento, sem push, ou chase perto do topo -> resto.
    return "C"

PH={e["n"]:classify(e) for e in ENTRIES}
KEEP=sorted(n for n,p in PH.items() if p in ("A","B"))   # KEEP = A uniao B

# ---------- SCORE REAL ----------
SC=score(KEEP)
print("=== 4-STATE PHASE MACHINE — score REAL ===")
print("P =", P)
print("dist fases:", dict(Counter(PH.values())))
print("score =", SC)

# ---------- SANITY-CHECK post-hoc (NAO usado na logica) ----------
loser_targets=set([21,23,31,49,50,55,56,57,59,60,65,66,67,68,69,79,83,84,85,89,93,94])
winner_keys=set([1,11,12,13,14,26,28,29,30,44,45,61,62,63,71,72,73,74,75,82,95,96])
keepset=set(KEEP)
lt_cut=sorted(n for n in loser_targets if n not in keepset)   # loser-targets CORTADOS (bom)
wk_kept=sorted(n for n in winner_keys if n in keepset)        # winners-chave MANTIDOS (bom)
print("\n=== SANITY-CHECK post-hoc ===")
print(f"loser-targets cortados: {len(lt_cut)}/{len(loser_targets)}  {lt_cut}")
print(f"winners-chave mantidos: {len(wk_kept)}/{len(winner_keys)}  {wk_kept}")
print("fase/loser-target:", {n:PH[n] for n in sorted(loser_targets)})
print("fase/winner-key:  ", {n:PH[n] for n in sorted(winner_keys)})
print("\nKEEP_NS =", KEEP)
