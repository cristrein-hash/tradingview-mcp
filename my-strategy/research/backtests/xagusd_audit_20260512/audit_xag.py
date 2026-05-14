#!/usr/bin/env python3
"""XAGUSD deep audit — SWING 4H + INTRADAY 1H with DXY macro filter."""
import pandas as pd
import numpy as np
from pathlib import Path
import sys

OUT_DIR = Path(__file__).parent
SPREAD_R = 0.05

FILES = {
    '1D':  '/Users/cristrein/Downloads/PEPPERSTONE_XAGUSD, 1D_4b306.csv',
    '12H': '/Users/cristrein/Downloads/PEPPERSTONE_XAGUSD, 720_ab708.csv',
    '4H':  '/Users/cristrein/Downloads/PEPPERSTONE_XAGUSD, 240_47164.csv',
    '1H':  '/Users/cristrein/Downloads/PEPPERSTONE_XAGUSD, 60_1a0a1.csv',
}
DXY_4H = '/Users/cristrein/Downloads/TVC_DXY, 240_cf460.csv'


def load_asset(path):
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
    return df


def load_dxy():
    df = pd.read_csv(DXY_4H)
    df.columns = [c.strip() for c in df.columns]
    df['time'] = pd.to_datetime(df['time'], unit='s')
    df = df.sort_values('time').reset_index(drop=True)
    for c in ['open', 'high', 'low', 'close']:
        df[c] = pd.to_numeric(df[c], errors='coerce')
    df['dxy_ema50'] = df['close'].ewm(span=50, adjust=False).mean()
    df['dxy_ema200'] = df['close'].ewm(span=200, adjust=False).mean()
    df['dxy_bearish'] = df['close'] < df['dxy_ema50']
    df['dxy_below_ema200'] = df['close'] < df['dxy_ema200']
    df['dxy_falling'] = df['close'].diff(5) < 0
    df['dxy_strong_bear'] = df['dxy_bearish'] & df['dxy_falling']
    return df[['time', 'dxy_bearish', 'dxy_below_ema200', 'dxy_falling', 'dxy_strong_bear']]


def attach(df_a, df_m):
    return pd.merge_asof(df_a.sort_values('time').reset_index(drop=True),
                         df_m.sort_values('time').reset_index(drop=True),
                         on='time', direction='backward')


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


def simulate(df, idx, entry, stop, tgt_r, max_bars):
    R = abs(entry - stop)
    if R <= 0: return None
    target = entry + R * tgt_r
    cur_stop = stop
    moved_be = False
    for j in range(idx + 1, min(idx + 1 + max_bars, len(df))):
        h, l = df.at[j, 'high'], df.at[j, 'low']
        if not moved_be and h >= entry + R:
            cur_stop = max(cur_stop, entry)
            moved_be = True
        if l <= cur_stop:
            return {'exit_idx': j, 'r': (cur_stop - entry) / R, 'bars': j - idx, 'outcome': 'stop'}
        if h >= target:
            return {'exit_idx': j, 'r': (target - entry) / R, 'bars': j - idx, 'outcome': 'target'}
    last = min(idx + max_bars, len(df) - 1)
    return {'exit_idx': last, 'r': (df.at[last, 'close'] - entry) / R, 'bars': last - idx, 'outcome': 'timeout'}


def run_long(df, fn, tgt_r, max_bars, label):
    trades = []
    i = 50
    while i < len(df) - 1:
        row = df.iloc[i]
        if pd.isna(row.get('atr14')) or pd.isna(row.get('ema200')):
            i += 1; continue
        if fn(df, i, row):
            entry = row['close']
            stop = row['low'] - 0.5 * row['atr14']
            R = entry - stop
            if R <= 0 or R > 5 * row['atr14']:
                i += 1; continue
            tr = simulate(df, i, entry, stop, tgt_r, max_bars)
            if tr:
                tr['entry_time'] = row['time']
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
    r = np.array([t['r'] - spread for t in trades])
    wins = r > 0
    pf = r[r > 0].sum() / -r[r <= 0].sum() if (r <= 0).any() else float('inf')
    streak = mx = 0
    for w in wins:
        if not w: streak += 1; mx = max(mx, streak)
        else: streak = 0
    sd = np.sort(r)[::-1]
    nt5 = r.sum() - sd[:5].sum() if len(r) >= 5 else 0
    nt10 = r.sum() - sd[:10].sum() if len(r) >= 10 else 0
    times = [t['entry_time'] for t in trades]
    span_d = (max(times) - min(times)).days or 1
    return dict(
        n=len(r), total_r_net=round(r.sum(), 2), avg_r_net=round(r.mean(), 4),
        win_rate=round(wins.mean(), 3), pf_net=round(pf, 2), max_losing_streak=mx,
        r_no_top5_net=round(nt5, 2), r_no_top10_net=round(nt10, 2),
        trades_per_week=round(len(r) / (span_d / 7), 2),
        trades_per_month=round(len(r) / (span_d / 30), 2),
    )


def yearly(trades, spread=SPREAD_R):
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
    return pd.DataFrame([{'spread': s, **{k: metrics(trades, spread=s)[k]
                          for k in ['total_r_net', 'avg_r_net', 'pf_net']}}
                         for s in [0.0, 0.05, 0.07, 0.10]])


# ============= Triggers =============
def has_base_trend(row):
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


def trg_brk_decisive(df, i, row, body=0.6, rng=1.2):
    if not (row['close'] > row['open']): return False
    if pd.isna(row.get('body_pct')) or row['body_pct'] < body: return False
    if not (row['close'] > df.at[i-1, 'swhi_10']): return False
    field = 'range_ge_1_2_atr' if rng == 1.2 else 'range_ge_1_5_atr'
    if not row.get(field, False): return False
    return has_base_trend(row)


def trg_pullback(df, i, row):
    if not has_base_trend(row): return False
    rec = False
    for k in range(max(0, i-3), i+1):
        if df.at[k, 'low'] <= df.at[k, 'ema50'] <= df.at[k, 'high']:
            rec = True; break
    if not rec: return False
    if row['close'] <= row['ema50']: return False
    rsi_p = df.at[i-1, 'RSI'] if i > 0 else np.nan
    rsi_ma_p = df.at[i-1, 'RSI-based MA'] if i > 0 else np.nan
    if pd.isna(rsi_p) or pd.isna(rsi_ma_p) or rsi_p > rsi_ma_p: return False
    return True


def with_filters(trg_fn, *keys):
    def wrapped(df, i, row):
        if not trg_fn(df, i, row): return False
        for k in keys:
            if not row.get(k, False): return False
        return True
    return wrapped


def main():
    print("=== Loading XAGUSD + DXY ===")
    data = {tf: load_asset(p) for tf, p in FILES.items()}
    df1d, df12, df4, df1 = data['1D'], data['12H'], data['4H'], data['1H']
    df_dxy = load_dxy()
    print(f"4H rows={len(df4)} span={(df4.time.max()-df4.time.min()).days/365.25:.2f}y")
    print(f"1H rows={len(df1)} span={(df1.time.max()-df1.time.min()).days/365.25:.2f}y")

    df4 = htf_context(df4, df12, 'htf12h')
    df4 = htf_context(df4, df1d, 'htf1d')
    df4 = attach(df4, df_dxy)
    df1 = htf_context(df1, df4, 'htf4h')
    df1 = htf_context(df1, df12, 'htf12h')
    df1 = htf_context(df1, df1d, 'htf1d')
    df1 = attach(df1, df_dxy)

    summaries = []
    trades_by = {}

    # ============= SWING 4H =============
    macros = [
        ('no_macro', []),
        ('DXY_bear', ['dxy_bearish']),
        ('DXY_strong_bear', ['dxy_strong_bear']),
        ('DXY_below_ema200', ['dxy_below_ema200']),
    ]
    htfs = [
        ('HTF1D', ['htf1d_bullish']),
        ('HTF1D+12H', ['htf1d_bullish', 'htf12h_bullish']),
    ]
    swing_trgs = [
        ('brk10_b50', lambda df, i, r: trg_breakout(df, i, r, 10, 0.5)),
        ('brk10_b60', lambda df, i, r: trg_breakout(df, i, r, 10, 0.6)),
        ('brk10_b70', lambda df, i, r: trg_breakout(df, i, r, 10, 0.7)),
        ('brk_dec_b60_r12', lambda df, i, r: trg_brk_decisive(df, i, r, 0.6, 1.2)),
        ('brk_dec_b70_r15', lambda df, i, r: trg_brk_decisive(df, i, r, 0.7, 1.5)),
        ('pullback', trg_pullback),
    ]
    targets = [2.0, 2.5, 3.0, 4.0]

    sn = 0
    for mname, mk in macros:
        for hname, hk in htfs:
            for tname, tfn in swing_trgs:
                sig = with_filters(tfn, *mk, *hk)
                for trg in targets:
                    lbl = f'XAG_SWING_4H_{tname}|{mname}|{hname}|tgt{trg}R'
                    tr = run_long(df4, sig, trg, 24, lbl)
                    summaries.append({'strategy': lbl, **metrics(tr)})
                    trades_by[lbl] = tr
                    sn += 1
    print(f"\nSWING: {sn} configs")

    # ============= INTRADAY 1H =============
    intra_htfs = [
        ('HTF1D', ['htf1d_bullish']),
        ('HTF1D+HTF4H', ['htf1d_bullish', 'htf4h_bullish']),
    ]
    intra_trgs = [
        ('brk10_b60', lambda df, i, r: trg_breakout(df, i, r, 10, 0.6)),
        ('brk_dec_b60_r12', lambda df, i, r: trg_brk_decisive(df, i, r, 0.6, 1.2)),
        ('brk_dec_b70_r15', lambda df, i, r: trg_brk_decisive(df, i, r, 0.7, 1.5)),
        ('pullback', trg_pullback),
    ]
    intra_targets = [2.0, 2.5, 3.0, 4.0]

    inn = 0
    for mname, mk in macros:
        for hname, hk in intra_htfs:
            for tname, tfn in intra_trgs:
                sig = with_filters(tfn, *mk, *hk)
                for trg in intra_targets:
                    lbl = f'XAG_INTRA_1H_{tname}|{mname}|{hname}|tgt{trg}R'
                    tr = run_long(df1, sig, trg, 20, lbl)
                    summaries.append({'strategy': lbl, **metrics(tr)})
                    trades_by[lbl] = tr
                    inn += 1
    print(f"INTRADAY: {inn} configs")

    res = pd.DataFrame(summaries).sort_values('total_r_net', ascending=False)
    res.to_csv(OUT_DIR / 'XAG_audit_summary.csv', index=False)

    cols = ['strategy', 'n', 'trades_per_week', 'trades_per_month', 'total_r_net',
            'avg_r_net', 'win_rate', 'pf_net', 'max_losing_streak',
            'r_no_top5_net', 'r_no_top10_net']

    swing = res[res['strategy'].str.contains('SWING_4H')]
    intra = res[res['strategy'].str.contains('INTRA_1H')]

    print("\n=== TOP 15 SWING 4H ===")
    print(swing[cols].head(15).to_string(index=False))

    print("\n=== Robust SWING (PF>=1.5 & avg>=0.20 & no_top5>=5 & n>=40) ===")
    rb_s = swing[(swing.pf_net >= 1.5) & (swing.avg_r_net >= 0.20) &
                 (swing.r_no_top5_net >= 5) & (swing.n >= 40)]
    print(rb_s[cols].to_string(index=False) if len(rb_s) > 0 else "  NONE")

    print("\n=== TOP 15 INTRADAY 1H ===")
    print(intra[cols].head(15).to_string(index=False))

    print("\n=== Robust INTRADAY ===")
    rb_i = intra[(intra.pf_net >= 1.5) & (intra.avg_r_net >= 0.20) &
                 (intra.r_no_top5_net >= 5) & (intra.n >= 40)]
    print(rb_i[cols].to_string(index=False) if len(rb_i) > 0 else "  NONE")

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

    print(f"\nSaved: XAG_audit_summary.csv ({len(res)} configs)")


if __name__ == '__main__':
    main()
