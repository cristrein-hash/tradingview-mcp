#!/usr/bin/env python3
"""RODADA 3 — família CONTINUAÇÃO a-favor-da-tendência (perfil WR-alto/streak-baixo). Causal RAW.
LONG (macro BULL): tendência operacional (close>EMA21 ascendente) + pullback RASO ao EMA (min low recente perto do
EMA, SEM romper o swing-low anterior = HL intacto) + RETOMADA (close rompe a máxima recente do pullback). Entrada
close[i+1] (SHIFT1). SL = mínima do pullback −0.1ATR (piso 0.5ATR). Saída MODESTA: alvo 2.5R, BE após +1R, horizonte
60 barras. SHORT espelho em BEAR. Confluência (não-gate, NAS backward-only =sem look-ahead): nas_near, in_zone, rsi.
Verified 2026-06-26."""
import json, bisect, statistics as st, csv
from pathlib import Path
HERE = Path(__file__).parent
PRIM = {p.name.split(".")[0].replace("XAUUSD_15m_replay_", ""): json.loads(p.read_text())
        for p in (HERE / "primitives").glob("*.primitives.json")}
M = json.loads((HERE / "macro_regime_4h.json").read_text())["bars_4h"]; MEND = [b["t_end"] for b in M]
def macro_at(t):
    k = bisect.bisect_right(MEND, t) - 1; return M[k]["macro"] if k >= 0 else "WARMUP"
K, MIN_GAP, T_R, BE_R, H = 2, 6, 2.5, 1.0, 60
MIN_RISK_ATR = 0.5
def conf_low(s, i):
    L = [b["l"] for b in s]; lo = max(K, i - 60); best = None
    for p in range(lo, i - K + 1):
        if L[p] == min(L[p - K:p + K + 1]): best = L[p]
    return best
def conf_high(s, i):
    H_ = [b["h"] for b in s]; lo = max(K, i - 60); best = None
    for p in range(lo, i - K + 1):
        if H_[p] == max(H_[p - K:p + K + 1]): best = H_[p]
    return best
def outcome(s, ei, entry, sl0, long, atr):
    struct = (entry - sl0) if long else (sl0 - entry)
    if struct <= 0: return None
    risk = max(struct, MIN_RISK_ATR * atr); sl0 = (entry - risk) if long else (entry + risk)
    tgt = entry + T_R * risk if long else entry - T_R * risk
    stop = sl0; be = False; mfe = 0.0; exit_px = None; end = min(ei + H, len(s) - 1)
    for i in range(ei + 1, end + 1):
        bar = s[i]
        if long:
            mfe = max(mfe, (bar["h"] - entry) / risk)
            if bar["l"] <= stop: exit_px = stop; break
            if bar["h"] >= tgt: exit_px = tgt; break
            if not be and (bar["h"] - entry) / risk >= BE_R: stop = entry; be = True
        else:
            mfe = max(mfe, (entry - bar["l"]) / risk)
            if bar["h"] >= stop: exit_px = stop; break
            if bar["l"] <= tgt: exit_px = tgt; break
            if not be and (entry - bar["l"]) / risk >= BE_R: stop = entry; be = True
    if exit_px is None: exit_px = s[end]["c"]
    R = ((exit_px - entry) if long else (entry - exit_px)) / risk
    return {"R": R, "mfe_R": mfe, "runner": mfe >= 3.0, "win": R > 0}
def detect():
    cands = []
    for b, pr in PRIM.items():
        s = pr["series"]; n = len(s); L = [x["l"] for x in s]; Hh = [x["h"] for x in s]
        nas = sorted([(e["t"], e["dir"]) for e in pr["nas_events"] if e["t"]]); nt = [x[0] for x in nas]
        zones = pr["zones"]; last_fire = -999
        for i in range(40, n - 2):
            t = s[i]["t"]; atr = s[i]["atr"]; ema = s[i]["ema21"]
            if not atr or not ema or i - last_fire < MIN_GAP: continue
            mac = macro_at(t)
            if mac == "BULL":
                up = s[i]["c"] > ema and ema > s[i - 10]["ema21"]
                dip = min(L[i - 5:i + 1]); pulled = dip <= ema + 0.5 * atr
                resume = s[i]["c"] > max(Hh[i - 3:i])
                sl_lo = conf_low(s, i)
                hl = sl_lo is not None and dip >= sl_lo - 0.2 * atr
                if up and pulled and resume and hl:
                    ei = i + 1
                    if ei + 2 >= n: continue
                    entry = s[ei]["c"]; sl0 = dip - 0.1 * atr
                    oc = outcome(s, ei, entry, sl0, True, atr)
                    if not oc: continue
                    k = bisect.bisect_right(nt, t)  # backward-only (≤ t): sem look-ahead
                    nas_near = any(t - nas[x][0] <= 4 * 900 and nas[x][1] == "LONG" for x in range(max(0, k - 4), k))
                    in_dem = any("DEMAND" in z["text"] and z["born_t"] <= t <= z["last_t"] and z["low"] <= entry <= z["high"] for z in zones)
                    cands.append({"block": b, "t": t, "dir": "LONG", "rsi": s[i]["rsi"], "nas_near": int(nas_near), "in_zone": int(in_dem), **oc}); last_fire = i
            elif mac == "BEAR":
                dn = s[i]["c"] < ema and ema < s[i - 10]["ema21"]
                bounce = max(Hh[i - 5:i + 1]); pulled = bounce >= ema - 0.5 * atr
                resume = s[i]["c"] < min(L[i - 3:i])
                sh = conf_high(s, i); lh = sh is not None and bounce <= sh + 0.2 * atr
                if dn and pulled and resume and lh:
                    ei = i + 1
                    if ei + 2 >= n: continue
                    entry = s[ei]["c"]; sl0 = bounce + 0.1 * atr
                    oc = outcome(s, ei, entry, sl0, False, atr)
                    if not oc: continue
                    k = bisect.bisect_right(nt, t)
                    nas_near = any(t - nas[x][0] <= 4 * 900 and nas[x][1] == "SHORT" for x in range(max(0, k - 4), k))
                    in_sup = any("SUPPLY" in z["text"] and z["born_t"] <= t <= z["last_t"] and z["low"] <= entry <= z["high"] for z in zones)
                    cands.append({"block": b, "t": t, "dir": "SHORT", "rsi": s[i]["rsi"], "nas_near": int(nas_near), "in_zone": int(in_sup), **oc}); last_fire = i
    return cands
def agg(trs, label):
    if not trs: print(f"  [{label}] vazio"); return
    n = len(trs); w = sum(1 for t in trs if t["win"]); sumR = sum(t["R"] for t in trs); med = st.median([t["R"] for t in trs])
    ts = sorted(trs, key=lambda t: t["t"]); eq=0;peak=0;dd=0;stk=0;mstk=0
    for t in ts:
        eq += t["R"]; peak=max(peak,eq); dd=min(dd,eq-peak)
        if t["R"]<=0: stk+=1; mstk=max(mstk,stk)
        else: stk=0
    span=(ts[-1]["t"]-ts[0]["t"])/(7*86400) or 1
    print(f"  [{label}] n={n} WR={100*w/n:.0f}% medR={med:+.2f} avgR={sumR/n:+.2f} sumR={sumR:+.1f} DD={dd:.1f}R streakL={mstk} freq={n/span:.2f}/sem")
def leave_out(trs):
    byb={}
    for t in trs: byb.setdefault(t["block"],[]).append(t)
    drop=set(sorted(byb,key=lambda b:sum(x["R"] for x in byb[b]),reverse=True)[:2]); rem=[t for t in trs if t["block"] not in drop]
    rem2=sorted(rem,key=lambda t:t["R"],reverse=True)[5:]
    print(f"  leave-one-out: full {sum(t['R'] for t in trs):+.0f}R | −top2bloc {sum(t['R'] for t in rem):+.0f}R(n{len(rem)}) | −top2−top5 {sum(t['R'] for t in rem2):+.0f}R(n{len(rem2)}, avg{sum(t['R'] for t in rem2)/max(1,len(rem2)):+.2f})")
c=detect()
print(f"=== RODADA 3 | CONTINUAÇÃO (alvo{T_R}R, BE{BE_R}R, H{H}, piso{MIN_RISK_ATR}ATR) ===")
agg(c,"GERAL"); leave_out(c)
print(" por dir:"); agg([t for t in c if t["dir"]=="LONG"],"BULL-long"); agg([t for t in c if t["dir"]=="SHORT"],"BEAR-short")
print(" confluência:"); agg([t for t in c if t["nas_near"]],"+NAS"); agg([t for t in c if t["in_zone"]],"+zona"); agg([t for t in c if t["nas_near"] and t["in_zone"]],"+NAS&zona")
print(" por bloco:");
for b in sorted(set(t["block"] for t in c)): agg([t for t in c if t["block"]==b],b[:21])
with open(HERE/"candidates_continuation.csv","w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=list(c[0].keys())); w.writeheader(); w.writerows(c)
