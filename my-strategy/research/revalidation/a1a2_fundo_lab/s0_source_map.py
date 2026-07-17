#!/usr/bin/env python3
"""A1A2_FUNDO_LAB · Stage 2 — SOURCE MAP (protocolo XAU_15M V1).
Mapeia as fontes canónicas do lab ANTES de qualquer leitura de dados:
  (1) dataset_registry: entradas RAW 15M/4H/1D ativas (id, cobertura, path, sha)
  (2) GT unificado dos fundos (REGIME_GT_FUNDOS_UNIFIED_20260714.json) — contagem por família
  (3) presença física no HD externo
Output = tabela p/ colar no GATE_MANIFEST. Read-only, fail-loud. py3.9 stdlib.
"""
import json, sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
REG = REPO / "docs/data/dataset_registry.json"
GT = Path(__file__).resolve().parents[1] / "results" / "REGIME_GT_FUNDOS_UNIFIED_20260714.json"
HD = Path("/Volumes/GUTS_ LACIE/TradingData/raw_replay/XAUUSD")


def main():
    if not REG.exists():
        sys.exit(f"FALTA registry: {REG}")
    reg = json.load(open(REG))
    ds = reg.get("datasets") or reg
    if isinstance(ds, dict):
        ds = list(ds.values())
    print(f"# registry: {REG.name} · {len(ds)} datasets · keys COMPLETAS: {sorted(ds[0].keys())}")
    print("\n## RAW candidatos (15M / 4H / 1D):")
    for d in ds:
        tf = d.get("timeframe") or d.get("tf") or ""
        if str(tf) not in ("15M", "4H", "1D"):
            continue
        print(f"  - tf={tf} status={d.get('status')} {d.get('start_date','?')}→{d.get('end_date','?')} "
              f"bars={d.get('bars')} gz={d.get('raw_gz_path','?')} sha={str(d.get('sha256_original','?'))[:12]}")
    print("\n## GT unificado:")
    if not GT.exists():
        sys.exit(f"FALTA GT: {GT}")
    gt = json.load(open(GT))
    rows = gt.get("fundos") or gt.get("rows") or gt
    if isinstance(rows, dict):
        print(f"  keys: {list(rows.keys())[:10]}")
        rows = rows.get("fundos") or next((v for v in rows.values() if isinstance(v, list)), [])
    from collections import Counter
    fams = Counter(f"{r.get('classe','?')}/{r.get('subclasse','?')}" for r in rows)
    macs = Counter(str(r.get("macro", "?")) for r in rows)
    print(f"  {GT.name}: {len(rows)} fundos · por classe/subclasse: {dict(fams)}")
    print(f"  por macro: {dict(macs)}")
    if rows:
        print(f"  campos por fundo: {sorted(rows[0].keys())}")
        print(f"  exemplo: {json.dumps(rows[0], ensure_ascii=False)[:200]}")
    print("\n## HD físico:")
    for tf in ("15M", "4H", "1D"):
        p = HD / tf
        n = len(list(p.glob("*"))) if p.exists() else 0
        print(f"  {tf}: {'OK' if p.exists() else 'AUSENTE'} ({n} ficheiros)")


if __name__ == "__main__":
    main()
