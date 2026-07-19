#!/usr/bin/env python3
"""PARIDADE do loader LIVE do B (2026-07-19) — prova que load_series_live (gz + cauda do store) reproduz
BYTE-A-BYTE o b_signal gz-only nos B fundos in-sample. As barras históricas ficam intocadas (store só toca
a cauda recente; EMA/ATR causais forward). Gate anti-Telegram: sem PASS aqui, o B não vai a produção."""
import json, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent; sys.path.insert(0, str(HERE))
import b_forward_score as BF
import b_engine_v1 as BE
from a1_causal_entry import load_series

GT = json.load(open(HERE / "results" / "REGIME_GT_FUNDOS_UNIFIED_20260714.json"))
B = sorted([f for f in GT["fundos"] if f.get("subclasse") == "B_range"], key=lambda x: x["t"])
KEYS = ("ent", "sl", "R", "RATR")
mism = 0
print(f"{'fundo_t':>12} {'gz':>6} {'live':>6} {'entry(gz)':>18} {'entry(live)':>18} {'match':>6}")
for f in B:
    t0 = int(f["t"])
    r_gz = BE.b_signal(t0, load_series(BF.blocks_covering(t0)))
    r_lv = BE.b_signal(t0, BF.load_series_live(t0))
    on_gz, on_lv = r_gz.get("engine"), r_lv.get("engine")
    eg = r_gz.get("entry") or {}; el = r_lv.get("entry") or {}
    same = (on_gz == on_lv) and all(eg.get(k) == el.get(k) for k in KEYS) and r_gz.get("reason") == r_lv.get("reason")
    if not same: mism += 1
    sg = f"{eg.get('ent','-')}/{eg.get('sl','-')}" if on_gz else (r_gz.get("reason") or "-")
    sl = f"{el.get('ent','-')}/{el.get('sl','-')}" if on_lv else (r_lv.get("reason") or "-")
    print(f"{t0:>12} {str(on_gz):>6} {str(on_lv):>6} {sg:>18} {sl:>18} {'OK' if same else 'DIFF':>6}")
print(f"\n== PARIDADE B live: {len(B)-mism}/{len(B)} idênticos · mismatches={mism} ==")
print("PASS" if mism == 0 else "FAIL — store tail alterou histórico (investigar antes de go-live)")
sys.exit(0 if mism == 0 else 1)
