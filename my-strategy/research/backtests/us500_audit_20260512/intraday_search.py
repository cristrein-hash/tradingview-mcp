#!/usr/bin/env python3
"""Final intraday search for US500 — apply best swing insights to 1H/30M."""
import pandas as pd
import numpy as np
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent))
from backtest_us500 import load, simulate_trade, metrics, yearly_metrics, htf_context, FILES, SPREAD_R, OUT_DIR
from exhaustive_search import add_indicators, run_long_strat


def main():
    data = {tf: load(p) for tf, p in FILES.items()}
    df4 = data['4H']; df1 = data['1H']; df30 = data['30M']
    df1d = data['1D']; df12 = data['12H']
    df4 = htf_context(df4, df12, 'htf12h')
    df4 = htf_context(df4, df1d, 'htf1d')
    df1 = htf_context(df1, df4, 'htf4h')
    df1 = htf_context(df1, df1d, 'htf1d')
    df30 = htf_context(df30, df1, 'htf1h')
    df30 = htf_context(df30, df4, 'htf4h')
    df30 = htf_context(df30, df1d, 'htf1d')
    for d in [df4, df1, df30]:
        add_indicators(d)

    summaries = []
    trades_by = {}

    # =============================================================
    # Failed Breakdown 1H/30M with multi-HTF strict filter
    # =============================================================
    def sig_fb_intraday_strict(df, i, row):
        if not row.get('failed_breakdown', False): return False
        if not (row['close'] > row['open']): return False
        if row['body_to_range'] < 0.5: return False
        if not row.get('close_above_ema200', False): return False
        if not row.get('ema50_above_ema200', False): return False
        # HTF alignment
        if not row.get('htf1d_bullish', False): return False
        if not row.get('htf4h_bullish', False): return False
        # ATR expansion
        if not row.get('atr_expanding', False): return False
        return True

    print("=== Failed Breakdown intraday strict ===")
    for tf_label, df_use in [('1H', df1), ('30M', df30)]:
        for target_r in [2.0, 2.5, 3.0]:
            name = f'IFB_{tf_label}_FB_strict_target{target_r}R'
            t = run_long_strat(df_use, sig_fb_intraday_strict, target_r, 16, name, tf_label)
            summaries.append({'strategy': name, **metrics(t)})
            trades_by[name] = t

    # =============================================================
    # BB Squeeze 1H with HTF filter
    # =============================================================
    def sig_squeeze_1h_strict(df, i, row):
        prev_squeeze = df.at[i-1, 'bb_squeeze'] if i >= 1 else False
        if not prev_squeeze: return False
        if not (row['close'] > df.at[i-1, 'bb_upper']): return False
        if not (row['close'] > row['open'] and row['body_to_range'] >= 0.5): return False
        if not row.get('close_above_ema200', False): return False
        if not row.get('ema50_above_ema200', False): return False
        if not row.get('htf1d_bullish', False): return False
        if not row.get('htf4h_bullish', False): return False
        return True

    print("\n=== BB Squeeze 1H/30M strict ===")
    for tf_label, df_use in [('1H', df1), ('30M', df30)]:
        for target_r in [2.0, 2.5, 3.0]:
            name = f'IBB_{tf_label}_squeeze_strict_target{target_r}R'
            t = run_long_strat(df_use, sig_squeeze_1h_strict, target_r, 16, name, tf_label)
            summaries.append({'strategy': name, **metrics(t)})
            trades_by[name] = t

    # =============================================================
    # Combined FB OR Squeeze on 1H with strict HTF
    # =============================================================
    def sig_combo_intra(df, i, row):
        # HTF strict
        if not row.get('htf1d_bullish', False): return False
        if not row.get('htf4h_bullish', False): return False
        if not row.get('close_above_ema200', False): return False
        if not row.get('ema50_above_ema200', False): return False
        # H2 condition
        h2_ok = (row.get('failed_breakdown', False) and row['close'] > row['open']
                 and row['body_to_range'] >= 0.5)
        # H1 condition
        prev_squeeze = df.at[i-1, 'bb_squeeze'] if i >= 1 else False
        h1_ok = (prev_squeeze and row['close'] > df.at[i-1, 'bb_upper'] and
                  row['close'] > row['open'] and row['body_to_range'] >= 0.5)
        return h2_ok or h1_ok

    print("\n=== COMBO FB-or-Squeeze intraday ===")
    for tf_label, df_use in [('1H', df1), ('30M', df30)]:
        for target_r in [2.0, 2.5, 3.0]:
            name = f'COMBO_{tf_label}_FB_or_squeeze_HTF_target{target_r}R'
            t = run_long_strat(df_use, sig_combo_intra, target_r, 16, name, tf_label)
            summaries.append({'strategy': name, **metrics(t)})
            trades_by[name] = t

    # =============================================================
    # F_1H_BREAKOUT_REGIME_FILTERED (mantido como CANDIDATO_FORTE)
    # variants with extra filter
    # =============================================================
    print("\n=== F variants with additional filters ===")
    def sig_F_base(df, i, row):
        # Original F_1H breakout regime
        if not (row['close'] > row['open'] and row['body_to_range'] >= 0.5
                and row['close'] > df.at[i-1, 'swhi_10']): return False
        rsi = row.get('RSI', np.nan); rsi_ma = row.get('RSI-based MA', np.nan)
        if pd.isna(rsi) or pd.isna(rsi_ma) or rsi <= rsi_ma: return False
        if not row.get('close_above_ema200', False): return False
        if not row.get('ema50_above_ema200', False): return False
        if not row.get('atr_expanding', False): return False
        if not row.get('ema50_slope', 0) > 0: return False
        if pd.isna(row.get('adx14', np.nan)) or row['adx14'] < 20: return False
        return True

    def sig_F_htf1d(df, i, row):
        if not sig_F_base(df, i, row): return False
        return row.get('htf1d_bullish', False)

    def sig_F_htf1d_4h(df, i, row):
        if not sig_F_base(df, i, row): return False
        if not row.get('htf1d_bullish', False): return False
        if not row.get('htf4h_bullish', False): return False
        return True

    for target_r in [3.0, 4.0]:
        name = f'F_1H_breakout_HTF1D_target{target_r}R'
        t = run_long_strat(df1, sig_F_htf1d, target_r, 20, name, '1H')
        summaries.append({'strategy': name, **metrics(t)})
        trades_by[name] = t

        name = f'F_1H_breakout_HTF1D+4H_target{target_r}R'
        t = run_long_strat(df1, sig_F_htf1d_4h, target_r, 20, name, '1H')
        summaries.append({'strategy': name, **metrics(t)})
        trades_by[name] = t

    df_res = pd.DataFrame(summaries).sort_values('total_r_net', ascending=False)
    df_res.to_csv(OUT_DIR / 'US500_intraday_search_summary.csv', index=False)

    cols = ['strategy','n','trades_per_week','trades_per_month','total_r_net','avg_r_net',
            'win_rate','pf_net','max_losing_streak','r_no_top5_net','r_no_top10_net']
    print("\n=== Sorted by total_r_net ===")
    print(df_res[cols].to_string(index=False))

    print("\n=== Top 3 yearly ===")
    for name in df_res['strategy'].head(3):
        t = trades_by.get(name, [])
        if t:
            print(f"\n--- {name} ---")
            print(yearly_metrics(t).to_string(index=False))


if __name__ == '__main__':
    main()
