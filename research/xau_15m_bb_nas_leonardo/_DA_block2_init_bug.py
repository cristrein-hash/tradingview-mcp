#!/usr/bin/env python3
"""DA: confirm the first-snapshot init failure in block 2 (2024-08-25). 500 NAS events on one snap.
Hypothesis: the FIRST snapshot of block 2 had FEWER labels (or different ids) than a later snap, so
`first` init under-set max_nas, and when the full 500-buffer of pre-existing history arrived on snap 2,
all 500 ids > max_nas were emitted as 'new' events. Same mechanism inflates bc50 (504) for block start.
Reads block-2 primitives + RAW. Verified 2026-06-25."""
import json, gzip, glob
from pathlib import Path
HERE = Path(__file__).parent
RAW = Path("/Volumes/GUTS_ LACIE/TradingData/raw_replay/XAUUSD/15M")


def grp(rec, key, sub):
    return next((x for x in (rec.get(key) or []) if sub.lower() in str(x.get("name", "")).lower()), None)


prim = next(p for p in glob.glob(str(HERE / "primitives/*.json")) if "2024-08-25" in p)
d = json.load(open(prim))
from collections import Counter
c = Counter(e["t"] for e in d["nas_events"])
worst_t, worst_n = c.most_common(1)[0]
print(f"block2 nas_events total={len(d['nas_events'])}; worst snapshot t={worst_t} got {worst_n} 'new' NAS events")
import datetime as dt
print(f"  that t = {dt.datetime.utcfromtimestamp(worst_t)} UTC")

# Now inspect the RAW: first few snapshots' NAS buffers (ids)
raw = next(r for r in RAW.glob("*.jsonl.gz") if "2024-08-25" in r.name)
recs = []
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
            recs.append(r)
recs.sort(key=lambda r: r.get("replay_current_date") or 0)
print(f"  block2 snaps={len(recs)}")
for si in range(min(4, len(recs))):
    ng = grp(recs[si], "pine_labels", "NAS")
    ids = [l.get("id") for l in (ng.get("labels") or [])] if ng else []
    cur = recs[si]["ohlcv"][-1].get("time") if recs[si].get("ohlcv") else None
    print(f"  snap[{si}] cur_t={cur} n_NAS_labels={len(ids)} id_min={min(ids) if ids else None} id_max={max(ids) if ids else None}")
# Did the FIRST snapshot have NO NAS group at all? Then `first` stayed True with max_nas=-1,
# and the build code sets first=False at end of loop regardless -> snap2 emits everything > -1.
ng0 = grp(recs[0], "pine_labels", "NAS")
print(f"  snap[0] has NAS group? {ng0 is not None}; labels={len((ng0.get('labels') or [])) if ng0 else 0}")
