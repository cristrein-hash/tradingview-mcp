#!/usr/bin/env python3
"""_DA_ orphan-guard repro: audit phase44 FASE B range->bull breakout (buf 0.5).
Question: momentum edge or beta/buy-and-hold like the range-reteste?
Checks: (1) held-vs-stop split + sumR by outcome, (2) drop-top-1/2/3, (3) causality."""
import json,io,contextlib,sys,bisect,datetime as dt
from pathlib import Path
COST=0.35;HZ=120
VAL=Path("/Users/cristrein/tradingview-mcp/regime_turnstate_engine/validation");sys.path.insert(0,str(VAL))
with contextlib.redirect_stdout(io.StringIO()): import phase10_hybrid_regime as P
reg=P.run(0.03,1.15,0.88);T=P.T;H=P.H;L=P.L;C=P.C;n4=len(C)
def atrb(i,k=14): return sum(max(H[j]-L[j],abs(H[j]-C[j-1]),abs(L[j]-C[j-1])) for j in range(i-k+1,i+1))/k
segs=sorted(json.load(open("/tmp/causal_segments_v10.json")),key=lambda s:s['start'])

def letrun_detail(bi,entry,sl):
    """Return (R, outcome, bars_held) where outcome in {'stop','held120','ended_early'}."""
    if entry-sl<=0: return None
    end=min(bi+HZ,n4-1)
    for j in range(bi+1,end+1):
        if L[j]<=sl:
            return (-1.0,'stop',j-bi)
    # survived to end. Is 'end' the HZ120 cap or the data cap?
    outcome='held120' if end==bi+HZ else 'ended_early'
    return ((C[end]-entry)/(entry-sl),outcome,end-bi)

def breakouts(buf):
    out=[]
    for idx in range(len(segs)):
        s=segs[idx]
        if s['regime']!='RANGE': continue
        i0=bisect.bisect_left(T,s['start']);i1=bisect.bisect_right(T,s['end'])-1
        if i1-i0<6: continue
        for j in range(i0+4,i1+1):
            top=max(H[i0:j-2])
            if C[j]>top+0.5*atrb(j):
                entry=C[j];sl=top-buf*atrb(j)
                d=letrun_detail(j,entry,sl)
                if d is not None:
                    R,outcome,held=d
                    out.append({"date":dt.datetime.utcfromtimestamp(T[j]).strftime("%Y-%m-%d"),
                                "yr":dt.datetime.utcfromtimestamp(T[j]).year,
                                "R":round(R-COST,2),"outcome":outcome,"held":held,
                                "own_high_leaks": H[j]>top})  # does current bar high exceed level? (info only)
                break
    return out

def stats(g):
    n=len(g);w=sum(1 for x in g if x['R']>0);s=sum(x['R'] for x in g)
    return n,w,s

e=breakouts(0.5)
print(f"=== buf 0.5: N={len(e)} ===")
n,w,s=stats(e)
print(f"total: N={n} WR={100*w/n:.0f}% sumR={s:+.1f} avgR={s/n:+.2f}")

# (1) held vs stop
print("\n--- (1) OUTCOME SPLIT ---")
for oc in ('stop','held120','ended_early'):
    g=[x for x in e if x['outcome']==oc]
    if g:
        gs=sum(x['R'] for x in g)
        print(f"  {oc:12} N={len(g):2} sumR={gs:+6.1f}  (dates: {[x['date'] for x in g]})")
held=[x for x in e if x['outcome']!='stop']
stop=[x for x in e if x['outcome']=='stop']
print(f"  HELD-to-cap total: N={len(held)} sumR={sum(x['R'] for x in held):+.1f}")
print(f"  STOPPED total:     N={len(stop)} sumR={sum(x['R'] for x in stop):+.1f}")
# distribution of held-winner sizes
print(f"  held R values (sorted): {sorted([round(x['R'],1) for x in held])}")

# (2) drop-top
print("\n--- (2) DROP-TOP concentration ---")
srt=sorted(e,key=lambda z:z['R'],reverse=True)
print(f"  top R trades: {[(x['date'],x['R']) for x in srt[:4]]}")
for k in (0,1,2,3):
    rem=srt[k:]
    print(f"  drop-top-{k}: N={len(rem)} sumR={sum(x['R'] for x in rem):+.1f} avgR={sum(x['R'] for x in rem)/len(rem):+.2f}")

# (3) causality one-liner check
print("\n--- (3) CAUSALITY ---")
leaks=[x for x in e if x['own_high_leaks']]
print(f"  breakouts where current bar's own high H[j] > level top=max(H[i0:j-2]): {len(leaks)}/{len(e)}")
print(f"    (level uses H up to j-3 inclusive, so H[j],H[j-1],H[j-2] excluded from top -> no leak from own bar into the LEVEL)")
print(f"    entry=C[j] (close of breakout bar, known at close), SL & exit strictly forward (j+1..). trigger C[j]>top.")

# buffer decay confirm
print("\n--- buffer sensitivity (SL-matters => momentum) ---")
for buf in (0.5,1.0,1.5):
    g=breakouts(buf);n,w,s=stats(g)
    print(f"  buf {buf}: N={n} WR={100*w/n:.0f}% sumR={s:+.1f} stops={sum(1 for x in g if x['outcome']=='stop')}")
