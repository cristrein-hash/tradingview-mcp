#!/usr/bin/env python3
"""
RECALIBRATED Devil's Advocate — REALISM/DEPLOYABILITY audit of the XAU 15M
LONG-only 8ATR-confirmation bottoms stack.

Stack (as given):
  entry = 8ATR-confirmation (close of bar where price first rises 8*ATR above fractal-low)
  SL = min low to that bar -0.1ATR ; let-run trailing ; R cap 20
  keep if R2 = NOT(h1_eff<0.20 AND h4_pos<1.02)  AND  not R_B-cut
  R_B cut = (absorption==1 & sell_decel==0)
            OR (buy_sell_ratio4>7 & low_vol_rel>1.37)
            OR (regime_age_h<=25.2 & sell_skew_mig>0)

The dataset only exposes some of these fields. r2_keep is precomputed.
We reconstruct the FINAL set = r2_keep==1 AND NOT R_B-cut (using available fields),
verify it lands on n=1999, then run realism tasks.
"""
import json, math
from collections import defaultdict

ROWS = [json.loads(l) for l in open('dataset_r2refine.jsonl')]
BAR_SEC = 900  # 15m

def rb_cut(d):
    # R_B features available in dataset: absorption, sell_decel, buy_sell_ratio4,
    # low_vol_rel, regime_age_h, sell_skew_mig
    c1 = (d.get('absorption')==1 and d.get('sell_decel')==0)
    c2 = (d.get('buy_sell_ratio4',0)>7 and d.get('low_vol_rel',0)>1.37)
    c3 = (d.get('regime_age_h',1e9)<=25.2 and d.get('sell_skew_mig',0)>0)
    return c1 or c2 or c3

final = [d for d in ROWS if d.get('r2_keep')==1 and not rb_cut(d)]
print(f"[reconstruct] total rows={len(ROWS)}  r2_keep==1={sum(1 for d in ROWS if d['r2_keep']==1)}  final(after R_B)={len(final)}")

# ---- baseline stats helper ----
def stats(trades):
    n=len(trades)
    if n==0: return {}
    Rs=[t['R'] for t in trades]
    wins=[r for r in Rs if r>0]
    losses=[r for r in Rs if r<=0]
    wr=len(wins)/n
    avgR=sum(Rs)/n
    sumR=sum(Rs)
    # equity curve / maxDD on Rs in time order
    Rs_t=[t['R'] for t in sorted(trades,key=lambda x:x['low_t'])]
    eq=0; peak=0; maxdd=0
    cur_streak=0; max_losing=0
    for r in Rs_t:
        eq+=r; peak=max(peak,eq); maxdd=min(maxdd,eq-peak)
        if r<=0: cur_streak+=1; max_losing=max(max_losing,cur_streak)
        else: cur_streak=0
    # freq/week
    ts=[t['low_t'] for t in trades]
    span_weeks=(max(ts)-min(ts))/ (7*86400)
    freq=n/span_weeks if span_weeks>0 else 0
    runners=sum(1 for r in Rs if r>=5)
    Rsort=sorted(Rs)
    def pct(p):
        i=min(len(Rsort)-1,int(p*len(Rsort)))
        return Rsort[i]
    return dict(n=n, wr=wr, avgR=avgR, sumR=sumR, maxDD=maxdd,
                max_losing_streak=max_losing, freq_wk=freq, runners=runners,
                median=pct(0.5), p90=pct(0.9), maxR=max(Rs),
                avg_win=(sum(wins)/len(wins) if wins else 0),
                avg_loss=(sum(losses)/len(losses) if losses else 0))

def show(label, s):
    if not s: print(f"{label}: EMPTY"); return
    print(f"{label}: n={s['n']} WR={s['wr']*100:.1f}% avgR={s['avgR']:+.3f} sumR={s['sumR']:+.1f} "
          f"maxDD={s['maxDD']:.1f}R streak={s['max_losing_streak']} freq={s['freq_wk']:.1f}/wk runners(>=5)={s['runners']}")

print("\n=== BASELINE (final stack, no dedup) ===")
base=stats(final)
show("FINAL", base)

# =====================================================================
# TASK 1 — FREQUENCY / OVERLAP / DEDUP
# =====================================================================
print("\n"+"="*70)
print("TASK 1 — FREQUENCY / OVERLAP / DEDUP")
print("="*70)

fin_sorted = sorted(final, key=lambda x:x['low_t'])
# overlap: entries within N bars of the previous KEPT entry, by entry time
# Note: low_t is the fractal-low time, not entry time. Use it as the time anchor.
def proximity_count(trades, nbars):
    ts=sorted(t['low_t'] for t in trades)
    near=0
    for i in range(1,len(ts)):
        if (ts[i]-ts[i-1]) <= nbars*BAR_SEC:
            near+=1
    return near

for nb in (8,16,32):
    print(f"  entries within {nb} bars of the prior entry: {proximity_count(final,nb)} "
          f"({proximity_count(final,nb)/len(final)*100:.1f}% of {len(final)})")

# clustering: how many distinct fractal-low anchors? duplicates share low_t cluster
lowt_counts=defaultdict(int)
for d in final: lowt_counts[d['low_t']]+=1
dup_lowt=sum(1 for v in lowt_counts.values() if v>1)
print(f"  distinct low_t values: {len(lowt_counts)} ; low_t values appearing >1x: {dup_lowt}")

def dedup_mingap(trades, nbars):
    ts=sorted(trades, key=lambda x:x['low_t'])
    out=[]; last=None
    for t in ts:
        if last is None or (t['low_t']-last) > nbars*BAR_SEC:
            out.append(t); last=t['low_t']
    return out

print("\n  --- DEDUP (min-gap, keep first) ---")
for nb in (8,16,32):
    dd=dedup_mingap(final, nb)
    show(f"  min-gap {nb}b", stats(dd))

# =====================================================================
# TASK 2 — ZERO RUNNERS / R-PROFILE
# =====================================================================
print("\n"+"="*70)
print("TASK 2 — R DISTRIBUTION / SCALP vs CONVEX")
print("="*70)
Rs=sorted(t['R'] for t in final)
import statistics as st
print(f"  n={len(Rs)}  min={Rs[0]:.2f}  median={st.median(Rs):.2f}  mean={sum(Rs)/len(Rs):+.3f}  max={Rs[-1]:.2f}")
for p in (0.5,0.75,0.9,0.95,0.99):
    i=min(len(Rs)-1,int(p*len(Rs))); print(f"  p{int(p*100)}={Rs[i]:.2f}")
wins=[r for r in Rs if r>0]; losses=[r for r in Rs if r<=0]
print(f"  avg_win={sum(wins)/len(wins):+.3f} (n={len(wins)})  avg_loss={sum(losses)/len(losses):+.3f} (n={len(losses)})")
print(f"  payoff ratio avg_win/|avg_loss| = {abs(sum(wins)/len(wins))/abs(sum(losses)/len(losses)):.3f}")
# R buckets
buckets=defaultdict(int)
for r in Rs:
    if r<=-0.5: buckets['<=-0.5 (full loss)']+=1
    elif r<=0: buckets['-0.5..0 (small loss/BE)']+=1
    elif r<1: buckets['0..1']+=1
    elif r<2: buckets['1..2']+=1
    elif r<5: buckets['2..5']+=1
    else: buckets['>=5']+=1
for k in ['<=-0.5 (full loss)','-0.5..0 (small loss/BE)','0..1','1..2','2..5','>=5']:
    print(f"  R {k}: {buckets[k]} ({buckets[k]/len(Rs)*100:.1f}%)")

# =====================================================================
# TASK 3 — DD REALISM
# =====================================================================
print("\n"+"="*70)
print("TASK 3 — DD REALISM")
print("="*70)
print(f"  maxDD={base['maxDD']:.1f}R = {abs(base['maxDD'])/base['avgR']:.0f} avgR-units ; "
      f"{abs(base['maxDD'])/base['sumR']*100:.1f}% of sumR ({base['sumR']:+.0f}R)")
print("  --- per-year ---")
for yr in sorted(set(d['yr'] for d in final)):
    yt=[d for d in final if d['yr']==yr]
    s=stats(yt)
    print(f"  {yr}: n={s['n']} sumR={s['sumR']:+.1f} maxDD={s['maxDD']:.1f}R WR={s['wr']*100:.1f}% avgR={s['avgR']:+.3f}")

# =====================================================================
# TASK 4 — SLIPPAGE / SPREAD COST SENSITIVITY
# =====================================================================
print("\n"+"="*70)
print("TASK 4 — SLIPPAGE / SPREAD SENSITIVITY")
print("="*70)
# R is in units of risk = (entry - SL) per trade. We don't have absolute entry/SL price
# in the dataset, so we model cost as a fraction of the average risk-distance.
# Approach: cost is fixed in $ (spread+slippage). R = pnl/risk_dist.
# We need risk_dist distribution. Reconstruct from primitives via SL = minlow-0.1ATR
# is not directly in dataset. Instead use the conservative analytic approach:
# additional cost per trade in R = cost_$ / risk_dist_$.
# We estimate typical risk_dist from primitives (atr at entry region) below.
# Load ATR samples to estimate typical risk distance.
import glob
atr_samples=[]
for f in glob.glob('primitives/*.primitives.json'):
    d=json.load(open(f))
    for b in d['series']:
        if b.get('atr'): atr_samples.append(b['atr'])
atr_med = st.median(atr_samples) if atr_samples else None
print(f"  ATR(15m) median over corpus = {atr_med:.3f} $  (n_atr={len(atr_samples)})")
# 8ATR confirmation entry: risk_dist = entry - (minlow-0.1ATR). Entry is >=8ATR above
# the fractal low at minimum (price rose 8ATR above low). But SL is min low, so
# risk_dist >= 8*ATR + 0.1*ATR ~ 8.1 ATR. THIS IS A KEY POINT: huge risk distance.
# Realistically risk_dist ~ (entry-low). Lower bound 8.1*ATR.
risk_lb = 8.1*atr_med
print(f"  Implied MIN risk distance (8.1*ATR) = {risk_lb:.2f} $ per trade (entry is 8ATR above low, SL at low)")
for spread,slip_ticks in [(0.13,1),(0.18,2),(0.30,2)]:
    slip=slip_ticks*0.01
    cost = spread + 2*slip   # spread once + slippage on entry & exit
    costR = cost/risk_lb
    newavg = base['avgR'] - costR
    print(f"  spread={spread} slip={slip_ticks}tick: cost=${cost:.3f} = {costR:.4f}R/trade -> avgR {base['avgR']:+.3f} -> {newavg:+.3f}  (sumR {base['sumR']*1:.0f} -> {(newavg*base['n']):+.0f})")
print("  NOTE: 8ATR risk distance is LARGE, so cost-in-R is small. But see Task-2: winners are")
print("        small in R BECAUSE risk distance is huge; absolute $ profit per trade is tiny vs the")
print("        capital tied to an 8ATR stop. Cost-in-R understates real friction if position sizing")
print("        is by fixed-R (the prop-firm way) -> recompute with realistic risk where SL is the")
print("        confirmation-bar structure, not 8ATR below.")

# =====================================================================
# TASK 5 — LOOK-AHEAD RECHECK
# =====================================================================
print("\n"+"="*70)
print("TASK 5 — LOOK-AHEAD RECHECK")
print("="*70)
print("  See narrative in final report. Checking field causality flags present in data...")
# Quick sanity: sell_decel has sentinel -1e7 (means 'undefined'); ensure R_B logic
# isn't accidentally tripping on sentinels.
sent=sum(1 for d in ROWS if d.get('sell_decel')==-10000000.0)
print(f"  rows with sell_decel sentinel(-1e7): {sent} (R_B c1 needs sell_decel==0, sentinel!=0 OK)")
