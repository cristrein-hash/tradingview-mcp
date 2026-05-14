#!/usr/bin/env python3
"""Refine the winning candidates: H2 failed_breakdown + H1 BB squeeze breakout.

Try:
- Add filters
- Test intraday variants
- Combine signals
- Cost sensitivity
"""
import pandas as pd
import numpy as np
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent))
from backtest_us500 import load, simulate_trade, metrics, yearly_metrics, htf_context, FILES, SPREAD_R, OUT_DIR
from exhaustive_search import add_indicators, run_long_strat


def main():
    data = {tf: load(p) for tf, p in FILES.items()}
    df1d = data['1D']; df12 = data['12H']
    df4 = data['4H']; df1 = data['1H']; df30 = data['30M']
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
    # REFINE H2: failed_breakdown 4H
    # =============================================================
    print("=== Refining H2: Failed Breakdown variants ===")

    # Base — already validated
    def sig_fb_base(df, i, row):
        return (row.get('failed_breakdown', False) and
                row.get('close_above_ema200', False) and
                row.get('ema50_above_ema200', False))

    # Base + body >= 0.5 (decisive recovery)
    def sig_fb_body(df, i, row):
        if not sig_fb_base(df, i, row): return False
        return row['body_to_range'] >= 0.5

    # Base + ATR expanding
    def sig_fb_atr(df, i, row):
        if not sig_fb_base(df, i, row): return False
        return row.get('atr_expanding', False)

    # Base + RSI > MA
    def sig_fb_rsi(df, i, row):
        if not sig_fb_base(df, i, row): return False
        rsi = row.get('RSI', np.nan); rsi_ma = row.get('RSI-based MA', np.nan)
        if pd.isna(rsi) or pd.isna(rsi_ma): return False
        return rsi > rsi_ma

    # Base + HTF 1D bullish
    def sig_fb_htf1d(df, i, row):
        if not sig_fb_base(df, i, row): return False
        return row.get('htf1d_bullish', False)

    # Base + body + atr
    def sig_fb_body_atr(df, i, row):
        if not sig_fb_base(df, i, row): return False
        return row['body_to_range'] >= 0.5 and row.get('atr_expanding', False)

    # ALL filters combined
    def sig_fb_all(df, i, row):
        if not sig_fb_base(df, i, row): return False
        if row['body_to_range'] < 0.5: return False
        if not row.get('atr_expanding', False): return False
        if not row.get('htf1d_bullish', False): return False
        rsi = row.get('RSI', np.nan); rsi_ma = row.get('RSI-based MA', np.nan)
        if pd.isna(rsi) or pd.isna(rsi_ma) or rsi <= rsi_ma: return False
        return True

    # Higher target
    for target_r in [2.5, 3.0, 3.5, 4.0, 5.0]:
        for sig_name, sig_func in [
            ('base', sig_fb_base),
            ('body50', sig_fb_body),
            ('atr_exp', sig_fb_atr),
            ('rsi_above_ma', sig_fb_rsi),
            ('htf1d_bull', sig_fb_htf1d),
            ('body50+atr', sig_fb_body_atr),
            ('all_filters', sig_fb_all),
        ]:
            name = f'H2v_FB_4H_{sig_name}_target{target_r}R'
            t = run_long_strat(df4, sig_func, target_r, 24, name, '4H')
            summaries.append({'strategy': name, **metrics(t)})
            trades_by[name] = t

    # =============================================================
    # H2 INTRADAY: failed_breakdown 1H/30M with regime filter
    # =============================================================
    print("\n=== H2 Intraday variants ===")
    def sig_fb_1h_strict(df, i, row):
        if not sig_fb_base(df, i, row): return False
        if not row.get('htf1d_bullish', False): return False
        if not row.get('htf4h_bullish', False): return False
        return True

    for tf_label, df_use in [('1H', df1), ('30M', df30)]:
        for target_r in [2.0, 2.5, 3.0]:
            name = f'H2v_FB_{tf_label}_HTF1D+HTF4H_target{target_r}R'
            t = run_long_strat(df_use, sig_fb_1h_strict, target_r, 16, name, tf_label)
            summaries.append({'strategy': name, **metrics(t)})
            trades_by[name] = t

    # =============================================================
    # H1: BB Squeeze refinements
    # =============================================================
    print("\n=== H1 BB Squeeze refinements ===")
    def sig_squeeze_base(df, i, row):
        prev_squeeze = df.at[i-1, 'bb_squeeze'] if i >= 1 else False
        if not prev_squeeze: return False
        if not (row['close'] > df.at[i-1, 'bb_upper']): return False
        if not (row['close'] > row['open'] and row['body_to_range'] >= 0.5): return False
        if not row.get('ema50_above_ema200', False): return False
        if not row.get('close_above_ema200', False): return False
        return True

    def sig_squeeze_htf(df, i, row):
        if not sig_squeeze_base(df, i, row): return False
        return row.get('htf1d_bullish', False)

    def sig_squeeze_strong(df, i, row):
        if not sig_squeeze_base(df, i, row): return False
        if not row.get('htf1d_bullish', False): return False
        # Stronger squeeze
        return df.at[i-1, 'bb_width'] < df.at[i-1, 'bb_width_ma'] * 0.7

    for target_r in [2.5, 3.0, 4.0, 5.0]:
        for sig_name, sig_func in [
            ('base', sig_squeeze_base),
            ('htf1d_bull', sig_squeeze_htf),
            ('strong_squeeze', sig_squeeze_strong),
        ]:
            name = f'H1v_BB_squeeze_4H_{sig_name}_target{target_r}R'
            t = run_long_strat(df4, sig_func, target_r, 24, name, '4H')
            summaries.append({'strategy': name, **metrics(t)})
            trades_by[name] = t

    # =============================================================
    # COMBO: H1 OR H2 (failed_breakdown OR BB_squeeze)
    # =============================================================
    print("\n=== COMBO: H1 OR H2 ===")
    def sig_combo_h1_or_h2(df, i, row):
        # H2 condition
        h2 = sig_fb_base(df, i, row) and row['body_to_range'] >= 0.5
        # H1 condition
        h1 = sig_squeeze_base(df, i, row)
        return h2 or h1

    for target_r in [3.0, 3.5, 4.0]:
        name = f'COMBO_FB_or_squeeze_4H_target{target_r}R'
        t = run_long_strat(df4, sig_combo_h1_or_h2, target_r, 24, name, '4H')
        summaries.append({'strategy': name, **metrics(t)})
        trades_by[name] = t

    # =============================================================
    # SUMMARY
    # =============================================================
    df_res = pd.DataFrame(summaries).sort_values('total_r_net', ascending=False)
    df_res.to_csv(OUT_DIR / 'US500_refined_winners.csv', index=False)

    cols = ['strategy','n','trades_per_week','trades_per_month','total_r_net','avg_r_net',
            'win_rate','pf_net','max_losing_streak','r_no_top5_net','r_no_top10_net']

    print("\n=== Top 15 ===")
    print(df_res[cols].head(15).to_string(index=False))

    print("\n=== Top 5 yearly + cost sensitivity ===")
    for name in df_res['strategy'].head(5):
        t = trades_by.get(name, [])
        if t:
            print(f"\n--- {name} ---")
            print(yearly_metrics(t).to_string(index=False))
            # Cost sensitivity
            r_g = pd.DataFrame(t)['r_outcome']
            n = len(r_g)
            print(f"  Cost sensitivity:")
            for c in [0.00, 0.05, 0.07, 0.10]:
                r_n = r_g - c
                wins = r_n[r_n > 0]; losses = r_n[r_n < 0]
                pf = abs(wins.sum() / losses.sum()) if len(losses) and losses.sum() != 0 else float('inf')
                print(f"    spread {c:.2f}R: total={r_n.sum():.2f}  avg={r_n.mean():.4f}  PF={pf:.2f}")


if __name__ == '__main__':
    main()
