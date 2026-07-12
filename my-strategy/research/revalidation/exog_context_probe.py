#!/usr/bin/env python3
"""FASE 0/1 — LEITURA DE CONTEXTO EXÓGENO (DXY + US10Y) PARA O REGIME DETECTOR 4H.
Sonda de separação POR CASO (padrão obrigatório: sonda ANTES de qualquer regra/threshold).
Casos = 7 janelas do GT com concordância <60%. População de proteção por tipo de caso:
  - casos DIRECIONAIS (regra forçaria direção): proteção = 4 janelas RANGE do GT
  - caso RANGE (C3; regra forçaria range): proteção = todas as janelas BULL+BEAR do GT
Features exógenas CAUSAIS diárias (set fechado, sem thresholds ajustados):
  dxy_ret20 = DXY close/close[-20]−1 (%) · dxy_slope = ΔEMA20(5d)/ATR14
  y_chg20   = ΔUS10Y em 20d (pontos de yield) · y_slope = ΔEMA20(5d)/ATR14
Regra de veredicto DECLARADA: sobreposição = fração da proteção além da mediana do caso
(no sentido do caso); <10% SEPARA · 10-30% PARCIAL · >30% NÃO SEPARA.
Sem regras, sem fit, sem P&L. Output: fichas impressas + results/exog_case_probe_20260712.json"""
import json, statistics, datetime as dt
from pathlib import Path
HERE = Path(__file__).resolve().parent
GT = json.load(open(HERE/"results/REGIME_GT_CRIS_4H_20260712.json"))

def load(fn):
    rows = [json.loads(l) for l in open(HERE/fn)]
    return [r["t"] for r in rows], [r["c"] for r in rows], [r["h"] for r in rows], [r["l"] for r in rows]

def ema(vals, n):
    k = 2/(n+1); e = vals[0]; out = []
    for v in vals: e = v*k + e*(1-k); out.append(e)
    return out

def feats(fn):
    T, C, H, L = load(fn)
    E20 = ema(C, 20)
    TR = [0.0]+[max(H[i]-L[i], abs(H[i]-C[i-1]), abs(L[i]-C[i-1])) for i in range(1, len(T))]
    def atr(i, n=14):
        a = TR[max(1, i-n+1):i+1]; return sum(a)/len(a) if a else 1.0
    ret20 = [None]*len(T); slope = [None]*len(T); chg20 = [None]*len(T)
    for i in range(len(T)):
        if i >= 20:
            ret20[i] = 100*(C[i]/C[i-20]-1)
            chg20[i] = C[i]-C[i-20]
        if i >= 5:
            slope[i] = (E20[i]-E20[i-5])/(atr(i) or 1.0)
    return T, {"ret20": ret20, "slope": slope, "chg20": chg20}

DXY_T, DXY = feats("raw_dxy_1d.jsonl")
Y_T, Y = feats("raw_us10y_1d.jsonl")

CASES = [
    ("C1 V-turn pós-COVID",  "2020-03-24", "BULL"),
    ("C2 nov/2024 BEAR",     "2024-11-10", "BEAR"),
    ("C3 range 2021-22",     "2021-08-31", "RANGE"),
    ("C4 BULL abr-jun/21",   "2021-04-09", "BULL"),
    ("C5 BULL fev-abr/22",   "2022-02-16", "BULL"),
    ("C6 BEAR gigante",      "2020-08-11", "BEAR"),
    ("C7 BEAR jun-ago/21",   "2021-06-11", "BEAR"),
]
FEATS = [("dxy_ret20", DXY_T, DXY["ret20"]), ("dxy_slope", DXY_T, DXY["slope"]),
         ("y_chg20", Y_T, Y["chg20"]), ("y_slope", Y_T, Y["slope"])]

def win_by_d0(d0): return next(w for w in GT["windows"] if w["d0"] == d0)

def pop_vals(T, V, windows):
    out = []
    for i, t in enumerate(T):
        if V[i] is None: continue
        if any(w["t0"] <= t <= w["t1"] for w in windows): out.append(V[i])
    return out

def q(xs, p):
    s = sorted(xs); return s[min(len(s)-1, int(p*len(s)))]

def main():
    prot_dir = [w for w in GT["windows"] if w["regime"] == "RANGE"]
    prot_rng = [w for w in GT["windows"] if w["regime"] in ("BULL", "BEAR")]
    out = {"frozen_verdict_rule": "overlap <10% SEPARA · 10-30% PARCIAL · >30% NAO", "cases": []}
    for name, d0, reg in CASES:
        w = win_by_d0(d0)
        prot = prot_rng if reg == "RANGE" else prot_dir
        ficha = {"case": name, "window": [w["d0"], w["d1"]], "gt": reg, "feats": {}}
        print(f"\n== {name} ({w['d0']}→{w['d1']}, GT={reg}) · proteção = "
              f"{'janelas direcionais' if reg == 'RANGE' else '4 janelas RANGE'} ==")
        for fname, T, V in FEATS:
            a = pop_vals(T, V, [w]); b = pop_vals(T, V, prot)
            if len(a) < 3:
                print(f"  {fname:<10} n_caso={len(a)} — INSUFICIENTE"); continue
            med_a = statistics.median(a)
            # sentido do caso: acima ou abaixo da mediana da proteção
            med_b = statistics.median(b)
            if med_a >= med_b:
                overlap = 100*sum(1 for x in b if x >= med_a)/len(b); sent = ">="
            else:
                overlap = 100*sum(1 for x in b if x <= med_a)/len(b); sent = "<="
            verdict = "SEPARA" if overlap < 10 else ("PARCIAL" if overlap <= 30 else "NAO")
            ficha["feats"][fname] = {"n_caso": len(a), "med_caso": round(med_a, 3),
                                      "p25_caso": round(q(a, .25), 3), "p75_caso": round(q(a, .75), 3),
                                      "med_prot": round(med_b, 3), "p25_prot": round(q(b, .25), 3),
                                      "p75_prot": round(q(b, .75), 3),
                                      "overlap_pct": round(overlap, 1), "verdict": verdict}
            f = ficha["feats"][fname]
            print(f"  {fname:<10} caso: med={f['med_caso']:+.2f} [{f['p25_caso']:+.2f},{f['p75_caso']:+.2f}] "
                  f"(n={len(a)}) | prot: med={f['med_prot']:+.2f} [{f['p25_prot']:+.2f},{f['p75_prot']:+.2f}] "
                  f"| prot {sent} med_caso: {overlap:.1f}% -> {verdict}")
        out["cases"].append(ficha)
    (HERE/"results/exog_case_probe_20260712.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))
    print("\nsalvo: results/exog_case_probe_20260712.json")

if __name__ == "__main__":
    main()
