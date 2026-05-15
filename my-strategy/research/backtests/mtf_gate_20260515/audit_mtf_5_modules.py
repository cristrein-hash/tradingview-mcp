#!/usr/bin/env python3
"""MTF gate em 5 módulos restantes — config formal replicada inline.

Módulos:
  XAUUSD_1H_LONG_DECISIVE_BODY60_HTF (n_esperado=127)
  ETHUSD_4H_LONG_BREAKOUT_REGIME_FILTERED v1.2 (n_esperado=72, requer ETHBTC)
  US500_4H_LONG_FAILED_BREAKDOWN_REGIME (n_esperado=45, trigger sweep+reclaim)
  US500_1H_LONG_BREAKOUT_REGIME_FILTERED (n_esperado=222)
  XAGUSD_1H_LONG_DECISIVE_DXY_STRUCTURAL (n_esperado=69, requer DXY EMA200 4H)

Stop padrão: low_signal_bar - 0.5*ATR | Target 2.5R | BE@+1R | max 24 bars.
"""
import sys
import math
import json
import glob
from pathlib import Path
import numpy as np
import pandas as pd

DIR = Path(__file__).parent
sys.path.insert(0, str(DIR))
from audit_mtf_gate import load_csv as load_basic, find_csv, HTF_MAP, HTF_LOOKBACK, SPREAD_R
sys.path.insert(0, str(DIR.parent / 'xauusd_audit_20260512'))
from audit_xau_smc_v3 import detect_pivots, track_structure, PIVOT_LEN

TARGET_R_DEFAULT = 2.5
STOP_ATR_MULT = 0.5
ATR_R_CAP = 5.0
MAX_HOLD_BARS = 24


def load_full(path):
    """Load + add all indicators needed for various modules."""
    df = load_basic(path)
    # extras
    df['ema50_slope'] = df['ema50'] - df['ema50'].shift(5)
    df['close_above_ema200'] = df['close'] > df['ema200']
    df['ema50_above_ema200'] = df['ema50'] > df['ema200']
    # swing_low(20)
    df['swlo_20'] = df['low'].rolling(20, min_periods=1).min().shift(1)
    # range/ATR ratio
    df['range'] = df['high'] - df['low']
    df['range_x_atr'] = df['range'] / df['atr14']
    return df


def load_dxy():
    return load_basic('/Users/cristrein/Downloads/TVC_DXY, 240_cf460.csv')


def load_ethbtc():
    return load_basic('/Users/cristrein/Downloads/BINANCE_ETHBTC, 240_bdea6.csv')


def attach_macro(df_low, df_macro, prefix):
    """Join macro indicators by forward fill (df_macro values at each df_low time)."""
    macro = df_macro[['time', 'close', 'ema50', 'ema200']].copy()
    macro.columns = ['time', f'{prefix}_close', f'{prefix}_ema50', f'{prefix}_ema200']
    df_low = df_low.sort_values('time')
    macro = macro.sort_values('time')
    df = pd.merge_asof(df_low, macro, on='time', direction='backward')
    df[f'{prefix}_below_ema50'] = df[f'{prefix}_close'] < df[f'{prefix}_ema50']
    df[f'{prefix}_below_ema200'] = df[f'{prefix}_close'] < df[f'{prefix}_ema200']
    df[f'{prefix}_above_ema50'] = df[f'{prefix}_close'] > df[f'{prefix}_ema50']
    return df


def attach_htf_bias(df_low, df_htf, label):
    htf = df_htf[['time', 'close', 'ema50']].copy()
    htf.columns = ['time', f'{label}_close', f'{label}_ema50']
    df_low = df_low.sort_values('time')
    htf = htf.sort_values('time')
    df = pd.merge_asof(df_low, htf, on='time', direction='backward')
    df[f'{label}_bullish'] = df[f'{label}_close'] > df[f'{label}_ema50']
    return df


def simulate(df, entry_idx, entry, stop, target_r=TARGET_R_DEFAULT):
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
        if not moved_be and h >= entry + R:
            cur_stop = max(cur_stop, entry)
            moved_be = True
        if l <= cur_stop:
            return {'exit_idx': j, 'r': (cur_stop - entry) / R}
        if h >= target:
            return {'exit_idx': j, 'r': target_r}
    last = min(entry_idx + MAX_HOLD_BARS, n - 1)
    return {'exit_idx': last, 'r': (close[last] - entry) / R}


# ============================================================================
# SIG functions per module
# ============================================================================

def sig_xau_1h(df, i):
    """XAUUSD_1H_LONG_DECISIVE_BODY60_HTF"""
    if i < 11: return False
    r = df.iloc[i]
    if pd.isna(r['close']) or pd.isna(r['open']): return False
    if not (r['close'] > r['open']): return False
    if not (r['close'] > df.at[i-1, 'swhi_10']): return False
    if pd.isna(r['body_pct']) or r['body_pct'] < 0.6: return False
    if pd.isna(r['range_x_atr']) or r['range_x_atr'] < 1.2: return False
    if pd.isna(r['rsi14']) or pd.isna(r['rsi_ma']) or r['rsi14'] <= r['rsi_ma']: return False
    if not r['close_above_ema200']: return False
    if not r['ema50_above_ema200']: return False
    if not r['atr_expanding']: return False
    if not r.get('htf1d_bullish', False): return False
    if not r.get('htf4h_bullish', False): return False
    return True


def sig_eth_4h(df, i):
    """ETHUSD_4H_LONG_BREAKOUT_REGIME_FILTERED v1.2 (com ETHBTC)"""
    if i < 11: return False
    r = df.iloc[i]
    if pd.isna(r['close']) or pd.isna(r['open']): return False
    if not (r['close'] > r['open']): return False
    if not (r['close'] > df.at[i-1, 'swhi_10']): return False
    if pd.isna(r['body_pct']) or r['body_pct'] < 0.6: return False
    if pd.isna(r['rsi14']) or pd.isna(r['rsi_ma']) or r['rsi14'] <= r['rsi_ma']: return False
    if pd.isna(r['adx14']) or r['adx14'] < 25: return False
    if not r['close_above_ema200']: return False
    if not r['ema50_above_ema200']: return False
    if pd.isna(r['ema50_slope']) or r['ema50_slope'] <= 0: return False
    if not r['atr_expanding']: return False
    if not r.get('ethbtc_above_ema50', False): return False
    return True


def sig_us500_4h_fb(df, i):
    """US500_4H_LONG_FAILED_BREAKDOWN_REGIME — sweep+reclaim trigger"""
    if i < 21: return False
    r = df.iloc[i]
    if pd.isna(r['close']) or pd.isna(r['open']): return False
    if not (r['close'] > r['open']): return False
    if pd.isna(r['swlo_20']): return False
    if not (r['low'] < r['swlo_20']): return False
    if not (r['close'] > r['swlo_20']): return False
    if pd.isna(r['body_pct']) or r['body_pct'] < 0.5: return False
    if not r['close_above_ema200']: return False
    if not r['ema50_above_ema200']: return False
    if not r['atr_expanding']: return False
    return True


def sig_us500_1h(df, i):
    """US500_1H_LONG_BREAKOUT_REGIME_FILTERED"""
    if i < 11: return False
    r = df.iloc[i]
    if pd.isna(r['close']) or pd.isna(r['open']): return False
    if not (r['close'] > r['open']): return False
    if not (r['close'] > df.at[i-1, 'swhi_10']): return False
    if pd.isna(r['body_pct']) or r['body_pct'] < 0.5: return False
    if pd.isna(r['rsi14']) or pd.isna(r['rsi_ma']) or r['rsi14'] <= r['rsi_ma']: return False
    if not r['close_above_ema200']: return False
    if not r['ema50_above_ema200']: return False
    if pd.isna(r['ema50_slope']) or r['ema50_slope'] <= 0: return False
    if not r['atr_expanding']: return False
    if pd.isna(r['adx14']) or r['adx14'] < 20: return False
    if not r.get('htf1d_bullish', False): return False
    if not r.get('htf4h_bullish', False): return False
    return True


def sig_xag_1h(df, i):
    """XAGUSD_1H_LONG_DECISIVE_DXY_STRUCTURAL"""
    if i < 11: return False
    r = df.iloc[i]
    if pd.isna(r['close']) or pd.isna(r['open']): return False
    if not (r['close'] > r['open']): return False
    if not (r['close'] > df.at[i-1, 'swhi_10']): return False
    if pd.isna(r['body_pct']) or r['body_pct'] < 0.6: return False
    if pd.isna(r['range_x_atr']) or r['range_x_atr'] < 1.2: return False
    if pd.isna(r['rsi14']) or pd.isna(r['rsi_ma']) or r['rsi14'] <= r['rsi_ma']: return False
    if not r['close_above_ema200']: return False
    if not r['ema50_above_ema200']: return False
    if not r['atr_expanding']: return False
    if not r.get('htf1d_bullish', False): return False
    if not r.get('htf4h_bullish', False): return False
    if not r.get('dxy_below_ema200', False): return False
    return True


# ============================================================================
# Runner
# ============================================================================

def run_module(name, asset, ltf, sig_fn, extra_attach=None, htf_for_mtf=None):
    print(f"\n{'='*80}\n{name}\n{'='*80}")
    ltf_path = find_csv(asset, ltf)
    df = load_full(ltf_path)
    # Attach HTFs
    if asset == 'XAUUSD' or asset == 'XAGUSD' or asset == 'US500':
        if ltf == '1H':
            df_1d = load_full(find_csv(asset, '1D'))
            df_4h = load_full(find_csv(asset, '4H'))
            df = attach_htf_bias(df, df_1d, 'htf1d')
            df = attach_htf_bias(df, df_4h, 'htf4h')
        elif ltf == '4H':
            df_1d = load_full(find_csv(asset, '1D'))
            df = attach_htf_bias(df, df_1d, 'htf1d')
    if extra_attach:
        df = extra_attach(df)

    # Generate trades
    trades = []
    for i in range(21, len(df)):
        if not sig_fn(df, i):
            continue
        atr_e = df.at[i, 'atr14']
        if pd.isna(atr_e) or atr_e <= 0:
            continue
        low_bar = df.at[i, 'low']
        stop = low_bar - STOP_ATR_MULT * atr_e
        entry = df.at[i, 'close']
        R = entry - stop
        if R <= 0 or R > ATR_R_CAP * atr_e:
            continue
        res = simulate(df, i, entry, stop, TARGET_R_DEFAULT)
        if res is None:
            continue
        trades.append({
            'entry_time': df.at[i, 'time'],
            'r_net': float(res['r']) - SPREAD_R,
            'year': int(df.at[i, 'year']),
        })

    df_t = pd.DataFrame(trades)
    print(f"Trades gerados: {len(df_t)}")
    if len(df_t) < 5:
        print("  ⚠️  poucos trades — pulando")
        return None

    # MTF gate
    htf = htf_for_mtf or HTF_MAP[ltf]
    htf_path = find_csv(asset, htf)
    df_htf = load_basic(htf_path)
    ph, pl = detect_pivots(df_htf, PIVOT_LEN)
    htf_events = track_structure(df_htf, ph, pl)
    bull_events = [e for e in htf_events if e['type'] in ('BOS_BULL', 'CHOCH_BULL')]
    print(f"  HTF MTF={htf}, bull events: {len(bull_events)}")

    def check_aligned(t):
        ts = pd.to_datetime(t)
        if ts.tzinfo is not None:
            ts = ts.tz_localize(None)
        htf_times = pd.to_datetime(df_htf['time'])
        if htf_times.iloc[0].tzinfo is not None:
            htf_times = htf_times.dt.tz_localize(None)
        pos = htf_times.searchsorted(ts, side='left')
        if pos == 0:
            return False
        e_idx = pos - 1
        s_idx = max(0, e_idx - HTF_LOOKBACK + 1)
        for ev in bull_events:
            if s_idx <= ev['idx'] <= e_idx:
                return True
        return False

    df_t['aligned'] = df_t['entry_time'].apply(check_aligned)
    n_aligned = int(df_t['aligned'].sum())
    print(f"  Aligned: {n_aligned}/{len(df_t)} ({n_aligned/len(df_t)*100:.1f}%)")

    return df_t


def metrics(r):
    if len(r) == 0:
        return {'n': 0, 'total': 0, 'win': 0, 'pf': 0, 'sharpe': 0}
    arr = np.array(r)
    wins = arr[arr > 0].sum()
    losses = -arr[arr < 0].sum()
    pf = wins / losses if losses > 0 else float('inf')
    avg = arr.mean()
    std = arr.std(ddof=1) if len(arr) > 1 else 0
    sharpe = (avg / std * math.sqrt(len(arr))) if std > 0 else 0
    return {'n': len(arr), 'total': float(arr.sum()),
            'win': float((arr > 0).mean() * 100),
            'pf': float(pf) if pf != float('inf') else 999.0,
            'sharpe': float(sharpe)}


def report(name, df_t, expected_n):
    if df_t is None or len(df_t) == 0:
        print(f"\n{name}: skipped")
        return None
    all_m = metrics(df_t['r_net'].values)
    a = metrics(df_t[df_t['aligned']]['r_net'].values)
    m = metrics(df_t[~df_t['aligned']]['r_net'].values)
    print(f"\n  Esperado n={expected_n}, gerado n={all_m['n']} {'✓' if abs(all_m['n']-expected_n)<=5 else '⚠️ diferença significativa'}")
    print(f"  OVERALL:    n={all_m['n']:>3}  R={all_m['total']:>+7.2f}  PF={all_m['pf']:>4.2f}  win={all_m['win']:>5.1f}%  Sharpe={all_m['sharpe']:>+5.2f}")
    print(f"  ALIGNED:    n={a['n']:>3}  R={a['total']:>+7.2f}  PF={a['pf']:>4.2f}  win={a['win']:>5.1f}%  Sharpe={a['sharpe']:>+5.2f}")
    print(f"  MISALIGNED: n={m['n']:>3}  R={m['total']:>+7.2f}  PF={m['pf']:>4.2f}  win={m['win']:>5.1f}%  Sharpe={m['sharpe']:>+5.2f}")
    if a['n'] < 10:
        verdict = "SMALL_N"
    elif a['sharpe'] >= m['sharpe'] + 0.5 and a['pf'] >= m['pf'] + 0.3:
        verdict = "✅ ADOPT FORTE"
    elif a['sharpe'] >= m['sharpe'] + 0.2:
        verdict = "🟡 marginal"
    elif a['sharpe'] < m['sharpe'] - 0.2:
        verdict = "❌ HURTS"
    else:
        verdict = "— neutral"
    print(f"  VEREDITO: {verdict}")
    return {'name': name, 'all': all_m, 'aligned': a, 'misaligned': m, 'verdict': verdict}


def main():
    print("="*80)
    print("MTF Audit — 5 módulos restantes (config formal replicada)")
    print("="*80)
    results = []

    # 1. XAU 1H
    df = run_module('XAUUSD_1H_DECISIVE_BODY60_HTF', 'XAUUSD', '1H', sig_xau_1h)
    results.append(report('XAU 1H', df, 127))

    # 2. ETH 4H — needs ETHBTC
    def attach_ethbtc(df):
        ethbtc = load_full('/Users/cristrein/Downloads/BINANCE_ETHBTC, 240_bdea6.csv')
        e = ethbtc[['time','close','ema50']].copy()
        e.columns = ['time','ethbtc_close','ethbtc_ema50']
        df = df.sort_values('time')
        e = e.sort_values('time')
        merged = pd.merge_asof(df, e, on='time', direction='backward')
        merged['ethbtc_above_ema50'] = merged['ethbtc_close'] > merged['ethbtc_ema50']
        return merged

    df = run_module('ETHUSD_4H_BREAKOUT_REGIME_FILTERED_v1.2', 'ETHUSD', '4H', sig_eth_4h,
                    extra_attach=attach_ethbtc, htf_for_mtf='1D')
    results.append(report('ETH 4H', df, 72))

    # 3. US500 4H failed breakdown
    df = run_module('US500_4H_FAILED_BREAKDOWN_REGIME', 'US500', '4H', sig_us500_4h_fb,
                    htf_for_mtf='1D')
    results.append(report('US500 4H FB', df, 45))

    # 4. US500 1H
    df = run_module('US500_1H_BREAKOUT_REGIME_FILTERED', 'US500', '1H', sig_us500_1h)
    results.append(report('US500 1H', df, 222))

    # 5. XAG 1H — needs DXY EMA200 4H
    def attach_dxy(df):
        dxy = load_full('/Users/cristrein/Downloads/TVC_DXY, 240_cf460.csv')
        d = dxy[['time','close','ema200']].copy()
        d.columns = ['time','dxy_close','dxy_ema200']
        df = df.sort_values('time')
        d = d.sort_values('time')
        merged = pd.merge_asof(df, d, on='time', direction='backward')
        merged['dxy_below_ema200'] = merged['dxy_close'] < merged['dxy_ema200']
        return merged

    df = run_module('XAGUSD_1H_DECISIVE_DXY_STRUCTURAL', 'XAGUSD', '1H', sig_xag_1h,
                    extra_attach=attach_dxy)
    results.append(report('XAG 1H', df, 69))

    # Summary
    print(f"\n\n{'='*100}\nSUMMARY 5 módulos\n{'='*100}")
    print(f"{'Module':<14} | {'n':>4} | {'aligned%':>8} | {'Aligned':>30} | {'Misaligned':>30} | Verdict")
    print('-'*140)
    for r in results:
        if not r: continue
        a, m = r['aligned'], r['misaligned']
        ap = r['aligned']['n'] / max(r['all']['n'], 1) * 100
        a_str = f"n={a['n']:>3} R={a['total']:>+5.1f} PF={a['pf']:>4.2f} S={a['sharpe']:>+4.2f}"
        m_str = f"n={m['n']:>3} R={m['total']:>+5.1f} PF={m['pf']:>4.2f} S={m['sharpe']:>+4.2f}"
        print(f"{r['name']:<14} | {r['all']['n']:>4} | {ap:>7.1f}% | {a_str:>30} | {m_str:>30} | {r['verdict']}")

    with open(DIR / 'mtf_5_modules_results.json', 'w') as f:
        json.dump([r for r in results if r], f, indent=2, default=str)


if __name__ == '__main__':
    main()
