#!/usr/bin/env python3
"""
Adversarial verification of entry rule:
    macro_bull==1 AND smc_bos==1
on entry_dataset.jsonl (reclaim-anchored 15M dataset).

Checks (per Cris regua):
  - re-run rule, confirm reported n/WR/avgR
  - avgR per YEAR (sign stability)
  - leave-one-BLOCK-out avgR (worst fold; must beat base)
  - ex-top1 / ex-top2 / ex-top3 (tail dependence)
  - multiple-testing skepticism: how many simple 2-feature rules beat this?
R field = R_reclaim. No look-ahead audit of features here beyond flagging
near_M8/held8/runner/R_8atr as outcome-derived (must NOT be in the rule).
"""
import json
from collections import defaultdict, Counter

ROWS = [json.loads(l) for l in open('entry_dataset.jsonl')]
RKEY = 'R_reclaim'

def avg(xs):
    return sum(xs) / len(xs) if xs else float('nan')

def stats(sub):
    rs = [r[RKEY] for r in sub]
    wins = sum(1 for r in sub if r[RKEY] > 0)
    return dict(n=len(sub), wr=wins/len(sub) if sub else float('nan'),
                avgR=avg(rs), sumR=sum(rs))

def rule_mask(r):
    return r.get('macro_bull') == 1 and r.get('smc_bos') == 1

def main():
    base = stats(ROWS)
    sel = [r for r in ROWS if rule_mask(r)]
    s = stats(sel)
    print('=== BASE (all rows) ===')
    print(f"n={base['n']} WR={base['wr']:.3f} avgR={base['avgR']:.3f} sumR={base['sumR']:.1f}")
    print('=== RULE macro_bull==1 AND smc_bos==1 ===')
    print(f"n={s['n']} WR={s['wr']:.3f} avgR={s['avgR']:.3f} sumR={s['sumR']:.1f}")
    print(f"lift avgR vs base: {s['avgR']-base['avgR']:+.3f}")

    # --- per year ---
    print('\n=== PER YEAR ===')
    peryear = defaultdict(list)
    for r in sel:
        peryear[r['yr']].append(r)
    yrok = True
    yr_avgs = {}
    for yr in sorted(peryear):
        st = stats(peryear[yr])
        yr_avgs[yr] = st['avgR']
        print(f"  {yr}: n={st['n']:3d} WR={st['wr']:.3f} avgR={st['avgR']:+.3f} sumR={st['sumR']:+.1f}")
    # sign stability: all years same sign (positive)?
    signs = set((1 if v > 0 else (-1 if v < 0 else 0)) for v in yr_avgs.values())
    yrok = (signs == {1})
    print(f"  per-year all positive (peryear_ok core): {yrok}  signs={signs}")

    # --- leave-one-block-out ---
    print('\n=== LEAVE-ONE-BLOCK-OUT (avgR of remaining selection; must beat base avgR) ===')
    blocks = sorted(set(r['block'] for r in sel))
    worst = None
    folds_beat = 0
    for b in blocks:
        rem = [r for r in sel if r['block'] != b]
        held = [r for r in sel if r['block'] == b]
        st = stats(rem)
        hst = stats(held) if held else None
        beat = st['avgR'] > base['avgR']
        folds_beat += beat
        hstr = f"heldblk n={hst['n']:3d} avgR={hst['avgR']:+.3f}" if hst else "heldblk n=0"
        print(f"  drop {b}: rem n={st['n']:3d} avgR={st['avgR']:+.3f} beat_base={beat} | {hstr}")
        if worst is None or st['avgR'] < worst:
            worst = st['avgR']
    print(f"  folds beating base: {folds_beat}/{len(blocks)}  worst-fold avgR={worst:+.3f}")

    # also per-block standalone avgR sign stability
    print('\n=== PER-BLOCK STANDALONE (sign stability) ===')
    blk_signs = set()
    blk_avgs = {}
    for b in blocks:
        held = [r for r in sel if r['block'] == b]
        st = stats(held)
        blk_avgs[b] = st['avgR']
        blk_signs.add(1 if st['avgR'] > 0 else (-1 if st['avgR'] < 0 else 0))
        print(f"  {b}: n={st['n']:3d} WR={st['wr']:.3f} avgR={st['avgR']:+.3f}")
    print(f"  per-block standalone signs: {blk_signs}")

    # --- ex-topK ---
    print('\n=== TAIL DEPENDENCE (remove top winners) ===')
    sel_sorted = sorted(sel, key=lambda r: r[RKEY], reverse=True)
    for k in (1, 2, 3, 5):
        trimmed = sel_sorted[k:]
        st = stats(trimmed)
        print(f"  ex-top{k}: n={st['n']} avgR={st['avgR']:+.3f} sumR={st['sumR']:+.1f}")
    top5 = [round(r[RKEY], 2) for r in sel_sorted[:5]]
    print(f"  top5 R values: {top5}")
    # how much of sumR is the top5?
    print(f"  top5 sumR share: {sum(sel_sorted[i][RKEY] for i in range(5))/s['sumR']*100:.1f}%")

    # --- multiple testing context: count simple AND-pairs that beat base by >=0.3 avgR with n>=150 ---
    print('\n=== MULTIPLE-TESTING CONTEXT ===')
    bin_feats = ['macro_bull', 'macro_bear', 'killzone', 'near_M8', 'runner', 'held8',
                 'sell_S', 'sell_M', 'sell_L', 'buy_S', 'buy_M', 'buy_L']
    # binary-ize smc_bos as ==1; also smc_choch==1
    def feat_ok(r, f):
        if f == 'smc_bos==1':
            return r.get('smc_bos') == 1
        if f == 'smc_choch==1':
            return r.get('smc_choch') == 1
        return r.get(f) == 1
    feats = bin_feats + ['smc_bos==1', 'smc_choch==1']
    import itertools
    beating = []
    for a, b in itertools.combinations(feats, 2):
        sub = [r for r in ROWS if feat_ok(r, a) and feat_ok(r, b)]
        if len(sub) >= 150:
            st = stats(sub)
            if st['avgR'] - base['avgR'] >= 0.3:
                beating.append((a, b, st['n'], st['avgR']))
    beating.sort(key=lambda x: -x[3])
    print(f"  # of 2-feature AND-rules (n>=150) beating base by >=0.3 avgR: {len(beating)}")
    for a, b, n, ar in beating[:12]:
        print(f"    {a} & {b}: n={n} avgR={ar:+.3f}")

    # summary verdict signals
    print('\n=== VERDICT SIGNALS ===')
    extop2 = stats(sel_sorted[2:])['avgR']
    print(f"  rule avgR={s['avgR']:+.3f} | ex-top2 avgR={extop2:+.3f} | worst-block-fold avgR={worst:+.3f}")
    print(f"  per-year ok={yrok} | folds beat base {folds_beat}/{len(blocks)} | n={s['n']}")

if __name__ == '__main__':
    main()
