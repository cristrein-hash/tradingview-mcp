#!/usr/bin/env python3
"""
ETHUSD rule proposals — search for SWING and INTRADAY strategies
that pass minimum criteria with reduced fat-tail dependency.
"""
import pandas as pd
import numpy as np
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent))
from backtest_ethusd import (load, simulate_trade, metrics, yearly_metrics,
                              FILES, SPREAD_R)

OUT_DIR = Path(__file__).parent


def htf_context(df_low, df_high, label):
    """Add HTF column: HTF close > HTF EMA50 (bullish bias)."""
    df_high = df_high.copy()
    df_high['htf_ema50'] = df_high['close'].ewm(span=50, adjust=False).mean()
    df_high['htf_bullish'] = df_high['close'] > df_high['htf_ema50']
    df_high['htf_ema200'] = df_high['close'].ewm(span=200, adjust=False).mean()
    df_high['htf_ema50_above_ema200'] = df_high['htf_ema50'] > df_high['htf_ema200']
    lite = df_high[['time', 'htf_bullish', 'htf_ema50_above_ema200']].sort_values('time')
    df_low = df_low.sort_values('time').reset_index(drop=True)
    merged = pd.merge_asof(df_low, lite, on='time', direction='backward')
    df_low[f'{label}_bullish'] = merged['htf_bullish'].values
    df_low[f'{label}_stack'] = merged['htf_ema50_above_ema200'].values
    return df_low


def strat_breakout(df, target_r, max_bars, filters: dict, name: str, tf: str):
    """LONG breakout continuation with composable filters."""
    trades = []
    for i in range(200, len(df) - 1):
        row = df.iloc[i]
        # Base trigger
        if not (row['close'] > row['open']
                and row['body_pct'] >= filters.get('body_min', 0.5)
                and row['close'] > df.at[i-1, f"swhi_{filters.get('break_lookback', 10)}"]):
            continue
        # RSI > MA
        rsi = row.get('RSI', np.nan); rsi_ma = row.get('RSI-based MA', np.nan)
        if pd.isna(rsi) or pd.isna(rsi_ma) or rsi <= rsi_ma:
            continue
        # Filters
        if filters.get('require_close_above_ema200') and not row.get('close_above_ema200', False): continue
        if filters.get('require_ema50_above_ema200') and not row.get('ema50_above_ema200', False): continue
        if filters.get('require_atr_expanding') and not row.get('atr_expanding', False): continue
        if filters.get('require_adx_min') is not None and (pd.isna(row.get('adx14', np.nan)) or row['adx14'] < filters['require_adx_min']): continue
        if filters.get('require_ema50_slope_pos') and (pd.isna(row.get('ema50_slope', np.nan)) or row['ema50_slope'] <= 0): continue
        if filters.get('require_htf12h_bullish') and not row.get('htf12h_bullish', False): continue
        if filters.get('require_htf1d_bullish') and not row.get('htf1d_bullish', False): continue
        if filters.get('require_htf1d_stack') and not row.get('htf1d_stack', False): continue
        if filters.get('require_htf12h_stack') and not row.get('htf12h_stack', False): continue
        if filters.get('rsi_min') is not None and rsi < filters['rsi_min']: continue
        if filters.get('require_2bull_prior'):
            if not (df.at[i-1, 'close'] > df.at[i-1, 'open']):
                continue
        if filters.get('require_range_above_atr'):
            if (row['high'] - row['low']) <= row['atr14']:
                continue
        # Build trade
        entry = row['close']; atr = row['atr14']
        if pd.isna(atr) or atr <= 0: continue
        stop = row['low'] - atr * filters.get('stop_atr_mult', 0.5)
        R = abs(entry - stop)
        if R <= 0 or R / atr > 5: continue
        res = simulate_trade(df, i, 'LONG', entry, stop, target_r, max_bars,
                              be_at_1r=filters.get('be_at_1r', True),
                              trail_at=filters.get('trail_at'))
        if not res: continue
        res.update({'entry_time': row['time'], 'entry_price': entry,
                    'stop_price': stop, 'direction': 'LONG', 'r_planned': target_r,
                    'strategy': name, 'tf': tf})
        trades.append(res)
    return trades


def strat_pullback_to_ema(df, ema_col='ema50', target_r=3.0, max_bars=20,
                          name='?', tf='?', extra_filters=None):
    """
    LONG pullback to EMA in trending regime.
    Trigger: low touches/crosses EMA THEN closes above EMA with bullish bar
              + close > open + body >= 50% + Close > EMA200 + EMA50 > EMA200.
    """
    trades = []
    ef = extra_filters or {}
    for i in range(200, len(df) - 1):
        row = df.iloc[i]
        ema = row.get(ema_col, np.nan)
        if pd.isna(ema): continue
        # Pullback definition: low <= EMA (within bar range) AND close > EMA
        touched = row['low'] <= ema and row['close'] > ema
        if not touched: continue
        if not (row['close'] > row['open'] and row['body_pct'] >= 0.4): continue
        # Trend regime
        if not row.get('ema50_above_ema200', False): continue
        if not row.get('close_above_ema200', False): continue
        # RSI > MA (bullish momentum reclaim)
        rsi = row.get('RSI', np.nan); rsi_ma = row.get('RSI-based MA', np.nan)
        if pd.isna(rsi) or pd.isna(rsi_ma) or rsi <= rsi_ma: continue
        # Extra filters
        if ef.get('require_htf1d_bullish') and not row.get('htf1d_bullish', False): continue
        if ef.get('require_htf12h_bullish') and not row.get('htf12h_bullish', False): continue
        if ef.get('require_adx_min') is not None and (pd.isna(row.get('adx14', np.nan)) or row['adx14'] < ef['require_adx_min']): continue
        entry = row['close']; atr = row['atr14']
        if pd.isna(atr) or atr <= 0: continue
        stop = row['low'] - atr * 0.5
        R = abs(entry - stop)
        if R <= 0 or R / atr > 5: continue
        res = simulate_trade(df, i, 'LONG', entry, stop, target_r, max_bars, be_at_1r=True)
        if not res: continue
        res.update({'entry_time': row['time'], 'entry_price': entry,
                    'stop_price': stop, 'direction': 'LONG', 'r_planned': target_r,
                    'strategy': name, 'tf': tf})
        trades.append(res)
    return trades


def main():
    print("=== Loading ETHUSD data with HTF context ===")
    data = {tf: load(p) for tf, p in FILES.items()}
    df4, df1, df30 = data['4H'], data['1H'], data['30M']
    df12 = data['12H']; df1d = data['1D']
    # Attach HTF context to 4H, 1H, 30M
    df4 = htf_context(df4, df12, 'htf12h')
    df4 = htf_context(df4, df1d, 'htf1d')
    df1 = htf_context(df1, df4, 'htf4h')
    df1 = htf_context(df1, df12, 'htf12h')
    df1 = htf_context(df1, df1d, 'htf1d')
    df30 = htf_context(df30, df1, 'htf1h')
    df30 = htf_context(df30, df4, 'htf4h')

    print(f"  4H bars: {len(df4)} HTF1D bullish frac: {df4['htf1d_bullish'].mean():.2%}")
    print(f"  1H bars: {len(df1)} HTF1D bullish frac: {df1['htf1d_bullish'].mean():.2%}")

    summaries = []

    # =============================================================
    # SWING PROPOSALS
    # =============================================================
    print("\n=== SWING proposals ===\n")

    BASE_REGIME = {
        'require_close_above_ema200': True,
        'require_ema50_above_ema200': True,
        'require_atr_expanding': True,
        'require_ema50_slope_pos': True,
        'require_adx_min': 20,
    }

    proposals_swing = [
        # P0 = D current best (baseline) target 5R
        ('P0_4H_breakout_regime_5R', df4, dict(BASE_REGIME), 5.0, 30),
        # P1 = D + HTF1D bullish (filter chop years)
        ('P1_4H_breakout_regime_HTF1D', df4, {**BASE_REGIME, 'require_htf1d_bullish': True}, 5.0, 30),
        # P2 = D + HTF12H bullish (slightly less restrictive)
        ('P2_4H_breakout_regime_HTF12H', df4, {**BASE_REGIME, 'require_htf12h_bullish': True}, 5.0, 30),
        # P3 = D + HTF1D stack (50 > 200)
        ('P3_4H_breakout_regime_HTF1D_stack', df4, {**BASE_REGIME, 'require_htf1d_stack': True}, 5.0, 30),
        # P4 = D + 2 bull bars prior (sustained momentum)
        ('P4_4H_breakout_regime_2bull', df4, {**BASE_REGIME, 'require_2bull_prior': True}, 5.0, 30),
        # P5 = D + range > ATR (decisive bar)
        ('P5_4H_breakout_regime_strong_range', df4, {**BASE_REGIME, 'require_range_above_atr': True}, 5.0, 30),
        # P6 = D + ADX 25
        ('P6_4H_breakout_regime_adx25', df4, {**BASE_REGIME, 'require_adx_min': 25}, 5.0, 30),
        # P7 = D + RSI min 55 (stronger momentum)
        ('P7_4H_breakout_regime_rsi55', df4, {**BASE_REGIME, 'rsi_min': 55}, 5.0, 30),
        # P8 = D + RSI min 60
        ('P8_4H_breakout_regime_rsi60', df4, {**BASE_REGIME, 'rsi_min': 60}, 5.0, 30),
        # P9 = D + HTF12H + ADX25 + 2bull
        ('P9_4H_strict_combo', df4, {**BASE_REGIME, 'require_htf12h_bullish': True,
                                      'require_adx_min': 25, 'require_2bull_prior': True}, 5.0, 30),
        # P10 = D + break_lookback 20 (stronger break)
        ('P10_4H_break20', df4, {**BASE_REGIME, 'break_lookback': 20}, 5.0, 30),
        # P11 = Pullback to EMA50 in trending regime
        ('P11_4H_pullback_EMA50', df4, {}, 3.0, 20),  # special — uses pullback strat
        # P12 = Pullback + HTF1D
        ('P12_4H_pullback_EMA50_HTF1D', df4, {'require_htf1d_bullish': True}, 3.0, 20),
    ]
    swing_results = {}
    for cfg in proposals_swing:
        if cfg[0].startswith('P11') or cfg[0].startswith('P12'):
            t = strat_pullback_to_ema(cfg[1], 'ema50', cfg[3], cfg[4], name=cfg[0], tf='4H',
                                       extra_filters=cfg[2])
        else:
            t = strat_breakout(cfg[1], cfg[3], cfg[4], cfg[2], cfg[0], '4H')
        swing_results[cfg[0]] = t
        summaries.append({'group': 'SWING', 'strategy': cfg[0], **metrics(t)})

    # =============================================================
    # INTRADAY PROPOSALS
    # =============================================================
    print("\n=== INTRADAY proposals ===\n")

    BASE_REGIME_1H = {
        'require_close_above_ema200': True,
        'require_ema50_above_ema200': True,
        'require_atr_expanding': True,
        'require_ema50_slope_pos': True,
        'require_adx_min': 20,
    }

    proposals_intra = [
        ('I0_1H_breakout_regime_4R', df1, dict(BASE_REGIME_1H), 4.0, 24),
        ('I1_1H_breakout_regime_HTF4H', df1, {**BASE_REGIME_1H, 'require_htf4h_bullish': True} if False else BASE_REGIME_1H, 4.0, 24),
        ('I2_1H_breakout_regime_HTF1D', df1, {**BASE_REGIME_1H, 'require_htf1d_bullish': True}, 4.0, 24),
        ('I3_1H_breakout_regime_HTF12H', df1, {**BASE_REGIME_1H, 'require_htf12h_bullish': True}, 4.0, 24),
        ('I4_1H_breakout_regime_2bull', df1, {**BASE_REGIME_1H, 'require_2bull_prior': True}, 4.0, 24),
        ('I5_1H_breakout_regime_rsi55', df1, {**BASE_REGIME_1H, 'rsi_min': 55}, 4.0, 24),
        ('I6_1H_breakout_regime_rsi60', df1, {**BASE_REGIME_1H, 'rsi_min': 60}, 4.0, 24),
        ('I7_1H_breakout_regime_adx25', df1, {**BASE_REGIME_1H, 'require_adx_min': 25}, 4.0, 24),
        ('I8_1H_breakout_strict_combo', df1, {**BASE_REGIME_1H, 'require_htf1d_bullish': True,
                                                'require_adx_min': 25, 'rsi_min': 55}, 4.0, 24),
        ('I9_1H_breakout_break20', df1, {**BASE_REGIME_1H, 'break_lookback': 20}, 4.0, 24),
        ('I10_1H_breakout_range_above_atr', df1, {**BASE_REGIME_1H, 'require_range_above_atr': True}, 4.0, 24),
        ('I11_1H_pullback_EMA50', df1, {}, 3.0, 20),
        ('I12_1H_pullback_EMA50_HTF1D', df1, {'require_htf1d_bullish': True}, 3.0, 20),
    ]
    # Need to attach htf4h column on df1 for I1
    intra_results = {}
    for cfg in proposals_intra:
        if cfg[0].startswith('I11') or cfg[0].startswith('I12'):
            t = strat_pullback_to_ema(cfg[1], 'ema50', cfg[3], cfg[4], name=cfg[0], tf='1H',
                                       extra_filters=cfg[2])
        else:
            t = strat_breakout(cfg[1], cfg[3], cfg[4], cfg[2], cfg[0], '1H')
        intra_results[cfg[0]] = t
        summaries.append({'group': 'INTRADAY', 'strategy': cfg[0], **metrics(t)})

    # Print summary sorted by total_r_net within group
    print("\n=== SWING summary (sorted by total_r_net) ===")
    df_sum = pd.DataFrame(summaries)
    df_swing = df_sum[df_sum['group']=='SWING'].sort_values('total_r_net', ascending=False)
    cols = ['strategy','n','trades_per_week','trades_per_month','total_r_net','avg_r_net',
            'win_rate','pf_net','max_losing_streak','r_no_top5_net','r_no_top10_net']
    print(df_swing[cols].to_string(index=False))

    print("\n=== INTRADAY summary ===")
    df_intra = df_sum[df_sum['group']=='INTRADAY'].sort_values('total_r_net', ascending=False)
    print(df_intra[cols].to_string(index=False))

    # Year breakdown for top 3 of each
    print("\n=== TOP 3 SWING — yearly breakdown ===")
    for name in df_swing['strategy'].head(3):
        if name in swing_results and swing_results[name]:
            print(f"\n--- {name} ---")
            print(yearly_metrics(swing_results[name]).to_string(index=False))

    print("\n=== TOP 3 INTRADAY — yearly breakdown ===")
    for name in df_intra['strategy'].head(3):
        if name in intra_results and intra_results[name]:
            print(f"\n--- {name} ---")
            print(yearly_metrics(intra_results[name]).to_string(index=False))

    # Write outputs
    df_sum.to_csv(OUT_DIR / 'ETHUSD_rule_proposals_summary.csv', index=False)

    # Save trades of top swing and top intraday
    top_swing = df_swing['strategy'].iloc[0]
    if top_swing in swing_results:
        pd.DataFrame(swing_results[top_swing]).to_csv(OUT_DIR / f'ETHUSD_proposal_top_swing_trades.csv', index=False)
        print(f"\nTop swing saved: {top_swing}")

    top_intra = df_intra['strategy'].iloc[0]
    if top_intra in intra_results:
        pd.DataFrame(intra_results[top_intra]).to_csv(OUT_DIR / f'ETHUSD_proposal_top_intraday_trades.csv', index=False)
        print(f"Top intraday saved: {top_intra}")


if __name__ == '__main__':
    main()
