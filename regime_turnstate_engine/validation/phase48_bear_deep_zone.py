#!/usr/bin/env python3
"""Cris: BEAR só na VERDADEIRA CAPITULAÇÃO profunda. As 2 bear de 2023 no chart eram PRECOCES (topo do bear ~1927/1898),
não capitulação. A zona correta = lo do último RANGE de ACUMULAÇÃO SIGNIFICATIVO (dur real ≥15 barras, ignora micros) antes do bear.
Para 2023 = RANGE fev-mar lo~1810 -> capitulação em ~1832 cai lá; as precoces (1927/1898) ficam FORA.
Método A (por regime, aqui). BULL zona-top + RANGE fundo já validados. let-run, custo 0.35."""
import json,csv,io,contextlib,sys,bisect,datetime as dt
from pathlib import Path
from collections import defaultdict
VAL=Path("/Users/cristrein/tradingview-mcp/regime_turnstate_engine/validation");sys.path.insert(0,str(VAL))
with contextlib.redirect_stdout(io.StringIO()): import phase10_hybrid_regime as P
reg=P.run(0.03,1.15,0.88);T=P.T;H=P.H;L=P.L
segs=sorted(json.load(open("/tmp/causal_segments_v10.json")),key=lambda s:s['start'])
for s in segs: s['bars']=(s['end']-s['start'])/14400
def seg_idx(t):
    for i in range(len(segs)):
        if segs[i]['start']<=t<=segs[i]['end']: return i
    return None
def bear_deep(idx):
    """fundo da ACUMULAÇÃO de onde partiu a subida que o bear corrige = lo MÍNIMO dos regimes significativos
    (>=15 barras) nos ~180 dias antes do bear começar. zona = [lo_min, lo_min + banda]."""
    bear_start=segs[idx]['start'];win=180*86400
    cand=[segs[j] for j in range(idx) if segs[j]['bars']>=15 and segs[j]['start']>=bear_start-win]
    if not cand: cand=[segs[j] for j in range(idx) if segs[j]['bars']>=15]
    if not cand: return None
    lo_min=min(s['lo'] for s in cand)
    amp=max(s['hi']-s['lo'] for s in cand)
    return (lo_min, lo_min+amp/3)
D=Path("/Users/cristrein/tradingview-mcp/my-strategy/research/revalidation/XAU_4H_L2_BPT_BOS_CHOCH/v1/results")
tr=[]
for r in csv.DictReader(open(D/"l2_bpt_regua_structural.csv")):
    bi=int(r["bar_idx"]);t=T[bi];idx=seg_idx(t)
    if idx is None or idx==0: continue
    s=segs[idx];prev=segs[idx-1];entry=float(r["entry"]);amp=prev['hi']-prev['lo']
    ztop=(prev['hi']-amp/3,prev['hi'])
    zdeep=bear_deep(idx)
    i0=bisect.bisect_left(T,s['start']);rmin=min(L[i0:bi+1]);rmax=max(H[i0:bi+1]);pos=(entry-rmin)/(rmax-rmin) if rmax>rmin else .5
    tr.append({"bi":bi,"date":dt.datetime.utcfromtimestamp(t).strftime("%Y-%m-%d"),"ym":dt.datetime.utcfromtimestamp(t).strftime("%Y-%m"),
               "yr":dt.datetime.utcfromtimestamp(t).year,"reg":s['regime'],"entry":entry,"ztop":ztop,"zdeep":zdeep,"pos":pos,
               "R":round(float(r["letrun_struct"])-0.35,2)})
tr.sort(key=lambda x:x['bi'])
def keep(x):
    if x['reg']=='BULL': return x['ztop'][0]<=x['entry']<=x['ztop'][1]
    if x['reg']=='BEAR': return x['zdeep'] and x['zdeep'][0]<=x['entry']<=x['zdeep'][1]
    return x['pos']<0.34
def panel(fn,lab):
    k=[x for x in tr if fn(x)];n=len(k)
    if not n: print(f"  {lab:32} N=0");return
    w=sum(1 for x in k if x['R']>0);s=sum(x['R'] for x in k);big=sum(1 for x in k if x['R']>=3)
    cum=peak=dd=0;st=mx=0
    for x in sorted(k,key=lambda z:z['bi']):
        cum+=x['R'];peak=max(peak,cum);dd=min(dd,cum-peak)
        st=st+1 if x['R']<=0 else 0;mx=max(mx,st)
    print(f"  {lab:32} N={n:3} WR={100*w/n:3.0f}% sumR={s:+6.1f} avgR={s/n:+5.2f} DD={dd:6.1f} streak={mx:2} big={big}")
print("BEAR = capitulação profunda (último RANGE significativo). BULL-ztop + RANGE-fundo.\n")
panel(lambda x:True,"BASE")
panel(keep,"ZONA-COMPLETA (bull+bear-deep+range)")
print("\n### BEAR trade-a-trade: cai na zona de capitulação profunda? ###")
for x in [z for z in tr if z['reg']=='BEAR']:
    zd=x['zdeep'];inz=zd and zd[0]<=x['entry']<=zd[1]
    print(f"  {x['date']} entry {x['entry']:.0f} capit-zona[{zd[0]:.0f},{zd[1]:.0f}]{'' if zd else '?'} {'DENTRO' if inz else 'fora  '} R{x['R']:+.1f}")
print("\n### por regime (dentro da zona) ###")
for RG in ('BULL','BEAR','RANGE'):
    g=[x for x in tr if x['reg']==RG and keep(x)]
    if g: print(f"  {RG:5} N={len(g):2} WR={100*sum(1 for x in g if x['R']>0)/len(g):.0f}% sumR={sum(x['R'] for x in g):+.1f}")
