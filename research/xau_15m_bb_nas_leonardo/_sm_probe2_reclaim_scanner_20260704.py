#!/usr/bin/env python3
"""SM probe 2 — SCANNER outcome-blind do entry 'HL-RECLAIM' (designer estrutura-momentum).

ENTRY INDEPENDENTE, gatilho em nivel de barra 15M. NAO le nenhum outcome
(g_R, letrun, plan_outcome ficam intocados). Metricas permitidas: frequencia/semana,
cobertura dos 35 t0 (±6 barras), geometria do SL, dedup stats, contagem por ano.

Esqueleto (todas as lentes causais no close da barra i):
  S1 HIGHER_LOW  : >=2 swing lows (fractal ±2) na janela 96, ultimo > penultimo
  S2 CHOCH_REC24 : ultimo evento SMC 'CHoCH' <= 24 barras atras
  S3 RETRACE     : 0.30 <= (hi96-close)/(hi96-lo96) <= 0.70
  S4 PACIENCIA   : pullback_age (barras desde o high da janela 96) >= P
  S5 QUIET30     : media dos ultimos 4 TR de 30M (resample causal 2x15M) / ATR30 <= 1.0
  T  RECLAIM     : close >= ema21 + BUF*atr  E  close[i-1] < ema21[i-1] + BUF*atr (borda)
                   E  min(close-ema21) < 0 em [i-LB, i-1] (esteve abaixo ha pouco)
  SL             : low do swing do higher-low - 0.1*ATR; se dist < 1.0 ATR -> low da perna
                   de queda (min low desde o high96) - 0.1*ATR
  DEDUP          : cooldown 24 barras apos sinal (borda do reclaim ja evita re-fire trivial)

LOOK LEDGER: cada linha da grade = 1 look de frequencia/cobertura (outcome-blind).
"""
import json, bisect, glob, datetime as dt
from pathlib import Path

HERE = Path(__file__).resolve().parent

# ---------- load merged 15M series + smc events (all 9 blocks, dedup by t) ----------
series, smc = {}, {}
for p in sorted(glob.glob(str(HERE / "primitives" / "*.primitives.json"))):
    d = json.load(open(p))
    for b in d["series"]:
        series.setdefault(b["t"], b)
    for e in d["smc_events"]:
        if "CHOCH" in str(e.get("text", "")).upper():
            smc.setdefault((e["t"], e.get("id")), e)
S = sorted(series.values(), key=lambda b: b["t"])
TS = [b["t"] for b in S]
CH_TS = sorted(e["t"] for e in smc.values())
print(f"merged 15M: {len(S)} bars  {dt.datetime.utcfromtimestamp(TS[0])} -> {dt.datetime.utcfromtimestamp(TS[-1])}")
print(f"CHoCH events: {len(CH_TS)}")

# ---------- causal 30M resample for QUIET lens ----------
# 30M bar boundary: floor(t/1800). A 30M bar is complete at the close of its last 15M bar.
b30 = {}
for b in S:
    key = b["t"] // 1800
    r = b30.setdefault(key, {"h": b["h"], "l": b["l"], "t_close": b["t"]})
    r["h"] = max(r["h"], b["h"]); r["l"] = min(r["l"], b["l"])
    r["t_close"] = max(r["t_close"], b["t"])
B30 = sorted(b30.values(), key=lambda r: r["t_close"])
B30_CLOSE = [r["t_close"] for r in B30]
TR30 = [r["h"] - r["l"] for r in B30]
ATR30 = []
a = None
for i, tr in enumerate(TR30):
    a = tr if a is None else (a * 13 + tr) / 14.0   # RMA14
    ATR30.append(a)

def quiet30_at(t0):
    """mean of last 4 COMPLETED 30M TRs / ATR30, causal at 15M close t0."""
    j = bisect.bisect_right(B30_CLOSE, t0) - 1
    if j < 20: return None
    return sum(TR30[j - 3:j + 1]) / 4.0 / max(1e-9, ATR30[j])

# ---------- 35 manual t0s ----------
AN = json.load(open(HERE / "results" / "cris_trades_analysis_20260704.json"))
T35 = sorted(r["t"] for r in AN)

# ---------- per-bar state features (causal) ----------
W = 96
def state_at(i):
    b = S[i]; c = b["c"]; atr = b["atr"] or 1.0
    win = S[i - W:i + 1]
    lows = [x["l"] for x in win]; highs = [x["h"] for x in win]
    hi96 = max(highs); lo96 = min(lows)
    jh = max(range(len(win)), key=lambda k: win[k]["h"])
    pullback_age = len(win) - 1 - jh
    retrace = (hi96 - c) / ((hi96 - lo96) or atr)
    swl = [k for k in range(2, len(lows) - 2) if lows[k] == min(lows[k - 2:k + 3])]
    higher_low = len(swl) >= 2 and lows[swl[-1]] > lows[swl[-2]]
    hl_low = lows[swl[-1]] if swl else None
    dipleg_low = min(lows[jh:])  # low of the down-leg since the window high
    jc = bisect.bisect_right(CH_TS, b["t"]) - 1
    choch_age = (b["t"] - CH_TS[jc]) // 900 if jc >= 0 else 10**9
    return dict(c=c, atr=atr, retrace=retrace, pullback_age=pullback_age,
                higher_low=higher_low, hl_low=hl_low, dipleg_low=dipleg_low,
                choch_age=choch_age)

# ---------- scanner ----------
def scan(P_AGE, BUF, LB=8, COOLDOWN=24, QUIET_MAX=1.0, RET_LO=0.30, RET_HI=0.70, CH_WIN=24):
    sigs = []
    last_sig = -10**9
    for i in range(W + 2, len(S)):
        b = S[i]; pb = S[i - 1]
        e21, atr = b.get("ema21"), b["atr"] or 1.0
        if e21 is None or pb.get("ema21") is None: continue
        # T: reclaim edge
        buf_abs = BUF * atr
        if not (b["c"] >= e21 + buf_abs): continue
        if not (pb["c"] < pb["ema21"] + BUF * (pb["atr"] or atr)): continue
        if not any(S[k]["c"] < S[k]["ema21"] for k in range(i - LB, i) if S[k].get("ema21")): continue
        if i - last_sig <= COOLDOWN: continue
        st = state_at(i)
        if not st["higher_low"]: continue
        if st["choch_age"] > CH_WIN: continue
        if not (RET_LO <= st["retrace"] <= RET_HI): continue
        if st["pullback_age"] < P_AGE: continue
        q = quiet30_at(b["t"])
        if q is None or q > QUIET_MAX: continue
        # SL structural
        sl = (st["hl_low"] - 0.1 * atr) if st["hl_low"] is not None else (st["dipleg_low"] - 0.1 * atr)
        if (b["c"] - sl) < 1.0 * atr:
            sl = st["dipleg_low"] - 0.1 * atr
        dist_atr = (b["c"] - sl) / atr
        sigs.append(dict(i=i, t=b["t"], c=b["c"], sl=sl, dist_atr=dist_atr, dist_usd=b["c"] - sl))
        last_sig = i
    return sigs

def report(name, sigs):
    if not sigs:
        print(f"{name}: 0 sinais"); return
    weeks = len({dt.datetime.utcfromtimestamp(b["t"]).strftime("%G-%V") for b in S})
    n = len(sigs)
    per_wk = n / weeks
    # coverage of the 35: signal within t0 - 6 bars .. t0 + 6 bars
    sig_ts = [s["t"] for s in sigs]
    cov = 0
    for t0 in T35:
        j = bisect.bisect_left(sig_ts, t0 - 6 * 900)
        if j < len(sig_ts) and sig_ts[j] <= t0 + 6 * 900: cov += 1
    d_atr = sorted(s["dist_atr"] for s in sigs)
    d_usd = sorted(s["dist_usd"] for s in sigs)
    med = lambda a: a[len(a) // 2]
    q1 = lambda a: a[len(a) // 4]; q3 = lambda a: a[3 * len(a) // 4]
    byyear = {}
    for s in sigs:
        y = dt.datetime.utcfromtimestamp(s["t"]).year
        byyear[y] = byyear.get(y, 0) + 1
    print(f"{name}: N={n}  {per_wk:.2f}/sem ({weeks} sem)  cobertura35={cov}/35"
          f"  SL_atr med {med(d_atr):.2f} [{q1(d_atr):.2f}-{q3(d_atr):.2f}]"
          f"  SL$ med {med(d_usd):.1f} [{q1(d_usd):.1f}-{q3(d_usd):.1f}]  por-ano {byyear}")

# ---------- grid (LOOK LEDGER — outcome-blind) ----------
GRID = [
    ("L1  P=16 BUF=0.00", dict(P_AGE=16, BUF=0.00)),
    ("L2  P=16 BUF=0.15", dict(P_AGE=16, BUF=0.15)),
    ("L3  P=24 BUF=0.15", dict(P_AGE=24, BUF=0.15)),
    ("L4  P=32 BUF=0.15", dict(P_AGE=32, BUF=0.15)),
    ("L5  P=24 BUF=0.30", dict(P_AGE=24, BUF=0.30)),
    ("L6  P=24 BUF=0.15 semQUIET", dict(P_AGE=24, BUF=0.15, QUIET_MAX=99.0)),
]
for name, kw in GRID:
    report(name, scan(**kw))
