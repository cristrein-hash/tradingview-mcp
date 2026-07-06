#!/usr/bin/env python3
"""POLÍTICA DE ENTRADA INTRA-EVENTO = RECLAIM (2026-07-06, direção Cris confirmada pelo mapa).
Mapa: a entry-bar correta é a CONFIRMAÇÃO DE REVERSÃO (close>high[-1] após o low do evento),
não o 1º candidato — vira o NET de negativo p/ +156. Política 1-entrada-por-evento = 1º reclaim.
Combinar TIMING (reclaim) com QUALIDADE-DE-FUNDO (features RAW do evento-até-o-reclaim, causais):
  P0 timing puro: 1º cand pós-low com reclaim & body_up & close_in_range>=0.5
  P1 P0 & oversold: rsi_min8-acumulado<=35 no evento até o reclaim
  P2 P0 & capitulação: (sell_climax visto | nas_long visto) & below_poc acumulado
  P3 P0 & oversold & capitulação (convergência)
Painel completo + recall-círculo + null 4000× vs base-1/evento + streak distribucional + sub-ano.
Árbitro = null honesto. Tudo causal (features acumuladas só até o candidato de entrada).
SANITY_PROBE: reclaim causal (close>high[-1], barra fechada) · acumulação só candidatos<=entrada ·
1 entrada/evento · recall círculo distinto · null seed 801 · sub-ano se P<0,05."""
import json, bisect, hashlib, random
from pathlib import Path
HERE = Path(__file__).resolve().parent
exec((HERE / "macro_leg_position_veto_20260705.py").read_text().split("VETOS = {")[0])
GTF = HERE / "results" / "ground_truth_bottoms_20260705.json"
assert hashlib.sha256(GTF.read_bytes()).hexdigest() == (HERE / "results" / "ground_truth_bottoms_20260705.sha256").read_text().split()[0]
GT = json.load(open(GTF))
N = len(S); ATR = [b.get("atr") or 5.0 for b in S]
HI = [b["h"] for b in S]; LO = [b["l"] for b in S]; CL = [b["c"] for b in S]; OP = [b.get("o", b["c"]) for b in S]
CACHE = {r["cj_t"]: r for r in (json.loads(l) for l in open(HERE / "results" / "raw_feature_cache_20260706.jsonl"))}
UNIV = sorted([u for u in U if u["cj_t"] in R3 and u["cj_t"] in CACHE], key=lambda u: u["cj_t"])
UT = [u["cj_t"] for u in UNIV]; WK = len({u["g_week"] for u in U})
for u in UNIV:
    u["_flo"] = u["g_sl"] + 0.1 * (u.get("g_atr") or 5.0); u["_a"] = u.get("g_atr") or 5.0
    u["_circ"] = set(); u["_F"] = CACHE[u["cj_t"]]
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

# anota por candidato: reclaim/micro-forma + acumulados causais do evento até ele
for ev in EV:
    min_flo = 1e18; acc_rsi = 99; acc_climax = 0; acc_nas = 0; acc_belowpoc = 0
    for pos, u in enumerate(ev, 1):
        ci = bisect.bisect_right(TS, u["cj_t"]) - 1; a = u["_a"]; f = u["_F"]
        prevmin = min_flo
        u["_post_low"] = int(pos > 1 and u["_flo"] > prevmin + 0.05 * a)
        min_flo = min(min_flo, u["_flo"])
        rng = max(1e-9, HI[ci] - LO[ci])
        u["_reclaim"] = int(ci >= 1 and CL[ci] > HI[ci - 1])
        u["_body_up"] = int(CL[ci] > OP[ci])
        u["_cir"] = (CL[ci] - LO[ci]) / rng
        # acumulados causais (incluem este candidato)
        acc_rsi = min(acc_rsi, f["rsi_min8"]); acc_climax = max(acc_climax, f["sell_climax4"])
        acc_nas = max(acc_nas, f["nas_long_rec"]); acc_belowpoc = max(acc_belowpoc, f["below_poc"])
        u["_acc_rsi"] = acc_rsi; u["_acc_climax"] = acc_climax; u["_acc_nas"] = acc_nas; u["_acc_bp"] = acc_belowpoc

def first_reclaim(ev, extra=None):
    for u in ev:
        if u["_post_low"] == 1 and u["_reclaim"] == 1 and u["_body_up"] == 1 and u["_cir"] >= 0.5:
            if extra is None or extra(u):
                return u
    return None

def panel(rows, tag):
    n = len(rows)
    if not n: print(f"  {tag:<22} vazio"); return None
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
    print(f"  {tag:<22} N{n:>3} hit3R {100*h/n:>5.1f}% WR {100*w/n:>5.1f}% NET {sum(nets):>+7.1f} DD {dd:>6.1f} "
          f"stk-{mL} | {n/WK:.2f}/sem | círc {len(circ)}/60 | {yr}")
    return {"n": n, "hit": round(h/n, 3), "wr": round(w/n, 3), "net": round(sum(nets), 1), "dd": round(dd, 1), "stk": mL, "circ": len(circ)}

# base = 1-por-evento (1º reclaim, timing puro P0) — a referência de null é o pool de reclaims
BASE0 = [u for ev in EV if (u := first_reclaim(ev))]
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

# referência ampla p/ null: TODOS os candidatos (base de outcome do universo)
REF = UNIV
print(f"eventos {len(EV)} · reclaims-1/evento {len(BASE0)}")
panel(UNIV, "UNIVERSO(base)")
LOOKS = {
    "P0 timing": (801, lambda ev: first_reclaim(ev)),
    "P1 &oversold": (802, lambda ev: first_reclaim(ev, lambda u: u["_acc_rsi"] <= 35)),
    "P2 &capitul": (803, lambda ev: first_reclaim(ev, lambda u: (u["_acc_climax"] >= 1 or u["_acc_nas"] == 1) and u["_acc_bp"] == 1)),
    "P3 &os&cap": (804, lambda ev: first_reclaim(ev, lambda u: u["_acc_rsi"] <= 35 and (u["_acc_climax"] >= 1 or u["_acc_nas"] == 1) and u["_acc_bp"] == 1)),
}
out = {}
for nm, (seed, pol) in LOOKS.items():
    rows = [u for ev in EV if (u := pol(ev))]
    p = panel(rows, nm)
    if rows and p and len(rows) >= 8:
        pn = null_p(rows, REF, seed)
        q50, q95, pg5 = streak_dist(rows, seed + 20)
        print(f"      P(null vs universo)={pn:.4f} · streak q50 {q50} q95 {q95} P(>5) {pg5:.2f}")
        out[nm] = {**p, "p": pn, "stk_q95": q95}
        if pn < 0.05:
            print("      SUB-ANO:")
            for yy in (2024, 2025, 2026):
                ry = [r for r in rows if r["yr"] == yy]
                if ry:
                    hy = sum(1 for r in ry if R3[r["cj_t"]]["R3"] >= 3) / len(ry)
                    print(f"        {yy}: hit {100*hy:.0f}% N{len(ry)} NET {sum(R3[r['cj_t']]['net3'] for r in ry):+.1f}")
json.dump(out, open(HERE / "results" / "event_reclaim_entry_20260706.json", "w"), indent=1, default=float)
print("\nOK → results/event_reclaim_entry_20260706.json")
