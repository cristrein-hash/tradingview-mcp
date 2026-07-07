#!/usr/bin/env python3
"""STRICT-CAUSAL re-implementation + OVERFIT null of the FASE-B FLUSH+VARREDURA+RECLAIM candidate.

NO reference to loser/winner n-alvo anywhere in logic. All features causal (index<=j).
Goal: (1) reproduce; (2) isolate what is actually load-bearing; (3) null-test the grid selection.
"""
import sys, random; sys.path.insert(0,"/Users/cristrein/tradingview-mcp/research/xau_15m_bb_nas_leonardo")
from agent_ctx_kit import ENTRIES, HI, LO, CL, ATR, EMA, score, causal_swings_upto
import datetime as dt

def feats(e):
    i=e['i']; j=e['j']; lo=e['demand_low']; a=ATR[i] or 5.0
    K=8; seg=range(max(0,i-K),i+1)
    mh=max(HI[k] for k in seg); mhi=max(seg,key=lambda k:HI[k])
    drop_atr=(mh-lo)/a; span=i-mhi
    M=12; prior=[LO[k] for k in range(max(0,i-M),i)]
    priormin=min(prior) if prior else lo
    swept=lo<priormin; sweep_depth=(priormin-lo)/a
    rl=e['reclaim_lag']
    sw=causal_swings_upto(j)
    Hs=[pr for tp,idx,pr,ci in sw if tp=='H']; Ls=[pr for tp,idx,pr,ci in sw if tp=='L']
    slope=(EMA[j]-EMA[j-6])/a if (EMA[j] is not None and j>=6 and EMA[j-6] is not None) else 0.0
    rngpos=0.5
    if Hs and Ls and Hs[-1]>Ls[-1]: rngpos=(CL[j]-Ls[-1])/(Hs[-1]-Ls[-1])
    return dict(drop_atr=drop_atr,span=span,swept=swept,sweep_depth=sweep_depth,rl=rl,slope=slope,rngpos=rngpos)

F={e['n']:feats(e) for e in ENTRIES}

def keep_by(fn):
    return set(e['n'] for e in ENTRIES if fn(F[e['n']]))

print("=== A) EFFECTIVE grid-winner decomposed (rl<=6 AND not(rl>2 and rngpos>=0.7)) ===")
eff=keep_by(lambda f: f['rl']<=6 and not (f['rl']>2 and f['rngpos']>=0.7))
print(" effective 2-feature :", score(eff))

print("\n=== B) each live feature ALONE ===")
print(" rl<=6 only          :", score(keep_by(lambda f: f['rl']<=6)))
print(" rngpos<0.7 only      :", score(keep_by(lambda f: f['rngpos']<0.7)))
print(" rl<=4 only          :", score(keep_by(lambda f: f['rl']<=4)))

print("\n=== C) AUTHOR'S LITERAL HYPOTHESIS a-priori (flush+swept+controlled sweep+fast reclaim) ===")
hyp=keep_by(lambda f: f['drop_atr']>=1.5 and f['swept'] and f['sweep_depth']<=0.9 and f['rl']<=4)
print(" hypothesis config    :", score(hyp))

# ---- D) OVERFIT NULL: rerun the EXACT grid selection under permuted outcomes ----
def classify(F, DR,RL,SDmax,SDmin,req,spd,vsl,vrp):
    keep=set()
    for e in ENTRIES:
        f=F[e['n']]
        if f['drop_atr']<DR: continue
        if req and not f['swept']: continue
        if not (SDmin<=f['sweep_depth']<=SDmax): continue
        if f['rl']>RL: continue
        if f['span']>spd: continue
        if f['rl']>2 and f['slope']<=vsl and f['rngpos']>=vrp: continue
        keep.add(e['n'])
    return keep

GRID=[(DR,RL,SDmax,-9.9,False,99,vsl,vrp)
      for DR in [0.0,1.5,2.0,2.5] for RL in [3,4,5,6] for SDmax in [0.6,0.9,9.9]
      for vsl in [99.0,-0.4,-0.55,-0.7] for vrp in [0.6,0.65,0.7,0.75]]

ALLN=[e['n'] for e in ENTRIES]
YEAR={e['n']: dt.datetime.utcfromtimestamp(int(e['t'])).strftime('%Y') for e in ENTRIES}
TOTAL=len(ALLN)
# precompute the keep-set for every grid config ONCE (features fixed; only outcomes permute)
GRID_KEEPS=[classify(F,*g) for g in GRID]

def select_best(om):
    """Run the candidate's exact selection over an outcome map. Returns best hit3r or None."""
    cands=[]
    for keep in GRID_KEEPS:
        N=len(keep)
        if N<20: continue
        w=sum(om[n] for n in keep)
        wc=0; lc=0; y25w=y25n=y26w=y26n=0
        for n in ALLN:
            if n in keep:
                if YEAR[n]=='2025': y25n+=1; y25w+=om[n]
                elif YEAR[n]=='2026': y26n+=1; y26w+=om[n]
            else:
                if om[n]: wc+=1
                else: lc+=1
        pois=(wc/lc) if lc else (99 if wc else 0)
        posy = y25w>(y25n-y25w) and y26w>(y26n-y26w)
        if pois<0.9 and posy and N>=20:
            cands.append((pois<=0.82, w/N, N))
    if not cands: return None
    strong=[c for c in cands if c[0]]
    pool=strong if strong else cands
    pool.sort(key=lambda c:(c[1],c[2]),reverse=True)
    return pool[0][1]

# observed
obs_map={e['n']:e['out'] for e in ENTRIES}
obs=select_best(obs_map)
print("\n=== D) OVERFIT NULL on the grid-selection procedure ===")
print(" observed selected hit3r:", round(obs,3))
outs=[e['out'] for e in ENTRIES]
random.seed(42); T=2000; hits=[]
for _ in range(T):
    perm=outs[:]; random.shuffle(perm)
    pm={ALLN[k]:perm[k] for k in range(TOTAL)}
    b=select_best(pm)
    if b is not None: hits.append(b)
ge=sum(1 for h in hits if h>=obs-1e-9)
print(f" null trials producing a valid winner: {len(hits)}/{T}")
print(f" P(selected hit3r >= observed {round(obs,3)}) under permuted outcomes = {ge/T:.3f}")
import statistics as st
if hits:
    print(f" null selected-hit3r: median={st.median(hits):.3f} p90={sorted(hits)[int(.9*len(hits))]:.3f} p95={sorted(hits)[int(.95*len(hits))]:.3f} max={max(hits):.3f}")

print("\nKEEP_NS(effective)=",sorted(eff))
