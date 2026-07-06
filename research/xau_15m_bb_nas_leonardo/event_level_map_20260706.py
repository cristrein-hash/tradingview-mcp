#!/usr/bin/env python3
"""NÍVEL DE EVENTO — mapa (2026-07-06, aprovado Cris). Reframe: unidade = EVENTO (cluster de
candidatos que o olho vê como 1 ponto), densidade ~10-15:1 vs 37:1 do candidato.
FASE A (MAPA, agregação evento-inteiro — declarado, com possível leak de futuro-no-evento; serve só
p/ ver SE eventos-fundo são distintos): colapsa candidatos (±48h & ±3ATR), agrega 26 features RAW
(cache) por direção-winner + FEATURES NOVAS de evento (mente aberta, Cris):
  ev_pre_drop_atr  queda macro nas 96b antes do início do evento (a perna que leva ao fundo)
  ev_rev_speed     barras do low do evento ao close do último candidato (V rápido vs U lento)
  ev_low_wick_max  maior pavio inferior (rejeição) entre os candidatos
  ev_accel         acel. da queda (2ª metade da perna vs 1ª)
  ev_n_cand · ev_dur_h · ev_retr_min (família do evento)
Rótulo: evento-fundo = contém >=1 círculo. MWU evento-fundo vs evento-não em cada feature.
Se separar → FASE B causal (script seguinte).
SANITY_PROBE: sha GT · matcher v2 · cache causal p/ agregações · features novas causais no evento ·
MWU rank; FASE A explicitamente MAPA (agregação evento-inteiro pode olhar candidatos posteriores)."""
import json, bisect, hashlib, math, glob
from pathlib import Path
HERE = Path(__file__).resolve().parent
exec((HERE / "macro_leg_position_veto_20260705.py").read_text().split("VETOS = {")[0])  # U,R3,S,TS,fv
GTF = HERE / "results" / "ground_truth_bottoms_20260705.json"
assert hashlib.sha256(GTF.read_bytes()).hexdigest() == (HERE / "results" / "ground_truth_bottoms_20260705.sha256").read_text().split()[0]
GT = json.load(open(GTF))
N = len(S); ATR = [b.get("atr") or 5.0 for b in S]
HI = [b["h"] for b in S]; LO = [b["l"] for b in S]; CL = [b["c"] for b in S]; OP = [b.get("o", b["c"]) for b in S]
CACHE = {r["cj_t"]: r for r in (json.loads(l) for l in open(HERE / "results" / "raw_feature_cache_20260706.jsonl"))}
UNIV = sorted([u for u in U if u["cj_t"] in R3 and u["cj_t"] in CACHE], key=lambda u: u["cj_t"])
UT = [u["cj_t"] for u in UNIV]
for u in UNIV:
    u["_flo"] = u["g_sl"] + 0.1 * (u.get("g_atr") or 5.0); u["_a"] = u.get("g_atr") or 5.0
    u["_circ"] = set(); u["_F"] = CACHE[u["cj_t"]]
for gi, g in enumerate(GT):
    j = bisect.bisect_left(UT, g["flush_t"] - 8 * 3600)
    while j < len(UNIV) and UT[j] <= g["flush_t"] + 8 * 3600:
        u = UNIV[j]; d = u["_flo"] - g["flush_low"]
        if -3 * u["_a"] <= d <= 1 * u["_a"]: u["_circ"].add(gi)
        j += 1

# colapso em eventos (±48h & ±3ATR)
EV = []; cur = []
for u in UNIV:
    if cur and u["cj_t"] - cur[-1]["cj_t"] <= 48 * 3600 and abs(u["_flo"] - cur[-1]["_flo"]) <= 3 * u["_a"]:
        cur.append(u)
    else:
        if cur: EV.append(cur)
        cur = [u]
if cur: EV.append(cur)

def ev_feats(ev):
    o = {}
    F = [u["_F"] for u in ev]
    # agregações RAW por direção-winner
    o["nas_dist_min"] = min(f["nas_dist"] for f in F)
    o["rsi_min8_min"] = min(f["rsi_min8"] for f in F)
    o["rsi_cj_min"] = min(f["rsi_cj"] for f in F)
    o["below_poc_any"] = max(f["below_poc"] for f in F)
    o["poc_dist_min"] = min(f["poc_dist"] for f in F)
    o["vol_climax_max"] = max(f["vol_climax"] for f in F)
    o["sell_climax_max"] = max(f["sell_climax4"] for f in F)
    o["buy_accum_max"] = max(f["buy_accum12"] for f in F)
    o["choch_up_any"] = max(f["choch_up_rec24"] for f in F)
    o["ob_demand_any"] = max(f["ob_demand_mitig"] for f in F)
    o["flow_div_any"] = max(f["flow_divergence"] for f in F)
    o["nas_long_any"] = max(f["nas_long_rec"] for f in F)
    o["rsi_bull_div_any"] = max(f["rsi_bull_div"] for f in F)
    # features NOVAS de evento
    o["n_cand"] = len(ev)
    o["dur_h"] = (ev[-1]["cj_t"] - ev[0]["cj_t"]) / 3600
    # índices de barra
    si = bisect.bisect_right(TS, ev[0]["cj_t"]) - 1
    ei = bisect.bisect_right(TS, ev[-1]["cj_t"]) - 1
    lo_i = min(range(max(0, si - 8), ei + 1), key=lambda k: LO[k])
    a = ATR[ei] or 5.0
    pre_hi = max(HI[max(0, si - 96):si + 1])
    o["pre_drop_atr"] = (pre_hi - LO[lo_i]) / a
    o["rev_speed"] = (ei - lo_i)
    # maior pavio inferior entre barras dos candidatos
    wick = 0.0
    for u in ev:
        ci = bisect.bisect_right(TS, u["cj_t"]) - 1
        for k in range(max(0, ci - 3), ci + 1):
            w = (min(OP[k], CL[k]) - LO[k]) / a
            wick = max(wick, w)
    o["low_wick_max"] = wick
    # aceleração: queda 2ª metade da perna vs 1ª
    mid = (si - 96 + lo_i) // 2
    d1 = max(1e-9, HI[max(0, si - 96)] - LO[mid]); d2 = LO[mid] - LO[lo_i]
    o["accel"] = d2 / d1 if d1 else 0
    return o

for ev in EV:
    ev_circ = set()
    for u in ev: ev_circ |= u["_circ"]
    ev0 = ev[0]
    ev0["_ev_circ"] = ev_circ
FUND_EV = [ev for ev in EV if any(u["_circ"] for u in ev)]
NON_EV = [ev for ev in EV if not any(u["_circ"] for u in ev)]
print(f"eventos {len(EV)} · com-fundo {len(FUND_EV)} · densidade {len(NON_EV)/max(1,len(FUND_EV)):.1f}:1 "
      f"· círculos cobertos {len(set().union(*(set().union(*(u['_circ'] for u in ev)) for ev in FUND_EV)))}/60")
FA = {id(ev): ev_feats(ev) for ev in EV}
KEYS = list(next(iter(FA.values())).keys())

def mwu_p(a, b):
    na, nb = len(a), len(b)
    if na < 5 or nb < 5: return (1.0, None, None)
    allv = sorted([(v, 0) for v in a] + [(v, 1) for v in b]); ranks = [0.0] * len(allv); i = 0
    while i < len(allv):
        j = i
        while j + 1 < len(allv) and allv[j + 1][0] == allv[i][0]: j += 1
        for k in range(i, j + 1): ranks[k] = (i + j) / 2 + 1
        i = j + 1
    Ra = sum(ranks[k] for k in range(len(allv)) if allv[k][1] == 0)
    Ua = Ra - na * (na + 1) / 2; U = min(Ua, na * nb - Ua)
    mu = na * nb / 2; sd = math.sqrt(na * nb * (na + nb + 1) / 12)
    if sd == 0: return (1.0, None, None)
    z = (U - mu) / sd
    return (math.erfc(abs(z) / math.sqrt(2)), sorted(a)[na // 2], sorted(b)[nb // 2])

print(f"\nMWU evento-fundo ({len(FUND_EV)}) vs evento-não ({len(NON_EV)}) — p<0,10:")
res = []
for k in KEYS:
    a = [FA[id(ev)][k] for ev in FUND_EV]; b = [FA[id(ev)][k] for ev in NON_EV]
    p, ma, mb = mwu_p(a, b)
    if ma is not None: res.append((p, k, sum(a) / len(a), sum(b) / len(b)))
res.sort()
for p, k, mua, mub in res:
    if p < 0.10:
        print(f"  {k:<18} p={p:.4f} · fundo méd {mua:>7.2f} · não méd {mub:>7.2f}")
json.dump({"n_ev": len(EV), "fund": len(FUND_EV), "top": [(k, round(p, 4)) for p, k, _, _ in res[:12]]},
          open(HERE / "results" / "event_level_map_20260706.json", "w"), indent=1)
print("\nOK → results/event_level_map_20260706.json")
