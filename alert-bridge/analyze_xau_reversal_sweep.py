#!/usr/bin/env python3
"""
analyze_xau_reversal_sweep.py — Sweep do detector REVERSAL nas 8 janelas.

Pra cada bar das 8 janelas v3, aplica regras candidatas e calcula outcome H=10 bars.
Compara recall (dream trades capturadas) vs precision (win% triggers totais).

Regras:
  R0: NAS label LONG/SHORT nos últimos 5 bars (sem outros filtros)
  R1: R0 + Bubble exhaustion oposto últimos 10 bars
  R2: R0 + OB direction proximity (IN ou ±50% zone size)
  R3: R0 + R1 + R2 (todas confluências)
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

DREAM_TRADES = {
    # crosshair Cris (DST-naive). Sweep faz match ±2h tolerance pra encontrar bar 4H certo.
    # Verão (BST): bars abrem 02/06/10/14/18/22 UTC
    # Inverno (GMT): bars abrem 03/07/11/15/19/23 UTC
    "2026-05-04 15:00": ("#1", "LONG"),
    "2026-03-02 23:00": ("#2", "SHORT"),
    "2025-10-21 03:00": ("#4", "SHORT"),
    "2025-11-05 11:00": ("#5", "LONG"),
    "2026-03-12 10:00": ("#6", "LONG"),
    "2025-11-24 11:00": ("#7", "SHORT"),
    "2026-03-20 14:00": ("#8", "LONG"),
    "2026-03-24 10:00": ("#10", "LONG"),
    "2026-01-29 19:00": ("#11", "LONG"),
    "2026-04-15 23:00": ("#12", "SHORT"),
    "2026-02-03 03:00": ("#13", "LONG"),
}
DREAM_MATCH_TOLERANCE_SEC = 7200  # ±2h tolerance pra match bar 4H DST-aware

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
    """Retorna True se NAS label com text=want_text apareceu nos últimos max_delta bars do chart TV."""
    for s in (bar.get('pine_labels') or []):
        if 'NAS' not in s.get('name','').upper(): continue
        labels = s.get('labels') or []
        if not labels: continue
        xs = [lbl.get('x') for lbl in labels if lbl.get('x') is not None]
        if not xs: continue
        max_x = max(xs)
        for lbl in labels:
            lx = lbl.get('x')
            txt = (lbl.get('text') or '').upper()
            if lx is None or txt != want_text: continue
            delta = max_x - lx
            if 0 <= delta <= max_delta:
                return True
    return False


def has_bubble_exhaustion(bar, direction, lookback=10):
    """LONG: Sell bubbles nos últimos 'lookback' bars. SHORT: Buy bubbles."""
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
                    if p in want_plots:
                        return True
    return False


def has_ob_proximity(bar, direction):
    """OB matching direction (proximity ±50% zone size)."""
    ohlcv = bar.get('ohlcv_last_40_bars') or []
    close = ohlcv[-1].get('close') if ohlcv else None
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
            if lo <= close <= hi:
                return True
            dist = max((close - hi) if close > hi else 0, (lo - close) if close < lo else 0)
            if dist <= zone_size * 0.5:
                return True
    return False


def stats_block(rs):
    if not rs: return None
    wins = sum(1 for r in rs if r>0)
    return {
        'n':len(rs),'win%':100*wins/len(rs),
        'avg_R':mean(rs),'median_R':median(rs),
        'sum_R':sum(rs),
    }


def main():
    print(f"=== SWEEP DETECTOR REVERSAL — 8 janelas v3 ===\n")

    # Carrega TODOS bars de TODOS JSONLs, dedup por timestamp
    print("Carregando 8 JSONLs e construindo série mestre...")
    master = {}
    bar_to_window = {}  # time -> window label
    for label, fname in WINDOWS_V3:
        path = JSONL_DIR / fname
        if not path.exists(): continue
        bars = load_bars(path)
        for b in bars:
            ohlcv = b.get('ohlcv_last_40_bars') or []
            if not ohlcv: continue
            t = ohlcv[-1].get('time')
            if t is None: continue
            if t not in master:  # primeira janela que cobre fica
                master[t] = b
                bar_to_window[t] = label
    times_sorted = sorted(master.keys())
    bars_sorted = [master[t] for t in times_sorted]
    print(f"  {len(times_sorted)} bars únicos\n")

    # Pra cada bar, aplica regras e gera triggers
    # Pre-compute dream timestamps para match com tolerance
    dream_ts_list = []  # list of (target_ts, tid, direction)
    for dt_str, (tid, direction) in DREAM_TRADES.items():
        target_ts = int(datetime.strptime(dt_str+"+0000", "%Y-%m-%d %H:%M%z").timestamp())
        dream_ts_list.append((target_ts, tid, direction))

    def find_dream_match(bar_ts, direction):
        """Match bar_ts com dream trade dentro de ±DREAM_MATCH_TOLERANCE_SEC e mesma direção."""
        for d_ts, tid, d_dir in dream_ts_list:
            if d_dir != direction: continue
            if abs(bar_ts - d_ts) <= DREAM_MATCH_TOLERANCE_SEC:
                return tid
        return None
    dream_keys = set(DREAM_TRADES.keys())  # placeholder, não usado mais
    triggers = {  # rule_name -> {LONG: [trades], SHORT: [trades]}
        'R0_NAS_only': defaultdict(list),
        'R1_NAS_BubExh': defaultdict(list),
        'R2_NAS_OB': defaultdict(list),
        'R3_NAS_BubExh_OB': defaultdict(list),
    }

    for i, t in enumerate(times_sorted):
        b = bars_sorted[i]
        ohlcv = b.get('ohlcv_last_40_bars') or []
        close = ohlcv[-1].get('close') if ohlcv else None
        if close is None: continue
        atr = get_atr14(b)
        if not atr or atr <= 0: continue
        # Calcula outcome H=10 bars
        if i+HORIZON_4H >= len(bars_sorted): continue
        next_close = (bars_sorted[i+HORIZON_4H].get('ohlcv_last_40_bars') or [{}])[-1].get('close')
        if next_close is None: continue
        r_long = (next_close - close) / atr
        r_short = -r_long
        dt_str = datetime.fromtimestamp(t, tz=timezone.utc).strftime("%Y-%m-%d %H:%M")
        dream_long_match = find_dream_match(t, "LONG")
        dream_short_match = find_dream_match(t, "SHORT")

        # Check confluências
        c1_long = has_nas_label_recent(b, "LONG", max_delta=5)
        c1_short = has_nas_label_recent(b, "SHORT", max_delta=5)
        c2_long = has_bubble_exhaustion(b, "LONG", lookback=10)
        c2_short = has_bubble_exhaustion(b, "SHORT", lookback=10)
        c5_long = has_ob_proximity(b, "LONG")
        c5_short = has_ob_proximity(b, "SHORT")

        # LONG triggers
        if c1_long:
            trade = {'time':t,'dt':dt_str,'R':round(r_long,2),'window':bar_to_window[t],'is_dream':bool(dream_long_match),'dream_id':dream_long_match}
            triggers['R0_NAS_only']['LONG'].append(trade)
            if c2_long:
                triggers['R1_NAS_BubExh']['LONG'].append(trade)
            if c5_long:
                triggers['R2_NAS_OB']['LONG'].append(trade)
            if c2_long and c5_long:
                triggers['R3_NAS_BubExh_OB']['LONG'].append(trade)
        # SHORT triggers
        if c1_short:
            trade = {'time':t,'dt':dt_str,'R':round(r_short,2),'window':bar_to_window[t],'is_dream':bool(dream_short_match),'dream_id':dream_short_match}
            triggers['R0_NAS_only']['SHORT'].append(trade)
            if c2_short:
                triggers['R1_NAS_BubExh']['SHORT'].append(trade)
            if c5_short:
                triggers['R2_NAS_OB']['SHORT'].append(trade)
            if c2_short and c5_short:
                triggers['R3_NAS_BubExh_OB']['SHORT'].append(trade)

    # Reporta por regra: LONG, SHORT, combined
    print(f"{'regra':<22s} {'dir':<6s} {'n':>5s} {'win%':>5s} {'avg_R':>7s} {'med_R':>7s} {'sum_R':>7s} {'dreams':>7s} {'recall%':>8s} valid?")
    print("-"*100)

    dream_long_n = sum(1 for v in DREAM_TRADES.values() if v[1]=='LONG')
    dream_short_n = sum(1 for v in DREAM_TRADES.values() if v[1]=='SHORT')
    dream_total_n = len(DREAM_TRADES)

    for rname, dir_trades in triggers.items():
        # LONG
        ts_l = dir_trades.get('LONG',[])
        rs_l = [t['R'] for t in ts_l]
        s_l = stats_block(rs_l)
        dreams_l = len(set(t['dream_id'] for t in ts_l if t['is_dream'] and t['dream_id']))
        recall_l = 100*dreams_l/max(1,dream_long_n)
        if s_l:
            valid = "VÁLIDA" if s_l['win%']>=WIN_GATE else "  -   "
            print(f"  {rname:<22s} {'LONG':<6s} {s_l['n']:>5d} {s_l['win%']:>5.1f} {s_l['avg_R']:>+7.2f} {s_l['median_R']:>+7.2f} {s_l['sum_R']:>+7.2f} {dreams_l:>4d}/{dream_long_n:>2d} {recall_l:>7.0f}% {valid}")
        # SHORT
        ts_s = dir_trades.get('SHORT',[])
        rs_s = [t['R'] for t in ts_s]
        s_s = stats_block(rs_s)
        dreams_s = len(set(t['dream_id'] for t in ts_s if t['is_dream'] and t['dream_id']))
        recall_s = 100*dreams_s/max(1,dream_short_n)
        if s_s:
            valid = "VÁLIDA" if s_s['win%']>=WIN_GATE else "  -   "
            print(f"  {rname:<22s} {'SHORT':<6s} {s_s['n']:>5d} {s_s['win%']:>5.1f} {s_s['avg_R']:>+7.2f} {s_s['median_R']:>+7.2f} {s_s['sum_R']:>+7.2f} {dreams_s:>4d}/{dream_short_n:>2d} {recall_s:>7.0f}% {valid}")
        # Combined
        ts_c = ts_l + ts_s
        rs_c = [t['R'] for t in ts_c]
        s_c = stats_block(rs_c)
        dreams_c = dreams_l + dreams_s
        recall_c = 100*dreams_c/max(1,dream_total_n)
        if s_c:
            valid = "VÁLIDA" if s_c['win%']>=WIN_GATE else "  -   "
            print(f"  {rname:<22s} {'BOTH':<6s} {s_c['n']:>5d} {s_c['win%']:>5.1f} {s_c['avg_R']:>+7.2f} {s_c['median_R']:>+7.2f} {s_c['sum_R']:>+7.2f} {dreams_c:>4d}/{dream_total_n:>2d} {recall_c:>7.0f}% {valid}")
        print()

    # Por janela — só R0 e R3 (extremos)
    print(f"\n{'='*100}")
    print("PER WINDOW — R0_NAS_only vs R3_NAS_BubExh_OB (BOTH directions combined)")
    print(f"{'='*100}")
    for rname in ['R0_NAS_only', 'R3_NAS_BubExh_OB']:
        ts_all = triggers[rname].get('LONG',[]) + triggers[rname].get('SHORT',[])
        per_w = defaultdict(list)
        for t in ts_all:
            per_w[t['window']].append(t)
        print(f"\n  [{rname}]")
        print(f"    {'window':<14s} {'n':>4s} {'win%':>5s} {'avg_R':>7s} {'sum_R':>7s}")
        for wlabel, _ in WINDOWS_V3:
            ts = per_w.get(wlabel, [])
            rs = [t['R'] for t in ts]
            s = stats_block(rs)
            if s:
                valid = "VÁLIDA" if s['win%']>=WIN_GATE else "  -   "
                print(f"    {wlabel:<14s} {s['n']:>4d} {s['win%']:>5.1f} {s['avg_R']:>+7.2f} {s['sum_R']:>+7.2f}  {valid}")
            else:
                print(f"    {wlabel:<14s} {0:>4d}  -")

    # Dream trades capturadas: quais regras pegaram cada dream
    print(f"\n{'='*100}")
    print("DREAM TRADES — quais regras capturaram cada uma")
    print(f"{'='*100}")
    print(f"  {'#':<4s} {'datetime':<18s} {'dir':<6s} {'R0_NAS':<7s} {'R1_BubE':<7s} {'R2_OB':<7s} {'R3_All':<7s} {'R_outcome':>10s}")
    for dt_str, (tid, direction) in DREAM_TRADES.items():
        marks = {}
        r_outcome = None
        bar_dt = None
        for rname, dirs in triggers.items():
            found = any(t['dream_id']==tid for t in dirs.get(direction,[]))
            marks[rname] = "✓" if found else "·"
            if found and r_outcome is None:
                for t in dirs.get(direction,[]):
                    if t['dream_id']==tid:
                        r_outcome = t['R']
                        bar_dt = t['dt']
                        break
        r_str = f"{r_outcome:+.2f}" if r_outcome is not None else "-"
        bar_str = bar_dt if bar_dt else "-"
        print(f"  {tid:<4s} {dt_str:<18s}→{bar_str:<18s} {direction:<6s} {marks['R0_NAS_only']:<7s} {marks['R1_NAS_BubExh']:<7s} {marks['R2_NAS_OB']:<7s} {marks['R3_NAS_BubExh_OB']:<7s} {r_str:>10s}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
