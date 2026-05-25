#!/usr/bin/env python3
"""
analyze_xau_confluence_map.py — Mapa amplo de confluências XAU 4H.

Single + 2-way + 3-way de buckets dos indicators principais.
- Horizonte: H=10 (40 horas)
- Sample gate: n≥30
- Direções: LONG e SHORT (espelho)
- Reusa dataset existente do backtest XAU 4H.

Output: top confluências por avg_R em cada direção.
"""
from pathlib import Path
from datetime import datetime, timezone
from statistics import mean, median
from itertools import combinations
import json, sys

BASE = Path(__file__).parent.parent
JSONL = BASE / "alert-bridge" / "logs" / "backtests" / "XAUUSD_240_2025-11-19_to_2026-05-19.jsonl"
HORIZON_4H = 10
MIN_N = 30

# Bubble plot identifiers
BUY_PLOTS = {"plot_2", "plot_4", "plot_6", "plot_8"}   # New Buy, Small Buy, Medium Buy, Large Buy
SELL_PLOTS = {"plot_0", "plot_10"}                       # New Sell, Small Sell
LARGE_BUY = "plot_8"
LARGE_SELL = "plot_0"  # plot_0 é "Sell" market — equivalente a Large Sell no Leviathan
SMALL_BUY = "plot_4"
SMALL_SELL = "plot_10"
MEDIUM_BUY = "plot_6"


def get_features(bar):
    """Extract bucket features from a 4H bar."""
    feats = {}
    rsi = nas = None
    for s in (bar.get('study_values') or []):
        if 'Relative Strength' in s.get('name',''):
            try: rsi = float(s.get('values',{}).get('RSI','').replace('−','-'))
            except: pass
        if 'NAS' in s.get('name',''):
            try: nas = float(s.get('values',{}).get('NAS_DISTANCE_FROM_EMA_ATR','').replace('−','-'))
            except: pass

    # NAS bucket
    if nas is not None:
        if nas < -2: feats['NAS'] = 'NAS<-2'
        elif nas < -1: feats['NAS'] = 'NAS_-2to-1'
        elif nas < 1: feats['NAS'] = 'NAS_-1to1'
        elif nas < 2: feats['NAS'] = 'NAS_1to2'
        else: feats['NAS'] = 'NAS>2'

    # RSI bucket
    if rsi is not None:
        if rsi < 30: feats['RSI'] = 'RSI<30'
        elif rsi < 40: feats['RSI'] = 'RSI_30-40'
        elif rsi < 50: feats['RSI'] = 'RSI_40-50'
        elif rsi < 60: feats['RSI'] = 'RSI_50-60'
        elif rsi < 70: feats['RSI'] = 'RSI_60-70'
        else: feats['RSI'] = 'RSI>70'

    # IN_OB_ZONE
    ohlcv = bar.get('ohlcv_last_40_bars') or []
    close = ohlcv[-1].get('close') if ohlcv else None
    entry_time = ohlcv[-1].get('time') if ohlcv else None
    in_ob = False
    if close is not None:
        for s in (bar.get('pine_boxes') or []):
            if 'Custom OB' in s.get('name',''):
                for z in s.get('zones', []):
                    hi, lo = z.get('high'), z.get('low')
                    if hi is not None and lo is not None and lo <= close <= hi:
                        in_ob = True; break
                break
    feats['IN_OB_ZONE'] = 'IN_OB_yes' if in_ob else 'IN_OB_no'

    # Bubble activations no candle (mesmo time)
    plots_now = set()
    if entry_time is not None:
        for s in (bar.get('pine_shapes_bubbles') or []):
            if 'Bubbles' not in s.get('name',''): continue
            for act in s.get('activations', []):
                if act.get('time') == entry_time:
                    plots_now.update((act.get('shapes') or {}).keys())
    feats['BUB_BUY']  = 'BUB_buy_yes'  if (plots_now & BUY_PLOTS)  else 'BUB_buy_no'
    feats['BUB_SELL'] = 'BUB_sell_yes' if (plots_now & SELL_PLOTS) else 'BUB_sell_no'
    feats['BUB_LARGE_BUY']  = 'BUB_LB_yes' if LARGE_BUY  in plots_now else 'BUB_LB_no'
    feats['BUB_LARGE_SELL'] = 'BUB_LS_yes' if LARGE_SELL in plots_now else 'BUB_LS_no'
    feats['BUB_SMALL_BUY']  = 'BUB_SB_yes' if SMALL_BUY  in plots_now else 'BUB_SB_no'
    feats['BUB_SMALL_SELL'] = 'BUB_SS_yes' if SMALL_SELL in plots_now else 'BUB_SS_no'
    feats['BUB_MEDIUM_BUY'] = 'BUB_MB_yes' if MEDIUM_BUY in plots_now else 'BUB_MB_no'

    feats['_close'] = close
    feats['_entry_time'] = entry_time
    return feats


def get_atr14(bar):
    ohlcv = bar.get('ohlcv_last_40_bars') or []
    if len(ohlcv) <= 1: return None
    closed = ohlcv[:-1][-14:]
    r = [b['high']-b['low'] for b in closed if b.get('high') and b.get('low') and b['high']>b['low']]
    return mean(r) if r else None


def stats(rs):
    if not rs: return None
    return {
        'n': len(rs),
        'win%': round(100*sum(1 for r in rs if r>0)/len(rs), 1),
        'avg_R': round(mean(rs), 2),
        'median_R': round(median(rs), 2),
    }


def main():
    bars = []
    with JSONL.open() as f:
        for line in f:
            try: bars.append(json.loads(line))
            except: pass
    for i, b in enumerate(bars):
        if not (b.get('ohlcv_last_40_bars') or []):
            bars = bars[:i]; break
    print(f"=== Confluence map XAU 4H (H={HORIZON_4H}, n>={MIN_N}) ===")
    print(f"{len(bars)} bars 4H válidos\n")

    # Compute features + future R for each bar
    samples = []
    for i, b in enumerate(bars):
        feats = get_features(b)
        if feats.get('_close') is None: continue
        if i + HORIZON_4H >= len(bars): continue
        atr = get_atr14(b)
        if not atr or atr <= 0: continue
        next_close = (bars[i+HORIZON_4H].get('ohlcv_last_40_bars') or [{}])[-1].get('close')
        if next_close is None: continue
        close_R_long = (next_close - feats['_close']) / atr
        close_R_short = -close_R_long
        samples.append({
            'feats': {k: v for k, v in feats.items() if not k.startswith('_')},
            'R_long': close_R_long,
            'R_short': close_R_short,
        })
    print(f"{len(samples)} samples válidos\n")

    feature_keys = sorted(set().union(*(s['feats'].keys() for s in samples)))

    # === SINGLES ===
    def collect_singles():
        out = []
        for fk in feature_keys:
            vals = set(s['feats'].get(fk) for s in samples if fk in s['feats'])
            for v in vals:
                if v is None: continue
                rs_long = [s['R_long'] for s in samples if s['feats'].get(fk) == v]
                rs_short = [s['R_short'] for s in samples if s['feats'].get(fk) == v]
                sl = stats(rs_long); ss = stats(rs_short)
                if sl and sl['n'] >= MIN_N:
                    out.append(('LONG', (f"{v}",), sl))
                    out.append(('SHORT', (f"{v}",), ss))
        return out

    # === 2-WAY ===
    def collect_pairs():
        out = []
        for fk1, fk2 in combinations(feature_keys, 2):
            vals1 = set(s['feats'].get(fk1) for s in samples if fk1 in s['feats'])
            vals2 = set(s['feats'].get(fk2) for s in samples if fk2 in s['feats'])
            for v1 in vals1:
                for v2 in vals2:
                    if v1 is None or v2 is None: continue
                    rs_long = [s['R_long'] for s in samples
                               if s['feats'].get(fk1)==v1 and s['feats'].get(fk2)==v2]
                    if len(rs_long) < MIN_N: continue
                    rs_short = [s['R_short'] for s in samples
                                if s['feats'].get(fk1)==v1 and s['feats'].get(fk2)==v2]
                    out.append(('LONG', (v1, v2), stats(rs_long)))
                    out.append(('SHORT', (v1, v2), stats(rs_short)))
        return out

    # === 3-WAY ===
    def collect_triples():
        out = []
        for fk1, fk2, fk3 in combinations(feature_keys, 3):
            vals1 = set(s['feats'].get(fk1) for s in samples if fk1 in s['feats'])
            vals2 = set(s['feats'].get(fk2) for s in samples if fk2 in s['feats'])
            vals3 = set(s['feats'].get(fk3) for s in samples if fk3 in s['feats'])
            for v1 in vals1:
                for v2 in vals2:
                    for v3 in vals3:
                        if any(x is None for x in (v1,v2,v3)): continue
                        rs_long = [s['R_long'] for s in samples
                                   if s['feats'].get(fk1)==v1 and s['feats'].get(fk2)==v2 and s['feats'].get(fk3)==v3]
                        if len(rs_long) < MIN_N: continue
                        rs_short = [s['R_short'] for s in samples
                                    if s['feats'].get(fk1)==v1 and s['feats'].get(fk2)==v2 and s['feats'].get(fk3)==v3]
                        out.append(('LONG', (v1, v2, v3), stats(rs_long)))
                        out.append(('SHORT', (v1, v2, v3), stats(rs_short)))
        return out

    def report(label, items, top_n=20):
        # Filter trivial "no" tag-only combos and split per direction
        for dir_filter in ('LONG', 'SHORT'):
            rows = [(combo, st) for d, combo, st in items if d == dir_filter and st]
            rows.sort(key=lambda x: x[1]['avg_R'], reverse=(dir_filter=='LONG'))
            top = rows[:top_n] if dir_filter=='LONG' else rows[:top_n]
            print(f"\n--- {label} | {dir_filter} top {top_n} ---")
            print(f"  {'combo':<60s}  {'n':>4s}  {'win%':>5s}  {'avg_R':>7s}  {'med_R':>6s}")
            for combo, st in top:
                cs = " + ".join(combo)
                print(f"  {cs:<60s}  {st['n']:>4d}  {st['win%']:>5.1f}  {st['avg_R']:>+7.2f}  {st['median_R']:>+6.2f}")

    print("\n=== SINGLE features (gate n>=30) ===")
    singles = collect_singles()
    report("SINGLE", singles, top_n=10)

    print("\n=== 2-WAY confluences (gate n>=30) ===")
    pairs = collect_pairs()
    report("2-WAY", pairs, top_n=20)

    print("\n=== 3-WAY confluences (gate n>=30) ===")
    triples = collect_triples()
    report("3-WAY", triples, top_n=20)

    return 0


if __name__ == "__main__":
    sys.exit(main())
