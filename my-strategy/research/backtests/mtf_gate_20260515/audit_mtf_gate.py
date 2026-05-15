#!/usr/bin/env python3
"""MTF1 — Multi-TF gate audit.

Para cada trade gerado em LTF, verificar se HTF teve BOS_BULL ou CHOCH_BULL
nos ultimos 6 candles. Comparar cohorts aligned vs misaligned.

Triggers:
- 4H/1H: kit padrao + filtros tipo modulos mecanicos (close>swhi10 + body 60% +
         RSI>MA + EMA stack + ATR expanding + ADX 20)
- 30M/15M: trigger generico (mesmo kit, simplificado)

HTF gate:
- 4H trigger -> HTF=1D
- 1H trigger -> HTF=4H
- 30M trigger -> HTF=4H
- 15M trigger -> HTF=1H

Outputs: por cell (asset, TF), distribuicao aligned/misaligned + PF/Sharpe/win
+ analise outlier anual.
"""
import sys
import math
import json
from pathlib import Path
import numpy as np
import pandas as pd

DIR = Path(__file__).parent
XAU_DIR = DIR.parent / 'xauusd_audit_20260512'
sys.path.insert(0, str(XAU_DIR))
from audit_xau_smc_v3 import detect_pivots, track_structure, PIVOT_LEN

SPREAD_R = 0.05
MAX_HOLD_BARS = 24
HTF_LOOKBACK = 6   # how many HTF bars back BOS/CHOCH must have occurred

CSV_BASE = '/Users/cristrein/Downloads/PEPPERSTONE_{asset}, {tf}_{hash}.csv'

# Discovered file hashes (per asset-tf)
FILES = {
    'XAUUSD': {'15M':'24384','30M':'7ea8c','1H':'309fa','4H':'aea76','1D':'7f278'},
    'EURUSD': {'15M':'c43cf','30M':'2e138','1H':'2e3eb','4H':'28fd2','1D':'1ec8f'},
    'ETHUSD': {'15M':None,  '30M':None,  '1H':'e89c2','4H':'cbbf3','1D':None},
    'US500':  {'15M':None,  '30M':None,  '1H':'9097c','4H':'c18d8','1D':None},
    'XAGUSD': {'15M':'be865','30M':'0c1bf','1H':'1a0a1','4H':'47164','1D':'4b306'},
    'BTCUSD': {'15M':'797ea','30M':'490ce','1H':'807e4','4H':'cfb3e','1D':'dfd6b'},
    'XPTUSD': {'15M':'ae49d','30M':'6f0cd','1H':'5be86','4H':'d0ab6','1D':'21321'},
}

# HTF map
HTF_MAP = {'15M':'1H', '30M':'4H', '1H':'4H', '4H':'1D'}

# Default target/stop config
TARGET_R = 2.5
STOP_ATR_MULT = 0.5
ATR_R_CAP = 5.0


def find_csv(asset, tf):
    h = FILES.get(asset, {}).get(tf)
    if not h:
        return None
    # discover real filename pattern
    tf_map = {'15M':'15', '30M':'30', '1H':'60', '4H':'240', '1D':'1D', '12H':'720'}
    code = tf_map[tf]
    import glob
    pattern = f'/Users/cristrein/Downloads/PEPPERSTONE_{asset}, {code}_*.csv'
    matches = glob.glob(pattern)
    if matches:
        return matches[0]
    return None


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
    df['atr_ma20'] = df['atr14'].rolling(20, min_periods=1).mean()
    df['atr_expanding'] = df['atr14'] > df['atr_ma20']
    # EMAs
    df['ema50'] = df['close'].ewm(span=50, adjust=False).mean()
    df['ema200'] = df['close'].ewm(span=200, adjust=False).mean()
    # Swing high 10
    df['swhi_10'] = df['high'].rolling(10, min_periods=1).max().shift(1)
    # Body pct
    df['body_pct'] = (df['close'] - df['open']).abs() / (df['high'] - df['low']).replace(0, np.nan)
    # RSI + MA
    delta = df['close'].diff()
    gain = delta.where(delta > 0, 0).ewm(alpha=1/14, adjust=False).mean()
    loss = (-delta.where(delta < 0, 0)).ewm(alpha=1/14, adjust=False).mean()
    rs = gain / loss.replace(0, np.nan)
    df['rsi14'] = 100 - 100 / (1 + rs)
    df['rsi_ma'] = df['rsi14'].ewm(span=14, adjust=False).mean()
    # ADX
    up = df['high'].diff()
    dn = -df['low'].diff()
    pdm = np.where((up > dn) & (up > 0), up, 0)
    ndm = np.where((dn > up) & (dn > 0), dn, 0)
    pdi = 100 * pd.Series(pdm, index=df.index).ewm(alpha=1/14, adjust=False).mean() / df['atr14']
    ndi = 100 * pd.Series(ndm, index=df.index).ewm(alpha=1/14, adjust=False).mean() / df['atr14']
    dx = 100 * (pdi - ndi).abs() / (pdi + ndi).replace(0, np.nan)
    df['adx14'] = dx.ewm(alpha=1/14, adjust=False).mean()
    df['year'] = df['time'].dt.year
    return df


def trigger_long(df, i):
    """Generic LONG trigger — kit padrão dos módulos."""
    if i < 11:
        return False
    row = df.iloc[i]
    if pd.isna(row['close']) or pd.isna(row['open']):
        return False
    if not (row['close'] > row['open']):
        return False
    if not (row['close'] > df.at[i-1, 'swhi_10']):
        return False
    if pd.isna(row['body_pct']) or row['body_pct'] < 0.6:
        return False
    if pd.isna(row['rsi14']) or pd.isna(row['rsi_ma']) or row['rsi14'] <= row['rsi_ma']:
        return False
    if pd.isna(row['ema50']) or pd.isna(row['ema200']):
        return False
    if not (row['close'] > row['ema200'] and row['ema50'] > row['ema200']):
        return False
    if pd.isna(row['atr14']) or not row['atr_expanding']:
        return False
    if pd.isna(row['adx14']) or row['adx14'] < 20:
        return False
    return True


def simulate(df, entry_idx, entry, stop, target_r, max_bars=MAX_HOLD_BARS):
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
    for j in range(entry_idx + 1, min(entry_idx + 1 + max_bars, n)):
        h, l = high[j], low[j]
        if not moved_be and h >= entry + R:
            cur_stop = max(cur_stop, entry)
            moved_be = True
        if l <= cur_stop:
            return {'exit_idx': j, 'r': (cur_stop - entry) / R}
        if h >= target:
            return {'exit_idx': j, 'r': target_r}
    last = min(entry_idx + max_bars, n - 1)
    return {'exit_idx': last, 'r': (close[last] - entry) / R}


def htf_bos_check(htf_events, ltf_entry_time, htf_df, lookback=HTF_LOOKBACK):
    """Verifica se HTF teve BOS_BULL ou CHOCH_BULL nos ultimos `lookback` candles
    HTF antes de ltf_entry_time."""
    # encontrar idx HTF imediatamente antes ltf_entry_time
    htf_times = htf_df['time'].values
    pos = np.searchsorted(htf_times, np.datetime64(ltf_entry_time))
    if pos == 0:
        return False
    htf_end_idx = pos - 1
    htf_start_idx = max(0, htf_end_idx - lookback + 1)
    # checar events nessa janela
    for ev in htf_events:
        if ev['type'] in ('BOS_BULL', 'CHOCH_BULL'):
            if htf_start_idx <= ev['idx'] <= htf_end_idx:
                return True
    return False


def run_cell(asset, ltf, ltf_path, htf, htf_path):
    print(f"\n--- {asset} {ltf} (HTF={htf}) ---")
    df_ltf = load_csv(ltf_path)
    df_htf = load_csv(htf_path)
    # Detect HTF structural events
    ph, pl = detect_pivots(df_htf, PIVOT_LEN)
    htf_events = track_structure(df_htf, ph, pl)
    n_ltf = len(df_ltf)
    print(f"  LTF bars: {n_ltf}, HTF bars: {len(df_htf)}, HTF bull events: "
          f"{sum(1 for e in htf_events if e['type'] in ('BOS_BULL','CHOCH_BULL'))}")

    trades = []
    for i in range(11, n_ltf):
        if not trigger_long(df_ltf, i):
            continue
        atr_e = df_ltf.at[i, 'atr14']
        if pd.isna(atr_e) or atr_e <= 0:
            continue
        # Stop = low_signal_bar - 0.5*ATR
        low_bar = df_ltf.at[i, 'low']
        stop = low_bar - STOP_ATR_MULT * atr_e
        entry = df_ltf.at[i, 'close']
        R = entry - stop
        if R <= 0 or R > ATR_R_CAP * atr_e:
            continue
        res = simulate(df_ltf, i, entry, stop, TARGET_R)
        if res is None:
            continue
        entry_time = df_ltf.at[i, 'time']
        aligned = htf_bos_check(htf_events, entry_time, df_htf, HTF_LOOKBACK)
        trades.append({
            'entry_time': entry_time,
            'r': float(res['r']) - SPREAD_R,
            'aligned': bool(aligned),
            'year': int(df_ltf.at[i, 'year']),
        })

    df_tr = pd.DataFrame(trades)
    if len(df_tr) == 0:
        print("  ⚠️  Sem trades")
        return None
    print(f"  Total trades: {len(df_tr)} | aligned: {df_tr['aligned'].sum()} ({df_tr['aligned'].mean()*100:.1f}%)")
    return df_tr


def cohort_metrics(df, col='r'):
    if len(df) == 0:
        return {'n': 0, 'total': 0, 'win_pct': 0, 'pf': 0, 'avg': 0, 'sharpe': 0}
    r = df[col].values
    wins = r[r > 0].sum()
    losses = -r[r < 0].sum()
    pf = wins / losses if losses > 0 else float('inf')
    avg = r.mean()
    std = r.std(ddof=1) if len(r) > 1 else 0
    sharpe = (avg / std * math.sqrt(len(r))) if std > 0 else 0
    eq = np.cumsum(r)
    peak = np.maximum.accumulate(eq)
    dd = (eq - peak).min()
    return {'n': len(r), 'total': float(r.sum()),
            'win_pct': float((r > 0).mean() * 100),
            'pf': float(pf) if pf != float('inf') else 999.0,
            'avg': float(avg), 'sharpe': float(sharpe), 'max_dd': float(dd)}


def yearly_outliers(df, col='r'):
    if len(df) == 0:
        return None, []
    rows = []
    for yr, g in df.groupby('year'):
        m = cohort_metrics(g, col)
        rows.append({'year': int(yr), **m})
    ydf = pd.DataFrame(rows).sort_values('year').reset_index(drop=True)
    if len(ydf) < 3:
        return ydf, []
    mu, sigma = ydf['total'].mean(), ydf['total'].std(ddof=1)
    if sigma == 0:
        return ydf, []
    ydf['z'] = (ydf['total'] - mu) / sigma
    out = ydf[ydf['z'].abs() > 1.5]['year'].astype(int).tolist()
    return ydf, out


def main():
    print("="*80)
    print("MTF1 — Multi-TF gate (BOS/CHOCH HTF nos últimos 6 candles)")
    print("Trigger LONG genérico | target 2.5R | stop low-0.5ATR | spread 0.05R")
    print("="*80)

    all_results = []
    for asset in FILES:
        for ltf in ['15M', '30M', '1H', '4H']:
            htf = HTF_MAP[ltf]
            ltf_path = find_csv(asset, ltf)
            htf_path = find_csv(asset, htf)
            if not ltf_path or not htf_path:
                continue
            try:
                df_tr = run_cell(asset, ltf, ltf_path, htf, htf_path)
                if df_tr is None or len(df_tr) < 10:
                    continue
                aligned_m = cohort_metrics(df_tr[df_tr['aligned']])
                misaligned_m = cohort_metrics(df_tr[~df_tr['aligned']])
                all_m = cohort_metrics(df_tr)
                # outliers
                _, outl_aligned = yearly_outliers(df_tr[df_tr['aligned']])
                # Cohort sem outlier
                df_aligned_clean = df_tr[(df_tr['aligned']) & (~df_tr['year'].isin(outl_aligned))]
                clean_m = cohort_metrics(df_aligned_clean) if len(df_aligned_clean) > 0 else None
                all_results.append({
                    'asset': asset, 'ltf': ltf, 'htf': htf,
                    'all': all_m, 'aligned': aligned_m, 'misaligned': misaligned_m,
                    'aligned_outliers': outl_aligned,
                    'aligned_clean': clean_m,
                })
            except Exception as e:
                print(f"  ERRO: {e}")

    # Summary table
    print(f"\n\n{'='*100}")
    print("SUMÁRIO MULTI-TF GATE — todos os cells")
    print('='*100)
    print(f"{'Cell':<15} | {'All n':>6} | {'Aligned':>22} | {'Misaligned':>22} | {'Verdict':<18}")
    print(f"{'':15} | {'':>6} | {'n   PF   Sharpe   total':>22} | {'n   PF   Sharpe   total':>22} |")
    print('-'*100)
    for r in all_results:
        a = r['aligned']; m = r['misaligned']
        a_str = f"{a['n']:>3} {a['pf']:>4.2f} {a['sharpe']:>+5.2f} {a['total']:>+6.1f}"
        m_str = f"{m['n']:>3} {m['pf']:>4.2f} {m['sharpe']:>+5.2f} {m['total']:>+6.1f}"
        # Verdict
        if a['n'] < 10 or m['n'] < 10:
            v = 'SMALL_N'
        elif a['sharpe'] >= m['sharpe'] + 0.5 and a['pf'] >= m['pf'] + 0.3:
            v = '✅ ADOPT'
        elif a['sharpe'] >= m['sharpe'] + 0.2:
            v = '🟡 marginal'
        elif a['sharpe'] < m['sharpe'] - 0.2:
            v = '❌ HURTS'
        else:
            v = '— neutral'
        cell = f"{r['asset']} {r['ltf']}"
        print(f"{cell:<15} | {r['all']['n']:>6} | {a_str:>22} | {m_str:>22} | {v:<18}")

    # Save full results
    out_path = DIR / 'mtf_gate_results.json'
    with open(out_path, 'w') as f:
        json.dump(all_results, f, indent=2, default=str)
    print(f"\n✅ Resultados salvos em {out_path}")


if __name__ == '__main__':
    main()
