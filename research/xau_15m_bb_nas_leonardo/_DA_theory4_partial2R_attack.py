#!/usr/bin/env python3
"""DA ATTACK on theory4 partial2R (2026-06-26). Reproduces walk EXACTLY from theory4_exit_sizing.py
and runs: leave-one-out depth, walk-causality trace, FN survival reordering, slippage fragility,
same-bar-cluster concentration, and the n=88-vs-86 duplicate-row integrity check.
Saved per orphan-output guard. Read-only on data."""
import csv, json, random
from pathlib import Path
from collections import Counter
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
    sl = entry - risk; tgt2 = entry + 2 * risk; part = False; pr = 0.0; end = min(ei + HMAX, len(s) - 1)
    for i in range(ei + 1, end + 1):
        bar = s[i]
        if mode == "partial2R":
            if bar["l"] <= sl: return pr + 0.5 * ((sl - entry) / risk if part else (sl - entry) / risk)
            if not part and bar["h"] >= tgt2: pr = 0.5 * 2.0; part = True; sl = entry
            if part:
                sw = conf_low(s, i)
                if sw: sl = max(sl, sw - 0.1 * (risk / MIN_RISK_ATR))
        else:
            if bar["l"] <= sl: return (sl - entry) / risk
            if (bar["h"] - entry) / risk >= 1:
                sw = conf_low(s, i)
                if sw: sl = max(sl, sw - 0.1 * (risk / MIN_RISK_ATR))
    cl = s[end]["c"]
    if mode == "partial2R" and part: return pr + 0.5 * ((cl - entry) / risk)
    return (cl - entry) / risk

# load EXACTLY as the original (no dedup) to reproduce n=88
RAW = [r for r in csv.DictReader(open(HERE / "candidates_annotated.csv"))
       if r["setup_vs_macro"] == "with_macro" and r["dir"] == "LONG"]
def build(rows):
    out = []
    for r in rows:
        b = r["block"]; s = SER.get(b); ei = TID.get(b, {}).get(int(r["entry_t"]))
        if s is None or ei is None or ei + 2 >= len(s): continue
        entry = float(r["entry_close"]); zlo = float(r["zone_low"]); zhi = float(r["zone_high"]); zwa = float(r["zone_width_atr"])
        atr = (zhi - zlo) / zwa if zwa > 0 else None
        if not atr: continue
        sl0 = zlo - 0.1 * atr; risk = max(entry - sl0, MIN_RISK_ATR * atr)
        if risk <= 0: continue
        R = max(-1.0, min(R_CAP, walk(s, ei, entry, risk, "partial2R")))
        out.append({"t": int(r["entry_t"]), "block": b, "R": R, "dt": r["entry_dt"], "zid": r["zone_id"], "nas": r["nas_id"]})
    return sorted(out, key=lambda x: x["t"])

trs = build(RAW); n = len(trs); sumR = sum(t["R"] for t in trs)
print(f"=== REPRODUCED (no dedup): n={n} sumR={sumR:+.2f} avgR={sumR/n:+.3f} ===")

# integrity: duplicate (block,entry_t)
c = Counter((t["block"], t["t"]) for t in trs)
dups = {k: v for k, v in c.items() if v > 1}
print(f"\n# INTEGRITY: duplicate (block,entry_t) trades = {len(dups)} (extra trades = {sum(v-1 for v in dups.values())})")
for k in dups:
    ds = [t for t in trs if (t["block"], t["t"]) == k]
    print(f"  {k} dt={ds[0]['dt']} zids={[d['zid'] for d in ds]} nas={[d['nas'] for d in ds]} Rs={[round(d['R'],2) for d in ds]}")
# dedup keeping first
seen = set(); ded = []
for t in trs:
    key = (t["block"], t["t"])
    if key in seen: continue
    seen.add(key); ded.append(t)
print(f"  after dedup: n={len(ded)} sumR={sum(t['R'] for t in ded):+.2f}")

print("\n### ITEM 1: leave-one-out depth ###")
byb = {}
for t in trs: byb.setdefault(t["block"], []).append(t)
bss = sorted(byb, key=lambda b: sum(x["R"] for x in byb[b]), reverse=True)
npos = sum(1 for b in bss if sum(x["R"] for x in byb[b]) > 0)
for b in bss:
    print(f"  {b[:24]}: net={sum(x['R'] for x in byb[b]):+.2f} n={len(byb[b])}")
print(f"net-positive blocks: {npos}/8")
drop2 = set(bss[:2]); lo2 = sum(t["R"] for t in trs if t["block"] not in drop2)
print(f"leave-top-2-blocks: {lo2:+.2f}")
tbr = sorted(trs, key=lambda x: x["R"], reverse=True)
print("top-8 trades:", [f"{t['dt'][:10]}:{t['R']:+.1f}" for t in tbr[:8]])
for k in (3, 5, 7, 10): print(f"  leave-top-{k}-trades (from full): {sumR - sum(t['R'] for t in tbr[:k]):+.2f}")
remt = [t for t in trs if t["block"] not in drop2]; rems = sorted(remt, key=lambda x: x["R"], reverse=True)
print(f"leave-top2blk AND top5-remaining-trades: {sum(t['R'] for t in remt) - sum(t['R'] for t in rems[:5]):+.2f}")
cum = 0; flip = 0
for i, t in enumerate(rems):
    cum += t["R"]
    if lo2 - cum < 0: flip = i + 1; break
print(f"trades to flip leave-top2blk negative: {flip} of {len(remt)}")

print("\n### ITEM: same-day / same-cluster concentration ###")
byday = {}
for t in trs: byday.setdefault(t["dt"][:10], []).append(t)
topdays = sorted(byday, key=lambda d: sum(x["R"] for x in byday[d]), reverse=True)[:5]
for d in topdays:
    print(f"  {d}: net={sum(x['R'] for x in byday[d]):+.2f} n={len(byday[d])} Rs={[round(x['R'],1) for x in byday[d]]}")
top1day = topdays[0]
print(f"sumR without best day ({top1day}): {sumR - sum(x['R'] for x in byday[top1day]):+.2f}")

print("\n### ITEM 3: FN survival ordering ###")
def surv(seq, r, LIM=5.0, TGT=8.0):
    eq = 0; peak = 0; bust = None; hit = None
    for i, t in enumerate(seq):
        eq += t["R"] * r; peak = max(peak, eq)
        if peak - eq >= LIM and bust is None: bust = i + 1
        if eq >= TGT and hit is None and bust is None: hit = i + 1
    return ("BUST", bust) if bust else (("ALVO", hit) if hit else ("vivo", None))
random.seed(42); res = {"ALVO": 0, "BUST": 0, "vivo": 0}
for _ in range(5000):
    sh = trs[:]; random.shuffle(sh); res[surv(sh, 1.0)[0]] += 1
print(f"5000 shuffles @1%: {res} P(ALVO)={res['ALVO']/5000:.1%}")
random.seed(1); res2 = {"ALVO": 0, "BUST": 0, "vivo": 0}
for _ in range(5000):
    sh = trs[:]; random.shuffle(sh); res2[surv(sh, 0.5)[0]] += 1
print(f"5000 shuffles @0.5%: {res2} P(ALVO)={res2['ALVO']/5000:.1%}")
print(f"reversed @1%: {surv(list(reversed(trs)),1.0)}")

print("\n### ITEM 5: slippage fragility (partial trigger shift) ###")
def walk_tgt(s, ei, entry, risk, tm):
    sl = entry - risk; tgt = entry + tm * risk; p = False; pr = 0.0; end = min(ei + HMAX, len(s) - 1)
    for i in range(ei + 1, end + 1):
        bar = s[i]
        if bar["l"] <= sl: return pr + 0.5 * ((sl - entry) / risk)
        if not p and bar["h"] >= tgt: pr = 0.5 * tm; p = True; sl = entry
        if p:
            sw = conf_low(s, i)
            if sw: sl = max(sl, sw - 0.1 * (risk / MIN_RISK_ATR))
    cl = s[end]["c"]; return pr + 0.5 * ((cl - entry) / risk) if p else (cl - entry) / risk
for tm in (1.9, 2.0, 2.1, 2.2):
    sm = 0
    for r in RAW:
        b = r["block"]; s = SER.get(b); ei = TID.get(b, {}).get(int(r["entry_t"]))
        if s is None or ei is None or ei + 2 >= len(s): continue
        entry = float(r["entry_close"]); zlo = float(r["zone_low"]); zhi = float(r["zone_high"]); zwa = float(r["zone_width_atr"])
        atr = (zhi - zlo) / zwa if zwa > 0 else None
        if not atr: continue
        risk = max(entry - (zlo - 0.1 * atr), MIN_RISK_ATR * atr)
        sm += max(-1.0, min(R_CAP, walk_tgt(s, ei, entry, risk, tm)))
    print(f"  trigger {tm}R: sumR={sm:+.2f}")
# entry slippage: shift entry up by fraction of risk (worse fill)
print("\n# entry slippage (worse fill = entry + slip*risk, SL & tgt move with it):")
for slip in (0.0, 0.05, 0.1):
    sm = 0; ntr = 0
    for r in RAW:
        b = r["block"]; s = SER.get(b); ei = TID.get(b, {}).get(int(r["entry_t"]))
        if s is None or ei is None or ei + 2 >= len(s): continue
        entry0 = float(r["entry_close"]); zlo = float(r["zone_low"]); zhi = float(r["zone_high"]); zwa = float(r["zone_width_atr"])
        atr = (zhi - zlo) / zwa if zwa > 0 else None
        if not atr: continue
        risk = max(entry0 - (zlo - 0.1 * atr), MIN_RISK_ATR * atr)
        entry = entry0 + slip * risk
        sm += max(-1.0, min(R_CAP, walk(s, ei, entry, risk, "partial2R"))); ntr += 1
    print(f"  slip {slip}R: sumR={sm:+.2f} n={ntr}")
