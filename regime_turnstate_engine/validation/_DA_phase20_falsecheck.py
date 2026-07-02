#!/usr/bin/env python3
"""DA false-negative check on phase20 demand-retest filter.
Runs STRICTER retest definitions + alternative end-of-range proxies to see if the
user's 'block top until demand-retested' filter was unfairly killed by a loose def.
Read-only, causal, same 68-70 trade base."""
import json,csv,io,contextlib,sys,bisect,datetime as dt,statistics as st
from pathlib import Path
COST=0.35;VAL=Path("/Users/cristrein/tradingview-mcp/regime_turnstate_engine/validation");sys.path.insert(0,str(VAL))
with contextlib.redirect_stdout(io.StringIO()): import phase10_hybrid_regime as P
P.run(0.03,1.15,0.88);T=P.T;H=P.H;L=P.L;C=P.C
def atr(i,k=14): return sum(max(H[j]-L[j],abs(H[j]-C[j-1]),abs(L[j]-C[j-1])) for j in range(i-k+1,i+1))/k
segs=[s for s in json.load(open("/tmp/causal_segments_v10.json")) if s["regime"]=="RANGE"]
def box_of(ts):
    for s in segs:
        if s['start']<=ts<=s['end']: return s
    return None

# ---- retest counters with 3 strictness levels ----
def tests_loose(box,bi):   # ORIGINAL: bounce>=1ATR, return<=0.5ATR of running-min
    i0=bisect.bisect_left(T,box['start']);a=atr(max(20,i0));rmin=L[i0];armed=False;c=0
    for j in range(i0+1,bi):
        rmin=min(rmin,L[j])
        if C[j]>rmin+1.0*a: armed=True
        if armed and L[j]<=rmin+0.5*a: c+=1;armed=False
    return c
def tests_mid(box,bi):     # bounce must reach range MID, return<=0.3ATR of running-min
    i0=bisect.bisect_left(T,box['start']);a=atr(max(20,i0));rmin=L[i0];rmax=H[i0];armed=False;c=0
    for j in range(i0+1,bi):
        rmin=min(rmin,L[j]);rmax=max(rmax,H[j]);mid=(rmin+rmax)/2
        if C[j]>=mid: armed=True                       # rose to range midpoint
        if armed and L[j]<=rmin+0.3*a: c+=1;armed=False # deep return to demand
    return c
def tests_strict(box,bi):  # FULL swing: reach range HIGH (so-far), return<=0.3ATR of demand
    i0=bisect.bisect_left(T,box['start']);a=atr(max(20,i0));rmin=L[i0];rmax=H[i0];armed=False;c=0
    for j in range(i0+1,bi):
        rmax_prev=rmax;rmin=min(rmin,L[j])
        if H[j]>=rmax_prev-0.1*a: armed=True            # reached prior so-far high
        rmax=max(rmax,H[j])
        if armed and L[j]<=rmin+0.3*a: c+=1;armed=False
    return c

# ---- alt end-of-range proxies (all causal) ----
def bos_up_recent(box,bi,lookback=6):  # did close break the so-far range HIGH in last N bars?
    i0=bisect.bisect_left(T,box['start'])
    for j in range(max(i0+1,bi-lookback),bi+1):
        sofar_hi=max(H[i0:j])  # so-far high BEFORE bar j
        if C[j]>sofar_hi: return 1
    return 0
def time_in_range(box,bi):  # bars elapsed since box start (maturity)
    return bi-bisect.bisect_left(T,box['start'])
def prox_box_end(box,bi):   # fraction of box duration elapsed (LEAKY-ish: box end is future). flag only.
    i0=bisect.bisect_left(T,box['start']);i1=bisect.bisect_right(T,box['end'])
    return (bi-i0)/max(1,(i1-i0))

D=Path("/Users/cristrein/tradingview-mcp/my-strategy/research/revalidation/XAU_4H_L2_BPT_BOS_CHOCH/v1/results")
tr=[]
for r in csv.DictReader(open(D/"l2_bpt_regua_structural.csv")):
    bi=int(r["bar_idx"]);t=T[bi];y=dt.datetime.utcfromtimestamp(t).year
    if y<2023: continue
    box=box_of(t)
    if not box: continue
    entry=float(r["entry"]);R=round(float(r["letrun_struct"])-COST,2)
    i0=bisect.bisect_left(T,box['start']);sofar_lo=min(L[i0:bi+1]);sofar_hi=max(H[i0:bi+1])
    pos=(entry-sofar_lo)/(sofar_hi-sofar_lo) if sofar_hi>sofar_lo else 0.5
    tr.append({"bi":bi,"date":dt.datetime.utcfromtimestamp(t).strftime("%Y-%m-%d"),"pos":pos,"R":R,"win":R>0,
               "t_loose":tests_loose(box,bi),"t_mid":tests_mid(box,bi),"t_strict":tests_strict(box,bi),
               "bos":bos_up_recent(box,bi),"tir":time_in_range(box,bi),"pend":prox_box_end(box,bi)})
def stat(g):
    if not g: return "N=0"
    return f"N={len(g):2} WR={100*sum(x['win'] for x in g)/len(g):3.0f}% sumR={sum(x['R'] for x in g):+6.1f} avgR={sum(x['R'] for x in g)/len(g):+5.2f}"
TOPO=0.5;topo=[x for x in tr if x["pos"]>=TOPO]
print(f"TOP entries (pos>={TOPO}): N={len(topo)}  base RANGE N={len(tr)}\n")

print("="*80);print("PT1/PT3 — STRICTER RETEST DEFS: how many top entries become PRECOCE (0 tests)?");print("="*80)
for key,nm in [("t_loose","LOOSE(orig 1ATR/0.5)"),("t_mid","MID(reach mid /0.3)"),("t_strict","STRICT(full swing hi/0.3)")]:
    prec=[x for x in topo if x[key]==0];tard=[x for x in topo if x[key]>=1]
    blkW=sum(x['win'] for x in prec);base_sum=sum(x['R'] for x in tr)
    keep=[x for x in tr if not (x["pos"]>=TOPO and x[key]==0)]
    print(f"\n{nm}")
    print(f"   PRECOCE(block): {stat(prec)}  winners_blocked={blkW}")
    print(f"   TARDIO(keep):   {stat(tard)}")
    print(f"   FILTER effect base: {sum(x['R'] for x in tr):+.1f} -> {sum(x['R'] for x in keep):+.1f}  (blocks {len(prec)}, {blkW} winners)")

print("\n"+"="*80);print("PT2 — does retest-count separate TOP winners from losers? (per strict def)");print("="*80)
for key in ["t_loose","t_mid","t_strict"]:
    w=[x[key] for x in topo if x['win']];l=[x[key] for x in topo if not x['win']]
    print(f"  {key:9}: WIN tests mean={st.mean(w):.1f} med={st.median(w):.1f} | LOSS mean={st.mean(l):.1f} med={st.median(l):.1f}")
    # threshold sweep: block top with tests< thr
    best=None
    for thr in range(0,12):
        keep=[x for x in tr if not (x["pos"]>=TOPO and x[key]<thr)]
        s=sum(x['R'] for x in keep);blk=[x for x in tr if x["pos"]>=TOPO and x[key]<thr]
        if best is None or s>best[1]: best=(thr,s,len(blk),sum(v['win'] for v in blk))
    print(f"            best 'block top if tests<thr': thr={best[0]} -> sumR {best[1]:+.1f} (base {sum(x['R'] for x in tr):+.1f}), blocks {best[2]} ({best[3]} win)")

print("\n"+"="*80);print("PT4 — alt END-OF-RANGE proxies: separate top WINNERS from top LOSERS?");print("="*80)
tw=[x for x in topo if x['win']];tl=[x for x in topo if not x['win']]
for key,nm in [("bos","BOS-up recent(6b)"),("tir","time-in-range(bars)"),("pend","prox box_end[LEAKY]")]:
    w=[x[key] for x in tw];l=[x[key] for x in tl]
    print(f"  {nm:22}: WIN mean={st.mean(w):.2f} | LOSS mean={st.mean(l):.2f}")
# BOS split (the causal end-of-range signal)
print("\n  --- split TOP by BOS-up-recent (broke so-far range high in last 6 bars) ---")
print(f"    BOS=1 (breakout): {stat([x for x in topo if x['bos']==1])}")
print(f"    BOS=0 (in-range): {stat([x for x in topo if x['bos']==0])}")
print("\n  --- FILTER: keep TOP only if BOS-up recent; block TOP mid-range (bos=0) ---")
keep=[x for x in tr if not (x["pos"]>=TOPO and x['bos']==0)]
blk=[x for x in tr if x["pos"]>=TOPO and x['bos']==0]
print(f"    base {sum(x['R'] for x in tr):+.1f} -> {stat(keep)}  (blocks {len(blk)}, winners_lost={sum(x['win'] for x in blk)}, sumR_blocked {sum(x['R'] for x in blk):+.1f})")
