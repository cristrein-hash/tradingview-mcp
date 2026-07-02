#!/usr/bin/env python3
"""Cris (APROVADO) — NOVA ENTRY (Layer-2): RANGE RETEST do BOTTOM-do-regime-anterior (a demanda).
Espelho da bull-retest (que falhou pq bull DESCOLA) — mas aqui a estrutura SEGURA: o range volta ao bottom-anterior
e reverte (phase36: fundo do range mediana −0.1ATR do nível). Causal: lo_prev conhecido no fecho do regime anterior.
Mecânica: regime RANGE, nível=lo_prev; o range forma-se ACIMA (C[i0]>niv); reteste=1ª barra com low<=niv (pullback à demanda);
entry=close do reteste, SL=niv−buf·ATR (abaixo da demanda), exit=let-run HZ120. 1 entry por range. Testa buffers.
Compara com a bull-retest (assimetria). custo 0.35."""
import json,io,contextlib,sys,bisect,datetime as dt
from pathlib import Path
from collections import defaultdict
COST=0.35;HZ=120
VAL=Path("/Users/cristrein/tradingview-mcp/regime_turnstate_engine/validation");sys.path.insert(0,str(VAL))
with contextlib.redirect_stdout(io.StringIO()): import phase10_hybrid_regime as P
reg=P.run(0.03,1.15,0.88);T=P.T;H=P.H;L=P.L;C=P.C;n4=len(C)
def atrb(i,k=14): return sum(max(H[j]-L[j],abs(H[j]-C[j-1]),abs(L[j]-C[j-1])) for j in range(i-k+1,i+1))/k
segs=sorted(json.load(open("/tmp/causal_segments_v10.json")),key=lambda s:s['start'])
def letrun(bi,entry,sl):
    if entry-sl<=0: return None
    end=min(bi+HZ,n4-1)
    for j in range(bi+1,end+1):
        if L[j]<=sl: return -1.0
    return (C[end]-entry)/(entry-sl)
def find(buf):
    out=[]
    for idx in range(1,len(segs)):
        s=segs[idx]
        if s['regime']!='RANGE': continue
        niv=segs[idx-1]['lo']
        i0=bisect.bisect_left(T,s['start']);i1=bisect.bisect_right(T,s['end'])-1
        if i1-i0<3: continue
        if C[i0]<=niv: continue        # range tem de começar ACIMA da demanda-anterior (reteste vem de cima)
        rj=None
        for j in range(i0+1,i1+1):
            if L[j]<=niv: rj=j;break     # 1º pullback que toca a demanda-anterior
        if rj is None: continue
        a=atrb(rj);entry=C[rj];sl=niv-buf*a
        R=letrun(rj,entry,sl)
        if R is None: continue
        out.append({"date":dt.datetime.utcfromtimestamp(T[rj]).strftime("%Y-%m-%d"),"yr":dt.datetime.utcfromtimestamp(T[rj]).year,
                    "range_start":dt.datetime.utcfromtimestamp(s['start']).strftime("%Y-%m-%d"),
                    "niv":round(niv,0),"entry":round(entry,0),"R":round(R-COST,2)})
    return out
print("NOVA ENTRY — RANGE RETEST do bottom-do-regime-anterior (a demanda), causal\n")
for buf in (0.5,1.0,1.5):
    e=find(buf)
    if not e: print(f"  buf {buf}: 0 entries");continue
    n=len(e);w=sum(1 for x in e if x['R']>0);s=sum(x['R'] for x in e);big=sum(1 for x in e if x['R']>=3)
    print(f"  SL buf={buf}ATR: N={n:2} WR={100*w/n:3.0f}% sumR={s:+6.1f} avgR={s/n:+5.2f} big(>=3R)={big}")
print("\n### detalhe (buf=1.0) ###")
e=find(1.0)
for x in sorted(e,key=lambda z:z['date']):
    print(f"   range {x['range_start']:11} reteste {x['date']:11} demanda {x['niv']:.0f} entry {x['entry']:.0f} R {x['R']:+.1f}")
print("\n### por ano (buf=1.0) ###")
by=defaultdict(list)
for x in e: by[x['yr']].append(x['R'])
for y in sorted(by): print(f"   {y}: N={len(by[y]):2} sumR={sum(by[y]):+6.1f} WR={100*sum(1 for r in by[y] if r>0)/len(by[y]):.0f}%")
