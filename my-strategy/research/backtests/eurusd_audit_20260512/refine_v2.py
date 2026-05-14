#!/usr/bin/env python3
"""Refine top EURUSD V2 winners — G1 (4H swing) + G5 (1H decisive intraday)."""
import pandas as pd
import numpy as np
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent))
from backtest_eurusd import (load, load_macro_dxy, attach_dxy, htf_context,
                              simulate_trade, run_long, metrics, yearly_metrics,
                              SPREAD_R, OUT_DIR)
from audit_v2 import FILES_V2, add_extra_indicators


def main():
    print("=== Loading + indicators ===")
    data = {tf: load(p) for tf, p in FILES_V2.items()}
    df1d, df12, df4, df1, df30 = data['1D'], data['12H'], data['4H'], data['1H'], data['30M']
    df4 = htf_context(df4, df12, 'htf12h')
    df4 = htf_context(df4, df1d, 'htf1d')
    df1 = htf_context(df1, df4, 'htf4h')
    df1 = htf_context(df1, df12, 'htf12h')
    df1 = htf_context(df1, df1d, 'htf1d')
    df_dxy = load_macro_dxy()
    df4 = attach_dxy(df4, df_dxy)
    df1 = attach_dxy(df1, df_dxy)
    for d in [df4, df1]:
        add_extra_indicators(d)

    summaries = []
    trades_by = {}

    # =============================================================
    # SWING G1 REFINEMENT
    # Base: multi-TF strict (htf12h + htf1d bullish + close>EMA200 + EMA50>EMA200 + ATR exp + RSI>MA + breakout swhi10 + body>=0.5)
    # =============================================================
    print("\n=== SWING refinement (G1 base + variants) ===")

    def sig_swing_base(df, i, row):
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

    # Variants: add filters to improve quality
    def sig_swing_adx20(df, i, row):
        if not sig_swing_base(df, i, row): return False
        adx = row.get('adx14', np.nan)
        if pd.isna(adx) or adx < 20: return False
        return True

    def sig_swing_adx25(df, i, row):
        if not sig_swing_base(df, i, row): return False
        adx = row.get('adx14', np.nan)
        if pd.isna(adx) or adx < 25: return False
        return True

    def sig_swing_body60(df, i, row):
        if not sig_swing_base(df, i, row): return False
        return row['body_pct'] >= 0.6

    def sig_swing_body70(df, i, row):
        if not sig_swing_base(df, i, row): return False
        return row['body_pct'] >= 0.7

    def sig_swing_range_atr(df, i, row):
        if not sig_swing_base(df, i, row): return False
        atr = row.get('atr14', np.nan)
        if pd.isna(atr): return False
        return (row['high'] - row['low']) >= 1.2 * atr

    def sig_swing_dxy_strong_bear(df, i, row):
        if not sig_swing_base(df, i, row): return False
        # DXY in macro bear: close < EMA50 + falling slope
        if not row.get('dxy_bearish', False): return False
        if not row.get('dxy_falling', False): return False
        return True

    def sig_swing_combo_best(df, i, row):
        """Combine best filters: body 60% + ADX 25 + DXY bear"""
        if not sig_swing_base(df, i, row): return False
        if row['body_pct'] < 0.6: return False
        adx = row.get('adx14', np.nan)
        if pd.isna(adx) or adx < 25: return False
        if not row.get('dxy_bearish', False): return False
        return True

    def sig_swing_combo_strict(df, i, row):
        """All quality filters"""
        if not sig_swing_base(df, i, row): return False
        if row['body_pct'] < 0.6: return False
        adx = row.get('adx14', np.nan)
        if pd.isna(adx) or adx < 25: return False
        atr = row.get('atr14', np.nan)
        if pd.isna(atr): return False
        if (row['high'] - row['low']) < 1.2 * atr: return False
        if not row.get('dxy_bearish', False): return False
        return True

    swing_variants = [
        ('base_no_DXY', sig_swing_base),
        ('+ADX20', sig_swing_adx20),
        ('+ADX25', sig_swing_adx25),
        ('+body60', sig_swing_body60),
        ('+body70', sig_swing_body70),
        ('+range_>1.2ATR', sig_swing_range_atr),
        ('+DXY_strong_bear', sig_swing_dxy_strong_bear),
        ('+combo_body60_ADX25_DXY', sig_swing_combo_best),
        ('+combo_strict_all', sig_swing_combo_strict),
    ]
    for sig_name, sig_func in swing_variants:
        for trg in [2.5, 3.0]:
            name = f'SWING_4H_{sig_name}_target{trg}R'
            t = run_long(df4, sig_func, trg, 24, name, '4H')
            summaries.append({'strategy': name, **metrics(t)})
            trades_by[name] = t

    # =============================================================
    # INTRADAY G5 REFINEMENT (1H decisive breakout)
    # =============================================================
    print("\n=== INTRADAY refinement (G5 decisive base) ===")

    def sig_intra_base(df, i, row):
        # Body 70% + range > 1.5 ATR + breakout swhi10 + RSI > MA + EMA stack + ATR expanding
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

    def sig_intra_htf1d(df, i, row):
        if not sig_intra_base(df, i, row): return False
        return row.get('htf1d_bullish', False)

    def sig_intra_htf1d_4h(df, i, row):
        if not sig_intra_base(df, i, row): return False
        if not row.get('htf1d_bullish', False): return False
        if not row.get('htf4h_bullish', False): return False
        return True

    def sig_intra_htf1d_dxy(df, i, row):
        if not sig_intra_htf1d(df, i, row): return False
        if not row.get('dxy_bearish', False): return False
        return True

    def sig_intra_htf1d_4h_dxy(df, i, row):
        if not sig_intra_htf1d_4h(df, i, row): return False
        if not row.get('dxy_bearish', False): return False
        return True

    def sig_intra_htf1d_session(df, i, row):
        """Decisive + HTF1D + restrict to London/NY session"""
        if not sig_intra_htf1d(df, i, row): return False
        return row.get('london_session', False) or row.get('ny_session', False)

    def sig_intra_full_combo(df, i, row):
        """ALL filters: decisive + HTF1D + HTF4H + DXY + session"""
        if not sig_intra_htf1d_4h_dxy(df, i, row): return False
        return row.get('london_session', False) or row.get('ny_session', False)

    intra_variants = [
        ('base', sig_intra_base),
        ('+HTF1D', sig_intra_htf1d),
        ('+HTF1D+4H', sig_intra_htf1d_4h),
        ('+HTF1D+DXY', sig_intra_htf1d_dxy),
        ('+HTF1D+4H+DXY', sig_intra_htf1d_4h_dxy),
        ('+HTF1D+session', sig_intra_htf1d_session),
        ('+ALL_filters', sig_intra_full_combo),
    ]
    for sig_name, sig_func in intra_variants:
        for trg in [2.0, 2.5, 3.0, 4.0]:
            name = f'INTRA_1H_{sig_name}_target{trg}R'
            t = run_long(df1, sig_func, trg, 20, name, '1H')
            summaries.append({'strategy': name, **metrics(t)})
            trades_by[name] = t

    # =============================================================
    # OUTPUT
    # =============================================================
    df_res = pd.DataFrame(summaries).sort_values('total_r_net', ascending=False)
    df_res.to_csv(OUT_DIR / 'EURUSD_V2_refined.csv', index=False)

    cols = ['strategy', 'n', 'trades_per_week', 'trades_per_month', 'total_r_net',
            'avg_r_net', 'win_rate', 'pf_net', 'max_losing_streak',
            'r_no_top5_net', 'r_no_top10_net']

    swing_df = df_res[df_res['strategy'].str.contains('SWING_4H')]
    intra_df = df_res[df_res['strategy'].str.contains('INTRA_1H')]

    print("\n=== Top 10 SWING ===")
    print(swing_df[cols].head(10).to_string(index=False))

    print("\n=== Top 10 INTRADAY ===")
    print(intra_df[cols].head(10).to_string(index=False))

    print("\n=== Top 3 SWING yearly ===")
    for name in swing_df['strategy'].head(3):
        t = trades_by.get(name, [])
        if t:
            print(f"\n--- {name} ---")
            print(yearly_metrics(t).to_string(index=False))

    print("\n=== Top 3 INTRADAY yearly ===")
    for name in intra_df['strategy'].head(3):
        t = trades_by.get(name, [])
        if t:
            print(f"\n--- {name} ---")
            print(yearly_metrics(t).to_string(index=False))


if __name__ == '__main__':
    main()
