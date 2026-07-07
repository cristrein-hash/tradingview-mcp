import sys; sys.path.insert(0,"/Users/cristrein/tradingview-mcp/research/xau_15m_bb_nas_leonardo")
from agent_ctx_kit import S,TS,HI,LO,CL,ATR,EMA,RSI,N,ENTRIES,score,causal_swings_upto
from collections import Counter
import statistics as st

LOSER_T=set([21,23,31,49,50,55,56,57,59,60,65,66,67,68,69,79,83,84,85,89,93,94])
WIN_T=set([1,11,12,13,14,26,28,29,30,44,45,61,62,63,71,72,73,74,75,82,95,96])

def feats(e):
    j=e["j"]; i=e["i"]; lo=e["demand_low"]; a=ATR[i] or 5.0
    pivM=causal_swings_upto(j,6)  # macro
    pivF=causal_swings_upto(j,2)  # fine
    LsM=[(idx,pr) for tp,idx,pr,ci in pivM if tp=="L"]
    # leg origin = last macro L pivot at/before i
    origin=None
    for idx,pr in LsM:
        if idx<=i: origin=(idx,pr)
    oidx = origin[0] if origin else 0
    olo  = origin[1] if origin else LO[oidx]
    # leg high = max HI from origin..j (causal)
    leg_hi = max(HI[oidx:j+1])
    leg_range = max(leg_hi-olo, 1e-6)
    # retrace depth of demand low within leg (1=back to origin, 0=at top)
    retrace = (leg_hi - lo)/leg_range
    # fine pushes since origin: count monotonic higher-highs among fine H pivots with idx>oidx
    HsF=[(idx,pr) for tp,idx,pr,ci in pivF if tp=="H" and idx>oidx]
    HsF.sort()
    pushes=0; prevh=None
    for idx,pr in HsF:
        if prevh is None or pr>prevh: pushes+=1; prevh=pr
    # extension of leg_hi above origin in ATR
    ext = (leg_hi-olo)/a
    # entry chase: how far ent is above demand low in ATR
    chase = (e["ent"]-lo)/a
    # lower-highs (bear): last 3 fine H pivots monotonic down
    recH=[pr for idx,pr in sorted([(idx,pr) for tp,idx,pr,ci in pivF if tp=="H"])][-3:]
    lower_highs = len(recH)>=3 and recH[2]<recH[1]<recH[0]
    # bars since origin (leg age)
    legage=j-oidx
    return dict(retrace=round(retrace,2),pushes=pushes,ext=round(ext,1),chase=round(chase,1),
                LH=int(lower_highs),legage=legage)

print("feat  |  WIN mean/med   LOSE mean/med")
for k in ["retrace","pushes","ext","chase","legage"]:
    W=[feats(e)[k] for e in ENTRIES if e["out"]==1]
    L=[feats(e)[k] for e in ENTRIES if e["out"]==0]
    print(f"{k:>8} | W {st.mean(W):.2f}/{st.median(W):.2f}   L {st.mean(L):.2f}/{st.median(L):.2f}")

print("\npushes dist  WIN",dict(sorted(Counter(feats(e)['pushes'] for e in ENTRIES if e['out']==1).items())),
      " LOSE",dict(sorted(Counter(feats(e)['pushes'] for e in ENTRIES if e['out']==0).items())))
print("LH count  WIN",sum(feats(e)['LH'] for e in ENTRIES if e['out']==1),"/52  LOSE",sum(feats(e)['LH'] for e in ENTRIES if e['out']==0),"/44")

print("\n--- targets ---")
for tag,ns in [("LOSER_T",LOSER_T),("WIN_T",WIN_T)]:
    print("==",tag)
    for e in ENTRIES:
        if e["n"] in ns:
            f=feats(e); print(f"n{e['n']:>2} out{e['out']} retr{f['retrace']:>5} push{f['pushes']} ext{f['ext']:>5} chase{f['chase']:>4} LH{f['LH']} age{f['legage']:>3}")
