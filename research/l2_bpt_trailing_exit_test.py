#!/usr/bin/env python3
"""L2/BPT — EXIT por GESTÃO DE TENDÊNCIA (causal): trail estrutural (higher-low) + regime-flip vs let-run HZ120.
Cris (2026): em macro-regime BULL o exit segue a tendência (segura enquanto estrutura aguenta, sai na quebra) —
nível de saída conhecido barra-a-barra, ZERO look-ahead. Testa no FULL-BASE (régua inteira) E na seleção-17,
para separar edge real de overfit. Regras PRÉ-REGISTADAS. custo 0.35R. Fonte: RAW 4H + régua (entry/sl/risk)."""
import sys, io, contextlib, csv, json, bisect
from pathlib import Path
REPO=Path("/Users/cristrein/tradingview-mcp")
sys.path.insert(0,str(REPO/"regime_turnstate_engine/validation")); sys.path.insert(0,str(REPO))
with contextlib.redirect_stdout(io.StringIO()):
    import phase48_bear_deep_zone as Q
segs=Q.segs; keep=Q.keep; tr=Q.tr
SEL17={x['bi'] for x in tr if keep(x)}
bars=[json.loads(l) for l in open(REPO/"my-strategy/research/revalidation/raw_4h_ohlc.jsonl") if l.strip()]
def g(b,*k):
    for kk in k:
        if kk in b:return b[kk]
O=[float(g(b,'o','open')) for b in bars];H=[float(g(b,'h','high')) for b in bars];L=[float(g(b,'l','low')) for b in bars];C=[float(g(b,'c','close')) for b in bars];T=[int(g(b,'t','time','ts')) for b in bars];N=len(bars)
SEG_START=[s['start'] for s in segs]
def regime_at(j):
    i=bisect.bisect_right(SEG_START, T[j])-1
    return segs[i]['regime'] if 0<=i<len(segs) else 'RANGE'
REGUA=[r for r in csv.DictReader(open(REPO/"my-strategy/research/revalidation/XAU_4H_L2_BPT_BOS_CHOCH/v1/results/l2_bpt_regua_structural.csv"))]
COST=0.35; CAP=500
def R_of(entry,sl,exitpx): return (exitpx-entry)/(entry-sl)-COST
def letrun(bi,entry,sl):
    end=min(bi+120,N-1)
    for j in range(bi+1,end+1):
        if L[j]<=sl: return -1.0-COST
    return R_of(entry,sl,C[end])
def regime_flip(bi,entry,sl):
    for j in range(bi+1,min(bi+CAP,N-1)+1):
        if L[j]<=sl: return -1.0-COST
        if regime_at(j)=='BEAR': return R_of(entry,sl,C[j])
    return R_of(entry,sl,C[min(bi+CAP,N-1)])
def is_pivlow(p,lb):
    if p-lb<0 or p+lb>=N: return False
    return all(L[p]<=L[p-k] for k in range(1,lb+1)) and all(L[p]<L[p+k] for k in range(1,lb+1))
def trail_struct(bi,entry,sl,lb=2):
    trail=sl
    for j in range(bi+1,min(bi+CAP,N-1)+1):
        if L[j]<=trail: return R_of(entry,sl,trail if trail>=sl else sl) if trail>sl else (-1.0-COST)
        p=j-lb
        if p>bi and is_pivlow(p,lb) and sl<L[p]<C[j]:
            trail=max(trail,L[p])
    return R_of(entry,sl,C[min(bi+CAP,N-1)])
RULES=[("let-run HZ120",letrun),("regime-flip (→BEAR)",regime_flip),("trail higher-low",trail_struct)]
def panel(rs):
    import statistics as st
    n=len(rs); w=sum(1 for r in rs if r>0); s=sum(rs)
    cum=peak=dd=0; stk=mx=0
    for r in rs:
        cum+=r; peak=max(peak,cum); dd=min(dd,cum-peak); stk=stk+1 if r<=0 else 0; mx=max(mx,stk)
    return f"N={n:3} WR={100*w/n:3.0f}% sumR={s:+7.1f} avgR={s/n:+5.2f} DD={dd:6.1f} retDD={(s/abs(dd) if dd<0 else 0):5.1f}x streak={mx:2}"
print("="*100); print("EXIT por GESTÃO DE TENDÊNCIA (causal) — FULL-BASE vs SELEÇÃO-17"); print("="*100)
for name,fn in RULES:
    full=[fn(int(r['bar_idx']),float(r['entry']),float(r['sl'])) for r in REGUA]
    s17=[fn(int(r['bar_idx']),float(r['entry']),float(r['sl'])) for r in REGUA if int(r['bar_idx']) in SEL17]
    print(f"\n{name:22}")
    print(f"   FULL-BASE({len(full)}): {panel(full)}")
    print(f"   SELEÇÃO-17    : {panel(s17)}")
print("\nLeitura: se trail/regime-flip bate let-run no FULL-BASE (não só nos 17), é edge causal de gestão, não overfit.")
print("Cost 0.35R. Trail e regime conhecidos barra-a-barra (zero look-ahead). SEM veredito — DA arbitra.")
