#!/usr/bin/env python3
"""POC scan proativo — XAU 4H BREAKOUT_CONTINUATION_REGIME_FILTERED.

Objetivo: verificar quantos eventos teriam DISPARADO nos últimos 30 dias.
- OHLCV via yfinance (GC=F gold futures, alternativa XAUUSD=X)
- Aplicar 7 critérios do módulo XAU 4H BREAKOUT
- Contar eventos qualificados

Critérios módulo (do claude_recheck.py linha 845):
  T4: close > swing_high(10)
  T5: close > open
  T6: body_pct >= 0.5
  T7: RSI(14) > RSI MA
  F1: ADX(14) >= 20
  F2: Close > EMA(200)
  F3: EMA(50) > EMA(200)
  F4: EMA(50) slope positivo (5 bars)
  F5: ATR(14) > ATR_MA(20)
"""
import sys
import warnings
warnings.filterwarnings("ignore")

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Pull XAU OHLCV — yfinance "GC=F" é gold futures
# yfinance suporta 1h max pra periods curtos. Vou puxar 1h e resamplear pra 4h.
print("Pulling XAU OHLCV via yfinance...")

# yfinance: period max para interval 1h é 730d. Vamos pegar 60d.
df_1h = yf.download("GC=F", period="60d", interval="1h", progress=False, auto_adjust=False)
if df_1h.empty:
    print("ERRO: GC=F vazio. Tentando XAUUSD=X...")
    df_1h = yf.download("XAUUSD=X", period="60d", interval="1h", progress=False, auto_adjust=False)
    if df_1h.empty:
        print("Sem dados — abort.")
        sys.exit(1)

# Limpar colunas (yfinance retorna MultiIndex)
if isinstance(df_1h.columns, pd.MultiIndex):
    df_1h.columns = df_1h.columns.get_level_values(0)

print(f"1H bars: {len(df_1h)}, period: {df_1h.index.min()} a {df_1h.index.max()}")

# Resample 1H → 4H
df_4h = df_1h.resample("4h").agg({
    "Open": "first",
    "High": "max",
    "Low": "min",
    "Close": "last",
    "Volume": "sum",
}).dropna()

df = df_4h.rename(columns={"Open": "open", "High": "high", "Low": "low", "Close": "close", "Volume": "volume"})
print(f"4H bars: {len(df)}")
print(f"Period: {df.index.min()} a {df.index.max()}")

# Indicadores
def compute_indicators(df):
    h, l, c = df["high"], df["low"], df["close"]
    pc = c.shift(1)
    tr = pd.concat([(h - l).abs(), (h - pc).abs(), (l - pc).abs()], axis=1).max(axis=1)
    df["atr14"] = tr.ewm(alpha=1 / 14, adjust=False).mean()
    df["atr_ma20"] = df["atr14"].rolling(20, min_periods=1).mean()
    df["atr_expanding"] = df["atr14"] > df["atr_ma20"]

    df["ema50"] = df["close"].ewm(span=50, adjust=False).mean()
    df["ema200"] = df["close"].ewm(span=200, adjust=False).mean()
    df["ema50_slope"] = df["ema50"] - df["ema50"].shift(5)

    df["swhi_10"] = df["high"].rolling(10, min_periods=1).max().shift(1)
    df["body_pct"] = (df["close"] - df["open"]).abs() / (df["high"] - df["low"]).replace(0, np.nan)

    # RSI
    delta = df["close"].diff()
    gain = delta.where(delta > 0, 0).ewm(alpha=1 / 14, adjust=False).mean()
    loss = (-delta.where(delta < 0, 0)).ewm(alpha=1 / 14, adjust=False).mean()
    rs = gain / loss.replace(0, np.nan)
    df["rsi14"] = 100 - 100 / (1 + rs)
    df["rsi_ma"] = df["rsi14"].ewm(span=14, adjust=False).mean()

    # ADX (simples Wilder)
    up = df["high"].diff()
    dn = -df["low"].diff()
    pdm = np.where((up > dn) & (up > 0), up, 0)
    ndm = np.where((dn > up) & (dn > 0), dn, 0)
    pdi = 100 * pd.Series(pdm, index=df.index).ewm(alpha=1 / 14, adjust=False).mean() / df["atr14"]
    ndi = 100 * pd.Series(ndm, index=df.index).ewm(alpha=1 / 14, adjust=False).mean() / df["atr14"]
    dx = 100 * (pdi - ndi).abs() / (pdi + ndi).replace(0, np.nan)
    df["adx14"] = dx.ewm(alpha=1 / 14, adjust=False).mean()
    return df


df = compute_indicators(df)

# Aplicar módulo
def is_trigger_xau_4h(row, prev_swhi):
    if pd.isna(row["close"]) or pd.isna(row["open"]):
        return False, "no_data"
    # T4: close > swing_high(10)
    if pd.isna(prev_swhi) or row["close"] <= prev_swhi:
        return False, "T4_no_breakout"
    # T5: bullish
    if row["close"] <= row["open"]:
        return False, "T5_not_bullish"
    # T6: body >= 0.5
    if pd.isna(row["body_pct"]) or row["body_pct"] < 0.5:
        return False, "T6_body"
    # T7: RSI > MA
    if pd.isna(row["rsi14"]) or pd.isna(row["rsi_ma"]) or row["rsi14"] <= row["rsi_ma"]:
        return False, "T7_rsi"
    # F1: ADX >= 20
    if pd.isna(row["adx14"]) or row["adx14"] < 20:
        return False, "F1_adx"
    # F2: close > EMA200
    if pd.isna(row["ema200"]) or row["close"] <= row["ema200"]:
        return False, "F2_ema200"
    # F3: EMA50 > EMA200
    if pd.isna(row["ema50"]) or row["ema50"] <= row["ema200"]:
        return False, "F3_emastack"
    # F4: EMA50 slope > 0
    if pd.isna(row["ema50_slope"]) or row["ema50_slope"] <= 0:
        return False, "F4_slope"
    # F5: ATR expanding
    if not row["atr_expanding"]:
        return False, "F5_atr"
    return True, "QUALIFIED"


# Scan
triggers = []
reason_counter = {}
for i in range(11, len(df)):
    row = df.iloc[i]
    prev_swhi = df.iloc[i]["swhi_10"]
    qual, reason = is_trigger_xau_4h(row, prev_swhi)
    if qual:
        triggers.append({
            "time": df.index[i],
            "close": float(row["close"]),
            "swhi_10": float(prev_swhi),
            "body_pct": float(row["body_pct"]),
            "rsi": float(row["rsi14"]),
            "adx": float(row["adx14"]),
        })
    reason_counter[reason] = reason_counter.get(reason, 0) + 1

# Report
print(f"\n{'=' * 60}")
print(f"RESULTADO POC — XAU 4H BREAKOUT_CONTINUATION_REGIME_FILTERED")
print(f"{'=' * 60}")
print(f"Bars analisados: {len(df) - 11}")
print(f"Período: {df.index[11]} a {df.index[-1]}")
print(f"Eventos QUALIFICADOS (todos 9 critérios): {len(triggers)}")

print(f"\nReasons (por que cada bar não passou):")
for r, n in sorted(reason_counter.items(), key=lambda x: -x[1]):
    print(f"  {r:<25} {n}")

if triggers:
    print(f"\nEventos qualificados:")
    for t in triggers:
        print(f"  {t['time']} | close={t['close']:.2f} | swhi={t['swhi_10']:.2f} | body={t['body_pct']:.2f} | RSI={t['rsi']:.1f} | ADX={t['adx']:.1f}")
else:
    print("\n⚠️ Nenhum evento qualificou.")
