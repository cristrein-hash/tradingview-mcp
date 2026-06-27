"""DA verification of OB-lens CUT rule on dataset_5atr.jsonl.

RULE (CUT when EITHER clause true; KEEP otherwise):
  into_supply = dist_supply_atr < -0.28   (price pushed INTO overhead supply)
  at_node     = vpnode_dist_atr  <  1.07   (pinned to the VP POC node)
  CUT = into_supply OR at_node
  KEEP = neither

Claimed: base WR 60.5 -> keep WR 62.49, n_keep 2554, streak_keep 28,
         winners_kept 86.6%, losers_cut 20.43%, y24 61.59 y25 65.4 y26 55.99,
         robust 4/4 jitter, 7/8 blocks.

Régua (veto only by):
 1. look-ahead: any clause feature use future/outcome?
 2. stationarity: per-YEAR vs that year's OWN base, and per-BLOCK.
    WORSE in any year, OR >2/8 blocks worse = VETO.
 3. winners_kept < 85% = VETO.
 4. cherry-pick: +-20% threshold neighborhood collapses cutWR -> VETO.
"""
import json

rows = [json.loads(l) for l in open('dataset_5atr.jsonl')]
N = len(rows)

SUP_T = -0.28
NODE_T = 1.07


def into_supply(r, t=SUP_T):
    return r['dist_supply_atr'] < t


def at_node(r, t=NODE_T):
    return r['vpnode_dist_atr'] < t


def cut(r):
    return into_supply(r) or at_node(r)


def keep(r):
    return not cut(r)


def wr(rs):
    return sum(x['win'] for x in rs) / len(rs) * 100 if rs else float('nan')


def max_loss_streak(rs):
    s = sorted(rs, key=lambda r: r['low_t'])
    cur = best = 0
    for r in s:
        if r['win'] == 0:
            cur += 1
            best = max(best, cur)
        else:
            cur = 0
    return best


rows_sorted = sorted(rows, key=lambda r: r['low_t'])

base_wr = wr(rows)
base_streak = max_loss_streak(rows_sorted)
total_winners = sum(r['win'] for r in rows)
total_losers = N - total_winners
print(f"=== BASE: n={N} WR={base_wr:.2f} streak={base_streak} winners={total_winners} losers={total_losers}")

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

print(f"=== KEEP: n={len(kept)} WR={keep_wr:.2f} (+{keep_wr-base_wr:.2f}pp) streak={keep_streak} (base {base_streak})")
print(f"=== CUT:  n={len(cutset)} cutWR={cut_wr:.2f}")
print(f"    winners_kept={winners_kept}/{total_winners} = {winners_kept_pct:.2f}%")
print(f"    losers_cut={losers_cut}/{total_losers} = {losers_cut_pct:.2f}%")

# per YEAR vs own base
print("\n--- PER YEAR (base-of-year vs keep-of-year) ---")
year_ok = True
for y in sorted(set(r['yr'] for r in rows)):
    yr_all = [r for r in rows if r['yr'] == y]
    yr_keep = [r for r in kept if r['yr'] == y]
    b = wr(yr_all)
    kk = wr(yr_keep)
    worse = kk < b - 1e-9
    if worse:
        year_ok = False
    print(f"  y{y}: base={b:.2f} keep={kk:.2f} delta={kk-b:+.2f}  {'WORSE!' if worse else 'ok'}  (n_keep={len(yr_keep)})")
print(f"  year_ok (no year worse): {year_ok}")

# per BLOCK
print("\n--- PER BLOCK (base vs keep) ---")
blocks = sorted(set(r['block'] for r in rows))
nblk = len(blocks)
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
print(f"  worse_blocks = {worse_blocks}/{nblk} (veto if >2)")

# LOBO
print("\n--- LEAVE-ONE-BLOCK-OUT (keep WR lift on remaining blocks) ---")
lobo = []
for b in blocks:
    rest = [r for r in rows if r['block'] != b]
    rest_keep = [r for r in rest if keep(r)]
    lift = wr(rest_keep) - wr(rest)
    lobo.append(lift)
    print(f"  drop {b}: rest base={wr(rest):.2f} keep={wr(rest_keep):.2f} lift={lift:+.2f}")
print(f"  LOBO lift range: {min(lobo):+.2f} .. {max(lobo):+.2f}")

# threshold +-20% neighborhood (cherry-pick / jitter)
print("\n--- THRESHOLD +-20% NEIGHBORHOOD (full-rule keepWR + cutWR) ---")
collapse = False
for sm, lbl_s in [(SUP_T*0.8, '-20%'), (SUP_T, 'center'), (SUP_T*1.2, '+20%')]:
    for nm, lbl_n in [(NODE_T*0.8, '-20%'), (NODE_T, 'center'), (NODE_T*1.2, '+20%')]:
        def _cut(r, sm=sm, nm=nm):
            return r['dist_supply_atr'] < sm or r['vpnode_dist_atr'] < nm
        kp = [r for r in rows if not _cut(r)]
        cs = [r for r in rows if _cut(r)]
        kw = wr(kp)
        print(f"  sup<{sm:+.3f}[{lbl_s}] node<{nm:.3f}[{lbl_n}]: keepWR={kw:.2f} cutWR={wr(cs):.2f} n_keep={len(kp)}")

# robustness: keep WR across all 9 jitter cells stays above base?
jitter_keepwrs = []
for sm in [SUP_T*0.8, SUP_T, SUP_T*1.2]:
    for nm in [NODE_T*0.8, NODE_T, NODE_T*1.2]:
        kp = [r for r in rows if not (r['dist_supply_atr'] < sm or r['vpnode_dist_atr'] < nm)]
        jitter_keepwrs.append(wr(kp))
print(f"  jitter keepWR range: {min(jitter_keepwrs):.2f} .. {max(jitter_keepwrs):.2f} (all must exceed base {base_wr:.2f})")
jitter_ok = min(jitter_keepwrs) > base_wr

# leave-one-clause-out (no single carrier doing all the lift)
print("\n--- LEAVE-ONE-CLAUSE-OUT ---")
ks_only_supply = [r for r in rows if not into_supply(r)]   # drop node clause
ks_only_node = [r for r in rows if not at_node(r)]         # drop supply clause
print(f"  drop node (cut only into_supply): keepWR={wr(ks_only_supply):.2f} n={len(ks_only_supply)}")
print(f"  drop supply (cut only at_node):   keepWR={wr(ks_only_node):.2f} n={len(ks_only_node)}")
cs_sup = [r for r in rows if into_supply(r)]
cs_node = [r for r in rows if at_node(r)]
print(f"  clause into_supply alone: cut n={len(cs_sup)} cutWR={wr(cs_sup):.2f}")
print(f"  clause at_node alone:     cut n={len(cs_node)} cutWR={wr(cs_node):.2f}")

# LOOK-AHEAD audit
print("\n--- LOOK-AHEAD AUDIT (feature semantics from build_5atr_dataset.py) ---")
print("  dist_supply_atr: nearest supply zone above, zones born_t<=tc (entry bar). Signal-bar geometry; NOT outcome.")
print("  vpnode_dist_atr: dist c15->VP POC over seg=s[cj-96:cj+1] (bars up to entry). Causal window; NOT outcome.")
print("  Neither references s[k] for k>cj. No HTF-unclosed / no bubble-future. PASS.")

# VERDICT
print("\n=== VERDICT ===")
veto = []
if not year_ok:
    veto.append("a year got worse (non-stationary)")
if worse_blocks > 2:
    veto.append(f"{worse_blocks}/{nblk} blocks worse")
if winners_kept_pct < 85.0:
    veto.append(f"winners_kept {winners_kept_pct:.2f}% < 85%")
if not jitter_ok:
    veto.append("jitter neighborhood collapses below base (cherry-pick)")
survives = len(veto) == 0
print(f"survives={survives}")
print(f"wr_keep={keep_wr:.2f}")
print(f"streak_keep={keep_streak}")
print(f"winners_kept_pct={winners_kept_pct:.2f}")
print(f"jitter_ok={jitter_ok} year_ok={year_ok} worse_blocks={worse_blocks}/{nblk}")
print(f"veto_reasons={veto}")
