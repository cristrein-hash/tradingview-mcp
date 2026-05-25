#!/usr/bin/env python3
"""
analyze_xau_reversal_deep_dive.py — Deep debug das 6 dream trades NÃO capturadas.

Pra cada uma:
  - Bar exato (bar open time XAU 4H)
  - TODOS os NAS labels recentes (text + x_delta)
  - Bubbles em janelas 3, 5, 10, 20 candles
  - OB boxes ativas (cor + distância)
  - RSI evolution últimos 30 bars
  - Price action contexto (high/low últimos 10 bars, swing structure)
  - ATR 4H atual vs typical
  - dist_14d_high (regime macro)
  - Slope EMA50 5d (mas precisa daily — vou pular ou aproximar)

Objetivo: encontrar feature comum entre as 6 que o detector atual ignora.
"""
from pathlib import Path
from datetime import datetime, timezone
from statistics import mean
import json, sys

BASE = Path(__file__).parent.parent
JSONL_DIR = BASE / "alert-bridge" / "logs" / "backtests"

WINDOWS_V3 = [
    "XAUUSD_240_2023-01-19_to_2026-05-20_v3.jsonl",
    "XAUUSD_240_2023-07-19_to_2026-05-20_v3.jsonl",
    "XAUUSD_240_2024-01-19_to_2026-05-20_v3.jsonl",
    "XAUUSD_240_2024-07-19_to_2026-05-20_v3.jsonl",
    "XAUUSD_240_2025-05-19_to_2026-05-20_v3.jsonl",
    "XAUUSD_240_2025-09-15_to_2026-05-20_v3.jsonl",
    "XAUUSD_240_2025-11-19_to_2026-05-20_v3.jsonl",
    "XAUUSD_240_2026-03-19_to_2026-05-20_v3.jsonl",
]

# 6 dream trades NÃO capturadas pelo R0 (bar open times)
TARGETS_NOT_CAPTURED = [
    # Após DST fix tolerance, só #6 e #11 ficaram não capturadas
    ("#6",  "2026-03-12 10:00", "LONG"),
    ("#11", "2026-01-29 19:00", "LONG"),
]

# 5 dream trades CAPTURADAS — pra comparar
TARGETS_CAPTURED = [
    ("#1",  "2026-05-04 14:00", "LONG"),
    ("#4",  "2025-10-21 02:00", "SHORT"),
    ("#8",  "2026-03-20 14:00", "LONG"),
    ("#10", "2026-03-24 10:00", "LONG"),
    ("#12", "2026-04-15 22:00", "SHORT"),
]

SELL_PLOTS = {"plot_0", "plot_10"}
BUY_PLOTS = {"plot_2", "plot_4", "plot_6", "plot_8"}
COLOR_BULL = 2572201804
COLOR_BEAR = 2566953215
BAR_SECONDS_4H = 14400


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


def parse_dt(s):
    return int(datetime.strptime(s+"+0000", "%Y-%m-%d %H:%M%z").timestamp())


def main():
    print("=== DEEP DIVE — 2 dream trades NÃO capturadas + 5 capturadas (comparação) ===\n")

    # Construir master timeline
    master = {}
    bar_to_window = {}
    for fname in WINDOWS_V3:
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
                bar_to_window[t] = fname

    print(f"Master: {len(master)} bars únicos\n")
    times_sorted = sorted(master.keys())

    def find_bar_with_tolerance(target_ts, tol=7200):
        """Encontra bar dentro de ±tol seconds do target."""
        best_t = None; best_delta = None
        for t in times_sorted:
            d = abs(t - target_ts)
            if d <= tol and (best_delta is None or d < best_delta):
                best_delta = d; best_t = t
        return best_t

    def analyze_trade(tid, dt_str, direction, group):
        target_ts = parse_dt(dt_str)
        bar_t = find_bar_with_tolerance(target_ts)
        if bar_t is None:
            print(f"\n  [{group}] {tid} {dt_str} {direction} — BAR NOT FOUND within ±2h")
            return
        bar = master[bar_t]
        delta_min = (bar_t - target_ts) // 60
        if delta_min != 0:
            print(f"\n  [{group}] {tid} {dt_str} {direction}  (matched bar Δ={delta_min}min)")

        ohlcv = bar.get('ohlcv_last_40_bars') or []
        close = ohlcv[-1].get('close') if ohlcv else None
        high = ohlcv[-1].get('high') if ohlcv else None
        low = ohlcv[-1].get('low') if ohlcv else None
        open_ = ohlcv[-1].get('open') if ohlcv else None
        prev_close = ohlcv[-2].get('close') if len(ohlcv)>=2 else None

        bar_pct_change = ((close - open_)/open_*100) if (close and open_) else None
        # 10 bars previous range
        recent10 = ohlcv[-10:] if len(ohlcv)>=10 else ohlcv
        rng10_h = max(b['high'] for b in recent10) if recent10 else None
        rng10_l = min(b['low'] for b in recent10) if recent10 else None
        # is this bar a sweep? (extreme low for LONG or extreme high for SHORT)
        is_sweep_low = (low == rng10_l) if direction=="LONG" else None
        is_sweep_high = (high == rng10_h) if direction=="SHORT" else None
        # body % of range
        body = abs(close - open_) if close and open_ else 0
        candle_range = high - low if high and low else 0
        body_pct = (body / candle_range * 100) if candle_range > 0 else 0
        # bullish or bearish candle
        is_bull_candle = close > open_ if (close and open_) else None

        print(f"\n  ═══ [{group}] {tid}  {dt_str}  {direction} ═══")
        print(f"  Bar OHLC: O={open_:.2f} H={high:.2f} L={low:.2f} C={close:.2f}")
        print(f"  Body: {body:.2f} ({body_pct:.0f}% of range) | candle_change={bar_pct_change:+.2f}% | bull_candle={is_bull_candle}")
        if direction=="LONG":
            print(f"  Sweep low? {is_sweep_low}  | last 10 bars range: {rng10_l:.2f} - {rng10_h:.2f}")
        else:
            print(f"  Sweep high? {is_sweep_high}  | last 10 bars range: {rng10_l:.2f} - {rng10_h:.2f}")

        # NAS labels — TODOS os recentes (não só ±5)
        for s in (bar.get('pine_labels') or []):
            if 'NAS' not in s.get('name','').upper(): continue
            labels = s.get('labels') or []
            if not labels: continue
            xs = [l.get('x') for l in labels if l.get('x') is not None]
            max_x = max(xs) if xs else 0
            print(f"  NAS labels recent (sorted by x_delta from current):")
            sorted_by_x = sorted(labels, key=lambda x: max_x - x.get('x',0))
            for l in sorted_by_x[:15]:
                lx = l.get('x'); txt = l.get('text','')
                delta = max_x - lx if lx is not None else None
                if delta is not None and delta <= 20:
                    print(f"    Δ={delta:>3d}  text={txt:<6s}  price={l.get('price','?')}")
            break

        # NAS study_values atual
        for s in (bar.get('study_values') or []):
            if 'NAS' in s.get('name',''):
                vals = s.get('values') or {}
                print(f"  NAS_DIST values: {vals}")
                break
        # RSI atual
        for s in (bar.get('study_values') or []):
            if 'Relative Strength' in s.get('name',''):
                vals = s.get('values') or {}
                print(f"  RSI values: {vals}")
                break

        # Bubbles — múltiplas janelas
        want_plots_for_exh = SELL_PLOTS if direction == "LONG" else BUY_PLOTS
        for lb in [3, 5, 10, 20]:
            t_lb = target_ts - (lb-1)*BAR_SECONDS_4H
            hits = []
            for s in (bar.get('pine_shapes_bubbles') or []):
                if 'Bubbles' not in s.get('name',''): continue
                for act in s.get('activations', []):
                    t = act.get('time')
                    if t is None: continue
                    if t_lb <= t <= target_ts:
                        for p in (act.get('shapes') or {}):
                            if p in want_plots_for_exh:
                                hits.append((t, p))
            if hits:
                hit_summary = {}
                for t,p in hits:
                    hit_summary.setdefault(p, []).append((target_ts-t)//BAR_SECONDS_4H)
                print(f"  Bubble exhaustion oposto janela {lb}: {hit_summary}")
            else:
                print(f"  Bubble exhaustion oposto janela {lb}: -")

        # OB boxes — qual contém o close ou está perto?
        want_color = COLOR_BULL if direction == "LONG" else COLOR_BEAR
        ob_info = []
        for s in (bar.get('pine_boxes') or []):
            if 'Custom OB' not in s.get('name',''): continue
            for box in (s.get('all_boxes') or []):
                hi, lo = box.get('high'), box.get('low')
                bc = box.get('borderColor')
                if hi is None or lo is None: continue
                bul = "bull" if bc==COLOR_BULL else ("bear" if bc==COLOR_BEAR else "?")
                if lo <= close <= hi:
                    ob_info.append(f"IN_{bul}[{lo:.0f}-{hi:.0f}]")
                else:
                    dist = max((close-hi) if close>hi else 0, (lo-close) if close<lo else 0)
                    zone_size = hi - lo
                    pct = dist/zone_size if zone_size>0 else 0
                    if pct < 1.0:  # within zone-width away
                        ob_info.append(f"near_{bul}_{int(pct*100)}%[{lo:.0f}-{hi:.0f}]")
        if ob_info:
            print(f"  OB context: {' | '.join(ob_info[:5])}")
        else:
            print(f"  OB context: NO OB near")

    print("\n############ DREAM TRADES NÃO CAPTURADAS ############")
    for tid, dt_str, direction in TARGETS_NOT_CAPTURED:
        analyze_trade(tid, dt_str, direction, "NOT_CAP")

    print("\n\n############ DREAM TRADES CAPTURADAS (comparação) ############")
    for tid, dt_str, direction in TARGETS_CAPTURED:
        analyze_trade(tid, dt_str, direction, "CAP")

    return 0


if __name__ == "__main__":
    sys.exit(main())
