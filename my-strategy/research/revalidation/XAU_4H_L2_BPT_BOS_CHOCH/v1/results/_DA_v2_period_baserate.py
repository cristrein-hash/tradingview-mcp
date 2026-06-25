#!/usr/bin/env python3
"""DA part 3 — period base-rate context for the P1/P2 robustness claim.
The v2 staged result reports P1_rr 31.5 / P2_rr 35.3 as 'balanced, both above base'.
But the per-period BASE rates differ, so 'above base' must be judged per period, not vs the
pooled 26.1%. This script reports the correct per-period base and the per-period LIFT of S2.
verified-at: 2026-06-22"""
import csv, json
D="results"; RR="repro_recovery"
unc={int(r['bar_idx']):r for r in csv.DictReader(open(f"{D}/l2_bpt_uncapped_or_proxy_outcomes_276.csv"))}
eng={int(r['bar_idx']):r for r in csv.DictReader(open(f"{D}/l2_bpt_full276_macro_engine_confluence.csv"))}
xv2={int(r['bar_idx']):r for r in csv.DictReader(open(f"{D}/l2_bpt_full276_indicator_engine_cross_v2.csv"))}
pk={int(json.loads(l)['bar_idx']):json.loads(l) for l in open(f"{RR}/qual_packets.jsonl")}
def fn(v):
    try:return float(v)
    except:return None
EP=sorted(unc); MFE={b:fn(unc[b]['mfe_R']) for b in EP}
def vENGf(b):
    e=eng[b];v=0
    if e['capit']=='CLIMAX_RECLAIM':v+=1
    if e['momentum']=='LATE_TOP_EXHAUSTION':v-=1
    if e['supply'] in('CLEAN_SKY_BULLISH','MARKUP_BREAKING'):v+=1
    if e['supply'] in('SUPPLY_REJECTING_RISK','SUPPLY_BLOCKS_TARGET'):v-=1
    if e['macro_state'] in('NO_OVERHEAD_MARKUP','MACRO_BULL_RUN_CONTINUATION','RANGE_MACRO_BULL_RECLAIM','CAPITULATION_RECLAIM_VALID'):v+=1
    if e['macro_state'] in('BULL_PULLBACK_CONTINUATION','UNKNOWN_CONFLICT'):v-=1
    if e['fuel']=='high_fuel':v+=1
    return max(-1,min(1,v))
def vINDf(b):
    x=xv2.get(b,{});v=0
    if x.get('bubbles')=='BUBBLE_SELL_CLIMAX_BULL':v+=1
    if x.get('bubbles')=='BUBBLE_BUY_LATE':v-=1
    if x.get('smc')=='SMC_CHOCH_BULL_TRIGGER':v+=1
    if x.get('smc')=='SMC_CHOCH_TOP_REVERSAL':v-=1
    if x.get('nas')=='NAS_LONG_RECENT':v+=1
    if x.get('nas')=='NAS_SHORT_TOP':v-=1
    if x.get('indicator_confluence')=='STRONG_BEAR_CONFIRM':v+=1
    return max(-1,min(1,v))
def per(b): return 'P1' if pk[b]['datetime'][:10]<'2023-01-01' else 'P2'
def rate(s):
    r=sum(1 for b in s if MFE[b]>=5); n=len(s); return n,r,(100*r/n if n else 0)
for P in('P1','P2'):
    allp=[b for b in EP if per(b)==P]
    take=[b for b in allp if (vENGf(b)+vINDf(b))>=1]
    bn,br,brr=rate(allp); tn,tr,trr=rate(take)
    print(f"{P}: base n={bn} rr={brr:.1f}%  | S2_TAKE n={tn} rr={trr:.1f}%  per-period lift={trr/brr if brr else 0:.2f}")
print("DONE part3")
