"""_reopt5_univariate.py — univariate screening of all 48 causal features.

For each feature, find the threshold direction that best lifts WR while keeping
>=85% winners. Numeric features: scan deciles for keep-above and keep-below.
Binary/categorical: keep==value. Sentinel sell_decel=-1e7 treated as missing.

PROHIBITED: R, win, cj, low_idx, block, low_t, yr (never used as feature).
Output: ranked candidates by (wr_keep) with winners_kept>=85.
"""
import _reopt5_lib as L

ALLOWED = [
 'h1_trend','h1_dist','h1_pos','h1_eff','h4_trend','h4_dist','h4_pos','h4_eff',
 'hd_trend','hd_dist','hd_pos','hd_eff','dist_demand_atr','dist_supply_atr',
 'in_demand','demand_fresh','atr_regime','vol_low_vs_med','vol_climax',
 'vpnode_dist_atr','macro_drop_atr','macro_retr','macro_bull','macro_bear',
 'bars_to_base','path_eff','rsi','rsi_low','disp4_atr','killzone',
 'is_london_open','is_ny_overlap','is_deadzone','low_closepos','absorption',
 'bars_since_lowest','sell_decel','flow_accel','bars_since_sell',
 'buy_sell_ratio4','max_silence','smc_lag_bars','buy_after_smc',
 'naslong_after_smc','sell_skew_mig','buy_L_recent','regime_age_h','smc_bos'
]
SENTINEL = {'sell_decel': -10000000.0}


def clean(rows, f):
    s = SENTINEL.get(f)
    vals = []
    for r in rows:
        v = r.get(f)
        if v is None:
            continue
        if s is not None and v == s:
            continue
        vals.append(v)
    return vals


def main():
    rows = L.load()
    results = []
    for f in ALLOWED:
        vals = clean(rows, f)
        if not vals:
            continue
        uniq = sorted(set(vals))
        sent = SENTINEL.get(f)
        # decide candidate thresholds
        if len(uniq) <= 6:
            cands = []
            for u in uniq:
                cands.append((f'{f}=={u}', lambda r, u=u, s=sent: r.get(f) is not None and not (s is not None and r.get(f)==s) and r.get(f) == u))
                cands.append((f'{f}!={u}', lambda r, u=u, s=sent: r.get(f) is not None and not (s is not None and r.get(f)==s) and r.get(f) != u))
        else:
            qs = [uniq[int(len(uniq)*p)] for p in (0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9)]
            qs = sorted(set(qs))
            cands = []
            for q in qs:
                cands.append((f'{f}>={q}', lambda r, q=q, s=sent: r.get(f) is not None and not (s is not None and r.get(f)==s) and r.get(f) >= q))
                cands.append((f'{f}<={q}', lambda r, q=q, s=sent: r.get(f) is not None and not (s is not None and r.get(f)==s) and r.get(f) <= q))
        for name, fn in cands:
            kept = [r for r in rows if fn(r)]
            if len(kept) < 200:
                continue
            m = L.metrics(kept, rows)
            if m is None:
                continue
            m['name'] = name
            m['robust'] = L.is_robust(m)
            results.append(m)
    # rank: robust first, then wr_keep among winners_kept>=85
    results.sort(key=lambda m: (m['robust'], m['winners_kept_pct'] >= 85, m['wr_keep']), reverse=True)
    print('TOP univariate (winners_kept>=85, sorted by wr):')
    shown = 0
    for m in results:
        if m['winners_kept_pct'] < 85:
            continue
        print(f"  {m['name']:>26} n={m['n_keep']:>4} WR={m['wr_keep']:>5} "
              f"winK={m['winners_kept_pct']:>5}% losC={m['losers_cut_pct']:>4}% "
              f"streak{m['streak_base']}->{m['streak_keep']} "
              f"yr({m['by_year'][2024]},{m['by_year'][2025]},{m['by_year'][2026]}) "
              f"blk{m['blocks_ok']}/8 ROB={m['robust']}")
        shown += 1
        if shown >= 40:
            break
    print('\nROBUST univariate filters:')
    for m in results:
        if m['robust']:
            print('  ', L.report.__self__ if False else m['name'], '->',
                  f"WR={m['wr_keep']} winK={m['winners_kept_pct']}% blk{m['blocks_ok']}/8")


if __name__ == '__main__':
    main()
