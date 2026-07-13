#!/usr/bin/env python3
"""DETECTOR LAYER 1 (MACRO) — conforme LAYER1_MACRO_DETECTOR_PREREG_20260713.md (grelha congelada).
Substrato: 1D nativo (raw_1d_ohlc.jsonl). Causal close-only (dia D conhecido no fecho de D).
3 componentes, prioridade C>B>A:
 (A) núcleo tendência macro: zigzag %-reversal (p_rev) + estrutura HH/HL vs LH/LL + histerese H_macro
 (B) contenção: Donchian W_don, largura<=w_thr & close no meio -> RANGE (pega aninhados)
 (C) choque estrutural: |mov| >= s_thr% em <= s_days dias + confirmação exógena SINAL (DXY & US10Y
     na direção) -> BEAR/BULL. Único caminho p/ macro curto (nov/24).
Métrica: concordância barra-a-barra (diária) vs GT Layer 1 (rótulo efetivo = janela mais interna;
bordas ±5d fora). SEM P&L. Round 1 = reportar CURVA (por-BEAR + agregado), não escolher ótimo.
Detector 4H e leg v2 INTOCADOS."""
import json, sys, bisect, statistics, datetime as dt
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
GT = json.load(open(HERE/"results/REGIME_GT_LAYER1_CRIS_1D_20260713.json"))
TOL = GT["border_tolerance_s"]
# ---- substrato diário ----
D1 = [json.loads(l) for l in open(HERE/"raw_1d_ohlc.jsonl")]
T = [b["t"] for b in D1]; O = [b["o"] for b in D1]; H = [b["h"] for b in D1]
L = [b["l"] for b in D1]; C = [b["c"] for b in D1]
N = len(T)
KNOWN = [t+86400 for t in T]                     # dia D conhecido no fecho (D+1)
# ---- exógenas (features causais 20d, sinais) ----
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
    """+1 se DXY sobe & yields sobem (vento contra ouro = bear), -1 se ambos caem (bull), 0 misto."""
    d = _at(DXY_K, DXY_RET, t); y = _at(Y_K, Y_CHG, t)
    if d is None or y is None: return 0
    if d > 0 and y > 0: return +1
    if d < 0 and y < 0: return -1
    return 0

def zigzag_pct(p_rev):
    """pivots macro por reversão >= p_rev% do extremo. confirmed_at = fecho do dia confirmador."""
    hi, lo = [], []
    d = "UP"; ext_i = 0; ext = H[0]
    for i in range(1, N):
        if d == "UP":
            if H[i] > ext: ext = H[i]; ext_i = i
            if (ext-C[i])/ext*100 >= p_rev:
                hi.append((KNOWN[i], ext)); d = "DOWN"; ext = L[ext_i]; e2 = ext_i
                for q in range(ext_i, i+1):
                    if L[q] < ext: ext = L[q]; e2 = q
                ext_i = e2
        else:
            if L[i] < ext: ext = L[i]; ext_i = i
            if (C[i]-ext)/ext*100 >= p_rev:
                lo.append((KNOWN[i], ext)); d = "UP"; ext = H[ext_i]; e2 = ext_i
                for q in range(ext_i, i+1):
                    if H[q] > ext: ext = H[q]; e2 = q
                ext_i = e2
    return hi, lo

def build(p_rev, H_macro, W_don, w_thr, s_thr, s_days):
    hi, lo = zigzag_pct(p_rev)
    hct = [x[0] for x in hi]; lct = [x[0] for x in lo]
    core = "RANGE"; pend = None; pn = 0; hp = []; lp = []; ih = il = 0
    out = []
    for i in range(N):
        t = KNOWN[i]
        # ingest pivots confirmados <= t
        while ih < len(hi) and hi[ih][0] <= t: hp.append(hi[ih][1]); ih += 1
        while il < len(lo) and lo[il][0] <= t: lp.append(lo[il][1]); il += 1
        raw = "RANGE"
        if len(hp) >= 2 and len(lp) >= 2:
            if hp[-1] > hp[-2] and lp[-1] > lp[-2]: raw = "BULL"
            elif hp[-1] < hp[-2] and lp[-1] < lp[-2]: raw = "BEAR"
        # histerese núcleo
        if raw == core: pend = None; pn = 0
        elif raw == pend: pn += 1
        else: pend = raw; pn = 1
        if pend is not None and pn >= H_macro: core = pend; pend = None; pn = 0
        # (B) contenção Donchian (usa dias fechados <= i, i.e. i-W_don..i-1)
        contained = False
        if i >= W_don:
            hh = max(H[i-W_don:i]); ll = min(L[i-W_don:i])
            if hh > ll:
                width = (hh-ll)/C[i-1]
                pos = (C[i-1]-ll)/(hh-ll)
                contained = width <= w_thr and 0.25 <= pos <= 0.75
        # (C) choque estrutural + exógeno (usa fecho do dia i-1)
        shock = None
        if i >= s_days+1:
            mv = (C[i-1]-C[i-1-s_days])/C[i-1-s_days]*100
            ed = exog_dir(t)
            if mv <= -s_thr and ed == +1: shock = "BEAR"
            elif mv >= s_thr and ed == -1: shock = "BULL"
        # prioridade C > B > A
        label = shock or ("RANGE" if contained else core)
        out.append((t, label))
    return out

# ---- scoring vs GT (rótulo efetivo = janela mais interna; ±TOL fora) ----
def eff_label(t):
    hits = [w for w in GT["windows"] if w["t0"]+TOL <= t <= w["t1"]-TOL]
    if not hits: return None
    return min(hits, key=lambda w: w["t1"]-w["t0"])["regime"]   # mais interna = menor duração

SCOPE = [(KNOWN[i], eff_label(KNOWN[i])) for i in range(N)]
SCOPE = [(t, g) for t, g in SCOPE if g is not None]

def score(labels_by_t, scope=None):
    scope = scope or SCOPE
    per = {s: {"n": 0, "ok": 0} for s in ("BULL", "BEAR", "RANGE")}
    ok = 0
    for t, g in scope:
        lab = labels_by_t.get(t)
        per[g]["n"] += 1
        if lab == g: per[g]["ok"] += 1; ok += 1
    rec = {s: (100*per[s]["ok"]/per[s]["n"] if per[s]["n"] else None) for s in per}
    bal = statistics.mean([v for v in rec.values() if v is not None])
    return {"n": len(scope), "acc": round(100*ok/len(scope), 1), "bal": round(bal, 1), "recall": rec}

GRID = [(p, hm, wd, wt, st, sd)
        for p in (8, 12, 18) for hm in (10, 20) for wd in (60, 120)
        for wt in (0.10, 0.15) for st in (8, 12) for sd in (8, 15)]

def per_bear(labels_by_t):
    """recall de cada janela BEAR do GT (as 5) — a SHORT depende disto."""
    res = {}
    for w in GT["windows"]:
        if w["regime"] != "BEAR": continue
        sc = [t for t in KNOWN if w["t0"]+TOL <= t <= w["t1"]-TOL]
        if not sc: res[w["d0"]] = None; continue
        res[w["d0"]] = round(100*sum(1 for t in sc if labels_by_t.get(t) == "BEAR")/len(sc), 0)
    return res

def main():
    rows = []
    for cfg in GRID:
        lab = {t: l for t, l in build(*cfg)}
        s = score(lab); pb = per_bear(lab)
        bear_min = min([v for v in pb.values() if v is not None])
        bear_mean = statistics.mean([v for v in pb.values() if v is not None])
        rows.append({"cfg": cfg, "s": s, "pb": pb, "bear_min": bear_min, "bear_mean": bear_mean, "lab": lab})
    # CURVA: ordenar por BEAR mean (o "melhor possível" p/ BEAR), mostrar trade-off
    rows.sort(key=lambda r: -r["bear_mean"])
    print("== TOP-8 por BEAR-mean (curva; sem escolher ótimo) ==")
    print(f"  {'cfg(p,H,Wd,wt,st,sd)':<28} {'bal':>5} {'B/Be/R recall':>18} {'BEARmin':>7} {'BEARmean':>8}")
    for r in rows[:8]:
        rc = r["s"]["recall"]
        print(f"  {str(r['cfg']):<28} {r['s']['bal']:5.1f} "
              f"{rc['BULL']:.0f}/{rc['BEAR']:.0f}/{rc['RANGE']:.0f}".rjust(18) +
              f" {r['bear_min']:7.0f} {r['bear_mean']:8.1f}")
    print("\n== TOP-4 por balanced (contraste) ==")
    for r in sorted(rows, key=lambda x: -x["s"]["bal"])[:4]:
        rc = r["s"]["recall"]
        print(f"  {str(r['cfg']):<28} bal {r['s']['bal']:5.1f} B/Be/R {rc['BULL']:.0f}/{rc['BEAR']:.0f}/{rc['RANGE']:.0f} BEARmean {r['bear_mean']:.1f}")
    # per-BEAR detalhado do melhor-BEAR
    best = rows[0]
    print(f"\n== per-BEAR (config best-BEAR {best['cfg']}) ==")
    for d0, v in best["pb"].items():
        w = next(x for x in GT["windows"] if x["d0"] == d0)
        print(f"  {d0}→{w['d1']} ({w['dur_dias']:.0f}d) BEAR recall {v}%")
    print("\n== per-JANELA (best-BEAR) — todas as 16 ==")
    for w in GT["windows"]:
        sc = [t for t in KNOWN if w["t0"]+TOL <= t <= w["t1"]-TOL]
        if not sc: continue
        pct = 100*sum(1 for t in sc if best["lab"].get(t) == w["regime"])/len(sc)
        print(f"  {w['d0']}→{w['d1']} {w['regime']:<6}{' [nest]' if w['nested'] else '      '} {pct:5.1f}%")

if __name__ == "__main__":
    main()
