#!/usr/bin/env python3
"""DA audit of FINAL macro-regime layer: h1_eff>=0.15 AND macro_bear==0 on top of h1_eff>=0.15.
Reproduces harness numbers via filter_harness.run, decomposes the +4.9 sumR gain into
(BEAR removal) vs (new_trades surfaced by re-dedup), regime split of the 211, Wilson CI on
the BEAR block, by-year/by-block stability, and overfit/selection robustness (only-BULL,
h1_trend, h4_trend alternatives). Single source of truth = filter_harness. 2026-06-27."""
import math
from collections import defaultdict
import filter_harness as H

def regime(r):
    if r['macro_bear'] == 1: return 'BEAR'
    if r['macro_bull'] == 1: return 'BULL'
    return 'NEUTRAL'

def wilson(k, n, z=1.96):
    if n == 0: return (0.0, 0.0)
    p = k / n
    d = 1 + z*z/n
    c = (p + z*z/(2*n)) / d
    hw = z*math.sqrt(p*(1-p)/n + z*z/(4*n*n)) / d
    return (100*(c-hw), 100*(c+hw))

KEEP_211  = lambda r: r['h1_eff'] >= 0.15
KEEP_CAND = lambda r: r['h1_eff'] >= 0.15 and r['macro_bear'] == 0

def main():
    s211, t211 = H.run(KEEP_211)
    scand, tcand = H.run(KEEP_CAND)

    print("=== Regime split of the 211 (h1_eff taken) ===")
    g = defaultdict(lambda: [0, 0, 0.0])
    for c in t211:
        rg = regime(c); g[rg][0]+=1; g[rg][1]+=c['win']; g[rg][2]+=c['R']
    for rg, (n, w, sm) in sorted(g.items()):
        lo, hi = wilson(w, n)
        print(f"  {rg:8} n={n:3} WR={100*w/n:.1f} sumR={sm:+.1f} avgR={sm/n:+.3f} Wilson95=[{lo:.1f},{hi:.1f}]")

    # decomposition
    ids211 = {(c['block'], c['low_t']): c for c in t211}
    idscand = {(c['block'], c['low_t']): c for c in tcand}
    new_in_cand = [c for c in tcand if (c['block'], c['low_t']) not in ids211]
    lost = [c for c in t211 if (c['block'], c['low_t']) not in idscand]
    drop_bear = [c for c in lost if regime(c) == 'BEAR']
    drop_nonbear = [c for c in lost if regime(c) != 'BEAR']
    print("\n=== Decomposition of +4.9 sumR (211 -> cand) ===")
    print(f"  BEAR removed:        n={len(drop_bear)} sumR={sum(c['R'] for c in drop_bear):+.2f}")
    print(f"  non-BEAR collateral: n={len(drop_nonbear)} sumR={sum(c['R'] for c in drop_nonbear):+.2f} (reshuffle casualties)")
    print(f"  NEW trades surfaced: n={len(new_in_cand)} sumR={sum(c['R'] for c in new_in_cand):+.2f} wins={sum(c['win'] for c in new_in_cand)}")
    net = sum(c['R'] for c in new_in_cand) - sum(c['R'] for c in lost)
    print(f"  NET = new({sum(c['R'] for c in new_in_cand):+.2f}) - dropped({sum(c['R'] for c in lost):+.2f}) = {net:+.2f}  (vs harness delta {scand['sumr']-s211['sumr']:+.2f})")
    print(f"  => removing BEAR only nets {-sum(c['R'] for c in lost):+.2f}R; the NEW trades from re-dedup contribute {sum(c['R'] for c in new_in_cand):+.2f}R")

    # Wilson on BEAR block
    lo, hi = wilson(18, 36)
    print(f"\n=== BEAR block power: n=36 WR=50.0 sumR=-2.3 ===")
    print(f"  Wilson95 WR=[{lo:.1f},{hi:.1f}] -> straddles 50%; avgR=-0.064 (near breakeven, within noise)")

    # stability: by year / by block
    print("\n=== by_year / by_block (cand vs 211) ===")
    yr211, blk211 = H.by_splits(t211)
    yrc, blkc = H.by_splits(tcand)
    print("  YEAR    211(n,WR)        cand(n,WR)")
    for y in sorted(set(yr211)|set(yrc)):
        print(f"    {y}  {yr211.get(y)}   {yrc.get(y)}")
    print("  BLOCK         211(n,WR)        cand(n,WR)")
    for b in sorted(set(blk211)|set(blkc)):
        print(f"    {b}  {blk211.get(b)}   {blkc.get(b)}")

    # overfit / selection robustness
    print("\n=== Selection / robustness alternatives (on top of h1_eff>=0.15) ===")
    variants = {
        "macro_bear==0 (keep BULL+NEU)": lambda r: r['h1_eff']>=0.15 and r['macro_bear']==0,
        "only BULL (macro_bull==1)":     lambda r: r['h1_eff']>=0.15 and r['macro_bull']==1,
        "h1_trend>=0 (drop h1 bear)":    lambda r: r['h1_eff']>=0.15 and (r.get('h1_trend') is not None and r['h1_trend']>=0),
        "h4_trend>=0 (drop h4 bear)":    lambda r: r['h1_eff']>=0.15 and (r.get('h4_trend') is not None and r['h4_trend']>=0),
        "macro_bull OR macro NEU":       lambda r: r['h1_eff']>=0.15 and r['macro_bear']==0,
    }
    for name, fn in variants.items():
        s, t = H.run(fn)
        print(f"  {name:32} N={s['n']:3} WR={s['wr']:.1f} sumR={s['sumr']:+.1f} DD={s['dd']:.1f} streak={s['streak']} winLost={s['winners_lost']} bigLost={s['big_winners_lost']}")

    # BEAR block win/loss balance + standalone macro effect
    bear = [c for c in t211 if regime(c) == 'BEAR']
    print("\n=== BEAR block win/loss balance (the thing being cut) ===")
    print(f"  n={len(bear)} wins={sum(c['win'] for c in bear)} losers={sum(1-c['win'] for c in bear)} sumR={sum(c['R'] for c in bear):+.2f}")
    print(f"  BEAR winners sumR={sum(c['R'] for c in bear if c['win']):+.2f} | BEAR losers sumR={sum(c['R'] for c in bear if not c['win']):+.2f}")
    print("  => cutting BEAR discards 18 winners (+15.7R) to avoid 18 losers (-18.0R): near wash, NOT a clean danger block.")
    sa, _ = H.run(lambda r: r['macro_bear'] == 0)
    print(f"\n=== macro_bear==0 ALONE on base 267 (no h1_eff) ===")
    print(f"  N={sa['n']} WR={sa['wr']} sumR={sa['sumr']:+.1f} DD={sa['dd']} dSumR={sa['dSumR']:+.1f} big_winners_lost={sa['big_winners_lost']}")

if __name__ == "__main__":
    main()
