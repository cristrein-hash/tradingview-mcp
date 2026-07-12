#!/usr/bin/env python3
"""HARNESS PIVOT-ESTRUTURAL vs GT (prereg REGIME_PIVOT_STRUCTURE_PREREG_20260712.md — congelado).
Pivots CAUSAIS (fractal k, confirmado no fecho de i+k, nunca revisto; uso só se confirmed_at ≤ t).
V1 = estrutural puro 3-classes · V2 = decomposição A/B (A estrutural, B baseline-direcional).
Métrica única = balanced accuracy vs GT congelado (bordas ±3d fora). P&L fora do loop.
Split: seleção 2020-22 (max balanced) → cego 2023-26. Barra: baseline cego bal 73,4.
RAW only. Detector atual intocado. Sem commit sem ordem."""
import io, json, bisect, contextlib, datetime as dt
import importlib.util
from pathlib import Path
HERE = Path(__file__).resolve().parent
GT = json.load(open(HERE/"results/REGIME_GT_CRIS_4H_20260712.json"))
TOL = GT["border_tolerance_s"]
SPLIT = int(dt.datetime(2023, 1, 1, tzinfo=dt.timezone.utc).timestamp())
K_GRID, N_GRID, S_GRID, EPS_GRID = [3, 5], [4, 6], [2, 3], [0.5, 1.0]
BAR_S = 14400

def load_engine():
    spec = importlib.util.spec_from_file_location("eng", HERE/"engine_4h_regime_gate_RAW.py")
    eng = importlib.util.module_from_spec(spec)
    with contextlib.redirect_stdout(io.StringIO()):
        spec.loader.exec_module(eng)
    return eng

ENG = load_engine()
H4, L4, TS4 = ENG.H4, [b["l"] for b in ENG.B4], ENG.TS4
# ATR14 4H (trailing, causal)
TR4 = [0.0]
for i in range(1, len(TS4)):
    TR4.append(max(H4[i]-L4[i], abs(H4[i]-ENG.C4[i-1]), abs(L4[i]-ENG.C4[i-1])))
def atr4(i, n=14):
    a = TR4[max(1, i-n+1):i+1]; return sum(a)/len(a) if a else 5.0

def pivots(k):
    """(confirmed_at, price, atr_no_pivô) para highs e lows; confirmado no fecho de i+k."""
    hi, lo = [], []
    n = len(TS4)
    for i in range(k, n-k):
        if H4[i] > max(H4[i-k:i]) and H4[i] > max(H4[i+1:i+1+k]):
            hi.append((TS4[i+k]+BAR_S, H4[i], atr4(i)))
        if L4[i] < min(L4[i-k:i]) and L4[i] < min(L4[i+1:i+1+k]):
            lo.append((TS4[i+k]+BAR_S, L4[i], atr4(i)))
    return hi, lo

def struct_label_series(k, N, S, eps):
    """Rótulo estrutural V1 por barra 4H (causal). Devolve lista alinhada a TS4 + série A (direcional?)."""
    hi, lo = pivots(k)
    hct = [p[0] for p in hi]; lct = [p[0] for p in lo]
    half = N//2
    labs, Aser = [], []
    for t in TS4:
        out_l = "RANGE"; A = False
        j = bisect.bisect_right(hct, t); m = bisect.bisect_right(lct, t)
        hs = hi[max(0, j-(half+1)):j]; ls = lo[max(0, m-(half+1)):m]
        cmps = []
        for arr, up_lbl, dn_lbl, eq_lbl in ((hs, "HH", "LH", "EQ"), (ls, "HL", "LL", "EQ")):
            for a, b in zip(arr, arr[1:]):
                d = b[1]-a[1]; tol = eps*b[2]
                cmps.append(eq_lbl if abs(d) <= tol else (up_lbl if d > 0 else dn_lbl))
        if len(cmps) >= 2:
            score = sum(1 for c in cmps if c in ("HH", "HL")) - sum(1 for c in cmps if c in ("LH", "LL"))
            neq = sum(1 for c in cmps if c == "EQ")
            if neq >= 2: out_l, A = "RANGE", False
            elif score >= S: out_l, A = "BULL", True
            elif score <= -S: out_l, A = "BEAR", True
        labs.append(out_l); Aser.append(A)
    return labs, Aser

BASE = {t: ENG.regime_at(t) for t in TS4}

def scope():
    out = []
    for t in TS4:
        hits = [w for w in GT["windows"] if w["t0"]+TOL <= t <= w["t1"]-TOL]
        if hits: out.append((t, max(hits, key=lambda w: w["t0"])["regime"]))
    return out

SCOPE = scope()
T2I = {t: i for i, t in enumerate(TS4)}

def score_fn(get_label, sc):
    per = {s: {"n": 0, "ok": 0, "false": 0} for s in ("BULL", "BEAR", "RANGE")}
    ok = 0
    for t, g in sc:
        lab = get_label(t)
        per[g]["n"] += 1
        if lab == g: per[g]["ok"] += 1; ok += 1
        else: per[lab]["false"] += 1
    rec = {s: (100*per[s]["ok"]/per[s]["n"] if per[s]["n"] else None) for s in per}
    bal = sum(v for v in rec.values() if v is not None)/sum(1 for v in rec.values() if v is not None)
    return {"n": len(sc), "acc": round(100*ok/len(sc), 1), "bal": round(bal, 1),
            "recall": {s: (round(v, 1) if v is not None else None) for s, v in rec.items()},
            "false": {s: per[s]["false"] for s in per}}

def main():
    sc_in = [(t, g) for t, g in SCOPE if t < SPLIT]
    sc_out = [(t, g) for t, g in SCOPE if t >= SPLIT]
    base_get = lambda t: BASE[t]
    b_all, b_in, b_out = score_fn(base_get, SCOPE), score_fn(base_get, sc_in), score_fn(base_get, sc_out)
    print(f"BASELINE confirmado: all bal={b_all['bal']} | in bal={b_in['bal']} | CEGO 2023-26 bal={b_out['bal']} (barra a bater)")
    rows = []
    for k in K_GRID:
        for N in N_GRID:
            for S in S_GRID:
                for eps in EPS_GRID:
                    labs, Aser = struct_label_series(k, N, S, eps)
                    v1 = lambda t, _l=labs: _l[T2I[t]]
                    def v2(t, _l=labs, _a=Aser):
                        i = T2I[t]
                        if not _a[i]: return "RANGE"
                        bl = BASE[t]
                        return bl if bl in ("BULL", "BEAR") else _l[i]
                    for tag, fn in (("V1", v1), ("V2", v2)):
                        s_all, s_i, s_o = score_fn(fn, SCOPE), score_fn(fn, sc_in), score_fn(fn, sc_out)
                        rows.append({"var": tag, "k": k, "N": N, "S": S, "eps": eps,
                                     "all": s_all, "in": s_i, "out": s_o, "fn": fn})
                        print(f"{tag} k={k} N={N} S={S} eps={eps:<4} | all acc={s_all['acc']:5.1f} bal={s_all['bal']:5.1f} "
                              f"recall B/Be/R={s_all['recall']['BULL']}/{s_all['recall']['BEAR']}/{s_all['recall']['RANGE']} "
                              f"| in bal={s_i['bal']:5.1f} | CEGO bal={s_o['bal']:5.1f}")
    print("\n== SPLIT (regra congelada: max balanced in-sample 2020-22) ==")
    ranked = sorted(rows, key=lambda r: -r["in"]["bal"])
    for r in ranked[:3]:
        print(f"  IS-top {r['var']} k={r['k']} N={r['N']} S={r['S']} eps={r['eps']} | in bal={r['in']['bal']} "
              f"| CEGO bal={r['out']['bal']} acc={r['out']['acc']} "
              f"recall B/Be/R={r['out']['recall']['BULL']}/{r['out']['recall']['BEAR']}/{r['out']['recall']['RANGE']} "
              f"| barra 73.4 {'BATIDA' if r['out']['bal'] > b_out['bal'] else 'NÃO batida'}")
    print(f"  baseline           | in bal={b_in['bal']} | CEGO bal={b_out['bal']}")

if __name__ == "__main__":
    main()
