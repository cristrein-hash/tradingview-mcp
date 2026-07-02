#!/usr/bin/env python3
"""DEVIL'S ADVOCATE on phase30_operational_viability.
Cris's real objective = OPERATIONAL/PSYCHOLOGICAL holdability for a monthly-withdrawal prop firm,
NOT max expectancy. He proposes range->floor SL and PERCEIVES 'streak relief' on the chart.
The hard metric says max-loss-streak is UNCHANGED (11->11 book, 8->8 range). I must NOT rubber-stamp.

AUDIT PLAN (priority order):
 C1  Is the panel() measurement CORRECT? Re-implement independently:
     - max-consecutive-losses (v<=0 counts as loss; is BE=0 correctly a 'loss'?)
     - loss-runs>=3/>=5 histogram
     - month bucketing by YYYY-MM of ENTRY
     - avg-trades-between-wins
     Any off-by-one / tie / open-run-not-flushed bug that hides or fakes a streak change?
 C2  Is 'streak relief' REAL or ILLUSION? Full loss-run histogram base vs mod.
     Under WHICH metric does relief hold (fewer >=3 runs? higher win density? shallower monthly DD?)
     vs FAIL (single worst streak identical). Be explicit.
 C3  WHICH trades flipped loss->win. One cluster (e.g. 2024-06 chop) or spread? Concentration test.
 C4  Monthly-withdrawal lens: how many months actually CHANGED SIGN? worst-month depth. n=40 months => noise?
 C5  Look-ahead: prior DA said 69/70 causal, 1 offender 2025-04-10. Does removing it move the aggregates?
ORPHAN-GUARD: saved under validation/, run once, report."""
import json,csv,io,contextlib,sys,bisect,datetime as dt,statistics as stx
from pathlib import Path
from collections import defaultdict,Counter
COST=0.35;HZ=120
VAL=Path("/Users/cristrein/tradingview-mcp/regime_turnstate_engine/validation");sys.path.insert(0,str(VAL))
with contextlib.redirect_stdout(io.StringIO()): import phase10_hybrid_regime as P
REG=P.run(0.03,1.15,0.88);T=P.T;H=P.H;L=P.L;C=P.C;n4=len(C)
def atr(i,k=14): return sum(max(H[j]-L[j],abs(H[j]-C[j-1]),abs(L[j]-C[j-1])) for j in range(i-k+1,i+1))/k
segs=[s for s in json.load(open("/tmp/causal_segments_v10.json")) if s["regime"]=="RANGE"]
def box_of(ts):
    for s in segs:
        if s['start']<=ts<=s['end']: return s
    return None
def sim_letrun(bi,entry,sl):
    risk=entry-sl
    if risk<=0: return None
    end=min(bi+HZ,n4-1)
    for j in range(bi+1,end+1):
        if L[j]<=sl: return -1.0
    return (C[end]-entry)/risk
D=Path("/Users/cristrein/tradingview-mcp/my-strategy/research/revalidation/XAU_4H_L2_BPT_BOS_CHOCH/v1/results")
rows=[]
for r in csv.DictReader(open(D/"l2_bpt_regua_structural.csv")):
    bi=int(r["bar_idx"]);t=T[bi];y=dt.datetime.utcfromtimestamp(t).year
    if y<2023: continue
    box=box_of(t);entry=float(r["entry"])
    R_base=round(float(r["letrun_struct"])-COST,2)
    if box:
        i0=bisect.bisect_left(T,box['start']);rmin=min(L[i0:bi+1]);a=atr(bi)
        R_mod=round((sim_letrun(bi,entry,rmin-0.1*a) or 0)-COST,2)
    else:
        R_mod=R_base
    rows.append({"bi":bi,"t":t,"ym":dt.datetime.utcfromtimestamp(t).strftime("%Y-%m"),
                 "date":dt.datetime.utcfromtimestamp(t).strftime("%Y-%m-%d"),
                 "range":bool(box),"reg_at_entry":REG[bi],
                 "R_base":R_base,"R_mod":R_mod})
rows.sort(key=lambda x:x["bi"])
print(f"REPRO: {len(rows)} trades, {sum(1 for x in rows if x['range'])} intra-range")

# ============================================================
# C1  INDEPENDENT RE-IMPLEMENTATION OF THE STREAK/RUN/MONTH/GAP METRICS
# ============================================================
def independent_metrics(vals):
    """vals in trade order. loss = v<=0 (BE/0 counts as a loss, same as original)."""
    n=len(vals);w=sum(1 for v in vals if v>0)
    # max consecutive losses + full run list (flush the open run at the end!)
    runs=[];cur=0
    for v in vals:
        if v<=0: cur+=1
        else:
            if cur>0: runs.append(cur)
            cur=0
    if cur>0: runs.append(cur)   # flush trailing run
    mx=max(runs) if runs else 0
    # avg trades between wins: reset counter at each win, count includes the winning trade
    gaps=[];g=0
    for v in vals:
        g+=1
        if v>0: gaps.append(g);g=0
    avggap=sum(gaps)/len(gaps) if gaps else 0
    return {"n":n,"w":w,"wr":100*w/n,"mx":mx,"runs":sorted(runs),
            "r3":sum(1 for q in runs if q>=3),"r5":sum(1 for q in runs if q>=5),
            "avggap":avggap,"trail_open_run":cur}
vb=[x["R_base"] for x in rows]; vm=[x["R_mod"] for x in rows]
mb=independent_metrics(vb); mm=independent_metrics(vm)
print("\n"+"="*80);print("C1  INDEPENDENT RE-IMPL vs ORIGINAL panel()");print("="*80)
print(f"  BASE: N={mb['n']} WR={mb['wr']:.0f}% max-streak={mb['mx']} r3={mb['r3']} r5={mb['r5']} gap={mb['avggap']:.1f}")
print(f"  MOD : N={mm['n']} WR={mm['wr']:.0f}% max-streak={mm['mx']} r3={mm['r3']} r5={mm['r5']} gap={mm['avggap']:.1f}")
# BE/zero handling: how many trades are EXACTLY 0 or between -0.35..0 (BE-ish)?
zeros_b=sum(1 for v in vb if v==0); zeros_m=sum(1 for v in vm if v==0)
print(f"  exact-zero R trades: base {zeros_b} mod {zeros_m}   (these are counted as LOSSES by v<=0)")
# does the panel flush the trailing open run? original panel HAS 'if streak: runs.append(streak)' after loop -> yes
# but max-loss-streak is tracked by mx=max(mx,streak) INSIDE loop -> trailing run already captured for mx. verify:
def original_style_mx(vals):
    streak=mx=0;runs=[]
    for v in vals:
        if v<=0: streak+=1;mx=max(mx,streak)
        else:
            if streak: runs.append(streak)
            streak=0
    if streak: runs.append(streak)
    return mx,sorted(runs)
omb,orb=original_style_mx(vb); omm,orm=original_style_mx(vm)
print(f"  cross-check original-style max-streak: base {omb} mod {omm}  (must equal independent {mb['mx']}/{mm['mx']})")
print(f"  run-list identical base? {orb==mb['runs']}  mod? {orm==mm['runs']}")

# ============================================================
# C2  FULL LOSS-RUN HISTOGRAM + relief metrics
# ============================================================
print("\n"+"="*80);print("C2  FULL LOSS-RUN HISTOGRAM (book) base vs mod");print("="*80)
hb=Counter(mb['runs']); hm=Counter(mm['runs'])
allk=sorted(set(hb)|set(hm))
print(f"  {'run-len':>8} | {'base #runs':>11} | {'mod #runs':>10}")
for k in allk:
    print(f"  {k:>8} | {hb.get(k,0):>11} | {hm.get(k,0):>10}")
print(f"  total losing trades: base {sum(k*v for k,v in hb.items())} mod {sum(k*v for k,v in hm.items())}")
print(f"  total run-episodes : base {sum(hb.values())} mod {sum(hm.values())}")
print(f"  win density (wins/N): base {mb['w']}/{mb['n']}={mb['w']/mb['n']:.3f}  mod {mm['w']}/{mm['n']}={mm['w']/mm['n']:.3f}")
# tail mass: sum of losses sitting in runs >=5 (the truly unholdable episodes)
tail_b=sum(k for k in mb['runs'] if k>=5); tail_m=sum(k for k in mm['runs'] if k>=5)
print(f"  losing trades trapped in runs>=5: base {tail_b} mod {tail_m}")

# rolling max drawdown-in-trades (equity of R) & time-underwater
def dd_profile(vals):
    cum=peak=0;dd=0;underwater=0;maxuw=0
    for v in vals:
        cum+=v;peak=max(peak,cum);d=cum-peak;dd=min(dd,d)
        if d<0: underwater+=1;maxuw=max(maxuw,underwater)
        else: underwater=0
    return dd,maxuw
ddb,uwb=dd_profile(vb); ddm,uwm=dd_profile(vm)
print(f"  maxDD(R): base {ddb:.1f} mod {ddm:.1f}   longest-time-underwater(trades): base {uwb} mod {uwm}")

# ============================================================
# C3  WHICH TRADES FLIPPED loss->win  (concentration)
# ============================================================
print("\n"+"="*80);print("C3  FLIPS loss->win and win->loss (concentration)");print("="*80)
flips_up=[x for x in rows if x["R_base"]<=0 and x["R_mod"]>0]
flips_dn=[x for x in rows if x["R_base"]>0 and x["R_mod"]<=0]
print(f"  loss->win flips: {len(flips_up)}   win->loss flips: {len(flips_dn)}")
byq=Counter(x["ym"][:7] for x in flips_up)
print("  loss->win flips by month:", dict(sorted(byq.items())))
for x in flips_up:
    print(f"    +FLIP {x['date']} R {x['R_base']:+.2f} -> {x['R_mod']:+.2f}  reg@entry={x['reg_at_entry']}")
for x in flips_dn:
    print(f"    -FLIP {x['date']} R {x['R_base']:+.2f} -> {x['R_mod']:+.2f}  reg@entry={x['reg_at_entry']}")
# concentration: what % of the +sumR delta comes from the single biggest month of flips
net_delta=sum(x["R_mod"]-x["R_base"] for x in rows)
delta_by_month=defaultdict(float)
for x in rows: delta_by_month[x["ym"]]+=x["R_mod"]-x["R_base"]
top_month=max(delta_by_month.items(),key=lambda kv:kv[1]) if delta_by_month else (None,0)
print(f"  net sumR delta base->mod: {net_delta:+.1f}")
print(f"  biggest single-month contribution to delta: {top_month[0]} {top_month[1]:+.1f} ({100*top_month[1]/net_delta:.0f}% of net)" if net_delta else "")
print("  delta by month (nonzero):", {k:round(v,1) for k,v in sorted(delta_by_month.items()) if abs(v)>0.05})

# ============================================================
# C4  MONTHLY-WITHDRAWAL LENS: months that CHANGED SIGN
# ============================================================
print("\n"+"="*80);print("C4  MONTHLY-WITHDRAWAL LENS");print("="*80)
mth_b=defaultdict(float);mth_m=defaultdict(float)
for x in rows: mth_b[x["ym"]]+=x["R_base"];mth_m[x["ym"]]+=x["R_mod"]
allm=sorted(set(mth_b)|set(mth_m))
sign_changes=[]
for m in allm:
    b=mth_b[m];mo=mth_m[m]
    if (b<=0)!=(mo<=0): sign_changes.append((m,b,mo))
posb=sum(1 for v in mth_b.values() if v>0); posm=sum(1 for v in mth_m.values() if v>0)
print(f"  total months: {len(allm)}   positive months: base {posb} mod {posm}")
print(f"  months that CHANGED SIGN: {len(sign_changes)}")
for m,b,mo in sign_changes:
    print(f"    {m}: {b:+.1f}R -> {mo:+.1f}R  ({'red->green' if b<=0 else 'green->red'})")
print(f"  worst month: base {min(mth_b.values()):+.1f} mod {min(mth_m.values()):+.1f}")
# how many months are trade-active (>=1 trade) — n for the % test
print(f"  active months (n for %pos test): {len(allm)}  -> +1 month sign flip moves %pos by {100/len(allm):.1f}pp")
# distribution of monthly R
print(f"  monthly R stdev: base {stx.pstdev(list(mth_b.values())):.2f} mod {stx.pstdev(list(mth_m.values())):.2f}")

# ============================================================
# C5  LOOK-AHEAD: the 1 non-causal-RANGE trade, does removing it move aggregates?
# ============================================================
print("\n"+"="*80);print("C5  LOOK-AHEAD (regime membership causal at entry?)");print("="*80)
noncausal=[x for x in rows if x["range"] and x["reg_at_entry"]!="RANGE"]
print(f"  intra-range trades whose reg@entry != RANGE (look-ahead membership): {len(noncausal)}")
for x in noncausal:
    print(f"    {x['date']} reg@entry={x['reg_at_entry']} R_base {x['R_base']:+.2f} R_mod {x['R_mod']:+.2f} dR {x['R_mod']-x['R_base']:+.2f}")
# aggregate WITHOUT the non-causal offenders (they revert to keeping SL_CONTEXT = R_base)
rows_causal=[]
for x in rows:
    y=dict(x)
    if x["range"] and x["reg_at_entry"]!="RANGE":
        y["R_mod"]=x["R_base"]  # would NOT get floor-SL under strictly-causal membership
    rows_causal.append(y)
vmc=[x["R_mod"] for x in rows_causal]
mmc=independent_metrics(vmc)
print(f"  MOD strictly-causal membership: WR={mmc['wr']:.0f}% sumR={sum(vmc):+.1f} max-streak={mmc['mx']} r3={mmc['r3']} r5={mmc['r5']} gap={mmc['avggap']:.1f}")
print(f"  vs reported MOD              : WR={mm['wr']:.0f}% sumR={sum(vm):+.1f} max-streak={mm['mx']} r3={mm['r3']} r5={mm['r5']} gap={mm['avggap']:.1f}")

print("\nDONE.")
