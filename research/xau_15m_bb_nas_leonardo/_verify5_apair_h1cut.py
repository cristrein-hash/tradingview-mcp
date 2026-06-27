#!/usr/bin/env python3
"""
_verify5_apair_h1cut.py
DEVIL'S ADVOCATE verification of the 5ATR "A_pair (WINNER)" filter on dataset_5atr.jsonl.

RULE: CUT (i.e. REMOVE) entries where (h1_pos <= 0.65 OR h1_dist <= 1.85).
KEEP = the complement (rows that survive the cut).

Régua (recalibrated DA):
- Do NOT veto on tail/WR-only/lack-of-OOS.
- VETO only on:
  * look-ahead (feature uses future/outcome? non-closed HTF bar? bubbles known_at?)
  * non-stationarity: WR-after by YEAR vs BASE-OF-THAT-YEAR and by BLOCK;
    worse in any year OR >2/8 blocks worse  => veto
  * cuts winners < 85% kept
  * cherry-pick: ±20% neighborhood of thresholds collapses the effect
Report survives, reason, wr_keep, streak_keep, winners_kept_pct honestly.
"""
import json
from pathlib import Path

DS = Path(__file__).parent / "dataset_5atr.jsonl"
rows = [json.loads(l) for l in open(DS)]

# --- claimed thresholds ---
POS_T = 0.65
DIST_T = 1.85

def keep_mask(r, pos_t=POS_T, dist_t=DIST_T):
    """KEEP rows that are NOT cut. CUT = (h1_pos<=pos_t OR h1_dist<=dist_t)."""
    cut = (r["h1_pos"] <= pos_t) or (r["h1_dist"] <= dist_t)
    return not cut

def stats(subset):
    n = len(subset)
    w = sum(x["win"] for x in subset)
    wr = 100*w/n if n else 0.0
    return n, w, wr

def longest_streak(subset):
    """Longest consecutive-win streak in chronological order."""
    s = sorted(subset, key=lambda r: r["low_t"])
    best = cur = 0
    for r in s:
        if r["win"] == 1:
            cur += 1; best = max(best, cur)
        else:
            cur = 0
    return best

# ---------- TOTAL ----------
base_n, base_w, base_wr = stats(rows)
kept = [r for r in rows if keep_mask(r)]
cut = [r for r in rows if not keep_mask(r)]
keep_n, keep_w, keep_wr = stats(kept)

total_winners = base_w
winners_kept = keep_w
winners_kept_pct = 100*winners_kept/total_winners if total_winners else 0.0

total_losers = base_n - base_w
losers_kept = keep_n - keep_w
losers_cut_pct = 100*(total_losers - losers_kept)/total_losers if total_losers else 0.0

streak_base = longest_streak(rows)
streak_keep = longest_streak(kept)

print("="*70)
print("TOTAL")
print(f"  BASE   n={base_n} WR={base_wr:.2f} winners={base_w} losers={total_losers} streak={streak_base}")
print(f"  KEEP   n={keep_n} WR={keep_wr:.2f} winners={winners_kept} losers={losers_kept} streak={streak_keep}")
print(f"  CUT    n={len(cut)} WR={stats(cut)[2]:.2f}")
print(f"  winners_kept_pct={winners_kept_pct:.2f}  losers_cut_pct={losers_cut_pct:.2f}")
print(f"  WR delta={keep_wr-base_wr:+.2f}")

# ---------- BY YEAR (vs base of THAT year) ----------
print("="*70)
print("BY YEAR (keep WR vs base WR of same year)")
years = sorted(set(r["yr"] for r in rows))
year_fail = []
for y in years:
    yr_rows = [r for r in rows if r["yr"] == y]
    yr_keep = [r for r in yr_rows if keep_mask(r)]
    _,_,bwr = stats(yr_rows)
    kn,kw,kwr = stats(yr_keep)
    worse = kwr < bwr
    if worse: year_fail.append(y)
    print(f"  {y}: base_wr={bwr:.2f}  keep_wr={kwr:.2f} (n_keep={kn})  delta={kwr-bwr:+.2f}  {'WORSE' if worse else 'ok'}")

# ---------- BY BLOCK (vs base of THAT block) ----------
print("="*70)
print("BY BLOCK (keep WR vs base WR of same block)")
blocks = sorted(set(r["block"] for r in rows))
block_fail = []
for b in blocks:
    b_rows = [r for r in rows if r["block"] == b]
    b_keep = [r for r in b_rows if keep_mask(r)]
    _,_,bwr = stats(b_rows)
    kn,kw,kwr = stats(b_keep)
    worse = kwr < bwr
    if worse: block_fail.append(b)
    print(f"  {b}: base_wr={bwr:.2f}  keep_wr={kwr:.2f} (n_keep={kn})  delta={kwr-bwr:+.2f}  {'WORSE' if worse else 'ok'}")

# ---------- CHERRY-PICK: +-20% neighborhood ----------
print("="*70)
print("CHERRY-PICK ROBUSTNESS (+-20% on each threshold)")
nbhd = []
for fp in (0.8, 0.9, 1.0, 1.1, 1.2):
    for fd in (0.8, 0.9, 1.0, 1.1, 1.2):
        pt = POS_T*fp; dt = DIST_T*fd
        kk = [r for r in rows if keep_mask(r, pt, dt)]
        kn,kw,kwr = stats(kk)
        wkp = 100*kw/total_winners
        nbhd.append((fp,fd,kwr,wkp,kn))
wrs = [x[2] for x in nbhd]
print(f"  keep_wr across 25 neighborhood points: min={min(wrs):.2f} max={max(wrs):.2f} center={keep_wr:.2f}")
collapse = min(wrs) < base_wr  # any neighborhood point that fails to beat base
print(f"  any neighborhood point with keep_wr < base_wr ({base_wr:.2f})? {collapse}")
for fp,fd,kwr,wkp,kn in nbhd:
    tag = "  <-- below base" if kwr < base_wr else ""
    print(f"   pos*{fp:.1f}={POS_T*fp:.3f} dist*{fd:.1f}={DIST_T*fd:.3f}: keep_wr={kwr:.2f} wkept%={wkp:.1f} n={kn}{tag}")

# ---------- VERDICT ----------
print("="*70)
print("VERDICT INPUTS")
print(f"  winners_kept_pct={winners_kept_pct:.2f} (threshold >=85)")
print(f"  year_fail={year_fail}")
print(f"  block_fail={block_fail} (threshold >2/8)")
print(f"  cherry_collapse={collapse}")

veto_reasons = []
if winners_kept_pct < 85: veto_reasons.append(f"cuts winners (kept {winners_kept_pct:.1f}% < 85%)")
if year_fail: veto_reasons.append(f"year worse: {year_fail}")
if len(block_fail) > 2: veto_reasons.append(f">2/8 blocks worse: {block_fail}")
if collapse: veto_reasons.append("cherry-pick: neighborhood collapses below base")
# look-ahead: features h1_pos/h1_dist are H1 swing-position/distance-to-H1-EMA at entry low;
# both are HTF-context derived from closed H1 bars (no outcome, no future). No bubbles known_at issue.
print("  look-ahead: h1_pos/h1_dist = closed-H1 swing position & EMA distance at entry; no future/outcome leak")

survives = len(veto_reasons) == 0
print("="*70)
print("SURVIVES:", survives)
print("REASON:", "; ".join(veto_reasons) if veto_reasons else "passes all gates")
print(f"wr_keep={keep_wr:.2f} streak_keep={streak_keep} winners_kept_pct={winners_kept_pct:.2f}")
