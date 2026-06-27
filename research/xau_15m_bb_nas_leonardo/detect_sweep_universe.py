#!/usr/bin/env python3
"""RODADA 2 — UNIVERSO NOVO: gatilho = LIQUIDITY SWEEP+RECLAIM (não NAS-em-zona). Causal RAW.
LONG (macro BULL): bar i varre um swing-low confirmado recente (low[i] < liq − 0.05ATR) e RECLAMA (close[i] > liq).
SHORT (macro BEAR): espelho com swing-high. Macro 4H alinhado (gate). Dedup MIN_GAP barras. Entrada = close[i+1]
(SHIFT1). SL estrutural = extremo do sweep ∓0.1ATR (piso 0.5ATR). Let-run trailing estrutural. Confluência (score,
não-gate): NAS na direção ±3b, zona OB na direção, RSI, room-to-run. Agrega + leave-one-out. Verified 2026-06-26."""
import json, bisect, statistics as st
from pathlib import Path
HERE = Path(__file__).parent
PRIM = {p.name.split(".")[0].replace("XAUUSD_15m_replay_", ""): json.loads(p.read_text())
        for p in (HERE / "primitives").glob("*.primitives.json")}
M = json.loads((HERE / "macro_regime_4h.json").read_text())["bars_4h"]; MEND = [b["t_end"] for b in M]
def macro_at(t):
    k = bisect.bisect_right(MEND, t) - 1; return M[k]["macro"] if k >= 0 else "WARMUP"
K, LB, EPS_ATR, MIN_GAP = 2, 50, 0.05, 8
HMAX, RUNNER_R, MIN_RISK_ATR, R_CAP = 480, 3.0, 0.5, 15.0

def swing_lows(L, i):   # último swing-low confirmado até i (fractal k)
    for p in range(i - K, max(K, i - LB) - 1, -1):
        if L[p] == min(L[p - K:p + K + 1]): return L[p]
    return None
def swing_highs(H, i):
    for p in range(i - K, max(K, i - LB) - 1, -1):
        if H[p] == max(H[p - K:p + K + 1]): return H[p]
    return None
def conf_low(s, i):
    L = [b["l"] for b in s]; lo = max(K, i - 120); best = None
    for p in range(lo, i - K + 1):
        if L[p] == min(L[p - K:p + K + 1]): best = L[p]
    return best
def conf_high(s, i):
    H = [b["h"] for b in s]; lo = max(K, i - 120); best = None
    for p in range(lo, i - K + 1):
        if H[p] == max(H[p - K:p + K + 1]): best = H[p]
    return best

def outcome(s, ei, entry, sl0, long, atr):
    struct = (entry - sl0) if long else (sl0 - entry)
    if struct <= 0: return None
    risk = max(struct, MIN_RISK_ATR * atr); sl0 = (entry - risk) if long else (entry + risk)
    trail = sl0; r1 = False; mfe = 0.0; exit_px = None; end = min(ei + HMAX, len(s) - 1)
    for i in range(ei + 1, end + 1):
        bar = s[i]
        if long:
            mfe = max(mfe, (bar["h"] - entry) / risk)
            if bar["l"] <= trail: exit_px = trail; break
            if (bar["h"] - entry) / risk >= 1: r1 = True
            if r1:
                sw = conf_low(s, i)
                if sw: trail = max(trail, sw - 0.1 * atr)
        else:
            mfe = max(mfe, (entry - bar["l"]) / risk)
            if bar["h"] >= trail: exit_px = trail; break
            if (entry - bar["l"]) / risk >= 1: r1 = True
            if r1:
                sw = conf_high(s, i)
                if sw: trail = min(trail, sw + 0.1 * atr)
    if exit_px is None: exit_px = s[end]["c"]
    R = ((exit_px - entry) if long else (entry - exit_px)) / risk
    return {"R": R, "mfe_R": mfe, "runner": mfe >= RUNNER_R, "win": R > 0}

def detect():
    cands = []
    for b, pr in PRIM.items():
        s = pr["series"]; n = len(s); L = [x["l"] for x in s]; H = [x["h"] for x in s]
        nas = pr["nas_events"]; nas_t = sorted([(e["t"], e["dir"]) for e in nas if e["t"]])
        nt = [x[0] for x in nas_t]
        zones = pr["zones"]
        last_fire = -999
        for i in range(LB + K, n - 2):
            t = s[i]["t"]; atr = s[i]["atr"]
            if not atr: continue
            mac = macro_at(t)
            if i - last_fire < MIN_GAP: continue
            # LONG sweep+reclaim em BULL
            if mac == "BULL":
                liq = swing_lows(L, i)
                if liq and L[i] < liq - EPS_ATR * atr and s[i]["c"] > liq:
                    ei = i + 1
                    if ei + 2 >= n: continue
                    entry = s[ei]["c"]; sl0 = L[i] - 0.1 * atr
                    oc = outcome(s, ei, entry, sl0, True, atr)
                    if not oc: continue
                    # confluência
                    k = bisect.bisect_left(nt, t); nas_near = any(abs(nt[x] - t) <= 3 * 900 and nas_t[x][1] == "LONG" for x in range(max(0, k - 3), min(len(nt), k + 3)))
                    in_dem = any("DEMAND" in z["text"] and z["born_t"] <= t <= z["last_t"] and z["low"] <= entry <= z["high"] for z in zones)
                    cands.append({"block": b, "t": t, "dir": "LONG", "macro": mac, "rsi": s[i]["rsi"],
                                  "sweep_depth": round((liq - L[i]) / atr, 2), "reclaim_str": round((s[i]["c"] - liq) / atr, 2),
                                  "nas_near": int(nas_near), "in_zone": int(in_dem), **oc}); last_fire = i
            elif mac == "BEAR":
                liq = swing_highs(H, i)
                if liq and H[i] > liq + EPS_ATR * atr and s[i]["c"] < liq:
                    ei = i + 1
                    if ei + 2 >= n: continue
                    entry = s[ei]["c"]; sl0 = H[i] + 0.1 * atr
                    oc = outcome(s, ei, entry, sl0, False, atr)
                    if not oc: continue
                    k = bisect.bisect_left(nt, t); nas_near = any(abs(nt[x] - t) <= 3 * 900 and nas_t[x][1] == "SHORT" for x in range(max(0, k - 3), min(len(nt), k + 3)))
                    in_sup = any("SUPPLY" in z["text"] and z["born_t"] <= t <= z["last_t"] and z["low"] <= entry <= z["high"] for z in zones)
                    cands.append({"block": b, "t": t, "dir": "SHORT", "macro": mac, "rsi": s[i]["rsi"],
                                  "sweep_depth": round((H[i] - liq) / atr, 2), "reclaim_str": round((liq - s[i]["c"]) / atr, 2),
                                  "nas_near": int(nas_near), "in_zone": int(in_sup), **oc}); last_fire = i
    return cands

def agg(trs, label):
    if not trs: print(f"  [{label}] vazio"); return
    cap = lambda t: max(-1.0, min(R_CAP, t["R"])); n = len(trs); w = sum(1 for t in trs if t["win"])
    sumRc = sum(cap(t) for t in trs); med = st.median([t["R"] for t in trs]); runners = sum(1 for t in trs if t["runner"])
    ts = sorted(trs, key=lambda t: t["t"]); eq = 0; peak = 0; dd = 0; stk = 0; mstk = 0
    for t in ts:
        eq += cap(t); peak = max(peak, eq); dd = min(dd, eq - peak)
        if t["R"] <= 0: stk += 1; mstk = max(mstk, stk)
        else: stk = 0
    span = (ts[-1]["t"] - ts[0]["t"]) / (7 * 86400) or 1
    print(f"  [{label}] n={n} WR={100*w/n:.0f}% medR={med:+.2f} avgRc={sumRc/n:+.2f} sumRc={sumRc:+.1f} run={runners}({100*runners/n:.0f}%) DDc={dd:.1f}R streakL={mstk} freq={n/span:.2f}/sem")
def leave_out(trs):
    cap = lambda t: max(-1.0, min(R_CAP, t["R"])); byb = {}
    for t in trs: byb.setdefault(t["block"], []).append(t)
    drop = set(sorted(byb, key=lambda b: sum(cap(x) for x in byb[b]), reverse=True)[:2])
    rem = [t for t in trs if t["block"] not in drop]; rem2 = sorted(rem, key=cap, reverse=True)[5:]
    print(f"  leave-one-out: full {sum(cap(t) for t in trs):+.0f}R(n{len(trs)}) | −top2bloc {sum(cap(t) for t in rem):+.0f}R(n{len(rem)}) | −top2bloc−top5 {sum(cap(t) for t in rem2):+.0f}R(n{len(rem2)}, avg{sum(cap(t) for t in rem2)/max(1,len(rem2)):+.2f})")

c = detect()
print(f"=== RODADA 2 | universo SWEEP+RECLAIM (macro-alinhado) | piso{MIN_RISK_ATR}ATR Rcap{R_CAP} ===")
agg(c, "GERAL"); leave_out(c)
print(" por dir/macro:"); agg([t for t in c if t["dir"]=="LONG"], "BULL-long"); agg([t for t in c if t["dir"]=="SHORT"], "BEAR-short")
print(" confluência (não-gate, lift incremental):")
agg([t for t in c if t["nas_near"]], "+NAS_near"); agg([t for t in c if t["in_zone"]], "+in_zone")
agg([t for t in c if t["nas_near"] and t["in_zone"]], "+NAS&zone")
print(" por bloco:");
for b in sorted(set(t["block"] for t in c)): agg([t for t in c if t["block"]==b], b[:21])
import csv
with open(HERE/"candidates_sweep.csv","w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=list(c[0].keys())); w.writeheader(); w.writerows(c)
