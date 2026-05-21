#!/usr/bin/env python3
"""
analyze_xau_reversal_dream_trades.py — Analisa 11 dream trades REVERSAL contra 5 confluências.

Dream trades (definidas por Cris 2026-05-20):
  LONG REVERSAL (em bottoms): #1, #5, #6, #8, #10, #11, #13
  SHORT REVERSAL (em tops): #2, #4, #7, #12
  (#9 é DEMAND_BREAKOUT continuação, fora deste escopo)

5 confluências a checar:
  C1. NAS label TOP/BOTTOM próximo (±3 bars)
  C2. Bubble exhaustion oposto (Large Buy em TOP / Large Sell em BOTTOM) últimos 5-10 bars
  C3. RSI divergence local (Bull div pra LONG, Bear div pra SHORT)
  C4. CHoCH/BOS direction (label NAS)
  C5. IN_OB direction correta (bull demand pra LONG, bear supply pra SHORT)
"""
from pathlib import Path
from datetime import datetime, timezone
from statistics import mean
import json, sys
from collections import defaultdict

BASE = Path(__file__).parent.parent
JSONL_DIR = BASE / "alert-bridge" / "logs" / "backtests"

WINDOWS_V2 = [
    "XAUUSD_240_2023-01-19_to_2026-05-20_v3.jsonl",
    "XAUUSD_240_2023-07-19_to_2026-05-20_v3.jsonl",
    "XAUUSD_240_2024-01-19_to_2026-05-20_v3.jsonl",
    "XAUUSD_240_2024-07-19_to_2026-05-20_v3.jsonl",
    "XAUUSD_240_2025-05-19_to_2026-05-20_v3.jsonl",
    "XAUUSD_240_2025-09-15_to_2026-05-20_v3.jsonl",  # W8 (cobre #4 e #5)
    "XAUUSD_240_2025-11-19_to_2026-05-20_v3.jsonl",
    "XAUUSD_240_2026-03-19_to_2026-05-20_v3.jsonl",
]

DREAM_TRADES = [
    # (id, entry_dt_str, direction, note)
    ("#1",  "2026-05-04 15:00", "LONG",  "Bottom region"),
    ("#2",  "2026-03-02 23:00", "SHORT", "Top cluster"),
    ("#4",  "2025-10-21 03:00", "SHORT", "Rally top pre-crash"),
    ("#5",  "2025-11-05 11:00", "LONG",  "Bottom recovery"),
    ("#6",  "2026-03-12 10:00", "LONG",  "Mid-sell bottom"),
    ("#7",  "2025-11-24 11:00", "SHORT", "Top cluster"),
    ("#8",  "2026-03-20 14:00", "LONG",  "Bottom sell-off"),
    ("#10", "2026-03-24 10:00", "LONG",  "Bottom final"),
    ("#11", "2026-01-29 19:00", "LONG",  "Bottom Jan sell"),
    ("#12", "2026-04-15 23:00", "SHORT", "Top Abr"),
    ("#13", "2026-02-03 03:00", "LONG",  "Bottom Feb"),
]

# Cor mapping confirmada empiricamente (uptrend majority = bull)
COLOR_BULL = 2572201804  # demand
COLOR_BEAR = 2566953215  # supply

SELL_PLOTS = {"plot_0", "plot_10"}
BUY_PLOTS = {"plot_2", "plot_4", "plot_6", "plot_8"}
LARGE_BUY = "plot_8"
LARGE_SELL = "plot_0"
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


def calc_rsi(closes, period=14):
    """RSI clássico (Wilder smoothing)."""
    if len(closes) < period+1: return [None]*len(closes)
    gains, losses = [], []
    for i in range(1, len(closes)):
        diff = closes[i] - closes[i-1]
        gains.append(max(diff, 0))
        losses.append(max(-diff, 0))
    # initial avg
    avg_gain = mean(gains[:period])
    avg_loss = mean(losses[:period])
    rsi = [None]*(period)
    if avg_loss == 0:
        rsi.append(100)
    else:
        rs = avg_gain / avg_loss
        rsi.append(100 - (100 / (1 + rs)))
    # Wilder smoothing
    for i in range(period, len(closes)-1):
        avg_gain = (avg_gain*(period-1) + gains[i]) / period
        avg_loss = (avg_loss*(period-1) + losses[i]) / period
        if avg_loss == 0:
            rsi.append(100)
        else:
            rs = avg_gain / avg_loss
            rsi.append(100 - (100 / (1 + rs)))
    return rsi


def find_pivots_lows(closes, idx_end, lookback=50, window=3):
    """Acha pivots low nas últimas 'lookback' bars antes/incluindo idx_end."""
    pivots = []
    start = max(window, idx_end - lookback)
    for i in range(start, idx_end+1):
        if i < window or i > len(closes)-window-1: continue
        is_pivot = True
        for j in range(1, window+1):
            if closes[i] >= closes[i-j] or closes[i] >= closes[i+j]:
                is_pivot = False; break
        if is_pivot:
            pivots.append(i)
    return pivots


def find_pivots_highs(closes, idx_end, lookback=50, window=3):
    pivots = []
    start = max(window, idx_end - lookback)
    for i in range(start, idx_end+1):
        if i < window or i > len(closes)-window-1: continue
        is_pivot = True
        for j in range(1, window+1):
            if closes[i] <= closes[i-j] or closes[i] <= closes[i+j]:
                is_pivot = False; break
        if is_pivot:
            pivots.append(i)
    return pivots


def detect_bull_div(closes, rsi, idx_end, lookback=50):
    """Bull div: price faz LOWER LOW + RSI faz HIGHER LOW."""
    lows = find_pivots_lows(closes, idx_end, lookback)
    if len(lows) < 2: return False, None
    l_recent = lows[-1]
    l_prev = lows[-2]
    if rsi[l_recent] is None or rsi[l_prev] is None: return False, None
    is_div = (closes[l_recent] < closes[l_prev]) and (rsi[l_recent] > rsi[l_prev])
    return is_div, (l_recent, l_prev)


def detect_bear_div(closes, rsi, idx_end, lookback=50):
    """Bear div: price faz HIGHER HIGH + RSI faz LOWER HIGH."""
    highs = find_pivots_highs(closes, idx_end, lookback)
    if len(highs) < 2: return False, None
    h_recent = highs[-1]
    h_prev = highs[-2]
    if rsi[h_recent] is None or rsi[h_prev] is None: return False, None
    is_div = (closes[h_recent] > closes[h_prev]) and (rsi[h_recent] < rsi[h_prev])
    return is_div, (h_recent, h_prev)


def parse_dt(s):
    return int(datetime.strptime(s+"+0000", "%Y-%m-%d %H:%M%z").timestamp())


def main():
    print(f"=== ANÁLISE 11 DREAM TRADES REVERSAL — Confluências detector ===\n")

    # Carrega TODOS bars de TODOS JSONLs e dedup por timestamp
    print("Carregando 8 JSONLs e construindo série mestre...")
    master = {}  # time -> bar dict
    files_ok = 0
    for fname in WINDOWS_V2:
        path = JSONL_DIR / fname
        if not path.exists():
            print(f"  AVISO: {fname} não encontrado")
            continue
        bars = load_bars(path)
        for b in bars:
            ohlcv = b.get('ohlcv_last_40_bars') or []
            if not ohlcv: continue
            last = ohlcv[-1]
            t = last.get('time')
            if t is None: continue
            # Preserva a versão "mais completa" se já existe
            master[t] = b
        files_ok += 1
    print(f"  {files_ok} JSONLs lidos, {len(master)} bars únicos\n")

    times_sorted = sorted(master.keys())
    bars_by_idx = [master[t] for t in times_sorted]

    # Constrói série de closes/highs/lows
    closes = []
    for b in bars_by_idx:
        ohlcv = b.get('ohlcv_last_40_bars') or []
        closes.append(ohlcv[-1].get('close') if ohlcv else None)

    # Filtra Nones
    valid_idx = [i for i, c in enumerate(closes) if c is not None]
    if len(valid_idx) != len(closes):
        print(f"  WARN: {len(closes)-len(valid_idx)} closes None")

    rsi_series = calc_rsi(closes, period=14)

    def find_bar_idx(target_ts):
        """Acha o índice do bar com time mais próximo (≤ target)."""
        best = None
        for i, t in enumerate(times_sorted):
            if t <= target_ts:
                best = i
            else:
                break
        return best

    # === Analisar cada dream trade ===
    print(f"{'#':<4s} {'datetime':<18s} {'dir':<6s} {'C1_NAS':<10s} {'C2_Bubex':<10s} {'C3_RSIdiv':<11s} {'C4_CHoCH':<10s} {'C5_OBdir':<10s} {'score':>6s}")
    print("-"*100)

    rows = []
    for tid, dt_str, direction, note in DREAM_TRADES:
        target_ts = parse_dt(dt_str)
        idx = find_bar_idx(target_ts)
        if idx is None:
            print(f"  {tid:<4s} {dt_str:<18s} {direction:<6s} NOT FOUND")
            continue
        bar = bars_by_idx[idx]
        bar_time = times_sorted[idx]

        # C1 — NAS LONG/SHORT label próximo (usando x = bar_index TV)
        # NAS labels têm text="LONG" ou "SHORT", x = bar_index dentro do chart visível
        # Bar atual TV = max(x) entre todas as labels do mesmo study (approx)
        want_label = "LONG" if direction == "LONG" else "SHORT"
        c1_found = False
        c1_detail = "-"
        for s in (bar.get('pine_labels') or []):
            if 'NAS' not in s.get('name','').upper(): continue
            labels = s.get('labels') or []
            if not labels: continue
            xs = [lbl.get('x') for lbl in labels if lbl.get('x') is not None]
            if not xs: continue
            max_x = max(xs)  # proxy do bar atual no chart TV
            # Procura label com text matching e x próximo do max_x (±5 bars)
            for lbl in labels:
                txt = (lbl.get('text') or '').upper()
                lx = lbl.get('x')
                if lx is None or txt != want_label: continue
                delta = max_x - lx
                if 0 <= delta <= 5:
                    c1_found = True
                    c1_detail = f"{txt}@Δ{delta}"
                    break
            if c1_found: break

        # C2 — Bubble exhaustion oposto direção (últimos 10 bars)
        # LONG: Large Sell (plot_0) ou Small Sell (plot_10) presente
        # SHORT: Large Buy (plot_8) ou outros Buy (plot_2/4/6) presente
        want_plots = SELL_PLOTS if direction == "LONG" else BUY_PLOTS
        c2_found = False
        c2_detail = ""
        bubble_lookback = 10
        t_lb = bar_time - (bubble_lookback-1)*BAR_SECONDS_4H
        plots_hit = []
        for s in (bar.get('pine_shapes_bubbles') or []):
            if 'Bubbles' not in s.get('name',''): continue
            for act in s.get('activations', []):
                t = act.get('time')
                if t is None: continue
                if t_lb <= t <= bar_time:
                    for p in (act.get('shapes') or {}):
                        if p in want_plots:
                            plots_hit.append(p)
        plots_hit = list(set(plots_hit))
        c2_found = len(plots_hit) > 0
        c2_detail = ",".join(sorted(plots_hit)) if plots_hit else "-"

        # C3 — RSI divergence local
        c3_found = False
        c3_detail = "-"
        if direction == "LONG":
            is_div, pivs = detect_bull_div(closes, rsi_series, idx, lookback=50)
        else:
            is_div, pivs = detect_bear_div(closes, rsi_series, idx, lookback=50)
        c3_found = is_div
        if pivs:
            c3_detail = f"Δ{idx-pivs[1]}→{idx-pivs[0]}"

        # C4 — CHoCH/BOS direction
        # NAS indicator NÃO tem CHoCH/BOS labels (só LONG/SHORT)
        # CHoCH/BOS provavelmente vem de pine_shapes ou outro indicator
        # Por agora marca como "indisponível" e busca em pine_shapes_bubbles ou Custom OB
        c4_found = False
        c4_detail = "n/a"  # NAS labels só têm LONG/SHORT

        # C5 — OB direction PROXIMITY: preço dentro OU dentro de ±50% do tamanho da zone
        # (preço pode ter rompido a borda e estar próximo)
        c5_found = False
        c5_detail = "-"
        ohlcv = bar.get('ohlcv_last_40_bars') or []
        close = ohlcv[-1].get('close') if ohlcv else None
        want_color = COLOR_BULL if direction == "LONG" else COLOR_BEAR
        if close is not None:
            best_distance = None
            best_in = False
            for s in (bar.get('pine_boxes') or []):
                if 'Custom OB' not in s.get('name',''): continue
                for box in (s.get('all_boxes') or []):
                    hi, lo = box.get('high'), box.get('low')
                    bc = box.get('borderColor')
                    if hi is None or lo is None or bc != want_color: continue
                    zone_size = hi - lo
                    if zone_size <= 0: continue
                    if lo <= close <= hi:
                        c5_found = True
                        c5_detail = "IN_zone"
                        break
                    # próximo: distância <= 50% do zone_size
                    dist_above = (close - hi) if close > hi else 0
                    dist_below = (lo - close) if close < lo else 0
                    dist = max(dist_above, dist_below)
                    if dist <= zone_size * 0.5:
                        c5_found = True
                        c5_detail = f"near_{int(100*dist/zone_size)}%"
                        # não break, segue procurando IN_zone (preferencial)
                if c5_found and c5_detail == "IN_zone": break

        score = sum([c1_found, c2_found, c3_found, c4_found, c5_found])
        actual_dt = datetime.fromtimestamp(bar_time, tz=timezone.utc).strftime("%Y-%m-%d %H:%M")
        offset_bars = (target_ts - bar_time) // BAR_SECONDS_4H
        offset_str = f"(Δ{offset_bars})" if offset_bars != 0 else ""

        rows.append({
            'id':tid,'dt':dt_str,'dir':direction,
            'c1':c1_found,'c1d':c1_detail,
            'c2':c2_found,'c2d':c2_detail,
            'c3':c3_found,'c3d':c3_detail,
            'c4':c4_found,'c4d':c4_detail,
            'c5':c5_found,'c5d':c5_detail,
            'score':score,'actual_dt':actual_dt,'offset':offset_str,
        })
        m1 = "✓" if c1_found else "·"
        m2 = "✓" if c2_found else "·"
        m3 = "✓" if c3_found else "·"
        m4 = "✓" if c4_found else "·"
        m5 = "✓" if c5_found else "·"
        print(f"  {tid:<4s} {dt_str:<18s} {direction:<6s} {m1+' '+c1_detail:<10s} {m2+' '+c2_detail:<10s} {m3+' '+c3_detail:<11s} {m4+' '+c4_detail:<10s} {m5+' '+c5_detail:<10s} {score:>6d}")

    # Agregados
    print(f"\n=== AGREGADOS ===")
    counts = {'c1':0,'c2':0,'c3':0,'c4':0,'c5':0}
    score_counts = defaultdict(int)
    n = len(rows)
    for r in rows:
        for k in counts:
            if r[k]: counts[k] += 1
        score_counts[r['score']] += 1

    if n > 0:
        names = {'c1':'NAS label proximo','c2':'Bubble exhaustion oposto','c3':'RSI divergence','c4':'CHoCH/BOS proximo','c5':'OB direction correta'}
        for k, name in names.items():
            print(f"  {name}: {counts[k]}/{n} ({100*counts[k]/n:.0f}%)")
        print(f"\nDistribuição de score (n={n}):")
        for s in sorted(score_counts.keys(), reverse=True):
            print(f"  score {s}/5: {score_counts[s]} trades")

    # LONGs vs SHORTs
    longs = [r for r in rows if r['dir']=='LONG']
    shorts = [r for r in rows if r['dir']=='SHORT']
    print(f"\nLONGs (n={len(longs)}):")
    for r in longs:
        print(f"  {r['id']} {r['dt']}  score={r['score']}/5")
    print(f"\nSHORTs (n={len(shorts)}):")
    for r in shorts:
        print(f"  {r['id']} {r['dt']}  score={r['score']}/5")

    return 0


if __name__ == "__main__":
    sys.exit(main())
