"""DA probe for proposed feature WEEKDAY_TIME_REGIME_BLACKOUT.
Question: is a (dow x hour-bucket) calendar blackout causally feasible AND non-fitting on this 791-candidate substrate?
Checks:
 1. cell sample sizes for joint (dow x killzone) — can any cell be classified robustly?
 2. WR by hour and by dow marginals (is there real structure or noise?)
 3. how much of the right-tail (runners mfe>=3R) lives outside the 'dead' pre-registered cells?
Outcome via eval_engine.outcome() on candidates_annotated.csv (same ruler).
Verified 2026-06-26. Reproducible, saved per output-orphan guard.
"""
import csv, collections, statistics as st, json, datetime as dt
import importlib.util, os

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("eval_engine", os.path.join(HERE, "eval_engine.py"))
# eval_engine prints on import; we only need outcome(). Load primitives the same way it does.
PRIM = {}
for f in os.listdir(os.path.join(HERE, "primitives")):
    if f.endswith(".json"):
        d = json.load(open(os.path.join(HERE, "primitives", f)))
        key = f.split(".")[0].replace("XAUUSD_15m_replay_", "")
        PRIM[key] = d
SER = {b: pr["series"] for b, pr in PRIM.items()}
TID = {b: {x["t"]: i for i, x in enumerate(s)} for b, s in SER.items()}
K, HMAX, RUNNER_R = 2, 480, 3.0
MIN_RISK_ATR, R_CAP = 0.5, 15.0

def conf_swed_low(s, i):
    for j in range(i - K, K - 1, -1):
        w = s[j - K:j + K + 1]
        if len(w) == 2 * K + 1 and s[j]["l"] == min(x["l"] for x in w): return s[j]["l"]
    return None
def conf_swed_high(s, i):
    for j in range(i - K, K - 1, -1):
        w = s[j - K:j + K + 1]
        if len(w) == 2 * K + 1 and s[j]["h"] == max(x["h"] for x in w): return s[j]["h"]
    return None

def outcome(r):
    b = r["block"]; s = SER.get(b); tid = TID.get(b)
    if s is None: return None
    et = int(r["entry_t"]); i = tid.get(et)
    if i is None or i + 1 >= len(s): return None
    long = r["dir"] == "LONG"
    entry = float(r["entry_close"]); atr = s[i].get("atr") or 0
    if not atr: return None
    if long:
        sl = conf_swed_low(s, i); struct_risk = (entry - sl) if sl else MIN_RISK_ATR * atr
    else:
        sl = conf_swed_high(s, i); struct_risk = (sl - entry) if sl else MIN_RISK_ATR * atr
    risk = max(struct_risk, MIN_RISK_ATR * atr)
    trail = (entry - risk) if long else (entry + risk); reached = False; mfe = mae = 0.0; exit_px = None; bars = 0
    for k in range(i + 1, min(i + 1 + HMAX, len(s))):
        bar = s[k]; bars += 1
        if long:
            mfe = max(mfe, (bar["h"] - entry) / risk); mae = min(mae, (bar["l"] - entry) / risk)
            if bar["l"] <= trail: exit_px = trail; break
            if (bar["h"] - entry) / risk >= 1.0: reached = True
            if reached:
                nl = conf_swed_low(s, k)
                if nl and nl > trail: trail = nl
        else:
            mfe = max(mfe, (entry - bar["l"]) / risk); mae = min(mae, (entry - bar["h"]) / risk)
            if bar["h"] >= trail: exit_px = trail; break
            if (entry - bar["l"]) / risk >= 1.0: reached = True
            if reached:
                nh = conf_swed_high(s, k)
                if nh and nh < trail: trail = nh
    if exit_px is None: exit_px = s[min(i + HMAX, len(s) - 1)]["c"]
    R = ((exit_px - entry) if long else (entry - exit_px)) / risk
    return {"R": R, "win": R > 0, "runner": mfe >= RUNNER_R}

rows = list(csv.DictReader(open(os.path.join(HERE, "candidates_annotated.csv"))))
# attach outcome
recs = []
for r in rows:
    o = outcome(r)
    if o is None: continue
    h = int(float(r["hour_utc"])); d = int(float(r["dow"]))
    # killzone bucket (UTC): asia<6, london 6-12, ny 12-16, ny-pm 16-20, drift>=20
    kz = ("asia" if h < 6 else "london" if h < 12 else "ny" if h < 16 else "nypm" if h < 20 else "drift")
    recs.append({**o, "h": h, "d": d, "kz": kz})

n = len(recs)
print(f"evaluated outcomes: {n}")
W = sum(r["win"] for r in recs); RUN = sum(r["runner"] for r in recs)
print(f"baseline WR={100*W/n:.0f}%  runners={RUN} ({100*RUN/n:.0f}%)")

# 1. joint (dow x kz) cell sizes
cell = collections.defaultdict(list)
for r in recs: cell[(r["d"], r["kz"])].append(r)
print("\n=== joint (dow x killzone) cells: count, WR, runners ===")
small = 0
for key in sorted(cell):
    g = cell[key]; w = sum(x["win"] for x in g); ru = sum(x["runner"] for x in g)
    tag = " <SMALL" if len(g) < 15 else ""
    if len(g) < 15: small += 1
    print(f"  dow{key[0]} {key[1]:6s} n={len(g):3d} WR={100*w/len(g):3.0f}% run={ru}{tag}")
print(f"\ncells total={len(cell)}  cells with n<15 (untrainable)={small}")

# 2. marginals
print("\n=== WR by killzone (marginal) ===")
for kz in ["asia","london","ny","nypm","drift"]:
    g = [r for r in recs if r["kz"]==kz]
    if g: print(f"  {kz:6s} n={len(g):3d} WR={100*sum(x['win'] for x in g)/len(g):3.0f}% run={sum(x['runner'] for x in g)}")
print("=== WR by dow (marginal) ===")
for d in range(7):
    g = [r for r in recs if r["d"]==d]
    if g: print(f"  dow{d} n={len(g):3d} WR={100*sum(x['win'] for x in g)/len(g):3.0f}% run={sum(x['runner'] for x in g)}")

# 3. right-tail location vs pre-registered dead cells (Mon-asia, Fri-drift, ny-lunch)
DEAD = lambda r: (r["d"]==0 and r["kz"]=="asia") or (r["d"]==4 and r["kz"]=="drift") or (11<=r["h"]<13)
dead = [r for r in recs if DEAD(r)]; live = [r for r in recs if not DEAD(r)]
rd = sum(r["runner"] for r in dead); rl = sum(r["runner"] for r in live)
print(f"\n=== pre-registered DEAD cells (Mon-asia, Fri-drift, lunch11-13) ===")
print(f"  dead: n={len(dead)} WR={100*sum(r['win'] for r in dead)/max(1,len(dead)):.0f}% runners={rd}")
print(f"  live: n={len(live)} WR={100*sum(r['win'] for r in live)/len(live):.0f}% runners={rl}")
print(f"  right-tail removed by blackout: {rd}/{RUN} runners")
