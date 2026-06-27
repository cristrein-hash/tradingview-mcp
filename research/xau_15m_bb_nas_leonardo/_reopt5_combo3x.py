"""Focused 3-combo search anchored on top carriers + streak-minimization.

From 2-combo search the carriers are: macro_bear<=0, h1_pos>=0.68/h1_dist,
rsi>=~50, disp4_atr, vpnode_dist_atr, sell_skew_mig (R_B), flow_accel.
Build best robust 3-combo maximizing WR and minimizing max-losing-streak
while keeping winners>=85%, all years>=base, >=6/8 blocks (prefer 8/8).
RAW-causal. win=R>0.
"""
import _reopt5_lib as L
from itertools import combinations

ROWS = L.load()
N = len(ROWS)
BASE_STREAK = L.max_losing_streak(ROWS)
SENTINEL = {'sell_decel': lambda v: v <= -1e5}

FORB = L.FORBIDDEN
FEATS = []
for k in [x for x in ROWS[0].keys() if x not in FORB]:
    vals = [r.get(k) for r in ROWS if r.get(k) is not None]
    if len(vals) < N*0.5 or not all(isinstance(v,(int,float)) for v in vals) or len(set(vals))<2:
        continue
    FEATS.append(k)


def fv(r,k):
    v=r.get(k)
    if v is None: return None
    if k in SENTINEL and SENTINEL[k](v): return None
    return v

def mp(k,op,thr):
    if op=='>=':
        def p(r):
            v=fv(r,k); return v is not None and v>=thr
    else:
        def p(r):
            v=fv(r,k); return v is not None and v<=thr
    p.desc=f"{k}{op}{thr}"; p.k=k
    return p

def thresholds(k):
    vals=sorted(set(fv(r,k) for r in ROWS if fv(r,k) is not None))
    if len(vals)<=12: return vals
    return sorted(set(vals[int(len(vals)*q)] for q in (0.2,0.35,0.5,0.65,0.8)))

def apply(preds):
    return [r for r in ROWS if all(p(r) for p in preds)]

# brick pool >=92% wk (so 3-combos can stay >=85)
bricks=[]
for k in FEATS:
    for thr in thresholds(k):
        for op in ('>=','<='):
            p=mp(k,op,thr)
            kept=apply([p])
            if len(kept)<500: continue
            m=L.metrics(kept,ROWS)
            if m and m['winners_kept_pct']>=92.0:
                bricks.append(p)
print(f"brick_pool(>=92% wk)={len(bricks)}")

# exhaustive 3-combo (distinct features)
robust=[]
B=bricks
for i in range(len(B)):
    for j in range(i+1,len(B)):
        if B[i].k==B[j].k: continue
        # quick prune on 2 first
        k2=apply([B[i],B[j]])
        if len(k2)<700: continue
        m2=L.metrics(k2,ROWS)
        if m2['winners_kept_pct']<86: continue
        for l in range(j+1,len(B)):
            if B[l].k in (B[i].k,B[j].k): continue
            kept=[r for r in k2 if B[l](r)]
            if len(kept)<600: continue
            m=L.metrics(kept,ROWS)
            if m and m['winners_kept_pct']>=85.0 and L.is_robust(m):
                robust.append((B[i].desc,B[j].desc,B[l].desc,m))

print(f"ROBUST 3-combos: {len(robust)}")

# rank A: by WR
byWR=sorted(robust,key=lambda x:-x[3]['wr_keep'])[:12]
print("\nTOP by WR:")
for a,b,c,m in byWR:
    print(f"  {a} & {b} & {c}\n     n={m['n_keep']} wr={m['wr_keep']:.2f} wk={m['winners_kept_pct']:.0f}% "
          f"lc={m['losers_cut_pct']:.0f}% strk{BASE_STREAK}->{m['streak_keep']} yr={m['by_year']} blk{m['blocks_ok']}")

# rank B: by lowest streak then WR (prefer 8/8 blocks)
byStreak=sorted([r for r in robust if r[3]['blocks_ok']==8],
                key=lambda x:(x[3]['streak_keep'],-x[3]['wr_keep']))[:12]
print("\nTOP by LOWEST STREAK (8/8 blocks only):")
for a,b,c,m in byStreak:
    print(f"  {a} & {b} & {c}\n     n={m['n_keep']} wr={m['wr_keep']:.2f} wk={m['winners_kept_pct']:.0f}% "
          f"lc={m['losers_cut_pct']:.0f}% strk{BASE_STREAK}->{m['streak_keep']} yr={m['by_year']} blk{m['blocks_ok']}")

# combined score: WR gain*2 + streak cut*2 + (blocks_ok-6) + winners margin
def sc(m):
    return (m['wr_keep']-L.BASE_WR)*2 + (BASE_STREAK-m['streak_keep'])*2 + (m['blocks_ok']-6) + (m['winners_kept_pct']-85)*0.2
byScore=sorted(robust,key=lambda x:-sc(x[3]))[:10]
print("\nTOP by COMBINED SCORE:")
for a,b,c,m in byScore:
    print(f"  [{sc(m):.1f}] {a} & {b} & {c}\n     n={m['n_keep']} wr={m['wr_keep']:.2f} wk={m['winners_kept_pct']:.0f}% "
          f"strk{BASE_STREAK}->{m['streak_keep']} yr={m['by_year']} blk{m['blocks_ok']}")
