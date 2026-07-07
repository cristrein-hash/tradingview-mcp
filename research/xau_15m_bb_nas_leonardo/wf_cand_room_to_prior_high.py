#!/usr/bin/env python3
"""FILTRO MACRO-CONTEXTUAL CAUSAL: ROOM A RESISTENCIA PRIOR.

Hipotese: um LONG so vale a pena se tiver espaco ate a proxima resistencia REAL anterior
(swing-high CONFIRMADO ate a barra de decisao j). Se o preco em j ja esta encaixotado
imediatamente por baixo de um swing-high confirmado (room pequeno em ATR), a probabilidade
de bater 3R e menor (exaustao / falta de espaco). REJEITA room pequeno.

CAUSALIDADE:
  - Usa causal_swings_upto(j): swings cujo conf_bar<=j -> confirmados SO com barras <=j.
    Nenhuma confirmacao por movimento futuro (o zigzag do kit devolve conf_bar; filtramos <=j).
  - Preco de referencia = CL[j] (barra de decisao, indice j, permitido).
  - ATR[j] (barra j). Nenhuma janela LO[j:] / HI[j:] / last_t / out na feature.
  - ESTRUTURAL: o swing-high e um estado de trajetoria multi-barra (pivo confirmado por
    uma perna inteira), nao um valor snapshot isolado; escolhemos o swing-high confirmado
    mais proximo ACIMA de CL[j] = a primeira resistencia real que o preco enfrenta.

Feature por entry: room_atr = (nearest_conf_high_above - CL[j]) / ATR[j]
  Se NAO existe nenhum swing-high confirmado acima de CL[j] -> room = +inf (ceu-limpo, MANTEM).
Decisao: MANTEM se room_atr >= thr (espaco suficiente). REJEITA se encaixotado.
"""
import sys; sys.path.insert(0, "/Users/cristrein/tradingview-mcp/research/xau_15m_bb_nas_leonardo")
from agent_ctx_kit import S,TS,HI,LO,CL,ATR,EMA,RSI,N,ENTRIES,score,causal_swings_upto

INF = float("inf")
BASE = 52/96  # base hit-3R

def room_atr(e):
    j = e["j"]; px = CL[j]; a = ATR[j] or 5.0
    highs_above = [pr for (tp,i,pr,ci) in causal_swings_upto(j) if tp=="H" and pr > px]
    if not highs_above:
        return INF  # ceu-limpo acima: nenhuma resistencia confirmada
    nearest = min(highs_above)  # o swing-high confirmado mais proximo ACIMA
    return (nearest - px) / a

rooms = {e["n"]: room_atr(e) for e in ENTRIES}

# --- diagnostico da distribuicao winner vs loser ---
W = [rooms[e["n"]] for e in ENTRIES if e["out"]==1]
L = [rooms[e["n"]] for e in ENTRIES if e["out"]==0]
def med(x):
    x=sorted(v for v in x if v!=INF)
    return round(x[len(x)//2],2) if x else None
n_inf_W = sum(1 for v in W if v==INF); n_inf_L = sum(1 for v in L if v==INF)
print(f"[diag] winners: n={len(W)} inf(ceu-limpo)={n_inf_W} med_finito={med(W)}")
print(f"[diag] losers : n={len(L)} inf(ceu-limpo)={n_inf_L} med_finito={med(L)}")
fin = sorted(v for v in rooms.values() if v!=INF)
if fin:
    qs = [fin[int(q*(len(fin)-1))] for q in (0.1,0.25,0.5,0.75,0.9)]
    print("[diag] quantis room finito 10/25/50/75/90:", [round(q,2) for q in qs])

# --- varredura de thresholds ---
print("\n[sweep] MANTEM se room_atr >= thr:")
best=None
for thr in [0.5,0.75,1.0,1.25,1.5,1.75,2.0,2.5,3.0,4.0,5.0]:
    keep = {e["n"] for e in ENTRIES if rooms[e["n"]] >= thr}
    sc = score(keep)
    y25w,y25n = map(int, sc["y2025"].split("/")); y26w,y26n = map(int, sc["y2026"].split("/"))
    both_pos = y25w>0 and y26w>0 and y25n>0 and y26n>0
    ok = sc["N_kept"]>=20 and sc["poison_ratio"]<0.9 and sc["hit3r_kept"]>BASE and both_pos
    tag = " <== CANDIDATO" if ok else ""
    print(f" thr={thr:>4}: N={sc['N_kept']:>3} hit3r={sc['hit3r_kept']:.3f} "
          f"pois={sc['poison_ratio']:.2f} y25={sc['y2025']} y26={sc['y2026']} "
          f"Wcut={sc['winners_cut']} Lcut={sc['losers_cut']}{tag}")
    if ok:
        keyv=(sc["hit3r_kept"], sc["N_kept"])
        if best is None or keyv>best[0]:
            best=(keyv, thr, sc, keep)

print("\n" + "="*60)
if best:
    _, thr, sc, keep = best
    print(f"MELHOR CANDIDATO: thr={thr}")
    print("score:", sc)
    print("keep_ns:", sorted(keep))
else:
    print("NENHUM threshold passa (hit3r>base & poison<0.9 & ambos anos+ & N>=20).")
    print("Reportar HONESTO: a hipotese nao separa causalmente.")
