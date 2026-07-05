#!/usr/bin/env python3
"""AGULHA v2 — MACRO-ESTRUTURA PRIMEIRO, FEATURES DEPOIS (2026-07-05).
Ordem do método (Cris): leitura estrutural macro → só então features discriminantes.
  CAMADA 1 (estrutura): banda de retração da perna macro r=6, limites = quantis q10-q90 dos
  GT-membros do universo (calibração declarada — GT nunca vê outcome).
  CAMADA 2 (discriminação, perfil in-band GT vs sósia): bandas q25-75 one-sided dos GT in-band em
  g_atr_spike(>=) · g_sweep_depth(>=) · legpos60(<=) · n_supply_overhead(<=) · h1_pos(<=)
Painel + GT-precisão + null 4000× + streak distribucional + ablação 1-fora + membros p/ plot.
STATUS: CALIBRAÇÃO (bandas tiradas dos GT) — árbitro = visual Cris + rodada virgem futura.
SANITY_PROBE: P1 causalidade herdada (asserts nos builders) · P2 outcome nunca entra na
calibração das bandas · P3 null mesmo universo/matcher · P4 ablação detecta lente morta."""
import json, bisect, random
import statistics as st
import datetime as dt
from pathlib import Path
HERE = Path(__file__).resolve().parent
exec((HERE / "layer2_cris35_lenses_20260705.py").read_text().split("pb = panel(BASE")[0])
GT_60 = json.load(open(HERE / "results" / "ground_truth_bottoms_20260705.json"))
GT_ALL = [(g["flush_t"], g["flush_low"]) for g in GT_60]
N = len(S)
ATR = [b.get("atr") or 5.0 for b in S]
HI = [b["h"] for b in S]; LO = [b["l"] for b in S]

def zigzag_low_pivots(r=6):
    lows = []; d = 0; ehi = elo = 0
    for i in range(1, N):
        atr = ATR[i]
        if HI[i] > HI[ehi]: ehi = i
        if LO[i] < LO[elo]: elo = i
        if d >= 0 and HI[ehi] - LO[i] >= r * atr and ehi < i:
            d = -1; elo = min(range(ehi, i + 1), key=lambda k: LO[k])
        elif d <= 0 and HI[i] - LO[elo] >= r * atr and elo < i:
            lows.append((i, elo)); d = 1
            ehi = max(range(elo, i + 1), key=lambda k: HI[k])
    return lows
LOWS = zigzag_low_pivots(6); KLOW = [x[0] for x in LOWS]

UNIV = [u for u in U if u["cj_t"] in R3]
US = sorted(UNIV, key=lambda u: u["cj_t"]); UT = [u["cj_t"] for u in US]
for u in UNIV:
    u["_gt"] = 0
for g in GT_60:
    j = bisect.bisect_left(UT, g["flush_t"] - 8 * 3600)
    while j < len(UT) and UT[j] <= g["flush_t"] + 8 * 3600:
        v = US[j]
        if abs((v["g_sl"] + 0.1 * (v.get("g_atr") or 5.0)) - g["flush_low"]) <= (v.get("g_atr") or 5.0):
            v["_gt"] = 1
        j += 1
for u in UNIV:
    fi = bisect.bisect_right(TS, u["cj_t"]) - 1
    a = u.get("g_atr") or 5.0
    flo = u["g_sl"] + 0.1 * a
    j = bisect.bisect_right(KLOW, fi) - 1
    u["_retr"] = None
    if j >= 0:
        ki, l0i = LOWS[j]
        assert ki <= fi  # P1
        L0 = LO[l0i]
        H1 = max(HI[k] for k in range(l0i, fi + 1))
        if H1 - L0 > 1e-9:
            u["_retr"] = (H1 - flo) / (H1 - L0)

GTu = [u for u in UNIV if u["_gt"] and u["_retr"] is not None]
rv = sorted(u["_retr"] for u in GTu)
r_lo, r_hi = rv[int(0.10 * (len(rv) - 1))], rv[int(0.90 * (len(rv) - 1))]
print(f"GT no universo: {len(GTu)} · banda retr q10-q90 = [{r_lo:.2f}, {r_hi:.2f}]")
BAND = [u for u in UNIV if u["_retr"] is not None and r_lo <= u["_retr"] <= r_hi]
BGT = [u for u in BAND if u["_gt"]]
DISC = [("g_atr_spike", ">="), ("g_sweep_depth", ">="), ("legpos60", "<="),
        ("n_supply_overhead", "<="), ("h1_pos", "<=")]
def q(f, p):
    v = sorted(fv(u, f) for u in BGT if fv(u, f) is not None)
    return v[int(p * (len(v) - 1))]
cuts = {}
for f, op in DISC:
    cuts[f] = (q(f, 0.25), op) if op == ">=" else (q(f, 0.75), op)
print("cortes camada-2 (q25/q75 dos GT in-band): " +
      " · ".join(f"{f}{op}{c:.2f}" for f, (c, op) in cuts.items()))
def pass2(u, skip=None):
    for f, (c, op) in cuts.items():
        if f == skip:
            continue
        v = fv(u, f)
        if v is None:
            return False
        if op == ">=" and v < c:
            return False
        if op == "<=" and v > c:
            return False
    return True
NEEDLE = [u for u in BAND if pass2(u)]

def null_p(rows, ref, seed=51):
    H0 = [1 if R3[u["cj_t"]]["R3"] >= 3 else 0 for u in ref]
    obs = sum(1 for u in rows if R3[u["cj_t"]]["R3"] >= 3) / len(rows)
    random.seed(seed)
    return sum(1 for _ in range(4000) if sum(random.sample(H0, len(rows))) / len(rows) >= obs) / 4000

panel(UNIV, "UNIVERSO", GT_ALL)
panel(BAND, "CAMADA1 banda-macro", GT_ALL)
p = panel(NEEDLE, "AGULHA v2", GT_ALL)
if NEEDLE:
    pn = null_p(NEEDLE, UNIV)
    pb2 = null_p(NEEDLE, BAND, seed=52)
    gtp = sum(u["_gt"] for u in NEEDLE)
    print(f"  P(null|universo)={pn:.4f} · P(null|banda)={pb2:.4f} · GT-precisão {gtp}/{len(NEEDLE)} = {100*gtp/len(NEEDLE):.0f}%")
    nets = [R3[u["cj_t"]]["net3"] for u in sorted(NEEDLE, key=lambda x: x["cj_t"])]
    random.seed(53); qq = []
    for _ in range(2000):
        sq = random.choices(nets, k=len(nets)); c2 = m2 = 0
        for x in sq:
            c2 = c2 + 1 if x <= 0 else 0; m2 = max(m2, c2)
        qq.append(m2)
    qq.sort()
    print(f"  streak distribucional: q50 {qq[1000]} q95 {qq[int(0.95*2000)]} P(>5) {sum(1 for x in qq if x>5)/2000:.2f}")
    print("\nABLAÇÃO (remove 1 lente):")
    for f, _ in DISC:
        alt = [u for u in BAND if pass2(u, skip=f)]
        pa = panel(alt, f"  sem {f}", GT_ALL)
    print("\nMEMBROS AGULHA v2 (p/ plot):")
    for u in sorted(NEEDLE, key=lambda x: x["cj_t"]):
        r3 = R3[u["cj_t"]]
        print(f"  {dt.datetime.utcfromtimestamp(u['cj_t']).strftime('%Y-%m-%d %H:%M')} "
              f"{'WIN ' if r3['R3']>=3 else 'loss'} net {r3['net3']:+.1f} GT={u['_gt']} retr {u['_retr']:.2f}")
    json.dump({"band": [r_lo, r_hi], "cuts": {f: [c, op] for f, (c, op) in cuts.items()},
               "panel": p, "p_null_univ": pn, "p_null_band": pb2,
               "gt_precision": gtp / len(NEEDLE), "stk_q95": qq[int(0.95 * 2000)]},
              open(HERE / "results" / "needle_v2_macro_gtq_20260705.json", "w"), indent=1)
    print("OK → results/needle_v2_macro_gtq_20260705.json")
