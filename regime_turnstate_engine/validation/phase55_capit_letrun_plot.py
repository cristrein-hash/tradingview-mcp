#!/usr/bin/env python3
# LEGACY_PRE_CANON / DO_NOT_USE_AS_CANONICAL — convencao pre-canon (width 12 / label R). PLOTTING_CANON_MASTER_REQUIRED: docs/project_authority/PLOTTING_CANON_MASTER.md e a autoridade para novos plots (R2 2026-07-02).
"""Cris: TODOS os trades de CAPITULAÇÃO merecem let-run (potencial pós-fundo enorme). A régua V2 já calcula R com
let-run HZ120, mas o PLOT desenhava caixa curta (12b/+3R) que esconde o potencial. Aqui: identifica os trades de
capitulação entre os 17 V2, computa o let-run REAL (barra de saída, preço, R) e emite JSON de plotagem com a caixa
ESTENDIDA até a saída real e profitLevel = R real capturado. Capitulação = fundo profundo: BEAR bear_deep OU RANGE pos<0.25."""
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
def letrun_real(bi,entry,sl):
    """Retorna (R, exit_bar, exit_price). Stop-first, senão C em bi+HZ."""
    end=min(bi+HZ,n4-1)
    for j in range(bi+1,end+1):
        if L[j]<=sl: return (-1.0,j,sl)
    return ((C[end]-entry)/(entry-sl),end,C[end])
Dr=Path("/Users/cristrein/tradingview-mcp/my-strategy/research/revalidation/XAU_4H_L2_BPT_BOS_CHOCH/v1/results")
V2=[]  # reconstrói os 17 zona-pura (= phase49)
for r in csv.DictReader(open(Dr/"l2_bpt_regua_structural.csv")):
    bi=int(r["bar_idx"]);t=T[bi];idx=seg_idx(t)
    if idx is None or idx==0: continue
    s=segs[idx];prev=segs[idx-1];entry=float(r["entry"]);sl=float(r["sl"]);amp=prev['hi']-prev['lo']
    ztop=(prev['hi']-amp/3,prev['hi']);zdeep=bear_deep(idx)
    i0=bisect.bisect_left(T,s['start']);rmin=min(L[i0:bi+1]);rmax=max(H[i0:bi+1]);pos=(entry-rmin)/(rmax-rmin) if rmax>rmin else .5
    keep=(s['regime']=='BULL' and ztop[0]<=entry<=ztop[1]) or (s['regime']=='BEAR' and zdeep and zdeep[0]<=entry<=zdeep[1]) or (s['regime']=='RANGE' and pos<0.34)
    if not keep or entry-sl<=0: continue
    capit = (s['regime']=='BEAR') or (s['regime']=='RANGE' and pos<0.25)  # fundo profundo
    V2.append({"bi":bi,"date":dt.datetime.utcfromtimestamp(t).strftime("%Y-%m-%d"),"reg":s['regime'],"pos":round(pos,2),
               "entry":entry,"sl":sl,"capit":capit,"letrun_csv":round(float(r["letrun_struct"])-COST,2)})
V2.sort(key=lambda x:x['bi'])
print(f"{'#':2} {'date':11} {'reg':5} {'pos':5} {'CAPIT':6} {'R_csv':6} {'R_real':6} {'exit_date':11} {'barras':6}")
plot=[]
for i,x in enumerate(V2,1):
    R,ej,ep=letrun_real(x['bi'],x['entry'],x['sl'])
    R=round(R-COST,2);edate=dt.datetime.utcfromtimestamp(T[ej]).strftime("%Y-%m-%d");nb=ej-x['bi']
    tag="CAPIT" if x['capit'] else ""
    print(f"{i:2} {x['date']:11} {x['reg']:5} {x['pos']:5} {tag:6} {x['letrun_csv']:+6.2f} {R:+6.2f} {edate:11} {nb:6}")
    risk=x['entry']-x['sl'];ej_vis=max(ej,min(x['bi']+4,n4-1))  # largura mínima 4 barras p/ não colapsar
    plot.append({"bi":x['bi'],"date":x['date'],"reg":x['reg'],"capit":x['capit'],"R":R,
        "entry_time":T[x['bi']],"exit_time":T[ej_vis],"exit_price":round(ep,2),"entry":round(x['entry'],2),
        "stopLevel":int(round(risk/MT)),"profitLevel":int(round(max(R,0.5)*risk/MT)),"win":R>0})
json.dump(plot,open("/tmp/v2_capit_letrun.json","w"))
cap=[x for x in V2 if x['capit']]
print(f"\nCAPITULAÇÃO: {len(cap)} trades | não-capit: {len(V2)-len(cap)} | total {len(V2)}")
print(f"sumR total (let-run real): {sum(p['R'] for p in plot):+.1f}  |  só capitulação: {sum(p['R'] for p in plot if p['capit']):+.1f}")
