#!/usr/bin/env python3
"""_DA repro/audit of phase43_range_retest_entry.py — 3 checks only:
1) buffer sweep {0.5,1.0,1.5,2.0,2.5,3.0,4.0} with STOP-COUNT per buffer (edge vs buy-and-hold-in-disguise)
2) causality one-liner (level from PRIOR seg, entry@retest close, SL/exit forward-only)
3) concentration (big winners @1.5, drop-biggest)
Mirrors find() logic EXACTLY. Orphan-guard on deps."""
import json,io,contextlib,sys,bisect,datetime as dt,os
from pathlib import Path

# ---- orphan-guard ----
SEG="/tmp/causal_segments_v10.json"
VAL=Path("/Users/cristrein/tradingview-mcp/regime_turnstate_engine/validation")
if not os.path.exists(SEG):
    sys.exit(f"ORPHAN-GUARD: {SEG} missing — abort")
if not (VAL/"phase10_hybrid_regime.py").exists():
    sys.exit("ORPHAN-GUARD: phase10_hybrid_regime.py missing — abort")

COST=0.35;HZ=120
sys.path.insert(0,str(VAL))
with contextlib.redirect_stdout(io.StringIO()): import phase10_hybrid_regime as P
reg=P.run(0.03,1.15,0.88);T=P.T;H=P.H;L=P.L;C=P.C;n4=len(C)
def atrb(i,k=14): return sum(max(H[j]-L[j],abs(H[j]-C[j-1]),abs(L[j]-C[j-1])) for j in range(i-k+1,i+1))/k
segs=sorted(json.load(open(SEG)),key=lambda s:s['start'])

def letrun(bi,entry,sl):
    """returns (R, stopped_bool). R = None if invalid."""
    if entry-sl<=0: return None,None
    end=min(bi+HZ,n4-1)
    for j in range(bi+1,end+1):
        if L[j]<=sl: return -1.0,True
    return (C[end]-entry)/(entry-sl),False

def find(buf):
    out=[]
    for idx in range(1,len(segs)):
        s=segs[idx]
        if s['regime']!='RANGE': continue
        niv=segs[idx-1]['lo']
        i0=bisect.bisect_left(T,s['start']);i1=bisect.bisect_right(T,s['end'])-1
        if i1-i0<3: continue
        if C[i0]<=niv: continue
        rj=None
        for j in range(i0+1,i1+1):
            if L[j]<=niv: rj=j;break
        if rj is None: continue
        a=atrb(rj);entry=C[rj];sl=niv-buf*a
        R,stopped=letrun(rj,entry,sl)
        if R is None: continue
        out.append({"date":dt.datetime.utcfromtimestamp(T[rj]).strftime("%Y-%m-%d"),
                    "niv":round(niv,0),"entry":round(entry,0),"atr":round(a,1),
                    "sl":round(sl,0),"stopped":stopped,"R":round(R-COST,2)})
    return out

print("=== CHECK 1: BUFFER SWEEP + STOP-COUNT ===")
print(f"{'buf':>4} {'N':>2} {'stops':>5} {'held':>4} {'WR%':>4} {'sumR':>7} {'avgR':>6}")
per_buf={}
for buf in (0.5,1.0,1.5,2.0,2.5,3.0,4.0):
    e=find(buf);per_buf[buf]=e
    n=len(e)
    if n==0: print(f"{buf:>4} 0 entries");continue
    stops=sum(1 for x in e if x['stopped']);held=n-stops
    w=sum(1 for x in e if x['R']>0);s=sum(x['R'] for x in e)
    print(f"{buf:>4} {n:>2} {stops:>5} {held:>4} {100*w/n:>4.0f} {s:>+7.1f} {s/n:>+6.2f}")

print("\n=== CHECK 3: CONCENTRATION @ buf=1.5 ===")
e=sorted(per_buf[1.5],key=lambda z:z['R'],reverse=True)
print("per-trade (sorted by R desc):")
for x in e:
    print(f"   {x['date']} entry {x['entry']:.0f} demanda {x['niv']:.0f} sl {x['sl']:.0f} "
          f"stopped={str(x['stopped']):5} R {x['R']:+.2f}")
s=sum(x['R'] for x in e);n=len(e)
print(f"  full: N={n} sumR={s:+.1f} avgR={s/n:+.2f}")
for k in (1,2,3):
    drop=e[k:];sd=sum(x['R'] for x in drop);nd=len(drop)
    print(f"  drop top-{k}: N={nd} sumR={sd:+.1f} avgR={sd/nd:+.2f}")

print("\n=== CHECK 1b: how much of sumR is unrealized run vs realized stops ===")
for buf in (1.5,2.0,3.0,4.0):
    e=per_buf[buf];held=[x for x in e if not x['stopped']]
    if not e: continue
    print(f"  buf {buf}: held-sumR={sum(x['R'] for x in held):+.1f} (from {len(held)} held) "
          f"stop-sumR={sum(x['R'] for x in e if x['stopped']):+.1f}")
