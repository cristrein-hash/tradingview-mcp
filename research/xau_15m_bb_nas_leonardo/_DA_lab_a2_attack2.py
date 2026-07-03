#!/usr/bin/env python3
"""DA LAB A2 — probe 2: decomposição do Δ P1 (p+1 vs p+2), mecânica do null (risco menor
= R inflado?), null com risk-floor, RCAP hits, gross vs net."""
import random
from pathlib import Path

HERE = Path(__file__).parent
SB_USD = 0.80; RISK_FLOOR_USD = 6.40; RISK_FLOOR_ATR = 0.35
ns = {"__name__": "engine", "__file__": str(HERE / "engine_substrate4_v5_hourcausal.py")}
exec(compile((HERE / "engine_substrate4_v5_hourcausal.py").read_text(),
             "engine_substrate4_v5_hourcausal.py", "exec"), ns)
cand, ROWS, PRIMK = ns["cand"], ns["ROWS"], ns["PRIMK"]
letrun, cf_low, f = ns["letrun"], ns["cf_low"], ns["f"]
regime_h, QPOS, QRSI = ns["regime_hourcausal"], ns["QPOS"], ns["QRSI"]
HMAX, RCAP, ema_at = ns["HMAX"], ns["RCAP"], ns["ema_at"]
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
    SIG.append({"t": c["cj_t"], "yr": c["yr"], "R0": c["R"], "s": s, "p": p, "cj": cj,
                "atr": atr, "entry0": entry0, "sl": sl, "risk0": entry0 - sl, "row": r})
def net(R, risk): return R - SB_USD / risk

HAS_OPEN = True
def disp_ok(s, j, p, atr, C):
    b = s[j]
    if not (b["c"] > s[p]["h"]): return False
    if (b["c"] - b["o"]) < 0.5 * atr: return False
    return b["c"] > ema_at(C, j, 21)
def recomp_gates(s, j, entry, sl, atr):
    risk = entry - sl
    if risk <= 0 or risk < RISK_FLOOR_USD or risk < RISK_FLOOR_ATR * atr: return False
    if regime_h(s[j]["t"]) == "BEAR": return False
    if (s[j].get("rsi") or 50) < QRSI: return False
    lo20 = min(x["l"] for x in s[max(0, j - 19):j + 1]); hi20 = max(x["h"] for x in s[max(0, j - 19):j + 1])
    return (entry - lo20) / ((hi20 - lo20) or atr) >= QPOS

# P1 real: fired em p+1 ou p+2
d1 = d2 = 0.0; n1 = n2 = 0
for g in SIG:
    s, p, cj, atr, sl = g["s"], g["p"], g["cj"], g["atr"], g["sl"]
    C = [b["c"] for b in s]
    for j in (p + 1, p + 2):
        if j >= cj: break
        if disp_ok(s, j, p, atr, C) and recomp_gates(s, j, s[j]["c"], sl, atr):
            entry = s[j]["c"]; risk = entry - sl
            dd = net(letrun_from(s, j, entry, sl, atr), risk) - net(g["R0"], g["risk0"])
            if j == p + 1: n1 += 1; d1 += dd
            else: n2 += 1; d2 += dd
            break
print(f"P1 real: fired p+1 n{n1} Δ{d1:+.1f} ({d1/max(1,n1):+.3f}/tr) · fired p+2 n{n2} Δ{d2:+.1f} ({d2/max(1,n2):+.3f}/tr) · total {d1+d2:+.1f}")

# antecipar todos @p+1: decompor bruto vs custo, risco, RCAP
gb = gn = 0.0; rcap_hits_b = rcap_hits_a = 0; risks_a = []; risks_b = []
gain_bruto = gain_cost = 0.0
tiny = 0
for g in SIG:
    j = g["p"] + 1; entry = g["s"][j]["c"]; risk = entry - g["sl"]
    risks_b.append(g["risk0"])
    if g["R0"] >= RCAP - 1e-9: rcap_hits_b += 1
    if risk <= 0: continue
    risks_a.append(risk)
    R = letrun_from(g["s"], j, entry, g["sl"], g["atr"])
    if R >= RCAP - 1e-9: rcap_hits_a += 1
    if risk < RISK_FLOOR_USD or risk < RISK_FLOOR_ATR * g["atr"]: tiny += 1
    gain_bruto += (R - g["R0"])
    gain_cost += (SB_USD / g["risk0"] - SB_USD / risk)
risks_a.sort(); risks_b.sort()
print(f"antecipar todos @p+1: Δbruto {gain_bruto:+.1f} · Δcusto {gain_cost:+.1f} (negativo = custo maior) · ΔNET {gain_bruto+gain_cost:+.1f}")
print(f"  risco mediano: base ${risks_b[len(risks_b)//2]:.2f} vs @p+1 ${risks_a[len(risks_a)//2]:.2f} | trades abaixo do piso de risco @p+1: {tiny}/435")
print(f"  RCAP(20) hits: base {rcap_hits_b} vs @p+1 {rcap_hits_a}")

# null com o MESMO piso de risco do P1 (só antecipa se risk>=piso; senão base)
random.seed(123)
obs_delta = 23.5
nd = []
for _ in range(300):
    pick = set(random.sample(range(len(SIG)), 127))
    tot = 0.0
    for i, g in enumerate(SIG):
        if i in pick:
            j = g["p"] + 1; entry = g["s"][j]["c"]; risk = entry - g["sl"]
            if risk >= max(RISK_FLOOR_USD, RISK_FLOOR_ATR * g["atr"]):
                tot += net(letrun_from(g["s"], j, entry, g["sl"], g["atr"]), risk); continue
        tot += net(g["R0"], g["risk0"])
    nd.append(tot - sum(net(g["R0"], g["risk0"]) for g in SIG))
nd.sort()
p = sum(1 for d in nd if d >= obs_delta) / len(nd)
print(f"null @p+1 COM piso de risco (300 reps): med {nd[150]:+.1f} q05 {nd[15]:+.1f} q95 {nd[285]:+.1f} → p={p:.3f} (obs +23.5)")

# null @p+2 (mesma barra tardia que ~metade dos fires do P1?) com piso
nd2 = []
for _ in range(300):
    pick = set(random.sample(range(len(SIG)), 127))
    tot = 0.0
    for i, g in enumerate(SIG):
        if i in pick:
            j = g["p"] + 2; entry = g["s"][j]["c"]; risk = entry - g["sl"]
            if risk >= max(RISK_FLOOR_USD, RISK_FLOOR_ATR * g["atr"]):
                tot += net(letrun_from(g["s"], j, entry, g["sl"], g["atr"]), risk); continue
        tot += net(g["R0"], g["risk0"])
    nd2.append(tot - sum(net(g["R0"], g["risk0"]) for g in SIG))
nd2.sort()
p2 = sum(1 for d in nd2 if d >= obs_delta) / len(nd2)
print(f"null @p+2 COM piso de risco (300 reps): med {nd2[150]:+.1f} q05 {nd2[15]:+.1f} q95 {nd2[285]:+.1f} → p={p2:.3f}")
