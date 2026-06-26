#!/usr/bin/env python3
"""
_disc8_context_combo.py — Discovery part 2 on dataset_8atr.jsonl.
Pivot from naive vol lens: univariate showed losers cluster in FAST legs
(bars_to_8atr low), low macro_retr, and at/below-POC entries. Winners cluster
in slow-grind legs (high bars_to_8atr), high macro_retr (deep pullback already
recovered), extended above POC.

LENS REINTERPRETED (vol/volume CONTEXTUAL): the 8ATR move is CONFIRMATION. A move
that reached 8ATR SLOWLY (grind, many bars) while volatility was contained is an
ACCEPTED move (continuation). A move that spiked to 8ATR FAST in low-vol then is
at/below POC = exhaustion spike = loser. So combine:
  - bars_to_8atr (acceptance time)
  - macro_retr (depth of pullback recovered)
  - vpnode_dist / vol context

robust=True only if WR>base AND >=base each year AND winners_kept>=0.85.
RULES: win=R>0, no R/win as feature, chronological streak.
"""
import json

ROWS = [json.loads(l) for l in open('dataset_8atr.jsonl')]
ROWS.sort(key=lambda r: r['low_t'])
N = len(ROWS)
BASE_WR = sum(r['win'] for r in ROWS) / N
TOT_WIN = sum(r['win'] for r in ROWS)
TOT_LOSS = N - TOT_WIN
YR_BASE = {}
for y in (2024, 2025, 2026):
    sub = [r for r in ROWS if r['yr'] == y]
    YR_BASE[y] = sum(x['win'] for x in sub) / len(sub)

def max_losing_streak(rows):
    mx = cur = 0
    for r in rows:
        if r['win'] == 0:
            cur += 1; mx = max(mx, cur)
        else:
            cur = 0
    return mx

BASE_STREAK = max_losing_streak(ROWS)

def evaluate(name, pred):
    keep = [r for r in ROWS if pred(r)]
    if len(keep) < 50:
        return None
    nk = len(keep); wk = sum(r['win'] for r in keep); wr = wk / nk
    streak = max_losing_streak(keep)
    winners_kept = wk / TOT_WIN
    losers_cut = (TOT_LOSS - (nk - wk)) / TOT_LOSS
    yrwr = {}
    for y in (2024, 2025, 2026):
        sub = [r for r in keep if r['yr'] == y]
        yrwr[y] = (sum(x['win'] for x in sub) / len(sub)) if sub else None
    robust = (wr > BASE_WR and winners_kept >= 0.85
              and all(yrwr[y] is not None and yrwr[y] >= YR_BASE[y] for y in (2024, 2025, 2026)))
    return dict(name=name, n_keep=nk, wr_keep=round(wr, 4), streak_keep=streak,
                winners_kept_pct=round(winners_kept, 4), losers_cut_pct=round(losers_cut, 4),
                y24=round(yrwr[2024], 4), y25=round(yrwr[2025], 4), y26=round(yrwr[2026], 4),
                robust=robust)

RESULTS = []
def test(name, pred):
    r = evaluate(name, pred)
    if r: RESULTS.append(r)

# helper to treat null HTF as "unknown" -> default pass unless cond needs it
def hd(r, k, default=None):
    v = r.get(k); return default if v is None else v

print(f"N={N} BASE_WR={BASE_WR:.4f} BASE_STREAK={BASE_STREAK} "
      f"YR_BASE={ {y: round(v,3) for y,v in YR_BASE.items()} }")

# ---- acceptance-time + pullback-depth combos ----
test("bars_to_8atr>=60", lambda r: r['bars_to_8atr'] >= 60)
test("bars_to_8atr>=100", lambda r: r['bars_to_8atr'] >= 100)
test("macro_retr>=1.1", lambda r: r['macro_retr'] >= 1.1)
test("macro_retr>=1.0", lambda r: r['macro_retr'] >= 1.0)
test("bars_to_8atr>=60 OR macro_retr>=1.1",
     lambda r: r['bars_to_8atr'] >= 60 or r['macro_retr'] >= 1.1)
test("CUT(bars<31 & macro_retr<1.0)",
     lambda r: not (r['bars_to_8atr'] < 31 and r['macro_retr'] < 1.0))
test("CUT(bars<31 & vpnode<=2)",
     lambda r: not (r['bars_to_8atr'] < 31 and r['vpnode_dist_atr'] <= 2.0))
test("CUT(bars<31 & path_eff>0.6)",  # fast steep spike = exhaustion
     lambda r: not (r['bars_to_8atr'] < 31 and r['path_eff'] > 0.6))
test("CUT(bars<31)", lambda r: r['bars_to_8atr'] >= 31)

# ---- vol/volume contextual: low-vol acceptance + above POC + recovered ----
test("vpnode>2 & macro_retr>=1.0",
     lambda r: r['vpnode_dist_atr'] > 2.0 and r['macro_retr'] >= 1.0)
test("vpnode>2 & bars_to_8atr>=50",
     lambda r: r['vpnode_dist_atr'] > 2.0 and r['bars_to_8atr'] >= 50)
test("vpnode>3 & vol_low_vs_med<1.5",  # extended but vol contained = accepted
     lambda r: r['vpnode_dist_atr'] > 3.0 and r['vol_low_vs_med'] < 1.5)
test("CUT(vol_climax>1.5 & vpnode<=2)",  # climax spike not yet above POC = blowoff
     lambda r: not (r['vol_climax'] > 1.5 and r['vpnode_dist_atr'] <= 2.0))

# ---- HTF position contextual ----
test("h1_pos>=1.05", lambda r: r['h1_pos'] >= 1.05)
test("CUT(h1_pos<1.0)", lambda r: r['h1_pos'] >= 1.0)
test("rsi in [62,76]", lambda r: 62 <= r['rsi'] <= 76)
test("CUT(rsi>78)", lambda r: r['rsi'] <= 78)
test("h1_eff>=0.2", lambda r: r['h1_eff'] >= 0.2)

# ---- 2-3 feat contextual reads ----
test("macro_retr>=1.1 & h1_pos>=1.05",
     lambda r: r['macro_retr'] >= 1.1 and r['h1_pos'] >= 1.05)
test("bars_to_8atr>=60 & h1_eff>=0.2",
     lambda r: r['bars_to_8atr'] >= 60 and r['h1_eff'] >= 0.2)
test("CUT(bars<31 & macro_retr<1.0 & path_eff>0.5)",
     lambda r: not (r['bars_to_8atr'] < 31 and r['macro_retr'] < 1.0 and r['path_eff'] > 0.5))
test("macro_retr>=1.0 & rsi<=78 & h1_eff>=0.2",
     lambda r: r['macro_retr'] >= 1.0 and r['rsi'] <= 78 and r['h1_eff'] >= 0.2)
# slow-acceptance loser cut combined
test("CUT(bars<31 & h1_pos<1.0)",
     lambda r: not (r['bars_to_8atr'] < 31 and r['h1_pos'] < 1.0))
test("CUT(bars<31 & vpnode<=0)",
     lambda r: not (r['bars_to_8atr'] < 31 and r['vpnode_dist_atr'] <= 0.0))

RESULTS.sort(key=lambda x: (-x['wr_keep'], -x['n_keep']))
print("\nwr    nk   strk wk%   lc%   y24   y25   y26  rob name")
for r in RESULTS:
    print(f"{r['wr_keep']:.3f} {r['n_keep']:4d} {r['streak_keep']:4d} "
          f"{r['winners_kept_pct']:.2f}  {r['losers_cut_pct']:.2f}  "
          f"{r['y24']:.2f}  {r['y25']:.2f}  {r['y26']:.2f}  "
          f"{'Y' if r['robust'] else '.'}  {r['name']}")
