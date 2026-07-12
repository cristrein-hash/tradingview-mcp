#!/usr/bin/env python3
"""INTEGRAÇÃO DO CAMPO leg COMO CONTEXTO nos casos C4/C1/C5 (ordem Cris 2026-07-12).
Medição apenas (nenhuma regra adotada): a ESTRUTURA derivada do campo leg lê corretamente as
janelas que o macro falha, sem estragar as janelas RANGE?
Mapeamento declarado: estrutura(bar) = UP se leg ∈ {IMPULSO_UP, PULLBACK_BEAR} (ambos implicam
estrutura de pivots UP por construção) · DOWN se leg ∈ {IMPULSO_DOWN, PULLBACK_BULL} · NEUTRA se
ACUMULACAO. Concordância-contexto por janela GT: BULL→UP · BEAR→DOWN · RANGE→NEUTRA.
Tabela completa das 19 + sequências detalhadas de C1/C4/C5. Sem P&L. Detector intocado."""
import sys, bisect, datetime as dt
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import gt_pivot_structural_harness as R1
from leg_state_4h import build_leg_series
GT, TOL = R1.GT, R1.TOL
EST = {"IMPULSO_UP": "UP", "PULLBACK_BEAR": "UP",
       "IMPULSO_DOWN": "DOWN", "PULLBACK_BULL": "DOWN",
       "ACUMULACAO": "NEUTRA", "WARMUP": "NEUTRA"}
WANT = {"BULL": "UP", "BEAR": "DOWN", "RANGE": "NEUTRA"}
CASES = {"2020-03-24": "C1 V-turn", "2021-04-09": "C4 bull abr-jun/21", "2022-02-16": "C5 bull fev-abr/22"}

def main():
    ser = build_leg_series()
    byt = {r["t"]: r for r in ser}
    print(f"{'janela':<26} {'GT':<6} {'macro%':>7} {'leg-estrutura%':>15}")
    for w in GT["windows"]:
        sc = [t for t in R1.TS4 if w["t0"]+TOL <= t <= w["t1"]-TOL]
        if not sc: continue
        mac = 100*sum(1 for t in sc if byt[t]["macro"] == w["regime"])/len(sc)
        leg = 100*sum(1 for t in sc if EST[byt[t]["leg"]] == WANT[w["regime"]])/len(sc)
        tag = CASES.get(w["d0"], "")
        print(f"{w['d0']}→{w['d1']} {w['regime']:<6} {mac:6.1f}% {leg:14.1f}%  {tag}")
    for d0, name in CASES.items():
        w = next(x for x in GT["windows"] if x["d0"] == d0)
        ta, tb = w["t0"]-12*86400, w["t1"]+5*86400
        print(f"\n== {name} ({w['d0']}→{w['d1']}, GT={w['regime']}) ==")
        runs = []
        for r in ser:
            if not (ta <= r["t"] <= tb): continue
            key = (r["macro"], r["leg"])
            if runs and runs[-1][0] == key: runs[-1][2] = r["t"]
            else: runs.append([key, r["t"], r["t"]])
        f = lambda t: dt.datetime.utcfromtimestamp(t).strftime("%Y-%m-%d")
        for (mac, leg), t0, t1 in runs:
            mark = " <== janela" if w["t0"] <= t0 <= w["t1"] or w["t0"] <= t1 <= w["t1"] else ""
            print(f"  {f(t0)}→{f(t1)}  macro={mac:<6} leg={leg}{mark}")

if __name__ == "__main__":
    main()
