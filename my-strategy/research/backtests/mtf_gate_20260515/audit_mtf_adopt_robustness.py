#!/usr/bin/env python3
"""MTF1 follow-up: análise outlier anual + cross-check D2R live nos cells ADOPT.

Cells ADOPT do audit_mtf_gate.py:
  XAUUSD 15M (HTF=1H)
  EURUSD 30M (HTF=4H)
  EURUSD 1H  (HTF=4H)
  US500  1H  (HTF=4H)
  BTCUSD 4H  (HTF=1D)
  BTCUSD 15M (HTF=1H)
"""
import sys
import json
import math
from pathlib import Path
from datetime import datetime, timezone
import numpy as np
import pandas as pd

DIR = Path(__file__).parent
sys.path.insert(0, str(DIR))
from audit_mtf_gate import (
    load_csv, trigger_long, simulate, htf_bos_check, find_csv,
    HTF_MAP, SPREAD_R, TARGET_R, STOP_ATR_MULT, ATR_R_CAP, HTF_LOOKBACK
)
sys.path.insert(0, str(DIR.parent / 'xauusd_audit_20260512'))
from audit_xau_smc_v3 import detect_pivots, track_structure, PIVOT_LEN

ADOPT_CELLS = [
    ('XAUUSD', '15M'),
    ('EURUSD', '30M'),
    ('EURUSD', '1H'),
    ('US500',  '1H'),
    ('BTCUSD', '4H'),
    ('BTCUSD', '15M'),
]

RESEARCH_LOG = '/Users/cristrein/tradingview-mcp/alert-bridge/logs/setup_research_log.jsonl'
R_OUTCOME_LOG = '/Users/cristrein/tradingview-mcp/alert-bridge/logs/setup_r_outcome_log.jsonl'


def cohort_metrics(values):
    if len(values) == 0:
        return {'n': 0, 'total': 0, 'win': 0, 'pf': 0, 'sharpe': 0}
    r = np.array(values)
    wins = r[r > 0].sum()
    losses = -r[r < 0].sum()
    pf = wins / losses if losses > 0 else float('inf')
    avg = r.mean()
    std = r.std(ddof=1) if len(r) > 1 else 0
    sharpe = (avg / std * math.sqrt(len(r))) if std > 0 else 0
    return {'n': len(r), 'total': float(r.sum()),
            'win': float((r > 0).mean() * 100),
            'pf': float(pf) if pf != float('inf') else 999.0,
            'sharpe': float(sharpe)}


def backtest_cell(asset, ltf):
    htf = HTF_MAP[ltf]
    ltf_path = find_csv(asset, ltf)
    htf_path = find_csv(asset, htf)
    df_ltf = load_csv(ltf_path)
    df_htf = load_csv(htf_path)
    ph, pl = detect_pivots(df_htf, PIVOT_LEN)
    htf_events = track_structure(df_htf, ph, pl)
    trades = []
    for i in range(11, len(df_ltf)):
        if not trigger_long(df_ltf, i):
            continue
        atr_e = df_ltf.at[i, 'atr14']
        if pd.isna(atr_e) or atr_e <= 0:
            continue
        low_bar = df_ltf.at[i, 'low']
        stop = low_bar - STOP_ATR_MULT * atr_e
        entry = df_ltf.at[i, 'close']
        R = entry - stop
        if R <= 0 or R > ATR_R_CAP * atr_e:
            continue
        res = simulate(df_ltf, i, entry, stop, TARGET_R)
        if res is None:
            continue
        aligned = htf_bos_check(htf_events, df_ltf.at[i, 'time'], df_htf, HTF_LOOKBACK)
        trades.append({
            'time': df_ltf.at[i, 'time'],
            'r': float(res['r']) - SPREAD_R,
            'aligned': bool(aligned),
            'year': int(df_ltf.at[i, 'year']),
        })
    return pd.DataFrame(trades), htf_events, df_htf


def yearly_outliers(df):
    if len(df) < 3:
        return df.assign(z=0.0, is_outlier=False), []
    rows = []
    for yr, g in df.groupby('year'):
        m = cohort_metrics(g['r'].values)
        rows.append({'year': int(yr), **m})
    ydf = pd.DataFrame(rows).sort_values('year').reset_index(drop=True)
    mu, sigma = ydf['total'].mean(), ydf['total'].std(ddof=1)
    if sigma == 0:
        return ydf.assign(z=0.0, is_outlier=False), []
    ydf['z'] = (ydf['total'] - mu) / sigma
    ydf['is_outlier'] = ydf['z'].abs() > 1.5
    out = ydf[ydf['is_outlier']]['year'].astype(int).tolist()
    return ydf, out


def analyze_robust(asset, ltf):
    print(f"\n{'='*80}\n{asset} {ltf} (HTF={HTF_MAP[ltf]}) — outlier analysis")
    print('='*80)
    df_tr, _, _ = backtest_cell(asset, ltf)
    aligned_df = df_tr[df_tr['aligned']]
    if len(aligned_df) == 0:
        print("  Sem aligned trades")
        return None

    overall = cohort_metrics(aligned_df['r'].values)
    print(f"OVERALL aligned: n={overall['n']} | total={overall['total']:+.2f}R | "
          f"PF={overall['pf']:.2f} | win={overall['win']:.1f}% | Sharpe={overall['sharpe']:+.2f}")

    ydf, outliers = yearly_outliers(aligned_df)
    print(f"\nYearly breakdown:")
    print(ydf.to_string(index=False, float_format='%.2f'))

    if outliers:
        print(f"\n⚠️  Outliers: {outliers}")
        clean = aligned_df[~aligned_df['year'].isin(outliers)]
        clean_m = cohort_metrics(clean['r'].values)
        print(f"\nSEM outliers: n={clean_m['n']} | total={clean_m['total']:+.2f}R | "
              f"PF={clean_m['pf']:.2f} | win={clean_m['win']:.1f}% | Sharpe={clean_m['sharpe']:+.2f}")
        return {'cell': f'{asset} {ltf}', 'overall': overall, 'clean': clean_m,
                'outliers': outliers}
    else:
        print("\n✅ Nenhum outlier — amostra robusta")
        return {'cell': f'{asset} {ltf}', 'overall': overall, 'clean': overall, 'outliers': []}


# ============================================================================
# D2R LIVE CROSS-CHECK
# ============================================================================

def load_research_index():
    """event_id -> {symbol, tf, classification, ts}"""
    idx = {}
    with open(RESEARCH_LOG) as f:
        for ln in f:
            try:
                d = json.loads(ln)
                eid = d.get('event_id')
                if not eid:
                    continue
                cls = d.get('classification', '')
                if cls in ('SETUP_CANDIDATO_FORTE', 'SETUP_EM_OBSERVACAO'):
                    idx[eid] = {
                        'symbol': d.get('base_symbol', '?'),
                        'tf': d.get('timeframe', '?'),
                        'cls': cls,
                        'ts': d.get('evaluated_at', d.get('received_at', '')),
                    }
            except: pass
    return idx


def load_d2r():
    out = []
    with open(R_OUTCOME_LOG) as f:
        for ln in f:
            try:
                d = json.loads(ln)
                eid = d.get('event_id')
                if not eid:
                    continue
                out.append({
                    'event_id': eid,
                    'r': d.get('theoretical_r_outcome'),
                    'tradeable': d.get('would_have_been_tradeable'),
                    'symbol': d.get('symbol', ''),
                    'tf': str(d.get('timeframe', '')),
                })
            except: pass
    return out


def cross_check_d2r(adopt_cells):
    """Para cada cell ADOPT, cruzar D2R live com HTF gate check."""
    print(f"\n\n{'='*80}\nD2R LIVE CROSS-CHECK\n{'='*80}")

    research_idx = load_research_index()
    d2r = load_d2r()
    print(f"Research records (CANDIDATO_FORTE+OBSERVACAO): {len(research_idx)}")
    print(f"D2R outcomes total: {len(d2r)}")

    # Build cell match list
    tf_codes = {'15M':'15', '30M':'30', '1H':'60', '4H':'240'}
    cell_filter = {(asset, tf_codes[ltf]): (asset, ltf) for asset, ltf in adopt_cells}

    matched_records = []
    for rec in d2r:
        sym = rec['symbol'].replace('PEPPERSTONE:', '')
        tf = rec['tf']
        key = (sym, tf)
        if key in cell_filter:
            asset, ltf = cell_filter[key]
            matched_records.append({**rec, 'asset': asset, 'ltf': ltf})

    print(f"D2R records em cells ADOPT: {len(matched_records)}\n")

    if not matched_records:
        print("⚠️  Nenhum D2R record em cells ADOPT — aguardar acumulação")
        return

    # Para cada matched record, aplicar HTF gate retroativo
    cell_cache = {}  # (asset, ltf) -> (htf_events, df_htf)
    results_by_cell = {}

    for rec in matched_records:
        asset, ltf = rec['asset'], rec['ltf']
        htf = HTF_MAP[ltf]
        cache_key = (asset, htf)
        if cache_key not in cell_cache:
            htf_path = find_csv(asset, htf)
            if not htf_path:
                continue
            df_htf = load_csv(htf_path)
            ph, pl = detect_pivots(df_htf, PIVOT_LEN)
            htf_events = track_structure(df_htf, ph, pl)
            cell_cache[cache_key] = (htf_events, df_htf)
        htf_events, df_htf = cell_cache[cache_key]

        ts = rec['event_id'].split('_')[0]
        try:
            event_dt = pd.to_datetime(ts)
        except:
            continue
        if event_dt.tzinfo is None:
            event_dt = event_dt.tz_localize('UTC')

        aligned = htf_bos_check(htf_events, event_dt, df_htf, HTF_LOOKBACK)

        cell_key = f'{asset} {ltf}'
        results_by_cell.setdefault(cell_key, []).append({
            'r': rec['r'],
            'aligned': aligned,
            'tradeable': rec['tradeable'],
        })

    # Report per cell
    print(f"{'Cell':<15} | {'n':>4} | {'aligned/misaligned':>20} | {'Aligned r':>18} | {'Misaligned r':>18}")
    print('-'*90)
    for cell, recs in results_by_cell.items():
        n_total = len(recs)
        aligned_rs = [r['r'] for r in recs if r['aligned'] and r['r'] is not None]
        mis_rs = [r['r'] for r in recs if not r['aligned'] and r['r'] is not None]
        a_str = (f"{len(aligned_rs)} | avg={np.mean(aligned_rs):+.2f}R | win={sum(1 for r in aligned_rs if r>0)/max(len(aligned_rs),1)*100:.0f}%"
                 if aligned_rs else "0 (no data)")
        m_str = (f"{len(mis_rs)} | avg={np.mean(mis_rs):+.2f}R | win={sum(1 for r in mis_rs if r>0)/max(len(mis_rs),1)*100:.0f}%"
                 if mis_rs else "0 (no data)")
        align_count = sum(1 for r in recs if r['aligned'])
        print(f"{cell:<15} | {n_total:>4} | {f'{align_count}/{n_total-align_count}':>20} | {a_str:>18} | {m_str:>18}")


def main():
    print("="*80)
    print("MTF1 ROBUSTNESS — outlier + D2R cross-check")
    print("="*80)
    results = []
    for asset, ltf in ADOPT_CELLS:
        r = analyze_robust(asset, ltf)
        if r:
            results.append(r)

    # Summary
    print(f"\n\n{'='*80}\nROBUSTNESS SUMMARY (com vs sem outlier)\n{'='*80}")
    print(f"{'Cell':<15} | {'Overall':>30} | {'Sem outlier':>30} | {'Outliers':>15}")
    for r in results:
        o = r['overall']; c = r['clean']
        o_str = f"n={o['n']:>3} R={o['total']:>+5.1f} PF={o['pf']:>4.2f} S={o['sharpe']:>+4.2f}"
        c_str = f"n={c['n']:>3} R={c['total']:>+5.1f} PF={c['pf']:>4.2f} S={c['sharpe']:>+4.2f}"
        out = ','.join(map(str, r['outliers'])) if r['outliers'] else '—'
        print(f"{r['cell']:<15} | {o_str:>30} | {c_str:>30} | {out:>15}")

    # D2R cross check
    cross_check_d2r(ADOPT_CELLS)

    # Save
    with open(DIR / 'mtf_adopt_robustness.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)


if __name__ == '__main__':
    main()
