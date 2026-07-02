#!/usr/bin/env python3
"""Validar bull_break (1-após-capit): lista os +N trades, por-ano, jackknife-drop-ano, jackknife-drop-cada-trade.
Robusto = não depende de 1 ano nem 1 trade. Se OK, emite /tmp/capit_plus_bullbreak.json p/ plotagem. custo 0.35."""
import json,io,contextlib,sys,bisect,csv,datetime as dt
from pathlib import Path
from statistics import mean
from collections import defaultdict
MT=0.01;COST=0.35;HZ=120
VAL=Path("/Users/cristrein/tradingview-mcp/regime_turnstate_engine/validation");sys.path.insert(0,str(VAL))
with contextlib.redirect_stdout(io.StringIO()): import phase10_hybrid_regime as P
reg=P.run(0.03,1.15,0.88);T=P.T;H=P.H;L=P.L;C=P.C;n4=len(C)
segs=sorted(json.load(open("/tmp/causal_segments_v10.json")),key=lambda s:s['start'])
for s in segs: s['bars']=(s['end']-s['start'])/14400
def seg_idx(t):
    for i in range(len(segs)):
        if segs[i]['start']<=t<=segs[i]['end']: return i
    return None
def regime_at(bi):
    idx=seg_idx(T[bi]);return segs[idx]['regime'] if idx is not None else '?'
def bear_deep(idx):
    bs=segs[idx]['start'];win=180*86400
    cand=[s for j,s in enumerate(segs) if j<idx and s['bars']>=15 and s['start']>=bs-win]
    if not cand: cand=[s for j,s in enumerate(segs) if j<idx and s['bars']>=15]
    if not cand: return None
    lo=min(s['lo'] for s in cand);amp=max(s['hi']-s['lo'] for s in cand);return (lo,lo+amp/3)
TR=[0.0]*n4
for i in range(1,n4): TR[i]=max(H[i]-L[i],abs(H[i]-C[i-1]),abs(L[i]-C[i-1]))
ATR=[0.0]*n4
for i in range(14,n4): ATR[i]=mean(TR[i-13:i+1])
def SL(i): return min(L[max(0,i-4):i+1])-0.5*ATR[i]
def letrun_full(bi,entry,sl):
    if entry-sl<=0:return None,bi
    end=min(bi+HZ,n4-1)
    for j in range(bi+1,end+1):
        if L[j]<=sl:return -1.0,j
    return (C[end]-entry)/(entry-sl),end
Dr=Path("/Users/cristrein/tradingview-mcp/my-strategy/research/revalidation/XAU_4H_L2_BPT_BOS_CHOCH/v1/results")
capit=[]
for r in csv.DictReader(open(Dr/"l2_bpt_regua_structural.csv")):
    bi=int(r["bar_idx"]);entry=float(r["entry"]);sl=float(r["sl"]);t=T[bi];idx=seg_idx(t)
    if idx is None or idx==0 or entry-sl<=0: continue
    s=segs[idx];prev=segs[idx-1];amp=prev['hi']-prev['lo'];zdeep=bear_deep(idx)
    i0=bisect.bisect_left(T,s['start']);rmin=min(L[i0:bi+1]);rmax=max(H[i0:bi+1]);pos=(entry-rmin)/(rmax-rmin) if rmax>rmin else .5
    if (s['regime']=='BEAR' and zdeep and zdeep[0]<=entry<=zdeep[1]) or (s['regime']=='RANGE' and pos<0.25):
        rr,ej=letrun_full(bi,entry,sl)
        if rr is not None: capit.append({"bi":bi,"low":min(L[max(0,bi-4):bi+1]),"entry":entry,"sl":sl,"R":round(rr-COST,2),"ej":ej,"kind":"CAPIT"})
capit.sort(key=lambda x:x['bi'])
def bull_break(i): return C[i]>max(H[i-10:i]) and C[i]>C[i-1]
add=[]
for c in capit:
    cb=c['bi']
    for i in range(cb+2,min(cb+150,n4-HZ-1)):
        if regime_at(i)=='BEAR' or C[i]<c['low']: break
        if bull_break(i):
            sl=SL(i);r,ej=letrun_full(i,C[i],sl)
            if C[i]-sl>0 and r is not None:
                add.append({"bi":i,"entry":C[i],"sl":sl,"R":round(r-COST,2),"ej":ej,"kind":"BREAK","anchor":dt.datetime.utcfromtimestamp(T[cb]).strftime('%Y-%m-%d')});break
allt=sorted(capit+add,key=lambda x:x['bi'])
def stats(rows):
    rows=sorted(rows,key=lambda x:x['bi']);n=len(rows);w=sum(1 for x in rows if x['R']>0);s=sum(x['R'] for x in rows)
    cum=peak=dd=0;st=mx=0
    for x in rows:
        cum+=x['R'];peak=max(peak,cum);dd=min(dd,cum-peak);st=st+1 if x['R']<=0 else 0;mx=max(mx,st)
    return n,100*w/n,s,s/n,dd,mx
n,wr,s,avg,dd,mx=stats(allt)
print(f"CAPIT + bull_break: N={n} WR={wr:.0f}% sumR={s:+.1f} avgR={avg:+.2f} DD={dd:.1f} STREAK={mx}\n")
print("os +N trades bull_break (data | R | âncora-capit):")
for x in add: print(f"  {dt.datetime.utcfromtimestamp(T[x['bi']]).strftime('%Y-%m-%d')} | R={x['R']:+.2f} | pós-capit {x['anchor']}")
print("\nPOR-ANO (combinado):")
by=defaultdict(list)
for x in allt: by[dt.datetime.utcfromtimestamp(T[x['bi']]).year].append(x['R'])
for y in sorted(by): print(f"  {y}: n={len(by[y]):2} sumR={sum(by[y]):+6.1f} WR={100*sum(1 for r in by[y] if r>0)/len(by[y]):3.0f}%")
print("JACKKNIFE drop-ano (só bull_break add):")
addby=defaultdict(list)
for x in add: addby[dt.datetime.utcfromtimestamp(T[x['bi']]).year].append(x['R'])
tota=sum(x['R'] for x in add)
for y in sorted(addby): print(f"  add sem {y}: sumR={tota-sum(addby[y]):+.1f} (n={len(add)-len(addby[y])})")
print(f"JACKKNIFE drop-cada-add-trade: min sumR combinado se remover o melhor add = {s-max(x['R'] for x in add):+.1f}")
# plot json (só os add, para plotar como novos)
MTp=0.01;plot=[]
for i,x in enumerate(sorted(add,key=lambda z:z['bi']),1):
    risk=x['entry']-x['sl']
    plot.append({"n":i,"date":dt.datetime.utcfromtimestamp(T[x['bi']]).strftime("%Y-%m-%d"),"R":x['R'],
        "entry_time":T[x['bi']],"exit_time":T[x['ej'] if x['ej']>x['bi'] else min(x['bi']+4,n4-1)],"entry":round(x['entry'],2),
        "stopLevel":int(round(risk/MTp)),"profitLevel":int(round(max(x['R'],0.5)*risk/MTp)),"label_price":round(x['sl']-0.3*risk,2),"win":x['R']>0})
json.dump(plot,open("/tmp/capit_plus_bullbreak.json","w"))
print(f"\n(emitido /tmp/capit_plus_bullbreak.json com {len(plot)} trades bull_break p/ plotar)")
