#!/usr/bin/env python3
"""RE-AVALIAÇÃO PURGED/EMBARGOED K-FOLD (ordem Cris 2026-07-12 — substitui o split cronológico
2020-22/2023-26, que confundiu dificuldade das eras com qualidade dos candidatos).
PROTOCOLO CONGELADO (antes de rodar): K=5 blocos CONTÍGUOS de barras do SCOPE (por tempo);
teste = bloco k; treino = restantes blocos MENOS embargo de 15 dias em cada fronteira do bloco
de teste (purge). Por fold, seleção por bal de TREINO: leg_geometry entre as 8 configs
existentes; mtf_1d entre as 4 configs com MAPEAMENTO padrão→rótulo re-ajustado SÓ no treino do
fold (maioria GT; corrige o leak favorável do mapeamento fit-2020-22 dos labels originais).
Candidatos (só os que existem — nada novo): baseline · leg_geometry · mtf_1d_pattern ·
C_V voto(baseline, leg_sel, mtf_sel). Labels OOF: cada barra rotulada pelos parâmetros do fold
em que ela é TESTE. Report: bal médio entre folds ± dispersão + tabela das 19 janelas (OOF).
Sem re-treinar mecanismos novos. Sem tocar no detector. Sem commit. Sem P&L."""
import json, sys, bisect, statistics, datetime as dt
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import gt_pivot_structural_harness as R1
K = 5
EMBARGO_S = 15*86400
SCOPE = R1.SCOPE
T2I = R1.T2I
TS4 = R1.TS4

LEG = json.load(open(HERE/"results/feat_leg_geometry_labels.json"))["configs"]

# ---- mtf_1d: recomputar PADRÕES (mesmos params das 4 configs; mapeamento refit por fold) ----
D1 = [json.loads(l) for l in open(HERE/"raw_1d_ohlc.jsonl")]
DT = [b["t"] for b in D1]; DCLOSE = [b["c"] for b in D1]
D_KNOWN = [t+86400 for t in DT]      # dia D conhecido a partir do fecho (dia D+1)
def ema_series(vals, n):
    k2 = 2/(n+1); e = vals[0]; out = []
    for v in vals: e = v*k2 + e*(1-k2); out.append(e)
    return out
MTF_CFGS = [("c1", 21, 50, 5), ("c2", 21, 50, 10), ("c3", 10, 30, 5), ("c4", 10, 30, 10)]
def mtf_patterns(a, b, s):
    ea, eb = ema_series(DCLOSE, a), ema_series(DCLOSE, b)
    pat_d = []
    for i in range(len(DT)):
        p = (4 if DCLOSE[i] > ea[i] else 0) | (2 if ea[i] > eb[i] else 0) \
            | (1 if i >= s and ea[i] > ea[i-s] else 0)
        pat_d.append(p)
    out = []
    for t in TS4:
        j = bisect.bisect_right(D_KNOWN, t)-1
        out.append(pat_d[j] if j >= 0 else None)
    return out
MTF_PAT = {cid: mtf_patterns(a, b, s) for cid, a, b, s in MTF_CFGS}

def folds():
    n = len(SCOPE); out = []
    for k in range(K):
        lo, hi = k*n//K, (k+1)*n//K
        test = SCOPE[lo:hi]
        t0, t1 = test[0][0], test[-1][0]
        train = [(t, g) for t, g in SCOPE if t < t0-EMBARGO_S or t > t1+EMBARGO_S]
        out.append((train, test))
    return out

def bal_of(labels_at, sc):
    return R1.score_fn(labels_at, sc)["bal"]

def main():
    print(f"protocolo: K={K} blocos contíguos · embargo {EMBARGO_S//86400}d · seleção por bal de TREINO")
    oof = {"baseline": {}, "leg_geometry": {}, "mtf_1d_pattern": {}, "C_V": {}}
    fold_bals = {c: [] for c in oof}
    for fi, (train, test) in enumerate(folds(), 1):
        d0 = dt.datetime.utcfromtimestamp(test[0][0]).strftime("%Y-%m-%d")
        d1 = dt.datetime.utcfromtimestamp(test[-1][0]).strftime("%Y-%m-%d")
        # leg: seleciona config no treino
        leg_best = max(LEG, key=lambda c: bal_of(lambda t, _l=c["labels"]: _l[T2I[t]], train))
        leg_at = lambda t, _l=leg_best["labels"]: _l[T2I[t]]
        # mtf: refit mapeamento no treino, por config; seleciona config no treino
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
        mtf_bal, mtf_cid, mtf_at = max(mtf_cands, key=lambda x: x[0])
        def cv_at(t, _leg=leg_at, _mtf=mtf_at):
            labs = [R1.BASE[t], _leg(t), _mtf(t)]
            for cand in set(labs):
                if labs.count(cand) >= 2: return cand
            return R1.BASE[t]
        cands = {"baseline": (lambda t: R1.BASE[t]), "leg_geometry": leg_at,
                 "mtf_1d_pattern": mtf_at, "C_V": cv_at}
        line = f"fold {fi} teste {d0}→{d1} (n={len(test)}) sel: leg={leg_best['id']} mtf={mtf_cid} |"
        for name, fn in cands.items():
            b = bal_of(fn, test); fold_bals[name].append(b)
            line += f" {name}={b:.1f}"
            for t, g in test: oof[name][t] = fn(t)
        print(line)
    print("\n== RESUMO (bal por fold: média ± desvio) ==")
    for name in oof:
        m = statistics.mean(fold_bals[name]); sd = statistics.pstdev(fold_bals[name])
        agg = R1.score_fn(lambda t, _o=oof[name]: _o[t], SCOPE)
        print(f"  {name:<16} folds {['%.1f' % x for x in fold_bals[name]]} média {m:5.1f} ± {sd:4.1f} "
              f"| OOF agregado bal={agg['bal']} acc={agg['acc']} "
              f"recall B/Be/R={agg['recall']['BULL']}/{agg['recall']['BEAR']}/{agg['recall']['RANGE']}")
    print("\n== TABELA DAS 19 JANELAS (concordância OOF por candidato) ==")
    print(f"  {'janela':<26} {'GT':<6} " + " ".join(f"{n:<14}" for n in oof))
    for w in R1.GT["windows"]:
        sc = [(t, g) for t, g in SCOPE if w["t0"]+R1.TOL <= t <= w["t1"]-R1.TOL]
        if not sc: continue
        cells = []
        for name in oof:
            okc = sum(1 for t, g in sc if oof[name][t] == g)
            cells.append(f"{100*okc/len(sc):5.1f}%        ")
        print(f"  {w['d0']}→{w['d1']} {w['regime']:<6} " + " ".join(cells))

if __name__ == "__main__":
    main()
