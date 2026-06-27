#!/usr/bin/env python3
"""RAW-first: audita o schema REAL de um bloco RAW 15M (Custom OB v11 baseline) antes de montar o extrator.
Dump compacto: top-level keys, nomes de study_values/pine_boxes/pine_labels/pine_shapes, e UMA amostra de cada
estrutura relevante (Custom OB zona, NAS label, SMC label, bubbles, RSI, ohlcv). Fonte: RAW gz EXCLUSIVO.
NÃO produz resultado de backtest — só inspeção de estrutura. Verified 2026-06-25."""
import gzip, json
from pathlib import Path
RAW = Path("/Volumes/GUTS_ LACIE/TradingData/raw_replay/XAUUSD/15M")
BLOCK = RAW / "XAUUSD_15m_replay_2024-05-25_to_2024-08-25.jsonl.gz"
def short(o, n=240):
    s = json.dumps(o, ensure_ascii=False, default=str); return s if len(s) <= n else s[:n] + "…"
recs = []
with gzip.open(BLOCK, "rt") as fh:
    for i, line in enumerate(fh):
        line = line.strip()
        if not line: continue
        try: recs.append(json.loads(line))
        except Exception: continue
        if len(recs) >= 60: break
print(f"bloco: {BLOCK.name}  | registros lidos (amostra): {len(recs)}")
# achar um registro 'rico' (com ohlcv + estudos)
rich = next((r for r in recs if isinstance(r, dict) and (r.get("ohlcv") or r.get("study_values") or r.get("pine_boxes"))), recs[0] if recs else {})
print("\n=== TOP-LEVEL KEYS (registro rico) ===")
for k in (rich.keys() if isinstance(rich, dict) else []):
    v = rich[k]; t = type(v).__name__; ln = (len(v) if hasattr(v, "__len__") and not isinstance(v, str) else "")
    print(f"  {k:<28} {t:<8} {ln}")
def names(rec, key, namek="name"):
    out = []
    for x in (rec.get(key) or []):
        if isinstance(x, dict): out.append(str(x.get(namek, x.get("id", "?"))))
    return out
print("\n=== study_values names ===");      print("  ", names(rich, "study_values"))
print("=== pine_boxes names ===");          print("  ", names(rich, "pine_boxes"))
print("=== pine_labels names ===");         print("  ", names(rich, "pine_labels"))
print("=== pine_shapes* keys presentes ==="); print("  ", [k for k in rich if "shape" in k.lower() or "bubble" in k.lower()])
# amostras de estrutura
def grp(rec, key, sub):
    return next((x for x in (rec.get(key) or []) if sub.lower() in str(x.get("name", "")).lower()), None)
ob = grp(rich, "pine_boxes", "Custom OB")
print("\n=== AMOSTRA Custom OB (pine_boxes) ===")
if ob:
    print("  name:", ob.get("name"))
    z = (ob.get("zones") or [])[:2]
    print("  zones[:2]:", short(z, 400))
    print("  keys da box:", list(ob.keys()))
nas = grp(rich, "pine_labels", "NAS") or grp(rich, "pine_labels", "Nadaraya")
print("\n=== AMOSTRA NAS (pine_labels) ===")
if nas:
    print("  name:", nas.get("name")); print("  labels[-3:]:", short((nas.get("labels") or [])[-3:], 400))
smc = grp(rich, "pine_labels", "Smart Money") or grp(rich, "pine_labels", "SMC")
print("\n=== AMOSTRA SMC (pine_labels) ===")
if smc:
    print("  name:", smc.get("name")); print("  labels[-3:]:", short((smc.get("labels") or [])[-3:], 400))
bub = None
for k in rich:
    if "bubble" in k.lower() or "shape" in k.lower():
        g = rich[k]; bub = (k, g); break
print("\n=== AMOSTRA Bubbles/Shapes ===")
if bub: print("  key:", bub[0], "| sample:", short(bub[1], 400))
rsi = grp(rich, "study_values", "Relative Strength") or grp(rich, "study_values", "RSI")
print("\n=== AMOSTRA RSI (study_values) ==="); print("  ", short(rsi, 300) if rsi else "—")
oh = rich.get("ohlcv")
print("\n=== AMOSTRA ohlcv ===")
print("  type:", type(oh).__name__, "| tail:", short(oh[-2:] if isinstance(oh, list) else oh, 300))
print("\n=== meta do registro (campos de tempo/symbol) ===")
for k in ("replay_current_dt", "time", "ts", "symbol", "resolution", "tf"):
    if isinstance(rich, dict) and k in rich: print(f"  {k} = {rich[k]}")
