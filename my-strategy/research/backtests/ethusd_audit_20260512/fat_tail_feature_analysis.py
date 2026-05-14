#!/usr/bin/env python3
"""
Fat-tail feature analysis for ETHUSD_4H_LONG_BREAKOUT_REGIME_FILTERED.

Goal: find features at entry that distinguish big winners (>= +3R)
from the rest. If found, propose a Priority A filter.

Walks each trade, snapshots features at entry bar, compares distributions.
"""
import pandas as pd
import numpy as np
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent))
from backtest_ethusd import load, simulate_trade, FILES, SPREAD_R
from rule_proposals import htf_context

OUT_DIR = Path(__file__).parent


def collect_trades_with_features(df, target_r=5.0, max_bars=30, adx_min=25):
    """Run regime-filtered breakout and snapshot features at entry."""
    trades = []
    for i in range(200, len(df) - 1):
        row = df.iloc[i]
        # Trigger
        if not (row['close'] > row['open']
                and row['body_pct'] >= 0.5
                and row['close'] > df.at[i-1, 'swhi_10']):
            continue
        rsi = row.get('RSI', np.nan); rsi_ma = row.get('RSI-based MA', np.nan)
        if pd.isna(rsi) or pd.isna(rsi_ma) or rsi <= rsi_ma:
            continue
        # Regime filters
        if pd.isna(row.get('adx14', np.nan)) or row['adx14'] < adx_min:
            continue
        if not row.get('close_above_ema200', False): continue
        if not row.get('ema50_above_ema200', False): continue
        if not row.get('atr_expanding', False): continue
        if pd.isna(row.get('ema50_slope', np.nan)) or row['ema50_slope'] <= 0:
            continue

        entry = row['close']; atr = row['atr14']
        if pd.isna(atr) or atr <= 0: continue
        stop = row['low'] - atr * 0.5
        R = abs(entry - stop)
        if R <= 0 or R / atr > 5: continue

        res = simulate_trade(df, i, 'LONG', entry, stop, target_r, max_bars, be_at_1r=True)
        if not res: continue

        # FEATURE SNAPSHOT at entry bar
        feats = {
            'rsi': rsi,
            'rsi_minus_ma': rsi - rsi_ma,
            'rsi_above_60': rsi >= 60,
            'rsi_above_55': rsi >= 55,
            'adx': row['adx14'],
            'adx_above_30': row['adx14'] >= 30,
            'adx_above_35': row['adx14'] >= 35,
            'di_plus_minus_minus': row.get('di_plus', 0) - row.get('di_minus', 0),
            'atr_ratio_ma': row['atr14'] / row.get('atr_ma20', row['atr14']),
            'atr_strong_expansion': row['atr14'] / row.get('atr_ma20', row['atr14']) >= 1.2,
            'dist_above_ema50_in_atr': (entry - row.get('ema50', entry)) / atr if not pd.isna(row.get('ema50', np.nan)) else 0,
            'dist_above_ema200_in_atr': (entry - row.get('ema200', entry)) / atr if not pd.isna(row.get('ema200', np.nan)) else 0,
            'body_pct': row['body_pct'],
            'body_above_60pct': row['body_pct'] >= 0.6,
            'body_above_70pct': row['body_pct'] >= 0.7,
            'range_in_atr': (row['high'] - row['low']) / atr,
            'range_above_atr': (row['high'] - row['low']) >= atr,
            'range_above_1_2_atr': (row['high'] - row['low']) >= 1.2 * atr,
            'ema50_slope_in_atr': row.get('ema50_slope', 0) / atr,
            # HTF context
            'htf12h_bullish': bool(row.get('htf12h_bullish', False)),
            'htf1d_bullish': bool(row.get('htf1d_bullish', False)),
            'htf1d_stack': bool(row.get('htf1d_stack', False)),
            # Pre-entry context: prior bar strength
            'prior_bar_bull': df.at[i-1, 'close'] > df.at[i-1, 'open'],
            'prior_2bar_bull': (df.at[i-1, 'close'] > df.at[i-1, 'open']) and
                                (df.at[i-2, 'close'] > df.at[i-2, 'open']),
            # Volume expansion (if present)
            # Distance traveled in last N bars (momentum)
            'return_5bar': (entry - df.at[i-5, 'close']) / df.at[i-5, 'close'] if i >= 5 else 0,
            'return_10bar': (entry - df.at[i-10, 'close']) / df.at[i-10, 'close'] if i >= 10 else 0,
            'return_20bar': (entry - df.at[i-20, 'close']) / df.at[i-20, 'close'] if i >= 20 else 0,
        }

        trades.append({
            'entry_time': row['time'],
            'r_outcome': res['r_outcome'],
            'r_outcome_net': res['r_outcome'] - SPREAD_R,
            'big_winner': res['r_outcome'] >= 3.0,
            'winner': res['r_outcome'] > 0,
            'mfe': res['mfe'],
            'mae': res['mae'],
            **feats,
        })
    return trades


def compare_distributions(df_trades, feature_cols, group_col='big_winner'):
    """For each feature, compute mean in big winners vs rest, plus simple t-stat proxy."""
    results = []
    big = df_trades[df_trades[group_col]]
    rest = df_trades[~df_trades[group_col]]
    for col in feature_cols:
        if df_trades[col].dtype == bool:
            # Compare proportions
            p_big = big[col].mean()
            p_rest = rest[col].mean()
            results.append({
                'feature': col,
                'type': 'bool',
                'big_winner_mean': round(p_big, 3),
                'rest_mean': round(p_rest, 3),
                'diff': round(p_big - p_rest, 3),
                'big_n': int(big[col].sum()),
                'rest_n': int(rest[col].sum()),
                # Heuristic: how strong the separation
                'ratio': round(p_big / p_rest if p_rest > 0 else float('inf'), 2),
            })
        else:
            m_big = big[col].mean()
            m_rest = rest[col].mean()
            s_pool = np.sqrt(((big[col].std() ** 2) + (rest[col].std() ** 2)) / 2)
            t_proxy = (m_big - m_rest) / (s_pool + 1e-9)
            results.append({
                'feature': col,
                'type': 'numeric',
                'big_winner_mean': round(m_big, 3),
                'rest_mean': round(m_rest, 3),
                'diff': round(m_big - m_rest, 3),
                'cohens_d': round(t_proxy, 2),
            })
    return pd.DataFrame(results)


def main():
    data = {tf: load(p) for tf, p in FILES.items()}
    df4 = data['4H']
    df12 = data['12H']
    df1d = data['1D']
    df4 = htf_context(df4, df12, 'htf12h')
    df4 = htf_context(df4, df1d, 'htf1d')

    print("=== Collecting trades + features ===")
    trades = collect_trades_with_features(df4, target_r=5.0, max_bars=30, adx_min=25)
    print(f"Total trades: {len(trades)}")

    df_t = pd.DataFrame(trades)
    n_big = df_t['big_winner'].sum()
    print(f"Big winners (>= +3R): {n_big} ({100*n_big/len(df_t):.1f}%)")
    print(f"Winners (>0R): {df_t['winner'].sum()} ({100*df_t['winner'].mean():.1f}%)")
    print()

    feature_cols = [c for c in df_t.columns if c not in
                    ['entry_time', 'r_outcome', 'r_outcome_net', 'big_winner', 'winner', 'mfe', 'mae']]

    print("=== BIG WINNERS (>=+3R) vs REST — feature comparison ===\n")
    cmp_df = compare_distributions(df_t, feature_cols, group_col='big_winner')

    # Sort by absolute cohens_d for numeric, by diff for bool
    cmp_num = cmp_df[cmp_df['type'] == 'numeric'].copy()
    cmp_num['abs_d'] = cmp_num['cohens_d'].abs()
    cmp_num = cmp_num.sort_values('abs_d', ascending=False)
    print("Numeric features (sorted by Cohen's d — larger = more discriminative):")
    print(cmp_num[['feature', 'big_winner_mean', 'rest_mean', 'diff', 'cohens_d']].to_string(index=False))
    print()
    cmp_bool = cmp_df[cmp_df['type'] == 'bool'].copy()
    cmp_bool['abs_diff'] = cmp_bool['diff'].abs()
    cmp_bool = cmp_bool.sort_values('abs_diff', ascending=False)
    print("Bool features (sorted by absolute difference):")
    print(cmp_bool[['feature', 'big_winner_mean', 'rest_mean', 'diff', 'ratio']].to_string(index=False))
    print()

    # === Save full feature dataset ===
    df_t.to_csv(OUT_DIR / 'ETHUSD_trades_with_features.csv', index=False)
    cmp_df.to_csv(OUT_DIR / 'ETHUSD_feature_comparison.csv', index=False)

    # === Test filter hypotheses ===
    print("=== Testing candidate Priority A filters ===\n")
    candidates = [
        ('Baseline (all)', df_t),
        ('RSI >= 60', df_t[df_t['rsi_above_60']]),
        ('RSI >= 55', df_t[df_t['rsi_above_55']]),
        ('ADX >= 30', df_t[df_t['adx_above_30']]),
        ('ADX >= 35', df_t[df_t['adx_above_35']]),
        ('ATR ratio >= 1.2', df_t[df_t['atr_strong_expansion']]),
        ('Body >= 60%', df_t[df_t['body_above_60pct']]),
        ('Body >= 70%', df_t[df_t['body_above_70pct']]),
        ('Range >= 1.0 ATR', df_t[df_t['range_above_atr']]),
        ('Range >= 1.2 ATR', df_t[df_t['range_above_1_2_atr']]),
        ('HTF 1D bullish', df_t[df_t['htf1d_bullish']]),
        ('HTF 12H bullish', df_t[df_t['htf12h_bullish']]),
        ('Prior 2-bar bull', df_t[df_t['prior_2bar_bull']]),
        ('5-bar return >= 5%', df_t[df_t['return_5bar'] >= 0.05]),
        ('10-bar return >= 10%', df_t[df_t['return_10bar'] >= 0.10]),
        # Combinations
        ('RSI>=60 + ADX>=30', df_t[df_t['rsi_above_60'] & df_t['adx_above_30']]),
        ('RSI>=55 + Range>=1.2ATR', df_t[df_t['rsi_above_55'] & df_t['range_above_1_2_atr']]),
        ('RSI>=55 + ATR>=1.2 + body>=60%',
         df_t[df_t['rsi_above_55'] & df_t['atr_strong_expansion'] & df_t['body_above_60pct']]),
        ('ATR>=1.2 + body>=60% + range>=1.2ATR',
         df_t[df_t['atr_strong_expansion'] & df_t['body_above_60pct'] & df_t['range_above_1_2_atr']]),
        ('RSI>=60 + ATR>=1.2 + body>=60%',
         df_t[df_t['rsi_above_60'] & df_t['atr_strong_expansion'] & df_t['body_above_60pct']]),
    ]

    rows = []
    for name, sub in candidates:
        if len(sub) == 0:
            continue
        r_net = sub['r_outcome_net']
        n = len(sub)
        big_n = sub['big_winner'].sum()
        wins = r_net[r_net > 0]; losses = r_net[r_net < 0]
        pf = abs(wins.sum() / losses.sum()) if len(losses) and losses.sum() != 0 else float('inf')
        sorted_r = sorted(r_net.tolist(), reverse=True)
        r_no_top5 = sum(sorted_r[5:]) if len(sorted_r) > 5 else r_net.sum()
        r_no_top10 = sum(sorted_r[10:]) if len(sorted_r) > 10 else r_net.sum()
        rows.append({
            'filter': name,
            'n_trades': n,
            'big_winner_pct': round(100 * big_n / n, 1),
            'total_net_r': round(r_net.sum(), 2),
            'avg_net_r': round(r_net.mean(), 3),
            'pf_net': round(pf, 2) if pf != float('inf') else 'inf',
            'win_rate': round((r_net > 0).mean(), 3),
            'r_no_top5_net': round(r_no_top5, 2),
            'r_no_top10_net': round(r_no_top10, 2),
        })

    res_df = pd.DataFrame(rows)
    print(res_df.to_string(index=False))
    print()
    res_df.to_csv(OUT_DIR / 'ETHUSD_priority_A_filter_test.csv', index=False)

    # === Look at the actual big winners individually ===
    print("=== Top 10 winners — feature snapshot ===")
    top10 = df_t.nlargest(10, 'r_outcome_net')
    cols_show = ['entry_time', 'r_outcome_net', 'rsi', 'adx', 'atr_ratio_ma',
                  'body_pct', 'range_in_atr', 'dist_above_ema50_in_atr',
                  'return_5bar', 'return_10bar', 'htf1d_bullish', 'htf12h_bullish',
                  'prior_2bar_bull']
    print(top10[cols_show].to_string(index=False))
    print()

    # === Look at worst losers for contrast ===
    print("=== Worst 10 losers — feature snapshot ===")
    worst10 = df_t.nsmallest(10, 'r_outcome_net')
    print(worst10[cols_show].to_string(index=False))


if __name__ == '__main__':
    main()
