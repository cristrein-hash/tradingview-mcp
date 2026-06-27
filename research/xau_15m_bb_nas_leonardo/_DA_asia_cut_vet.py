#!/usr/bin/env python3
"""DA VET of the pre-registered Asia-cut loser-cut test (_deepen_asia_cut.py).
Decomposes the Asia 00-06 isolated bucket per-year to check whether the negative
edge is robust across years or carried by one year/a few trades. with_macro base,
let-run outcome (replica of _deepen_asia_cut.py outcome engine). Verified 2026-06-26."""
import csv, json, datetime as dt
from pathlib import Path
HERE = Path(__file__).parent
PRIM = {p.name.split(".")[0].replace("XAUUSD_15m_replay_", ""): json.loads(p.read_text())
        for p in (HERE / "primitives").glob("*.primitives.json")}
SER = {b: pr["series"] for b, pr in PRIM.items()}
TID = {b: {x["t"]: i for i, x in enumerate(s)} for b, s in SER.items()}
K, HMAX, MIN_RISK_ATR, R_CAP = 2, 480, 0.5, 15.0
def cl(s, i):
    L = [b["l"] for b in s]; lo = max(K, i-120); best = None
    for p in range(lo, i-K+1):
        if L[p] == min(L[p-K:p+K+1]): best = L[p]
    return best
def ch(s, i):
    H = [b["h"] for b in s]; lo = max(K, i-120); best = None
    for p in range(lo, i-K+1):
        if H[p] == max(H[p-K:p+K+1]): best = H[p]
    return best
def out(s, ei, e, sl0, lg, atr):
    struct = (e-sl0) if lg else (sl0-e)
    if struct <= 0: return None
    risk = max(struct, MIN_RISK_ATR*atr); sl0 = (e-risk) if lg else (e+risk)
    tr = sl0; r1 = False; ex = None; end = min(ei+HMAX, len(s)-1)
    for i in range(ei+1, end+1):
        b = s[i]
        if lg:
            if b["l"] <= tr: ex = tr; break
            if (b["h"]-e)/risk >= 1: r1 = True
            if r1:
                sw = cl(s, i)
                if sw: tr = max(tr, sw-0.1*atr)
        else:
            if b["h"] >= tr: ex = tr; break
            if (e-b["l"])/risk >= 1: r1 = True
            if r1:
                sh = ch(s, i)
                if sh: tr = min(tr, sh+0.1*atr)
    if ex is None: ex = s[end]["c"]
    return max(-1.0, min(R_CAP, ((ex-e) if lg else (e-ex))/risk))
T = []
for r in csv.DictReader(open(HERE/"candidates_annotated.csv")):
    if r["setup_vs_macro"] != "with_macro": continue
    b = r["block"]; s = SER.get(b); ei = TID.get(b, {}).get(int(r["entry_t"]))
    if s is None or ei is None or ei+2 >= len(s): continue
    e = float(r["entry_close"]); zlo = float(r["zone_low"]); zhi = float(r["zone_high"]); zwa = float(r["zone_width_atr"])
    atr = (zhi-zlo)/zwa if zwa > 0 else None
    if not atr: continue
    lg = r["dir"] == "LONG"; sl0 = (zlo-0.1*atr) if lg else (zhi+0.1*atr)
    R = out(s, ei, e, sl0, lg, atr)
    if R is None: continue
    d = dt.datetime.utcfromtimestamp(int(r["entry_t"]))
    if 0 <= d.hour < 7:
        T.append({"R": R, "win": R > 0, "yr": d.year})
print("ASIA 00-06 isolated, per-year (with_macro, let-run):")
for yr in (2024, 2025, 2026):
    sub = [x for x in T if x["yr"] == yr]
    if sub:
        n = len(sub); w = sum(1 for x in sub if x["win"]); sm = sum(x["R"] for x in sub)
        print(f"  {yr}: n={n} WR={100*w/n:.0f}% sumR={sm:+.1f} avgR={sm/n:+.2f}")
n = len(T); w = sum(1 for x in T if x["win"]); sm = sum(x["R"] for x in T)
print(f"  ALL: n={n} WR={100*w/n:.0f}% sumR={sm:+.1f}")
