#!/usr/bin/env python3
"""DA ENGINE 3 — shared core (Cris 2026-06-28). Ruthless devil's advocate on Engine-3 frontier R-outcome.
Reproduces EXACTLY engine3_routcome.py's let-run sim + engine3_qualify.py's threshold/passes/dirn logic so all
attack scripts (_DA_engine3_1..6) share one source of truth. In-sample, RAW-causal, NO OOS. Régua:
entry=close cj, SL=min low s[p..cj]-0.1ATR, cf_low trail, HMAX480, RCAP20."""
import json, statistics as st
from pathlib import Path
HERE = Path(__file__).parent

PRIM = {p.name.split(".")[0].replace("XAUUSD_15m_replay_", ""): json.loads(p.read_text())
        for p in sorted((HERE / "primitives").glob("*.primitives.json"))}
PRIMK = {k[:10]: v for k, v in PRIM.items()}
ROWS = [json.loads(l) for l in (HERE / "entry_candidates_htf.jsonl").read_text().splitlines()]
QJ = json.load(open(HERE / "engine3_qualify.json"))
base = QJ["base"]; MFtot = QJ["MFtot"]
aucs = dict(QJ["aucs"]); dirn = {f: (1 if a >= .5 else -1) for f, a in aucs.items()}

def isnum(v): return isinstance(v, (int, float)) and not isinstance(v, bool)
def thr(f, q):
    vals = sorted(r[f] for r in ROWS if isnum(r.get(f))); return vals[int(q * len(vals))]

TOP = [f for f, _ in QJ["aucs"][:14] if f != "falling_knife"]
TH = {f: (thr(f, 0.80) if dirn[f] > 0 else thr(f, 0.20)) for f in TOP}
# combo of interest may use features not in TOP14? all three are in TOP14. Build TH for them defensively:
for f in ("reclaim_atr", "swept_prior_low", "buy_bub_w"):
    if f not in TH:
        TH[f] = thr(f, 0.80) if dirn.get(f, .5) > 0 else thr(f, 0.20)

G = [r for r in ROWS if r.get("falling_knife", 0) == 0]
STANDOUT = ("reclaim_atr", "swept_prior_low", "buy_bub_w")

def passes(r, cc):
    for f in cc:
        v = r.get(f)
        if not isnum(v): return False
        if dirn[f] > 0 and v < TH[f]: return False
        if dirn[f] < 0 and v > TH[f]: return False
    return True

HMAX = 480; RCAP = 20.0
def cf_low(s, i):
    L = [b["l"] for b in s]; lo = max(2, i - 120); bst = None
    for p in range(lo, i - 1):
        if L[p] == min(L[p - 2:p + 3]): bst = L[p]
    return bst
def letrun(s, cj, entry, sl, atr):
    risk = entry - sl
    if risk <= 0: return None
    trail = sl; r1 = False; ex = None; end = min(cj + HMAX, len(s) - 1)
    for k in range(cj + 1, end + 1):
        if s[k]["l"] <= trail: ex = trail; break
        if (s[k]["h"] - entry) / risk >= 1: r1 = True
        if r1:
            sw = cf_low(s, k)
            if sw: trail = max(trail, sw - 0.1 * atr)
    if ex is None: ex = s[end]["c"]
    return max(-1.0, min(RCAP, (ex - entry) / risk))
_cache = {}
def R_of(r):
    key = (r["block"], r["cj_t"])
    if key in _cache: return _cache[key]
    pr = PRIMK.get(r["block"]); s = pr["series"]; tmap = {b["t"]: i for i, b in enumerate(s)}
    p = tmap.get(r["t"]); cj = tmap.get(r["cj_t"]); R = None
    if p is not None and cj is not None and cj + 2 < len(s):
        atr = s[p]["atr"] or s[cj]["atr"]
        if atr:
            entry = s[cj]["c"]; sl = min(x["l"] for x in s[p:cj + 1]) - 0.1 * atr
            R = letrun(s, cj, entry, sl, atr)
    _cache[key] = R; return R

def metr(sel):
    rs = [R_of(r) for r in sel]; rs = [x for x in rs if x is not None]; n = len(rs)
    if not n: return None
    sm = sum(rs); w = sum(1 for x in rs if x > 0)
    eq = pk = dd = 0
    for x in rs:
        eq += x; pk = max(pk, eq); dd = min(dd, eq - pk)
    return {"n": n, "WR": round(100 * w / n, 1), "sumR": round(sm, 1),
            "avgR": round(sm / n, 3), "maxDD": round(dd, 1)}

def R_list(sel):
    return [x for x in (R_of(r) for r in sel) if x is not None]

if __name__ == "__main__":
    print("G (knife-gated):", len(G), "MFtot", MFtot, "base", round(base, 5))
    print("TH standout:", {f: TH[f] for f in STANDOUT})
    sel = [r for r in G if passes(r, STANDOUT)]
    print("standout n:", len(sel), "metr:", metr(sel))
    print("TAKE-ALL:", metr(G))
