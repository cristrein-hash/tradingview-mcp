#!/usr/bin/env python3
"""VERIFICACAO ADVERSARIAL ESTRITO-CAUSAL — impulse_efficiency_prior_leg.

Diferenca vs candidato: NAO uso e['leg_top'] (que vem do zigzag FULL nao-causal)
para casar o topo. Reconstruo a perna PURAMENTE de causal_swings_upto(j):
  top  = ultimo swing H confirmado (ci<=j) com idx<=i  (antes da demand-low)
  start= swing L imediatamente anterior a esse H
ER = |CL[top]-CL[start]| / soma passos bar-a-bar (todos indices < i < j).
Nenhuma barra > j e tocada. Sem e['out'] na decisao.
"""
import sys; sys.path.insert(0, "/Users/cristrein/tradingview-mcp/research/xau_15m_bb_nas_leonardo")
from agent_ctx_kit import S,TS,HI,LO,CL,ATR,EMA,RSI,N,ENTRIES,score,causal_swings_upto

def leg_efficiency_strict(e):
    j=e["j"]; i=e["i"]
    sw=causal_swings_upto(j)          # SO swings confirmados ate j
    # ultimo H confirmado com idx<=i (nao usa e['leg_top'])
    top=None
    for k in range(len(sw)-1,-1,-1):
        tp,idx,pr,ci=sw[k]
        if tp=="H" and idx<=i:
            top=k; break
    if top is None: return None
    top_idx=sw[top][1]
    # swing L imediatamente antes do topo
    start_idx=None
    for k in range(top-1,-1,-1):
        if sw[k][0]=="L":
            start_idx=sw[k][1]; break
    if start_idx is None or start_idx>=top_idx: return None
    net=abs(CL[top_idx]-CL[start_idx])
    path=sum(abs(CL[k]-CL[k-1]) for k in range(start_idx+1,top_idx+1))
    if path<=0: return None
    return net/path

feat={}; undefined=[]
for e in ENTRIES:
    r=leg_efficiency_strict(e)
    if r is None: undefined.append(e["n"])
    else: feat[e["n"]]=r

print(f"# feature definida: {len(feat)}/{len(ENTRIES)}  (indef {len(undefined)})")
import statistics as st
er_w=[feat[e['n']] for e in ENTRIES if e['n'] in feat and e['out']==1]
er_l=[feat[e['n']] for e in ENTRIES if e['n'] in feat and e['out']==0]
print(f"# ER winners median={st.median(er_w):.3f} n={len(er_w)}")
print(f"# ER losers  median={st.median(er_l):.3f} n={len(er_l)}")

# quanto o strict diverge do candidato (match de topo por preco)?
# compara idx do topo escolhido strict vs price-match do candidato
mismatch=0
for e in ENTRIES:
    j=e["j"]; i=e["i"]; ltp=e["leg_top"]
    sw=causal_swings_upto(j)
    price_top=None
    for k in range(len(sw)-1,-1,-1):
        tp,idx,pr,ci=sw[k]
        if tp=="H" and idx<=i and abs(pr-ltp)<1e-6: price_top=sw[k][1]; break
    strict_top=None
    for k in range(len(sw)-1,-1,-1):
        tp,idx,pr,ci=sw[k]
        if tp=="H" and idx<=i: strict_top=sw[k][1]; break
    if price_top is not None and strict_top is not None and price_top!=strict_top: mismatch+=1
print(f"# topo strict != topo price-match em {mismatch} entries (0 = candidato ja era estrito)")

# thr principal do candidato = 0.26, undefined MANTIDOS (como candidato)
thr=0.26
keep=set(undefined) | {n for n,er in feat.items() if er>=thr}
sc=score(keep)
print(f"\n# STRICT thr={thr} (undefined mantidos): {sc}")

# sweep para band
print("\n# SWEEP strict (undefined mantidos):")
for t in [x/100 for x in range(20,41,2)]:
    keep=set(undefined) | {n for n,er in feat.items() if er>=t}
    s=score(keep)
    y25w,y25n=[int(x) for x in s["y2025"].split("/")]
    y26w,y26n=[int(x) for x in s["y2026"].split("/")]
    ok = s["N_kept"]>=20 and s["poison_ratio"]<0.9 and y25w>=y25n-y25w and y26w>=y26n-y26w
    print(f"thr={t:.2f} N={s['N_kept']:3d} hit3r={s['hit3r_kept']:.3f} pois={s['poison_ratio']:.2f} "
          f"y25={s['y2025']} y26={s['y2026']} wc/lc={s['winners_cut']}/{s['losers_cut']}{'  <==OK' if ok else ''}")
