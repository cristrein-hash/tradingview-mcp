#!/usr/bin/env python3
"""Refined strategies + temporal stability + filter analysis on 1H/4H."""
import pandas as pd
import numpy as np
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent))
from backtest_xauusd import load, simulate_trade, trade_metrics, strategy_rejection_close, strategy_momentum_continuation, FILES, OUT_DIR


def metrics_by_year(trades: list) -> pd.DataFrame:
    if not trades:
        return pd.DataFrame()
    df = pd.DataFrame(trades)
    df['year'] = pd.to_datetime(df['entry_time']).dt.year
    out = df.groupby('year').agg(
        n=('r_outcome', 'count'),
        total_r=('r_outcome', 'sum'),
        avg_r=('r_outcome', 'mean'),
        win_rate=('r_outcome', lambda r: (r > 0).mean()),
    ).round(3).reset_index()
    return out


def main():
    data = {tf: load(p) for tf, p in FILES.items()}
    df4, df1, df30, df15 = data['4H'], data['1H'], data['30M'], data['15M']
    results = []

    # =========================================================
    # Refined 4H swing: LONG breakout with RSI extreme exit filter
    # =========================================================
    # Use momentum continuation but add RSI > 50 filter AND keep low frequency
    # Try with body_max tighter to be more selective on rejection
    print("=== 4H REFINED SWING ===")

    # 4H LONG rejection + RSI <= 35 (oversold-ish but not pristine 30)
    t = strategy_rejection_close(df4, 'LONG', target_r=3.0, max_bars=30, be=True,
        trail=True, trail_dist=1.5,
        require_rsi_extreme=True, rsi_oversold=35,
        wick_min=0.5, body_max=0.4,
        tf_label='4H', name='REF_4H_LONG_rejection_rsi35_trail')
    by_year = metrics_by_year(t)
    print("4H LONG rejection RSI<=35 trail+3R per year:")
    print(by_year.to_string(index=False))
    m = trade_metrics(t, '4H', 'REF_4H_LONG_rejection_rsi35_trail', df4['time'].min(), df4['time'].max())
    results.append(m)

    # 4H LONG rejection + RSI <= 40 (more permissive)
    t = strategy_rejection_close(df4, 'LONG', target_r=3.0, max_bars=30, be=True,
        trail=False, require_rsi_extreme=True, rsi_oversold=40,
        wick_min=0.5, body_max=0.4,
        tf_label='4H', name='REF_4H_LONG_rejection_rsi40_target3R')
    print("\n4H LONG rejection RSI<=40 target=3R per year:")
    print(metrics_by_year(t).to_string(index=False))
    results.append(trade_metrics(t, '4H', 'REF_4H_LONG_rejection_rsi40_target3R', df4['time'].min(), df4['time'].max()))

    # 4H LONG breakout — more selective: require RSI > MA (momentum confirmation)
    t = strategy_momentum_continuation(df4, 'LONG', target_r=4.0, max_bars=24, be=True,
        rsi_filter=True, name='REF_4H_LONG_breakout_target4R', tf_label='4H')
    print("\n4H LONG breakout target=4R per year:")
    print(metrics_by_year(t).to_string(index=False))
    results.append(trade_metrics(t, '4H', 'REF_4H_LONG_breakout_target4R', df4['time'].min(), df4['time'].max()))

    # =========================================================
    # Refined 1H execution
    # =========================================================
    print("\n=== 1H REFINED EXECUTION ===")

    # 1H LONG rejection + RSI <= 35 (oversold)
    t = strategy_rejection_close(df1, 'LONG', target_r=3.0, max_bars=48, be=True,
        trail=True, trail_dist=0.75,
        require_rsi_extreme=True, rsi_oversold=35,
        wick_min=0.5, body_max=0.4,
        tf_label='1H', name='REF_1H_LONG_rejection_rsi35_trail')
    print("1H LONG rejection RSI<=35 per year:")
    print(metrics_by_year(t).to_string(index=False))
    results.append(trade_metrics(t, '1H', 'REF_1H_LONG_rejection_rsi35_trail', df1['time'].min(), df1['time'].max()))

    # 1H LONG rejection + RSI <= 40
    t = strategy_rejection_close(df1, 'LONG', target_r=2.5, max_bars=36, be=True,
        require_rsi_extreme=True, rsi_oversold=40,
        wick_min=0.5, body_max=0.4,
        tf_label='1H', name='REF_1H_LONG_rejection_rsi40_target25R')
    print("\n1H LONG rejection RSI<=40 target=2.5R per year:")
    print(metrics_by_year(t).to_string(index=False))
    results.append(trade_metrics(t, '1H', 'REF_1H_LONG_rejection_rsi40_target25R', df1['time'].min(), df1['time'].max()))

    # 1H LONG rejection + RSI < 40 + divergence
    t = strategy_rejection_close(df1, 'LONG', target_r=2.5, max_bars=36, be=True,
        require_rsi_extreme=True, rsi_oversold=40, require_div=True,
        wick_min=0.5, body_max=0.4,
        tf_label='1H', name='REF_1H_LONG_rejection_rsi40_div_target25R')
    print("\n1H LONG rejection RSI<=40 + divergence per year:")
    print(metrics_by_year(t).to_string(index=False))
    results.append(trade_metrics(t, '1H', 'REF_1H_LONG_rejection_rsi40_div_target25R', df1['time'].min(), df1['time'].max()))

    # =========================================================
    # Refined 30M intraday
    # =========================================================
    print("\n=== 30M REFINED INTRADAY ===")
    t = strategy_rejection_close(df30, 'LONG', target_r=2.5, max_bars=36, be=True,
        require_rsi_extreme=True, rsi_oversold=35,
        wick_min=0.55, body_max=0.4,
        tf_label='30M', name='REF_30M_LONG_rejection_rsi35_target25R')
    print("30M LONG rejection RSI<=35 per year:")
    print(metrics_by_year(t).to_string(index=False))
    results.append(trade_metrics(t, '30M', 'REF_30M_LONG_rejection_rsi35_target25R', df30['time'].min(), df30['time'].max()))

    # =========================================================
    # Save and report
    # =========================================================
    refined_df = pd.DataFrame([{k: v for k, v in r.items() if k != 'by_direction'} for r in results])
    refined_df.to_csv(OUT_DIR / 'XAUUSD_strategy_refined.csv', index=False)
    print("\n=== REFINED SUMMARY ===")
    cols = ['strategy','tf','n_trades','trades_per_week','trades_per_month','total_r','avg_r',
            'win_rate','max_losing_streak','profit_factor',
            'r_without_top3','r_without_top5','span_years']
    print(refined_df[cols].to_string(index=False))


if __name__ == '__main__':
    main()
