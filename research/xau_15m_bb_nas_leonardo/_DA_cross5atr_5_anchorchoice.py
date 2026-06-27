#!/usr/bin/env python3
"""DA POINT 5 — ANCHOR CHOICE. Matching uses low_t (fractal low) within ±3 bars by TIME.
Alternatives: (a) match by PRICE proximity too (the M8 BOT price ~= entry sl/low),
(b) ask the inverse — what fraction of the 205 M8 BOTs ever become a 5ATR anchor at all?
If most reversals never trigger a 5ATR entry, the entry logic ignores reversals -> the
cross is structurally weak regardless of window. Also test price+time joint match."""
import csv, bisect
from pathlib import Path
from filter_harness import ROWS, dedup
HERE=Path(__file__).parent; BAR=900
REV=[{**r,"t":int(r["t"]),"price":float(r["price"]),"atr":float(r["atr"])} for r in csv.DictReader(open(HERE/"reversal_power.csv"))]
BOTS=[r for r in REV if r["kind"]=="BOT"]
base=dedup(ROWS)
low_ts=sorted(r["low_t"] for r in base)
# fraction of BOTs that have a 5ATR anchor within W bars
def anchored(bot,W):
    lo,hi=bot["t"]-W*BAR,bot["t"]+W*BAR
    k=bisect.bisect_left(low_ts,lo)
    return k<len(low_ts) and low_ts[k]<=hi
for W in (3,6,12,24,48):
    c=sum(1 for b in BOTS if anchored(b,W))
    print(f"M8 BOTs with a 5ATR anchor within ±{W} bars: {c}/{len(BOTS)} ({100*c/len(BOTS):.0f}%)")
# joint price+time match for entries (does requiring price-near tighten or loosen?)
REVt=sorted(REV,key=lambda r:r["t"]); RT=[r["t"] for r in REVt]
def nearest_bot_priceaware(r,W,pf=0.5):
    # search BOTs within W bars; accept if |entry - bot.price| <= pf*bot.atr*... use entry price
    k=bisect.bisect_left(RT,r["low_t"]); best=None
    for j in range(max(0,k-6),min(len(REVt),k+6)):
        rv=REVt[j]
        if rv["kind"]!="BOT": continue
        dt=abs(rv["t"]-r["low_t"])
        if dt>W*BAR: continue
        dp=abs(r["entry"]-rv["price"])/max(rv["atr"],1e-9)
        if best is None or dt<best[0]: best=(dt,dp,rv)
    return best
W=3
both=0; time_only=0
for r in base:
    m=nearest_bot_priceaware(r,W)
    if m:
        time_only+=1
        if m[1]<=2.0: both+=1   # within 2 ATR in price
print(f"\nentries time-matched to a BOT (±{W}b): {time_only}/{len(base)}; also price-within-2ATR: {both}/{len(base)}")
print("If price+time barely changes the matched count, time-match wasn't the limiter — entries just")
print("aren't AT reversals. If most BOTs never anchor a 5ATR entry, the strategy doesn't trade reversals.")
