#!/usr/bin/env python3
"""
_disc8_volvolume.py — Discovery on dataset_8atr.jsonl (8ATR confirmation entry).
LENS: volatility/volume. Hypothesis: losers = low-vol grind / buying-rich above
volume POC (vpnode_dist>0) without climax; winners = climax at low + expansion.

Approach: NOT lazy univariate. Test CONTEXTUAL COMBOS (2-3 features), measure:
n_keep, wr_keep, max-losing-streak (ordered by low_t) before/after, winners_kept_pct,
losers_cut_pct, and WR per year (2024/2025/2026).

robust=True only if WR(keep) > base AND WR(keep) >= base-WR in ALL 3 years AND not
carried by a few trades.

RULES: win = R>0. R/win NEVER used as a feature. RAW-causal as-of bar.
"""
import json, collections

ROWS = [json.loads(l) for l in open('dataset_8atr.jsonl')]
ROWS.sort(key=lambda r: r['low_t'])  # chronological for streak
N = len(ROWS)
BASE_WR = sum(r['win'] for r in ROWS) / N
TOT_WIN = sum(r['win'] for r in ROWS)
TOT_LOSS = N - TOT_WIN
YR_BASE = {}
for y in (2024, 2025, 2026):
    sub = [r for r in ROWS if r['yr'] == y]
    YR_BASE[y] = sum(x['win'] for x in sub) / len(sub)

def max_losing_streak(rows):
    """rows must be chronological. streak of consecutive losers."""
    mx = cur = 0
    for r in rows:
        if r['win'] == 0:
            cur += 1; mx = max(mx, cur)
        else:
            cur = 0
    return mx

BASE_STREAK = max_losing_streak(ROWS)

def g(r, k):
    return r.get(k)

def evaluate(name, pred):
    """pred(r)->bool means KEEP the trade. Trades failing pred are CUT."""
    keep = [r for r in ROWS if pred(r)]
    if not keep:
        return None
    nk = len(keep)
    wk = sum(r['win'] for r in keep)
    wr = wk / nk
    streak = max_losing_streak(keep)  # keep already chronological (ROWS sorted)
    winners_kept = wk / TOT_WIN
    losers_cut = (TOT_LOSS - (nk - wk)) / TOT_LOSS
    yrwr = {}
    for y in (2024, 2025, 2026):
        sub = [r for r in keep if r['yr'] == y]
        yrwr[y] = (sum(x['win'] for x in sub) / len(sub)) if sub else None
    # robustness: WR up overall AND >= base each year AND winners_kept>=0.85
    robust = (wr > BASE_WR
              and winners_kept >= 0.85
              and all(yrwr[y] is not None and yrwr[y] >= YR_BASE[y] for y in (2024, 2025, 2026)))
    return dict(name=name, n_keep=nk, wr_keep=round(wr, 4), streak_keep=streak,
                winners_kept_pct=round(winners_kept, 4), losers_cut_pct=round(losers_cut, 4),
                y24=round(yrwr[2024], 4) if yrwr[2024] is not None else None,
                y25=round(yrwr[2025], 4) if yrwr[2025] is not None else None,
                y26=round(yrwr[2026], 4) if yrwr[2026] is not None else None,
                robust=robust)

print(f"N={N} BASE_WR={BASE_WR:.4f} BASE_STREAK={BASE_STREAK}")
print(f"TOT_WIN={TOT_WIN} TOT_LOSS={TOT_LOSS}")
print(f"YR_BASE={ {y: round(v,4) for y,v in YR_BASE.items()} }")
print("="*100)

# ------------------------------------------------------------------
# Step 1: univariate WR by quantile bins for vol/volume features (sanity of lens)
# ------------------------------------------------------------------
def quant_report(key):
    vals = [(g(r, key), r['win']) for r in ROWS if g(r, key) is not None]
    vals_sorted = sorted(vals, key=lambda x: x[0])
    n = len(vals_sorted)
    print(f"\n--- {key} (n={n}) quintiles ---")
    for q in range(5):
        a = q * n // 5; b = (q + 1) * n // 5
        seg = vals_sorted[a:b]
        wr = sum(x[1] for x in seg) / len(seg)
        print(f"  Q{q+1} [{seg[0][0]:.2f},{seg[-1][0]:.2f}] wr={wr:.3f}")

for k in ['atr_regime', 'atr_expand', 'vol_low_vs_med', 'vol_climax',
          'vpnode_dist_atr', 'path_eff', 'macro_retr', 'rsi', 'rsi_low',
          'h1_pos', 'h1_eff', 'dist_supply_atr', 'disp4_atr', 'bars_to_8atr']:
    quant_report(k)

RESULTS = []

def test(name, pred):
    r = evaluate(name, pred)
    if r is None:
        return
    RESULTS.append(r)

# ------------------------------------------------------------------
# Step 2: lens-driven CONTEXTUAL COMBOS
# vpnode_dist_atr: close vs POC volume. >0 = above POC (buying rich).
# vol_climax: high = climax. atr_expand: >1 expanding. path_eff: impulse vs grind.
# ------------------------------------------------------------------
# A. Cut "buying rich above POC in low-vol grind without climax"
test("KEEP vpnode<=2 (not far above POC)", lambda r: r['vpnode_dist_atr'] <= 2.0)
test("KEEP vpnode<=1", lambda r: r['vpnode_dist_atr'] <= 1.0)
test("KEEP vpnode<=0 (at/below POC)", lambda r: r['vpnode_dist_atr'] <= 0.0)
test("KEEP path_eff>=0.5 (impulse not grind)", lambda r: r['path_eff'] >= 0.5)
test("KEEP path_eff>=0.4", lambda r: r['path_eff'] >= 0.4)
test("KEEP atr_expand>=1", lambda r: r['atr_expand'] >= 1.0)
test("KEEP vol_climax>=1.2", lambda r: r['vol_climax'] >= 1.2)
test("KEEP atr_regime>=1", lambda r: r['atr_regime'] >= 1.0)

# COMBO 2-feat: vpnode + path_eff
test("vpnode<=2 & path_eff>=0.4", lambda r: r['vpnode_dist_atr'] <= 2.0 and r['path_eff'] >= 0.4)
test("vpnode<=1 & path_eff>=0.4", lambda r: r['vpnode_dist_atr'] <= 1.0 and r['path_eff'] >= 0.4)
test("vpnode<=2 & atr_expand>=1", lambda r: r['vpnode_dist_atr'] <= 2.0 and r['atr_expand'] >= 1.0)
test("vpnode<=2 & vol_climax>=1", lambda r: r['vpnode_dist_atr'] <= 2.0 and r['vol_climax'] >= 1.0)
test("path_eff>=0.4 & atr_expand>=1", lambda r: r['path_eff'] >= 0.4 and r['atr_expand'] >= 1.0)
test("path_eff>=0.4 & vol_climax>=1", lambda r: r['path_eff'] >= 0.4 and r['vol_climax'] >= 1.0)
# CUT grind: low path_eff AND low vol => grind no-climax
test("NOT(path_eff<0.3 & vol_climax<1)", lambda r: not (r['path_eff'] < 0.3 and r['vol_climax'] < 1.0))
test("NOT(path_eff<0.4 & vpnode>2)", lambda r: not (r['path_eff'] < 0.4 and r['vpnode_dist_atr'] > 2.0))

# COMBO 3-feat
test("vpnode<=2 & path_eff>=0.4 & atr_expand>=1",
     lambda r: r['vpnode_dist_atr'] <= 2.0 and r['path_eff'] >= 0.4 and r['atr_expand'] >= 1.0)
test("NOT(vpnode>2 & path_eff<0.4 & vol_climax<1)",
     lambda r: not (r['vpnode_dist_atr'] > 2.0 and r['path_eff'] < 0.4 and r['vol_climax'] < 1.0))

# print sorted by wr_keep desc among those with winners_kept>=0.85
RESULTS.sort(key=lambda x: (-x['wr_keep'], -x['n_keep']))
print("\n" + "="*100)
print("RESULTS (sorted by wr_keep):")
hdr = "wr    nk   strk wk%   lc%   y24   y25   y26   rob  name"
print(hdr)
for r in RESULTS:
    print(f"{r['wr_keep']:.3f} {r['n_keep']:4d} {r['streak_keep']:4d} "
          f"{r['winners_kept_pct']:.2f}  {r['losers_cut_pct']:.2f}  "
          f"{(r['y24'] if r['y24'] is not None else 0):.2f}  "
          f"{(r['y25'] if r['y25'] is not None else 0):.2f}  "
          f"{(r['y26'] if r['y26'] is not None else 0):.2f}  "
          f"{'Y' if r['robust'] else '.'}    {r['name']}")
