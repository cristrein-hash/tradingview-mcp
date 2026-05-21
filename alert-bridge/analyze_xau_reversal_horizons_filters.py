#!/usr/bin/env python3
"""
analyze_xau_reversal_horizons_filters.py — Filter combos sobre LONG/SHORT separados em H=10/20/30.

Sobre base F0_nas_5, testa todas as combinações de filtros adicionais:
  F1_dist:    NAS_DIST extremo direção (LONG: <-2; SHORT: >+2)
  F2_rsi_ext: RSI extremo (LONG: <35; SHORT: >65)
  F3_bub_3:   Bubble exhaustion oposto 3 candles
  F4_bub_10:  Bubble exhaustion oposto 10 candles
  F5_ob:      OB direction matching
  F6_nas_0:   NAS label EXATAMENTE no bar atual (Δ=0)

Pra cada combo, mostra LONG separado, SHORT separado, em horizons 10/20/30.
Encontra combo que atinge win% >=70% com sample size razoável.
"""
from pathlib import Path
from datetime import datetime, timezone
from statistics import mean, median
import json, sys
from collections import defaultdict
from itertools import combinations

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

HORIZONS = [10, 20, 30]
COLOR_BULL = 2572201804
COLOR_BEAR = 2566953215
SELL_PLOTS = {"plot_0", "plot_10"}
BUY_PLOTS = {"plot_2", "plot_4", "plot_6", "plot_8"}
BAR_SECONDS_4H = 14400
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


def has_bubble_oposto(bar, direction, lookback=10):
    entry_time = (bar.get('ohlcv_last_40_bars') or [{}])[-1].get('time')
    if entry_time is None: return False
    want_plots = SELL_PLOTS if direction == "LONG" else BUY_PLOTS
    t_lb = entry_time - (lookback-1)*BAR_SECONDS_4H
    for s in (bar.get('pine_shapes_bubbles') or []):
        if 'Bubbles' not in s.get('name',''): continue
        for act in s.get('activations', []):
            t = act.get('time')
            if t is None: continue
            if t_lb <= t <= entry_time:
                for p in (act.get('shapes') or {}):
                    if p in want_plots: return True
    return False


def get_nas_dist(bar):
    for s in (bar.get('study_values') or []):
        if 'NAS' in s.get('name',''):
            v = s.get('values',{}).get('NAS_DISTANCE_FROM_EMA_ATR','')
            try: return float(v.replace('−','-'))
            except: return None
    return None


def get_rsi(bar):
    for s in (bar.get('study_values') or []):
        if 'Relative Strength' in s.get('name',''):
            v = s.get('values',{}).get('RSI','')
            try: return float(v.replace('−','-'))
            except: return None
    return None


def has_ob_match(bar, direction):
    close = (bar.get('ohlcv_last_40_bars') or [{}])[-1].get('close')
    if close is None: return False
    want_color = COLOR_BULL if direction == "LONG" else COLOR_BEAR
    for s in (bar.get('pine_boxes') or []):
        if 'Custom OB' not in s.get('name',''): continue
        for box in (s.get('all_boxes') or []):
            hi, lo = box.get('high'), box.get('low')
            bc = box.get('borderColor')
            if hi is None or lo is None or bc != want_color: continue
            zone_size = hi - lo
            if zone_size <= 0: continue
            if lo <= close <= hi: return True
            dist = max((close-hi) if close>hi else 0, (lo-close) if close<lo else 0)
            if dist <= zone_size * 0.5: return True
    return False


def stats_block(rs):
    if not rs: return None
    wins = sum(1 for r in rs if r>0)
    return {'n':len(rs),'win%':100*wins/len(rs),'avg_R':mean(rs),'median_R':median(rs),'sum_R':sum(rs)}


def main():
    print(f"=== FILTER COMBOS LONG/SHORT separados, horizons {HORIZONS} ===\n")

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

    # Compute features + outcomes pra cada bar
    print("Computando...")
    bar_data = []
    for i, t in enumerate(times_sorted):
        b = bars_sorted[i]
        ohlcv = b.get('ohlcv_last_40_bars') or []
        close = ohlcv[-1].get('close') if ohlcv else None
        if close is None: continue
        atr = get_atr14(b)
        if not atr or atr <= 0: continue
        # outcomes
        rs_long = {}; rs_short = {}
        for h in HORIZONS:
            if i+h >= len(bars_sorted): continue
            next_close = (bars_sorted[i+h].get('ohlcv_last_40_bars') or [{}])[-1].get('close')
            if next_close is None: continue
            r_l = (next_close - close) / atr
            rs_long[h] = round(r_l, 2)
            rs_short[h] = round(-r_l, 2)
        if not rs_long: continue
        nas_dist = get_nas_dist(b)
        rsi = get_rsi(b)
        # features per direction
        f_long = {
            'F0': has_nas_label_recent(b, "LONG", 5),
            'F1_dist': (nas_dist is not None and nas_dist <= -2.0),
            'F2_rsi_ext': (rsi is not None and rsi < 35),
            'F3_bub_3': has_bubble_oposto(b, "LONG", 3),
            'F4_bub_10': has_bubble_oposto(b, "LONG", 10),
            'F5_ob': has_ob_match(b, "LONG"),
            'F6_nas_0': has_nas_label_recent(b, "LONG", 0),
        }
        f_short = {
            'F0': has_nas_label_recent(b, "SHORT", 5),
            'F1_dist': (nas_dist is not None and nas_dist >= 2.0),
            'F2_rsi_ext': (rsi is not None and rsi > 65),
            'F3_bub_3': has_bubble_oposto(b, "SHORT", 3),
            'F4_bub_10': has_bubble_oposto(b, "SHORT", 10),
            'F5_ob': has_ob_match(b, "SHORT"),
            'F6_nas_0': has_nas_label_recent(b, "SHORT", 0),
        }
        bar_data.append({
            'time':t,'window':bar_to_window[t],
            'rs_long':rs_long,'rs_short':rs_short,
            'f_long':f_long,'f_short':f_short,
        })

    additionals = ['F1_dist','F2_rsi_ext','F3_bub_3','F4_bub_10','F5_ob','F6_nas_0']
    rule_sets = [('F0_only', ['F0'])]
    for a in additionals:
        rule_sets.append(('F0+'+a, ['F0', a]))
    for a1, a2 in combinations(additionals, 2):
        rule_sets.append(('F0+'+a1+'+'+a2, ['F0', a1, a2]))
    for a1, a2, a3 in combinations(additionals, 3):
        rule_sets.append(('F0+'+a1+'+'+a2+'+'+a3, ['F0', a1, a2, a3]))

    print(f"Total combos: {len(rule_sets)}")

    # Pra cada combo, computar resultados LONG e SHORT separados em todos horizons
    results = []
    for name, feats in rule_sets:
        for dname, fkey, rskey in [('LONG','f_long','rs_long'), ('SHORT','f_short','rs_short')]:
            matched = [bd for bd in bar_data if all(bd[fkey].get(f) for f in feats)]
            for h in HORIZONS:
                rs = [bd[rskey][h] for bd in matched if h in bd[rskey]]
                s = stats_block(rs)
                if not s: continue
                # per window count
                per_w_n = defaultdict(int)
                for bd in matched:
                    if h in bd[rskey]:
                        per_w_n[bd['window']] += 1
                windows_with_n10 = sum(1 for w, n in per_w_n.items() if n >= 10)
                # win% per window
                per_w_win = []
                for wlabel, _ in WINDOWS_V3:
                    rs_w = [bd[rskey][h] for bd in matched if bd['window']==wlabel and h in bd[rskey]]
                    sw = stats_block(rs_w)
                    if sw and sw['n']>=10:
                        per_w_win.append(sw['win%'])
                windows_passing = sum(1 for w in per_w_win if w >= WIN_GATE)
                results.append({
                    'name':name,'dir':dname,'h':h,
                    'n':s['n'],'win%':s['win%'],'avg_R':s['avg_R'],'sum_R':s['sum_R'],
                    'wp':windows_passing,'we':len(per_w_win),
                })

    # Sort: priorizar win% high + n>=200
    valid_results = [r for r in results if r['n'] >= 100]
    valid_results.sort(key=lambda r: (-r['win%'], -r['n']))

    print(f"\n=== TOP 30 combos por win% (n>=100) ===")
    print(f"{'rule':<48s} {'dir':<6s} {'H':>3s} {'n':>5s} {'win%':>5s} {'avg_R':>7s} {'sum_R':>8s} {'wp/we':>6s}")
    print("-"*100)
    for r in valid_results[:30]:
        marker = "★" if r['win%']>=WIN_GATE else " "
        print(f"{marker}{r['name']:<47s} {r['dir']:<6s} {r['h']:>3d} {r['n']:>5d} {r['win%']:>5.1f} {r['avg_R']:>+7.2f} {r['sum_R']:>+8.2f} {r['wp']:>2d}/{r['we']:<2d}")

    # Focus: passing gate
    passing = [r for r in results if r['win%']>=WIN_GATE and r['n']>=50]
    passing.sort(key=lambda r: (-r['wp'], -r['win%']))
    if passing:
        print(f"\n=== COMBOS QUE PASSAM GATE (win%>=70, n>=50) ===")
        print(f"{'rule':<48s} {'dir':<6s} {'H':>3s} {'n':>5s} {'win%':>5s} {'avg_R':>7s} {'sum_R':>8s} {'wp/we':>6s}")
        for r in passing[:30]:
            print(f"  {r['name']:<48s} {r['dir']:<6s} {r['h']:>3d} {r['n']:>5d} {r['win%']:>5.1f} {r['avg_R']:>+7.2f} {r['sum_R']:>+8.2f} {r['wp']:>2d}/{r['we']:<2d}")
    else:
        print(f"\nNenhum combo passa gate {WIN_GATE}% com n>=50.")

    # Best LONG combo per horizon
    print(f"\n=== BEST LONG combo por horizon (n>=100) ===")
    for h in HORIZONS:
        long_h = [r for r in results if r['dir']=='LONG' and r['h']==h and r['n']>=100]
        long_h.sort(key=lambda r: -r['win%'])
        if long_h:
            r = long_h[0]
            print(f"  H={h:>2d}: {r['name']:<40s} n={r['n']:>4d} win%={r['win%']:>5.1f} avg_R={r['avg_R']:>+5.2f}")

    print(f"\n=== BEST SHORT combo por horizon (n>=100) ===")
    for h in HORIZONS:
        short_h = [r for r in results if r['dir']=='SHORT' and r['h']==h and r['n']>=100]
        short_h.sort(key=lambda r: -r['win%'])
        if short_h:
            r = short_h[0]
            print(f"  H={h:>2d}: {r['name']:<40s} n={r['n']:>4d} win%={r['win%']:>5.1f} avg_R={r['avg_R']:>+5.2f}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
