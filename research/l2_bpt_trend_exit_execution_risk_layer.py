#!/usr/bin/env python3
"""L2/BPT trend-exit — EXECUTION/RISK LAYER (prereg L2_BPT_TREND_EXIT_EXECUTION_RISK_PREREG_20260708).
Testa familias de risco PRE-REGISTADAS sobre a estrategia aprovada (regime-flip), SELECT-17 e FULL-base,
com painel completo. NAO otimiza best-of-N; reporta TODAS as variantes (incl. negativas). Fail-loud se baseline
nao bate. RAW-first (RAW 4H + regua SL_CONTEXT). Zero RAW write, zero producao, deterministico. custo 0.35R."""
import sys, io, contextlib, csv, json, bisect, datetime as dt, statistics as st
from pathlib import Path
REPO=Path("/Users/cristrein/tradingview-mcp")
sys.path.insert(0,str(REPO/"regime_turnstate_engine/validation")); sys.path.insert(0,str(REPO))
with contextlib.redirect_stdout(io.StringIO()):
    import phase48_bear_deep_zone as Q
segs=Q.segs; keep=Q.keep; tr=Q.tr
SEL17=sorted({x['bi'] for x in tr if keep(x)})
bars=[json.loads(l) for l in open(REPO/"my-strategy/research/revalidation/raw_4h_ohlc.jsonl") if l.strip()]
def g(b,*k):
    for kk in k:
        if kk in b:return b[kk]
H=[float(g(b,'h','high')) for b in bars];L=[float(g(b,'l','low')) for b in bars];C=[float(g(b,'c','close')) for b in bars];T=[int(g(b,'t','time','ts')) for b in bars];N=len(bars)
SEG_START=[s['start'] for s in segs]
def regime_at(j):
    i=bisect.bisect_right(SEG_START,T[j])-1
    return segs[i]['regime'] if 0<=i<len(segs) else 'RANGE'
RG=[r for r in csv.DictReader(open(REPO/"my-strategy/research/revalidation/XAU_4H_L2_BPT_BOS_CHOCH/v1/results/l2_bpt_regua_structural.csv"))]
COST=0.35;CAP=500

def sim(bi,entry,sl,cap=CAP,gap_extra=0.0,wide=80,partial_at=None):
    """regime-flip stop-first. Devolve dict(R,exit_bar,mot,hold,risk_pts).
    gap_extra: perda extra em R nos STOP com risco-pontos>wide (modelo de gap). partial_at: 50% em +R antes de sair."""
    risk=entry-sl; half_done=False; realized=0.0
    for j in range(bi+1,min(bi+cap,N-1)+1):
        # partial: metade sai em +partial_at R (por HIGH), SL da outra metade -> BE
        if partial_at is not None and not half_done and H[j]>=entry+partial_at*risk:
            realized+=0.5*(partial_at-COST); half_done=True; sl=entry  # BE na metade restante
        if L[j]<=sl:
            base=-1.0 if not half_done else (0.0)  # se ja fez partial e SL=BE -> ~0
            R=base-COST
            if not half_done and (entry-sl_orig(bi))>=0 and risk_pts(bi)>wide: R-=gap_extra
            tot=realized + (0.5 if half_done else 1.0)*R
            return dict(bi=bi,R=round(tot,2),exit_bar=j,mot="STOP",hold=j-bi,risk_pts=round(risk_pts(bi),1))
        if regime_at(j)=='BEAR':
            r=(C[j]-entry)/risk-COST; tot=realized+(0.5 if half_done else 1.0)*r
            return dict(bi=bi,R=round(tot,2),exit_bar=j,mot="BEAR",hold=j-bi,risk_pts=round(risk_pts(bi),1))
    ej=min(bi+cap,N-1); r=(C[ej]-entry)/risk-COST; tot=realized+(0.5 if half_done else 1.0)*r
    return dict(bi=bi,R=round(tot,2),exit_bar=ej,mot="CAP",hold=ej-bi,risk_pts=round(risk_pts(bi),1))
_RGmap={int(r['bar_idx']):r for r in RG}
def risk_pts(bi): rr=_RGmap[bi]; return abs(float(rr['entry'])-float(rr['sl']))
def sl_orig(bi): return float(_RGmap[bi]['sl'])

def panel(rows):
    if not rows: return dict(N=0)
    n=len(rows);s=sum(x['R'] for x in rows);w=sum(1 for x in rows if x['R']>0)
    cum=peak=dd=0;stk=mx=0
    for x in sorted(rows,key=lambda z:z['bi']):
        cum+=x['R'];peak=max(peak,cum);dd=min(dd,cum-peak);stk=stk+1 if x['R']<=0 else 0;mx=max(mx,stk)
    holds=[x['hold'] for x in rows]
    return dict(N=n,sumR=round(s,1),WR=round(100*w/n),maxDD=round(dd,1),streak=mx,
                retDD=round(s/abs(dd),1) if dd<0 else None,avg_hold=round(st.mean(holds)),max_hold=max(holds),
                exposure_days=round(sum(holds)*4/24),worst=round(min(x['R'] for x in rows),2))

def base_rows(universe, **kw):
    return [sim(int(r['bar_idx']),float(r['entry']),float(r['sl']),**kw) for r in RG if int(r['bar_idx']) in universe]

# ---- sequence rules (skip entries por estado) ----
def apply_dd_guard(rows, dd_stop):
    rows=sorted(rows,key=lambda z:z['bi']);kept=[];cum=peak=0;halt=False
    for x in rows:
        if halt:
            if cum>=peak: halt=False       # retoma no novo pico (aqui cum nao muda; simplif: retoma sempre proxima)
        if not halt:
            kept.append(x);cum+=x['R'];peak=max(peak,cum)
            if cum-peak<=dd_stop: halt=True
    return kept
def apply_streak_pause(rows, nlose):
    rows=sorted(rows,key=lambda z:z['bi']);kept=[];run=0;skip=False
    for x in rows:
        if skip:
            skip=False  # pausa 1 trade apos streak; retoma
        kept.append(x)
        run=run+1 if x['R']<=0 else 0
        if run>=nlose: skip=True
    return kept
def apply_concurrent(rows, K):
    rows=sorted(rows,key=lambda z:z['bi']);kept=[]
    for x in rows:
        open_now=sum(1 for y in kept if y['bi']<=x['bi']<y['exit_bar'])
        if open_now<K: kept.append(x)
    return kept

UNI={'SELECT-17':set(SEL17),'FULL-245':set(int(r['bar_idx']) for r in RG)}
VARIANTS=[
  ('BASELINE regime-flip cap500', lambda u: base_rows(u)),
  ('hold-cap 360', lambda u: base_rows(u,cap=360)),
  ('hold-cap 240', lambda u: base_rows(u,cap=240)),
  ('stop-width cap <=100pt', lambda u: [x for x in base_rows(u) if x['risk_pts']<=100]),
  ('stop-width cap <=80pt',  lambda u: [x for x in base_rows(u) if x['risk_pts']<=80]),
  ('stop-width cap <=60pt',  lambda u: [x for x in base_rows(u) if x['risk_pts']<=60]),
  ('gap-buffer -0.5R (stops>80pt)', lambda u: base_rows(u,gap_extra=0.5,wide=80)),
  ('gap-buffer -1.0R (stops>80pt)', lambda u: base_rows(u,gap_extra=1.0,wide=80)),
  ('partial 50%@+2R + BE', lambda u: base_rows(u,partial_at=2.0)),
  ('DD-guard halt@-15R', lambda u: apply_dd_guard(base_rows(u),-15)),
  ('streak-pause after 3', lambda u: apply_streak_pause(base_rows(u),3)),
  ('max-concurrent 2', lambda u: apply_concurrent(base_rows(u),2)),
  ('max-concurrent 1', lambda u: apply_concurrent(base_rows(u),1)),
]
# fail-loud baseline
b17=panel(base_rows(UNI['SELECT-17']));bF=panel(base_rows(UNI['FULL-245']))
assert abs(b17['sumR']-105.3)<0.6, f"BASELINE 17 nao bate: {b17['sumR']}"
assert b17['maxDD']==-4.1 and b17['streak']==3, f"BASELINE 17 DD/streak: {b17}"
print("BASELINE OK · SELECT-17",b17['sumR'],"maxDD",b17['maxDD'],"streak",b17['streak'],"| FULL-245",bF['sumR'],"maxDD",bF['maxDD'],"streak",bF['streak'])
print("="*118)
out=[]
def six(u,rows):
    r=[x for x in rows if x['bi']==5875]  # #6 bar_idx
    return r[0]['R'] if r else None
for name,fn in VARIANTS:
    line={'variant':name}
    for un in ('SELECT-17','FULL-245'):
        rows=fn(UNI[un]);p=panel(rows);p['#6']=six(un,rows)
        line[un]=p
    out.append(line)
    p17=line['SELECT-17'];pF=line['FULL-245']
    print(f"\n{name}")
    print(f"  SELECT-17: N={p17['N']:2} sumR={p17['sumR']:+7} WR={p17['WR']}% maxDD={p17['maxDD']:6} streak={p17['streak']:2} retDD={p17['retDD']} maxHold={p17['max_hold']} expoDias={p17['exposure_days']} worst={p17['worst']} #6={p17['#6']}")
    print(f"  FULL-245 : N={pF['N']:3} sumR={pF['sumR']:+7} WR={pF['WR']}% maxDD={pF['maxDD']:6} streak={pF['streak']:2} retDD={pF['retDD']} maxHold={pF['max_hold']} expoDias={pF['exposure_days']} worst={pF['worst']}")
json.dump(out,open(REPO/"research/results/l2_bpt_trend_exit_execution_risk_summary.json","w"),indent=1,default=str)
with open(REPO/"research/results/l2_bpt_trend_exit_execution_risk_results.csv","w",newline="") as fh:
    w=csv.writer(fh);w.writerow(['variant','universe','N','sumR','WR','maxDD','streak','retDD','avg_hold','max_hold','exposure_days','worst','#6'])
    for line in out:
        for un in ('SELECT-17','FULL-245'):
            p=line[un];w.writerow([line['variant'],un,p['N'],p['sumR'],p['WR'],p['maxDD'],p['streak'],p['retDD'],p.get('avg_hold'),p.get('max_hold'),p.get('exposure_days'),p['worst'],p['#6'] if un=='SELECT-17' else ''])
print("\nsaved results/l2_bpt_trend_exit_execution_risk_{results.csv,summary.json} · SEM veredito — DA arbitra")
