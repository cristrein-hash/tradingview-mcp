#!/usr/bin/env python3
"""XAUUSD 4H — REAL operational strategy backtest.

Strategy: SMC demand/supply zone + bubble cluster + NAS TOP/BOTTOM + multi-touch
+ structure break + pullback entry. LONG + SHORT. Single-position rule.

Per user's operational spec (2026-05-12):
- Entry on 2nd or 3rd touch (never first)
- After 1st 4H candle breaking structure (BOS), entry on pullback
- Stop wider than obvious — "survive then thrive"
- SHORT requires bear divergence; LONG bull divergence optional
- Cluster: >=5 of 6 Shapes non-zero in 10-bar window + at least 1 NAS LONG/SHORT
- Target 2-5R, BE after +1R, no trailing
"""
import pandas as pd
import numpy as np
from pathlib import Path

OUT_DIR = Path(__file__).parent
SPREAD_R = 0.05
CSV_4H = '/Users/cristrein/Downloads/PEPPERSTONE_XAUUSD, 240_aea76.csv'


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
    # Numeric coerce Pine cols
    pine_bin = ['NAS_LONG_SIGNAL', 'NAS_SHORT_SIGNAL', 'NAS_BOTTOM_SIGNAL', 'NAS_TOP_SIGNAL',
                'Shapes', 'Shapes.1', 'Shapes.2', 'Shapes.3', 'Shapes.4', 'Shapes.5']
    for c in pine_bin:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)
    # Sparse value cols (preserve NaN)
    for c in ['Regular Bullish', 'Regular Bullish Label',
              'Regular Bearish', 'Regular Bearish Label']:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors='coerce')
    # Shapes count per bar
    shape_cols = ['Shapes', 'Shapes.1', 'Shapes.2', 'Shapes.3', 'Shapes.4', 'Shapes.5']
    df['shape_count'] = df[shape_cols].sum(axis=1)
    # Swing levels
    for n in (5, 10, 20):
        df[f'swhi_{n}'] = df['high'].rolling(n).max()
        df[f'swlo_{n}'] = df['low'].rolling(n).min()
    return df


def detect_long_zone(df, i, lookback=50):
    """Find most recent qualifying LONG zone origin bar k in [i-lookback, i-3].
    Returns dict with zone_low, zone_top, k, or None."""
    atr_i = df.at[i, 'atr14']
    if pd.isna(atr_i):
        return None
    for k in range(max(10, i - lookback), i - 2):
        # Cluster check: >=5 shapes non-zero in [k-9, k]
        win = df.iloc[max(0, k - 9):k + 1]
        shape_active = (win[['Shapes', 'Shapes.1', 'Shapes.2', 'Shapes.3', 'Shapes.4', 'Shapes.5']] > 0).any(axis=0).sum()
        if shape_active < 5:
            continue
        # NAS_BOTTOM_SIGNAL >= 1 in same window
        nas_active = (win['NAS_BOTTOM_SIGNAL'] > 0).sum()
        if nas_active < 1:
            continue
        # Zone definition
        zone_low = df.iloc[max(0, k - 2):k + 3]['low'].min()
        atr_k = df.at[k, 'atr14']
        if pd.isna(atr_k) or atr_k <= 0:
            continue
        zone_top = zone_low + 1.0 * atr_k
        # Impulse confirmation: in [k, k+10], max(high) > zone_low + 2 * atr_k
        end_imp = min(len(df), k + 11)
        max_high = df.iloc[k:end_imp]['high'].max()
        if max_high - zone_low < 2.0 * atr_k:
            continue
        # Zone validity: no close < zone_low - 0.5*atr_k between k+1 and i
        invalidator = (df.iloc[k + 1:i + 1]['close'] < zone_low - 0.5 * atr_k).any()
        if invalidator:
            continue
        return {'k': k, 'zone_low': zone_low, 'zone_top': zone_top, 'atr_k': atr_k}
    return None


def detect_short_zone(df, i, lookback=50):
    """Same for SHORT — supply zone."""
    atr_i = df.at[i, 'atr14']
    if pd.isna(atr_i):
        return None
    for k in range(max(10, i - lookback), i - 2):
        win = df.iloc[max(0, k - 9):k + 1]
        shape_active = (win[['Shapes', 'Shapes.1', 'Shapes.2', 'Shapes.3', 'Shapes.4', 'Shapes.5']] > 0).any(axis=0).sum()
        if shape_active < 5:
            continue
        nas_active = (win['NAS_TOP_SIGNAL'] > 0).sum()
        if nas_active < 1:
            continue
        zone_high = df.iloc[max(0, k - 2):k + 3]['high'].max()
        atr_k = df.at[k, 'atr14']
        if pd.isna(atr_k) or atr_k <= 0:
            continue
        zone_bot = zone_high - 1.0 * atr_k
        end_imp = min(len(df), k + 11)
        min_low = df.iloc[k:end_imp]['low'].min()
        if zone_high - min_low < 2.0 * atr_k:
            continue
        invalidator = (df.iloc[k + 1:i + 1]['close'] > zone_high + 0.5 * atr_k).any()
        if invalidator:
            continue
        return {'k': k, 'zone_high': zone_high, 'zone_bot': zone_bot, 'atr_k': atr_k}
    return None


def count_long_touches(df, k, i, zone_top, zone_low):
    """Count distinct touches: low entered zone, then exited, then re-entered."""
    touches = 0
    in_zone = False
    for j in range(k + 1, i + 1):
        low_in = df.at[j, 'low'] <= zone_top
        # 'exited zone' means close above zone_top by 0.3 ATR (to avoid noise)
        if not in_zone and low_in:
            touches += 1
            in_zone = True
        elif in_zone and df.at[j, 'close'] > zone_top + 0.3 * df.at[k, 'atr14']:
            in_zone = False
    return touches


def count_short_touches(df, k, i, zone_bot, zone_high):
    touches = 0
    in_zone = False
    for j in range(k + 1, i + 1):
        high_in = df.at[j, 'high'] >= zone_bot
        if not in_zone and high_in:
            touches += 1
            in_zone = True
        elif in_zone and df.at[j, 'close'] < zone_bot - 0.3 * df.at[k, 'atr14']:
            in_zone = False
    return touches


def has_recent_bull_div(df, i, lookback=15):
    win = df.iloc[max(0, i - lookback + 1):i + 1]
    if 'Regular Bullish' in df.columns:
        if win['Regular Bullish'].notna().any():
            return True
    if 'Regular Bullish Label' in df.columns:
        if win['Regular Bullish Label'].notna().any():
            return True
    return False


def has_recent_bear_div_label(df, i, lookback=15):
    if 'Regular Bearish Label' not in df.columns:
        return False
    win = df.iloc[max(0, i - lookback + 1):i + 1]
    return win['Regular Bearish Label'].notna().any()


def find_bos_long(df, i, lookback_high=3, scan_ahead=5):
    """Find first BOS up: close > recent micro-high within scan_ahead bars."""
    recent_high = df.iloc[max(0, i - lookback_high):i + 1]['high'].max()
    for j in range(i + 1, min(len(df), i + 1 + scan_ahead)):
        if df.at[j, 'close'] > recent_high:
            return j
    return None


def find_bos_short(df, i, lookback_low=3, scan_ahead=5):
    recent_low = df.iloc[max(0, i - lookback_low):i + 1]['low'].min()
    for j in range(i + 1, min(len(df), i + 1 + scan_ahead)):
        if df.at[j, 'close'] < recent_low:
            return j
    return None


def find_pullback_long(df, bos_idx, retrace_atr=0.3, scan=3):
    bos_close = df.at[bos_idx, 'close']
    atr_b = df.at[bos_idx, 'atr14']
    for m in range(bos_idx + 1, min(len(df), bos_idx + 1 + scan)):
        if df.at[m, 'close'] < bos_close - retrace_atr * atr_b:
            return m
    return None


def find_pullback_short(df, bos_idx, retrace_atr=0.3, scan=3):
    bos_close = df.at[bos_idx, 'close']
    atr_b = df.at[bos_idx, 'atr14']
    for m in range(bos_idx + 1, min(len(df), bos_idx + 1 + scan)):
        if df.at[m, 'close'] > bos_close + retrace_atr * atr_b:
            return m
    return None


def simulate(df, idx, direction, entry, stop, tgt_r, max_bars):
    R = abs(entry - stop)
    if R <= 0: return None
    sign = 1 if direction == 'LONG' else -1
    target = entry + sign * R * tgt_r
    cur_stop = stop
    moved_be = False
    for j in range(idx + 1, min(idx + 1 + max_bars, len(df))):
        h, l = df.at[j, 'high'], df.at[j, 'low']
        if direction == 'LONG':
            if not moved_be and h >= entry + R:
                cur_stop = max(cur_stop, entry); moved_be = True
            if l <= cur_stop:
                return {'exit_idx': j, 'r': (cur_stop - entry) / R, 'bars': j - idx}
            if h >= target:
                return {'exit_idx': j, 'r': (target - entry) / R, 'bars': j - idx}
        else:
            if not moved_be and l <= entry - R:
                cur_stop = min(cur_stop, entry); moved_be = True
            if h >= cur_stop:
                return {'exit_idx': j, 'r': (entry - cur_stop) / R, 'bars': j - idx}
            if l <= target:
                return {'exit_idx': j, 'r': (entry - target) / R, 'bars': j - idx}
    last = min(idx + max_bars, len(df) - 1)
    final = df.at[last, 'close']
    return {'exit_idx': last, 'r': sign * (final - entry) / R, 'bars': last - idx}


def run_strategy(df, direction, target_r, stop_mult, entry_style, div_required=False):
    """
    direction: 'LONG' or 'SHORT'
    entry_style: 'direct_bos' or 'pullback'
    """
    trades = []
    i = 50
    while i < len(df) - 1:
        row = df.iloc[i]
        if pd.isna(row.get('atr14')):
            i += 1; continue

        # Find qualifying zone
        if direction == 'LONG':
            zone = detect_long_zone(df, i, lookback=50)
            if zone is None:
                i += 1; continue
            # Touch eligibility
            if row['low'] > zone['zone_top']:  # not currently touching
                i += 1; continue
            touches = count_long_touches(df, zone['k'], i, zone['zone_top'], zone['zone_low'])
            if touches not in (2, 3):
                i += 1; continue
            # Divergence (optional)
            div_ok = has_recent_bull_div(df, i, 15)
            if div_required and not div_ok:
                i += 1; continue
            # Find BOS up
            bos = find_bos_long(df, i, lookback_high=3, scan_ahead=5)
            if bos is None:
                i += 1; continue
            # Entry
            if entry_style == 'direct_bos':
                entry_idx = bos
            else:
                pb = find_pullback_long(df, bos, retrace_atr=0.3, scan=3)
                if pb is None:
                    i += 1; continue
                if pb + 1 >= len(df):
                    i += 1; continue
                if df.at[pb + 1, 'close'] <= df.at[pb, 'close']:
                    i += 1; continue
                entry_idx = pb + 1
            entry = df.at[entry_idx, 'close']
            atr_e = df.at[entry_idx, 'atr14']
            stop = zone['zone_low'] - stop_mult * atr_e
            R = entry - stop
            if R <= 0 or R > 5 * atr_e:
                i = entry_idx + 1; continue
            tr = simulate(df, entry_idx, 'LONG', entry, stop, target_r, 24)
            if tr:
                trades.append({
                    'entry_time': df.at[entry_idx, 'time'],
                    'entry_idx': entry_idx, 'entry': entry, 'stop': stop,
                    'r': tr['r'], 'bars': tr['bars'],
                    'zone_k_time': df.at[zone['k'], 'time'].isoformat(),
                    'touch_count': touches, 'div_present': div_ok,
                })
                i = tr['exit_idx'] + 1
                continue
        else:  # SHORT
            zone = detect_short_zone(df, i, lookback=50)
            if zone is None:
                i += 1; continue
            if row['high'] < zone['zone_bot']:
                i += 1; continue
            touches = count_short_touches(df, zone['k'], i, zone['zone_bot'], zone['zone_high'])
            if touches not in (2, 3):
                i += 1; continue
            div_ok = has_recent_bear_div_label(df, i, 15)
            if div_required and not div_ok:
                i += 1; continue
            bos = find_bos_short(df, i, lookback_low=3, scan_ahead=5)
            if bos is None:
                i += 1; continue
            if entry_style == 'direct_bos':
                entry_idx = bos
            else:
                pb = find_pullback_short(df, bos, retrace_atr=0.3, scan=3)
                if pb is None:
                    i += 1; continue
                if pb + 1 >= len(df):
                    i += 1; continue
                if df.at[pb + 1, 'close'] >= df.at[pb, 'close']:
                    i += 1; continue
                entry_idx = pb + 1
            entry = df.at[entry_idx, 'close']
            atr_e = df.at[entry_idx, 'atr14']
            stop = zone['zone_high'] + stop_mult * atr_e
            R = stop - entry
            if R <= 0 or R > 5 * atr_e:
                i = entry_idx + 1; continue
            tr = simulate(df, entry_idx, 'SHORT', entry, stop, target_r, 24)
            if tr:
                trades.append({
                    'entry_time': df.at[entry_idx, 'time'],
                    'entry_idx': entry_idx, 'entry': entry, 'stop': stop,
                    'r': tr['r'], 'bars': tr['bars'],
                    'zone_k_time': df.at[zone['k'], 'time'].isoformat(),
                    'touch_count': touches, 'div_present': div_ok,
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


def main():
    print("=== Loading XAUUSD 4H ===")
    df = load_4h()
    print(f"  rows={len(df)} span={(df.time.max()-df.time.min()).days/365.25:.2f}y")

    summaries = []
    trades_by = {}

    # LONG variants
    print("\n=== LONG variants ===")
    for entry_style in ['pullback', 'direct_bos']:
        for stop_mult in [0.75, 1.0]:
            for div_req in [False, True]:
                for trg in [2.0, 2.5, 3.0, 4.0, 5.0]:
                    lbl = f'XAU_4H_LONG_smc|entry_{entry_style}|stop{stop_mult}|div_req_{div_req}|tgt{trg}R'
                    tr = run_strategy(df, 'LONG', trg, stop_mult, entry_style, div_required=div_req)
                    summaries.append({'strategy': lbl, **metrics(tr)})
                    trades_by[lbl] = tr

    # SHORT variants (bear div ALWAYS required per user spec)
    print("=== SHORT variants ===")
    for entry_style in ['pullback', 'direct_bos']:
        for stop_mult in [0.75, 1.0]:
            for trg in [2.0, 2.5, 3.0, 4.0, 5.0]:
                lbl = f'XAU_4H_SHORT_smc|entry_{entry_style}|stop{stop_mult}|div_req_True|tgt{trg}R'
                tr = run_strategy(df, 'SHORT', trg, stop_mult, entry_style, div_required=True)
                summaries.append({'strategy': lbl, **metrics(tr)})
                trades_by[lbl] = tr

    res = pd.DataFrame(summaries).sort_values('total_r_net', ascending=False)
    res.to_csv(OUT_DIR / 'XAU_4H_SMC_audit_summary.csv', index=False)

    cols = ['strategy', 'n', 'trades_per_week', 'trades_per_month', 'total_r_net',
            'avg_r_net', 'win_rate', 'pf_net', 'max_losing_streak',
            'r_no_top5_net', 'r_no_top10_net']

    long_df = res[res['strategy'].str.contains('LONG')]
    short_df = res[res['strategy'].str.contains('SHORT')]

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

    # Top 3 each: yearly + cost
    for layer, sub in [('LONG', long_df), ('SHORT', short_df)]:
        print(f"\n\n========= TOP 3 {layer} DETAIL =========")
        for name in sub['strategy'].head(3):
            tr = trades_by.get(name, [])
            if tr:
                print(f"\n--- {name} ---")
                print("Yearly:")
                print(yearly(tr).to_string(index=False))

    # Save best trade lists
    if len(long_df) > 0:
        top_long = long_df.iloc[0]['strategy']
        pd.DataFrame(trades_by[top_long]).to_csv(OUT_DIR / 'XAU_4H_SMC_best_LONG_trades.csv', index=False)
    if len(short_df) > 0:
        top_short = short_df.iloc[0]['strategy']
        pd.DataFrame(trades_by[top_short]).to_csv(OUT_DIR / 'XAU_4H_SMC_best_SHORT_trades.csv', index=False)

    print(f"\nSaved: XAU_4H_SMC_audit_summary.csv ({len(res)} configs)")


if __name__ == '__main__':
    main()
