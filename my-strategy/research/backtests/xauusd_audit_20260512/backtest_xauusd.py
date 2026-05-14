#!/usr/bin/env python3
"""
XAUUSD Deep Strategy Audit — read-only backtest framework.
Date: 2026-05-12
"""
import pandas as pd
import numpy as np
from pathlib import Path
import json
import sys

OUT_DIR = Path(__file__).parent
OUT_DIR.mkdir(parents=True, exist_ok=True)

FILES = {
    '1D':  '/Users/cristrein/Downloads/PEPPERSTONE_XAUUSD, 1D_5b26a.csv',
    '12H': '/Users/cristrein/Downloads/PEPPERSTONE_XAUUSD, 720_8fe91.csv',
    '4H':  '/Users/cristrein/Downloads/PEPPERSTONE_XAUUSD, 240_a0fec.csv',
    '1H':  '/Users/cristrein/Downloads/PEPPERSTONE_XAUUSD, 60_e8c70.csv',
    '30M': '/Users/cristrein/Downloads/PEPPERSTONE_XAUUSD, 30_95a6d.csv',
    '15M': '/Users/cristrein/Downloads/PEPPERSTONE_XAUUSD, 15_52362.csv',
}


def load(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    df.columns = [c.strip() for c in df.columns]
    cols = list(df.columns)
    seen, new = {}, []
    for c in cols:
        if c in seen:
            seen[c] += 1
            new.append(f"{c}_{seen[c]}")
        else:
            seen[c] = 0
            new.append(c)
    df.columns = new
    df['time'] = pd.to_datetime(df['time'], unit='s')
    df = df.sort_values('time').reset_index(drop=True)
    # Numeric coercion
    for c in ['open','high','low','close','RSI','RSI-based MA','NAS_RSI',
              'NAS_DISTANCE_FROM_EMA_ATR','NAS_LONG_SIGNAL','NAS_SHORT_SIGNAL',
              'NAS_BOTTOM_SIGNAL','NAS_TOP_SIGNAL','Regular Bullish','Regular Bearish']:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors='coerce')
    # ATR(14) by Wilder's smoothing
    h, l, c = df['high'], df['low'], df['close']
    pc = c.shift(1)
    tr = pd.concat([(h - l).abs(), (h - pc).abs(), (l - pc).abs()], axis=1).max(axis=1)
    df['atr14'] = tr.ewm(alpha=1/14, adjust=False).mean()
    # Body / wick ratios
    body = (df['close'] - df['open']).abs()
    rng = (df['high'] - df['low']).replace(0, np.nan)
    df['body_pct'] = body / rng
    df['upper_wick'] = (df['high'] - df[['open','close']].max(axis=1)) / rng
    df['lower_wick'] = (df[['open','close']].min(axis=1) - df['low']) / rng
    df['close_in_upper_third'] = (df['close'] - df['low']) / rng >= 2/3
    df['close_in_lower_third'] = (df['close'] - df['low']) / rng <= 1/3
    # Bubble cluster: any Shapes column non-zero
    shape_cols = [c for c in df.columns if c.startswith('Shapes')]
    if shape_cols:
        df['has_bubble'] = (df[shape_cols].fillna(0).abs().sum(axis=1) > 0)
    else:
        df['has_bubble'] = False
    # RSI cross above MA
    if 'RSI' in df.columns and 'RSI-based MA' in df.columns:
        df['rsi_above_ma'] = df['RSI'] > df['RSI-based MA']
        df['rsi_cross_up'] = df['rsi_above_ma'] & (~df['rsi_above_ma'].shift(1).fillna(False))
        df['rsi_cross_down'] = (~df['rsi_above_ma']) & (df['rsi_above_ma'].shift(1).fillna(True))
    # Swing structure: rolling N-bar highs/lows
    for n in (5, 10, 20):
        df[f'swhi_{n}'] = df['high'].rolling(n).max()
        df[f'swlo_{n}'] = df['low'].rolling(n).min()
    return df


# ----------------------------------------------------------------------
# Trade simulator
# ----------------------------------------------------------------------
def simulate_trade(df: pd.DataFrame, entry_idx: int, direction: str,
                   entry: float, stop: float, target_r: float,
                   max_bars: int, be_at_1r: bool = False,
                   trail_at_3r: bool = False, trail_dist_r: float = 0.75):
    """
    Simulates one trade bar-by-bar starting at entry_idx+1.
    Returns dict with exit info and R outcome.
    Conservative ordering: stop checked before target if both hit same bar.
    MFE/MAE tracked. Exit at max_bars => mark-to-market.
    """
    R = abs(entry - stop)
    if R <= 0:
        return None
    sign = 1 if direction == 'LONG' else -1
    target = entry + sign * R * target_r
    cur_stop = stop
    mfe = 0.0
    mae = 0.0
    hit_1r = False
    moved_to_be = False
    activated_trail = False

    for j in range(entry_idx + 1, min(entry_idx + 1 + max_bars, len(df))):
        h = df.at[j, 'high']
        l = df.at[j, 'low']
        # Track MFE/MAE in R
        if direction == 'LONG':
            fav = (h - entry) / R
            adv = (entry - l) / R
        else:
            fav = (entry - l) / R
            adv = (h - entry) / R
        mfe = max(mfe, fav)
        mae = max(mae, adv)

        # BE move after +1R
        if be_at_1r and not moved_to_be and fav >= 1.0:
            cur_stop = entry
            moved_to_be = True
            hit_1r = True
        elif not hit_1r and fav >= 1.0:
            hit_1r = True

        # Trailing after +3R
        if trail_at_3r and not activated_trail and fav >= 3.0:
            activated_trail = True
            # trail stop = best price - trail_dist_r * R (for LONG) ; using fav-based
            if direction == 'LONG':
                cur_stop = max(cur_stop, entry + (fav - trail_dist_r) * R)
            else:
                cur_stop = min(cur_stop, entry - (fav - trail_dist_r) * R)
        elif trail_at_3r and activated_trail:
            if direction == 'LONG':
                cur_stop = max(cur_stop, entry + (fav - trail_dist_r) * R)
            else:
                cur_stop = min(cur_stop, entry - (fav - trail_dist_r) * R)

        # Check stop first (conservative)
        if direction == 'LONG':
            if l <= cur_stop:
                exit_price = cur_stop
                r_out = (exit_price - entry) / R
                return {'exit_idx': j, 'exit_price': exit_price, 'r_outcome': r_out,
                        'exit_reason': 'stop' if cur_stop <= entry else 'be_or_trail',
                        'mfe': mfe, 'mae': mae, 'bars_held': j - entry_idx}
            if h >= target:
                exit_price = target
                r_out = (exit_price - entry) / R
                return {'exit_idx': j, 'exit_price': exit_price, 'r_outcome': r_out,
                        'exit_reason': 'target', 'mfe': mfe, 'mae': mae, 'bars_held': j - entry_idx}
        else:  # SHORT
            if h >= cur_stop:
                exit_price = cur_stop
                r_out = (entry - exit_price) / R
                return {'exit_idx': j, 'exit_price': exit_price, 'r_outcome': r_out,
                        'exit_reason': 'stop' if cur_stop >= entry else 'be_or_trail',
                        'mfe': mfe, 'mae': mae, 'bars_held': j - entry_idx}
            if l <= target:
                exit_price = target
                r_out = (entry - exit_price) / R
                return {'exit_idx': j, 'exit_price': exit_price, 'r_outcome': r_out,
                        'exit_reason': 'target', 'mfe': mfe, 'mae': mae, 'bars_held': j - entry_idx}

    # Max bars reached → mark-to-market
    exit_idx = min(entry_idx + max_bars, len(df) - 1)
    last = df.at[exit_idx, 'close']
    if direction == 'LONG':
        r_out = (last - entry) / R
    else:
        r_out = (entry - last) / R
    return {'exit_idx': exit_idx, 'exit_price': last, 'r_outcome': r_out,
            'exit_reason': 'time_exit', 'mfe': mfe, 'mae': mae, 'bars_held': max_bars}


# ----------------------------------------------------------------------
# Helper: compute metrics for a list of trades
# ----------------------------------------------------------------------
def trade_metrics(trades: list, tf_label: str, strategy_name: str,
                  start: pd.Timestamp, end: pd.Timestamp) -> dict:
    if not trades:
        return {'strategy': strategy_name, 'tf': tf_label, 'n': 0}
    df = pd.DataFrame(trades)
    r = df['r_outcome']
    span_days = max(1, (end - start).days)
    span_weeks = span_days / 7
    span_months = span_days / 30.44
    span_years = span_days / 365.25
    wins_r = r[r > 0]
    losses_r = r[r < 0]
    # Max losing streak
    streak, max_streak = 0, 0
    for v in r:
        if v <= 0:
            streak += 1
            max_streak = max(max_streak, streak)
        else:
            streak = 0
    pf = abs(wins_r.sum() / losses_r.sum()) if len(losses_r) and losses_r.sum() != 0 else float('inf')
    # Top-N dependency
    sorted_r = sorted(r.tolist(), reverse=True)
    total_r = r.sum()
    r_no_top1 = total_r - sum(sorted_r[:1]) if len(sorted_r) >= 1 else total_r
    r_no_top3 = total_r - sum(sorted_r[:3]) if len(sorted_r) >= 3 else total_r
    r_no_top5 = total_r - sum(sorted_r[:5]) if len(sorted_r) >= 5 else total_r
    # Direction split
    by_dir = df.groupby('direction')['r_outcome'].agg(['count', 'sum', 'mean']).to_dict('index') if 'direction' in df.columns else {}
    return {
        'strategy': strategy_name,
        'tf': tf_label,
        'period_start': str(start.date()),
        'period_end': str(end.date()),
        'span_years': round(span_years, 2),
        'n_trades': len(df),
        'trades_per_week': round(len(df) / span_weeks, 2),
        'trades_per_month': round(len(df) / span_months, 2),
        'total_r': round(total_r, 2),
        'avg_r': round(r.mean(), 3),
        'median_r': round(r.median(), 3),
        'win_rate': round((r > 0).mean(), 3),
        'losses': int((r < 0).sum()),
        'breakeven': int((r.abs() < 0.05).sum()),
        'wins': int((r > 0).sum()),
        'profit_factor': round(pf, 2) if pf != float('inf') else 'inf',
        'max_losing_streak': max_streak,
        'best_trade_r': round(sorted_r[0], 2) if sorted_r else 0,
        'worst_trade_r': round(sorted_r[-1], 2) if sorted_r else 0,
        'avg_bars_held': round(df['bars_held'].mean(), 1) if 'bars_held' in df.columns else None,
        'avg_mfe_r': round(df['mfe'].mean(), 2) if 'mfe' in df.columns else None,
        'avg_mae_r': round(df['mae'].mean(), 2) if 'mae' in df.columns else None,
        'r_without_top1': round(r_no_top1, 2),
        'r_without_top3': round(r_no_top3, 2),
        'r_without_top5': round(r_no_top5, 2),
        'by_direction': by_dir,
    }


# ----------------------------------------------------------------------
# STRATEGIES
# ----------------------------------------------------------------------

def strategy_rejection_close(df, direction='LONG', target_r=2.0, max_bars=30,
                              be=True, trail=False, trail_dist=0.75,
                              require_rsi_extreme=False, require_bubble=False,
                              require_nas=False, require_div=False,
                              rsi_oversold=30, rsi_overbought=70,
                              wick_min=0.5, body_max=0.5,
                              stop_atr_mult=0.5,
                              tf_label='?', name='?'):
    """
    Generic rejection-close strategy.
    LONG: lower_wick >= wick_min, body <= body_max, close in upper third.
    SHORT: upper_wick >= wick_min, body <= body_max, close in lower third.
    """
    trades = []
    for i in range(20, len(df) - 1):
        row = df.iloc[i]
        if direction == 'LONG':
            structure = (row['lower_wick'] >= wick_min and row['body_pct'] <= body_max
                         and row.get('close_in_upper_third', False))
        else:
            structure = (row['upper_wick'] >= wick_min and row['body_pct'] <= body_max
                         and row.get('close_in_lower_third', False))
        if not structure:
            continue

        # Optional filters
        if require_rsi_extreme:
            rsi = row.get('RSI', np.nan)
            if pd.isna(rsi): continue
            if direction == 'LONG' and rsi > rsi_oversold + 5: continue
            if direction == 'SHORT' and rsi < rsi_overbought - 5: continue
        if require_bubble and not row.get('has_bubble', False):
            continue
        if require_nas:
            if direction == 'LONG' and row.get('NAS_BOTTOM_SIGNAL', 0) == 0 and row.get('NAS_LONG_SIGNAL', 0) == 0:
                continue
            if direction == 'SHORT' and row.get('NAS_TOP_SIGNAL', 0) == 0 and row.get('NAS_SHORT_SIGNAL', 0) == 0:
                continue
        if require_div:
            if direction == 'LONG' and (row.get('Regular Bullish', 0) or 0) == 0: continue
            if direction == 'SHORT' and (row.get('Regular Bearish', 0) or 0) == 0: continue

        # Entry at next bar open
        entry_idx = i
        entry = df.at[i, 'close']  # entry on close of signal bar (simplification)
        atr = df.at[i, 'atr14']
        if pd.isna(atr) or atr <= 0:
            continue
        if direction == 'LONG':
            stop = row['low'] - atr * stop_atr_mult
        else:
            stop = row['high'] + atr * stop_atr_mult
        # R:R sanity
        R = abs(entry - stop)
        if R <= 0:
            continue
        if R / atr > 5:  # avoid absurdly wide stops
            continue
        res = simulate_trade(df, entry_idx, direction, entry, stop, target_r,
                              max_bars, be_at_1r=be, trail_at_3r=trail, trail_dist_r=trail_dist)
        if not res:
            continue
        res.update({
            'entry_time': df.at[entry_idx, 'time'], 'entry_price': entry,
            'stop_price': stop, 'direction': direction, 'r_planned': target_r,
            'strategy': name, 'tf': tf_label,
        })
        trades.append(res)
    return trades


def strategy_sweep_reentry(df, direction='LONG', target_r=2.0, max_bars=30,
                            be=True, trail=False, lookback=10,
                            stop_atr_mult=0.5, tf_label='?', name='?'):
    """
    LONG: candle sweeps below swlo_lookback then closes above prev swing low.
    SHORT: candle sweeps above swhi_lookback then closes below prev swing high.
    """
    trades = []
    swlo = f'swlo_{lookback}'
    swhi = f'swhi_{lookback}'
    for i in range(lookback + 5, len(df) - 1):
        row = df.iloc[i]
        prev_low = df.at[i-1, swlo]
        prev_high = df.at[i-1, swhi]
        if direction == 'LONG':
            condition = row['low'] < prev_low and row['close'] > prev_low
        else:
            condition = row['high'] > prev_high and row['close'] < prev_high
        if not condition:
            continue
        entry = row['close']
        atr = row['atr14']
        if pd.isna(atr) or atr <= 0: continue
        if direction == 'LONG':
            stop = row['low'] - atr * stop_atr_mult
        else:
            stop = row['high'] + atr * stop_atr_mult
        R = abs(entry - stop)
        if R <= 0 or R / atr > 5: continue
        res = simulate_trade(df, i, direction, entry, stop, target_r, max_bars,
                              be_at_1r=be, trail_at_3r=trail)
        if not res: continue
        res.update({'entry_time': row['time'], 'entry_price': entry,
                    'stop_price': stop, 'direction': direction, 'r_planned': target_r,
                    'strategy': name, 'tf': tf_label})
        trades.append(res)
    return trades


def strategy_momentum_continuation(df, direction='LONG', target_r=2.0, max_bars=20,
                                    be=True, rsi_filter=True, name='?', tf_label='?'):
    """
    LONG: bar makes new N-bar high with close > open + body_pct > 0.5 + (optional) RSI > MA.
    SHORT: reverse.
    """
    trades = []
    for i in range(20, len(df) - 1):
        row = df.iloc[i]
        if direction == 'LONG':
            cond = (row['close'] > row['open'] and row['body_pct'] >= 0.5
                    and row['close'] > df.at[i-1, 'swhi_10'])
            if rsi_filter and (row.get('RSI', np.nan) - row.get('RSI-based MA', np.nan) < 0):
                continue
        else:
            cond = (row['close'] < row['open'] and row['body_pct'] >= 0.5
                    and row['close'] < df.at[i-1, 'swlo_10'])
            if rsi_filter and (row.get('RSI', np.nan) - row.get('RSI-based MA', np.nan) > 0):
                continue
        if not cond:
            continue
        entry = row['close']
        atr = row['atr14']
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
                    'strategy': name, 'tf': tf_label})
        trades.append(res)
    return trades


def strategy_rsi_reclaim(df, direction='LONG', target_r=2.0, max_bars=20,
                          name='?', tf_label='?'):
    """
    LONG: RSI crosses up over its MA AND price is in a recent low area (close near 20-bar low).
    SHORT: RSI crosses down under its MA AND price is in recent high.
    """
    trades = []
    if 'rsi_cross_up' not in df.columns:
        return trades
    for i in range(20, len(df) - 1):
        row = df.iloc[i]
        if direction == 'LONG':
            cond = row['rsi_cross_up'] and (row['close'] - df.at[i, 'swlo_20']) / (df.at[i, 'swhi_20'] - df.at[i, 'swlo_20'] + 1e-9) < 0.4
        else:
            cond = row['rsi_cross_down'] and (df.at[i, 'swhi_20'] - row['close']) / (df.at[i, 'swhi_20'] - df.at[i, 'swlo_20'] + 1e-9) < 0.4
        if not cond:
            continue
        entry = row['close']
        atr = row['atr14']
        if pd.isna(atr) or atr <= 0: continue
        if direction == 'LONG':
            stop = row['low'] - atr * 0.5
        else:
            stop = row['high'] + atr * 0.5
        R = abs(entry - stop)
        if R <= 0 or R / atr > 5: continue
        res = simulate_trade(df, i, direction, entry, stop, target_r, max_bars, be_at_1r=True)
        if not res: continue
        res.update({'entry_time': row['time'], 'entry_price': entry,
                    'stop_price': stop, 'direction': direction, 'r_planned': target_r,
                    'strategy': name, 'tf': tf_label})
        trades.append(res)
    return trades


# ----------------------------------------------------------------------
# MAIN
# ----------------------------------------------------------------------
def main():
    summaries = []
    all_trades_by_strategy = {}

    print("=== LOADING DATA ===")
    data = {}
    for tf, path in FILES.items():
        data[tf] = load(path)
        print(f"  {tf}: {len(data[tf])} bars, {data[tf]['time'].min().date()} → {data[tf]['time'].max().date()}")

    # =============================================================
    # 4H swing strategies
    # =============================================================
    df4 = data['4H']
    start4, end4 = df4['time'].min(), df4['time'].max()

    print("\n=== 4H STRATEGIES ===")
    # A. Old global rule (strict): RSI extreme + bubble + rejection + LONG
    t = strategy_rejection_close(df4, 'LONG', target_r=2.0, max_bars=30,
        be=True, require_rsi_extreme=True, require_bubble=True,
        tf_label='4H', name='A_old_global_strict_LONG')
    summaries.append(trade_metrics(t, '4H', 'A_old_global_strict_LONG', start4, end4))
    all_trades_by_strategy['A_old_global_strict_LONG'] = t

    # A2. Old global SHORT
    t = strategy_rejection_close(df4, 'SHORT', target_r=2.0, max_bars=30,
        be=True, require_rsi_extreme=True, require_bubble=True,
        tf_label='4H', name='A_old_global_strict_SHORT')
    summaries.append(trade_metrics(t, '4H', 'A_old_global_strict_SHORT', start4, end4))
    all_trades_by_strategy['A_old_global_strict_SHORT'] = t

    # A3. Old global SOFTENED (drop bubble, keep RSI extreme)
    t = strategy_rejection_close(df4, 'LONG', target_r=2.0, max_bars=30,
        be=True, require_rsi_extreme=True, require_bubble=False,
        tf_label='4H', name='A_old_softened_no_bubble_LONG')
    summaries.append(trade_metrics(t, '4H', 'A_old_softened_no_bubble_LONG', start4, end4))
    all_trades_by_strategy['A_old_softened_no_bubble_LONG'] = t

    # B. XAUUSD_4H_LONG_REJECTION_SWING — quality rejection, BE+1R, trail+3R 1.5R
    t = strategy_rejection_close(df4, 'LONG', target_r=4.0, max_bars=30,
        be=True, trail=True, trail_dist=1.5,
        require_rsi_extreme=False, require_bubble=False,
        wick_min=0.5, body_max=0.4,
        tf_label='4H', name='B_XAUUSD_4H_LONG_REJECTION_SWING')
    summaries.append(trade_metrics(t, '4H', 'B_XAUUSD_4H_LONG_REJECTION_SWING', start4, end4))
    all_trades_by_strategy['B_XAUUSD_4H_LONG_REJECTION_SWING'] = t

    # New 4H breakout/retest LONG
    t = strategy_momentum_continuation(df4, 'LONG', target_r=3.0, max_bars=20,
        be=True, rsi_filter=True, name='New_4H_breakout_LONG', tf_label='4H')
    summaries.append(trade_metrics(t, '4H', 'New_4H_breakout_LONG', start4, end4))
    all_trades_by_strategy['New_4H_breakout_LONG'] = t

    # New 4H sweep+reentry LONG
    t = strategy_sweep_reentry(df4, 'LONG', target_r=2.5, max_bars=30, be=True,
        lookback=10, name='New_4H_sweep_reentry_LONG', tf_label='4H')
    summaries.append(trade_metrics(t, '4H', 'New_4H_sweep_reentry_LONG', start4, end4))
    all_trades_by_strategy['New_4H_sweep_reentry_LONG'] = t

    # =============================================================
    # 1H execution strategies
    # =============================================================
    df1 = data['1H']
    start1, end1 = df1['time'].min(), df1['time'].max()
    print("\n=== 1H STRATEGIES ===")

    # C. XAUUSD_1H_LONG_REJECTION_EXECUTION
    t = strategy_rejection_close(df1, 'LONG', target_r=3.0, max_bars=48,
        be=True, trail=True, trail_dist=0.75,
        wick_min=0.5, body_max=0.4,
        tf_label='1H', name='C_XAUUSD_1H_LONG_REJECTION_EXECUTION')
    summaries.append(trade_metrics(t, '1H', 'C_XAUUSD_1H_LONG_REJECTION_EXECUTION', start1, end1))
    all_trades_by_strategy['C_XAUUSD_1H_LONG_REJECTION_EXECUTION'] = t

    # New 1H simple rejection (no filters) for comparison
    t = strategy_rejection_close(df1, 'LONG', target_r=2.0, max_bars=24,
        be=True, wick_min=0.55, body_max=0.35,
        tf_label='1H', name='New_1H_simple_rejection_LONG')
    summaries.append(trade_metrics(t, '1H', 'New_1H_simple_rejection_LONG', start1, end1))
    all_trades_by_strategy['New_1H_simple_rejection_LONG'] = t

    # New 1H SHORT rejection (to test if SHORT has edge)
    t = strategy_rejection_close(df1, 'SHORT', target_r=2.0, max_bars=24,
        be=True, wick_min=0.55, body_max=0.35,
        tf_label='1H', name='New_1H_simple_rejection_SHORT')
    summaries.append(trade_metrics(t, '1H', 'New_1H_simple_rejection_SHORT', start1, end1))
    all_trades_by_strategy['New_1H_simple_rejection_SHORT'] = t

    # New 1H RSI reclaim LONG
    t = strategy_rsi_reclaim(df1, 'LONG', target_r=2.0, max_bars=24,
        name='New_1H_rsi_reclaim_LONG', tf_label='1H')
    summaries.append(trade_metrics(t, '1H', 'New_1H_rsi_reclaim_LONG', start1, end1))
    all_trades_by_strategy['New_1H_rsi_reclaim_LONG'] = t

    # =============================================================
    # 30M strategies
    # =============================================================
    df30 = data['30M']
    start30, end30 = df30['time'].min(), df30['time'].max()
    print("\n=== 30M STRATEGIES ===")

    # D. XAUUSD_INTRADAY_BB_CONFLUENCE — 30M setup, both directions (proxy: rejection both ways)
    t_long = strategy_rejection_close(df30, 'LONG', target_r=2.0, max_bars=24,
        be=True, wick_min=0.55, body_max=0.4,
        tf_label='30M', name='D_intraday_bb_30M_rejection_LONG')
    t_short = strategy_rejection_close(df30, 'SHORT', target_r=2.0, max_bars=24,
        be=True, wick_min=0.55, body_max=0.4,
        tf_label='30M', name='D_intraday_bb_30M_rejection_SHORT')
    summaries.append(trade_metrics(t_long, '30M', 'D_intraday_bb_30M_rejection_LONG', start30, end30))
    summaries.append(trade_metrics(t_short, '30M', 'D_intraday_bb_30M_rejection_SHORT', start30, end30))
    all_trades_by_strategy['D_intraday_bb_30M_rejection_LONG'] = t_long
    all_trades_by_strategy['D_intraday_bb_30M_rejection_SHORT'] = t_short

    # New 30M momentum continuation both
    t_long = strategy_momentum_continuation(df30, 'LONG', target_r=2.0, max_bars=16,
        be=True, rsi_filter=True, name='New_30M_momentum_LONG', tf_label='30M')
    t_short = strategy_momentum_continuation(df30, 'SHORT', target_r=2.0, max_bars=16,
        be=True, rsi_filter=True, name='New_30M_momentum_SHORT', tf_label='30M')
    summaries.append(trade_metrics(t_long, '30M', 'New_30M_momentum_LONG', start30, end30))
    summaries.append(trade_metrics(t_short, '30M', 'New_30M_momentum_SHORT', start30, end30))
    all_trades_by_strategy['New_30M_momentum_LONG'] = t_long
    all_trades_by_strategy['New_30M_momentum_SHORT'] = t_short

    # New 30M sweep+reentry both
    t_long = strategy_sweep_reentry(df30, 'LONG', target_r=2.0, max_bars=20, be=True,
        lookback=10, name='New_30M_sweep_reentry_LONG', tf_label='30M')
    t_short = strategy_sweep_reentry(df30, 'SHORT', target_r=2.0, max_bars=20, be=True,
        lookback=10, name='New_30M_sweep_reentry_SHORT', tf_label='30M')
    summaries.append(trade_metrics(t_long, '30M', 'New_30M_sweep_reentry_LONG', start30, end30))
    summaries.append(trade_metrics(t_short, '30M', 'New_30M_sweep_reentry_SHORT', start30, end30))
    all_trades_by_strategy['New_30M_sweep_reentry_LONG'] = t_long
    all_trades_by_strategy['New_30M_sweep_reentry_SHORT'] = t_short

    # =============================================================
    # 15M execution strategies
    # =============================================================
    df15 = data['15M']
    start15, end15 = df15['time'].min(), df15['time'].max()
    print("\n=== 15M STRATEGIES ===")
    t_long = strategy_rejection_close(df15, 'LONG', target_r=2.0, max_bars=24,
        be=True, wick_min=0.55, body_max=0.4,
        tf_label='15M', name='New_15M_rejection_LONG')
    t_short = strategy_rejection_close(df15, 'SHORT', target_r=2.0, max_bars=24,
        be=True, wick_min=0.55, body_max=0.4,
        tf_label='15M', name='New_15M_rejection_SHORT')
    summaries.append(trade_metrics(t_long, '15M', 'New_15M_rejection_LONG', start15, end15))
    summaries.append(trade_metrics(t_short, '15M', 'New_15M_rejection_SHORT', start15, end15))
    all_trades_by_strategy['New_15M_rejection_LONG'] = t_long
    all_trades_by_strategy['New_15M_rejection_SHORT'] = t_short

    # =============================================================
    # FILTER IMPACT ANALYSIS — on the 4H LONG rejection baseline
    # =============================================================
    print("\n=== FILTER IMPACT (4H LONG rejection baseline) ===")
    filter_impact = []
    base_kw = dict(direction='LONG', target_r=2.0, max_bars=30, be=True, wick_min=0.5, body_max=0.4)
    filter_configs = [
        ('baseline_no_filter', {}),
        ('with_rsi_extreme', {'require_rsi_extreme': True}),
        ('with_bubble', {'require_bubble': True}),
        ('with_nas', {'require_nas': True}),
        ('with_divergence', {'require_div': True}),
        ('with_rsi_AND_bubble', {'require_rsi_extreme': True, 'require_bubble': True}),
        ('with_rsi_AND_bubble_AND_nas', {'require_rsi_extreme': True, 'require_bubble': True, 'require_nas': True}),
    ]
    for fname, fkw in filter_configs:
        kw = dict(base_kw); kw.update(fkw)
        t = strategy_rejection_close(df4, tf_label='4H', name=f'FILT_{fname}', **kw)
        m = trade_metrics(t, '4H', f'FILT_{fname}', start4, end4)
        filter_impact.append({
            'filter': fname,
            'n_trades': m.get('n_trades', 0),
            'trades_per_year': round(m.get('n_trades', 0) / max(0.01, m.get('span_years', 1)), 1),
            'total_r': m.get('total_r', 0),
            'avg_r': m.get('avg_r', 0),
            'win_rate': m.get('win_rate', 0),
            'max_losing_streak': m.get('max_losing_streak', 0),
            'profit_factor': m.get('profit_factor', 0),
        })

    # ============================================
    # WRITE OUTPUTS
    # ============================================
    print("\n=== WRITING OUTPUTS ===")
    summary_df = pd.DataFrame([{k: v for k, v in s.items() if k != 'by_direction'} for s in summaries])
    summary_df.to_csv(OUT_DIR / 'XAUUSD_strategy_search_summary.csv', index=False)
    print(f"  Summary written: {len(summary_df)} strategies")

    # Best intraday trades
    intraday_strats = [k for k in all_trades_by_strategy if any(tag in k for tag in ['1H', '30M', '15M'])]
    if intraday_strats:
        # Pick best by avg_r * sqrt(n)
        scoreboard = []
        for k in intraday_strats:
            trades = all_trades_by_strategy[k]
            if len(trades) >= 20:
                rs = [t['r_outcome'] for t in trades]
                score = (np.mean(rs)) * np.sqrt(len(rs))
                scoreboard.append((k, score, len(rs), np.mean(rs)))
        if scoreboard:
            scoreboard.sort(key=lambda x: -x[1])
            best_name = scoreboard[0][0]
            best_trades = all_trades_by_strategy[best_name]
            bt_df = pd.DataFrame(best_trades)
            bt_df.to_csv(OUT_DIR / 'XAUUSD_best_intraday_trades.csv', index=False)
            print(f"  Best intraday: {best_name} ({scoreboard[0][2]} trades, avg_r={scoreboard[0][3]:.3f})")

    # Best swing trades (4H/12H/1D)
    swing_strats = [k for k in all_trades_by_strategy if any(tag in k for tag in ['4H', '12H', '1D'])]
    if swing_strats:
        scoreboard = []
        for k in swing_strats:
            trades = all_trades_by_strategy[k]
            if len(trades) >= 10:
                rs = [t['r_outcome'] for t in trades]
                score = np.mean(rs) * np.sqrt(len(rs))
                scoreboard.append((k, score, len(rs), np.mean(rs)))
        if scoreboard:
            scoreboard.sort(key=lambda x: -x[1])
            best_name = scoreboard[0][0]
            best_trades = all_trades_by_strategy[best_name]
            bt_df = pd.DataFrame(best_trades)
            bt_df.to_csv(OUT_DIR / 'XAUUSD_best_swing_trades.csv', index=False)
            print(f"  Best swing: {best_name} ({scoreboard[0][2]} trades, avg_r={scoreboard[0][3]:.3f})")

    # Filter impact CSV
    pd.DataFrame(filter_impact).to_csv(OUT_DIR / 'XAUUSD_filter_impact_analysis.csv', index=False)
    print(f"  Filter impact: {len(filter_impact)} configs")

    # Save full JSON of summaries for report
    with open(OUT_DIR / 'all_summaries.json', 'w') as f:
        json.dump([{k: (str(v) if isinstance(v, (pd.Timestamp,)) else v) for k, v in s.items()}
                   for s in summaries], f, indent=2, default=str)

    return summaries, filter_impact, all_trades_by_strategy


if __name__ == '__main__':
    main()
