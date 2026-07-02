#!/usr/bin/env python3
"""Cris (2026-07-01): cortar FREQUÊNCIA de entradas por range = atacar o cluster de losses (13:1) que quebra o humano.
Ideia: "manter a 1ª e as 2 ÚLTIMAS" de cada range. Testar com painel de VIABILIDADE (foco max-loss-streak, a métrica
que o SL-piso NÃO mexeu). SL das mantidas = piso-da-box causal −0.1ATR (o que o Cris quer). Book completo 2023+:
range → variante de frequência; não-range → sempre mantidas c/ SL_CONTEXT.
CAUSALIDADE: '2 últimas' literais = HINDSIGHT (só se sabe no fim do range) → reporto como TECTO.
Proxy CAUSAL das últimas = BOS-up (rompeu topo do range, detectável na hora, =o que daria no Telegram). let-run HZ120, custo 0.35."""
import json,csv,io,contextlib,sys,bisect,datetime as dt
from pathlib import Path
from collections import defaultdict
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
def sim(bi,entry,sl):
    if entry-sl<=0: return None
    end=min(bi+HZ,n4-1)
    for j in range(bi+1,end+1):
        if L[j]<=sl: return -1.0
    return (C[end]-entry)/(entry-sl)
def bos_up(bi,box):
    i0=bisect.bisect_left(T,box['start'])
    if bi-3<=i0: return False
    return C[bi]>max(H[i0:bi-2])   # fechou acima do topo do range formado antes = rompimento causal
D=Path("/Users/cristrein/tradingview-mcp/my-strategy/research/revalidation/XAU_4H_L2_BPT_BOS_CHOCH/v1/results")
rows=[]
for r in csv.DictReader(open(D/"l2_bpt_regua_structural.csv")):
    bi=int(r["bar_idx"]);t=T[bi];y=dt.datetime.utcfromtimestamp(t).year
    if y<2023: continue
    box=box_of(t);entry=float(r["entry"])
    R_base=round(float(r["letrun_struct"])-COST,2)
    d={"bi":bi,"ym":dt.datetime.utcfromtimestamp(t).strftime("%Y-%m"),"range":bool(box),"R_base":R_base}
    if box:
        i0=bisect.bisect_left(T,box['start']);rmin=min(L[i0:bi+1]);a=atr(bi)
        d["R_piso"]=round((sim(bi,entry,rmin-0.1*a) or 0)-COST,2)
        d["boxkey"]=(box['start'],box['end']);d["bos"]=bos_up(bi,box)
    else:
        d["R_piso"]=R_base;d["boxkey"]=None;d["bos"]=False
    rows.append(d)
rows.sort(key=lambda x:x["bi"])
# marcar posição na sequência do range (1ª, últimas)
byrange=defaultdict(list)
for x in rows:
    if x["range"]: byrange[x["boxkey"]].append(x)
for k,g in byrange.items():
    g.sort(key=lambda z:z["bi"])
    for i,x in enumerate(g):
        x["is_first"]=(i==0);x["is_last2"]=(i>=len(g)-2);x["idx"]=i;x["nrange"]=len(g)
def keep_all(x): return True
def keep_first_last2(x): return x["is_first"] or x["is_last2"]      # HINDSIGHT (tecto)
def keep_first_bos(x):  return x["is_first"] or x["bos"]            # CAUSAL (Telegram-implementável)
def keep_cap3(x):       return x["idx"]<3                           # 3 primeiras (causal)
def keep_first(x):      return x["is_first"]                        # só a 1ª (causal)
def panel(keepfn,Rkey,label):
    kept=[x for x in rows if (not x["range"]) or keepfn(x)]
    rs=[x[Rkey] if x["range"] else x["R_base"] for x in kept]
    n=len(rs);w=sum(1 for v in rs if v>0);s=sum(rs)
    cum=peak=dd=0;streak=mx=0;runs=[]
    for v in rs:
        cum+=v;peak=max(peak,cum);dd=min(dd,cum-peak)
        if v<=0: streak+=1;mx=max(mx,streak)
        else:
            if streak: runs.append(streak)
            streak=0
    if streak: runs.append(streak)
    r5=sum(1 for q in runs if q>=5)
    mth=defaultdict(float)
    for x,v in zip(kept,rs): mth[x["ym"]]+=v
    posm=sum(1 for v in mth.values() if v>0);tot=len(mth);worst=min(mth.values()) if mth else 0
    nr=sum(1 for x in kept if x["range"])
    print(f"  {label:32} N={n:3}(range {nr:2}) WR={100*w/n:3.0f}% sumR={s:+6.1f} DD={dd:6.1f} | MAXstreak={mx:2} runs>=5:{r5} | meses {posm}/{tot}+ pior{worst:+5.1f}")
print(f"BOOK L2/BPT 2023+ = {len(rows)} trades ({sum(1 for x in rows if x['range'])} range). Cortar frequência de entradas por range:")
print("\n### REFERÊNCIAS ###")
panel(keep_all,"R_base","BASELINE tudo SL_CONTEXT")
panel(keep_all,"R_piso","todas range + SL-piso")
print("\n### CORTAR FREQUÊNCIA (range mantidas usam SL-piso) ###")
panel(keep_first_last2,"R_piso","1ª+2ULTIMAS (HINDSIGHT tecto)")
panel(keep_first_bos,"R_piso","1ª+BOS-up (CAUSAL/Telegram)")
panel(keep_cap3,"R_piso","3 primeiras (causal)")
panel(keep_first,"R_piso","só a 1ª (causal)")
print("\n### mesmas variantes mas com SL_CONTEXT (isola efeito da FREQUÊNCIA, sem o SL) ###")
panel(keep_first_last2,"R_base","1ª+2ULTIMAS SL_CONTEXT")
panel(keep_first_bos,"R_base","1ª+BOS-up SL_CONTEXT")
# quantas entradas por range (distribuição) + quantas mantém cada regra
print("\n### diagnóstico por range ###")
for k,g in sorted(byrange.items()):
    d0=dt.datetime.utcfromtimestamp(g[0]['bi'] and T[g[0]['bi']]).strftime("%Y-%m-%d")
    nb=sum(1 for x in g if x['bos']);nl2=sum(1 for x in g if x['is_last2'])
    wb=sum(1 for x in g if x['bos'] and x['R_piso']>0)
    print(f"  range {d0}: {len(g):2} entradas | BOS-up:{nb} (win {wb}) | 2-últimas win: {sum(1 for x in g if x['is_last2'] and x['R_piso']>0)}/{nl2}")
