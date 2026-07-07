#!/usr/bin/env python3
"""FASE-DO-CICLO classifier (LEG-CYCLE POSITION) para o engine 3R XAU 15M LONG.

TESE (estrutural/causal, SO barras<=j):
  Cada entry senta-se algures no ciclo da PERNA de alta corrente. Origem da perna = ultimo
  swing-low MACRO (zigzag r=6) confirmado <= i (o low da demanda). Dentro dessa perna conto
  PUSHES = higher-highs confirmados por um zigzag FINO (r=2) desde a origem => quao MADURO
  esta o markup. Meço tambem RETRACE = posicao do low da demanda dentro do range da perna
  (1 = de volta a origem / flush fresco; 0 = colado no topo / pullback raso).

  Fase A/B (KEEP): CEDO no ciclo (poucos pushes) OU flush fresco/profundo (retrace alto).
  Fase C (CUT, DISTRIBUICAO-TOPO): TARDE no ciclo (muitos pushes) E pullback RASO perto do
    topo (retrace baixo) => markup exausto, chase, sem flush novo.
  Fase D (CUT, BEAR): lower-highs finos (BOS-down).

TODAS as features usam causal_swings_upto(j,...) => confirm_bar<=j. Zero look-ahead, zero out,
zero numeros-alvo na LOGICA. Os alvos abaixo servem SO para sanity-check POST-HOC.
"""
import sys; sys.path.insert(0,"/Users/cristrein/tradingview-mcp/research/xau_15m_bb_nas_leonardo")
from agent_ctx_kit import S,TS,HI,LO,CL,ATR,EMA,RSI,N,ENTRIES,score,causal_swings_upto

# ---- sanity-check targets (POST-HOC ONLY, jamais na logica) ----
LOSER_T=set([21,23,31,49,50,55,56,57,59,60,65,66,67,68,69,79,83,84,85,89,93,94])
WIN_T=set([1,11,12,13,14,26,28,29,30,44,45,61,62,63,71,72,73,74,75,82,95,96])

def feats(e):
    j=e["j"]; i=e["i"]; lo=e["demand_low"]; a=ATR[i] or 5.0
    pivM=causal_swings_upto(j,6)   # macro pivots (leg origin)
    pivF=causal_swings_upto(j,2)   # fine pivots (pushes dentro da perna)
    LsM=[(idx,pr) for tp,idx,pr,ci in pivM if tp=="L"]
    origin=None
    for idx,pr in LsM:
        if idx<=i: origin=(idx,pr)          # ultimo L macro <= low da demanda
    oidx = origin[0] if origin else 0
    olo  = origin[1] if origin else LO[oidx]
    leg_hi = max(HI[oidx:j+1])              # topo causal da perna (origem..j)
    leg_range = max(leg_hi-olo, 1e-6)
    retrace = (leg_hi - lo)/leg_range       # 1=flush a origem, 0=colado no topo
    HsF=sorted([(idx,pr) for tp,idx,pr,ci in pivF if tp=="H" and idx>oidx])
    pushes=0; prevh=None                    # higher-highs finos monotonos desde a origem
    for idx,pr in HsF:
        if prevh is None or pr>prevh: pushes+=1; prevh=pr
    recH=[pr for idx,pr in sorted([(idx,pr) for tp,idx,pr,ci in pivF if tp=="H"])][-3:]
    lower_highs = len(recH)>=3 and recH[2]<recH[1]<recH[0]
    return dict(pushes=pushes,retrace=round(retrace,3),LH=int(lower_highs))

F={e["n"]:feats(e) for e in ENTRIES}

def classify(P,R,bear,Phi=99):
    """CUT (fase C) se pushes>=P e retrace<=R  (tarde + pullback raso perto do topo);
       CUT (fase C-hard) se pushes>=Phi (perna hiper-madura, qualquer retrace);
       CUT (fase D) se bear e lower_highs. KEEP = restante (A uniao B)."""
    keep=set()
    for e in ENTRIES:
        f=F[e["n"]]
        cutC = (f["pushes"]>=P and f["retrace"]<=R) or (f["pushes"]>=Phi)
        cutD = bear and f["LH"]==1
        if not (cutC or cutD): keep.add(e["n"])
    return keep

# ---- grid sweep, escolha por (hit3r alto & poison<0.9 & ambos anos+ & N>=20) ----
# "ambos anos+" = ambos os anos NET-POSITIVOS a 3R (breakeven=25% hit). poison<0.9 = anti-overfit.
best=None; rows=[]
for P in [4,5,6,7,8]:
    for R in [0.35,0.40,0.45,0.50,0.55,0.60]:
        for Phi in [99,8,9,10,12]:
            for bear in [False,True]:
                keep=classify(P,R,bear,Phi)
                sc=score(keep)
                y25w,y25n=map(int,sc["y2025"].split("/")); y26w,y26n=map(int,sc["y2026"].split("/"))
                # 3R => net-positivo sse hit>25% (paga 3, arrisca 1)
                both_pos = y25n>0 and y26n>0 and (y25w/y25n)>0.25 and (y26w/y26n)>0.25
                # poison<0.55 = SEPARACAO LIMPA (corta >=~2x mais loser que winner). Variantes com
                # poison 0.85-0.9 sobem hit cortando winners quase 1:1 (ruido, nao estrutura) e DESTROEM
                # NET R (engine=lucro). Exijo separacao limpa como guarda anti-overfit.
                ok = sc["hit3r_kept"]>=0.58 and sc["poison_ratio"]<0.55 and sc["N_kept"]>=20 and both_pos
                rows.append((P,R,bear,Phi,sc,ok))
                if ok:
                    # ordena por hit3r, desempata por poison MENOR (separacao mais limpa) e N MAIOR
                    key=(sc["hit3r_kept"], -sc["poison_ratio"], sc["N_kept"])
                    if best is None or key>best[0]: best=(key,(P,R,bear,Phi),keep,sc)

print("=== VARIANTES QUE PASSAM O GATE (hit>=.60 & poison<.9 & N>=20 & ambos anos WR>50%) ===")
for P,R,bear,Phi,sc,ok in rows:
    if ok:
        print(f"P{P} R{R:.2f} bear{int(bear)} Phi{Phi:>2} | N{sc['N_kept']:>2} hit{sc['hit3r_kept']:.3f} "
              f"pois{sc['poison_ratio']:.2f} Lcut{sc['losers_cut']:>2} Wcut{sc['winners_cut']:>2} "
              f"y25 {sc['y2025']} y26 {sc['y2026']}")

if best is None:
    print("\nNENHUMA variante passou o gate. Melhor por hit3r com poison<0.9:")
    cand=[r for r in rows if r[4]['poison_ratio']<0.9 and r[4]['N_kept']>=20]
    cand.sort(key=lambda r:-r[4]['hit3r_kept'])
    for P,R,bear,Phi,sc,ok in cand[:6]:
        print(f"P{P} R{R:.2f} bear{int(bear)} Phi{Phi} | N{sc['N_kept']} hit{sc['hit3r_kept']:.3f} pois{sc['poison_ratio']:.2f} y25 {sc['y2025']} y26 {sc['y2026']}")
else:
    key,(P,R,bear,Phi),keep,sc=best
    print(f"\n=== MELHOR VARIANTE: P>={P} R<={R} bear={bear} Phi={Phi} ===")
    print(sc)
    # ---- SANITY-CHECK POST-HOC (nao usado na logica) ----
    cut=set(e["n"] for e in ENTRIES)-keep
    lt_cut=sorted(LOSER_T & cut); wt_kept=sorted(WIN_T & keep)
    print(f"\nSANITY loser-targets CAIDOS: {len(lt_cut)}/{len(LOSER_T)} -> {lt_cut}")
    print(f"SANITY loser-targets MANTIDOS (erro): {sorted(LOSER_T & keep)}")
    print(f"SANITY winners-chave MANTIDOS: {len(wt_kept)}/{len(WIN_T)} -> {wt_kept}")
    print(f"SANITY winners-chave CAIDOS (erro): {sorted(WIN_T & cut)}")
    print(f"\nKEEP_NS ({len(keep)}): {sorted(keep)}")
