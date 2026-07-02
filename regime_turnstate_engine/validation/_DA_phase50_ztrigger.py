#!/usr/bin/env python3
"""DA repro for phase50_zone_trigger. Orphan-guard: refuses to run if source moved.
Answers 3 things: (1) RANGE beta-or-edge (held/stop split + drop-top on RANGE sumR),
(2) BULL fallback real-or-concentrated (drop-top), (3) causal leak check.
Reuses phase50's exact entry/exit logic by importing its module."""
import json,io,contextlib,sys,bisect
from pathlib import Path
VAL=Path("/Users/cristrein/tradingview-mcp/regime_turnstate_engine/validation")
SRC=VAL/"phase50_zone_trigger.py"
if not SRC.exists():
    sys.exit("ORPHAN-GUARD: phase50_zone_trigger.py not found — source moved, aborting.")
sys.path.insert(0,str(VAL))
with contextlib.redirect_stdout(io.StringIO()):
    import phase10_hybrid_regime as P
    reg=P.run(0.03,1.15,0.88)
T=P.T;H=P.H;L=P.L;C=P.C;n4=len(C)
COST=0.35;HZ=120
def atr(i,k=14): return sum(max(H[j]-L[j],abs(H[j]-C[j-1]),abs(L[j]-C[j-1])) for j in range(i-k+1,i+1))/k
segs=sorted(json.load(open("/tmp/causal_segments_v10.json")),key=lambda s:s['start'])
for s in segs: s['bars']=(s['end']-s['start'])/14400

# letrun that ALSO reports whether trade stopped or was held to HZ end, and bars-held
def letrun_detail(bi,entry,sl):
    if entry-sl<=0: return None
    end=min(bi+HZ,n4-1)
    for j in range(bi+1,end+1):
        if L[j]<=sl:
            return {"R":-1.0,"exit":"STOP","held":j-bi}
    return {"R":(C[end]-entry)/(entry-sl),"exit":"HZ_END","held":end-bi}

def bear_deep(idx):
    bs=segs[idx]['start'];win=180*86400
    cand=[s for j,s in enumerate(segs) if j<idx and s['bars']>=15 and s['start']>=bs-win]
    if not cand: cand=[s for j,s in enumerate(segs) if j<idx and s['bars']>=15]
    if not cand: return None
    lo=min(s['lo'] for s in cand);amp=max(s['hi']-s['lo'] for s in cand);return (lo,lo+amp/3)

def entries():
    out=[]
    for idx in range(1,len(segs)):
        s=segs[idx];prev=segs[idx-1];amp=prev['hi']-prev['lo']
        i0=bisect.bisect_left(T,s['start']);i1=bisect.bisect_right(T,s['end'])-1
        if i1-i0<3: continue
        if s['regime']=='BULL':
            niv=prev['hi'];zlo=niv-amp/3
            k=next((j for j in range(i0,i1+1) if C[j]>niv),None)
            if k is None: continue
            rj=next((j for j in range(k+1,min(k+21,i1+1)) if L[j]<=niv),None)
            if rj is not None:
                out.append((rj,C[rj],zlo-0.5*atr(rj),'BULL','reteste'))
            else:
                out.append((i0,C[i0],min(L[i0:k+1])-0.5*atr(i0),'BULL','fallback'))
        elif s['regime']=='BEAR':
            zd=bear_deep(idx)
            if not zd: continue
            j=next((j for j in range(i0,i1+1) if L[j]<=zd[1]),None)
            if j is not None: out.append((j,C[j],zd[0]-0.5*atr(j),'BEAR','capit'))
        else:
            for j in range(i0+2,i1+1):
                rmin=min(L[i0:j+1]);rmax=max(H[i0:j+1])
                if rmax>rmin and (C[j]-rmin)/(rmax-rmin)<0.34:
                    out.append((j,C[j],rmin-0.5*atr(j),'RANGE','fundo'));break
    return out

rows=[]
for j,entry,sl,rg,typ in entries():
    d=letrun_detail(j,entry,sl)
    if d is None: continue
    import datetime as dt
    rows.append({"bi":j,"date":dt.datetime.utcfromtimestamp(T[j]).strftime("%Y-%m-%d"),
                 "reg":rg,"typ":typ,"R":round(d["R"]-COST,2),"exit":d["exit"],"held":d["held"]})
rows.sort(key=lambda x:x["bi"])

def blk(name,g):
    n=len(g);w=sum(1 for x in g if x['R']>0);s=sum(x['R'] for x in g)
    return f"{name}: N={n} WR={100*w/n:.0f}% sumR={s:+.1f} avgR={s/n:+.2f}"

print("="*70)
print("TOTAL",blk("",rows))
for RG in ('BULL','BEAR','RANGE'):
    g=[x for x in rows if x['reg']==RG]
    if g: print(" ",blk(RG,g))

print("\n### (1) RANGE — beta or edge? held vs stop ###")
rng=[x for x in rows if x['reg']=='RANGE']
held=[x for x in rng if x['exit']=='HZ_END']
stop=[x for x in rng if x['exit']=='STOP']
print(f"  RANGE N={len(rng)}  held-to-HZ120: {len(held)} (sumR={sum(x['R'] for x in held):+.1f})  stopped: {len(stop)} (sumR={sum(x['R'] for x in stop):+.1f})")
rng_sorted=sorted(rng,key=lambda x:-x['R'])
print("  RANGE trades sorted by R:")
for x in rng_sorted:
    print(f"    {x['date']} R={x['R']:+6.2f} exit={x['exit']:7} held={x['held']:3}b")
sR=sum(x['R'] for x in rng)
for k in (1,2,3):
    s2=sum(x['R'] for x in rng_sorted[k:])
    print(f"  RANGE drop-top-{k}: sumR {sR:+.1f} -> {s2:+.1f}  ({len(rng)-k} trades, avgR={s2/max(1,len(rng)-k):+.2f})")

print("\n### (2) BULL fallback — real or concentrated? ###")
fb=[x for x in rows if x['reg']=='BULL' and x['typ']=='fallback']
fb_sorted=sorted(fb,key=lambda x:-x['R'])
print(f"  fallback N={len(fb)} WR={100*sum(1 for x in fb if x['R']>0)/len(fb):.0f}% sumR={sum(x['R'] for x in fb):+.1f}")
for x in fb_sorted: print(f"    {x['date']} R={x['R']:+6.2f} exit={x['exit']:7} held={x['held']:3}b")
sfb=sum(x['R'] for x in fb)
print(f"  fallback drop-top-1: {sfb:+.1f} -> {sum(x['R'] for x in fb_sorted[1:]):+.1f}  ({len(fb)-1} trades)")
print(f"  fallback drop-top-2: {sfb:+.1f} -> {sum(x['R'] for x in fb_sorted[2:]):+.1f}  ({len(fb)-2} trades)")

print("\n### (3) system minus RANGE ###")
nr=[x for x in rows if x['reg']!='RANGE']
print(" ",blk("BULL+BEAR only",nr))
