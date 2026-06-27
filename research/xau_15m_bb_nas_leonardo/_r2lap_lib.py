"""Shared lib for R2 lapidation. Operates ONLY on r2_keep==1.
RAW-causal: orthogonal NEW features only. win = R>0.
"""
import json

PATH = '/Users/cristrein/tradingview-mcp/research/xau_15m_bb_nas_leonardo/dataset_r2refine.jsonl'


def load():
    rows = [json.loads(l) for l in open(PATH)]
    k = [r for r in rows if r['r2_keep'] == 1]
    k.sort(key=lambda r: r['low_t'])  # chronological by low_t
    return k


def max_losing_streak(rows):
    """rows already chronological; streak of consecutive win==0."""
    cur = mx = 0
    for r in rows:
        if r['win'] == 0:
            cur += 1
            mx = max(mx, cur)
        else:
            cur = 0
    return mx


def wr(rows):
    return 100.0 * sum(r['win'] for r in rows) / len(rows) if rows else 0.0


# per-year base WR inside r2_keep
BASE_YR = {2024: 66.05, 2025: 70.91, 2026: 65.19}
BASE_WR = 68.54


def blocks(rows):
    """split chronological rows into 8 equal-count contiguous blocks."""
    n = len(rows)
    size = n // 8
    out = []
    for i in range(8):
        lo = i * size
        hi = (i + 1) * size if i < 7 else n
        out.append(rows[lo:hi])
    return out


def evaluate(allk, mask_keep, desc):
    """mask_keep: function(row)->bool, True means KEEP the trade.
    Returns dict of metrics. allk must be chronological.
    """
    kept = [r for r in allk if mask_keep(r)]
    cut = [r for r in allk if not mask_keep(r)]
    if not kept:
        return None
    winners_total = sum(r['win'] for r in allk)
    losers_total = len(allk) - winners_total
    winners_kept = sum(r['win'] for r in kept)
    losers_kept = len(kept) - winners_kept
    winners_kept_pct = 100.0 * winners_kept / winners_total
    losers_cut_pct = 100.0 * (losers_total - losers_kept) / losers_total
    streak_before = max_losing_streak(allk)
    streak_after = max_losing_streak(kept)
    wr_keep = wr(kept)

    # per year
    yr_wr = {}
    yr_ok = {}
    for y in (2024, 2025, 2026):
        suby = [r for r in kept if r['yr'] == y]
        yr_wr[y] = wr(suby) if suby else 0.0
        yr_ok[y] = (len(suby) > 0) and (yr_wr[y] >= BASE_YR[y])

    # 8 blocks: not-worse than block base WR
    base_blocks = blocks(allk)
    kept_set = set(id(r) for r in kept)
    non_worse = 0
    block_detail = []
    for bb in base_blocks:
        base_b = wr(bb)
        kb = [r for r in bb if id(r) in kept_set]
        kw = wr(kb) if kb else 0.0
        ok = (len(kb) > 0) and (kw >= base_b)
        non_worse += 1 if ok else 0
        block_detail.append((round(base_b, 1), round(kw, 1), len(kb), ok))

    robust = (wr_keep > BASE_WR and
              yr_ok[2024] and yr_ok[2025] and yr_ok[2026] and
              winners_kept_pct >= 85.0 and
              non_worse >= 6 and
              streak_after < streak_before)

    return {
        'desc': desc,
        'n_keep': len(kept),
        'wr_keep': round(wr_keep, 2),
        'streak_before': streak_before,
        'streak_keep': streak_after,
        'winners_kept_pct': round(winners_kept_pct, 1),
        'losers_cut_pct': round(losers_cut_pct, 1),
        'y24': round(yr_wr[2024], 2),
        'y25': round(yr_wr[2025], 2),
        'y26': round(yr_wr[2026], 2),
        'yr_ok': yr_ok,
        'non_worse': non_worse,
        'blocks': block_detail,
        'robust': robust,
    }


def report(m):
    if m is None:
        print('  (empty keep set)')
        return
    print(f"  {m['desc']}")
    print(f"    n_keep={m['n_keep']} wr_keep={m['wr_keep']} streak {m['streak_before']}->{m['streak_keep']} "
          f"win_kept%={m['winners_kept_pct']} los_cut%={m['losers_cut_pct']}")
    print(f"    yr: 24={m['y24']}(b66.05) 25={m['y25']}(b70.91) 26={m['y26']}(b65.19) "
          f"ok={m['yr_ok']} blocks_nonworse={m['non_worse']}/8 ROBUST={m['robust']}")
