"""Shared lib for 8ATR confirmation-entry loser-cut discovery.
RAW-causal: all features as-of bar of confirmation. win = R>0.
Rule = boolean KEEP mask over rows (True = keep/take trade).
Reports n_keep, wr_keep, max-losing-streak (ordered by low_t),
winners_kept_pct, losers_cut_pct, WR per year.
"""
import json

PATH = "/Users/cristrein/tradingview-mcp/research/xau_15m_bb_nas_leonardo/dataset_8atr.jsonl"


def load():
    rows = [json.loads(l) for l in open(PATH)]
    rows.sort(key=lambda r: r["low_t"])  # chronological for streak
    return rows


def max_losing_streak(rows_subset):
    """rows_subset already ordered by low_t; streak of consecutive R<=0 (win==0)."""
    mx = cur = 0
    for r in rows_subset:
        if r["win"] == 0:
            cur += 1
            mx = max(mx, cur)
        else:
            cur = 0
    return mx


def base_stats(rows):
    n = len(rows)
    w = sum(r["win"] for r in rows)
    return n, w, w / n, max_losing_streak(rows)


def eval_rule(rows, keep_fn, desc=""):
    """keep_fn(r)->bool. Returns dict of metrics. rows must be low_t-sorted."""
    kept = [r for r in rows if keep_fn(r)]
    n_all = len(rows)
    w_all = sum(r["win"] for r in rows)
    l_all = n_all - w_all
    n_keep = len(kept)
    if n_keep == 0:
        return None
    w_keep = sum(r["win"] for r in kept)
    wr_keep = w_keep / n_keep
    streak_keep = max_losing_streak(kept)
    winners_kept = w_keep / w_all if w_all else 0
    losers_cut = (l_all - (n_keep - w_keep)) / l_all if l_all else 0
    # per year
    yr = {}
    for y in (2024, 2025, 2026):
        ky = [r for r in kept if r["yr"] == y]
        ay = [r for r in rows if r["yr"] == y]
        if ky:
            yr[y] = (sum(r["win"] for r in ky) / len(ky), len(ky),
                     sum(r["win"] for r in ay) / len(ay) if ay else None)
        else:
            yr[y] = (None, 0, None)
    # per block
    blk = {}
    for b in sorted(set(r["block"] for r in rows)):
        kb = [r for r in kept if r["block"] == b]
        if kb:
            blk[b] = (sum(r["win"] for r in kb) / len(kb), len(kb))
        else:
            blk[b] = (None, 0)
    return {
        "desc": desc, "n_keep": n_keep, "wr_keep": round(wr_keep, 4),
        "streak_keep": streak_keep,
        "winners_kept_pct": round(winners_kept, 4),
        "losers_cut_pct": round(losers_cut, 4),
        "yr": {y: (round(v[0], 3) if v[0] is not None else None, v[1],
                   round(v[2], 3) if v[2] is not None else None) for y, v in yr.items()},
        "blk": {b: (round(v[0], 3) if v[0] is not None else None, v[1]) for b, v in blk.items()},
    }


def print_rule(m):
    if m is None:
        print("  (empty keep set)")
        return
    print(f"  {m['desc']}")
    print(f"    n_keep={m['n_keep']} wr_keep={m['wr_keep']} streak_keep={m['streak_keep']} "
          f"winners_kept={m['winners_kept_pct']} losers_cut={m['losers_cut_pct']}")
    print(f"    yr: 24={m['yr'][2024]} 25={m['yr'][2025]} 26={m['yr'][2026]}")
    nb_ge = sum(1 for v in m['blk'].values() if v[0] is not None and v[0] > 0.6612)
    nb_have = sum(1 for v in m['blk'].values() if v[0] is not None)
    print(f"    blocks>base: {nb_ge}/{nb_have}  detail={m['blk']}")


if __name__ == "__main__":
    rows = load()
    n, w, wr, st = base_stats(rows)
    print(f"BASE n={n} wins={w} WR={wr:.4f} max_losing_streak={st}")
    for y in (2024, 2025, 2026):
        ay = [r for r in rows if r["yr"] == y]
        print(f"  {y}: n={len(ay)} WR={sum(r['win'] for r in ay)/len(ay):.4f}")
