#!/usr/bin/env python3
# LEGACY_PRE_CANON / DO_NOT_USE_AS_CANONICAL — convencao pre-canon (width 12 / label R). PLOTTING_CANON_MASTER_REQUIRED: docs/project_authority/PLOTTING_CANON_MASTER.md e a autoridade para novos plots (R2 2026-07-02).
"""Plota os 13 trades L2-EXTRA (1 L2 após cada V2, máquina de estado do phase56) com let-run REAL (caixa estendida)
e label AZUL numerado #L1..#L13. Mantém os 17 V2 já no chart. Emite /tmp/l2extra_trades.json + linhas pipe p/ desenho."""
import json,io,contextlib,sys,bisect,csv,datetime as dt
from pathlib import Path
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
def bear_deep(idx):
    bs=segs[idx]['start'];win=180*86400
    cand=[s for j,s in enumerate(segs) if j<idx and s['bars']>=15 and s['start']>=bs-win]
    if not cand: cand=[s for j,s in enumerate(segs) if j<idx and s['bars']>=15]
    if not cand: return None
    lo=min(s['lo'] for s in cand);amp=max(s['hi']-s['lo'] for s in cand);return (lo,lo+amp/3)
def is_v2(bi,entry,sl):
    t=T[bi];idx=seg_idx(t)
    if idx is None or idx==0 or entry-sl<=0: return False
    s=segs[idx];prev=segs[idx-1];amp=prev['hi']-prev['lo']
    ztop=(prev['hi']-amp/3,prev['hi']);zdeep=bear_deep(idx)
    i0=bisect.bisect_left(T,s['start']);rmin=min(L[i0:bi+1]);rmax=max(H[i0:bi+1]);pos=(entry-rmin)/(rmax-rmin) if rmax>rmin else .5
    return (s['regime']=='BULL' and ztop[0]<=entry<=ztop[1]) or (s['regime']=='BEAR' and zdeep and zdeep[0]<=entry<=zdeep[1]) or (s['regime']=='RANGE' and pos<0.34)
def letrun_real(bi,entry,sl):
    end=min(bi+HZ,n4-1)
    for j in range(bi+1,end+1):
        if L[j]<=sl: return (-1.0,j)
    return ((C[end]-entry)/(entry-sl),end)
Dr=Path("/Users/cristrein/tradingview-mcp/my-strategy/research/revalidation/XAU_4H_L2_BPT_BOS_CHOCH/v1/results")
sig=[]
for r in csv.DictReader(open(Dr/"l2_bpt_regua_structural.csv")):
    bi=int(r["bar_idx"]);entry=float(r["entry"]);sl=float(r["sl"])
    if entry-sl<=0: continue
    sig.append({"bi":bi,"entry":entry,"sl":sl,"v2":is_v2(bi,entry,sl)})
sig.sort(key=lambda x:x['bi'])
extra=[];armed=False
for s in sig:
    if s['v2']: armed=True
    elif armed: extra.append(s);armed=False
plot=[]
for i,x in enumerate(extra,1):
    R,ej=letrun_real(x['bi'],x['entry'],x['sl']);R=round(R-COST,2)
    ej_vis=max(ej,min(x['bi']+4,n4-1));risk=x['entry']-x['sl']
    plot.append({"n":i,"date":dt.datetime.utcfromtimestamp(T[x['bi']]).strftime("%Y-%m-%d"),"R":R,
        "entry_time":T[x['bi']],"exit_time":T[ej_vis],"entry":round(x['entry'],2),
        "stopLevel":int(round(risk/MT)),"profitLevel":int(round(max(R,0.5)*risk/MT)),
        "label_price":round(x['sl']-0.3*risk,2),"win":R>0})
json.dump(plot,open("/tmp/l2extra_trades.json","w"))
print(f"L2-EXTRA: {len(plot)} trades (win {sum(1 for x in plot if x['win'])}) sumR {sum(x['R'] for x in plot):+.1f}")
for x in plot:
    tgt=round(x['entry']+x['profitLevel']*MT,2)
    print(f'{x["n"]}|{x["entry_time"]}|{x["entry"]}|{x["exit_time"]}|{tgt}|{x["stopLevel"]}|{x["profitLevel"]}|{x["label_price"]}|{1 if x["win"] else 0}|{x["date"]}|{x["R"]:+.2f}')
