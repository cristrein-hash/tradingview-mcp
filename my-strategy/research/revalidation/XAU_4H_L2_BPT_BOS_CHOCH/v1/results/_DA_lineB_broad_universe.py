#!/usr/bin/env python3
"""LINHA B RECONSTRUÍDO — universo AMPLO sem trava de regime. Candidato = PULLBACK causal (close ≤ máx-10b − 1.0ATR
E caindo) em QUALQUER regime, fora dos 276, dedup causal. Outcome régua oficial (demanda RAW −0.1ATR, let-run, 0.35R).
QUEBRA por REGIME (BULL/TRANSITION/BEAR) p/ ver ONDE os runners se concentram. Causal as-of. Verified 2026-06-25."""
import json, gzip, bisect, datetime as dt
from pathlib import Path
V1 = Path(__file__).resolve().parents[1]
F = [json.loads(l) for l in open(V1 / "repro_recovery/raw_features_2020_2026.jsonl")]
N = len(F); H = [r["high"] for r in F]; L = [r["low"] for r in F]; C = [r["close"] for r in F]; TS = [int(r["ts_epoch"]) for r in F]
ATR = [None] * N; trs = []
for i in range(1, N):
    trs.append(max(H[i] - L[i], abs(H[i] - C[i - 1]), abs(L[i] - C[i - 1])))
    if i >= 14: ATR[i] = sum(trs[i - 14:i]) / 14
REG = V1 / "../../../../strategies/candidates/regime_classifier_v3/regime_B_v3_classifications.jsonl"
def toep(s):
    try: return int(dt.datetime.fromisoformat(str(s).replace("Z", "+00:00")).timestamp())
    except Exception: return int(dt.datetime.strptime(str(s)[:10], "%Y-%m-%d").replace(tzinfo=dt.timezone.utc).timestamp())
rb = [json.loads(l) for l in open(REG) if json.loads(l).get("ts")]
for r in rb: r["_e"] = toep(r["ts"])
rb.sort(key=lambda r: r["_e"]); rbt = [r["_e"] for r in rb]
def reg_asof(et):
    k = bisect.bisect_right(rbt, et) - 1
    return rb[k].get("raw_state") if k >= 0 else None
import csv
OUT276 = set(int(r["bar_idx"]) for r in csv.DictReader(open(V1 / "results/l2_bpt_uncapped_or_proxy_outcomes_276.csv")))
def near276(i): return any(abs(i - b) <= 6 for b in OUT276)

# universo AMPLO: pullback causal em qualquer regime
pool = []
for i in range(30, N):
    if not ATR[i]: continue
    hi10 = max(H[max(0, i - 10):i])
    if C[i] <= hi10 - 1.0 * ATR[i] and C[i] < C[i - 3] and not near276(i):
        pool.append(i)
# dedup 12b, primeira barra
pool.sort(); groups = []; cur = []
for i in pool:
    if cur and i - cur[-1] > 12: groups.append(cur); cur = []
    cur.append(i)
if cur: groups.append(cur)
cand = [g[0] for g in groups]
print(f"universo amplo: {len(pool)} barras → {len(cand)} pullbacks distintos (todos regimes)")

# demanda RAW (1 passada gz)
SVP = "/Volumes/GUTS_ LACIE/TradingData/raw_replay/XAUUSD/4H/XAUUSD_4H_replay_2019-12_to_2026-current_SVP_LUX_RAW.jsonl.gz"
def to_ep(t):
    t = float(t); return int(t / 1000) if t > 1e11 else int(t)
ob = {}
with gzip.open(SVP, "rt") as fh:
    for line in fh:
        if "Custom OB" not in line: continue
        rec = json.loads(line); oh = rec.get("ohlcv"); last = oh[-1] if isinstance(oh, list) and oh else None
        if not isinstance(last, dict): continue
        at = to_ep(last.get("time"))
        if at is None or at in ob: continue
        g = next((x for x in (rec.get("pine_boxes") or []) if "Custom OB" in str(x.get("name", ""))), None)
        if g: ob[at] = [(z["high"], z["low"]) for z in (g.get("zones") or []) if z.get("high") is not None]
obt = sorted(ob)
def sim(i):
    et = TS[i]; entry = C[i]; k = bisect.bisect_right(obt, et) - 1
    zones = ob.get(obt[k], []) if k >= 0 else []
    below = [(hi, lo) for hi, lo in zones if hi <= entry]
    if below: sl = max(below, key=lambda z: z[0])[1] - 0.1 * ATR[i]
    else: sl = min(L[max(0, i - 5):i + 1]) - 0.1 * ATR[i]
    risk = entry - sl
    if risk <= 0: return None
    end = min(i + 120, N - 1)
    stopped = any(L[j] <= sl for j in range(i + 1, end + 1))
    lr = -1.0 if stopped else (C[end] - entry) / risk
    return dict(i=i, net=lr - 0.35, lr=lr, reg=reg_asof(et))

res = [r for i in cand if (r := sim(i))]
def stats(g, lab):
    if not g: print(f"  {lab}: vazio"); return
    w = sum(1 for r in g if r["net"] > 0); s = sum(r["net"] for r in g); run = sum(1 for r in g if r["lr"] >= 5)
    print(f"  {lab:>14}: n={len(g):>3} WR={100*w/len(g):>3.0f}% sumR={s:>+7.1f} avgR={s/len(g):>+6.2f} runners={run}")
print(f"\nfundos medidos = {len(res)}")
stats(res, "TODOS")
print("=== POR REGIME (onde os runners moram?) ===")
for rg in ("BULL", "TRANSITION", "BEAR"):
    stats([r for r in res if r["reg"] == rg], rg)
byyr = {}
for r in res: byyr.setdefault(dt.datetime.utcfromtimestamp(TS[r["i"]]).year, [0, 0.0]); byyr[dt.datetime.utcfromtimestamp(TS[r["i"]]).year][0] += 1; byyr[dt.datetime.utcfromtimestamp(TS[r["i"]]).year][1] += r["net"]
print("por ano (n,sumR):", {y: (v[0], round(v[1], 1)) for y, v in sorted(byyr.items())})
json.dump(res, open(V1 / "results/l2_bpt_lineB_broad.json", "w"))
print("\nCalibração 276. Causal. Achar o REGIME/subset onde fundos correm net+, depois multi-fatorial lá.")
