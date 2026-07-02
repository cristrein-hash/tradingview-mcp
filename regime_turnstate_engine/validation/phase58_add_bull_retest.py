#!/usr/bin/env python3
"""Cris: adicionar entradas de BULL em RETESTE (só reteste, NÃO fallback) aos 17 da base V2 pura.
Bull-reteste = após rompimento (close>hi_prev), 1º pullback que TOCA a zona-top [hi_prev-amp/3, hi_prev]. Entrada
sintética (gatilho de zona), SL=zona-bottom−0.5ATR, exit let-run HZ120. Dedup vs V2 por bar_idx. Painel combinado
+ por-ano + comparação com V2-base. Emite /tmp/bull_retest_add.json (só as adicionais) p/ plotagem. custo 0.35."""
import json,io,contextlib,sys,bisect,csv,datetime as dt
from pathlib import Path
from collections import defaultdict
MT=0.01;COST=0.35;HZ=120
VAL=Path("/Users/cristrein/tradingview-mcp/regime_turnstate_engine/validation");sys.path.insert(0,str(VAL))
with contextlib.redirect_stdout(io.StringIO()): import phase10_hybrid_regime as P
reg=P.run(0.03,1.15,0.88);T=P.T;H=P.H;L=P.L;C=P.C;n4=len(C)
def atr(i,k=14): return sum(max(H[j]-L[j],abs(H[j]-C[j-1]),abs(L[j]-C[j-1])) for j in range(i-k+1,i+1))/k
segs=sorted(json.load(open("/tmp/causal_segments_v10.json")),key=lambda s:s['start'])
for s in segs: s['bars']=(s['end']-s['start'])/14400
def seg_idx(t):
    for i in range(len(segs)):
        if segs[i]['start']<=t<=segs[i]['end']: return i
    return None
def bear_deep(idx):
    bs=segs[idx]['start'];win=180*86400
    cand=[s for j,s in enumerate(segs) if j<idx and s['bars']>=15 and s['start']>=bs-win]
    if not cand: cand=[s for j,s in enumerate(segs) if j<idx and s['bars']>=15]
    if not cand: return None
    lo=min(s['lo'] for s in cand);amp=max(s['hi']-s['lo'] for s in cand);return (lo,lo+amp/3)
def letrun_real(bi,entry,sl):
    if entry-sl<=0: return (None,bi)
    end=min(bi+HZ,n4-1)
    for j in range(bi+1,end+1):
        if L[j]<=sl: return (-1.0,j)
    return ((C[end]-entry)/(entry-sl),end)
# --- 17 V2 base (= phase55) ---
Dr=Path("/Users/cristrein/tradingview-mcp/my-strategy/research/revalidation/XAU_4H_L2_BPT_BOS_CHOCH/v1/results")
V2=[]
for r in csv.DictReader(open(Dr/"l2_bpt_regua_structural.csv")):
    bi=int(r["bar_idx"]);t=T[bi];idx=seg_idx(t)
    if idx is None or idx==0: continue
    s=segs[idx];prev=segs[idx-1];entry=float(r["entry"]);sl=float(r["sl"]);amp=prev['hi']-prev['lo']
    ztop=(prev['hi']-amp/3,prev['hi']);zdeep=bear_deep(idx)
    i0=bisect.bisect_left(T,s['start']);rmin=min(L[i0:bi+1]);rmax=max(H[i0:bi+1]);pos=(entry-rmin)/(rmax-rmin) if rmax>rmin else .5
    keep=(s['regime']=='BULL' and ztop[0]<=entry<=ztop[1]) or (s['regime']=='BEAR' and zdeep and zdeep[0]<=entry<=zdeep[1]) or (s['regime']=='RANGE' and pos<0.34)
    if not keep or entry-sl<=0: continue
    R,ej=letrun_real(bi,entry,sl)
    V2.append({"bi":bi,"entry":entry,"sl":sl,"R":round(R-COST,2),"kind":"V2","reg":s['regime']})
v2bars=set(x['bi'] for x in V2)
# --- BULL-reteste sintéticas (gatilho de zona, só reteste) ---
add=[]
for idx in range(1,len(segs)):
    s=segs[idx]
    if s['regime']!='BULL': continue
    prev=segs[idx-1];amp=prev['hi']-prev['lo'];niv=prev['hi'];zlo=niv-amp/3
    i0=bisect.bisect_left(T,s['start']);i1=bisect.bisect_right(T,s['end'])-1
    if i1-i0<3: continue
    k=next((j for j in range(i0,i1+1) if C[j]>niv),None)
    if k is None: continue
    rj=next((j for j in range(k+1,min(k+21,i1+1)) if L[j]<=niv),None)   # reteste (senão seria fallback → ignoro)
    if rj is None: continue
    entry=C[rj];sl=zlo-0.5*atr(rj)
    if entry-sl<=0: continue
    if any(abs(rj-b)<=1 for b in v2bars): continue   # dedup vs V2
    R,ej=letrun_real(rj,entry,sl)
    add.append({"bi":rj,"entry":entry,"sl":sl,"R":round(R-COST,2),"kind":"BULLret","reg":"BULL"})
def panel(rows,tag):
    rows=sorted(rows,key=lambda x:x['bi']);n=len(rows);w=sum(1 for x in rows if x['R']>0);s=sum(x['R'] for x in rows)
    cum=peak=dd=0;st=mx=0
    for x in rows:
        cum+=x['R'];peak=max(peak,cum);dd=min(dd,cum-peak);st=st+1 if x['R']<=0 else 0;mx=max(mx,st)
    print(f"{tag:20} N={n:2} WR={100*w/n:4.0f}% sumR={s:+6.1f} avgR={s/n:+5.2f} DD={dd:5.1f} ret/DD={(s/-dd if dd<0 else 0):5.1f} streak={mx} big={sum(1 for x in rows if x['R']>=3)}")
comb=V2+add
print("COMPARAÇÃO — V2 base vs V2 + BULL-reteste adicionais:\n")
panel(V2,"V2 base")
panel(add,"BULL-reteste add só")
panel(comb,"V2 + BULL-reteste")
print(f"\nBULL-reteste adicionais: {len(add)}")
print("\n### por-ano (combinado) ###")
by=defaultdict(list)
for x in comb: by[dt.datetime.utcfromtimestamp(T[x['bi']]).year].append(x['R'])
for y in sorted(by): print(f"  {y}: N={len(by[y]):2} sumR={sum(by[y]):+6.1f} WR={100*sum(1 for r in by[y] if r>0)/len(by[y]):3.0f}%")
# JSON plotagem das adicionais (let-run real, caixa estendida)
plot=[]
for i,x in enumerate(sorted(add,key=lambda z:z['bi']),1):
    R,ej=letrun_real(x['bi'],x['entry'],x['sl']);R=round(R-COST,2)
    ej_vis=max(ej,min(x['bi']+4,n4-1));risk=x['entry']-x['sl']
    plot.append({"n":i,"date":dt.datetime.utcfromtimestamp(T[x['bi']]).strftime("%Y-%m-%d"),"R":R,
        "entry_time":T[x['bi']],"exit_time":T[ej_vis],"entry":round(x['entry'],2),
        "stopLevel":int(round(risk/MT)),"profitLevel":int(round(max(R,0.5)*risk/MT)),
        "label_price":round(x['sl']-0.3*risk,2),"win":R>0})
json.dump(plot,open("/tmp/bull_retest_add.json","w"))
print("\n### adicionais (data|R) p/ plot ###")
for x in plot: print(f'  {x["n"]}|{x["entry_time"]}|{x["entry"]}|{x["exit_time"]}|{round(x["entry"]+x["profitLevel"]*MT,2)}|{x["stopLevel"]}|{x["profitLevel"]}|{x["label_price"]}|{1 if x["win"] else 0}|{x["date"]}|{x["R"]:+.2f}')
