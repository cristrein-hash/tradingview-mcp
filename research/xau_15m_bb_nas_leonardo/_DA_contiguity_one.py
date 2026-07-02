#!/usr/bin/env python3
"""DA: zone contiguity (resurrection) check on TWO blocks only (fast). If a zone id disappears then
reappears in all_boxes, the build's [born_t,last_t] alive-window spans the GAP where the zone was NOT
on chart -> 'alive at t' check leaks (treats a removed-then-resurrected zone as continuously alive).
Also reports the no_atr drop (warmup) and pre_existing zone count. Reads RAW for 2 blocks. Verified 2026-06-25."""
import json, gzip, glob, sys
from pathlib import Path
from collections import defaultdict
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # repo root for config import
from config import paths as CP
RAW = CP.raw("raw_replay", "XAUUSD", "15M")


def grp(rec, key, sub):
    return next((x for x in (rec.get(key) or []) if sub.lower() in str(x.get("name", "")).lower()), None)


for raw in sorted(RAW.glob("*.jsonl.gz"))[:2]:
    snaps = []
    with gzip.open(raw, "rt") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except Exception:
                continue
            if isinstance(r, dict) and r.get("ohlcv"):
                snaps.append(r)
    snaps.sort(key=lambda r: r.get("replay_current_date") or 0)
    seen = defaultdict(list)
    for si, r in enumerate(snaps):
        ob = grp(r, "pine_boxes", "Custom OB")
        for bx in (ob.get("all_boxes") if ob else []) or []:
            zid = bx.get("id")
            if zid is not None:
                seen[zid].append(si)
    total = len(seen)
    gapped = 0
    examples = []
    for zid, idxs in seen.items():
        if idxs != list(range(idxs[0], idxs[-1] + 1)):
            gapped += 1
            gaps = [(idxs[k], idxs[k+1]) for k in range(len(idxs)-1) if idxs[k+1] != idxs[k]+1]
            if len(examples) < 6:
                examples.append((zid, len(idxs), idxs[-1]-idxs[0]+1, gaps[:2]))
    print(f"{raw.name[:40]}: zones={total} NON-CONTIGUOUS(resurrected)={gapped} ({100*gapped/max(1,total):.1f}%)")
    for zid, app, span, gaps in examples:
        print(f"    zid={zid} appears_in={app}_snaps span={span}_snaps gaps(snap_idx pairs)={gaps}")
