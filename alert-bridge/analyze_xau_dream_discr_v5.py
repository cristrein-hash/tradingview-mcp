#!/usr/bin/env python3
"""
analyze_xau_dream_discr_v5.py — Deep dive dos 5 dream LONG não-capturados pelo CAPITULATION.

Usa dataset v5 (com LuxAlgo SMC + 3 CVDs capturados).

5 dream trades:
  #1   2026-05-04 15:00 LONG  (bar 14:00)
  #6   2026-03-12 10:00 LONG  (bar 10:00) — gap em v3, verificar v5
  #8   2026-03-20 14:00 LONG  (bar 14:00)
  #10  2026-03-24 10:00 LONG  (bar 10:00)
  #11  2026-01-29 19:00 LONG  (bar 19:00) — outlier provável (RSI 85.6)
  #13  2026-02-03 03:00 LONG  (bar 03:00)

Pra cada trade, extrair features novas:
  - LuxAlgo: CHoCH/BOS bullish nos últimos 20 bars, FVG Bull ativa, Strong Low
  - UAlgo CVD: +RD/Reg/Hid/Abs nos últimos 20 bars
  - TradingFinder CVD: +RD nos últimos 20 bars, current Hist sign
  - QuantAlgo CVD: Rolling CVD vs Signal Line cross recente
"""
from pathlib import Path
from datetime import datetime, timezone
from statistics import mean
import json, sys
from collections import defaultdict

BASE = Path(__file__).parent.parent
JSONL_DIR = BASE / "alert-bridge" / "logs" / "backtests"

# Janelas que cobrem as dream trades
RELEVANT_FILES = [
    "XAUUSD_240_2025-11-19_to_2026-05-21_v5.jsonl",  # cobre #11, #13 + parte de Jan-Mar 2026
    "XAUUSD_240_2026-03-19_to_2026-05-21_v5.jsonl",  # cobre #1, #8, #10 + #6 talvez
]

DREAM_NO_CAPIT = [
    ("#1",  "2026-05-04 15:00"),
    ("#6",  "2026-03-12 10:00"),
    ("#8",  "2026-03-20 14:00"),
    ("#10", "2026-03-24 10:00"),
    ("#11", "2026-01-29 19:00"),
    ("#13", "2026-02-03 03:00"),
]
TOLERANCE_SEC = 7200  # ±2h DST tolerance
BAR_SECONDS_4H = 14400


def load_bars(p):
    bars=[]
    with Path(p).open() as f:
        for line in f:
            try: bars.append(json.loads(line))
            except: pass
    for i,b in enumerate(bars):
        if b.get('_error') or not (b.get('ohlcv_last_40_bars') or []):
            bars = bars[:i]; break
    return bars


def find_bar(master, target_ts):
    best_t = None; best_d = None
    for t in master.keys():
        d = abs(t-target_ts)
        if d <= TOLERANCE_SEC and (best_d is None or d<best_d):
            best_d = d; best_t = t
    return best_t


LUX_BULL_TEXTCOLOR = 4286683400  # bullish color (cinza esverdeado)
LUX_BEAR_TEXTCOLOR = 4282726130  # bearish color (marrom-vermelho)

def get_recent_labels(bar, study_substr, lookback=20):
    """Pega labels recentes. Retorna lista (delta, text, direction, raw_label)."""
    out = []
    for s in (bar.get('pine_labels') or []):
        if study_substr.upper() not in s.get('name','').upper(): continue
        labels = s.get('labels') or []
        if not labels: continue
        xs = [l.get('x') for l in labels if l.get('x') is not None]
        if not xs: continue
        max_x = max(xs)
        for l in labels:
            lx = l.get('x'); txt = l.get('text','')
            if lx is None: continue
            delta = max_x - lx
            if 0 <= delta <= lookback:
                tc = l.get('textColor')
                direction = 'BULL' if tc == LUX_BULL_TEXTCOLOR else 'BEAR' if tc == LUX_BEAR_TEXTCOLOR else '?'
                out.append((delta, txt, direction, l))
        return out
    return out


def get_recent_boxes(bar, study_substr):
    """Pega boxes ativas (todas). Retorna lista de dicts."""
    out = []
    for s in (bar.get('pine_boxes') or []):
        if study_substr.upper() not in s.get('name','').upper(): continue
        return s.get('all_boxes', [])
    return out


def get_recent_lines(bar, study_substr, lookback=30):
    """Lines recentes do study."""
    for s in (bar.get('pine_lines') or []):
        if study_substr.upper() not in s.get('name','').upper(): continue
        lines = s.get('all_lines', [])
        if not lines: continue
        # x2 mais alto = línea mais recente
        xs = [l.get('x2') for l in lines if l.get('x2') is not None]
        if not xs: return lines
        max_x = max(xs)
        return [l for l in lines if l.get('x2') is not None and (max_x - l.get('x2')) <= lookback]
    return []


def get_study_value(bar, study_substr, key=None):
    """Pega valor de study_values. Retorna dict de keys ou valor único."""
    for s in (bar.get('study_values') or []):
        if study_substr.upper() not in s.get('name','').upper(): continue
        vals = s.get('values', {})
        if key: return vals.get(key)
        return vals
    return None


def main():
    print("=== DEEP DIVE v5 — 6 dream LONG (incluindo gap #6 e outlier #11) ===\n")

    # Load all v5 master
    master = {}
    for fname in RELEVANT_FILES:
        p = JSONL_DIR / fname
        if not p.exists():
            print(f"WARN: {fname} missing"); continue
        print(f"Loading {fname}...")
        bars = load_bars(p)
        for b in bars:
            ohlcv = b.get('ohlcv_last_40_bars') or []
            if not ohlcv: continue
            t = ohlcv[-1].get('time')
            if t is None or t in master: continue
            master[t] = b
    print(f"Master 4H: {len(master)} bars únicos\n")

    for tid, dt_str in DREAM_NO_CAPIT:
        target_ts = int(datetime.strptime(dt_str+"+0000","%Y-%m-%d %H:%M%z").timestamp())
        bar_t = find_bar(master, target_ts)
        if bar_t is None:
            print(f"\n══ [{tid}] {dt_str} BAR NOT FOUND in v5\n")
            continue
        b = master[bar_t]
        bar_dt = datetime.fromtimestamp(bar_t, tz=timezone.utc).strftime('%Y-%m-%d %H:%M')
        ohlcv = b.get('ohlcv_last_40_bars') or []
        close = ohlcv[-1].get('close')

        print(f"\n══ [{tid}] crosshair {dt_str}  bar matched {bar_dt}  close={close}")

        # LuxAlgo SMC labels — distinguindo bull vs bear via textColor
        lux_labels = get_recent_labels(b, "LuxAlgo", lookback=20)
        lux_by_key = defaultdict(list)
        for delta, txt, direction, _ in lux_labels:
            key = f"{txt}_{direction}"
            lux_by_key[key].append(delta)
        print(f"  LuxAlgo SMC labels (lookback 20, bull vs bear via cor):")
        # Order: bullish first
        for key in sorted(lux_by_key.keys(), key=lambda k: (k.endswith('BEAR'), k)):
            deltas = sorted(lux_by_key[key])
            print(f"    '{key}': closest_Δ={deltas[0]}  count={len(deltas)}")

        # LuxAlgo boxes (OB, FVG)
        lux_boxes = get_recent_boxes(b, "LuxAlgo")
        print(f"  LuxAlgo boxes: {len(lux_boxes)} total")
        # Boxes que contém o close
        in_zone = []
        for box in lux_boxes:
            hi, lo = box.get('high'), box.get('low')
            if hi is None or lo is None or close is None: continue
            if lo <= close <= hi:
                in_zone.append(box)
        if in_zone:
            print(f"    Boxes que contém close ({close}):")
            for box in in_zone:
                print(f"      {box}")

        # UAlgo CVD labels
        ualgo_labels = get_recent_labels(b, "CVD Divergence & Absorption", lookback=20)
        ualgo_by_text = defaultdict(list)
        for delta, txt, _, _ in ualgo_labels:
            ualgo_by_text[txt].append(delta)
        print(f"  UAlgo CVD labels (lookback 20):")
        for txt, deltas in ualgo_by_text.items():
            deltas.sort()
            print(f"    '{txt}': closest_Δ={deltas[0]}  count={len(deltas)}")

        # TradingFinder CVD labels
        tf_labels = get_recent_labels(b, "TradingFinder", lookback=20)
        tf_by_text = defaultdict(list)
        for delta, txt, _, _ in tf_labels:
            tf_by_text[txt].append(delta)
        print(f"  TradingFinder CVD labels (lookback 20):")
        for txt, deltas in tf_by_text.items():
            deltas.sort()
            print(f"    '{txt}': closest_Δ={deltas[0]}  count={len(deltas)}")

        # TradingFinder CVD value
        tf_hist = get_study_value(b, "TradingFinder", "Show Cumulative Vol Delta")
        print(f"  TradingFinder CVD Hist atual: {tf_hist}")

        # QuantAlgo CVD vs Signal
        quant_vals = get_study_value(b, "QuantAlgo")
        if quant_vals:
            print(f"  QuantAlgo: {quant_vals}")

        # UAlgo CVD value
        ualgo_cvd = get_study_value(b, "CVD Divergence & Absorption", "CVD")
        print(f"  UAlgo CVD value: {ualgo_cvd}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
