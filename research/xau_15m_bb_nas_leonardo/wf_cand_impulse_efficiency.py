#!/usr/bin/env python3
"""FILTRO MACRO-CONTEXTUAL CAUSAL — QUALIDADE DE IMPULSO DA PERNA ANTERIOR.

Hipotese: a perna de alta ANTES do pullback (do ultimo higher-low CONFIRMADO ate o
leg_top, ambos passados) foi impulsiva/limpa (alta eficiencia direcional, poucos
overlaps) vs choppy. MANTEM pullbacks de pernas impulsivas.

CAUSALIDADE:
  - leg_top e leg_start vem de causal_swings_upto(j): so swings CONFIRMADOS ate a
    barra j (conf_bar<=j). Nenhum depende de movimento futuro alem de j.
  - A eficiencia usa SO closes CL[start..top], todos com indice < i < j (a perna
    inteira acontece ANTES da demand-low e da barra de decisao). Zero look-ahead.
  - Nao usa e['out'] na decisao; out so entra no score().
  - Estrutural: eficiencia = trajetoria multi-barra da perna (Kaufman efficiency
    ratio = net move / soma dos passos), nao um snapshot de uma barra.
"""
import sys; sys.path.insert(0, "/Users/cristrein/tradingview-mcp/research/xau_15m_bb_nas_leonardo")
from agent_ctx_kit import S,TS,HI,LO,CL,ATR,EMA,RSI,N,ENTRIES,score,causal_swings_upto

def leg_efficiency(e):
    """Devolve (ER, n_bars, leg_start_idx, leg_top_idx) CAUSAL, ou None se indefinido."""
    j=e["j"]; i=e["i"]; leg_top_price=e["leg_top"]
    sw=causal_swings_upto(j)
    # Encontra o swing H (leg_top) confirmado: ultimo H com idx <= i (antes do pullback)
    # que case com o leg_top_price (mesma perna que gerou o entry).
    top=None
    for k in range(len(sw)-1,-1,-1):
        tp,idx,pr,ci=sw[k]
        if tp=="H" and idx<=i and abs(pr-leg_top_price)<1e-6:
            top=k; break
    if top is None:
        # fallback: ultimo H confirmado com idx<=i
        for k in range(len(sw)-1,-1,-1):
            tp,idx,pr,ci=sw[k]
            if tp=="H" and idx<=i: top=k; break
    if top is None: return None
    top_idx=sw[top][1]
    # swing L imediatamente antes do topo = inicio do impulso (higher-low)
    start_idx=None
    for k in range(top-1,-1,-1):
        if sw[k][0]=="L":
            start_idx=sw[k][1]; break
    if start_idx is None or start_idx>=top_idx: return None
    # Kaufman efficiency ratio sobre closes da perna (tudo <= top_idx <= i < j)
    net=abs(CL[top_idx]-CL[start_idx])
    path=sum(abs(CL[k]-CL[k-1]) for k in range(start_idx+1,top_idx+1))
    if path<=0: return None
    ER=net/path
    return (ER, top_idx-start_idx, start_idx, top_idx)

# --- computa feature por entry ---
feat={}
undefined=[]
for e in ENTRIES:
    r=leg_efficiency(e)
    if r is None: undefined.append(e["n"]); continue
    feat[e["n"]]=r[0]

print(f"# entries com feature definida: {len(feat)} / {len(ENTRIES)}  (indefinida: {len(undefined)})")
# distribuicao ER winners vs losers
import statistics as st
er_w=[feat[e['n']] for e in ENTRIES if e['n'] in feat and e['out']==1]
er_l=[feat[e['n']] for e in ENTRIES if e['n'] in feat and e['out']==0]
print(f"# ER winners: median={st.median(er_w):.3f} mean={st.mean(er_w):.3f} n={len(er_w)}")
print(f"# ER losers : median={st.median(er_l):.3f} mean={st.mean(er_l):.3f} n={len(er_l)}")

# --- sweep de thresholds (MANTEM ER >= thr). Undefined: mantem (nao penaliza) ---
print("\n# SWEEP (keep ER>=thr; undefined mantidos):")
best=None
for thr in [x/100 for x in range(20,71,2)]:
    keep=set(undefined) | {n for n,er in feat.items() if er>=thr}
    sc=score(keep)
    # criterio: hit3r alto & poison<0.9 & ambos anos+ & N>=20
    y25w,y25n=[int(x) for x in sc["y2025"].split("/")]
    y26w,y26n=[int(x) for x in sc["y2026"].split("/")]
    ok = sc["N_kept"]>=20 and sc["poison_ratio"]<0.9 and y25w>=y25n-y25w and y26w>=y26n-y26w
    flag="  <== OK" if ok else ""
    print(f"thr={thr:.2f}  N={sc['N_kept']:3d} hit3r={sc['hit3r_kept']:.3f} pois={sc['poison_ratio']:.2f} "
          f"y25={sc['y2025']} y26={sc['y2026']} wc/lc={sc['winners_cut']}/{sc['losers_cut']}{flag}")
    if ok:
        # score de bondade: hit3r alto, poison baixo, N razoavel
        goodness=(sc["hit3r_kept"], -sc["poison_ratio"], sc["N_kept"])
        if best is None or goodness>best[0]:
            best=(goodness, thr, keep, sc)

# variante: undefined CORTADOS
print("\n# SWEEP alt (undefined CORTADOS):")
for thr in [x/100 for x in range(20,71,2)]:
    keep={n for n,er in feat.items() if er>=thr}
    sc=score(keep)
    y25w,y25n=[int(x) for x in sc["y2025"].split("/")]
    y26w,y26n=[int(x) for x in sc["y2026"].split("/")]
    ok = sc["N_kept"]>=20 and sc["poison_ratio"]<0.9 and y25w>=y25n-y25w and y26w>=y26n-y26w
    flag="  <== OK" if ok else ""
    print(f"thr={thr:.2f}  N={sc['N_kept']:3d} hit3r={sc['hit3r_kept']:.3f} pois={sc['poison_ratio']:.2f} "
          f"y25={sc['y2025']} y26={sc['y2026']} wc/lc={sc['winners_cut']}/{sc['losers_cut']}{flag}")
    if ok:
        goodness=(sc["hit3r_kept"], -sc["poison_ratio"], sc["N_kept"])
        if best is None or goodness>best[0]:
            best=(goodness, thr, keep, sc)

print("\n# ===== MELHOR =====")
if best is None:
    print("NENHUMA variante atinge (hit3r alto & poison<0.9 & ambos anos+ & N>=20).")
    print("Reporto o sweep honesto acima; a hipotese NAO separa causalmente.")
else:
    _,thr,keep,sc=best
    print(f"thr={thr:.2f}")
    print("score:",sc)
    print("keep_ns:",sorted(keep))
