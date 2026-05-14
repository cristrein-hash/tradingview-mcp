#!/usr/bin/env python3
"""Test additional US500 hypotheses — buy-the-dip variants, stricter HTF, target adjustment."""
import pandas as pd
import numpy as np
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent))
from backtest_us500 import load, simulate_trade, metrics, yearly_metrics, htf_context, FILES, SPREAD_R, OUT_DIR


def strat_pullback_ema50_v2(df, target_r=3.0, max_bars=20, stop_atr_mult=0.3,
                             require_htf=False, htf_col=None,
                             body_min=0.4, allow_close_below_ema50=False,
                             name='?', tf='?'):
    """Buy-the-dip: pullback to EMA50, more permissive."""
    trades = []
    for i in range(200, len(df) - 1):
        row = df.iloc[i]
        ema50 = row.get('ema50', np.nan)
        if pd.isna(ema50): continue
        # Pullback definition
        if allow_close_below_ema50:
            # Just need low touching or going below ema50 with bullish bar
            touched = row['low'] <= ema50 * 1.005  # within 0.5%
        else:
            touched = row['low'] <= ema50 and row['close'] > ema50
        if not touched: continue
        if not (row['close'] > row['open'] and row['body_pct'] >= body_min): continue
        if not row.get('ema50_above_ema200', False): continue
        if not row.get('close_above_ema200', False): continue
        if require_htf and htf_col and not row.get(htf_col, False): continue
        entry = row['close']; atr = row['atr14']
        if pd.isna(atr) or atr <= 0: continue
        stop = row['low'] - atr * stop_atr_mult
        R = abs(entry - stop)
        if R <= 0 or R / atr > 5: continue
        res = simulate_trade(df, i, 'LONG', entry, stop, target_r, max_bars, be_at_1r=True)
        if not res: continue
        res.update({'entry_time': row['time'], 'entry_price': entry, 'stop_price': stop,
                    'direction': 'LONG', 'r_planned': target_r, 'strategy': name, 'tf': tf})
        trades.append(res)
    return trades


def strat_pullback_ema20(df, target_r=2.0, max_bars=12, body_min=0.4, name='?', tf='?'):
    """Faster pullback: to EMA20 (intraday-friendly)."""
    trades = []
    for i in range(200, len(df) - 1):
        row = df.iloc[i]
        ema20 = row.get('ema20', np.nan)
        if pd.isna(ema20): continue
        if not (row['low'] <= ema20 and row['close'] > ema20): continue
        if not (row['close'] > row['open'] and row['body_pct'] >= body_min): continue
        if not row.get('ema50_above_ema200', False): continue
        if not row.get('close_above_ema200', False): continue
        entry = row['close']; atr = row['atr14']
        if pd.isna(atr) or atr <= 0: continue
        stop = row['low'] - atr * 0.4
        R = abs(entry - stop)
        if R <= 0 or R / atr > 5: continue
        res = simulate_trade(df, i, 'LONG', entry, stop, target_r, max_bars, be_at_1r=True)
        if not res: continue
        res.update({'entry_time': row['time'], 'entry_price': entry, 'stop_price': stop,
                    'direction': 'LONG', 'r_planned': target_r, 'strategy': name, 'tf': tf})
        trades.append(res)
    return trades


def strat_breakout_target2R(df, max_bars=12, body_min=0.5,
                             require_regime=True, name='?', tf='?'):
    """Breakout but with low target (2R) — captures small continuation in trending markets."""
    trades = []
    for i in range(200, len(df) - 1):
        row = df.iloc[i]
        if not (row['close'] > row['open'] and row['body_pct'] >= body_min
                and row['close'] > df.at[i-1, 'swhi_10']): continue
        rsi = row.get('RSI', np.nan); rsi_ma = row.get('RSI-based MA', np.nan)
        if pd.isna(rsi) or pd.isna(rsi_ma) or rsi <= rsi_ma: continue
        if require_regime:
            if not row.get('close_above_ema200', False): continue
            if not row.get('ema50_above_ema200', False): continue
            if not row.get('atr_expanding', False): continue
            if pd.isna(row.get('adx14', np.nan)) or row['adx14'] < 20: continue
        entry = row['close']; atr = row['atr14']
        if pd.isna(atr) or atr <= 0: continue
        stop = row['low'] - atr * 0.5
        R = abs(entry - stop)
        if R <= 0 or R / atr > 5: continue
        res = simulate_trade(df, i, 'LONG', entry, stop, 2.0, max_bars, be_at_1r=True)
        if not res: continue
        res.update({'entry_time': row['time'], 'entry_price': entry, 'stop_price': stop,
                    'direction': 'LONG', 'r_planned': 2.0, 'strategy': name, 'tf': tf})
        trades.append(res)
    return trades


def main():
    print("=== Loading ===")
    data = {tf: load(p) for tf, p in FILES.items()}
    df4, df1, df30 = data['4H'], data['1H'], data['30M']
    df1d = data['1D']; df12 = data['12H']
    df4 = htf_context(df4, df12, 'htf12h')
    df4 = htf_context(df4, df1d, 'htf1d')
    df1 = htf_context(df1, df4, 'htf4h')
    df1 = htf_context(df1, df1d, 'htf1d')
    df30 = htf_context(df30, df1, 'htf1h')
    df30 = htf_context(df30, df4, 'htf4h')

    summaries = []
    trades_by = {}

    # =============================================================
    # Buy-the-dip variants (4H)
    # =============================================================
    print("\n=== Buy-the-dip 4H variants ===")
    for tr_R in [2.0, 2.5, 3.0]:
        t = strat_pullback_ema50_v2(df4, target_r=tr_R, max_bars=16, stop_atr_mult=0.3,
            body_min=0.4, name=f'BTD_4H_pullback_EMA50_target{tr_R}R', tf='4H')
        summaries.append({'strategy': f'BTD_4H_pullback_EMA50_target{tr_R}R', **metrics(t)})
        trades_by[f'BTD_4H_pullback_EMA50_target{tr_R}R'] = t

    # With HTF1D filter
    t = strat_pullback_ema50_v2(df4, target_r=2.5, max_bars=16, stop_atr_mult=0.3,
        require_htf=True, htf_col='htf1d_bullish', body_min=0.4,
        name='BTD_4H_pullback_EMA50_HTF1D_target2.5R', tf='4H')
    summaries.append({'strategy': 'BTD_4H_pullback_EMA50_HTF1D_target2.5R', **metrics(t)})
    trades_by['BTD_4H_pullback_EMA50_HTF1D_target2.5R'] = t

    # =============================================================
    # Buy-the-dip 1H variants
    # =============================================================
    print("\n=== Buy-the-dip 1H variants ===")
    for tr_R in [2.0, 2.5, 3.0]:
        t = strat_pullback_ema50_v2(df1, target_r=tr_R, max_bars=24, stop_atr_mult=0.3,
            body_min=0.4, name=f'BTD_1H_pullback_EMA50_target{tr_R}R', tf='1H')
        summaries.append({'strategy': f'BTD_1H_pullback_EMA50_target{tr_R}R', **metrics(t)})
        trades_by[f'BTD_1H_pullback_EMA50_target{tr_R}R'] = t

    # With HTF1D filter
    t = strat_pullback_ema50_v2(df1, target_r=2.5, max_bars=24, stop_atr_mult=0.3,
        require_htf=True, htf_col='htf1d_bullish', body_min=0.4,
        name='BTD_1H_pullback_EMA50_HTF1D_target2.5R', tf='1H')
    summaries.append({'strategy': 'BTD_1H_pullback_EMA50_HTF1D_target2.5R', **metrics(t)})
    trades_by['BTD_1H_pullback_EMA50_HTF1D_target2.5R'] = t

    # With HTF4H filter (stronger HTF)
    t = strat_pullback_ema50_v2(df1, target_r=2.5, max_bars=24, stop_atr_mult=0.3,
        require_htf=True, htf_col='htf4h_bullish', body_min=0.4,
        name='BTD_1H_pullback_EMA50_HTF4H_target2.5R', tf='1H')
    summaries.append({'strategy': 'BTD_1H_pullback_EMA50_HTF4H_target2.5R', **metrics(t)})
    trades_by['BTD_1H_pullback_EMA50_HTF4H_target2.5R'] = t

    # =============================================================
    # EMA20 pullback (more frequent)
    # =============================================================
    print("\n=== EMA20 pullback ===")
    t = strat_pullback_ema20(df1, target_r=2.0, max_bars=8, name='EMA20_1H_target2R', tf='1H')
    summaries.append({'strategy': 'EMA20_pullback_1H_target2R', **metrics(t)})
    trades_by['EMA20_1H_target2R'] = t

    t = strat_pullback_ema20(df30, target_r=2.0, max_bars=12, name='EMA20_30M_target2R', tf='30M')
    summaries.append({'strategy': 'EMA20_pullback_30M_target2R', **metrics(t)})
    trades_by['EMA20_30M_target2R'] = t

    # =============================================================
    # Breakout with target 2R (small fast wins)
    # =============================================================
    print("\n=== Breakout target 2R (small wins) ===")
    t = strat_breakout_target2R(df4, max_bars=10, name='BREAK2R_4H', tf='4H')
    summaries.append({'strategy': 'BREAK_2R_4H_regime', **metrics(t)})
    trades_by['BREAK2R_4H'] = t
    t = strat_breakout_target2R(df1, max_bars=8, name='BREAK2R_1H', tf='1H')
    summaries.append({'strategy': 'BREAK_2R_1H_regime', **metrics(t)})
    trades_by['BREAK2R_1H'] = t
    t = strat_breakout_target2R(df30, max_bars=6, name='BREAK2R_30M', tf='30M')
    summaries.append({'strategy': 'BREAK_2R_30M_regime', **metrics(t)})
    trades_by['BREAK2R_30M'] = t

    df_res = pd.DataFrame(summaries).sort_values('total_r_net', ascending=False)
    df_res.to_csv(OUT_DIR / 'US500_extra_variants_summary.csv', index=False)

    cols = ['strategy','n','trades_per_week','trades_per_month','total_r_net','avg_r_net',
            'win_rate','pf_net','max_losing_streak','r_no_top5_net','r_no_top10_net']
    print("\n=== Sorted by total_r_net ===")
    print(df_res[cols].to_string(index=False))

    # Year for top 3
    print("\n=== Top 3 yearly ===")
    for name in df_res['strategy'].head(3):
        # find key
        key = name.replace('BTD_', 'BTD_').replace('EMA20_pullback_', 'EMA20_').replace('BREAK_2R_', 'BREAK2R_').replace('_regime', '')
        # Try exact match in trades_by first
        match_key = None
        for k in trades_by:
            if k == name or k.replace('_', '') == name.replace('_', ''):
                match_key = k; break
        # Fallback: substring match
        if match_key is None:
            for k in trades_by:
                if name in k or k in name:
                    match_key = k; break
        if match_key and trades_by.get(match_key):
            print(f"\n--- {match_key} ---")
            print(yearly_metrics(trades_by[match_key]).to_string(index=False))


if __name__ == '__main__':
    main()
