#!/usr/bin/env python3
"""Gera dados de plotagem canónica dos 39 trades do ESQUELETO + RANGE só-FUNDO (perfil segurabilidade: +47,9R DD−8,1 streak6).
Regras: BEAR capitulação-refinada · BULL 1ª+pullback(dist<=3) · RANGE só-fundo(pos<0,34). SL=SL_CONTEXT(régua), let-run.
Convenção: long_position, stopLevel/profitLevel em TICKS (mintick 0,01), alvo +3R, largura 12 barras, borda verde/vermelha."""
import json,csv,io,contextlib,sys,bisect,datetime as dt
from pathlib import Path
MT=0.01
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
rows=[]
for r in csv.DictReader(open(Dr/"results/l2_bpt_regua_structural.csv")):
    bi=int(r["bar_idx"]);t=T[bi];idx=seg_idx(t)
    if idx is None or idx==0: continue
    s=segs[idx];prev=segs[idx-1];a=atrb(bi);entry=float(r["entry"]);sl=float(r["sl"])
    niv=prev['hi'] if s['regime']=='BULL' else prev['lo'];dist=(entry-niv)/a
    nb=[segs[j]['lo'] for j in range(idx) if segs[j]['lo']<entry];nearest=(entry-max(nb))/a if nb else 99
    rsi=(raw.get(int(t)) or {}).get("rsi") or 50
    i0=bisect.bisect_left(T,s['start']);rmin=min(L[i0:bi+1]);rmax=max(H[i0:bi+1]);pos=(entry-rmin)/(rmax-rmin) if rmax>rmin else 0.5
    rows.append({"bi":bi,"t":t,"reg":s['regime'],"segkey":idx,"entry":entry,"sl":sl,"dist":dist,"nb":nearest,"rsi":rsi,"pos":pos,
                 "R":round(float(r["letrun_struct"])-0.35,2)})
rows.sort(key=lambda x:x['bi'])
from collections import defaultdict
byseg=defaultdict(list)
for x in rows: byseg[x['segkey']].append(x)
for k,g in byseg.items():
    g.sort(key=lambda z:z['bi'])
    for i,z in enumerate(g): z['first']=(i==0)
def keep(x):
    if x['reg']=='BEAR': return x['dist']<=-2 and x['nb']<=14 and x['rsi']<=60
    if x['reg']=='BULL': return x['first'] or x['dist']<=3
    return x['pos']<0.34
out=[]
for x in rows:
    if not keep(x): continue
    entry=x['entry'];sl=x['sl'];risk=entry-sl
    if risk<=0: continue
    out.append({"date":dt.datetime.utcfromtimestamp(x['t']).strftime("%Y-%m-%d"),"reg":x['reg'],
        "entry_time":x['t'],"exit_time":x['t']+12*14400,"entry":round(entry,2),"target":round(entry+3*risk,2),
        "stopLevel":int(round(risk/MT)),"profitLevel":int(round(3*risk/MT)),"R":round(x['R'],1),"win":x['R']>0})
json.dump(out,open("/tmp/skeleton_fundo_trades.json","w"))
w=sum(1 for x in out if x['win'])
print(f"esqueleto+só-fundo: {len(out)} trades (win {w}/loss {len(out)-w}) sumR {sum(x['R'] for x in out):+.1f}")
for x in out:
    print(f'{x["entry_time"]}|{x["entry"]}|{x["exit_time"]}|{x["target"]}|{x["stopLevel"]}|{x["profitLevel"]}|{1 if x["win"] else 0}|{x["reg"]}|{x["date"]}')
