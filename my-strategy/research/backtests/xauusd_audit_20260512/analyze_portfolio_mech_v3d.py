#!/usr/bin/env python3
"""Analise de portfolio: Mecanico (n=234) + V3d melhor combinados.

Metricas:
- Equity curve combinada vs solo
- Max drawdown comparativo
- Sharpe/Sortino approx (anualizado)
- Correlacao Pearson dos returns mensais
- Periodos exclusivos por ano
- Sizing scenarios: 50/50, 70/30, equal-vol, Kelly approx
"""
import pandas as pd
import numpy as np
import sys
from pathlib import Path

DIR = Path(__file__).parent
sys.path.insert(0, str(DIR))
from regime_filter_test import compute_indicators, htf_context, run_strategy
from backtest_xauusd import load
from audit_xau_smc_v3 import (
    load_data as load_v3, detect_pivots, track_structure,
    PIVOT_LEN, MAX_HOLD_BARS,
)
from audit_xau_smc_v3d import run_v3d_struct

SPREAD_R = 0.05
FILES = {
    '4H':  '/Users/cristrein/Downloads/PEPPERSTONE_XAUUSD, 240_aea76.csv',
    '12H': '/Users/cristrein/Downloads/PEPPERSTONE_XAUUSD, 720_8fe91.csv',
    '1D':  '/Users/cristrein/Downloads/PEPPERSTONE_XAUUSD, 1D_7f278.csv',
}


def get_mech_trades():
    df4 = load(FILES['4H'])
    df4 = compute_indicators(df4)
    df12 = load(FILES['12H'])
    df1d = load(FILES['1D'])
    df4 = htf_context(df4, df12, 'htf12h')
    df4 = htf_context(df4, df1d, 'htf1d')
    filt = {'adx_min': 20, 'close_above_ema200': True, 'ema50_above_ema200': True,
            'ema50_slope_pos': True, 'atr_expanding': True}
    trades = run_strategy(df4, filt, target_r=4.0, max_bars=24, be=True, name='mech')
    df = pd.DataFrame(trades)
    df['entry_time'] = pd.to_datetime(df['entry_time'])
    df['r_net'] = df['r_outcome'] - SPREAD_R
    df['source'] = 'MECH'
    return df[['entry_time', 'r_net', 'source']].sort_values('entry_time').reset_index(drop=True)


def get_v3d_trades():
    df = load_v3()
    ph, pl = detect_pivots(df, PIVOT_LEN)
    events = track_structure(df, ph, pl)
    # V3d best: struct buf=0% BE@2R tgt5R
    trades = run_v3d_struct(df, events, buffer_pct=0.0, be_at_r=2.0, target_r=5.0)
    df_t = pd.DataFrame(trades)
    df_t['entry_time'] = pd.to_datetime(df_t['entry_time'])
    df_t['r_net'] = df_t['r'] - SPREAD_R
    df_t['source'] = 'V3D'
    return df_t[['entry_time', 'r_net', 'source']].sort_values('entry_time').reset_index(drop=True)


def equity_curve(df_trades):
    df = df_trades.sort_values('entry_time').copy()
    df['cum_r'] = df['r_net'].cumsum()
    return df


def max_drawdown(equity):
    eq = equity['cum_r'].values
    peaks = np.maximum.accumulate(eq)
    dd = eq - peaks
    return float(dd.min()), int(dd.argmin())


def sharpe_annualized(df_trades, periods_per_year=52):
    """Sharpe approx usando R semanal. Trades agregados em buckets semanais."""
    df = df_trades.copy()
    df['week'] = df['entry_time'].dt.to_period('W')
    weekly = df.groupby('week')['r_net'].sum()
    mean = weekly.mean()
    std = weekly.std()
    if std == 0 or np.isnan(std):
        return 0.0
    return float((mean / std) * np.sqrt(periods_per_year))


def sortino_annualized(df_trades, periods_per_year=52):
    df = df_trades.copy()
    df['week'] = df['entry_time'].dt.to_period('W')
    weekly = df.groupby('week')['r_net'].sum()
    mean = weekly.mean()
    downside = weekly[weekly < 0].std()
    if downside == 0 or np.isnan(downside):
        return float('inf')
    return float((mean / downside) * np.sqrt(periods_per_year))


def yearly_breakdown(df_trades):
    df = df_trades.copy()
    df['year'] = df['entry_time'].dt.year
    return df.groupby('year').agg(
        n=('r_net', 'count'),
        total_r=('r_net', 'sum'),
        win_rate=('r_net', lambda x: (x > 0).mean()),
    ).round(3)


def yearly_correlation(mech_df, v3d_df):
    """Correlacao Pearson dos R semanais entre mech e v3d."""
    m = mech_df.copy()
    v = v3d_df.copy()
    m['week'] = m['entry_time'].dt.to_period('W')
    v['week'] = v['entry_time'].dt.to_period('W')
    m_w = m.groupby('week')['r_net'].sum().rename('mech')
    v_w = v.groupby('week')['r_net'].sum().rename('v3d')
    merged = pd.concat([m_w, v_w], axis=1).fillna(0)
    if len(merged) < 5:
        return 0.0, len(merged)
    corr = merged['mech'].corr(merged['v3d'])
    return float(corr), len(merged)


def sizing_scenarios(mech_df, v3d_df):
    """Combina sob diferentes pesos."""
    scenarios = {}
    for w_mech, w_v3d in [(1.0, 0.0), (0.0, 1.0), (0.5, 0.5),
                          (0.7, 0.3), (0.3, 0.7)]:
        m = mech_df.copy()
        v = v3d_df.copy()
        m['r_weighted'] = m['r_net'] * w_mech
        v['r_weighted'] = v['r_net'] * w_v3d
        combined = pd.concat([m[['entry_time', 'r_weighted']],
                              v[['entry_time', 'r_weighted']]])
        combined = combined.sort_values('entry_time').reset_index(drop=True)
        combined['cum_r'] = combined['r_weighted'].cumsum()
        peaks = np.maximum.accumulate(combined['cum_r'].values)
        dd = (combined['cum_r'].values - peaks).min()
        total = combined['r_weighted'].sum()
        # Recovery factor
        rf = total / abs(dd) if dd < 0 else float('inf')
        scenarios[f'mech{int(w_mech*100)}/v3d{int(w_v3d*100)}'] = {
            'total_r': round(total, 2),
            'max_dd': round(float(dd), 2),
            'recovery_factor': round(rf, 2) if rf != float('inf') else 999,
            'n_trades': len(combined),
        }
    return scenarios


def main():
    print("=== Loading mech (R_full_trend_regime) ===")
    mech = get_mech_trades()
    print(f"  {len(mech)} trades")

    print("=== Loading V3d best (struct buf=0% BE@2R tgt5R) ===")
    v3d = get_v3d_trades()
    print(f"  {len(v3d)} trades")

    # Combine (no dedup needed — overlap is minimal as we showed)
    combined = pd.concat([mech, v3d]).sort_values('entry_time').reset_index(drop=True)

    print("\n=== EQUITY METRICS ===")
    eq_m = equity_curve(mech)
    eq_v = equity_curve(v3d)
    eq_c = equity_curve(combined)

    dd_m, _ = max_drawdown(eq_m)
    dd_v, _ = max_drawdown(eq_v)
    dd_c, _ = max_drawdown(eq_c)

    rows = []
    for label, df, dd in [('MECH solo', mech, dd_m), ('V3D solo', v3d, dd_v),
                           ('COMBINADO', combined, dd_c)]:
        total = df['r_net'].sum()
        rf = total / abs(dd) if dd < 0 else float('inf')
        sh = sharpe_annualized(df)
        so = sortino_annualized(df)
        wr = (df['r_net'] > 0).mean()
        rows.append({
            'portfolio': label,
            'n': len(df),
            'total_r': round(total, 2),
            'win_rate': round(wr, 3),
            'max_dd': round(dd, 2),
            'recovery_factor': round(rf, 2) if rf != float('inf') else 999,
            'sharpe_annual': round(sh, 2),
            'sortino_annual': round(so, 2) if so != float('inf') else 999,
        })
    summary = pd.DataFrame(rows)
    print(summary.to_string(index=False))

    print("\n=== CORRELACAO ===")
    corr, n_w = yearly_correlation(mech, v3d)
    print(f"  Pearson r (R semanal): {corr:.3f}  (n_weeks={n_w})")
    if abs(corr) < 0.2:
        diversif = "BAIXA correlacao -> diversificacao real"
    elif abs(corr) < 0.5:
        diversif = "MEDIA correlacao -> diversificacao parcial"
    else:
        diversif = "ALTA correlacao -> redundancia"
    print(f"  Diagnostico: {diversif}")

    print("\n=== SIZING SCENARIOS ===")
    scen = sizing_scenarios(mech, v3d)
    sd = pd.DataFrame(scen).T
    print(sd.to_string())

    print("\n=== YEARLY BREAKDOWN ===")
    yearly_m = yearly_breakdown(mech)
    yearly_v = yearly_breakdown(v3d)
    yearly_m.columns = [f"mech_{c}" for c in yearly_m.columns]
    yearly_v.columns = [f"v3d_{c}" for c in yearly_v.columns]
    yearly = yearly_m.join(yearly_v, how='outer').fillna(0)
    print(yearly.to_string())

    # Detect anos onde v3d "salva" o mech
    print("\n=== ANOS ONDE V3D COMPLEMENTA MECH ===")
    if 'mech_total_r' in yearly.columns and 'v3d_total_r' in yearly.columns:
        yearly['mech_alone'] = yearly['mech_total_r']
        yearly['combined'] = yearly['mech_total_r'] + yearly['v3d_total_r']
        yearly['v3d_helped'] = yearly['v3d_total_r'] > 0
        yearly['mech_struggling'] = yearly['mech_total_r'] < 5
        flagged = yearly[(yearly['v3d_helped']) & (yearly['mech_struggling'])]
        if len(flagged) > 0:
            print("  Anos onde V3D adicionou enquanto mech estava fraco:")
            print(flagged[['mech_total_r', 'v3d_total_r']].to_string())
        else:
            print("  Nenhum ano com esse padrao claro (V3D bom + mech fraco simultaneo)")

    summary.to_csv(DIR / 'portfolio_metrics_mech_v3d.csv', index=False)
    sd.to_csv(DIR / 'portfolio_sizing_scenarios.csv')
    yearly.to_csv(DIR / 'portfolio_yearly_breakdown.csv')
    print("\nSalvos: portfolio_metrics_mech_v3d.csv, portfolio_sizing_scenarios.csv, portfolio_yearly_breakdown.csv")


if __name__ == '__main__':
    main()
