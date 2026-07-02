#!/usr/bin/env python3
"""Cris: adicionar trades com GATILHO L2 à lógica V2. Regra (máquina de estado): cada trade V2 acionado ARMA o gatilho
para exatamente 1 trade L2 seguinte (o próximo sinal L2 que NÃO é V2); depois TRAVA até vir o próximo V2, que rearma.
Aumenta N pós-confirmação de forma controlada. Mesmo exit (let-run HZ120 via letrun_struct da régua), custo 0.35.
Percorre os 245 sinais L2 da régua em ordem; marca V2 = zona-pura keep (=phase49/55). Painel completo + por-ano + comparação."""
import json,io,contextlib,sys,bisect,csv,datetime as dt
from pathlib import Path
from collections import defaultdict
COST=0.35
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
Dr=Path("/Users/cristrein/tradingview-mcp/my-strategy/research/revalidation/XAU_4H_L2_BPT_BOS_CHOCH/v1/results")
sig=[]  # todos os sinais L2 da régua, ordenados por bar_idx
for r in csv.DictReader(open(Dr/"l2_bpt_regua_structural.csv")):
    bi=int(r["bar_idx"]);entry=float(r["entry"]);sl=float(r["sl"])
    if entry-sl<=0: continue
    sig.append({"bi":bi,"entry":entry,"sl":sl,"R":round(float(r["letrun_struct"])-COST,2),"v2":is_v2(bi,entry,sl)})
sig.sort(key=lambda x:x['bi'])
# máquina de estado
taken=[];armed=False
for s in sig:
    if s['v2']:
        s['kind']='V2';taken.append(s);armed=True          # V2 aciona e rearma
    elif armed:
        s['kind']='L2';taken.append(s);armed=False           # 1 L2 após V2, depois trava
def panel(rows,tag):
    if not rows: print(f"{tag}: vazio");return
    rows=sorted(rows,key=lambda x:x['bi']);n=len(rows);w=sum(1 for x in rows if x['R']>0);s=sum(x['R'] for x in rows)
    cum=peak=dd=0;st=mx=0
    for x in rows:
        cum+=x['R'];peak=max(peak,cum);dd=min(dd,cum-peak);st=st+1 if x['R']<=0 else 0;mx=max(mx,st)
    print(f"{tag:16} N={n:2} WR={100*w/n:4.0f}% sumR={s:+6.1f} avgR={s/n:+5.2f} DD={dd:5.1f} ret/DD={(s/-dd if dd<0 else 0):5.1f} streak={mx} big(≥3R)={sum(1 for x in rows if x['R']>=3)}")
print("COMPARAÇÃO — V2 base vs V2+L2-após-cada-V2:\n")
panel([s for s in taken if s['kind']=='V2'],"V2 base")
panel([s for s in taken if s['kind']=='L2'],"L2-extra só")
panel(taken,"V2+L2 combinado")
print(f"\nL2-extra acionados: {sum(1 for s in taken if s['kind']=='L2')} (de 17 V2 possíveis armas)")
print("\n### por-ano (combinado) ###")
by=defaultdict(list)
for s in taken: by[dt.datetime.utcfromtimestamp(T[s['bi']]).year].append(s['R'])
for y in sorted(by): print(f"  {y}: N={len(by[y]):2} sumR={sum(by[y]):+6.1f} WR={100*sum(1 for r in by[y] if r>0)/len(by[y]):3.0f}%")
print("\n### sequência (data | tipo | R) ###")
for s in taken: print(f"  {dt.datetime.utcfromtimestamp(T[s['bi']]).strftime('%Y-%m-%d')} | {s['kind']} | {s['R']:+.2f}")
