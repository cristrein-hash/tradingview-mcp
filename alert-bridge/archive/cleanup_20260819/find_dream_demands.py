#!/usr/bin/env python3
"""find_dream_demands.py — localiza as 3 DEMANDs marcadas por Cris no dataset.

DEMANDs alvo:
  LONG 2: high=4033.27, low=3999.34  (altura 33.93)
  LONG 4: high=4745.23, low=4596.15  (altura 149.08)
  LONG 5: high=4310.00, low=4108.01  (altura 201.99)

Encontrar em qual bar foi CRIADA, quanto durou, e comparar com outras DEMANDs ativas no mesmo bar.
"""
from pathlib import Path
import json
from datetime import datetime, timezone
from statistics import mean

def repo_root():
    """Resolve the tradingview-mcp repo root robustly (survives file moves)."""
    import os
    from pathlib import Path as _Path
    env = os.environ.get("TVMCP_ROOT")
    if env and _Path(env).expanduser().is_dir():
        return _Path(env).expanduser().resolve()
    cur = _Path(__file__).resolve().parent
    for d in (cur, *cur.parents):
        if (d / ".git").exists() or (d / "src" / "server.js").exists() \
           or ((d / "alert-bridge").is_dir() and (d / "my-strategy").is_dir()):
            return d
    raise RuntimeError(f"TVMCP repo root not found from {__file__}; set TVMCP_ROOT or run inside the repo")


BASE = repo_root()
JSONL_DIR = BASE / "alert-bridge" / "logs" / "backtests"
WINDOWS = [
    ("W1_2023H1","XAUUSD_240_2023-01-19_to_2026-05-21_v6.jsonl"),
    ("W2_2023H2","XAUUSD_240_2023-07-19_to_2026-05-21_v6.jsonl"),
    ("W3_2024H1","XAUUSD_240_2024-01-19_to_2026-05-21_v6.jsonl"),
    ("W4_2024H2","XAUUSD_240_2024-07-19_to_2026-05-21_v6.jsonl"),
    ("W5_2025May","XAUUSD_240_2025-05-19_to_2026-05-21_v6.jsonl"),
    ("W6_2025Sep","XAUUSD_240_2025-09-15_to_2026-05-21_v6.jsonl"),
    ("W7_2025Nov","XAUUSD_240_2025-11-19_to_2026-05-21_v6.jsonl"),
    ("W8_2026Mar","XAUUSD_240_2026-03-19_to_2026-05-21_v6.jsonl"),
]
TARGETS = [
    ("LONG 2", 4033.27, 3999.34),
    ("LONG 4", 4745.23, 4596.15),
    ("LONG 5", 4310.00, 4108.01),
]
PRICE_TOL = 30.0  # ±$30 — boxes desenhadas manualmente podem ter offset


def fmt(t):
    return datetime.fromtimestamp(t, tz=timezone.utc).strftime("%Y-%m-%d %H:%M")


def main():
    print(f"=== Find Dream DEMANDs ===\n")

    # Para cada target, varrer todas as windows e achar bars onde DEMAND com high/low próximos existem
    for label, target_hi, target_lo in TARGETS:
        print(f"\n--- {label} target high={target_hi} low={target_lo} (height={target_hi-target_lo:.2f}) ---")
        found_in_bars = []  # [(window, time, all_demands_at_this_bar)]
        for w_label, fname in WINDOWS:
            p = JSONL_DIR / fname
            if not p.exists(): continue
            with p.open() as f:
                for line in f:
                    try: b = json.loads(line)
                    except: continue
                    t = (b.get('ohlcv_last_40_bars') or [{}])[-1].get('time')
                    if t is None: continue
                    # Look in ALL pine_boxes (Custom OB + LuxAlgo + qualquer outro)
                    for s in (b.get('pine_boxes') or []):
                        s_name = s.get('name','')
                        for box in (s.get('all_boxes') or []):
                            hi = box.get('high'); lo = box.get('low')
                            if hi is None or lo is None: continue
                            if abs(hi-target_hi)<=PRICE_TOL and abs(lo-target_lo)<=PRICE_TOL:
                                found_in_bars.append({
                                    'window':w_label,'time':t,'box_id':box.get('id'),
                                    'indicator':s_name,
                                    'box_high':hi,'box_low':lo,'box_text':box.get('text'),
                                    'bar_close':(b.get('ohlcv_last_40_bars') or [{}])[-1].get('close'),
                                    'bar_low':(b.get('ohlcv_last_40_bars') or [{}])[-1].get('low'),
                                    'bar_high':(b.get('ohlcv_last_40_bars') or [{}])[-1].get('high'),
                                })
            # Skip duplicates by box_id and time
        # Dedup por (window, time)
        seen = set(); deduped = []
        for f in found_in_bars:
            key = (f['window'], f['time'])
            if key in seen: continue
            seen.add(key); deduped.append(f)

        if not deduped:
            print(f"  NOT FOUND. ⚠️")
            continue
        deduped.sort(key=lambda x:(x['window'],x['time']))
        # Agrupar por indicator + box_id
        by_source = {}
        for f in deduped:
            key = (f['indicator'], f['box_text'])
            by_source.setdefault(key, []).append(f)
        for (ind, txt), bars_list in by_source.items():
            first = bars_list[0]; last = bars_list[-1]
            print(f"  → INDICATOR: '{ind}'  TEXT: {repr(txt)}")
            print(f"    Encontrada em {len(bars_list)} bars")
            print(f"    PRIMEIRO: {first['window']} {fmt(first['time'])} (high={first['box_high']:.2f}, low={first['box_low']:.2f})")
            print(f"    ÚLTIMO: {last['window']} {fmt(last['time'])}")
            print(f"    DURAÇÃO: ~{(last['time']-first['time'])//14400} bars 4H ({(last['time']-first['time'])/86400:.1f} dias)")

    return 0


if __name__ == "__main__":
    main()
