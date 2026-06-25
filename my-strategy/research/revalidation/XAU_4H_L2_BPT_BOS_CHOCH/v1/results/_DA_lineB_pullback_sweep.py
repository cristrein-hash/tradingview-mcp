#!/usr/bin/env python3
"""LINHA B — sweep da PROFUNDIDADE do pullback (K×ATR abaixo da máx-10b), K=1..5, sobre a base BULL. Mesma régua
oficial (SL demanda −0.1ATR, let-run, 0.35R). Reporta TODOS os K (n,WR,sumR,avgR,runners) p/ ver a filtragem. Causal. Verified 2026-06-25."""
import json, gzip, bisect, csv, datetime as dt
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
    k = bisect.bisect_right(rbt, et) - 1; return rb[k].get("raw_state") if k >= 0 else None
OUT276 = set(int(r["bar_idx"]) for r in csv.DictReader(open(V1 / "results/l2_bpt_uncapped_or_proxy_outcomes_276.csv")))
def near276(i): return any(abs(i - b) <= 6 for b in OUT276)
# OB demanda (1 passada)
SVP = "/Volumes/GUTS_ LACIE/TradingData/raw_replay/XAUUSD/4H/XAUUSD_4H_replay_2019-12_to_2026-current_SVP_LUX_RAW.jsonl.gz"
def to_ep(t): t = float(t); return int(t / 1000) if t > 1e11 else int(t)
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
    zs = ob.get(obt[k], []) if k >= 0 else []; below = [(hi, lo) for hi, lo in zs if hi <= entry]
    sl = (max(below, key=lambda z: z[0])[1] - 0.1 * ATR[i]) if below else (min(L[max(0, i - 5):i + 1]) - 0.1 * ATR[i])
    risk = entry - sl
    if risk <= 0: return None
    end = min(i + 120, N - 1); stopped = any(L[j] <= sl for j in range(i + 1, end + 1))
    lr = -1.0 if stopped else (C[end] - entry) / risk
    return lr - 0.35, lr

def run_K(K):
    pool = [i for i in range(30, N) if ATR[i] and C[i] <= max(H[max(0, i - 10):i]) - K * ATR[i] and C[i] < C[i - 3]
            and reg_asof(TS[i]) == "BULL" and not near276(i)]
    pool.sort(); groups = []; cur = []
    for i in pool:
        if cur and i - cur[-1] > 12: groups.append(cur); cur = []
        cur.append(i)
    if cur: groups.append(cur)
    cand = [g[0] for g in groups]
    res = [s for i in cand if (s := sim(i))]
    n = len(res); w = sum(1 for net, _ in res if net > 0); s = sum(net for net, _ in res); run = sum(1 for _, lr in res if lr >= 5)
    return (n, round(100 * w / n) if n else 0, round(s, 1), round(s / n, 2) if n else 0, run)

print("=== SWEEP profundidade pullback (BULL, régua oficial let-run) ===")
print(f"{'K×ATR':>6} | {'n':>3} | {'WR':>4} | {'sumR':>7} | {'avgR':>6} | {'runners':>7}")
for K in (1, 2, 3, 4, 5):
    n, wr, s, a, run = run_K(K)
    print(f"{K:>6} | {n:>3} | {wr:>3}% | {s:>+7} | {a:>+6} | {run:>7}")
print("\nCausal, RAW. Sweep de 1 param (5 valores) — todos reportados.")
