#!/usr/bin/env python3
"""RAW-first parte 2: estrutura de all_boxes (Custom OB: texto DEMAND/SUPPLY + mitigação = ciclo de vida da zona),
pine_lines, ohlcv_meta, _feature_availability, SMC pine_boxes, e acumulação de labels NAS/SMC entre snapshots
(p/ detectar first-appearance causal). Fonte RAW gz exclusiva. Inspeção, não backtest. Verified 2026-06-25."""
import gzip, json
from pathlib import Path
BLOCK = Path("/Volumes/GUTS_ LACIE/TradingData/raw_replay/XAUUSD/15M/XAUUSD_15m_replay_2024-05-25_to_2024-08-25.jsonl.gz")
def short(o, n=600): s = json.dumps(o, ensure_ascii=False, default=str); return s if len(s) <= n else s[:n] + "…"
recs = []
with gzip.open(BLOCK, "rt") as fh:
    for line in fh:
        line = line.strip()
        if line:
            try: recs.append(json.loads(line))
            except Exception: pass
        if len(recs) >= 400: break
def grp(rec, key, sub): return next((x for x in (rec.get(key) or []) if sub.lower() in str(x.get("name","")).lower()), None)
rich = next((r for r in recs if grp(r, "pine_boxes", "Custom OB")), recs[0])
ob = grp(rich, "pine_boxes", "Custom OB")
print("=== Custom OB: all_boxes[0..2] (ciclo de vida / DEMAND-SUPPLY / mitigação) ===")
ab = ob.get("all_boxes") or []
print("  total all_boxes:", len(ab))
for b in ab[:3]: print("   ", short(b, 400))
print("  keys de um all_box:", list(ab[0].keys()) if ab else "—")
print("\n=== SMC pine_boxes (order blocks) ===")
smcb = grp(rich, "pine_boxes", "Smart Money")
if smcb:
    print("  keys:", list(smcb.keys())); print("  zones[:2]:", short((smcb.get("zones") or [])[:2], 300))
    print("  all_boxes[0]:", short((smcb.get("all_boxes") or [{}])[0], 300))
print("\n=== pine_lines ===")
pl = rich.get("pine_lines") or []
print("  names:", [x.get("name") for x in pl if isinstance(x, dict)])
print("  sample:", short(pl[0] if pl else None, 300))
print("\n=== ohlcv_meta ===");            print("  ", short(rich.get("ohlcv_meta"), 300))
print("=== _feature_availability ===");   print("  ", short(rich.get("_feature_availability"), 400))
# NAS study_values (pode ter contadores/diferente de labels)
nasv = grp(rich, "study_values", "NAS")
print("\n=== NAS study_values ===");       print("  ", short(nasv, 300))
bub = grp(rich, "study_values", "Bubbles") or grp(rich, "study_values", "Market Order")
print("=== Bubbles study_values (activations_per_plot?) ===")
print("  keys:", list(bub.keys()) if bub else "—"); print("  ", short(bub, 400))
# acumulação de labels entre snapshots (first-appearance causal)
def lblids(rec, sub):
    g = grp(rec, "pine_labels", sub); return set(l.get("id") for l in (g.get("labels") or [])) if g else set()
import itertools
sample_idx = [50, 150, 250, 350]
print("\n=== acumulação de ids NAS/SMC entre snapshots (first-appearance) ===")
for i in sample_idx:
    if i < len(recs):
        r = recs[i]; dt = r.get("replay_current_dt")
        print(f"  rec[{i}] {dt}: NAS_ids={len(lblids(r,'NAS'))} SMC_ids={len(lblids(r,'Smart Money'))} bar_index={r.get('bar_index')}")
# diff: novos NAS entre dois snapshots consecutivos do sample
if len(recs) > 150:
    a, b = lblids(recs[149], "NAS"), lblids(recs[150], "NAS")
    print(f"  novos NAS ids rec[149]→[150]: {sorted(b - a)[:10]}")
