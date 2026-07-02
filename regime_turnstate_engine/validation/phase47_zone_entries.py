#!/usr/bin/env python3
"""Cris: SEM variáveis inventadas. Regra DIRETA = a entrada cai DENTRO da zona estrutural (terço) do regime ANTERIOR.
  BULL  -> entry na ZONA TOP do regime anterior (terço superior [hi_prev-amp/3, hi_prev]); reteste-suporte, NÃO acima nem middle.
  BEAR  -> entry na ZONA BOTTOM do regime anterior (terço inferior [lo_prev, lo_prev+amp/3]); capitulação PROFUNDA real.
  RANGE -> entry no FUNDO do range corrente (pos<0.34) [validado].
Nível/zona = hi/lo do regime anterior (causal, conhecido no fecho dele). SEM rsi/nearest_below/dist. let-run, custo 0.35."""
import json,csv,io,contextlib,sys,bisect,datetime as dt
from pathlib import Path
from collections import defaultdict
VAL=Path("/Users/cristrein/tradingview-mcp/regime_turnstate_engine/validation");sys.path.insert(0,str(VAL))
with contextlib.redirect_stdout(io.StringIO()): import phase10_hybrid_regime as P
reg=P.run(0.03,1.15,0.88);T=P.T;H=P.H;L=P.L;C=P.C
segs=sorted(json.load(open("/tmp/causal_segments_v10.json")),key=lambda s:s['start'])
def seg_idx(t):
    for i in range(len(segs)):
        if segs[i]['start']<=t<=segs[i]['end']: return i
    return None
D=Path("/Users/cristrein/tradingview-mcp/my-strategy/research/revalidation/XAU_4H_L2_BPT_BOS_CHOCH/v1/results")
tr=[]
for r in csv.DictReader(open(D/"l2_bpt_regua_structural.csv")):
    bi=int(r["bar_idx"]);t=T[bi];idx=seg_idx(t)
    if idx is None or idx==0: continue
    s=segs[idx];prev=segs[idx-1];entry=float(r["entry"])
    amp=prev['hi']-prev['lo']
    ztop=(prev['hi']-amp/3, prev['hi'])
    # BEAR (Cris): bottom estrutural PROFUNDO = região de bottom do RANGE+BULL ANTERIORES ao bull-prévio-do-bear (idx-1).
    # ou seja os regimes idx-2 e idx-3 (a acumulação de onde partiu a subida), NÃO o fundo do bull-topo (idx-1).
    if idx>=2:
        refs=segs[max(0,idx-3):idx-1]           # regimes antes do prévio (idx-1)
        lo_ref=min(r['lo'] for r in refs);amp_ref=max(r['hi']-r['lo'] for r in refs)
        zbot=(lo_ref, lo_ref+amp_ref/3)
    else:
        zbot=(prev['lo'], prev['lo']+amp/3)
    i0=bisect.bisect_left(T,s['start']);rmin=min(L[i0:bi+1]);rmax=max(H[i0:bi+1]);pos=(entry-rmin)/(rmax-rmin) if rmax>rmin else 0.5
    tr.append({"bi":bi,"ym":dt.datetime.utcfromtimestamp(t).strftime("%Y-%m"),"yr":dt.datetime.utcfromtimestamp(t).year,
               "reg":s['regime'],"entry":entry,"ztop":ztop,"zbot":zbot,"pos":pos,"R":round(float(r["letrun_struct"])-0.35,2)})
tr.sort(key=lambda x:x['bi'])
def in_ztop(x): return x['ztop'][0]<=x['entry']<=x['ztop'][1]
def in_zbot(x): return x['zbot'][0]<=x['entry']<=x['zbot'][1]
def keep(x):
    if x['reg']=='BULL': return in_ztop(x)
    if x['reg']=='BEAR': return in_zbot(x)
    return x['pos']<0.34   # RANGE fundo
def panel(keepfn,lab):
    k=[x for x in tr if keepfn(x)];k.sort(key=lambda z:z['bi'])
    if not k: print(f"  {lab:34} N=0");return
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
    print(f"  {lab:34} N={n:3} WR={100*w/n:3.0f}% sumR={s:+6.1f} avgR={s/n:+5.2f} DD={dd:6.1f} streak={mx:2} big={big:2} meses{posm}/{tot}({100*posm/tot:.0f}%+)")
print("REGRA DIRETA — entrada DENTRO da zona (terço) do regime anterior\n")
panel(lambda x:True,"BASE (todos)")
panel(keep,"ZONA-DIRETA (bull-ztop/bear-zbot/range-fundo)")
print("\n### por regime — quantas entradas caem DENTRO da zona vs FORA ###")
for RG in ('BULL','BEAR','RANGE'):
    g=[x for x in tr if x['reg']==RG]
    if RG=='BULL': inz=[x for x in g if in_ztop(x)]
    elif RG=='BEAR': inz=[x for x in g if in_zbot(x)]
    else: inz=[x for x in g if x['pos']<0.34]
    outz=[x for x in g if x not in inz]
    print(f"  {RG:5} total {len(g):3} | DENTRO {len(inz):2} (WR{100*sum(1 for x in inz if x['R']>0)/len(inz) if inz else 0:.0f}% sumR{sum(x['R'] for x in inz):+.1f}) | FORA {len(outz):2} (sumR{sum(x['R'] for x in outz):+.1f})")
print("\n### por-ano ZONA-DIRETA ###")
for y in (2023,2024,2025,2026):
    k=[x for x in tr if x['yr']==y and keep(x)]
    if k: print(f"  {y}: N={len(k):2} sumR={sum(x['R'] for x in k):+6.1f}")
