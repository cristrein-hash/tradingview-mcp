#!/usr/bin/env python3
"""
_reopt5_loserdense.py — find LOSER-DENSE intersections to CUT (preserve >=85% winners).
Strategy: instead of keep-filters (drop too many winners), build CUT predicates that
remove pockets with WR << base. Combine 2-3 conditions to isolate pockets that are
loser-dense (low WR) AND small in winner-count so winners_kept stays high.
MULTI-TF R2 lens: loser pocket = 15M no drive + HTF range/topo/down.
Then assemble best CUT-stack and run full robustness (per-year, per-block, streak).
"""
import json

ROWS = [json.loads(l) for l in open('dataset_5atr.jsonl')]
N = len(ROWS)
BASE_WR = sum(r['win'] for r in ROWS) / N
TOT_WIN = sum(r['win'] for r in ROWS)
TOT_LOSE = N - TOT_WIN
YEARS = sorted(set(r['yr'] for r in ROWS))
BLOCKS = sorted(set(r['block'] for r in ROWS))
YEAR_BASE = {yr: sum(x['win'] for x in ROWS if x['yr'] == yr) /
             sum(1 for x in ROWS if x['yr'] == yr) for yr in YEARS}
BLOCK_BASE = {b: sum(x['win'] for x in ROWS if x['block'] == b) /
              sum(1 for x in ROWS if x['block'] == b) for b in BLOCKS}


def pocket(pred):
    """stats for the CUT pocket (rows matching pred = removed)."""
    p = [r for r in ROWS if pred(r)]
    if not p:
        return None
    nw = sum(r['win'] for r in p)
    return dict(n=len(p), wr=nw/len(p), wins=nw, losers=len(p)-nw)


# ---- candidate loser-dense pockets (these get CUT) ----
POCKETS = [
    ("h1_down", lambda r: r['h1_trend'] == -1),
    ("h1_down & noeff", lambda r: r['h1_trend'] == -1 and r['h1_eff'] < 0.20),
    ("h1_down & pos<0.95", lambda r: r['h1_trend'] == -1 and r['h1_pos'] < 0.95),
    ("macro_bear", lambda r: r['macro_bear'] == 1),
    ("macro_bear & h1_notup", lambda r: r['macro_bear'] == 1 and r['h1_trend'] != 1),
    ("london_open", lambda r: r['is_london_open'] == 1),
    ("naslong_after_smc", lambda r: r['naslong_after_smc'] == 1),
    ("h4_range(0)", lambda r: r['h4_trend'] == 0),
    ("h4_range & h1_notup", lambda r: r['h4_trend'] == 0 and r['h1_trend'] != 1),
    ("noeff & pos<0.95", lambda r: r['h1_eff'] < 0.20 and r['h1_pos'] < 0.95),
    ("noeff & h1_notup", lambda r: r['h1_eff'] < 0.20 and r['h1_trend'] != 1),
    ("smc_bos>=2 & h1_notup", lambda r: r['smc_bos'] >= 2 and r['h1_trend'] != 1),
    ("london & h1_notup", lambda r: r['is_london_open'] == 1 and r['h1_trend'] != 1),
    ("absorption & h1_notup", lambda r: r['absorption'] == 1 and r['h1_trend'] != 1),
    ("macro_bear & noeff", lambda r: r['macro_bear'] == 1 and r['h1_eff'] < 0.20),
    ("h1_down & london", lambda r: r['h1_trend'] == -1 and r['is_london_open'] == 1),
    ("h1_down & macro_bear", lambda r: r['h1_trend'] == -1 and r['macro_bear'] == 1),
    ("noeff & pos<0.9 & notup",
     lambda r: r['h1_eff'] < 0.20 and r['h1_pos'] < 0.90 and r['h1_trend'] != 1),
    ("h1_down & noeff & pos<0.95",
     lambda r: r['h1_trend'] == -1 and r['h1_eff'] < 0.20 and r['h1_pos'] < 0.95),
]

if __name__ == '__main__':
    print(f"BASE_WR={BASE_WR:.4f} N={N} TOT_WIN={TOT_WIN} TOT_LOSE={TOT_LOSE}")
    print(f"(target: CUT pockets with low WR, few winners. Each cut winner costs winners_kept.)")
    print(f"\n{'pocket':38s} {'n':>5s} {'pocketWR':>9s} {'wins_lost':>9s} {'losers_cut':>10s} {'wk_after':>9s}")
    rows = []
    for nm, pred in POCKETS:
        ps = pocket(pred)
        if not ps:
            continue
        wk_after = (TOT_WIN - ps['wins']) / TOT_WIN
        rows.append((ps['wr'], nm, ps, wk_after))
    rows.sort()  # lowest WR pockets first = best to cut
    for wr, nm, ps, wk_after in rows:
        print(f"{nm:38s} {ps['n']:5d} {ps['wr']:9.3f} {ps['wins']:9d} "
              f"{ps['losers']:10d} {wk_after:9.3f}")
