#!/usr/bin/env python3
"""DA LAB A2 — probe 3: null JUSTO (mesma mistura de timing 53@p+1/74@p+2, mesmo piso de
risco, mesma fração efetiva) + contagem de anticipations efetivas no null do lab."""
import random
from pathlib import Path

HERE = Path(__file__).parent
SB_USD = 0.80; RISK_FLOOR_USD = 6.40; RISK_FLOOR_ATR = 0.35
ns = {"__name__": "engine", "__file__": str(HERE / "engine_substrate4_v5_hourcausal.py")}
exec(compile((HERE / "engine_substrate4_v5_hourcausal.py").read_text(),
             "engine_substrate4_v5_hourcausal.py", "exec"), ns)
cand, ROWS, PRIMK = ns["cand"], ns["ROWS"], ns["PRIMK"]
letrun, cf_low, f = ns["letrun"], ns["cf_low"], ns["f"]
HMAX, RCAP = ns["HMAX"], ns["RCAP"]
base_c = sorted([c for c in cand if c["v5h"] != "BEAR"], key=lambda z: z["cj_t"])
rmap = {r["cj_t"]: r for r in ROWS}

def letrun_from(s, j0, entry, sl, atr):
    risk = entry - sl
    if risk <= 0: return None
    trail = sl; r1 = False; ex = None; end = min(j0 + HMAX, len(s) - 1)
    for k in range(j0 + 1, end + 1):
        if s[k]["l"] <= trail: ex = trail; break
        if (s[k]["h"] - entry) / risk >= 1: r1 = True
        if r1:
            sw = cf_low(s, k)
            if sw: trail = max(trail, sw - 0.1 * atr)
    if ex is None: ex = s[end]["c"]
    return max(-1.0, min(RCAP, (ex - entry) / risk))

SIG = []
for c in base_c:
    r = rmap[c["cj_t"]]; s = PRIMK[r["block"]]["series"]
    tmap = {b["t"]: i for i, b in enumerate(s)}
    p, cj = tmap[r["t"]], tmap[r["cj_t"]]
    atr = s[p]["atr"] or s[cj]["atr"]
    entry0 = s[cj]["c"]; sl = min(x["l"] for x in s[p:cj + 1]) - 0.1 * atr
    SIG.append({"R0": c["R"], "s": s, "p": p, "cj": cj, "atr": atr, "sl": sl, "risk0": entry0 - sl})
def net(R, risk): return R - SB_USD / risk
BASE_NET = sum(net(g["R0"], g["risk0"]) for g in SIG)

# cache R antecipado por (i, j_off)
cache = {}
def antR(i, off):
    key = (i, off)
    if key in cache: return cache[key]
    g = SIG[i]; j = g["p"] + off; entry = g["s"][j]["c"]; risk = entry - g["sl"]
    if risk <= 0: cache[key] = None; return None
    ok_floor = risk >= RISK_FLOOR_USD and risk >= RISK_FLOOR_ATR * g["atr"]
    R = letrun_from(g["s"], j, entry, g["sl"], g["atr"])
    cache[key] = (net(R, risk), ok_floor)
    return cache[key]

# 1) null do LAB (sem piso): quantas anticipations "tiny-risk" ele usa por rep?
random.seed(9)
tiny_per_rep = []
for _ in range(50):
    pick = random.sample(range(435), 127)
    tiny = sum(1 for i in pick if antR(i, 1) and not antR(i, 1)[1])
    tiny_per_rep.append(tiny)
print(f"null do lab: por rep, {sum(tiny_per_rep)/len(tiny_per_rep):.0f}/127 anticipations abaixo do piso de risco (P1 nunca usa essas)")

# 2) null JUSTO: mistura 53@p+1 + 74@p+2, piso aplicado (falha piso → base), 500 reps
obs = 23.5
nd = []
for _ in range(500):
    pick = random.sample(range(435), 127)
    tot = 0.0; used = set()
    for k, i in enumerate(pick):
        off = 1 if k < 53 else 2
        a = antR(i, off)
        if a and a[1]: tot += a[0]; used.add(i)
    for i in range(435):
        if i not in used:
            tot += net(SIG[i]["R0"], SIG[i]["risk0"])
    nd.append(tot - BASE_NET)
nd.sort()
p = sum(1 for d in nd if d >= obs) / len(nd)
print(f"null JUSTO (mistura 53/74 + piso, 500 reps): med {nd[250]:+.1f} q05 {nd[25]:+.1f} q95 {nd[475]:+.1f} → p={p:.3f} (obs +23.5)")
# fração efetiva antecipada no null justo (última rep é representativa? calc média)
effs = []
for _ in range(30):
    pick = random.sample(range(435), 127)
    eff = sum(1 for k, i in enumerate(pick) if (a := antR(i, 1 if k < 53 else 2)) and a[1])
    effs.append(eff)
print(f"null justo: anticipations efetivas por rep ~{sum(effs)/len(effs):.0f}/127 (P1 real: 127/127 por seleção do disp)")

# 3) null justo com fração efetiva IGUAL a 127 (amostra até conseguir 127 acima do piso)
elig1 = [i for i in range(435) if (a := antR(i, 1)) and a[1]]
elig2 = [i for i in range(435) if (a := antR(i, 2)) and a[1]]
print(f"elegíveis acima do piso: @p+1 {len(elig1)}/435 · @p+2 {len(elig2)}/435")
nd3 = []
for _ in range(500):
    p1pick = random.sample(elig1, 53)
    rem = [i for i in elig2 if i not in set(p1pick)]
    p2pick = random.sample(rem, 74)
    tot = 0.0; used = {}
    for i in p1pick: used[i] = antR(i, 1)[0]
    for i in p2pick: used[i] = antR(i, 2)[0]
    for i in range(435):
        tot += used[i] if i in used else net(SIG[i]["R0"], SIG[i]["risk0"])
    nd3.append(tot - BASE_NET)
nd3.sort()
p3 = sum(1 for d in nd3 if d >= obs) / len(nd3)
print(f"null JUSTO 127 efetivas (500 reps): med {nd3[250]:+.1f} q05 {nd3[25]:+.1f} q95 {nd3[475]:+.1f} → p={p3:.3f} (obs +23.5)")
