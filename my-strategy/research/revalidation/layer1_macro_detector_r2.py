#!/usr/bin/env python3
"""DETECTOR LAYER 1 (MACRO) ROUND 2 — núcleo de DESLOCAMENTO por EMAs longas (substitui o
zigzag-% esparso do round 1, que travava a estrutura). Autorizado Cris 2026-07-13.
Núcleo A (novo): sobre closes diários — EMA_f vs EMA_s (longas), slope de EMA_f normalizado por
ATR, e efficiency-ratio macro; BULL/BEAR/RANGE por regra + histerese H_macro dias.
B contenção Donchian (mantida, revista: usa também RANGE quando slope~0 mesmo sem largura mínima).
C override choque estrutural + confirmação exógena SINAL (mantido do r1).
Prioridade C>B>A. Causal close-only (dia D no fecho). Métrica intrínseca vs GT Layer 1. SEM P&L.
Round 2 = reportar CURVA (por-BEAR + agregado + per-janela), não escolher ótimo."""
import json, sys, bisect, statistics, datetime as dt
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
GT = json.load(open(HERE/"results/REGIME_GT_LAYER1_CRIS_1D_20260713.json"))
TOL = GT["border_tolerance_s"]
D1 = [json.loads(l) for l in open(HERE/"raw_1d_ohlc.jsonl")]
T = [b["t"] for b in D1]; H = [b["h"] for b in D1]; L = [b["l"] for b in D1]; C = [b["c"] for b in D1]
N = len(T); KNOWN = [t+86400 for t in T]
TR = [0.0]+[max(H[i]-L[i], abs(H[i]-C[i-1]), abs(L[i]-C[i-1])) for i in range(1, N)]
def atr(i, n=14):
    a = TR[max(1, i-n+1):i+1]; return sum(a)/len(a) if a else 1.0
def ema_series(vals, n):
    k = 2/(n+1); e = vals[0]; out = []
    for v in vals: e = v*k + e*(1-k); out.append(e)
    return out

def daily_feat(fn):
    rows = [json.loads(l) for l in open(HERE/fn)]
    kt = [r["t"]+86400 for r in rows]; c = [r["c"] for r in rows]
    ret20 = [None if i < 20 else 100*(c[i]/c[i-20]-1) for i in range(len(c))]
    chg20 = [None if i < 20 else c[i]-c[i-20] for i in range(len(c))]
    return kt, ret20, chg20
DXY_K, DXY_RET, _ = daily_feat("raw_dxy_1d.jsonl")
Y_K, _, Y_CHG = daily_feat("raw_us10y_1d.jsonl")
def _at(kt, v, t):
    j = bisect.bisect_right(kt, t)-1
    return v[j] if j >= 0 else None
def exog_dir(t):
    d = _at(DXY_K, DXY_RET, t); y = _at(Y_K, Y_CHG, t)
    if d is None or y is None: return 0
    if d > 0 and y > 0: return +1
    if d < 0 and y < 0: return -1
    return 0

def build(ef, es, slope_thr, eff_thr, H_macro, W_don, s_thr, s_days):
    EF = ema_series(C, ef); ES = ema_series(C, es)
    core = "RANGE"; pend = None; pn = 0
    out = []
    for i in range(N):
        t = KNOWN[i]
        raw = "RANGE"
        if i >= es:                                      # núcleo usa dados <= i (close de i, causal)
            a = atr(i) or 1.0
            slope = (EF[i]-EF[i-10])/a                    # slope EMA rápida em ATR (10 dias)
            seg = C[i-es:i+1]; net = seg[-1]-seg[0]
            path = sum(abs(seg[j]-seg[j-1]) for j in range(1, len(seg)))
            eff = abs(net)/path if path > 0 else 0
            trend_up = EF[i] > ES[i] and slope > slope_thr and eff >= eff_thr
            trend_dn = EF[i] < ES[i] and slope < -slope_thr and eff >= eff_thr
            if trend_up: raw = "BULL"
            elif trend_dn: raw = "BEAR"
            else: raw = "RANGE"
        if raw == core: pend = None; pn = 0
        elif raw == pend: pn += 1
        else: pend = raw; pn = 1
        if pend is not None and pn >= H_macro: core = pend; pend = None; pn = 0
        # (B) contenção
        contained = False
        if i >= W_don:
            hh = max(H[i-W_don:i]); ll = min(L[i-W_don:i])
            if hh > ll:
                pos = (C[i-1]-ll)/(hh-ll)
                a = atr(i) or 1.0
                slope = (EF[i-1]-EF[i-1-10])/a if i >= 11+1 else 0
                contained = 0.2 <= pos <= 0.8 and abs(slope) < slope_thr
        # (C) choque + exógeno
        shock = None
        if i >= s_days+1:
            mv = (C[i-1]-C[i-1-s_days])/C[i-1-s_days]*100
            ed = exog_dir(t)
            if mv <= -s_thr and ed == +1: shock = "BEAR"
            elif mv >= s_thr and ed == -1: shock = "BULL"
        label = shock or ("RANGE" if (contained and core != "BULL" and core != "BEAR") else
                          ("RANGE" if contained else core))
        out.append((t, label))
    return out

def eff_label(t):
    hits = [w for w in GT["windows"] if w["t0"]+TOL <= t <= w["t1"]-TOL]
    if not hits: return None
    return min(hits, key=lambda w: w["t1"]-w["t0"])["regime"]
SCOPE = [(KNOWN[i], eff_label(KNOWN[i])) for i in range(N)]
SCOPE = [(t, g) for t, g in SCOPE if g is not None]

def score(lab, scope=None):
    scope = scope or SCOPE
    per = {s: {"n": 0, "ok": 0} for s in ("BULL", "BEAR", "RANGE")}
    ok = 0
    for t, g in scope:
        l = lab.get(t); per[g]["n"] += 1
        if l == g: per[g]["ok"] += 1; ok += 1
    rec = {s: (100*per[s]["ok"]/per[s]["n"] if per[s]["n"] else None) for s in per}
    bal = statistics.mean([v for v in rec.values() if v is not None])
    return {"n": len(scope), "acc": round(100*ok/len(scope), 1), "bal": round(bal, 1), "recall": rec}

def per_bear(lab):
    res = {}
    for w in GT["windows"]:
        if w["regime"] != "BEAR": continue
        sc = [t for t in KNOWN if w["t0"]+TOL <= t <= w["t1"]-TOL]
        res[w["d0"]] = round(100*sum(1 for t in sc if lab.get(t) == "BEAR")/len(sc), 0) if sc else None
    return res

GRID = [(ef, es, sl, ev, hm, wd, st, sd)
        for ef in (20, 50) for es in (100, 200) for sl in (0.05, 0.15)
        for ev in (0.20, 0.30) for hm in (10, 20) for wd in (90, 180)
        for st in (10,) for sd in (12,)]

def main():
    rows = []
    for cfg in GRID:
        lab = {t: l for t, l in build(*cfg)}
        s = score(lab); pb = per_bear(lab)
        vals = [v for v in pb.values() if v is not None]
        rows.append({"cfg": cfg, "s": s, "pb": pb, "bmin": min(vals), "bmean": statistics.mean(vals), "lab": lab})
    print(f"grelha {len(GRID)} · GT Layer1 16 janelas · métrica intrínseca (P&L fora)")
    print("\n== TOP-6 por BEAR-mean ==")
    for r in sorted(rows, key=lambda x: -x["bmean"])[:6]:
        rc = r["s"]["recall"]
        print(f"  {str(r['cfg']):<34} bal {r['s']['bal']:5.1f} B/Be/R {rc['BULL']:.0f}/{rc['BEAR']:.0f}/{rc['RANGE']:.0f} BEARmin {r['bmin']:.0f} BEARmean {r['bmean']:.1f}")
    print("\n== TOP-6 por balanced ==")
    for r in sorted(rows, key=lambda x: -x["s"]["bal"])[:6]:
        rc = r["s"]["recall"]
        print(f"  {str(r['cfg']):<34} bal {r['s']['bal']:5.1f} B/Be/R {rc['BULL']:.0f}/{rc['BEAR']:.0f}/{rc['RANGE']:.0f} BEARmean {r['bmean']:.1f}")
    best = max(rows, key=lambda x: x["s"]["bal"])
    print(f"\n== per-BEAR + per-JANELA (best-balanced {best['cfg']}, bal {best['s']['bal']}) ==")
    for w in GT["windows"]:
        sc = [t for t in KNOWN if w["t0"]+TOL <= t <= w["t1"]-TOL]
        if not sc: continue
        pct = 100*sum(1 for t in sc if best["lab"].get(t) == w["regime"])/len(sc)
        print(f"  {w['d0']}→{w['d1']} {w['regime']:<6}{' [nest]' if w['nested'] else '      '} {pct:5.1f}%")

if __name__ == "__main__":
    main()
