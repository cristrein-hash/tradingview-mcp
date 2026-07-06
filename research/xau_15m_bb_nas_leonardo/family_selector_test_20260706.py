#!/usr/bin/env python3
"""PASSO 3b — SELETORES POR FAMÍLIA: o mapa vira teste (2026-07-06, aprovado Cris).
O mapa (family_feature_map) mostrou 3 arquétipos distintos. Aqui cada família ganha um seletor
declarado das suas 3 features CONTÍNUAS de maior separação (ignoro binárias degeneradas), bandas
q20-q80 dos winners da família. Teste: aplicar o seletor a TODOS os candidatos da família →
  hit3R vs base-da-família · círculos capturados (recall) · null 4000× DENTRO da família (seed
  fixa) · painel por EPISÓDIO · sub-janela anual (FIX-5) se P<0,05.
Objetivo: lucro + streak baixo. Winners oracle = calibração declarada; árbitro real = null+recall.
SELETORES (features contínuas top-sep, do mapa; binárias como CONTEXTO fixo da família):
  BANDA: g_atr_spike, h4n_dist_demand_atr, rsi_min8   [ctx: h1_trend<=0, h4n_in_demand]
  FUNDO: sell_bub_w, g_sweep_depth, h1n_clean_sky_atr  [ctx: h1_trend<=0, h4n_in_demand]
  RASO:  h4n_dist_demand_atr, g_atr, reclaim_ema_bars   [ctx: h1_trend==1]
SANITY_PROBE: sha GT · matcher v2 · bandas dos WINNERS (calibração, não outcome dos não-winners) ·
null dentro da família seed 201/202/203 · círculo-recall por família."""
import json, bisect, hashlib, random
import statistics as st
import datetime as dt
from pathlib import Path
HERE = Path(__file__).resolve().parent
exec((HERE / "family_feature_map_20260706.py").read_text().split('WINNERS = [')[0])
GT_ALL = [(g["flush_t"], g["flush_low"]) for g in GT]
WINNERS = [u for u in UNIV if u["_circ"] and R3[u["cj_t"]]["R3"] >= 3]
WK = len({u["g_week"] for u in U})

def qb(rows, k, lo, hi):
    v = sorted(fv(u, k) for u in rows if fv(u, k) is not None)
    if not v: return (None, None)
    return v[int(lo * (len(v) - 1))], v[int(hi * (len(v) - 1))]

FAMDEF = {
    "BANDA": {"feats": ["g_atr_spike", "h4n_dist_demand_atr", "rsi_min8"],
              "ctx": lambda u: fv(u, "h1_trend", 9) <= 0 and fv(u, "h4n_in_demand", 0) == 1},
    "FUNDO": {"feats": ["sell_bub_w", "g_sweep_depth", "h1n_clean_sky_atr"],
              "ctx": lambda u: fv(u, "h1_trend", 9) <= 0 and fv(u, "h4n_in_demand", 0) == 1},
    "RASO": {"feats": ["h4n_dist_demand_atr", "g_atr", "reclaim_ema_bars"],
             "ctx": lambda u: fv(u, "h1_trend", -9) == 1},
}
# direção de corte: por default banda q20-q80; para features "quanto maior melhor" (sweep, spike,
# sell_bub, clean_sky, dist_demand, atr) usa >= q20; rsi_min8 <= q80; reclaim_ema_bars <= q80
GEQ = {"g_atr_spike", "g_sweep_depth", "sell_bub_w", "h1n_clean_sky_atr", "h4n_dist_demand_atr", "g_atr"}
LEQ = {"rsi_min8", "reclaim_ema_bars"}

def episodes(rows):
    eps = []; cur = []
    for u in sorted(rows, key=lambda x: x["cj_t"]):
        a = u.get("g_atr") or 5.0; flo = u["g_sl"] + 0.1 * a
        if cur and u["cj_t"] - cur[-1]["cj_t"] <= 8 * 3600 and abs(flo - (cur[-1]["g_sl"] + 0.1 * (cur[-1].get("g_atr") or 5.0))) <= a:
            cur.append(u)
        else:
            if cur: eps.append(cur)
            cur = [u]
    if cur: eps.append(cur)
    return [e[0] for e in eps]
def panel(rows, tag):
    n = len(rows)
    if not n: print(f"  {tag:<26} vazio"); return None
    rs = sorted(rows, key=lambda u: u["cj_t"]); nets = [R3[u["cj_t"]]["net3"] for u in rs]
    h = sum(1 for u in rs if R3[u["cj_t"]]["R3"] >= 3)
    eq = pk = dd = 0.0; mL = cl = 0
    for x in nets:
        eq += x; pk = max(pk, eq); dd = min(dd, eq - pk)
        if x <= 0: cl += 1; mL = max(mL, cl)
        else: cl = 0
    yr = {}
    for u2, x in zip(rs, nets): yr[u2["yr"]] = round(yr.get(u2["yr"], 0) + x, 1)
    circ = set().union(*(u2["_circ"] for u2 in rs)) if rs else set()
    ne = len(episodes(rs))
    print(f"  {tag:<26} N{n:>4}(ep{ne:>3}) hit3R {100*h/n:>5.1f}% NET {sum(nets):>+7.1f} DD {dd:>6.1f} stk-{mL} "
          f"| {n/WK:.2f}/sem | círc {len(circ)} | {yr}")
    return {"n": n, "ep": ne, "hit": round(h/n, 3), "net": round(sum(nets), 1), "stk": mL, "circ": len(circ)}
def null_p(rows, ref, seed):
    H0 = [1 if R3[u["cj_t"]]["R3"] >= 3 else 0 for u in ref]
    obs = sum(1 for u in rows if R3[u["cj_t"]]["R3"] >= 3) / len(rows)
    random.seed(seed)
    return sum(1 for _ in range(4000) if sum(random.sample(H0, len(rows))) / len(rows) >= obs) / 4000
def streak_dist(rows, seed):
    nets = [R3[u["cj_t"]]["net3"] for u in sorted(rows, key=lambda x: x["cj_t"])]
    random.seed(seed); q = []
    for _ in range(2000):
        sq = random.choices(nets, k=len(nets)); c2 = m2 = 0
        for x in sq:
            c2 = c2 + 1 if x <= 0 else 0; m2 = max(m2, c2)
        q.append(m2)
    q.sort()
    return q[1000], q[int(0.95 * 2000)], sum(1 for x in q if x > 5) / 2000

SEEDS = {"BANDA": 201, "FUNDO": 202, "RASO": 203}
out = {}
for fam, spec in FAMDEF.items():
    POOL = [u for u in UNIV if u["_fam"] == fam and spec["ctx"](u)]
    W = [u for u in WINNERS if u["_fam"] == fam and spec["ctx"](u)]
    if len(W) < 5 or not POOL:
        print(f"\n### {fam}: winners-ctx {len(W)} insuficiente"); continue
    bands = {k: qb(W, k, 0.20, 0.80) for k in spec["feats"]}
    print(f"\n### FAMÍLIA {fam} · pool-ctx {len(POOL)} · winners-ctx {len(W)}")
    print("    bandas winner q20-q80: " + " · ".join(f"{k}[{a:.2f},{b:.2f}]" for k, (a, b) in bands.items()))
    def sel(u):
        for k in spec["feats"]:
            v = fv(u, k)
            lo, hi = bands[k]
            if v is None or lo is None: return False
            if k in GEQ and v < lo: return False
            if k in LEQ and v > hi: return False
            if k not in GEQ and k not in LEQ and not (lo <= v <= hi): return False
        return True
    SEL = [u for u in POOL if sel(u)]
    panel(POOL, f"{fam} pool-ctx (base)")
    p = panel(SEL, f"{fam} SELETOR")
    if SEL and p:
        pn = null_p(SEL, POOL, SEEDS[fam])
        ep = episodes(SEL); pe = null_p(ep, episodes(POOL), SEEDS[fam] + 50) if len(ep) >= 8 else None
        q50, q95, pg5 = streak_dist(SEL, SEEDS[fam] + 100)
        print(f"      P(null cand)={pn:.4f}" + (f" · P(null ep)={pe:.4f}" if pe is not None else "")
              + f" · streak q50 {q50} q95 {q95} P(>5) {pg5:.2f}")
        out[fam] = {**p, "p": pn, "p_ep": pe, "stk_q95": q95}
        if pn < 0.05:
            print("      SUB-JANELA ANUAL:")
            for yy in (2024, 2025, 2026):
                ry = [u for u in SEL if u["yr"] == yy]; by = [u for u in POOL if u["yr"] == yy]
                if ry and by:
                    hy = sum(1 for u in ry if R3[u["cj_t"]]["R3"] >= 3) / len(ry)
                    hb = sum(1 for u in by if R3[u["cj_t"]]["R3"] >= 3) / len(by)
                    print(f"        {yy}: sel {100*hy:.0f}% (N{len(ry)}) vs base {100*hb:.0f}% (N{len(by)})")
json.dump(out, open(HERE / "results" / "family_selector_test_20260706.json", "w"), indent=1, default=float)
print("\nOK → results/family_selector_test_20260706.json")
