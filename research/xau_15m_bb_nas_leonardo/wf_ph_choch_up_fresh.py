#!/usr/bin/env python3
"""CLASSIFICADOR DE FASE DO CICLO — engine 3R XAU 15M LONG (agente CHoCH-UP FRESCO).

TESE (rule 5): KEEP = Fase A (MARKUP, higher-highs) uniao Fase B (INICIACAO: flush/varredura
a demanda + reclaim + CHoCH-up, comeca nova perna). CUT = Fase C (DISTRIBUICAO-TOPO: markup
exausto, EQH, chase) uniao Fase D (BEAR-ATIVO: lower-highs/BOS-down).

ACHADO EMPIRICO (feat2.py, exploracao pre-registada): nas TARGET lists o "close acima do ULTIMO
LOWER-HIGH" (break/choch_fresh no lado do TOPO) e uma assinatura de LOSER (chase de topo, Fase C):
LOSER choch_fresh 0.36 / brk_lastH 0.14  vs  WINK 0.09 / 0.00. O CHoCH-up que marca INICIACAO
sadia esta no lado do FUNDO: a sequencia de LOWS confirmados vira a subir (higher-low) = mudanca
de caracter bullish da estrutura de baixos = nova perna a partir de base mais alta, ANTES do chase.
Por isso o classificador localiza o CHoCH-up na trajetoria dos LOWS (higher-low staircase) e VETA
o chase de topo. Tudo causal (swings confirmados conf_bar<=j; closes<=j).

CAUSAL: features usam SO barras indice<=j via causal_swings_upto(j) e CL/HI/LO/ATR ate j.
NAO usa e['out'], nao usa numeros-alvo, nao usa janelas que passam de j.
"""
import sys; sys.path.insert(0,"/Users/cristrein/tradingview-mcp/research/xau_15m_bb_nas_leonardo")
from agent_ctx_kit import S,TS,HI,LO,CL,ATR,EMA,RSI,N,ENTRIES,score,causal_swings_upto

# --- sanity-check lists (POST-HOC apenas; NUNCA usadas na logica) ---
LOSER_TGT=[21,23,31,49,50,55,56,57,59,60,65,66,67,68,69,79,83,84,85,89,93,94]
WIN_KEY  =[1,11,12,13,14,26,28,29,30,44,45,61,62,63,71,72,73,74,75,82,95,96]

def phase_feats(e, r=3, W=32):
    """Estado ESTRUTURAL/SEQUENCIAL causal na barra de decisao j. So barras<=j."""
    j=e["j"]; a=ATR[j] or 5.0
    sw=causal_swings_upto(j,r)                 # swings confirmados conf_bar<=j (CAUSAL)
    H=[pr for tp,i,pr,ci in sw if tp=="H"]
    L=[pr for tp,i,pr,ci in sw if tp=="L"]
    lastL=L[-1] if L else CL[j]; prevL=L[-2] if len(L)>=2 else lastL
    prevL2=L[-3] if len(L)>=3 else prevL
    lastH=H[-1] if H else CL[j]; prevH=H[-2] if len(H)>=2 else lastH
    f={}
    # --- lado FUNDO: CHoCH-up = trajetoria dos lows a subir (higher-low staircase) ---
    f["higher_low"]  = int(lastL>prevL)                 # ultimo low confirmado sobe = char bullish
    f["low_stair"]   = int(lastL>prevL>=prevL2)         # 2 lows a subir = escada bullish (trajetoria)
    f["lower_low"]   = int(lastL<prevL)                 # low a descer = Fase D (bear ativo)
    # --- lado TOPO: markup estabelecido (Fase A) ---
    f["higher_high"] = int(lastH>prevH)
    # --- CHASE de topo (Fase C distribuicao): close rompe o ultimo high recentemente ---
    brk=99
    for k in range(j, max(1,j-W)-1, -1):
        if CL[k]>lastH and CL[k-1]<=lastH: brk=j-k; break
    f["chase_top"]   = int(brk<=W)                      # rompeu o ultimo high nas ultimas W barras = chase
    # ref: ultimo lower-high confirmado (para o teste LITERAL da tese, comparacao honesta)
    ref=None
    for idx in range(len(H)-1,0,-1):
        if H[idx]<H[idx-1]: ref=H[idx]; break
    ch=99
    if ref is not None:
        for k in range(j, max(1,j-W)-1, -1):
            if CL[k]>ref and CL[k-1]<=ref: ch=j-k; break
    f["choch_top_fresh"]=int(ch<=W)                     # tese LITERAL (topo) — esperado LOSER-side
    return f

FEA={e["n"]:phase_feats(e) for e in ENTRIES}

def keep_variant(v):
    ks=set()
    for e in ENTRIES:
        f=FEA[e["n"]]; n=e["n"]
        if v=="V0_literal":           # tese LITERAL: CHoCH-up de TOPO fresco OU markup
            k = f["choch_top_fresh"] or f["higher_high"]
        elif v=="V1_hl":              # so higher-low (CHoCH de fundo)
            k = f["higher_low"]
        elif v=="V2_hl_nochase":      # higher-low E sem chase de topo (A/B sem C)
            k = f["higher_low"] and not f["chase_top"]
        elif v=="V3_bull_nochase":    # (higher-low OU markup) E nao bear E sem chase
            k = (f["higher_low"] or f["higher_high"]) and not f["lower_low"] and not f["chase_top"]
        elif v=="V4_stair_or_markup": # escada de lows OU markup, sem chase de topo
            k = (f["low_stair"] or f["higher_high"]) and not f["chase_top"]
        elif v=="V5_notbear_nochase": # NAO bear (sem lower-low) E sem chase de topo
            k = (not f["lower_low"]) and not f["chase_top"]
        else: k=True
        if k: ks.add(n)
    return ks

VARIANTS=["V0_literal","V1_hl","V2_hl_nochase","V3_bull_nochase","V4_stair_or_markup","V5_notbear_nochase"]
print("MULTIFATORIAL(low-structure trajetoria + veto chase-topo + veto bear) · TRAJETORIA(swing lows multi-barra) · 2 OBJETIVOS(manter A/B, cortar C/D) · SANITY_PROBE")
print(f"BASE: {score([e['n'] for e in ENTRIES])['base']}\n")
results={}
for v in VARIANTS:
    ks=keep_variant(v); sc=score(ks); results[v]=(ks,sc)
    print(f"{v:20s} N={sc['N_kept']:3d} hit={sc['hit3r_kept']:.3f} poison={sc['poison_ratio']:5.2f} "
          f"Lcut={sc['losers_cut']:2d} Wcut={sc['winners_cut']:2d} y25={sc['y2025']:6s} y26={sc['y2026']:6s}")

# escolher melhor por (poison<0.9 & ambos anos+ & N>=20) -> maior hit3r
def yrs_pos(sc):
    def p(s):
        w,n=s.split("/"); return int(n)>0 and int(w)>0
    return p(sc["y2025"]) and p(sc["y2026"])
elig=[(v,ks,sc) for v,(ks,sc) in results.items()
      if sc["poison_ratio"]<0.9 and sc["N_kept"]>=20 and yrs_pos(sc)]
elig.sort(key=lambda x:(-x[2]["hit3r_kept"], x[2]["poison_ratio"]))
print("\nELIGIVEIS (poison<0.9 & N>=20 & ambos anos+):")
for v,ks,sc in elig: print(f"  {v:20s} hit={sc['hit3r_kept']:.3f} poison={sc['poison_ratio']}")
if elig:
    bv,bks,bsc=elig[0]
    print(f"\n>>> MELHOR: {bv}  {bsc}")
    # SANITY-CHECK post-hoc (NAO usado na logica)
    lc=sum(1 for n in LOSER_TGT if n not in bks)
    wk=sum(1 for n in WIN_KEY  if n in bks)
    print(f"SANITY post-hoc: loser-targets cortados {lc}/{len(LOSER_TGT)} · winners-chave mantidos {wk}/{len(WIN_KEY)}")
    print("KEEP_NS:", sorted(bks))
else:
    print("\n>>> NENHUMA variante elegivel — reportar honesto.")
