#!/usr/bin/env python3
"""CASO C2 — regra de exceção exógena conforme CASE_C2_NOV24_EXOG_PREREG.md (congelado).
Override BEAR sse dxy_ret20>=θ1 E y_chg20>=θ2 E gold_ret20<0 (dia D conhecido no fecho, D_KNOWN).
Grelha fechada 2×2. Aceitação: C2>50% E dano<=0 nas outras 18 janelas. Reporta sujeira fora de C2.
Sem P&L. Detector intocado."""
import json, sys, bisect, datetime as dt
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import gt_pivot_structural_harness as R1
GT, SCOPE, TS4 = R1.GT, R1.SCOPE, R1.TS4
TH_DXY = [2.0, 2.5]
TH_Y = [0.25, 0.30]

def daily_feats(fn, col="c"):
    rows = [json.loads(l) for l in open(HERE/fn)]
    T = [r["t"] for r in rows]; C = [r[col] for r in rows]
    known = [t+86400 for t in T]
    ret20 = [None if i < 20 else 100*(C[i]/C[i-20]-1) for i in range(len(T))]
    chg20 = [None if i < 20 else C[i]-C[i-20] for i in range(len(T))]
    return known, ret20, chg20

DXY_K, DXY_RET, _ = daily_feats("raw_dxy_1d.jsonl")
Y_K, _, Y_CHG = daily_feats("raw_us10y_1d.jsonl")
# ouro: resample diário do RAW 4H (ENG.DK dias, ENG.DC closes) — dia D conhecido no fim do dia D
G_K = [(k+1)*86400 for k in R1.ENG.DK]
G_RET = [None if i < 20 else 100*(R1.ENG.DC[i]/R1.ENG.DC[i-20]-1) for i in range(len(R1.ENG.DK))]

def at(known, vals, t):
    j = bisect.bisect_right(known, t)-1
    return vals[j] if j >= 0 else None

def fired(t, th1, th2):
    d = at(DXY_K, DXY_RET, t); y = at(Y_K, Y_CHG, t); g = at(G_K, G_RET, t)
    return d is not None and y is not None and g is not None and d >= th1 and y >= th2 and g < 0

def main():
    base = lambda t: R1.BASE[t]
    wins = GT["windows"]
    c2 = next(w for w in wins if w["d0"] == "2024-11-10")
    def wscore(fn, w):
        sc = [(t, g) for t, g in SCOPE if w["t0"]+R1.TOL <= t <= w["t1"]-R1.TOL]
        return (100*sum(1 for t, g in sc if fn(t) == g)/len(sc)) if sc else None
    base_w = {w["id"]: wscore(base, w) for w in wins}
    for th1 in TH_DXY:
        for th2 in TH_Y:
            fn = lambda t, _a=th1, _b=th2: "BEAR" if fired(t, _a, _b) else R1.BASE[t]
            c2_pct = wscore(fn, c2)
            worst = []; dano_ok = True
            for w in wins:
                if w["id"] == c2["id"]: continue
                b0, b1 = base_w[w["id"]], wscore(fn, w)
                if b0 is None: continue
                if b1 < b0 - 1e-9:
                    dano_ok = False; worst.append((w["d0"], w["regime"], round(b0, 1), round(b1, 1)))
            dirt_in = sum(1 for t in TS4 if fired(t, th1, th2) and c2["t0"] <= t <= c2["t1"])
            dirt_out = sum(1 for t in TS4 if fired(t, th1, th2)) - dirt_in
            span_w = (TS4[-1]-TS4[0])/(7*86400)
            agg = R1.score_fn(fn, SCOPE)
            ok_a = c2_pct is not None and c2_pct > 50
            print(f"θ_dxy={th1} θ_y={th2} | C2={c2_pct:.1f}% {'PASS' if ok_a else 'FAIL'} | "
                  f"dano: {'ZERO PASS' if dano_ok else 'FAIL'} | fora-C2 {dirt_out} barras "
                  f"({dirt_out/span_w:.2f}/sem) | GT agregado bal {agg['bal']} (base 64,1)")
            for d0, reg, b0, b1 in worst:
                print(f"    piora: {d0} {reg} {b0}→{b1}")
            print(f"    VEREDICTO: {'ACEITA' if (ok_a and dano_ok) else 'REJEITA'}")

if __name__ == "__main__":
    main()
