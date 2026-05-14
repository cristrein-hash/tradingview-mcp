#!/usr/bin/env python3
"""XAUUSD 4H SMC backtest V2 — OPTIMIZED.

Pre-computes zone state for every bar ONCE, then configs reuse it.
Reduces runtime from 30+ min to <5 min.
"""
import pandas as pd
import numpy as np
from pathlib import Path

OUT_DIR = Path(__file__).parent
SPREAD_R = 0.05
CSV_4H = '/Users/cristrein/Downloads/PEPPERSTONE_XAUUSD, 240_aea76.csv'
ZONE_LOOKBACK = 50  # bars back to find zone origin
TOUCH_LOOKBACK = 50  # bars back for touch counting from origin


def load_4h():
    df = pd.read_csv(CSV_4H)
    df.columns = [c.strip() for c in df.columns]
    df['time'] = pd.to_datetime(df['time'], unit='s')
    df = df.sort_values('time').reset_index(drop=True)
    for c in ['open', 'high', 'low', 'close']:
        df[c] = pd.to_numeric(df[c], errors='coerce')
    # ATR
    h, l, c = df['high'], df['low'], df['close']
    pc = c.shift(1)
    tr = pd.concat([(h - l).abs(), (h - pc).abs(), (l - pc).abs()], axis=1).max(axis=1)
    df['atr14'] = tr.ewm(alpha=1/14, adjust=False).mean()
    # Pine binary cols
    pine_bin = ['NAS_LONG_SIGNAL', 'NAS_SHORT_SIGNAL', 'NAS_BOTTOM_SIGNAL', 'NAS_TOP_SIGNAL',
                'Shapes', 'Shapes.1', 'Shapes.2', 'Shapes.3', 'Shapes.4', 'Shapes.5']
    for col in pine_bin:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    for col in ['Regular Bullish', 'Regular Bullish Label',
                'Regular Bearish', 'Regular Bearish Label']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    return df


def precompute_origins(df, cluster_threshold=5):
    """Vectorized: for each bar, identify if it's a LONG/SHORT zone origin.
    cluster_threshold = minimum total shape EVENTS in 10-bar window.
    """
    n = len(df)
    shape_cols = ['Shapes', 'Shapes.1', 'Shapes.2', 'Shapes.3', 'Shapes.4', 'Shapes.5']

    # Total shape events in 10-bar window (sum across all 6 columns)
    shape_events = df[shape_cols].sum(axis=1)
    total_events_10 = shape_events.rolling(10, min_periods=1).sum().values
    shape_qualifying = total_events_10 >= cluster_threshold

    nas_bot_arr = df['NAS_BOTTOM_SIGNAL'].values if 'NAS_BOTTOM_SIGNAL' in df.columns else np.zeros(n)
    nas_top_arr = df['NAS_TOP_SIGNAL'].values if 'NAS_TOP_SIGNAL' in df.columns else np.zeros(n)
    nas_bot_active = pd.Series(nas_bot_arr).rolling(10, min_periods=1).sum().values > 0
    nas_top_active = pd.Series(nas_top_arr).rolling(10, min_periods=1).sum().values > 0

    is_long_origin = shape_qualifying & nas_bot_active
    is_short_origin = shape_qualifying & nas_top_active

    return is_long_origin, is_short_origin


def precompute_zone_params(df, is_long_origin, is_short_origin):
    """For each origin bar, compute zone_low/top (LONG) or zone_high/bot (SHORT),
    impulse confirmation, and invalidation bar."""
    n = len(df)
    low_arr = df['low'].values
    high_arr = df['high'].values
    close_arr = df['close'].values
    atr_arr = df['atr14'].values

    long_zones = {}  # k -> dict
    short_zones = {}

    for k in range(2, n - 2):
        if pd.isna(atr_arr[k]) or atr_arr[k] <= 0:
            continue
        if is_long_origin[k]:
            zone_low = low_arr[max(0, k - 2):min(n, k + 3)].min()
            zone_top = zone_low + 1.0 * atr_arr[k]
            # Impulse: max high in [k, k+10] - zone_low >= 2*atr_k
            end = min(n, k + 11)
            max_high = high_arr[k:end].max()
            if max_high - zone_low < 2.0 * atr_arr[k]:
                continue
            # Invalidation bar (vectorized scan)
            invalidator = (close_arr[k + 1:] < zone_low - 0.5 * atr_arr[k])
            if invalidator.any():
                inv_bar = k + 1 + np.argmax(invalidator)
            else:
                inv_bar = n
            long_zones[k] = {
                'zone_low': zone_low, 'zone_top': zone_top,
                'atr_k': atr_arr[k], 'inv_bar': inv_bar,
            }
        if is_short_origin[k]:
            zone_high = high_arr[max(0, k - 2):min(n, k + 3)].max()
            zone_bot = zone_high - 1.0 * atr_arr[k]
            end = min(n, k + 11)
            min_low = low_arr[k:end].min()
            if zone_high - min_low < 2.0 * atr_arr[k]:
                continue
            invalidator = (close_arr[k + 1:] > zone_high + 0.5 * atr_arr[k])
            if invalidator.any():
                inv_bar = k + 1 + np.argmax(invalidator)
            else:
                inv_bar = n
            short_zones[k] = {
                'zone_high': zone_high, 'zone_bot': zone_bot,
                'atr_k': atr_arr[k], 'inv_bar': inv_bar,
            }

    return long_zones, short_zones


def precompute_state_per_bar(df, long_zones, short_zones):
    """For each bar i, find most recent ACTIVE zone (LONG and SHORT),
    compute touch count. Stores eligibility state."""
    n = len(df)
    low_arr = df['low'].values
    high_arr = df['high'].values
    close_arr = df['close'].values

    long_state = [None] * n
    short_state = [None] * n

    # Sort origins by k for efficient lookup
    long_ks = sorted(long_zones.keys())
    short_ks = sorted(short_zones.keys())

    for i in range(50, n):
        # LONG: find most recent k in [i-ZONE_LOOKBACK, i-3] where zone active
        best_k = None
        for k in reversed(long_ks):
            if k > i - 3:
                continue
            if k < i - ZONE_LOOKBACK:
                break  # going further back, all worse
            z = long_zones[k]
            if z['inv_bar'] <= i:
                continue
            # Current bar touching the zone?
            if low_arr[i] > z['zone_top']:
                continue
            best_k = k
            break  # found most recent
        if best_k is not None:
            z = long_zones[best_k]
            # Count touches in [k+1, i]
            touches = 0
            in_zone = False
            buf = 0.3 * z['atr_k']
            for j in range(best_k + 1, i + 1):
                low_in = low_arr[j] <= z['zone_top']
                if not in_zone and low_in:
                    touches += 1
                    in_zone = True
                elif in_zone and close_arr[j] > z['zone_top'] + buf:
                    in_zone = False
            long_state[i] = {'k': best_k, 'touches': touches, **z}

        # SHORT: same logic
        best_k = None
        for k in reversed(short_ks):
            if k > i - 3:
                continue
            if k < i - ZONE_LOOKBACK:
                break
            z = short_zones[k]
            if z['inv_bar'] <= i:
                continue
            if high_arr[i] < z['zone_bot']:
                continue
            best_k = k
            break
        if best_k is not None:
            z = short_zones[best_k]
            touches = 0
            in_zone = False
            buf = 0.3 * z['atr_k']
            for j in range(best_k + 1, i + 1):
                high_in = high_arr[j] >= z['zone_bot']
                if not in_zone and high_in:
                    touches += 1
                    in_zone = True
                elif in_zone and close_arr[j] < z['zone_bot'] - buf:
                    in_zone = False
            short_state[i] = {'k': best_k, 'touches': touches, **z}

    return long_state, short_state


def precompute_div_flags(df, lookback=15):
    """Pre-compute presence of bullish/bearish divergence in last 15 bars."""
    n = len(df)
    bull_div = np.zeros(n, dtype=bool)
    bear_div = np.zeros(n, dtype=bool)
    if 'Regular Bullish' in df.columns:
        s1 = df['Regular Bullish'].notna().astype(int).values
        s1_roll = pd.Series(s1).rolling(lookback, min_periods=1).sum().values > 0
        bull_div |= s1_roll
    if 'Regular Bullish Label' in df.columns:
        s2 = df['Regular Bullish Label'].notna().astype(int).values
        s2_roll = pd.Series(s2).rolling(lookback, min_periods=1).sum().values > 0
        bull_div |= s2_roll
    if 'Regular Bearish Label' in df.columns:
        sb = df['Regular Bearish Label'].notna().astype(int).values
        sb_roll = pd.Series(sb).rolling(lookback, min_periods=1).sum().values > 0
        bear_div |= sb_roll
    return bull_div, bear_div


def find_bos_long(df, i, scan=5):
    n = len(df)
    high_arr = df['high'].values
    close_arr = df['close'].values
    recent_high = high_arr[max(0, i - 3):i + 1].max()
    for j in range(i + 1, min(n, i + 1 + scan)):
        if close_arr[j] > recent_high:
            return j
    return None


def find_bos_short(df, i, scan=5):
    n = len(df)
    low_arr = df['low'].values
    close_arr = df['close'].values
    recent_low = low_arr[max(0, i - 3):i + 1].min()
    for j in range(i + 1, min(n, i + 1 + scan)):
        if close_arr[j] < recent_low:
            return j
    return None


def find_pullback_long(df, bos_idx, retrace_atr=0.3, scan=3):
    n = len(df)
    close_arr = df['close'].values
    atr_arr = df['atr14'].values
    bos_close = close_arr[bos_idx]
    atr_b = atr_arr[bos_idx]
    for m in range(bos_idx + 1, min(n, bos_idx + 1 + scan)):
        if close_arr[m] < bos_close - retrace_atr * atr_b:
            return m
    return None


def find_pullback_short(df, bos_idx, retrace_atr=0.3, scan=3):
    n = len(df)
    close_arr = df['close'].values
    atr_arr = df['atr14'].values
    bos_close = close_arr[bos_idx]
    atr_b = atr_arr[bos_idx]
    for m in range(bos_idx + 1, min(n, bos_idx + 1 + scan)):
        if close_arr[m] > bos_close + retrace_atr * atr_b:
            return m
    return None


def simulate(df, idx, direction, entry, stop, tgt_r, max_bars=24):
    n = len(df)
    high_arr = df['high'].values
    low_arr = df['low'].values
    close_arr = df['close'].values
    R = abs(entry - stop)
    if R <= 0: return None
    sign = 1 if direction == 'LONG' else -1
    target = entry + sign * R * tgt_r
    cur_stop = stop
    moved_be = False
    for j in range(idx + 1, min(idx + 1 + max_bars, n)):
        h, l = high_arr[j], low_arr[j]
        if direction == 'LONG':
            if not moved_be and h >= entry + R:
                cur_stop = max(cur_stop, entry); moved_be = True
            if l <= cur_stop:
                return {'exit_idx': j, 'r': (cur_stop - entry) / R}
            if h >= target:
                return {'exit_idx': j, 'r': (target - entry) / R}
        else:
            if not moved_be and l <= entry - R:
                cur_stop = min(cur_stop, entry); moved_be = True
            if h >= cur_stop:
                return {'exit_idx': j, 'r': (entry - cur_stop) / R}
            if l <= target:
                return {'exit_idx': j, 'r': (entry - target) / R}
    last = min(idx + max_bars, n - 1)
    return {'exit_idx': last, 'r': sign * (close_arr[last] - entry) / R}


def run_config(df, state, direction, target_r, stop_mult, entry_style,
               div_required, bull_div, bear_div):
    """Run one config using pre-computed state."""
    n = len(df)
    close_arr = df['close'].values
    atr_arr = df['atr14'].values
    trades = []
    i = 50
    while i < n - 1:
        s = state[i]
        if s is None or pd.isna(atr_arr[i]):
            i += 1; continue
        if s['touches'] not in (2, 3):
            i += 1; continue
        # Divergence check
        if direction == 'LONG':
            div_ok = bull_div[i]
            if div_required and not div_ok:
                i += 1; continue
        else:
            div_ok = bear_div[i]
            if div_required and not div_ok:
                i += 1; continue
        # BOS
        if direction == 'LONG':
            bos = find_bos_long(df, i)
        else:
            bos = find_bos_short(df, i)
        if bos is None:
            i += 1; continue
        # Entry
        if entry_style == 'direct_bos':
            entry_idx = bos
        else:
            if direction == 'LONG':
                pb = find_pullback_long(df, bos, 0.3, 3)
                if pb is None:
                    i += 1; continue
                if pb + 1 >= n:
                    i += 1; continue
                if close_arr[pb + 1] <= close_arr[pb]:
                    i += 1; continue
            else:
                pb = find_pullback_short(df, bos, 0.3, 3)
                if pb is None:
                    i += 1; continue
                if pb + 1 >= n:
                    i += 1; continue
                if close_arr[pb + 1] >= close_arr[pb]:
                    i += 1; continue
            entry_idx = pb + 1
        entry = close_arr[entry_idx]
        atr_e = atr_arr[entry_idx]
        if direction == 'LONG':
            stop = s['zone_low'] - stop_mult * atr_e
            R = entry - stop
        else:
            stop = s['zone_high'] + stop_mult * atr_e
            R = stop - entry
        if R <= 0 or R > 5 * atr_e:
            i = entry_idx + 1; continue
        tr = simulate(df, entry_idx, direction, entry, stop, target_r, 24)
        if tr:
            trades.append({
                'entry_time': df.at[entry_idx, 'time'],
                'entry_idx': entry_idx, 'entry': float(entry), 'stop': float(stop),
                'r': tr['r'], 'touch_count': s['touches'], 'div_present': bool(div_ok),
            })
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
    if not trades: return pd.DataFrame()
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


def main():
    import time as t_mod
    t0 = t_mod.time()
    print("=== Loading XAUUSD 4H ===")
    df = load_4h()
    print(f"  rows={len(df)} span={(df.time.max()-df.time.min()).days/365.25:.2f}y  ({t_mod.time()-t0:.1f}s)")

    print("=== Pre-computing divergence flags ===")
    bull_div, bear_div = precompute_div_flags(df, 15)
    print(f"  bull_div bars: {bull_div.sum()}  bear_div_label bars: {bear_div.sum()}  ({t_mod.time()-t0:.1f}s)")

    summaries = []
    trades_by = {}

    # Test both cluster thresholds (5 and 7) and full param sweep
    for cluster_th in [5, 7]:
        print(f"\n=== Cluster threshold {cluster_th} ===")
        is_long, is_short = precompute_origins(df, cluster_threshold=cluster_th)
        print(f"  LONG origins: {is_long.sum()}  SHORT origins: {is_short.sum()}  ({t_mod.time()-t0:.1f}s)")
        long_zones, short_zones = precompute_zone_params(df, is_long, is_short)
        print(f"  LONG valid zones: {len(long_zones)}  SHORT valid zones: {len(short_zones)}  ({t_mod.time()-t0:.1f}s)")
        long_state, short_state = precompute_state_per_bar(df, long_zones, short_zones)
        print(f"  state computed  ({t_mod.time()-t0:.1f}s)")

        # LONG variants
        for entry_style in ['pullback', 'direct_bos']:
            for stop_mult in [0.75, 1.0]:
                for div_req in [False, True]:
                    for trg in [2.0, 2.5, 3.0, 4.0, 5.0]:
                        lbl = f'LONG|cl{cluster_th}|{entry_style}|stop{stop_mult}|div_req={div_req}|tgt{trg}R'
                        tr = run_config(df, long_state, 'LONG', trg, stop_mult,
                                        entry_style, div_req, bull_div, bear_div)
                        summaries.append({'strategy': lbl, **metrics(tr)})
                        trades_by[lbl] = tr

        # SHORT variants
        for entry_style in ['pullback', 'direct_bos']:
            for stop_mult in [0.75, 1.0]:
                for trg in [2.0, 2.5, 3.0, 4.0, 5.0]:
                    lbl = f'SHORT|cl{cluster_th}|{entry_style}|stop{stop_mult}|div_req=True|tgt{trg}R'
                    tr = run_config(df, short_state, 'SHORT', trg, stop_mult,
                                    entry_style, True, bull_div, bear_div)
                    summaries.append({'strategy': lbl, **metrics(tr)})
                    trades_by[lbl] = tr

    print(f"  All configs run  ({t_mod.time()-t0:.1f}s total)")

    res = pd.DataFrame(summaries).sort_values('total_r_net', ascending=False)
    res.to_csv(OUT_DIR / 'XAU_4H_SMC_audit_summary.csv', index=False)

    cols = ['strategy', 'n', 'trades_per_week', 'trades_per_month', 'total_r_net',
            'avg_r_net', 'win_rate', 'pf_net', 'max_losing_streak',
            'r_no_top5_net', 'r_no_top10_net']
    long_df = res[res['strategy'].str.startswith('LONG')]
    short_df = res[res['strategy'].str.startswith('SHORT')]

    print("\n=== TOP 10 LONG ===")
    print(long_df[cols].head(10).to_string(index=False))
    print("\n=== TOP 10 SHORT ===")
    print(short_df[cols].head(10).to_string(index=False))

    print("\n=== Robust LONG (PF>=1.5, avg>=0.20, no_top5>=5, n>=30) ===")
    rl = long_df[(long_df.pf_net >= 1.5) & (long_df.avg_r_net >= 0.20) &
                 (long_df.r_no_top5_net >= 5) & (long_df.n >= 30)]
    print(rl[cols].to_string(index=False) if len(rl) > 0 else '  NONE')

    print("\n=== Robust SHORT (PF>=1.5, avg>=0.20, no_top5>=5, n>=20) ===")
    rs = short_df[(short_df.pf_net >= 1.5) & (short_df.avg_r_net >= 0.20) &
                  (short_df.r_no_top5_net >= 5) & (short_df.n >= 20)]
    print(rs[cols].to_string(index=False) if len(rs) > 0 else '  NONE')

    # Top 3 each: yearly
    for layer, sub in [('LONG', long_df), ('SHORT', short_df)]:
        print(f"\n\n========= TOP 3 {layer} YEARLY =========")
        for name in sub['strategy'].head(3):
            tr = trades_by.get(name, [])
            if tr:
                print(f"\n--- {name} ---")
                print(yearly(tr).to_string(index=False))

    if len(long_df) > 0:
        pd.DataFrame(trades_by[long_df.iloc[0]['strategy']]).to_csv(
            OUT_DIR / 'XAU_4H_SMC_best_LONG_trades.csv', index=False)
    if len(short_df) > 0:
        pd.DataFrame(trades_by[short_df.iloc[0]['strategy']]).to_csv(
            OUT_DIR / 'XAU_4H_SMC_best_SHORT_trades.csv', index=False)

    print(f"\nDone. Total runtime: {t_mod.time()-t0:.1f}s")


if __name__ == '__main__':
    main()
