#!/usr/bin/env python3
"""LAYER 2 — IMPULSE-DIP: ranking de potencial + engine round 1 (2026-07-05).
Leitura dos 17 prints: arquétipo dominante dos fundos perdidos = dip rápido/raso que varre low
local durante IMPULSO forte, V-reclaim; sempre perto de demanda; sem cascata; RSI-1H nem sempre
oversold. O lucro está na frequência + risco pequeno.

PARTE 1 — RANKING DE POTENCIAL dos 56 fundos GT perdidos: R_max let-run (480b, sem cap) a partir
da entrada causal (reclaim flush+0,3ATR) + classe (BULL-impulso / RANGE / BEAR-complexo) → onde
está o dinheiro por classe (oracle-condicional, declarado).

PARTE 2 — ENGINE IMPULSE-DIP round 1 (DESIGN CONGELADO, features dos prints):
  UNIVERSO: candidatos fractais (lab_g) com contexto de IMPULSO: perna prévia forte
    I1 ganho da perna: high96b − low192b >= 8 ATR e o high96 foi feito nas últimas 48b (HH recente)
  GATILHO (forma do dip nos prints):
    I2 dip raso: profundidade high48→flush <= 3 ATR
    I3 dip rápido: <= 12 barras do high local ao flush
    I4 V-reclaim: reclaim_atr >= 1,5 (já no candidato = virada com força)
    I5 sweep: swept_prior_low == 1
    I6 demanda: in_demand OU dist_demand <= 0,5 (52/56 dos perdidos)
  BASE = I1&I2&I4&I6 (núcleo declarado); I3/I5 = lentes de refino (+ pares), FDR q=0,10.
  Exclui membros CASCEX (layer separada). Painel completo + null bootstrap + recall GT-perdidos.
  Convenção exit: 3R first-touch 480b capado (canónica) — via R3 quando o candidato existe."""
import json, bisect, random, hashlib
import datetime as dt
from pathlib import Path
HERE = Path(__file__).resolve().parent
src = (HERE / "macro_leg_position_veto_20260705.py").read_text()
exec(src.split("VETOS = {")[0])   # U, R3, S, TS, CTX, POCKET, _ml, cascade, fv, macro_leg
GT = HERE / "results" / "ground_truth_bottoms_20260705.json"
assert hashlib.sha256(GT.read_bytes()).hexdigest() == (HERE / "results" / "ground_truth_bottoms_20260705.sha256").read_text().split()[0]
gap = json.load(open(HERE / "results" / "layer2_gap_map_20260705.json"))
MISSED = gap["missed_rows"]

# ---- PARTE 1: ranking de potencial (R_max let-run) por classe ----
def rmax_letrun(ft, flo):
    i = bisect.bisect_right(TS, ft) - 1
    atr = S[i].get("atr") or 5.0
    for k in range(i, min(len(S), i + 33)):
        if S[k]["c"] >= flo + 0.3 * atr:
            e = S[k]["c"]; sl = flo - 0.1 * atr; risk = e - sl
            if risk <= 0:
                return None
            hi = e
            for m in range(k + 1, min(len(S), k + 481)):
                if S[m]["l"] <= sl:
                    break
                hi = max(hi, S[m]["h"])
            return (hi - e) / risk
    return None

classes = {}
for r in MISSED:
    reg = r["reg"]
    cls = "BULL-impulso" if reg == "BULL" else ("BEAR-complexo" if reg == "BEAR" else "RANGE")
    rm = rmax_letrun(r["ft"], r["flo"])
    classes.setdefault(cls, []).append(rm if rm is not None else 0)
print("PARTE 1 — POTENCIAL POR CLASSE (R_max let-run 480b, oracle-condicional declarado):")
for cls, v in sorted(classes.items(), key=lambda kv: -sum(kv[1])):
    import statistics as st
    print(f"  {cls:<14} N{len(v):>2} · R_max mediano {st.median(v):>5.1f} · soma {sum(v):>+7.1f} · "
          f">=3R: {sum(1 for x in v if x>=3)}/{len(v)} · >=6R: {sum(1 for x in v if x>=6)}/{len(v)}")

# ---- PARTE 2: engine IMPULSE-DIP ----
def is_cascex_member(u):
    if cascade(u["cj_t"]) < 4:
        return False
    if not (fv(u, "reclaim_atr", 0) >= 1.5 and (fv(u, "in_demand", 0) == 1 or fv(u, "dist_demand_atr", 9) <= 0.5)
            and fv(u, "h1_rsi", 99) <= 42):
        return False
    ml = macro_leg(u["cj_t"])
    return ml["vel"] < 0.10 and ml["recent_frac"] < 0.5

def impulse_feats(u):
    cj = u["cj_t"]
    i = bisect.bisect_right(TS, cj) - 1
    if i < 192:
        return None
    atr = S[i].get("atr") or 5.0
    hi96_k = max(range(i - 96, i + 1), key=lambda k: S[k]["h"])
    hi96 = S[hi96_k]["h"]
    lo192 = min(S[k]["l"] for k in range(i - 192, i + 1))
    flo = u["g_sl"] + 0.1 * u["g_atr"]
    hi48_k = max(range(i - 48, i + 1), key=lambda k: S[k]["h"])
    # flush bar ~ fractal t
    fi = bisect.bisect_right(TS, u["t"]) - 1
    return {"leg_gain": (hi96 - lo192) / atr,
            "hh_recent": int(i - hi96_k <= 48),
            "dip_depth": (S[hi48_k]["h"] - flo) / atr,
            "dip_bars": max(0, fi - hi48_k)}

L2U = []
for u in U:
    if u["cj_t"] not in R3 or is_cascex_member(u):
        continue
    f = impulse_feats(u)
    if f is None:
        continue
    u["_if"] = f
    L2U.append(u)

BASE = [u for u in L2U if u["_if"]["leg_gain"] >= 8 and u["_if"]["hh_recent"] == 1
        and u["_if"]["dip_depth"] <= 3.0
        and fv(u, "reclaim_atr", 0) >= 1.5
        and (fv(u, "in_demand", 0) == 1 or fv(u, "dist_demand_atr", 9) <= 0.5)]
WEEKS = len({u["g_week"] for u in U})
MISSED_FT = sorted(r["ft"] for r in MISSED)

def recall_of(rows):
    ts = sorted(u["cj_t"] for u in rows); r = 0
    for ft in MISSED_FT:
        j = bisect.bisect_left(ts, ft - 8 * 3600)
        if j < len(ts) and ts[j] <= ft + 8 * 3600:
            r += 1
    return r

def full_panel(rows, tag):
    rows = sorted(rows, key=lambda u: u["cj_t"])
    nets = [R3[u["cj_t"]]["net3"] for u in rows]
    n = len(rows); h = sum(1 for u in rows if R3[u["cj_t"]]["R3"] >= 3)
    w = sum(1 for x in nets if x > 0); s = sum(nets)
    eq = pk = dd = 0.0; mL = cl = 0
    for x in nets:
        eq += x; pk = max(pk, eq); dd = min(dd, eq - pk)
        if x <= 0: cl += 1; mL = max(mL, cl)
        else: cl = 0
    yr = {y: round(sum(nets[i] for i, u in enumerate(rows) if u["yr"] == y), 1) for y in (2024, 2025, 2026)}
    print(f"  {tag:<34} N{n:>4} hit3R {100*h/n:>5.1f}% sumR {s:>+7.1f} avgR {s/n:>+.3f} DD {dd:>6.1f} "
          f"stk-{mL} | {n/WEEKS:.2f}/sem | recall {recall_of(rows)}/56 | {yr}")
    return {"n": n, "hit": h / n, "sum": s, "stk": mL}

print("\nPARTE 2 — IMPULSE-DIP round 1:")
b = full_panel(BASE, "BASE I1&I2&I4&I6 (núcleo)")
H0 = [1 if R3[u["cj_t"]]["R3"] >= 3 else 0 for u in BASE]
base_hit = sum(H0) / len(H0) if H0 else 0
LENS = {
    "I3_dip<=12b": lambda u: u["_if"]["dip_bars"] <= 12,
    "I5_swept": lambda u: fv(u, "swept_prior_low", 0) == 1,
    "R_rsi1h<=55": lambda u: fv(u, "h1_rsi", 99) <= 55,
    "R_legdeep": lambda u: fv(u, "pullback_depth", 0) >= 0.5,
    "R_bull": lambda u: u.get("g_v5h") == "BULL",
    "R_casc>=1": lambda u: cascade(u["cj_t"]) >= 1,
}
groups = {}
K = list(LENS)
for nm in K:
    groups[frozenset([nm])] = [u for u in BASE if LENS[nm](u)]
for i in range(len(K)):
    for j in range(i + 1, len(K)):
        groups[frozenset([K[i], K[j]])] = [u for u in BASE if LENS[K[i]](u) and LENS[K[j]](u)]
groups = {fs: g for fs, g in groups.items() if len(g) >= 40}
random.seed(23)
stats = []
for fs, g in groups.items():
    hs = [1 if R3[u["cj_t"]]["R3"] >= 3 else 0 for u in g]
    obs = sum(hs) / len(hs)
    ge = 0
    for _ in range(2000):
        if sum(random.sample(H0, len(g))) / len(g) >= obs:
            ge += 1
    stats.append((fs, len(g), obs, sum(R3[u["cj_t"]]["net3"] for u in g), recall_of(g), ge / 2000))
m = len(stats); stats.sort(key=lambda x: x[5])
fdr = {fs for rank, (fs, *_ , p) in enumerate([(s[0],)+s[1:] for s in stats], 1)
       for p in [stats[rank-1][5]] if p <= 0.10 * rank / m}
stats.sort(key=lambda x: -x[2])
print(f"\n  lentes (FDR q=0,10 sobre {m} grupos):")
print(f"  {'grupo':<28} {'N':>5} {'hit%':>6} {'NET3':>8} {'recall':>6} {'P':>7}")
for fs, n, obs, net, rec, p in stats[:12]:
    print(f"  {'&'.join(sorted(fs)):<28} {n:>5} {100*obs:>5.1f}% {net:>+8.1f} {rec:>3}/56 {p:>7.4f}"
          f"{'  <<< FDR' if fs in fdr else ''}")
json.dump({"base": {"n": b["n"], "hit": round(b["hit"], 3), "sum": round(b["sum"], 1)},
           "top": [{"g": "&".join(sorted(fs)), "n": n, "hit": round(o, 3), "net3": round(float(net), 1),
                    "recall": rec, "p": p} for fs, n, o, net, rec, p in stats[:15]]},
          open(HERE / "results" / "layer2_impulsedip_20260705.json", "w"), indent=1)
print("OK → results/layer2_impulsedip_20260705.json")
