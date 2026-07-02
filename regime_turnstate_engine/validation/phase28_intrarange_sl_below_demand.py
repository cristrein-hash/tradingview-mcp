#!/usr/bin/env python3
"""Cris: TESTAR o SL de TODAS as trades INTRA-RANGE recolocado ABAIXO da DEMANDA ORIGINAL (=piso da BOX INTEIRA do detector).
Intra-range = entry dentro de uma box RANGE do phase10. Só essas trades.
SL testado = box_floor - buf*ATR (piso do range - buffer). Comparar com o SL atual (SL_CONTEXT, coluna sl -> letrun_struct).
Alargar o SL p/ o piso aumenta o risk (entry-SL) => R-multiplo menor por trade, MAS menos stops (SL mais longe). Mede-se o NET.
⚠️ CAUSALIDADE: box_floor = min(L) da BOX INTEIRA = inclui barras FUTURAS = HINDSIGHT PARCIAL. Reporto TAMBÉM rmin_causal
(running-min até à entrada = 100% causal). Onde divergem, a demanda-origem NÃO estava formada na entrada (aviso). let-run HZ120, custo 0.35."""
import json,csv,io,contextlib,sys,bisect,datetime as dt
from pathlib import Path
COST=0.35;HZ=120
VAL=Path("/Users/cristrein/tradingview-mcp/regime_turnstate_engine/validation");sys.path.insert(0,str(VAL))
with contextlib.redirect_stdout(io.StringIO()): import phase10_hybrid_regime as P
P.run(0.03,1.15,0.88);T=P.T;H=P.H;L=P.L;C=P.C;n4=len(C)
def atr(i,k=14): return sum(max(H[j]-L[j],abs(H[j]-C[j-1]),abs(L[j]-C[j-1])) for j in range(i-k+1,i+1))/k
segs=[s for s in json.load(open("/tmp/causal_segments_v10.json")) if s["regime"]=="RANGE"]
def box_of(ts):
    for s in segs:
        if s['start']<=ts<=s['end']: return s
    return None
def sim_letrun(bi,entry,sl):
    risk=entry-sl
    if risk<=0: return None
    end=min(bi+HZ,n4-1)
    for j in range(bi+1,end+1):
        if L[j]<=sl: return -1.0
    return (C[end]-entry)/risk
D=Path("/Users/cristrein/tradingview-mcp/my-strategy/research/revalidation/XAU_4H_L2_BPT_BOS_CHOCH/v1/results")
tr=[]
for r in csv.DictReader(open(D/"l2_bpt_regua_structural.csv")):
    bi=int(r["bar_idx"]);t=T[bi];box=box_of(t)
    if not box: continue                                   # SÓ intra-range
    i0=bisect.bisect_left(T,box['start']);iE=bisect.bisect_right(T,box['end'])-1
    box_floor=min(L[i0:iE+1])                              # piso da BOX INTEIRA (hindsight parcial)
    rmin_causal=min(L[i0:bi+1])                            # running-min até entrada (causal)
    a=atr(bi);entry=float(r["entry"]);orig_sl=float(r["sl"])
    tr.append({"bi":bi,"date":dt.datetime.utcfromtimestamp(t).strftime("%Y-%m-%d"),"yr":dt.datetime.utcfromtimestamp(t).year,
               "entry":entry,"orig_sl":orig_sl,"box_floor":box_floor,"rmin_causal":rmin_causal,"atr":a,
               "R_base":round(float(r["letrun_struct"])-COST,2)})
def agg(rs,keyR):
    rs=[x for x in rs if x.get(keyR) is not None];n=len(rs)
    if not n: return "N=0"
    rs=sorted(rs,key=lambda x:x["bi"]);s=sum(x[keyR] for x in rs);w=sum(1 for x in rs if x[keyR]>0)
    cum=peak=dd=0
    for x in rs: cum+=x[keyR];peak=max(peak,cum);dd=min(dd,cum-peak)
    return f"N={n:3} WR={100*w/n:3.0f}% sumR={s:+7.1f} avgR={s/n:+5.2f} DD={dd:7.1f}"
print(f"TRADES INTRA-RANGE (todas as boxes RANGE, todos os anos): {len(tr)}")
# reconciliação: R_base(letrun_struct) vs sim(orig_sl) — garante que a diferença é o SL, não o simulador
for x in tr: x["R_simorig"]=round((sim_letrun(x["bi"],x["entry"],x["orig_sl"]) or 0)-COST,2)
print("\n### RECONCILIAÇÃO (mesmo simulador, SL atual) ###")
print(f"  R_base (letrun_struct canónico) : {agg(tr,'R_base')}")
print(f"  R_sim  (meu sim, orig_sl)       : {agg(tr,'R_simorig')}   <- deve bater ~R_base")
# SL abaixo do piso da box, vários buffers, nas 2 versões (hindsight vs causal)
for buf in (0.1,0.5,1.0):
    for src,lab in [("box_floor","PISO-BOX-INTEIRA (hindsight)"),("rmin_causal","running-min-causal")]:
        for x in tr: x[f"R_{src}_{buf}"]=round((sim_letrun(x["bi"],x["entry"],x[src]-buf*x["atr"]) or 0)-COST,2)
print("\n### SL = DEMANDA-ORIGINAL(piso) − buff, let-run ###")
for buf in (0.1,0.5,1.0):
    print(f"  -- buffer {buf}ATR abaixo do piso --")
    print(f"     {'PISO-BOX-INTEIRA (hindsight)':32} {agg(tr,f'R_box_floor_{buf}')}")
    print(f"     {'running-min-causal':32} {agg(tr,f'R_rmin_causal_{buf}')}")
# quantas trades a box-inteira difere do causal (=novo low pós-entrada = demanda não formada na entrada)
diff=[x for x in tr if abs(x["box_floor"]-x["rmin_causal"])>0.01*x["atr"]]
print(f"\n### CAUSALIDADE: trades onde piso-box-inteira < running-min-na-entrada (hindsight real): {len(diff)}/{len(tr)}")
for x in sorted(diff,key=lambda z:z['bi'])[:12]:
    gap=(x["rmin_causal"]-x["box_floor"])/x["atr"]
    print(f"    {x['date']} piso-box {x['box_floor']:.0f} vs causal-na-entrada {x['rmin_causal']:.0f}  (novo low {gap:.1f}ATR mais baixo depois)")
# por-trade principal: base vs PISO-causal −0.1 (a versão honesta do pedido)
print("\n### POR-TRADE: base(SL atual) -> SL=piso-causal−0.1ATR  (SALVOU=loser virou winner) ###")
sc=0;sl_saved=0
for x in sorted(tr,key=lambda z:z['bi']):
    rb=x["R_base"];rn=x["R_rmin_causal_0.1"]
    tag="SALVOU" if rn>0 and rb<=0 else ("piorou" if rn<rb-0.3 else "")
    if tag=="SALVOU": sl_saved+=1
    print(f"    {x['date']} entry {x['entry']:6.0f} piso {x['rmin_causal']:6.0f} risk {x['entry']-(x['rmin_causal']-0.1*x['atr']):5.0f} | base R {rb:+5.2f} -> piso R {rn:+5.2f}  {tag}")
print(f"\n  losers que viraram winners (piso-causal−0.1): {sl_saved}")
print("  NB: base sumR vs piso sumR já em cima; alargar SL = risk maior por trade (R-múltiplo menor) vs menos stops = tradeoff medido.")
