#!/usr/bin/env python3
"""Cris: formalizar as peças ESTRUTURAIS causais e medir TUDO JUNTO (book completo, painel de viabilidade).
Camadas (todas causais, nível=hi/lo de regimes detectados conhecidos no fecho do anterior):
  BEAR  -> keep SÓ capitulação-refinada: dist<=-2 ao bottom-anterior AND nearest_below<=NB AND rsi<=RS ; resto SKIP (faca)
  BULL  -> cap-tardias: keep 1ª trade do bloco BULL ; resto SKIP
  RANGE -> keep (estrutura não filtra limpo; big-winners espalhados)
⚠️ NB/RS calibrados sobre 11 bear-capit (n minúsculo) = CALIBRAÇÃO in-sample, NÃO validação. Mostro sensibilidade.
raw_features p/ rsi. let-run−0.35. Painel: N·WR·sumR·avgR·DD·maxStreak·runs>=5·big(>=3R)·%meses+ · por-ano."""
import json,csv,io,contextlib,sys,bisect,datetime as dt
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
D=Dr/"results"
tr=[]
for r in csv.DictReader(open(D/"l2_bpt_regua_structural.csv")):
    bi=int(r["bar_idx"]);t=T[bi];idx=seg_idx(t)
    if idx is None or idx==0: continue
    s=segs[idx];prev=segs[idx-1];a=atrb(bi);entry=float(r["entry"])
    niv=prev['hi'] if s['regime']=='BULL' else prev['lo']
    dist=(entry-niv)/a
    los_below=[segs[j]['lo'] for j in range(idx) if segs[j]['lo']<entry]
    nearest_below=(entry-max(los_below))/a if los_below else 99
    rsi=(raw.get(int(t)) or {}).get("rsi") or 50
    R=round(float(r["letrun_struct"])-0.35,2)
    tr.append({"bi":bi,"t":t,"yr":dt.datetime.utcfromtimestamp(t).year,"ym":dt.datetime.utcfromtimestamp(t).strftime("%Y-%m"),
               "reg":s['regime'],"segkey":idx,"dist":dist,"nb":nearest_below,"rsi":rsi,"R":R})
tr.sort(key=lambda x:x['bi'])
# is_first do bloco BULL
byseg=defaultdict(list)
for x in tr: byseg[x['segkey']].append(x)
for k,g in byseg.items():
    g.sort(key=lambda z:z['bi'])
    for i,z in enumerate(g): z['first']=(i==0)
def panel(keepfn,lab):
    k=[x for x in tr if keepfn(x)];k.sort(key=lambda z:z['bi'])
    if not k: print(f"  {lab:38} N=0");return
    n=len(k);w=sum(1 for x in k if x['R']>0);s=sum(x['R'] for x in k);big=sum(1 for x in k if x['R']>=3)
    cum=peak=dd=0;streak=mx=0;runs=[]
    for x in k:
        cum+=x['R'];peak=max(peak,cum);dd=min(dd,cum-peak)
        if x['R']<=0: streak+=1;mx=max(mx,streak)
        else:
            if streak: runs.append(streak)
            streak=0
    if streak: runs.append(streak)
    r5=sum(1 for q in runs if q>=5)
    mth=defaultdict(float)
    for x in k: mth[x['ym']]+=x['R']
    posm=sum(1 for v in mth.values() if v>0);tot=len(mth)
    print(f"  {lab:38} N={n:3} WR={100*w/n:3.0f}% sumR={s:+6.1f} avgR={s/n:+5.2f} DD={dd:6.1f} streak={mx:2} runs>=5:{r5} big={big:2} meses{posm}/{tot}({100*posm/tot:.0f}%+)")
NB,RS=14,60
def bear_capit(x): return x['reg']=='BEAR' and x['dist']<=-2 and x['nb']<=NB and x['rsi']<=RS
def keep_full(x):
    if x['reg']=='BEAR': return bear_capit(x)
    if x['reg']=='BULL': return x['first']
    return True   # RANGE
print(f"BOOK L2/BPT (todos anos, {len(tr)} trades). Camadas estruturais causais. [BEAR-capit NB<={NB} RS<={RS} = calibração n11]\n")
print("### CAMADAS INCREMENTAIS — painel de viabilidade ###")
panel(lambda x:True,"BASE (todos)")
panel(lambda x: not (x['reg']=='BEAR' and not bear_capit(x)),"+ BEAR: keep só capitulação-refinada")
panel(lambda x: not (x['reg']=='BULL' and not x['first']),"+ BULL: cap-tardias (só)")
panel(keep_full,"FULL (BEAR-capit + BULL-cap + RANGE)")
print("\n### por-ano do FULL ###")
for y in (2020,2021,2022,2023,2024,2025,2026):
    ky=[x for x in tr if x['yr']==y and keep_full(x)];by=[x for x in tr if x['yr']==y]
    if by: print(f"  {y}: BASE {sum(x['R'] for x in by):+6.1f}(n{len(by):2}) -> FULL {sum(x['R'] for x in ky):+6.1f}(n{len(ky):2})")
print("\n### sensibilidade do corte da capitulação BEAR (NB, RS) — quantos bear-capit sobram e sumR deles ###")
bearc=[x for x in tr if x['reg']=='BEAR' and x['dist']<=-2]
for nb in (10,14,20,99):
    for rs in (55,60,100):
        g=[x for x in bearc if x['nb']<=nb and x['rsi']<=rs]
        w=sum(1 for x in g if x['R']>0)
        print(f"   NB<={nb:3} RS<={rs:3}: keep {len(g):2} capit ({w}W) sumR {sum(x['R'] for x in g):+5.1f}")
print("\n### as trades BEAR mantidas pelo FULL (a zona de capitulação) ###")
for x in sorted([z for z in tr if bear_capit(z)],key=lambda z:z['bi']):
    print(f"   {dt.datetime.utcfromtimestamp(x['t']).strftime('%Y-%m-%d')} dist{x['dist']:+5.1f} nb{x['nb']:+5.1f} rsi{x['rsi']:.0f} R{x['R']:+5.1f}")
