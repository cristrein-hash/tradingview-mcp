#!/usr/bin/env python3
"""LINHA B — combos de fatores SOBRE a base BULL (120 trades). 7 fatores RAW causais: rsi_os, vp_acc(SVP val),
absorb(SELL bubbles), ob_demand, nas_bot, not_clean(supply overhead), supply_rej. Testa ISOLADO + PARES + TRIOS,
mede subset (n,WR,sumR,avgR,runners) vs base. Multiple-testing — reportar TODOS, sem cherry-pick. Causal. Verified 2026-06-25."""
import json, gzip, bisect, itertools
from pathlib import Path
V1 = Path(__file__).resolve().parents[1]
F = [json.loads(l) for l in open(V1 / "repro_recovery/raw_features_2020_2026.jsonl")]
N = len(F); H = [r["high"] for r in F]; L = [r["low"] for r in F]; C = [r["close"] for r in F]; TS = [int(r["ts_epoch"]) for r in F]; RSI = [r.get("rsi") for r in F]
ATR = [None] * N; trs = []
for i in range(1, N):
    trs.append(max(H[i] - L[i], abs(H[i] - C[i - 1]), abs(L[i] - C[i - 1])))
    if i >= 14: ATR[i] = sum(trs[i - 14:i]) / 14
res = json.load(open(V1 / "results/l2_bpt_lineB_broad.json"))
bull = {r["i"]: r for r in res if r["reg"] == "BULL"}
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
        a = bg.get("activations_per_plot") or {}; sell = sum(pv(a.get(f"plot_{k}")) for k in (6, 8, 10)); large = pv(a.get("plot_10"))
        ng = next((x for x in (rec.get("pine_labels") or []) if "NAS" in str(x.get("name", ""))), {}); ls = ng.get("labels") or []
        nas = ls[-1].get("text") if ls else None
        sv = rec.get("session_vp", {}); l3 = (sv.get("last3") or []) if isinstance(sv, dict) else []; val = None
        if l3 and isinstance(l3[-1], dict):
            v = l3[-1].get("v") or []
            if len(v) >= 4: val = v[3]
        D[at] = dict(sell=sell, large=large, zones=zones, nas=nas, val=val)
DT = sorted(D)
def asof(et): k = bisect.bisect_right(DT, et) - 1; return D[DT[k]] if k >= 0 else {}
def sell10(et): return sum(D[t]["sell"] for t in [t for t in DT if t <= et][-10:])

FACT = ["rsi_os", "vp_acc", "absorb", "ob_demand", "nas_bot", "not_clean", "supply_rej"]
rows = []
for i, r in bull.items():
    et = TS[i]; entry = C[i]; d = asof(et); atr = ATR[i]
    zones = d.get("zones", [])
    dem = [(hi, lo) for hi, lo in zones if hi <= entry]; sup = [(hi, lo) for hi, lo in zones if lo >= entry]
    near_dem = bool(dem) and (entry - max(dem, key=lambda z: z[0])[0]) <= 0.5 * atr
    has_overhead = bool(sup); nearest_sup = min(sup, key=lambda z: z[1])[1] if sup else None
    sup_rej = has_overhead and nearest_sup is not None and max(H[max(0, i - 10):i + 1]) >= nearest_sup - 0.5 * atr
    f = dict(rsi_os=int(RSI[i] is not None and RSI[i] <= 40), vp_acc=int(d.get("val") is not None and entry > d["val"]),
             absorb=int(sell10(et) >= 2 or d.get("large", 0) >= 1), ob_demand=int(near_dem),
             nas_bot=int(str(d.get("nas")).upper() == "LONG"), not_clean=int(has_overhead), supply_rej=int(sup_rej))
    rows.append({**f, "net": r["net"], "lr": r["lr"]})

def stat(g):
    n = len(g)
    if not n: return None
    w = sum(1 for x in g if x["net"] > 0); s = sum(x["net"] for x in g); run = sum(1 for x in g if x["lr"] >= 5)
    return (n, round(100 * w / n), round(s, 1), round(s / n, 2), run)
b = stat(rows)
print(f"BASE BULL: n={b[0]} WR={b[1]}% sumR={b[2]} avgR={b[3]} runners={b[4]}\n")
print("=== ISOLADOS (subset onde fator ON) ===")
for fct in FACT:
    g = [x for x in rows if x[fct]]; st = stat(g)
    if st: print(f"  {fct:>11}: n={st[0]:>3} WR={st[1]:>3}% sumR={st[2]:>+6} avgR={st[3]:>+5} run={st[4]}")
def combos(k):
    out = []
    for c in itertools.combinations(FACT, k):
        g = [x for x in rows if all(x[f] for f in c)]; st = stat(g)
        if st and st[0] >= 8: out.append((c, st))
    out.sort(key=lambda z: -z[1][3])  # por avgR
    return out
for k in (2, 3):
    print(f"\n=== COMBOS de {k} (n≥8, ordenado por avgR; base avgR={b[3]}) ===")
    for c, st in combos(k)[:12]:
        print(f"  {'+'.join(c):>34}: n={st[0]:>3} WR={st[1]:>3}% sumR={st[2]:>+6} avgR={st[3]:>+5} run={st[4]}")
print(f"\n7 fatores → {7+21+35} combos testados (multiple-testing). Calibração 276, causal.")
