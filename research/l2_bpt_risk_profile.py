#!/usr/bin/env python3
"""L2/BPT trend-exit (APROVADO) — PERFIL DE RISCO da estrategia aprovada (17-selecao, regime-flip).
Caracterizacao (nao lab novo): por-trade R, risco-pontos, hold-barras, motivo-saida, DD/streak driver,
sobreposicao (posicoes concorrentes) e exposicao a gap (stops largos). Base para desenhar a camada exec/risco.
Read-only sobre a estrategia aprovada. Reproduz o regime-flip ja commitado (l2_bpt_trailing_exit_test.py)."""
import sys, io, contextlib, csv, json, bisect, datetime as dt, statistics as st
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
H=[float(g(b,'h','high')) for b in bars];L=[float(g(b,'l','low')) for b in bars];C=[float(g(b,'c','close')) for b in bars];T=[int(g(b,'t','time','ts')) for b in bars];N=len(bars)
SEG_START=[s['start'] for s in segs]
def regime_at(j):
    i=bisect.bisect_right(SEG_START,T[j])-1
    return segs[i]['regime'] if 0<=i<len(segs) else 'RANGE'
RG={int(r['bar_idx']):r for r in csv.DictReader(open(REPO/"my-strategy/research/revalidation/XAU_4H_L2_BPT_BOS_CHOCH/v1/results/l2_bpt_regua_structural.csv"))}
COST=0.35;CAP=500
def d(j): return dt.datetime.utcfromtimestamp(T[j]).strftime('%Y-%m-%d')
def regime_flip(bi,entry,sl):
    for j in range(bi+1,min(bi+CAP,N-1)+1):
        if L[j]<=sl: return (-1.0-COST, j, "STOP")
        if regime_at(j)=='BEAR': return ((C[j]-entry)/(entry-sl)-COST, j, "BEAR")
    ej=min(bi+CAP,N-1); return ((C[ej]-entry)/(entry-sl)-COST, ej, "CAP")
rows=[]
for bi in sorted(SEL17):
    r=RG[bi];entry=float(r['entry']);sl=float(r['sl']);risk=abs(entry-sl)
    R,ej,mot=regime_flip(bi,entry,sl)
    rows.append(dict(bi=bi,entry_d=d(bi),exit_d=d(ej),reg=next(x['reg'] for x in tr if x['bi']==bi),
                     risk_pts=round(risk,1),R=round(R,2),mot=mot,hold_bars=ej-bi,exit_bar=ej))
rows.sort(key=lambda x:x['bi'])
print("="*100);print("L2/BPT trend-exit APROVADO — PERFIL DE RISCO (17-selecao)");print("="*100)
print(f"{'entry':<11}{'exit':<11}{'reg':<6}{'risk_pt':>8}{'R':>7}{'motivo':>7}{'hold_bars':>10}{'hold_dias':>10}")
for x in rows:
    print(f"{x['entry_d']:<11}{x['exit_d']:<11}{x['reg']:<6}{x['risk_pts']:>8}{x['R']:>+7}{x['mot']:>7}{x['hold_bars']:>10}{x['hold_bars']*4//24:>10}")
# DD/streak
cum=peak=dd=0;stk=mx=0
for x in rows:
    cum+=x['R'];peak=max(peak,cum);dd=min(dd,cum-peak);stk=stk+1 if x['R']<=0 else 0;mx=max(mx,stk)
print("-"*100)
print(f"N={len(rows)} sumR={sum(x['R'] for x in rows):+.1f} maxDD={dd:.1f}R streak(perdas)={mx}")
# risco em pontos (stops largos)
rp=[x['risk_pts'] for x in rows]
print(f"\nRISCO EM PONTOS: min={min(rp)} med={st.median(rp):.0f} max={max(rp)} | stops largos (>80pt): {[(x['entry_d'],x['risk_pts']) for x in rows if x['risk_pts']>80]}")
# holding
hb=[x['hold_bars'] for x in rows]
print(f"HOLD: med={st.median(hb):.0f} barras (~{st.median(hb)*4//24:.0f}d) max={max(hb)} (~{max(hb)*4//24}d) | trades no CAP-500: {sum(1 for x in rows if x['mot']=='CAP')} | saidas: STOP={sum(1 for x in rows if x['mot']=='STOP')} BEAR={sum(1 for x in rows if x['mot']=='BEAR')} CAP={sum(1 for x in rows if x['mot']=='CAP')}")
# sobreposicao (posicoes concorrentes)
maxconc=0
for x in rows:
    conc=sum(1 for y in rows if y['bi']<=x['bi']<y['exit_bar'])
    maxconc=max(maxconc,conc)
print(f"SOBREPOSICAO: max posicoes concorrentes (holds simultaneos) = {maxconc}")
json.dump(rows,open(REPO/"research/results/l2_bpt_risk_profile.json","w"),indent=1)
print("\nsaved research/results/l2_bpt_risk_profile.json · caracterizacao p/ desenhar camada exec/risco")
