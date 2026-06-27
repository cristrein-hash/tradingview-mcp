#!/usr/bin/env python3
"""
_verify5_f4_h1pos_h1dist_naslong.py
DEVIL'S ADVOCATE verification of the 5ATR "F4" 3-cut filter on dataset_5atr.jsonl.

RULE (CUT = REMOVE): CUT (h1_pos<=0.65 OR h1_dist<=1.85 OR naslong_after_smc==1).
KEEP = complement.

Recalibrated DA régua:
- Do NOT veto on tail/WR-only/lack-of-OOS.
- VETO only on:
  * look-ahead (feature uses future/outcome? non-closed HTF bar? bubbles known_at?)
  * non-stationarity: WR-after by YEAR vs BASE-OF-THAT-YEAR and by BLOCK;
    worse in any year OR >2/8 blocks worse  => veto
  * cuts winners < 85% kept
  * cherry-pick: +-20% neighborhood of thresholds collapses the effect
Report survives, reason, wr_keep, streak_keep, winners_kept_pct honestly.
"""
import json
from pathlib import Path

DS = Path(__file__).parent / "dataset_5atr.jsonl"
rows = [json.loads(l) for l in open(DS)]

POS_T = 0.65
DIST_T = 1.85

def keep_mask(r, pos_t=POS_T, dist_t=DIST_T):
    cut = (r["h1_pos"] is not None and r["h1_pos"] <= pos_t) \
          or (r["h1_dist"] is not None and r["h1_dist"] <= dist_t) \
          or (r.get("naslong_after_smc") == 1)
    return not cut

def stats(subset):
    n = len(subset); w = sum(x["win"] for x in subset)
    return n, w, (100*w/n if n else 0.0)

def longest_streak(subset):
    s = sorted(subset, key=lambda r: r["low_t"]); best = cur = 0
    for r in s:
        if r["win"] == 1: cur += 1; best = max(best, cur)
        else: cur = 0
    return best

# null h1 check
n_null = sum(1 for r in rows if r["h1_pos"] is None or r["h1_dist"] is None)
print(f"rows with null h1_pos/h1_dist: {n_null}")

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

print("="*70); print("CHERRY-PICK ROBUSTNESS (+-20% on h1_pos & h1_dist; naslong cut fixed)")
nbhd=[]
for fp in (0.8,0.9,1.0,1.1,1.2):
    for fd in (0.8,0.9,1.0,1.1,1.2):
        pt=POS_T*fp; dtv=DIST_T*fd
        kk=[r for r in rows if keep_mask(r,pt,dtv)]
        kn,kw,kwr=stats(kk); nbhd.append((fp,fd,kwr,100*kw/total_winners,kn))
wrs=[x[2] for x in nbhd]
collapse = min(wrs) < base_wr
print(f"  keep_wr neighborhood: min={min(wrs):.2f} max={max(wrs):.2f} center={keep_wr:.2f}")
print(f"  any point keep_wr < base_wr ({base_wr:.2f})? {collapse}")
for fp,fd,kwr,wkp,kn in nbhd:
    tag = "  <-- below base" if kwr<base_wr else ""
    print(f"   pos*{fp:.1f}={POS_T*fp:.3f} dist*{fd:.1f}={DIST_T*fd:.3f}: keep_wr={kwr:.2f} wkept%={wkp:.1f} n={kn}{tag}")

# marginal value of the naslong cut alone (vs F2 2-cut)
def f2_keep(r):
    return not ((r["h1_pos"] is not None and r["h1_pos"]<=POS_T) or (r["h1_dist"] is not None and r["h1_dist"]<=DIST_T))
f2=[r for r in rows if f2_keep(r)]
_,f2w,f2wr=stats(f2)
print("="*70); print("MARGINAL: naslong cut on top of F2")
print(f"  F2 keep: n={len(f2)} WR={f2wr:.2f} winners_kept%={100*f2w/total_winners:.1f}")
print(f"  F4 keep: n={keep_n} WR={keep_wr:.2f} winners_kept%={winners_kept_pct:.1f}  => naslong adds WR {keep_wr-f2wr:+.2f}")

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
print("  look-ahead: h1_pos/h1_dist from CLOSED H1 bars at entry; naslong_after_smc uses NAS LONG events with ev_t<e_t<=tc (causal, no outcome) -> no leak")

survives = len(veto)==0
print("="*70); print("SURVIVES:", survives)
print("REASON:", "; ".join(veto) if veto else "passes all gates")
print(f"wr_keep={keep_wr:.2f} streak_keep={streak_keep} winners_kept_pct={winners_kept_pct:.2f} n_keep={keep_n} losers_cut_pct={losers_cut_pct:.2f}")
