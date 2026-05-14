#!/usr/bin/env python3
"""Information Gain Analysis — XAUUSD 4H module.

Baseline: R_full_trend_regime (current active module signal).
For each Pine indicator candidate, filter baseline trades and measure
marginal improvement in avg_r, no_top5, no_top10, max_streak.

Anti-overfit by design: inclusion-only, no parameter optimization.
"""
import pandas as pd
import numpy as np
from pathlib import Path

OUT_DIR = Path(__file__).parent
SPREAD_R = 0.05
CSV_4H = '/Users/cristrein/Downloads/PEPPERSTONE_XAUUSD, 240_aea76.csv'

PINE_COLS = [
    'NAS BOTTOM / LONG', 'NAS TOP / SHORT',
    'NAS_LONG_SIGNAL', 'NAS_SHORT_SIGNAL',
    'NAS_BOTTOM_SIGNAL', 'NAS_TOP_SIGNAL',
    'NAS_DISTANCE_FROM_EMA_ATR', 'NAS_RSI',
    'Shapes', 'Shapes.1', 'Shapes.2', 'Shapes.3', 'Shapes.4', 'Shapes.5',
    'Regular Bullish', 'Regular Bullish Label',
    'Regular Bearish', 'Regular Bearish Label',
]


def load_4h():
    df = pd.read_csv(CSV_4H)
    df.columns = [c.strip() for c in df.columns]
    df['time'] = pd.to_datetime(df['time'], unit='s')
    df = df.sort_values('time').reset_index(drop=True)
    for c in ['open', 'high', 'low', 'close', 'RSI', 'RSI-based MA',
              'NAS_DISTANCE_FROM_EMA_ATR', 'NAS_RSI']:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors='coerce')
    # Compute technical indicators
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
    df['ema50_slope'] = df['ema50'].diff(5)
    df['ema50_slope_pos'] = df['ema50_slope'] > 0
    # ADX
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
    return df


def baseline_signal(df, i, row):
    """R_full_trend_regime — current active XAU 4H module signal."""
    if not (row['close'] > row['open']): return False
    if pd.isna(row.get('body_pct')) or row['body_pct'] < 0.5: return False
    if not (row['close'] > df.at[i-1, 'swhi_10']): return False
    rsi = row.get('RSI', np.nan); rsi_ma = row.get('RSI-based MA', np.nan)
    if pd.isna(rsi) or pd.isna(rsi_ma) or rsi <= rsi_ma: return False
    if not row.get('close_above_ema200', False): return False
    if not row.get('ema50_above_ema200', False): return False
    if not row.get('atr_expanding', False): return False
    if not row.get('ema50_slope_pos', False): return False
    adx = row.get('adx14', np.nan)
    if pd.isna(adx) or adx < 20: return False
    return True


def simulate(df, i, entry, stop, tgt_r=4.0, max_bars=24):
    R = abs(entry - stop)
    if R <= 0: return None
    target = entry + R * tgt_r
    cur_stop = stop
    moved_be = False
    for j in range(i + 1, min(i + 1 + max_bars, len(df))):
        h, l = df.at[j, 'high'], df.at[j, 'low']
        if not moved_be and h >= entry + R:
            cur_stop = max(cur_stop, entry); moved_be = True
        if l <= cur_stop:
            return {'exit_idx': j, 'r': (cur_stop - entry) / R, 'bars': j - i}
        if h >= target:
            return {'exit_idx': j, 'r': (target - entry) / R, 'bars': j - i}
    last = min(i + max_bars, len(df) - 1)
    return {'exit_idx': last, 'r': (df.at[last, 'close'] - entry) / R, 'bars': last - i}


def run_baseline(df):
    """Run baseline signal and return list of (entry_idx, r, time, features_at_entry)."""
    trades = []
    i = 50
    while i < len(df) - 1:
        row = df.iloc[i]
        if pd.isna(row.get('atr14')) or pd.isna(row.get('ema200')):
            i += 1; continue
        if baseline_signal(df, i, row):
            entry = row['close']
            stop = row['low'] - 0.5 * row['atr14']
            R = entry - stop
            if R <= 0 or R > 5 * row['atr14']:
                i += 1; continue
            tr = simulate(df, i, entry, stop, 4.0, 24)
            if tr:
                trades.append({
                    'entry_idx': i,
                    'entry_time': row['time'],
                    'r': tr['r'],
                    'bars': tr['bars'],
                })
                i = tr['exit_idx'] + 1
                continue
        i += 1
    return trades


# =========================================================
# Feature engineering — Pine signals at/near entry
# =========================================================
def extract_features(df, trades):
    """For each trade, snapshot Pine features in lookback windows around entry_idx."""
    feats = []
    for t in trades:
        i = t['entry_idx']
        f = {'entry_idx': i, 'r': t['r'], 'entry_time': t['entry_time']}

        # Binary signals — "any in last N bars"
        def any_pos(col, lookback):
            if col not in df.columns: return False
            for k in range(max(0, i - lookback + 1), i + 1):
                v = df.at[k, col]
                if not pd.isna(v) and v != 0:
                    return True
            return False

        # Non-null signal in window (for divergence Labels which are sparse)
        def any_not_null(col, lookback):
            if col not in df.columns: return False
            for k in range(max(0, i - lookback + 1), i + 1):
                v = df.at[k, col]
                if not pd.isna(v):
                    return True
            return False

        # NAS binary signals
        f['nas_long_last_3'] = any_pos('NAS_LONG_SIGNAL', 3)
        f['nas_long_last_5'] = any_pos('NAS_LONG_SIGNAL', 5)
        f['nas_long_last_10'] = any_pos('NAS_LONG_SIGNAL', 10)
        f['nas_bottom_last_3'] = any_pos('NAS_BOTTOM_SIGNAL', 3)
        f['nas_bottom_last_5'] = any_pos('NAS_BOTTOM_SIGNAL', 5)
        f['nas_bottom_last_10'] = any_pos('NAS_BOTTOM_SIGNAL', 10)
        f['nas_bottom_last_20'] = any_pos('NAS_BOTTOM_SIGNAL', 20)

        # NAS RSI thresholds at entry bar
        nas_rsi = df.at[i, 'NAS_RSI']
        f['nas_rsi_gt_50'] = (not pd.isna(nas_rsi)) and nas_rsi > 50
        f['nas_rsi_gt_55'] = (not pd.isna(nas_rsi)) and nas_rsi > 55
        f['nas_rsi_gt_60'] = (not pd.isna(nas_rsi)) and nas_rsi > 60

        # NAS distance thresholds at entry bar
        nas_dist = df.at[i, 'NAS_DISTANCE_FROM_EMA_ATR']
        f['nas_dist_positive'] = (not pd.isna(nas_dist)) and nas_dist > 0
        f['nas_dist_strong_pos'] = (not pd.isna(nas_dist)) and nas_dist > 1.0
        f['nas_dist_pullback_0_05'] = (not pd.isna(nas_dist)) and 0 <= nas_dist <= 0.5
        f['nas_dist_pullback_0_10'] = (not pd.isna(nas_dist)) and 0 <= nas_dist <= 1.0
        f['nas_dist_above_pullback'] = (not pd.isna(nas_dist)) and nas_dist > 0.5

        # Bullish divergences (labeled = strong signal)
        f['bull_div_label_last_5'] = any_not_null('Regular Bullish Label', 5)
        f['bull_div_label_last_10'] = any_not_null('Regular Bullish Label', 10)
        f['bull_div_label_last_20'] = any_not_null('Regular Bullish Label', 20)
        # Generic divergence values (more frequent)
        f['bull_div_any_last_5'] = any_not_null('Regular Bullish', 5)
        f['bull_div_any_last_10'] = any_not_null('Regular Bullish', 10)

        # Bearish divergence in lookback — EXCLUSION signal (should NOT have bearish div near LONG entry)
        f['no_bear_div_label_last_10'] = not any_not_null('Regular Bearish Label', 10)
        f['no_bear_div_any_last_5'] = not any_not_null('Regular Bearish', 5)

        # Bubble shapes (any Shapes column non-zero)
        def any_shape(lookback):
            for k in range(max(0, i - lookback + 1), i + 1):
                for col in ['Shapes', 'Shapes.1', 'Shapes.2', 'Shapes.3', 'Shapes.4', 'Shapes.5']:
                    if col in df.columns:
                        v = df.at[k, col]
                        if not pd.isna(v) and v != 0:
                            return True
            return False

        f['shape_any_last_3'] = any_shape(3)
        f['shape_any_last_5'] = any_shape(5)
        f['shape_any_last_10'] = any_shape(10)

        feats.append(f)
    return pd.DataFrame(feats)


# =========================================================
# Metrics
# =========================================================
def metrics(r_arr, spread=SPREAD_R):
    if len(r_arr) == 0:
        return {'n': 0, 'total_r': 0, 'avg_r': 0, 'win_rate': 0, 'pf': 0,
                'max_streak': 0, 'no_top5': 0, 'no_top10': 0}
    r = np.array(r_arr) - spread
    wins = r > 0
    pf = r[r > 0].sum() / -r[r <= 0].sum() if (r <= 0).any() else float('inf')
    streak = mx = 0
    for w in wins:
        if not w: streak += 1; mx = max(mx, streak)
        else: streak = 0
    sd = np.sort(r)[::-1]
    nt5 = r.sum() - sd[:5].sum() if len(r) >= 5 else 0
    nt10 = r.sum() - sd[:10].sum() if len(r) >= 10 else 0
    return {
        'n': len(r), 'total_r': round(r.sum(), 2), 'avg_r': round(r.mean(), 4),
        'win_rate': round(wins.mean(), 3), 'pf': round(pf, 2),
        'max_streak': mx, 'no_top5': round(nt5, 2), 'no_top10': round(nt10, 2),
    }


def main():
    print("=== Loading XAUUSD 4H ===")
    df = load_4h()
    print(f"  rows={len(df)} span={(df.time.max()-df.time.min()).days/365.25:.2f}y")

    print("\n=== Running baseline signal (R_full_trend_regime) ===")
    trades = run_baseline(df)
    print(f"  baseline trades: {len(trades)}")

    bl_r = [t['r'] for t in trades]
    bl_m = metrics(bl_r)
    print(f"  Baseline metrics: {bl_m}")

    print("\n=== Extracting Pine features at entry ===")
    fdf = extract_features(df, trades)
    print(f"  features extracted for {len(fdf)} trades")
    print(f"  feature columns: {len([c for c in fdf.columns if c not in ['entry_idx', 'r', 'entry_time']])}")

    # For each feature, filter trades and recompute metrics
    print("\n=== Information Gain — per feature ===")
    rows = []
    feature_cols = [c for c in fdf.columns if c not in ['entry_idx', 'r', 'entry_time']]
    for feat in feature_cols:
        mask = fdf[feat].astype(bool)
        n_kept = int(mask.sum())
        n_dropped = len(fdf) - n_kept
        if n_kept == 0:
            continue
        r_kept = fdf.loc[mask, 'r'].values
        r_dropped = fdf.loc[~mask, 'r'].values
        m_kept = metrics(r_kept)
        m_dropped = metrics(r_dropped) if n_dropped > 0 else {'avg_r': 0, 'win_rate': 0}
        # Information gain proxy: how much avg_r the dropped trades had
        # If we drop trades with WORSE avg_r, this filter is useful
        rows.append({
            'feature': feat,
            'n_kept': n_kept,
            'frac_kept': round(n_kept / len(fdf), 3),
            'avg_r_kept': m_kept['avg_r'],
            'avg_r_dropped': m_dropped['avg_r'] if n_dropped > 0 else None,
            'delta_avg_r': round(m_kept['avg_r'] - bl_m['avg_r'], 4),
            'pf_kept': m_kept['pf'],
            'win_rate_kept': m_kept['win_rate'],
            'max_streak_kept': m_kept['max_streak'],
            'no_top5_kept': m_kept['no_top5'],
            'no_top10_kept': m_kept['no_top10'],
            'total_r_kept': m_kept['total_r'],
        })

    res = pd.DataFrame(rows).sort_values('delta_avg_r', ascending=False)
    res.to_csv(OUT_DIR / 'XAU_4H_info_gain.csv', index=False)

    print("\n=== Baseline reference ===")
    print(f"  n={bl_m['n']} total_r={bl_m['total_r']} avg_r={bl_m['avg_r']} pf={bl_m['pf']}")
    print(f"  win={bl_m['win_rate']} streak={bl_m['max_streak']} no_top5={bl_m['no_top5']} no_top10={bl_m['no_top10']}")

    print("\n=== Features RANKED by delta_avg_r (n_kept >= 50 to avoid overfit) ===")
    robust = res[res.n_kept >= 50].copy()
    print(robust[['feature', 'n_kept', 'frac_kept', 'avg_r_kept', 'delta_avg_r',
                  'pf_kept', 'win_rate_kept', 'max_streak_kept',
                  'no_top5_kept', 'no_top10_kept']].to_string(index=False))

    print("\n=== Features RANKED — ALL (incl. small samples, n>=20) ===")
    small = res[(res.n_kept >= 20) & (res.n_kept < 50)].copy()
    if len(small) > 0:
        print(small[['feature', 'n_kept', 'frac_kept', 'avg_r_kept', 'delta_avg_r',
                     'pf_kept', 'win_rate_kept', 'max_streak_kept',
                     'no_top5_kept', 'no_top10_kept']].to_string(index=False))

    print(f"\nSaved: XAU_4H_info_gain.csv")


if __name__ == '__main__':
    main()
