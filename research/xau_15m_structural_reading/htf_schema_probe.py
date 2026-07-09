#!/usr/bin/env python3
"""SANITY_PROBE — verificar schema dos RAW 30M/1H do HD: as boxes do Custom OB Detector existem?
Read-only, 3 linhas por ficheiro, ledgered. Zero primitives."""
import gzip, json
BASE = "/Volumes/GUTS_ LACIE/TradingData/raw_replay/XAUUSD"
for p in (f"{BASE}/1H/XAUUSD_60m_replay_2025-11-25_to_2026-05-25.jsonl.gz",
          f"{BASE}/30M/XAUUSD_30m_replay_2025-05-25_to_2025-11-25.jsonl.gz"):
    print("=== ", p.split("/")[-1])
    with gzip.open(p, "rt", errors="replace") as fh:
        for k, ln in enumerate(fh):
            if k > 400: break
            r = json.loads(ln)
            pb = r.get("pine_boxes")
            if pb:
                studies = [s.get("study") or s.get("name") for s in pb] if isinstance(pb, list) else list(pb.keys())
                print("  keys:", sorted(r.keys()))
                print("  pine_boxes studies:", studies[:6])
                if isinstance(pb, list) and pb:
                    z = pb[0]
                    print("  sample:", json.dumps(z)[:300])
                elif isinstance(pb, dict):
                    k0 = list(pb.keys())[0]
                    print("  sample:", json.dumps(pb[k0])[:300])
                break
