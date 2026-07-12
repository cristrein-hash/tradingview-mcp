#!/usr/bin/env python3
"""HARNESS r2 — pivots à ESCALA MACRO vs GT (revisão ordenada pelo Cris; prereg §REVISÃO r2).
Pivot defs: zigzag-ATR R∈{4,6,10} (máquina de ciclos causal: reversão ≥R·ATR14_4H confirma o
extremo; confirmed_at = fecho da barra confirmadora; nunca revisto) + fractal largo k∈{12,24}.
Resto idêntico ao r1 (V1 estrutural puro / V2 A-estrutural+B-baseline; N/S/ε; bordas ±3d;
split 2020-22→cego 2023-26; barra = baseline cego bal 73,4). SEM P&L. SEM commit sem ordem."""
import io, json, bisect, contextlib, datetime as dt
import importlib.util
from pathlib import Path
HERE = Path(__file__).resolve().parent
import sys; sys.path.insert(0, str(HERE))
import gt_pivot_structural_harness as R1   # reutiliza ENG, GT, SCOPE, score_fn, atr4, pivots(k)
ENG, GT, SCOPE, T2I = R1.ENG, R1.GT, R1.SCOPE, R1.T2I
TS4, H4, L4 = R1.TS4, R1.H4, R1.L4
BAR_S = R1.BAR_S
SPLIT = R1.SPLIT
N_GRID, S_GRID, EPS_GRID = [4, 6], [2, 3], [0.5, 1.0]
ZZ_R = [4, 6, 10]
FR_K = [12, 24]

def zigzag(R):
    """Pivots por máquina de ciclos (A2-style, causal): extremo confirmado quando o CLOSE
    reverte ≥ R·ATR14_4H do extremo corrente. confirmed_at = fecho da barra confirmadora."""
    n = len(TS4)
    hi, lo = [], []
    d = "UP"; ext_i = 0; ext_px = H4[0]
    for i in range(1, n):
        a = R1.atr4(i) or 5.0
        if d == "UP":
            if H4[i] > ext_px:
                ext_px = H4[i]; ext_i = i
            if (ext_px - ENG.C4[i])/a >= R:
                hi.append((TS4[i]+BAR_S, ext_px, R1.atr4(ext_i)))
                d = "DOWN"
                ext_px = L4[ext_i]; ext_i2 = ext_i
                for q in range(ext_i, i+1):
                    if L4[q] < ext_px: ext_px = L4[q]; ext_i2 = q
                ext_i = ext_i2
        else:
            if L4[i] < ext_px:
                ext_px = L4[i]; ext_i = i
            if (ENG.C4[i] - ext_px)/a >= R:
                lo.append((TS4[i]+BAR_S, ext_px, R1.atr4(ext_i)))
                d = "UP"
                ext_px = H4[ext_i]; ext_i2 = ext_i
                for q in range(ext_i, i+1):
                    if H4[q] > ext_px: ext_px = H4[q]; ext_i2 = q
                ext_i = ext_i2
    return hi, lo

def label_series(hi, lo, N, S, eps):
    hct = [p[0] for p in hi]; lct = [p[0] for p in lo]
    half = N//2
    labs, Aser = [], []
    for t in TS4:
        out_l = "RANGE"; A = False
        j = bisect.bisect_right(hct, t); m = bisect.bisect_right(lct, t)
        hs = hi[max(0, j-(half+1)):j]; ls = lo[max(0, m-(half+1)):m]
        cmps = []
        for arr, up_lbl, dn_lbl in ((hs, "HH", "LH"), (ls, "HL", "LL")):
            for a, b in zip(arr, arr[1:]):
                d = b[1]-a[1]; tol = eps*b[2]
                cmps.append("EQ" if abs(d) <= tol else (up_lbl if d > 0 else dn_lbl))
        if len(cmps) >= 2:
            score = sum(1 for c in cmps if c in ("HH", "HL")) - sum(1 for c in cmps if c in ("LH", "LL"))
            neq = sum(1 for c in cmps if c == "EQ")
            if neq >= 2: out_l, A = "RANGE", False
            elif score >= S: out_l, A = "BULL", True
            elif score <= -S: out_l, A = "BEAR", True
        labs.append(out_l); Aser.append(A)
    return labs, Aser

def main():
    sc_in = [(t, g) for t, g in SCOPE if t < SPLIT]
    sc_out = [(t, g) for t, g in SCOPE if t >= SPLIT]
    base_get = lambda t: R1.BASE[t]
    b_in, b_out = R1.score_fn(base_get, sc_in), R1.score_fn(base_get, sc_out)
    print(f"BASELINE: in bal={b_in['bal']} | CEGO bal={b_out['bal']} (barra)")
    defs = [(f"zz{R}", zigzag(R)) for R in ZZ_R] + [(f"fr{k}", R1.pivots(k)) for k in FR_K]
    for tag, (hi, lo) in defs:
        print(f"  [{tag}] pivots: {len(hi)+len(lo)} ({(len(hi)+len(lo))/6.5:.0f}/ano)")
    rows = []
    for tag, (hi, lo) in defs:
        for N in N_GRID:
            for S in S_GRID:
                for eps in EPS_GRID:
                    labs, Aser = label_series(hi, lo, N, S, eps)
                    v1 = lambda t, _l=labs: _l[T2I[t]]
                    def v2(t, _l=labs, _a=Aser):
                        i = T2I[t]
                        if not _a[i]: return "RANGE"
                        bl = R1.BASE[t]
                        return bl if bl in ("BULL", "BEAR") else _l[i]
                    for var, fn in (("V1", v1), ("V2", v2)):
                        s_all = R1.score_fn(fn, SCOPE)
                        s_i = R1.score_fn(fn, sc_in); s_o = R1.score_fn(fn, sc_out)
                        rows.append({"var": var, "def": tag, "N": N, "S": S, "eps": eps,
                                     "all": s_all, "in": s_i, "out": s_o})
                        print(f"{var} {tag:<5} N={N} S={S} eps={eps:<4}| all bal={s_all['bal']:5.1f} "
                              f"recall B/Be/R={s_all['recall']['BULL']}/{s_all['recall']['BEAR']}/{s_all['recall']['RANGE']} "
                              f"| in bal={s_i['bal']:5.1f} | CEGO bal={s_o['bal']:5.1f}")
    print("\n== SPLIT (regra congelada: max balanced in-sample) ==")
    ranked = sorted(rows, key=lambda r: -r["in"]["bal"])
    for r in ranked[:4]:
        print(f"  IS-top {r['var']} {r['def']} N={r['N']} S={r['S']} eps={r['eps']} | in bal={r['in']['bal']} "
              f"| CEGO bal={r['out']['bal']} recall B/Be/R={r['out']['recall']['BULL']}/{r['out']['recall']['BEAR']}/{r['out']['recall']['RANGE']} "
              f"| barra {b_out['bal']} {'BATIDA' if r['out']['bal'] > b_out['bal'] else 'NÃO batida'}")

if __name__ == "__main__":
    main()
