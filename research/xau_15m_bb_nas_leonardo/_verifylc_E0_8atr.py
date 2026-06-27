#!/usr/bin/env python3
import json
PATH="/Users/cristrein/tradingview-mcp/research/xau_15m_bb_nas_leonardo/entry_dataset.jsonl"
rows=[]
with open(PATH) as f:
    for line in f:
        line=line.strip()
        if not line: continue
        d=json.loads(line)
        if d.get("R_8atr") is not None:
            rows.append(d)
rows.sort(key=lambda r:r["low_t"])
def win(r): return r["R_8atr"]>0
def loss(r): return r["R_8atr"]<=0
def streak(seq):
    best=cur=0
    for r in seq:
        if loss(r): cur+=1; best=max(best,cur)
        else: cur=0
    return best
def stats(seq):
    n=len(seq); w=sum(1 for r in seq if win(r))
    return n,w,n-w,(round(100*w/n,1) if n else 0),streak(seq)

N0,W0,L0,WR0,ST0=stats(rows)
print("BEFORE n=%d W=%d L=%d WR=%.1f streak=%d"%(N0,W0,L0,WR0,ST0))

# claimed filter
TH=0.637
keep=[r for r in rows if r.get("atr_regime") is not None and r["atr_regime"]>=TH]
n,w,l,wr,stk=stats(keep)
wk=round(100*w/W0,1); lc=round(100*(L0-l)/L0,1)
print("AFTER(atr_regime>=%.3f) n=%d W=%d L=%d WR=%.1f streak=%d"%(TH,n,w,l,wr,stk))
print("winners_kept_pct=%.1f losers_cut_pct=%.1f"%(wk,lc))

# by year
print("\n--- WR by year (before vs after) ---")
for y in (2024,2025,2026):
    b=[r for r in rows if r["yr"]==y]
    a=[r for r in keep if r["yr"]==y]
    nb,wb,lb,wrb,_=stats(b); na,wa,la,wra,_=stats(a)
    print("  y%d before WR=%.1f (n=%d) -> after WR=%.1f (n=%d)  delta=%+.1f"%(y,wrb,nb,wra,na,wra-wrb))

# by block
print("\n--- WR by block (before vs after) ---")
blocks=sorted(set(r["block"] for r in rows))
for bl in blocks:
    b=[r for r in rows if r["block"]==bl]
    a=[r for r in keep if r["block"]==bl]
    nb,wb,lb,wrb,_=stats(b); na,wa,la,wra,_=stats(a)
    print("  %s before WR=%.1f (n=%d) -> after WR=%.1f (n=%d)  delta=%+.1f"%(bl,wrb,nb,wra,na,(wra-wrb)))

# neighborhood robustness around threshold
print("\n--- threshold neighborhood ---")
for t in [0.55,0.60,0.62,0.637,0.65,0.70,0.75]:
    k=[r for r in rows if r.get("atr_regime") is not None and r["atr_regime"]>=t]
    n2,w2,l2,wr2,stk2=stats(k)
    wk2=round(100*w2/W0,1); lc2=round(100*(L0-l2)/L0,1)
    print("  >=%.3f n=%d WR=%.1f keepW=%.1f cutL=%.1f streak=%d"%(t,n2,wr2,wk2,lc2,stk2))
