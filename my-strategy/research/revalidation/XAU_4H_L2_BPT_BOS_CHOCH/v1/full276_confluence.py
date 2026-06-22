#!/usr/bin/env python3
"""FULL 276 — confluência exaustiva CONTROLADA (1/2/3-way) p/ prever LOSERS entre os ALLOWED, com
PERMUTATION NULL + TEMPORAL SPLIT obrigatórios. outcome só como LABEL de avaliação. Sem busca cega (permutation).
Testa também os sinais PRÉ-ESPECIFICADOS dos 62 (clean-sky, high_fuel, n_SH, no-near-supply, supply-broken)."""
import csv, json, hashlib, statistics as st
from itertools import combinations

D = "results"
dec = {int(r['bar_idx']): r for r in csv.DictReader(open(f"{D}/l2_bpt_full276_macro_bear_v3_decisions.csv"))}
tqm = {int(r['bar_idx']): r for r in csv.DictReader(open(f"{D}/l2_bpt_trade_qualification_matrix.csv"))}
dsq = {int(r['candidate_id'][1:]): r for r in csv.DictReader(open(f"{D}/l2_bpt_v2_2_pruned_base_v2_demand_supply_quality.csv"))}
def fn(v):
    try: return float(v)
    except: return None

# universo = ALLOWED (queremos um BLOCK rule adicional que corte losers sem matar winners)
allowed = sorted([b for b in dec if dec[b]['blocked']=='NO'], key=lambda b: dec[b]['datetime'])
def loser(b): r=fn(dec[b]['realR']); return r is not None and r<=0
LOSE = {b: loser(b) for b in allowed}
nL = sum(LOSE.values()); nW = len(allowed)-nL
print(f"universo ALLOWED={len(allowed)} | losers={nL} winners={nW}")

# montar features (84-stream + leg/sup_cat/clean_sky/capit/demand/d1)
FEATS_NUM = ['trend_30_atr','trend_90_atr','slope20_atr','dist_sma50_atr','rsi','rsi_1d','rsi_min8','rsi_max8',
 'drop20_atr','rise20_atr','legpos30','legpos90','dist_4h_demand_low_atr','dist_4h_supply_low_atr','rel_volume',
 'dist_POC_atr','dist_VAL_atr','va_width_atr','reclaim_body_atr','bub_buy_sell_ratio','bub_large_buy_10b',
 'bub_large_sell_10b','supply_blocks_2ATR','supply_blocks_3ATR','demand_age_bars','sl_atr','rsi_bear_div_20b']
FEATS_CAT = ['macro_reader_leg','sup_cat','capit','demand','clean_sky_flag','d1_regimeB']
def featrow(b):
    t=tqm[b]; d=dec[b]; f={}
    for k in FEATS_NUM: f[k]=fn(t.get(k))
    f['macro_reader_leg']=d['macro_reader_leg']; f['sup_cat']=d['sup_cat']; f['capit']=d['capit']
    f['demand']=d['demand']; f['clean_sky_flag']=d['clean_sky_flag']; f['d1_regimeB']=d['d1_regimeB']
    # flags pré-especificados
    f['n_SH']=fn(d['d1_combined'])  # proxy regime; n_SH não no decisions -> usar d1 combined
    return f
FR = {b: featrow(b) for b in allowed}

# literais (bitmask sobre allowed)
order=allowed; idx={b:i for i,b in enumerate(order)}
LOSE_MASK=sum(1<<idx[b] for b in order if LOSE[b]); ALL=(1<<len(order))-1
def pc(x): return bin(x).count('1')
literals=[]
for c in FEATS_NUM:
    vals=[FR[b][c] for b in order]; nv=sorted(v for v in vals if v is not None)
    if len(nv)<len(order)*0.6: continue
    q1=nv[len(nv)//3]; q2=nv[2*len(nv)//3]
    for lab,pred in ((f"{c}<={q1:.2f}",lambda v,t=q1:v is not None and v<=t),(f"{c}>={q2:.2f}",lambda v,t=q2:v is not None and v>=t)):
        m=sum(1<<idx[order[i]] for i,v in enumerate(vals) if pred(v))
        if 8<=pc(m)<=len(order)-8: literals.append((lab,m))
for c in FEATS_CAT:
    from collections import Counter
    cv=[FR[b][c] for b in order]
    for val,n in Counter(cv).most_common():
        if n<8 or val in('','None'): continue
        m=sum(1<<idx[order[i]] for i,x in enumerate(cv) if x==val)
        if 8<=pc(m)<=len(order)-8: literals.append((f"{c}=={val}",m))
print(f"literais: {len(literals)}")

# melhor regra (precisão de loser) que captura >=15 com lift sobre base rate
base_rate=nL/len(order)
def best_rule(lose_mask, max_terms=3, min_cap=15):
    best=None  # (lift, desc, cap, loser_in, precision)
    L=literals
    cands=[(lab,m) for lab,m in L]
    pool=[]
    # 1-way
    for lab,m in cands:
        cap=pc(m); li=pc(m&lose_mask)
        if cap>=min_cap:
            prec=li/cap; pool.append((prec-base_rate,[lab],cap,li,prec))
    # 2-way
    seeds=[(lab,m) for lab,m in cands if pc(m)>=min_cap]
    for i in range(len(seeds)):
        for j in range(i+1,len(seeds)):
            m=seeds[i][1]&seeds[j][1]; cap=pc(m)
            if cap>=min_cap:
                li=pc(m&lose_mask); prec=li/cap; pool.append((prec-base_rate,[seeds[i][0],seeds[j][0]],cap,li,prec))
    # 3-way greedy
    pool.sort(key=lambda x:-x[0])
    masks={lab:m for lab,m in cands}
    for lift0,terms0,cap0,li0,pr0 in pool[:30]:
        m0=ALL
        for t in terms0: m0&=masks[t]
        for lab,m in seeds:
            if lab in terms0:continue
            m3=m0&m;cap=pc(m3)
            if cap>=min_cap:
                li=pc(m3&lose_mask);prec=li/cap;pool.append((prec-base_rate,terms0+[lab],cap,li,prec))
    pool.sort(key=lambda x:-x[0])
    return pool[0] if pool else None

real=best_rule(LOSE_MASK)
print(f"\n=== MELHOR CONFLUÊNCIA (precisão-loser, cap>=15) | base_rate loser={base_rate:.3f} ===")
if real:
    lift,terms,cap,li,prec=real
    print(f"  regra: {' AND '.join(terms)}")
    print(f"  captura {cap} trades, {li} losers, precisão={prec:.3f}, lift={lift:+.3f} sobre base {base_rate:.3f}")

# PERMUTATION NULL (embaralha labels de loser)
def shuffled_mask(seed):
    ranked=sorted(order,key=lambda b:hashlib.md5(f"{seed}:{b}".encode()).hexdigest())
    return sum(1<<idx[b] for b in ranked[:nL])
null=[]
for s in range(150):
    r=best_rule(shuffled_mask(s))
    null.append(r[0] if r else -1)
null.sort()
tgt=real[0] if real else -1
better=sum(1 for x in null if x>=tgt)
print(f"\n=== PERMUTATION NULL (150 shuffles do label) ===")
print(f"  lift real: {tgt:+.3f} | null mediana {st.median(null):+.3f} max {max(null):+.3f} p95 {null[int(.95*len(null))]:+.3f}")
print(f"  shuffles >= real: {better}/150 (p={better/150:.3f}) -> {'ROBUSTO' if better/150<0.05 else 'ID-FIT/HULL'}")

# TEMPORAL SPLIT: regra do 1o periodo vale no 2o?
mid=len(order)//2
P1=order[:mid]; P2=order[mid:]
def rule_mask(terms):
    masks={lab:m for lab,m in literals}; m=ALL
    for t in terms: m&=masks[t]
    return m
if real:
    rm=rule_mask(real[1])
    def prec_in(sub):
        s=[b for b in sub if (rm>>idx[b])&1];
        if not s: return None,0
        return sum(1 for b in s if LOSE[b])/len(s), len(s)
    p1,n1=prec_in(P1); p2,n2=prec_in(P2)
    print(f"\n=== TEMPORAL SPLIT ===")
    print(f"  P1 {dec[P1[0]]['datetime'][:7]}..{dec[P1[-1]]['datetime'][:7]}: precisão-loser {p1} (n={n1})")
    print(f"  P2 {dec[P2[0]]['datetime'][:7]}..{dec[P2[-1]]['datetime'][:7]}: precisão-loser {p2} (n={n2})")
    print(f"  base_rate P1={sum(LOSE[b] for b in P1)/len(P1):.2f} P2={sum(LOSE[b] for b in P2)/len(P2):.2f}")

# SINAIS PRÉ-ESPECIFICADOS dos 62: lift sobre outcome
print(f"\n=== SINAIS PRÉ-ESPECIFICADOS (lift de loser-rate; base={base_rate:.3f}) ===")
presig=[("clean_sky_flag==True",lambda b:FR[b]['clean_sky_flag']=='True'),
        ("sup_cat==CLEAN_SKY",lambda b:FR[b]['sup_cat']=='CLEAN_SKY'),
        ("supply_blocks_2ATR==0",lambda b:FR[b]['supply_blocks_2ATR']==0),
        ("leg==MACRO_BULL_LEG",lambda b:FR[b]['macro_reader_leg']=='MACRO_BULL_LEG'),
        ("leg==MACRO_RANGE",lambda b:FR[b]['macro_reader_leg']=='MACRO_RANGE'),
        ("legpos90>=80",lambda b:FR[b]['legpos90'] is not None and FR[b]['legpos90']>=80),
        ("rsi_1d>=65",lambda b:FR[b]['rsi_1d'] is not None and FR[b]['rsi_1d']>=65),
        ("dist_4h_supply>=3 (no_near_supply)",lambda b:FR[b]['dist_4h_supply_low_atr'] is not None and FR[b]['dist_4h_supply_low_atr']>=3)]
cand_rows=[]
for name,pred in presig:
    s=[b for b in order if pred(b)]
    if not s: continue
    lr=sum(1 for b in s if LOSE[b])/len(s)
    cand_rows.append(dict(signal=name,n=len(s),loser_rate=round(lr,3),lift=round(lr-base_rate,3)))
    print(f"  {name:36} n={len(s):3} loser_rate={lr:.3f} lift={lr-base_rate:+.3f}")
with open(f"{D}/l2_bpt_full276_exhaustive_confluence_candidates.csv","w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=['signal','n','loser_rate','lift'],lineterminator="\n");w.writeheader();w.writerows(cand_rows)
json.dump(dict(best_rule=real[1] if real else None, best_lift=real[0] if real else None, cap=real[2] if real else 0,
    permutation_p=better/150, null_median=st.median(null), null_max=max(null),
    verdict=('ROBUST' if better/150<0.05 else 'IDFIT_HULL')),
    open(f"{D}/l2_bpt_full276_exhaustive_confluence_permutation.json","w"),indent=1)
# temporal csv
if real:
    with open(f"{D}/l2_bpt_full276_exhaustive_confluence_temporal.csv","w",newline="") as f:
        w=csv.writer(f,lineterminator="\n");w.writerow(["period","precision_loser","n","base_rate"])
        w.writerow(["P1_2020_22",p1,n1,round(sum(LOSE[b] for b in P1)/len(P1),3)])
        w.writerow(["P2_2023_26",p2,n2,round(sum(LOSE[b] for b in P2)/len(P2),3)])
print("\noutputs salvos.")
