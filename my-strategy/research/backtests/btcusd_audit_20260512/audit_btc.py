#!/usr/bin/env python3
"""BTCUSD deep audit — SWING 4H + INTRADAY 1H.

Approach mirrors ETHUSD audit but without ETHBTC macro filter (BTC is denominator).
Tests technical-only edge for both swing and intraday.
"""
import pandas as pd
import numpy as np
from pathlib import Path

OUT_DIR = Path(__file__).parent
SPREAD_R = 0.05

FILES = {
    '1D':  '/Users/cristrein/Downloads/PEPPERSTONE_BTCUSD, 1D_dfd6b.csv',
    '12H': '/Users/cristrein/Downloads/PEPPERSTONE_BTCUSD, 720_18378.csv',
    '4H':  '/Users/cristrein/Downloads/PEPPERSTONE_BTCUSD, 240_cfb3e.csv',
    '1H':  '/Users/cristrein/Downloads/PEPPERSTONE_BTCUSD, 60_807e4.csv',
}


def load(path):
    df = pd.read_csv(path)
    df.columns = [c.strip() for c in df.columns]
    df['time'] = pd.to_datetime(df['time'], unit='s')
    df = df.sort_values('time').reset_index(drop=True)
    for c in ['open', 'high', 'low', 'close', 'RSI', 'RSI-based MA']:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors='coerce')
    h, l, c = df['high'], df['low'], df['close']
    pc = c.shift(1)
    tr = pd.concat([(h - l).abs(), (h - pc).abs(), (l - pc).abs()], axis=1).max(axis=1)
    df['atr14'] = tr.ewm(alpha=1/14, adjust=False).mean()
    df['atr_ma20'] = df['atr14'].rolling(20).mean()
    df['atr_expanding'] = df['atr14'] > df['atr_ma20']
    body = (df['close'] - df['open']).abs()
    rng = (df['high'] - df['low']).replace(0, np.nan)
    df['body_pct'] = body / rng
    df['ema50'] = df['close'].ewm(span=50, adjust=False).mean()
    df['ema200'] = df['close'].ewm(span=200, adjust=False).mean()
    df['close_above_ema200'] = df['close'] > df['ema200']
    df['ema50_above_ema200'] = df['ema50'] > df['ema200']
    df['close_above_ema50'] = df['close'] > df['ema50']
    df['ema50_slope_pos'] = df['ema50'].diff(5) > 0
    up = df['high'].diff()
    dn = -df['low'].diff()
    plus_dm = np.where((up > dn) & (up > 0), up, 0.0)
    minus_dm = np.where((dn > up) & (dn > 0), dn, 0.0)
    atr = df['atr14']
    plus_di = 100 * pd.Series(plus_dm, index=df.index).ewm(alpha=1/14, adjust=False).mean() / atr
    minus_di = 100 * pd.Series(minus_dm, index=df.index).ewm(alpha=1/14, adjust=False).mean() / atr
    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)
    df['adx14'] = dx.ewm(alpha=1/14, adjust=False).mean()
    for n in (5, 10, 20):
        df[f'swhi_{n}'] = df['high'].rolling(n).max()
        df[f'swlo_{n}'] = df['low'].rolling(n).min()
    df['range'] = df['high'] - df['low']
    df['range_ge_1_2_atr'] = df['range'] >= 1.2 * df['atr14']
    df['range_ge_1_5_atr'] = df['range'] >= 1.5 * df['atr14']
    df['hour_utc'] = df['time'].dt.hour
    return df


def htf_context(df_low, df_high, label):
    df_h = df_high.copy()
    df_h['htf_ema50'] = df_h['close'].ewm(span=50, adjust=False).mean()
    df_h['htf_ema200'] = df_h['close'].ewm(span=200, adjust=False).mean()
    df_h['htf_bullish'] = df_h['close'] > df_h['htf_ema50']
    df_h['htf_stack'] = df_h['htf_ema50'] > df_h['htf_ema200']
    lite = df_h[['time', 'htf_bullish', 'htf_stack']].sort_values('time')
    df_low = df_low.sort_values('time').reset_index(drop=True)
    merged = pd.merge_asof(df_low, lite, on='time', direction='backward')
    df_low[f'{label}_bullish'] = merged['htf_bullish'].values
    df_low[f'{label}_stack'] = merged['htf_stack'].values
    return df_low


def simulate_trade(df, idx, entry, stop, target_r, max_bars, be_at_1r=True):
    R = abs(entry - stop)
    if R <= 0:
        return None
    target = entry + R * target_r
    cur_stop = stop
    moved_be = False
    for j in range(idx + 1, min(idx + 1 + max_bars, len(df))):
        h, l = df.at[j, 'high'], df.at[j, 'low']
        if be_at_1r and not moved_be:
            if h >= entry + R:
                cur_stop = max(cur_stop, entry)
                moved_be = True
        if l <= cur_stop:
            r = (cur_stop - entry) / R
            return {'exit_idx': j, 'exit': cur_stop, 'r': r, 'bars': j - idx, 'outcome': 'stop'}
        if h >= target:
            r = (target - entry) / R
            return {'exit_idx': j, 'exit': target, 'r': r, 'bars': j - idx, 'outcome': 'target'}
    last = min(idx + max_bars, len(df) - 1)
    r = (df.at[last, 'close'] - entry) / R
    return {'exit_idx': last, 'exit': df.at[last, 'close'], 'r': r, 'bars': last - idx, 'outcome': 'timeout'}


def run_long(df, sig_func, target_r, max_bars, label):
    trades = []
    i = 50
    while i < len(df) - 1:
        row = df.iloc[i]
        if pd.isna(row.get('atr14')) or pd.isna(row.get('ema200')):
            i += 1
            continue
        if sig_func(df, i, row):
            entry = row['close']
            stop = row['low'] - 0.5 * row['atr14']
            R = entry - stop
            if R <= 0 or R > 5 * row['atr14']:
                i += 1
                continue
            tr = simulate_trade(df, i, entry, stop, target_r, max_bars)
            if tr:
                tr['entry_time'] = row['time']
                tr['entry'] = entry
                tr['stop'] = stop
                tr['R_dollars'] = R
                tr['strategy'] = label
                trades.append(tr)
                i = tr['exit_idx'] + 1
                continue
        i += 1
    return trades


def metrics(trades, spread=SPREAD_R):
    if not trades:
        return dict(n=0, total_r_net=0, avg_r_net=0, win_rate=0, pf_net=0,
                    max_losing_streak=0, r_no_top5_net=0, r_no_top10_net=0,
                    trades_per_week=0, trades_per_month=0)
    r_net = np.array([t['r'] - spread for t in trades])
    wins = r_net > 0
    n = len(r_net)
    win_r = r_net[r_net > 0].sum()
    loss_r = -r_net[r_net <= 0].sum()
    pf = win_r / loss_r if loss_r > 0 else float('inf')
    streak = mx = 0
    for w in wins:
        if not w:
            streak += 1
            mx = max(mx, streak)
        else:
            streak = 0
    sorted_desc = np.sort(r_net)[::-1]
    no_top5 = r_net.sum() - sorted_desc[:5].sum() if n >= 5 else 0
    no_top10 = r_net.sum() - sorted_desc[:10].sum() if n >= 10 else 0
    times = [t['entry_time'] for t in trades]
    span_d = (max(times) - min(times)).days or 1
    return dict(
        n=n,
        total_r_net=round(r_net.sum(), 2),
        avg_r_net=round(r_net.mean(), 4),
        win_rate=round(wins.mean(), 3),
        pf_net=round(pf, 2),
        max_losing_streak=mx,
        r_no_top5_net=round(no_top5, 2),
        r_no_top10_net=round(no_top10, 2),
        trades_per_week=round(n / (span_d / 7), 2),
        trades_per_month=round(n / (span_d / 30), 2),
    )


def yearly(trades, spread=SPREAD_R):
    if not trades:
        return pd.DataFrame()
    df = pd.DataFrame(trades)
    df['year'] = pd.to_datetime(df['entry_time']).dt.year
    df['r_net'] = df['r'] - spread
    rows = []
    for yr, g in df.groupby('year'):
        rows.append({'year': int(yr), 'n': len(g),
                     'total_r_net': round(g['r_net'].sum(), 2),
                     'avg_r_net': round(g['r_net'].mean(), 3),
                     'win_rate': round((g['r_net'] > 0).mean(), 3)})
    return pd.DataFrame(rows)


def cost_sensitivity(trades):
    rows = []
    for s in [0.0, 0.05, 0.07, 0.10]:
        m = metrics(trades, spread=s)
        rows.append({'spread': s, 'total_r_net': m['total_r_net'],
                     'avg_r_net': m['avg_r_net'], 'pf_net': m['pf_net']})
    return pd.DataFrame(rows)


def main():
    print("=== Loading BTCUSD CSVs ===")
    data = {tf: load(p) for tf, p in FILES.items()}
    df1d, df12, df4, df1 = data['1D'], data['12H'], data['4H'], data['1H']
    print(f"4H rows={len(df4)} span={(df4.time.max()-df4.time.min()).days/365.25:.2f}y")
    print(f"1H rows={len(df1)} span={(df1.time.max()-df1.time.min()).days/365.25:.2f}y")

    df4 = htf_context(df4, df12, 'htf12h')
    df4 = htf_context(df4, df1d, 'htf1d')
    df1 = htf_context(df1, df4, 'htf4h')
    df1 = htf_context(df1, df12, 'htf12h')
    df1 = htf_context(df1, df1d, 'htf1d')

    summaries = []
    trades_by = {}

    # =========================================================
    # SWING 4H variants
    # =========================================================
    def sig_swing_base(df, i, row):
        if not (row['close'] > row['open'] and row['body_pct'] >= 0.5
                and row['close'] > df.at[i-1, 'swhi_10']): return False
        rsi = row.get('RSI', np.nan); rsi_ma = row.get('RSI-based MA', np.nan)
        if pd.isna(rsi) or pd.isna(rsi_ma) or rsi <= rsi_ma: return False
        if not row.get('close_above_ema200', False): return False
        if not row.get('ema50_above_ema200', False): return False
        if not row.get('atr_expanding', False): return False
        return True

    def sig_swing_htf1d(df, i, row):
        if not sig_swing_base(df, i, row): return False
        return bool(row.get('htf1d_bullish', False))

    def sig_swing_htf1d_12h(df, i, row):
        if not sig_swing_htf1d(df, i, row): return False
        return bool(row.get('htf12h_bullish', False))

    def sig_swing_htf1d_adx20(df, i, row):
        if not sig_swing_htf1d(df, i, row): return False
        adx = row.get('adx14', np.nan)
        if pd.isna(adx) or adx < 20: return False
        return True

    def sig_swing_htf1d_adx25(df, i, row):
        if not sig_swing_htf1d(df, i, row): return False
        adx = row.get('adx14', np.nan)
        if pd.isna(adx) or adx < 25: return False
        return True

    def sig_swing_htf1d_body60(df, i, row):
        if not sig_swing_htf1d(df, i, row): return False
        return row['body_pct'] >= 0.6

    def sig_swing_htf1d_body70(df, i, row):
        if not sig_swing_htf1d(df, i, row): return False
        return row['body_pct'] >= 0.7

    def sig_swing_htf1d_range(df, i, row):
        if not sig_swing_htf1d(df, i, row): return False
        return bool(row.get('range_ge_1_2_atr', False))

    def sig_swing_htf1d_12h_body60(df, i, row):
        if not sig_swing_htf1d_12h(df, i, row): return False
        return row['body_pct'] >= 0.6

    def sig_swing_htf1d_12h_adx25(df, i, row):
        if not sig_swing_htf1d_12h(df, i, row): return False
        adx = row.get('adx14', np.nan)
        if pd.isna(adx) or adx < 25: return False
        return True

    def sig_swing_strict_combo(df, i, row):
        """body60 + ADX25 + HTF1D + HTF12H + range_ge_1.2"""
        if not sig_swing_htf1d_12h(df, i, row): return False
        if row['body_pct'] < 0.6: return False
        adx = row.get('adx14', np.nan)
        if pd.isna(adx) or adx < 25: return False
        return bool(row.get('range_ge_1_2_atr', False))

    swing_variants = [
        ('base_no_HTF', sig_swing_base),
        ('+HTF1D', sig_swing_htf1d),
        ('+HTF1D+HTF12H', sig_swing_htf1d_12h),
        ('+HTF1D+ADX20', sig_swing_htf1d_adx20),
        ('+HTF1D+ADX25', sig_swing_htf1d_adx25),
        ('+HTF1D+body60', sig_swing_htf1d_body60),
        ('+HTF1D+body70', sig_swing_htf1d_body70),
        ('+HTF1D+range12', sig_swing_htf1d_range),
        ('+HTF1D+12H+body60', sig_swing_htf1d_12h_body60),
        ('+HTF1D+12H+ADX25', sig_swing_htf1d_12h_adx25),
        ('strict_combo', sig_swing_strict_combo),
    ]

    print(f"\n=== SWING 4H: {len(swing_variants)} variants × 4 targets ===")
    for name, fn in swing_variants:
        for trg in [2.0, 2.5, 3.0, 4.0]:
            label = f'BTC_SWING_4H_{name}_target{trg}R'
            tr = run_long(df4, fn, trg, 24, label)
            summaries.append({'strategy': label, **metrics(tr)})
            trades_by[label] = tr

    # =========================================================
    # INTRADAY 1H variants
    # =========================================================
    def sig_intra_decisive_base(df, i, row):
        if not (row['close'] > row['open']): return False
        if pd.isna(row.get('body_pct')) or row['body_pct'] < 0.6: return False
        if not (row['close'] > df.at[i-1, 'swhi_10']): return False
        if not row.get('range_ge_1_2_atr', False): return False
        rsi = row.get('RSI', np.nan); rsi_ma = row.get('RSI-based MA', np.nan)
        if pd.isna(rsi) or pd.isna(rsi_ma) or rsi <= rsi_ma: return False
        if not row.get('close_above_ema200', False): return False
        if not row.get('ema50_above_ema200', False): return False
        if not row.get('atr_expanding', False): return False
        return True

    def sig_intra_decisive_body70(df, i, row):
        if not (row['close'] > row['open']): return False
        if pd.isna(row.get('body_pct')) or row['body_pct'] < 0.7: return False
        if not (row['close'] > df.at[i-1, 'swhi_10']): return False
        if not row.get('range_ge_1_5_atr', False): return False
        rsi = row.get('RSI', np.nan); rsi_ma = row.get('RSI-based MA', np.nan)
        if pd.isna(rsi) or pd.isna(rsi_ma) or rsi <= rsi_ma: return False
        if not row.get('close_above_ema200', False): return False
        if not row.get('ema50_above_ema200', False): return False
        if not row.get('atr_expanding', False): return False
        return True

    def sig_intra_dec_htf1d(df, i, row):
        if not sig_intra_decisive_base(df, i, row): return False
        return bool(row.get('htf1d_bullish', False))

    def sig_intra_dec_htf1d_4h(df, i, row):
        if not sig_intra_dec_htf1d(df, i, row): return False
        return bool(row.get('htf4h_bullish', False))

    def sig_intra_body70_htf1d(df, i, row):
        if not sig_intra_decisive_body70(df, i, row): return False
        return bool(row.get('htf1d_bullish', False))

    def sig_intra_body70_htf1d_4h(df, i, row):
        if not sig_intra_body70_htf1d(df, i, row): return False
        return bool(row.get('htf4h_bullish', False))

    # Pullback EMA50 reclaim (ETH winner pattern)
    def sig_pullback_ema50_rsi(df, i, row):
        if not bool(row.get('htf1d_bullish', False)): return False
        if not row.get('ema50_above_ema200', False): return False
        if not row.get('atr_expanding', False): return False
        recent_touch = False
        for k in range(max(0, i-3), i+1):
            if df.at[k, 'low'] <= df.at[k, 'ema50'] <= df.at[k, 'high']:
                recent_touch = True
                break
        if not recent_touch: return False
        if row['close'] <= row['ema50']: return False
        rsi = row.get('RSI', np.nan); rsi_ma = row.get('RSI-based MA', np.nan)
        if pd.isna(rsi) or pd.isna(rsi_ma): return False
        if rsi <= rsi_ma: return False
        rsi_prev = df.at[i-1, 'RSI'] if i > 0 else np.nan
        rsi_ma_prev = df.at[i-1, 'RSI-based MA'] if i > 0 else np.nan
        if pd.isna(rsi_prev) or pd.isna(rsi_ma_prev): return False
        if rsi_prev > rsi_ma_prev: return False
        return True

    intra_variants = [
        ('decisive_body60', sig_intra_decisive_base),
        ('decisive_body70', sig_intra_decisive_body70),
        ('decisive_body60+HTF1D', sig_intra_dec_htf1d),
        ('decisive_body60+HTF1D+HTF4H', sig_intra_dec_htf1d_4h),
        ('decisive_body70+HTF1D', sig_intra_body70_htf1d),
        ('decisive_body70+HTF1D+HTF4H', sig_intra_body70_htf1d_4h),
        ('PULLBACK_EMA50_RSI+HTF1D', sig_pullback_ema50_rsi),
    ]

    print(f"\n=== INTRADAY 1H: {len(intra_variants)} variants × 4 targets ===")
    for name, fn in intra_variants:
        for trg in [2.0, 2.5, 3.0, 4.0]:
            label = f'BTC_INTRA_1H_{name}_target{trg}R'
            tr = run_long(df1, fn, trg, 20, label)
            summaries.append({'strategy': label, **metrics(tr)})
            trades_by[label] = tr

    res = pd.DataFrame(summaries).sort_values('total_r_net', ascending=False)
    res.to_csv(OUT_DIR / 'BTC_audit_summary.csv', index=False)

    cols = ['strategy', 'n', 'trades_per_week', 'trades_per_month', 'total_r_net',
            'avg_r_net', 'win_rate', 'pf_net', 'max_losing_streak',
            'r_no_top5_net', 'r_no_top10_net']

    print("\n=== TOP 10 SWING 4H ===")
    swing_df = res[res['strategy'].str.contains('SWING_4H')]
    print(swing_df[cols].head(10).to_string(index=False))

    print("\n=== TOP 10 INTRADAY 1H ===")
    intra_df = res[res['strategy'].str.contains('INTRA_1H')]
    print(intra_df[cols].head(10).to_string(index=False))

    # Yearly + cost sensitivity for top 3 each layer
    for layer, df_sub in [('SWING 4H', swing_df), ('INTRADAY 1H', intra_df)]:
        print(f"\n\n=== TOP 3 {layer} yearly + cost ===")
        for name in df_sub['strategy'].head(3):
            tr = trades_by.get(name, [])
            if tr:
                print(f"\n--- {name} ---")
                print("Yearly:")
                print(yearly(tr).to_string(index=False))
                print("Cost:")
                print(cost_sensitivity(tr).to_string(index=False))

    top_swing = swing_df.iloc[0]['strategy']
    top_intra = intra_df.iloc[0]['strategy']
    pd.DataFrame(trades_by[top_swing]).to_csv(OUT_DIR / 'BTC_best_swing_trades.csv', index=False)
    pd.DataFrame(trades_by[top_intra]).to_csv(OUT_DIR / 'BTC_best_intra_trades.csv', index=False)
    print(f"\nSaved: BTC_audit_summary.csv, BTC_best_swing_trades.csv (top={top_swing}), BTC_best_intra_trades.csv (top={top_intra})")


if __name__ == '__main__':
    main()
