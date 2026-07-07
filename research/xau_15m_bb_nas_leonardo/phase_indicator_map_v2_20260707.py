#!/usr/bin/env python3
"""MAPA DE INDICADORES POR FASE v2 (2026-07-07) — features PROPRIAS (v1 tinha bugs).
Corrige: (1) direcao SMC via maquina de estrutura de mercado causal (nao sign de 8-barras); (2) RSI bear
divergence real (2 swing-highs de preco a subir com RSI a descer); (3) EQH-touches (distribuicao no topo);
(4) momentum decay (higher-highs a encolher); (5) estado de estrutura (bull/bear). Etiquetas de FASE do Cris.
Caracteriza por fase (nao minera corte). Causal barras<=j."""
import json, glob, bisect, sys
import statistics as st
sys.path.insert(0,"/Users/cristrein/tradingview-mcp/research/xau_15m_bb_nas_leonardo")
from agent_ctx_kit import S,TS,HI,LO,CL,ATR,EMA,RSI,N,ENTRIES,causal_swings_upto
RSIMA=[None]*N
for i in range(N):
    w=[RSI[k] for k in range(max(0,i-13),i+1) if RSI[k] is not None]; RSIMA[i]=sum(w)/len(w) if w else None
PHASE={}
for n in [1,11,12,13,14,28,29,30,44,45,71,72,73,74,75,95,96]: PHASE[n]="A"
for n in [82,61,62,63,26]: PHASE[n]="B"
for n in [21,23,25,31,55,56,57,59,60,65,67,79,83,84,85]: PHASE[n]="C"
for n in [66,68,69,86,87,89,92,93,94,49,50]: PHASE[n]="D"
def market_structure(j):
    """maquina de estrutura causal: caminha swings confirmados<=j; devolve estado + eventos CHoCH direcionais.
    counts CHoCH janelados aos ultimos ~192 bars; estado = ultimo evento de estrutura (bull/bear)."""
    sw=[x for x in causal_swings_upto(j,6) if x[3]>=j-192]
    swf=causal_swings_upto(j,6)  # completo p/ estado
    # estado corrente pela sequencia completa
    _lh=_ll=None; stt=0
    for tp,i,pr,ci in swf:
        if tp=="H": _lh=pr
        else:
            if _ll is not None and pr<_ll and stt>=0: stt=-1
            if _ll is not None and pr>_ll and stt<0: stt=1
            _ll=pr
    lastH=lastL=None; state=0; choch_dn=0; choch_up=0; hh_seq=[]; ll=0
    for tp,i,pr,ci in sw:
        if tp=="H":
            if lastH is not None: hh_seq.append(pr-lastH)
            lastH=pr
        else:
            # CHoCH bearish = rompe abaixo do ultimo higher-low estando em uptrend
            if lastL is not None and pr<lastL and state>=0: choch_dn+=1; state=-1
            if lastL is not None and pr>lastL:
                if state<0: choch_up+=1; state=1
            lastL=pr
    return {"choch_dn":choch_dn,"choch_up":choch_up,"state":stt,"hh_last":hh_seq[-1] if hh_seq else 0,
            "hh_decay":1 if len(hh_seq)>=2 and hh_seq[-1]<hh_seq[-2] and hh_seq[-1]>0 else 0}
def lastH0(x): return x
def rsi_bear_div(j,a):
    # 2 ultimos swing-highs de preco (fractais) a subir E RSI a descer neles = divergencia bear
    hs=[k for k in range(max(2,j-192),j-1) if HI[k]==max(HI[max(0,k-3):k+4])]
    if len(hs)<2: return 0
    k1,k2=hs[-2],hs[-1]
    if HI[k2]>HI[k1] and (RSI[k2] or 50)<(RSI[k1] or 50)-2: return 1
    return 0
def eqh_touches(j,a):
    # nº de vezes que o preco testou o mesmo teto (+-0.4A do maximo de 96b) = distribuicao
    top=max(HI[max(0,j-96):j+1]); c=0; k=max(0,j-96)
    while k<=j:
        if HI[k]>=top-0.4*a:
            c+=1; k+=6  # dedup toques proximos
        else: k+=1
    return c
def feats(e):
    j=e["j"]; i=e["i"]; a=ATR[j] or 5
    ms=market_structure(j)
    return {"ms_state":ms["state"],"choch_dn":ms["choch_dn"],"choch_up":ms["choch_up"],"hh_decay":ms["hh_decay"],
            "bear_div":rsi_bear_div(j,a),"eqh_touches":eqh_touches(j,a),
            "rsi_lo":RSI[i] or 50,"rsi_above_ma":int((RSI[j] or 50)>(RSIMA[j] or 50)),
            "reclaim_lag":e["reclaim_lag"],
            # posicao: preco na entrada vs range de 96b (distribuicao = alto)
            "pos96":round((CL[j]-min(LO[max(0,j-96):j+1]))/((max(HI[max(0,j-96):j+1])-min(LO[max(0,j-96):j+1])) or 1),2)}
rows=[]
for e in ENTRIES:
    if e["n"] not in PHASE: continue
    f=feats(e); f.update({"ph":PHASE[e["n"]],"n":e["n"],"out":e["out"]}); rows.append(f)
FEATS=["ms_state","choch_dn","choch_up","hh_decay","bear_div","eqh_touches","rsi_lo","rsi_above_ma","pos96","reclaim_lag"]
A=[r for r in rows if r["ph"]=="A"]; B=[r for r in rows if r["ph"]=="B"]; C=[r for r in rows if r["ph"]=="C"]; D=[r for r in rows if r["ph"]=="D"]
WIN=A+B; LOSE=C+D
def med(s,k): return st.median([r[k] for r in s]) if s else 0
print(f"A{len(A)} B{len(B)} C{len(C)} D{len(D)}")
print(f"\n{'feature':<13} {'A':>6} {'B':>6} {'C':>6} {'D':>6} | {'WIN(AB)':>8} {'LOSE(CD)':>8}  effect")
for k in FEATS:
    allv=[r[k] for r in rows]; sd=st.pstdev(allv) or 1; eff=(med(WIN,k)-med(LOSE,k))/sd
    flag=" <<<" if abs(eff)>=0.5 else ""
    print(f"{k:<13} {med(A,k):>6.2f} {med(B,k):>6.2f} {med(C,k):>6.2f} {med(D,k):>6.2f} | {med(WIN,k):>8.2f} {med(LOSE,k):>8.2f}  {eff:+.2f}{flag}")
# mostrar C (distribuicao) vs A (markup) especificamente — o par mais dificil
print("\n=== A (markup-win) vs C (distribuicao-lose) — o par que o Cris diz ser distinto ===")
for k in FEATS:
    allv=[r[k] for r in rows]; sd=st.pstdev(allv) or 1; eff=(med(A,k)-med(C,k))/sd
    flag=" <<<" if abs(eff)>=0.6 else ""
    print(f"  {k:<13} A {med(A,k):>6.2f}  C {med(C,k):>6.2f}  eff {eff:+.2f}{flag}")
json.dump(rows,open("/Users/cristrein/tradingview-mcp/research/xau_15m_bb_nas_leonardo/results/phase_indicator_map_v2_20260707.json","w"),indent=1)
print("\nsaved · OK")
