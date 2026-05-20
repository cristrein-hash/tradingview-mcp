#!/usr/bin/env python3
"""
analyze_xau_4h_backtest.py — análise post-hoc exploratória do backtest XAU 4H.

Input: logs/backtests/XAUUSD_240_*.jsonl (540 bars com captura rica)

Estratégia (sem hipóteses fechadas — cruza tudo):
  1. Carrega bars sequenciais
  2. Deduplica Bubbles via bar_index interno do TV (cada signal cap em janela móvel)
  3. Mapeia time → sequential index pra correlacionar com OHLCV
  4. Calcula ATR(14) sequencial
  5. Pra cada bar deriva estado dos indicators:
     - bubble_active (6 tipos + none)
     - rsi_bucket (5 níveis)
     - nas_dist_bucket (5 níveis)
     - in_ob_zone (none / bullish / bearish)
  6. Pra cada bar calcula outcome em 5/10/20/40 bars seguintes (LONG e SHORT)
  7. Cruza single + 2-way + 3-way de buckets
  8. Reporta top combinações por edge, com sample gate

Sample gate:
  n<10 = descartar (ruído)
  n=10-29 = INTERIM (mostrar com flag)
  n=30-99 = directional (mostrar como preliminar)
  n>=100 = sólido

Usage:
  python3 analyze_xau_4h_backtest.py
  python3 analyze_xau_4h_backtest.py --input <jsonl> --output-prefix <name>
"""

from pathlib import Path
from collections import defaultdict
from datetime import datetime, timezone
from statistics import mean, median
import argparse
import json
import sys

DEFAULT_JSONL = "/Users/cristrein/tradingview-mcp/alert-bridge/logs/backtests/XAUUSD_240_2025-11-19_to_2026-05-19.jsonl"

# Bucket definitions
RSI_BUCKETS = [(0, 30, "RSI<30"), (30, 40, "RSI_30-40"), (40, 60, "RSI_40-60"), (60, 70, "RSI_60-70"), (70, 100, "RSI>70")]
NAS_DIST_BUCKETS = [(-99, -2, "NAS<-2"), (-2, -1, "NAS_-2to-1"), (-1, 1, "NAS_-1to1"), (1, 2, "NAS_1to2"), (2, 99, "NAS>2")]

BUBBLE_PLOTS = {
    "plot_0":  "Sell",
    "plot_2":  "Buy",
    "plot_4":  "SmallBuy",
    "plot_6":  "MediumBuy",
    "plot_8":  "LargeBuy",
    "plot_10": "SmallSell",
}

OUTCOME_HORIZONS = [5, 10, 20, 40]


def bucket(value, buckets):
    if value is None:
        return None
    for lo, hi, name in buckets:
        if lo <= value < hi:
            return name
    return None


def parse_float(s):
    if s is None:
        return None
    if isinstance(s, (int, float)):
        return float(s)
    try:
        return float(str(s).replace("−", "-"))
    except (ValueError, TypeError):
        return None


def extract_bar_state(bar):
    """Extrai estado do bar pra análise (RSI, NAS, OHLCV, OB zones, ATR-ready)."""
    state = {
        "bar_index": bar.get("bar_index"),
        "replay_dt": bar.get("replay_current_dt"),
        "replay_ts": bar.get("replay_current_date"),
        "ohlc": None,
        "rsi": None,
        "rsi_ma": None,
        "nas_dist": None,
        "nas_rsi": None,
        "ob_zones": [],
        "ob_box_count": 0,
    }

    # OHLCV last bar
    meta = bar.get("ohlcv_meta") or {}
    ohlcv_bars = bar.get("ohlcv_last_40_bars") or []
    if ohlcv_bars:
        last = ohlcv_bars[-1]
        state["ohlc"] = {
            "time": last.get("time"),
            "open": last.get("open"),
            "high": last.get("high"),
            "low": last.get("low"),
            "close": last.get("close"),
            "volume": last.get("volume"),
        }
        # 14 anteriores para ATR
        state["ohlcv_14_bars"] = ohlcv_bars[-14:] if len(ohlcv_bars) >= 14 else ohlcv_bars

    # Study values
    for s in (bar.get("study_values") or []):
        name = s.get("name", "")
        vals = s.get("values", {})
        if "Relative Strength" in name:
            state["rsi"] = parse_float(vals.get("RSI"))
            state["rsi_ma"] = parse_float(vals.get("RSI-based MA"))
        elif "NAS" in name:
            state["nas_dist"] = parse_float(vals.get("NAS_DISTANCE_FROM_EMA_ATR"))
            state["nas_rsi"] = parse_float(vals.get("NAS_RSI"))

    # OB boxes
    for s in (bar.get("pine_boxes") or []):
        if "Custom OB" in s.get("name", ""):
            state["ob_zones"] = s.get("zones", [])
            state["ob_box_count"] = s.get("total_boxes", 0)
            break

    return state


def dedupe_bubbles(bars):
    """Deduplica Bubble activations via bar_index interno do TV.
    Cada bar capturado mostrou bubbles em janela ±20 bars (duplicados).
    Retorna {tv_bar_time: {plot_id: True}} — set de bubbles únicos.
    """
    unique = defaultdict(dict)  # key=time, value={plot_id: 1}
    for bar in bars:
        for s in (bar.get("pine_shapes_bubbles") or []):
            if "Bubbles" not in s.get("name", ""):
                continue
            for act in s.get("activations", []):
                t = act.get("time")
                if t is None:
                    continue
                for plot_id in act.get("shapes", {}):
                    unique[t][plot_id] = 1
    return unique


def compute_atr_sequential(states):
    """Calcula ATR(14) usando os bars CLOSED do próprio snapshot ohlcv_14_bars.
    Exclui o último bar (current, com O=H=L=C degenerado em modo replay).
    """
    for i, st in enumerate(states):
        bars14 = st.get("ohlcv_14_bars") or []
        if len(bars14) <= 1:
            st["atr14"] = None
            continue
        # Excluir o último bar (current, frequentemente degenerado em replay)
        closed_bars = bars14[:-1]
        ranges = []
        for b in closed_bars:
            h, l = b.get("high"), b.get("low")
            if h is not None and l is not None and h > l:
                ranges.append(h - l)
        st["atr14"] = mean(ranges) if ranges else None


def derive_signals(states, bubble_map):
    """Pra cada bar, deriva os signals e buckets.
    Atribui campos in-place: rsi_bucket, nas_bucket, bubble_active (dict por tipo), in_ob_bullish, in_ob_bearish.
    """
    for st in states:
        st["rsi_bucket"] = bucket(st.get("rsi"), RSI_BUCKETS)
        st["nas_bucket"] = bucket(st.get("nas_dist"), NAS_DIST_BUCKETS)

        # Bubble do bar atual via lookup pelo time do OHLC bar (mais próximo)
        ohlc = st.get("ohlc") or {}
        ohlc_time = ohlc.get("time")
        bubbles_now = bubble_map.get(ohlc_time, {}) if ohlc_time else {}
        st["bubble_active"] = {BUBBLE_PLOTS.get(k, k): True for k in bubbles_now}

        # OB zone: bar.close dentro de alguma zone? Próxima zone bullish/bearish?
        if ohlc and ohlc.get("close") is not None:
            close = ohlc["close"]
            in_zone = False
            zone_above = None  # menor zone com low > close (resistência)
            zone_below = None  # maior zone com high < close (suporte)
            for z in st.get("ob_zones", []):
                hi, lo = z.get("high"), z.get("low")
                if hi is None or lo is None:
                    continue
                if lo <= close <= hi:
                    in_zone = True
                if lo > close:  # acima
                    if zone_above is None or lo < zone_above["low"]:
                        zone_above = z
                if hi < close:  # abaixo
                    if zone_below is None or hi > zone_below["high"]:
                        zone_below = z
            st["in_ob_zone"] = in_zone
            st["zone_above_dist_atr"] = None
            st["zone_below_dist_atr"] = None
            atr = st.get("atr14")
            if atr and atr > 0:
                if zone_above:
                    st["zone_above_dist_atr"] = (zone_above["low"] - close) / atr
                if zone_below:
                    st["zone_below_dist_atr"] = (close - zone_below["high"]) / atr


def compute_outcomes(states):
    """Pra cada bar, calcula outcome_R em horizontes 5/10/20/40 bars (LONG e SHORT).
    Usa próximos N bars no sequential. Stop = 2×ATR; target = max_favorable ou close@N.
    Métricas registradas in-place:
      outcomes[H]['long']  = {max_favorable_R, max_adverse_R, close_R}
      outcomes[H]['short'] = {max_favorable_R, max_adverse_R, close_R}
    Onde close_R = (close[N] - close[0]) / atr ; max_favorable_R = (max(high[1..N]) - close[0]) / atr ; max_adverse_R simétrico.
    """
    for i, st in enumerate(states):
        atr = st.get("atr14")
        ohlc = st.get("ohlc") or {}
        close = ohlc.get("close")
        st["outcomes"] = {}
        if atr is None or atr <= 0 or close is None:
            continue
        for H in OUTCOME_HORIZONS:
            if i + H >= len(states):
                break
            future = states[i+1: i+H+1]
            highs = [s.get("ohlc", {}).get("high") for s in future if s.get("ohlc")]
            lows = [s.get("ohlc", {}).get("low") for s in future if s.get("ohlc")]
            closes_future = [s.get("ohlc", {}).get("close") for s in future if s.get("ohlc")]
            if not highs or not lows or not closes_future:
                continue
            max_h = max(h for h in highs if h is not None)
            min_l = min(l for l in lows if l is not None)
            close_at_H = closes_future[-1]

            # LONG: favoravel = preço subiu; adverso = caiu
            long_fav = (max_h - close) / atr
            long_adv = (min_l - close) / atr  # negativo
            long_close_R = (close_at_H - close) / atr

            # SHORT: favoravel = preço caiu (positivo em multiplicador)
            short_fav = (close - min_l) / atr
            short_adv = (close - max_h) / atr  # negativo
            short_close_R = (close - close_at_H) / atr

            st["outcomes"][H] = {
                "long":  {"max_favorable_R": round(long_fav, 2),  "max_adverse_R": round(long_adv, 2),  "close_R": round(long_close_R, 2)},
                "short": {"max_favorable_R": round(short_fav, 2), "max_adverse_R": round(short_adv, 2), "close_R": round(short_close_R, 2)},
            }


def signals_for_bar(st):
    """Retorna lista de tags ATIVAS pra esse bar (pra cruzamento)."""
    tags = []
    if st.get("rsi_bucket"): tags.append(f"RSI:{st['rsi_bucket']}")
    if st.get("nas_bucket"): tags.append(f"NAS:{st['nas_bucket']}")
    if st.get("in_ob_zone"): tags.append("IN_OB_ZONE")
    # Bubble actives — cada tipo é um signal separado
    for bub_type in (st.get("bubble_active") or {}):
        tags.append(f"BUB:{bub_type}")
    return tags


def analyze_combinations(states, horizon, direction):
    """Cruza single + pair + triple combos. Retorna lista de dicts ordenados por avg close_R.
    Filtra por n>=10.
    """
    buckets = defaultdict(list)  # combo (tuple frozen) -> list of close_R
    for st in states:
        if not st.get("outcomes") or horizon not in st["outcomes"]:
            continue
        out = st["outcomes"][horizon][direction]
        close_R = out["close_R"]
        max_fav_R = out["max_favorable_R"]
        tags = signals_for_bar(st)
        if not tags:
            continue
        # Single
        for t in tags:
            buckets[(t,)].append((close_R, max_fav_R))
        # 2-way
        sorted_tags = sorted(tags)
        for i in range(len(sorted_tags)):
            for j in range(i+1, len(sorted_tags)):
                buckets[(sorted_tags[i], sorted_tags[j])].append((close_R, max_fav_R))
        # 3-way
        for i in range(len(sorted_tags)):
            for j in range(i+1, len(sorted_tags)):
                for k in range(j+1, len(sorted_tags)):
                    buckets[(sorted_tags[i], sorted_tags[j], sorted_tags[k])].append((close_R, max_fav_R))

    results = []
    for combo, outs in buckets.items():
        n = len(outs)
        if n < 10:
            continue
        rs = [r for r,_ in outs]
        favs = [f for _,f in outs]
        wins = sum(1 for r in rs if r > 0)
        gate = "SOLIDO" if n >= 100 else ("PRELIMINAR" if n >= 30 else "INTERIM")
        results.append({
            "combo": combo,
            "combo_str": " + ".join(combo),
            "ways": len(combo),
            "n": n,
            "win_pct": round(100 * wins / n, 1),
            "avg_close_R": round(mean(rs), 3),
            "median_close_R": round(median(rs), 3),
            "avg_max_favorable_R": round(mean(favs), 3),
            "sample_gate": gate,
        })
    return results


def print_top(results, label, top_n=15, by="avg_close_R"):
    sorted_r = sorted(results, key=lambda r: r[by], reverse=True)
    print(f"\n=== {label} — top {top_n} por {by} ===")
    print(f"{'n':>4s} {'win%':>5s} {'avgR':>7s} {'medR':>7s} {'mfeR':>7s} {'gate':>10s}  {'combo':70s}")
    for r in sorted_r[:top_n]:
        print(f"{r['n']:>4d} {r['win_pct']:>5.1f} {r['avg_close_R']:>+7.3f} {r['median_close_R']:>+7.3f} {r['avg_max_favorable_R']:>+7.3f} {r['sample_gate']:>10s}  {r['combo_str'][:68]}")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--input", default=DEFAULT_JSONL)
    p.add_argument("--top", type=int, default=15)
    p.add_argument("--output-prefix", default=None, help="Optional: salvar JSON detalhado")
    args = p.parse_args()

    print(f"Carregando {args.input}...")
    bars = []
    with open(args.input) as f:
        for line in f:
            bars.append(json.loads(line))
    print(f"  {len(bars)} bars carregados")

    # AUTO-TRUNCATE em corrupção: parar no primeiro bar com ohlcv vazio
    # (sintoma de symbol mudou durante backtest por interferência externa).
    truncate_at = None
    for i, b in enumerate(bars):
        if not (b.get('ohlcv_last_40_bars') or []):
            truncate_at = i
            print(f"  AUTO-TRUNCATE: bar {i} tem ohlcv vazio (provável symbol switch). Descartando bars {i}..{len(bars)-1}.")
            break
    if truncate_at is not None:
        bars = bars[:truncate_at]
        print(f"  Bars válidos: {len(bars)}")

    print("\nExtraindo estado por bar...")
    states = [extract_bar_state(b) for b in bars]

    print("Deduplicando Bubbles via bar_index TV...")
    bubble_map = dedupe_bubbles(bars)
    print(f"  bubble_map: {len(bubble_map)} timestamps únicos com Bubbles")

    print("Calculando ATR(14) sequencial...")
    compute_atr_sequential(states)

    print("Derivando signals + buckets...")
    derive_signals(states, bubble_map)

    print("Calculando outcomes...")
    compute_outcomes(states)

    print("\n=== distribuição de signals nos 540 bars ===")
    counters = defaultdict(int)
    bubble_per_bar = defaultdict(int)
    for st in states:
        if st.get("rsi_bucket"): counters[f"RSI:{st['rsi_bucket']}"] += 1
        if st.get("nas_bucket"): counters[f"NAS:{st['nas_bucket']}"] += 1
        if st.get("in_ob_zone"): counters["IN_OB_ZONE"] += 1
        for b in (st.get("bubble_active") or {}):
            counters[f"BUB:{b}"] += 1
            bubble_per_bar[b] += 1
    for k in sorted(counters, key=counters.get, reverse=True):
        print(f"  {counters[k]:>5d}  {k}")

    # Análise por horizon × direction
    for H in OUTCOME_HORIZONS:
        for direction in ["long", "short"]:
            results = analyze_combinations(states, H, direction)
            label = f"Horizon {H} bars × {direction.upper()}"
            print_top(results, label, top_n=args.top, by="avg_close_R")
            # Bottom-N também (anti-padrões)
            print(f"\n=== {label} — BOTTOM 5 (anti-padrões) ===")
            sorted_r = sorted(results, key=lambda r: r["avg_close_R"])
            print(f"{'n':>4s} {'win%':>5s} {'avgR':>7s} {'medR':>7s} {'mfeR':>7s} {'gate':>10s}  {'combo':70s}")
            for r in sorted_r[:5]:
                print(f"{r['n']:>4d} {r['win_pct']:>5.1f} {r['avg_close_R']:>+7.3f} {r['median_close_R']:>+7.3f} {r['avg_max_favorable_R']:>+7.3f} {r['sample_gate']:>10s}  {r['combo_str'][:68]}")

    if args.output_prefix:
        outp = Path(f"{args.output_prefix}_analysis.json")
        all_results = {}
        for H in OUTCOME_HORIZONS:
            for direction in ["long", "short"]:
                all_results[f"H{H}_{direction}"] = analyze_combinations(states, H, direction)
        outp.write_text(json.dumps(all_results, indent=2, ensure_ascii=False))
        print(f"\nDetalhe salvo em: {outp}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
