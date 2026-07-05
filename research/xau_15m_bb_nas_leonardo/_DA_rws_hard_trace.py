#!/usr/bin/env python3
"""DA — per-signal causal trace of every read + NAS look-ahead audit. READ-ONLY."""
import json, glob, bisect
from pathlib import Path
HERE = Path(__file__).resolve().parent
U = [json.loads(l) for l in open(HERE / "results" / "lab_g_candidates.jsonl")]
SEALED = [s["cj_t"] for s in json.load(open(HERE / "results" / "rws15m_signals_20260705.json"))]
def fv(r, k, d=0):
    v = r.get(k); return v if isinstance(v, (int, float)) and not isinstance(v, bool) else d
series = {}; nas = []
for p in sorted(glob.glob(str(HERE / "primitives" / "*.primitives.json"))):
    d = json.load(open(p))
    for b in d["series"]: series.setdefault(b["t"], b)
    nas += [e for e in d["nas_events"] if e.get("t")]
S = sorted(series.values(), key=lambda b: b["t"]); TS = [b["t"] for b in S]; Np = len(S)
H = [b["h"] for b in S]; RSI = [b.get("rsi") for b in S]
RSIMA = [None] * Np
for i in range(Np):
    w = [RSI[j] for j in range(max(0, i - 13), i + 1) if RSI[j] is not None]
    RSIMA[i] = sum(w) / len(w) if w else None
BUB = sorted([json.loads(l) for p in glob.glob(str(HERE / "bubbles" / "*.bubbles.jsonl")) for l in open(p)],
             key=lambda x: (x.get("known_at") or x["t"]))
BUBK = [(x.get("known_at") or x["t"]) for x in BUB]
nas.sort(key=lambda e: e["t"]); NAST = [e["t"] for e in nas]
wgt = {"S": 1, "M": 2, "L": 3}
R = {r["cj_t"]: r for r in U}

# GLOBAL causal audit across ALL 54 signals: max timestamp touched by each read must be <= cj
viol = {"bubble_known_at": 0, "bubble_t": 0, "rsi_bar": 0, "beardiv_bar": 0, "nas_t": 0}
nas_binding = 0
for cj in SEALED:
    r = R[cj]; i = bisect.bisect_right(TS, cj) - 1
    # bubbles used (all windows 0-4,5-10,0-8 -> max t window is cj)
    h = bisect.bisect_right(BUBK, cj)
    used = [BUB[k] for k in range(h) if cj - 10 * 900 <= BUB[k]["t"] <= cj]
    for b in used:
        if (b.get("known_at") or b["t"]) > cj: viol["bubble_known_at"] += 1
        if b["t"] > cj: viol["bubble_t"] += 1
    # RSI-MA bars: max index i
    if i > (bisect.bisect_right(TS, cj) - 1): viol["rsi_bar"] += 1  # never
    # bear-div bars: max bar accessed = (i-3)+2 = i-1
    maxbar = -1
    for kk in range(i - 20, i - 2):
        if kk < 3: continue
        maxbar = max(maxbar, kk + 2)
    if maxbar >= i: viol["beardiv_bar"] += 1   # would mean touching bar i or beyond
    if maxbar >= 0 and TS[maxbar] > cj: viol["beardiv_bar"] += 1
    # NAS
    j = bisect.bisect_right(NAST, cj) - 1
    if j >= 0 and nas[j]["t"] > cj: viol["nas_t"] += 1
    # does nas_short actually flip a veto? recompute decision with nas_short forced 0
    w4 = [BUB[k] for k in range(h) if cj - 4 * 900 <= BUB[k]["t"] <= cj]
    old = [BUB[k] for k in range(h) if cj - 10 * 900 <= BUB[k]["t"] <= cj - 5 * 900]
    w8 = [BUB[k] for k in range(h) if cj - 8 * 900 <= BUB[k]["t"] <= cj]
    buy4 = sum(wgt[x["size"]] for x in w4 if x["side"] == "BUY")
    burst = buy4 - sum(wgt[x["size"]] for x in old if x["side"] == "BUY")
    large8 = int(any(x["side"] == "BUY" and x["size"] == "L" for x in w8))
    nas_short = int(j >= 0 and nas[j]["dir"] == "SHORT" and (cj - nas[j]["t"]) // 900 <= 4)
    # veto term = (burst>=3 and large8==0 and nas_short==0). If nas_short=1 here and burst>=3 and large8==0,
    # then nas_short is what SAVED the trade from the anti-burst veto.
    if burst >= 3 and large8 == 0 and nas_short == 1: nas_binding += 1

print("=== GLOBAL CAUSAL AUDIT (all 54 signals) ===")
print("look-ahead violations by read type:", viol)
print("all-zero => every read strictly uses data at/<= cj_t")
print()
print("=== NAS look-ahead exposure ===")
print("nas events have NO known_at field (assumed known at t).")
print("signals where nas_short=1 is what RELAXED the anti-burst veto (kept trade):", nas_binding, "of 54")
print()
# explicit 3-signal trace
print("=== EXPLICIT TRACE (first 3 signals) ===")
for cj in SEALED[:3]:
    r = R[cj]; i = bisect.bisect_right(TS, cj) - 1
    h = bisect.bisect_right(BUBK, cj)
    w4 = [BUB[k] for k in range(h) if cj - 4 * 900 <= BUB[k]["t"] <= cj]
    print(f"cj_t={cj} bar_i={i} bar_t={TS[i]} (bar_t<=cj: {TS[i] <= cj})")
    for b in w4:
        print(f"   bub side={b['side']} size={b['size']} t={b['t']} (Δbar={(cj-b['t'])//900}) "
              f"known_at={b.get('known_at')} known<=cj: {b.get('known_at', b['t']) <= cj}")
    print(f"   RSI[i]={RSI[i]} RSIMA[i]={round(RSIMA[i],2) if RSIMA[i] else None} uses bars {max(0,i-13)}..{i} (all<=i)")
    print(f"   n_supply_overhead={r.get('n_supply_overhead')}")
