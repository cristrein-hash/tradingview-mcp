#!/usr/bin/env python3
"""LINHA B Round 1 — inventário de dados ANTES de construir o extrator de bottoms NOVOS. Verifica: (1) estrutura do
raw_features (sinais por-bar deriváveis: capitulação/oversold/bubbles/NAS/SMC); (2) zonas de demanda por-bar p/ SL_CONTEXT
(SVP gz pine_boxes / Custom OB?). Verified 2026-06-25."""
import json, gzip
from pathlib import Path
V1 = Path(__file__).resolve().parents[1]
SVP = "/Volumes/GUTS_ LACIE/TradingData/raw_replay/XAUUSD/4H/XAUUSD_4H_replay_2019-12_to_2026-current_SVP_LUX_RAW.jsonl.gz"

print("=== raw_features_2020_2026.jsonl ===")
recs = [json.loads(l) for l in open(V1 / "repro_recovery/raw_features_2020_2026.jsonl")]
print(f"n bars = {len(recs)}")
r = recs[5000]
print("keys:", list(r.keys()))
for k in ("bubbles_recent", "nas_recent", "smc_recent"):
    v = r.get(k)
    print(f"  {k}: type={type(v).__name__}", (v if not isinstance(v, (list, dict)) else (v[:2] if isinstance(v, list) else list(v.items())[:3])))

print("\n=== SVP gz — tem pine_boxes / Custom OB (demanda) por bar? ===")
found = False
with gzip.open(SVP, "rt") as fh:
    for i, line in enumerate(fh):
        if '"pine_boxes"' in line or "Custom OB" in line or "Order Block" in line:
            rec = json.loads(line)
            pb = rec.get("pine_boxes")
            print(f"  achou em linha {i}: pine_boxes presente={pb is not None}")
            if pb:
                names = [g.get("name") for g in pb][:8]
                print(f"  grupos pine_boxes: {names}")
                ob = next((g for g in pb if "OB" in str(g.get("name", "")) or "Order" in str(g.get("name", ""))), None)
                if ob:
                    zs = ob.get("zones") or ob.get("boxes") or []
                    print(f"  Custom OB zones sample: {zs[:2]}")
            found = True
            break
        if i > 5000: break
if not found:
    print("  NÃO achou pine_boxes/Custom OB nos primeiros 5000 — SL_CONTEXT por-bar pode precisar de outra fonte")
