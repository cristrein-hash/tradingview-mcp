#!/usr/bin/env python3
"""EURUSD Deep Strategy Audit — 2026-05-12. Full search incl. macro DXY."""
import pandas as pd
import numpy as np
from pathlib import Path
import sys

OUT_DIR = Path(__file__).parent

FILES = {
    '1D':  '/Users/cristrein/Downloads/PEPPERSTONE_EURUSD, 1D_2f9df.csv',
    '12H': '/Users/cristrein/Downloads/PEPPERSTONE_EURUSD, 720_77e25.csv',
    '4H':  '/Users/cristrein/Downloads/PEPPERSTONE_EURUSD, 240_c99e7.csv',
    '30M': '/Users/cristrein/Downloads/PEPPERSTONE_EURUSD, 30_cc449.csv',
    '15M': '/Users/cristrein/Downloads/PEPPERSTONE_EURUSD, 15_59a92.csv',
}

DXY_FILE = '/Users/cristrein/Downloads/TVC_DXY, 240_43cf2.csv'

SPREAD_R = 0.05


def load(path):
    df = pd.read_csv(path)
    df.columns = [c.strip() for c in df.columns]
    cols = list(df.columns); seen, new = {}, []
    for c in cols:
        if c in seen: seen[c] += 1; new.append(f"{c}_{seen[c]}")
        else: seen[c] = 0; new.append(c)
    df.columns = new
    df['time'] = pd.to_datetime(df['time'], unit='s')
    df = df.sort_values('time').reset_index(drop=True)
    for c in ['open','high','low','close','RSI','RSI-based MA','NAS_RSI',
              'NAS_DISTANCE_FROM_EMA_ATR','NAS_LONG_SIGNAL','NAS_SHORT_SIGNAL',
              'NAS_BOTTOM_SIGNAL','NAS_TOP_SIGNAL','Regular Bullish','Regular Bearish']:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors='coerce')
    h, l, c = df['high'], df['low'], df['close']
    pc = c.shift(1)
    tr = pd.concat([(h - l).abs(), (h - pc).abs(), (l - pc).abs()], axis=1).max(axis=1)
    df['atr14'] = tr.ewm(alpha=1/14, adjust=False).mean()
    body = (df['close'] - df['open']).abs()
    rng = (df['high'] - df['low']).replace(0, np.nan)
    df['body_pct'] = body / rng
    df['upper_wick'] = (df['high'] - df[['open','close']].max(axis=1)) / rng
    df['lower_wick'] = (df[['open','close']].min(axis=1) - df['low']) / rng
    df['close_in_upper_third'] = (df['close'] - df['low']) / rng >= 2/3
    df['close_in_lower_third'] = (df['close'] - df['low']) / rng <= 1/3
    shape_cols = [c for c in df.columns if c.startswith('Shapes')]
    df['has_bubble'] = (df[shape_cols].fillna(0).abs().sum(axis=1) > 0) if shape_cols else False
    if 'RSI' in df.columns and 'RSI-based MA' in df.columns:
        df['rsi_above_ma'] = df['RSI'] > df['RSI-based MA']
    for n in (5, 10, 20):
        df[f'swhi_{n}'] = df['high'].rolling(n).max()
        df[f'swlo_{n}'] = df['low'].rolling(n).min()
    # ADX
    up = h - h.shift(1); dn = l.shift(1) - l
    plus_dm = np.where((up > dn) & (up > 0), up, 0.0)
    minus_dm = np.where((dn > up) & (dn > 0), dn, 0.0)
    plus_dm_s = pd.Series(plus_dm, index=df.index).ewm(alpha=1/14, adjust=False).mean()
    minus_dm_s = pd.Series(minus_dm, index=df.index).ewm(alpha=1/14, adjust=False).mean()
    di_plus = 100 * plus_dm_s / df['atr14'].replace(0, np.nan)
    di_minus = 100 * minus_dm_s / df['atr14'].replace(0, np.nan)
    dx = 100 * (di_plus - di_minus).abs() / (di_plus + di_minus).replace(0, np.nan)
    df['adx14'] = dx.ewm(alpha=1/14, adjust=False).mean()
    df['di_plus'] = di_plus; df['di_minus'] = di_minus
    df['ema20'] = c.ewm(span=20, adjust=False).mean()
    df['ema50'] = c.ewm(span=50, adjust=False).mean()
    df['ema200'] = c.ewm(span=200, adjust=False).mean()
    df['ema50_slope'] = df['ema50'].diff(5)
    df['close_above_ema50'] = c > df['ema50']
    df['close_above_ema200'] = c > df['ema200']
    df['ema50_above_ema200'] = df['ema50'] > df['ema200']
    df['atr_ma20'] = df['atr14'].rolling(20).mean()
    df['atr_expanding'] = df['atr14'] > df['atr_ma20']
    # Bollinger
    df['bb_mid'] = c.rolling(20).mean()
    df['bb_std'] = c.rolling(20).std()
    df['bb_upper'] = df['bb_mid'] + 2 * df['bb_std']
    df['bb_lower'] = df['bb_mid'] - 2 * df['bb_std']
    df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['bb_mid'].replace(0, np.nan)
    df['bb_width_ma'] = df['bb_width'].rolling(20).mean()
    df['bb_squeeze'] = df['bb_width'] < df['bb_width_ma'] * 0.85
    # Failed breakdown
    df['failed_breakdown'] = (df['low'] < df['swlo_20'].shift(1)) & \
                              (df['close'] > df['swlo_20'].shift(1)) & \
                              (df['close'] > df['open'])
    # Inside bar
    df['inside_bar'] = (df['high'] < df['high'].shift(1)) & (df['low'] > df['low'].shift(1))
    # Hammer
    df['hammer'] = (df['lower_wick'] >= 0.6) & (df['body_pct'] <= 0.3) & (df['close'] > df['open'])
    # Hour-of-day (in UTC) — EUR session most active 7-15 UTC
    df['hour_utc'] = df['time'].dt.hour
    df['eu_session'] = df['hour_utc'].isin([7, 8, 9, 10, 11, 12, 13, 14])
    df['us_session'] = df['hour_utc'].isin([13, 14, 15, 16, 17, 18])
    return df


def load_macro_dxy():
    df = pd.read_csv(DXY_FILE)
    df.columns = [c.strip() for c in df.columns]
    df['time'] = pd.to_datetime(df['time'], unit='s')
    df = df.sort_values('time').reset_index(drop=True)
    for c in ['open','high','low','close']:
        df[c] = pd.to_numeric(df[c], errors='coerce')
    df['dxy_ema50'] = df['close'].ewm(span=50, adjust=False).mean()
    df['dxy_ema200'] = df['close'].ewm(span=200, adjust=False).mean()
    df['dxy_bullish'] = df['close'] > df['dxy_ema50']
    df['dxy_bearish'] = df['close'] < df['dxy_ema50']
    df['dxy_below_ema200'] = df['close'] < df['dxy_ema200']
    df['dxy_slope'] = df['close'].diff(5)
    df['dxy_falling'] = df['dxy_slope'] < 0
    return df[['time', 'close', 'dxy_bullish', 'dxy_bearish', 'dxy_below_ema200', 'dxy_falling']].rename(
        columns={'close': 'dxy_close'})


def attach_dxy(df_eur, df_dxy):
    df = df_eur.sort_values('time').reset_index(drop=True)
    macro = df_dxy.sort_values('time').reset_index(drop=True)
    return pd.merge_asof(df, macro, on='time', direction='backward')


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


def simulate_trade(df, idx, direction, entry, stop, target_r, max_bars, be_at_1r=False):
    R = abs(entry - stop)
    if R <= 0: return None
    sign = 1 if direction == 'LONG' else -1
    target = entry + sign * R * target_r
    cur_stop = stop; mfe = mae = 0.0
    moved_be = False
    for j in range(idx + 1, min(idx + 1 + max_bars, len(df))):
        h = df.at[j, 'high']; l = df.at[j, 'low']
        if direction == 'LONG':
            fav = (h - entry) / R; adv = (entry - l) / R
        else:
            fav = (entry - l) / R; adv = (h - entry) / R
        mfe = max(mfe, fav); mae = max(mae, adv)
        if be_at_1r and not moved_be and fav >= 1.0:
            cur_stop = entry; moved_be = True
        if direction == 'LONG':
            if l <= cur_stop:
                exit_price = cur_stop; r_out = (exit_price - entry) / R
                return {'exit_idx': j, 'exit_price': exit_price, 'r_outcome': r_out,
                        'exit_reason': 'stop' if cur_stop <= entry else 'be',
                        'mfe': mfe, 'mae': mae, 'bars_held': j - idx}
            if h >= target:
                exit_price = target; r_out = (exit_price - entry) / R
                return {'exit_idx': j, 'exit_price': exit_price, 'r_outcome': r_out,
                        'exit_reason': 'target', 'mfe': mfe, 'mae': mae, 'bars_held': j - idx}
        else:
            if h >= cur_stop:
                exit_price = cur_stop; r_out = (entry - exit_price) / R
                return {'exit_idx': j, 'exit_price': exit_price, 'r_outcome': r_out,
                        'exit_reason': 'stop' if cur_stop >= entry else 'be',
                        'mfe': mfe, 'mae': mae, 'bars_held': j - idx}
            if l <= target:
                exit_price = target; r_out = (entry - exit_price) / R
                return {'exit_idx': j, 'exit_price': exit_price, 'r_outcome': r_out,
                        'exit_reason': 'target', 'mfe': mfe, 'mae': mae, 'bars_held': j - idx}
    exit_idx = min(idx + max_bars, len(df) - 1)
    last = df.at[exit_idx, 'close']
    r_out = (last - entry) / R if direction == 'LONG' else (entry - last) / R
    return {'exit_idx': exit_idx, 'exit_price': last, 'r_outcome': r_out,
            'exit_reason': 'time_exit', 'mfe': mfe, 'mae': mae, 'bars_held': max_bars}


def metrics(trades, spread=SPREAD_R):
    if not trades:
        return {'n': 0}
    df = pd.DataFrame(trades)
    r_g = df['r_outcome']; r_n = r_g - spread
    span_days = (pd.to_datetime(df['entry_time'].max()) - pd.to_datetime(df['entry_time'].min())).days
    sw = max(1, span_days/7); sm = max(1, span_days/30.44)
    wins = r_n[r_n > 0]; losses = r_n[r_n < 0]
    pf = abs(wins.sum() / losses.sum()) if len(losses) and losses.sum() != 0 else float('inf')
    streak = max_streak = 0
    for v in r_n:
        if v <= 0: streak += 1; max_streak = max(max_streak, streak)
        else: streak = 0
    sorted_r = sorted(r_n.tolist(), reverse=True)
    return {
        'n': len(df),
        'trades_per_week': round(len(df)/sw, 2),
        'trades_per_month': round(len(df)/sm, 2),
        'total_r_net': round(r_n.sum(), 2),
        'avg_r_net': round(r_n.mean(), 4),
        'win_rate': round((r_n > 0).mean(), 3),
        'pf_net': round(pf, 2) if pf != float('inf') else 'inf',
        'max_losing_streak': max_streak,
        'r_no_top5_net': round(sum(sorted_r[5:]), 2),
        'r_no_top10_net': round(sum(sorted_r[10:]), 2),
        'best_r_net': round(sorted_r[0], 2),
    }


def yearly_metrics(trades, spread=SPREAD_R):
    if not trades: return pd.DataFrame()
    df = pd.DataFrame(trades)
    df['year'] = pd.to_datetime(df['entry_time']).dt.year
    df['r_net'] = df['r_outcome'] - spread
    return df.groupby('year').agg(
        n=('r_net', 'count'),
        total_net=('r_net', 'sum'),
        avg_net=('r_net', 'mean'),
        win_rate=('r_net', lambda x: (x > 0).mean()),
    ).round(3).reset_index()


# ============================================================
# STRATEGY DEFINITIONS — long-only
# ============================================================

def run_long(df, signal_func, target_r, max_bars, name, tf, stop_atr_mult=0.5, be=True):
    trades = []
    for i in range(200, len(df) - 1):
        row = df.iloc[i]
        if not signal_func(df, i, row): continue
        entry = row['close']; atr = row['atr14']
        if pd.isna(atr) or atr <= 0: continue
        stop = row['low'] - atr * stop_atr_mult
        R = abs(entry - stop)
        if R <= 0 or R / atr > 5: continue
        res = simulate_trade(df, i, 'LONG', entry, stop, target_r, max_bars, be_at_1r=be)
        if not res: continue
        res.update({'entry_time': row['time'], 'entry_price': entry, 'stop_price': stop,
                    'direction': 'LONG', 'r_planned': target_r, 'strategy': name, 'tf': tf})
        trades.append(res)
    return trades


def main():
    print("=== Loading EURUSD + indicators ===")
    data = {tf: load(p) for tf, p in FILES.items()}
    df4, df30, df15 = data['4H'], data['30M'], data['15M']
    df12, df1d = data['12H'], data['1D']

    # HTF context
    df4 = htf_context(df4, df12, 'htf12h')
    df4 = htf_context(df4, df1d, 'htf1d')
    df30 = htf_context(df30, df4, 'htf4h')
    df30 = htf_context(df30, df1d, 'htf1d')

    # DXY macro
    print("=== Loading DXY macro ===")
    df_dxy = load_macro_dxy()
    print(f"  DXY bars: {len(df_dxy)}  {df_dxy['time'].min().date()} → {df_dxy['time'].max().date()}")
    df4 = attach_dxy(df4, df_dxy)
    df30 = attach_dxy(df30, df_dxy)

    print(f"\n  EUR 4H bars: {len(df4)}  DXY bearish fraction: {df4['dxy_bearish'].mean():.2%}")

    summaries = []
    trades_by = {}

    # =============================================================
    # A. CURRENT module: EURUSD_30M_LONG_QUALITY_BREAKOUT_CONTINUATION
    # Expected rules: 30M setup, LONG only, RSI >= 54, 4H/1D supportive,
    # BE +1R, target 3R
    # =============================================================
    def sig_current_30m_qbreak(df, i, row):
        if not (row['close'] > row['open'] and row['body_pct'] >= 0.5
                and row['close'] > df.at[i-1, 'swhi_10']): return False
        rsi = row.get('RSI', np.nan)
        if pd.isna(rsi) or rsi < 54: return False
        if not row.get('close_above_ema50', False): return False
        if not row.get('ema50_above_ema200', False): return False
        return True

    print("\n=== A. Current: EURUSD_30M_QUALITY_BREAKOUT ===")
    t = run_long(df30, sig_current_30m_qbreak, 3.0, 16, 'A_30M_current', '30M')
    summaries.append({'strategy': 'A_EURUSD_30M_QUALITY_BREAKOUT_CONTINUATION (atual)', **metrics(t)})
    trades_by['A_30M_current'] = t

    # =============================================================
    # B. OLD GLOBAL: rejection close with RSI extreme
    # =============================================================
    def sig_old_strict_long(df, i, row):
        # Lower wick rejection + RSI <= 35
        if not (row['lower_wick'] >= 0.5 and row['body_pct'] <= 0.4
                and row.get('close_in_upper_third', False)): return False
        rsi = row.get('RSI', np.nan)
        if pd.isna(rsi) or rsi > 35: return False
        return True

    print("\n=== B. Old global rule ===")
    t = run_long(df4, sig_old_strict_long, 2.0, 30, 'B_old_strict_LONG_4H', '4H')
    summaries.append({'strategy': 'B_old_global_strict_LONG_4H (rejection+RSI ext)', **metrics(t)})

    # =============================================================
    # D. NEW 4H regime-filtered breakout (XAU/ETH pattern)
    # =============================================================
    def sig_4h_breakout_regime(df, i, row):
        if not (row['close'] > row['open'] and row['body_pct'] >= 0.5
                and row['close'] > df.at[i-1, 'swhi_10']): return False
        rsi = row.get('RSI', np.nan); rsi_ma = row.get('RSI-based MA', np.nan)
        if pd.isna(rsi) or pd.isna(rsi_ma) or rsi <= rsi_ma: return False
        if not row.get('close_above_ema200', False): return False
        if not row.get('ema50_above_ema200', False): return False
        if not row.get('atr_expanding', False): return False
        if pd.isna(row.get('ema50_slope', np.nan)) or row['ema50_slope'] <= 0: return False
        if pd.isna(row.get('adx14', np.nan)) or row['adx14'] < 20: return False
        return True

    print("\n=== D. NEW 4H Regime Breakout ===")
    for trg in [3.0, 4.0, 5.0]:
        for mb in [24, 30]:
            name = f'D_4H_BREAKOUT_REGIME_target{trg}R_hold{mb}'
            t = run_long(df4, sig_4h_breakout_regime, trg, mb, name, '4H')
            summaries.append({'strategy': name, **metrics(t)})
            trades_by[name] = t

    # =============================================================
    # E. 4H Failed Breakdown Regime (US500 winner pattern)
    # =============================================================
    def sig_4h_failed_breakdown(df, i, row):
        if not row.get('failed_breakdown', False): return False
        if row['body_pct'] < 0.5: return False
        if not row.get('close_above_ema200', False): return False
        if not row.get('ema50_above_ema200', False): return False
        if not row.get('atr_expanding', False): return False
        return True

    print("\n=== E. 4H Failed Breakdown ===")
    for trg, mb in [(2.5, 20), (3.0, 24), (3.5, 24), (4.0, 30)]:
        name = f'E_4H_FAILED_BREAKDOWN_target{trg}R'
        t = run_long(df4, sig_4h_failed_breakdown, trg, mb, name, '4H')
        summaries.append({'strategy': name, **metrics(t)})
        trades_by[name] = t

    # =============================================================
    # F. BB squeeze breakout 4H
    # =============================================================
    def sig_bb_squeeze_4h(df, i, row):
        prev_squeeze = df.at[i-1, 'bb_squeeze'] if i >= 1 else False
        if not prev_squeeze: return False
        if not (row['close'] > df.at[i-1, 'bb_upper']): return False
        if not (row['close'] > row['open'] and row['body_pct'] >= 0.5): return False
        if not row.get('ema50_above_ema200', False): return False
        if not row.get('close_above_ema200', False): return False
        return True

    print("\n=== F. BB Squeeze 4H ===")
    for trg in [3.0, 4.0]:
        name = f'F_BB_squeeze_4H_target{trg}R'
        t = run_long(df4, sig_bb_squeeze_4h, trg, 24, name, '4H')
        summaries.append({'strategy': name, **metrics(t)})
        trades_by[name] = t

    # =============================================================
    # G. Pullback EMA50 4H + 30M
    # =============================================================
    def sig_pullback_ema50(df, i, row):
        ema50 = row.get('ema50', np.nan)
        if pd.isna(ema50): return False
        if not (row['low'] <= ema50 and row['close'] > ema50): return False
        if not (row['close'] > row['open'] and row['body_pct'] >= 0.4): return False
        if not row.get('close_above_ema200', False): return False
        if not row.get('ema50_above_ema200', False): return False
        rsi = row.get('RSI', np.nan); rsi_ma = row.get('RSI-based MA', np.nan)
        if pd.isna(rsi) or pd.isna(rsi_ma) or rsi <= rsi_ma: return False
        return True

    print("\n=== G. Pullback EMA50 ===")
    for tf_label, df_use, trg, mb in [('4H', df4, 3.0, 20), ('30M', df30, 2.5, 16)]:
        name = f'G_pullback_EMA50_{tf_label}_target{trg}R'
        t = run_long(df_use, sig_pullback_ema50, trg, mb, name, tf_label)
        summaries.append({'strategy': name, **metrics(t)})
        trades_by[name] = t

    # =============================================================
    # H. Hammer/Bullish engulfing in trend
    # =============================================================
    def sig_hammer_4h(df, i, row):
        if not row.get('hammer', False): return False
        if not row.get('close_above_ema200', False): return False
        if not row.get('ema50_above_ema200', False): return False
        ema20 = row.get('ema20', np.nan)
        if pd.isna(ema20): return False
        if row['low'] > ema20 * 1.003: return False
        return True

    print("\n=== H. Hammer in trend ===")
    name = 'H_hammer_4H_target3R'
    t = run_long(df4, sig_hammer_4h, 3.0, 20, name, '4H')
    summaries.append({'strategy': name, **metrics(t)})
    trades_by[name] = t

    # =============================================================
    # MACRO: Apply DXY filter on best candidates
    # =============================================================
    print("\n=== MACRO: DXY filter on 4H breakout regime ===")
    def sig_4h_breakout_dxy_bearish(df, i, row):
        if not sig_4h_breakout_regime(df, i, row): return False
        if not row.get('dxy_bearish', False): return False
        return True

    def sig_4h_breakout_dxy_falling(df, i, row):
        if not sig_4h_breakout_regime(df, i, row): return False
        if not row.get('dxy_falling', False): return False
        return True

    def sig_4h_breakout_dxy_both(df, i, row):
        if not sig_4h_breakout_regime(df, i, row): return False
        if not row.get('dxy_bearish', False): return False
        if not row.get('dxy_falling', False): return False
        return True

    for trg in [3.0, 4.0, 5.0]:
        for sig_name, sig_func in [
            ('DXY_bearish', sig_4h_breakout_dxy_bearish),
            ('DXY_falling', sig_4h_breakout_dxy_falling),
            ('DXY_bear+falling', sig_4h_breakout_dxy_both),
        ]:
            name = f'MACRO_4H_breakout_{sig_name}_target{trg}R'
            t = run_long(df4, sig_func, trg, 24, name, '4H')
            summaries.append({'strategy': name, **metrics(t)})
            trades_by[name] = t

    # Also failed_breakdown + DXY bearish
    print("\n=== MACRO: DXY on failed breakdown ===")
    def sig_4h_fb_dxy_bearish(df, i, row):
        if not sig_4h_failed_breakdown(df, i, row): return False
        if not row.get('dxy_bearish', False): return False
        return True

    for trg in [2.5, 3.0]:
        name = f'MACRO_4H_FB_DXY_bearish_target{trg}R'
        t = run_long(df4, sig_4h_fb_dxy_bearish, trg, 20, name, '4H')
        summaries.append({'strategy': name, **metrics(t)})
        trades_by[name] = t

    # =============================================================
    # 30M intraday — same patterns
    # =============================================================
    print("\n=== 30M intraday variants ===")
    def sig_30m_breakout_regime(df, i, row):
        if not (row['close'] > row['open'] and row['body_pct'] >= 0.5
                and row['close'] > df.at[i-1, 'swhi_10']): return False
        rsi = row.get('RSI', np.nan); rsi_ma = row.get('RSI-based MA', np.nan)
        if pd.isna(rsi) or pd.isna(rsi_ma) or rsi <= rsi_ma: return False
        if not row.get('close_above_ema200', False): return False
        if not row.get('ema50_above_ema200', False): return False
        if not row.get('atr_expanding', False): return False
        if pd.isna(row.get('adx14', np.nan)) or row['adx14'] < 20: return False
        # HTF strict
        if not row.get('htf4h_bullish', False): return False
        if not row.get('htf1d_bullish', False): return False
        return True

    def sig_30m_breakout_dxy(df, i, row):
        if not sig_30m_breakout_regime(df, i, row): return False
        if not row.get('dxy_bearish', False): return False
        return True

    for trg in [2.5, 3.0, 4.0]:
        name = f'I_30M_breakout_regime_HTF_target{trg}R'
        t = run_long(df30, sig_30m_breakout_regime, trg, 16, name, '30M')
        summaries.append({'strategy': name, **metrics(t)})
        trades_by[name] = t

        name = f'I_30M_breakout_DXY_target{trg}R'
        t = run_long(df30, sig_30m_breakout_dxy, trg, 16, name, '30M')
        summaries.append({'strategy': name, **metrics(t)})
        trades_by[name] = t

    # EU session filter
    def sig_30m_eu_session_dxy(df, i, row):
        if not row.get('eu_session', False): return False
        if not sig_30m_breakout_dxy(df, i, row): return False
        return True

    name = 'I_30M_EU_session_DXY_target3R'
    t = run_long(df30, sig_30m_eu_session_dxy, 3.0, 16, name, '30M')
    summaries.append({'strategy': name, **metrics(t)})
    trades_by[name] = t

    # =============================================================
    # OUTPUT
    # =============================================================
    df_res = pd.DataFrame(summaries).sort_values('total_r_net', ascending=False)
    df_res.to_csv(OUT_DIR / 'EURUSD_strategy_search_summary.csv', index=False)

    cols = ['strategy','n','trades_per_week','trades_per_month','total_r_net','avg_r_net',
            'win_rate','pf_net','max_losing_streak','r_no_top5_net','r_no_top10_net']
    print("\n=== Top 15 ===")
    print(df_res[cols].head(15).to_string(index=False))

    print("\n=== Top 5 yearly ===")
    for name in df_res['strategy'].head(5):
        # Find key
        for k in trades_by:
            if k in name or name.endswith(k) or k.endswith(name):
                t = trades_by[k]
                if t:
                    print(f"\n--- {name} ---")
                    print(yearly_metrics(t).to_string(index=False))
                break


if __name__ == '__main__':
    main()
