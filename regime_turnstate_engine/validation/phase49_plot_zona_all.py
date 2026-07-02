#!/usr/bin/env python3
"""Gera plot canónico de TODAS as operações da estratégia V2 ZONA-PURA em todo o período disponível.
Regra: BULL entry na zona-top [hi_prev-amp/3, hi_prev] · BEAR entry na zona-capitulação-profunda (lo min acumulação 180d) ·
RANGE entry no fundo (pos<0.34). SL=SL_CONTEXT(régua), let-run. long_position: stopLevel/profitLevel TICKS, largura 12 barras."""
import json,csv,io,contextlib,sys,bisect,datetime as dt
from pathlib import Path
MT=0.01
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
    bs=segs[idx]['start'];win=180*86400
    cand=[s for j,s in enumerate(segs) if j<idx and s['bars']>=15 and s['start']>=bs-win]
    if not cand: cand=[s for j,s in enumerate(segs) if j<idx and s['bars']>=15]
    if not cand: return None
    lo=min(s['lo'] for s in cand);amp=max(s['hi']-s['lo'] for s in cand);return (lo,lo+amp/3)
Dr=Path("/Users/cristrein/tradingview-mcp/my-strategy/research/revalidation/XAU_4H_L2_BPT_BOS_CHOCH/v1/results")
out=[]
for r in csv.DictReader(open(Dr/"l2_bpt_regua_structural.csv")):
    bi=int(r["bar_idx"]);t=T[bi];idx=seg_idx(t)
    if idx is None or idx==0: continue
    s=segs[idx];prev=segs[idx-1];entry=float(r["entry"]);sl=float(r["sl"]);amp=prev['hi']-prev['lo']
    ztop=(prev['hi']-amp/3,prev['hi']);zdeep=bear_deep(idx)
    i0=bisect.bisect_left(T,s['start']);rmin=min(L[i0:bi+1]);rmax=max(H[i0:bi+1]);pos=(entry-rmin)/(rmax-rmin) if rmax>rmin else .5
    keep = (s['regime']=='BULL' and ztop[0]<=entry<=ztop[1]) or \
           (s['regime']=='BEAR' and zdeep and zdeep[0]<=entry<=zdeep[1]) or \
           (s['regime']=='RANGE' and pos<0.34)
    if not keep: continue
    risk=entry-sl
    if risk<=0: continue
    R=round(float(r["letrun_struct"])-0.35,1)
    out.append({"date":dt.datetime.utcfromtimestamp(t).strftime("%Y-%m-%d"),"reg":s['regime'],
        "entry_time":t,"exit_time":t+12*14400,"entry":round(entry,2),"target":round(entry+3*risk,2),
        "stopLevel":int(round(risk/MT)),"profitLevel":int(round(3*risk/MT)),"R":R,"win":R>0})
out.sort(key=lambda x:x['entry_time'])
json.dump(out,open("/tmp/zona_all_trades.json","w"))
w=sum(1 for x in out if x['win'])
print(f"V2 ZONA-PURA — todas as operações: {len(out)} (win {w}/loss {len(out)-w}) sumR {sum(x['R'] for x in out):+.1f}")
print(f"período: {out[0]['date']} -> {out[-1]['date']}  |  por regime: "+str({rg:sum(1 for x in out if x['reg']==rg) for rg in ('BULL','RANGE','BEAR')}))
for x in out:
    print(f'{x["entry_time"]}|{x["entry"]}|{x["exit_time"]}|{x["target"]}|{x["stopLevel"]}|{x["profitLevel"]}|{1 if x["win"] else 0}|{x["reg"]}|{x["date"]}')
