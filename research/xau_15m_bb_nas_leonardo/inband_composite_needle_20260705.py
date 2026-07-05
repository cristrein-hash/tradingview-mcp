#!/usr/bin/env python3
"""AGULHA COMPOSTA NA BANDA — ondas × snapshot (2026-07-05, 4 looks finais declarados).
A2 achou trajetória com sinal (n_waves 4v3 · bottom_time 0,16v0,29 · vol_dryup 0,85v0,94; C2
P=0,018). Snapshot em-banda (perfil GT): spike 1,37v1,05 · sweep 0,77v0,54 · legpos 0,02v0,17 ·
supply 40v70. Nunca compostos. LEDGER (4 looks, bandas q25-75 dos GT em-banda, calibração
declarada):
  D1 C2(W1&W5) & spike & sweep         D2 C2 & legpos & supply
  D3 C3(W1&W5&W7) & spike              D4 C2 & rsi_low-banda & vol_dryup<=q75
Painel + GT-precisão + null vs banda + streak distribucional nos P<0,10.
SANITY_PROBE: herda P1-P4 da v2; zero recalibração de banda macro; multiplicidade do dia
reportada no resultado (12 looks em-banda acumulados)."""
import json, bisect, random
import datetime as dt
from pathlib import Path
HERE = Path(__file__).resolve().parent
exec((HERE / "inband_wave_structure_20260705.py").read_text().split('panel3(BAND, "BANDA (base)")')[0])

def qgt_s(f, p):
    v = sorted(fv(u, f) for u in Bgt if fv(u, f) is not None)
    return v[int(p * (len(v) - 1))]
SB = {f: (qgt_s(f, 0.25), qgt_s(f, 0.75)) for f in
      ("g_atr_spike", "g_sweep_depth", "legpos60", "n_supply_overhead", "rsi_low")}
print("bandas snapshot GT em-banda: " + " · ".join(f"{f}[{a:.2f},{b:.2f}]" for f, (a, b) in SB.items()))
W = {f: (qgt(f, 0.25), qgt(f, 0.75)) for f in FEATS}  # bandas de onda q25-75 (mesma regra da v2)
C2f = lambda u: inb(u, "W1_n_waves", *W["W1_n_waves"]) and inb(u, "W5_bottom_time", *W["W5_bottom_time"])
C3f = lambda u: C2f(u) and inb(u, "W7_vol_dryup", *W["W7_vol_dryup"])
looks = {
    "D1 C2&spike&sweep": lambda u: C2f(u) and fv(u, "g_atr_spike", 0) >= SB["g_atr_spike"][0]
        and fv(u, "g_sweep_depth", -9) >= SB["g_sweep_depth"][0],
    "D2 C2&legpos&supply": lambda u: C2f(u) and fv(u, "legpos60", 9) <= SB["legpos60"][1]
        and fv(u, "n_supply_overhead", 999) <= SB["n_supply_overhead"][1],
    "D3 C3&spike": lambda u: C3f(u) and fv(u, "g_atr_spike", 0) >= SB["g_atr_spike"][0],
    "D4 C2&rsi&vdry": lambda u: C2f(u) and SB["rsi_low"][0] <= fv(u, "rsi_low", -1) <= SB["rsi_low"][1]
        and u["_w"]["W7_vol_dryup"] is not None and u["_w"]["W7_vol_dryup"] <= W["W7_vol_dryup"][1],
}
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
panel3(BAND, "BANDA (base)")
out = {}
for nm, fn in looks.items():
    rows = [u for u in BAND if fn(u)]
    p = panel3(rows, nm)
    if rows and p:
        pn = null_p(rows, BAND, abs(hash(nm)) % 997)
        line = f"      P(null vs banda)={pn:.4f}"
        if pn < 0.10 and len(rows) >= 10:
            q50, q95, pg5 = streak_dist(rows, abs(hash(nm)) % 991)
            line += f" · streak q50 {q50} q95 {q95} P(>5) {pg5:.2f}"
        print(line)
        out[nm] = {**p, "p": pn}
best = min((k for k in out if out[k]["n"] >= 10), key=lambda k: out[k]["p"], default=None)
if best:
    fn = looks[best]
    rows = sorted([u for u in BAND if fn(u)], key=lambda x: x["cj_t"])
    print(f"\nmembros {best} (p/ visual):")
    for u in rows:
        r3 = R3[u["cj_t"]]
        print(f"  {dt.datetime.utcfromtimestamp(u['cj_t']).strftime('%Y-%m-%d %H:%M')} "
              f"{'WIN ' if r3['R3']>=3 else 'loss'} net {r3['net3']:+.1f} GT={u['_gt']} "
              f"waves {u['_w']['W1_n_waves']} btime {u['_w']['W5_bottom_time']:.2f}")
json.dump({"snapshot_bands": {f: list(v) for f, v in SB.items()}, "looks": out,
           "multiplicity_note": "12 looks em-banda acumulados hoje (B1-4, C1-4, D1-4)"},
          open(HERE / "results" / "inband_composite_needle_20260705.json", "w"), indent=1, default=float)
print("OK → results/inband_composite_needle_20260705.json")
