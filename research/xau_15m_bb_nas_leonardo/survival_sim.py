#!/usr/bin/env python3
"""TESTE DE TETO — simulação de sobrevivência FundedNext. Equity sequencial (ordem temporal), risco/trade r%,
bust se DD trailing >= LIM%, sucesso se equity >= TARGET% antes de bust. R por trade do candidates_sweep.csv
(uncapped e capped). Responde: a meta (streak≤3 / DD-funded) é alcançável por entrada-seleção neste substrato?
Verified 2026-06-26."""
import csv
from pathlib import Path
HERE = Path(__file__).parent
LIM, TARGET = 5.0, 8.0   # FundedNext: ~5% DD trailing, ~8% alvo
rows = sorted(csv.DictReader(open(HERE / "candidates_sweep.csv")), key=lambda r: int(r["t"]))
def sim(trs, r_pct, cap):
    eq = 0.0; peak = 0.0; maxdd = 0.0; busted = None; hit = None
    for i, t in enumerate(trs):
        R = float(t["R"]);
        if cap: R = max(-1.0, min(15.0, R))
        eq += R * r_pct; peak = max(peak, eq); dd = peak - eq; maxdd = max(maxdd, dd)
        if dd >= LIM and busted is None: busted = i + 1
        if eq >= TARGET and hit is None and busted is None: hit = i + 1
    return eq, maxdd, busted, hit
def run(name, trs):
    print(f"\n[{name}] n={len(trs)}")
    for cap in (True, False):
        for r in (1.0, 0.5, 0.25):
            eq, mdd, bust, hit = sim(trs, r, cap)
            tag = f"BUST@{bust}" if bust else (f"ALVO@{hit}" if hit else "vivo s/ alvo")
            print(f"   {'capped' if cap else 'uncap '} risco{r}% : equityFinal={eq:+.1f}% maxDD={mdd:.1f}% -> {tag}")
run("GERAL (sweep, macro-gated)", rows)
run("+NAS_near", [r for r in rows if r["nas_near"] == "1"])
run("+NAS&zona", [r for r in rows if r["nas_near"] == "1" and r["in_zone"] == "1"])
print(f"\nFN: bust se DD trailing>={LIM}%, sucesso se +{TARGET}% antes. Se BUST cedo em todos os riscos => entrada-seleção")
print("neste substrato NÃO é funded-survivable (a cauda direita não paga antes do streak quebrar).")
