#!/usr/bin/env python3
"""DA part 2: block-join dedup integrity, leg_dir recency-condition adversarial probe,
NEUTRAL-swallowing (ema-lag mislabel), item-5 is_pullback distribution. Reproducible 2026-06-26."""
import json, bisect, csv, datetime as dt
from pathlib import Path
from collections import Counter
HERE=Path(__file__).parent; BUCKET=14400; K=2
PRIM=sorted((HERE/"primitives").glob("*.primitives.json"))

print("="*60); print("ITEM 7b — dedup conflict: do duplicate t have DIFFERENT OHLC across blocks?")
seen={}; conflicts=0; cross_block_dups=0
for p in PRIM:
    for b in json.load(open(p))["series"]:
        t=b["t"]
        if t in seen:
            cross_block_dups+=1
            o=seen[t]
            if (o["o"],o["h"],o["l"],o["c"])!=(b["o"],b["h"],b["l"],b["c"]): conflicts+=1
        else: seen[t]=b
# build_macro uses bars[b["t"]]=b -> LAST block wins for dup t. Check if that flips any 4H bucket.
print(f"  cross-block duplicate timestamps={cross_block_dups} OHLC_conflicts={conflicts}")
print(f"  (build_macro dedups via dict bars[t]=b → last-writer-wins; conflicts above = silent overwrite risk)")

print("="*60); print("ITEM 3b — leg_dir recency condition adversarial")
# The orig has: high sets last_t unconditionally; low sets only if last_t is None or i>=last_t.
# Adversarial: can a HIGH at index i_h then a LOW at SMALLER index never happen (loop is ascending) -
# so i is monotonic increasing. Therefore i>=last_t is ALWAYS true when low fires after any high.
# The ONLY asymmetry: a high ALWAYS overwrites (no condition). A low at SAME index i as a high:
# both is_high and is_low true at same i -> high sets last=-1,last_t=i; then low: i>=last_t(==i) True -> last=1 overwrites.
# So at a same-bar high+low tie, LOW wins. Probe frequency of same-index tie.
ties=0; checked=0
for p in PRIM:
    s=json.load(open(p))["series"]; H=[b["h"] for b in s]; L=[b["l"] for b in s]
    for i in range(K,len(s)-K):
        ih=H[i]==max(H[i-K:i+K+1]); il=L[i]==min(L[i-K:i+K+1])
        if ih and il: ties+=1
        checked+=1
print(f"  same-bar high&low pivot ties={ties}/{checked} (low wins these → arbitrary but rare)")
print(f"  loop ascending ⇒ i monotonic ⇒ 'i>=last_t' always True after first pivot ⇒ condition is a no-op")
print(f"  net effect: last pivot in time wins regardless of type — CORRECT recency (confirmed item3 0 mismatch)")

print("="*60); print("ITEM 4 — NEUTRAL swallowing: ema-lag mislabel of strong trends")
M=json.load(open(HERE/"macro_regime_4h.json"))["bars_4h"]
# how many 4H bars have swing_dir!=0 but macro=NEUTRAL purely because ema disagreed?
swing_but_neutral=sum(1 for b in M if b["swing_dir"]!=0 and b["macro"]=="NEUTRAL")
swing_pos_ema_neg=sum(1 for b in M if b["swing_dir"]>0 and b["ema_pos"]<0)
swing_neg_ema_pos=sum(1 for b in M if b["swing_dir"]<0 and b["ema_pos"]>0)
ema_pos_no_swing=sum(1 for b in M if b["swing_dir"]==0 and b["ema_pos"]>0)
print(f"  4H bars total={len(M)}")
print(f"  swing!=0 but NEUTRAL (ema vetoed)={swing_but_neutral} ({100*swing_but_neutral/len(M):.0f}%)")
print(f"    of which swing+ ema- (uptrend ema lag)={swing_pos_ema_neg}, swing- ema+ ={swing_neg_ema_pos}")
print(f"  swing==0 (no confirmed structure) with ema+ = {ema_pos_no_swing} (these are NEUTRAL despite ema bull)")
nz=sum(1 for b in M if b['swing_dir']==0)
print(f"  swing_dir==0 bars (insufficient pivots / no clean HH-HL or LH-LL)={nz} ({100*nz/len(M):.0f}%)")

print("="*60); print("ITEM 5/6 — is_pullback + selection counts")
rows=list(csv.DictReader(open(HERE/"candidates_annotated.csv")))
svm=Counter(r["setup_vs_macro"] for r in rows)
pb=[r for r in rows if r["is_pullback"]=="True"]
wm=[r for r in rows if r["setup_vs_macro"]=="with_macro"]
print(f"  total={len(rows)} svm={dict(svm)}")
print(f"  with_macro={len(wm)} is_pullback={len(pb)} ({100*len(pb)/max(len(wm),1):.0f}% of with_macro)")
# is_pullback by dir/leg sanity
for D in ("LONG","SHORT"):
    sub=[r for r in pb if r["dir"]==D]
    legs=Counter(r["leg_dir"] for r in sub)
    print(f"    pullback {D}: n={len(sub)} leg_dir dist={dict(legs)}")
# counter_macro that are actually mean-reversion-into-trend? just report
print(f"  counter_macro={svm['counter_macro']} neutral_macro={svm['neutral_macro']}")
