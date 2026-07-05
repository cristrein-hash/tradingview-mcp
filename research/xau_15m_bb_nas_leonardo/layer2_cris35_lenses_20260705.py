#!/usr/bin/env python3
"""LAYER 2 — LENTES CRIS35 REPRECIFICADAS sobre a base v3 (2026-07-05).
Resgate da memória (remap reprecificado selado 2026-07-04): sobreviventes no preço real =
higher_low+CHoCH-15M (par 2,67×) · quiet-30M · anti-iniciativa-1H (vol dry-up) — aplicadas pela
1ª vez à Layer 2, sobre a base v3 causal (contexto pré-perna + demanda + reclaim, N~1555,
recall estrito 19/33). + contexto por PREÇO (h1_trend, lab_g causal).
LEDGER (6 lentes + pares, FDR q=0,10, declarado):
  L1 hlch15  micro_hl==1 & CHoCH+ <=24 barras (known_at)
  L2 quiet30 média TR das últimas 4 barras 30M fechadas / ATR30 <= 1,0
  L3 vdry1h  vol médio últimas 4×1H fechadas / vol médio 16×1H prévias <= 0,8
  L4 h1up    h1_trend==1 (contexto por preço)
  L5 rsi4060 40<=rsi_low<=60 (banda do remap)
  L6 nasL24  nas_long_16==1 (proxy causal lab_g)
Recall ESTRITO + painel completo + null bootstrap por grupo."""
import json, bisect, hashlib, glob, random
import datetime as dt
from pathlib import Path
HERE = Path(__file__).resolve().parent
src = (HERE / "macro_leg_position_veto_20260705.py").read_text()
exec(src.split("VETOS = {")[0])
GT = HERE / "results" / "ground_truth_bottoms_20260705.json"
assert hashlib.sha256(GT.read_bytes()).hexdigest() == (HERE / "results" / "ground_truth_bottoms_20260705.sha256").read_text().split()[0]
gap = json.load(open(HERE / "results" / "layer2_gap_map_20260705.json"))
MISS_BULL = [(r["ft"], r["flo"]) for r in gap["missed_rows"] if r["reg"] == "BULL"]
MISS_ALL = [(r["ft"], r["flo"]) for r in gap["missed_rows"]]

EV2 = []
seen2 = set()
for p in sorted(glob.glob(str(HERE / "primitives" / "*.primitives.json"))):
    for e in json.load(open(p))["smc_events"]:
        key = (e["t"], e["text"], round(e["price"], 2))
        if key in seen2:
            continue
        seen2.add(key)
        c = close_at(e["t"])
        if c is None:
            continue
        tok = e["text"] + (("+" if c > e["price"] else "-") if e["text"] in ("BOS", "CHoCH") else "")
        EV2.append({"t": e["t"], "tok": tok, "price": e["price"]})
EV2.sort(key=lambda x: x["t"]); ET2 = [e["t"] for e in EV2]

def agg(step):
    out = []; cur = None
    for b in S:
        k = b["t"] - (b["t"] % step)
        if cur is None or cur["t"] != k:
            if cur:
                out.append(cur)
            cur = {"t": k, "h": b["h"], "l": b["l"], "c": b["c"], "v": float(b.get("v") or 0)}
        else:
            cur["h"] = max(cur["h"], b["h"]); cur["l"] = min(cur["l"], b["l"])
            cur["c"] = b["c"]; cur["v"] += float(b.get("v") or 0)
    return out
B30 = agg(1800); T30 = [b["t"] for b in B30]
B60 = agg(3600); T60 = [b["t"] for b in B60]

def atr_series(bars, n=14):
    trs = [bars[0]["h"] - bars[0]["l"]]
    for i in range(1, len(bars)):
        trs.append(max(bars[i]["h"] - bars[i]["l"], abs(bars[i]["h"] - bars[i - 1]["c"]),
                       abs(bars[i]["l"] - bars[i - 1]["c"])))
    a = [trs[0]]
    for i in range(1, len(bars)):
        a.append((a[-1] * (n - 1) + trs[i]) / n)
    return a, trs
A30, TR30 = atr_series(B30)
_, _ = atr_series(B60)

def quiet30(cj):
    i = bisect.bisect_right(T30, cj - 1800)   # última 30M FECHADA
    i -= 1
    if i < 20:
        return None
    return (sum(TR30[i - 3:i + 1]) / 4) / max(0.01, A30[i])

V60 = [b["v"] for b in B60]
def vdry1h(cj):
    i = bisect.bisect_right(T60, cj - 3600) - 1
    if i < 24:
        return None
    rec = sum(V60[i - 3:i + 1]) / 4
    prev = sum(V60[i - 19:i - 3]) / 16
    return rec / max(1e-9, prev)

def choch_rec24(cj):
    hi = bisect.bisect_right(ET2, cj)
    for m in range(hi - 1, -1, -1):
        if cj - EV2[m]["t"] > 24 * 900:
            break
        if EV2[m]["tok"] == "CHoCH+":
            return 1
    return 0

def preleg_ctx(u):
    i = bisect.bisect_right(TS, u["cj_t"]) - 1
    if i < 96:
        return None
    hi_k = max(range(i - 96, i + 1), key=lambda k: S[k]["h"])
    t_hi = S[hi_k]["t"]; t0 = t_hi - 384 * 900
    hi = bisect.bisect_right(ET2, t_hi)
    dirs = [EV2[m] for m in range(hi) if EV2[m]["t"] >= t0 and EV2[m]["tok"][-1] in "+-"]
    last8 = dirs[-8:]
    n_bull = sum(1 for e in last8 if e["tok"].endswith("+"))
    cd = 0
    for e in reversed(dirs):
        if e["tok"] in ("BOS-", "CHoCH-"):
            cd += 1
        else:
            break
    return {"n_bull": n_bull, "n8": len(last8), "cd": cd}

def is_cascex_member(u):
    if cascade(u["cj_t"]) < 4:
        return False
    if not (fv(u, "reclaim_atr", 0) >= 1.5 and (fv(u, "in_demand", 0) == 1 or fv(u, "dist_demand_atr", 9) <= 0.5)
            and fv(u, "h1_rsi", 99) <= 42):
        return False
    ml = macro_leg(u["cj_t"])
    return ml["vel"] < 0.10 and ml["recent_frac"] < 0.5

def dem_ok(u):
    return fv(u, "in_demand", 0) == 1 or fv(u, "dist_demand_atr", 9) <= 0.5

BASE = []
for u in U:
    if u["cj_t"] not in R3 or is_cascex_member(u):
        continue
    pc = preleg_ctx(u)
    if pc is None or not (pc["n8"] >= 6 and pc["n_bull"] >= 5 and pc["cd"] <= 1):
        continue
    if not (dem_ok(u) and fv(u, "reclaim_atr", 0) >= 1.0):
        continue
    BASE.append(u)
WEEKS = len({u["g_week"] for u in U})

def strict_recall(rows, gtlist):
    got = 0
    ts = sorted((u["cj_t"], u["g_sl"] + 0.1 * u["g_atr"], u.get("g_atr") or 5.0) for u in rows)
    T = [x[0] for x in ts]
    for ft, flo in gtlist:
        j = bisect.bisect_left(T, ft - 8 * 3600); ok = False
        while j < len(T) and T[j] <= ft + 8 * 3600:
            if abs(ts[j][1] - flo) <= ts[j][2]:
                ok = True; break
            j += 1
        got += ok
    return got

def panel(rows, tag, gtlist=MISS_BULL):
    if not rows:
        print(f"  {tag:<26} vazio"); return None
    rows = sorted(rows, key=lambda u: u["cj_t"])
    nets = [R3[u["cj_t"]]["net3"] for u in rows]
    n = len(rows); h = sum(1 for u in rows if R3[u["cj_t"]]["R3"] >= 3)
    s = sum(nets); eq = pk = dd = 0.0; mL = cl = 0
    for x in nets:
        eq += x; pk = max(pk, eq); dd = min(dd, eq - pk)
        if x <= 0: cl += 1; mL = max(mL, cl)
        else: cl = 0
    yr = {y: round(sum(nets[i] for i, u in enumerate(rows) if u["yr"] == y), 1) for y in (2024, 2025, 2026)}
    print(f"  {tag:<26} N{n:>4} hit3R {100*h/n:>5.1f}% sumR {s:>+7.1f} DD {dd:>6.1f} stk-{mL} "
          f"| {n/WEEKS:.2f}/sem | recall {strict_recall(rows, gtlist)}/{len(gtlist)} | {yr}")
    return {"n": n, "hit": round(h / n, 3), "sum": round(s, 1), "stk": mL,
            "recall": strict_recall(rows, gtlist)}

for u in BASE:
    u["_q30"] = quiet30(u["cj_t"]); u["_vd"] = vdry1h(u["cj_t"]); u["_ch"] = choch_rec24(u["cj_t"])
LENS = {
    "L1_hlch15": lambda u: fv(u, "micro_hl", 0) == 1 and u["_ch"] == 1,
    "L2_quiet30": lambda u: u["_q30"] is not None and u["_q30"] <= 1.0,
    "L3_vdry1h": lambda u: u["_vd"] is not None and u["_vd"] <= 0.8,
    "L4_h1up": lambda u: fv(u, "h1_trend", 0) == 1,
    "L5_rsi4060": lambda u: 40 <= fv(u, "rsi_low", -1) <= 60,
    "L6_nasL24": lambda u: fv(u, "nas_long_16", 0) == 1,
}
pb = panel(BASE, "BASE v3 (ctx+confl)")
H0 = [1 if R3[u["cj_t"]]["R3"] >= 3 else 0 for u in BASE]
random.seed(43)
groups = {}
K = list(LENS)
for nm in K:
    groups[frozenset([nm])] = [u for u in BASE if LENS[nm](u)]
for i in range(len(K)):
    for j in range(i + 1, len(K)):
        groups[frozenset([K[i], K[j]])] = [u for u in BASE if LENS[K[i]](u) and LENS[K[j]](u)]
groups = {fs: g for fs, g in groups.items() if len(g) >= 30}
stats = []
for fs, g in groups.items():
    hs = [1 if R3[u["cj_t"]]["R3"] >= 3 else 0 for u in g]
    obs = sum(hs) / len(hs)
    ge = sum(1 for _ in range(2000) if sum(random.sample(H0, len(g))) / len(g) >= obs)
    stats.append((fs, len(g), obs, sum(R3[u["cj_t"]]["net3"] for u in g),
                  strict_recall(g, MISS_BULL), ge / 2000))
m = len(stats)
bh = sorted(stats, key=lambda x: x[5]); fdr = set()
for rank, st_ in enumerate(bh, 1):
    if st_[5] <= 0.10 * rank / m:
        fdr.add(st_[0])
stats.sort(key=lambda x: -x[2])
print(f"\n  lentes CRIS35 sobre a base (FDR q=0,10 / {m} grupos):")
print(f"  {'grupo':<26} {'N':>5} {'hit%':>6} {'NET3':>8} {'recall':>6} {'P':>7}")
for fs, n, obs, net, rec, p in stats[:14]:
    print(f"  {'&'.join(sorted(fs)):<26} {n:>5} {100*obs:>5.1f}% {net:>+8.1f} {rec:>3}/33 {p:>7.4f}"
          f"{'  <<< FDR' if fs in fdr else ''}")
json.dump({"base": pb, "top": [{"g": "&".join(sorted(fs)), "n": n, "hit": round(o, 3),
                                "net3": round(float(net), 1), "recall": rec, "p": p}
                               for fs, n, o, net, rec, p in stats[:20]]},
          open(HERE / "results" / "layer2_cris35_lenses_20260705.json", "w"), indent=1)
print("OK → results/layer2_cris35_lenses_20260705.json")
