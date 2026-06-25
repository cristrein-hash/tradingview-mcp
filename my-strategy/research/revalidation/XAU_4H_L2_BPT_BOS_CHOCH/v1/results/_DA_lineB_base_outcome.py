#!/usr/bin/env python3
"""LINHA B — pergunta BASE: os 123 fundos NOVOS (capit/oversold, BEAR/TRANS, fora dos 276) dão lucro líquido na RÉGUA
OFICIAL (SL = demanda 4H defendida −0.1ATR as-of-bar [Custom OB v11, RAW]; exit let-run, custo 0.35R)? Forward-sim causal
sobre raw_features (OHLC contíguo). Mede n, winners/losers, sumR, runners, por ano. SEM leads sofisticados ainda. Verified 2026-06-25."""
import json, gzip, bisect
from pathlib import Path
import datetime as dt
V1 = Path(__file__).resolve().parents[1]
F = [json.loads(l) for l in open(V1 / "repro_recovery/raw_features_2020_2026.jsonl")]
N = len(F); H = [r["high"] for r in F]; L = [r["low"] for r in F]; C = [r["close"] for r in F]; TS = [int(r["ts_epoch"]) for r in F]
ATR = [None] * N; trs = []
for i in range(1, N):
    trs.append(max(H[i] - L[i], abs(H[i] - C[i - 1]), abs(L[i] - C[i - 1])))
    if i >= 14: ATR[i] = sum(trs[i - 14:i]) / 14
cand = json.load(open(V1 / "results/l2_bpt_lineB_distinct_bottoms.json"))  # 123 bar_idx
SVP = "/Volumes/GUTS_ LACIE/TradingData/raw_replay/XAUUSD/4H/XAUUSD_4H_replay_2019-12_to_2026-current_SVP_LUX_RAW.jsonl.gz"

def to_ep(t):
    t = float(t); return int(t / 1000) if t > 1e11 else int(t)
# RAW gz: zonas Custom OB por asof_t (1 passada)
ob = {}  # asof_t -> list[(high,low)]
with gzip.open(SVP, "rt") as fh:
    for line in fh:
        if "Custom OB" not in line: continue
        rec = json.loads(line); oh = rec.get("ohlcv"); last = oh[-1] if isinstance(oh, list) and oh else None
        if not isinstance(last, dict): continue
        at = to_ep(last.get("time"))
        if at is None or at in ob: continue
        g = next((x for x in (rec.get("pine_boxes") or []) if "Custom OB" in str(x.get("name", ""))), None)
        if not g: continue
        ob[at] = [(z["high"], z["low"]) for z in (g.get("zones") or []) if z.get("high") is not None and z.get("low") is not None]
obt = sorted(ob)
print(f"asof_t com Custom OB = {len(obt)}")

def demand_sl(i):
    et = TS[i]; k = bisect.bisect_right(obt, et) - 1   # as-of: latest <= entry (causal)
    if k < 0: return None
    zones = ob[obt[k]]; entry = C[i]
    below = [(hi, lo) for hi, lo in zones if hi <= entry]
    if not below: return None
    hi, lo = max(below, key=lambda z: z[0])   # demanda mais próxima abaixo
    return lo - 0.1 * ATR[i] if ATR[i] else None

def sim(i, HZ=120):
    if not ATR[i]: return None
    entry = C[i]; sl = demand_sl(i)
    fb = "demand"
    if sl is None or entry - sl <= 0:   # fallback: swing-low 6 barras −0.1ATR
        lo6 = min(L[max(0, i - 5):i + 1]); sl = lo6 - 0.1 * ATR[i]; fb = "swing_fallback"
    risk = entry - sl
    if risk <= 0: return None
    end = min(i + HZ, N - 1)
    stopped = any(L[j] <= sl for j in range(i + 1, end + 1))
    lr = -1.0 if stopped else (C[end] - entry) / risk
    mfe = max(((H[j] - entry) / risk for j in range(i + 1, end + 1)), default=0.0)
    return dict(i=i, net=lr - 0.35, lr=lr, mfe=mfe, risk_atr=risk / ATR[i], fb=fb)

res = [r for i in cand if (r := sim(i))]
n = len(res); W = sum(1 for r in res if r["net"] > 0); run = sum(1 for r in res if r["lr"] >= 5)
sumR = sum(r["net"] for r in res); fbk = sum(1 for r in res if r["fb"] == "swing_fallback")
print(f"\nFUNDOS NOVOS medidos = {n}/{len(cand)} | usaram fallback swing = {fbk}")
print(f"winners = {W} | losers = {n-W} | WR = {100*W/n:.0f}%")
print(f"sumR LÍQUIDO = {sumR:+.1f}R | avgR = {sumR/n:+.2f}R | runners(let-run≥5R) = {run}")
print(f"SL mediano = {sorted(r['risk_atr'] for r in res)[n//2]:.2f} ATR")
import collections
byyr = collections.defaultdict(lambda: [0, 0.0])
for r in res:
    y = dt.datetime.utcfromtimestamp(TS[r["i"]]).year; byyr[y][0] += 1; byyr[y][1] += r["net"]
print("por ano (n, sumR):", {y: (v[0], round(v[1], 1)) for y, v in sorted(byyr.items())})
json.dump(res, open(V1 / "results/l2_bpt_lineB_base_outcome.json", "w"))
print("\nBASE: capit/oversold só. Confirmação (bubbles/v1.6/svp) = próximo, incremental, uma de cada vez.")
