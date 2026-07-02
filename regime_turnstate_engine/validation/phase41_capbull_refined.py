#!/usr/bin/env python3
"""Cris (opção 2): refinar cap-bull com o EIXO ESTRUTURAL. Em BULL, manter 1ª + tardias que são PULLBACK-a-suporte
(dist pequeno/negativo ao top-do-regime-anterior), cortar só as ESTICADAS (dist alto = chasing).
Escolher o corte olhando TODAS as tardias-bull (não só 2024). Medir book + viabilidade + 2024 + por-ano.
Compara: BASE · esqueleto(cap-bull cru=só-1ª) · cap-bull-refinado(THR) · sem-cap-bull. Causal (dist=nível regime anterior)."""
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
    tr.append({"bi":bi,"t":t,"yr":dt.datetime.utcfromtimestamp(t).year,"ym":dt.datetime.utcfromtimestamp(t).strftime("%Y-%m"),
               "reg":s['regime'],"segkey":idx,"dist":dist,"nb":nearest,"rsi":rsi,"R":round(float(r["letrun_struct"])-0.35,2)})
tr.sort(key=lambda x:x['bi'])
byseg=defaultdict(list)
for x in tr: byseg[x['segkey']].append(x)
for k,g in byseg.items():
    g.sort(key=lambda z:z['bi'])
    for i,z in enumerate(g): z['first']=(i==0)
# diagnóstico: tardias-bull por dist
tard=[x for x in tr if x['reg']=='BULL' and not x['first']]
print(f"TARDIAS-BULL (não-1ª): {len(tard)} | dist × R:")
for lab,f in [("dist<=0 (pullback fundo)",lambda d:d<=0),("0..3 (perto suporte)",lambda d:0<d<=3),
              ("3..8",lambda d:3<d<=8),(">8 (esticada)",lambda d:d>8)]:
    g=[x for x in tard if f(x['dist'])]
    if g: print(f"   {lab:24} N={len(g):2} WR={100*sum(1 for x in g if x['R']>0)/len(g):3.0f}% sumR={sum(x['R'] for x in g):+5.1f} avgR={sum(x['R'] for x in g)/len(g):+.2f}")
def bear_capit(x): return x['reg']=='BEAR' and x['dist']<=-2 and x['nb']<=14 and x['rsi']<=60
def panel(keepfn,lab):
    k=[x for x in tr if keepfn(x)];k.sort(key=lambda z:z['bi'])
    n=len(k);w=sum(1 for x in k if x['R']>0);s=sum(x['R'] for x in k);big=sum(1 for x in k if x['R']>=3)
    cum=peak=dd=0;streak=mx=0;runs=[]
    for x in k:
        cum+=x['R'];peak=max(peak,cum);dd=min(dd,cum-peak)
        if x['R']<=0: streak+=1;mx=max(mx,streak)
        else:
            if streak:runs.append(streak)
            streak=0
    if streak:runs.append(streak)
    mth=defaultdict(float)
    for x in k:mth[x['ym']]+=x['R']
    posm=sum(1 for v in mth.values() if v>0);tot=len(mth)
    print(f"  {lab:40} N={n:3} WR={100*w/n:3.0f}% sumR={s:+6.1f} avgR={s/n:+5.2f} DD={dd:6.1f} streak={mx:2} runs>=5:{sum(1 for q in runs if q>=5)} big={big:2} meses{posm}/{tot}({100*posm/tot:.0f}%+)")
def keep_ref(THR):
    def f(x):
        if x['reg']=='BEAR': return bear_capit(x)
        if x['reg']=='BULL': return x['first'] or x['dist']<=THR
        return True
    return f
def keep_cru(x):
    if x['reg']=='BEAR': return bear_capit(x)
    if x['reg']=='BULL': return x['first']
    return True
def keep_nocap(x):
    if x['reg']=='BEAR': return bear_capit(x)
    return True
print("\n### BOOK — comparar cap-bull cru vs refinado (manter tardias pullback dist<=THR) ###")
panel(lambda x:True,"BASE (todos)")
panel(keep_nocap,"sem cap-bull (só bear-capit + range)")
panel(keep_cru,"cap-bull CRU (só 1ª) = esqueleto atual")
for THR in (3,5,8):
    panel(keep_ref(THR),f"cap-bull REFINADO (keep tardia dist<={THR})")
print("\n### 2024 e por-ano — cru vs refinado(THR=3) ###")
for y in (2023,2024,2025,2026):
    b=[x for x in tr if x['yr']==y];cru=[x for x in b if keep_cru(x)];ref=[x for x in b if keep_ref(3)(x)]
    print(f"  {y}: BASE {sum(x['R'] for x in b):+6.1f} | cru {sum(x['R'] for x in cru):+6.1f} | refinado {sum(x['R'] for x in ref):+6.1f}")
