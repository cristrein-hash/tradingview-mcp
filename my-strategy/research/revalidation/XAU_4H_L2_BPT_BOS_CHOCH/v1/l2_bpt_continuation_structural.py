#!/usr/bin/env python3
"""CAMADA 3b — CONTINUAÇÃO ESTRUTURAL. 'Mesmo movimento' = entradas que partem do MESMO swing HIGH significativo
(o swing OPOSTO de onde o dip caiu — a origem da perna). Liga 4926 ao mesmo topo pré-flush do 4918, a dias de
distância. Swing high CAUSAL (confirmado K barras depois) + SIGNIFICATIVO (proeminência >= PROM*ATR). NÃO usa outcome."""
import json, csv
D="results"; RR="repro_recovery"
F=[json.loads(l) for l in open(f"{RR}/raw_features_2020_2026.jsonl")]
H=[r['high'] for r in F]; L=[r['low'] for r in F]; Cl=[r['close'] for r in F]; TS=[r['ts_epoch'] for r in F]
import datetime as dt
def d10(t): return dt.datetime.utcfromtimestamp(t).strftime('%Y-%m-%d')
# ATR14
ATR=[None]*len(F); trs=[]
for i in range(1,len(F)):
    trs.append(max(H[i]-L[i],abs(H[i]-Cl[i-1]),abs(L[i]-Cl[i-1])))
    if i>=14: ATR[i]=sum(trs[i-14:i])/14
EP=sorted(int(json.loads(l)['episode_id']) for l in open(f"{D}/l2_bpt_episode_readings_276.jsonl"))
PK={int(json.loads(l)['episode_id']):json.loads(l) for l in open(f"{D}/l2_bpt_episode_context_packets_276.jsonl")}
def mfe(b): return PK[b]['_AUDIT_outcome_NOT_FOR_READING']['mfe_R']
K=4          # força do fractal (swing high = máximo numa janela de K barras de cada lado)
PROM=1.2     # proeminência mínima em ATR (filtra wiggles, mantém topos de perna)

def is_pivot_high(i):
    if i-K<0 or i+K>=len(H) or ATR[i] is None: return False
    hi=H[i]
    if not (all(H[j]<=hi for j in range(i-K,i)) and all(H[j]<=hi for j in range(i+1,i+K+1))): return False
    # proeminência: o topo se destaca >= PROM*ATR acima do menor low na janela
    lows=[L[j] for j in range(i-K,i+K+1)]
    return (hi-min(lows))>=PROM*ATR[i]
pivhighs=[i for i in range(len(H)) if is_pivot_high(i)]
def anchor_of(e):
    # swing HIGH significativo mais recente CONFIRMADO até e (i+K<=e) e acima do close de e (e está na queda/recuperação dele)
    cand=[i for i in pivhighs if i+K<=e and H[i]>Cl[e]]
    return max(cand) if cand else None

anchors={e:anchor_of(e) for e in EP}
# agrupa por anchor: mesmo movimento
from collections import defaultdict
groups=defaultdict(list)
for e in EP:
    a=anchors[e]
    if a is not None: groups[a].append(e)
movements={a:sorted(es) for a,es in groups.items() if len(es)>1}  # só os que têm continuação

print("="*92)
print(f"CONTINUAÇÃO ESTRUTURAL (3b) | K={K} PROM={PROM}ATR | {len(pivhighs)} swing highs significativos | {len(EP)} entradas")
n_with_sibling=sum(1 for e in EP if anchors[e] is not None and len(groups[anchors[e]])>1)
print(f"entradas com ≥1 irmão de movimento (continuação): {n_with_sibling}/{len(EP)} | {len(movements)} movimentos multi-entrada")

# ---- PROVA: 4918 e 4926 partem do mesmo swing high (origem da perna)? ----
print("\nPROVA — 4918 (fundo) e 4926 (continuação):")
for e in (4918,4926):
    a=anchors[e]
    print(f"  entrada {e} {d10(TS[e])}  anchor=swing_high bar {a} ({d10(TS[a]) if a is not None else '·'}, high={round(H[a],1) if a is not None else '·'})  mfe={mfe(e):+.1f}")
same = anchors[4918]==anchors[4926]
print(f"  >> MESMO MOVIMENTO: {'SIM ✓ (3b liga os dois)' if same else 'NÃO ✗'}")
if not same:
    btwn=[i for i in pivhighs if anchors[4918] is not None and anchors[4918]<i<=4926]
    print(f"     swing highs significativos entre 4918-anchor e 4926: {[(i,d10(TS[i]),round(H[i],1)) for i in btwn]}")

# ---- alguns movimentos com continuação, ordenados por nº de entradas ----
print("\nMOVIMENTOS com mais entradas (mesmo swing high de origem):")
for a in sorted(movements,key=lambda a:-len(movements[a]))[:8]:
    es=movements[a]
    print(f"  anchor {a} ({d10(TS[a])} high {H[a]:.1f}) | {len(es)} entradas: "+", ".join(f"{e}({d10(TS[e])[5:]},{mfe(e):+.0f}R)" for e in es))

# ---- export ----
with open(f"{D}/l2_bpt_continuation_movements.csv","w",newline="") as f:
    w=csv.writer(f,lineterminator="\n")
    w.writerow(['bar_idx','datetime','anchor_swinghigh_bar','anchor_date','anchor_high','movement_size','movement_siblings'])
    for e in EP:
        a=anchors[e]; sibs=[x for x in groups.get(a,[]) if x!=e] if a is not None else []
        w.writerow([e,d10(TS[e]),a if a is not None else '',d10(TS[a]) if a is not None else '',
                    round(H[a],1) if a is not None else '',len(groups.get(a,[])) if a is not None else 1,
                    " ".join(map(str,sibs))])
print(f"\nexport: {D}/l2_bpt_continuation_movements.csv | swing high CAUSAL (confirmado +{K}) significativo. NÃO usa outcome.")
