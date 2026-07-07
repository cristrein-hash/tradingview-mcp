import sys; sys.path.insert(0,"/Users/cristrein/tradingview-mcp/research/xau_15m_bb_nas_leonardo")
from agent_ctx_kit import S,TS,HI,LO,CL,ATR,EMA,RSI,N,ENTRIES,score,causal_swings_upto

loser_targets=set([21,23,31,49,50,55,56,57,59,60,65,66,67,68,69,79,83,84,85,89,93,94])
winner_keys=set([1,11,12,13,14,26,28,29,30,44,45,61,62,63,71,72,73,74,75,82,95,96])

def feats(e):
    j=e["j"]; i=e["i"]; a=ATR[i] or 5.0
    sw=causal_swings_upto(j)
    Hs=[(idx,pr) for tp,idx,pr,ci in sw if tp=="H"]
    Ls=[(idx,pr) for tp,idx,pr,ci in sw if tp=="L"]
    f={}
    # --- structure direction: recent highs ascending vs descending ---
    if len(Hs)>=2:
        f["hh"]=1 if Hs[-1][1]>Hs[-2][1] else 0     # last high higher than prev
        f["dh_slope"]=(Hs[-1][1]-Hs[-2][1])/a
    else:
        f["hh"]=1; f["dh_slope"]=0
    if len(Hs)>=3:
        f["hh2"]=1 if (Hs[-1][1]>Hs[-2][1]>Hs[-3][1]) else 0  # two consecutive higher highs
        f["lh2"]=1 if (Hs[-1][1]<Hs[-2][1]<Hs[-3][1]) else 0  # two consecutive lower highs (bear)
    else:
        f["hh2"]=0; f["lh2"]=0
    # lows ascending (higher lows = uptrend)
    if len(Ls)>=2:
        f["hl"]=1 if Ls[-1][1]>Ls[-2][1] else 0
    else:
        f["hl"]=1
    # --- push count: consecutive HH since last major low ---
    push=0
    for k in range(len(Hs)-1,0,-1):
        if Hs[k][1]>Hs[k-1][1]: push+=1
        else: break
    f["push"]=push
    # --- pullback depth / flush ---
    lt=e["leg_top"]; dl=e["demand_low"]
    f["depth"]=(lt-dl)/a                     # pullback depth in ATR
    f["reclaim"]=e["reclaim_lag"]
    # speed: bars from leg_top index to demand low i
    # find most recent H before i in swings
    lt_idx=None
    for idx,pr in Hs:
        if idx<=i: lt_idx=idx
    if lt_idx is not None:
        f["flush_bars"]=i-lt_idx
        f["flush_speed"]=(lt-dl)/max(1,(i-lt_idx))/a   # depth per bar
    else:
        f["flush_bars"]=99; f["flush_speed"]=0
    # position of entry within recent range (topping vs fresh)
    # last confirmed H price vs entry
    if Hs:
        lastH=Hs[-1][1]
        f["ent_vs_H"]=(e["ent"]-lastH)/a   # entry above last high = breakout/chase-topish
    else:
        f["ent_vs_H"]=0
    # rsi at j
    f["rsi"]=RSI[j] if RSI[j] is not None else 50
    # ema dist
    f["ema_dist"]=(e["ent"]-(EMA[j] or e["ent"]))/a
    return f

rows=[(e["n"],e["out"],feats(e)) for e in ENTRIES]

import statistics as st
def split(key):
    W=[f[key] for n,o,f in rows if o==1]
    L=[f[key] for n,o,f in rows if o==0]
    return f"{key:12s} W_med={st.median(W):7.2f} L_med={st.median(L):7.2f}  W_mean={st.mean(W):7.2f} L_mean={st.mean(L):7.2f}"

for k in ["hh","hh2","lh2","hl","dh_slope","push","depth","reclaim","flush_bars","flush_speed","ent_vs_H","rsi","ema_dist"]:
    print(split(k))

print("\n--- loser_targets feature medians vs winner_keys ---")
def grp(ns):
    return {k:st.median([f[k] for n,o,f in rows if n in ns]) for k in ["hh2","lh2","push","depth","ent_vs_H","dh_slope","flush_bars","rsi"]}
print("LOSER_TGT:",grp(loser_targets))
print("WINNER_KY:",grp(winner_keys))
