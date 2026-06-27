"""Finalize 5ATR re-opt: full metrics for finalist stacks + null-permutation context.

Finalists (carriers from my 2x/3x forward-search, all 8ATR-family rooted):
  F1 R2+disp+R_B : h1_pos>=0.54 & disp4_atr>=0.77 & sell_skew_mig<=0.65 (best 8/8, low streak)
  F2 momentum    : macro_bear<=0 & rsi>=53.0 & flow_accel<=78          (fwd-selected)
  F3 simplest    : macro_bear<=0 & rsi>=50.7                           (2-brick robust)
  F4 R_B no-h1   : rsi>=53.0 & disp4_atr>=0.77 & sell_skew_mig<=0.65   (8/8)
RAW-causal. win=R>0.
"""
import _reopt5_lib as L
import random
random.seed(7)

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

def apply(ps): return [r for r in ROWS if all(p(r) for p in ps)]

FIN = {
 'F1 h1_pos>=0.54 & disp4_atr>=0.77 & sell_skew_mig<=0.65':
     [P('h1_pos','>=',0.54),P('disp4_atr','>=',0.77),P('sell_skew_mig','<=',0.65)],
 'F2 macro_bear<=0 & rsi>=53.0 & flow_accel<=78':
     [P('macro_bear','<=',0),P('rsi','>=',53.0),P('flow_accel','<=',78)],
 'F3 macro_bear<=0 & rsi>=50.7':
     [P('macro_bear','<=',0),P('rsi','>=',50.7)],
 'F4 rsi>=53.0 & disp4_atr>=0.77 & sell_skew_mig<=0.65':
     [P('rsi','>=',53.0),P('disp4_atr','>=',0.77),P('sell_skew_mig','<=',0.65)],
}

finmetrics={}
for name,ps in FIN.items():
    m=L.report(name,apply(ps),ROWS)
    finmetrics[name]=m

print("\n"+"="*70)
print("NULL CONTEXT: random subsets of same size, WR distribution (2000 draws)")
wins=[r['win'] for r in ROWS]
for name,ps in FIN.items():
    n=len(apply(ps))
    draws=sorted(100*sum(random.sample(wins,n))/n for _ in range(2000))
    obs=finmetrics[name]['wr_keep']
    p95=draws[1899]; p99=draws[1979]
    pval=sum(1 for d in draws if d>=obs)/len(draws)
    print(f"  {name[:42]:42s} obs={obs:.2f} null_p95={p95:.2f} null_p99={p99:.2f} emp_p={pval:.3f}")
