#!/usr/bin/env python3
"""LAYER 1 ROUND 3b — incorpora a DICA do Cris: queda-relâmpago 1-2 dias = BEAR causal forte
(2026 caiu −9,1%/1d, −13,2%/2d = extremo; p1% histórico −2,7/−3,7). Gatilho CRASH limpo e raro
substitui a parabólica confusa E permite APERTAR o rollover (K maior) para recuperar o RANGE que
o r3 colapsou. BEAR = 3 gatilhos causais: rollover(exog) · crash(1-2d) · [parabólica opcional off].
BULL/RANGE = núcleo EMA + contenção (r3). FSM segura BEAR meses. Causal. Métrica intrínseca. SEM P&L."""
import json, sys, bisect, statistics
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import layer1_macro_detector_r3 as R
GT, TOL, KNOWN, N = R.GT, R.TOL, R.KNOWN, R.N
C, H, L, EF, ES = R.C, R.H, R.L, R.EF, R.ES
atr = R.atr; rollover_score = R.rollover_score; eff_label = R.eff_label

def crash(i, d1_thr, d2_thr):
    d1 = (C[i-1]/C[i-2]-1)*100
    d2 = (C[i-1]/C[i-3]-1)*100
    return d1 <= d1_thr or d2 <= d2_thr

def build(K_roll, d1_thr, d2_thr, H_bull, W_don):
    core = "RANGE"; pend = None; pn = 0; state = "RANGE"
    out = []
    for i in range(N):
        t = KNOWN[i]
        raw = "RANGE"
        if i >= 200:
            a = atr(i) or 1.0; slope = (EF[i]-EF[i-10])/a
            if EF[i] > ES[i] and slope > 0.05: raw = "BULL"
            elif EF[i] < ES[i] and slope < -0.05: raw = "BEAR"
        if raw == core: pend = None; pn = 0
        elif raw == pend: pn += 1
        else: pend = raw; pn = 1
        if pend is not None and pn >= H_bull: core = pend; pend = None; pn = 0
        contained = False
        if i >= W_don:
            hh = max(H[i-W_don:i]); ll = min(L[i-W_don:i])
            if hh > ll:
                pos = (C[i-1]-ll)/(hh-ll); a = atr(i) or 1.0
                sl = (EF[i-1]-EF[i-11])/a
                contained = 0.2 <= pos <= 0.8 and abs(sl) < 0.05
        bear = False
        if i >= 130:
            if rollover_score(i) >= K_roll: bear = True
            elif crash(i, d1_thr, d2_thr): bear = True
        if bear:
            state = "BEAR"
        elif state == "BEAR":
            if i >= 200 and EF[i] > ES[i] and (EF[i]-EF[i-10]) > 0:
                state = "BULL" if core == "BULL" else "RANGE"
        else:
            state = "RANGE" if contained else core
        out.append((t, state))
    return out

SCOPE = R.SCOPE
def score(lab):
    per = {s: {"n": 0, "ok": 0} for s in ("BULL", "BEAR", "RANGE")}; ok = 0
    for t, g in SCOPE:
        l = lab.get(t); per[g]["n"] += 1
        if l == g: per[g]["ok"] += 1; ok += 1
    rec = {s: (round(100*per[s]["ok"]/per[s]["n"], 0) if per[s]["n"] else None) for s in per}
    bal = statistics.mean([v for v in rec.values() if v is not None])
    return {"acc": round(100*ok/len(SCOPE), 1), "bal": round(bal, 1), "recall": rec}
def per_bear(lab):
    res = {}
    for w in GT["windows"]:
        if w["regime"] != "BEAR": continue
        sc = [t for t in KNOWN if w["t0"]+TOL <= t <= w["t1"]-TOL]
        res[w["d0"]] = round(100*sum(1 for t in sc if lab.get(t) == "BEAR")/len(sc), 0) if sc else None
    return res

GRID = [(kr, d1, d2, hb, wd) for kr in (4, 5) for (d1, d2) in ((-5.0, -6.0), (-4.0, -5.0))
        for hb in (10, 20) for wd in (90, 180)]

def main():
    rows = []
    for cfg in GRID:
        lab = {t: l for t, l in build(*cfg)}
        s = score(lab); pb = per_bear(lab)
        vals = [v for v in pb.values() if v is not None]
        rows.append({"cfg": cfg, "s": s, "pb": pb, "bmin": min(vals), "bmean": statistics.mean(vals), "lab": lab})
    print(f"ROUND 3b · grelha {len(GRID)} · BEAR triplo (rollover exog + CRASH 1-2d) · GT 16 janelas")
    print("\n== ordenado por balanced (BEAR já alto; ver se RANGE recupera) ==")
    for r in sorted(rows, key=lambda x: -x["s"]["bal"]):
        rc = r["s"]["recall"]
        print(f"  {str(r['cfg']):<28} bal {r['s']['bal']:5.1f} B/Be/R {rc['BULL']:.0f}/{rc['BEAR']:.0f}/{rc['RANGE']:.0f} BEARmin {r['bmin']:.0f} BEARmean {r['bmean']:.1f}")
    best = max(rows, key=lambda x: x["s"]["bal"])
    print(f"\n== per-BEAR (best balanced {best['cfg']}, bal {best['s']['bal']}) ==")
    for d0, v in best["pb"].items():
        w = next(x for x in GT["windows"] if x["d0"] == d0)
        print(f"  {d0}→{w['d1']} ({w['dur_dias']:.0f}d) BEAR {v}%")
    print(f"\n== per-JANELA (best balanced) ==")
    for w in GT["windows"]:
        sc = [t for t in KNOWN if w["t0"]+TOL <= t <= w["t1"]-TOL]
        if not sc: continue
        pct = 100*sum(1 for t in sc if best["lab"].get(t) == w["regime"])/len(sc)
        print(f"  {w['d0']}→{w['d1']} {w['regime']:<6}{' [nest]' if w['nested'] else '      '} {pct:5.1f}%")

if __name__ == "__main__":
    main()
