#!/usr/bin/env python3
"""DEEP CONFLUENCE EXHAUSTIVE — busca à exaustão de confluências 1/2/3-way (incl. features antes excluídas)
que separam o grupo-alvo do Cris {T2,T3,T4,T16,T17,T23,T24} dos demais preservados.
GUARDA ANTI-ID-FIT = TESTE DE PERMUTAÇÃO: compara a melhor confluência do alvo vs a melhor de N subsets-7
aleatórios. Se aleatórios atingem pureza igual, é overfit/hull = sem sinal real. DIAGNÓSTICO 62; sem 276/OOS.
Inclui features REFERENCE_ONLY/mortas + todas as 97 da matriz mestra (fraqueza isolada != inútil)."""
import csv, json, statistics as st
from itertools import combinations

D = "results"
rows = {r['plot_id']: r for r in csv.DictReader(open(f"{D}/l2_bpt_deep_master_matrix_62.csv"))}
tq = {r['datetime']: r for r in csv.DictReader(open(f"{D}/l2_bpt_trade_qualification_matrix.csv"))}
vm = {r['plot_id']: r for r in csv.DictReader(open(f"{D}/l2_bpt_visual_matrix_v0.csv"))}
g = json.load(open(f"{D}/_deep_groups.json"))
TARGET = g['TARGET']; PRES = g['PRES']
NONT = [p for p in PRES if p not in TARGET]  # 36 não-alvo preservados (inclui os 4 B-excluídos)

def fn(v):
    try: return float(v)
    except: return None

# adicionar features ANTES EXCLUÍDAS (mortas / reference-only)
EXTRA = ['macro_leg_direction','macro_leg_phase']
for p in rows:
    t = tq[vm[p]['datetime']]
    for k in EXTRA: rows[p][k] = t.get(k, '')

allcols = [c for c in next(iter(rows.values())) if c not in ('plot_id','set','datetime','blocked_v3')]
# construir LITERAIS (predicados binários) sobre TODAS as features
order = PRES  # universo = 43 preservados
idx = {p: i for i, p in enumerate(order)}
TGT_MASK = sum(1 << idx[p] for p in TARGET)
ALL_MASK = (1 << len(order)) - 1
def popcount(x): return bin(x).count('1')

literals = []  # (nome, mask sobre os 43)
for c in allcols:
    vals = [fn(rows[p][c]) for p in order]
    numok = sum(1 for v in vals if v is not None)
    if numok >= 35:  # numérica: terços por quantil
        nv = sorted(v for v in vals if v is not None)
        q1 = nv[len(nv)//3]; q2 = nv[2*len(nv)//3]
        for lab, pred in ((f"{c}<=q1({q1:.2f})", lambda v,t=q1: v is not None and v<=t),
                          (f"{c}>=q2({q2:.2f})", lambda v,t=q2: v is not None and v>=t)):
            mask = sum(1 << idx[order[i]] for i, v in enumerate(vals) if pred(v))
            if 3 <= popcount(mask) <= 40: literals.append((lab, mask))
    else:  # categórica: cada valor frequente
        from collections import Counter
        cv = [rows[p][c] for p in order]
        for val, n in Counter(cv).most_common():
            if n < 3 or val in ('', 'None'): continue
            mask = sum(1 << idx[order[i]] for i, x in enumerate(cv) if x == val)
            if 3 <= popcount(mask) <= 40: literals.append((f"{c}=={val}", mask))
print(f"universo: {len(order)} preservados | alvo {len(TARGET)} | literais {len(literals)}")

def best_confluence(tgt_mask, max_terms=3, min_recall=6):
    """melhor regra AND (<=max_terms) que captura >=min_recall do alvo, minimizando falsos. retorna (score,desc,tgt_cap,false)."""
    tgt_n = popcount(tgt_mask)
    best = None  # (false_count, -tgt_cap, terms)
    L = literals
    # 1-way
    cand1 = []
    for lab, m in L:
        cap = popcount(m & tgt_mask)
        if cap >= min_recall:
            fp = popcount(m & ~tgt_mask & ALL_MASK)
            cand1.append((fp, cap, [lab], m))
    # 2-way (sobre literais que sozinhos pegam >=4 do alvo, p/ podar)
    seeds = [(lab, m) for lab, m in L if popcount(m & tgt_mask) >= 4]
    cand = list(cand1)
    for i in range(len(seeds)):
        l1, m1 = seeds[i]
        for j in range(i+1, len(seeds)):
            l2, m2 = seeds[j]; m = m1 & m2
            cap = popcount(m & tgt_mask)
            if cap >= min_recall:
                fp = popcount(m & ~tgt_mask & ALL_MASK)
                cand.append((fp, cap, [l1,l2], m))
    # 3-way greedy: estender melhores 2-way
    cand.sort(key=lambda x:(x[0],-x[1]))
    for fp0,cap0,terms0,m0 in cand[:40]:
        for lab,m in seeds:
            if lab in terms0:continue
            m3=m0&m; cap=popcount(m3&tgt_mask)
            if cap>=min_recall:
                fp=popcount(m3&~tgt_mask&ALL_MASK)
                cand.append((fp,cap,terms0+[lab],m3))
    cand.sort(key=lambda x:(x[0],-x[1]))
    if not cand: return None
    fp,cap,terms,_=cand[0]
    # score = recall - false_rate
    return (cap/tgt_n - fp/(popcount(ALL_MASK)-tgt_n), terms, cap, fp)

# ALVO
res = best_confluence(TGT_MASK)
print("\n=== MELHOR CONFLUÊNCIA p/ o ALVO (>=6/7) ===")
if res:
    score, terms, cap, fp = res
    print(f"  regra: {' AND '.join(terms)}")
    print(f"  captura {cap}/7 do alvo, {fp}/36 falsos | score={score:.3f}")
else:
    print("  nenhuma regra captura >=6/7")

# PERMUTAÇÃO NULL: melhor confluência p/ subsets-7 aleatórios (determinístico via hash de índices)
print("\n=== TESTE DE PERMUTAÇÃO (anti-ID-fit) ===")
import hashlib
def pseudo_subsets(n_sub, k=7):
    out=[]
    for s in range(n_sub):
        # ordenação determinística por hash(seed,plot_id)
        ranked=sorted(order,key=lambda p:hashlib.md5(f"{s}:{p}".encode()).hexdigest())
        out.append(ranked[:k])
    return out
null_scores=[]
for sub in pseudo_subsets(120):
    sm=sum(1<<idx[p] for p in sub)
    r=best_confluence(sm)
    null_scores.append(r[0] if r else -1)
null_scores.sort()
tgt_score=res[0] if res else -1
better=sum(1 for s in null_scores if s>=tgt_score)
print(f"  score do ALVO: {tgt_score:.3f}")
print(f"  null (120 subsets-7 aleatórios): mediana {st.median(null_scores):.3f}, max {max(null_scores):.3f}, p90 {null_scores[int(.9*len(null_scores))]:.3f}")
print(f"  subsets aleatórios com score >= alvo: {better}/120  (p={better/120:.3f})")
print(f"  -> {'SINAL REAL (alvo bate o acaso, p<0.1)' if better/120<0.10 else 'ID-FIT/HULL (acaso atinge igual) = SEM sinal real'}")

json.dump(dict(target_score=tgt_score, null_median=st.median(null_scores), null_max=max(null_scores),
               p_value=better/120, rule=res[1] if res else None, cap=res[2] if res else 0, fp=res[3] if res else None),
          open(f"{D}/l2_bpt_deep_confluence_permutation.json","w"), indent=1)
print("\nsalvo -> l2_bpt_deep_confluence_permutation.json")
