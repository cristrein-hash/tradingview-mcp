"""Devil's Advocate prep: orthogonality + carrier sanity for 5ATR re-opt.

Checks:
 1. Overlap (Jaccard) between top carrier predicates -> are they redundant?
 2. Marginal lift of each brick GIVEN the others already applied.
 3. Per-block winners cut by the leading stack (no block emptied / winner-starved).
 4. macro_bear / h1_pos value distributions among winners vs losers (real signal?).
RAW-causal. win=R>0.
"""
import _reopt5_lib as L

ROWS = L.load()
SENT = {'sell_decel': lambda v: v <= -1e5}

def fv(r,k):
    v=r.get(k)
    if v is None: return None
    if k in SENT and SENT[k](v): return None
    return v

def P(k,op,thr):
    if op=='>=':
        f=lambda r:(fv(r,k) is not None and fv(r,k)>=thr)
    else:
        f=lambda r:(fv(r,k) is not None and fv(r,k)<=thr)
    f.desc=f"{k}{op}{thr}"
    return f

carriers = {
    'macro_bear<=0': P('macro_bear','<=',0),
    'h1_pos>=0.68':  P('h1_pos','>=',0.68),
    'rsi>=50.7':     P('rsi','>=',50.7),
    'vpnode>=0.34':  P('vpnode_dist_atr','>=',0.34),
    'disp4>=0.53':   P('disp4_atr','>=',0.53),
    'sell_skew<=0.2':P('sell_skew_mig','<=',0.2),
}

def setof(p): return set(i for i,r in enumerate(ROWS) if p(r))
sets={n:setof(p) for n,p in carriers.items()}

print("=== JACCARD overlap between carriers (kept-sets) ===")
names=list(carriers)
for i in range(len(names)):
    for j in range(i+1,len(names)):
        a,b=sets[names[i]],sets[names[j]]
        jac=len(a&b)/len(a|b)
        print(f"  {names[i]:16s} vs {names[j]:16s} jaccard={jac:.2f}")

print("\n=== marginal lift: WR of each carrier among rows NOT cut by macro_bear ===")
base_keep=[r for r in ROWS if carriers['macro_bear<=0'](r)]
bwr=100*sum(r['win'] for r in base_keep)/len(base_keep)
print(f"  after macro_bear<=0: n={len(base_keep)} wr={bwr:.2f}")
for n,p in carriers.items():
    if n=='macro_bear<=0': continue
    k2=[r for r in base_keep if p(r)]
    if not k2: continue
    print(f"   +{n:16s} n={len(k2)} wr={100*sum(r['win'] for r in k2)/len(k2):.2f}")

print("\n=== winner/loser distribution: macro_bear & h1_pos (real signal check) ===")
W=[r for r in ROWS if r['win']==1]; Lz=[r for r in ROWS if r['win']==0]
import statistics
for k in ['macro_bear','h1_pos','rsi','vpnode_dist_atr','disp4_atr','sell_skew_mig']:
    wv=[fv(r,k) for r in W if fv(r,k) is not None]
    lv=[fv(r,k) for r in Lz if fv(r,k) is not None]
    print(f"  {k:16s} winners_med={statistics.median(wv):.3f} losers_med={statistics.median(lv):.3f} "
          f"W_mean={statistics.mean(wv):.3f} L_mean={statistics.mean(lv):.3f}")

print("\n=== leading 2-stack per-block winner retention ===")
stack=[carriers['macro_bear<=0'],carriers['rsi>=50.7']]
for b in L.BLOCK_ORDER:
    blk=[r for r in ROWS if r['block']==b]
    bw=sum(r['win'] for r in blk)
    kept=[r for r in blk if all(p(r) for p in stack)]
    kw=sum(r['win'] for r in kept)
    print(f"  {b}: winners {bw}->{kw} ({100*kw/bw:.0f}%) wr {100*sum(r['win'] for r in blk)/len(blk):.1f}->"
          f"{(100*kw/len(kept)) if kept else 0:.1f}")
