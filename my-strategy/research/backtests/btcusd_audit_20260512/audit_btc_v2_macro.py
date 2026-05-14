#!/usr/bin/env python3
"""BTCUSD V2 deep audit — with DXY + BTC.D macro filters.

2-stage: (1) broad sweep over macro × HTF, (2) refine top combos with triggers/targets.
"""
import pandas as pd
import numpy as np
from pathlib import Path

OUT_DIR = Path(__file__).parent
SPREAD_R = 0.05

BTC_FILES = {
    '1D':  '/Users/cristrein/Downloads/PEPPERSTONE_BTCUSD, 1D_dfd6b.csv',
    '12H': '/Users/cristrein/Downloads/PEPPERSTONE_BTCUSD, 720_18378.csv',
    '4H':  '/Users/cristrein/Downloads/PEPPERSTONE_BTCUSD, 240_cfb3e.csv',
    '1H':  '/Users/cristrein/Downloads/PEPPERSTONE_BTCUSD, 60_807e4.csv',
}
DXY_4H = '/Users/cristrein/Downloads/TVC_DXY, 240_cf460.csv'
BTCD_1D = '/Users/cristrein/Downloads/CRYPTOCAP_BTC.D, 1D_e4d67.csv'


def load_btc(path):
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
    df['atr_squeeze'] = df['atr14'] < df['atr_ma20']  # opposite
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


def load_macro_dxy():
    df = pd.read_csv(DXY_4H)
    df.columns = [c.strip() for c in df.columns]
    df['time'] = pd.to_datetime(df['time'], unit='s')
    df = df.sort_values('time').reset_index(drop=True)
    for c in ['open', 'high', 'low', 'close']:
        df[c] = pd.to_numeric(df[c], errors='coerce')
    df['dxy_ema50'] = df['close'].ewm(span=50, adjust=False).mean()
    df['dxy_ema200'] = df['close'].ewm(span=200, adjust=False).mean()
    df['dxy_bearish'] = df['close'] < df['dxy_ema50']
    df['dxy_bullish'] = df['close'] > df['dxy_ema50']
    df['dxy_below_ema200'] = df['close'] < df['dxy_ema200']
    df['dxy_falling'] = df['close'].diff(5) < 0
    df['dxy_strong_bear'] = df['dxy_bearish'] & df['dxy_falling']
    return df[['time', 'close', 'dxy_bearish', 'dxy_bullish', 'dxy_below_ema200',
               'dxy_falling', 'dxy_strong_bear']].rename(columns={'close': 'dxy_close'})


def load_macro_btcd():
    df = pd.read_csv(BTCD_1D)
    df.columns = [c.strip() for c in df.columns]
    df['time'] = pd.to_datetime(df['time'], unit='s')
    df = df.sort_values('time').reset_index(drop=True)
    for c in ['open', 'high', 'low', 'close']:
        df[c] = pd.to_numeric(df[c], errors='coerce')
    df['btcd_ema50'] = df['close'].ewm(span=50, adjust=False).mean()
    df['btcd_ema200'] = df['close'].ewm(span=200, adjust=False).mean()
    df['btcd_bullish'] = df['close'] > df['btcd_ema50']
    df['btcd_bearish'] = df['close'] < df['btcd_ema50']
    df['btcd_rising'] = df['close'].diff(5) > 0
    df['btcd_falling'] = df['close'].diff(5) < 0
    df['btcd_strong_bull'] = df['btcd_bullish'] & df['btcd_rising']
    df['btcd_altseason'] = df['btcd_bearish'] & df['btcd_falling']  # alts gaining vs BTC
    return df[['time', 'close', 'btcd_bullish', 'btcd_bearish',
               'btcd_rising', 'btcd_falling', 'btcd_strong_bull',
               'btcd_altseason']].rename(columns={'close': 'btcd_close'})


def attach_macro(df_btc, df_macro):
    df = df_btc.sort_values('time').reset_index(drop=True)
    m = df_macro.sort_values('time').reset_index(drop=True)
    return pd.merge_asof(df, m, on='time', direction='backward')


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


def cost_sens(trades):
    rows = []
    for s in [0.0, 0.05, 0.07, 0.10]:
        m = metrics(trades, spread=s)
        rows.append({'spread': s, 'total': m['total_r_net'], 'avg': m['avg_r_net'], 'pf': m['pf_net']})
    return pd.DataFrame(rows)


# =========================================================
# Trigger functions — base requirements
# =========================================================
def has_base_trend(row):
    """Required for ALL: regime EMA stack + ATR expanding."""
    if not row.get('close_above_ema200', False): return False
    if not row.get('ema50_above_ema200', False): return False
    if not row.get('atr_expanding', False): return False
    rsi = row.get('RSI', np.nan); rsi_ma = row.get('RSI-based MA', np.nan)
    if pd.isna(rsi) or pd.isna(rsi_ma) or rsi <= rsi_ma: return False
    return True


def trg_breakout(df, i, row, n=10, body=0.5):
    if not (row['close'] > row['open']): return False
    if pd.isna(row.get('body_pct')) or row['body_pct'] < body: return False
    if not (row['close'] > df.at[i-1, f'swhi_{n}']): return False
    return has_base_trend(row)


def trg_breakout_decisive(df, i, row, body=0.6, rng=1.2):
    if not (row['close'] > row['open']): return False
    if pd.isna(row.get('body_pct')) or row['body_pct'] < body: return False
    if not (row['close'] > df.at[i-1, 'swhi_10']): return False
    range_field = 'range_ge_1_2_atr' if rng == 1.2 else 'range_ge_1_5_atr'
    if not row.get(range_field, False): return False
    return has_base_trend(row)


def trg_pullback_reclaim(df, i, row):
    """Pullback EMA50 + RSI cross up — ETH winner pattern."""
    if not has_base_trend(row): return False
    recent_touch = False
    for k in range(max(0, i-3), i+1):
        if df.at[k, 'low'] <= df.at[k, 'ema50'] <= df.at[k, 'high']:
            recent_touch = True
            break
    if not recent_touch: return False
    if row['close'] <= row['ema50']: return False
    rsi_prev = df.at[i-1, 'RSI'] if i > 0 else np.nan
    rsi_ma_prev = df.at[i-1, 'RSI-based MA'] if i > 0 else np.nan
    if pd.isna(rsi_prev) or pd.isna(rsi_ma_prev): return False
    if rsi_prev > rsi_ma_prev: return False
    return True


def trg_failed_breakdown(df, i, row):
    """Reclaim swing low — US500 winner pattern."""
    if not (row['close'] > row['open']): return False
    if pd.isna(row.get('body_pct')) or row['body_pct'] < 0.5: return False
    # Recent breakdown below swlo_10 within last 5 bars
    breakdown = False
    for k in range(max(0, i-5), i):
        if df.at[k, 'low'] < df.at[max(0, k-1), 'swlo_10']:
            breakdown = True
            break
    if not breakdown: return False
    # Reclaim: close back above swlo_10
    if row['close'] <= df.at[i-1, 'swlo_10']: return False
    return has_base_trend(row)


# =========================================================
# Macro filter wrappers
# =========================================================
def with_filters(trg_fn, *filter_keys):
    def wrapped(df, i, row):
        if not trg_fn(df, i, row): return False
        for k in filter_keys:
            if not row.get(k, False): return False
        return True
    return wrapped


def main():
    print("=== Loading BTC + macro CSVs ===")
    data = {tf: load_btc(p) for tf, p in BTC_FILES.items()}
    df1d, df12, df4, df1 = data['1D'], data['12H'], data['4H'], data['1H']
    df_dxy = load_macro_dxy()
    df_btcd = load_macro_btcd()

    print(f"BTC 4H rows={len(df4)} span={(df4.time.max()-df4.time.min()).days/365.25:.2f}y")
    print(f"BTC 1H rows={len(df1)} span={(df1.time.max()-df1.time.min()).days/365.25:.2f}y")

    # Attach HTF + macro
    df4 = htf_context(df4, df12, 'htf12h')
    df4 = htf_context(df4, df1d, 'htf1d')
    df4 = attach_macro(df4, df_dxy)
    df4 = attach_macro(df4, df_btcd)

    df1 = htf_context(df1, df4, 'htf4h')
    df1 = htf_context(df1, df12, 'htf12h')
    df1 = htf_context(df1, df1d, 'htf1d')
    df1 = attach_macro(df1, df_dxy)
    df1 = attach_macro(df1, df_btcd)

    summaries = []
    trades_by = {}

    # =====================================================
    # SWING 4H — comprehensive sweep
    # =====================================================
    print(f"\n=== SWING 4H sweep ===")

    # Macro combos to test (8 combos)
    macro_combos = [
        ('no_macro', []),
        ('DXY_bear', ['dxy_bearish']),
        ('DXY_strong_bear', ['dxy_strong_bear']),
        ('DXY_below_ema200', ['dxy_below_ema200']),
        ('BTCD_bull', ['btcd_bullish']),
        ('BTCD_strong_bull', ['btcd_strong_bull']),
        ('BTCD_altseason', ['btcd_altseason']),
        ('DXY_bear+BTCD_bull', ['dxy_bearish', 'btcd_bullish']),
        ('DXY_strong_bear+BTCD_bull', ['dxy_strong_bear', 'btcd_bullish']),
        ('DXY_bear+BTCD_strong_bull', ['dxy_bearish', 'btcd_strong_bull']),
        ('DXY_strong_bear+BTCD_strong_bull', ['dxy_strong_bear', 'btcd_strong_bull']),
        ('DXY_bear+BTCD_altseason', ['dxy_bearish', 'btcd_altseason']),
    ]

    # HTF combos
    htf_combos = [
        ('HTF_none', []),
        ('HTF1D', ['htf1d_bullish']),
        ('HTF1D+12H', ['htf1d_bullish', 'htf12h_bullish']),
    ]

    # Triggers (5 base triggers)
    swing_triggers = [
        ('brk10_b50', lambda df, i, r: trg_breakout(df, i, r, n=10, body=0.5)),
        ('brk10_b60', lambda df, i, r: trg_breakout(df, i, r, n=10, body=0.6)),
        ('brk10_b70', lambda df, i, r: trg_breakout(df, i, r, n=10, body=0.7)),
        ('brk20_b50', lambda df, i, r: trg_breakout(df, i, r, n=20, body=0.5)),
        ('brk_dec_b60_r12', lambda df, i, r: trg_breakout_decisive(df, i, r, body=0.6, rng=1.2)),
        ('brk_dec_b70_r15', lambda df, i, r: trg_breakout_decisive(df, i, r, body=0.7, rng=1.5)),
        ('pullback_ema50', trg_pullback_reclaim),
        ('failed_breakdown', trg_failed_breakdown),
    ]

    targets = [2.0, 2.5, 3.0, 4.0]

    print(f"  Macro combos: {len(macro_combos)} | HTF: {len(htf_combos)} | Triggers: {len(swing_triggers)} | Targets: {len(targets)}")
    print(f"  Total: {len(macro_combos)*len(htf_combos)*len(swing_triggers)*len(targets)} swing configs")

    swing_count = 0
    for mname, mkeys in macro_combos:
        for hname, hkeys in htf_combos:
            for tname, tfn in swing_triggers:
                signal = with_filters(tfn, *mkeys, *hkeys)
                for trg in targets:
                    label = f'BTC_SWING_4H_{tname}|{mname}|{hname}|tgt{trg}R'
                    tr = run_long(df4, signal, trg, 24, label)
                    summaries.append({'strategy': label, **metrics(tr)})
                    trades_by[label] = tr
                    swing_count += 1
    print(f"  Completed {swing_count} swing configs")

    # =====================================================
    # INTRADAY 1H — leaner sweep
    # =====================================================
    print(f"\n=== INTRADAY 1H sweep ===")

    intra_macro_combos = [
        ('no_macro', []),
        ('DXY_bear', ['dxy_bearish']),
        ('DXY_strong_bear', ['dxy_strong_bear']),
        ('BTCD_bull', ['btcd_bullish']),
        ('DXY_bear+BTCD_bull', ['dxy_bearish', 'btcd_bullish']),
        ('DXY_bear+BTCD_strong_bull', ['dxy_bearish', 'btcd_strong_bull']),
    ]
    intra_htf = [
        ('HTF1D', ['htf1d_bullish']),
        ('HTF1D+HTF4H', ['htf1d_bullish', 'htf4h_bullish']),
    ]
    intra_triggers = [
        ('brk_dec_b60_r12', lambda df, i, r: trg_breakout_decisive(df, i, r, body=0.6, rng=1.2)),
        ('brk_dec_b70_r15', lambda df, i, r: trg_breakout_decisive(df, i, r, body=0.7, rng=1.5)),
        ('pullback_ema50', trg_pullback_reclaim),
    ]
    intra_targets = [2.0, 2.5, 3.0, 4.0]

    intra_count = 0
    for mname, mkeys in intra_macro_combos:
        for hname, hkeys in intra_htf:
            for tname, tfn in intra_triggers:
                signal = with_filters(tfn, *mkeys, *hkeys)
                for trg in intra_targets:
                    label = f'BTC_INTRA_1H_{tname}|{mname}|{hname}|tgt{trg}R'
                    tr = run_long(df1, signal, trg, 20, label)
                    summaries.append({'strategy': label, **metrics(tr)})
                    trades_by[label] = tr
                    intra_count += 1
    print(f"  Completed {intra_count} intraday configs")

    # =====================================================
    # Output
    # =====================================================
    res = pd.DataFrame(summaries).sort_values('total_r_net', ascending=False)
    res.to_csv(OUT_DIR / 'BTC_V2_macro_audit_summary.csv', index=False)

    cols = ['strategy', 'n', 'trades_per_week', 'trades_per_month', 'total_r_net',
            'avg_r_net', 'win_rate', 'pf_net', 'max_losing_streak',
            'r_no_top5_net', 'r_no_top10_net']

    # Filter for robust edge: PF >= 1.5, avg >= 0.20, no_top5 >= 5
    swing = res[res['strategy'].str.contains('SWING_4H')]
    intra = res[res['strategy'].str.contains('INTRA_1H')]

    print("\n=== TOP 15 SWING 4H by total_r_net ===")
    print(swing[cols].head(15).to_string(index=False))

    print("\n=== SWING — robust edge filter (PF>=1.5 AND avg>=0.20 AND no_top5>=5 AND n>=40) ===")
    robust_swing = swing[(swing.pf_net >= 1.5) & (swing.avg_r_net >= 0.20) &
                         (swing.r_no_top5_net >= 5) & (swing.n >= 40)]
    if len(robust_swing) > 0:
        print(robust_swing[cols].head(20).to_string(index=False))
    else:
        print("  NONE — no swing config meets robust edge criteria.")

    print("\n=== TOP 15 INTRADAY 1H by total_r_net ===")
    print(intra[cols].head(15).to_string(index=False))

    print("\n=== INTRADAY — robust edge filter ===")
    robust_intra = intra[(intra.pf_net >= 1.5) & (intra.avg_r_net >= 0.20) &
                         (intra.r_no_top5_net >= 5) & (intra.n >= 40)]
    if len(robust_intra) > 0:
        print(robust_intra[cols].head(20).to_string(index=False))
    else:
        print("  NONE — no intraday config meets robust edge criteria.")

    # Detail TOP 5 from each layer
    for layer, sub in [('SWING', swing), ('INTRADAY', intra)]:
        print(f"\n\n========= TOP 5 {layer} DETAIL =========")
        for name in sub['strategy'].head(5):
            tr = trades_by.get(name, [])
            if tr:
                print(f"\n--- {name} ---")
                print("Yearly:")
                print(yearly(tr).to_string(index=False))
                print("Cost:")
                print(cost_sens(tr).to_string(index=False))

    print(f"\nSaved: BTC_V2_macro_audit_summary.csv ({len(res)} configs total)")


if __name__ == '__main__':
    main()
