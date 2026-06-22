#!/usr/bin/env python3
"""L2/BPT — DYNAMIC READER v2: INCORPORA os estados aprendidos dos 2 engines + prior layers (correção Cris).
v1 era PARTIAL (só 7 sub-leitores novos). v2 carrega como EVIDÊNCIA os estados do Macro Structural Reading Engine
(9 estados de especialista determinístico + macro_state) + Indicator/confluence engine v2 (bubbles/NAS/SMC/RSI
context-aware) + prior layers condicionais (bear_leg_block, clean_sky, capit+rsi, macro_phase). Comparação em 4
estágios para isolar o que cada fonte adiciona. Causal. Base 276. realR uncapped (let-run) régua. DIAGNÓSTICO,
sem promoção/OOS. Multi-fatorial (convergência de votos, satisfaz anti-miopia)."""
import csv, json, random
D="results"; RR="repro_recovery"
pk={int(json.loads(l)['bar_idx']):json.loads(l) for l in open(f"{RR}/qual_packets.jsonl")}
unc={int(r['bar_idx']):r for r in csv.DictReader(open(f"{D}/l2_bpt_uncapped_or_proxy_outcomes_276.csv"))}
eng={int(r['bar_idx']):r for r in csv.DictReader(open(f"{D}/l2_bpt_full276_macro_engine_confluence.csv"))}
xv2={int(r['bar_idx']):r for r in csv.DictReader(open(f"{D}/l2_bpt_full276_indicator_engine_cross_v2.csv"))}
dec={int(r['bar_idx']):r for r in csv.DictReader(open(f"{D}/l2_bpt_full276_macro_bear_v3_decisions.csv"))}
mph={int(r['episode_id']):r['macro_phase_causal'] for r in csv.DictReader(open(f"{D}/l2_bpt_full276_macro_phase_causal_candidate.csv"))}
v1={int(r['bar_idx']):r for r in csv.DictReader(open(f"{D}/l2_bpt_dynamic_reader_v1_reading.csv"))}
def fn(v):
    try:return float(v)
    except:return None
EP=sorted(unc); MFE={b:fn(unc[b]['mfe_R']) for b in EP}
nR=sum(1 for b in EP if MFE[b]>=5); base=nR/len(EP); WIN6={919,159,55,391,2053,351}

# ---- VOTOS por FONTE (cada um normaliza p/ +1 runner-context / -1 loser-context / 0). AUDITÁVEL. ----
def vote_SR(b):  # 7 sub-leitores novos (v1)
    w=v1[b]['why']
    if w in('REVERSAL_RUNNER','LEGITIMATE_BEAR_BUY','MARKUP_CONTINUATION'): return 1
    if w in('BEAR_PULLBACK_TRAP','TOP_TRAP_AVOID'): return -1
    return 0
def vote_ENG(b):  # Macro Structural Reading Engine (estados de especialista + macro_state)
    e=eng[b]; v=0
    if e.get('capit')=='CLIMAX_RECLAIM': v+=1
    if e.get('momentum')=='LATE_TOP_EXHAUSTION': v-=1
    if e.get('supply') in('CLEAN_SKY_BULLISH','MARKUP_BREAKING'): v+=1
    if e.get('supply') in('SUPPLY_REJECTING_RISK','SUPPLY_BLOCKS_TARGET'): v-=1
    if e.get('macro_state') in('NO_OVERHEAD_MARKUP','MACRO_BULL_RUN_CONTINUATION','RANGE_MACRO_BULL_RECLAIM','CAPITULATION_RECLAIM_VALID'): v+=1
    if e.get('macro_state') in('BULL_PULLBACK_CONTINUATION','UNKNOWN_CONFLICT'): v-=1
    if e.get('fuel')=='high_fuel': v+=1
    return max(-1,min(1,v))
def vote_IND(b):  # Indicator/confluence engine v2 (context-aware)
    x=xv2.get(b,{}); v=0
    if x.get('bubbles')=='BUBBLE_SELL_CLIMAX_BULL': v+=1
    if x.get('bubbles')=='BUBBLE_BUY_LATE': v-=1
    if x.get('smc')=='SMC_CHOCH_BULL_TRIGGER': v+=1
    if x.get('smc')=='SMC_CHOCH_TOP_REVERSAL': v-=1
    if x.get('nas')=='NAS_LONG_RECENT': v+=1
    if x.get('nas')=='NAS_SHORT_TOP': v-=1
    if x.get('indicator_confluence')=='STRONG_BEAR_CONFIRM': v+=1  # inversão (achado): bearish-confirm precede runners
    return max(-1,min(1,v))
def vote_LAYERS(b):  # prior layers condicionais
    d=dec.get(b,{}); v=0
    if d.get('clean_sky_flag')=='True': v+=1
    if d.get('capit')=='CLIMAX_RECLAIM': v+=1
    if mph.get(b)=='MACRO_BULL_RUN': v+=1
    if d.get('macro_reader_leg')=='MACRO_BEAR_LEG' and v1[b]['s_bearbuy']=='BEAR_PULLBACK_TRAP': v-=1
    return max(-1,min(1,v))

def policy(b, sources, thr=1):
    net=sum(f(b) for f in sources)
    if net>=thr: return 'TAKE'
    if net<=-thr: return 'SKIP'
    return 'REVIEW'

def evalstage(name, sources, thr=1):
    rng=random.Random(5)
    TAKE=[b for b in EP if policy(b,sources,thr)=='TAKE']
    n=len(TAKE); run=sum(1 for b in TAKE if MFE[b]>=5); rr=(run/n if n else 0)
    sw=sum(1 for b in EP if MFE[b]>=5 and eng[b]['policy'] in('SKIP','REVIEW','REVIEW_RISK') and policy(b,sources,thr)=='TAKE')
    lc=sum(1 for b in EP if MFE[b]<2 and eng[b]['policy']=='TAKE' and policy(b,sources,thr)=='SKIP')
    sumlet=round(sum(fn(unc[b]['realized_letrun_120']) for b in TAKE),1)
    k=n; obs=rr; ge=0; mv=[MFE[b] for b in EP]
    if k:
        for _ in range(3000):
            idx=list(range(len(EP)));rng.shuffle(idx);s=idx[:k]
            if sum(1 for j in s if mv[j]>=5)/k>=obs: ge+=1
    p=ge/3000 if k else 1
    miss=[b for b in WIN6 if b in EP and policy(b,sources,thr)=='SKIP']
    def w(b): return 'P1' if pk[b]['datetime'][:10]<'2023-01-01' else 'P2'
    p1=[b for b in TAKE if w(b)=='P1']; p2=[b for b in TAKE if w(b)=='P2']
    rr1=(sum(1 for b in p1 if MFE[b]>=5)/len(p1) if p1 else 0); rr2=(sum(1 for b in p2 if MFE[b]>=5)/len(p2) if p2 else 0)
    return dict(stage=name,n_take=n,runner_rate=round(100*rr,1),lift=round(rr/base,2),skip_winners_recovered=sw,
        loser_takes_cut=lc,sumR_letrun=sumlet,null_p=round(p,3),recall_miss=len(miss),
        P1_rr=round(100*rr1,1),P2_rr=round(100*rr2,1))

STAGES=[
 ("S1_7subreaders_alone",[vote_SR]),
 ("S2_prior_engines_alone",[vote_ENG,vote_IND]),
 ("S3_7sub+engines",[vote_SR,vote_ENG,vote_IND]),
 ("S4_7sub+engines+layers",[vote_SR,vote_ENG,vote_IND,vote_LAYERS]),
]
print("="*98);print(f"DYNAMIC READER v2 — COMPARAÇÃO ESTAGIADA (base 276, runners={nR}, base_rate={base*100:.1f}%, thr=net>=1)")
print(f"{'stage':26}{'nTAKE':>6}{'run%':>6}{'lift':>6}{'skipW+':>7}{'losC':>6}{'sumLet':>8}{'null_p':>7}{'recallMiss':>11}{'P1/P2':>11}")
rows=[]
for nm,srcs in STAGES:
    r=evalstage(nm,srcs); rows.append(r)
    print(f"{r['stage']:26}{r['n_take']:>6}{r['runner_rate']:>6}{r['lift']:>6}{r['skip_winners_recovered']:>7}{r['loser_takes_cut']:>6}{r['sumR_letrun']:>8}{r['null_p']:>7}{r['recall_miss']:>11}{str(r['P1_rr'])+'/'+str(r['P2_rr']):>11}")
r2=evalstage("S4_thr2_strongconv",[vote_SR,vote_ENG,vote_IND,vote_LAYERS],thr=2); rows.append(r2)
print(f"{r2['stage']:26}{r2['n_take']:>6}{r2['runner_rate']:>6}{r2['lift']:>6}{r2['skip_winners_recovered']:>7}{r2['loser_takes_cut']:>6}{r2['sumR_letrun']:>8}{r2['null_p']:>7}{r2['recall_miss']:>11}{str(r2['P1_rr'])+'/'+str(r2['P2_rr']):>11}")
with open(f"{D}/l2_bpt_dynamic_reader_v2_staged_comparison.csv","w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0].keys()),lineterminator="\n");w.writeheader();w.writerows(rows)
print(f"\nbaselines estáticos a bater: supply_reject lift 1.08, bear_leg 1.63")
print("DONE v2 staged.")
