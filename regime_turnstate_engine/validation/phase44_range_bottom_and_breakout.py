#!/usr/bin/env python3
"""Cris — arquitetura RANGE em 2 peças (testar em profundidade):
 FASE A (FILTRO): em RANGE, manter só entradas no BOTTOM (pos baixa no range CORRENTE, causal running-min/max até entrada);
   LIMPAR as tardias do MEIO (numerosas, zona-morta). Perde-se o TOPO (breakouts de fim de range).
 FASE B (ENTRY NOVA): breakout de RANGE->BULL — rompe o TOPO estabelecido do range (causal), entry long momentum,
   recupera as boas de fim-de-range que a FASE A corta.
pos = (entry−rmin)/(rmax−rmin) no range corrente. Breakout = close > max(H[i0:j-3]) + 0.5ATR. let-run HZ120, custo 0.35."""
import json,csv,io,contextlib,sys,bisect,datetime as dt
from pathlib import Path
from collections import defaultdict
COST=0.35;HZ=120
VAL=Path("/Users/cristrein/tradingview-mcp/regime_turnstate_engine/validation");sys.path.insert(0,str(VAL))
with contextlib.redirect_stdout(io.StringIO()): import phase10_hybrid_regime as P
reg=P.run(0.03,1.15,0.88);T=P.T;H=P.H;L=P.L;C=P.C;n4=len(C)
def atrb(i,k=14): return sum(max(H[j]-L[j],abs(H[j]-C[j-1]),abs(L[j]-C[j-1])) for j in range(i-k+1,i+1))/k
segs=sorted(json.load(open("/tmp/causal_segments_v10.json")),key=lambda s:s['start'])
def seg_idx(t):
    for i in range(len(segs)):
        if segs[i]['start']<=t<=segs[i]['end']: return i
    return None
def letrun(bi,entry,sl):
    if entry-sl<=0: return None
    end=min(bi+HZ,n4-1)
    for j in range(bi+1,end+1):
        if L[j]<=sl: return -1.0
    return (C[end]-entry)/(entry-sl)
D=Path("/Users/cristrein/tradingview-mcp/my-strategy/research/revalidation/XAU_4H_L2_BPT_BOS_CHOCH/v1/results")
# ---- FASE A: trades RANGE existentes, por pos no range corrente ----
rng=[]
for r in csv.DictReader(open(D/"l2_bpt_regua_structural.csv")):
    bi=int(r["bar_idx"]);t=T[bi];idx=seg_idx(t)
    if idx is None: continue
    s=segs[idx]
    if s['regime']!='RANGE': continue
    i0=bisect.bisect_left(T,s['start']);rmin=min(L[i0:bi+1]);rmax=max(H[i0:bi+1]);entry=float(r["entry"])
    pos=(entry-rmin)/(rmax-rmin) if rmax>rmin else 0.5
    rng.append({"bi":bi,"date":dt.datetime.utcfromtimestamp(t).strftime("%Y-%m-%d"),"pos":pos,"R":round(float(r["letrun_struct"])-COST,2)})
def agg(g,lab):
    if not g: print(f"  {lab:30} N=0");return
    n=len(g);w=sum(1 for x in g if x['R']>0);s=sum(x['R'] for x in g);big=sum(1 for x in g if x['R']>=3)
    print(f"  {lab:30} N={n:3} WR={100*w/n:3.0f}% sumR={s:+6.1f} avgR={s/n:+5.2f} big={big}")
print("FASE A — trades RANGE por POSIÇÃO no range corrente (causal)")
agg(rng,"RANGE todas (base)")
agg([x for x in rng if x['pos']<0.34],"FUNDO (pos<0.34)")
agg([x for x in rng if 0.34<=x['pos']<0.67],"MEIO (0.34-0.67) = tardias")
agg([x for x in rng if x['pos']>=0.67],"TOPO (>=0.67) = breakout-zone")
print("\n  filtros candidatos:")
agg([x for x in rng if x['pos']<0.34],"só FUNDO")
agg([x for x in rng if x['pos']<0.34 or x['pos']>=0.67],"FUNDO+TOPO (skip meio)")
# ---- FASE B: entry NOVA breakout de range->bull ----
def breakouts(buf):
    out=[]
    for idx in range(len(segs)):
        s=segs[idx]
        if s['regime']!='RANGE': continue
        i0=bisect.bisect_left(T,s['start']);i1=bisect.bisect_right(T,s['end'])-1
        if i1-i0<6: continue
        for j in range(i0+4,i1+1):
            top=max(H[i0:j-2])          # topo estabelecido do range (causal, exclui ult. 2 barras)
            if C[j]>top+0.5*atrb(j):
                entry=C[j];sl=top-buf*atrb(j)  # SL no topo-rompido (agora suporte) − buffer
                R=letrun(j,entry,sl)
                if R is not None:
                    out.append({"date":dt.datetime.utcfromtimestamp(T[j]).strftime("%Y-%m-%d"),"yr":dt.datetime.utcfromtimestamp(T[j]).year,"R":round(R-COST,2)})
                break   # 1 breakout por range
    return out
print("\nFASE B — ENTRY NOVA breakout de range->bull (rompe topo estabelecido)")
for buf in (0.5,1.0,1.5):
    e=breakouts(buf)
    if not e: print(f"  buf {buf}: 0");continue
    n=len(e);w=sum(1 for x in e if x['R']>0);s=sum(x['R'] for x in e);big=sum(1 for x in e if x['R']>=3)
    print(f"  SL buf={buf}: N={n:2} WR={100*w/n:3.0f}% sumR={s:+6.1f} avgR={s/n:+5.2f} big={big}")
print("\n  detalhe breakout (buf=1.0):")
for x in sorted(breakouts(1.0),key=lambda z:z['date']): print(f"    {x['date']} R{x['R']:+.1f}")
