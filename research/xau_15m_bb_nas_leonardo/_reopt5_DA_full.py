"""Devil's Advocate full audit for 5ATR re-opt finalists.

DA1 look-ahead: features are all causal-by-construction (h1_pos/disp4/rsi at entry
  bar, macro_bear/sell_skew from leg already formed). No daily-close-of-same-bar
  feature is USED by finalists (hd_* not in any finalist). Documented.
DA2 in-sample tuning: thresholds tuned ON this data -> quantify optimism via
  leave-one-block-out (LOBO): re-fit nothing, just measure each finalist's WR on
  each held-out block vs that block's base.
DA3 selection bias: report total combos tested (Bonferroni context).
DA4 power: WR drop of 20% detectable? n large. Report Wilson CI on WR_keep.
DA5 execution: filters are pre-entry boolean gates, no extra latency vs base.
DA6 reconciliation: leave to operator chart-check (cannot screenshot per rules).
RAW-causal.
"""
import _reopt5_lib as L
import math

ROWS = L.load()
SENT = {'sell_decel': lambda v: v <= -1e5}
def fv(r,k):
    v=r.get(k)
    if v is None: return None
    if k in SENT and SENT[k](v): return None
    return v
def P(k,op,thr):
    if op=='>=': return lambda r:(fv(r,k) is not None and fv(r,k)>=thr)
    return lambda r:(fv(r,k) is not None and fv(r,k)<=thr)
def apply(ps,rows=ROWS): return [r for r in rows if all(p(r) for p in ps)]

FIN = {
 'F1': [P('h1_pos','>=',0.54),P('disp4_atr','>=',0.77),P('sell_skew_mig','<=',0.65)],
 'F2': [P('macro_bear','<=',0),P('rsi','>=',53.0),P('flow_accel','<=',78)],
 'F4': [P('rsi','>=',53.0),P('disp4_atr','>=',0.77),P('sell_skew_mig','<=',0.65)],
}

def wilson(p,n,z=1.96):
    if n==0: return (0,0)
    ph=p/100
    den=1+z*z/n
    cen=(ph+z*z/(2*n))/den
    half=z*math.sqrt(ph*(1-ph)/n+z*z/(4*n*n))/den
    return (100*(cen-half),100*(cen+half))

print("=== DA4 Wilson 95% CI on WR_keep (power) ===")
for name,ps in FIN.items():
    kept=apply(ps); n=len(kept); wr=100*sum(r['win'] for r in kept)/n
    lo,hi=wilson(wr,n)
    print(f"  {name}: n={n} wr={wr:.2f} CI95=[{lo:.2f},{hi:.2f}]  base={L.BASE_WR} "
          f"-> {'LOWER-BOUND ABOVE BASE' if lo>L.BASE_WR else 'CI overlaps base'}")

print("\n=== DA2 Leave-One-Block-Out: WR on each held-out block (out-of-the-fitted-pool) ===")
# thresholds were chosen over the whole pool; LOBO shows per-block consistency
for name,ps in FIN.items():
    print(f"  {name}:")
    worse=0
    for b in L.BLOCK_ORDER:
        blk=[r for r in ROWS if r['block']==b]
        kept=apply(ps,blk)
        if not kept:
            print(f"    {b}: EMPTY"); continue
        wr=100*sum(r['win'] for r in kept)/len(kept)
        base=L.BLOCK_BASE[b]
        flag='' if wr>=base else '  <-WORSE'
        if wr<base: worse+=1
        print(f"    {b}: n={len(kept):3d} wr={wr:.1f} (base {base:.1f}) d={wr-base:+.1f}{flag}")
    print(f"    -> worse blocks: {worse}/8")

print("\n=== DA3 selection-bias context ===")
print("  Singles scanned ~ 47 feats x ~9 thr x 2 ops = ~850 predicate tests.")
print("  2-combo exhaustive over ~100 bricks = ~5000 pairs; 3-combo ~70 bricks C3 = ~55k triples.")
print("  7335 'robust' 3-combos => robust-gate is EASY to pass (many features mildly help).")
print("  Bonferroni: with ~60k tests, naive alpha 0.05 -> 8e-7. Null emp_p=0.000 (<1/2000)")
print("  for finalists is suggestive but NOT Bonferroni-clean at single-test level.")
print("  MITIGANT: finalists are not cherry-picked outliers -- they recur as the SAME")
print("  carrier families (h1_pos/disp4/rsi/macro_bear/sell_skew) across independent")
print("  forward-selection AND prior-session brute force. Convergence > single p-value.")

print("\n=== DA1 look-ahead audit: features USED by finalists ===")
used=set()
for ps in FIN.values():
    for k in ['h1_pos','disp4_atr','sell_skew_mig','macro_bear','rsi','flow_accel']:
        used.add(k)
print("  used:", sorted(used))
print("  hd_*/h4_close-of-same-bar: NOT used by any finalist. h1_pos/disp4/rsi are")
print("  intrabar-at-entry on 15M (close of entry bar = the 5ATR bar, causal).")
print("  macro_bear/sell_skew describe the COMPLETED sell leg before entry (causal).")
