#!/usr/bin/env python3
"""Compara Mecanico R_full_trend_regime (n=234) vs V3c Leonardo (touch_in_zone tgt5R, n=36).

Re-extrai trades mecanicos via run_strategy, cruza com V3c por proximidade temporal.
Objetivo: separar trades em (mech only) / (V3c only) / (both), comparar outcome.
"""
import pandas as pd
import numpy as np
import sys
from pathlib import Path

DIR = Path(__file__).parent
sys.path.insert(0, str(DIR))
from regime_filter_test import (
    compute_indicators, htf_context, run_strategy, SPREAD_R,
)
from backtest_xauusd import load

FILES = {
    '4H':  '/Users/cristrein/Downloads/PEPPERSTONE_XAUUSD, 240_aea76.csv',
    '12H': '/Users/cristrein/Downloads/PEPPERSTONE_XAUUSD, 720_8fe91.csv',
    '1D':  '/Users/cristrein/Downloads/PEPPERSTONE_XAUUSD, 1D_7f278.csv',
}


def main():
    print("=== Loading + indicators ===")
    df4 = load(FILES['4H'])
    df4 = compute_indicators(df4)
    df12 = load(FILES['12H'])
    df1d = load(FILES['1D'])
    df4 = htf_context(df4, df12, 'htf12h')
    df4 = htf_context(df4, df1d, 'htf1d')

    print("=== Extracting mecanic R_full_trend_regime trades (n=234 expected) ===")
    mech_filter = {
        'adx_min': 20,
        'close_above_ema200': True,
        'ema50_above_ema200': True,
        'ema50_slope_pos': True,
        'atr_expanding': True,
    }
    mech_trades = run_strategy(df4, mech_filter, target_r=4.0, max_bars=24,
                               be=True, name='R_full_trend_regime')
    mech_df = pd.DataFrame(mech_trades)
    print(f"  Extracted: {len(mech_df)} trades")
    mech_df.to_csv(DIR / 'XAUUSD_4H_mechanic_R_full_trades.csv', index=False)

    print("=== Loading V3c best trades ===")
    v3c_df = pd.read_csv(DIR / 'XAU_4H_SMC_v3_V3c_best_trades.csv')
    v3c_df['entry_time'] = pd.to_datetime(v3c_df['entry_time'])
    mech_df['entry_time'] = pd.to_datetime(mech_df['entry_time'])
    print(f"  V3c trades: {len(v3c_df)}")

    print("\n=== Overlap analysis (entry within 4 bars = 16h) ===")
    matches = []
    used_v3c = set()
    for i, m in mech_df.iterrows():
        t_mech = m['entry_time']
        for j, v in v3c_df.iterrows():
            if j in used_v3c:
                continue
            t_v3c = v['entry_time']
            diff_h = abs((t_mech - t_v3c).total_seconds()) / 3600
            if diff_h <= 16:
                matches.append({
                    'mech_idx': i,
                    'v3c_idx': j,
                    'mech_entry_time': t_mech,
                    'v3c_entry_time': t_v3c,
                    'diff_hours': diff_h,
                    'mech_entry': m['entry_price'],
                    'v3c_entry': v['entry'],
                    'mech_stop': m['stop_price'],
                    'v3c_stop': v['stop'],
                    'mech_r': m['r_outcome'],
                    'v3c_r': v['r'],
                })
                used_v3c.add(j)
                break

    overlap_df = pd.DataFrame(matches)
    mech_only_idx = set(mech_df.index) - {m['mech_idx'] for m in matches}
    v3c_only_idx = set(v3c_df.index) - used_v3c
    mech_only_df = mech_df.loc[list(mech_only_idx)]
    v3c_only_df = v3c_df.loc[list(v3c_only_idx)]

    print(f"\n  Overlap (both saw same event): {len(overlap_df)}")
    print(f"  Mech only (mech saw, V3c missed): {len(mech_only_df)}")
    print(f"  V3c only (V3c saw, mech missed): {len(v3c_only_df)}")

    # Outcome comparison
    def stats(r_array, label):
        r_array = pd.Series(r_array)
        r_net = r_array - SPREAD_R
        wins = (r_net > 0).sum()
        total = r_net.sum()
        return f"  {label}: n={len(r_array)}, total_net={total:.2f}R, " \
               f"wins={wins}/{len(r_array)} ({100*wins/len(r_array):.1f}%), " \
               f"avg={r_net.mean():.3f}R"

    print("\n=== Outcome summary ===")
    if len(overlap_df) > 0:
        print(stats(overlap_df['mech_r'].values, 'OVERLAP (mech R)'))
        print(stats(overlap_df['v3c_r'].values, 'OVERLAP (v3c R)'))
        agree = ((overlap_df['mech_r'] > 0) == (overlap_df['v3c_r'] > 0)).sum()
        print(f"  Agree (same direction win/loss): {agree}/{len(overlap_df)} ({100*agree/len(overlap_df):.1f}%)")
    print(stats(mech_only_df['r_outcome'].values, 'MECH ONLY'))
    print(stats(v3c_only_df['r'].values, 'V3C ONLY'))

    # Combined portfolio
    print("\n=== Hipotetico portfolio combinado (mech + v3c_only) ===")
    combined_r = list(mech_df['r_outcome'].values) + list(v3c_only_df['r'].values)
    print(stats(combined_r, 'MECH + V3C_ONLY (sem duplicar overlap)'))

    if len(overlap_df) > 0:
        print("\n=== Sample overlap trades (10 primeiros) ===")
        print(overlap_df.head(10).to_string(index=False))

    overlap_df.to_csv(DIR / 'compare_mech_v3c_overlap.csv', index=False)
    mech_only_df.to_csv(DIR / 'compare_mech_only.csv', index=False)
    v3c_only_df.to_csv(DIR / 'compare_v3c_only.csv', index=False)
    print(f"\nSaved: compare_mech_v3c_overlap.csv, compare_mech_only.csv, compare_v3c_only.csv")


if __name__ == '__main__':
    main()
