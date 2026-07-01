#!/usr/bin/env python3
"""DEVIL'S ADVOCATE on phase19 FUNDO=+3.93 finding.
phase19 box_pos uses box['lo']/box['hi'] = min/max over FULL segment (start->END) => HINDSIGHT.
Here we build the CAUSAL counterparts, measured only from data available at/ before the entry bar:
  - causal_pos  = (entry - lo_sofar)/(hi_sofar - lo_sofar)   [so-far bounds from box start to entry bar]
  - dist_atr    = (entry - lo_sofar)/ATR14                    [ATR above demand-low established so far]
Then re-bucket and compare to the hindsight full_pos. Also: drop-top-2, per-year, box-level jackknife.
let-run post-cost 0.35. Reproducible + committable (systematic_error_guards hook)."""
import json,csv,io,contextlib,sys,bisect,datetime as dt
from pathlib import Path
COST=0.35;VAL=Path("/Users/cristrein/tradingview-mcp/regime_turnstate_engine/validation");sys.path.insert(0,str(VAL))
with contextlib.redirect_stdout(io.StringIO()): import phase10_hybrid_regime as P
reg=P.run(0.03,1.15,0.88);T=P.T;H=P.H;L=P.L;C=P.C
segs=json.load(open("/tmp/causal_segments_v10.json"))
def atr(bi):
    tr=[max(H[j]-L[j],abs(H[j]-C[j-1]),abs(L[j]-C[j-1])) for j in range(max(1,bi-13),bi+1)]
    return sum(tr)/len(tr) if tr else 1.0
def box_of(ts):
    c=[s for s in segs if s['start']<=ts<=s['end']];return c[0] if c else None
D=Path("/Users/cristrein/tradingview-mcp/my-strategy/research/revalidation/XAU_4H_L2_BPT_BOS_CHOCH/v1/results")
tr=[]
for r in csv.DictReader(open(D/"l2_bpt_regua_structural.csv")):
    bi=int(r["bar_idx"]);t=T[bi];y=dt.datetime.utcfromtimestamp(t).year
    if y<2023: continue
    box=box_of(t)
    if not box or box['regime']!='RANGE': continue
    entry=float(r["entry"]);R=round(float(r["letrun_struct"])-COST,2)
    si=bisect.bisect_left(T,box['start'])           # bar index of box start
    lo_sofar=min(L[si:bi+1]);hi_sofar=max(H[si:bi+1])
    a=atr(bi)
    causal_pos=(entry-lo_sofar)/(hi_sofar-lo_sofar) if hi_sofar>lo_sofar else 0.5
    dist_atr=(entry-lo_sofar)/a
    full_pos=(entry-box['lo'])/(box['hi']-box['lo']) if box['hi']>box['lo'] else 0.5
    tr.append(dict(date=dt.datetime.utcfromtimestamp(t).strftime("%Y-%m-%d"),R=R,y=y,
        full_pos=full_pos,causal_pos=causal_pos,dist_atr=dist_atr,bars_into=bi-si,
        boxkey=(box['d0'],box['d1'])))
print("n RANGE:",len(tr))
def bucket(key,edges,label):
    print("---",label,"---")
    for a,b in edges:
        g=[x for x in tr if a<=x[key]<b]
        if g: print(f"  [{a:>5.2f},{b:>5.2f}) N={len(g):2} WR={100*sum(1 for x in g if x['R']>0)/len(g):3.0f}% sumR={sum(x['R'] for x in g):+6.1f} avgR={sum(x['R'] for x in g)/len(g):+5.2f}")
bucket('full_pos',[(0,.25),(.25,.5),(.5,.75),(.75,1.01)],"FULL box_pos (HINDSIGHT, phase19)")
bucket('causal_pos',[(0,.25),(.25,.5),(.5,.75),(.75,3.0)],"CAUSAL box_pos (so-far bounds)")
bucket('dist_atr',[(-1,1),(1,2.5),(2.5,4),(4,50)],"CAUSAL dist above demand-low-so-far (ATR)")
# FUNDO drivers: which trades land in hindsight FUNDO, and drop-top-2
fundo=sorted([x for x in tr if x['full_pos']<0.25],key=lambda x:-x['R'])
print("\n--- HINDSIGHT FUNDO 0-0.25 members (sorted by R) ---")
for x in fundo: print(f"  {x['date']} R={x['R']:+6.2f} causal_pos={x['causal_pos']:.2f} dist_atr={x['dist_atr']:+.2f} bars_into={x['bars_into']}")
s=sum(x['R'] for x in fundo);print(f"  full sum={s:+.1f} N={len(fundo)} avg={s/len(fundo):+.2f}")
d2=fundo[2:];print(f"  drop-top-2 sum={sum(x['R'] for x in d2):+.1f} N={len(d2)} avg={sum(x['R'] for x in d2)/len(d2) if d2 else 0:+.2f}")
# per-year for hindsight FUNDO vs mid(0.5-0.75)
print("\n--- per-year: FUNDO(<0.25) vs DEATH(0.5-0.75) hindsight ---")
for y in sorted(set(x['y'] for x in tr)):
    f=[x for x in tr if x['y']==y and x['full_pos']<0.25];m=[x for x in tr if x['y']==y and .5<=x['full_pos']<.75]
    fs=f"N{len(f)} {sum(x['R'] for x in f):+.1f}" if f else "-"
    ms=f"N{len(m)} {sum(x['R'] for x in m):+.1f}" if m else "-"
    print(f"  {y}: FUNDO {fs:14} | DEATH {ms}")
# box-level jackknife on hindsight FUNDO
print("\n--- box-level jackknife: hindsight FUNDO avgR dropping one box at a time ---")
boxes=sorted(set(x['boxkey'] for x in fundo))
for bk in boxes:
    rest=[x for x in fundo if x['boxkey']!=bk]
    print(f"  drop {bk[0]}->{bk[1]}: N={len(rest)} avgR={sum(x['R'] for x in rest)/len(rest) if rest else 0:+.2f}")
