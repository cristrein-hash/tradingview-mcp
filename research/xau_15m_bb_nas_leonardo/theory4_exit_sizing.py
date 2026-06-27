#!/usr/bin/env python3
"""RODADA 4 (bounded, a alavanca do canon) — EXIT + SIZING sobre a base mais robusta R1 with_macro BULL-long (n80).
Testa variantes de saída {let-run, parcial-50%@2R, alvo-fixo-3R+BE} × sizing {1%,0.5%,0.25%} com sim de sobrevivência
FN (DD trailing 5%, alvo +8%) + leave-one-out. Sucesso pré-registrado: funded a ≥0.5% SEM freq<1/sem E leave-one-out
positivo. Causal. Verified 2026-06-26."""
import csv, json, statistics as st
from pathlib import Path
HERE = Path(__file__).parent
PRIM = {p.name.split(".")[0].replace("XAUUSD_15m_replay_", ""): json.loads(p.read_text())
        for p in (HERE / "primitives").glob("*.primitives.json")}
SER = {b: pr["series"] for b, pr in PRIM.items()}; TID = {b: {x["t"]: i for i, x in enumerate(s)} for b, s in SER.items()}
K, HMAX, MIN_RISK_ATR, R_CAP = 2, 480, 0.5, 15.0
def conf_low(s, i):
    L = [b["l"] for b in s]; lo = max(K, i - 120); best = None
    for p in range(lo, i - K + 1):
        if L[p] == min(L[p - K:p + K + 1]): best = L[p]
    return best
def walk(s, ei, entry, risk, mode):
    """retorna R conforme modo de saída. LONG only (base é BULL-long)."""
    sl = entry - risk; tgt3 = entry + 3 * risk; tgt2 = entry + 2 * risk
    be = False; part = False; pr = 0.0; end = min(ei + HMAX, len(s) - 1); atr = risk / MIN_RISK_ATR if False else None
    for i in range(ei + 1, end + 1):
        bar = s[i]
        if mode == "fixed3R":
            if bar["l"] <= sl: return (entry - sl) / risk * (-1) if not be else 0.0  # -1R ou BE
            if bar["h"] >= tgt3: return 3.0
            if not be and (bar["h"] - entry) / risk >= 1: sl = entry; be = True
        elif mode == "partial2R":
            if bar["l"] <= sl: return pr + 0.5 * ((sl - entry) / risk if part else (sl - entry) / risk)
            if not part and bar["h"] >= tgt2:
                pr = 0.5 * 2.0; part = True; sl = entry  # realiza metade @2R, resto BE+trail
            if part:
                sw = conf_low(s, i)
                if sw: sl = max(sl, sw - 0.1 * (risk / MIN_RISK_ATR))
        else:  # letrun (trailing estrutural)
            if bar["l"] <= sl: return (sl - entry) / risk
            if (bar["h"] - entry) / risk >= 1:
                sw = conf_low(s, i)
                if sw: sl = max(sl, sw - 0.1 * (risk / MIN_RISK_ATR))
    cl = s[end]["c"]
    if mode == "partial2R" and part: return pr + 0.5 * ((cl - entry) / risk)
    return (cl - entry) / risk
def trades(mode):
    out = []
    for r in csv.DictReader(open(HERE / "candidates_annotated.csv")):
        if r["setup_vs_macro"] != "with_macro" or r["dir"] != "LONG": continue
        b = r["block"]; s = SER.get(b); ei = TID.get(b, {}).get(int(r["entry_t"]))
        if s is None or ei is None or ei + 2 >= len(s): continue
        entry = float(r["entry_close"]); zlo = float(r["zone_low"]); zhi = float(r["zone_high"]); zwa = float(r["zone_width_atr"])
        atr = (zhi - zlo) / zwa if zwa > 0 else None
        if not atr: continue
        sl0 = zlo - 0.1 * atr; risk = max(entry - sl0, MIN_RISK_ATR * atr)
        if risk <= 0: continue
        R = max(-1.0, min(R_CAP, walk(s, ei, entry, risk, mode)))
        out.append({"t": int(r["entry_t"]), "block": b, "R": R, "win": R > 0})
    return sorted(out, key=lambda x: x["t"])
def metrics(trs):
    n = len(trs); w = sum(1 for t in trs if t["win"]); sumR = sum(t["R"] for t in trs)
    eq=0;peak=0;dd=0;stk=0;mstk=0
    for t in trs:
        eq+=t["R"];peak=max(peak,eq);dd=min(dd,eq-peak)
        if t["R"]<=0:stk+=1;mstk=max(mstk,stk)
        else:stk=0
    span=(trs[-1]["t"]-trs[0]["t"])/(7*86400) or 1
    byb={};
    for t in trs: byb.setdefault(t["block"],[]).append(t)
    drop=set(sorted(byb,key=lambda b:sum(x["R"] for x in byb[b]),reverse=True)[:2]); lo=sum(t["R"] for t in trs if t["block"] not in drop)
    return n,100*w/n,sumR/n,sumR,dd,mstk,n/span,lo
def survive(trs, r_pct, LIM=5.0, TGT=8.0):
    eq=0;peak=0;bust=None;hit=None
    for i,t in enumerate(trs):
        eq+=t["R"]*r_pct;peak=max(peak,eq)
        if peak-eq>=LIM and bust is None:bust=i+1
        if eq>=TGT and hit is None and bust is None:hit=i+1
    return "BUST@%d"%bust if bust else ("ALVO@%d"%hit if hit else "vivo")
print("=== RODADA 4 | EXIT+SIZING sobre R1 with_macro BULL-long ===")
for mode in ("letrun","partial2R","fixed3R"):
    trs=trades(mode); n,wr,avg,sm,dd,stk,fq,lo=metrics(trs)
    print(f"\n[{mode}] n={n} WR={wr:.0f}% avgR={avg:+.2f} sumR={sm:+.1f} DD={dd:.1f}R streakL={stk} freq={fq:.2f}/sem | leave−top2bloc={lo:+.0f}R")
    print(f"   survive FN: 1%→{survive(trs,1.0)} | 0.5%→{survive(trs,0.5)} | 0.25%→{survive(trs,0.25)}")
print("\nSucesso pré-registrado: funded a ≥0.5% SEM freq<1/sem E leave-one-out positivo. (base já é 0.83/sem)")
