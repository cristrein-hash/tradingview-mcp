#!/usr/bin/env python3
"""DA RAW probe: confirm buffer cap, NAS label.x vs snapshot bar, and label price semantics.
Reads one RAW gz block EXCLUSIVELY. Verified 2026-06-25."""
import gzip, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # repo root for config import
from config import paths as CP
RAW = CP.raw("raw_replay", "XAUUSD", "15M")
BLOCK = RAW / "XAUUSD_15m_replay_2024-05-25_to_2024-08-25.jsonl.gz"


def grp(rec, key, sub):
    return next((x for x in (rec.get(key) or []) if sub.lower() in str(x.get("name", "")).lower()), None)


recs = []
with gzip.open(BLOCK, "rt") as fh:
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
print(f"snaps={len(recs)}")

# meta keys of a snapshot
r0 = recs[len(recs)//2]
print("meta keys:", [k for k in r0 if not isinstance(r0[k], (list, dict))][:20])
print("replay_current_date:", r0.get("replay_current_date"), "| ohlcv tail t:", r0["ohlcv"][-1].get("time") if r0.get("ohlcv") else None)
print("ohlcv len per snap (sample 10):", [len(x.get("ohlcv") or []) for x in recs[100:110]])

# NAS buffer sizes + a label sample (fields)
nas_lens = []
sample_lab = None
for r in recs:
    ng = grp(r, "pine_labels", "NAS")
    if ng:
        labs = ng.get("labels") or []
        nas_lens.append(len(labs))
        if sample_lab is None and labs:
            sample_lab = labs[-1]
print("NAS buffer sizes: max", max(nas_lens) if nas_lens else 0, "min", min(nas_lens) if nas_lens else 0)
print("NAS label fields:", json.dumps(sample_lab, default=str)[:300])

smc_lens = []
smc_lab = None
for r in recs:
    sg = grp(r, "pine_labels", "Smart Money")
    if sg:
        labs = sg.get("labels") or []
        smc_lens.append(len(labs))
        if smc_lab is None and labs:
            smc_lab = labs[-1]
print("SMC buffer sizes: max", max(smc_lens) if smc_lens else 0)
print("SMC label fields:", json.dumps(smc_lab, default=str)[:300])

# OB box fields
ob_box = None
for r in recs:
    ob = grp(r, "pine_boxes", "Custom OB")
    if ob and (ob.get("all_boxes")):
        ob_box = ob["all_boxes"][0]
        print("OB box keys:", list(ob_box.keys()))
        print("OB box sample:", json.dumps(ob_box, default=str)[:300])
        print("OB box other keys present? 'zones':", "zones" in ob, "'all_boxes' len:", len(ob.get("all_boxes") or []))
        break

# KEY QUESTION: does NAS label have an 'x' that maps to an EARLIER bar than the snapshot current bar?
# x is a bar index in TV's frame; we can't map directly, but check whether a NEW id appears on a
# snapshot whose current bar time is LATER than where the label visually sits. Proxy: does label 'price'
# match the snapshot current bar's OHLC range (i.e., fired on current bar) or an earlier bar?
matched_cur, matched_earlier, off = 0, 0, 0
prev_max = -1
first = True
for r in recs:
    cur = r["ohlcv"][-1] if r.get("ohlcv") else None
    ng = grp(r, "pine_labels", "NAS")
    if not ng or cur is None:
        continue
    for l in (ng.get("labels") or []):
        lid = l.get("id")
        if lid is None:
            continue
        if first:
            continue
        if lid > prev_max:
            pr = l.get("price")
            if pr is None:
                off += 1
                continue
            lo, hi = cur.get("low"), cur.get("high")
            if lo is not None and hi is not None and lo - 0.5 <= pr <= hi + 0.5:
                matched_cur += 1
            else:
                matched_earlier += 1
    ids = [l.get("id") for l in (ng.get("labels") or []) if l.get("id") is not None]
    if ids:
        prev_max = max([prev_max] + ids)
    first = False
print(f"NEW-NAS price within current bar's range = {matched_cur}; OUTSIDE (=earlier/lagged bar) = {matched_earlier}; no price = {off}")
print("  -> if 'OUTSIDE' is large, the NAS fired on a bar BEFORE the snapshot's current bar => event time (cur_t) is LATE; SHIFT1 from j may be off")
