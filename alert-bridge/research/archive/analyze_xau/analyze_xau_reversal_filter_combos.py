#!/usr/bin/env python3
"""
analyze_xau_reversal_filter_combos.py — Testar muitas combinações de filtros pra REVERSAL.

Base: R0 = NAS label LONG/SHORT nos últimos 5 bars (recall 9/10 = 90%)
Sobre R0, testar adicionais:

  F1_dist_extreme: |NAS_DIST| >= 2.0
  F2_rsi_extreme: LONG: RSI<35; SHORT: RSI>65
  F3_bubble_opposite_3: Bubble Sell (LONG) / Bubble Buy (SHORT) últimos 3 bars
  F4_bubble_opposite_10: Bubble nos últimos 10 bars
  F5_ob_match: OB color matching direction (IN ou ±50% near)
  F6_nas_at_bar: NAS label Δ=0 (no bar atual, mais seletivo)
  F7_rsi_cross_50: LONG: RSI<50; SHORT: RSI>50

Cada combinação: (recall_dream, precision_sweep, sample size)
Identificar combos com (recall>=80%, win%>=70%, n>=30 per window)
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

DREAM_TRADES = [
    ("2026-05-04 15:00", "#1", "LONG"),
    ("2026-03-02 23:00", "#2", "SHORT"),
    ("2025-10-21 03:00", "#4", "SHORT"),
    ("2025-11-05 11:00", "#5", "LONG"),
    ("2026-03-12 10:00", "#6", "LONG"),  # gap coleta
    ("2025-11-24 11:00", "#7", "SHORT"),
    ("2026-03-20 14:00", "#8", "LONG"),
    ("2026-03-24 10:00", "#10", "LONG"),
    ("2026-01-29 19:00", "#11", "LONG"),  # contexto estranho
    ("2026-04-15 23:00", "#12", "SHORT"),
    ("2026-02-03 03:00", "#13", "LONG"),
]
DREAM_TOLERANCE_SEC = 7200

COLOR_BULL = 2572201804
COLOR_BEAR = 2566953215
SELL_PLOTS = {"plot_0", "plot_10"}
BUY_PLOTS = {"plot_2", "plot_4", "plot_6", "plot_8"}
BAR_SECONDS_4H = 14400
HORIZON_4H = 10
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
    print("=== FILTER COMBOS — REVERSAL detector ===\n")

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

    dream_ts = []
    for dt_str, tid, direction in DREAM_TRADES:
        ts = int(datetime.strptime(dt_str+"+0000","%Y-%m-%d %H:%M%z").timestamp())
        dream_ts.append((ts, tid, direction))
    dream_total = len(DREAM_TRADES)

    def is_dream(bar_t, direction):
        for d_ts, tid, d_dir in dream_ts:
            if d_dir==direction and abs(bar_t-d_ts) <= DREAM_TOLERANCE_SEC:
                return tid
        return None

    # Compute features pra cada bar
    print("Computando features e outcomes...")
    bar_data = []
    for i, t in enumerate(times_sorted):
        b = bars_sorted[i]
        ohlcv = b.get('ohlcv_last_40_bars') or []
        close = ohlcv[-1].get('close') if ohlcv else None
        if close is None: continue
        atr = get_atr14(b)
        if not atr or atr <= 0: continue
        if i+HORIZON_4H >= len(bars_sorted): continue
        next_close = (bars_sorted[i+HORIZON_4H].get('ohlcv_last_40_bars') or [{}])[-1].get('close')
        if next_close is None: continue
        r_long = (next_close - close) / atr
        r_short = -r_long
        nas_dist = get_nas_dist(b)
        rsi = get_rsi(b)

        features_long = {
            'F0_nas_5':  has_nas_label_recent(b, "LONG", 5),
            'F6_nas_0':  has_nas_label_recent(b, "LONG", 0),
            'F1_dist':   (nas_dist is not None and nas_dist <= -2.0),
            'F2_rsi35':  (rsi is not None and rsi < 35),
            'F7_rsi50':  (rsi is not None and rsi < 50),
            'F3_bub_3':  has_bubble_oposto(b, "LONG", 3),
            'F4_bub_10': has_bubble_oposto(b, "LONG", 10),
            'F5_ob':     has_ob_match(b, "LONG"),
        }
        features_short = {
            'F0_nas_5':  has_nas_label_recent(b, "SHORT", 5),
            'F6_nas_0':  has_nas_label_recent(b, "SHORT", 0),
            'F1_dist':   (nas_dist is not None and nas_dist >= 2.0),
            'F2_rsi65':  (rsi is not None and rsi > 65),
            'F7_rsi50':  (rsi is not None and rsi > 50),
            'F3_bub_3':  has_bubble_oposto(b, "SHORT", 3),
            'F4_bub_10': has_bubble_oposto(b, "SHORT", 10),
            'F5_ob':     has_ob_match(b, "SHORT"),
        }

        bar_data.append({
            'time':t,'window':bar_to_window[t],
            'r_long':round(r_long,2),'r_short':round(r_short,2),
            'dream_long':is_dream(t,"LONG"),'dream_short':is_dream(t,"SHORT"),
            'f_long':features_long,'f_short':features_short,
        })
    print(f"  {len(bar_data)} bars com R+features\n")

    # Define rule sets to test
    # Each rule = base F0_nas_5 + additional list
    rule_sets = []
    # SINGLES
    additionals = ['F1_dist','F3_bub_3','F4_bub_10','F5_ob','F6_nas_0']
    for a in additionals:
        rule_sets.append(('F0+'+a, ['F0_nas_5', a]))
    # PAIRS
    for a1, a2 in combinations(additionals, 2):
        rule_sets.append(('F0+'+a1+'+'+a2, ['F0_nas_5', a1, a2]))
    # TRIPLES
    for a1, a2, a3 in combinations(additionals, 3):
        rule_sets.append(('F0+'+a1+'+'+a2+'+'+a3, ['F0_nas_5', a1, a2, a3]))
    # RSI variants pra LONG only / SHORT only
    rule_sets.insert(0, ('F0_only', ['F0_nas_5']))

    # Pra cada rule, computar (recall, precision, n, per-window)
    print(f"Testando {len(rule_sets)} combos\n")
    results = []
    for name, feats in rule_sets:
        long_trades = []
        short_trades = []
        for bd in bar_data:
            # LONG
            if all(bd['f_long'].get(f) for f in feats):
                long_trades.append({'time':bd['time'],'R':bd['r_long'],'window':bd['window'],'dream':bd['dream_long']})
            # SHORT
            if all(bd['f_short'].get(f) for f in feats):
                short_trades.append({'time':bd['time'],'R':bd['r_short'],'window':bd['window'],'dream':bd['dream_short']})
        all_trades = long_trades + short_trades
        rs = [t['R'] for t in all_trades]
        s = stats_block(rs)
        dreams_captured = len(set(t['dream'] for t in all_trades if t['dream']))
        recall_pct = 100*dreams_captured/dream_total
        # Per window stats
        per_w = defaultdict(list)
        for t in all_trades: per_w[t['window']].append(t['R'])
        per_w_stats = {}
        for w, rs_w in per_w.items():
            sw = stats_block(rs_w)
            per_w_stats[w] = sw
        windows_passing = sum(1 for sw in per_w_stats.values() if sw and sw['n']>=10 and sw['win%']>=WIN_GATE)
        windows_evaluated = sum(1 for sw in per_w_stats.values() if sw and sw['n']>=10)
        results.append({
            'name':name,'n':s['n'] if s else 0,
            'win%':s['win%'] if s else 0,
            'avg_R':s['avg_R'] if s else 0,
            'sum_R':s['sum_R'] if s else 0,
            'recall':recall_pct,'dreams':dreams_captured,
            'wp':windows_passing,'we':windows_evaluated,
        })

    # Sort: priorizar recall>=80 + win%>=70 + n>=200
    results.sort(key=lambda r: (
        -(1 if r['recall']>=70 and r['win%']>=WIN_GATE else 0),
        -r['win%'],
        -r['recall'],
        -r['n']
    ))

    print(f"{'rule':<55s}  {'n':>5s}  {'win%':>5s}  {'avg_R':>7s}  {'sum_R':>8s}  {'recall':>7s}  {'dreams':>7s}  {'wp/we':>6s}")
    print("-"*120)
    for r in results[:50]:
        marker = "★" if r['recall']>=70 and r['win%']>=WIN_GATE else " "
        print(f"{marker}{r['name']:<54s}  {r['n']:>5d}  {r['win%']:>5.1f}  {r['avg_R']:>+7.2f}  {r['sum_R']:>+8.2f}  {r['recall']:>6.0f}%  {r['dreams']:>2d}/{dream_total:<2d}  {r['wp']:>2d}/{r['we']:<2d}")

    print(f"\n★ = passa recall>=70% E win%>={WIN_GATE}%")
    print(f"\nWP = windows passing gate (n>=10), WE = windows evaluated\n")

    # Top 5 detalhes per-window
    print("="*120)
    print("TOP 5 RULES — detalhe per-window")
    print("="*120)
    for r in results[:5]:
        print(f"\n  [{r['name']}]")
        feats = []
        for rname, fs in rule_sets:
            if rname == r['name']:
                feats = fs; break
        long_trades = []
        short_trades = []
        for bd in bar_data:
            if all(bd['f_long'].get(f) for f in feats):
                long_trades.append({'time':bd['time'],'R':bd['r_long'],'window':bd['window']})
            if all(bd['f_short'].get(f) for f in feats):
                short_trades.append({'time':bd['time'],'R':bd['r_short'],'window':bd['window']})
        all_trades = long_trades + short_trades
        per_w = defaultdict(list)
        for t in all_trades: per_w[t['window']].append(t['R'])
        print(f"    {'window':<14s} {'n':>4s} {'win%':>5s} {'avg_R':>7s} {'sum_R':>8s}")
        for wlabel, _ in WINDOWS_V3:
            rs_w = per_w.get(wlabel, [])
            sw = stats_block(rs_w)
            if sw:
                v = "✓" if sw['n']>=10 and sw['win%']>=WIN_GATE else " "
                print(f"    {wlabel:<14s} {sw['n']:>4d} {sw['win%']:>5.1f} {sw['avg_R']:>+7.2f} {sw['sum_R']:>+8.2f}  {v}")
            else:
                print(f"    {wlabel:<14s} {0:>4d}  -")

    return 0


if __name__ == "__main__":
    sys.exit(main())
