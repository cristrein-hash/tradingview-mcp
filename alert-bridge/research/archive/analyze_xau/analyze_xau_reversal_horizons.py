#!/usr/bin/env python3
"""
analyze_xau_reversal_horizons.py — Testa REVERSAL detector em horizons múltiplos.

Pra cada bar onde NAS LONG/SHORT label disparou nos últimos 5 bars:
  - Calcula outcome em H=5, 10, 15, 20, 30 bars (close-only)
  - Compara win% por horizon
  - Identifica horizon "natural" pra REVERSAL setup

Base: F0_nas_5 (regra mínima com recall 82%)
"""
from pathlib import Path
from datetime import datetime, timezone
from statistics import mean, median
import json, sys
from collections import defaultdict

BASE = Path(__file__).parent.parent
JSONL_DIR = BASE / "alert-bridge" / "logs" / "backtests"

WINDOWS_V3 = [
    ("W1_2023H1",    "XAUUSD_240_2023-01-19_to_2026-05-20_v3.jsonl"),
    ("W2_2023H2",    "XAUUSD_240_2023-07-19_to_2026-05-20_v3.jsonl"),
    ("W3_2024H1",    "XAUUSD_240_2024-01-19_to_2026-05-20_v3.jsonl"),
    ("W4_2024H2",    "XAUUSD_240_2024-07-19_to_2026-05-20_v3.jsonl"),
    ("W5_2025May",   "XAUUSD_240_2025-05-19_to_2026-05-20_v3.jsonl"),
    ("W6_2025Sep",   "XAUUSD_240_2025-09-15_to_2026-05-20_v3.jsonl"),
    ("W7_2025Nov",   "XAUUSD_240_2025-11-19_to_2026-05-20_v3.jsonl"),
    ("W8_2026Mar",   "XAUUSD_240_2026-03-19_to_2026-05-20_v3.jsonl"),
]

HORIZONS = [3, 5, 10, 15, 20, 30, 40]
WIN_GATE = 70.0


def load_bars(p):
    bars = []
    with Path(p).open() as f:
        for line in f:
            try: bars.append(json.loads(line))
            except: pass
    for i, b in enumerate(bars):
        if b.get('_error') or not (b.get('ohlcv_last_40_bars') or []):
            bars = bars[:i]; break
    return bars


def get_atr14(bar):
    ohlcv = bar.get('ohlcv_last_40_bars') or []
    if len(ohlcv) <= 1: return None
    closed = ohlcv[:-1][-14:]
    r = [b['high']-b['low'] for b in closed if b.get('high') and b.get('low') and b['high']>b['low']]
    return mean(r) if r else None


def has_nas_label_recent(bar, want_text, max_delta=5):
    for s in (bar.get('pine_labels') or []):
        if 'NAS' not in s.get('name','').upper(): continue
        labels = s.get('labels') or []
        if not labels: continue
        xs = [lbl.get('x') for lbl in labels if lbl.get('x') is not None]
        if not xs: continue
        max_x = max(xs)
        for lbl in labels:
            lx = lbl.get('x'); txt = (lbl.get('text') or '').upper()
            if lx is None or txt != want_text: continue
            delta = max_x - lx
            if 0 <= delta <= max_delta:
                return True
    return False


def stats_block(rs):
    if not rs: return None
    wins = sum(1 for r in rs if r>0)
    return {'n':len(rs),'win%':100*wins/len(rs),'avg_R':mean(rs),'median_R':median(rs),'sum_R':sum(rs)}


def main():
    print(f"=== HORIZON SWEEP REVERSAL — H={HORIZONS} ===\n")

    master = {}
    bar_to_window = {}
    for label, fname in WINDOWS_V3:
        path = JSONL_DIR / fname
        if not path.exists(): continue
        bars = load_bars(path)
        for b in bars:
            ohlcv = b.get('ohlcv_last_40_bars') or []
            if not ohlcv: continue
            t = ohlcv[-1].get('time')
            if t is None: continue
            if t not in master:
                master[t] = b
                bar_to_window[t] = label
    times_sorted = sorted(master.keys())
    bars_sorted = [master[t] for t in times_sorted]
    print(f"Master: {len(times_sorted)} bars únicos\n")

    # Pra cada bar, captura todos os outcomes nos múltiplos horizons
    # Trigger: NAS LONG/SHORT label nos últimos 5 bars
    # Pra cada trigger LONG/SHORT, registra R em cada horizon
    triggers = []  # {time, window, direction, r_h5, r_h10, ...}
    for i, t in enumerate(times_sorted):
        b = bars_sorted[i]
        ohlcv = b.get('ohlcv_last_40_bars') or []
        close = ohlcv[-1].get('close') if ohlcv else None
        if close is None: continue
        atr = get_atr14(b)
        if not atr or atr <= 0: continue
        c1_long = has_nas_label_recent(b, "LONG", 5)
        c1_short = has_nas_label_recent(b, "SHORT", 5)
        if not (c1_long or c1_short): continue
        # Compute Rs pra todos horizons (skip se algum não disponível)
        rs_long = {}
        rs_short = {}
        for h in HORIZONS:
            if i+h >= len(bars_sorted): continue
            next_close = (bars_sorted[i+h].get('ohlcv_last_40_bars') or [{}])[-1].get('close')
            if next_close is None: continue
            r_l = (next_close - close) / atr
            rs_long[h] = round(r_l, 2)
            rs_short[h] = round(-r_l, 2)
        if c1_long and rs_long:
            triggers.append({'time':t,'window':bar_to_window[t],'direction':'LONG','rs':rs_long})
        if c1_short and rs_short:
            triggers.append({'time':t,'window':bar_to_window[t],'direction':'SHORT','rs':rs_short})

    print(f"{len(triggers)} triggers total\n")

    # Stats por horizon, separado LONG/SHORT/BOTH
    print(f"{'horizon':<8s}  {'dir':<6s}  {'n':>5s}  {'win%':>5s}  {'avg_R':>7s}  {'med_R':>7s}  {'sum_R':>8s}  valid?")
    print("-"*80)
    for h in HORIZONS:
        ts_l = [t for t in triggers if t['direction']=='LONG' and h in t['rs']]
        ts_s = [t for t in triggers if t['direction']=='SHORT' and h in t['rs']]
        rs_l = [t['rs'][h] for t in ts_l]
        rs_s = [t['rs'][h] for t in ts_s]
        s_l = stats_block(rs_l)
        s_s = stats_block(rs_s)
        s_b = stats_block(rs_l + rs_s)
        for dname, s in [('LONG', s_l), ('SHORT', s_s), ('BOTH', s_b)]:
            if s:
                v = "VÁLIDA" if s['win%']>=WIN_GATE else "  -   "
                print(f"H={h:<5d}  {dname:<6s} {s['n']:>5d}  {s['win%']:>5.1f}  {s['avg_R']:>+7.2f}  {s['median_R']:>+7.2f}  {s['sum_R']:>+8.2f}  {v}")
        print()

    # Best horizon by direction
    print("="*80)
    print("BEST horizon por dir (max win%)")
    print("="*80)
    for dname in ['LONG','SHORT','BOTH']:
        best_h = None; best_win = 0
        for h in HORIZONS:
            if dname=='BOTH':
                ts = [t for t in triggers if h in t['rs']]
                rs = [t['rs'][h] for t in ts]
            else:
                ts = [t for t in triggers if t['direction']==dname and h in t['rs']]
                rs = [t['rs'][h] for t in ts]
            s = stats_block(rs)
            if s and s['win%'] > best_win:
                best_win = s['win%']; best_h = h
        print(f"  {dname}: melhor H={best_h} com win%={best_win:.1f}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
