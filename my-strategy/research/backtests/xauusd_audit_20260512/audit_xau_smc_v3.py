#!/usr/bin/env python3
"""XAUUSD 4H SMC backtest V3 — comparação CHoCH/BOS estrutural.

Testa 3 variantes de Order Block + stop:
- V3a: low extremo do range pos-BOS, stop ATR-based (BigBeluga-style structural)
- V3b: ultimo candle bearish antes do impulso, stop ATR-based (Leonardo OB + ATR stop)
- V3c: ultimo candle bearish antes do impulso, stop estrutural (Leonardo OB + LVB stop)

CHoCH/BOS detection: pivot_high/pivot_low(5,5) padrao, close cross = event.
Logica state-machine independente, nao deriva do source BigBeluga (MPL 2.0).

Targets: 2.0, 2.5, 3.0, 4.0, 5.0 R. Entry: direct_bos OR touch_in_zone. BE @ +1R.
"""
import pandas as pd
import numpy as np
from pathlib import Path

CSV_4H = '/Users/cristrein/Downloads/PEPPERSTONE_XAUUSD, 240_aea76.csv'
OUT_DIR = Path(__file__).parent
SPREAD_R = 0.05
PIVOT_LEN = 5
MAX_HOLD_BARS = 24
LOOKBACK_OB = 50
TOUCH_LOOKAHEAD = 12


def load_data():
    df = pd.read_csv(CSV_4H)
    df.columns = [c.strip() for c in df.columns]
    df['time'] = pd.to_datetime(df['time'], unit='s')
    df = df.sort_values('time').reset_index(drop=True)
    for c in ['open', 'high', 'low', 'close']:
        df[c] = pd.to_numeric(df[c], errors='coerce')
    df = df.dropna(subset=['open', 'high', 'low', 'close']).reset_index(drop=True)
    h, l, c = df['high'], df['low'], df['close']
    pc = c.shift(1)
    tr = pd.concat([(h - l).abs(), (h - pc).abs(), (l - pc).abs()], axis=1).max(axis=1)
    df['atr14'] = tr.ewm(alpha=1 / 14, adjust=False).mean()
    df['atr200'] = tr.ewm(alpha=1 / 200, adjust=False).mean()
    return df


def detect_pivots(df, length=PIVOT_LEN):
    n = len(df)
    ph = np.zeros(n, dtype=bool)
    pl = np.zeros(n, dtype=bool)
    high = df['high'].values
    low = df['low'].values
    for i in range(length, n - length):
        window_high = high[i - length:i + length + 1]
        window_low = low[i - length:i + length + 1]
        if high[i] == window_high.max():
            ph[i] = True
        if low[i] == window_low.min():
            pl[i] = True
    return ph, pl


def track_structure(df, ph, pl):
    """State machine identifying BOS_BULL/BOS_BEAR/CHOCH_BULL/CHOCH_BEAR events.

    For each event, records:
      - idx: bar that closed past the pivot
      - level: price of pivot broken
      - last_pivot_idx: most recent OPPOSITE pivot before the event
        (e.g. for BOS_BULL = last pivot LOW = start of the rally leg)
      - broken_pivot_idx: pivot that got broken
    """
    n = len(df)
    close = df['close'].values
    high = df['high'].values
    low = df['low'].values

    last_ph_idx_arr = np.full(n, -1, dtype=int)
    last_pl_idx_arr = np.full(n, -1, dtype=int)
    last_ph = -1
    last_pl = -1
    for i in range(n):
        if ph[i]:
            last_ph = i
        if pl[i]:
            last_pl = i
        last_ph_idx_arr[i] = last_ph
        last_pl_idx_arr[i] = last_pl

    events = []
    trend = 0
    anchor_ph = -1
    anchor_pl = -1

    for i in range(PIVOT_LEN, n):
        lph = last_ph_idx_arr[i]
        lpl = last_pl_idx_arr[i]
        if lph < 0 or lpl < 0:
            continue
        ph_price = high[lph]
        pl_price = low[lpl]

        if trend in (0, -1) and close[i] > ph_price and lph != anchor_ph:
            etype = 'CHOCH_BULL' if trend == -1 else 'BOS_BULL'
            events.append({
                'idx': i,
                'type': etype,
                'level': float(ph_price),
                'last_pivot_idx': lpl,
                'broken_pivot_idx': lph,
            })
            trend = 1
            anchor_ph = lph
            anchor_pl = -1
        elif trend in (0, 1) and close[i] < pl_price and lpl != anchor_pl:
            etype = 'CHOCH_BEAR' if trend == 1 else 'BOS_BEAR'
            events.append({
                'idx': i,
                'type': etype,
                'level': float(pl_price),
                'last_pivot_idx': lph,
                'broken_pivot_idx': lpl,
            })
            trend = -1
            anchor_pl = lpl
            anchor_ph = -1

    return events


def identify_ob_a(df, event):
    """V3a: low extremo no range desde last_pivot_idx. Zone [low_ex, low_ex + 1*ATR200]."""
    if event['type'] not in ('BOS_BULL', 'CHOCH_BULL'):
        return None
    idx = event['idx']
    low = df['low'].values
    high = df['high'].values
    atr200 = df['atr200'].values
    start = event['last_pivot_idx']
    if start is None or start < 0 or start >= idx:
        start = max(0, idx - LOOKBACK_OB)
    range_lows = low[start:idx + 1]
    if len(range_lows) == 0:
        return None
    min_off = int(np.argmin(range_lows))
    ob_idx = start + min_off
    ob_low = float(low[ob_idx])
    atr_at = atr200[ob_idx]
    if np.isnan(atr_at):
        atr_at = atr200[idx]
    if np.isnan(atr_at) or atr_at <= 0:
        return None
    ob_top = ob_low + float(atr_at)
    high_val = float(high[ob_idx])
    if ob_top > high_val:
        ob_top = high_val
    return {'ob_idx': ob_idx, 'ob_low': ob_low, 'ob_top': ob_top}


def identify_ob_leonardo(df, event):
    """V3b/V3c: ultimo candle BEARISH antes do impulso. Zone = corpo do candle inteiro."""
    if event['type'] not in ('BOS_BULL', 'CHOCH_BULL'):
        return None
    idx = event['idx']
    open_arr = df['open'].values
    close_arr = df['close'].values
    high_arr = df['high'].values
    low_arr = df['low'].values
    start = event['last_pivot_idx']
    if start is None or start < 0:
        start = max(0, idx - LOOKBACK_OB)
    for j in range(idx - 1, start - 1, -1):
        if j < 0:
            break
        if close_arr[j] < open_arr[j]:
            return {
                'ob_idx': j,
                'ob_low': float(low_arr[j]),
                'ob_top': float(high_arr[j]),
            }
    return None


def find_last_valid_bottom(df, event):
    """V3c stop ref: low minimo do range entre last_pivot_idx e o evento."""
    if event['type'] not in ('BOS_BULL', 'CHOCH_BULL'):
        return None
    idx = event['idx']
    low_arr = df['low'].values
    start = event['last_pivot_idx']
    if start is None or start < 0:
        start = max(0, idx - LOOKBACK_OB)
    rng = low_arr[start:idx + 1]
    if len(rng) == 0:
        return None
    return float(np.min(rng))


def simulate(df, entry_idx, entry, stop, target_r, max_bars=MAX_HOLD_BARS):
    n = len(df)
    high = df['high'].values
    low = df['low'].values
    close = df['close'].values
    R = entry - stop
    if R <= 0:
        return None
    target = entry + R * target_r
    cur_stop = stop
    moved_be = False
    for j in range(entry_idx + 1, min(entry_idx + 1 + max_bars, n)):
        h, l = high[j], low[j]
        if not moved_be and h >= entry + R:
            cur_stop = max(cur_stop, entry)
            moved_be = True
        if l <= cur_stop:
            return {'exit_idx': j, 'r': (cur_stop - entry) / R}
        if h >= target:
            return {'exit_idx': j, 'r': target_r}
    last = min(entry_idx + max_bars, n - 1)
    return {'exit_idx': last, 'r': (close[last] - entry) / R}


def run_variant(df, events, variant, entry_style, target_r, stop_atr_mult=0.5):
    trades = []
    n = len(df)
    close = df['close'].values
    low = df['low'].values
    atr14 = df['atr14'].values

    for ev in events:
        if ev['type'] not in ('BOS_BULL', 'CHOCH_BULL'):
            continue
        if variant == 'V3a':
            ob = identify_ob_a(df, ev)
        else:
            ob = identify_ob_leonardo(df, ev)
        if ob is None:
            continue

        if entry_style == 'direct_bos':
            entry_idx = ev['idx']
            entry = float(close[entry_idx])
        else:
            entry_idx = None
            entry = None
            for j in range(ev['idx'] + 1, min(ev['idx'] + 1 + TOUCH_LOOKAHEAD, n)):
                if low[j] <= ob['ob_top']:
                    if close[j] < ob['ob_low']:
                        break
                    entry_idx = j
                    entry = ob['ob_top']
                    break
            if entry_idx is None:
                continue

        if variant in ('V3a', 'V3b'):
            atr_e = atr14[entry_idx]
            if np.isnan(atr_e):
                continue
            stop = ob['ob_low'] - stop_atr_mult * float(atr_e)
        else:
            lvb = find_last_valid_bottom(df, ev)
            if lvb is None:
                continue
            stop = lvb * (1 - 0.0005)

        if entry <= stop:
            continue
        R = entry - stop
        atr_e = atr14[entry_idx]
        if not np.isnan(atr_e) and R > 5 * atr_e:
            continue

        result = simulate(df, entry_idx, entry, stop, target_r)
        if result is None:
            continue
        trades.append({
            'event_idx': ev['idx'],
            'event_type': ev['type'],
            'ob_idx': ob['ob_idx'],
            'entry_idx': entry_idx,
            'entry_time': df.at[entry_idx, 'time'],
            'entry': float(entry),
            'stop': float(stop),
            'R_pts': float(R),
            'r': float(result['r']),
            'exit_idx': result['exit_idx'],
        })
    return trades


def metrics(trades, spread=SPREAD_R):
    if not trades:
        return dict(n=0, total_r_net=0, avg_r_net=0, win_rate=0, pf_net=0,
                    max_losing_streak=0, r_no_top5=0, r_no_top10=0,
                    trades_per_month=0)
    r = np.array([t['r'] - spread for t in trades])
    wins = r > 0
    pos = r[r > 0].sum()
    neg = -r[r <= 0].sum()
    pf = pos / neg if neg > 0 else float('inf')
    streak = mx = 0
    for w in wins:
        if not w:
            streak += 1
            mx = max(mx, streak)
        else:
            streak = 0
    sd = np.sort(r)[::-1]
    nt5 = r.sum() - sd[:5].sum() if len(r) >= 5 else 0
    nt10 = r.sum() - sd[:10].sum() if len(r) >= 10 else 0
    times = [t['entry_time'] for t in trades]
    span_d = (max(times) - min(times)).days or 1
    return dict(
        n=len(r),
        total_r_net=round(float(r.sum()), 2),
        avg_r_net=round(float(r.mean()), 4),
        win_rate=round(float(wins.mean()), 3),
        pf_net=round(float(pf), 2) if pf != float('inf') else 999.0,
        max_losing_streak=int(mx),
        r_no_top5=round(float(nt5), 2),
        r_no_top10=round(float(nt10), 2),
        trades_per_month=round(len(r) / (span_d / 30), 2),
    )


def main():
    import time as t_mod
    t0 = t_mod.time()
    print("=== Loading XAU 4H ===")
    df = load_data()
    print(f"  Rows: {len(df)}, span: {(df.time.max() - df.time.min()).days/365.25:.2f}y  ({t_mod.time()-t0:.1f}s)")

    print("=== Detecting pivots ===")
    ph, pl = detect_pivots(df, PIVOT_LEN)
    print(f"  Pivot highs: {int(ph.sum())}, pivot lows: {int(pl.sum())}  ({t_mod.time()-t0:.1f}s)")

    print("=== Tracking market structure (CHoCH/BOS) ===")
    events = track_structure(df, ph, pl)
    bull = [e for e in events if e['type'] in ('BOS_BULL', 'CHOCH_BULL')]
    print(f"  Total events: {len(events)}, bull events: {len(bull)}  ({t_mod.time()-t0:.1f}s)")

    print("=== Running variants ===")
    results = []
    trades_by = {}
    for variant in ['V3a', 'V3b', 'V3c']:
        for entry_style in ['direct_bos', 'touch_in_zone']:
            for target_r in [2.0, 2.5, 3.0, 4.0, 5.0]:
                trades = run_variant(df, events, variant, entry_style, target_r)
                m = metrics(trades)
                label = f"{variant}|{entry_style}|tgt{target_r}R"
                results.append({'config': label, **m})
                trades_by[label] = trades
                print(f"  {label}: n={m['n']}, total={m['total_r_net']}R, "
                      f"PF={m['pf_net']}, win={m['win_rate']}, no_top5={m['r_no_top5']}")

    df_res = pd.DataFrame(results).sort_values('total_r_net', ascending=False)
    df_res.to_csv(OUT_DIR / 'XAU_4H_SMC_v3_summary.csv', index=False)

    print()
    print("=== TOP 10 ===")
    cols = ['config', 'n', 'trades_per_month', 'total_r_net', 'avg_r_net',
            'win_rate', 'pf_net', 'max_losing_streak', 'r_no_top5', 'r_no_top10']
    print(df_res[cols].head(10).to_string(index=False))

    print()
    print("=== Robust (PF>=1.4, total>=10R, no_top5>=0, n>=20) ===")
    robust = df_res[(df_res.pf_net >= 1.4) & (df_res.total_r_net >= 10) &
                    (df_res.r_no_top5 >= 0) & (df_res.n >= 20)]
    if len(robust) > 0:
        print(robust[cols].to_string(index=False))
    else:
        print("  NONE")

    print()
    print("=== BASELINE: Mecanico atual (XAUUSD_4H_LONG_BREAKOUT_CONTINUATION_REGIME_FILTERED) ===")
    print("  n=234, total=+64.57R, PF=1.64, win=28.6%, no_top5=+44.82R")

    # Save best trades per variant
    for v in ['V3a', 'V3b', 'V3c']:
        v_configs = df_res[df_res.config.str.startswith(v)].head(1)
        if len(v_configs) > 0:
            best_label = v_configs.iloc[0]['config']
            tr = trades_by.get(best_label, [])
            if tr:
                pd.DataFrame(tr).to_csv(
                    OUT_DIR / f'XAU_4H_SMC_v3_{v}_best_trades.csv', index=False)

    print(f"\nDone. Runtime: {t_mod.time()-t0:.1f}s")


if __name__ == '__main__':
    main()
