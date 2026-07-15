#!/usr/bin/env python3
"""ANÁLISE PROFUNDA dos trades Cp (Cris 2026-07-15): (1) os LOSS são GRABS de liquidez? (SL varrido,
depois preço reverte e alcança o 3R) = região certa, entrada precipitada. (2) MFE (max favorable
excursion em R) por trade = dinheiro na mesa p/ alongar exits. (3) SL alternativo (mais fundo = wick /
mais curto = estrutural) — qual sobrevive ao grab. RAW-only 15M, causal p/ o desfecho."""
import gzip, json, bisect, statistics, datetime as dt
from pathlib import Path
import sys; HERE = Path(__file__).resolve().parent; sys.path.insert(0, str(HERE))
ds = lambda t: dt.datetime.utcfromtimestamp(int(t)).strftime("%m-%d %H:%M")
def iso2ep(x):
    try: return int(dt.datetime.fromisoformat(x.replace("Z", "+00:00")).timestamp())
    except Exception: return None
M_FRAC, LEGWIN, HMAX, LEGMIN = 3, 480, 480, 15
BLOCKS = ["XAUUSD_15m_replay_2025-11-25_to_2026-02-25.jsonl.gz", "XAUUSD_15m_replay_2026-02-25_to_2026-05-25_rerun_customOBbaseline.jsonl.gz", "XAUUSD_15m_replay_2026-05-25_to_2026-07-04.jsonl.gz"]
grp = lambda rec, k, s: next((x for x in (rec.get(k) or []) if s.lower() in str(x.get("name", "")).lower()), None)
bars = {}; buyb = {}; sellb = {}
for blk in BLOCKS:
    snaps = []
    with gzip.open(Path("/Volumes/GUTS_ LACIE/TradingData/raw_replay/XAUUSD/15M")/blk, "rt") as fh:
        for line in fh:
            try: r = json.loads(line)
            except Exception: continue
            if isinstance(r, dict) and r.get("ohlcv"): snaps.append(r)
    snaps.sort(key=lambda r: r.get("replay_current_date") or 0)
    for r in snaps:
        for b in (r.get("ohlcv") or []):
            if isinstance(b, dict) and b.get("time") is not None: bars[b["time"]] = {"o": b["open"], "h": b["high"], "l": b["low"], "c": b["close"]}
        pb = r.get("pine_shapes_bubbles")
        if pb:
            BUY = {"plot_0": 1, "plot_2": 2, "plot_4": 3}; SELL = {"plot_6": 1, "plot_8": 2, "plot_10": 3}
            for act in (pb[0].get("activations") or []):
                tt = act.get("time")
                for plot in (act.get("shapes") or {}):
                    if plot in BUY and (tt, plot) not in buyb: buyb[(tt, plot)] = {"t": tt, "sz": BUY[plot]}
                    if plot in SELL and (tt, plot) not in sellb: sellb[(tt, plot)] = {"t": tt, "sz": SELL[plot]}
T = sorted(bars); O = [bars[t]["o"] for t in T]; H = [bars[t]["h"] for t in T]; L = [bars[t]["l"] for t in T]; C = [bars[t]["c"] for t in T]
N = len(T); ATR = [None]*N; trs = []
for i in range(N):
    if i > 0: trs.append(max(H[i]-L[i], abs(H[i]-C[i-1]), abs(L[i]-C[i-1])))
    ATR[i] = sum(trs[-14:])/14 if len(trs) >= 14 else None
BUYS = sorted(buyb.values(), key=lambda x: x["t"]); SELLS = sorted(sellb.values(), key=lambda x: x["t"]); BT = [x["t"] for x in BUYS]; ST = [x["t"] for x in SELLS]
def is_sl(p): return p-M_FRAC >= 0 and p+M_FRAC < N and L[p] == min(L[p-M_FRAC:p+M_FRAC+1]) and L[p] < min(L[p-M_FRAC:p])
SLB = [p for p in range(M_FRAC, N-M_FRAC) if is_sl(p)]
t_lo = int(dt.datetime(2026, 2, 1, tzinfo=dt.timezone.utc).timestamp()); t_hi = int(dt.datetime(2026, 7, 4, tzinfo=dt.timezone.utc).timestamp())
def cnt(bubs, ts, t0, t1): return sum(bubs[i]["sz"] for i in range(bisect.bisect_left(ts, t0), bisect.bisect_right(ts, t1)))
def analyze(j):
    atr = ATR[j] or 5.0
    for k in range(j+M_FRAC, min(N, j+96)):
        if L[k] <= round(L[j]-0.1*atr, 2): return None
        if C[k] > H[k-1] and C[k] > O[k]:
            ent = round(C[k], 2); sl = round(L[j]-0.1*atr, 2); r = ent-sl
            if r <= 0.05*atr: continue
            tgt = ent+3*r; o = "OPEN"; stop_bar = None; mfe = 0
            for m in range(k+1, min(N, k+HMAX+1)):
                mfe = max(mfe, (H[m]-ent)/r)                    # MFE mede toda a excursão (mesmo pós-3R)
                if o == "OPEN" and L[m] <= sl: o, stop_bar = "LOSS", m
                elif o == "OPEN" and H[m] >= tgt: o = "WIN"
            # GRAB? se LOSS, o preço reverte e alcança 3R DEPOIS do stop?
            grab = False
            if o == "LOSS" and stop_bar:
                for m in range(stop_bar+1, min(N, k+HMAX+1)):
                    if H[m] >= tgt: grab = True; break
            return {"j": j, "ent": ent, "sl": sl, "R": round(r, 2), "o": o, "mfe": round(mfe, 1), "grab": grab, "k": k}
    return None
GT = []
for a, b in [(1770015600, 1770210000), (1770339600, 1771448400), (1774242000, 1774270800), (1781128800, 1781128800), (1782781200, 1782907200)]:
    aa = bisect.bisect_left(T, min(a, b)-12*3600); bb = bisect.bisect_right(T, max(a, b)+12*3600); GT.append(T[min(range(aa, bb), key=lambda k: L[k])])
trades = []
for p in SLB:
    if not (t_lo <= T[p] <= t_hi): continue
    hb = max(range(max(0, p-LEGWIN), p+1), key=lambda k: H[k]); atr = ATR[p] or 5.0; dur = max(1, p-hb)
    if (H[hb]-L[p])/atr < LEGMIN or not (L[p] <= min(L[max(0, p-192):p+1])+1e-9): continue
    buy_dens = cnt(BUYS, BT, T[hb], T[p])/dur; leg_sell = cnt(SELLS, ST, T[hb], T[p])
    if not (buy_dens >= 0.25 or leg_sell >= 180): continue
    a = analyze(p)
    if not a: continue
    a["gt"] = any(abs(T[p]-g) < 6*3600 for g in GT); a["dt"] = ds(T[a["k"]]); trades.append(a)
v = [t for t in trades if t["o"] in ("WIN", "LOSS")]; W = [t for t in v if t["o"] == "WIN"]; Lo = [t for t in v if t["o"] == "LOSS"]
grabs = [t for t in Lo if t["grab"]]
print(f"=== ANÁLISE PROFUNDA Cp ({len(trades)} trades) ===")
print(f"  WIN {len(W)} · LOSS {len(Lo)} · OPEN {len(trades)-len(v)} · GT {sum(1 for t in trades if t['gt'])}/5")
print(f"\n(1) GRABS DE LIQUIDEZ: dos {len(Lo)} LOSS, {len(grabs)} revertem e alcançam 3R DEPOIS do stop = região certa, entrada precipitada")
for t in grabs: print(f"    GRAB {t['dt']} ent{t['ent']} SL{t['sl']} (R{t['R']}pt) mfe-pós {t['mfe']}R")
print(f"    LOSS reais (não recuperam): {len(Lo)-len(grabs)}")
print(f"\n(2) MFE (dinheiro na mesa) — WIN só contabiliza 3R mas foram até:")
for t in sorted(W, key=lambda x: -x["mfe"])[:8]: print(f"    {t['dt']} {'★GT ' if t['gt'] else ''}chegou {t['mfe']}R (fechámos em 3R)")
print(f"    MFE mediano dos WIN: {statistics.median([t['mfe'] for t in W]):.1f}R · dos que passaram de 5R: {sum(1 for t in W if t['mfe']>=5)}/{len(W)}")
print(f"\n(3) se convertêssemos os grabs (SL sobrevive) + exit no MFE real:")
wr2 = (len(W)+len(grabs))/len(v)*100
print(f"    WR: {100*len(W)/len(v):.0f}% -> {wr2:.0f}% (grabs viram WIN) · MFE médio WIN {statistics.mean([t['mfe'] for t in W]):.1f}R")