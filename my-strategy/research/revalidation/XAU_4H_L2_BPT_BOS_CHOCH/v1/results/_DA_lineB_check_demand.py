#!/usr/bin/env python3
"""Verifica estrutura das zonas de demanda (Custom OB) no RAW SVP gz, antes de extrair SL_CONTEXT p/ os 123 fundos.
So inspeção. Verified 2026-06-25."""
import json, gzip
SVP = "/Volumes/GUTS_ LACIE/TradingData/raw_replay/XAUUSD/4H/XAUUSD_4H_replay_2019-12_to_2026-current_SVP_LUX_RAW.jsonl.gz"
import collections
seen_names = collections.Counter()
checked = 0; shown = False
with gzip.open(SVP, "rt") as fh:
    for line in fh:
        if '"pine_boxes"' not in line: continue
        rec = json.loads(line); pb = rec.get("pine_boxes") or []
        checked += 1
        for g in pb:
            seen_names[g.get("name")] += 1
        nonempty = [g for g in pb if (g.get("zones") or g.get("boxes"))]
        if nonempty and not shown:
            print(f"primeiro registro com zonas (após {checked} com pine_boxes):")
            for g in nonempty[:6]:
                zlist = g.get("zones") or g.get("boxes") or []
                print(f"  grupo '{g.get('name')}' keys={list(g.keys())} | n={len(zlist)} | sample={zlist[:2]}")
            shown = True
        if checked > 6000: break
print("\nnomes de grupos pine_boxes vistos (freq):", dict(seen_names.most_common(15)))
