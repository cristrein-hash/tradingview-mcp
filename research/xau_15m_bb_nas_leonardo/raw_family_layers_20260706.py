#!/usr/bin/env python3
"""LAYERS POR FAMÍLIA com features RAW discriminantes (2026-07-06, ordem Cris: não desistir).
Lê o cache de features RAW. Cada família = seletor de CONVERGÊNCIA das suas discriminantes MWU
(p<0,05), não banda larga. Painel completo (N·hit3R·WR·NET·DD·streak·freq·por-ano) + recall-círculo
+ null 4000× DENTRO da família (seed fixa) + streak distribucional + painel por episódio.
LAYERS (das assinaturas MWU):
  FUNDO (absorção): sell_absorb8>=2 & sell_climax4>=1                    [+ conv_absorb_choch opcional]
  BANDA (oversold+SVP): rsi_min8<=35 & below_poc==1 & vol_climax>=1.10
  RASO (NAS+SVP): nas_dist<=0.6 & rsi_min8<=45 & below_poc==1
Cada layer testado isolado E com reforço de convergência cruzada (conv_full).
SANITY_PROBE: cache já causal; cortes das discriminantes reais; null dentro da família seeds fixas
301/302/303; recall por círculo distinto; sub-ano se P<0,05."""
import json, random
from pathlib import Path
HERE = Path(__file__).resolve().parent
ROWS = [json.loads(l) for l in open(HERE / "results" / "raw_feature_cache_20260706.jsonl")]
WK = len({r["g_week"] for r in ROWS})
for r in ROWS:
    r["_win"] = bool(r["circ"]) and r["R3"] >= 3
def episodes(rows):
    eps = []; cur = []
    for r in sorted(rows, key=lambda x: x["cj_t"]):
        if cur and r["cj_t"] - cur[-1]["cj_t"] <= 8 * 3600:
            cur.append(r)
        else:
            if cur: eps.append(cur)
            cur = [r]
    if cur: eps.append(cur)
    return [e[0] for e in eps]
def panel(rows, tag):
    n = len(rows)
    if not n: print(f"  {tag:<30} vazio"); return None
    rs = sorted(rows, key=lambda r: r["cj_t"]); nets = [r["net3"] for r in rs]
    h = sum(1 for r in rs if r["R3"] >= 3); w = sum(1 for x in nets if x > 0)
    eq = pk = dd = 0.0; mL = cl = 0
    for x in nets:
        eq += x; pk = max(pk, eq); dd = min(dd, eq - pk)
        if x <= 0: cl += 1; mL = max(mL, cl)
        else: cl = 0
    yr = {}
    for r, x in zip(rs, nets): yr[r["yr"]] = round(yr.get(r["yr"], 0) + x, 1)
    circ = set()
    for r in rs: circ |= set(r["circ"])
    ne = len(episodes(rs))
    print(f"  {tag:<30} N{n:>4}(ep{ne:>3}) hit3R {100*h/n:>5.1f}% WR {100*w/n:>5.1f}% NET {sum(nets):>+7.1f} "
          f"DD {dd:>6.1f} stk-{mL} | {n/WK:.2f}/sem | círc {len(circ)} | {yr}")
    return {"n": n, "ep": ne, "hit": round(h/n, 3), "wr": round(w/n, 3), "net": round(sum(nets), 1),
            "dd": round(dd, 1), "stk": mL, "circ": len(circ)}
def null_p(rows, ref, seed):
    H0 = [1 if r["R3"] >= 3 else 0 for r in ref]
    obs = sum(1 for r in rows if r["R3"] >= 3) / len(rows)
    random.seed(seed)
    return sum(1 for _ in range(4000) if sum(random.sample(H0, len(rows))) / len(rows) >= obs) / 4000
def streak_dist(rows, seed):
    nets = [r["net3"] for r in sorted(rows, key=lambda x: x["cj_t"])]
    random.seed(seed); q = []
    for _ in range(2000):
        sq = random.choices(nets, k=len(nets)); c2 = m2 = 0
        for x in sq:
            c2 = c2 + 1 if x <= 0 else 0; m2 = max(m2, c2)
        q.append(m2)
    q.sort()
    return q[1000], q[int(0.95 * 2000)], sum(1 for x in q if x > 5) / 2000

# seletores das features CAUSAIS sobreviventes (pós-fix look-ahead): FUNDO só sell_climax4;
# BANDA rsi+SVP; RASO (mais rica) nas_dist+rsi+SVP+vol
LAYERS = {
    "FUNDO": (301, [
        ("F-climax2", lambda r: r["fam"] == "FUNDO" and r["sell_climax4"] >= 2),
        ("F-climax&choch", lambda r: r["fam"] == "FUNDO" and r["sell_climax4"] >= 1 and r["choch_up_rec24"] == 1),
    ]),
    "BANDA": (302, [
        ("B-osvp", lambda r: r["fam"] == "BANDA" and r["rsi_min8"] <= 35 and r["poc_dist"] <= -2.5 and r["vol_climax"] >= 1.10),
        ("B-os&nas", lambda r: r["fam"] == "BANDA" and r["rsi_min8"] <= 35 and r["poc_dist"] <= -2.5 and r["nas_dist"] <= -0.5),
    ]),
    "RASO": (303, [
        ("R-nassvp", lambda r: r["fam"] == "RASO" and r["nas_dist"] <= 0.6 and r["rsi_min8"] <= 45 and r["below_poc"] == 1),
        ("R-nassvp&vol", lambda r: r["fam"] == "RASO" and r["nas_dist"] <= 0.6 and r["rsi_min8"] <= 45 and r["below_poc"] == 1 and r["vol_climax"] >= 1.05),
        ("R-tight", lambda r: r["fam"] == "RASO" and r["nas_dist"] <= 0.5 and r["rsi_min8"] <= 43 and r["below_poc"] == 1 and r["vol_climax"] >= 1.05 and r["poc_dist"] <= 0),
    ]),
}
out = {}
for fam, (seed, looks) in LAYERS.items():
    POOL = [r for r in ROWS if r["fam"] == fam]
    print(f"\n### FAMÍLIA {fam} · pool {len(POOL)} · winners {sum(1 for r in POOL if r['_win'])}")
    panel(POOL, f"{fam} pool (base)")
    for nm, fn in looks:
        SEL = [r for r in POOL if fn(r)]
        p = panel(SEL, nm)
        if SEL and p and len(SEL) >= 8:
            pn = null_p(SEL, POOL, seed)
            ep = episodes(SEL); pe = null_p(ep, episodes(POOL), seed + 40) if len(ep) >= 6 else None
            q50, q95, pg5 = streak_dist(SEL, seed + 80)
            print(f"      P(null)={pn:.4f}" + (f" · P(null ep)={pe:.4f}" if pe is not None else "")
                  + f" · streak q50 {q50} q95 {q95} P(>5) {pg5:.2f}")
            out[nm] = {**p, "p": pn, "p_ep": pe, "stk_q95": q95}
            if pn < 0.05:
                print("      SUB-ANO:")
                for yy in (2024, 2025, 2026):
                    ry = [r for r in SEL if r["yr"] == yy]; by = [r for r in POOL if r["yr"] == yy]
                    if ry and by:
                        hy = sum(1 for r in ry if r["R3"] >= 3) / len(ry)
                        hb = sum(1 for r in by if r["R3"] >= 3) / len(by)
                        nety = sum(r["net3"] for r in ry)
                        print(f"        {yy}: {100*hy:.0f}% (N{len(ry)}, NET {nety:+.1f}) vs base {100*hb:.0f}%")
json.dump(out, open(HERE / "results" / "raw_family_layers_20260706.json", "w"), indent=1, default=float)
print("\nOK → results/raw_family_layers_20260706.json")
