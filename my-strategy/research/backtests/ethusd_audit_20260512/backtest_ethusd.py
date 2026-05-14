#!/usr/bin/env python3
"""
ETHUSD Deep Strategy Audit — read-only backtest framework.
Date: 2026-05-12
"""
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import json

OUT_DIR = Path(__file__).parent

FILES = {
    '1D':  '/Users/cristrein/Downloads/PEPPERSTONE_ETHUSD, 1D_a88d1.csv',
    '12H': '/Users/cristrein/Downloads/PEPPERSTONE_ETHUSD, 720_582bc.csv',
    '4H':  '/Users/cristrein/Downloads/PEPPERSTONE_ETHUSD, 240_8f55c.csv',
    '1H':  '/Users/cristrein/Downloads/PEPPERSTONE_ETHUSD, 60_392b3.csv',
    '30M': '/Users/cristrein/Downloads/PEPPERSTONE_ETHUSD, 30_c9f6b.csv',
    '15M': '/Users/cristrein/Downloads/PEPPERSTONE_ETHUSD, 15_ec388.csv',
}

SPREAD_R = 0.05


def load(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    df.columns = [c.strip() for c in df.columns]
    cols = list(df.columns)
    seen, new = {}, []
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
    up = h - h.shift(1)
    dn = l.shift(1) - l
    plus_dm = np.where((up > dn) & (up > 0), up, 0.0)
    minus_dm = np.where((dn > up) & (dn > 0), dn, 0.0)
    plus_dm_s = pd.Series(plus_dm, index=df.index).ewm(alpha=1/14, adjust=False).mean()
    minus_dm_s = pd.Series(minus_dm, index=df.index).ewm(alpha=1/14, adjust=False).mean()
    di_plus = 100 * plus_dm_s / df['atr14'].replace(0, np.nan)
    di_minus = 100 * minus_dm_s / df['atr14'].replace(0, np.nan)
    dx = 100 * (di_plus - di_minus).abs() / (di_plus + di_minus).replace(0, np.nan)
    df['adx14'] = dx.ewm(alpha=1/14, adjust=False).mean()
    df['di_plus'] = di_plus
    df['di_minus'] = di_minus
    # EMAs
    df['ema50'] = c.ewm(span=50, adjust=False).mean()
    df['ema200'] = c.ewm(span=200, adjust=False).mean()
    df['ema50_slope'] = df['ema50'].diff(5)
    df['ema200_slope'] = df['ema200'].diff(10)
    df['close_above_ema50'] = c > df['ema50']
    df['close_above_ema200'] = c > df['ema200']
    df['ema50_above_ema200'] = df['ema50'] > df['ema200']
    df['ema50_below_ema200'] = df['ema50'] < df['ema200']
    df['close_below_ema200'] = c < df['ema200']
    # ATR expansion
    df['atr_ma20'] = df['atr14'].rolling(20).mean()
    df['atr_expanding'] = df['atr14'] > df['atr_ma20']
    return df


def simulate_trade(df, entry_idx, direction, entry, stop, target_r, max_bars,
                   be_at_1r=False, trail_at=None, trail_dist=0.75):
    R = abs(entry - stop)
    if R <= 0:
        return None
    sign = 1 if direction == 'LONG' else -1
    target = entry + sign * R * target_r
    cur_stop = stop
    mfe = mae = 0.0
    hit_1r = False; moved_be = False; activated_trail = False
    for j in range(entry_idx + 1, min(entry_idx + 1 + max_bars, len(df))):
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
                        'mfe': mfe, 'mae': mae, 'bars_held': j - entry_idx}
            if h >= target:
                exit_price = target; r_out = (exit_price - entry) / R
                return {'exit_idx': j, 'exit_price': exit_price, 'r_outcome': r_out,
                        'exit_reason': 'target', 'mfe': mfe, 'mae': mae, 'bars_held': j - entry_idx}
        else:
            if h >= cur_stop:
                exit_price = cur_stop; r_out = (entry - exit_price) / R
                return {'exit_idx': j, 'exit_price': exit_price, 'r_outcome': r_out,
                        'exit_reason': 'stop' if cur_stop >= entry else 'be_or_trail',
                        'mfe': mfe, 'mae': mae, 'bars_held': j - entry_idx}
            if l <= target:
                exit_price = target; r_out = (entry - exit_price) / R
                return {'exit_idx': j, 'exit_price': exit_price, 'r_outcome': r_out,
                        'exit_reason': 'target', 'mfe': mfe, 'mae': mae, 'bars_held': j - entry_idx}
    exit_idx = min(entry_idx + max_bars, len(df) - 1)
    last = df.at[exit_idx, 'close']
    r_out = (last - entry) / R if direction == 'LONG' else (entry - last) / R
    return {'exit_idx': exit_idx, 'exit_price': last, 'r_outcome': r_out,
            'exit_reason': 'time_exit', 'mfe': mfe, 'mae': mae, 'bars_held': max_bars}


def metrics(trades, spread=SPREAD_R):
    if not trades:
        return {'n': 0}
    df = pd.DataFrame(trades)
    r_gross = df['r_outcome']
    r_net = r_gross - spread
    span_days = (pd.to_datetime(df['entry_time'].max()) - pd.to_datetime(df['entry_time'].min())).days
    sw = max(1, span_days / 7); sm = max(1, span_days / 30.44)
    wins = r_net[r_net > 0]; losses = r_net[r_net < 0]
    pf = abs(wins.sum() / losses.sum()) if len(losses) and losses.sum() != 0 else float('inf')
    streak = max_streak = 0
    for v in r_net:
        if v <= 0: streak += 1; max_streak = max(max_streak, streak)
        else: streak = 0
    sorted_r = sorted(r_net.tolist(), reverse=True)
    return {
        'n': len(df),
        'trades_per_week': round(len(df) / sw, 2),
        'trades_per_month': round(len(df) / sm, 2),
        'total_r_gross': round(r_gross.sum(), 2),
        'total_r_net': round(r_net.sum(), 2),
        'avg_r_gross': round(r_gross.mean(), 4),
        'avg_r_net': round(r_net.mean(), 4),
        'median_r': round(r_net.median(), 3),
        'win_rate': round((r_net > 0).mean(), 3),
        'pf_net': round(pf, 2) if pf != float('inf') else 'inf',
        'max_losing_streak': max_streak,
        'best_r_net': round(sorted_r[0], 2),
        'worst_r_net': round(sorted_r[-1], 2),
        'r_no_top1_net': round(sum(sorted_r[1:]), 2),
        'r_no_top3_net': round(sum(sorted_r[3:]), 2),
        'r_no_top5_net': round(sum(sorted_r[5:]), 2),
        'r_no_top10_net': round(sum(sorted_r[10:]), 2),
        'avg_mfe': round(df['mfe'].mean(), 2) if 'mfe' in df.columns else None,
        'avg_mae': round(df['mae'].mean(), 2) if 'mae' in df.columns else None,
        'avg_bars_held': round(df['bars_held'].mean(), 1) if 'bars_held' in df.columns else None,
    }


def yearly_metrics(trades, spread=SPREAD_R):
    if not trades:
        return pd.DataFrame()
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

def strat_breakout_continuation(df, target_r=5.0, max_bars=24, be=True,
                                 trail_at=None, name='?', tf='?',
                                 require_rsi_above_ma=True, rsi_min=None,
                                 require_close_above_ema200=False,
                                 require_ema50_above_ema200=False,
                                 require_atr_expanding=False,
                                 require_adx_min=None,
                                 require_ema50_slope_pos=False):
    """LONG breakout continuation."""
    trades = []
    for i in range(200, len(df) - 1):
        row = df.iloc[i]
        if not (row['close'] > row['open'] and row['body_pct'] >= 0.5
                and row['close'] > df.at[i-1, 'swhi_10']):
            continue
        if require_rsi_above_ma:
            rsi = row.get('RSI', np.nan); rsi_ma = row.get('RSI-based MA', np.nan)
            if pd.isna(rsi) or pd.isna(rsi_ma) or rsi <= rsi_ma: continue
        if rsi_min is not None:
            rsi = row.get('RSI', np.nan)
            if pd.isna(rsi) or rsi < rsi_min: continue
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
        res = simulate_trade(df, i, 'LONG', entry, stop, target_r, max_bars,
                              be_at_1r=be, trail_at=trail_at)
        if not res: continue
        res.update({'entry_time': row['time'], 'entry_price': entry,
                    'stop_price': stop, 'direction': 'LONG', 'r_planned': target_r,
                    'strategy': name, 'tf': tf})
        trades.append(res)
    return trades


def strat_momentum_30m(df, direction='LONG', target_r=4.0, max_bars=16, be=True,
                       require_rsi_aligned=True, require_confirmation=True,
                       name='?', tf='30M'):
    """30M momentum continuation, both directions."""
    trades = []
    for i in range(50, len(df) - 1):
        row = df.iloc[i]
        # Momentum bar
        if direction == 'LONG':
            base = (row['close'] > row['open'] and row['body_pct'] >= 0.5
                    and row['close'] > df.at[i-1, 'swhi_10'])
        else:
            base = (row['close'] < row['open'] and row['body_pct'] >= 0.5
                    and row['close'] < df.at[i-1, 'swlo_10'])
        if not base: continue
        # RSI aligned
        if require_rsi_aligned:
            rsi = row.get('RSI', np.nan); rsi_ma = row.get('RSI-based MA', np.nan)
            if pd.isna(rsi) or pd.isna(rsi_ma): continue
            if direction == 'LONG' and rsi <= rsi_ma: continue
            if direction == 'SHORT' and rsi >= rsi_ma: continue
        # At least 1 confirmation: NAS / bubble / divergence / rsi_cross
        if require_confirmation:
            confs = 0
            if direction == 'LONG':
                if row.get('NAS_BOTTOM_SIGNAL', 0) or row.get('NAS_LONG_SIGNAL', 0): confs += 1
                if row.get('has_bubble', False): confs += 1
                if (row.get('Regular Bullish', 0) or 0) != 0: confs += 1
                if row.get('rsi_cross_up', False): confs += 1
            else:
                if row.get('NAS_TOP_SIGNAL', 0) or row.get('NAS_SHORT_SIGNAL', 0): confs += 1
                if row.get('has_bubble', False): confs += 1
                if (row.get('Regular Bearish', 0) or 0) != 0: confs += 1
                if row.get('rsi_cross_down', False): confs += 1
            if confs < 1: continue
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


def strat_rejection(df, direction='LONG', target_r=2.0, max_bars=24, be=True,
                    require_rsi_extreme=False, require_bubble=False,
                    require_nas=False, wick_min=0.5, body_max=0.4,
                    rsi_oversold=30, rsi_overbought=70,
                    name='?', tf='?'):
    """Classic rejection close (used to test old global rule)."""
    trades = []
    for i in range(20, len(df) - 1):
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


def main():
    print("=== Loading ETHUSD data ===")
    data = {tf: load(p) for tf, p in FILES.items()}
    for tf, df in data.items():
        print(f"  {tf}: {len(df)} bars  {df['time'].min().date()} → {df['time'].max().date()}")
    df4, df1, df30, df15 = data['4H'], data['1H'], data['30M'], data['15M']
    df12 = data['12H']; df1d = data['1D']

    summaries = []
    trades_by = {}

    # =============================================================
    # A. CURRENT: ETHUSD_4H_LONG_BREAKOUT_CONTINUATION
    # Regras esperadas: 4H, LONG, breakout, contexto 12H/1D bull,
    # RSI >= 52, BE+1R, target 5R, runner 8R Priority A
    # =============================================================
    print("\n=== A. ETHUSD_4H_LONG_BREAKOUT_CONTINUATION (atual) ===")
    t = strat_breakout_continuation(df4, target_r=5.0, max_bars=30, be=True,
        require_rsi_above_ma=True, rsi_min=52, name='A_4H_breakout_current', tf='4H')
    summaries.append({'strategy': 'A_ETHUSD_4H_LONG_BREAKOUT_CONTINUATION (atual)', **metrics(t)})
    trades_by['A_4H_breakout_current'] = t

    # Runner 8R version
    t = strat_breakout_continuation(df4, target_r=8.0, max_bars=40, be=True,
        require_rsi_above_ma=True, rsi_min=52, name='A_4H_breakout_runner8R', tf='4H')
    summaries.append({'strategy': 'A_ETHUSD_4H_LONG_BREAKOUT_runner_8R', **metrics(t)})
    trades_by['A_4H_breakout_runner8R'] = t

    # Without RSI >= 52
    t = strat_breakout_continuation(df4, target_r=5.0, max_bars=30, be=True,
        require_rsi_above_ma=True, rsi_min=None, name='A_4H_breakout_no_rsi52', tf='4H')
    summaries.append({'strategy': 'A_4H_breakout_no_RSI52_filter', **metrics(t)})
    trades_by['A_4H_breakout_no_rsi52'] = t

    # =============================================================
    # B. CURRENT: ETHUSD_30M_CONFIRMED_MOMENTUM_EXECUTION
    # Regras: 30M, LONG+SHORT, momentum confirmed, 1+ confirmation,
    # BE+1R, target 4R
    # =============================================================
    print("\n=== B. ETHUSD_30M_CONFIRMED_MOMENTUM_EXECUTION (atual) ===")
    t_long = strat_momentum_30m(df30, 'LONG', target_r=4.0, max_bars=16, be=True,
        require_rsi_aligned=True, require_confirmation=True,
        name='B_30M_momentum_LONG_current', tf='30M')
    t_short = strat_momentum_30m(df30, 'SHORT', target_r=4.0, max_bars=16, be=True,
        require_rsi_aligned=True, require_confirmation=True,
        name='B_30M_momentum_SHORT_current', tf='30M')
    summaries.append({'strategy': 'B_ETHUSD_30M_CONFIRMED_MOMENTUM_LONG (atual)', **metrics(t_long)})
    summaries.append({'strategy': 'B_ETHUSD_30M_CONFIRMED_MOMENTUM_SHORT (atual)', **metrics(t_short)})
    summaries.append({'strategy': 'B_ETHUSD_30M_CONFIRMED_MOMENTUM_BOTH (atual)', **metrics(t_long + t_short)})
    trades_by['B_30M_momentum_LONG_current'] = t_long
    trades_by['B_30M_momentum_SHORT_current'] = t_short

    # B without confirmation requirement
    t = strat_momentum_30m(df30, 'LONG', target_r=4.0, max_bars=16, be=True,
        require_rsi_aligned=True, require_confirmation=False,
        name='B_30M_momentum_LONG_no_conf', tf='30M')
    summaries.append({'strategy': 'B_30M_momentum_LONG_NO_confirmation', **metrics(t)})

    # =============================================================
    # C. Old global rule — rejection-based
    # =============================================================
    print("\n=== C. Régua antiga global ===")
    t = strat_rejection(df4, 'LONG', target_r=2.0, max_bars=30, be=True,
        require_rsi_extreme=True, require_bubble=True,
        name='C_old_strict_LONG_4H', tf='4H')
    summaries.append({'strategy': 'C_old_global_strict_LONG_4H (RSI ext + bubble)', **metrics(t)})
    t = strat_rejection(df4, 'SHORT', target_r=2.0, max_bars=30, be=True,
        require_rsi_extreme=True, require_bubble=True,
        name='C_old_strict_SHORT_4H', tf='4H')
    summaries.append({'strategy': 'C_old_global_strict_SHORT_4H', **metrics(t)})
    # Softened: only RSI extreme
    t = strat_rejection(df4, 'LONG', target_r=2.0, max_bars=30, be=True,
        require_rsi_extreme=True, require_bubble=False,
        name='C_old_softened_LONG_4H', tf='4H')
    summaries.append({'strategy': 'C_old_softened_LONG_4H (only RSI ext)', **metrics(t)})

    # =============================================================
    # D. NEW: Regime-filtered 4H breakout (à la XAUUSD success)
    # =============================================================
    print("\n=== D. NEW 4H regime-filtered breakout ===")
    t = strat_breakout_continuation(df4, target_r=5.0, max_bars=30, be=True,
        require_rsi_above_ma=True,
        require_close_above_ema200=True,
        require_ema50_above_ema200=True,
        require_atr_expanding=True,
        require_ema50_slope_pos=True,
        require_adx_min=20,
        name='D_4H_breakout_regime_5R', tf='4H')
    summaries.append({'strategy': 'D_4H_BREAKOUT_REGIME_FILTERED_target5R', **metrics(t)})
    trades_by['D_4H_breakout_regime_5R'] = t

    # Try target 4R
    t = strat_breakout_continuation(df4, target_r=4.0, max_bars=24, be=True,
        require_rsi_above_ma=True,
        require_close_above_ema200=True,
        require_ema50_above_ema200=True,
        require_atr_expanding=True,
        require_ema50_slope_pos=True,
        require_adx_min=20,
        name='D_4H_breakout_regime_4R', tf='4H')
    summaries.append({'strategy': 'D_4H_BREAKOUT_REGIME_FILTERED_target4R', **metrics(t)})

    # Try target 3R
    t = strat_breakout_continuation(df4, target_r=3.0, max_bars=24, be=True,
        require_rsi_above_ma=True,
        require_close_above_ema200=True,
        require_ema50_above_ema200=True,
        require_atr_expanding=True,
        require_ema50_slope_pos=True,
        require_adx_min=20,
        name='D_4H_breakout_regime_3R', tf='4H')
    summaries.append({'strategy': 'D_4H_BREAKOUT_REGIME_FILTERED_target3R', **metrics(t)})

    # Try target 6R
    t = strat_breakout_continuation(df4, target_r=6.0, max_bars=36, be=True,
        require_rsi_above_ma=True,
        require_close_above_ema200=True,
        require_ema50_above_ema200=True,
        require_atr_expanding=True,
        require_ema50_slope_pos=True,
        require_adx_min=20,
        name='D_4H_breakout_regime_6R', tf='4H')
    summaries.append({'strategy': 'D_4H_BREAKOUT_REGIME_FILTERED_target6R', **metrics(t)})

    # =============================================================
    # E. 30M LONG without confirmation, with regime filter on 30M
    # =============================================================
    print("\n=== E. 30M LONG regime-filtered ===")
    t = strat_breakout_continuation(df30, target_r=3.0, max_bars=20, be=True,
        require_rsi_above_ma=True,
        require_close_above_ema200=True,
        require_ema50_above_ema200=True,
        require_atr_expanding=True,
        require_ema50_slope_pos=True,
        require_adx_min=20,
        name='E_30M_breakout_regime', tf='30M')
    summaries.append({'strategy': 'E_30M_BREAKOUT_REGIME_FILTERED_LONG', **metrics(t)})
    trades_by['E_30M_breakout_regime'] = t

    # =============================================================
    # F. 1H breakout regime-filtered
    # =============================================================
    print("\n=== F. 1H breakout regime-filtered ===")
    t = strat_breakout_continuation(df1, target_r=4.0, max_bars=24, be=True,
        require_rsi_above_ma=True,
        require_close_above_ema200=True,
        require_ema50_above_ema200=True,
        require_atr_expanding=True,
        require_ema50_slope_pos=True,
        require_adx_min=20,
        name='F_1H_breakout_regime', tf='1H')
    summaries.append({'strategy': 'F_1H_BREAKOUT_REGIME_FILTERED_LONG', **metrics(t)})
    trades_by['F_1H_breakout_regime'] = t

    # =============================================================
    # G. 30M SHORT regime-filtered (test if SHORT works in bear regime)
    # =============================================================
    print("\n=== G. 30M SHORT regime-filtered ===")
    df30_for_short = df30.copy()
    # For SHORT we'd want close_below_ema200, ema50_below_ema200, etc.
    # Build manually:
    trades_short = []
    for i in range(200, len(df30_for_short) - 1):
        row = df30_for_short.iloc[i]
        if not (row['close'] < row['open'] and row['body_pct'] >= 0.5
                and row['close'] < df30_for_short.at[i-1, 'swlo_10']):
            continue
        rsi = row.get('RSI', np.nan); rsi_ma = row.get('RSI-based MA', np.nan)
        if pd.isna(rsi) or pd.isna(rsi_ma) or rsi >= rsi_ma: continue
        if not row.get('close_below_ema200', False): continue
        if not row.get('ema50_below_ema200', False): continue
        if not row.get('atr_expanding', False): continue
        if pd.isna(row.get('adx14', np.nan)) or row['adx14'] < 20: continue
        if pd.isna(row.get('ema50_slope', np.nan)) or row['ema50_slope'] >= 0: continue
        entry = row['close']; atr = row['atr14']
        if pd.isna(atr) or atr <= 0: continue
        stop = row['high'] + atr * 0.5
        R = abs(entry - stop)
        if R <= 0 or R / atr > 5: continue
        res = simulate_trade(df30_for_short, i, 'SHORT', entry, stop, 3.0, 20, be_at_1r=True)
        if not res: continue
        res.update({'entry_time': row['time'], 'entry_price': entry,
                    'stop_price': stop, 'direction': 'SHORT', 'r_planned': 3.0,
                    'strategy': 'G_30M_SHORT_regime_filtered', 'tf': '30M'})
        trades_short.append(res)
    summaries.append({'strategy': 'G_30M_SHORT_BREAKDOWN_REGIME_FILTERED', **metrics(trades_short)})

    # =============================================================
    # Filter impact analysis (4H LONG breakout baseline)
    # =============================================================
    print("\n=== Filter impact (4H LONG breakout baseline) ===")
    filter_impact = []
    base_kw = dict(target_r=5.0, max_bars=30, be=True, require_rsi_above_ma=True, tf='4H')
    configs = [
        ('baseline_breakout_RSI_MA',  {}),
        ('with_rsi52_min',            {'rsi_min': 52}),
        ('with_close_above_ema200',   {'require_close_above_ema200': True}),
        ('with_ema50_above_ema200',   {'require_ema50_above_ema200': True}),
        ('with_atr_expanding',        {'require_atr_expanding': True}),
        ('with_adx20',                {'require_adx_min': 20}),
        ('with_adx25',                {'require_adx_min': 25}),
        ('with_ema50_slope_pos',      {'require_ema50_slope_pos': True}),
        ('full_regime_filter',        {'require_close_above_ema200': True, 'require_ema50_above_ema200': True,
                                        'require_atr_expanding': True, 'require_ema50_slope_pos': True,
                                        'require_adx_min': 20}),
    ]
    for fname, fkw in configs:
        kw = dict(base_kw); kw.update(fkw); kw['name'] = f'FILT_{fname}'
        t = strat_breakout_continuation(df4, **kw)
        m = metrics(t)
        filter_impact.append({
            'filter': fname, 'n': m.get('n', 0),
            'total_net_r': m.get('total_r_net', 0),
            'avg_net_r': m.get('avg_r_net', 0),
            'pf_net': m.get('pf_net', 0),
            'win_rate': m.get('win_rate', 0),
            'max_losing_streak': m.get('max_losing_streak', 0),
            'r_no_top5_net': m.get('r_no_top5_net', 0),
            'r_no_top10_net': m.get('r_no_top10_net', 0),
        })
    pd.DataFrame(filter_impact).to_csv(OUT_DIR / 'ETHUSD_filter_impact_analysis.csv', index=False)

    # =============================================================
    # Cost sensitivity for D_4H_breakout_regime_5R
    # =============================================================
    print("\n=== Cost sensitivity for D_4H_breakout_regime_5R ===")
    cost_rows = []
    base = trades_by['D_4H_breakout_regime_5R']
    if base:
        r_gross = pd.DataFrame(base)['r_outcome']
        n = len(r_gross); total_g = r_gross.sum()
        for c in [0.00, 0.02, 0.03, 0.05, 0.07, 0.10]:
            r_net = r_gross - c
            wins = r_net[r_net > 0]; losses = r_net[r_net < 0]
            pf = abs(wins.sum() / losses.sum()) if len(losses) and losses.sum() != 0 else float('inf')
            cost_rows.append({'spread': c, 'total_r_net': round(r_net.sum(), 2),
                              'avg_r_net': round(r_net.mean(), 4),
                              'pf_net': round(pf, 2) if pf != float('inf') else 'inf',
                              'win_rate': round((r_net > 0).mean(), 3),
                              'positive_overall': r_net.sum() > 0})
        be_spread = total_g / n
        cost_rows.append({'spread': 'break_even', 'total_r_net': 'N/A',
                          'avg_r_net': round(be_spread, 4), 'pf_net': 'N/A',
                          'win_rate': 'N/A', 'positive_overall': 'N/A'})
    pd.DataFrame(cost_rows).to_csv(OUT_DIR / 'ETHUSD_cost_sensitivity.csv', index=False)

    # =============================================================
    # Write outputs
    # =============================================================
    pd.DataFrame(summaries).to_csv(OUT_DIR / 'ETHUSD_strategy_search_summary.csv', index=False)

    # Best intraday + swing
    def score(t):
        if len(t) < 10: return -999
        r = [x['r_outcome'] - SPREAD_R for x in t]
        return np.mean(r) * np.sqrt(len(r))

    # Swing candidates (4H+)
    swing_keys = [k for k, v in trades_by.items() if any(t in k for t in ['4H', '12H', '1D'])]
    if swing_keys:
        best_swing = max(swing_keys, key=lambda k: score(trades_by[k]))
        pd.DataFrame(trades_by[best_swing]).to_csv(OUT_DIR / 'ETHUSD_best_swing_trades.csv', index=False)
        print(f"\nBest swing: {best_swing} (n={len(trades_by[best_swing])})")

    intraday_keys = [k for k, v in trades_by.items() if any(t in k for t in ['1H', '30M', '15M'])]
    if intraday_keys:
        best_intra = max(intraday_keys, key=lambda k: score(trades_by[k]))
        pd.DataFrame(trades_by[best_intra]).to_csv(OUT_DIR / 'ETHUSD_best_intraday_trades.csv', index=False)
        print(f"Best intraday: {best_intra} (n={len(trades_by[best_intra])})")

    # Yearly for top
    print("\n=== Yearly for D_4H_breakout_regime_5R ===")
    print(yearly_metrics(trades_by['D_4H_breakout_regime_5R']).to_string(index=False))

    print("\n=== Yearly for A_ETHUSD_4H_LONG_BREAKOUT_CONTINUATION (atual) ===")
    print(yearly_metrics(trades_by['A_4H_breakout_current']).to_string(index=False))

    print("\n=== Yearly for B LONG (current) ===")
    print(yearly_metrics(trades_by['B_30M_momentum_LONG_current']).to_string(index=False))

    print("\n=== Yearly for B SHORT (current) ===")
    print(yearly_metrics(trades_by['B_30M_momentum_SHORT_current']).to_string(index=False))


if __name__ == '__main__':
    main()
