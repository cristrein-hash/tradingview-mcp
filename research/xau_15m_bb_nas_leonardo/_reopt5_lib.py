"""Re-optimize 5ATR-confirm selection filters. Shared library.

Base = candidatos 5ATR-confirm (mínima fractal, entry no bar do 5ATR,
SL=flush-0.1ATR, EXIT=let-run), SEM dedup: n=3047, WR base=60.5%, avgR +0.30.
win = R>0.

PROIBIDO usar R/win/cj/low_idx como feature.
Objetivo: STACK de filtros (1-3 combos, podem ser CUT-when-loser-dense) que
SUBA o WR acima de 60.5% com ESTABILIDADE:
  - wr_keep > 60.5
  - >= base-de-cada-ano em cada 2024/2025/2026
  - winners_kept >= 85%
  - >= 6/8 blocos nao-piores
  - reduzir max-losing-streak
"""
import json
import collections

PATH = "/Users/cristrein/tradingview-mcp/research/xau_15m_bb_nas_leonardo/dataset_5atr.jsonl"

FORBIDDEN = {"R", "win", "cj", "low_idx", "block", "low_t", "yr"}

YEAR_BASE = {2024: 58.77, 2025: 63.47, 2026: 54.83}
BASE_WR = 60.49

# per-block base WR (for non-worse test)
BLOCK_BASE = {
    "2024-05-25": 59.80, "2024-08-25": 60.36, "2024-11-25": 62.66,
    "2025-02-25": 61.87, "2025-05-25": 53.64, "2025-08-25": 70.15,
    "2025-11-25": 64.52, "2026-02-25": 47.59,
}
BLOCK_ORDER = sorted(BLOCK_BASE.keys())


def load():
    rows = [json.loads(l) for l in open(PATH)]
    # keep original time order for streak computation
    rows.sort(key=lambda r: r["low_t"])
    return rows


def max_losing_streak(rows):
    """rows in time order; max consecutive losers (win==0)."""
    mx = 0
    cur = 0
    for r in rows:
        if r["win"] == 0:
            cur += 1
            mx = max(mx, cur)
        else:
            cur = 0
    return mx


def metrics(kept, allrows):
    """Compute full metric set for a kept subset vs all."""
    n = len(kept)
    if n == 0:
        return None
    wins_all = sum(r["win"] for r in allrows)
    losers_all = len(allrows) - wins_all
    wins_keep = sum(r["win"] for r in kept)
    losers_keep = n - wins_keep
    wr_keep = 100.0 * wins_keep / n
    winners_kept_pct = 100.0 * wins_keep / wins_all if wins_all else 0
    losers_cut_pct = 100.0 * (losers_all - losers_keep) / losers_all if losers_all else 0
    avgR = sum(r["R"] for r in kept) / n
    sumR = sum(r["R"] for r in kept)
    streak = max_losing_streak(kept)
    streak_base = max_losing_streak(allrows)

    # per year
    by_year = {}
    for yr in (2024, 2025, 2026):
        sub = [r for r in kept if r["yr"] == yr]
        by_year[yr] = round(100.0 * sum(r["win"] for r in sub) / len(sub), 2) if sub else None

    # per block non-worse
    blocks_ok = 0
    block_detail = {}
    for b in BLOCK_ORDER:
        sub = [r for r in kept if r["block"] == b]
        if sub:
            wr = 100.0 * sum(r["win"] for r in sub) / len(sub)
            block_detail[b] = (len(sub), round(wr, 1))
            if wr >= BLOCK_BASE[b] - 0.001:
                blocks_ok += 1
        else:
            block_detail[b] = (0, None)
            # empty block: cannot be "worse" but contributes nothing; count as not-worse only if we keep some?
            # Convention: empty block = not-worse (no losers there). But that hides coverage loss.
            blocks_ok += 1

    return {
        "n_keep": n,
        "wr_keep": round(wr_keep, 2),
        "avgR": round(avgR, 3),
        "sumR": round(sumR, 1),
        "streak_keep": streak,
        "streak_base": streak_base,
        "winners_kept_pct": round(winners_kept_pct, 1),
        "losers_cut_pct": round(losers_cut_pct, 1),
        "by_year": by_year,
        "blocks_ok": blocks_ok,
        "block_detail": block_detail,
    }


def is_robust(m):
    if m is None:
        return False
    if m["wr_keep"] <= BASE_WR:
        return False
    for yr in (2024, 2025, 2026):
        if m["by_year"][yr] is None or m["by_year"][yr] < YEAR_BASE[yr]:
            return False
    if m["winners_kept_pct"] < 85.0:
        return False
    if m["blocks_ok"] < 6:
        return False
    return True


def report(name, kept, allrows):
    m = metrics(kept, allrows)
    print("=" * 70)
    print(name)
    if m is None:
        print("  EMPTY")
        return None
    rob = is_robust(m)
    print(f"  n_keep={m['n_keep']} wr_keep={m['wr_keep']} (base {BASE_WR}) "
          f"avgR={m['avgR']} sumR={m['sumR']}")
    print(f"  streak {m['streak_base']} -> {m['streak_keep']}")
    print(f"  winners_kept={m['winners_kept_pct']}%  losers_cut={m['losers_cut_pct']}%")
    print(f"  by_year={m['by_year']}  (base {YEAR_BASE})")
    print(f"  blocks_ok={m['blocks_ok']}/8")
    print(f"  block_detail={m['block_detail']}")
    print(f"  ROBUST={rob}")
    m["robust"] = rob
    m["name"] = name
    return m
