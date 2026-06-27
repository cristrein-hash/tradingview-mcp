"""DA verification of F4 CUT[buyL_recent & ny_overlap] on r2_keep==1 subset.
Filter: DROP trades where buy_L_recent==1 AND is_ny_overlap==1 (keep the rest).
Régua: veta só por look-ahead / estacionariedade (ano vs base-do-ano, blocos) /
winners<85% / combo cherry-picked. Recompute WR before/after total+year+block, streak.
Causality of inputs already confirmed in build_r2_features.py:
  - buy_L_recent: known_bubbles filtered known_at<=tc and s_rec sells t<=tc (no future).
  - is_ny_overlap: UTC hour of tc only. No outcome/future leakage.
"""
import json
from collections import defaultdict

PATH = '/Users/cristrein/tradingview-mcp/research/xau_15m_bb_nas_leonardo/dataset_r2refine.jsonl'

rows = [json.loads(l) for l in open(PATH)]
allk = sorted([r for r in rows if r['r2_keep'] == 1], key=lambda r: r['low_t'])


def wr(rs):
    return 100.0 * sum(r['win'] for r in rs) / len(rs) if rs else 0.0


def streak(rs):
    cur = mx = 0
    for r in rs:
        if r['win'] == 0:
            cur += 1; mx = max(mx, cur)
        else:
            cur = 0
    return mx


def cut(r):  # True = dropped by F4
    return r['buy_L_recent'] == 1 and r['is_ny_overlap'] == 1


keep = [r for r in allk if not cut(r)]
dropped = [r for r in allk if cut(r)]

winners_total = sum(r['win'] for r in allk)
losers_total = len(allk) - winners_total
winners_kept = sum(r['win'] for r in keep)
losers_kept = len(keep) - winners_kept
winners_kept_pct = 100.0 * winners_kept / winners_total
losers_cut_pct = 100.0 * (losers_total - losers_kept) / losers_total

print('=== F4 CUT[buyL_recent & ny_overlap] on r2_keep==1 ===')
print(f'base: n={len(allk)} WR={wr(allk):.2f} streak={streak(allk)}')
print(f'KEEP: n={len(keep)} WR={wr(keep):.2f} streak={streak(keep)}')
print(f'dropped n={len(dropped)} (winners={sum(r["win"] for r in dropped)} losers={len(dropped)-sum(r["win"] for r in dropped)})')
print(f'winners_kept_pct={winners_kept_pct:.1f}  losers_cut_pct={losers_cut_pct:.1f}')

# ---- per-year vs BASE-OF-YEAR within r2_keep ----
print('\n--- per year (kept WR vs base-of-year within r2_keep) ---')
yr_fail = []
for y in (2024, 2025, 2026):
    by = [r for r in allk if r['yr'] == y]
    ky = [r for r in keep if r['yr'] == y]
    base_y = wr(by)
    keep_y = wr(ky)
    ok = len(ky) > 0 and keep_y >= base_y
    if not ok:
        yr_fail.append(y)
    print(f'  {y}: base={base_y:.2f} (n={len(by)})  kept={keep_y:.2f} (n={len(ky)})  {"OK" if ok else "WORSE!!"}')

# ---- 8 contiguous equal-count blocks, kept vs block-base ----
print('\n--- 8 blocks (kept WR vs block-base WR) ---')
n = len(allk); size = n // 8
worse_blocks = 0
for i in range(8):
    lo = i * size
    hi = (i + 1) * size if i < 7 else n
    bb = allk[lo:hi]
    kb = [r for r in bb if not cut(r)]
    base_b = wr(bb); keep_b = wr(kb) if kb else 0.0
    ok = len(kb) > 0 and keep_b >= base_b
    if not ok:
        worse_blocks += 1
    print(f'  block{i+1} [{bb[0]["block"]}..]: base={base_b:.1f} kept={keep_b:.1f} (n_kept={len(kb)}/{len(bb)})  {"ok" if ok else "WORSE"}')

print(f'\nworse_blocks={worse_blocks}/8 (claim: 6/8 non-worse => 2 worse)')

# ---- neighborhood / cherry-pick collapse: each leg alone + AND ----
print('\n--- neighborhood (does combo collapse to one leg?) ---')
for name, fn in [
    ('buyL_recent==1 alone', lambda r: r['buy_L_recent'] == 1),
    ('ny_overlap==1 alone', lambda r: r['is_ny_overlap'] == 1),
    ('AND (F4 drop)', cut),
]:
    sub = [r for r in allk if fn(r)]
    if sub:
        print(f'  {name}: n={len(sub)} WR={wr(sub):.2f} (these are the DROPPED pocket; lower=better cut)')

# robustness on lifted thresholds: drop one leg, does pocket stay loser-dense?
print('\n--- single-leg pockets WR (cherry-pick check) ---')
buyL = [r for r in allk if r['buy_L_recent'] == 1]
ny = [r for r in allk if r['is_ny_overlap'] == 1]
print(f'  buyL pocket WR={wr(buyL):.1f} vs base {wr(allk):.2f} -> lift {wr(buyL)-wr(allk):+.1f}')
print(f'  ny  pocket WR={wr(ny):.1f} vs base {wr(allk):.2f} -> lift {wr(ny)-wr(allk):+.1f}')

# ---- verdict ----
fail_reasons = []
if wr(keep) <= wr(allk):
    fail_reasons.append('no WR improvement')
if yr_fail:
    fail_reasons.append(f'year(s) worse vs base-of-year: {yr_fail}')
if worse_blocks > 2:
    fail_reasons.append(f'{worse_blocks}/8 blocks worse (>2)')
if winners_kept_pct < 85.0:
    fail_reasons.append(f'winners_kept {winners_kept_pct:.1f}% < 85%')

print('\n=== VERDICT ===')
print('SURVIVES' if not fail_reasons else 'VETO: ' + '; '.join(fail_reasons))
print(json.dumps({
    'survives': not fail_reasons,
    'wr_keep': round(wr(keep), 2),
    'streak_keep': streak(keep),
    'winners_kept_pct': round(winners_kept_pct, 1),
    'losers_cut_pct': round(losers_cut_pct, 1),
    'worse_blocks': worse_blocks,
    'yr_fail': yr_fail,
}))
