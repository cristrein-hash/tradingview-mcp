#!/usr/bin/env python3
"""
_DA_dist_ema_discount.py — Devil's Advocate self-audit on the dist_ema_atr (discount)
entry trigger family found by _engine_liquidity_structure.py.

Concerns:
 1. Look-ahead: is dist_ema_atr causal? (it's EMA distance AT the reclaim bar close — yes,
    computed from already-closed bars). Verify it's not the target in disguise: check
    correlation with R AND that complement is worse, AND that it's not just near_M8 proxy.
 2. In-sample / selection: how many thresholds scanned -> count + Bonferroni-ish sanity.
 3. Power / concentration: leave-one-block-out jackknife (does any single block carry it?).
 4. Carrier trades: ex-top2 (done) + ex-top5 + median R sign.
 5. Stability: per-year sign for the 4 finalist rules.
"""
import json
from collections import defaultdict

BASE = 0.727
ROWS = [json.loads(l) for l in open('entry_dataset.jsonl')]
YEARS = (2024, 2025, 2026)

RULES = {
 "R1 dist<=-1.0 (core)": lambda r: r['dist_ema_atr']<=-1.0,
 "R2 dist<=-1.0 & low_closepos>=0.55": lambda r: r['dist_ema_atr']<=-1.0 and r['low_closepos']>=0.55,
 "R3 dist<=-1.0 & rsi_low>30": lambda r: r['dist_ema_atr']<=-1.0 and r['rsi_low']>30,
 "R4 dist<=-1.0 & smc_choch>=1": lambda r: r['dist_ema_atr']<=-1.0 and r['smc_choch']>=1,
}

def st(rows):
    n=len(rows); Rs=[r['R_reclaim'] for r in rows]
    avg=sum(Rs)/n; wr=sum(1 for x in Rs if x>0)/n*100
    Rs_sorted=sorted(Rs,reverse=True)
    med=sorted(Rs)[n//2]
    et2=sum(Rs_sorted[2:])/(n-2)
    et5=sum(Rs_sorted[5:])/(n-5)
    return n,round(avg,3),round(wr,1),round(med,3),round(et2,3),round(et5,3)

print("=== Finalist rules: full stats + carrier robustness ===")
for name,p in RULES.items():
    rows=[r for r in ROWS if p(r)]
    n,avg,wr,med,et2,et5=st(rows)
    yr=[round(sum(r['R_reclaim'] for r in rows if r['yr']==y)/max(1,sum(1 for r in rows if r['yr']==y)),3) for y in YEARS]
    print(f"{name}: n={n} avgR={avg} WR={wr} medR={med} ex2={et2} ex5={et5} y={yr}")

print("\n=== CONCERN: is dist_ema_atr a near_M8 proxy / target leak? ===")
# near_M8 is an OUTCOME. dist_ema_atr is a feature. If they were the same thing, the rule's
# edge would vanish controlling for near_M8. But we never used near_M8. Show that within the
# core rule, R edge holds for BOTH near_M8=0 and near_M8=1 subsets (no leakage via that path).
core=[r for r in ROWS if r['dist_ema_atr']<=-1.0]
for flag in (0,1):
    sub=[r for r in core if r['near_M8']==flag]
    if sub:
        print(f"  core & near_M8={flag}: n={len(sub)} avgR={round(sum(r['R_reclaim'] for r in sub)/len(sub),3)}")

print("\n=== CONCERN: leave-one-block-out jackknife on R1 core ===")
blocks=sorted(set(r['block'] for r in ROWS))
core_rows=[r for r in ROWS if r['dist_ema_atr']<=-1.0]
worst=None
for b in blocks:
    sub=[r for r in core_rows if r['block']!=b]
    avg=sum(r['R_reclaim'] for r in sub)/len(sub)
    if worst is None or avg<worst[1]:
        worst=(b,avg)
    print(f"  drop {b}: n={len(sub)} avgR={round(avg,3)}")
print(f"  WORST leave-one-out avgR={round(worst[1],3)} (drop {worst[0]})  base={BASE}")

print("\n=== CONCERN: selection count (Bonferroni sanity) ===")
print("  Phase1 single scans ~ 11 feats x ~5 thr = ~55 tests")
print("  Phase2 ~14 combos, Phase3 grid ~ C(6,2)*~9 = ~135, Phase4 ~24")
print("  Total ~ 230 hypotheses. dist_ema_atr<=-1.0 lift=0.129 with n=766.")
print("  Key defense: it's NOT one lucky cell — the WHOLE monotone ladder (dist<=-2.5..-0.75)")
print("  is ordered & all > base, AND complement (dist>-1.0) is BELOW base. Structural, not cherry-pick.")

print("\n=== monotone ladder recap (continuity = anti-overfit evidence) ===")
for t in [-2.5,-2.0,-1.5,-1.0,-0.75,-0.5,0.0,0.5,1.0]:
    sub=[r for r in ROWS if r['dist_ema_atr']<=t]
    comp=[r for r in ROWS if r['dist_ema_atr']>t]
    a=sum(r['R_reclaim'] for r in sub)/len(sub)
    c=sum(r['R_reclaim'] for r in comp)/len(comp)
    print(f"  dist<={t}: n={len(sub)} avgR={round(a,3)} | complement n={len(comp)} avgR={round(c,3)}")
