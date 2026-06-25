#!/usr/bin/env python3
"""Sweep de profundidade de pullback (K×ATR, K=1..5) APENAS nos 55 trades not_clean distintos (BULL, supply acima,
NÃO interpolam absorb). Outcome da régua oficial (já em broad.json: net/lr com SL demanda + let-run). Causal. Verified 2026-06-25."""
import json, gzip, bisect
from pathlib import Path
V1 = Path(__file__).resolve().parents[1]
F = [json.loads(l) for l in open(V1 / "repro_recovery/raw_features_2020_2026.jsonl")]
N = len(F); H = [r["high"] for r in F]; L = [r["low"] for r in F]; C = [r["close"] for r in F]; TS = [int(r["ts_epoch"]) for r in F]
ATR = [None] * N; trs = []
for i in range(1, N):
    trs.append(max(H[i] - L[i], abs(H[i] - C[i - 1]), abs(L[i] - C[i - 1])))
    if i >= 14: ATR[i] = sum(trs[i - 14:i]) / 14
bull = {r["i"]: r for r in json.load(open(V1 / "results/l2_bpt_lineB_broad.json")) if r["reg"] == "BULL"}
SVP = "/Volumes/GUTS_ LACIE/TradingData/raw_replay/XAUUSD/4H/XAUUSD_4H_replay_2019-12_to_2026-current_SVP_LUX_RAW.jsonl.gz"
def to_ep(t): t = float(t); return int(t / 1000) if t > 1e11 else int(t)
def pv(s):
    if s is None: return 0
    s = str(s).replace(" ", "").replace(",", "").strip(); m = 1.0
    if s[-1:] in ("K", "M", "B"): m = {"K": 1e3, "M": 1e6, "B": 1e9}[s[-1]]; s = s[:-1]
    try: return float(s) * m
    except Exception: return 0
D = {}
with gzip.open(SVP, "rt") as fh:
    for line in fh:
        if '"ohlcv"' not in line: continue
        rec = json.loads(line); oh = rec.get("ohlcv"); last = oh[-1] if isinstance(oh, list) and oh else None
        if not isinstance(last, dict): continue
        at = to_ep(last.get("time"))
        if at is None or at in D: continue
        g = next((x for x in (rec.get("pine_boxes") or []) if "Custom OB" in str(x.get("name", ""))), {})
        zones = [(z["high"], z["low"]) for z in (g.get("zones") or []) if z.get("high") is not None]
        bg = next((x for x in (rec.get("pine_shapes_bubbles") or []) if "Bubble" in str(x.get("name", ""))), {})
        a = bg.get("activations_per_plot") or {}
        D[at] = dict(zones=zones, sell=sum(pv(a.get(f"plot_{k}")) for k in (6, 8, 10)), large=pv(a.get("plot_10")))
DT = sorted(D)
def asof(et): k = bisect.bisect_right(DT, et) - 1; return D[DT[k]] if k >= 0 else {}
def sell10(et): return sum(D[t]["sell"] for t in [t for t in DT if t <= et][-10:])
absorb = set(i for i in bull if (sell10(TS[i]) >= 2 or asof(TS[i]).get("large", 0) >= 1))
new55 = [i for i in bull if any(lo >= C[i] for hi, lo in asof(TS[i]).get("zones", [])) and i not in absorb]
print(f"trades not_clean distintos (55) = {len(new55)}")
# profundidade por trade
depth = {i: (max(H[max(0, i - 10):i]) - C[i]) / ATR[i] for i in new55}
print("\n=== SWEEP profundidade K×ATR nos 55 (régua oficial let-run) ===")
print(f"{'K':>3} | {'n':>3} | {'WR':>4} | {'sumR':>7} | {'avgR':>6} | {'runners':>7}")
for K in (1, 2, 3, 4, 5):
    g = [i for i in new55 if depth[i] >= K]
    if not g: print(f"{K:>3} | {'0':>3} | (vazio)"); continue
    nets = [bull[i]["net"] for i in g]; lrs = [bull[i]["lr"] for i in g]
    w = sum(1 for x in nets if x > 0); s = sum(nets); run = sum(1 for x in lrs if x >= 5)
    print(f"{K:>3} | {len(g):>3} | {100*w/len(g):>3.0f}% | {s:>+7.1f} | {s/len(g):>+6.2f} | {run:>7}")
print("\nCausal, RAW. Subset dos 55 not_clean; profundidade por trade.")
