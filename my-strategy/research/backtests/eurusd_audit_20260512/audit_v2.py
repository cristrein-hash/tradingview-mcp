#!/usr/bin/env python3
"""
EURUSD Deep Audit V2 — with 1H data + new hypotheses.
Categories tested:
- Session-aware (London open, NY open, Asia range break)
- Multi-TF strict (1D+12H+4H aligned)
- DXY macro regime filters (more nuanced than just bearish)
- Body/range strength filters
- Failed breakdown + macro confluence
- BB squeeze + session
- Quality momentum continuation
- Cooldown filters to avoid overtrading
"""
import pandas as pd
import numpy as np
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent))
from backtest_eurusd import (load, load_macro_dxy, attach_dxy, htf_context,
                              simulate_trade, run_long, metrics, yearly_metrics,
                              SPREAD_R, OUT_DIR)

FILES_V2 = {
    '1D':  '/Users/cristrein/Downloads/PEPPERSTONE_EURUSD, 1D_2f9df.csv',
    '12H': '/Users/cristrein/Downloads/PEPPERSTONE_EURUSD, 720_77e25.csv',
    '4H':  '/Users/cristrein/Downloads/PEPPERSTONE_EURUSD, 240_c99e7.csv',
    '1H':  '/Users/cristrein/Downloads/PEPPERSTONE_EURUSD, 60_74b6d.csv',
    '30M': '/Users/cristrein/Downloads/PEPPERSTONE_EURUSD, 30_cc449.csv',
    '15M': '/Users/cristrein/Downloads/PEPPERSTONE_EURUSD, 15_59a92.csv',
}


def add_extra_indicators(df):
    """Add session flags, Asia/London/NY ranges, more nuanced DXY interpretation."""
    df['hour_utc'] = df['time'].dt.hour
    df['weekday'] = df['time'].dt.dayofweek
    df['asia_session'] = df['hour_utc'].isin([0, 1, 2, 3, 4, 5, 6])  # 00-07 UTC
    df['london_session'] = df['hour_utc'].isin([7, 8, 9, 10, 11, 12])  # 07-13 UTC
    df['ny_session'] = df['hour_utc'].isin([13, 14, 15, 16, 17])  # 13-18 UTC
    df['london_open'] = df['hour_utc'].isin([7, 8])  # London open volatility window
    df['ny_open'] = df['hour_utc'].isin([13, 14])  # NY open volatility window
    df['power_hour'] = df['hour_utc'].isin([14, 15])  # Strong move window
    return df


def main():
    print("=== Loading EURUSD V2 + 1H ===")
    data = {tf: load(p) for tf, p in FILES_V2.items()}
    df1d, df12, df4, df1, df30, df15 = (data['1D'], data['12H'], data['4H'],
                                          data['1H'], data['30M'], data['15M'])
    for tf, df in data.items():
        print(f"  {tf}: {len(df)} bars  {df['time'].min().date()} → {df['time'].max().date()}")

    # Add HTF context
    df4 = htf_context(df4, df12, 'htf12h')
    df4 = htf_context(df4, df1d, 'htf1d')
    df1 = htf_context(df1, df4, 'htf4h')
    df1 = htf_context(df1, df12, 'htf12h')
    df1 = htf_context(df1, df1d, 'htf1d')
    df30 = htf_context(df30, df1, 'htf1h')
    df30 = htf_context(df30, df4, 'htf4h')
    df30 = htf_context(df30, df1d, 'htf1d')

    # DXY macro
    df_dxy = load_macro_dxy()
    df4 = attach_dxy(df4, df_dxy)
    df1 = attach_dxy(df1, df_dxy)
    df30 = attach_dxy(df30, df_dxy)

    # Add session indicators
    for d in [df4, df1, df30]:
        add_extra_indicators(d)

    summaries = []
    trades_by = {}

    # =============================================================
    # GROUP 1: Multi-TF strict + body + DXY (most stringent)
    # =============================================================
    print("\n=== G1: Multi-TF strict (1D+12H+4H all bullish) + DXY filter ===")

    def sig_multi_tf_strict_4h(df, i, row):
        if not row.get('htf1d_bullish', False): return False
        if not row.get('htf12h_bullish', False): return False
        if not (row['close'] > row['open'] and row['body_pct'] >= 0.5
                and row['close'] > df.at[i-1, 'swhi_10']): return False
        rsi = row.get('RSI', np.nan); rsi_ma = row.get('RSI-based MA', np.nan)
        if pd.isna(rsi) or pd.isna(rsi_ma) or rsi <= rsi_ma: return False
        if not row.get('close_above_ema200', False): return False
        if not row.get('ema50_above_ema200', False): return False
        if not row.get('atr_expanding', False): return False
        return True

    def sig_multi_tf_strict_4h_dxy_macro_bear(df, i, row):
        if not sig_multi_tf_strict_4h(df, i, row): return False
        # DXY in macro bear regime: close < EMA200 AND falling
        if not row.get('dxy_below_ema200', False): return False
        if not row.get('dxy_falling', False): return False
        return True

    def sig_multi_tf_strict_4h_dxy_bear(df, i, row):
        if not sig_multi_tf_strict_4h(df, i, row): return False
        if not row.get('dxy_bearish', False): return False
        return True

    for sig_name, sig_func in [
        ('multi_TF_strict', sig_multi_tf_strict_4h),
        ('multi_TF_strict_DXY_bear', sig_multi_tf_strict_4h_dxy_bear),
        ('multi_TF_strict_DXY_macro_bear', sig_multi_tf_strict_4h_dxy_macro_bear),
    ]:
        for trg in [2.5, 3.0, 4.0]:
            name = f'G1_{sig_name}_4H_target{trg}R'
            t = run_long(df4, sig_func, trg, 24, name, '4H')
            summaries.append({'strategy': name, **metrics(t)})
            trades_by[name] = t

    # =============================================================
    # GROUP 2: 1H pullback to EMA50 with macro/HTF filters
    # =============================================================
    print("\n=== G2: 1H pullback EMA50 + multi-TF + DXY variants ===")

    def sig_1h_pb_ema50_base(df, i, row):
        ema50 = row.get('ema50', np.nan)
        if pd.isna(ema50): return False
        if not (row['low'] <= ema50 and row['close'] > ema50): return False
        if not (row['close'] > row['open'] and row['body_pct'] >= 0.4): return False
        if not row.get('close_above_ema200', False): return False
        if not row.get('ema50_above_ema200', False): return False
        return True

    def sig_1h_pb_htf1d(df, i, row):
        if not sig_1h_pb_ema50_base(df, i, row): return False
        if not row.get('htf1d_bullish', False): return False
        return True

    def sig_1h_pb_htf1d_htf4h(df, i, row):
        if not sig_1h_pb_ema50_base(df, i, row): return False
        if not row.get('htf1d_bullish', False): return False
        if not row.get('htf4h_bullish', False): return False
        return True

    def sig_1h_pb_htf1d_dxy_bear(df, i, row):
        if not sig_1h_pb_htf1d(df, i, row): return False
        if not row.get('dxy_bearish', False): return False
        return True

    def sig_1h_pb_all_filters(df, i, row):
        if not sig_1h_pb_ema50_base(df, i, row): return False
        if not row.get('htf1d_bullish', False): return False
        if not row.get('htf4h_bullish', False): return False
        if not row.get('dxy_bearish', False): return False
        rsi = row.get('RSI', np.nan); rsi_ma = row.get('RSI-based MA', np.nan)
        if pd.isna(rsi) or pd.isna(rsi_ma) or rsi <= rsi_ma: return False
        return True

    for sig_name, sig_func in [
        ('pb_base', sig_1h_pb_ema50_base),
        ('pb_HTF1D', sig_1h_pb_htf1d),
        ('pb_HTF1D+4H', sig_1h_pb_htf1d_htf4h),
        ('pb_HTF1D_DXY_bear', sig_1h_pb_htf1d_dxy_bear),
        ('pb_ALL_filters', sig_1h_pb_all_filters),
    ]:
        for trg, mb in [(2.0, 16), (2.5, 20), (3.0, 24)]:
            name = f'G2_1H_{sig_name}_target{trg}R'
            t = run_long(df1, sig_func, trg, mb, name, '1H')
            summaries.append({'strategy': name, **metrics(t)})
            trades_by[name] = t

    # =============================================================
    # GROUP 3: Session-aware 1H breakouts
    # =============================================================
    print("\n=== G3: Session-aware 1H breakouts ===")

    def sig_london_open_breakout(df, i, row):
        if not row.get('london_open', False): return False
        if not (row['close'] > row['open'] and row['body_pct'] >= 0.5
                and row['close'] > df.at[i-1, 'swhi_10']): return False
        if not row.get('ema50_above_ema200', False): return False
        if not row.get('close_above_ema200', False): return False
        return True

    def sig_ny_open_continuation(df, i, row):
        if not row.get('ny_open', False): return False
        if not (row['close'] > row['open'] and row['body_pct'] >= 0.5
                and row['close'] > df.at[i-1, 'swhi_10']): return False
        rsi = row.get('RSI', np.nan); rsi_ma = row.get('RSI-based MA', np.nan)
        if pd.isna(rsi) or pd.isna(rsi_ma) or rsi <= rsi_ma: return False
        if not row.get('ema50_above_ema200', False): return False
        if not row.get('close_above_ema200', False): return False
        return True

    def sig_london_open_dxy_bear(df, i, row):
        if not sig_london_open_breakout(df, i, row): return False
        if not row.get('dxy_bearish', False): return False
        return True

    def sig_ny_open_dxy_bear(df, i, row):
        if not sig_ny_open_continuation(df, i, row): return False
        if not row.get('dxy_bearish', False): return False
        return True

    for sig_name, sig_func in [
        ('london_open', sig_london_open_breakout),
        ('london_open_DXY_bear', sig_london_open_dxy_bear),
        ('ny_open', sig_ny_open_continuation),
        ('ny_open_DXY_bear', sig_ny_open_dxy_bear),
    ]:
        for trg in [2.0, 2.5, 3.0]:
            name = f'G3_1H_{sig_name}_target{trg}R'
            t = run_long(df1, sig_func, trg, 16, name, '1H')
            summaries.append({'strategy': name, **metrics(t)})
            trades_by[name] = t

    # =============================================================
    # GROUP 4: 1H failed breakdown (US500 winner pattern adapted)
    # =============================================================
    print("\n=== G4: 1H failed breakdown ===")

    def sig_1h_failed_breakdown_base(df, i, row):
        # Local definition for 1H
        if not (row['low'] < df.at[i-1, 'swlo_20']): return False
        if not (row['close'] > df.at[i-1, 'swlo_20']): return False
        if not (row['close'] > row['open'] and row['body_pct'] >= 0.5): return False
        if not row.get('close_above_ema200', False): return False
        if not row.get('ema50_above_ema200', False): return False
        if not row.get('atr_expanding', False): return False
        return True

    def sig_1h_fb_htf1d(df, i, row):
        if not sig_1h_failed_breakdown_base(df, i, row): return False
        if not row.get('htf1d_bullish', False): return False
        return True

    def sig_1h_fb_dxy_bear(df, i, row):
        if not sig_1h_failed_breakdown_base(df, i, row): return False
        if not row.get('dxy_bearish', False): return False
        return True

    def sig_1h_fb_htf1d_dxy(df, i, row):
        if not sig_1h_fb_htf1d(df, i, row): return False
        if not row.get('dxy_bearish', False): return False
        return True

    for sig_name, sig_func in [
        ('fb_base', sig_1h_failed_breakdown_base),
        ('fb_HTF1D', sig_1h_fb_htf1d),
        ('fb_DXY_bear', sig_1h_fb_dxy_bear),
        ('fb_HTF1D+DXY', sig_1h_fb_htf1d_dxy),
    ]:
        for trg in [2.0, 2.5, 3.0]:
            name = f'G4_1H_{sig_name}_target{trg}R'
            t = run_long(df1, sig_func, trg, 20, name, '1H')
            summaries.append({'strategy': name, **metrics(t)})
            trades_by[name] = t

    # =============================================================
    # GROUP 5: 1H breakout with body 70%+ and range > 1.5x ATR (decisive moves only)
    # =============================================================
    print("\n=== G5: 1H decisive breakout (body 70% + range > 1.5 ATR) ===")

    def sig_1h_decisive_breakout(df, i, row):
        if not (row['close'] > row['open'] and row['body_pct'] >= 0.7): return False
        if not (row['close'] > df.at[i-1, 'swhi_10']): return False
        atr = row.get('atr14', np.nan)
        if pd.isna(atr): return False
        if (row['high'] - row['low']) < 1.5 * atr: return False
        rsi = row.get('RSI', np.nan); rsi_ma = row.get('RSI-based MA', np.nan)
        if pd.isna(rsi) or pd.isna(rsi_ma) or rsi <= rsi_ma: return False
        if not row.get('close_above_ema200', False): return False
        if not row.get('ema50_above_ema200', False): return False
        if not row.get('atr_expanding', False): return False
        return True

    def sig_1h_decisive_dxy(df, i, row):
        if not sig_1h_decisive_breakout(df, i, row): return False
        if not row.get('dxy_bearish', False): return False
        return True

    def sig_1h_decisive_htf1d(df, i, row):
        if not sig_1h_decisive_breakout(df, i, row): return False
        if not row.get('htf1d_bullish', False): return False
        return True

    for sig_name, sig_func in [
        ('decisive', sig_1h_decisive_breakout),
        ('decisive_DXY_bear', sig_1h_decisive_dxy),
        ('decisive_HTF1D', sig_1h_decisive_htf1d),
    ]:
        for trg in [2.0, 2.5, 3.0, 4.0]:
            name = f'G5_1H_{sig_name}_target{trg}R'
            t = run_long(df1, sig_func, trg, 20, name, '1H')
            summaries.append({'strategy': name, **metrics(t)})
            trades_by[name] = t

    # =============================================================
    # GROUP 6: 4H breakout with body 70% + range > 1.5 ATR + DXY divergence
    # =============================================================
    print("\n=== G6: 4H decisive breakout + macro divergence ===")

    def sig_4h_decisive_breakout(df, i, row):
        if not (row['close'] > row['open'] and row['body_pct'] >= 0.7): return False
        if not (row['close'] > df.at[i-1, 'swhi_10']): return False
        atr = row.get('atr14', np.nan)
        if pd.isna(atr): return False
        if (row['high'] - row['low']) < 1.5 * atr: return False
        rsi = row.get('RSI', np.nan); rsi_ma = row.get('RSI-based MA', np.nan)
        if pd.isna(rsi) or pd.isna(rsi_ma) or rsi <= rsi_ma: return False
        if not row.get('close_above_ema200', False): return False
        if not row.get('ema50_above_ema200', False): return False
        if not row.get('atr_expanding', False): return False
        return True

    def sig_4h_decisive_dxy(df, i, row):
        if not sig_4h_decisive_breakout(df, i, row): return False
        if not row.get('dxy_bearish', False): return False
        return True

    def sig_4h_decisive_htf1d(df, i, row):
        if not sig_4h_decisive_breakout(df, i, row): return False
        if not row.get('htf1d_bullish', False): return False
        return True

    for sig_name, sig_func in [
        ('decisive', sig_4h_decisive_breakout),
        ('decisive_DXY_bear', sig_4h_decisive_dxy),
        ('decisive_HTF1D', sig_4h_decisive_htf1d),
    ]:
        for trg in [2.5, 3.0, 4.0]:
            name = f'G6_4H_{sig_name}_target{trg}R'
            t = run_long(df4, sig_func, trg, 24, name, '4H')
            summaries.append({'strategy': name, **metrics(t)})
            trades_by[name] = t

    # =============================================================
    # GROUP 7: Inside bar break + multi-TF strict (rare but high quality)
    # =============================================================
    print("\n=== G7: Inside bar break + multi-TF ===")

    def sig_1h_inside_bar_strict(df, i, row):
        prev_inside = (df.at[i-1, 'high'] < df.at[i-2, 'high']) and (df.at[i-1, 'low'] > df.at[i-2, 'low']) if i >= 2 else False
        if not prev_inside: return False
        prev_high = df.at[i-1, 'high']
        if not (row['close'] > prev_high): return False
        if not (row['close'] > row['open'] and row['body_pct'] >= 0.5): return False
        if not row.get('close_above_ema200', False): return False
        if not row.get('ema50_above_ema200', False): return False
        if not row.get('htf1d_bullish', False): return False
        if not row.get('htf4h_bullish', False): return False
        return True

    for trg in [2.0, 2.5, 3.0]:
        name = f'G7_1H_inside_bar_strict_target{trg}R'
        t = run_long(df1, sig_1h_inside_bar_strict, trg, 16, name, '1H')
        summaries.append({'strategy': name, **metrics(t)})
        trades_by[name] = t

    # =============================================================
    # GROUP 8: BB squeeze break + 1H + DXY
    # =============================================================
    print("\n=== G8: BB squeeze 1H ===")

    # Compute BB squeeze on 1H
    c1 = df1['close']
    df1['bb_mid'] = c1.rolling(20).mean()
    df1['bb_std'] = c1.rolling(20).std()
    df1['bb_upper'] = df1['bb_mid'] + 2 * df1['bb_std']
    df1['bb_lower'] = df1['bb_mid'] - 2 * df1['bb_std']
    df1['bb_width'] = (df1['bb_upper'] - df1['bb_lower']) / df1['bb_mid'].replace(0, np.nan)
    df1['bb_width_ma'] = df1['bb_width'].rolling(20).mean()
    df1['bb_squeeze'] = df1['bb_width'] < df1['bb_width_ma'] * 0.85

    def sig_1h_bb_squeeze(df, i, row):
        prev_squeeze = df.at[i-1, 'bb_squeeze'] if i >= 1 else False
        if not prev_squeeze: return False
        if not (row['close'] > df.at[i-1, 'bb_upper']): return False
        if not (row['close'] > row['open'] and row['body_pct'] >= 0.5): return False
        if not row.get('ema50_above_ema200', False): return False
        if not row.get('close_above_ema200', False): return False
        return True

    def sig_1h_bb_squeeze_htf1d(df, i, row):
        if not sig_1h_bb_squeeze(df, i, row): return False
        if not row.get('htf1d_bullish', False): return False
        return True

    def sig_1h_bb_squeeze_dxy(df, i, row):
        if not sig_1h_bb_squeeze(df, i, row): return False
        if not row.get('dxy_bearish', False): return False
        return True

    for sig_name, sig_func in [
        ('bb_squeeze', sig_1h_bb_squeeze),
        ('bb_squeeze_HTF1D', sig_1h_bb_squeeze_htf1d),
        ('bb_squeeze_DXY', sig_1h_bb_squeeze_dxy),
    ]:
        for trg in [2.0, 2.5, 3.0]:
            name = f'G8_1H_{sig_name}_target{trg}R'
            t = run_long(df1, sig_func, trg, 16, name, '1H')
            summaries.append({'strategy': name, **metrics(t)})
            trades_by[name] = t

    # =============================================================
    # OUTPUT
    # =============================================================
    df_res = pd.DataFrame(summaries).sort_values('total_r_net', ascending=False)
    df_res.to_csv(OUT_DIR / 'EURUSD_V2_summary.csv', index=False)

    cols = ['strategy', 'n', 'trades_per_week', 'trades_per_month', 'total_r_net',
            'avg_r_net', 'win_rate', 'pf_net', 'max_losing_streak',
            'r_no_top5_net', 'r_no_top10_net']

    print("\n=== Top 20 ===")
    print(df_res[cols].head(20).to_string(index=False))

    print("\n=== Bottom 5 (for contrast) ===")
    print(df_res[cols].tail(5).to_string(index=False))

    print("\n=== Top 5 yearly breakdown ===")
    for name in df_res['strategy'].head(5):
        t = trades_by.get(name, [])
        if t:
            print(f"\n--- {name} ---")
            print(yearly_metrics(t).to_string(index=False))


if __name__ == '__main__':
    main()
