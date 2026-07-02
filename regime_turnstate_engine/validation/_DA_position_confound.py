#!/usr/bin/env python3
"""DA audit of the position-thesis. Key tests:
1. Segment-age degeneracy: how many RANGE trades sit in segments <N bars old at entry (range ill-defined)?
2. SL confound: decompose avgR = price_move / risk. Does FUNDO win on bigger MOVE or smaller RISK?
   Re-run FUNDO-vs-TOPO on price-move-in-ATR (denominator-free) and on a FIXED-risk R.
3. pos vs risk correlation (does pos just proxy sl_atr?).
4. Bonferroni-adjust the null_p.
"""
import csv,io,contextlib,sys,random,statistics as st,datetime as dt
from pathlib import Path
COST=0.35;VAL=Path("/Users/cristrein/tradingview-mcp/regime_turnstate_engine/validation");sys.path.insert(0,str(VAL))
with contextlib.redirect_stdout(io.StringIO()): import phase10_hybrid_regime as P
reg=P.run(0.03,1.15,0.88);T=P.T;H=P.H;L=P.L;C=P.C
D=Path("/Users/cristrein/tradingview-mcp/my-strategy/research/revalidation/XAU_4H_L2_BPT_BOS_CHOCH/v1/results")
slx={int(r["i"]):r for r in csv.DictReader(open(D/"l2_bpt_sl_context_policy_results.csv"))}
def seg_bounds(bi):
    rg=reg[bi];s=bi
    while s>0 and reg[s-1]==rg: s-=1
    lo=min(L[s:bi+1]);hi=max(H[s:bi+1]);return s,lo,hi
# rough ATR(14) causal at bi from H/L/C
def atr(bi,n=14):
    trs=[]
    for k in range(max(1,bi-n+1),bi+1):
        trs.append(max(H[k]-L[k],abs(H[k]-C[k-1]),abs(L[k]-C[k-1])))
    return sum(trs)/len(trs) if trs else 0
rows=[]
for r in csv.DictReader(open(D/"l2_bpt_regua_structural.csv")):
    bi=int(r["bar_idx"]);t=T[bi];y=dt.datetime.utcfromtimestamp(t).year
    if y<2023: continue
    R=round(float(r["letrun_struct"])-COST,2);mfe=float(r["mfe_struct"]);entry=float(r["entry"])
    risk=float(r["risk"]);letrun=float(r["letrun_struct"])
    s,lo,hi=seg_bounds(bi);age=bi-s;pos=(entry-lo)/(hi-lo) if hi>lo else 0.5
    a=atr(bi)
    # price move realized (in ATR, denominator-free): letrun_R * risk / atr
    move_atr=(letrun*risk)/a if a>0 else 0
    # fixed-risk R: same price move but risk fixed at 2.5 ATR (median-ish)
    fixed_R=(letrun*risk)/(2.5*a) - COST if a>0 else 0
    rows.append({"bi":bi,"date":dt.datetime.utcfromtimestamp(t).strftime("%Y-%m-%d"),"yr":y,"regime":reg[bi],
        "entry":entry,"R":R,"mfe":mfe,"win":R>0,"pos":pos,"age":age,"risk":risk,"atr":a,
        "sl_atr":float(slx.get(bi,{}).get("sl_atr",0) or 0),"move_atr":move_atr,"fixed_R":fixed_R,"range_atr":(hi-lo)/a if a>0 else 0})
RG=[x for x in rows if x['regime']=='RANGE']
print("="*90);print("(1) SEGMENT-AGE DEGENERACY — RANGE trades whose containing segment is very young at entry");print("="*90)
for thr in [3,5,8,12]:
    young=[x for x in RG if x['age']<thr];print(f"  age<{thr:2} bars: {len(young):2}/{len(RG)} trades | range width median {st.median([x['range_atr'] for x in RG if x['age']<thr]) if young else 0:.1f} ATR")
print(f"  RANGE segment-age: min {min(x['age'] for x in RG)} median {st.median([x['age'] for x in RG]):.0f} max {max(x['age'] for x in RG)}")
print(f"  range width (hi-lo)/ATR: median {st.median([x['range_atr'] for x in RG]):.1f}  (a real range should be several ATR wide)")
# does pos correlate with age? (young seg -> extreme pos artifact)
def corr(a,b):
    n=len(a);ma=sum(a)/n;mb=sum(b)/n;num=sum((a[i]-ma)*(b[i]-mb) for i in range(n))
    da=(sum((x-ma)**2 for x in a))**.5;db=(sum((x-mb)**2 for x in b))**.5;return num/(da*db) if da*db else 0
print(f"  corr(pos, age)={corr([x['pos'] for x in RG],[x['age'] for x in RG]):+.2f}  corr(pos, range_width_atr)={corr([x['pos'] for x in RG],[x['range_atr'] for x in RG]):+.2f}")

print("\n"+"="*90);print("(3) SL CONFOUND — is FUNDO's higher avgR just a smaller risk denominator?");print("="*90)
bot=[x for x in RG if x['pos']<=0.4];top=[x for x in RG if x['pos']>=0.6]
def mn(g,k): return st.mean([x[k] for x in g]) if g else 0
print(f"  FUNDO(n{len(bot)}): avgR {mn(bot,'R'):+.2f} | risk(price) {mn(bot,'risk'):.1f} | sl_atr {mn(bot,'sl_atr'):.1f} | MOVE_atr {mn(bot,'move_atr'):+.2f} | fixedRiskR {mn(bot,'fixed_R'):+.2f}")
print(f"  TOPO(n{len(top)}): avgR {mn(top,'R'):+.2f} | risk(price) {mn(top,'risk'):.1f} | sl_atr {mn(top,'sl_atr'):.1f} | MOVE_atr {mn(top,'move_atr'):+.2f} | fixedRiskR {mn(top,'fixed_R'):+.2f}")
print(f"  corr(pos, sl_atr) in RANGE = {corr([x['pos'] for x in RG],[x['sl_atr'] for x in RG]):+.2f}  (neg => fundo=tighter SL)")
print(f"  >> RAW avgR gap {mn(bot,'R')-mn(top,'R'):+.2f} | denominator-free MOVE_atr gap {mn(bot,'move_atr')-mn(top,'move_atr'):+.2f} | FIXED-risk R gap {mn(bot,'fixed_R')-mn(top,'fixed_R'):+.2f}")
# null on MOVE_atr (denominator-free)
def nullp(g,key):
    b=[x[key] for x in g if x['pos']<=0.4];tp=[x[key] for x in g if x['pos']>=0.6]
    if not(b and tp): return None
    real=st.mean(b)-st.mean(tp);allv=[x[key] for x in g];flag=[1 if x['pos']<=0.4 else(0 if x['pos']>=0.6 else -1) for x in g]
    idx=[i for i in range(len(g)) if flag[i]>=0];vals=[allv[i] for i in range(len(g)) if flag[i]>=0];fl=[flag[i] for i in idx]
    random.seed(11);dd=[]
    for _ in range(5000):
        random.shuffle(fl);bb=[vals[i] for i in range(len(vals)) if fl[i]==1];tt=[vals[i] for i in range(len(vals)) if fl[i]==0]
        if bb and tt: dd.append(st.mean(bb)-st.mean(tt))
    return real,sum(1 for x in dd if abs(x)>=abs(real))/len(dd)
for key in ['R','move_atr','fixed_R']:
    r=nullp(RG,key)
    if r: print(f"  null_p FUNDO-vs-TOPO on {key:9}: diff {r[0]:+.2f} p={r[1]:.3f}")
print("\n(6) Bonferroni: ~ tests = 3 regimes x 1 fundo-vs-topo + per-year(3) => treat family ~6-9. p=0.067 x 6 = %.2f (fails)"%(0.067*6))

print("\n"+"="*90);print("PER-YEAR, denominator-free (MOVE_atr) — does 2025 still reverse when SL confound removed?");print("="*90)
for yy in sorted(set(x['yr'] for x in RG)):
    b=[x['move_atr'] for x in RG if x['yr']==yy and x['pos']<=0.4];tp=[x['move_atr'] for x in RG if x['yr']==yy and x['pos']>=0.6]
    fb=f"{st.mean(b):+.2f}(n{len(b)})" if b else "-(n0)";ft=f"{st.mean(tp):+.2f}(n{len(tp)})" if tp else "-(n0)"
    print(f"    {yy}: fundo_move {fb} / topo_move {ft}")
print("  and RAW R per year for reference:")
for yy in sorted(set(x['yr'] for x in RG)):
    b=[x['R'] for x in RG if x['yr']==yy and x['pos']<=0.4];tp=[x['R'] for x in RG if x['yr']==yy and x['pos']>=0.6]
    print(f"    {yy}: fundo_R {st.mean(b):+.2f}(n{len(b)}) / topo_R {st.mean(tp):+.2f}(n{len(tp)})" if b and tp else f"    {yy}: sparse")
