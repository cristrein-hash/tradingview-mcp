"""_reopt5_devils_advocate.py — adversarial audit of the top 5ATR robust filters.

Audits the 4 candidate filters:
 F1 = CUT(h1_pos<=0.65)                          [R2 single]
 F2 = CUT(h1_pos<=0.65 OR naslong_after_smc==1)  [R2 + structure->flow lens]  *BEST*
 F3 = CUT(h1_pos<=0.65 OR h1_dist<=1.85)         [R2 pair, max WR robust]
 F4 = CUT(h1_pos<=0.65 OR h1_dist<=1.85 OR naslong==1)  [3-cut]

DA questions:
 (1) Look-ahead: are daily/h4 features same-bar? -> documented, see notes.
 (2) In-sample / selection: how many variations tested; is lift inside noise?
 (3) Statistical power: binomial SE of the WR lift.
 (4) Block worst-case: min block WR-delta (no empty-block masking).
 (5) Year worst margins.
 (6) Random-cut null: cut same #losers/winners at random, compare WR lift.
"""
import _reopt5_lib as L
import random
import math


def keep_F1(r): return not (r['h1_pos'] is not None and r['h1_pos'] <= 0.65)
def keep_F2(r): return not ((r['h1_pos'] is not None and r['h1_pos'] <= 0.65) or r['naslong_after_smc'] == 1)
def keep_F3(r): return not ((r['h1_pos'] is not None and r['h1_pos'] <= 0.65) or (r['h1_dist'] is not None and r['h1_dist'] <= 1.85))
def keep_F4(r): return not ((r['h1_pos'] is not None and r['h1_pos'] <= 0.65) or (r['h1_dist'] is not None and r['h1_dist'] <= 1.85) or r['naslong_after_smc'] == 1)

FILTERS = {'F1':keep_F1,'F2':keep_F2,'F3':keep_F3,'F4':keep_F4}


def block_worstcase(rows, keep):
    """min (kept_block_wr - base_block_wr); empty kept block = catastrophic (-base)."""
    import collections
    base = collections.defaultdict(list); kp = collections.defaultdict(list)
    for r in rows:
        base[r['block']].append(r)
        if keep(r): kp[r['block']].append(r)
    deltas = {}
    for b in base:
        bw = 100*sum(x['win'] for x in base[b])/len(base[b])
        kv = kp.get(b, [])
        kw = 100*sum(x['win'] for x in kv)/len(kv) if kv else 0.0
        deltas[b] = round(kw - bw, 2)
    return deltas


def random_null(rows, keep, trials=2000):
    """Null: removing the SAME count of rows at random — what WR lift do we get?
    Tests whether the lift is just 'cutting any rows' vs targeted loser-cut."""
    n_removed = sum(1 for r in rows if not keep(r))
    base_wr = 100*sum(r['win'] for r in rows)/len(rows)
    real_wr = 100*sum(r['win'] for r in rows if keep(r))/sum(1 for r in rows if keep(r))
    idx = list(range(len(rows)))
    wins = [r['win'] for r in rows]
    cnt_ge = 0
    rnd = random.Random(42)
    for _ in range(trials):
        rm = set(rnd.sample(idx, n_removed))
        kept_wins = sum(wins[i] for i in idx if i not in rm)
        kept_n = len(idx) - n_removed
        wr = 100*kept_wins/kept_n
        if wr >= real_wr:
            cnt_ge += 1
    return base_wr, real_wr, n_removed, cnt_ge/trials


def main():
    rows = L.load()
    base_wr = 100*sum(r['win'] for r in rows)/len(rows)
    print(f"BASE WR {base_wr:.2f} n={len(rows)}\n")
    print("# Selection count: univariate scanned ~48 feats x ~12 thresholds (~400 tests);")
    print("# combos: 8-rule pairs/triples (~92) + targeted stacks (~25). Bonferroni-aware.")
    print("# Power: to detect a -20% relative WR drop (60->48) at n~2700, binomial SE ~0.94pp.\n")

    for name, keep in FILTERS.items():
        kept = [r for r in rows if keep(r)]
        n = len(kept)
        wr = 100*sum(r['win'] for r in kept)/n
        # binomial SE of difference (independent approx)
        p1, n1 = wr/100, n
        p0, n0 = base_wr/100, len(rows)
        se = math.sqrt(p1*(1-p1)/n1 + p0*(1-p0)/n0)
        z = (p1-p0)/se if se else 0
        dws = block_worstcase(rows, keep)
        worst_b = min(dws.items(), key=lambda kv: kv[1])
        b_wr, r_wr, nrm, pval = random_null(rows, keep)
        print(f"=== {name} ===")
        print(f"  n_keep={n} WR={wr:.2f} lift={wr-base_wr:+.2f}pp  z={z:.2f}")
        print(f"  worst block delta: {worst_b[0]} {worst_b[1]:+.2f}pp ; all={dws}")
        print(f"  random-null (same #removed={nrm}): P(random WR >= real {r_wr:.2f}) = {pval:.3f}")
        print()


if __name__ == '__main__':
    main()
