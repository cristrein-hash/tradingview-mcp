#!/usr/bin/env python3
"""MAPA DE INDICADORES POR FASE (2026-07-07) — etiquetas de FASE do Cris como ground-truth.
Cris: as 4 fases (A markup / B iniciacao / C distribuicao-topo / D bear) tem indicadores CLARAMENTE
distintos; mapear features de indicadores + snapshot dentro de cada familia. NAO minerar corte (o DA
matou isso); CARACTERIZAR assinaturas por fase. Todas causais (barras<=j). Reporta medianas por fase +
efeito winner-fases(A,B) vs loser-fases(C,D) para cada feature."""
import json, glob, bisect, sys
import statistics as st
sys.path.insert(0,"/Users/cristrein/tradingview-mcp/research/xau_15m_bb_nas_leonardo")
from agent_ctx_kit import S,TS,HI,LO,CL,ATR,EMA,RSI,N,ENTRIES,causal_swings_upto
# indicadores extra do primitives
smc=[]; nas=[]
VOL=[b.get("v") or 0 for b in S]; NASD=[b.get("nas_dist") for b in S]
for p in sorted(glob.glob("/Users/cristrein/tradingview-mcp/research/xau_15m_bb_nas_leonardo/primitives/*.primitives.json")):
    d=json.load(open(p)); smc+=[e for e in d.get("smc_events",[]) if e.get("t")]; nas+=[e for e in d.get("nas_events",[]) if e.get("t")]
smc.sort(key=lambda e:e["t"]); SMCT=[e["t"] for e in smc]; nas.sort(key=lambda e:e["t"]); NAST=[e["t"] for e in nas]
BUB=sorted([json.loads(l) for p in glob.glob("/Users/cristrein/tradingview-mcp/research/xau_15m_bb_nas_leonardo/bubbles/*.bubbles.jsonl") for l in open(p)], key=lambda x:(x.get("known_at") or x["t"]))
BUBK=[(x.get("known_at") or x["t"]) for x in BUB]
RSIMA=[None]*N
for i in range(N):
    w=[RSI[k] for k in range(max(0,i-13),i+1) if RSI[k] is not None]; RSIMA[i]=sum(w)/len(w) if w else None
# ETIQUETAS DE FASE do Cris (ground-truth)
PHASE={}
for n in [1,11,12,13,14,28,29,30,44,45,71,72,73,74,75,95,96]: PHASE[n]="A"
for n in [82,61,62,63,26]: PHASE[n]="B"
for n in [21,23,25,31,55,56,57,59,60,65,67,79,83,84,85]: PHASE[n]="C"
for n in [66,68,69,86,87,89,92,93,94,49,50]: PHASE[n]="D"
def smc_dir(e_i, price):
    # direcao inferida: preco a subir(>) ou descer(<) nas 8 barras ate ao evento
    return 1 if CL[e_i]>CL[max(0,e_i-8)] else -1
def feats(e):
    j=e["j"]; i=e["i"]; a=ATR[j] or 5; px=CL[j]
    lo=SMCT and bisect.bisect_left(SMCT,TS[max(0,j-96)]); hi=bisect.bisect_right(SMCT,TS[j])
    seg=smc[lo:hi] if lo is not None else []
    def cnt(txt,dir=None):
        c=0
        for e2 in seg:
            if e2["text"]!=txt: continue
            ei=bisect.bisect_right(TS,e2["t"])-1
            if dir is None or smc_dir(ei,e2["price"])==dir: c+=1
        return c
    # RSI bear div: preco faz HH mas RSI faz LH nas ultimas 20 barras (exaustao)
    seg20=range(max(0,j-20),j+1); ph=max(HI[k] for k in seg20);
    rsi_at_ph=RSI[max(seg20,key=lambda k:HI[k])] or 50
    rsi_now=RSI[j] or 50
    bear_div=1 if (HI[j]>=ph-0.2*a and rsi_now<rsi_at_ph-3) else 0
    # NAS recente
    nl=bisect.bisect_right(NAST,TS[j]); nseg=nas[max(0,nl-12):nl]
    nas_short=sum(1 for e2 in nseg if e2["dir"]=="SHORT" and TS[j]-e2["t"]<=48*900)
    nas_long=sum(1 for e2 in nseg if e2["dir"]=="LONG" and TS[j]-e2["t"]<=48*900)
    # bubbles: sell M/L (distribuicao) vs buy recente (acumulacao) na entrada
    bl=bisect.bisect_right(BUBK,TS[j]); bseg=[BUB[k] for k in range(max(0,bl-40),bl) if TS[j]-BUB[k]["t"]<=16*900]
    sell_ml=sum(1 for x in bseg if x["side"]=="SELL" and x["size"] in ("M","L"))
    buy_ml=sum(1 for x in bseg if x["side"]=="BUY" and x["size"] in ("M","L"))
    # volume climax no low, vol dry
    vlo=VOL[max(0,i-2):i+2]; vbase=VOL[max(0,i-48):i] or [1]
    vol_climax=(max(vlo)/ (sum(vbase)/len(vbase)+1e-9)) if vlo else 0
    # overlap no topo (distribuicao) 48b
    shi=max(HI[max(0,j-48):j+1]); slo=min(LO[max(0,j-48):j+1]); rng=(shi-slo) or 1
    overlap_top=sum(1 for k in range(max(0,j-48),j+1) if (CL[k]-slo)/rng>=0.66)/min(49,j+1)
    # pushes (higher-highs confirmados) desde origem
    sw=causal_swings_upto(j,6); highs=[pr for tp,ii,pr,ci in sw if tp=="H"]
    pushes=0
    for m in range(len(highs)-1,0,-1):
        if highs[m]>highs[m-1]: pushes+=1
        else: break
    return {"bos_up":cnt("BOS",1),"bos_dn":cnt("BOS",-1),"choch_up":cnt("CHoCH",1),"choch_dn":cnt("CHoCH",-1),
            "eqh":cnt("EQH"),"eql":cnt("EQL"),"bear_div":bear_div,"rsi_lo":RSI[i] or 50,"rsi_now":round(rsi_now,1),
            "nas_short":nas_short,"nas_long":nas_long,"sell_ml":sell_ml,"buy_ml":buy_ml,
            "vol_climax":round(vol_climax,2),"overlap_top":round(overlap_top,2),"pushes":pushes,"reclaim_lag":e["reclaim_lag"]}
rows=[]
for e in ENTRIES:
    if e["n"] not in PHASE: continue
    f=feats(e); f["ph"]=PHASE[e["n"]]; f["n"]=e["n"]; f["out"]=e["out"]; rows.append(f)
FEATS=["bos_up","bos_dn","choch_up","choch_dn","eqh","eql","bear_div","rsi_lo","rsi_now","nas_short","nas_long","sell_ml","buy_ml","vol_climax","overlap_top","pushes","reclaim_lag"]
def med(sub,k):
    v=[r[k] for r in sub]; return st.median(v) if v else 0
A=[r for r in rows if r["ph"]=="A"]; B=[r for r in rows if r["ph"]=="B"]; C=[r for r in rows if r["ph"]=="C"]; D=[r for r in rows if r["ph"]=="D"]
WIN=A+B; LOSE=C+D
print(f"labels: A{len(A)} B{len(B)} C{len(C)} D{len(D)}  (winner-fases {len(WIN)} / loser-fases {len(LOSE)})")
print(f"\n{'feature':<12} {'A':>7} {'B':>7} {'C':>7} {'D':>7} | {'AB':>7} {'CD':>7}  effect")
for k in FEATS:
    a,b,c,d=med(A,k),med(B,k),med(C,k),med(D,k); ab,cd=med(WIN,k),med(LOSE,k)
    # effect: |med(AB)-med(CD)| / (std pooled)
    allv=[r[k] for r in rows]; sd=st.pstdev(allv) or 1
    eff=(ab-cd)/sd
    flag=" <<<" if abs(eff)>=0.5 else ""
    print(f"{k:<12} {a:>7.2f} {b:>7.2f} {c:>7.2f} {d:>7.2f} | {ab:>7.2f} {cd:>7.2f}  {eff:+.2f}{flag}")
json.dump(rows,open("/Users/cristrein/tradingview-mcp/research/xau_15m_bb_nas_leonardo/results/phase_indicator_map_20260707.json","w"),indent=1)
print("\nsaved · OK")
