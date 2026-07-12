#!/usr/bin/env python3
"""HARNESS GT×DETECTOR 4H (prompt Cris/Claude-chat 2026-07-12). Métrica ÚNICA = concordância
barra-a-barra com o GT congelado REGIME_GT_CRIS_4H_20260712.json (19 janelas; bordas ±3d
EXCLUÍDAS). SEM P&L de L1/L2 em nenhum ponto. Causal close-only (convenção do fix ovr_at:
última barra FECHADA ≤ t; estável = dia ANTERIOR; CONTAINED = ER diário conhecido no fecho de
D aplicado a partir de D+1). Dados: raw_4h/raw_1h_ohlc.jsonl (RAW ONLY, extraídos do HD GUTS
LACIE via extract_raw_ohlc.py). Nenhuma alteração ao detector de produção/pesquisa.

PASSO 1 baseline (config atual K5/K5, dd 6%) agregada + por janela.
PASSO 2 triagem contenção ER(N=120) diário 2020-26, grelha congelada θ×M (prereg), saldo pp.
PASSO 3 grelha fechada: dd_override {6,5,4.5,4,3.5}% × K_entrada {3,5} × K_saída {5,8,12}
        (histerese assimétrica p/ BULL E BEAR: sair de estado direcional exige K_saída).
PASSO 4 curva completa (recall e falsos por estado) — reportar, NÃO escolher ótimo.
PASSO 5 split: seleção declarada = max balanced-accuracy em 2020-2022 → congela → cego 2023-26."""
import io, json, sys, bisect, contextlib, datetime as dt
import importlib.util
from pathlib import Path
HERE = Path(__file__).resolve().parent
GT = json.load(open(HERE/"results/REGIME_GT_CRIS_4H_20260712.json"))
TOL = GT["border_tolerance_s"]
DD_GRID = [0.06, 0.05, 0.045, 0.04, 0.035]
KIN_GRID = [3, 5]
KOUT_GRID = [5, 8, 12]
ER_N = 120
ER_TH = [0.10, 0.15, 0.20, 0.25]
ER_M = [5, 10]
SPLIT = int(dt.datetime(2023, 1, 1, tzinfo=dt.timezone.utc).timestamp())

def load_engine():
    spec = importlib.util.spec_from_file_location("eng", HERE/"engine_4h_regime_gate_RAW.py")
    eng = importlib.util.module_from_spec(spec)
    with contextlib.redirect_stdout(io.StringIO()):
        spec.loader.exec_module(eng)
    return eng

ENG = load_engine()

def stable_series(k_in, k_out):
    out = []; cur = "RANGE"; pend = None; pn = 0
    for v in ENG.rawS:
        if v == cur: pend = None; pn = 0
        elif v == pend: pn += 1
        else: pend = v; pn = 1
        need = k_out if cur in ("BULL", "BEAR") else k_in
        if pend is not None and pn >= need: cur = pend; pend = None; pn = 0
        out.append(cur)
    return out

def ov_arrays(dd):
    return (ENG.override(ENG.TS1, ENG.C1, ENG.H1, 48, 24, dd, 120),
            ENG.override(ENG.TS4, ENG.C4, ENG.H4, 12, 6, dd, 30))

def make_regime(stable, OV1, OV4):
    def regime_at(ts):
        di = bisect.bisect_left(ENG.DK, ts//86400)-1
        st = "RANGE" if di < 0 else stable[di]
        if ts >= ENG.T1MIN:
            j = bisect.bisect_right(ENG.TS1, ts-3600)-1; ov = OV1[j] if j >= 0 else False
        else:
            j = bisect.bisect_right(ENG.TS4, ts-14400)-1; ov = OV4[j] if j >= 0 else False
        return "BEAR" if (ov or st == "BEAR") else st
    return regime_at

# ---- escopo GT: barras 4H dentro das janelas menos ±TOL; overlap -> janela mais recente ----
def gt_scope():
    scoped = []
    for t in ENG.TS4:
        hits = [w for w in GT["windows"] if w["t0"]+TOL <= t <= w["t1"]-TOL]
        if not hits: continue
        scoped.append((t, max(hits, key=lambda w: w["t0"])["regime"]))
    return scoped

SCOPE = gt_scope()

def score(regime_at, scope=None):
    scope = scope or SCOPE
    per = {s: {"n": 0, "ok": 0, "false": 0} for s in ("BULL", "BEAR", "RANGE")}
    ok = 0
    for t, g in scope:
        lab = regime_at(t)
        per[g]["n"] += 1
        if lab == g: per[g]["ok"] += 1; ok += 1
        else: per[lab]["false"] += 1
    n = len(scope)
    rec = {s: (100*per[s]["ok"]/per[s]["n"] if per[s]["n"] else None) for s in per}
    bal = sum(v for v in rec.values() if v is not None)/sum(1 for v in rec.values() if v is not None)
    return {"n": n, "acc": round(100*ok/n, 1), "bal": round(bal, 1),
            "recall": {k: (round(v, 1) if v is not None else None) for k, v in rec.items()},
            "false": {s: per[s]["false"] for s in per}}

def main():
    # sanity: reimplementação (K5/K5, dd6%) == engine pós-fix, barra a barra
    base = make_regime(stable_series(5, 5), ENG.OV1, ENG.OV4)
    mism = sum(1 for t in ENG.TS4 if base(t) != ENG.regime_at(t))
    assert mism == 0, f"REIMPLEMENTAÇÃO DIVERGE DO ENGINE: {mism} barras"
    print("SANITY: reimplementação == engine (0 divergências)\n")

    print("== PASSO 1 — BASELINE (K5/K5, dd6%) ==")
    b = score(base)
    print(json.dumps(b, ensure_ascii=False))
    for w in GT["windows"]:
        sc = [(t, g) for t, g in SCOPE if w["t0"]+TOL <= t <= w["t1"]-TOL and g == w["regime"]]
        if not sc: continue
        s = score(base, sc)
        print(f"  {w['d0']}→{w['d1']} {w['regime']:<6} concord {s['acc']:5.1f}% (n={s['n']})")

    print("\n== PASSO 2 — TRIAGEM CONTENÇÃO ER(N=120) diário 2020-26 (overlay no baseline) ==")
    # ER causal: eff no fecho do dia i aplica a partir de i+1
    DC = ENG.DC; nd = len(DC)
    diffs = [0.0]+[abs(DC[i]-DC[i-1]) for i in range(1, nd)]
    pref = [0.0]
    for d in diffs: pref.append(pref[-1]+d)
    eff = [None]*nd
    for i in range(ER_N, nd):
        path = pref[i+1]-pref[i-ER_N+1]
        eff[i] = abs(DC[i]-DC[i-ER_N])/path if path > 0 else 0.0
    best_net = -1e9
    for th in ER_TH:
        for M in ER_M:
            cont = [False]*nd; run = 0
            for i in range(nd):
                run = run+1 if (eff[i] is not None and eff[i] < th) else 0
                cont[i] = run >= M
            def reg_c(ts, _c=cont):
                di = bisect.bisect_left(ENG.DK, ts//86400)-1   # di = dia ANTERIOR ao dia de ts
                if di >= 0 and _c[di]:            # CONTAINED do fecho de D-1 (causal; DA corrigiu D-2→D-1)
                    return "RANGE"
                return base(ts)
            lost = sum(1 for t, g in SCOPE if g in ("BULL", "BEAR") and base(t) == g and reg_c(t) != g)
            gain = sum(1 for t, g in SCOPE if g == "RANGE" and base(t) != g and reg_c(t) == g)
            net_pp = round(100*(gain-lost)/len(SCOPE), 2)
            best_net = max(best_net, net_pp)
            print(f"  θ={th:<5} M={M:<3} perdidas(BULL/BEAR certas→RANGE)={lost:<5} "
                  f"ganhas(RANGE)={gain:<5} saldo={net_pp:+.2f} pp")
    print(f"  VEREDICTO TRIAGEM: {'ARQUIVAR CONTENÇÃO (saldo ≤ 0 em toda a grelha)' if best_net <= 0 else 'segue viva (algum saldo > 0)'}")

    print("\n== PASSO 3/4 — GRELHA dd × K_in × K_out (curva completa; sem escolher ótimo) ==")
    rows = []
    for dd in DD_GRID:
        OV1, OV4 = ov_arrays(dd)
        for ki in KIN_GRID:
            for ko in KOUT_GRID:
                r = make_regime(stable_series(ki, ko), OV1, OV4)
                s = score(r)
                rows.append((dd, ki, ko, s, r))
                print(f"  dd={dd:<6} Kin={ki} Kout={ko:<3} acc={s['acc']:5.1f} bal={s['bal']:5.1f} "
                      f"recall B/Be/R={s['recall']['BULL']}/{s['recall']['BEAR']}/{s['recall']['RANGE']} "
                      f"falsos B/Be/R={s['false']['BULL']}/{s['false']['BEAR']}/{s['false']['RANGE']}")

    print("\n== PASSO 5 — SPLIT 2020-22 (desenho) → 2023-26 (cego) ==")
    sc_in = [(t, g) for t, g in SCOPE if t < SPLIT]
    sc_out = [(t, g) for t, g in SCOPE if t >= SPLIT]
    print(f"  barras in={len(sc_in)} out={len(sc_out)} · regra de seleção DECLARADA: max bal-accuracy in-sample")
    ranked = sorted(rows, key=lambda x: -score(x[4], sc_in)["bal"])
    for tag, (dd, ki, ko, _, r) in [("VENCEDOR-IS", ranked[0]), ("2º-IS", ranked[1]), ("baseline", (0.06, 5, 5, None, base))]:
        si, so = score(r, sc_in), score(r, sc_out)
        print(f"  {tag:<12} dd={dd} Kin={ki} Kout={ko} | IN acc={si['acc']} bal={si['bal']} "
              f"| OUT acc={so['acc']} bal={so['bal']} recall B/Be/R={so['recall']['BULL']}/{so['recall']['BEAR']}/{so['recall']['RANGE']}")

if __name__ == "__main__":
    main()
