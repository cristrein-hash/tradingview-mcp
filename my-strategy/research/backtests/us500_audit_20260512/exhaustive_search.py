#!/usr/bin/env python3
"""
US500 — exhaustive search for LONG-ONLY edge using new indicators + confluences.

Hypotheses tested:
1. Bollinger Band squeeze breakout (low vol → expansion)
2. Failed breakdown / sweep low reclaim
3. Higher Low (HL) structure trade
4. Inside bar breakout in trend
5. Bull flag (impulse + tight consolidation + break)
6. RSI oversold (in bull trend) bounce
7. Multi-TF strict alignment (1D+12H+4H+1H all bullish)
8. Trend pullback (deep) + immediate bullish reversal
9. Volatility regime: ATR squeeze + expansion
10. Hammer/bullish engulfing in oversold (not yet tried)
11. EMA10 fast pullback in strong trend
12. Volume burst breakout (if vol data present)
13. RSI divergence in bull regime
14. Open/close-by-time filter (1H setups around US session times)
"""
import pandas as pd
import numpy as np
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent))
from backtest_us500 import load, simulate_trade, metrics, yearly_metrics, htf_context, FILES, SPREAD_R, OUT_DIR


def add_indicators(df):
    """Add Bollinger Bands, EMA10, additional structural indicators."""
    c = df['close']
    # Bollinger Bands (20, 2)
    df['bb_mid'] = c.rolling(20).mean()
    df['bb_std'] = c.rolling(20).std()
    df['bb_upper'] = df['bb_mid'] + 2 * df['bb_std']
    df['bb_lower'] = df['bb_mid'] - 2 * df['bb_std']
    df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['bb_mid'].replace(0, np.nan)
    df['bb_width_ma'] = df['bb_width'].rolling(20).mean()
    df['bb_squeeze'] = df['bb_width'] < df['bb_width_ma'] * 0.85
    df['ema10'] = c.ewm(span=10, adjust=False).mean()
    df['close_above_ema10'] = c > df['ema10']
    # Inside bar
    df['inside_bar'] = (df['high'] < df['high'].shift(1)) & (df['low'] > df['low'].shift(1))
    # Hammer (large lower wick + small body + close > open)
    rng = (df['high'] - df['low']).replace(0, np.nan)
    df['lower_wick_pct'] = (df[['open','close']].min(axis=1) - df['low']) / rng
    df['body_to_range'] = (df['close'] - df['open']).abs() / rng
    df['hammer'] = (df['lower_wick_pct'] >= 0.6) & (df['body_to_range'] <= 0.3) & (df['close'] > df['open'])
    # Bullish engulfing
    df['bull_engulf'] = (df['close'].shift(1) < df['open'].shift(1)) & \
                        (df['open'] <= df['close'].shift(1)) & \
                        (df['close'] > df['open'].shift(1)) & \
                        (df['body_to_range'] >= 0.5)
    # Higher Low pattern (last bar low > N-bar back swing low but < prev bar low)
    df['lower_low_3'] = df['low'] < df['low'].shift(1)
    df['hl_pattern'] = (df['low'].shift(2) > df['low'].shift(1)) & (df['low'] > df['low'].shift(1)) & \
                       (df['close'] > df['open'])
    # Failed breakdown: low < swlo_20 but close > swlo_20
    df['failed_breakdown'] = (df['low'] < df['swlo_20'].shift(1)) & \
                              (df['close'] > df['swlo_20'].shift(1)) & \
                              (df['close'] > df['open'])
    # Volume burst (if volume data is meaningful)
    if 'volume' in df.columns:
        df['vol_ma20'] = df['volume'].rolling(20).mean()
        df['vol_burst'] = df['volume'] > df['vol_ma20'] * 1.5
    else:
        df['vol_burst'] = True  # assume always pass if no volume
    # Time-of-day for intraday
    df['hour_utc'] = df['time'].dt.hour
    df['weekday'] = df['time'].dt.dayofweek  # 0=Mon
    df['us_session'] = df['hour_utc'].isin([13, 14, 15, 16, 17, 18, 19])  # ~9am-4pm ET UTC (DST adjusted)
    # RSI oversold reset (RSI was <= 40 in last 5 bars and now crossing back up)
    if 'RSI' in df.columns:
        df['rsi_was_below_40'] = (df['RSI'].rolling(5).min() <= 40)
        df['rsi_now_above_45'] = df['RSI'] >= 45
        df['rsi_oversold_reset'] = df['rsi_was_below_40'] & df['rsi_now_above_45']
    return df


def run_long_strat(df, signal_func, target_r, max_bars, name, tf, stop_atr_mult=0.5, be=True, trail_at=None):
    """Run generic LONG strategy with custom signal function."""
    trades = []
    for i in range(200, len(df) - 1):
        row = df.iloc[i]
        if not signal_func(df, i, row): continue
        entry = row['close']; atr = row['atr14']
        if pd.isna(atr) or atr <= 0: continue
        stop = row['low'] - atr * stop_atr_mult
        R = abs(entry - stop)
        if R <= 0 or R / atr > 5: continue
        res = simulate_trade(df, i, 'LONG', entry, stop, target_r, max_bars,
                              be_at_1r=be, trail_at=trail_at)
        if not res: continue
        res.update({'entry_time': row['time'], 'entry_price': entry, 'stop_price': stop,
                    'direction': 'LONG', 'r_planned': target_r, 'strategy': name, 'tf': tf})
        trades.append(res)
    return trades


def main():
    print("=== Loading + adding indicators ===")
    data = {tf: load(p) for tf, p in FILES.items()}
    df1d = data['1D']; df12 = data['12H']
    df4 = data['4H']; df1 = data['1H']; df30 = data['30M']

    # HTF context for 4H and 1H
    df4 = htf_context(df4, df12, 'htf12h')
    df4 = htf_context(df4, df1d, 'htf1d')
    df1 = htf_context(df1, df4, 'htf4h')
    df1 = htf_context(df1, df12, 'htf12h')
    df1 = htf_context(df1, df1d, 'htf1d')
    df30 = htf_context(df30, df1, 'htf1h')
    df30 = htf_context(df30, df4, 'htf4h')
    df30 = htf_context(df30, df1d, 'htf1d')

    # Add new indicators
    for d in [df4, df1, df30]:
        add_indicators(d)

    summaries = []
    trades_by = {}

    # =============================================================
    # HYPOTHESIS 1 — Bollinger Band Squeeze Breakout (4H)
    # =============================================================
    def sig_bb_squeeze_break(df, i, row):
        # Prior bar was in squeeze, current bar breaks above prior BB upper
        prev_squeeze = df.at[i-1, 'bb_squeeze'] if i >= 1 else False
        if not prev_squeeze: return False
        if not (row['close'] > df.at[i-1, 'bb_upper']): return False
        if not (row['close'] > row['open'] and row['body_to_range'] >= 0.5): return False
        # Bull regime
        if not row.get('ema50_above_ema200', False): return False
        if not row.get('close_above_ema200', False): return False
        return True

    print("\n=== H1: BB Squeeze Breakout ===")
    for tf_label, df_use, tr, mb in [('4H', df4, 3.0, 24), ('4H', df4, 4.0, 30), ('1H', df1, 2.5, 16)]:
        for target_r in [tr]:
            name = f'H1_BB_squeeze_breakout_{tf_label}_target{target_r}R'
            t = run_long_strat(df_use, sig_bb_squeeze_break, target_r, mb, name, tf_label)
            summaries.append({'strategy': name, **metrics(t)})
            trades_by[name] = t

    # =============================================================
    # HYPOTHESIS 2 — Failed Breakdown + Reclaim
    # =============================================================
    def sig_failed_breakdown(df, i, row):
        if not row.get('failed_breakdown', False): return False
        # Bull regime
        if not row.get('close_above_ema200', False): return False
        if not row.get('ema50_above_ema200', False): return False
        return True

    print("\n=== H2: Failed Breakdown ===")
    for tf_label, df_use, tr, mb in [('4H', df4, 2.5, 20), ('4H', df4, 3.5, 24), ('1H', df1, 2.0, 12), ('1H', df1, 3.0, 16)]:
        name = f'H2_failed_breakdown_{tf_label}_target{tr}R'
        t = run_long_strat(df_use, sig_failed_breakdown, tr, mb, name, tf_label)
        summaries.append({'strategy': name, **metrics(t)})
        trades_by[name] = t

    # =============================================================
    # HYPOTHESIS 3 — Higher Low (HL) Pattern in Bull Regime
    # =============================================================
    def sig_hl_pattern(df, i, row):
        if not row.get('hl_pattern', False): return False
        if not row.get('close_above_ema50', False): return False
        if not row.get('ema50_above_ema200', False): return False
        return True

    print("\n=== H3: Higher Low Pattern ===")
    for tf_label, df_use, tr, mb in [('4H', df4, 3.0, 20), ('1H', df1, 2.5, 16)]:
        name = f'H3_higher_low_{tf_label}_target{tr}R'
        t = run_long_strat(df_use, sig_hl_pattern, tr, mb, name, tf_label)
        summaries.append({'strategy': name, **metrics(t)})
        trades_by[name] = t

    # =============================================================
    # HYPOTHESIS 4 — Inside Bar Breakout in Trend
    # =============================================================
    def sig_inside_bar_break(df, i, row):
        prev_inside = df.at[i-1, 'inside_bar'] if i >= 1 else False
        if not prev_inside: return False
        prev_high = df.at[i-1, 'high']
        if not (row['close'] > prev_high): return False
        if not (row['close'] > row['open'] and row['body_to_range'] >= 0.4): return False
        if not row.get('close_above_ema50', False): return False
        if not row.get('ema50_above_ema200', False): return False
        return True

    print("\n=== H4: Inside Bar Breakout in Trend ===")
    for tf_label, df_use, tr, mb in [('4H', df4, 3.0, 16), ('1H', df1, 2.5, 12)]:
        name = f'H4_inside_bar_break_{tf_label}_target{tr}R'
        t = run_long_strat(df_use, sig_inside_bar_break, tr, mb, name, tf_label)
        summaries.append({'strategy': name, **metrics(t)})
        trades_by[name] = t

    # =============================================================
    # HYPOTHESIS 5 — Hammer Reversal in Bull Trend
    # =============================================================
    def sig_hammer_in_trend(df, i, row):
        if not row.get('hammer', False): return False
        if not row.get('close_above_ema200', False): return False
        if not row.get('ema50_above_ema200', False): return False
        # And bar low touched EMA20 or below (pullback)
        ema20 = row.get('ema20', np.nan)
        if pd.isna(ema20): return False
        if row['low'] > ema20 * 1.005: return False  # didn't touch
        return True

    print("\n=== H5: Hammer in Bull Trend ===")
    for tf_label, df_use, tr, mb in [('4H', df4, 3.0, 20), ('1H', df1, 2.5, 16)]:
        name = f'H5_hammer_in_trend_{tf_label}_target{tr}R'
        t = run_long_strat(df_use, sig_hammer_in_trend, tr, mb, name, tf_label)
        summaries.append({'strategy': name, **metrics(t)})
        trades_by[name] = t

    # =============================================================
    # HYPOTHESIS 6 — RSI Oversold Reset in Bull Trend
    # =============================================================
    def sig_rsi_reset(df, i, row):
        if not row.get('rsi_oversold_reset', False): return False
        if not (row['close'] > row['open']): return False
        if not row.get('close_above_ema200', False): return False
        if not row.get('ema50_above_ema200', False): return False
        return True

    print("\n=== H6: RSI Oversold Reset ===")
    for tf_label, df_use, tr, mb in [('4H', df4, 3.0, 20), ('1H', df1, 2.5, 16), ('30M', df30, 2.0, 12)]:
        name = f'H6_rsi_reset_{tf_label}_target{tr}R'
        t = run_long_strat(df_use, sig_rsi_reset, tr, mb, name, tf_label)
        summaries.append({'strategy': name, **metrics(t)})
        trades_by[name] = t

    # =============================================================
    # HYPOTHESIS 7 — Multi-TF Strict (1D+12H+4H+1H all bullish)
    # =============================================================
    def sig_strict_multi_tf(df, i, row):
        # All HTF bullish + price > EMA10 (fast pullback in mega-trend)
        if not row.get('htf1d_bullish', False): return False
        if not row.get('htf12h_bullish', False): return False
        if not row.get('htf4h_bullish', False): return False
        if not row.get('close_above_ema50', False): return False
        # Pullback to EMA10 with reclaim
        ema10 = row.get('ema10', np.nan)
        if pd.isna(ema10): return False
        if not (row['low'] <= ema10 * 1.003 and row['close'] > ema10): return False
        if not (row['close'] > row['open']): return False
        return True

    print("\n=== H7: Multi-TF Strict 1H ===")
    name = 'H7_multi_tf_strict_1H_pullback_EMA10'
    t = run_long_strat(df1, sig_strict_multi_tf, 2.0, 16, name, '1H')
    summaries.append({'strategy': name, **metrics(t)})
    trades_by[name] = t

    name = 'H7_multi_tf_strict_1H_pullback_EMA10_target3R'
    t = run_long_strat(df1, sig_strict_multi_tf, 3.0, 20, name, '1H')
    summaries.append({'strategy': name, **metrics(t)})
    trades_by[name] = t

    # =============================================================
    # HYPOTHESIS 8 — Bullish Engulfing in Pullback
    # =============================================================
    def sig_bull_engulf_pullback(df, i, row):
        if not row.get('bull_engulf', False): return False
        if not row.get('close_above_ema200', False): return False
        if not row.get('ema50_above_ema200', False): return False
        # Came from pullback to EMA50 area
        ema50 = row.get('ema50', np.nan)
        if pd.isna(ema50): return False
        if row['low'] > ema50 * 1.01: return False  # within 1% of EMA50
        return True

    print("\n=== H8: Bullish Engulfing at EMA50 ===")
    for tf_label, df_use, tr, mb in [('4H', df4, 3.0, 20), ('1H', df1, 2.5, 16)]:
        name = f'H8_bull_engulf_EMA50_{tf_label}_target{tr}R'
        t = run_long_strat(df_use, sig_bull_engulf_pullback, tr, mb, name, tf_label)
        summaries.append({'strategy': name, **metrics(t)})
        trades_by[name] = t

    # =============================================================
    # HYPOTHESIS 9 — US Session Filter for 1H
    # =============================================================
    def sig_breakout_us_session(df, i, row):
        if not row.get('us_session', False): return False
        if not (row['close'] > row['open'] and row['body_to_range'] >= 0.5): return False
        if not (row['close'] > df.at[i-1, 'swhi_10']): return False
        if not row.get('close_above_ema200', False): return False
        if not row.get('ema50_above_ema200', False): return False
        if not row.get('atr_expanding', False): return False
        return True

    print("\n=== H9: Breakout filtered by US Session ===")
    name = 'H9_breakout_us_session_1H_target3R'
    t = run_long_strat(df1, sig_breakout_us_session, 3.0, 16, name, '1H')
    summaries.append({'strategy': name, **metrics(t)})
    trades_by[name] = t

    name = 'H9_breakout_us_session_1H_target2R'
    t = run_long_strat(df1, sig_breakout_us_session, 2.0, 12, name, '1H')
    summaries.append({'strategy': name, **metrics(t)})
    trades_by[name] = t

    # =============================================================
    # HYPOTHESIS 10 — Bull Flag (impulse + tight consol + break)
    # =============================================================
    def sig_bull_flag(df, i, row):
        # Look at last 10 bars: was there a strong impulse 8-10 bars ago?
        if i < 12: return False
        impulse_start = df.at[i-10, 'close']
        impulse_end = df.at[i-5, 'close']
        if impulse_end <= impulse_start * 1.02: return False  # need 2%+ move
        # Last 5 bars consolidate within 50% of impulse range
        impulse_range = impulse_end - impulse_start
        consol_high = df['high'].iloc[i-5:i].max()
        consol_low = df['low'].iloc[i-5:i].min()
        if (consol_high - consol_low) > impulse_range * 0.6: return False
        # Current bar breaks above consol_high
        if row['close'] <= consol_high: return False
        if not (row['close'] > row['open'] and row['body_to_range'] >= 0.5): return False
        if not row.get('close_above_ema200', False): return False
        return True

    print("\n=== H10: Bull Flag ===")
    for tf_label, df_use, tr, mb in [('4H', df4, 3.0, 16), ('1H', df1, 2.5, 12)]:
        name = f'H10_bull_flag_{tf_label}_target{tr}R'
        t = run_long_strat(df_use, sig_bull_flag, tr, mb, name, tf_label)
        summaries.append({'strategy': name, **metrics(t)})
        trades_by[name] = t

    # =============================================================
    # HYPOTHESIS 11 — Regular Bullish Divergence in trend
    # =============================================================
    def sig_bull_div(df, i, row):
        bull_div = (row.get('Regular Bullish', 0) or 0) != 0
        if not bull_div: return False
        if not (row['close'] > row['open']): return False
        if not row.get('ema50_above_ema200', False): return False
        return True

    print("\n=== H11: Regular Bullish Divergence ===")
    for tf_label, df_use, tr, mb in [('4H', df4, 3.0, 20), ('1H', df1, 2.5, 16)]:
        name = f'H11_bull_div_{tf_label}_target{tr}R'
        t = run_long_strat(df_use, sig_bull_div, tr, mb, name, tf_label)
        summaries.append({'strategy': name, **metrics(t)})
        trades_by[name] = t

    # =============================================================
    # HYPOTHESIS 12 — Volume Burst Breakout (if volume meaningful)
    # =============================================================
    def sig_vol_breakout(df, i, row):
        if not row.get('vol_burst', False): return False
        if not (row['close'] > row['open'] and row['body_to_range'] >= 0.5): return False
        if not (row['close'] > df.at[i-1, 'swhi_10']): return False
        if not row.get('ema50_above_ema200', False): return False
        if not row.get('close_above_ema200', False): return False
        return True

    print("\n=== H12: Volume Burst Breakout ===")
    for tf_label, df_use, tr, mb in [('4H', df4, 3.0, 20), ('1H', df1, 2.5, 16)]:
        name = f'H12_vol_burst_{tf_label}_target{tr}R'
        t = run_long_strat(df_use, sig_vol_breakout, tr, mb, name, tf_label)
        summaries.append({'strategy': name, **metrics(t)})
        trades_by[name] = t

    # =============================================================
    # SUMMARY
    # =============================================================
    df_res = pd.DataFrame(summaries).sort_values('total_r_net', ascending=False)
    df_res.to_csv(OUT_DIR / 'US500_exhaustive_search_summary.csv', index=False)

    cols = ['strategy','n','trades_per_week','trades_per_month','total_r_net','avg_r_net',
            'win_rate','pf_net','max_losing_streak','r_no_top5_net','r_no_top10_net']

    print("\n=== Top 15 candidates (by total_r_net) ===")
    print(df_res[cols].head(15).to_string(index=False))

    print("\n=== Top 5 yearly breakdown ===")
    for name in df_res['strategy'].head(5):
        t = trades_by.get(name, [])
        if t:
            print(f"\n--- {name} ---")
            print(yearly_metrics(t).to_string(index=False))

    # Save top swing + intraday
    swing_pool = df_res[df_res['strategy'].str.contains('_4H_')]
    intra_pool = df_res[df_res['strategy'].str.contains('_1H_|_30M_|_15M_')]
    if len(swing_pool) > 0:
        top_sw = swing_pool['strategy'].iloc[0]
        if trades_by.get(top_sw):
            pd.DataFrame(trades_by[top_sw]).to_csv(OUT_DIR / 'US500_exhaustive_top_swing_trades.csv', index=False)
            print(f"\nTop swing: {top_sw} ({len(trades_by[top_sw])} trades)")
    if len(intra_pool) > 0:
        top_in = intra_pool['strategy'].iloc[0]
        if trades_by.get(top_in):
            pd.DataFrame(trades_by[top_in]).to_csv(OUT_DIR / 'US500_exhaustive_top_intraday_trades.csv', index=False)
            print(f"Top intraday: {top_in} ({len(trades_by[top_in])} trades)")


if __name__ == '__main__':
    main()
