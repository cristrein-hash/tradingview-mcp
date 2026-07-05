#!/usr/bin/env python3
"""LAYER 2 — IMPULSE-DIP v3 (ancora HH 96b, mudanca unica declarada): perna como IMPULSO, dip PROPORCIONAL (2026-07-05).
Round 1 invertia o arquétipo (media caixa, não impulso; dip absoluto ≤3ATR quando o real é 3-10ATR
proporcional). v2, DESIGN CONGELADO antes de rodar (thresholds da matriz de recall do DA + espelho
do veto macro-leg validado — vel 0,10 ATR/b como marca de perna genuína):

PERNA PRÉVIA (up-leg causal): hi48 = argmax high [i-48..i]; lo = argmin low [hi-96..hi]:
  leg_gain  = (hi−lo)/ATR          leg_vel = gain/barras (IMPULSO; espelho do veto)
  leg_eff   = gain / Σ|Δclose|     leg_retr = nº retraces >1ATR dentro da up-leg
DIP (forma real dos prints): dip_depth=(hi−flush)/ATR · dip_ratio=depth/gain · dip_bars=flush−hi_k
BASE v2 (congelada): leg_gain>=5 & leg_vel>=0.10 & dip_ratio em [0.15,0.65] & dip_bars<=24
  & reclaim_atr>=1.0 & demanda & ex-CASCEX.
LENTES (declaradas; singles+pares; FDR q=0,10): dip_speed>=0.4ATR/b · swept · rsi1h<=55 ·
  leg_eff>=0.3 · leg_retr<=1 · casc>=1.
MÉTRICAS: painel completo + recall dos 56 GT perdidos + null bootstrap vs universo L2U (27,4%).
GATE declarado: recall>=60% E hit>universo E stk/DD reportados sem seleção."""
import json, bisect, random, hashlib
import datetime as dt
from pathlib import Path
HERE = Path(__file__).resolve().parent
src = (HERE / "macro_leg_position_veto_20260705.py").read_text()
exec(src.split("VETOS = {")[0])
GT = HERE / "results" / "ground_truth_bottoms_20260705.json"
assert hashlib.sha256(GT.read_bytes()).hexdigest() == (HERE / "results" / "ground_truth_bottoms_20260705.sha256").read_text().split()[0]
gap = json.load(open(HERE / "results" / "layer2_gap_map_20260705.json"))
MISSED_FT = sorted(r["ft"] for r in gap["missed_rows"])

def is_cascex_member(u):
    if cascade(u["cj_t"]) < 4:
        return False
    if not (fv(u, "reclaim_atr", 0) >= 1.5 and (fv(u, "in_demand", 0) == 1 or fv(u, "dist_demand_atr", 9) <= 0.5)
            and fv(u, "h1_rsi", 99) <= 42):
        return False
    ml = macro_leg(u["cj_t"])
    return ml["vel"] < 0.10 and ml["recent_frac"] < 0.5

def upleg_feats(u):
    cj = u["cj_t"]; i = bisect.bisect_right(TS, cj) - 1
    if i < 192:
        return None
    atr = S[i].get("atr") or 5.0
    hi_k = max(range(i - 96, i + 1), key=lambda k: S[k]["h"]); hi = S[hi_k]["h"]
    lo_k = min(range(max(0, hi_k - 144), hi_k + 1), key=lambda k: S[k]["l"]); lo = S[lo_k]["l"]
    bars = max(1, hi_k - lo_k)
    gain = (hi - lo) / atr
    path = sum(abs(S[k]["c"] - S[k - 1]["c"]) for k in range(lo_k + 1, hi_k + 1)) / atr
    eff = gain / max(0.001, path)
    # retraces >1ATR dentro da up-leg
    nr = 0; run_hi = S[lo_k]["h"]; armed = True
    for k in range(lo_k, hi_k + 1):
        run_hi = max(run_hi, S[k]["h"])
        if (run_hi - S[k]["l"]) / atr >= 1.0 and armed:
            nr += 1; armed = False
        if S[k]["h"] >= run_hi:
            armed = True
    fi = bisect.bisect_right(TS, u["t"]) - 1
    flo = u["g_sl"] + 0.1 * u["g_atr"]
    depth = (hi - flo) / atr
    return {"gain": gain, "vel": gain / bars, "eff": eff, "retr": nr,
            "depth": depth, "ratio": depth / max(0.001, gain), "dip_bars": max(0, fi - hi_k),
            "dip_speed": depth / max(1, fi - hi_k)}

L2U = []
for u in U:
    if u["cj_t"] not in R3 or is_cascex_member(u):
        continue
    f = upleg_feats(u)
    if f is None:
        continue
    u["_il"] = f
    L2U.append(u)
BASE = [u for u in L2U if u["_il"]["gain"] >= 5 and u["_il"]["vel"] >= 0.10
        and 0.15 <= u["_il"]["ratio"] <= 0.65 and u["_il"]["dip_bars"] <= 24
        and fv(u, "reclaim_atr", 0) >= 1.0
        and (fv(u, "in_demand", 0) == 1 or fv(u, "dist_demand_atr", 9) <= 0.5)]
WEEKS = len({u["g_week"] for u in U})

def recall_of(rows):
    ts = sorted(u["cj_t"] for u in rows); r = 0
    for ft in MISSED_FT:
        j = bisect.bisect_left(ts, ft - 8 * 3600)
        if j < len(ts) and ts[j] <= ft + 8 * 3600:
            r += 1
    return r

def full_panel(rows, tag):
    if not rows:
        print(f"  {tag:<30} vazio"); return None
    rows = sorted(rows, key=lambda u: u["cj_t"])
    nets = [R3[u["cj_t"]]["net3"] for u in rows]
    n = len(rows); h = sum(1 for u in rows if R3[u["cj_t"]]["R3"] >= 3)
    s = sum(nets); eq = pk = dd = 0.0; mL = cl = 0
    for x in nets:
        eq += x; pk = max(pk, eq); dd = min(dd, eq - pk)
        if x <= 0: cl += 1; mL = max(mL, cl)
        else: cl = 0
    yr = {y: round(sum(nets[i] for i, u in enumerate(rows) if u["yr"] == y), 1) for y in (2024, 2025, 2026)}
    print(f"  {tag:<30} N{n:>4} hit3R {100*h/n:>5.1f}% sumR {s:>+7.1f} avgR {s/n:>+.3f} DD {dd:>6.1f} "
          f"stk-{mL} | {n/WEEKS:.2f}/sem | recall {recall_of(rows)}/56 | {yr}")
    return {"n": n, "hit": h / n, "sum": round(s, 1), "dd": round(dd, 1), "stk": mL, "recall": recall_of(rows)}

uni_hit = sum(1 for u in L2U if R3[u["cj_t"]]["R3"] >= 3) / len(L2U)
print(f"universo L2U: N{len(L2U)} hit {100*uni_hit:.1f}% · recall {recall_of(L2U)}/56")
b = full_panel(BASE, "BASE v2 (impulso+proporção)")
H0 = [1 if R3[u["cj_t"]]["R3"] >= 3 else 0 for u in BASE]
LENS = {
    "dip_speed>=0.4": lambda u: u["_il"]["dip_speed"] >= 0.4,
    "swept": lambda u: fv(u, "swept_prior_low", 0) == 1,
    "rsi1h<=55": lambda u: fv(u, "h1_rsi", 99) <= 55,
    "eff>=0.3": lambda u: u["_il"]["eff"] >= 0.3,
    "retr<=1": lambda u: u["_il"]["retr"] <= 1,
    "casc>=1": lambda u: cascade(u["cj_t"]) >= 1,
}
groups = {}
K = list(LENS)
for nm in K:
    groups[frozenset([nm])] = [u for u in BASE if LENS[nm](u)]
for i in range(len(K)):
    for j in range(i + 1, len(K)):
        groups[frozenset([K[i], K[j]])] = [u for u in BASE if LENS[K[i]](u) and LENS[K[j]](u)]
groups = {fs: g for fs, g in groups.items() if len(g) >= 30}
random.seed(29)
stats = []
for fs, g in groups.items():
    hs = [1 if R3[u["cj_t"]]["R3"] >= 3 else 0 for u in g]
    obs = sum(hs) / len(hs)
    ge = sum(1 for _ in range(2000) if sum(random.sample(H0, len(g))) / len(g) >= obs)
    stats.append((fs, len(g), obs, sum(R3[u["cj_t"]]["net3"] for u in g), recall_of(g), ge / 2000))
m = len(stats)
bh = sorted(stats, key=lambda x: x[5])
fdr = set()
for rank, st_ in enumerate(bh, 1):
    if st_[5] <= 0.10 * rank / m:
        fdr.add(st_[0])
stats.sort(key=lambda x: -x[2])
print(f"\n  lentes (FDR q=0,10 / {m} grupos):")
print(f"  {'grupo':<30} {'N':>5} {'hit%':>6} {'NET3':>8} {'recall':>6} {'P':>7}")
for fs, n, obs, net, rec, p in stats[:12]:
    print(f"  {'&'.join(sorted(fs)):<30} {n:>5} {100*obs:>5.1f}% {net:>+8.1f} {rec:>3}/56 {p:>7.4f}"
          f"{'  <<< FDR' if fs in fdr else ''}")
json.dump({"universe": {"n": len(L2U), "hit": round(uni_hit, 3)},
           "base": b, "top": [{"g": "&".join(sorted(fs)), "n": n, "hit": round(o, 3),
                               "net3": round(float(net), 1), "recall": rec, "p": p}
                              for fs, n, o, net, rec, p in stats[:15]]},
          open(HERE / "results" / "layer2_impulsedip_v3_20260705.json", "w"), indent=1)
print("OK → results/layer2_impulsedip_v3_20260705.json")
