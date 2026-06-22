#!/usr/bin/env python3
"""L2/BPT — testar o CONTEXTO APRENDIDO nos DOIS engines contra a verdade de CONVEXIDADE (runner vs loser).
Faltava na analise anterior (Cris): usei policy binaria (TAKE/SKIP), nao os estados RICOS aprendidos.
Macro engine: supply/momentum/capit/macro_state (CLEAN_SKY_BULLISH/MARKUP_BREAKING vs SUPPLY_REJECTING_RISK;
LATE_TOP_EXHAUSTION vs HEALTHY_HIGH_LEGPOS; NO_OVERHEAD_MARKUP vs ...). Indicator v2: bubbles/smc/nas/context.
Para cada VALOR de estado: runner_rate (MFE>=5) e lift vs base 26%. CALIBRACAO (multi-testing in-sample) —
estados que separam exigem null/sub-janela depois. DIAGNOSTICO. Outcome so avaliacao."""
import csv
D="results"
unc={int(r['bar_idx']):r for r in csv.DictReader(open(f"{D}/l2_bpt_uncapped_or_proxy_outcomes_276.csv"))}
eng={int(r['bar_idx']):r for r in csv.DictReader(open(f"{D}/l2_bpt_full276_macro_engine_confluence.csv"))}
xv2={int(r['bar_idx']):r for r in csv.DictReader(open(f"{D}/l2_bpt_full276_indicator_engine_cross_v2.csv"))}
def fn(v):
    try:return float(v)
    except:return None
EP=sorted(unc); MFE={b:fn(unc[b]['mfe_R']) for b in EP}
nR=sum(1 for b in EP if MFE[b]>=5); base=nR/len(EP)
print(f"base runner_rate (MFE>=5) = {base*100:.1f}% (runners {nR}/{len(EP)})\n")
def analyze(dim, getter):
    from collections import defaultdict
    g=defaultdict(list)
    for b in EP:
        v=getter(b)
        if v: g[v].append(b)
    rows=[]
    for val,bs in g.items():
        n=len(bs); run=sum(1 for b in bs if MFE[b]>=5); los=sum(1 for b in bs if MFE[b]<2)
        rr=run/n; lift=rr/base
        rows.append((dim,val,n,run,los,round(100*rr,1),round(lift,2)))
    return sorted(rows,key=lambda x:-x[6])
DIMS=[
 ('macro_state', lambda b: eng[b].get('macro_state')),
 ('supply_spec', lambda b: eng[b].get('supply')),
 ('momentum_spec',lambda b: eng[b].get('momentum')),
 ('capit_spec',  lambda b: eng[b].get('capit')),
 ('fuel_spec',   lambda b: eng[b].get('fuel')),
 ('regime_spec', lambda b: eng[b].get('regime')),
 ('mtf_spec',    lambda b: eng[b].get('mtf')),
 ('ind_context', lambda b: xv2.get(b,{}).get('context')),
 ('ind_confluence',lambda b: xv2.get(b,{}).get('indicator_confluence')),
 ('ind_bubbles', lambda b: xv2.get(b,{}).get('bubbles')),
 ('ind_smc',     lambda b: xv2.get(b,{}).get('smc')),
 ('ind_nas',     lambda b: xv2.get(b,{}).get('nas')),
]
allrows=[]
print(f"{'dim':16}{'state':32}{'n':>4}{'run':>4}{'los':>4}{'run%':>6}{'lift':>6}")
for dim,get in DIMS:
    for r in analyze(dim,get):
        if r[2]>=6:  # n>=6 p/ não ruído
            allrows.append(r)
            mark=' <<MARKUP' if r[6]>=1.4 else ' <<REJECT' if r[6]<=0.6 else ''
            print(f"{r[0]:16}{r[1]:32}{r[2]:>4}{r[3]:>4}{r[4]:>4}{r[5]:>6}{r[6]:>6}{mark}")
    print()
with open(f"{D}/l2_bpt_learned_states_vs_convexity.csv","w",newline="") as f:
    w=csv.writer(f,lineterminator="\n");w.writerow(['dim','state','n','runners','losers','runner_pct','lift_vs_base'])
    w.writerows(allrows)
# combinação aprendida: supply markup + momentum healthy vs supply reject + late-top
def cls(b):
    sup=eng[b].get('supply');mom=eng[b].get('momentum')
    markup = sup in('CLEAN_SKY_BULLISH','MARKUP_BREAKING') and mom in('HEALTHY_HIGH_LEGPOS','STRONG_BULL_MOMENTUM')
    reject = sup in('SUPPLY_REJECTING_RISK','SUPPLY_BLOCKS_TARGET') or mom=='LATE_TOP_EXHAUSTION'
    return 'MARKUP_LEARNED' if markup and not reject else 'REJECT_LEARNED' if reject and not markup else 'MIXED'
print("=== COMBINAÇÃO APRENDIDA (supply+momentum dos especialistas) ===")
from collections import defaultdict
gg=defaultdict(list)
for b in EP: gg[cls(b)].append(b)
for k,bs in gg.items():
    n=len(bs);run=sum(1 for b in bs if MFE[b]>=5);los=sum(1 for b in bs if MFE[b]<2)
    print(f"  {k:16} n={n:>3} runners={run:>3} ({100*run/n:.1f}%, lift {run/n/base:.2f}) losers={los:>3} ({100*los/n:.1f}%)")
