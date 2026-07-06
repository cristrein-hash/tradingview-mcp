#!/usr/bin/env python3
"""AFINAÇÃO DO RECLAIM POR MICRO-FORMA (2026-07-06, ordem Cris: features de entry-bar como filtro).
P0 (1º reclaim/evento) = edge causal (hit 31,9%, P=0,03, anos+). Objetivo: subir WR/baixar streak
distinguindo reclaim BOM de FALSO com micro-forma da barra de entrada. Features de afinação (causais,
só a barra do reclaim e anteriores):
  rec_strength   (close − high[-1])/atr — força do rompimento
  prev_wick      pavio inferior da barra ANTERIOR /atr — rejeição no fundo antes de virar
  rec_vol        volume da barra / média 20 — confirmação
  dist_to_low    (close − low_evento)/atr — bom preço (perto) vs tarde (longe)
  two_up         2 closes de alta consecutivos (momentum de virada)
  choch_at_rec   CHoCH+ conhecido na barra do reclaim (quebra de estrutura)
  body_frac      corpo/range da barra
FASE A: hit3R por cada feature (quartis) nos 376 reclaims → quais afinam. FASE B: reclaim-afinado
(convergência das que sobem WR) 1/evento + null + streak + recall + sub-ano.
SANITY_PROBE: micro-forma causal (barra do cj e anteriores) · 1/evento · null seed 811 · recall
círculo · não muda exit (3R fixo, mandato Cris)."""
import json, bisect, hashlib, random, glob
from pathlib import Path
HERE = Path(__file__).resolve().parent
exec((HERE / "macro_leg_position_veto_20260705.py").read_text().split("VETOS = {")[0])
GTF = HERE / "results" / "ground_truth_bottoms_20260705.json"
assert hashlib.sha256(GTF.read_bytes()).hexdigest() == (HERE / "results" / "ground_truth_bottoms_20260705.sha256").read_text().split()[0]
GT = json.load(open(GTF))
N = len(S); ATR = [b.get("atr") or 5.0 for b in S]
HI = [b["h"] for b in S]; LO = [b["l"] for b in S]; CL = [b["c"] for b in S]; OP = [b.get("o", b["c"]) for b in S]; VOL = [float(b.get("v") or 0) for b in S]
# SMC events p/ CHoCH+ (do módulo: events/ET globais)
UNIV = sorted([u for u in U if u["cj_t"] in R3], key=lambda u: u["cj_t"])
UT = [u["cj_t"] for u in UNIV]; WK = len({u["g_week"] for u in U})
for u in UNIV:
    u["_flo"] = u["g_sl"] + 0.1 * (u.get("g_atr") or 5.0); u["_a"] = u.get("g_atr") or 5.0; u["_circ"] = set()
for gi, g in enumerate(GT):
    j = bisect.bisect_left(UT, g["flush_t"] - 8 * 3600)
    while j < len(UNIV) and UT[j] <= g["flush_t"] + 8 * 3600:
        u = UNIV[j]; d = u["_flo"] - g["flush_low"]
        if -3 * u["_a"] <= d <= 1 * u["_a"]: u["_circ"].add(gi)
        j += 1
EV = []; cur = []
for u in UNIV:
    if cur and u["cj_t"] - cur[-1]["cj_t"] <= 48 * 3600 and abs(u["_flo"] - cur[-1]["_flo"]) <= 3 * u["_a"]:
        cur.append(u)
    else:
        if cur: EV.append(cur)
        cur = [u]
if cur: EV.append(cur)

def annotate(ev):
    min_flo = 1e18; prev_close = None; up = 0
    for pos, u in enumerate(ev, 1):
        ci = bisect.bisect_right(TS, u["cj_t"]) - 1; a = u["_a"]
        prevmin = min_flo
        u["_post_low"] = int(pos > 1 and u["_flo"] > prevmin + 0.05 * a)
        min_flo = min(min_flo, u["_flo"])
        rng = max(1e-9, HI[ci] - LO[ci])
        u["_reclaim"] = int(ci >= 1 and CL[ci] > HI[ci - 1])
        u["_body_up"] = int(CL[ci] > OP[ci]); u["_cir"] = (CL[ci] - LO[ci]) / rng
        if prev_close is not None: up = up + 1 if CL[ci] > prev_close else 0
        prev_close = CL[ci]
        # afinação
        u["_rec_strength"] = (CL[ci] - HI[ci - 1]) / a if ci >= 1 else 0
        u["_prev_wick"] = (min(OP[ci - 1], CL[ci - 1]) - LO[ci - 1]) / a if ci >= 1 else 0
        v20 = VOL[max(0, ci - 20):ci]; u["_rec_vol"] = VOL[ci] / (sum(v20) / len(v20)) if v20 and VOL[ci] else 1.0
        u["_dist_to_low"] = (CL[ci] - min_flo) / a
        u["_two_up"] = int(up >= 2)
        u["_body_frac"] = abs(CL[ci] - OP[ci]) / rng
        hi_e = bisect.bisect_right(ET, u["cj_t"]); ch = 0
        for m in range(hi_e - 1, -1, -1):
            if u["cj_t"] - events[m]["t"] > 4 * 900: break
            if events[m]["tok"] == "CHoCH+": ch = 1; break
        u["_choch_at_rec"] = ch
for ev in EV: annotate(ev)

def base_reclaim(u):
    return u["_post_low"] == 1 and u["_reclaim"] == 1 and u["_body_up"] == 1 and u["_cir"] >= 0.5
RECL = [u for ev in EV for u in ev if base_reclaim(u)]
# 1/evento (1º reclaim) p/ os painéis
def first(ev, extra=None):
    for u in ev:
        if base_reclaim(u) and (extra is None or extra(u)):
            return u
    return None
def hit(rows):
    return 100 * sum(1 for u in rows if R3[u["cj_t"]]["R3"] >= 3) / len(rows) if rows else 0

print(f"reclaims (todos) {len(RECL)}")
print("\nFASE A — hit3R por micro-forma (quartis, nos reclaims):")
AFF = ["_rec_strength", "_prev_wick", "_rec_vol", "_dist_to_low", "_two_up", "_body_frac", "_choch_at_rec"]
for f in AFF:
    vals = sorted(u[f] for u in RECL)
    q1, q3 = vals[len(vals)//4], vals[3*len(vals)//4]
    lo = [u for u in RECL if u[f] <= q1]; hi = [u for u in RECL if u[f] >= q3]
    print(f"  {f:<16} baixo(<= {q1:.2f}) hit {hit(lo):.1f}% (N{len(lo)}) · alto(>= {q3:.2f}) hit {hit(hi):.1f}% (N{len(hi)})")

def panel(rows, tag):
    n = len(rows)
    if not n: print(f"  {tag:<26} vazio"); return None
    rs = sorted(rows, key=lambda r: r["cj_t"]); nets = [R3[r["cj_t"]]["net3"] for r in rs]
    h = sum(1 for r in rs if R3[r["cj_t"]]["R3"] >= 3); w = sum(1 for x in nets if x > 0)
    eq = pk = dd = 0.0; mL = cl = 0
    for x in nets:
        eq += x; pk = max(pk, eq); dd = min(dd, eq - pk)
        if x <= 0: cl += 1; mL = max(mL, cl)
        else: cl = 0
    yr = {}
    for r, x in zip(rs, nets): yr[r["yr"]] = round(yr.get(r["yr"], 0) + x, 1)
    circ = set()
    for r in rs: circ |= r["_circ"]
    print(f"  {tag:<26} N{n:>3} hit3R {100*h/n:>5.1f}% WR {100*w/n:>5.1f}% NET {sum(nets):>+7.1f} DD {dd:>6.1f} "
          f"stk-{mL} | {n/WK:.2f}/sem | círc {len(circ)}/60 | {yr}")
    return {"n": n, "hit": round(h/n, 3), "wr": round(w/n, 3), "net": round(sum(nets), 1), "dd": round(dd, 1), "stk": mL, "circ": len(circ)}
def null_p(rows, ref, seed):
    H0 = [1 if R3[r["cj_t"]]["R3"] >= 3 else 0 for r in ref]
    obs = sum(1 for r in rows if R3[r["cj_t"]]["R3"] >= 3) / len(rows)
    random.seed(seed)
    return sum(1 for _ in range(4000) if sum(random.sample(H0, len(rows))) / len(rows) >= obs) / 4000
def streak_dist(rows, seed):
    nets = [R3[r["cj_t"]]["net3"] for r in sorted(rows, key=lambda x: x["cj_t"])]
    random.seed(seed); q = []
    for _ in range(2000):
        sq = random.choices(nets, k=len(nets)); c2 = m2 = 0
        for x in sq:
            c2 = c2 + 1 if x <= 0 else 0; m2 = max(m2, c2)
        q.append(m2)
    q.sort(); return q[1000], q[int(0.95*2000)], sum(1 for x in q if x > 5) / 2000

print("\nFASE B — reclaim-afinado (das que sobem hit) 1/evento:")
panel([u for ev in EV if (u := first(ev))], "R0 base")
REF = UNIV
LOOKS = {
    "R-strength": (811, lambda u: u["_rec_strength"] >= 0.1),
    "R-prevwick": (812, lambda u: u["_prev_wick"] >= 0.3),
    "R-choch": (813, lambda u: u["_choch_at_rec"] == 1),
    "R-twoup": (814, lambda u: u["_two_up"] == 1),
    "R-str&wick": (815, lambda u: u["_rec_strength"] >= 0.1 and u["_prev_wick"] >= 0.3),
    "R-str&choch": (816, lambda u: u["_rec_strength"] >= 0.1 and u["_choch_at_rec"] == 1),
}
out = {}
for nm, (seed, ex) in LOOKS.items():
    rows = [u for ev in EV if (u := first(ev, ex))]
    p = panel(rows, nm)
    if rows and p and len(rows) >= 8:
        pn = null_p(rows, REF, seed); q50, q95, pg5 = streak_dist(rows, seed + 20)
        print(f"      P(null)={pn:.4f} · streak q50 {q50} q95 {q95} P(>5) {pg5:.2f}"
              + ("  <<< WR>=45%" if p["wr"] >= 0.45 else ""))
        out[nm] = {**p, "p": pn, "stk_q95": q95}
json.dump(out, open(HERE / "results" / "reclaim_microform_refine_20260706.json", "w"), indent=1, default=float)
print("\nOK → results/reclaim_microform_refine_20260706.json")
