#!/usr/bin/env python3
"""DA part 2 — is the 'skip_winners_recovered=19' metric circular, and do those 19 depend on
the in-sample signs? skip_winner = a runner (mfe>=5) that the ENGINE POLICY skipped/reviewed but
the new vote TAKEs. The new vote partly USES engine STATES, while the comparison is vs engine POLICY.
We quantify: (a) of the 139 FULL-S2 TAKE, how the eng policy splits; (b) of the 19 recovered, how many
survive when the two in-sample signs are removed; (c) how many recovered runners have eng policy TAKE
already (i.e. not actually 'missed by the engine').
verified-at: 2026-06-22"""
import csv, json
D="results"; RR="repro_recovery"
unc={int(r['bar_idx']):r for r in csv.DictReader(open(f"{D}/l2_bpt_uncapped_or_proxy_outcomes_276.csv"))}
eng={int(r['bar_idx']):r for r in csv.DictReader(open(f"{D}/l2_bpt_full276_macro_engine_confluence.csv"))}
xv2={int(r['bar_idx']):r for r in csv.DictReader(open(f"{D}/l2_bpt_full276_indicator_engine_cross_v2.csv"))}
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
def vENGs(b):
    e=eng[b];v=0
    if e['capit']=='CLIMAX_RECLAIM':v+=1
    if e['momentum']=='LATE_TOP_EXHAUSTION':v-=1
    if e['supply'] in('CLEAN_SKY_BULLISH','MARKUP_BREAKING'):v+=1
    if e['supply'] in('SUPPLY_REJECTING_RISK','SUPPLY_BLOCKS_TARGET'):v-=1
    if e['macro_state'] in('NO_OVERHEAD_MARKUP','MACRO_BULL_RUN_CONTINUATION','RANGE_MACRO_BULL_RECLAIM','CAPITULATION_RECLAIM_VALID'):v+=1
    if e['macro_state']=='UNKNOWN_CONFLICT':v-=1
    if e['fuel']=='high_fuel':v+=1
    return max(-1,min(1,v))
def vINDs(b):
    x=xv2.get(b,{});v=0
    if x.get('bubbles')=='BUBBLE_SELL_CLIMAX_BULL':v+=1
    if x.get('bubbles')=='BUBBLE_BUY_LATE':v-=1
    if x.get('smc')=='SMC_CHOCH_BULL_TRIGGER':v+=1
    if x.get('smc')=='SMC_CHOCH_TOP_REVERSAL':v-=1
    if x.get('nas')=='NAS_LONG_RECENT':v+=1
    if x.get('nas')=='NAS_SHORT_TOP':v-=1
    return max(-1,min(1,v))
def take(b,srcs,thr=1): return sum(f(b) for f in srcs)>=thr

TAKE_full=[b for b in EP if take(b,[vENGf,vINDf])]
TAKE_str =[b for b in EP if take(b,[vENGs,vINDs])]
from collections import Counter
print("=== eng policy split of the 139 FULL-S2 TAKE ===")
print(Counter(eng[b]['policy'] for b in TAKE_full))
ENG_TAKE={b for b in EP if eng[b]['policy']=='TAKE'}
print(f"  of {len(TAKE_full)} TAKE, eng-policy=TAKE already: {len(set(TAKE_full)&ENG_TAKE)}  (overlap, NOT recovered)")

# recovered skip-winners = runner & eng policy in SKIP/REVIEW/REVIEW_RISK & new TAKE
recov_full=[b for b in EP if MFE[b]>=5 and eng[b]['policy'] in('SKIP','REVIEW','REVIEW_RISK') and b in set(TAKE_full)]
recov_str =[b for b in EP if MFE[b]>=5 and eng[b]['policy'] in('SKIP','REVIEW','REVIEW_RISK') and b in set(TAKE_str)]
print(f"\nrecovered skip-winners FULL = {len(recov_full)} ; STRUCT-only = {len(recov_str)}")
print(f"  survive removal of in-sample signs: {len(set(recov_full)&set(recov_str))} of {len(recov_full)}")
print(f"  lost when in-sample signs removed: {sorted(set(recov_full)-set(recov_str))}")

# how many recovered owe their TAKE to STRONG_BEAR_CONFIRM specifically (B sign)?
owe_bear=[b for b in recov_full if xv2.get(b,{}).get('indicator_confluence')=='STRONG_BEAR_CONFIRM' and not take(b,[vENGf,vINDs])]
print(f"\nrecovered runners whose TAKE flips OFF without STRONG_BEAR_CONFIRM=+1: {len(owe_bear)} -> {owe_bear}")
print("\n(circularity note) new vote reads engine STATES; comparison is vs engine POLICY -> a recovery")
print(" is 'fair' only insofar as state->policy is non-trivial. eng policy of recovered set:")
print(" ", Counter(eng[b]['policy'] for b in recov_full))
print("DONE part2")
