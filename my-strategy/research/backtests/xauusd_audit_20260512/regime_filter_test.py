#!/usr/bin/env python3
"""
XAUUSD_4H_LONG_BREAKOUT_CONTINUATION — regime filter sweep.
Tests multiple filters to find the version that avoids chop years (2021-2023)
while preserving trending years (2019-2020, 2024-2026).

Net R @ 0.05R spread is the headline metric.
"""
import pandas as pd
import numpy as np
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))
from backtest_xauusd import load, simulate_trade, FILES, OUT_DIR

SPREAD_R = 0.05


def compute_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Add ADX, EMA50, EMA200, slopes, range metrics."""
    h, l, c = df['high'], df['low'], df['close']
    pc = c.shift(1)
    # True Range (already in atr14 base column; recompute for clarity)
    tr = pd.concat([(h - l).abs(), (h - pc).abs(), (l - pc).abs()], axis=1).max(axis=1)
    # Directional Movement
    up = h - h.shift(1)
    dn = l.shift(1) - l
    plus_dm = np.where((up > dn) & (up > 0), up, 0.0)
    minus_dm = np.where((dn > up) & (dn > 0), dn, 0.0)
    period = 14
    # Wilder's smoothing
    atr = pd.Series(tr).ewm(alpha=1/period, adjust=False).mean()
    plus_dm_s = pd.Series(plus_dm).ewm(alpha=1/period, adjust=False).mean()
    minus_dm_s = pd.Series(minus_dm).ewm(alpha=1/period, adjust=False).mean()
    di_plus = 100 * plus_dm_s / atr.replace(0, np.nan)
    di_minus = 100 * minus_dm_s / atr.replace(0, np.nan)
    dx = 100 * (di_plus - di_minus).abs() / (di_plus + di_minus).replace(0, np.nan)
    df['adx14'] = dx.ewm(alpha=1/period, adjust=False).mean()
    df['di_plus'] = di_plus
    df['di_minus'] = di_minus
    # EMAs
    df['ema50'] = c.ewm(span=50, adjust=False).mean()
    df['ema200'] = c.ewm(span=200, adjust=False).mean()
    df['ema50_slope'] = df['ema50'].diff(5)  # slope over 5 bars
    df['ema200_slope'] = df['ema200'].diff(10)
    df['close_above_ema50'] = c > df['ema50']
    df['close_above_ema200'] = c > df['ema200']
    df['ema50_above_ema200'] = df['ema50'] > df['ema200']
    # ATR expansion: current ATR vs its 20-bar MA
    df['atr_ma20'] = df['atr14'].rolling(20).mean()
    df['atr_expanding'] = df['atr14'] > df['atr_ma20']
    # Range contraction: avg range last 5 vs prior 15
    df['range'] = h - l
    df['range_recent'] = df['range'].rolling(5).mean()
    df['range_prior'] = df['range'].rolling(15).mean().shift(5)
    df['range_contraction'] = df['range_recent'] < df['range_prior']  # we want EXPANSION (FALSE) for breakouts
    # Sideways indicator: net displacement last 10 bars / sum of absolute moves
    abs_ret = c.diff().abs()
    net_disp_10 = (c - c.shift(10)).abs()
    sum_abs_10 = abs_ret.rolling(10).sum()
    df['directional_ratio_10'] = net_disp_10 / sum_abs_10.replace(0, np.nan)
    # High > 30% means strong direction; low (<20%) means chop
    df['is_sideways_10'] = df['directional_ratio_10'] < 0.20
    # Breakout-into-old-range filter:
    # Did current close break the 10-bar high AND is that high notably higher than 30-bar high?
    # If 10-bar high ≈ 30-bar high, we're breaking into the same old range → reject.
    df['hi_10'] = df['high'].rolling(10).max()
    df['hi_30'] = df['high'].rolling(30).max()
    df['breakout_expanding_range'] = df['hi_10'] >= df['hi_30'] * 0.9995  # 10-bar high near 30-bar high = at or above
    return df


def htf_context(df_4h: pd.DataFrame, df_htf: pd.DataFrame, htf_label: str) -> pd.DataFrame:
    """Add HTF supportive flag: HTF close > HTF EMA50."""
    df_htf = df_htf.copy()
    df_htf['htf_ema50'] = df_htf['close'].ewm(span=50, adjust=False).mean()
    df_htf['htf_bullish'] = df_htf['close'] > df_htf['htf_ema50']
    # For each 4H bar, find the most recent HTF bar
    htf_lite = df_htf[['time', 'htf_bullish']].sort_values('time')
    df_4h_sorted = df_4h.sort_values('time').reset_index(drop=True)
    merged = pd.merge_asof(df_4h_sorted, htf_lite, on='time', direction='backward')
    df_4h[f'{htf_label}_bullish'] = merged['htf_bullish'].values
    return df_4h


def breakout_signal(row, prev_swing_high: float) -> bool:
    """Base breakout: close > open, body >= 50% range, close > prev 10-bar swing high."""
    if pd.isna(prev_swing_high):
        return False
    rng = row['high'] - row['low']
    if rng <= 0:
        return False
    body = abs(row['close'] - row['open'])
    return (row['close'] > row['open']
            and body / rng >= 0.5
            and row['close'] > prev_swing_high)


def run_strategy(df: pd.DataFrame, filters: dict, target_r=4.0, max_bars=24,
                 be=True, name='?') -> list:
    """Runs the breakout LONG strategy with optional regime filters."""
    trades = []
    for i in range(200, len(df) - 1):  # need 200 bars for EMA200
        row = df.iloc[i]
        prev_swhi = df.at[i-1, 'swhi_10']
        # Base breakout
        if not breakout_signal(row, prev_swhi):
            continue
        # RSI > MA (already part of base in our prior model)
        rsi = row.get('RSI', np.nan)
        rsi_ma = row.get('RSI-based MA', np.nan)
        if pd.isna(rsi) or pd.isna(rsi_ma) or rsi <= rsi_ma:
            continue
        # Apply filters
        if filters.get('adx_min') is not None:
            if pd.isna(row.get('adx14', np.nan)) or row['adx14'] < filters['adx_min']:
                continue
        if filters.get('atr_expanding') and not row.get('atr_expanding', False):
            continue
        if filters.get('ema50_slope_pos') and (pd.isna(row.get('ema50_slope', np.nan)) or row['ema50_slope'] <= 0):
            continue
        if filters.get('close_above_ema50') and not row.get('close_above_ema50', False):
            continue
        if filters.get('close_above_ema200') and not row.get('close_above_ema200', False):
            continue
        if filters.get('ema50_above_ema200') and not row.get('ema50_above_ema200', False):
            continue
        if filters.get('no_chop_10') and row.get('is_sideways_10', True):
            continue
        if filters.get('breakout_expansion_required') and not row.get('breakout_expanding_range', False):
            continue
        if filters.get('range_expanding') and row.get('range_contraction', True):
            continue
        if filters.get('htf_12h_bullish') and not row.get('htf12h_bullish', False):
            continue
        if filters.get('htf_1d_bullish') and not row.get('htf1d_bullish', False):
            continue

        # Build trade
        entry = row['close']
        atr = row['atr14']
        if pd.isna(atr) or atr <= 0:
            continue
        stop = row['low'] - atr * 0.5
        R = abs(entry - stop)
        if R <= 0 or R / atr > 5:
            continue
        res = simulate_trade(df, i, 'LONG', entry, stop, target_r, max_bars, be_at_1r=be)
        if not res:
            continue
        res.update({
            'entry_time': df.at[i, 'time'], 'entry_price': entry,
            'stop_price': stop, 'direction': 'LONG', 'r_planned': target_r,
            'strategy': name, 'tf': '4H',
        })
        trades.append(res)
    return trades


def metrics_with_spread(trades: list, spread: float = SPREAD_R) -> dict:
    if not trades:
        return {'n': 0, 'total_net_r': 0, 'avg_net_r': 0, 'pf_net': 0,
                'win_rate': 0, 'max_losing_streak': 0, 'r_no_top5_net': 0,
                'r_no_top10_net': 0, 'trades_per_week': 0, 'trades_per_month': 0}
    df = pd.DataFrame(trades)
    r = df['r_outcome'] - spread
    span_days = (pd.to_datetime(df['entry_time'].max()) - pd.to_datetime(df['entry_time'].min())).days
    span_weeks = max(1, span_days / 7)
    span_months = max(1, span_days / 30.44)
    wins = r[r > 0]
    losses = r[r < 0]
    pf = abs(wins.sum() / losses.sum()) if len(losses) and losses.sum() != 0 else float('inf')
    # Streak
    streak = max_streak = 0
    for v in r:
        if v <= 0:
            streak += 1
            max_streak = max(max_streak, streak)
        else:
            streak = 0
    sorted_r = sorted(r.tolist(), reverse=True)
    r_no_top5 = sum(sorted_r[5:]) if len(sorted_r) > 5 else 0
    r_no_top10 = sum(sorted_r[10:]) if len(sorted_r) > 10 else 0
    return {
        'n': len(df),
        'total_net_r': round(r.sum(), 2),
        'avg_net_r': round(r.mean(), 4),
        'pf_net': round(pf, 2) if pf != float('inf') else float('inf'),
        'win_rate': round((r > 0).mean(), 3),
        'max_losing_streak': max_streak,
        'r_no_top5_net': round(r_no_top5, 2),
        'r_no_top10_net': round(r_no_top10, 2),
        'trades_per_week': round(len(df) / span_weeks, 2),
        'trades_per_month': round(len(df) / span_months, 2),
        'best_r': round(sorted_r[0], 2),
        'worst_r': round(sorted_r[-1], 2),
    }


def yearly_breakdown(trades: list, spread: float = SPREAD_R) -> pd.DataFrame:
    if not trades:
        return pd.DataFrame()
    df = pd.DataFrame(trades)
    df['year'] = pd.to_datetime(df['entry_time']).dt.year
    df['r_net'] = df['r_outcome'] - spread
    return df.groupby('year').agg(
        n=('r_net', 'count'),
        total_net_r=('r_net', 'sum'),
        avg_net_r=('r_net', 'mean'),
        win_rate=('r_net', lambda x: (x > 0).mean()),
    ).round(3).reset_index()


def main():
    print("=== Loading data ===")
    df4 = load(FILES['4H'])
    df4 = compute_indicators(df4)
    df12 = load(FILES['12H'])
    df1d = load(FILES['1D'])
    df4 = htf_context(df4, df12, 'htf12h')
    df4 = htf_context(df4, df1d, 'htf1d')

    print(f"  4H bars with indicators: {len(df4)}")
    print(f"  ADX14 mean: {df4['adx14'].mean():.1f}  median: {df4['adx14'].median():.1f}")
    print(f"  EMA50 > EMA200 fraction: {df4['ema50_above_ema200'].mean():.2%}")
    print(f"  Close > EMA200 fraction: {df4['close_above_ema200'].mean():.2%}")
    print(f"  HTF 12H bullish fraction: {df4['htf12h_bullish'].mean():.2%}")
    print(f"  HTF 1D bullish fraction: {df4['htf1d_bullish'].mean():.2%}")

    # Run filter combinations
    configs = [
        ('A_baseline_no_regime',        {}),
        ('B_adx18',                     {'adx_min': 18}),
        ('C_adx20',                     {'adx_min': 20}),
        ('D_adx22',                     {'adx_min': 22}),
        ('E_adx25',                     {'adx_min': 25}),
        ('F_atr_expanding',             {'atr_expanding': True}),
        ('G_ema50_slope_pos',           {'ema50_slope_pos': True}),
        ('H_close_above_ema50',         {'close_above_ema50': True}),
        ('I_close_above_ema200',        {'close_above_ema200': True}),
        ('J_ema50_above_ema200',        {'ema50_above_ema200': True}),
        ('K_no_chop_10',                {'no_chop_10': True}),
        ('L_breakout_expansion',        {'breakout_expansion_required': True}),
        ('M_range_expanding',           {'range_expanding': True}),
        ('N_htf12h_bullish',            {'htf_12h_bullish': True}),
        ('O_htf1d_bullish',             {'htf_1d_bullish': True}),
        # Combinations
        ('P_adx20+ema_stack',           {'adx_min': 20, 'close_above_ema200': True, 'ema50_above_ema200': True}),
        ('Q_adx22+ema_stack',           {'adx_min': 22, 'close_above_ema200': True, 'ema50_above_ema200': True}),
        ('R_full_trend_regime',         {'adx_min': 20, 'close_above_ema200': True, 'ema50_above_ema200': True,
                                          'ema50_slope_pos': True, 'atr_expanding': True}),
        ('S_full_trend_htf',            {'adx_min': 20, 'close_above_ema200': True, 'ema50_above_ema200': True,
                                          'htf_1d_bullish': True}),
        ('T_minimal_trend_htf',         {'close_above_ema200': True, 'ema50_above_ema200': True,
                                          'htf_1d_bullish': True}),
        ('U_anti_chop',                 {'no_chop_10': True, 'breakout_expansion_required': True, 'atr_expanding': True}),
        ('V_robust',                    {'adx_min': 18, 'ema50_above_ema200': True, 'htf_1d_bullish': True,
                                          'breakout_expansion_required': True}),
    ]

    print(f"\n=== Running {len(configs)} filter configurations ===\n")
    rows = []
    yearly_data = {}
    for name, filt in configs:
        trades = run_strategy(df4, filt, target_r=4.0, max_bars=24, be=True, name=name)
        m = metrics_with_spread(trades, SPREAD_R)
        rows.append({'config': name, **m, 'filters': str(filt)})
        yearly_data[name] = yearly_breakdown(trades, SPREAD_R)

    df_out = pd.DataFrame(rows)
    df_out = df_out.sort_values('total_net_r', ascending=False)
    df_out.to_csv(OUT_DIR / 'XAUUSD_4H_breakout_regime_filter_sweep.csv', index=False)

    print("=== Filter sweep results (sorted by total NET R @ 0.05R spread) ===")
    print()
    cols_show = ['config', 'n', 'trades_per_week', 'trades_per_month',
                 'total_net_r', 'avg_net_r', 'pf_net', 'win_rate',
                 'max_losing_streak', 'r_no_top5_net', 'r_no_top10_net']
    print(df_out[cols_show].to_string(index=False))

    # Detail the top 3 — yearly breakdown
    top3 = df_out['config'].head(3).tolist()
    print("\n=== Top 3 — per year breakdown ===")
    for cfg in top3:
        print(f"\n--- {cfg} ---")
        print(yearly_data[cfg].to_string(index=False))

    # Also detail the worst-year filter (baseline) for comparison
    if 'A_baseline_no_regime' in yearly_data and 'A_baseline_no_regime' not in top3:
        print(f"\n--- A_baseline_no_regime (for comparison) ---")
        print(yearly_data['A_baseline_no_regime'].to_string(index=False))


if __name__ == '__main__':
    main()
