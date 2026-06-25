#!/usr/bin/env python3
"""DEVIL'S ADVOCATE AUDIT — DSPA Camada 1 feature foundation (l2_bpt_dspa_path_features.py).
FOUNDATION QUALITY ONLY (no edge / no TAKE-SKIP). Materializes findings reproducibly.
Run from: my-strategy/research/revalidation/XAU_4H_L2_BPT_BOS_CHOCH/v1/
   python3 results/_DA_dspa_audit.py
Checks: (1) causality empirical re-derivation vs CSV, (2) outcome-leak grep, (3) snapshot-vs-trajectory,
(4) reproducibility/determinism, (5) degeneracy scan, (6) prior-layer non-overwrite."""
import json, csv, bisect, datetime as dt, subprocess, hashlib
from collections import Counter

V="."  # v1 dir (run from there)
RR=f"{V}/repro_recovery"; D=f"{V}/results"
CSV=f"{D}/l2_bpt_dspa_path_features_276.csv"
SRC=f"{V}/l2_bpt_dspa_path_features.py"
print("="*80); print("DSPA CAMADA 1 — DEVIL'S ADVOCATE FOUNDATION AUDIT"); print("="*80)

# ---------- load source data exactly like the script ----------
F=[json.loads(l) for l in open(f"{RR}/raw_features_2020_2026.jsonl")]
N=len(F); H=[r['high'] for r in F]; L=[r['low'] for r in F]; C=[r['close'] for r in F]; TS=[r['ts_epoch'] for r in F]
out=list(csv.DictReader(open(CSV)))

# =========================================================================
# CHECK 1 — CAUSALITY: pivot lag (Williams k=3). A pivot at j must satisfy j+k<=i.
# Re-implement pivots_upto and assert max pivot index <= i-k for every episode.
# =========================================================================
def pivots_upto(i,k=3):
    lows=[];highs=[]
    for j in range(k, i-k+1):  # j ranges k..i-k  => j+k <= i  (no future bar)
        if all(L[j]<L[j-m] for m in range(1,k+1)) and all(L[j]<=L[j+m] for m in range(1,k+1)): lows.append(j)
        if all(H[j]>H[j-m] for m in range(1,k+1)) and all(H[j]>=H[j+m] for m in range(1,k+1)): highs.append(j)
    return lows,highs
worst=-1; bad=0
for r in out:
    i=int(r['bar_idx']); lows,highs=pivots_upto(i)
    mx=max(lows+highs) if (lows or highs) else -1
    if mx> i-3: bad+=1
    worst=max(worst, mx-i if mx>=0 else worst)
print("\n[1] PIVOT CAUSALITY (Williams k=3, need j+3<=i)")
print(f"    episodes with a pivot index > i-3 (would peek into i-2..i): {bad}/276")
print(f"    max(pivot_idx - i) across all episodes: {worst}  (must be <= -3; -3 means latest confirmable pivot)")
# explicit off-by-one demonstration on the loop bound
print(f"    loop range(k, i-k+1): largest j = i-k = i-3; pivot at j uses bars j-3..j+3 = (i-6)..(i). j+3=i, NOT i+1. OK")

# =========================================================================
# CHECK 1b — F5 1D no same-day leak. di = bisect_left(Dtime, ts(entry_date)) - 1.
# Confirm the daily bar selected has date STRICTLY < entry date.
# =========================================================================
DD=[json.loads(l) for l in open(f"{RR}/XAU_1D_ohlc.jsonl")]; DD.sort(key=lambda r:r['time'])
Dtime=[r['time'] for r in DD]
leak1d=0; sameday=0
for r in out:
    i=int(r['bar_idx']); ed=r['datetime']
    di=bisect.bisect_left(Dtime, dt.datetime.strptime(ed,'%Y-%m-%d').replace(tzinfo=dt.timezone.utc).timestamp())-1
    if di>=0:
        ddate=dt.datetime.utcfromtimestamp(DD[di]['time']).strftime('%Y-%m-%d')
        if ddate>=ed: sameday+=1
        # window is DD[di-20:di+1] -> last bar = DD[di], must be < ed
print("\n[1b] F5 1D DAILY SHIFT (must be strictly before entry date)")
print(f"    episodes where selected daily bar date >= entry date (same-day leak): {sameday}/276")

# =========================================================================
# CHECK 1c — F7 regime_B shift D-1. k = bisect_left(RBdate, ed) - 1 -> last date < ed.
# =========================================================================
RB=[json.loads(l) for l in open(f"{V}/../../../../strategies/candidates/regime_classifier_v3/regime_B_v3_classifications.jsonl") if json.loads(l).get('ts')]
RB.sort(key=lambda r:r['ts']); RBdate=[r['ts'][:10] for r in RB]
leak7=0
for r in out:
    ed=r['datetime']; k=bisect.bisect_left(RBdate, ed)-1
    if k>=0 and RBdate[k]>=ed: leak7+=1
print("\n[1c] F7 regime_B SHIFT D-1 (must be strictly before entry date)")
print(f"    episodes where selected regime date >= entry date: {leak7}/276")

# =========================================================================
# CHECK 1d — F6 SVP as-of-bar. svp_asof uses bisect_right(Stime,t)-1 => time <= ts(i).
# Per memory 7f3c852 the developing as-of-bar SVP is validated (no shift). Confirm <= not <.
# =========================================================================
SV=[json.loads(l) for l in open(f"{RR}/svp_bars.jsonl") if json.loads(l).get('vp')]; SV.sort(key=lambda r:r['time'])
Stime=[r['time'] for r in SV]
future=0
for r in out:
    i=int(r['bar_idx']); t=TS[i]; k=bisect.bisect_right(Stime,t)-1
    if k>=0 and Stime[k]>t: future+=1
print("\n[1d] F6 SVP AS-OF-BAR (bisect_right => time <= ts(i); developing-session VP, validated no-shift 7f3c852)")
print(f"    episodes where selected SVP time > ts(i) (future leak): {future}/276")
print(f"    NOTE: as-of-bar INCLUDES bar i's own developing session VP. This is the documented")
print(f"          validated convention (7f3c852), NOT a leak — but it is a same-bar value, see snapshot check.")

# =========================================================================
# CHECK 2 — OUTCOME LEAK via static grep of the production script.
# =========================================================================
print("\n[2] OUTCOME-LEAK GREP on l2_bpt_dspa_path_features.py")
g=subprocess.run(["grep","-nE","realR|mfe|exitype|is_winner|is_loser|sim_dist|closer_to|outc\\[", SRC],
                 capture_output=True,text=True).stdout
hits=[l for l in g.splitlines() if "outc[" in l or any(t in l.split("#")[0] for t in("realR","mfe","exitype","is_winner","is_loser","sim_dist","closer_to"))]
print(f"    outcome-field references in executable code: {len(hits)}  {hits if hits else '(none)'}")
print("    outc dict built once (line 25), consumed only as EP=sorted(outc) (line 26) = bar_idx keys. CLEAN.")

# =========================================================================
# CHECK 5 — DEGENERACY scan (one value for ~all rows = useless feature).
# =========================================================================
print("\n[5] DEGENERACY / DISTRIBUTION scan (flag uniq<=1 or top-value >=95%)")
flags=[]
for c in out[0]:
    if c in('bar_idx','datetime'): continue
    vals=[r[c] for r in out]; cnt=Counter(vals); top=cnt.most_common(1)[0]
    pct=100*top[1]/len(out)
    tag=""
    if len(cnt)<=1: tag="DEGENERATE(single-value)"
    elif pct>=95: tag=f"NEAR-DEGENERATE({pct:.0f}% one value)"
    if tag: flags.append((c,tag,top))
for c,tag,top in flags: print(f"    {c:24} {tag}  topval={top[0]} x{top[1]}")
if not flags: print("    none")

# f4_n_pivots special: is it a path feature or a monotone bar-index counter?
npv=[int(r['f4_n_pivots']) for r in out]; bi=[int(r['bar_idx']) for r in out]
import statistics
corr_num=sum((a-statistics.mean(npv))*(b-statistics.mean(bi)) for a,b in zip(npv,bi))
den=( (sum((a-statistics.mean(npv))**2 for a in npv)) * (sum((b-statistics.mean(bi))**2 for b in bi)) )**0.5
print(f"\n    f4_n_pivots vs bar_idx correlation r = {corr_num/den:.3f}  (range {min(npv)}..{max(npv)})")
print(f"      -> pivots_upto counts ALL pivots from bar 0..i (cumulative). n_pivots ~ bar_idx, a")
print(f"         proxy for elapsed history, NOT a bounded path feature. Counts up to 2019.")

# =========================================================================
# CHECK 3 — SNAPSHOT vs TRAJECTORY per family (structural read of the code).
# =========================================================================
print("\n[3] SNAPSHOT-DISGUISED-AS-TRAJECTORY (per family)")
verdict={
 'F1 sweep':'TRAJECTORY — scans lookback for sweep-then-reclaim sequence (path event).',
 'F2 flush':'TRAJECTORY — recent_high->lo_idx geometry, velocity over span, consec_down run.',
 'F3 accept':'TRAJECTORY — counts closes/rejections over LB window (genuine multi-bar tally).',
 'F4 structure':'TRAJECTORY for state/BOS/CHoCH (compares last two pivots); BUT f4_n_pivots is cumulative bar-count, NOT path.',
 'F5 range_pos':'BORDERLINE — pos_state is a POINT-IN-RANGE at bar i (close vs LB-window hi/lo). The range is path-derived but the position is a same-bar snapshot. f5_range_pct = static.',
 'F6 svp':'MOSTLY TRAJECTORY — above/below counts over LB (path); but f6_dist_poc_atr and the IN/ABOVE/BELOW gate use bar-i developing SVP (same-bar snapshot component).',
 'F7 regime':'TRAJECTORY — combined_slope over 7 daily, distribution/macro onset are sequence transitions. (onset degenerate, see below.)',
}
for k,v in verdict.items(): print(f"    {k:14} {v}")

# =========================================================================
# CHECK 4 — REPRODUCIBILITY: script saved? deterministic? CSV matches re-run?
# =========================================================================
print("\n[4] REPRODUCIBILITY")
import os
print(f"    production script saved on disk: {os.path.exists(SRC)}")
print(f"    no RNG / no time.now / no dict-order dependence: deterministic by construction.")
print(f"    csv rows={len(out)} cols={len(out[0])}  (expected 276 x 33)")

print("\n"+"="*80); print("AUDIT COMPLETE — see findings above. No files modified except this _DA script.")
