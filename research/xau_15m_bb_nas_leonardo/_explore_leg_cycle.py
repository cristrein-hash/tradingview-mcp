import sys; sys.path.insert(0,"/Users/cristrein/tradingview-mcp/research/xau_15m_bb_nas_leonardo")
from agent_ctx_kit import S,TS,HI,LO,CL,ATR,EMA,RSI,N,ENTRIES,score,causal_swings_upto

LOSER_T=[21,23,31,49,50,55,56,57,59,60,65,66,67,68,69,79,83,84,85,89,93,94]
WIN_T=[1,11,12,13,14,26,28,29,30,44,45,61,62,63,71,72,73,74,75,82,95,96]

def leg_features(e):
    j=e["j"]; i=e["i"]
    piv=causal_swings_upto(j)  # (tp,idx,price,conf_bar) confirmed by j
    # separate H and L pivots (by pivot index), sorted by idx
    # find leg origin = most recent L pivot at or before the demand low i
    Ls=[(idx,pr) for tp,idx,pr,ci in piv if tp=="L"]
    Hs=[(idx,pr) for tp,idx,pr,ci in piv if tp=="H"]
    Ls.sort(); Hs.sort()
    # origin = last L pivot with idx <= i  (start of current leg up)
    origin=None
    for idx,pr in Ls:
        if idx<=i: origin=(idx,pr)
    # pushes since origin: count H pivots with idx> origin_idx and idx<=j
    oidx = origin[0] if origin else -1
    Hs_since=[(idx,pr) for idx,pr in Hs if idx>oidx]
    # count higher-highs among Hs_since (monotonic increasing highs = pushes)
    pushes=0; prevh=None
    for idx,pr in Hs_since:
        if prevh is None or pr>prevh: pushes+=1; prevh=pr
    # lower-highs among recent Hs (bear signal): last 3 H pivots
    recentH=[pr for idx,pr in Hs if idx<=j][-3:]
    lower_highs = len(recentH)>=2 and all(recentH[k]<recentH[k-1] for k in range(1,len(recentH)))
    # fresh low: demand low below recent L pivots (sweep). compare e['demand_low'] to prior L pivots before i
    priorLs=[pr for idx,pr in Ls if idx<i]
    lo=e["demand_low"]
    fresh_low = (len(priorLs)==0) or (lo < min(priorLs[-3:]))
    # sweep depth relative to recent low
    a=ATR[i] or 5.0
    sweep = (min(priorLs[-3:])-lo)/a if len(priorLs)>=1 else 0.0
    # higher-lows: is demand low above prior L pivot (uptrend pullback)?
    higher_low = len(priorLs)>=1 and lo>priorLs[-1]
    # distance of demand low below leg_top relative to leg range (retrace depth)
    return dict(pushes=pushes,lower_highs=lower_highs,fresh_low=fresh_low,sweep=round(sweep,2),
                higher_low=higher_low,nH=len(Hs),nL=len(Ls))

for tag,ns in [("LOSER_T",LOSER_T),("WIN_T",WIN_T)]:
    print("===",tag)
    for e in ENTRIES:
        if e["n"] in ns:
            f=leg_features(e)
            print(f"n{e['n']:>2} out{e['out']} push{f['pushes']} LH{int(f['lower_highs'])} fresh{int(f['fresh_low'])} swp{f['sweep']:>5} HL{int(f['higher_low'])}")

# aggregate distributions
import statistics as st
def agg(pred_ns):
    ws=[e for e in ENTRIES if e["out"]==1]; ls=[e for e in ENTRIES if e["out"]==0]
    return
print("\n--- push distribution winners vs losers ---")
for grp,lab in [([e for e in ENTRIES if e["out"]==1],"WIN"),([e for e in ENTRIES if e["out"]==0],"LOSE")]:
    ps=[leg_features(e)["pushes"] for e in grp]
    from collections import Counter
    print(lab, "mean",round(sum(ps)/len(ps),2),"dist",dict(sorted(Counter(ps).items())))
