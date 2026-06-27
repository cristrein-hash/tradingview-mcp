#!/usr/bin/env python3
"""SANITY_PROBE (DA item 6): does partial2R add edge or just rescue let-run trail give-back?
Deterministic give-back accounting on the 2R-touchers. Read-only."""
import csv, json
from pathlib import Path
HERE = Path(__file__).parent
PRIM = {p.name.split(".")[0].replace("XAUUSD_15m_replay_", ""): json.loads(p.read_text()) for p in (HERE/"primitives").glob("*.primitives.json")}
SER = {b: pr["series"] for b, pr in PRIM.items()}; TID = {b: {x["t"]: i for i, x in enumerate(s)} for b, s in SER.items()}
K, HMAX, MIN_RISK_ATR, R_CAP = 2, 480, 0.5, 15.0
def conf_low(s, i):
    L = [b["l"] for b in s]; lo = max(K, i-120); best = None
    for p in range(lo, i-K+1):
        if L[p] == min(L[p-K:p+K+1]): best = L[p]
    return best
RAW = [r for r in csv.DictReader(open(HERE/"candidates_annotated.csv")) if r["setup_vs_macro"]=="with_macro" and r["dir"]=="LONG"]
def walk_letrun(s, ei, entry, risk):
    sl = entry-risk; end = min(ei+HMAX, len(s)-1)
    for i in range(ei+1, end+1):
        bar = s[i]
        if bar["l"] <= sl: return (sl-entry)/risk
        if (bar["h"]-entry)/risk >= 1:
            sw = conf_low(s, i)
            if sw: sl = max(sl, sw-0.1*(risk/MIN_RISK_ATR))
    return (s[end]["c"]-entry)/risk
def walk_partial(s, ei, entry, risk):
    sl = entry-risk; tgt2 = entry+2*risk; part = False; pr = 0.0; end = min(ei+HMAX, len(s)-1)
    for i in range(ei+1, end+1):
        bar = s[i]
        if bar["l"] <= sl: return pr+0.5*((sl-entry)/risk)
        if not part and bar["h"] >= tgt2: pr = 1.0; part = True; sl = entry
        if part:
            sw = conf_low(s, i)
            if sw: sl = max(sl, sw-0.1*(risk/MIN_RISK_ATR))
    return pr+0.5*((s[end]["c"]-entry)/risk) if part else (s[end]["c"]-entry)/risk
def mfe(s, ei, entry, risk):
    sl = entry-risk; end = min(ei+HMAX, len(s)-1); m = 0
    for i in range(ei+1, end+1):
        bar = s[i]
        if bar["l"] <= sl: return m
        m = max(m, (bar["h"]-entry)/risk)
    return m
cnt = 0; gl = 0; gp = 0; gaveback = 0
for r in RAW:
    b = r["block"]; s = SER.get(b); ei = TID.get(b, {}).get(int(r["entry_t"]))
    if s is None or ei is None or ei+2 >= len(s): continue
    entry = float(r["entry_close"]); zlo = float(r["zone_low"]); zhi = float(r["zone_high"]); zwa = float(r["zone_width_atr"])
    atr = (zhi-zlo)/zwa if zwa > 0 else None
    if not atr: continue
    risk = max(entry-(zlo-0.1*atr), MIN_RISK_ATR*atr)
    if mfe(s, ei, entry, risk) >= 2.0:
        cnt += 1
        lr = max(-1, min(R_CAP, walk_letrun(s, ei, entry, risk)))
        pr = max(-1, min(R_CAP, walk_partial(s, ei, entry, risk)))
        gl += lr; gp += pr
        if lr < 0.5: gaveback += 1
print(f"2R-touchers n={cnt}")
print(f"  letrun sumR on these  = {gl:+.1f}")
print(f"  partial sumR on these = {gp:+.1f}")
print(f"  partial advantage from give-back rescue = {gp-gl:+.1f}R")
print(f"  2R-touchers letrun gave back to <0.5R = {gaveback}/{cnt}")
