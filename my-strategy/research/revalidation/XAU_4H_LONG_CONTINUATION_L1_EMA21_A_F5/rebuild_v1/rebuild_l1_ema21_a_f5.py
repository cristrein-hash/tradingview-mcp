#!/usr/bin/env python3
"""RECONSTRUÇÃO (não validação) da L1 EMA21_A + F5 a partir do RAW 4H + regime_B_v3 + Custom OB v11.
Restaura fonte perdida. NÃO toca produção, NÃO chama MCP/chart, escreve só em rebuild_v1/.
Fontes: RAW 4H gz (ohlcv+pine_boxes), regime_B_v3_classifications.jsonl. SLIM proibido.
Convenção causal: gates usam dados de bars FECHADOS <= entry; indicadores que repintam (OB) via SHIFT1 (snapshot i-1).
"""
import gzip, json, bisect, statistics
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[4]  # .../tradingview-mcp
RAW = "/Volumes/GUTS_ LACIE/TradingData/raw_replay/XAUUSD/4H/XAUUSD_4H_replay_2019-12_to_2026-current_SVP_LUX_RAW.jsonl.gz"
REGIME = REPO / "my-strategy/strategies/candidates/regime_classifier_v3/regime_B_v3_classifications.jsonl"
CFG = json.load(open(HERE / "config.json"))

P_START = int(datetime(2020, 1, 1, tzinfo=timezone.utc).timestamp())
P_END = int(datetime(2025, 12, 31, 23, 59, tzinfo=timezone.utc).timestamp())
ATR_MIN, ATR_MAX = 0.004, 0.030
BODY_MIN, F5_MAX, RET5_MIN = 0.35, 1.0, -0.04
OB_TOL, MA_TOL = 0.001, 0.002
R_FLOOR_ATR, R_CEIL_ATR = 0.3, 1.5
TARGET_R, TIME_STOP, SLIP = 20.0, 60, 0.1
# V_stair_A: (mfe_threshold_R, lock_R)
STAIR = [(2.0, 0.0), (5.0, 1.0), (8.0, 3.0), (12.0, 6.0), (16.0, 10.0)]

# ---- 1. RAW: bar_time -> ohlcv ; bar_time -> OB zones (snapshot onde o bar é o corrente) ----
bars = {}          # t -> dict(o,h,l,c,v)
zones_at = {}      # t -> list[(high,low)]  (zonas conhecidas nesse bar)
with gzip.open(RAW, "rt") as f:
    for line in f:
        if '"replay_current_date"' not in line:
            continue
        r = json.loads(line)
        ov = r.get("ohlcv") or []
        if not ov:
            continue
        for b in ov:
            if b.get("time") is not None and b.get("close") is not None:
                bars[b["time"]] = {"o": b["open"], "h": b["high"], "l": b["low"], "c": b["close"], "v": b.get("volume") or 0}
        cur = max(b["time"] for b in ov)
        zs = []
        for s in (r.get("pine_boxes") or []):
            if "Custom OB" in s.get("name", ""):
                for z in (s.get("zones") or []):
                    if z.get("high") is not None and z.get("low") is not None:
                        zs.append((z["high"], z["low"]))
        if zs:
            zones_at[cur] = zs

T = sorted(bars)
idx = {t: i for i, t in enumerate(T)}
N = len(T)
O = [bars[t]["o"] for t in T]; H = [bars[t]["h"] for t in T]
L = [bars[t]["l"] for t in T]; C = [bars[t]["c"] for t in T]; V = [bars[t]["v"] for t in T]

# ---- 2. indicadores causais ----
def ema(series, span):
    k = 2 / (span + 1); out = [None] * len(series); e = series[0]
    for i, x in enumerate(series):
        e = x if i == 0 else x * k + e * (1 - k); out[i] = e
    return out
def sma(series, n):
    out = [None] * len(series); s = 0.0
    from collections import deque
    dq = deque()
    for i, x in enumerate(series):
        dq.append(x); s += x
        if len(dq) > n: s -= dq.popleft()
        if len(dq) == n: out[i] = s / n
    return out
EMA21 = ema(C, 21); SMA50 = sma(C, 50)
TR = [H[0] - L[0]] + [max(H[i] - L[i], abs(H[i] - C[i-1]), abs(L[i] - C[i-1])) for i in range(1, N)]
ATR14 = [None] * N
if N >= 14:
    a = sum(TR[:14]) / 14; ATR14[13] = a
    for i in range(14, N):
        a = (a * 13 + TR[i]) / 14; ATR14[i] = a

# ---- 3. regime D-1 SHIFT1 ----
reg = []
for l in open(REGIME):
    r = json.loads(l)
    ts = r.get("ts")
    try: t = int(datetime.fromisoformat(ts.replace("Z", "+00:00")).timestamp())
    except: t = int(datetime.strptime(ts[:10], "%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp())
    reg.append((t, r.get("v3_state")))
reg.sort(); RT = [t for t, _ in reg]
def regime_d1(entry_t):
    i = bisect.bisect_left(RT, entry_t) - 1
    while i > 0 and RT[i] >= entry_t: i -= 1
    return reg[i][1] if i >= 0 else None

# ---- 4. zonas SHIFT1: demand zone (high < close[i-1]) mais próxima abaixo ----
def demand_zone(i):
    t_prev = T[i-1]
    zs = zones_at.get(t_prev)
    if not zs:  # procurar último snapshot com zonas <= i-1
        j = i-1
        while j >= 0 and T[j] not in zones_at: j -= 1
        zs = zones_at.get(T[j]) if j >= 0 else None
    if not zs: return None
    cprev = C[i-1]
    below = [(hi, lo) for hi, lo in zs if hi < cprev_safe(cprev)]
    if not below: return None
    hi, lo = max(below, key=lambda z: z[0])  # mais alta abaixo do preço
    return hi, lo
def cprev_safe(x): return x

# ---- 5. exit V_stair_A forward ----
def simulate_exit(i_entry, entry, stop0):
    Runit = entry - stop0
    if Runit <= 0: return None
    stop = stop0; mfe_R = 0.0; locked = 0.0
    last = min(i_entry + TIME_STOP, N - 1)
    for j in range(i_entry + 1, last + 1):
        fav = (H[j] - entry) / Runit
        if fav > mfe_R: mfe_R = fav
        for thr, lk in STAIR:
            if mfe_R >= thr and lk >= locked:
                locked = lk; stop = entry + locked * Runit
        # conservador: stop antes do target no mesmo bar
        if L[j] <= stop:
            raw = (stop - entry) / Runit
            return raw - SLIP, mfe_R, T[j], "stop/lock"
        if H[j] >= entry + TARGET_R * Runit:
            return TARGET_R - SLIP, mfe_R, T[j], "target"
    rawc = (C[last] - entry) / Runit
    return rawc - SLIP, mfe_R, T[last], "time"

# ---- 6. loop principal ----
trades = []
busy_until = -1
for i in range(60, N):
    t = T[i]
    if t < P_START or t > P_END: continue
    if i <= busy_until: continue
    if None in (EMA21[i-1], SMA50[i-1], ATR14[i-1], SMA50[i-7] if i-7 >= 0 else None): continue
    # gates close-only-causal (i-1) + confirm (i)
    if regime_d1(t) != "BULL": continue
    if not (C[i-1] > EMA21[i-1] and C[i-1] > SMA50[i-1]): continue
    if not (EMA21[i-1] > EMA21[i-4]): continue
    if not (SMA50[i-1] > SMA50[i-7]): continue
    hh20 = max(H[i-21:i-1]) if i-21 >= 0 else max(H[max(0,i-21):i-1])
    if not (hh20 > max(C[max(0,i-21):i-1])): continue
    atrr = ATR14[i-1] / C[i-1]
    if not (ATR_MIN <= atrr <= ATR_MAX): continue
    # zona
    dz = demand_zone(i); src = "OB_v11"
    if dz is None:
        zhi = zlo = EMA21[i-1]; src = "EMA21_proxy"; tol = MA_TOL
    else:
        zhi, zlo = dz; tol = OB_TOL
    touched = (L[i] <= zhi*(1+tol) and L[i] >= zlo*(1-tol)) or (L[i-1] <= zhi*(1+tol) and L[i-1] >= zlo*(1-tol)) or (L[i] < zlo and C[i] > zhi)
    if not touched: continue
    if not (C[i] > zhi): continue
    rng = H[i]-L[i]
    if rng <= 0 or (C[i]-O[i])/rng < BODY_MIN: continue
    if not (C[i] > C[i-1]): continue
    if i-5 < 0 or (C[i]/C[i-5]-1) <= RET5_MIN: continue
    # F5
    vmed = statistics.median(V[i-50:i]) if i-50 >= 0 else None
    if not vmed or vmed <= 0: continue
    if (V[i]/vmed) > F5_MAX: continue
    # stop estrutural
    zlow = zlo
    sl = min(L[i], min(L[max(0,i-4):i+1]), zlow) - 0.1*ATR14[i-1]
    entry = C[i]; Runit = entry - sl
    if Runit <= 0: continue
    if Runit < R_FLOOR_ATR*ATR14[i-1]: sl = entry - R_FLOOR_ATR*ATR14[i-1]; Runit = entry - sl
    if Runit > R_CEIL_ATR*ATR14[i-1]: continue  # abort
    res = simulate_exit(i, entry, sl)
    if res is None: continue
    R, mfe, t_exit, reason = res
    trades.append({"ts": datetime.utcfromtimestamp(t).isoformat(), "entry_time": t, "entry": round(entry,2),
                   "stop": round(sl,2), "Runit": round(Runit,2), "zone_source": src,
                   "vol_ratio": round(V[i]/vmed,3), "R": round(R,2), "MFE_R": round(mfe,2),
                   "exit_reason": reason, "exit_ts": datetime.utcfromtimestamp(t_exit).isoformat()})
    busy_until = idx[t_exit]

# ---- 7. outputs ----
with open(HERE/"trades.jsonl","w") as f:
    for tr in trades: f.write(json.dumps(tr)+"\n")
Rs = [tr["R"] for tr in trades]; n = len(Rs)
wins = [r for r in Rs if r > 0]
sumR = round(sum(Rs),2); wr = round(100*len(wins)/n,1) if n else 0
peak=eq=dd=0
for r in Rs:
    eq+=r; peak=max(peak,eq); dd=max(dd,peak-eq)
mls=cls=0
for r in Rs:
    cls = cls+1 if r<=0 else 0; mls=max(mls,cls)
big15 = sum(1 for r in Rs if r>=15); big10=sum(1 for r in Rs if r>=10); big5=sum(1 for r in Rs if r>=5)
old_n, old_sumR, old_wr = 16, 31.74, 43.8
def near(a,b,tol): return abs(a-b)<=tol
if n==0: rec="MISMATCH"
elif near(n,old_n,2) and near(sumR,old_sumR,8) and near(wr,old_wr,8): rec="PARTIAL_MATCH"
elif near(n,old_n,4): rec="PARTIAL_MATCH"
else: rec="MISMATCH"
rec_note="CANNOT_RECONCILE_NO_ORIGINAL_TRADES (sem lista original; comparação só agregada)"
summary={"strategy_id": CFG["strategy_id"], "NOT_VALIDATION": True,
  "n": n, "date_range": [trades[0]["ts"][:10] if n else None, trades[-1]["ts"][:10] if n else None],
  "sumR": sumR, "WR": wr, "avgR": round(sumR/n,2) if n else 0, "maxDD_R": round(dd,1),
  "max_losing_streak": mls, "big15W": big15, "big10W": big10, "big5W": big5,
  "expected_old_n": old_n, "expected_old_sumR": old_sumR, "expected_old_WR": old_wr,
  "reconciliation_status": rec, "reconciliation_note": rec_note,
  "warning": "NOT_VALIDATION — reconstrução da fonte, não prova de edge",
  "assumptions": CFG["NOTES_UNKNOWN"]}
json.dump(summary, open(HERE/"summary.json","w"), indent=2)
print(json.dumps(summary, indent=2, ensure_ascii=False))
print(f"\ntrades.jsonl: {n} trades | RAW bars usados: {N} ({datetime.utcfromtimestamp(T[0]).date()}->{datetime.utcfromtimestamp(T[-1]).date()})")
