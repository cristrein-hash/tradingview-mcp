#!/usr/bin/env python3
"""LAB E — SLIPPAGE/COST sensitivity da XAU 15M LONG base #4 (N435).
Pré-registro (LER ANTES): docs/architecture/XAU_15M_LONG_LAB_E_SLIPPAGE_COST_PREREG_20260703.md
Cenários FIXADOS no prereg antes do cálculo: S0 $0 · SA $0,40 · SB $0,80 · SC $1,50 · SD $3,00
(round-trip, $ constante/trade; cost_R_i = cost_$/risk_$_i; R_net = R − cost_R).
Determinístico · fail-loud no baseline · sem RAW write/chart/plot/produção · stdlib only.
Outputs pequenos: results/lab_e_slippage_cost_results.csv + results/lab_e_slippage_cost_summary.json
"""
import csv, json
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "results"; OUT.mkdir(exist_ok=True)

# ---- deriva os 435 do ENGINE APROVADO REAL (exec; zero lógica copiada) ----
ns = {"__name__": "engine_exec", "__file__": str(HERE / "engine_substrate4_v5_hourcausal.py")}
exec(compile(open(HERE / "engine_substrate4_v5_hourcausal.py").read(),
             "engine_substrate4_v5_hourcausal.py", "exec"), ns)
cand, ROWS, PRIMK = ns["cand"], ns["ROWS"], ns["PRIMK"]
sel = sorted([c for c in cand if c["v5h"] != "BEAR"], key=lambda z: z["cj_t"])
rmap = {}
for r in ROWS: rmap.setdefault(r["cj_t"], r)

trades = []
for c in sel:
    r = rmap[c["cj_t"]]; s = PRIMK[r["block"]]["series"]
    tm = {b["t"]: i for i, b in enumerate(s)}
    p, cj = tm[r["t"]], tm[r["cj_t"]]
    atr = s[p]["atr"] or s[cj]["atr"]
    entry = s[cj]["c"]; sl = min(x["l"] for x in s[p:cj + 1]) - 0.1 * atr
    risk = entry - sl
    assert risk > 0
    trades.append({"t": c["cj_t"], "yr": c["yr"], "R": c["R"], "risk_usd": risk})

# ---- sanity: população exata ----
assert len(trades) == 435, len(trades)

SCEN = [("S0_baseline", 0.00), ("SA_low", 0.40), ("SB_mid", 0.80), ("SC_high", 1.50), ("SD_stress", 3.00)]
BUCKETS = [("R<=-0.5", -99, -0.5), ("-0.5..0", -0.5, 0.0001), ("0..1", 0.0001, 1), ("1..3", 1, 3), ("R>=3", 3, 999)]

def panel(rs):
    n = len(rs); sm = sum(rs); w = sum(1 for x in rs if x > 0)
    eq = pk = dd = 0.0
    for x in rs:
        eq += x; pk = max(pk, eq); dd = min(dd, eq - pk)
    mL = cl = 0
    for x in rs:
        if x > 0: cl = 0
        else: cl += 1
        mL = max(mL, cl)
    return {"N": n, "WR": round(100 * w / n, 1), "sumR": round(sm, 1), "avgR": round(sm / n, 3),
            "maxDD": round(dd, 1), "rDD": round(abs(sm / dd), 2) if dd < 0 else None, "worst_streak": mL}

rows_csv, summary = [], {"prereg": "XAU_15M_LONG_LAB_E_SLIPPAGE_COST_PREREG_20260703.md",
                         "population": 435, "scenarios": {}}
prev_sum = None
for name, usd in SCEN:
    net = [t["R"] - (usd / t["risk_usd"]) for t in trades]
    P = panel(net)
    per_yr = {y: round(sum(t["R"] - usd / t["risk_usd"] for t in trades if t["yr"] == y), 1) for y in (2024, 2025, 2026)}
    flips = sum(1 for t in trades if t["R"] > 0 and t["R"] - usd / t["risk_usd"] <= 0)
    runners = sum(1 for t in trades if t["R"] - usd / t["risk_usd"] >= 3)
    cost_R = [usd / t["risk_usd"] for t in trades]
    med_cost = sorted(cost_R)[len(cost_R) // 2]
    bucket_delta = {}
    for bn, lo, hi in BUCKETS:
        b = [t for t in trades if lo <= t["R"] < hi]
        if b: bucket_delta[bn] = {"n": len(b), "delta_sumR": round(-sum(usd / t["risk_usd"] for t in b), 1)}
    summary["scenarios"][name] = {**P, "usd_roundtrip": usd, "per_year": per_yr, "flips_pos_to_neg": flips,
                                  "runners_net_ge3": runners, "median_cost_R": round(med_cost, 4),
                                  "bucket_cost": bucket_delta}
    rows_csv.append({"scenario": name, "usd": usd, **P, "yr2024": per_yr[2024], "yr2025": per_yr[2025],
                     "yr2026": per_yr[2026], "flips": flips, "runners": runners, "median_cost_R": round(med_cost, 4)})
    # sanity monotônica
    if prev_sum is not None and P["sumR"] > prev_sum + 1e-9:
        raise SystemExit(f"SANITY FAIL: sumR não-decrescente em {name}")
    prev_sum = P["sumR"]

# ---- fail-loud: baseline reproduz painel aprovado ----
b = summary["scenarios"]["S0_baseline"]
ok = (b["N"] == 435 and abs(b["sumR"] - 291.5) < 0.5 and abs(b["WR"] - 47.6) < 0.2
      and abs(b["maxDD"] + 11.0) < 0.3 and b["worst_streak"] == 8)
if not ok:
    print(json.dumps(b, indent=1))
    raise SystemExit("BASELINE MISMATCH — parar e documentar; NÃO interpretar cenários.")
print("BASELINE OK — reproduz painel aprovado.")

with open(OUT / "lab_e_slippage_cost_results.csv", "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows_csv[0].keys())); w.writeheader(); w.writerows(rows_csv)
json.dump(summary, open(OUT / "lab_e_slippage_cost_summary.json", "w"), indent=1)

# risco $ para contexto (custo relativo por era de preço)
rk = sorted(t["risk_usd"] for t in trades)
summary_risk = {"risk_usd_min": round(rk[0], 2), "med": round(rk[len(rk)//2], 2), "max": round(rk[-1], 2)}
print("risk_usd (min/med/max):", summary_risk)
for r in rows_csv:
    print(f"{r['scenario']:<12} ${r['usd']:.2f} | WR{r['WR']:>5}% sumR{r['sumR']:>7} avgR{r['avgR']:>6} "
          f"DD{r['maxDD']:>6} r/DD{r['rDD']!s:>6} streak-{r['worst_streak']} | yr {r['yr2024']}/{r['yr2025']}/{r['yr2026']} "
          f"| flips {r['flips']} runners {r['runners']} custo_med {r['median_cost_R']}R")
print("outputs:", OUT / "lab_e_slippage_cost_results.csv", "+ summary.json")
