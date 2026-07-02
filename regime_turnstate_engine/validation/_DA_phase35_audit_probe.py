#!/usr/bin/env python3
"""_DA_phase35_audit_probe.py — audit probe for the DA on _DA_phase35_causal_zones.py.

Checks raised by the second-order Devil's Advocate:
  (A) segment/trade coverage: how many of the 245 trades are even eligible
      (inside a segment 2022-12-30..2026-05-24)? which regime?
  (B) does the causal zone construction anchor at prior.lo correctly, and is the
      'no_seg' drop (114 trades) biasing the base-rate comparison?
  (C) hand-drawn BOTTOM windows vs causal segment structure — did the causal
      test even look at the SAME segments the hand-drawn zones reference?
Only analysis; nothing touches production or the chart."""
import json, csv, io, contextlib, sys, datetime as dt
from collections import Counter
from pathlib import Path

VAL = Path("/Users/cristrein/tradingview-mcp/regime_turnstate_engine/validation")
sys.path.insert(0, str(VAL))
with contextlib.redirect_stdout(io.StringIO()):
    import phase10_hybrid_regime as P
T = P.T

segs = json.load(open("/tmp/causal_segments_v10.json"))
segs = sorted(segs, key=lambda s: s["start"])
D = Path("/Users/cristrein/tradingview-mcp/my-strategy/research/revalidation/"
         "XAU_4H_L2_BPT_BOS_CHOCH/v1/results")
trades = []
for r in csv.DictReader(open(D / "l2_bpt_regua_structural.csv")):
    bi = int(r["bar_idx"])
    trades.append({"bi": bi, "t": T[bi], "entry": float(r["entry"]),
                   "R": round(float(r["letrun_struct"]) - 0.35, 2)})


def dds(t):
    return dt.datetime.utcfromtimestamp(t).strftime("%Y-%m-%d")


def seg_index_at(t):
    for i, s in enumerate(segs):
        if s["start"] <= t <= s["end"]:
            return i
    return None


def stats(rows):
    if not rows:
        return "EMPTY"
    n = len(rows)
    wr = 100 * sum(1 for x in rows if x["R"] > 0) / n
    sr = sum(x["R"] for x in rows)
    return f"N={n} WR={wr:.0f}% sumR={sr:+.1f} avgR={sr / n:+.3f}"


print("=" * 90)
print("(A) COVERAGE")
insid = [x for x in trades if seg_index_at(x["t"]) is not None]
outsid = [x for x in trades if seg_index_at(x["t"]) is None]
print("  total trades:", len(trades))
print("  inside a segment (eligible):", len(insid), "->", stats(insid))
print("  outside all segments (no_seg dropped):", len(outsid), "->", stats(outsid))
c = Counter(segs[seg_index_at(x["t"])]["regime"] for x in insid)
print("  regime of eligible trades:", dict(c))
print("  segments span:", dds(segs[0]["start"]), "->", dds(segs[-1]["end"]))
print("  trades span:", dds(trades[0]["t"]), "->", dds(trades[-1]["t"]))

print("=" * 90)
print("(B) BASE-RATE FRAMING: >=2023 book vs eligible-in-segment book")
Y23 = [x for x in trades if dt.datetime.utcfromtimestamp(x["t"]).year >= 2023]
print("  >=2023 (used as base in script):", stats(Y23))
print("  eligible-in-segment (true universe of zone test):", stats(insid))
# BEAR-only and RANGE-only eligible (where 'bottom retest' thesis should live)
for reg in ("BULL", "RANGE", "BEAR"):
    sub = [x for x in insid if segs[seg_index_at(x["t"])]["regime"] == reg]
    print(f"    eligible {reg}:", stats(sub))

print("=" * 90)
print("(C) HAND-DRAWN BOTTOM windows vs segment overlap")
HAND_BOT = [("eKxgPH", 2542.55, 2429.92, 1723456800, 1738551600),
            ("klGwY0", 4007.03, 3819.12, 1759284000, 1770202800)]
for bid, hi, lo, t0, t1 in HAND_BOT:
    overlap = [s["regime"] for s in segs if s["start"] <= t1 and s["end"] >= t0]
    hits = [x for x in trades if t0 <= x["t"] <= t1 and lo <= x["entry"] <= hi]
    hits_elig = [x for x in hits if seg_index_at(x["t"]) is not None]
    print(f"  [{bid}] {dds(t0)}->{dds(t1)} zone[{lo:.0f},{hi:.0f}]")
    print(f"     segments overlapping window regimes: {overlap}")
    print(f"     hand-drawn hits: {len(hits)}  Rs={[x['R'] for x in hits]}")
    print(f"     of which inside a causal segment: {len(hits_elig)}")
    # were these hits BULL-regime (uptrend pullback) not BEAR-bottom?
    regs = [segs[seg_index_at(x['t'])]['regime'] if seg_index_at(x['t']) is not None else 'NONE' for x in hits]
    print(f"     regime at each hit: {regs}")

print("\n(fim probe)")
