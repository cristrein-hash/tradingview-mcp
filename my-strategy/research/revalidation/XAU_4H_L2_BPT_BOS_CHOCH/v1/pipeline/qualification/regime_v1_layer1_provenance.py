#!/usr/bin/env python3
"""REGIME/CONTEXT/FUEL v1 — LAYER 1: feature provenance + validação de join causal das externas.
DIAGNÓSTICO. Não usa outcome. Não toca engine/produção. Externas (diárias) entram SÓ com shift causal D-1
(estado do dia anterior já fechado) — anti look-ahead (lição A1' SUPERTREND). Para e reporta se join inseguro.
"""
import json,csv,os,bisect,datetime as dt
RR="repro_recovery";D="results"
EXT_DIR_V3="../../../../strategies/candidates/regime_classifier_v3"
EXT_DIR_L1="../../../../core/regime_l1"
pk={int(json.loads(l)['bar_idx']):json.loads(l) for l in open(f"{RR}/qual_packets.jsonl")}
KEYS=[k for k in next(iter(pk.values())) if not k.startswith('_')]

# ---- carregar externas (diárias, date string) ----
def load_daily(path):
    rows=[json.loads(l) for l in open(path)]
    rows=[r for r in rows if r.get('ts')]
    rows.sort(key=lambda r:r['ts'])
    return rows
extB=load_daily(f"{EXT_DIR_V3}/regime_B_v3_classifications.jsonl")
extD=load_daily(f"{EXT_DIR_V3}/xau_daily_with_features.jsonl")
extL1=load_daily(f"{EXT_DIR_L1}/regime_l1_v4_classifications.jsonl")
def causal_lookup(rows,entry_date):  # último row com date ESTRITAMENTE < entry_date (D-1 ou anterior) = causal
    dates=[r['ts'] for r in rows]
    i=bisect.bisect_left(dates,entry_date)-1
    return rows[i] if i>=0 else None

# ---- validar join causal sobre os episódios ----
eps=sorted(pk)
join_issues=[];cov=0;null_state=0
for i in eps:
    ed=pk[i]['datetime'][:10]  # UTC date do bar 4H
    rB=causal_lookup(extB,ed)
    if rB is None: join_issues.append((i,ed,'sem_D-1_em_regime_B'));continue
    if rB['ts']>=ed: join_issues.append((i,ed,f'NAO-CAUSAL ts={rB["ts"]}'));continue
    cov+=1
    if rB.get('v3_state') in (None,''): null_state+=1
shift_days=[]
for i in eps[:200]:
    ed=pk[i]['datetime'][:10];rB=causal_lookup(extB,ed)
    if rB: shift_days.append((dt.date.fromisoformat(ed)-dt.date.fromisoformat(rB['ts'])).days)
import statistics as stt
print(f"JOIN externas: {cov}/{len(eps)} episódios com row causal D-1 | null v3_state={null_state}")
print(f"shift médio (dias entre entry e row externa usada): min={min(shift_days)} mediana={stt.median(shift_days)} max={max(shift_days)} (>=1 = causal OK)")
print(f"join_issues: {len(join_issues)}",join_issues[:3] if join_issues else "(nenhum)")
assert all(s>=1 for s in shift_days),"FALHA CAUSAL: shift <1 dia"

# ---- comportamento real: macro_leg morto? ----
from collections import Counter
ml_dir=Counter(pk[i].get('macro_leg_direction') for i in eps)
ml_ph=Counter(pk[i].get('macro_leg_phase') for i in eps)
print(f"\nmacro_leg_direction distrib: {dict(ml_dir)}")
print(f"macro_leg_phase distrib: {dict(ml_ph)}")
ml_dead = len(ml_dir)<=1 and len(ml_ph)<=1
print(f"=> macro_leg MORTO (constante/REFERENCE_ONLY)? {ml_dead}")

# ---- provenance table ----
def prov(k):
    src='84packet';shift='no';la='low';causal='yes'
    if 'd1' in k or k in('rsi_1d','rsi_1d_ma','rsi_1d_sub_ma'): src='84packet(daily-derived)';shift='ja-shiftado-no-build';la='check'
    if k in('smc_bos','smc_choch'): la='REPAINT->usar direcao/recencia'
    if k.startswith(('macro_leg',)): la='DEAD' if ml_dead else 'low'
    return dict(feature=k,source=src,timestamp='bar_i (4H close)',causal_at_entry=causal,shift_needed=shift,lookahead_risk=la)
rows=[prov(k) for k in KEYS]
# externas como features (com shift D-1)
for fk,desc in [('ext_regime_B_v3_state','regime_B_v3 v3_state (D-1)'),('ext_regime_B_v3_combined_score','combined_score (D-1)'),
                ('ext_regime_B_v3_macro_broken','macro_broken (D-1)'),('ext_regime_B_v3_stage_dir','stage_dir (D-1)'),
                ('ext_regime_l1_v4','regime_l1_v4 (D-1)'),('ext_daily_slope_20_pct','daily slope_20_pct (D-1)'),
                ('ext_daily_rsi_14','daily rsi_14 (D-1)')]:
    rows.append(dict(feature=fk,source='EXTERNAL(daily)',timestamp='D-1 (causal shift)',causal_at_entry='yes(com shift)',shift_needed='YES-D1',lookahead_risk='MITIGADO-por-shift'))
with open(f"{D}/l2_bpt_regime_v1_provenance.csv","w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=['feature','source','timestamp','causal_at_entry','shift_needed','lookahead_risk']);w.writeheader();w.writerows(rows)
print(f"\nprovenance: {len(rows)} features -> l2_bpt_regime_v1_provenance.csv")
print(f"  84packet={sum(1 for r in rows if '84packet' in r['source'])} | externas(shift D-1)={sum(1 for r in rows if r['source']=='EXTERNAL(daily)')}")
print("LAYER 1 OK: join causal validado (shift D-1), macro_leg testado, provenance escrita.")
