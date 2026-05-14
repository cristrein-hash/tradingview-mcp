#!/usr/bin/env python3
"""EURUSD-specific hypotheses: forex-style patterns + session timing."""
import pandas as pd
import numpy as np
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent))
from backtest_eurusd import (load, load_macro_dxy, attach_dxy, htf_context,
                              simulate_trade, run_long, metrics, yearly_metrics,
                              FILES, SPREAD_R, OUT_DIR)


def main():
    data = {tf: load(p) for tf, p in FILES.items()}
    df4, df30 = data['4H'], data['30M']
    df12, df1d = data['12H'], data['1D']
    df4 = htf_context(df4, df12, 'htf12h')
    df4 = htf_context(df4, df1d, 'htf1d')
    df30 = htf_context(df30, df4, 'htf4h')
    df30 = htf_context(df30, df12, 'htf12h')
    df30 = htf_context(df30, df1d, 'htf1d')
    df_dxy = load_macro_dxy()
    df4 = attach_dxy(df4, df_dxy)
    df30 = attach_dxy(df30, df_dxy)

    summaries = []
    trades_by = {}

    # =============================================================
    # H1. London Session Breakout 30M (8-10 UTC)
    # =============================================================
    def sig_london_open_breakout(df, i, row):
        if not row.get('hour_utc') in [8, 9]: return False
        # Need range from Asia (1-7 UTC)
        # Simplification: just check breakout above 6-bar swing high
        if not (row['close'] > df.at[i-1, 'swhi_10']): return False
        if not (row['close'] > row['open'] and row['body_pct'] >= 0.5): return False
        if not row.get('htf4h_bullish', False): return False
        return True

    print("=== H1. London Open Breakout 30M ===")
    for trg in [2.0, 2.5, 3.0]:
        name = f'H1_london_open_30M_target{trg}R'
        t = run_long(df30, sig_london_open_breakout, trg, 16, name, '30M')
        summaries.append({'strategy': name, **metrics(t)})
        trades_by[name] = t

    # =============================================================
    # H2. EMA20 fast pullback (forex respects EMA20 strongly)
    # =============================================================
    def sig_ema20_pullback(df, i, row):
        ema20 = row.get('ema20', np.nan)
        if pd.isna(ema20): return False
        if not (row['low'] <= ema20 and row['close'] > ema20): return False
        if not (row['close'] > row['open'] and row['body_pct'] >= 0.4): return False
        if not row.get('ema50_above_ema200', False): return False
        if not row.get('close_above_ema200', False): return False
        return True

    print("\n=== H2. EMA20 Pullback ===")
    for tf_label, df_use, trg, mb in [('4H', df4, 2.5, 16), ('4H', df4, 3.0, 20),
                                        ('30M', df30, 2.0, 12), ('30M', df30, 2.5, 16)]:
        name = f'H2_EMA20_pullback_{tf_label}_target{trg}R'
        t = run_long(df_use, sig_ema20_pullback, trg, mb, name, tf_label)
        summaries.append({'strategy': name, **metrics(t)})
        trades_by[name] = t

    # =============================================================
    # H3. Strict multi-TF aligned (1D + 12H + 4H all bullish) + EMA20 pullback
    # =============================================================
    def sig_multi_tf_pullback(df, i, row):
        if not row.get('htf1d_bullish', False): return False
        if not row.get('htf12h_bullish', False): return False
        if not row.get('htf4h_bullish', False): return False
        ema20 = row.get('ema20', np.nan)
        if pd.isna(ema20): return False
        if not (row['low'] <= ema20 * 1.002 and row['close'] > ema20): return False
        if not (row['close'] > row['open'] and row['body_pct'] >= 0.4): return False
        return True

    print("\n=== H3. Strict Multi-TF Pullback EMA20 ===")
    for trg in [2.0, 2.5, 3.0]:
        name = f'H3_multi_TF_pullback_30M_target{trg}R'
        t = run_long(df30, sig_multi_tf_pullback, trg, 16, name, '30M')
        summaries.append({'strategy': name, **metrics(t)})
        trades_by[name] = t

    # =============================================================
    # H4. Failed Breakdown + DXY bearish + ATR expanding (combined macro+technical)
    # =============================================================
    def sig_fb_full_macro(df, i, row):
        if not row.get('failed_breakdown', False): return False
        if not (row['close'] > row['open'] and row['body_pct'] >= 0.4): return False
        if not row.get('ema50_above_ema200', False): return False
        if not row.get('dxy_bearish', False): return False
        if not row.get('atr_expanding', False): return False
        return True

    print("\n=== H4. Failed Breakdown + DXY bearish ===")
    for trg in [2.0, 2.5, 3.0]:
        name = f'H4_FB_DXY_bearish_4H_target{trg}R'
        t = run_long(df4, sig_fb_full_macro, trg, 20, name, '4H')
        summaries.append({'strategy': name, **metrics(t)})
        trades_by[name] = t

    # =============================================================
    # H5. Inside bar break in trend
    # =============================================================
    def sig_inside_bar_break_eu(df, i, row):
        prev_inside = df.at[i-1, 'inside_bar'] if i >= 1 else False
        if not prev_inside: return False
        prev_high = df.at[i-1, 'high']
        if not (row['close'] > prev_high): return False
        if not (row['close'] > row['open'] and row['body_pct'] >= 0.4): return False
        if not row.get('close_above_ema50', False): return False
        if not row.get('ema50_above_ema200', False): return False
        return True

    print("\n=== H5. Inside Bar Break ===")
    for tf_label, df_use, trg in [('4H', df4, 2.5), ('30M', df30, 2.0)]:
        name = f'H5_inside_bar_break_{tf_label}_target{trg}R'
        t = run_long(df_use, sig_inside_bar_break_eu, trg, 16, name, tf_label)
        summaries.append({'strategy': name, **metrics(t)})
        trades_by[name] = t

    # =============================================================
    # H6. Mean reversion bounce (oversold in uptrend)
    # =============================================================
    def sig_oversold_bounce(df, i, row):
        rsi = row.get('RSI', np.nan)
        if pd.isna(rsi): return False
        # RSI was below 35 in last 3 bars and now bouncing
        rsi_low = df['RSI'].iloc[max(0,i-3):i].min()
        if rsi_low > 35: return False
        if rsi < 40 or rsi > 55: return False  # Bouncing
        if not (row['close'] > row['open']): return False
        if not row.get('ema50_above_ema200', False): return False
        if not row.get('close_above_ema200', False): return False
        return True

    print("\n=== H6. RSI Oversold Bounce in Uptrend ===")
    for tf_label, df_use, trg in [('4H', df4, 2.5), ('4H', df4, 3.0), ('30M', df30, 2.0)]:
        name = f'H6_RSI_oversold_bounce_{tf_label}_target{trg}R'
        t = run_long(df_use, sig_oversold_bounce, trg, 16, name, tf_label)
        summaries.append({'strategy': name, **metrics(t)})
        trades_by[name] = t

    # =============================================================
    # H7. 4H Breakout + DXY DECLINING TODAY (slope < 0 strong)
    # =============================================================
    def sig_4h_breakout_dxy_declining(df, i, row):
        if not (row['close'] > row['open'] and row['body_pct'] >= 0.5
                and row['close'] > df.at[i-1, 'swhi_10']): return False
        rsi = row.get('RSI', np.nan); rsi_ma = row.get('RSI-based MA', np.nan)
        if pd.isna(rsi) or pd.isna(rsi_ma) or rsi <= rsi_ma: return False
        if not row.get('close_above_ema200', False): return False
        if not row.get('ema50_above_ema200', False): return False
        if not row.get('dxy_below_ema200', False): return False  # DXY in macro bear
        if not row.get('dxy_falling', False): return False  # currently falling
        return True

    print("\n=== H7. 4H Breakout + DXY in MACRO bear regime ===")
    for trg in [2.5, 3.0, 4.0]:
        name = f'H7_4H_breakout_DXY_macro_bear_target{trg}R'
        t = run_long(df4, sig_4h_breakout_dxy_declining, trg, 24, name, '4H')
        summaries.append({'strategy': name, **metrics(t)})
        trades_by[name] = t

    # =============================================================
    # OUTPUT
    # =============================================================
    df_res = pd.DataFrame(summaries).sort_values('total_r_net', ascending=False)
    df_res.to_csv(OUT_DIR / 'EURUSD_forex_specific_summary.csv', index=False)
    cols = ['strategy','n','trades_per_week','trades_per_month','total_r_net','avg_r_net',
            'win_rate','pf_net','max_losing_streak','r_no_top5_net','r_no_top10_net']

    print("\n=== ALL sorted by total_r_net ===")
    print(df_res[cols].to_string(index=False))

    print("\n=== Top 5 yearly ===")
    for name in df_res['strategy'].head(5):
        t = trades_by.get(name, [])
        if t and len(t) > 0:
            print(f"\n--- {name} ---")
            print(yearly_metrics(t).to_string(index=False))


if __name__ == '__main__':
    main()
