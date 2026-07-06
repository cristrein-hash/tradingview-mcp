#!/usr/bin/env python3
"""NÍVEL DE EVENTO — FASE B CAUSAL (2026-07-06). O mapa (FASE A) mostrou eventos-fundo fortemente
distintos (rsi_min8 p<1e-4, dur/n_cand/sell_climax/nas p<1e-3). Aqui: agregação EVENTO-ATÉ-AGORA
(só candidatos com cj_t <= ponto de decisão — ZERO futuro-no-evento) e política 1-entrada-por-evento
(1º candidato que qualifica). O seletor exige EVENTO MADURO (o Cris espera a capitulação se
desenrolar antes de entrar).
SELETOR causal (convergência das discriminantes de evento fortes e causais):
  rsi_min8_acc <= 32  &  n_cand_so_far >= 2  &  (sell_climax_acc>=1 OU nas_long_acc==1)
  &  below_poc_acc==1
+ variantes (afrouxar/apertar). Painel completo + recall-círculo + null 4000× + streak distribucional
+ sub-ano. Árbitro = null honesto (não in-sample); é CALIBRAÇÃO (cortes das medianas do mapa).
SANITY_PROBE: agregação estritamente cj_t<=decisão (assert) · 1 entrada por evento · recall por
círculo distinto · null seed fixa 601 · sub-ano se P<0,05."""
import json, bisect, hashlib, random
from pathlib import Path
HERE = Path(__file__).resolve().parent
exec((HERE / "macro_leg_position_veto_20260705.py").read_text().split("VETOS = {")[0])
GTF = HERE / "results" / "ground_truth_bottoms_20260705.json"
assert hashlib.sha256(GTF.read_bytes()).hexdigest() == (HERE / "results" / "ground_truth_bottoms_20260705.sha256").read_text().split()[0]
GT = json.load(open(GTF))
N = len(S); ATR = [b.get("atr") or 5.0 for b in S]
HI = [b["h"] for b in S]; LO = [b["l"] for b in S]
CACHE = {r["cj_t"]: r for r in (json.loads(l) for l in open(HERE / "results" / "raw_feature_cache_20260706.jsonl"))}
UNIV = sorted([u for u in U if u["cj_t"] in R3 and u["cj_t"] in CACHE], key=lambda u: u["cj_t"])
UT = [u["cj_t"] for u in UNIV]
WK = len({u["g_week"] for u in U})
for u in UNIV:
    u["_flo"] = u["g_sl"] + 0.1 * (u.get("g_atr") or 5.0); u["_a"] = u.get("g_atr") or 5.0
    u["_circ"] = set(); u["_F"] = CACHE[u["cj_t"]]
for gi, g in enumerate(GT):
    j = bisect.bisect_left(UT, g["flush_t"] - 8 * 3600)
    while j < len(UNIV) and UT[j] <= g["flush_t"] + 8 * 3600:
        u = UNIV[j]; d = u["_flo"] - g["flush_low"]
        if -3 * u["_a"] <= d <= 1 * u["_a"]: u["_circ"].add(gi)
        j += 1
# eventos (mesmo colapso ±48h/±3ATR) + id do evento por candidato
EV = []; cur = []
for u in UNIV:
    if cur and u["cj_t"] - cur[-1]["cj_t"] <= 48 * 3600 and abs(u["_flo"] - cur[-1]["_flo"]) <= 3 * u["_a"]:
        cur.append(u)
    else:
        if cur: EV.append(cur)
        cur = [u]
if cur: EV.append(cur)
for ei, ev in enumerate(EV):
    for u in ev: u["_ev"] = ei

# agregação EVENTO-ATÉ-AGORA (causal) por candidato
for ev in EV:
    st_i = bisect.bisect_right(TS, ev[0]["cj_t"]) - 1
    pre_hi = max(HI[max(0, st_i - 96):st_i + 1])
    acc = {"rsi_min8": 99, "nas_dist": 99, "sell_climax": 0, "nas_long": 0, "below_poc": 0,
           "n": 0, "poc_dist": 99, "low_wick": 0, "buy_accum": 0}
    for u in ev:
        assert u["cj_t"] >= ev[0]["cj_t"]  # ordem
        f = u["_F"]
        acc["rsi_min8"] = min(acc["rsi_min8"], f["rsi_min8"])
        acc["nas_dist"] = min(acc["nas_dist"], f["nas_dist"])
        acc["sell_climax"] = max(acc["sell_climax"], f["sell_climax4"])
        acc["nas_long"] = max(acc["nas_long"], f["nas_long_rec"])
        acc["below_poc"] = max(acc["below_poc"], f["below_poc"])
        acc["poc_dist"] = min(acc["poc_dist"], f["poc_dist"])
        acc["buy_accum"] = max(acc["buy_accum"], f["buy_accum12"])
        acc["n"] += 1
        ci = bisect.bisect_right(TS, u["cj_t"]) - 1
        a = u["_a"]
        u["_acc"] = dict(acc)
        u["_acc"]["dur_h"] = (u["cj_t"] - ev[0]["cj_t"]) / 3600
        u["_acc"]["pre_drop"] = (pre_hi - min(LO[max(0, st_i - 8):ci + 1])) / a

def selector(name):
    if name == "S1":
        return lambda u: u["_acc"]["rsi_min8"] <= 32 and u["_acc"]["n"] >= 2 and \
            (u["_acc"]["sell_climax"] >= 1 or u["_acc"]["nas_long"] == 1) and u["_acc"]["below_poc"] == 1
    if name == "S2":  # + perna e capitulação mais forte
        return lambda u: u["_acc"]["rsi_min8"] <= 30 and u["_acc"]["n"] >= 3 and \
            u["_acc"]["sell_climax"] >= 1 and u["_acc"]["below_poc"] == 1 and u["_acc"]["pre_drop"] >= 8
    if name == "S3":  # NAS-driven
        return lambda u: u["_acc"]["rsi_min8"] <= 40 and u["_acc"]["nas_long"] == 1 and \
            u["_acc"]["n"] >= 2 and u["_acc"]["below_poc"] == 1
    if name == "S4":  # afrouxado
        return lambda u: u["_acc"]["rsi_min8"] <= 34 and u["_acc"]["n"] >= 2 and \
            (u["_acc"]["sell_climax"] >= 1 or u["_acc"]["nas_long"] == 1)

def first_per_event(sel):
    out = {}
    for u in UNIV:
        if u["_ev"] in out: continue
        if sel(u): out[u["_ev"]] = u
    return list(out.values())

def panel(rows, tag):
    n = len(rows)
    if not n: print(f"  {tag:<14} vazio"); return None
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
    print(f"  {tag:<14} N{n:>3} hit3R {100*h/n:>5.1f}% WR {100*w/n:>5.1f}% NET {sum(nets):>+7.1f} DD {dd:>6.1f} "
          f"stk-{mL} | {n/WK:.2f}/sem | círc {len(circ)}/60 | {yr}")
    return {"n": n, "hit": round(h / n, 3), "wr": round(w / n, 3), "net": round(sum(nets), 1), "dd": round(dd, 1), "stk": mL, "circ": len(circ)}

# base p/ null = 1 candidato por evento (o 1º cronológico de cada evento) — comparação justa
BASE1 = list({u["_ev"]: u for u in reversed(UNIV)}.values())  # arbitrário; usar todos eventos
BASE_first = []
seen = set()
for u in UNIV:
    if u["_ev"] not in seen: BASE_first.append(u); seen.add(u["_ev"])
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
    q.sort()
    return q[1000], q[int(0.95 * 2000)], sum(1 for x in q if x > 5) / 2000

print(f"eventos {len(EV)} · 1-por-evento base N{len(BASE_first)}")
panel(BASE_first, "BASE 1/evento")
out = {}
for nm in ("S1", "S2", "S3", "S4"):
    sel = selector(nm); rows = first_per_event(sel)
    p = panel(rows, nm)
    if rows and p and len(rows) >= 8:
        pn = null_p(rows, BASE_first, 601)
        q50, q95, pg5 = streak_dist(rows, 611)
        print(f"      P(null vs 1/evento)={pn:.4f} · streak q50 {q50} q95 {q95} P(>5) {pg5:.2f}")
        out[nm] = {**p, "p": pn, "stk_q95": q95}
        if pn < 0.05:
            print("      SUB-ANO:")
            for yy in (2024, 2025, 2026):
                ry = [r for r in rows if r["yr"] == yy]
                if ry:
                    hy = sum(1 for r in ry if R3[r["cj_t"]]["R3"] >= 3) / len(ry)
                    print(f"        {yy}: hit {100*hy:.0f}% N{len(ry)} NET {sum(R3[r['cj_t']]['net3'] for r in ry):+.1f}")
json.dump(out, open(HERE / "results" / "event_causal_layer_20260706.json", "w"), indent=1, default=float)
print("\nOK → results/event_causal_layer_20260706.json")
