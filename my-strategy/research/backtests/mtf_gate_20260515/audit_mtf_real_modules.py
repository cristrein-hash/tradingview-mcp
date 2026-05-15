#!/usr/bin/env python3
"""MTF gate em MÓDULOS MECÂNICOS REAIS (n confere com strategy_rules).

Fase 1 — 4 módulos com CSV de trades existente e n batendo:
  XAU 4H BREAKOUT_CONTINUATION_REGIME_FILTERED (n=234)
  EUR 4H BREAKOUT_COMBO_STRICT_DXY            (n=47)
  EUR 1H DECISIVE_HTF1D_DXY                   (n=73)
  ETH 1H PULLBACK_EMA50_REGIME                (n=96)

Pra cada trade, verificar se HTF teve BOS_BULL/CHOCH_BULL nos últimos 6 candles.
Comparar cohort aligned vs misaligned + outlier anual.
"""
import sys
import json
import math
from pathlib import Path
import numpy as np
import pandas as pd

DIR = Path(__file__).parent
sys.path.insert(0, str(DIR))
from audit_mtf_gate import load_csv, find_csv, HTF_MAP, HTF_LOOKBACK, SPREAD_R
sys.path.insert(0, str(DIR.parent / 'xauusd_audit_20260512'))
from audit_xau_smc_v3 import detect_pivots, track_structure, PIVOT_LEN

# Module → (CSV trade path, asset, LTF code → HTF tf)
MODULES = [
    {
        'name': 'XAUUSD_4H_BREAKOUT_CONTINUATION_REGIME_FILTERED',
        'csv': '/Users/cristrein/tradingview-mcp/my-strategy/research/backtests/xauusd_audit_20260512/XAUUSD_4H_mechanic_R_full_trades.csv',
        'asset': 'XAUUSD',
        'ltf_label': '4H',
        'expected_n': 234,
    },
    {
        'name': 'EURUSD_4H_BREAKOUT_COMBO_STRICT_DXY',
        'csv': '/Users/cristrein/tradingview-mcp/my-strategy/research/backtests/eurusd_audit_20260512/EURUSD_V2_best_swing_trades.csv',
        'asset': 'EURUSD',
        'ltf_label': '4H',
        'expected_n': 47,
    },
    {
        'name': 'EURUSD_1H_DECISIVE_HTF1D_DXY',
        'csv': '/Users/cristrein/tradingview-mcp/my-strategy/research/backtests/eurusd_audit_20260512/EURUSD_V2_best_intraday_trades.csv',
        'asset': 'EURUSD',
        'ltf_label': '1H',
        'expected_n': 73,
    },
    {
        'name': 'ETHUSD_1H_PULLBACK_EMA50_REGIME',
        'csv': '/Users/cristrein/tradingview-mcp/my-strategy/research/backtests/ethusd_audit_20260512/ETHUSD_proposal_top_intraday_trades.csv',
        'asset': 'ETHUSD',
        'ltf_label': '1H',
        'expected_n': 96,
    },
]


def cohort_metrics(values):
    if len(values) == 0:
        return {'n': 0, 'total': 0, 'win': 0, 'pf': 0, 'sharpe': 0, 'max_dd': 0}
    r = np.array(values)
    wins = r[r > 0].sum()
    losses = -r[r < 0].sum()
    pf = wins / losses if losses > 0 else float('inf')
    avg = r.mean()
    std = r.std(ddof=1) if len(r) > 1 else 0
    sharpe = (avg / std * math.sqrt(len(r))) if std > 0 else 0
    eq = np.cumsum(r)
    peak = np.maximum.accumulate(eq)
    dd = float((eq - peak).min())
    return {'n': len(r), 'total': float(r.sum()),
            'win': float((r > 0).mean() * 100),
            'pf': float(pf) if pf != float('inf') else 999.0,
            'sharpe': float(sharpe), 'max_dd': dd}


def htf_bos_check(htf_events, ltf_entry_time, htf_df, lookback=HTF_LOOKBACK):
    """Verifica BOS_BULL/CHOCH_BULL nos últimos `lookback` candles HTF antes de entry."""
    ltf_ts = pd.to_datetime(ltf_entry_time)
    if ltf_ts.tzinfo is not None:
        ltf_ts = ltf_ts.tz_localize(None)
    htf_times = pd.to_datetime(htf_df['time'])
    if htf_times.iloc[0].tzinfo is not None:
        htf_times = htf_times.dt.tz_localize(None)
    pos = htf_times.searchsorted(ltf_ts, side='left')
    if pos == 0:
        return False
    htf_end_idx = pos - 1
    htf_start_idx = max(0, htf_end_idx - lookback + 1)
    for ev in htf_events:
        if ev['type'] in ('BOS_BULL', 'CHOCH_BULL'):
            if htf_start_idx <= ev['idx'] <= htf_end_idx:
                return True
    return False


def yearly_outliers(df):
    if len(df) < 3:
        return df.assign(z=0.0, is_outlier=False), []
    rows = []
    for yr, g in df.groupby('year'):
        m = cohort_metrics(g['r_net'].values)
        rows.append({'year': int(yr), **m})
    ydf = pd.DataFrame(rows).sort_values('year').reset_index(drop=True)
    mu, sigma = ydf['total'].mean(), ydf['total'].std(ddof=1)
    if sigma == 0:
        return ydf.assign(z=0.0, is_outlier=False), []
    ydf['z'] = (ydf['total'] - mu) / sigma
    ydf['is_outlier'] = ydf['z'].abs() > 1.5
    out = ydf[ydf['is_outlier']]['year'].astype(int).tolist()
    return ydf, out


def analyze_module(mod, htf_cache):
    print(f"\n{'='*80}\n{mod['name']}\n{'='*80}")
    df_t = pd.read_csv(mod['csv'])
    print(f"Trades loaded: {len(df_t)} (esperado: {mod['expected_n']})")
    if 'r_outcome' not in df_t.columns or 'entry_time' not in df_t.columns:
        print(f"  ⚠️  Colunas missing")
        return None
    df_t['r_net'] = df_t['r_outcome'].astype(float) - SPREAD_R
    df_t['entry_time'] = pd.to_datetime(df_t['entry_time'])
    df_t['year'] = df_t['entry_time'].dt.year

    # HTF
    htf = HTF_MAP[mod['ltf_label']]
    cache_key = (mod['asset'], htf)
    if cache_key not in htf_cache:
        htf_path = find_csv(mod['asset'], htf)
        if not htf_path:
            print(f"  ❌ CSV {mod['asset']} {htf} não encontrado")
            return None
        df_htf = load_csv(htf_path)
        ph, pl = detect_pivots(df_htf, PIVOT_LEN)
        htf_events = track_structure(df_htf, ph, pl)
        htf_cache[cache_key] = (htf_events, df_htf)
    htf_events, df_htf = htf_cache[cache_key]
    print(f"  HTF={htf}, bull events: {sum(1 for e in htf_events if e['type'] in ('BOS_BULL','CHOCH_BULL'))}")

    # Aligned check
    df_t['aligned'] = df_t['entry_time'].apply(
        lambda t: htf_bos_check(htf_events, t, df_htf, HTF_LOOKBACK))
    n_aligned = int(df_t['aligned'].sum())
    print(f"  Aligned: {n_aligned}/{len(df_t)} ({n_aligned/len(df_t)*100:.1f}%)")

    # Cohorts
    a = cohort_metrics(df_t[df_t['aligned']]['r_net'].values)
    m = cohort_metrics(df_t[~df_t['aligned']]['r_net'].values)
    all_m = cohort_metrics(df_t['r_net'].values)
    print(f"\n  OVERALL:    n={all_m['n']:>3}  R={all_m['total']:>+7.2f}  PF={all_m['pf']:>4.2f}  win={all_m['win']:>5.1f}%  Sharpe={all_m['sharpe']:>+5.2f}  DD={all_m['max_dd']:>+6.2f}")
    print(f"  ALIGNED:    n={a['n']:>3}  R={a['total']:>+7.2f}  PF={a['pf']:>4.2f}  win={a['win']:>5.1f}%  Sharpe={a['sharpe']:>+5.2f}  DD={a['max_dd']:>+6.2f}")
    print(f"  MISALIGNED: n={m['n']:>3}  R={m['total']:>+7.2f}  PF={m['pf']:>4.2f}  win={m['win']:>5.1f}%  Sharpe={m['sharpe']:>+5.2f}  DD={m['max_dd']:>+6.2f}")

    # Verdict
    if a['n'] < 10:
        verdict = "SMALL_N (insuficiente)"
    elif a['sharpe'] >= m['sharpe'] + 0.5 and a['pf'] >= m['pf'] + 0.3:
        verdict = "✅ ADOPT FORTE"
    elif a['sharpe'] >= m['sharpe'] + 0.2:
        verdict = "🟡 marginal"
    elif a['sharpe'] < m['sharpe'] - 0.2:
        verdict = "❌ HURTS (não usar filtro aqui)"
    else:
        verdict = "— neutral"
    print(f"\n  VEREDITO: {verdict}")

    # Yearly outliers no aligned
    aligned_df = df_t[df_t['aligned']].copy()
    if len(aligned_df) >= 3:
        ydf, outliers = yearly_outliers(aligned_df)
        print(f"\n  Yearly aligned breakdown:")
        print(ydf.to_string(index=False, float_format='%.2f'))
        if outliers:
            clean = aligned_df[~aligned_df['year'].isin(outliers)]
            clean_m = cohort_metrics(clean['r_net'].values)
            print(f"\n  SEM outliers {outliers}: n={clean_m['n']} R={clean_m['total']:+.2f} "
                  f"PF={clean_m['pf']:.2f} Sharpe={clean_m['sharpe']:+.2f}")

    return {
        'name': mod['name'],
        'overall': all_m, 'aligned': a, 'misaligned': m,
        'verdict': verdict,
        'aligned_pct': float(n_aligned / len(df_t) * 100),
    }


def main():
    print("="*80)
    print("MTF Gate em MÓDULOS REAIS — 4 com CSV exato (Fase 1)")
    print(f"Gate: HTF BOS_BULL/CHOCH_BULL nos últimos {HTF_LOOKBACK} candles do HTF")
    print("="*80)

    htf_cache = {}
    results = []
    for mod in MODULES:
        r = analyze_module(mod, htf_cache)
        if r:
            results.append(r)

    # Summary table
    print(f"\n\n{'='*100}\nSUMMARY\n{'='*100}")
    print(f"{'Module':<48} | {'aligned%':>8} | {'Aligned':>30} | {'Misaligned':>30} | Verdict")
    print('-'*150)
    for r in results:
        a, m = r['aligned'], r['misaligned']
        a_str = f"n={a['n']:>3} R={a['total']:>+5.1f} PF={a['pf']:>4.2f} S={a['sharpe']:>+4.2f}"
        m_str = f"n={m['n']:>3} R={m['total']:>+5.1f} PF={m['pf']:>4.2f} S={m['sharpe']:>+4.2f}"
        print(f"{r['name']:<48} | {r['aligned_pct']:>7.1f}% | {a_str:>30} | {m_str:>30} | {r['verdict']}")

    with open(DIR / 'mtf_real_modules_results.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\n✅ Salvo em {DIR / 'mtf_real_modules_results.json'}")


if __name__ == '__main__':
    main()
