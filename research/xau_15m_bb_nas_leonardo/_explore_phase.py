import sys; sys.path.insert(0,"/Users/cristrein/tradingview-mcp/research/xau_15m_bb_nas_leonardo")
from agent_ctx_kit import S,TS,HI,LO,CL,ATR,EMA,RSI,N,ENTRIES,score,causal_swings_upto

# Explore causal swing structure at each entry's j
loser_targets=set([21,23,31,49,50,55,56,57,59,60,65,66,67,68,69,79,83,84,85,89,93,94])
winner_keys=set([1,11,12,13,14,26,28,29,30,44,45,61,62,63,71,72,73,74,75,82,95,96])

for e in ENTRIES[:8]:
    j=e["j"]; i=e["i"]
    sw=causal_swings_upto(j)
    # last few swings
    tail=sw[-6:]
    print(f"n={e['n']} out={e['out']} i={i} j={j} rlag={e['reclaim_lag']} legtop={e['leg_top']:.1f} dlow={e['demand_low']:.1f}")
    for tp,idx,pr,ci in tail:
        print(f"    {tp} idx={idx} pr={pr:.1f} conf={ci}")
