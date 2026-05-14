#!/usr/bin/env python3
"""
Macro-filter framework for ETHUSD strategies.

Goal: integrate external macro context (BTC dominance, BTCUSD regime,
ETHBTC relative strength, DXY) as additional filter to reduce
fat-tail dependency in ETH breakout strategy.

Inputs expected in DOWNLOADS_DIR:
- CRYPTOCAP_BTC.D, 240*.csv      ← BTC dominance 4H
- BINANCE_ETHBTC, 240*.csv       ← ETH/BTC ratio 4H
- (optional) Pepperstone_BTCUSD already used elsewhere
- (optional) TVC_DXY, 240*.csv   ← US Dollar Index 4H

Behavior:
- If CSVs missing, framework reports "data unavailable, skipping macro test"
- If present, computes macro features per timestamp and aligns to ETHUSD 4H
- Backtests current best ETH strategy with macro filters
- Outputs sensitivity tables
"""
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import glob

sys.path.insert(0, str(Path(__file__).parent))
from backtest_ethusd import load as load_eth, simulate_trade, SPREAD_R, FILES
from rule_proposals import htf_context

DOWNLOADS = Path('/Users/cristrein/Downloads')
OUT_DIR = Path(__file__).parent


def find_macro_csv(pattern_keywords):
    """Find CSV in Downloads matching any keyword (case-insensitive)."""
    for p in DOWNLOADS.glob('*.csv'):
        name = p.name.upper()
        if all(kw.upper() in name for kw in pattern_keywords):
            return p
    return None


def load_macro(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    df.columns = [c.strip() for c in df.columns]
    df['time'] = pd.to_datetime(df['time'], unit='s')
    df = df.sort_values('time').reset_index(drop=True)
    # Numeric
    for c in ['open','high','low','close']:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors='coerce')
    # EMAs
    if 'close' in df.columns:
        df['ema20'] = df['close'].ewm(span=20, adjust=False).mean()
        df['ema50'] = df['close'].ewm(span=50, adjust=False).mean()
        df['ema200'] = df['close'].ewm(span=200, adjust=False).mean()
        df['slope_5'] = df['close'].diff(5)
        df['slope_10'] = df['close'].diff(10)
        df['bullish_vs_ema50'] = df['close'] > df['ema50']
        df['bullish_vs_ema200'] = df['close'] > df['ema200']
        df['ema50_above_ema200'] = df['ema50'] > df['ema200']
    return df


def align_macro(df_eth: pd.DataFrame, df_macro: pd.DataFrame, prefix: str) -> pd.DataFrame:
    """Merge backwards-asof: each ETH 4H bar gets most recent macro value."""
    cols = ['time', 'close', 'bullish_vs_ema50', 'bullish_vs_ema200',
            'ema50_above_ema200', 'slope_5', 'slope_10']
    cols_present = [c for c in cols if c in df_macro.columns]
    sub = df_macro[cols_present].rename(columns={c: f'{prefix}_{c}' for c in cols_present if c != 'time'})
    df_eth = df_eth.sort_values('time').reset_index(drop=True)
    sub = sub.sort_values('time').reset_index(drop=True)
    merged = pd.merge_asof(df_eth, sub, on='time', direction='backward')
    return merged


def run_strategy(df, macro_filters: dict, target_r=5.0, max_bars=30, adx_min=25,
                 require_body_60pct=True, name='?'):
    """ETH 4H breakout regime-filtered + optional macro filters."""
    trades = []
    for i in range(200, len(df) - 1):
        row = df.iloc[i]
        if not (row['close'] > row['open']
                and row['body_pct'] >= 0.5
                and row['close'] > df.at[i-1, 'swhi_10']):
            continue
        if require_body_60pct and row['body_pct'] < 0.6:
            continue
        rsi = row.get('RSI', np.nan); rsi_ma = row.get('RSI-based MA', np.nan)
        if pd.isna(rsi) or pd.isna(rsi_ma) or rsi <= rsi_ma:
            continue
        if pd.isna(row.get('adx14', np.nan)) or row['adx14'] < adx_min: continue
        if not row.get('close_above_ema200', False): continue
        if not row.get('ema50_above_ema200', False): continue
        if not row.get('atr_expanding', False): continue
        if pd.isna(row.get('ema50_slope', np.nan)) or row['ema50_slope'] <= 0: continue

        # === MACRO FILTERS ===
        if macro_filters.get('btcd_bearish') and not (row.get('btcd_close', np.nan) < row.get('btcd_ema50', np.nan)
                                                       if not pd.isna(row.get('btcd_close', np.nan)) and not pd.isna(row.get('btcd_ema50', np.nan)) else False):
            continue
        if macro_filters.get('btcd_falling') and not (row.get('btcd_slope_10', 0) < 0):
            continue
        if macro_filters.get('ethbtc_bullish') and not row.get('ethbtc_bullish_vs_ema50', False):
            continue
        if macro_filters.get('btc_bull_regime'):
            if not row.get('btc_bullish_vs_ema200', False): continue
            if not row.get('btc_ema50_above_ema200', False): continue
        if macro_filters.get('dxy_bearish') and not (row.get('dxy_close', np.nan) < row.get('dxy_ema50', np.nan)
                                                      if not pd.isna(row.get('dxy_close', np.nan)) and not pd.isna(row.get('dxy_ema50', np.nan)) else False):
            continue

        entry = row['close']; atr = row['atr14']
        if pd.isna(atr) or atr <= 0: continue
        stop = row['low'] - atr * 0.5
        R = abs(entry - stop)
        if R <= 0 or R / atr > 5: continue
        res = simulate_trade(df, i, 'LONG', entry, stop, target_r, max_bars, be_at_1r=True)
        if not res: continue
        res.update({'entry_time': row['time'], 'entry_price': entry,
                    'stop_price': stop, 'direction': 'LONG', 'r_planned': target_r,
                    'strategy': name, 'tf': '4H'})
        trades.append(res)
    return trades


def metrics_with_spread(trades, spread=SPREAD_R):
    if not trades:
        return {'n': 0}
    df = pd.DataFrame(trades)
    r_net = df['r_outcome'] - spread
    wins = r_net[r_net > 0]; losses = r_net[r_net < 0]
    pf = abs(wins.sum() / losses.sum()) if len(losses) and losses.sum() != 0 else float('inf')
    sorted_r = sorted(r_net.tolist(), reverse=True)
    streak = max_streak = 0
    for v in r_net:
        if v <= 0: streak += 1; max_streak = max(max_streak, streak)
        else: streak = 0
    return {
        'n': len(df),
        'total_net_r': round(r_net.sum(), 2),
        'avg_net_r': round(r_net.mean(), 4),
        'pf_net': round(pf, 2) if pf != float('inf') else 'inf',
        'win_rate': round((r_net > 0).mean(), 3),
        'max_losing_streak': max_streak,
        'r_no_top5_net': round(sum(sorted_r[5:]), 2) if len(sorted_r) > 5 else round(r_net.sum(),2),
        'r_no_top10_net': round(sum(sorted_r[10:]), 2) if len(sorted_r) > 10 else round(r_net.sum(),2),
    }


def yearly(trades, spread=SPREAD_R):
    if not trades:
        return pd.DataFrame()
    df = pd.DataFrame(trades)
    df['year'] = pd.to_datetime(df['entry_time']).dt.year
    df['r_net'] = df['r_outcome'] - spread
    return df.groupby('year').agg(
        n=('r_net', 'count'),
        total_net=('r_net', 'sum'),
        avg_net=('r_net', 'mean'),
        win_rate=('r_net', lambda x: (x > 0).mean()),
    ).round(3).reset_index()


def main():
    print("=== Loading ETHUSD 4H + adding HTF context ===")
    df4 = load_eth(FILES['4H'])
    df12 = load_eth(FILES['12H'])
    df1d = load_eth(FILES['1D'])
    df4 = htf_context(df4, df12, 'htf12h')
    df4 = htf_context(df4, df1d, 'htf1d')

    # === Look for macro CSVs ===
    print("\n=== Searching for macro CSVs in ~/Downloads ===")
    macro_paths = {
        'btcd': find_macro_csv(['BTC.D']) or find_macro_csv(['BTC_D']) or find_macro_csv(['CRYPTOCAP_BTC.D']),
        'ethbtc': find_macro_csv(['ETHBTC']),
        'btc': find_macro_csv(['BTCUSD']),
        'dxy': find_macro_csv(['DXY']),
    }
    for name, p in macro_paths.items():
        if p:
            print(f"  ✅ {name}: {p.name}")
        else:
            print(f"  ❌ {name}: NÃO encontrado")

    # === Build composite df with macro columns ===
    if macro_paths['btcd']:
        df_btcd = load_macro(macro_paths['btcd'])
        df4 = align_macro(df4, df_btcd, 'btcd')
        print(f"\n  BTC.D current = {df_btcd['close'].iloc[-1]:.2f}%, bullish_vs_ema50 frac = {df4['btcd_bullish_vs_ema50'].mean():.2%}")
    if macro_paths['ethbtc']:
        df_ethbtc = load_macro(macro_paths['ethbtc'])
        df4 = align_macro(df4, df_ethbtc, 'ethbtc')
        print(f"  ETHBTC bullish vs EMA50 frac = {df4['ethbtc_bullish_vs_ema50'].mean():.2%}")
    if macro_paths['btc']:
        df_btc = load_macro(macro_paths['btc'])
        df4 = align_macro(df4, df_btc, 'btc')
        print(f"  BTCUSD bullish vs EMA200 frac = {df4['btc_bullish_vs_ema200'].mean():.2%}")
    if macro_paths['dxy']:
        df_dxy = load_macro(macro_paths['dxy'])
        df4 = align_macro(df4, df_dxy, 'dxy')
        print(f"  DXY bullish vs EMA50 frac = {df4['dxy_bullish_vs_ema50'].mean():.2%}")

    if not any(macro_paths.values()):
        print("\n⚠️  Nenhum CSV macro encontrado. Não há como testar.")
        print("\nPara prosseguir, exporte do TradingView (4H, mesma janela do ETHUSD ou maior):")
        print("  1. CRYPTOCAP:BTC.D     → salvar como 'CRYPTOCAP_BTC.D, 240.csv'")
        print("  2. BINANCE:ETHBTC      → salvar como 'BINANCE_ETHBTC, 240.csv'")
        print("  3. PEPPERSTONE:BTCUSD  → salvar como 'PEPPERSTONE_BTCUSD, 240.csv'")
        print("  4. (opcional) TVC:DXY  → salvar como 'TVC_DXY, 240.csv'")
        print("\nDepois rode novamente: python3 macro_filter_framework.py")
        return

    # === Configs to test ===
    configs = [
        ('baseline_v1.0', {}, False),
        ('v1.1_body60', {}, True),
    ]
    if macro_paths['btcd']:
        configs.append(('v1.1+BTC.D_bearish (BTCD < EMA50)', {'btcd_bearish': True}, True))
        configs.append(('v1.1+BTC.D_falling (slope_10 < 0)', {'btcd_falling': True}, True))
    if macro_paths['ethbtc']:
        configs.append(('v1.1+ETHBTC_bullish', {'ethbtc_bullish': True}, True))
    if macro_paths['btc']:
        configs.append(('v1.1+BTC_bull_regime', {'btc_bull_regime': True}, True))
    if macro_paths['dxy']:
        configs.append(('v1.1+DXY_bearish', {'dxy_bearish': True}, True))
    # Combos
    if macro_paths['btcd'] and macro_paths['btc']:
        configs.append(('v1.1+BTCD_bearish+BTC_bull', {'btcd_bearish': True, 'btc_bull_regime': True}, True))
    if macro_paths['ethbtc'] and macro_paths['btc']:
        configs.append(('v1.1+ETHBTC_bull+BTC_bull', {'ethbtc_bullish': True, 'btc_bull_regime': True}, True))
    if all([macro_paths['btcd'], macro_paths['ethbtc'], macro_paths['btc']]):
        configs.append(('v1.1+ALL_macro_bullish',
                        {'btcd_bearish': True, 'ethbtc_bullish': True, 'btc_bull_regime': True}, True))

    # === Run all ===
    print(f"\n=== Testing {len(configs)} configurations ===\n")
    rows = []
    detail = {}
    for name, mf, body60 in configs:
        trades = run_strategy(df4, mf, target_r=5.0, max_bars=30, adx_min=25,
                              require_body_60pct=body60, name=name)
        m = metrics_with_spread(trades)
        rows.append({'config': name, **m})
        detail[name] = trades

    df_res = pd.DataFrame(rows).sort_values('total_net_r', ascending=False)
    df_res.to_csv(OUT_DIR / 'ETHUSD_macro_filter_test.csv', index=False)

    print("=== Results sorted by total_net_r (5.4y, 0.05R spread) ===")
    print(df_res.to_string(index=False))

    # Yearly breakdown for top 3
    print("\n=== Top 3 — yearly breakdown ===")
    for cfg in df_res['config'].head(3):
        print(f"\n--- {cfg} ---")
        print(yearly(detail[cfg]).to_string(index=False))


if __name__ == '__main__':
    main()
