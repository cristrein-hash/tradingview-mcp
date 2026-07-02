#!/usr/bin/env python3
"""DEVIL'S ADVOCATE on phase31_range_frequency_cut (Cris' "keep 1st + last-2" range freq-cut).
GOAL of the user: operational viability (kill 13:1 loss cluster / max-loss-streak) for a monthly-withdrawal prop.
The tempting-but-wrong conclusion = "last-2 win, so it works". last-2 is HINDSIGHT.

This script investigates 5 DA points:
 1. Is "last-2 win" a LET-RUN TAUTOLOGY? Decompose last-2 R into within-range vs post-range-end contribution.
    Truncate let-run at range box end -> do last-2 still win?
 2. Where does max-loss-streak=11 live? Print the actual 11-run: range vs non-range, dates. Streak within range-only.
 3. Any CAUSAL proxy for "the last entries" better than BOS-up? Test upper-third+age, higher-lows, post-HH, vol-contraction.
    Must beat permutation-null-of-max.
 4. Selection/multiple-testing across ~6 rules x 2 SL.
 5. Honest viability: does ANY causal freq-cut lower runs>=5 / max-streak / raise %green-months without hindsight?

Orphan-guard: standalone repro, reads same inputs as phase31. Does NOT touch production."""
import json,csv,io,contextlib,sys,bisect,datetime as dt,random
from pathlib import Path
from collections import defaultdict
COST=0.35;HZ=120
VAL=Path("/Users/cristrein/tradingview-mcp/regime_turnstate_engine/validation");sys.path.insert(0,str(VAL))
with contextlib.redirect_stdout(io.StringIO()): import phase10_hybrid_regime as P
P.run(0.03,1.15,0.88);T=P.T;H=P.H;L=P.L;C=P.C;n4=len(C)
def atr(i,k=14): return sum(max(H[j]-L[j],abs(H[j]-C[j-1]),abs(L[j]-C[j-1])) for j in range(i-k+1,i+1))/k
segs=[s for s in json.load(open("/tmp/causal_segments_v10.json")) if s["regime"]=="RANGE"]
def box_of(ts):
    for s in segs:
        if s['start']<=ts<=s['end']: return s
    return None

# sim: full let-run to HZ (as phase31). Returns R.
def sim(bi,entry,sl,hz=HZ):
    if entry-sl<=0: return None
    end=min(bi+hz,n4-1)
    for j in range(bi+1,end+1):
        if L[j]<=sl: return -1.0
    return (C[end]-entry)/(entry-sl)

# sim TRUNCATED at a given last-bar index (exit at close of exit_idx or SL, whichever first).
def sim_trunc(bi,entry,sl,exit_idx):
    if entry-sl<=0: return None
    end=min(exit_idx,bi+HZ,n4-1)
    if end<=bi: end=min(bi+1,n4-1)
    for j in range(bi+1,end+1):
        if L[j]<=sl: return -1.0
    return (C[end]-entry)/(entry-sl)

def bos_up(bi,box):
    i0=bisect.bisect_left(T,box['start'])
    if bi-3<=i0: return False
    return C[bi]>max(H[i0:bi-2])

D=Path("/Users/cristrein/tradingview-mcp/my-strategy/research/revalidation/XAU_4H_L2_BPT_BOS_CHOCH/v1/results")
rows=[]
for r in csv.DictReader(open(D/"l2_bpt_regua_structural.csv")):
    bi=int(r["bar_idx"]);t=T[bi];y=dt.datetime.utcfromtimestamp(t).year
    if y<2023: continue
    box=box_of(t);entry=float(r["entry"])
    R_base=round(float(r["letrun_struct"])-COST,2)
    d={"bi":bi,"t":t,"ym":dt.datetime.utcfromtimestamp(t).strftime("%Y-%m"),
       "date":dt.datetime.utcfromtimestamp(t).strftime("%Y-%m-%d"),"range":bool(box),"R_base":R_base,"entry":entry}
    if box:
        i0=bisect.bisect_left(T,box['start']);rmin=min(L[i0:bi+1]);a=atr(bi)
        sl_piso=rmin-0.1*a
        d["sl_piso"]=sl_piso
        d["R_piso"]=round((sim(bi,entry,sl_piso) or 0)-COST,2)
        d["boxkey"]=(box['start'],box['end']);d["box_end"]=box['end'];d["bos"]=bos_up(bi,box)
        # position within range box (upper-third etc.)
        d["box_hi"]=box['hi'];d["box_lo"]=box['lo']
    else:
        d["R_piso"]=R_base;d["boxkey"]=None;d["bos"]=False;d["box_end"]=None;d["sl_piso"]=None
    rows.append(d)
rows.sort(key=lambda x:x["bi"])
byrange=defaultdict(list)
for x in rows:
    if x["range"]: byrange[x["boxkey"]].append(x)
for k,g in byrange.items():
    g.sort(key=lambda z:z["bi"])
    for i,x in enumerate(g):
        x["is_first"]=(i==0);x["is_last2"]=(i>=len(g)-2);x["idx"]=i;x["nrange"]=len(g)

def stats(rs):
    n=len(rs);w=sum(1 for v in rs if v>0);s=sum(rs)
    cum=peak=dd=0;streak=mx=0;runs=[]
    for v in rs:
        cum+=v;peak=max(peak,cum);dd=min(dd,cum-peak)
        if v<=0: streak+=1;mx=max(mx,streak)
        else:
            if streak: runs.append(streak)
            streak=0
    if streak: runs.append(streak)
    r5=sum(1 for q in runs if q>=5)
    return n,(100*w/n if n else 0),s,dd,mx,r5

print("="*100)
print("DA POINT 1 — IS 'last-2 win' A LET-RUN TAUTOLOGY? (within-range R vs post-range-end R)")
print("="*100)
print("For each last-2 entry: R with full let-run (HZ120) vs R truncated at range box_end.")
print("If the win comes ONLY from holding into the post-range bull leg, it's hindsight-of-outcome, not tradeable.\n")
last2=[x for x in rows if x["range"] and x["is_last2"]]
# box_end index
def endidx(box_end): return bisect.bisect_right(T,box_end)-1
tot_full=tot_trunc=0
wins_full=wins_trunc=0
detail=[]
for x in last2:
    ei=endidx(x["box_end"])
    Rf=x["R_piso"]  # full let-run piso (already -COST)
    # truncated at box end, same SL piso
    rt=sim_trunc(x["bi"],x["entry"],x["sl_piso"],ei)
    Rt=round((rt if rt is not None else 0)-COST,2)
    # how many bars is the entry from range end?
    bars_to_end=ei-x["bi"]
    tot_full+=Rf;tot_trunc+=Rt
    wins_full+=(Rf>0);wins_trunc+=(Rt>0)
    detail.append((x["date"],x["nrange"],bars_to_end,Rf,Rt))
print(f"  {'date':11} {'nrange':>6} {'bars2end':>8} {'R_full':>7} {'R_trunc@boxend':>14}")
for dte,nr,b2e,Rf,Rt in detail:
    flag=" <-- flips" if (Rf>0)!=(Rt>0) else ""
    print(f"  {dte:11} {nr:>6} {b2e:>8} {Rf:>+7.2f} {Rt:>+14.2f}{flag}")
print(f"\n  LAST-2 TOTAL: full let-run sumR={tot_full:+.1f} (wins {wins_full}/{len(last2)})  |  truncated@boxend sumR={tot_trunc:+.1f} (wins {wins_trunc}/{len(last2)})")
print(f"  => fraction of last-2 R that survives truncation at range end: {(tot_trunc/tot_full if tot_full else 0):.2f}")
print("  INTERPRETATION: if trunc sumR collapses / wins drop sharply, the last-2 edge is post-range hindsight (tautology).")

print("\n"+"="*100)
print("DA POINT 2 — WHERE DOES max-loss-streak=11 LIVE? (range vs non-range, dates)")
print("="*100)
# reconstruct baseline sequence order = rows sorted by bi, R_base
seq=[(x["date"],x["range"],x["R_base"]) for x in rows]
# find the run of length 11 (longest losing run)
best=None;cur=[];
for i,(dte,rng,R) in enumerate(seq):
    if R<=0: cur.append(i)
    else:
        if best is None or len(cur)>len(best): best=cur[:]
        cur=[]
if best is None or len(cur)>len(best): best=cur[:]
print(f"  Longest losing run in BASELINE (SL_CONTEXT) = {len(best)} trades. Composition:")
nr_run=sum(1 for i in best if seq[i][1])
print(f"    range trades in the run: {nr_run}/{len(best)}  |  non-range: {len(best)-nr_run}/{len(best)}")
for i in best:
    dte,rng,R=seq[i]
    print(f"      {dte}  {'RANGE' if rng else 'non-range':10}  R={R:+.2f}")
# streak WITHIN range-only trades, under each keep-rule
print("\n  Max-loss-streak computed on RANGE-ONLY subsequence (does cutting frequency lower THIS?):")
def range_only_streak(keepfn,Rkey):
    sub=[x for x in rows if x["range"] and keepfn(x)]
    rs=[x[Rkey] for x in sub]
    _,_,_,_,mx,r5=stats(rs)
    return len(rs),mx,r5
for name,keepfn in [("all range",lambda x:True),
                    ("1st+last2 (hindsight)",lambda x:x["is_first"] or x["is_last2"]),
                    ("1st+BOS (causal)",lambda x:x["is_first"] or x["bos"]),
                    ("cap3 (causal)",lambda x:x["idx"]<3),
                    ("1st only (causal)",lambda x:x["is_first"])]:
    n,mx,r5=range_only_streak(keepfn,"R_piso")
    print(f"    {name:26} range-N={n:2}  max-loss-streak(range-only)={mx:2}  runs>=5:{r5}")
print("  NOTE: the book streak=11 is what the human feels; the range-only streak is the '13:1 cluster' claim.")

print("\n"+"="*100)
print("DA POINT 3 — ANY CAUSAL PROXY FOR 'the last entries' BETTER THAN BOS-up?")
print("="*100)
# Build candidate causal 'late/resolution' proxies, evaluated at entry bar bi (close-only causal).
def upper_third(x):
    if x["box_hi"]==x["box_lo"]: return False
    return (x["entry"]-x["box_lo"])/(x["box_hi"]-x["box_lo"])>=0.667
def range_age_high(x):
    # entry is in the late portion of the range's entry-sequence by TIME, not index (idx is hindsight-ish? idx is causal:
    # you DO know how many entries have fired so far. but 'age high' by absolute bars from box start is causal.)
    i0=bisect.bisect_left(T,x["boxkey"][0])
    age=x["bi"]-i0
    return age  # numeric; threshold applied below
def n_higher_lows(x,k=3):
    # k consecutive higher-lows ending at entry bar (causal)
    bi=x["bi"]
    if bi-k-1<0: return False
    lows=[L[bi-j] for j in range(k+1)][::-1]  # oldest..newest
    return all(lows[j+1]>lows[j] for j in range(k))
def after_hh(x):
    # first entry after a higher-high forms vs prior 10 bars (causal): C[bi]>max(H[bi-10:bi])
    bi=x["bi"]
    if bi-10<0: return False
    return C[bi]>max(H[bi-10:bi])
def vol_contraction(x):
    # ATR now < 0.8 * ATR 10 bars ago (coiled) — causal
    bi=x["bi"]
    if bi-24<0: return False
    return atr(bi)<0.8*atr(bi-10)
# range_age: compute median age to threshold "high"
for k,g in byrange.items():
    i0=bisect.bisect_left(T,k[0])
    for x in g: x["_age"]=x["bi"]-i0
ages=sorted(x["_age"] for x in rows if x["range"])
age_med=ages[len(ages)//2] if ages else 0
def age_high(x): return x["range"] and x["_age"]>=age_med

proxies={
 "BOS-up (baseline proxy)":lambda x:x["bos"],
 "upper-third of box":upper_third,
 "age>=median":age_high,
 "3 consec higher-lows":lambda x:n_higher_lows(x,3),
 "after higher-high(10)":after_hh,
 "vol-contraction":vol_contraction,
 "upper-third AND age-high":lambda x:upper_third(x) and age_high(x),
 "upper-third AND after-HH":lambda x:upper_third(x) and after_hh(x),
}
# ground truth: last-2 membership
print("  Each proxy as a selector of range entries. Precision/recall vs the hindsight 'last-2' set, and realized sumR (SL_CONTEXT).")
range_rows=[x for x in rows if x["range"]]
last2set=set(id(x) for x in range_rows if x["is_last2"])
print(f"  {'proxy':28} {'fires':>5} {'prec(last2)':>11} {'rec(last2)':>10} {'sumR(fired,base)':>16} {'sumR(fired,piso)':>16}")
proxy_results={}
for name,fn in proxies.items():
    fired=[x for x in range_rows if fn(x)]
    nf=len(fired)
    hit=sum(1 for x in fired if id(x) in last2set)
    prec=hit/nf if nf else 0
    rec=hit/len(last2set) if last2set else 0
    sumR_base=sum(x["R_base"] for x in fired)
    sumR_piso=sum(x["R_piso"] for x in fired)
    proxy_results[name]=(nf,sumR_base,sumR_piso)
    print(f"  {name:28} {nf:>5} {prec:>11.2f} {rec:>10.2f} {sumR_base:>+16.1f} {sumR_piso:>+16.1f}")

print("\n"+"="*100)
print("DA POINT 3b — PERMUTATION NULL-OF-MAX for the best causal proxy (is fired-sumR beyond random selection?)")
print("="*100)
# Null: randomly pick k range entries (same count as proxy fires), sumR. Take MAX over all proxies' best -> null-of-max.
# We do a per-proxy null AND a null-of-max across the searched proxies.
random.seed(42)
NPERM=20000
range_R_base=[x["R_base"] for x in range_rows]
range_R_piso=[x["R_piso"] for x in range_rows]
def perm_pvalue(observed,k,pool):
    ge=0
    for _ in range(NPERM):
        samp=random.sample(pool,k)
        if sum(samp)>=observed: ge+=1
    return (ge+1)/(NPERM+1)
# best causal proxy by piso sumR (exclude the hindsight last2, exclude 1st-only which isn't a 'late' proxy)
causal_names=[n for n in proxies if n!="BOS-up (baseline proxy)"] + ["BOS-up (baseline proxy)"]
best_name=max(proxies,key=lambda n:proxy_results[n][2])  # by piso sumR
kbest,sb_base,sb_piso=proxy_results[best_name]
print(f"  best causal proxy by fired sumR(piso) = '{best_name}': k={kbest} fires, sumR_piso={sb_piso:+.1f}, sumR_base={sb_base:+.1f}")
if kbest>0:
    p_piso=perm_pvalue(sb_piso,kbest,range_R_piso)
    p_base=perm_pvalue(sb_base,kbest,range_R_base)
    print(f"    per-proxy permutation p (random k range entries): piso p={p_piso:.4f}  base p={p_base:.4f}")
# null-of-max across searched proxies: for each perm draw, take the MAX sumR achievable at each proxy's k -> compare
# Simplify: compute distribution of MAX-over-proxies of (random-k sumR) using each proxy's k.
ks=[proxy_results[n][0] for n in proxies if proxy_results[n][0]>0]
obs_max_piso=max(proxy_results[n][2] for n in proxies)
random.seed(7)
ge=0
for _ in range(NPERM):
    m=-1e9
    for k in set(ks):
        s=sum(random.sample(range_R_piso,k))
        if s>m: m=s
    if m>=obs_max_piso: ge+=1
p_nom=(ge+1)/(NPERM+1)
print(f"  NULL-OF-MAX (best proxy piso sumR={obs_max_piso:+.1f} vs max over random selections at searched k's): p={p_nom:.4f}")
print("  If p_nom > 0.1, no causal proxy beats random selection after accounting for the search.")

print("\n"+"="*100)
print("DA POINT 4 — SELECTION / MULTIPLE-TESTING vs BASELINE on viability metrics")
print("="*100)
def full_panel(keepfn,Rkey):
    kept=[x for x in rows if (not x["range"]) or keepfn(x)]
    rs=[x[Rkey] if x["range"] else x["R_base"] for x in kept]
    n,wr,s,dd,mx,r5=stats(rs)
    mth=defaultdict(float)
    for x,v in zip(kept,rs): mth[x["ym"]]+=v
    posm=sum(1 for v in mth.values() if v>0);totm=len(mth)
    return n,wr,s,dd,mx,r5,posm,totm
variants=[
 ("BASELINE all SL_CONTEXT",lambda x:True,"R_base"),
 ("all range +SL-piso",lambda x:True,"R_piso"),
 ("1st+last2 HINDSIGHT piso",lambda x:x["is_first"] or x["is_last2"],"R_piso"),
 ("1st+last2 HINDSIGHT ctx",lambda x:x["is_first"] or x["is_last2"],"R_base"),
 ("1st+BOS causal piso",lambda x:x["is_first"] or x["bos"],"R_piso"),
 ("cap3 causal piso",lambda x:x["idx"]<3,"R_piso"),
 ("1st only causal piso",lambda x:x["is_first"],"R_piso"),
]
print(f"  {'variant':30} {'N':>3} {'WR':>4} {'sumR':>7} {'DD':>7} {'streak':>6} {'runs>=5':>7} {'green-m':>8}")
base_row=None
for name,fn,rk in variants:
    n,wr,s,dd,mx,r5,pm,tm=full_panel(fn,rk)
    tag=""
    if name.startswith("BASELINE"): base_row=(mx,r5,pm/tm if tm else 0)
    print(f"  {name:30} {n:>3} {wr:>3.0f}% {s:>+7.1f} {dd:>+7.1f} {mx:>6} {r5:>7} {pm:>3}/{tm:<3}({100*pm/tm:.0f}%)")
print(f"\n  Baseline viability: max-streak={base_row[0]} runs>=5={base_row[1]} green-months={100*base_row[2]:.0f}%")
print("  A causal variant only 'helps' if it lowers streak/runs>=5 or raises green-m WITHOUT losing money AND survives ~12-test search.")

print("\n"+"="*100)
print("DA POINT 5 — HONEST VIABILITY BOTTOM LINE")
print("="*100)
# does any CAUSAL freq-cut lower runs>=5 or streak or raise green-m while staying >=0 sumR?
print("  Causal candidates (piso) net sumR and viability delta vs baseline:")
for name,fn,rk in variants:
    if "HINDSIGHT" in name or name.startswith("BASELINE") or name.startswith("all range"): continue
    n,wr,s,dd,mx,r5,pm,tm=full_panel(fn,rk)
    d_streak=mx-base_row[0];d_r5=r5-base_row[1];d_green=(pm/tm if tm else 0)-base_row[2]
    profit="PROFIT" if s>=0 else "LOSES MONEY"
    print(f"    {name:26} sumR={s:+6.1f}[{profit}]  Δstreak={d_streak:+d} Δruns>=5={d_r5:+d} Δgreen-m={100*d_green:+.0f}pp")
print("\n  Same for the HINDSIGHT ceiling (for reference only — NOT tradeable):")
for name,fn,rk in variants:
    if "HINDSIGHT" not in name: continue
    n,wr,s,dd,mx,r5,pm,tm=full_panel(fn,rk)
    d_streak=mx-base_row[0];d_r5=r5-base_row[1];d_green=(pm/tm if tm else 0)-base_row[2]
    print(f"    {name:26} sumR={s:+6.1f}  Δstreak={d_streak:+d} Δruns>=5={d_r5:+d} Δgreen-m={100*d_green:+.0f}pp  (HINDSIGHT)")

print("\n"+"="*100)
print("DA POINT 3c — STRESS-TEST the one 'promising' proxy (age>=median): viability + robustness")
print("="*100)
# The user's goal is VIABILITY (kill loss-cluster), not raw sumR. Does age>=median as a KEEP-RULE
# (keep 1st + age-high range entries) actually improve viability, and is the sumR concentrated / stable?
def age_keep(x): return x["is_first"] or age_high(x)
n,wr,s,dd,mx,r5,pm,tm=full_panel(age_keep,"R_piso")
print(f"  KEEP-RULE '1st + age>=median' (piso): N={n} WR={wr:.0f}% sumR={s:+.1f} DD={dd:+.1f} streak={mx} runs>=5:{r5} green-m={pm}/{tm}({100*pm/tm:.0f}%)")
print(f"    vs baseline streak=11 runs>=5=6 green-m=40%")
# is the age>=median sumR concentrated in 1-2 ranges? leave-one-range-out
print("\n  Leave-one-RANGE-out on age>=median fired entries (piso sumR):")
fired=[x for x in range_rows if age_high(x)]
by_r=defaultdict(list)
for x in fired: by_r[x["boxkey"]].append(x)
total=sum(x["R_piso"] for x in fired)
worst=None
for k in sorted(by_r):
    rest=total-sum(x["R_piso"] for x in by_r[k])
    d0=dt.datetime.utcfromtimestamp(k[0]).strftime("%Y-%m-%d")
    contrib=sum(x['R_piso'] for x in by_r[k])
    if worst is None or contrib>worst[1]: worst=(d0,contrib,rest,len(by_r[k]))
print(f"    biggest single-range contributor: {worst[0]} contributes {worst[1]:+.1f}R ({worst[3]} entries); sumR without it = {worst[2]:+.1f}")
# by year
print("\n  age>=median fired sumR by YEAR (piso):")
by_y=defaultdict(float);by_yn=defaultdict(int)
for x in fired:
    y=x["date"][:4];by_y[y]+=x["R_piso"];by_yn[y]+=1
for y in sorted(by_y): print(f"    {y}: N={by_yn[y]:2} sumR={by_y[y]:+.1f}")
# WHAT is age>=median really selecting? correlation with just 'more bars held' -> longer let-run window before HZ cap
# Check: does age-high simply = entries that are NOT in the first-few of a range (so overlaps with 'not-first losers')?
print("\n  Sanity: age>=median composition — how many are ALSO is_first / is_last2 / neither:")
af=[x for x in range_rows if age_high(x)]
print(f"    fired={len(af)}  also is_first={sum(1 for x in af if x['is_first'])}  also is_last2={sum(1 for x in af if x['is_last2'])}  neither={sum(1 for x in af if not x['is_first'] and not x['is_last2'])}")
print("  => if age>=median is mostly the SAME entries as last-2 or just 'held longer into bull', it inherits the let-run tautology.")
# decompose age>=median R into within-range vs post-range (like point 1)
tot_full=tot_trunc=0
for x in af:
    ei=endidx(x["box_end"])
    rt=sim_trunc(x["bi"],x["entry"],x["sl_piso"],ei)
    Rt=round((rt if rt is not None else 0)-COST,2)
    tot_full+=x["R_piso"];tot_trunc+=Rt
print(f"  age>=median R decomposition: full let-run sumR={tot_full:+.1f}  truncated@boxend sumR={tot_trunc:+.1f}  (survives {100*tot_trunc/tot_full if tot_full else 0:.0f}%)")

print("\n"+"="*100)
print("DA POINT 3d — age>=median: is the +37R CONCENTRATED and does it FADE? (the kill-shot)")
print("="*100)
fired=[x for x in range_rows if age_high(x)]
srt=sorted(fired,key=lambda x:-x["R_piso"])
top3=sum(x["R_piso"] for x in srt[:3]);tot=sum(x["R_piso"] for x in fired)
print(f"  top-3 entries contribute {top3:+.1f} of {tot:+.1f} total = {100*top3/tot:.0f}% of the proxy's sumR")
for x in srt[:3]: print(f"     {x['date']} R={x['R_piso']:+.2f} (range starting {dt.datetime.utcfromtimestamp(x['boxkey'][0]).strftime('%Y-%m-%d')})")
print(f"  2023 alone = +23.8R from N=4; 2024=+12.2 N=13; 2025=+1.2 N=18  => edge FADES to ~0 by 2025 (18 trades, +1.2R).")
print(f"  As a KEEP-RULE it does NOT lower streak (still 11, lives in non-range) and green-months stays 40% (no viability gain).")
