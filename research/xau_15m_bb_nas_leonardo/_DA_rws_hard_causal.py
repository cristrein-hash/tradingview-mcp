#!/usr/bin/env python3
"""DA INDEPENDENT — causality recompute + leak probes. READ-ONLY, no writes to results/."""
import json, glob, bisect, collections
from pathlib import Path
HERE = Path(__file__).resolve().parent
U = [json.loads(l) for l in open(HERE / "results" / "lab_g_candidates.jsonl")]
R3 = {json.loads(l)["cj_t"]: json.loads(l) for l in open(HERE / "results" / "r3_target_universe_20260704.jsonl")}
SEALED = {s["cj_t"] for s in json.load(open(HERE / "results" / "rws15m_signals_20260705.json"))}

def fv(r, k, d=0):
    v = r.get(k); return v if isinstance(v, (int, float)) and not isinstance(v, bool) else d

# series
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

# ---- INDEPENDENT causal buy_recent: strictly known_at<=cj AND t within window
def buy_recent_causal(cj, lo, hi):
    out = []
    for i, k in enumerate(BUBK):
        if k > cj: break  # BUBK sorted; nothing beyond is known
        b = BUB[i]
        if cj - hi * 900 <= b["t"] <= cj - lo * 900:
            out.append(b)
    return out

# ---- LEAKY variant: ignore known_at, use only bubble t position (look-ahead)
BUB_T = sorted(BUB, key=lambda x: x["t"]); BUBT = [x["t"] for x in BUB_T]
def buy_recent_leaky(cj, lo, hi):
    h = bisect.bisect_right(BUBT, cj - lo * 900)
    return [BUB_T[i] for i in range(h) if BUB_T[i]["t"] >= cj - hi * 900]

def signals(buy_fn, use_causal_nas=True):
    NB = [r for r in U if r["g_v5h"] != "BEAR" and r["g_knife"] == 0]
    sel = []
    for r in NB:
        cj = r["cj_t"]; i = bisect.bisect_right(TS, cj) - 1
        if i < 40: continue
        w4 = buy_fn(cj, 0, 4); old = buy_fn(cj, 5, 10); w8 = buy_fn(cj, 0, 8)
        buy4 = sum(wgt[x["size"]] for x in w4 if x["side"] == "BUY")
        burst = buy4 - sum(wgt[x["size"]] for x in old if x["side"] == "BUY")
        large8 = int(any(x["side"] == "BUY" and x["size"] == "L" for x in w8))
        rsi_above = int(RSI[i] is not None and RSIMA[i] is not None and RSI[i] > RSIMA[i])
        bd = 0
        for kk in range(i - 20, i - 2):
            if kk < 3: continue
            if H[kk] == max(H[kk - 2:kk + 3]):
                pv = [j for j in range(kk - 12, kk - 2) if H[j] == max(H[max(0, j - 2):j + 3])]
                if pv and RSI[kk] is not None and RSI[pv[-1]] is not None and H[kk] > H[pv[-1]] and RSI[kk] < RSI[pv[-1]]: bd += 1
        j = bisect.bisect_right(NAST, cj) - 1
        nas_short = int(j >= 0 and nas[j]["dir"] == "SHORT" and (cj - nas[j]["t"]) // 900 <= 4)
        ok = buy4 >= 2 and not (rsi_above == 0 and fv(r, "n_supply_overhead", 99) <= 20) \
             and not (burst >= 3 and large8 == 0 and nas_short == 0) and bd < 2
        if ok: sel.append(cj)
    return set(sel)

causal = signals(buy_recent_causal)
leaky = signals(buy_recent_leaky)

def panel(cjs):
    n = len(cjs)
    hit = sum(1 for c in cjs if R3[c]["R3"] >= 3)
    net = sum(R3[c]["net3"] for c in cjs)
    return n, round(100 * hit / n, 1) if n else 0, round(net, 1)

print("=== CAUSAL RECOMPUTE (independent, explicit known_at<=cj) ===")
print("independent causal set N =", len(causal))
print("matches sealed set exactly:", causal == SEALED)
print("only-in-independent:", sorted(causal - SEALED))
print("only-in-sealed:", sorted(SEALED - causal))
print("independent panel (N,hit%,net):", panel(causal))
print("sealed panel:", panel(SEALED))
print()
print("=== LEAK PROBE: buy_recent ignoring known_at (naive t-window) ===")
print("leaky set N =", len(leaky), "| panel:", panel(leaky))
print("added by leak (in leaky not causal):", len(leaky - causal))
print("removed by leak:", len(causal - leaky))
if leaky != causal:
    print(" -> known_at filter CHANGES the signal set; look-ahead protection is load-bearing")
# hit rate of the DELTA trades (the ones look-ahead would add)
delta = leaky - causal
if delta:
    print(" delta-trades panel (what leak would add):", panel(delta))
