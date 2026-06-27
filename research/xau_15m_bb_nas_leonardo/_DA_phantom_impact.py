#!/usr/bin/env python3
"""DA: quantify the empty-first-snapshot init bug across ALL blocks and its impact on the 791 candidates.
For each primitives block: count nas_events / smc_events sharing the SINGLE worst timestamp (phantom flood).
Then check candidates_stageB.csv: how many candidates have nas_t == a phantom-flood timestamp.
Reads primitives + candidates CSV (no RAW). Verified 2026-06-25."""
import json, glob, csv
from pathlib import Path
from collections import Counter
import datetime as dt
HERE = Path(__file__).parent

phantom_ts = {}  # block -> set of flood timestamps
print("=== per-block phantom flood (>=20 events at one timestamp = pre-existing buffer dumped) ===")
for p in sorted(glob.glob(str(HERE / "primitives/*.json"))):
    d = json.load(open(p))
    blk = d["block"].replace("XAUUSD_15m_replay_", "").replace(".jsonl.gz", "")
    cn = Counter(e["t"] for e in d["nas_events"])
    cs = Counter(e["t"] for e in d["smc_events"])
    nas_flood = {t: n for t, n in cn.items() if n >= 20}
    smc_flood = {t: n for t, n in cs.items() if n >= 20}
    phantom_ts[blk] = set(nas_flood) | set(smc_flood)
    if nas_flood or smc_flood:
        nf = list(nas_flood.items())[:1]
        sf = list(smc_flood.items())[:1]
        print(f"  {blk}: NAS_flood={nas_flood} SMC_flood={smc_flood}")
    else:
        print(f"  {blk}: clean (no flood)")

print("\n=== impact on candidates_stageB.csv ===")
rows = list(csv.DictReader(open(HERE / "candidates_stageB.csv")))
poll = 0
for r in rows:
    blk = r["block"]
    if int(r["nas_t"]) in phantom_ts.get(blk, set()):
        poll += 1
print(f"  total candidates = {len(rows)}; candidates whose nas_t is a PHANTOM-FLOOD timestamp = {poll}")
# also: candidates at the very first usable bar of each block (j small) get corrupted bc50/op_flow regardless
small_j = sum(1 for r in rows if int(r["smc_bos_choch_50"]) > 50)
print(f"  candidates with bc50>50 (corrupted SMC window from flood) = {small_j}")
# direction split of phantom candidates
ph = [r for r in rows if int(r["nas_t"]) in phantom_ts.get(r["block"], set())]
print(f"  phantom candidates dir split: {Counter(r['dir'] for r in ph)}")
for r in ph[:10]:
    print(f"    {r['block']} {r['entry_dt']} {r['dir']} nas_id={r['nas_id']} bc50={r['smc_bos_choch_50']}")
