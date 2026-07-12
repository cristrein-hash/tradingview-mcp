#!/usr/bin/env python3
"""CASO C2 r2 — variante com CAP DE ONSET (prereg CASE_C2_NOV24_EXOG_PREREG_R2_ONSET.md).
Condição exógena diária (r1) + exceção ativa só nos primeiros N_cap dias após o ONSET
(condição liga com false no dia anterior). Grelha 2 θ-pares × 3 caps. Critério igual (as três).
Causal close-only. Sem P&L. Detector intocado."""
import json, sys, bisect
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import gt_pivot_structural_harness as R1
from case_c2_nov24_rule import DXY_K, DXY_RET, Y_K, Y_CHG, G_K, G_RET, at
GT, SCOPE, TS4 = R1.GT, R1.SCOPE, R1.TS4
THETAS = [(2.5, 0.30), (2.0, 0.25)]
CAPS = [5, 8, 12]

def active_days(th1, th2, ncap):
    """Dias (índices do calendário DXY) em que a exceção está ativa, com cap de onset.
    Condição avaliada dia a dia no calendário do DXY (features via at() nos fechos)."""
    act = {}   # known_time -> True
    onset = None; prev = False
    for j, kt in enumerate(DXY_K):
        d = DXY_RET[j]
        y = at(Y_K, Y_CHG, kt); g = at(G_K, G_RET, kt)
        cond = d is not None and y is not None and g is not None and d >= th1 and y >= th2 and g < 0
        if cond and not prev:
            onset = j
        if cond and onset is not None and (j-onset) < ncap:
            act[kt] = True
        prev = cond
    return act

def main():
    base = lambda t: R1.BASE[t]
    wins = GT["windows"]
    c2 = next(w for w in wins if w["d0"] == "2024-11-10")
    def wscore(fn, w):
        sc = [(t, g) for t, g in SCOPE if w["t0"]+R1.TOL <= t <= w["t1"]-R1.TOL]
        return (100*sum(1 for t, g in sc if fn(t) == g)/len(sc)) if sc else None
    base_w = {w["id"]: wscore(base, w) for w in wins}
    span_w = (TS4[-1]-TS4[0])/(7*86400)
    for th1, th2 in THETAS:
        for ncap in CAPS:
            act = active_days(th1, th2, ncap)
            def fired(t, _a=act):
                j = bisect.bisect_right(DXY_K, t)-1
                return j >= 0 and DXY_K[j] in _a
            fn = lambda t, _f=fired: "BEAR" if _f(t) else R1.BASE[t]
            c2_pct = wscore(fn, c2)
            worst = []; dano_ok = True
            for w in wins:
                if w["id"] == c2["id"]: continue
                b0, b1 = base_w[w["id"]], wscore(fn, w)
                if b0 is None: continue
                if b1 < b0 - 1e-9:
                    dano_ok = False; worst.append((w["d0"], w["regime"], round(b0, 1), round(b1, 1)))
            dirt_in = sum(1 for t in TS4 if fired(t) and c2["t0"] <= t <= c2["t1"])
            dirt_out = sum(1 for t in TS4 if fired(t)) - dirt_in
            agg = R1.score_fn(fn, SCOPE)
            ok_a = c2_pct is not None and c2_pct > 50
            print(f"θ=({th1},{th2}) cap={ncap:>2}d | C2={c2_pct:５.1f}% {'PASS' if ok_a else 'FAIL'} "
                  f"| dano: {'ZERO PASS' if dano_ok else 'FAIL'} | fora-C2 {dirt_out} barras "
                  f"({dirt_out/span_w:.2f}/sem) | agregado bal {agg['bal']} (base 64,1)")
            for d0, reg, b0, b1 in worst:
                print(f"    piora: {d0} {reg} {b0}→{b1}")
            print(f"    VEREDICTO: {'ACEITA' if (ok_a and dano_ok) else 'REJEITA'}")

if __name__ == "__main__":
    main()
