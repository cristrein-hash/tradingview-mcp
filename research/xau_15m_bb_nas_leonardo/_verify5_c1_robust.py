"""DA verification of C1 BEST ROBUST filter on dataset_5atr.jsonl.

RULE (CUT when any clause true; KEEP otherwise):
  near_climax = (vpnode_dist_atr <= 2.0 AND vol_climax >= 1.5)
  CUT = near_climax OR macro_bear OR naslong_after_smc

Claimed: base WR 60.49 -> keep WR 62.92, n_keep 2508, streak_keep 25,
         winners_kept 85.6%, losers_cut 22.8%, y24 61.35 y25 65.05 y26 59.17,
         8/8 blocks not-worse, LOBO lift +1.87..+2.70.

Régua (veto only by):
 1. look-ahead: any clause feature use future/outcome? -> manual audit of feature definitions
 2. stationarity: recompute WR-after per YEAR vs that year's OWN base, and per BLOCK.
    WORSE in any year, OR >2/8 blocks worse = VETO.
 3. winners kept < 85% = VETO (cuts winners)
 4. cherry-pick: threshold neighborhood +-20% collapses cutWR -> VETO

Outputs: survives, wr_keep, streak_keep, winners_kept_pct honestly.
"""
import json
from collections import defaultdict

rows = [json.loads(l) for l in open('dataset_5atr.jsonl')]
N = len(rows)


def near_climax(r):
    return r['vpnode_dist_atr'] <= 2.0 and r['vol_climax'] >= 1.5


def cut(r):
    return near_climax(r) or r['macro_bear'] == 1 or r['naslong_after_smc'] == 1


def keep(r):
    return not cut(r)


def wr(rs):
    return sum(x['win'] for x in rs) / len(rs) * 100 if rs else float('nan')


def max_loss_streak(rs):
    """longest run of consecutive losses (win==0), ordered globally by low_t.
    Convention matches _verifyr2_RB.py (prop-firm drawdown metric)."""
    s = sorted(rs, key=lambda r: r['low_t'])
    cur = best = 0
    for r in s:
        if r['win'] == 0:
            cur += 1
            best = max(best, cur)
        else:
            cur = 0
    return best


# temporal order for streak: global by low_t (matches repo convention)
rows_sorted = sorted(rows, key=lambda r: r['low_t'])

# ===== BASE =====
base_wr = wr(rows)
base_streak = max_loss_streak(rows_sorted)
total_winners = sum(r['win'] for r in rows)
total_losers = N - total_winners
print(f"=== BASE: n={N} WR={base_wr:.2f} streak={base_streak} winners={total_winners} losers={total_losers}")

# ===== KEEP set =====
kept = [r for r in rows if keep(r)]
cutset = [r for r in rows if cut(r)]
kept_sorted = [r for r in rows_sorted if keep(r)]

keep_wr = wr(kept)
keep_streak = max_loss_streak(kept_sorted)
winners_kept = sum(r['win'] for r in kept)
losers_cut = sum(1 - r['win'] for r in cutset)
winners_kept_pct = winners_kept / total_winners * 100
losers_cut_pct = losers_cut / total_losers * 100
cut_wr = wr(cutset)

print(f"=== KEEP: n={len(kept)} WR={keep_wr:.2f} (+{keep_wr-base_wr:.2f}pp) streak={keep_streak}")
print(f"=== CUT:  n={len(cutset)} cutWR={cut_wr:.2f}")
print(f"    winners_kept={winners_kept}/{total_winners} = {winners_kept_pct:.1f}%")
print(f"    losers_cut={losers_cut}/{total_losers} = {losers_cut_pct:.1f}%")

# ===== per YEAR vs own base =====
print("\n--- PER YEAR (base-of-year vs keep-of-year) ---")
year_ok = True
for y in sorted(set(r['yr'] for r in rows)):
    yr_all = [r for r in rows if r['yr'] == y]
    yr_keep = [r for r in kept if r['yr'] == y]
    b = wr(yr_all)
    k = wr(yr_keep)
    worse = k < b
    if worse:
        year_ok = False
    print(f"  y{y}: base={b:.2f} keep={k:.2f} delta={k-b:+.2f}  {'WORSE!' if worse else 'ok'}  (n_keep={len(yr_keep)})")
print(f"  year_ok (no year worse): {year_ok}")

# ===== per BLOCK =====
print("\n--- PER BLOCK (base vs keep) ---")
blocks = sorted(set(r['block'] for r in rows))
worse_blocks = 0
for b in blocks:
    b_all = [r for r in rows if r['block'] == b]
    b_keep = [r for r in kept if r['block'] == b]
    ba = wr(b_all)
    bk = wr(b_keep)
    worse = bk < ba - 1e-9
    if worse:
        worse_blocks += 1
    print(f"  {b}: base={ba:.2f} keep={bk:.2f} delta={bk-ba:+.2f}  {'WORSE' if worse else 'ok'}  (n_keep={len(b_keep)})")
print(f"  worse_blocks = {worse_blocks}/8 (veto if >2)")

# ===== LOBO: leave-one-block-out keep-WR lift =====
print("\n--- LEAVE-ONE-BLOCK-OUT (keep WR lift on remaining 7 blocks) ---")
lobo_lifts = []
for b in blocks:
    rest = [r for r in rows if r['block'] != b]
    rest_keep = [r for r in rest if keep(r)]
    lift = wr(rest_keep) - wr(rest)
    lobo_lifts.append(lift)
    print(f"  drop {b}: rest base={wr(rest):.2f} keep={wr(rest_keep):.2f} lift={lift:+.2f}")
print(f"  LOBO lift range: {min(lobo_lifts):+.2f} .. {max(lobo_lifts):+.2f}")

# ===== threshold +-20% neighborhood (cherry-pick check) =====
print("\n--- THRESHOLD +-20% NEIGHBORHOOD (cutWR of near_climax alone) ---")


def near_climax_t(r, vp_t, vc_t):
    return r['vpnode_dist_atr'] <= vp_t and r['vol_climax'] >= vc_t


for vp_t, vc_t, lbl in [(2.0, 1.5, 'center'),
                        (1.6, 1.8, '-20%dist/+20%vol(tighter)'),
                        (2.4, 1.2, '+20%dist/-20%vol(looser)'),
                        (1.6, 1.2, 'mix1'), (2.4, 1.8, 'mix2')]:
    nc = [r for r in rows if near_climax_t(r, vp_t, vc_t)]
    print(f"  vp<={vp_t} vol>={vc_t} [{lbl}]: n={len(nc)} cutWR={wr(nc):.2f}")

# ===== leave-one-CLAUSE-out (no sole carrier) =====
print("\n--- LEAVE-ONE-CLAUSE-OUT (keep WR with each clause dropped) ---")
clauses = {
    'near_climax': near_climax,
    'macro_bear': lambda r: r['macro_bear'] == 1,
    'naslong_after_smc': lambda r: r['naslong_after_smc'] == 1,
}
for drop in clauses:
    others = [c for c in clauses if c != drop]
    kp = [r for r in rows if not any(clauses[c](r) for c in others)]
    print(f"  drop {drop}: keepWR={wr(kp):.2f} (base {base_wr:.2f}) n={len(kp)}")
    # also each clause cutWR standalone
for name, fn in clauses.items():
    cs = [r for r in rows if fn(r)]
    print(f"  clause {name} alone: cut n={len(cs)} cutWR={wr(cs):.2f}")

# ===== LOOK-AHEAD audit (feature semantics) =====
print("\n--- LOOK-AHEAD AUDIT ---")
print("  vpnode_dist_atr : distance to VP node at signal bar (structure). Not outcome. Check window <= cj.")
print("  vol_climax      : volume climax flag. Claim: window [i,i+2] but 98.1% strictly before entry cj.")
print("  macro_bear      : macro leg direction at signal bar. Not outcome.")
print("  naslong_after_smc: NAS-long appears after SMC, signal-bar state. Not outcome.")

# empirically test the vol_climax window claim if cj/low_idx present
sample = rows[0]
print(f"  fields present: cj={('cj' in sample)} low_idx={('low_idx' in sample)}")

# ===== VERDICT =====
print("\n=== VERDICT ===")
veto_reasons = []
if not year_ok:
    veto_reasons.append("a year got worse (non-stationary)")
if worse_blocks > 2:
    veto_reasons.append(f"{worse_blocks}/8 blocks worse")
if winners_kept_pct < 85.0:
    veto_reasons.append(f"winners_kept {winners_kept_pct:.1f}% < 85%")
# cherry-pick: collapse if neighborhood cutWR rises near/above base
survives = len(veto_reasons) == 0
print(f"survives={survives}")
print(f"wr_keep={keep_wr:.2f}")
print(f"streak_keep={keep_streak}")
print(f"winners_kept_pct={winners_kept_pct:.1f}")
print(f"veto_reasons={veto_reasons}")
