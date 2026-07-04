#!/usr/bin/env python3
"""DA-PRE probe2: runners mortos vs classes protegidas do runnerpres;
sentinela 99 em h1n/h4n; unicidade do join cj_t; HALF size-null week-aware p/ E2."""
import json, random
from collections import defaultdict

RES = "/Users/cristrein/tradingview-mcp/research/xau_15m_bb_nas_leonardo/results"
rows = [json.loads(l) for l in open(f"{RES}/lab_g_candidates.jsonl")]
base = [r for r in rows if r.get("g_in_base435") == 1 and r.get("g_v5h") != "BEAR"]
def net(r): return r["g_R"] - 0.80 / r["g_risk"]

# join uniqueness
cjs = [r["cj_t"] for r in base]
print("cj_t unique in base:", len(set(cjs)) == len(cjs))

# sentinel 99 prevalence
for f in ("h1n_clean_sky_atr", "h4n_clean_sky_atr", "clean_sky_atr"):
    v = [r[f] for r in base]
    print(f"{f}: sentinel>=99 count={sum(1 for x in v if x >= 99)} / 435")

# protected contexts (runnerpres) membership of killed runners
def protected(r):
    tags = []
    if r["h1n_clean_sky_atr"] <= 0.29 and r["h4n_clean_sky_atr"] <= 0.12: tags.append("CONV4")
    if 0.906 <= r["g_box96"] < 0.947: tags.append("box96top")
    if r["legpos90"] >= 0.804: tags.append("legtop90")
    if 0.487 <= r["legpos60"] < 0.763: tags.append("legmidhigh")
    return tags

E2 = lambda r: r["legpos60"] <= 0.25 and r["h1_pos"] <= 0.61
CAL8 = lambda r: r["legpos60"] < 0.249 and r["g_ema21_dist"] < 0.16
for name, fn in (("E2", E2), ("CAL8", CAL8)):
    killed = [r for r in base if fn(r) and r["g_R"] >= 3]
    for r in killed:
        print(f"{name} kills runner g_R={r['g_R']:.2f} week={r['g_week']} protected={protected(r)}")

# HALF-size null (week-aware) for E2: does HALF on flagged beat HALF on random same-N week-blocks?
nets = [net(r) for r in base]
wks = [r["g_week"] for r in base]
flagged = {i for i, r in enumerate(base) if E2(r)}
def half_panel(half_set):
    eq = pk = dd = 0.0; stk = ws = 0
    for i, v in enumerate(nets):
        vv = v * 0.5 if i in half_set else v
        eq += vv; pk = max(pk, eq); dd = min(dd, eq - pk)
        stk = stk + 1 if vv < 0 else 0; ws = max(ws, stk)
    return eq, dd, ws
real = half_panel(flagged)
print(f"\nE2 HALF real: sum={real[0]:+.1f} DD={real[1]:+.1f} stk=-{real[2]}")
wkg = defaultdict(list)
for i, w in enumerate(wks): wkg[w].append(i)
weeks = list(wkg); rng = random.Random(7); beat = 0
N = len(flagged)
for _ in range(2000):
    rng.shuffle(weeks); pick = []
    for w in weeks:
        pick += wkg[w]
        if len(pick) >= N: break
    pick = set(rng.sample(pick, N))
    pn = half_panel(pick)
    if pn[0] >= real[0] and pn[1] >= real[1] and pn[2] <= real[2]: beat += 1
print(f"E2 HALF size-null(week-aware,2000): P(random-half >= real-half on sum&DD&stk) = {beat/2000:.4f}")
