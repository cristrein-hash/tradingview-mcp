#!/usr/bin/env python3
"""XAUUSD 1H deep audit — decisive breakout + multi-TF + regime variants."""
import pandas as pd
import numpy as np
from pathlib import Path

OUT_DIR = Path(__file__).parent
SPREAD_R = 0.05

FILES = {
    '1D':  '/Users/cristrein/Downloads/PEPPERSTONE_XAUUSD, 1D_7f278.csv',
    '12H': '/Users/cristrein/Downloads/PEPPERSTONE_XAUUSD, 720_8fe91.csv',
    '4H':  '/Users/cristrein/Downloads/PEPPERSTONE_XAUUSD, 240_aea76.csv',
    '1H':  '/Users/cristrein/Downloads/PEPPERSTONE_XAUUSD, 60_309fa.csv',
}


def load(path):
    df = pd.read_csv(path)
    df.columns = [c.strip() for c in df.columns]
    df['time'] = pd.to_datetime(df['time'], unit='s')
    df = df.sort_values('time').reset_index(drop=True)
    for c in ['open', 'high', 'low', 'close', 'RSI', 'RSI-based MA']:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors='coerce')
    # ATR(14) Wilder
    h, l, c = df['high'], df['low'], df['close']
    pc = c.shift(1)
    tr = pd.concat([(h - l).abs(), (h - pc).abs(), (l - pc).abs()], axis=1).max(axis=1)
    df['atr14'] = tr.ewm(alpha=1/14, adjust=False).mean()
    df['atr_ma20'] = df['atr14'].rolling(20).mean()
    df['atr_expanding'] = df['atr14'] > df['atr_ma20']
    # Body / range
    body = (df['close'] - df['open']).abs()
    rng = (df['high'] - df['low']).replace(0, np.nan)
    df['body_pct'] = body / rng
    # EMA stack
    df['ema50'] = df['close'].ewm(span=50, adjust=False).mean()
    df['ema200'] = df['close'].ewm(span=200, adjust=False).mean()
    df['close_above_ema200'] = df['close'] > df['ema200']
    df['ema50_above_ema200'] = df['ema50'] > df['ema200']
    df['close_above_ema50'] = df['close'] > df['ema50']
    df['ema50_slope_pos'] = df['ema50'].diff(5) > 0
    # ADX(14)
    up = df['high'].diff()
    dn = -df['low'].diff()
    plus_dm = np.where((up > dn) & (up > 0), up, 0.0)
    minus_dm = np.where((dn > up) & (dn > 0), dn, 0.0)
    atr = df['atr14']
    plus_di = 100 * pd.Series(plus_dm, index=df.index).ewm(alpha=1/14, adjust=False).mean() / atr
    minus_di = 100 * pd.Series(minus_dm, index=df.index).ewm(alpha=1/14, adjust=False).mean() / atr
    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)
    df['adx14'] = dx.ewm(alpha=1/14, adjust=False).mean()
    # Swing high(N)
    for n in (5, 10, 20):
        df[f'swhi_{n}'] = df['high'].rolling(n).max()
        df[f'swlo_{n}'] = df['low'].rolling(n).min()
    # Range expansion
    df['range'] = df['high'] - df['low']
    df['range_ge_1_2_atr'] = df['range'] >= 1.2 * df['atr14']
    df['range_ge_1_5_atr'] = df['range'] >= 1.5 * df['atr14']
    df['range_ge_2_0_atr'] = df['range'] >= 2.0 * df['atr14']
    # Session (UTC hour) — London 7-15, NY 12-20, Asia 0-7
    df['hour_utc'] = df['time'].dt.hour
    df['london_session'] = df['hour_utc'].isin([7, 8, 9, 10, 11, 12, 13, 14])
    df['ny_session'] = df['hour_utc'].isin([12, 13, 14, 15, 16, 17, 18, 19])
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
    rows = []
    df = pd.DataFrame(trades)
    df['year'] = pd.to_datetime(df['entry_time']).dt.year
    df['r_net'] = df['r'] - spread
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
    print("=== Loading XAUUSD CSVs ===")
    data = {tf: load(p) for tf, p in FILES.items()}
    df1d, df12, df4, df1 = data['1D'], data['12H'], data['4H'], data['1H']
    print(f"1H rows={len(df1)} span={(df1.time.max()-df1.time.min()).days/365.25:.2f}y")

    df1 = htf_context(df1, df4, 'htf4h')
    df1 = htf_context(df1, df12, 'htf12h')
    df1 = htf_context(df1, df1d, 'htf1d')

    # =========================================================
    # Signal definitions — DECISIVE breakout family
    # =========================================================

    def sig_base_decisive(df, i, row):
        """Base: close > swhi(10) + body>=0.7 + range>=1.5*ATR + RSI>MA + EMA stack + ATR exp."""
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

    def sig_base_decisive_body60(df, i, row):
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

    def sig_decisive_htf1d(df, i, row):
        if not sig_base_decisive(df, i, row): return False
        return bool(row.get('htf1d_bullish', False))

    def sig_decisive_htf1d_4h(df, i, row):
        if not sig_decisive_htf1d(df, i, row): return False
        return bool(row.get('htf4h_bullish', False))

    def sig_decisive_htf1d_12h(df, i, row):
        if not sig_decisive_htf1d(df, i, row): return False
        return bool(row.get('htf12h_bullish', False))

    def sig_decisive_htf1d_12h_4h(df, i, row):
        if not sig_decisive_htf1d_4h(df, i, row): return False
        return bool(row.get('htf12h_bullish', False))

    def sig_decisive_htf1d_adx25(df, i, row):
        if not sig_decisive_htf1d(df, i, row): return False
        adx = row.get('adx14', np.nan)
        if pd.isna(adx) or adx < 25: return False
        return True

    def sig_decisive_htf1d_session(df, i, row):
        if not sig_decisive_htf1d(df, i, row): return False
        return bool(row.get('london_session', False)) or bool(row.get('ny_session', False))

    def sig_decisive_all_combo(df, i, row):
        """Decisive + HTF1D + HTF4H + ADX25 + session"""
        if not sig_decisive_htf1d_4h(df, i, row): return False
        adx = row.get('adx14', np.nan)
        if pd.isna(adx) or adx < 25: return False
        return bool(row.get('london_session', False)) or bool(row.get('ny_session', False))

    def sig_body60_htf1d_4h(df, i, row):
        if not sig_base_decisive_body60(df, i, row): return False
        if not bool(row.get('htf1d_bullish', False)): return False
        return bool(row.get('htf4h_bullish', False))

    # XAU-specific: pullback EMA50 + RSI reclaim + HTF1D (mirror ETHUSD 1H winner)
    def sig_pullback_ema50_rsi(df, i, row):
        if not bool(row.get('htf1d_bullish', False)): return False
        if not row.get('ema50_above_ema200', False): return False
        if not row.get('atr_expanding', False): return False
        # Pullback: low touched EMA50 within last 3 bars
        recent_touch = False
        for k in range(max(0, i-3), i+1):
            if df.at[k, 'low'] <= df.at[k, 'ema50'] <= df.at[k, 'high']:
                recent_touch = True
                break
        if not recent_touch: return False
        # Reclaim: close > EMA50 + RSI cross above RSI MA on this bar
        if row['close'] <= row['ema50']: return False
        rsi = row.get('RSI', np.nan); rsi_ma = row.get('RSI-based MA', np.nan)
        if pd.isna(rsi) or pd.isna(rsi_ma): return False
        if rsi <= rsi_ma: return False
        rsi_prev = df.at[i-1, 'RSI'] if i > 0 else np.nan
        rsi_ma_prev = df.at[i-1, 'RSI-based MA'] if i > 0 else np.nan
        if pd.isna(rsi_prev) or pd.isna(rsi_ma_prev): return False
        if rsi_prev > rsi_ma_prev: return False  # need cross UP this bar
        return True

    variants = [
        ('base_decisive', sig_base_decisive),
        ('base_decisive_body60_r12', sig_base_decisive_body60),
        ('+HTF1D', sig_decisive_htf1d),
        ('+HTF1D+HTF4H', sig_decisive_htf1d_4h),
        ('+HTF1D+HTF12H', sig_decisive_htf1d_12h),
        ('+HTF1D+HTF12H+HTF4H', sig_decisive_htf1d_12h_4h),
        ('+HTF1D+ADX25', sig_decisive_htf1d_adx25),
        ('+HTF1D+session', sig_decisive_htf1d_session),
        ('+HTF1D+HTF4H+ADX25+session', sig_decisive_all_combo),
        ('body60+HTF1D+HTF4H', sig_body60_htf1d_4h),
        ('PULLBACK_EMA50_RSI_reclaim+HTF1D', sig_pullback_ema50_rsi),
    ]

    summaries = []
    trades_by = {}
    targets = [2.0, 2.5, 3.0, 4.0]

    print(f"\n=== Running {len(variants)} variants × {len(targets)} targets = {len(variants)*len(targets)} configs ===\n")
    for name, fn in variants:
        for trg in targets:
            label = f'XAU_1H_{name}_target{trg}R'
            tr = run_long(df1, fn, trg, 20, label)
            summaries.append({'strategy': label, **metrics(tr)})
            trades_by[label] = tr

    res = pd.DataFrame(summaries).sort_values('total_r_net', ascending=False)
    res.to_csv(OUT_DIR / 'XAU_1H_audit_summary.csv', index=False)

    cols = ['strategy', 'n', 'trades_per_week', 'trades_per_month', 'total_r_net',
            'avg_r_net', 'win_rate', 'pf_net', 'max_losing_streak',
            'r_no_top5_net', 'r_no_top10_net']

    print("=== TOP 15 by total_r_net ===")
    print(res[cols].head(15).to_string(index=False))

    print("\n=== TOP 5 yearly + cost sensitivity ===")
    for name in res['strategy'].head(5):
        tr = trades_by.get(name, [])
        if tr:
            print(f"\n--- {name} ---")
            print("Yearly:")
            print(yearly(tr).to_string(index=False))
            print("Cost sensitivity:")
            print(cost_sensitivity(tr).to_string(index=False))

    # Save top trades CSV
    top_name = res.iloc[0]['strategy']
    pd.DataFrame(trades_by[top_name]).to_csv(OUT_DIR / 'XAU_1H_best_trades.csv', index=False)
    print(f"\nSaved: XAU_1H_audit_summary.csv, XAU_1H_best_trades.csv (top={top_name})")


if __name__ == '__main__':
    main()
