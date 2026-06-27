#!/usr/bin/env python3
"""Independent verification of E3_shallowleg loser-cut filter.
Filter under test: low_wick>=0.155 AND sell_pol<=0.5 (KEEP).
Recompute WR before/after, maxstreak before/after, winners_kept, losers_cut,
and WR-after by YEAR and by BLOCK. Check threshold-neighborhood stability.
"""
import json

PATH = "/Users/cristrein/tradingview-mcp/research/xau_15m_bb_nas_leonardo/entry_dataset.jsonl"
rows = [json.loads(l) for l in open(PATH) if l.strip()]

# membership: macro_drop_atr<4 AND disp4_atr<-0.5
mem = [r for r in rows if r.get("macro_drop_atr", 99) < 4 and r.get("disp4_atr", 99) < -0.5]
mem.sort(key=lambda r: r["low_t"])

def is_win(r): return r["R_reclaim"] > 0

def maxstreak(rs):
    cur = mx = 0
    for r in rs:
        if not is_win(r): cur += 1; mx = max(mx, cur)
        else: cur = 0
    return mx

def stats(rs):
    n = len(rs); w = sum(is_win(r) for r in rs)
    return n, w, n-w, round(100*w/n,1) if n else 0, maxstreak(rs)

# ---- look-ahead check: does keep fn touch any outcome/future field?
KEEP_FIELDS = {"low_wick","sell_pol"}
OUTCOME = {"R_reclaim","R_8atr","near_M8","held8","runner","reclaim_idx"}
print("Filter fields:", KEEP_FIELDS, "| outcome overlap:", KEEP_FIELDS & OUTCOME)

def keep(r):
    return (r.get("low_wick") is not None and r["low_wick"] >= 0.155
            and r.get("sell_pol") is not None and r["sell_pol"] <= 0.5)

kept = [r for r in mem if keep(r)]
cut  = [r for r in mem if not keep(r)]

n0,w0,l0,wr0,ms0 = stats(mem)
n1,w1,l1,wr1,ms1 = stats(kept)
W0 = w0; L0 = l0
wkept = 100*w1/W0 if W0 else 0
lcut  = 100*(L0-l1)/L0 if L0 else 0

print(f"\nBEFORE: n={n0} W={w0} L={l0} WR={wr0}% maxstreak={ms0}")
print(f"AFTER : n={n1} W={w1} L={l1} WR={wr1}% maxstreak={ms1}")
print(f"winners_kept={w1}/{W0} ({wkept:.1f}%)  losers_cut={L0-l1}/{L0} ({lcut:.1f}%)")
print(f"winners_cut={W0-w1}  (winners removed by filter)")

# ---- per YEAR
print("\nPer YEAR (before -> after):")
yr_fail = []
for y in sorted(set(r["yr"] for r in mem)):
    mb=[r for r in mem if r["yr"]==y]; ma=[r for r in kept if r["yr"]==y]
    _,_,_,wrb,_ = stats(mb); _,_,_,wra,_ = stats(ma)
    flag = "WORSE" if (wra is not None and wrb is not None and wra < wrb) else ""
    print(f"  {y}: n {len(mb)}->{len(ma)}  WR {wrb}% -> {wra}%  {flag}")
    if wra is not None and wrb is not None and wra < wrb: yr_fail.append(y)

# ---- per BLOCK
print("\nPer BLOCK (before -> after):")
blk_fail=[]
for b in sorted(set(r["block"] for r in mem)):
    mb=[r for r in mem if r["block"]==b]; ma=[r for r in kept if r["block"]==b]
    _,_,_,wrb,_ = stats(mb); _,_,_,wra,_ = stats(ma)
    flag=""
    if ma and wra is not None and wrb is not None and wra < wrb:
        flag="WORSE"; blk_fail.append(b)
    print(f"  {b}: n {len(mb)}->{len(ma)}  WR {wrb}% -> {wra}%  {flag}")

# ---- threshold-neighborhood stability
print("\nThreshold neighborhood (low_wick thr, sell_pol<=0.5 fixed):")
for lw in [0.10,0.13,0.155,0.18,0.20]:
    k=[r for r in mem if r.get("low_wick") is not None and r["low_wick"]>=lw
       and r.get("sell_pol") is not None and r["sell_pol"]<=0.5]
    n,w,l,wr,ms=stats(k)
    print(f"  low_wick>={lw}: n={n} WR={wr}% streak={ms} wkept={100*w/W0:.1f}%")
print("sell_pol neighborhood (low_wick>=0.155 fixed):")
for sp in [0.3,0.4,0.5,0.6]:
    k=[r for r in mem if r.get("low_wick") is not None and r["low_wick"]>=0.155
       and r.get("sell_pol") is not None and r["sell_pol"]<=sp]
    n,w,l,wr,ms=stats(k)
    print(f"  sell_pol<={sp}: n={n} WR={wr}% streak={ms} wkept={100*w/W0:.1f}%")

print("\nSUMMARY years_worse:", yr_fail, "blocks_worse:", len(blk_fail))
