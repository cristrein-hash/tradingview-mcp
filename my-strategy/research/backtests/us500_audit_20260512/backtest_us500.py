#!/usr/bin/env python3
"""US500 Deep Strategy Audit — 2026-05-12."""
import pandas as pd
import numpy as np
from pathlib import Path
import sys

OUT_DIR = Path(__file__).parent

FILES = {
    '1D':  '/Users/cristrein/Downloads/PEPPERSTONE_US500, 1D_69ece.csv',
    '12H': '/Users/cristrein/Downloads/PEPPERSTONE_US500, 720_e7b1f.csv',
    '4H':  '/Users/cristrein/Downloads/PEPPERSTONE_US500, 240_d6b2d.csv',
    '1H':  '/Users/cristrein/Downloads/PEPPERSTONE_US500, 60_ba86f.csv',
    '30M': '/Users/cristrein/Downloads/PEPPERSTONE_US500, 30_df88a.csv',
    '15M': '/Users/cristrein/Downloads/PEPPERSTONE_US500, 15_71607.csv',
}

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
        df['rsi_cross_up'] = df['rsi_above_ma'] & (~df['rsi_above_ma'].shift(1).fillna(False))
        df['rsi_cross_down'] = (~df['rsi_above_ma']) & (df['rsi_above_ma'].shift(1).fillna(True))
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
    return df


def simulate_trade(df, idx, direction, entry, stop, target_r, max_bars, be_at_1r=False, trail_at=None, trail_dist=0.75):
    R = abs(entry - stop)
    if R <= 0: return None
    sign = 1 if direction == 'LONG' else -1
    target = entry + sign * R * target_r
    cur_stop = stop; mfe = mae = 0.0
    hit_1r = False; moved_be = False; activated_trail = False
    for j in range(idx + 1, min(idx + 1 + max_bars, len(df))):
        h = df.at[j, 'high']; l = df.at[j, 'low']
        if direction == 'LONG':
            fav = (h - entry) / R; adv = (entry - l) / R
        else:
            fav = (entry - l) / R; adv = (h - entry) / R
        mfe = max(mfe, fav); mae = max(mae, adv)
        if be_at_1r and not moved_be and fav >= 1.0:
            cur_stop = entry; moved_be = True; hit_1r = True
        elif not hit_1r and fav >= 1.0:
            hit_1r = True
        if trail_at is not None and not activated_trail and fav >= trail_at:
            activated_trail = True
            if direction == 'LONG':
                cur_stop = max(cur_stop, entry + (fav - trail_dist) * R)
            else:
                cur_stop = min(cur_stop, entry - (fav - trail_dist) * R)
        elif activated_trail:
            if direction == 'LONG':
                cur_stop = max(cur_stop, entry + (fav - trail_dist) * R)
            else:
                cur_stop = min(cur_stop, entry - (fav - trail_dist) * R)
        if direction == 'LONG':
            if l <= cur_stop:
                exit_price = cur_stop; r_out = (exit_price - entry) / R
                return {'exit_idx': j, 'exit_price': exit_price, 'r_outcome': r_out,
                        'exit_reason': 'stop' if cur_stop <= entry else 'be_or_trail',
                        'mfe': mfe, 'mae': mae, 'bars_held': j - idx}
            if h >= target:
                exit_price = target; r_out = (exit_price - entry) / R
                return {'exit_idx': j, 'exit_price': exit_price, 'r_outcome': r_out,
                        'exit_reason': 'target', 'mfe': mfe, 'mae': mae, 'bars_held': j - idx}
        else:
            if h >= cur_stop:
                exit_price = cur_stop; r_out = (entry - exit_price) / R
                return {'exit_idx': j, 'exit_price': exit_price, 'r_outcome': r_out,
                        'exit_reason': 'stop' if cur_stop >= entry else 'be_or_trail',
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
        'total_r_gross': round(r_g.sum(), 2),
        'total_r_net': round(r_n.sum(), 2),
        'avg_r_gross': round(r_g.mean(), 4),
        'avg_r_net': round(r_n.mean(), 4),
        'win_rate': round((r_n > 0).mean(), 3),
        'pf_net': round(pf, 2) if pf != float('inf') else 'inf',
        'max_losing_streak': max_streak,
        'r_no_top1_net': round(sum(sorted_r[1:]), 2),
        'r_no_top3_net': round(sum(sorted_r[3:]), 2),
        'r_no_top5_net': round(sum(sorted_r[5:]), 2),
        'r_no_top10_net': round(sum(sorted_r[10:]), 2),
        'best_r_net': round(sorted_r[0], 2),
        'worst_r_net': round(sorted_r[-1], 2),
        'avg_mfe': round(df['mfe'].mean(), 2) if 'mfe' in df.columns else None,
        'avg_mae': round(df['mae'].mean(), 2) if 'mae' in df.columns else None,
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
# STRATEGIES
# ============================================================

def strat_rejection(df, direction='LONG', target_r=4.5, max_bars=30, be=True,
                    require_rsi_extreme=False, require_bubble=False, require_nas=False,
                    wick_min=0.5, body_max=0.4, rsi_oversold=30, rsi_overbought=70,
                    name='?', tf='?'):
    """Classic rejection close."""
    trades = []
    for i in range(50, len(df) - 1):
        row = df.iloc[i]
        if direction == 'LONG':
            structure = (row['lower_wick'] >= wick_min and row['body_pct'] <= body_max
                         and row.get('close_in_upper_third', False))
        else:
            structure = (row['upper_wick'] >= wick_min and row['body_pct'] <= body_max
                         and row.get('close_in_lower_third', False))
        if not structure: continue
        if require_rsi_extreme:
            rsi = row.get('RSI', np.nan)
            if pd.isna(rsi): continue
            if direction == 'LONG' and rsi > rsi_oversold + 5: continue
            if direction == 'SHORT' and rsi < rsi_overbought - 5: continue
        if require_bubble and not row.get('has_bubble', False): continue
        if require_nas:
            if direction == 'LONG' and row.get('NAS_BOTTOM_SIGNAL', 0) == 0 and row.get('NAS_LONG_SIGNAL', 0) == 0: continue
            if direction == 'SHORT' and row.get('NAS_TOP_SIGNAL', 0) == 0 and row.get('NAS_SHORT_SIGNAL', 0) == 0: continue
        entry = row['close']; atr = row['atr14']
        if pd.isna(atr) or atr <= 0: continue
        if direction == 'LONG':
            stop = row['low'] - atr * 0.5
        else:
            stop = row['high'] + atr * 0.5
        R = abs(entry - stop)
        if R <= 0 or R / atr > 5: continue
        res = simulate_trade(df, i, direction, entry, stop, target_r, max_bars, be_at_1r=be)
        if not res: continue
        res.update({'entry_time': row['time'], 'entry_price': entry,
                    'stop_price': stop, 'direction': direction, 'r_planned': target_r,
                    'strategy': name, 'tf': tf})
        trades.append(res)
    return trades


def strat_pullback_rejection_bull(df, target_r=4.5, max_bars=30, be=True,
                                   wick_min=0.5, body_max=0.4,
                                   require_close_above_ema200=True,
                                   require_ema50_above_ema200=True,
                                   name='?', tf='?'):
    """LONG pullback rejection within bullish regime — for US500 current module."""
    trades = []
    for i in range(200, len(df) - 1):
        row = df.iloc[i]
        # Rejection structure
        if not (row['lower_wick'] >= wick_min and row['body_pct'] <= body_max
                and row.get('close_in_upper_third', False)):
            continue
        # Bull regime
        if require_close_above_ema200 and not row.get('close_above_ema200', False): continue
        if require_ema50_above_ema200 and not row.get('ema50_above_ema200', False): continue
        entry = row['close']; atr = row['atr14']
        if pd.isna(atr) or atr <= 0: continue
        stop = row['low'] - atr * 0.5
        R = abs(entry - stop)
        if R <= 0 or R / atr > 5: continue
        res = simulate_trade(df, i, 'LONG', entry, stop, target_r, max_bars, be_at_1r=be)
        if not res: continue
        res.update({'entry_time': row['time'], 'entry_price': entry,
                    'stop_price': stop, 'direction': 'LONG', 'r_planned': target_r,
                    'strategy': name, 'tf': tf})
        trades.append(res)
    return trades


def strat_breakout(df, target_r=4.0, max_bars=24, be=True,
                   require_rsi_above_ma=True,
                   require_close_above_ema200=False,
                   require_ema50_above_ema200=False,
                   require_atr_expanding=False,
                   require_adx_min=None,
                   require_ema50_slope_pos=False,
                   body_min=0.5,
                   name='?', tf='?'):
    """LONG breakout continuation."""
    trades = []
    for i in range(200, len(df) - 1):
        row = df.iloc[i]
        if not (row['close'] > row['open'] and row['body_pct'] >= body_min
                and row['close'] > df.at[i-1, 'swhi_10']):
            continue
        if require_rsi_above_ma:
            rsi = row.get('RSI', np.nan); rsi_ma = row.get('RSI-based MA', np.nan)
            if pd.isna(rsi) or pd.isna(rsi_ma) or rsi <= rsi_ma: continue
        if require_close_above_ema200 and not row.get('close_above_ema200', False): continue
        if require_ema50_above_ema200 and not row.get('ema50_above_ema200', False): continue
        if require_atr_expanding and not row.get('atr_expanding', False): continue
        if require_adx_min is not None and (pd.isna(row.get('adx14', np.nan)) or row['adx14'] < require_adx_min): continue
        if require_ema50_slope_pos and (pd.isna(row.get('ema50_slope', np.nan)) or row['ema50_slope'] <= 0): continue
        entry = row['close']; atr = row['atr14']
        if pd.isna(atr) or atr <= 0: continue
        stop = row['low'] - atr * 0.5
        R = abs(entry - stop)
        if R <= 0 or R / atr > 5: continue
        res = simulate_trade(df, i, 'LONG', entry, stop, target_r, max_bars, be_at_1r=be)
        if not res: continue
        res.update({'entry_time': row['time'], 'entry_price': entry,
                    'stop_price': stop, 'direction': 'LONG', 'r_planned': target_r,
                    'strategy': name, 'tf': tf})
        trades.append(res)
    return trades


def strat_pullback_ema50(df, target_r=4.0, max_bars=20, be=True,
                          require_htf_bullish=False, htf_col=None,
                          name='?', tf='?'):
    """LONG pullback to EMA50 + close above EMA50 + bull regime."""
    trades = []
    for i in range(200, len(df) - 1):
        row = df.iloc[i]
        ema50 = row.get('ema50', np.nan)
        if pd.isna(ema50): continue
        if not (row['low'] <= ema50 and row['close'] > ema50): continue
        if not (row['close'] > row['open'] and row['body_pct'] >= 0.4): continue
        if not row.get('ema50_above_ema200', False): continue
        if not row.get('close_above_ema200', False): continue
        rsi = row.get('RSI', np.nan); rsi_ma = row.get('RSI-based MA', np.nan)
        if pd.isna(rsi) or pd.isna(rsi_ma) or rsi <= rsi_ma: continue
        if require_htf_bullish and htf_col and not row.get(htf_col, False): continue
        entry = row['close']; atr = row['atr14']
        if pd.isna(atr) or atr <= 0: continue
        stop = row['low'] - atr * 0.5
        R = abs(entry - stop)
        if R <= 0 or R / atr > 5: continue
        res = simulate_trade(df, i, 'LONG', entry, stop, target_r, max_bars, be_at_1r=be)
        if not res: continue
        res.update({'entry_time': row['time'], 'entry_price': entry,
                    'stop_price': stop, 'direction': 'LONG', 'r_planned': target_r,
                    'strategy': name, 'tf': tf})
        trades.append(res)
    return trades


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


def main():
    print("=== Loading US500 ===")
    data = {tf: load(p) for tf, p in FILES.items()}
    df4, df1, df30, df15 = data['4H'], data['1H'], data['30M'], data['15M']
    df12 = data['12H']; df1d = data['1D']
    df4 = htf_context(df4, df12, 'htf12h')
    df4 = htf_context(df4, df1d, 'htf1d')
    df1 = htf_context(df1, df4, 'htf4h')
    df1 = htf_context(df1, df1d, 'htf1d')

    for tf, df in data.items():
        print(f"  {tf}: {len(df)} bars  {df['time'].min().date()} → {df['time'].max().date()}")

    summaries = []
    trades_by = {}

    # =============================================================
    # A. CURRENT: US500_4H_LONG_PULLBACK_REJECTION
    # =============================================================
    print("\n=== A. US500_4H_LONG_PULLBACK_REJECTION (atual) ===")
    t = strat_pullback_rejection_bull(df4, target_r=4.5, max_bars=30, be=True,
        require_close_above_ema200=True, require_ema50_above_ema200=True,
        name='A_4H_pullback_rejection_current', tf='4H')
    summaries.append({'strategy': 'A_US500_4H_LONG_PULLBACK_REJECTION (atual)', **metrics(t)})
    trades_by['A_4H_pullback_rejection_current'] = t

    # =============================================================
    # B. CURRENT: US500_INTRADAY_LONG_PULLBACK_EXECUTION (proxy 30M)
    # =============================================================
    print("\n=== B. US500_INTRADAY_LONG_PULLBACK_EXECUTION (atual, proxy 30M rejection) ===")
    t = strat_pullback_rejection_bull(df30, target_r=4.0, max_bars=24, be=True,
        require_close_above_ema200=True, require_ema50_above_ema200=True,
        name='B_30M_pullback_rejection_current', tf='30M')
    summaries.append({'strategy': 'B_US500_INTRADAY_LONG_PULLBACK_EXECUTION (atual 30M)', **metrics(t)})
    trades_by['B_30M_pullback_rejection_current'] = t

    # =============================================================
    # C. Old global rule
    # =============================================================
    print("\n=== C. Régua antiga global ===")
    t = strat_rejection(df4, 'LONG', target_r=2.0, max_bars=30, be=True,
        require_rsi_extreme=True, require_bubble=True,
        name='C_old_strict_LONG_4H', tf='4H')
    summaries.append({'strategy': 'C_old_global_strict_LONG_4H (RSI+Bubble)', **metrics(t)})
    t = strat_rejection(df4, 'SHORT', target_r=2.0, max_bars=30, be=True,
        require_rsi_extreme=True, require_bubble=True,
        name='C_old_strict_SHORT_4H', tf='4H')
    summaries.append({'strategy': 'C_old_global_strict_SHORT_4H', **metrics(t)})
    t = strat_rejection(df4, 'LONG', target_r=2.0, max_bars=30, be=True,
        require_rsi_extreme=True, require_bubble=False,
        name='C_old_softened_LONG_4H', tf='4H')
    summaries.append({'strategy': 'C_old_softened_LONG_4H (only RSI ext)', **metrics(t)})

    # =============================================================
    # D. Regime-filtered breakout (XAU/ETH pattern)
    # =============================================================
    print("\n=== D. NEW 4H regime-filtered breakout ===")
    for trg, mb in [(3.0, 24), (4.0, 24), (4.5, 30), (5.0, 30)]:
        t = strat_breakout(df4, target_r=trg, max_bars=mb, be=True,
            require_rsi_above_ma=True,
            require_close_above_ema200=True, require_ema50_above_ema200=True,
            require_atr_expanding=True, require_ema50_slope_pos=True,
            require_adx_min=20, body_min=0.5,
            name=f'D_4H_breakout_regime_{trg}R', tf='4H')
        summaries.append({'strategy': f'D_4H_BREAKOUT_REGIME_FILTERED_target{trg}R', **metrics(t)})
        trades_by[f'D_4H_breakout_regime_{trg}R'] = t

    # D with body >= 60%
    t = strat_breakout(df4, target_r=4.5, max_bars=30, be=True,
        require_rsi_above_ma=True,
        require_close_above_ema200=True, require_ema50_above_ema200=True,
        require_atr_expanding=True, require_ema50_slope_pos=True,
        require_adx_min=20, body_min=0.6,
        name='D_4H_breakout_regime_body60_4.5R', tf='4H')
    summaries.append({'strategy': 'D_4H_BREAKOUT_REGIME_body60_target4.5R', **metrics(t)})
    trades_by['D_4H_breakout_regime_body60_4.5R'] = t

    # D with ADX 25
    t = strat_breakout(df4, target_r=4.5, max_bars=30, be=True,
        require_rsi_above_ma=True,
        require_close_above_ema200=True, require_ema50_above_ema200=True,
        require_atr_expanding=True, require_ema50_slope_pos=True,
        require_adx_min=25, body_min=0.5,
        name='D_4H_breakout_regime_adx25_4.5R', tf='4H')
    summaries.append({'strategy': 'D_4H_BREAKOUT_REGIME_adx25_target4.5R', **metrics(t)})

    # =============================================================
    # E. Pullback to EMA50 (like ETH 1H)
    # =============================================================
    print("\n=== E. Pullback to EMA50 in bull regime ===")
    # 4H
    t = strat_pullback_ema50(df4, target_r=3.0, max_bars=20, be=True, name='E_4H_pullback_EMA50_3R', tf='4H')
    summaries.append({'strategy': 'E_4H_pullback_EMA50_target3R', **metrics(t)})
    trades_by['E_4H_pullback_EMA50_3R'] = t
    t = strat_pullback_ema50(df4, target_r=4.0, max_bars=24, be=True, name='E_4H_pullback_EMA50_4R', tf='4H')
    summaries.append({'strategy': 'E_4H_pullback_EMA50_target4R', **metrics(t)})
    trades_by['E_4H_pullback_EMA50_4R'] = t

    # 1H
    t = strat_pullback_ema50(df1, target_r=3.0, max_bars=20, be=True, name='E_1H_pullback_EMA50_3R', tf='1H')
    summaries.append({'strategy': 'E_1H_pullback_EMA50_target3R', **metrics(t)})
    trades_by['E_1H_pullback_EMA50_3R'] = t
    t = strat_pullback_ema50(df1, target_r=4.0, max_bars=24, be=True, name='E_1H_pullback_EMA50_4R', tf='1H')
    summaries.append({'strategy': 'E_1H_pullback_EMA50_target4R', **metrics(t)})
    trades_by['E_1H_pullback_EMA50_4R'] = t

    # 1H with HTF 1D bullish filter
    t = strat_pullback_ema50(df1, target_r=3.0, max_bars=20, be=True,
        require_htf_bullish=True, htf_col='htf1d_bullish',
        name='E_1H_pullback_EMA50_HTF1D_3R', tf='1H')
    summaries.append({'strategy': 'E_1H_pullback_EMA50_HTF1D_target3R', **metrics(t)})
    trades_by['E_1H_pullback_EMA50_HTF1D_3R'] = t

    t = strat_pullback_ema50(df1, target_r=4.0, max_bars=24, be=True,
        require_htf_bullish=True, htf_col='htf1d_bullish',
        name='E_1H_pullback_EMA50_HTF1D_4R', tf='1H')
    summaries.append({'strategy': 'E_1H_pullback_EMA50_HTF1D_target4R', **metrics(t)})
    trades_by['E_1H_pullback_EMA50_HTF1D_4R'] = t

    # =============================================================
    # F. 1H breakout regime-filtered
    # =============================================================
    print("\n=== F. 1H breakout regime-filtered ===")
    t = strat_breakout(df1, target_r=4.0, max_bars=24, be=True,
        require_rsi_above_ma=True,
        require_close_above_ema200=True, require_ema50_above_ema200=True,
        require_atr_expanding=True, require_ema50_slope_pos=True,
        require_adx_min=20, body_min=0.5,
        name='F_1H_breakout_regime', tf='1H')
    summaries.append({'strategy': 'F_1H_BREAKOUT_REGIME_FILTERED', **metrics(t)})
    trades_by['F_1H_breakout_regime'] = t

    # =============================================================
    # G. 30M LONG breakout regime-filtered
    # =============================================================
    print("\n=== G. 30M breakout regime-filtered ===")
    t = strat_breakout(df30, target_r=3.0, max_bars=20, be=True,
        require_rsi_above_ma=True,
        require_close_above_ema200=True, require_ema50_above_ema200=True,
        require_atr_expanding=True, require_ema50_slope_pos=True,
        require_adx_min=20, body_min=0.5,
        name='G_30M_breakout_regime', tf='30M')
    summaries.append({'strategy': 'G_30M_BREAKOUT_REGIME_FILTERED', **metrics(t)})
    trades_by['G_30M_breakout_regime'] = t

    # =============================================================
    # FILTER IMPACT — 4H breakout baseline
    # =============================================================
    print("\n=== Filter impact (4H LONG breakout baseline) ===")
    filter_impact = []
    base = dict(target_r=4.5, max_bars=30, be=True, require_rsi_above_ma=True, tf='4H', body_min=0.5)
    configs = [
        ('baseline_RSI_MA', {}),
        ('with_close_above_ema200', {'require_close_above_ema200': True}),
        ('with_ema50_above_ema200', {'require_ema50_above_ema200': True}),
        ('with_atr_expanding', {'require_atr_expanding': True}),
        ('with_adx20', {'require_adx_min': 20}),
        ('with_adx25', {'require_adx_min': 25}),
        ('with_ema50_slope_pos', {'require_ema50_slope_pos': True}),
        ('full_regime_filter', {'require_close_above_ema200': True, 'require_ema50_above_ema200': True,
                                 'require_atr_expanding': True, 'require_ema50_slope_pos': True,
                                 'require_adx_min': 20}),
        ('full_regime_body60', {'require_close_above_ema200': True, 'require_ema50_above_ema200': True,
                                 'require_atr_expanding': True, 'require_ema50_slope_pos': True,
                                 'require_adx_min': 20, 'body_min': 0.6}),
    ]
    for fname, fkw in configs:
        kw = dict(base); kw.update(fkw); kw['name'] = f'FILT_{fname}'
        t = strat_breakout(df4, **kw)
        m = metrics(t)
        filter_impact.append({'filter': fname, 'n': m.get('n', 0),
                              'total_net_r': m.get('total_r_net', 0),
                              'avg_net_r': m.get('avg_r_net', 0),
                              'pf_net': m.get('pf_net', 0),
                              'win_rate': m.get('win_rate', 0),
                              'max_losing_streak': m.get('max_losing_streak', 0),
                              'r_no_top5_net': m.get('r_no_top5_net', 0),
                              'r_no_top10_net': m.get('r_no_top10_net', 0)})
    pd.DataFrame(filter_impact).to_csv(OUT_DIR / 'US500_filter_impact_analysis.csv', index=False)

    # =============================================================
    # COST SENSITIVITY — top candidate
    # =============================================================
    print("\n=== Cost sensitivity ===")
    # Will calculate later for the best identified
    # ==

    pd.DataFrame(summaries).to_csv(OUT_DIR / 'US500_strategy_search_summary.csv', index=False)

    # Save trades
    if 'A_4H_pullback_rejection_current' in trades_by and trades_by['A_4H_pullback_rejection_current']:
        pd.DataFrame(trades_by['A_4H_pullback_rejection_current']).to_csv(OUT_DIR / 'US500_current_4H_trades.csv', index=False)

    # Best by score
    def score(trades):
        if len(trades) < 10: return -999
        r = [t['r_outcome'] - SPREAD_R for t in trades]
        return np.mean(r) * np.sqrt(len(r))

    swing_keys = [k for k in trades_by if any(t in k for t in ['4H', '12H'])]
    intra_keys = [k for k in trades_by if any(t in k for t in ['1H', '30M', '15M'])]
    if swing_keys:
        best_sw = max(swing_keys, key=lambda k: score(trades_by[k]))
        pd.DataFrame(trades_by[best_sw]).to_csv(OUT_DIR / 'US500_best_swing_trades.csv', index=False)
        print(f"Best swing: {best_sw} (n={len(trades_by[best_sw])})")
    if intra_keys:
        best_in = max(intra_keys, key=lambda k: score(trades_by[k]))
        pd.DataFrame(trades_by[best_in]).to_csv(OUT_DIR / 'US500_best_intraday_trades.csv', index=False)
        print(f"Best intraday: {best_in} (n={len(trades_by[best_in])})")

    # Cost sensitivity for best swing + best intraday
    cost_rows = []
    for key_label, key in [('best_swing', best_sw), ('best_intraday', best_in)]:
        if key not in trades_by or not trades_by[key]: continue
        r_g = pd.DataFrame(trades_by[key])['r_outcome']
        for c in [0.00, 0.02, 0.03, 0.05, 0.07, 0.10]:
            r_n = r_g - c
            wins = r_n[r_n > 0]; losses = r_n[r_n < 0]
            pf = abs(wins.sum() / losses.sum()) if len(losses) and losses.sum() != 0 else float('inf')
            cost_rows.append({'model': key_label, 'strategy': key, 'spread': c,
                              'total_r_net': round(r_n.sum(), 2),
                              'avg_r_net': round(r_n.mean(), 4),
                              'pf_net': round(pf, 2) if pf != float('inf') else 'inf',
                              'win_rate': round((r_n > 0).mean(), 3),
                              'positive': r_n.sum() > 0})
    pd.DataFrame(cost_rows).to_csv(OUT_DIR / 'US500_cost_sensitivity.csv', index=False)

    # Year-by-year for top candidates
    print("\n=== Yearly for best swing ===")
    if best_sw and trades_by[best_sw]:
        print(yearly_metrics(trades_by[best_sw]).to_string(index=False))
    print("\n=== Yearly for A (current) ===")
    if trades_by.get('A_4H_pullback_rejection_current'):
        print(yearly_metrics(trades_by['A_4H_pullback_rejection_current']).to_string(index=False))
    print("\n=== Yearly for best intraday ===")
    if best_in and trades_by[best_in]:
        print(yearly_metrics(trades_by[best_in]).to_string(index=False))


if __name__ == '__main__':
    main()
