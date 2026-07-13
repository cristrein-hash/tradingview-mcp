#!/usr/bin/env python3
"""DETECTOR LAYER 1 ROUND 3 — BEAR com LÓGICA DUPLA informada pela análise de onsets
(ordem Cris 2026-07-13). BEAR macro = 2 mecanismos causais:
 (BEAR-1 ROLLOVER, exógeno-liderado): score de convergência dos top-rollovers — pico recente +
   corrida prévia + pullback moderado do pico + ret20<0 + DÓLAR A SUBIR. score>=K -> BEAR.
 (BEAR-2 PARABÓLICA): run120 extremo + desaceleração (ret20 caiu do pico recente) -> BEAR;
   apanha 2026 (que NÃO tem sinal de dólar).
BULL/RANGE: núcleo EMA-longo + contenção Donchian (do r2, que já capta ranges aninhados).
Histerese: uma vez em BEAR, segura até condição BULL clara (segura meses). Prioridade:
BEAR(1|2) > contenção-RANGE > núcleo(BULL/RANGE). Causal close-only. Métrica intrínseca. SEM P&L."""
import json, sys, bisect, statistics
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
EF = ema_series(C, 50); ES = ema_series(C, 200); E50 = ema_series(C, 50)

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

def rollover_score(i):
    """convergência causal (dia i fechado). Retorna (score 0-5, componentes)."""
    peak120 = max(H[i-120:i]); ipk = max(range(i-120, i), key=lambda k: H[k])
    dd_peak = (peak120-C[i-1])/peak120*100
    days_since_peak = (i-1)-ipk
    run120 = (C[i-1]/C[i-121]-1)*100
    ret20 = (C[i-1]/C[i-21]-1)*100
    t = KNOWN[i]; dxy = _at(DXY_K, DXY_RET, t)
    s = 0
    s += days_since_peak <= 45
    s += run120 >= 6
    s += 4.0 <= dd_peak <= 14.0
    s += ret20 < 0
    s += (dxy is not None and dxy > 0.5)
    return s

def parabolic(i, run_thr):
    run120 = (C[i-1]/C[i-121]-1)*100
    ret20 = (C[i-1]/C[i-21]-1)*100
    ret20_prev = (C[i-11]/C[i-31]-1)*100
    return run120 >= run_thr and ret20 < ret20_prev and ret20 < run120/6

def build(K_roll, run_thr, H_bull, W_don):
    core = "RANGE"; pend = None; pn = 0; state = "RANGE"
    out = []
    for i in range(N):
        t = KNOWN[i]
        # núcleo BULL/RANGE (EMA)
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
        # BEAR duplo
        bear = False
        if i >= 130:
            if rollover_score(i) >= K_roll: bear = True
            elif parabolic(i, run_thr): bear = True
        # máquina de estado macro (segura meses): entra BEAR por gatilho; sai p/ BULL quando núcleo BULL forte
        if bear:
            state = "BEAR"
        elif state == "BEAR":
            # sai do bear só quando núcleo vira BULL claro (EF>ES e slope+) OU novo topo 120d
            if i >= 200 and EF[i] > ES[i] and (EF[i]-EF[i-10]) > 0:
                state = "BULL" if core == "BULL" else "RANGE"
        else:
            state = "RANGE" if contained else core
        out.append((t, state))
    return out

def eff_label(t):
    hits = [w for w in GT["windows"] if w["t0"]+TOL <= t <= w["t1"]-TOL]
    return min(hits, key=lambda w: w["t1"]-w["t0"])["regime"] if hits else None
SCOPE = [(KNOWN[i], eff_label(KNOWN[i])) for i in range(N)]
SCOPE = [(t, g) for t, g in SCOPE if g is not None]

def score(lab, scope=None):
    scope = scope or SCOPE
    per = {s: {"n": 0, "ok": 0} for s in ("BULL", "BEAR", "RANGE")}; ok = 0
    for t, g in scope:
        l = lab.get(t); per[g]["n"] += 1
        if l == g: per[g]["ok"] += 1; ok += 1
    rec = {s: (round(100*per[s]["ok"]/per[s]["n"], 0) if per[s]["n"] else None) for s in per}
    bal = statistics.mean([v for v in rec.values() if v is not None])
    return {"acc": round(100*ok/len(scope), 1), "bal": round(bal, 1), "recall": rec}

def per_bear(lab):
    res = {}
    for w in GT["windows"]:
        if w["regime"] != "BEAR": continue
        sc = [t for t in KNOWN if w["t0"]+TOL <= t <= w["t1"]-TOL]
        res[w["d0"]] = round(100*sum(1 for t in sc if lab.get(t) == "BEAR")/len(sc), 0) if sc else None
    return res

GRID = [(kr, rt, hb, wd) for kr in (3, 4) for rt in (30, 40) for hb in (10, 20) for wd in (90, 180)]

def main():
    rows = []
    for cfg in GRID:
        lab = {t: l for t, l in build(*cfg)}
        s = score(lab); pb = per_bear(lab)
        vals = [v for v in pb.values() if v is not None]
        rows.append({"cfg": cfg, "s": s, "pb": pb, "bmin": min(vals), "bmean": statistics.mean(vals), "lab": lab})
    print(f"ROUND 3 · grelha {len(GRID)} · BEAR duplo (rollover exog + parabólica) · GT 16 janelas")
    print("\n== ordenado por BEAR-mean ==")
    for r in sorted(rows, key=lambda x: -x["bmean"]):
        rc = r["s"]["recall"]
        print(f"  {str(r['cfg']):<22} bal {r['s']['bal']:5.1f} B/Be/R {rc['BULL']:.0f}/{rc['BEAR']:.0f}/{rc['RANGE']:.0f} BEARmin {r['bmin']:.0f} BEARmean {r['bmean']:.1f}")
    best = max(rows, key=lambda x: x["bmean"])
    print(f"\n== per-BEAR (best BEAR-mean {best['cfg']}) ==")
    for d0, v in best["pb"].items():
        w = next(x for x in GT["windows"] if x["d0"] == d0)
        print(f"  {d0}→{w['d1']} ({w['dur_dias']:.0f}d) BEAR {v}%")
    print(f"\n== per-JANELA (best BEAR-mean, bal {best['s']['bal']}) ==")
    for w in GT["windows"]:
        sc = [t for t in KNOWN if w["t0"]+TOL <= t <= w["t1"]-TOL]
        if not sc: continue
        pct = 100*sum(1 for t in sc if best["lab"].get(t) == w["regime"])/len(sc)
        print(f"  {w['d0']}→{w['d1']} {w['regime']:<6}{' [nest]' if w['nested'] else '      '} {pct:5.1f}%")

if __name__ == "__main__":
    main()
