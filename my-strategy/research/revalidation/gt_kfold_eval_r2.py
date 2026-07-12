#!/usr/bin/env python3
"""K-FOLD r2 (ordem Cris 2026-07-12): (1) embargo CORRIGIDO — purge por JANELA GT: além do
embargo de 15d, o treino EXCLUI todas as barras de qualquer janela GT que toque o bloco de
teste (mata a partilha das 4 janelas longas dos folds 2/4/5). (2) novo candidato HIERÁRQUICO:
baseline decide RANGE vs direcional; se direcional, a direção vem do mtf_1d (se o mtf disser
RANGE, mantém a direção do baseline — regra declarada). (3) comparação baseline · C_V · HIER
no MESMO k-fold corrigido. CRITÉRIO DE APROVAÇÃO CONGELADO (Cris): HIER adotado só se
OOF bal > 64,1 E recall RANGE OOF >= 53,1 E janela nov/2024 predominantemente BEAR (>50%).
As três. Sem tocar no detector. Sem commit. Sem P&L."""
import json, sys, bisect, statistics, datetime as dt
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import gt_pivot_structural_harness as R1
from gt_kfold_eval import LEG, MTF_PAT, K, EMBARGO_S   # reutiliza dados/padrões já auditados
SCOPE, T2I = R1.SCOPE, R1.T2I
WINS = R1.GT["windows"]

def win_of(t):
    hits = [w for w in WINS if w["t0"] <= t <= w["t1"]]
    return max(hits, key=lambda w: w["t0"])["id"] if hits else None

def folds():
    n = len(SCOPE); out = []
    for k in range(K):
        lo, hi = k*n//K, (k+1)*n//K
        test = SCOPE[lo:hi]
        t0, t1 = test[0][0], test[-1][0]
        test_wins = {win_of(t) for t, _ in test} - {None}
        train = [(t, g) for t, g in SCOPE
                 if (t < t0-EMBARGO_S or t > t1+EMBARGO_S) and win_of(t) not in test_wins]
        out.append((train, test, test_wins))
    return out

def bal_of(fn, sc): return R1.score_fn(fn, sc)["bal"]

def main():
    print(f"protocolo r2: K={K} · embargo 15d + PURGE POR JANELA GT (janela tocada pelo teste sai do treino inteira)")
    oof = {"baseline": {}, "C_V": {}, "HIER": {}}
    fold_bals = {c: [] for c in oof}
    for fi, (train, test, twins) in enumerate(folds(), 1):
        d0 = dt.datetime.utcfromtimestamp(test[0][0]).strftime("%Y-%m-%d")
        d1 = dt.datetime.utcfromtimestamp(test[-1][0]).strftime("%Y-%m-%d")
        leg_best = max(LEG, key=lambda c: bal_of(lambda t, _l=c["labels"]: _l[T2I[t]], train))
        leg_at = lambda t, _l=leg_best["labels"]: _l[T2I[t]]
        mtf_cands = []
        for cid, pat in MTF_PAT.items():
            cnt = {}
            for t, g in train:
                p = pat[T2I[t]]
                if p is None: continue
                cnt.setdefault(p, {"BULL": 0, "BEAR": 0, "RANGE": 0})[g] += 1
            mapping = {p: max(v, key=v.get) for p, v in cnt.items()}
            fn = lambda t, _p=pat, _m=mapping: _m.get(_p[T2I[t]], "RANGE")
            mtf_cands.append((bal_of(fn, train), cid, fn))
        _, mtf_cid, mtf_at = max(mtf_cands, key=lambda x: x[0])
        def cv_at(t, _leg=leg_at, _mtf=mtf_at):
            labs = [R1.BASE[t], _leg(t), _mtf(t)]
            for cand in set(labs):
                if labs.count(cand) >= 2: return cand
            return R1.BASE[t]
        def hier_at(t, _mtf=mtf_at):
            b = R1.BASE[t]
            if b == "RANGE": return "RANGE"
            m = _mtf(t)
            return m if m in ("BULL", "BEAR") else b
        cands = {"baseline": (lambda t: R1.BASE[t]), "C_V": cv_at, "HIER": hier_at}
        line = f"fold {fi} teste {d0}→{d1} (n={len(test)}, treino n={len(train)}, janelas purgadas {len(twins)}) sel leg={leg_best['id']} mtf={mtf_cid} |"
        for name, fn in cands.items():
            b = bal_of(fn, test); fold_bals[name].append(b)
            line += f" {name}={b:.1f}"
            for t, g in test: oof[name][t] = fn(t)
        print(line)
    print("\n== RESUMO ==")
    agg = {}
    for name in oof:
        m = statistics.mean(fold_bals[name]); sd = statistics.pstdev(fold_bals[name])
        a = R1.score_fn(lambda t, _o=oof[name]: _o[t], SCOPE); agg[name] = a
        print(f"  {name:<9} folds {['%.1f' % x for x in fold_bals[name]]} média {m:5.1f} ± {sd:4.1f} "
              f"| OOF bal={a['bal']} acc={a['acc']} recall B/Be/R={a['recall']['BULL']}/{a['recall']['BEAR']}/{a['recall']['RANGE']}")
    print("\n== TABELA DAS 19 JANELAS (OOF) ==")
    print(f"  {'janela':<26} {'GT':<6} " + " ".join(f"{n:<10}" for n in oof))
    nov24 = {}
    for w in WINS:
        sc = [(t, g) for t, g in SCOPE if w["t0"]+R1.TOL <= t <= w["t1"]-R1.TOL]
        if not sc: continue
        cells = []
        for name in oof:
            pct = 100*sum(1 for t, g in sc if oof[name][t] == g)/len(sc)
            cells.append(f"{pct:5.1f}%    ")
            if w["d0"] == "2024-11-10": nov24[name] = pct
        print(f"  {w['d0']}→{w['d1']} {w['regime']:<6} " + " ".join(cells))
    print("\n== CRITÉRIO CONGELADO (HIER adotado só se as TRÊS) ==")
    h = agg["HIER"]
    c1 = h["bal"] > 64.1; c2 = h["recall"]["RANGE"] >= 53.1; c3 = nov24.get("HIER", 0) > 50
    print(f"  1) OOF bal > 64,1        : {h['bal']} -> {'PASS' if c1 else 'FAIL'}")
    print(f"  2) recall RANGE >= 53,1  : {h['recall']['RANGE']} -> {'PASS' if c2 else 'FAIL'}")
    print(f"  3) nov/2024 BEAR > 50%   : {nov24.get('HIER', 0):.1f}% -> {'PASS' if c3 else 'FAIL'}")
    print(f"  VEREDICTO: {'ADOTÁVEL' if (c1 and c2 and c3) else 'NÃO ADOTADO'}")

if __name__ == "__main__":
    main()
