#!/usr/bin/env python3
"""CONJUNÇÕES SEQUENCIAIS NÍTIDAS (2026-07-05, Cris: afiar não afrouxar; expandir N mantendo streak<=4).
Em vez de soft-score (diluiu), defino 4 conjunções APERTADAS, cada uma = footprint distinto de fundo
genuíno na leitura sequencial (multi-barra), e faço a UNIÃO das que mantêm streak<=4 e hit>>25%:
  C0 RWS (ref)   : buy_recent>=2 · rsi_above|supply · anti-burst · anti-beardiv
  C1 ABSORÇÃO    : sell M/L absorvido>=2 (vendedor preso) · reclaim rápido (vel>=0.5) · buy4>=1 · anti-beardiv
  C2 INSTITUCIONAL: large_buy_win8 (L) · reclaim_atr>=1.5 · (rsi_above|nas_long) · anti-beardiv
  C3 ACUM-FORTE  : buy4>=4 (acumulação pesada recente) · anti-burst-fake · anti-beardiv
  C4 NAS+ACUM    : nas_long recente · buy4>=2 · reclaim>=1.5 · anti-beardiv
Ledger = 5 conjunções declaradas. União só das streak<=4. Walk-forward por ano em cada. Universo selado."""
import json, glob, bisect
from pathlib import Path
HERE = Path(__file__).resolve().parent
U = [json.loads(l) for l in open(HERE / "results" / "lab_g_candidates.jsonl")]
R3 = {json.loads(l)["cj_t"]: json.loads(l) for l in open(HERE / "results" / "r3_target_universe_20260704.jsonl")}
def fv(r, k, d=0):
    v = r.get(k); return v if isinstance(v, (int, float)) and not isinstance(v, bool) else d
WEEKS = len({r["g_week"] for r in U})
series = {}; nas = []
for p in sorted(glob.glob(str(HERE / "primitives" / "*.primitives.json"))):
    d = json.load(open(p))
    for b in d["series"]: series.setdefault(b["t"], b)
    nas += [e for e in d["nas_events"] if e.get("t")]
S = sorted(series.values(), key=lambda b: b["t"]); TS = [b["t"] for b in S]; Np = len(S)
RSI = [b.get("rsi") for b in S]; RSIMA = [None] * Np
for i in range(Np):
    w = [RSI[j] for j in range(max(0, i - 13), i + 1) if RSI[j] is not None]
    RSIMA[i] = sum(w) / len(w) if w else None
BUB = sorted([json.loads(l) for p in glob.glob(str(HERE / "bubbles" / "*.bubbles.jsonl")) for l in open(p)],
             key=lambda x: (x.get("known_at") or x["t"]))
BUBK = [(x.get("known_at") or x["t"]) for x in BUB]
nas.sort(key=lambda e: e["t"]); NAST = [e["t"] for e in nas]
wgt = {"S": 1, "M": 2, "L": 3}
def bub(t0, wlo, whi):
    hi = bisect.bisect_right(BUBK, t0)
    return [BUB[i] for i in range(hi) if t0 - whi * 900 <= BUB[i]["t"] <= t0 - wlo * 900]
def feats(cj_t):
    i = bisect.bisect_right(TS, cj_t) - 1
    if i < 40: return None
    atr = S[i].get("atr") or 1.0; close = S[i]["c"]
    w4 = bub(cj_t, 0, 4); w8 = bub(cj_t, 0, 8); old = bub(cj_t, 5, 10)
    buy4 = sum(wgt[x["size"]] for x in w4 if x["side"] == "BUY")
    burst = buy4 - sum(wgt[x["size"]] for x in old if x["side"] == "BUY")
    large8 = int(any(x["side"] == "BUY" and x["size"] == "L" for x in w8))
    absorb = sum(1 for x in w8 if x["side"] == "SELL" and x["size"] in ("M", "L") and x.get("c") is not None and close > x["c"])
    lo_i = min(range(max(0, i - 12), i + 1), key=lambda k: S[k]["l"])
    vel = (close - S[lo_i]["l"]) / atr / max(1, i - lo_i)
    rsi_above = int(RSI[i] is not None and RSIMA[i] is not None and RSI[i] > RSIMA[i])
    bd = 0
    for k in range(i - 20, i - 2):
        if k < 3: continue
        if S[k]["h"] == max(x["h"] for x in S[k - 2:k + 3]):
            pv = [j for j in range(k - 12, k - 2) if S[j]["h"] == max(x["h"] for x in S[max(0, j - 2):j + 3])]
            if pv and RSI[k] is not None and RSI[pv[-1]] is not None and S[k]["h"] > S[pv[-1]]["h"] and RSI[k] < RSI[pv[-1]]: bd += 1
    j = bisect.bisect_right(NAST, cj_t) - 1
    nas_short = int(j >= 0 and nas[j]["dir"] == "SHORT" and (cj_t - nas[j]["t"]) // 900 <= 4)
    nas_long = int(j >= 0 and nas[j]["dir"] == "LONG" and (cj_t - nas[j]["t"]) // 900 <= 24)
    return dict(buy4=buy4, burst=burst, large8=large8, absorb=absorb, vel=vel, rsi_above=rsi_above,
                bd=bd, nas_short=nas_short, nas_long=nas_long)
F = {r["cj_t"]: feats(r["cj_t"]) for r in U}
def ok(r): return F.get(r["cj_t"]) is not None
NB = [r for r in U if r["g_v5h"] != "BEAR" and r["g_knife"] == 0 and ok(r)]
def anti(f): return f["bd"] < 2 and not (f["burst"] >= 3 and f["large8"] == 0 and f["nas_short"] == 0)
CONJ = {
 "C0_RWS": lambda r: (lambda f: f["buy4"] >= 2 and (f["rsi_above"] == 1 or fv(r, "n_supply_overhead", 99) > 20) and anti(f))(F[r["cj_t"]]),
 "C1_ABSORB": lambda r: (lambda f: f["absorb"] >= 2 and f["vel"] >= 0.5 and f["buy4"] >= 1 and anti(f))(F[r["cj_t"]]),
 "C2_INSTIT": lambda r: (lambda f: f["large8"] == 1 and fv(r, "reclaim_atr", 0) >= 1.5 and (f["rsi_above"] == 1 or f["nas_long"] == 1) and anti(f))(F[r["cj_t"]]),
 "C3_ACUMF": lambda r: (lambda f: f["buy4"] >= 4 and anti(f))(F[r["cj_t"]]),
 "C4_NASACUM": lambda r: (lambda f: f["nas_long"] == 1 and f["buy4"] >= 2 and fv(r, "reclaim_atr", 0) >= 1.5 and anti(f))(F[r["cj_t"]]),
}
def panel(rows, tag, show=True):
    n = len(rows)
    if not n:
        if show: print(f"  {tag:<24} vazio")
        return None
    rs = sorted(rows, key=lambda r: r["cj_t"]); nets = [R3[r["cj_t"]]["net3"] for r in rs]
    h = sum(1 for r in rs if R3[r["cj_t"]]["R3"] >= 3)
    eq = pk = dd = 0.0; mL = cl = 0
    for x in nets:
        eq += x; pk = max(pk, eq); dd = min(dd, eq - pk)
        if x <= 0: cl += 1; mL = max(mL, cl)
        else: cl = 0
    yr = {y: round(sum(nets[k] for k, r in enumerate(rs) if r["yr"] == y), 1) for y in (2024, 2025, 2026)}
    ap = all(v > 0 for v in yr.values())
    if show:
        print(f"  {tag:<24} N{n:>4} hit3R {100*h/n:>5.1f}% NET {sum(nets):>7.1f} DD {dd:>6.1f} stk-{mL:>2} "
              f"| {n/WEEKS:.2f}/sem | {yr} {'✓' if ap else ''}")
    return {"n": n, "hit": h / n, "stk": mL, "net": sum(nets), "yr": yr, "ap": ap, "members": [r["cj_t"] for r in rs]}
print("=" * 104)
print("CONJUNÇÕES SEQUENCIAIS NÍTIDAS — cada footprint, streak<=4 = candidata à união")
print("=" * 104)
res = {}
for nm, fn in CONJ.items():
    s = panel([r for r in NB if fn(r)], nm)
    if s: res[nm] = s
# UNIÃO das conjunções com streak<=4 e hit>=0.38 (qualidade preservada)
winners = [nm for nm, s in res.items() if s["stk"] <= 4 and s["hit"] >= 0.38]
print(f"\nCONJUNÇÕES QUE PASSAM (streak<=4 & hit>=38%): {winners}")
if winners:
    union = {}
    for nm in winners:
        for cj in res[nm]["members"]: union[cj] = next(r for r in NB if r["cj_t"] == cj)
    UN = list(union.values())
    su = panel(UN, "UNIÃO (limpa)")
    # overlaps entre winners
    print("  overlaps:", {f"{a}∩{b}": len(set(res[a]['members']) & set(res[b]['members']))
                          for i, a in enumerate(winners) for b in winners[i+1:]})
    json.dump({"conjunctions": {nm: {k: s[k] for k in ("n", "hit", "stk", "net", "yr", "ap")} for nm, s in res.items()},
               "winners": winners, "union": {k: su[k] for k in ("n", "hit", "stk", "net", "yr")},
               "union_members": [r["cj_t"] for r in UN], "per_week": su["n"] / WEEKS},
              open(HERE / "results" / "sharp_conjunctions_engine_20260705.json", "w"), indent=1)
print("OK → results/sharp_conjunctions_engine_20260705.json")
