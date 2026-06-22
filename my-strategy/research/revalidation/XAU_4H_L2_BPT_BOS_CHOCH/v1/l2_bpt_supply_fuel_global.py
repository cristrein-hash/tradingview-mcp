#!/usr/bin/env python3
"""L2/BPT — testar o predicado GLOBAL supply_reject + fuel_low (o que marca 100% dos losers bem-cortados no bear_leg)
no FULL 276 como LOSER-cut (DA pivot: predicado global validado, não carve-out bear-leg). DIAGNÓSTICO. uncapped."""
import csv
D="results"
unc={int(r['bar_idx']):r for r in csv.DictReader(open(f"{D}/l2_bpt_uncapped_or_proxy_outcomes_276.csv"))}
eng={int(r['bar_idx']):r for r in csv.DictReader(open(f"{D}/l2_bpt_full276_macro_engine_confluence.csv"))}
dec={int(r['bar_idx']):r for r in csv.DictReader(open(f"{D}/l2_bpt_full276_macro_bear_v3_decisions.csv"))}
def fn(v):
    try:return float(v)
    except:return None
EP=sorted(unc); MFE={b:fn(unc[b]['mfe_R']) for b in EP}
nR=sum(1 for b in EP if MFE[b]>=5); nL=sum(1 for b in EP if MFE[b]<2)
base_r=nR/len(EP); base_l=nL/len(EP)
def sup_reject(b): return dec.get(b,{}).get('sup_cat') in('SUPPLY_NEAR_AND_REJECTING','SUPPLY_FRESH_DANGEROUS','SUPPLY_BLOCKS_TARGET')
def fuel_low(b): return eng[b].get('fuel')=='low_fuel'
print(f"FULL 276: runners={nR} ({100*base_r:.0f}%) losers={nL} ({100*base_l:.0f}%)\n")
for name,pred in [('sup_reject',sup_reject),('fuel_low',fuel_low),('sup_reject AND fuel_low',lambda b:sup_reject(b) and fuel_low(b)),('sup_reject OR fuel_low',lambda b:sup_reject(b) or fuel_low(b))]:
    g=[b for b in EP if pred(b)]; n=len(g)
    if not n: print(f"{name}: n=0"); continue
    run=sum(1 for b in g if MFE[b]>=5); los=sum(1 for b in g if MFE[b]<2)
    print(f"{name:26} n={n:>3} | runner_rate={100*run/n:>4.0f}% (lift {(run/n)/base_r:.2f}) | loser_rate={100*los/n:>4.0f}% (lift {(los/n)/base_l:.2f}) | {los} losers, {run} runners no grupo")
blk=[b for b in EP if sup_reject(b) and fuel_low(b)]
rc=sum(1 for b in blk if MFE[b]>=5); lc=sum(1 for b in blk if MFE[b]<2)
print(f"\nBLOQUEAR sup_reject AND fuel_low (276): corta {lc}/{nL} losers ({100*lc/nL:.0f}%) e {rc}/{nR} runners ({100*rc/nR:.0f}%)")
print(f"  loser/runner cut lift = ({lc}/{nL})/({rc}/{nR}) = {((lc/nL)/(rc/nR)) if rc else 999:.2f}  (baseline bear_leg 1.63)")
print("DONE.")
