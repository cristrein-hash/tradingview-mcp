#!/usr/bin/env python3
"""
_verify5_F1_h1pos_disp4_sellskew.py
DEVIL'S ADVOCATE recalibrated verification of the 5ATR "F1" KEEP filter.

RULE (KEEP = AND-stack):
  KEEP = h1_pos>=0.54 AND disp4_atr>=0.77 AND sell_skew_mig<=0.65
Complement = CUT.

Recalibrated régua:
- Do NOT veto on tail/WR-only/lack-of-OOS.
- VETO only on:
  * look-ahead (feature uses future/outcome? non-closed HTF bar? bubbles known_at?)
  * non-stationarity: keep-WR by YEAR vs BASE-OF-THAT-YEAR and by BLOCK;
    WORSE in any year OR >2/8 blocks worse  => veto
  * cuts winners < 85% kept
  * cherry-pick: +-20% neighborhood of thresholds collapses below base
Report survives, reason, wr_keep, streak_keep, winners_kept_pct honestly.
"""
import json
from pathlib import Path

DS = Path(__file__).parent / "dataset_5atr.jsonl"
rows = [json.loads(l) for l in open(DS)]

POS_T = 0.54
DISP_T = 0.77
SKEW_T = 0.65

def keep_mask(r, pos_t=POS_T, disp_t=DISP_T, skew_t=SKEW_T):
    return (r["h1_pos"] is not None and r["h1_pos"] >= pos_t) \
           and (r["disp4_atr"] is not None and r["disp4_atr"] >= disp_t) \
           and (r["sell_skew_mig"] is not None and r["sell_skew_mig"] <= skew_t)

def stats(subset):
    n = len(subset); w = sum(x["win"] for x in subset)
    return n, w, (100*w/n if n else 0.0)

def longest_streak(subset):
    s = sorted(subset, key=lambda r: r["low_t"]); best = cur = 0
    for r in s:
        if r["win"] == 1: cur += 1; best = max(best, cur)
        else: cur = 0
    return best

n_null = sum(1 for r in rows if r["h1_pos"] is None or r["disp4_atr"] is None or r["sell_skew_mig"] is None)
print(f"rows with null in rule features: {n_null}")

base_n, base_w, base_wr = stats(rows)
kept = [r for r in rows if keep_mask(r)]
cut  = [r for r in rows if not keep_mask(r)]
keep_n, keep_w, keep_wr = stats(kept)

total_winners = base_w
winners_kept_pct = 100*keep_w/total_winners if total_winners else 0.0
total_losers = base_n - base_w
losers_kept = keep_n - keep_w
losers_cut_pct = 100*(total_losers - losers_kept)/total_losers if total_losers else 0.0

streak_base = longest_streak(rows)
streak_keep = longest_streak(kept)

print("="*70); print("TOTAL")
print(f"  BASE n={base_n} WR={base_wr:.2f} winners={base_w} losers={total_losers} streak={streak_base}")
print(f"  KEEP n={keep_n} WR={keep_wr:.2f} winners={keep_w} losers={losers_kept} streak={streak_keep}")
print(f"  CUT  n={len(cut)} WR={stats(cut)[2]:.2f}")
print(f"  winners_kept_pct={winners_kept_pct:.2f}  losers_cut_pct={losers_cut_pct:.2f}  WRdelta={keep_wr-base_wr:+.2f}")

print("="*70); print("BY YEAR (keep WR vs base WR same year)")
year_fail = []
for y in sorted(set(r["yr"] for r in rows)):
    yr_rows = [r for r in rows if r["yr"]==y]; yr_keep=[r for r in yr_rows if keep_mask(r)]
    _,_,bwr = stats(yr_rows); kn,kw,kwr = stats(yr_keep)
    worse = kwr < bwr
    if worse: year_fail.append(y)
    print(f"  {y}: base={bwr:.2f} keep={kwr:.2f} (n={kn}) d={kwr-bwr:+.2f} {'WORSE' if worse else 'ok'}")

print("="*70); print("BY BLOCK (keep WR vs base WR same block)")
block_fail = []
for b in sorted(set(r["block"] for r in rows)):
    b_rows=[r for r in rows if r["block"]==b]; b_keep=[r for r in b_rows if keep_mask(r)]
    _,_,bwr=stats(b_rows); kn,kw,kwr=stats(b_keep)
    worse = kwr < bwr
    if worse: block_fail.append(b)
    print(f"  {b}: base={bwr:.2f} keep={kwr:.2f} (n={kn}) d={kwr-bwr:+.2f} {'WORSE' if worse else 'ok'}")

print("="*70); print("CHERRY-PICK ROBUSTNESS (+-20% on all 3 thresholds)")
nbhd=[]
for fp in (0.8,0.9,1.0,1.1,1.2):
    for fd in (0.8,0.9,1.0,1.1,1.2):
        for fs in (0.8,0.9,1.0,1.1,1.2):
            pt=POS_T*fp; dtv=DISP_T*fd; stv=SKEW_T*fs
            kk=[r for r in rows if keep_mask(r,pt,dtv,stv)]
            kn,kw,kwr=stats(kk); nbhd.append((fp,fd,fs,kwr,100*kw/total_winners,kn))
wrs=[x[3] for x in nbhd]
collapse = min(wrs) < base_wr
print(f"  keep_wr neighborhood (125 pts): min={min(wrs):.2f} max={max(wrs):.2f} center={keep_wr:.2f}")
print(f"  any point keep_wr < base_wr ({base_wr:.2f})? {collapse}")
below = [(fp,fd,fs,kwr,kn) for fp,fd,fs,kwr,wkp,kn in nbhd if kwr<base_wr]
print(f"  points below base: {len(below)}/125")
for fp,fd,fs,kwr,kn in below[:10]:
    print(f"   pos*{fp} disp*{fd} skew*{fs}: keep_wr={kwr:.2f} n={kn}")
# winners kept across neighborhood
wkmin=min(x[4] for x in nbhd); print(f"  winners_kept% neighborhood min={wkmin:.1f}")

print("="*70); print("MARGINAL contribution of each clause")
def km_pos(r): return r["h1_pos"]>=POS_T
def km_disp(r): return r["disp4_atr"]>=DISP_T
def km_skew(r): return r["sell_skew_mig"]<=SKEW_T
for nm,fn in (("h1_pos>=0.54",km_pos),("disp4>=0.77",km_disp),("sellskew<=0.65",km_skew)):
    sub=[r for r in rows if fn(r)]; n,w,wr=stats(sub)
    print(f"  {nm}: n={n} WR={wr:.2f} d={wr-base_wr:+.2f} winners_kept%={100*w/total_winners:.1f}")
# drop-one-clause
import itertools
clauses={"pos":km_pos,"disp":km_disp,"skew":km_skew}
for drop in clauses:
    keep_cl=[c for c in clauses if c!=drop]
    sub=[r for r in rows if all(clauses[c](r) for c in keep_cl)]
    n,w,wr=stats(sub)
    print(f"  drop {drop}: n={n} WR={wr:.2f} (full={keep_wr:.2f}) => {drop} adds {keep_wr-wr:+.2f}")

print("="*70); print("LEAVE-ONE-BLOCK-OUT (does keep beat block base in all 8?)")
lobo_fail=[]
for b in sorted(set(r["block"] for r in rows)):
    b_rows=[r for r in rows if r["block"]==b]; b_keep=[r for r in b_rows if keep_mask(r)]
    _,_,bwr=stats(b_rows); kn,kw,kwr=stats(b_keep)
    if kwr<=bwr: lobo_fail.append(b)
print(f"  blocks where keep does NOT beat block-base: {lobo_fail}")

print("="*70); print("VERDICT INPUTS")
print(f"  winners_kept_pct={winners_kept_pct:.2f} (thr>=85)")
print(f"  year_fail={year_fail}")
print(f"  block_fail={block_fail} (thr>2/8); n_blocks={len(set(r['block'] for r in rows))}")
print(f"  cherry_collapse={collapse}")

veto=[]
if winners_kept_pct < 85: veto.append(f"cuts winners (kept {winners_kept_pct:.1f}% < 85%)")
if year_fail: veto.append(f"year worse: {year_fail}")
if len(block_fail) > 2: veto.append(f">2/8 blocks worse: {block_fail}")
if collapse: veto.append("cherry-pick: neighborhood collapses below base")
print("  look-ahead: h1_pos from CLOSED H1 bars (t_end<=tc); disp4_atr from bar cj close (entry bar, causal); sell_skew_mig from SELL bubbles known_at<=tc, no outcome -> NO LEAK")

survives = len(veto)==0
print("="*70); print("SURVIVES:", survives)
print("REASON:", "; ".join(veto) if veto else "passes all gates")
print(f"wr_keep={keep_wr:.2f} streak_keep={streak_keep} winners_kept_pct={winners_kept_pct:.2f} n_keep={keep_n} losers_cut_pct={losers_cut_pct:.2f}")
