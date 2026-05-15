#!/usr/bin/env python3
"""SMC6 — V3d Leonardo OB em ETH/EUR/US500 4H + analise de anomalia anual.

Reusa logica de audit_xau_smc_v3.py (CHoCH/BOS detection, OB Leonardo, LVB stop).
Roda V3d config vencedora: buffer=0%, BE@+2R, target=5R, touch_in_zone.

Acrescenta:
  - Metricas por ano (n, R total, win%, PF, avg R)
  - Z-score do total_R anual e flag de ano outlier (|Z| > 1.5)
  - Metricas COM e SEM ano outlier
"""
import sys
import json
import math
from pathlib import Path
import numpy as np
import pandas as pd

DIR = Path(__file__).parent
XAU_DIR = DIR.parent / 'xauusd_audit_20260512'
sys.path.insert(0, str(XAU_DIR))
from audit_xau_smc_v3 import (
    detect_pivots, track_structure, identify_ob_leonardo,
    find_last_valid_bottom, SPREAD_R, PIVOT_LEN, MAX_HOLD_BARS, TOUCH_LOOKAHEAD,
)

ASSETS = {
    'ETHUSD': '/Users/cristrein/Downloads/PEPPERSTONE_ETHUSD, 240_cbbf3.csv',
    'EURUSD': '/Users/cristrein/Downloads/PEPPERSTONE_EURUSD, 240_28fd2.csv',
    'US500':  '/Users/cristrein/Downloads/PEPPERSTONE_US500, 240_c18d8.csv',
}

# V3d winning config (from XAU audit)
BUFFER_PCT = 0.0
BE_AT_R = 2.0
TARGET_R = 5.0
ATR_R_CAP = 5.0  # reject if entry-stop > 5*ATR14


def load_csv(path):
    df = pd.read_csv(path)
    df.columns = [c.strip() for c in df.columns]
    df['time'] = pd.to_datetime(df['time'], unit='s')
    df = df.sort_values('time').reset_index(drop=True)
    for c in ['open', 'high', 'low', 'close']:
        df[c] = pd.to_numeric(df[c], errors='coerce')
    df = df.dropna(subset=['open', 'high', 'low', 'close']).reset_index(drop=True)
    h, l, c = df['high'], df['low'], df['close']
    pc = c.shift(1)
    tr = pd.concat([(h - l).abs(), (h - pc).abs(), (l - pc).abs()], axis=1).max(axis=1)
    df['atr14'] = tr.ewm(alpha=1 / 14, adjust=False).mean()
    df['atr200'] = tr.ewm(alpha=1 / 200, adjust=False).mean()
    df['year'] = df['time'].dt.year
    return df


def simulate(df, entry_idx, entry, stop, target_r, be_at_r):
    n = len(df)
    high = df['high'].values
    low = df['low'].values
    close = df['close'].values
    R = entry - stop
    if R <= 0:
        return None
    target = entry + R * target_r
    cur_stop = stop
    moved_be = False
    for j in range(entry_idx + 1, min(entry_idx + 1 + MAX_HOLD_BARS, n)):
        h, l = high[j], low[j]
        if be_at_r is not None and not moved_be and h >= entry + R * be_at_r:
            cur_stop = max(cur_stop, entry)
            moved_be = True
        if l <= cur_stop:
            return {'exit_idx': j, 'r': (cur_stop - entry) / R}
        if h >= target:
            return {'exit_idx': j, 'r': target_r}
    last = min(entry_idx + MAX_HOLD_BARS, n - 1)
    return {'exit_idx': last, 'r': (close[last] - entry) / R}


def run_v3d(df, events):
    trades = []
    n = len(df)
    close = df['close'].values
    low = df['low'].values
    atr14 = df['atr14'].values

    for ev in events:
        if ev['type'] not in ('BOS_BULL', 'CHOCH_BULL'):
            continue
        ob = identify_ob_leonardo(df, ev)
        if ob is None:
            continue

        # touch_in_zone entry
        entry_idx = None
        entry = None
        for j in range(ev['idx'] + 1, min(ev['idx'] + 1 + TOUCH_LOOKAHEAD, n)):
            if low[j] <= ob['ob_top']:
                if close[j] < ob['ob_low']:
                    break
                entry_idx = j
                entry = ob['ob_top']
                break
        if entry_idx is None:
            continue

        lvb = find_last_valid_bottom(df, ev)
        if lvb is None:
            continue
        stop = lvb * (1 - BUFFER_PCT / 100.0)
        if entry <= stop:
            continue
        R = entry - stop
        atr_e = atr14[entry_idx]
        if not np.isnan(atr_e) and atr_e > 0 and R > ATR_R_CAP * atr_e:
            continue

        res = simulate(df, entry_idx, entry, stop, TARGET_R, BE_AT_R)
        if res is None:
            continue
        trades.append({
            'event_idx': ev['idx'],
            'entry_time': df.at[entry_idx, 'time'],
            'entry': float(entry),
            'stop': float(stop),
            'R_pts': float(R),
            'r': float(res['r']) - SPREAD_R,
            'year': int(df.at[entry_idx, 'year']),
        })
    return pd.DataFrame(trades)


def metrics(trades_df):
    if len(trades_df) == 0:
        return {'n': 0, 'total_r': 0, 'win_pct': 0, 'pf': 0, 'avg_r': 0, 'sharpe': 0, 'max_dd': 0}
    r = trades_df['r'].values
    wins = r[r > 0].sum()
    losses = -r[r < 0].sum()
    pf = wins / losses if losses > 0 else float('inf')
    avg = r.mean()
    std = r.std(ddof=1) if len(r) > 1 else 0
    sharpe = (avg / std * math.sqrt(len(r))) if std > 0 else 0
    eq = np.cumsum(r)
    peak = np.maximum.accumulate(eq)
    dd = eq - peak
    max_dd = float(dd.min())
    return {
        'n': len(r),
        'total_r': float(r.sum()),
        'win_pct': float((r > 0).mean() * 100),
        'pf': float(pf) if pf != float('inf') else 999.0,
        'avg_r': float(avg),
        'sharpe': float(sharpe),
        'max_dd': max_dd,
    }


def yearly_breakdown(trades_df):
    if len(trades_df) == 0:
        return pd.DataFrame()
    rows = []
    for yr, g in trades_df.groupby('year'):
        m = metrics(g)
        rows.append({'year': int(yr), **m})
    return pd.DataFrame(rows).sort_values('year').reset_index(drop=True)


def detect_year_outliers(yearly_df, z_thresh=1.5):
    """Z-score do total_r anual. Anos com |Z| > thresh = outlier."""
    if len(yearly_df) < 3:
        return yearly_df.assign(zscore=0.0, is_outlier=False)
    mu = yearly_df['total_r'].mean()
    sigma = yearly_df['total_r'].std(ddof=1)
    if sigma == 0:
        return yearly_df.assign(zscore=0.0, is_outlier=False)
    yearly_df = yearly_df.copy()
    yearly_df['zscore'] = (yearly_df['total_r'] - mu) / sigma
    yearly_df['is_outlier'] = yearly_df['zscore'].abs() > z_thresh
    return yearly_df


def analyze_asset(asset, csv_path):
    print(f"\n{'='*70}")
    print(f"ASSET: {asset}")
    print('='*70)
    df = load_csv(csv_path)
    print(f"Bars: {len(df)} | {df['time'].iloc[0]} → {df['time'].iloc[-1]}")
    ph, pl = detect_pivots(df, PIVOT_LEN)
    events = track_structure(df, ph, pl)
    bull_events = [e for e in events if e['type'] in ('BOS_BULL', 'CHOCH_BULL')]
    print(f"BOS/CHOCH bull events: {len(bull_events)}")
    trades = run_v3d(df, events)
    if len(trades) == 0:
        print("⚠️  Nenhum trade gerado. Pulando.")
        return None

    overall = metrics(trades)
    print(f"\nV3d OVERALL: n={overall['n']} | total_R={overall['total_r']:+.2f} | "
          f"PF={overall['pf']:.2f} | win={overall['win_pct']:.1f}% | "
          f"Sharpe={overall['sharpe']:.2f} | MaxDD={overall['max_dd']:+.2f}")

    yearly = yearly_breakdown(trades)
    yearly = detect_year_outliers(yearly, z_thresh=1.5)
    print(f"\n--- Yearly breakdown ---")
    print(yearly.to_string(index=False, float_format='%.2f'))

    outliers = yearly[yearly['is_outlier']]
    if len(outliers) > 0:
        print(f"\n⚠️  Anos OUTLIER (|Z|>1.5):")
        for _, row in outliers.iterrows():
            sign = "EXTREMO POSITIVO" if row['zscore'] > 0 else "EXTREMO NEGATIVO"
            print(f"   {int(row['year'])}: total_R={row['total_r']:+.2f}, Z={row['zscore']:+.2f} ({sign})")

        outlier_years = outliers['year'].astype(int).tolist()
        clean_trades = trades[~trades['year'].isin(outlier_years)]
        clean = metrics(clean_trades)
        print(f"\n--- V3d SEM ano(s) outlier ({outlier_years}) ---")
        print(f"n={clean['n']} | total_R={clean['total_r']:+.2f} | PF={clean['pf']:.2f} | "
              f"win={clean['win_pct']:.1f}% | Sharpe={clean['sharpe']:.2f} | MaxDD={clean['max_dd']:+.2f}")
    else:
        print("\n✅ Nenhum ano outlier — amostra anual homogenea")

    return {
        'asset': asset,
        'overall': overall,
        'yearly': yearly.to_dict('records'),
        'outliers': outliers['year'].astype(int).tolist() if len(outliers) > 0 else [],
        'trades_n': len(trades),
        'first_trade': str(trades['entry_time'].min()),
        'last_trade': str(trades['entry_time'].max()),
    }


def main():
    print("="*70)
    print("SMC6 — V3d Leonardo OB | ETH / EUR / US500 4H")
    print("Config: buffer=0% | BE@+2R | target=5R | touch_in_zone | spread=0.05R")
    print("="*70)

    results = {}
    for asset, path in ASSETS.items():
        try:
            res = analyze_asset(asset, path)
            if res:
                results[asset] = res
        except Exception as e:
            print(f"❌ {asset} FALHOU: {e}")
            import traceback
            traceback.print_exc()

    print(f"\n\n{'='*70}")
    print("SUMARIO COMPARATIVO")
    print('='*70)
    print(f"{'Asset':<8} | {'n':>5} | {'TotalR':>9} | {'PF':>5} | {'Win%':>6} | "
          f"{'Sharpe':>7} | {'MaxDD':>8} | Outliers")
    print('-'*80)
    for asset, r in results.items():
        o = r['overall']
        out = ','.join(map(str, r['outliers'])) if r['outliers'] else '—'
        print(f"{asset:<8} | {o['n']:>5} | {o['total_r']:>+9.2f} | {o['pf']:>5.2f} | "
              f"{o['win_pct']:>6.1f} | {o['sharpe']:>7.2f} | {o['max_dd']:>+8.2f} | {out}")

    print(f"\n  Reference XAUUSD 4H V3d (audit anterior): n=37 | total_R=+9.28 | PF=1.49 | win=43.2%")

    out_path = DIR / 'v3d_multi_asset_results.json'
    with open(out_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\n✅ Resultados salvos em {out_path}")


if __name__ == '__main__':
    main()
