#!/usr/bin/env python3
"""
_reopt5_multitf.py — MULTI-TF combo optimizer for 5ATR dataset (R2 axis re-derived).
Base: n=3047, WR 60.5%, no dedup. win=R>0.
R2 axis = "15M has drive (h1_eff/pos) + HTF not range/topo + not macro_bear".
We define KEEP filters (and optional CUT-when-loser-dense). Evaluate each combo:
  n_keep, wr_keep, winners_kept_pct, losers_cut_pct, streak before/after,
  WR per year (2024/25/26), per-block non-worse count.
robust=True iff: wr_keep>BASE & wr_keep>=each year base & winners_kept>=85%
                 & >=6/8 blocks non-worse (block WR_keep >= block base - eps).
PROIBIDO: R/win/cj/low_idx as feature.
"""
import json

ROWS = [json.loads(l) for l in open('dataset_5atr.jsonl')]
N = len(ROWS)
BASE_WR = sum(r['win'] for r in ROWS) / N
TOT_WIN = sum(r['win'] for r in ROWS)
YEARS = sorted(set(r['yr'] for r in ROWS))
BLOCKS = sorted(set(r['block'] for r in ROWS))
YEAR_BASE = {yr: sum(x['win'] for x in ROWS if x['yr'] == yr) /
             sum(1 for x in ROWS if x['yr'] == yr) for yr in YEARS}
BLOCK_BASE = {b: sum(x['win'] for x in ROWS if x['block'] == b) /
              sum(1 for x in ROWS if x['block'] == b) for b in BLOCKS}
EPS = 0.005  # block tolerance: "non-worse" if keep WR >= base - EPS


def max_losing_streak(rows):
    """rows ordered by low_t; longest run of consecutive losers."""
    rs = sorted(rows, key=lambda r: r['low_t'])
    best = cur = 0
    for r in rs:
        if r['win'] == 0:
            cur += 1
            best = max(best, cur)
        else:
            cur = 0
    return best


def evaluate(name, predicate, desc=''):
    keep = [r for r in ROWS if predicate(r)]
    cut = [r for r in ROWS if not predicate(r)]
    nk = len(keep)
    if nk == 0:
        return None
    wk = sum(r['win'] for r in keep)
    wr = wk / nk
    winners_kept = wk / TOT_WIN
    losers_total = N - TOT_WIN
    losers_cut = sum(1 for r in cut if r['win'] == 0)
    losers_cut_pct = losers_cut / losers_total
    streak_before = max_losing_streak(ROWS)
    streak_after = max_losing_streak(keep)
    # per year
    yr_wr = {}
    for yr in YEARS:
        sub = [r for r in keep if r['yr'] == yr]
        yr_wr[yr] = (sum(x['win'] for x in sub) / len(sub)) if sub else 0.0
    # per block non-worse
    blk_ok = 0
    blk_detail = {}
    for b in BLOCKS:
        sub = [r for r in keep if r['block'] == b]
        bw = (sum(x['win'] for x in sub) / len(sub)) if sub else 0.0
        blk_detail[b] = (bw, len(sub))
        if sub and bw >= BLOCK_BASE[b] - EPS:
            blk_ok += 1
    robust = (wr > BASE_WR and
              all(yr_wr[yr] >= YEAR_BASE[yr] for yr in YEARS) and
              winners_kept >= 0.85 and
              blk_ok >= 6)
    return dict(name=name, desc=desc, n_keep=nk, wr_keep=round(wr, 4),
                winners_kept_pct=round(winners_kept, 4),
                losers_cut_pct=round(losers_cut_pct, 4),
                streak_before=streak_before, streak_after=streak_after,
                y24=round(yr_wr[2024], 4), y25=round(yr_wr[2025], 4),
                y26=round(yr_wr[2026], 4), blk_ok=blk_ok,
                blk_detail={k: (round(v[0], 3), v[1]) for k, v in blk_detail.items()},
                robust=robust)


def pr(res):
    if not res:
        print("  (empty)")
        return
    print(f"\n### {res['name']}  {res['desc']}")
    print(f"  n_keep={res['n_keep']} wr_keep={res['wr_keep']} (base {BASE_WR:.4f})")
    print(f"  winners_kept={res['winners_kept_pct']:.3f} losers_cut={res['losers_cut_pct']:.3f}")
    print(f"  streak {res['streak_before']}->{res['streak_after']}")
    print(f"  Y24={res['y24']} (b{YEAR_BASE[2024]:.3f}) "
          f"Y25={res['y25']} (b{YEAR_BASE[2025]:.3f}) "
          f"Y26={res['y26']} (b{YEAR_BASE[2026]:.3f})")
    print(f"  blocks non-worse {res['blk_ok']}/8")
    for b in BLOCKS:
        bw, bn = res['blk_detail'][b]
        mark = 'OK ' if bw >= BLOCK_BASE[b] - EPS and bn > 0 else '<<<'
        print(f"     {b} keepWR={bw:.3f} n={bn:3d} base={BLOCK_BASE[b]:.3f} {mark}")
    print(f"  ROBUST={res['robust']}")


# ---- predicates ----
def f(r, k):
    return r[k]


CANDIDATES = [
    # singles
    ("h1_trend_up", lambda r: r['h1_trend'] == 1, "15M HTF(h1) uptrend"),
    ("h1_eff_ge02", lambda r: r['h1_eff'] >= 0.20, "15M has directional drive"),
    ("h1_pos_ge095", lambda r: r['h1_pos'] >= 0.95, "price holding above h1 mid"),
    ("not_macro_bear", lambda r: r['macro_bear'] == 0, "not macro bear leg"),
    ("hd_eff_ge012", lambda r: r['hd_eff'] is not None and r['hd_eff'] >= 0.12, "daily has drive"),
    # CUT-when-loser-dense: cut h1 down OR macro_bear
    ("cut_h1down_or_bear",
     lambda r: not (r['h1_trend'] == -1 or r['macro_bear'] == 1),
     "CUT 15M-htf-down OR macro-bear"),
    # 2-combos
    ("h1up_AND_eff02",
     lambda r: r['h1_trend'] == 1 and r['h1_eff'] >= 0.20,
     "h1 uptrend + drive"),
    ("h1up_AND_pos095",
     lambda r: r['h1_trend'] == 1 and r['h1_pos'] >= 0.95,
     "h1 uptrend + holding mid"),
    ("drive_AND_notbear",
     lambda r: r['h1_eff'] >= 0.20 and r['macro_bear'] == 0,
     "drive + not macro bear"),
    ("h1up_AND_notbear",
     lambda r: r['h1_trend'] == 1 and r['macro_bear'] == 0,
     "h1 up + not macro bear"),
    ("pos095_AND_notbear",
     lambda r: r['h1_pos'] >= 0.95 and r['macro_bear'] == 0,
     "holding mid + not bear"),
    # CUT combos: cut loser-dense region (h1 down OR macro_bear OR london_open)
    ("cut_down_bear_london",
     lambda r: not (r['h1_trend'] == -1 or r['macro_bear'] == 1 or r['is_london_open'] == 1),
     "CUT down|bear|london"),
    # 3-combos
    ("h1up_drive_notbear",
     lambda r: r['h1_trend'] == 1 and r['h1_eff'] >= 0.20 and r['macro_bear'] == 0,
     "h1 up + drive + not bear"),
    ("h1up_pos_notbear",
     lambda r: r['h1_trend'] == 1 and r['h1_pos'] >= 0.95 and r['macro_bear'] == 0,
     "h1 up + holding + not bear"),
    # CUT 3-combo (keep everything except the loser-dense intersection)
    ("cut_loserdense3",
     lambda r: not (r['h1_trend'] == -1 and r['h1_eff'] < 0.20),
     "CUT (h1 down AND no drive)"),
]

if __name__ == '__main__':
    print(f"BASE_WR={BASE_WR:.4f} N={N}  YEAR_BASE={ {k:round(v,4) for k,v in YEAR_BASE.items()} }")
    print(f"BLOCK_BASE={ {k:round(v,3) for k,v in BLOCK_BASE.items()} }")
    results = []
    for nm, pred, desc in CANDIDATES:
        res = evaluate(nm, pred, desc)
        results.append(res)
        pr(res)
    print("\n\n===== ROBUST SUMMARY (winners_kept>=85% required) =====")
    for res in results:
        if res:
            print(f"  {res['name']:22s} wr={res['wr_keep']:.4f} wk={res['winners_kept_pct']:.3f} "
                  f"blk={res['blk_ok']}/8 streak{res['streak_before']}->{res['streak_after']} "
                  f"ROBUST={res['robust']}")
