#!/usr/bin/env python3
"""Independent verification of loser-cut filter for E4_bullbos.
Target = macro_bull==1 AND smc_bos==1. Filter = keep buy_L==0 (cut buy_L>=1).
winner = R_reclaim>0.
"""
import json
from collections import defaultdict

ROWS=[json.loads(l) for l in open('/Users/cristrein/tradingview-mcp/research/xau_15m_bb_nas_leonardo/entry_dataset.jsonl')]
MEM=[r for r in ROWS if r.get('macro_bull')==1 and r.get('smc_bos')==1]
MEM.sort(key=lambda r:r['low_t'])

def win(r): return r['R_reclaim']>0
def maxstreak(rows):
    best=cur=0
    for r in rows:
        if not win(r): cur+=1; best=max(best,cur)
        else: cur=0
    return best
def stats(rows):
    n=len(rows); w=sum(win(r) for r in rows)
    return n,w,n-w,round(w/n*100,2) if n else 0,maxstreak(rows)

n0,w0,l0,wr0,ms0=stats(MEM)
print(f"BEFORE: n={n0} W={w0} L={l0} WR={wr0}% maxstreak={ms0}")

# Filter: keep buy_L==0
kept=[r for r in MEM if r.get('buy_L')==0]
cut=[r for r in MEM if r.get('buy_L')!=0]  # buy_L>=1 (count)
n1,w1,l1,wr1,ms1=stats(kept)
print(f"AFTER (keep buy_L==0): n={n1} W={w1} L={l1} WR={wr1}% maxstreak={ms1}")
print(f"winners_kept_pct={round(w1/w0*100,2)}%  losers_cut_pct={round((l0-l1)/l0*100,2)}%")

cw=sum(win(r) for r in cut)
print(f"CUT group (buy_L>=1): n={len(cut)} W={cw} L={len(cut)-cw} WR={round(cw/len(cut)*100,1)}%")

# Check buy_L value distribution (count vs flag)
vals=defaultdict(int)
for r in MEM: vals[r.get('buy_L')]+=1
print("buy_L value distribution:", dict(sorted(vals.items(), key=lambda x:(x[0] is None, x[0]))))

# WR-after by YEAR (kept group)
print("\n--- WR-after (kept) by year ---")
for y in (2024,2025,2026):
    yk=[r for r in kept if r['yr']==y]
    if yk:
        ywr=sum(win(r) for r in yk)/len(yk)*100
        print(f"  KEPT y{y}: n={len(yk)} WR={ywr:.1f}%")
# WR-before by year for comparison + cut group by year
print("\n--- per-year: BEFORE vs AFTER + cut group ---")
for y in (2024,2025,2026):
    yb=[r for r in MEM if r['yr']==y]
    yk=[r for r in kept if r['yr']==y]
    yc=[r for r in cut if r['yr']==y]
    bwr=sum(win(r) for r in yb)/len(yb)*100 if yb else 0
    awr=sum(win(r) for r in yk)/len(yk)*100 if yk else 0
    cwr=sum(win(r) for r in yc)/len(yc)*100 if yc else 0
    delta=awr-bwr
    print(f"  y{y}: before n={len(yb)} WR={bwr:.1f}% | after n={len(yk)} WR={awr:.1f}% (Δ{delta:+.1f}) | cut n={len(yc)} WR={cwr:.1f}%")

# WR-after by BLOCK (kept group)
print("\n--- per-block: before vs after ---")
blocks=sorted(set(r['block'] for r in MEM))
worse_blocks=0
for b in blocks:
    bb=[r for r in MEM if r['block']==b]
    bk=[r for r in kept if r['block']==b]
    if not bb: continue
    bwr=sum(win(r) for r in bb)/len(bb)*100
    awr=sum(win(r) for r in bk)/len(bk)*100 if bk else 0
    flag=""
    if bk and awr<bwr-0.01:
        flag=" <-- WORSE"; worse_blocks+=1
    print(f"  {b}: before n={len(bb)} WR={bwr:.1f}% | after n={len(bk)} WR={awr:.1f}%{flag}")
print(f"blocks where filter makes WR worse: {worse_blocks}/{len(blocks)}")

# Threshold neighborhood: buy_L is a count. Compare keep buy_L==0 vs keep buy_L<=1 etc.
print("\n--- neighborhood (does cherry-pick collapse?) ---")
for thr in (0,1,2):
    k=[r for r in MEM if r.get('buy_L')<=thr]
    n,w,l,wr,ms=stats(k)
    print(f"  keep buy_L<={thr}: n={n} WR={wr}% kept_w%={round(w/w0*100,1)} cut_l%={round((l0-l)/l0*100,1)} ms={ms}")

# Look-ahead check: is buy_L derived from outcome? buy_L is bubble count at reclaim bar.
print("\n--- look-ahead sanity ---")
print("buy_L = count of LARGE buy bubbles at reclaim bar (pre-entry indicator, not outcome-derived)")
