#!/usr/bin/env python3
"""DA attack on LAB E slippage/cost. READ-ONLY: writes nothing to results/.
Checks:
 A) rmap (cj_t -> first ROWS row) consistency: does the rmap-chosen row reproduce
    the engine's R via letrun? (If not, risk_usd is computed off the wrong pivot.)
 B) duplicate cj_t within the 435 selection.
 C) per-year risk_usd distribution (min/median/p25) + low-risk trade counts,
    and per-year cost damage decomposition at SC ($1.50) to test the 2024 story.
 D) independent recomputation of SB panel (sumR, WR, DD, per-year) vs summary.json.
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ns = {"__name__": "engine_exec", "__file__": str(HERE / "engine_substrate4_v5_hourcausal.py")}
exec(compile(open(HERE / "engine_substrate4_v5_hourcausal.py").read(),
             "engine_substrate4_v5_hourcausal.py", "exec"), ns)
cand, ROWS, PRIMK, letrun, f, knife_v2 = ns["cand"], ns["ROWS"], ns["PRIMK"], ns["letrun"], ns["f"], ns["knife_v2"]
QPOS, QRSI = ns["QPOS"], ns["QRSI"]

sel = sorted([c for c in cand if c["v5h"] != "BEAR"], key=lambda z: z["cj_t"])
print(f"sel N = {len(sel)}")

# B) duplicates
from collections import Counter
dup = [k for k, v in Counter(c["cj_t"] for c in sel).items() if v > 1]
print(f"B) duplicate cj_t in selection: {len(dup)}")

# group ROWS by cj_t
by_cjt = {}
for r in ROWS:
    by_cjt.setdefault(r["cj_t"], []).append(r)

# A) rmap-first-row: recompute R via letrun and compare to engine's cand R
mism_R, mism_risk, multi = 0, 0, 0
risks = []
for c in sel:
    rows = by_cjt[c["cj_t"]]
    if len(rows) > 1:
        multi += 1
    r = rows[0]  # exactly what lab script's rmap.setdefault picks
    s = PRIMK[r["block"]]["series"]
    tm = {b["t"]: i for i, b in enumerate(s)}
    p, cj = tm[r["t"]], tm[r["cj_t"]]
    atr = s[p]["atr"] or s[cj]["atr"]
    entry = s[cj]["c"]; sl = min(x["l"] for x in s[p:cj + 1]) - 0.1 * atr
    risk = entry - sl
    R2 = letrun(s, cj, entry, sl, atr)
    if R2 is None or abs(R2 - c["R"]) > 1e-9:
        mism_R += 1
    risks.append({"t": c["cj_t"], "yr": c["yr"], "R": c["R"], "risk": risk})
print(f"A) cj_t with >1 ROWS row: {multi} | letrun(R from rmap-row) != cand R: {mism_R}")

# C) per-year risk_usd distribution + SC damage decomposition
import statistics as st
for y in (2024, 2025, 2026):
    g = [x for x in risks if x["yr"] == y]
    rk = sorted(x["risk"] for x in g)
    q25 = rk[len(rk)//4]; med = rk[len(rk)//2]
    low2 = sum(1 for v in rk if v < 2.0); low4 = sum(1 for v in rk if v < 4.0)
    grossR = sum(x["R"] for x in g)
    costR_SC = sum(1.5 / x["risk"] for x in g)
    costR_SB = sum(0.8 / x["risk"] for x in g)
    print(f"C) {y}: n={len(g)} risk$ min={rk[0]:.2f} p25={q25:.2f} med={med:.2f} max={rk[-1]:.2f} "
          f"| <$2: {low2} <$4: {low4} | grossR={grossR:.1f} costR@SB={costR_SB:.1f} costR@SC={costR_SC:.1f} "
          f"netSC={grossR-costR_SC:.1f}")

# share of SC-2024 cost paid by the lowest-risk quartile of 2024
g24 = sorted([x for x in risks if x["yr"] == 2024], key=lambda z: z["risk"])
q = len(g24)//4
lowq = g24[:q]
print(f"C+) 2024 lowest-risk quartile (n={q}): cost@SC={sum(1.5/x['risk'] for x in lowq):.1f}R "
      f"of total {sum(1.5/x['risk'] for x in g24):.1f}R | grossR of that quartile={sum(x['R'] for x in lowq):.1f}")

# D) independent SB recomputation
net = [x["R"] - 0.8 / x["risk"] for x in risks]
n = len(net); sm = sum(net); w = sum(1 for v in net if v > 0)
eq = pk = dd = 0.0
for v in net:
    eq += v; pk = max(pk, eq); dd = min(dd, eq - pk)
py = {y: sum(x["R"] - 0.8 / x["risk"] for x in risks if x["yr"] == y) for y in (2024, 2025, 2026)}
print(f"D) SB recompute: N{n} WR{100*w/n:.1f}% sumR{sm:.1f} DD{dd:.1f} r/DD{abs(sm/dd):.2f} "
      f"| yr {py[2024]:.1f}/{py[2025]:.1f}/{py[2026]:.1f}")

# E) sanity: engine letrun floor/cap interaction with cost
floor_hits = sum(1 for x in risks if x["R"] <= -0.9999)
print(f"E) trades at bruto R floor -1.0 (gap-through-stop truncated in BASELINE): {floor_hits}")
