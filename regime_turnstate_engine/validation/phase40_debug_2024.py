#!/usr/bin/env python3
"""Cris: 2024 PIORA (+13,9->+6,5) mas NÃO há BEAR em 2024 -> skip-bear-faca não pode cortar nada lá.
Abrir 2024 trade-a-trade: regime, is_first(bull), dist, keep_full?, R, e QUAL camada corta cada um.
Descobrir se é custo real do cap-bull (corta winners bull-tardios) ou bug de atribuição."""
import json,csv,io,contextlib,sys,datetime as dt
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
    nb=[segs[j]['lo'] for j in range(idx) if segs[j]['lo']<entry]
    nearest=(entry-max(nb))/a if nb else 99
    rsi=(raw.get(int(t)) or {}).get("rsi") or 50
    tr.append({"bi":bi,"t":t,"yr":dt.datetime.utcfromtimestamp(t).year,"reg":s['regime'],"segkey":idx,
               "dist":dist,"nb":nearest,"rsi":rsi,"R":round(float(r["letrun_struct"])-0.35,2)})
tr.sort(key=lambda x:x['bi'])
byseg=defaultdict(list)
for x in tr: byseg[x['segkey']].append(x)
for k,g in byseg.items():
    g.sort(key=lambda z:z['bi'])
    for i,z in enumerate(g): z['first']=(i==0);z['ord']=i;z['nseg']=len(g)
def bear_capit(x): return x['reg']=='BEAR' and x['dist']<=-2 and x['nb']<=14 and x['rsi']<=60
def keep(x):
    if x['reg']=='BEAR': return bear_capit(x)
    if x['reg']=='BULL': return x['first']
    return True
def why_cut(x):
    if x['reg']=='BEAR' and not bear_capit(x): return "SKIP bear-faca"
    if x['reg']=='BULL' and not x['first']: return f"SKIP bull-tardia (ord {x['ord']}/{x['nseg']})"
    return ""
t24=[x for x in tr if x['yr']==2024]
print(f"2024: {len(t24)} trades | por regime: {dict((r,sum(1 for x in t24 if x['reg']==r)) for r in ('BULL','RANGE','BEAR'))}")
print(f"BASE 2024 sumR={sum(x['R'] for x in t24):+.1f} | FULL 2024 sumR={sum(x['R'] for x in t24 if keep(x)):+.1f}\n")
print(f"{'date':11} {'reg':5} {'first':5} {'dist':>5} {'R':>6} keep? razão-de-corte")
cut_sum=0
for x in t24:
    kp=keep(x);w=why_cut(x)
    if not kp: cut_sum+=x['R']
    print(f"{dt.datetime.utcfromtimestamp(x['t']).strftime('%Y-%m-%d'):11} {x['reg']:5} {str(x['first']):5} {x['dist']:5.1f} {x['R']:+6.1f} {'KEEP' if kp else 'CUT '} {w}")
print(f"\n>>> 2024 cortados somam R = {cut_sum:+.1f} (isto é o que 2024 perde)")
# os blocos BULL de 2024: 1ª vs tardias, para ver se cap-bull corta winners
print("\n### blocos BULL 2024 — 1ª (keep) vs tardias (cut): o cap-bull corta winners? ###")
for k,g in sorted(byseg.items()):
    if g[0]['yr']!=2024 or g[0]['reg']!='BULL': continue
    fr=g[0];tard=g[1:]
    print(f"  bloco BULL {dt.datetime.utcfromtimestamp(fr['t']).strftime('%Y-%m-%d')} n={len(g)}: 1ª R{fr['R']:+.1f}(keep) | tardias R={sum(x['R'] for x in tard):+.1f} n{len(tard)}(cut) -> {'CORTA WINNERS' if sum(x['R'] for x in tard)>0 else 'corta losers ok'}")
