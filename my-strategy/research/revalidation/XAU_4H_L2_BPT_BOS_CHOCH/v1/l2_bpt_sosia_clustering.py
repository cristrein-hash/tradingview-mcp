#!/usr/bin/env python3
"""SÓSIA CLUSTERING — substrato CONTRASTIVO da leitura (motor da leitura boa: discriminar ENTRE casos, não dentro).
Match na SUPERFÍCIE (flush+clean_sky+demand+acceptance). Discriminadores (weekly_slope, cascade, FORMA) ficam de FORA
do match — variam dentro do cluster: essa variação É o contraste.
Clustering é CEGO ao outcome. Outcome usado SÓ p/ VERIFICAR se o substrato produz pares duros (mesma superfície,
desfecho oposto) — não para arbitrar leitura. Marca 'HARD' clusters com runner E loser juntos = onde mora a leitura."""
import json, csv
from collections import defaultdict
D="results"
PK={int(json.loads(l)['episode_id']):json.loads(l) for l in open(f"{D}/l2_bpt_episode_context_packets_276.jsonl")}
RD={int(json.loads(l)['episode_id']):json.loads(l) for l in open(f"{D}/l2_bpt_episode_readings_276.jsonl")}
def fn(v):
    try: return float(v)
    except: return None
def norm(v):
    if v in (None,'','None','nan'): return '·'
    return str(v)
# ---- SUPERFÍCIE (match) ----
def surface(b):
    p=PK[b]
    flush=p['dspa_path'].get('flush')
    clean=p['supply_demand'].get('clean_sky')
    demand=p['supply_demand'].get('demand_cat') or p['supply_demand'].get('demand')
    accept=p['dspa_path'].get('acceptance')
    return (norm(flush),norm(clean),norm(demand),norm(accept))
# ---- DISCRIMINADORES (fora do match, variam dentro) ----
def weekly(b):
    w=PK[b]['weekly_1d_context']
    return fn(w.get('weekly_slope_decisions')) if fn(w.get('weekly_slope_decisions')) is not None else fn(w.get('weekly_slope_20pct'))
def cascade(b):
    rb=PK[b]['regime_B']; c=fn(rb.get('cascade_score'))
    return c if c is not None else fn(PK[b]['dspa_path'].get('cascade_now'))
def mfe(b): return PK[b]['_AUDIT_outcome_NOT_FOR_READING']['mfe_R']
EP=sorted(PK)
clusters=defaultdict(list)
for b in EP: clusters[surface(b)].append(b)

# ---- verificação: quantos clusters HARD (runner>=5 E loser<2 no mesmo cluster) ----
hard=[]; singletons=0; total_in_hard=0
for sig,bs in clusters.items():
    runners=[b for b in bs if mfe(b)>=5]; losers=[b for b in bs if mfe(b)<2]
    if len(bs)==1: singletons+=1
    if runners and losers:
        hard.append((sig,bs,runners,losers)); total_in_hard+=len(bs)
print("="*100)
print(f"SÓSIA CLUSTERING | {len(EP)} episódios → {len(clusters)} clusters de superfície | singletons={singletons}")
print(f"match=(flush,clean_sky,demand,acceptance) | discriminadores FORA: weekly,cascade,forma")
print(f"\nCLUSTERS HARD (runner E loser na mesma superfície = onde a leitura tem que discriminar): {len(hard)} clusters, {total_in_hard} episódios")
hard.sort(key=lambda x:-len(x[1]))
for sig,bs,runners,losers in hard[:12]:
    wk=[weekly(b) for b in bs if weekly(b) is not None]
    print(f"\n  superfície {sig}  | n={len(bs)} runners={len(runners)} losers={len(losers)}")
    print(f"    weekly range [{min(wk):+.2f},{max(wk):+.2f}]" if wk else "    weekly n/a")
    for b in sorted(bs,key=lambda b:-(mfe(b))):
        tag='RUN' if mfe(b)>=5 else ('LOS' if mfe(b)<2 else '   ')
        print(f"      {b:>5} {PK[b]['timestamp'][:10]} wk={str(round(weekly(b),2)) if weekly(b) is not None else '·':>6} casc={str(cascade(b)):>5} mfe={mfe(b):>5.1f} {tag}  [{RD[b]['episode_type'][:18]}/{RD[b]['provisional_decision']}]")

# ---- prova: o cluster do 4918 (monumental seed) tem sósias weekly-negativos? ----
print("\n"+"="*100)
seed=4918
sig=surface(seed); cl=clusters[sig]
print(f"PROVA — cluster do 4918 (monumental seed, weekly {weekly(seed):+.2f}): superfície {sig}, n={len(cl)}")
for b in sorted(cl,key=lambda b:weekly(b) if weekly(b) is not None else 9):
    tag='RUN' if mfe(b)>=5 else ('LOS' if mfe(b)<2 else '   ')
    print(f"  {b:>5} {PK[b]['timestamp'][:10]} wk={str(round(weekly(b),2)) if weekly(b) is not None else '·':>6} casc={str(cascade(b)):>5} mfe={mfe(b):>5.1f} {tag}  [{RD[b]['episode_type'][:18]}/{RD[b]['provisional_decision']}]")

# ---- export do substrato p/ a leitura ----
with open(f"{D}/l2_bpt_sosia_clusters.csv","w",newline="") as f:
    w=csv.writer(f,lineterminator="\n")
    w.writerow(['cluster_id','bar_idx','datetime','flush','clean_sky','demand','acceptance','weekly','cascade','mfe_R','is_hard_cluster','block_type','block_decision'])
    cid={sig:i for i,sig in enumerate(clusters)}
    hardsigs={sig for sig,_,_,_ in hard}
    for sig,bs in clusters.items():
        for b in bs:
            w.writerow([cid[sig],b,PK[b]['timestamp'][:16],*sig,
                        round(weekly(b),3) if weekly(b) is not None else '',cascade(b),round(mfe(b),1),
                        int(sig in hardsigs),RD[b]['episode_type'],RD[b]['provisional_decision']])
print(f"\nsubstrato exportado: {D}/l2_bpt_sosia_clusters.csv")
print("Clustering CEGO ao outcome. HARD = onde superfície não separa → a leitura (forma+weekly+cascade) tem que decidir.")
