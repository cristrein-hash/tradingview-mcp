#!/usr/bin/env python3
"""Cp REFINADO (Cris 2026-07-15) — entrada-PÓS-GRAB + exit TRAILING, sobre o entry-por-construção validado.
 ENTRADA pós-grab (causal, mata a entrada precipitada): após o fundo-de-perna-significativa, espera um
   HIGHER-LOW (swing-low acima do grab-low corrente; novo grab reseta) e entra no RECLAIM seguinte;
   SL = grab-low − 0.1ATR (abaixo da varredura mais funda = sobrevive ao grab).
 EXIT trailing (R1-armed, trail em swing-lows fractais, cap 20R, horizonte 480) — apanha os runners (MFE 6R).
Compara 4 variantes (baseline↔refinado) na confluência auction. RAW-only 15M. Validação: WR·avgR·NET·streak·DD·GT."""
import gzip, json, bisect, statistics, datetime as dt
from pathlib import Path
import sys; HERE = Path(__file__).resolve().parent; sys.path.insert(0, str(HERE))
ds = lambda t: dt.datetime.utcfromtimestamp(int(t)).strftime("%m-%d %H:%M")
M_FRAC, LEGWIN, HMAX, LEGMIN, RCAP = 3, 480, 480, 15, 20.0
BLOCKS = ["XAUUSD_15m_replay_2025-11-25_to_2026-02-25.jsonl.gz", "XAUUSD_15m_replay_2026-02-25_to_2026-05-25_rerun_customOBbaseline.jsonl.gz", "XAUUSD_15m_replay_2026-05-25_to_2026-07-04.jsonl.gz"]
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
def sz(bubs, ts, t0, t1): return sum(bubs[i]["sz"] for i in range(bisect.bisect_left(ts, t0), bisect.bisect_right(ts, t1)))
def last_swinglow(m):
    i = bisect.bisect_right(SLB, m-M_FRAC)-1
    return L[SLB[i]] if i >= 0 else None
t_lo = int(dt.datetime(2026, 2, 1, tzinfo=dt.timezone.utc).timestamp()); t_hi = int(dt.datetime(2026, 7, 4, tzinfo=dt.timezone.utc).timestamp())
GT = []
for a, b in [(1770015600, 1770210000), (1770339600, 1771448400), (1774242000, 1774270800), (1781128800, 1781128800), (1782781200, 1782907200)]:
    aa = bisect.bisect_left(T, min(a, b)-12*3600); bb = bisect.bisect_right(T, max(a, b)+12*3600); GT.append(T[min(range(aa, bb), key=lambda k: L[k])])

def entry_first(j):   # baseline: 1º reclaim
    atr = ATR[j] or 5.0; sl = round(L[j]-0.1*atr, 2)
    for k in range(j+M_FRAC, min(N, j+96)):
        if L[k] <= sl: return None
        if C[k] > H[k-1] and C[k] > O[k]:
            ent = round(C[k], 2); r = ent-sl
            if r > 0.05*atr: return {"k": k, "ent": ent, "sl": sl, "R": round(r, 2)}
    return None
def entry_postgrab(j):   # espera higher-low acima do grab, entra no reclaim; SL abaixo do grab
    atr0 = ATR[j] or 5.0; lowest = L[j]; hl = False
    for k in range(j+1, min(N, j+96)):
        if L[k] < lowest: lowest = L[k]; hl = False            # novo grab -> exige novo higher-low
        p = k-M_FRAC
        if p > j and is_sl(p) and L[p] > lowest+0.05*atr0: hl = True
        if hl and C[k] > H[k-1] and C[k] > O[k]:
            ent = round(C[k], 2); sl = round(lowest-0.1*atr0, 2); r = ent-sl
            if r > 0.05*atr0: return {"k": k, "ent": ent, "sl": sl, "R": round(r, 2)}
    return None
def exit_fixed3R(k, ent, sl):
    r = ent-sl; tgt = ent+3*r
    for m in range(k+1, min(N, k+HMAX+1)):
        if L[m] <= sl: return -1.0
        if H[m] >= tgt: return 3.0
    return round((C[min(N-1, k+HMAX)]-ent)/r, 2)
def exit_trail(k, ent, sl):
    r = ent-sl; trail = sl; armed = False; end = min(N-1, k+HMAX)
    for m in range(k+1, end+1):
        if L[m] <= trail: return round(max(-1.0, min(RCAP, (trail-ent)/r)), 2)
        if (H[m]-ent)/r >= 1: armed = True
        if armed:
            sw = last_swinglow(m)
            if sw is not None: trail = max(trail, round(sw-0.1*(ATR[m] or 5.0), 2))
    return round(max(-1.0, min(RCAP, (C[end]-ent)/r)), 2)
def exit_trail_after3R(k, ent, sl):
    """Base 3R travada: SL original até +3R; ao tocar 3R, trava em +3R e trai swing-lows NUNCA abaixo de 3R."""
    r = ent-sl; base = ent+3*r; trail = sl; armed3 = False; end = min(N-1, k+HMAX)
    for m in range(k+1, end+1):
        if L[m] <= trail: return round(max(-1.0, min(RCAP, (trail-ent)/r)), 2)
        if not armed3 and H[m] >= base: armed3 = True; trail = base       # trava +3R
        if armed3:
            sw = last_swinglow(m)
            trail = max(trail, base, round((sw-0.1*(ATR[m] or 5.0)) if sw is not None else base, 2))
    return round(max(-1.0, min(RCAP, (C[end]-ent)/r)), 2)

def run(entry_fn, exit_fn):
    rows = []
    for p in SLB:
        if not (t_lo <= T[p] <= t_hi): continue
        hb = max(range(max(0, p-LEGWIN), p+1), key=lambda k: H[k]); atr = ATR[p] or 5.0; dur = max(1, p-hb)
        if (H[hb]-L[p])/atr < LEGMIN or not (L[p] <= min(L[max(0, p-192):p+1])+1e-9): continue
        if not (sz(BUYS, BT, T[hb], T[p])/dur >= 0.25 or sz(SELLS, ST, T[hb], T[p]) >= 180): continue
        e = entry_fn(p)
        if not e: continue
        R = exit_fn(e["k"], e["ent"], e["sl"])
        rows.append({"R": R, "win": R > 0, "gt": any(abs(T[p]-g) < 6*3600 for g in GT), "dt": ds(T[e["k"]])})
    return rows
def panel(name, rows):
    n = len(rows); w = sum(1 for r in rows if r["win"]); net = sum(r["R"] for r in rows)
    eq = pk = dd = strk = mx = 0
    for r in rows:
        eq += r["R"]; pk = max(pk, eq); dd = min(dd, eq-pk); strk = strk+1 if not r["win"] else 0; mx = min(mx, -strk)
    avg = net/n if n else 0; ng = sum(1 for r in rows if r["gt"])
    print(f"  {name:<34} N={n:>2} WR {100*w/max(1,n):>3.0f}% avgR {avg:>+5.2f} NET {net:>+6.1f}R DD {dd:>+5.1f} streak {mx:>3} GT {ng}/5")

print("=== Cp: baseline → REFINADO (confluência auction, bear 2026) ===")
panel("① 1º-reclaim + 3R-fixo (baseline)", run(entry_first, exit_fixed3R))
panel("② 1º-reclaim + TRAILING", run(entry_first, exit_trail))
panel("⑤ 1º-reclaim + TRAIL-APÓS-3R (b)", run(entry_first, exit_trail_after3R))
panel("③ PÓS-GRAB + 3R-fixo", run(entry_postgrab, exit_fixed3R))
panel("⑥ PÓS-GRAB + TRAIL-APÓS-3R", run(entry_postgrab, exit_trail_after3R))
# distribuição dos R da variante (b) p/ ver os runners
rb = run(entry_first, exit_trail_after3R)
print("\n  variante (b) — R por trade:", sorted([r["R"] for r in rb], reverse=True))