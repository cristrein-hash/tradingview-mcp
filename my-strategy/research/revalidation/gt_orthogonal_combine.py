#!/usr/bin/env python3
"""COMBINADOR (escrito ANTES de ver os resultados das famílias — grelha congelada).
Consome results/feat_<fam>_labels.json (só famílias com DA=CAUSAL_OK, passadas via --fams) +
baseline causal. Combos FECHADOS por config de família F (top-2 por família, escolhidos por
in-sample bal calculado AQUI, só t<SPLIT):
  C_R  : RANGE se F==RANGE, senão baseline          (overlay de range)
  C_D  : F se baseline==RANGE, senão baseline       (preenchimento direcional)
  C_F  : F sozinho
  C_V  : maioria(baseline, F1_top1, F2_top1) por par de famílias distintas; empate -> baseline
Seleção: rank por in-sample bal; CEGO avaliado UMA vez para o top-3 (declarado: 3 looks).
Barra: baseline cego bal 73,4. Sem P&L. Sem alterar detector."""
import json, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import gt_pivot_structural_harness as R1
SPLIT = R1.SPLIT
SC_IN = [(t, g) for t, g in R1.SCOPE if t < SPLIT]
SC_OUT = [(t, g) for t, g in R1.SCOPE if t >= SPLIT]
T2I = R1.T2I

def get_fn(labels):
    return lambda t, _l=labels: _l[T2I[t]]

def main():
    fams = sys.argv[1:]
    assert fams, "uso: gt_orthogonal_combine.py <fam1> <fam2> ... (só DA=CAUSAL_OK)"
    base_get = lambda t: R1.BASE[t]
    b_in, b_out = R1.score_fn(base_get, SC_IN), R1.score_fn(base_get, SC_OUT)
    print(f"baseline: in bal={b_in['bal']} | CEGO bal={b_out['bal']} (barra)")
    # top-2 configs por família, por in-sample bal
    top = {}
    for fam in fams:
        data = json.load(open(HERE/f"results/feat_{fam}_labels.json"))
        scored = []
        for c in data["configs"]:
            labs = c["labels"]
            s = R1.score_fn(get_fn(labs), SC_IN)
            scored.append((s["bal"], c["id"], c.get("params"), labs))
        scored.sort(key=lambda x: -x[0])
        top[fam] = scored[:2]
        for bal, cid, params, _ in scored:
            print(f"  [{fam}] {cid} {params} in_bal={bal}")
    combos = [("baseline", base_get)]
    for fam, lst in top.items():
        for bal, cid, params, labs in lst:
            f = get_fn(labs)
            combos.append((f"C_F {fam}:{cid}", f))
            combos.append((f"C_R {fam}:{cid}", lambda t, _f=f: "RANGE" if _f(t) == "RANGE" else R1.BASE[t]))
            combos.append((f"C_D {fam}:{cid}", lambda t, _f=f: _f(t) if R1.BASE[t] == "RANGE" else R1.BASE[t]))
    fkeys = list(top.keys())
    for i in range(len(fkeys)):
        for j in range(i+1, len(fkeys)):
            if not top[fkeys[i]] or not top[fkeys[j]]: continue
            f1 = get_fn(top[fkeys[i]][0][3]); f2 = get_fn(top[fkeys[j]][0][3])
            def vote(t, _f1=f1, _f2=f2):
                labs = [R1.BASE[t], _f1(t), _f2(t)]
                for cand in set(labs):
                    if labs.count(cand) >= 2: return cand
                return R1.BASE[t]
            combos.append((f"C_V {fkeys[i]}+{fkeys[j]}", vote))
    ranked = []
    for name, fn in combos:
        s = R1.score_fn(fn, SC_IN)
        ranked.append((s["bal"], name, fn, s))
    ranked.sort(key=lambda x: -x[0])
    print("\n== IN-SAMPLE (top-10) ==")
    for bal, name, _, s in ranked[:10]:
        print(f"  {name:<38} in bal={bal:5.1f} recall B/Be/R={s['recall']['BULL']}/{s['recall']['BEAR']}/{s['recall']['RANGE']}")
    print("\n== CEGO 2023-26 (só top-3 in-sample; 3 looks declarados) ==")
    for bal, name, fn, _ in ranked[:3]:
        so = R1.score_fn(fn, SC_OUT)
        print(f"  {name:<38} in bal={bal:5.1f} | CEGO bal={so['bal']:5.1f} acc={so['acc']} "
              f"recall B/Be/R={so['recall']['BULL']}/{so['recall']['BEAR']}/{so['recall']['RANGE']} "
              f"| barra {b_out['bal']} {'BATIDA' if so['bal'] > b_out['bal'] else 'NÃO batida'}")

if __name__ == "__main__":
    main()
