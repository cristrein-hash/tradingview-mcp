#!/usr/bin/env python3
"""XAUUSD 4H V3d — refino do V3c (Leonardo OB + stop estrutural touch_in_zone).

Varia 3 parametros que afetam stop placement e exit timing:
  - buffer (% do LVB):   0.0, 0.05, 0.1, 0.2, 0.5
  - BE timing:           BE@+0.5R, BE@+1R, BE@+2R, sem BE
  - target R:            2.0, 2.5, 3.0, 4.0, 5.0

Tambem testa ATR-blend stop: lvb - X*ATR (X=0.0, 0.2, 0.5).

Total: 5 buffers x 4 BE x 5 targets + 3 atr-blend variants = 103 configs.
Foco em otimizar XAU 4H V3c. Mecanico baseline: +64.57R, 234 trades.
"""
import pandas as pd
import numpy as np
import sys
from pathlib import Path

DIR = Path(__file__).parent
sys.path.insert(0, str(DIR))
from audit_xau_smc_v3 import (
    load_data, detect_pivots, track_structure, identify_ob_leonardo,
    find_last_valid_bottom, metrics, SPREAD_R, PIVOT_LEN, MAX_HOLD_BARS,
    LOOKBACK_OB, TOUCH_LOOKAHEAD,
)


def simulate_v3d(df, entry_idx, entry, stop, target_r, be_at_r=1.0, max_bars=MAX_HOLD_BARS):
    """Simulate trade with configurable BE timing.
    be_at_r=None: no BE move. be_at_r=0.5/1.0/2.0: move stop to entry when +0.5/1/2 R reached."""
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
        if be_at_r is not None and not moved_be and h >= entry + R * be_at_r:
            cur_stop = max(cur_stop, entry)
            moved_be = True
        if l <= cur_stop:
            return {'exit_idx': j, 'r': (cur_stop - entry) / R}
        if h >= target:
            return {'exit_idx': j, 'r': target_r}
    last = min(entry_idx + max_bars, n - 1)
    return {'exit_idx': last, 'r': (close[last] - entry) / R}


def run_v3d_struct(df, events, buffer_pct, be_at_r, target_r):
    """V3d struct: Leonardo OB + stop = lvb * (1 - buffer_pct/100)."""
    trades = []
    n = len(df)
    close = df['close'].values
    low = df['low'].values
    atr14 = df['atr14'].values

    for ev in events:
        if ev['type'] not in ('BOS_BULL', 'CHOCH_BULL'):
            continue
        ob = identify_ob_leonardo(df, ev)
        if ob is None:
            continue

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

        lvb = find_last_valid_bottom(df, ev)
        if lvb is None:
            continue
        stop = lvb * (1 - buffer_pct / 100.0)
        if entry <= stop:
            continue
        R = entry - stop
        atr_e = atr14[entry_idx]
        if not np.isnan(atr_e) and R > 5 * atr_e:
            continue

        res = simulate_v3d(df, entry_idx, entry, stop, target_r, be_at_r=be_at_r)
        if res is None:
            continue
        trades.append({
            'event_idx': ev['idx'], 'entry_idx': entry_idx,
            'entry_time': df.at[entry_idx, 'time'],
            'entry': float(entry), 'stop': float(stop),
            'R_pts': float(R), 'r': float(res['r']),
        })
    return trades


def run_v3d_atr_blend(df, events, atr_mult, be_at_r, target_r):
    """V3d blend: stop = lvb - atr_mult * ATR(14_at_entry).
    Combina LVB estrutural com buffer ATR — testa se metade-caminho ajuda."""
    trades = []
    n = len(df)
    close = df['close'].values
    low = df['low'].values
    atr14 = df['atr14'].values

    for ev in events:
        if ev['type'] not in ('BOS_BULL', 'CHOCH_BULL'):
            continue
        ob = identify_ob_leonardo(df, ev)
        if ob is None:
            continue

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

        lvb = find_last_valid_bottom(df, ev)
        if lvb is None:
            continue
        atr_e = atr14[entry_idx]
        if np.isnan(atr_e):
            continue
        stop = lvb - atr_mult * float(atr_e)
        if entry <= stop:
            continue
        R = entry - stop
        if R > 5 * atr_e:
            continue

        res = simulate_v3d(df, entry_idx, entry, stop, target_r, be_at_r=be_at_r)
        if res is None:
            continue
        trades.append({
            'event_idx': ev['idx'], 'entry_idx': entry_idx,
            'entry_time': df.at[entry_idx, 'time'],
            'entry': float(entry), 'stop': float(stop),
            'R_pts': float(R), 'r': float(res['r']),
        })
    return trades


def main():
    import time as t_mod
    t0 = t_mod.time()
    print("=== Loading + pivots + structure ===")
    df = load_data()
    ph, pl = detect_pivots(df, PIVOT_LEN)
    events = track_structure(df, ph, pl)
    bull = [e for e in events if e['type'] in ('BOS_BULL', 'CHOCH_BULL')]
    print(f"  Rows: {len(df)}, bull events: {len(bull)}  ({t_mod.time()-t0:.1f}s)")

    results = []
    trades_by = {}

    print("\n=== V3d STRUCT: buffer x BE x target ===")
    for buf in [0.0, 0.05, 0.1, 0.2, 0.5]:
        for be in [0.5, 1.0, 2.0, None]:
            for tg in [2.0, 2.5, 3.0, 4.0, 5.0]:
                tr = run_v3d_struct(df, events, buf, be, tg)
                m = metrics(tr)
                be_str = f"be{be}" if be else "noBE"
                label = f"struct|buf{buf}|{be_str}|tgt{tg}R"
                results.append({'config': label, **m})
                trades_by[label] = tr

    print(f"  struct done  ({t_mod.time()-t0:.1f}s)")

    print("=== V3d ATR-BLEND: atr_mult x BE x target ===")
    for atr_m in [0.0, 0.2, 0.5, 1.0]:
        for be in [0.5, 1.0, 2.0, None]:
            for tg in [2.0, 2.5, 3.0, 4.0, 5.0]:
                tr = run_v3d_atr_blend(df, events, atr_m, be, tg)
                m = metrics(tr)
                be_str = f"be{be}" if be else "noBE"
                label = f"blend|atr{atr_m}|{be_str}|tgt{tg}R"
                results.append({'config': label, **m})
                trades_by[label] = tr

    print(f"  blend done  ({t_mod.time()-t0:.1f}s)")

    df_res = pd.DataFrame(results).sort_values('total_r_net', ascending=False)
    df_res.to_csv(DIR / 'XAU_4H_SMC_v3d_summary.csv', index=False)

    print()
    print("=== TOP 15 ===")
    cols = ['config', 'n', 'trades_per_month', 'total_r_net', 'avg_r_net',
            'win_rate', 'pf_net', 'max_losing_streak', 'r_no_top5', 'r_no_top10']
    print(df_res[cols].head(15).to_string(index=False))

    print()
    print("=== Robust (PF>=1.4, total>=10R, no_top5>=0, n>=20) ===")
    rob = df_res[(df_res.pf_net >= 1.4) & (df_res.total_r_net >= 10) &
                 (df_res.r_no_top5 >= 0) & (df_res.n >= 20)]
    if len(rob) > 0:
        print(rob[cols].to_string(index=False))
    else:
        print("  NONE")

    print()
    print("=== V3c original (referencia): touch+lvb*0.9995+BE@1R+tgt5R ===")
    print("   n=36, total=+6.54R, PF=1.36, win=36.1%, no_top5=-10.54R")

    print(f"\nDone. Runtime: {t_mod.time()-t0:.1f}s")


if __name__ == '__main__':
    main()
