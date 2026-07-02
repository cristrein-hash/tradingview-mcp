#!/usr/bin/env python3
"""Integrar FASE A (skip-meio-range) no esqueleto estrutural e medir book completo.
Breakout (FASE B) REFUTADO=beta (phase44/DA). Fica só o FILTRO: RANGE mantém FUNDO+TOPO (pos<0.34 ou >=0.67), skip MEIO.
pos = posição no range CORRENTE (running-min/max causal até entrada). Comparar esqueleto (RANGE=base) vs +skip-meio.
Painel viabilidade + por-ano. ⚠️ pos-thresholds=calibração; achado robusto = meio soma ~0 (zona-morta)."""
import json,csv,io,contextlib,sys,bisect,datetime as dt
from pathlib import Path
from collections import defaultdict
VAL=Path("/Users/cristrein/tradingview-mcp/regime_turnstate_engine/validation");sys.path.insert(0,str(VAL))
with contextlib.redirect_stdout(io.StringIO()): import phase10_hybrid_regime as P
reg=P.run(0.03,1.15,0.88);T=P.T;H=P.H;L=P.L;C=P.C
def atrb(i,k=14): return sum(max(H[j]-L[j],abs(H[j]-C[j-1]),abs(L[j]-C[j-1])) for j in range(i-k+1,i+1))/k
segs=sorted(json.load(open("/tmp/causal_segments_v10.json")),key=lambda s:s['start'])
Dr=Path("/Users/cristrein/tradingview-mcp/my-strategy/research/revalidation/XAU_4H_L2_BPT_BOS_CHOCH/v1")
raw={int(json.loads(l)["ts_epoch"]):json.loads(l) for l in open(Dr/"repro_recovery/raw_features_2020_2026.jsonl")}
def seg_idx(t):
    for i in range(len(segs)):
        if segs[i]['start']<=t<=segs[i]['end']: return i
    return None
tr=[]
for r in csv.DictReader(open(Dr/"results/l2_bpt_regua_structural.csv")):
    bi=int(r["bar_idx"]);t=T[bi];idx=seg_idx(t)
    if idx is None or idx==0: continue
    s=segs[idx];prev=segs[idx-1];a=atrb(bi);entry=float(r["entry"])
    niv=prev['hi'] if s['regime']=='BULL' else prev['lo']
    dist=(entry-niv)/a
    nb=[segs[j]['lo'] for j in range(idx) if segs[j]['lo']<entry];nearest=(entry-max(nb))/a if nb else 99
    rsi=(raw.get(int(t)) or {}).get("rsi") or 50
    i0=bisect.bisect_left(T,s['start']);rmin=min(L[i0:bi+1]);rmax=max(H[i0:bi+1])
    pos=(entry-rmin)/(rmax-rmin) if rmax>rmin else 0.5
    tr.append({"bi":bi,"ym":dt.datetime.utcfromtimestamp(t).strftime("%Y-%m"),"yr":dt.datetime.utcfromtimestamp(t).year,
               "reg":s['regime'],"segkey":idx,"dist":dist,"nb":nearest,"rsi":rsi,"pos":pos,"R":round(float(r["letrun_struct"])-0.35,2)})
tr.sort(key=lambda x:x['bi'])
byseg=defaultdict(list)
for x in tr: byseg[x['segkey']].append(x)
for k,g in byseg.items():
    g.sort(key=lambda z:z['bi'])
    for i,z in enumerate(g): z['first']=(i==0)
def bear_capit(x): return x['reg']=='BEAR' and x['dist']<=-2 and x['nb']<=14 and x['rsi']<=60
def panel(keepfn,lab):
    k=[x for x in tr if keepfn(x)];k.sort(key=lambda z:z['bi'])
    n=len(k);w=sum(1 for x in k if x['R']>0);s=sum(x['R'] for x in k);big=sum(1 for x in k if x['R']>=3)
    cum=peak=dd=0;streak=mx=0;runs=[]
    for x in k:
        cum+=x['R'];peak=max(peak,cum);dd=min(dd,cum-peak)
        if x['R']<=0: streak+=1;mx=max(mx,streak)
        else:
            if streak:runs.append(streak)
            streak=0
    if streak:runs.append(streak)
    mth=defaultdict(float)
    for x in k:mth[x['ym']]+=x['R']
    posm=sum(1 for v in mth.values() if v>0);tot=len(mth)
    print(f"  {lab:40} N={n:3} WR={100*w/n:3.0f}% sumR={s:+6.1f} avgR={s/n:+5.2f} DD={dd:6.1f} streak={mx:2} runs>=5:{sum(1 for q in runs if q>=5)} big={big:2} meses{posm}/{tot}({100*posm/tot:.0f}%+)")
def bull_ok(x): return x['first'] or x['dist']<=3
def esq(x):   # esqueleto atual (RANGE=base)
    if x['reg']=='BEAR': return bear_capit(x)
    if x['reg']=='BULL': return bull_ok(x)
    return True
def esq_rf(x):  # + skip-meio-range
    if x['reg']=='BEAR': return bear_capit(x)
    if x['reg']=='BULL': return bull_ok(x)
    return x['pos']<0.34 or x['pos']>=0.67   # RANGE skip meio
def esq_fundo(x):  # RANGE só fundo (mais agressivo)
    if x['reg']=='BEAR': return bear_capit(x)
    if x['reg']=='BULL': return bull_ok(x)
    return x['pos']<0.34
print("### INTEGRAR skip-meio-range no esqueleto ###")
panel(lambda x:True,"BASE (todos)")
panel(esq,"ESQUELETO atual (RANGE=base)")
panel(esq_rf,"ESQUELETO + RANGE skip-meio (F+T)")
panel(esq_fundo,"ESQUELETO + RANGE só-FUNDO")
print("\n### por-ano (esqueleto vs +skip-meio) ###")
for y in (2020,2021,2022,2023,2024,2025,2026):
    a=[x for x in tr if x['yr']==y and esq(x)];b=[x for x in tr if x['yr']==y and esq_rf(x)]
    if [x for x in tr if x['yr']==y]:
        print(f"  {y}: esq {sum(x['R'] for x in a):+6.1f}(n{len(a):2}) -> +skip-meio {sum(x['R'] for x in b):+6.1f}(n{len(b):2})")
