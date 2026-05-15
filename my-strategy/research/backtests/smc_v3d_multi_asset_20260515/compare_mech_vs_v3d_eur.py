#!/usr/bin/env python3
"""Comparativo trade-by-trade: Mech EUR (sig_swing_combo_strict) vs V3d EUR Leonardo.

Mech: 47 trades, +13.35R, PF 2.03, win 42.6%
V3d:  45 trades, +25.75R, PF 2.65, win 53.3%

Cruzamento por proximidade temporal (entry_time diff <= 3 dias = 18 candles 4H).
Categorias: overlap / mech_only / v3d_only.
"""
import pandas as pd
import numpy as np
import sys
import math
from pathlib import Path

EUR_DIR = Path(__file__).parent.parent / 'eurusd_audit_20260512'
XAU_DIR = Path(__file__).parent.parent / 'xauusd_audit_20260512'
sys.path.insert(0, str(EUR_DIR))
sys.path.insert(0, str(XAU_DIR))

import backtest_eurusd as _be
import audit_v2 as _av2

# Override paths to current CSVs (15/05/2026 re-export)
_NEW_EUR_FILES = {
    '1D':  '/Users/cristrein/Downloads/PEPPERSTONE_EURUSD, 1D_1ec8f.csv',
    '12H': '/Users/cristrein/Downloads/PEPPERSTONE_EURUSD, 720_40a8c.csv',
    '4H':  '/Users/cristrein/Downloads/PEPPERSTONE_EURUSD, 240_28fd2.csv',
    '1H':  '/Users/cristrein/Downloads/PEPPERSTONE_EURUSD, 60_2e3eb.csv',
    '30M': '/Users/cristrein/Downloads/PEPPERSTONE_EURUSD, 30_2e138.csv',
    '15M': '/Users/cristrein/Downloads/PEPPERSTONE_EURUSD, 15_c43cf.csv',
}
_NEW_DXY = '/Users/cristrein/Downloads/TVC_DXY, 240_cf460.csv'
_av2.FILES_V2 = _NEW_EUR_FILES
_be.DXY_FILE = _NEW_DXY  # if module reads it at call-time

from backtest_eurusd import (load, load_macro_dxy, attach_dxy, htf_context,
                              run_long, metrics, SPREAD_R)
from audit_v2 import FILES_V2, add_extra_indicators

# V3d EUR loader (reusa CSV novo + lógica V3d)
DIR = Path(__file__).parent
sys.path.insert(0, str(DIR))
from audit_v3d_eth_eur_us500 import load_csv, run_v3d
from audit_xau_smc_v3 import detect_pivots, track_structure, PIVOT_LEN

EUR_CSV_NEW = '/Users/cristrein/Downloads/PEPPERSTONE_EURUSD, 240_28fd2.csv'


def sig_swing_combo_strict(df, i, row):
    """Mech EUR signal — replicado de refine_v2.py."""
    if not row.get('htf1d_bullish', False): return False
    if not row.get('htf12h_bullish', False): return False
    if not (row['close'] > row['open'] and row['body_pct'] >= 0.5
            and row['close'] > df.at[i-1, 'swhi_10']): return False
    rsi = row.get('RSI', np.nan); rsi_ma = row.get('RSI-based MA', np.nan)
    if pd.isna(rsi) or pd.isna(rsi_ma) or rsi <= rsi_ma: return False
    if not row.get('close_above_ema200', False): return False
    if not row.get('ema50_above_ema200', False): return False
    if not row.get('atr_expanding', False): return False
    if row['body_pct'] < 0.6: return False
    adx = row.get('adx14', np.nan)
    if pd.isna(adx) or adx < 25: return False
    atr = row.get('atr14', np.nan)
    if pd.isna(atr): return False
    if (row['high'] - row['low']) < 1.2 * atr: return False
    if not row.get('dxy_bearish', False): return False
    return True


def get_mech_trades():
    print("=== Loading mech EUR data (4H + HTF + DXY) ===")
    data = {tf: load(p) for tf, p in FILES_V2.items()}
    df1d, df12, df4 = data['1D'], data['12H'], data['4H']
    df4 = htf_context(df4, df12, 'htf12h')
    df4 = htf_context(df4, df1d, 'htf1d')
    df_dxy = load_macro_dxy()
    df4 = attach_dxy(df4, df_dxy)
    add_extra_indicators(df4)
    print(f"  4H bars: {len(df4)}")
    trades = run_long(df4, sig_swing_combo_strict, 2.5, 24,
                      'mech_combo_strict', '4H')
    print(f"  Mech trades: {len(trades)}")
    mdf = pd.DataFrame(trades)
    # run_long returns 'r_outcome' (gross); subtract spread to match V3d net
    mdf['r'] = mdf['r_outcome'].astype(float) - SPREAD_R
    return mdf


def get_v3d_trades():
    print("\n=== Loading V3d EUR (Leonardo OB) ===")
    df = load_csv(EUR_CSV_NEW)
    ph, pl = detect_pivots(df, PIVOT_LEN)
    events = track_structure(df, ph, pl)
    trades = run_v3d(df, events)
    print(f"  V3d trades: {len(trades)}")
    return trades


def cross_match(mech_df, v3d_df, tolerance_hours=72):
    """Match trades with entry_time within tolerance_hours."""
    if 'entry_time' not in mech_df.columns:
        for col in mech_df.columns:
            if 'time' in col.lower() or 'entry' in col.lower():
                print(f"  mech columns: {list(mech_df.columns)}")
                break
    mech_df = mech_df.copy()
    v3d_df = v3d_df.copy()
    mech_df['entry_time'] = pd.to_datetime(mech_df['entry_time'])
    v3d_df['entry_time'] = pd.to_datetime(v3d_df['entry_time'])
    mech_df = mech_df.sort_values('entry_time').reset_index(drop=True)
    v3d_df = v3d_df.sort_values('entry_time').reset_index(drop=True)

    tol = pd.Timedelta(hours=tolerance_hours)
    used_v3d = set()
    overlap = []
    mech_only = []

    for i, mrow in mech_df.iterrows():
        match_idx = None
        for j, vrow in v3d_df.iterrows():
            if j in used_v3d:
                continue
            dt = abs(vrow['entry_time'] - mrow['entry_time'])
            if dt <= tol:
                match_idx = j
                break
        if match_idx is not None:
            used_v3d.add(match_idx)
            overlap.append({
                'time_mech': mrow['entry_time'],
                'time_v3d': v3d_df.at[match_idx, 'entry_time'],
                'r_mech': mrow['r'],
                'r_v3d': v3d_df.at[match_idx, 'r'],
                'delta_h': (v3d_df.at[match_idx, 'entry_time'] - mrow['entry_time']).total_seconds() / 3600.0,
            })
        else:
            mech_only.append({
                'time': mrow['entry_time'],
                'r': mrow['r'],
                'year': mrow['entry_time'].year,
            })

    v3d_only = []
    for j, vrow in v3d_df.iterrows():
        if j not in used_v3d:
            v3d_only.append({
                'time': vrow['entry_time'],
                'r': vrow['r'],
                'year': vrow['entry_time'].year,
            })

    return pd.DataFrame(overlap), pd.DataFrame(mech_only), pd.DataFrame(v3d_only)


def cohort_metrics(df, col='r'):
    if len(df) == 0:
        return {'n': 0, 'total': 0, 'win_pct': 0, 'avg': 0, 'pf': 0}
    r = df[col].values
    wins = r[r > 0].sum()
    losses = -r[r < 0].sum()
    pf = wins / losses if losses > 0 else float('inf')
    return {
        'n': len(r),
        'total': float(r.sum()),
        'win_pct': float((r > 0).mean() * 100),
        'avg': float(r.mean()),
        'pf': float(pf) if pf != float('inf') else 999.0,
    }


def combined_portfolio_metrics(mech_df, v3d_df, overlap_df):
    """Combinado sem duplicar overlap: mech_only + v3d_only + overlap_mech_R."""
    # Conservative: for overlap, conta apenas 1 trade (do mech) — não duplica risco
    mech_df = mech_df.copy()
    mech_df['entry_time'] = pd.to_datetime(mech_df['entry_time'])
    if len(overlap_df) == 0:
        combined_r = list(mech_df['r'].values) + list(v3d_df['r'].values)
    else:
        # exclude v3d trades that overlapped
        overlap_v3d_times = set(pd.to_datetime(overlap_df['time_v3d']).values)
        v3d_unique = v3d_df[~pd.to_datetime(v3d_df['entry_time']).isin(overlap_v3d_times)]
        combined_r = list(mech_df['r'].values) + list(v3d_unique['r'].values)

    r = np.array(combined_r)
    total = r.sum()
    wins = r[r > 0].sum()
    losses = -r[r < 0].sum()
    pf = wins / losses if losses > 0 else float('inf')
    avg = r.mean() if len(r) > 0 else 0
    std = r.std(ddof=1) if len(r) > 1 else 0
    sharpe = (avg / std * math.sqrt(len(r))) if std > 0 else 0
    eq = np.cumsum(r)
    peak = np.maximum.accumulate(eq)
    dd = eq - peak
    return {
        'n': len(r),
        'total': float(total),
        'win_pct': float((r > 0).mean() * 100),
        'avg': float(avg),
        'pf': float(pf) if pf != float('inf') else 999.0,
        'sharpe': float(sharpe),
        'max_dd': float(dd.min()),
    }


def main():
    print("="*70)
    print("EUR Mech vs V3d — comparativo trade-by-trade")
    print("="*70)

    mech_df = get_mech_trades()
    v3d_df = get_v3d_trades()

    print(f"\n=== Cruzamento (tolerância ±72h) ===")
    overlap, mech_only, v3d_only = cross_match(mech_df, v3d_df, tolerance_hours=72)
    print(f"  OVERLAP:    {len(overlap)} trades")
    print(f"  MECH ONLY:  {len(mech_only)} trades")
    print(f"  V3D ONLY:   {len(v3d_only)} trades")

    if len(overlap) > 0:
        print(f"\n--- OVERLAP detalhe ---")
        print(overlap.to_string(index=False, float_format='%.2f'))
        ov_pearson = overlap[['r_mech', 'r_v3d']].corr().iloc[0, 1] if len(overlap) > 1 else None
        print(f"\n  Pearson r(mech, v3d) nos overlap: {ov_pearson:.3f}" if ov_pearson is not None else "  n=1 — sem correlação computável")

    print("\n=== Métricas por coorte ===")
    coh = {
        'OVERLAP_mech_R': cohort_metrics(overlap, 'r_mech') if len(overlap) > 0 else {'n': 0},
        'OVERLAP_v3d_R':  cohort_metrics(overlap, 'r_v3d')  if len(overlap) > 0 else {'n': 0},
        'MECH_ONLY':      cohort_metrics(mech_only),
        'V3D_ONLY':       cohort_metrics(v3d_only),
    }
    print(f"{'Cohort':<20} | {'n':>4} | {'Total':>8} | {'Avg':>6} | {'Win%':>6} | {'PF':>5}")
    print("-"*68)
    for name, m in coh.items():
        if m['n'] == 0:
            print(f"{name:<20} | {'0':>4} | {'—':>8} | {'—':>6} | {'—':>6} | {'—':>5}")
        else:
            print(f"{name:<20} | {m['n']:>4} | {m['total']:>+8.2f} | {m['avg']:>+6.3f} | {m['win_pct']:>5.1f}% | {m['pf']:>5.2f}")

    print("\n=== PORTFOLIO COMBINADO (sem duplicar overlap) ===")
    combined = combined_portfolio_metrics(mech_df, v3d_df, overlap)
    mech_alone = cohort_metrics(mech_df.assign(r=mech_df['r']))
    v3d_alone = cohort_metrics(v3d_df)

    # Sharpe solos
    def solo_sharpe(df):
        r = df['r'].values
        std = r.std(ddof=1)
        if std == 0 or len(r) < 2:
            return 0
        return r.mean() / std * math.sqrt(len(r))

    print(f"{'Strategy':<22} | {'n':>4} | {'Total R':>9} | {'PF':>5} | {'Win%':>6} | {'Sharpe':>7}")
    print("-"*75)
    print(f"{'Mech solo':<22} | {mech_alone['n']:>4} | {mech_alone['total']:>+9.2f} | {mech_alone['pf']:>5.2f} | {mech_alone['win_pct']:>5.1f}% | {solo_sharpe(mech_df):>7.2f}")
    print(f"{'V3d solo':<22} | {v3d_alone['n']:>4} | {v3d_alone['total']:>+9.2f} | {v3d_alone['pf']:>5.2f} | {v3d_alone['win_pct']:>5.1f}% | {solo_sharpe(v3d_df):>7.2f}")
    print(f"{'COMBINED':<22} | {combined['n']:>4} | {combined['total']:>+9.2f} | {combined['pf']:>5.2f} | {combined['win_pct']:>5.1f}% | {combined['sharpe']:>7.2f}")
    print(f"\n  MaxDD combined: {combined['max_dd']:+.2f}R")

    # Year breakdown of MECH_ONLY vs V3D_ONLY
    if len(mech_only) > 0 and len(v3d_only) > 0:
        print("\n=== Distribuição anual (mech_only vs v3d_only) ===")
        mo_years = mech_only.groupby('year').size().to_dict()
        vo_years = v3d_only.groupby('year').size().to_dict()
        all_years = sorted(set(list(mo_years.keys()) + list(vo_years.keys())))
        print(f"{'Year':>5} | {'mech_only':>10} | {'v3d_only':>9}")
        for yr in all_years:
            print(f"{yr:>5} | {mo_years.get(yr, 0):>10} | {vo_years.get(yr, 0):>9}")

    print("\n" + "="*70)
    print("CONCLUSÃO HONESTA")
    print("="*70)
    overlap_pct = (len(overlap) / max(len(mech_df), 1)) * 100
    if overlap_pct < 20:
        verdict = "COMPLEMENTARES — nichos majoritariamente disjuntos. V3d adiciona como módulo paralelo."
    elif overlap_pct > 50:
        verdict = "REDUNDANTES — mesmo nicho. V3d superior pode SUBSTITUIR mech."
    else:
        verdict = "PARCIALMENTE sobrepostos. Avaliar substituição parcial ou paralelo."
    print(f"Overlap: {overlap_pct:.1f}% dos mech também aparecem em V3d")
    print(f"Veredito: {verdict}")
    delta_total = combined['total'] - mech_alone['total']
    print(f"Ganho COMBINED vs Mech solo: {delta_total:+.2f}R ({delta_total/max(mech_alone['total'],0.01)*100:+.1f}%)")
    sharpe_solo = solo_sharpe(mech_df)
    delta_sharpe = combined['sharpe'] - sharpe_solo
    print(f"Sharpe combined vs mech solo: {combined['sharpe']:.2f} vs {sharpe_solo:.2f} (delta {delta_sharpe:+.2f})")


if __name__ == '__main__':
    main()
