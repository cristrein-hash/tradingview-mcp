#!/usr/bin/env python3
"""L2/BPT — Tarefas 4-6: reavaliar ENTRADA e ENGINE pelo alvo de CONVEXIDADE (não hit-rate capado).
T4: entry attribution por convexidade (L2/BPT vs random-long context-matched) — MFE/runner-freq/tail.
T5: macro engine buckets por convexidade (runner capture, MFE, stop-avoidance) em vez de WR capado.
T6: classificar fonte de edge (ENTRY_ALPHA/CONVEXITY_ALPHA/RISK_SHAPING/BETA_ONLY/...).
DIAGNÓSTICO. Causal (walk forward stop-first). Sem produção/promoção/OOS. realR capado nunca árbitro."""
import json, csv, random
D="results"; RR="repro_recovery"
frozen=[json.loads(l) for l in open(f"{RR}/raw_features_2020_2026.jsonl")]
N=len(frozen); H=[r['high'] for r in frozen]; L=[r['low'] for r in frozen]; C=[r['close'] for r in frozen]
ATR=[None]*N; trs=[]
for i in range(1,N):
    trs.append(max(H[i]-L[i],abs(H[i]-C[i-1]),abs(L[i]-C[i-1])))
    if i>=14: ATR[i]=sum(trs[i-14:i])/14
unc={int(r['bar_idx']):r for r in csv.DictReader(open(f"{D}/l2_bpt_uncapped_or_proxy_outcomes_276.csv"))}
eng={int(r['bar_idx']):r for r in csv.DictReader(open(f"{D}/l2_bpt_full276_macro_engine_confluence.csv"))}
xv2={int(r['bar_idx']):r for r in csv.DictReader(open(f"{D}/l2_bpt_full276_indicator_engine_cross_v2.csv"))}
pk={int(json.loads(l)['bar_idx']):json.loads(l) for l in open(f"{RR}/qual_packets.jsonl")}
def fn(v):
    try:return float(v)
    except:return None
RW=6;R_FLOOR=0.3;R_CEIL=1.5
def mfe_of(i,HZ=120):
    p=C[i];atr=ATR[i]
    if not atr: return None
    lo=min(L[max(0,i-RW+1):i+1]);sl=lo-0.1*atr;risk=p-sl
    if risk<=0: return None
    if risk<R_FLOOR*atr: risk=R_FLOOR*atr;sl=p-risk
    if risk>R_CEIL*atr: risk=R_CEIL*atr;sl=p-risk
    end=min(i+HZ,N-1);mfe=0.0
    for j in range(i+1,end+1):
        if L[j]<=sl: break
        hr=(H[j]-p)/risk
        if hr>mfe: mfe=hr
    return mfe

EP=sorted(unc); MFE={b:fn(unc[b]['mfe_R']) for b in EP}
def stats(vals):
    vals=[v for v in vals if v is not None]; n=len(vals)
    if not n: return dict(n=0)
    s=sorted(vals)
    return dict(n=n, median=round(s[n//2],2), p75=round(s[int(n*0.75)],2), p90=round(s[int(n*0.90)],2),
        mean=round(sum(vals)/n,2), runner_freq=round(100*sum(1 for v in vals if v>=5)/n,1),
        monster_freq=round(100*sum(1 for v in vals if v>=10)/n,1), sum_mfe=round(sum(vals),1))

# ===== T4: ENTRY ATTRIBUTION POR CONVEXIDADE =====
# baseline = random-long CONTEXT-MATCHED: p/ cada entry, M bars aleatórios em [i-50,i+50] (mesmo regime local/beta)
rng=random.Random(2026); M=5; rand_mfe=[]
for b in EP:
    cand=[j for j in range(max(20,b-50),min(N-121,b+50)) if j!=b and ATR[j]]
    for j in rng.sample(cand,min(M,len(cand))):
        m=mfe_of(j)
        if m is not None: rand_mfe.append(m)
l2=stats([MFE[b] for b in EP]); rnd=stats(rand_mfe)
# bootstrap: runner_freq L2 vs random (diferença significativa?)
def boot_diff(a,b_pool,k_a,Nb=2000):
    rngb=random.Random(7); ge=0; obs=sum(1 for v in a if v>=5)/len(a)
    pool=b_pool
    for _ in range(Nb):
        s=[pool[rngb.randrange(len(pool))] for _ in range(k_a)]
        if sum(1 for v in s if v>=5)/k_a >= obs: ge+=1
    return round(ge/Nb,3)
p_runner=boot_diff([MFE[b] for b in EP], rand_mfe, len(EP))
print("="*68);print("T4 — ENTRY ATTRIBUTION POR CONVEXIDADE (L2/BPT vs random-long context-matched)")
print(f"{'metric':14}{'L2/BPT':>12}{'RANDOM':>12}")
for k in ('n','median','p75','p90','mean','runner_freq','monster_freq'):
    print(f"{k:14}{l2[k]:>12}{rnd[k]:>12}")
print(f"runner_freq L2={l2['runner_freq']}% vs random={rnd['runner_freq']}% | bootstrap p(rand>=L2)={p_runner}")
with open(f"{D}/l2_bpt_entry_attribution_convexity_audit.csv","w",newline="") as f:
    w=csv.writer(f,lineterminator="\n");w.writerow(['metric','L2_BPT','random_long_ctx_matched'])
    for k in ('n','median','p75','p90','mean','runner_freq','monster_freq','sum_mfe'): w.writerow([k,l2[k],rnd[k]])
    w.writerow(['bootstrap_p_random_ge_L2_runnerfreq',p_runner,''])

# ===== T5: MACRO ENGINE POR CONVEXIDADE =====
def bucket_conv(bidxs,label):
    vals=[MFE[b] for b in bidxs if b in MFE]
    s=stats(vals)
    stop_b2=sum(1 for b in bidxs if unc.get(b) and unc[b]['stop_before_2R']=='1')
    vstair=sum(fn(unc[b]['realized_vstair_120']) for b in bidxs if b in unc)
    s.update(label=label,stop_before_2R=stop_b2,sumR_vstair=round(vstair,1),
             runners_captured=sum(1 for b in bidxs if MFE.get(b,0)>=5),
             monsters_captured=sum(1 for b in bidxs if MFE.get(b,0)>=10))
    return s
TOTrun=sum(1 for b in EP if MFE[b]>=5); TOTmon=sum(1 for b in EP if MFE[b]>=10)
ENG_TAKE=[b for b in EP if eng[b]['policy']=='TAKE']; ENG_SKIP=[b for b in EP if eng[b]['policy']=='SKIP']
TC=[b for b in EP if xv2.get(b,{}).get('crossed_policy')=='TAKE_CONFIRMED']
print(f"\nT5 — MACRO ENGINE POR CONVEXIDADE | total runners={TOTrun} monsters={TOTmon}")
print(f"{'bucket':22}{'n':>4}{'run_freq':>9}{'mon_freq':>9}{'run_cap':>8}{'mon_cap':>8}{'sumMFE':>8}{'sumVstair':>10}{'stop<2R':>8}")
brows=[]
for lab,bs in [('ENGINE_TAKE',ENG_TAKE),('ENGINE_SKIP',ENG_SKIP),('INDIC_TAKE_CONFIRMED',TC),('BASELINE_276',EP)]:
    s=bucket_conv(bs,lab);brows.append(s)
    print(f"{lab:22}{s['n']:>4}{s['runner_freq']:>9}{s['monster_freq']:>9}{s['runners_captured']:>8}{s['monsters_captured']:>8}{s['sum_mfe']:>8}{s['sumR_vstair']:>10}{s['stop_before_2R']:>8}")
with open(f"{D}/l2_bpt_macro_engine_convexity_evaluation.csv","w",newline="") as f:
    cols=['label','n','runner_freq','monster_freq','runners_captured','monsters_captured','median','p90','sum_mfe','sumR_vstair','stop_before_2R']
    w=csv.DictWriter(f,fieldnames=cols,extrasaction='ignore',lineterminator="\n");w.writeheader();w.writerows(brows)

# ===== T6: EDGE SOURCE CLASSIFICATION =====
# por episódio: onde mora o valor?
ecls=[]
for b in EP:
    mfe=MFE[b]; cap=fn(unc[b]['capped_realR']); vstair=fn(unc[b]['realized_vstair_120']); letrun=fn(unc[b]['realized_letrun_120'])
    stop2=unc[b]['stop_before_2R']=='1'
    if mfe>=10: cls='CONVEXITY_ALPHA'
    elif mfe>=5: cls='CONVEXITY_ALPHA' if vstair>cap+2 else 'RISK_SHAPING_EDGE'
    elif mfe>=2: cls='EXIT_MANAGEMENT_EDGE' if vstair>cap else 'BETA_ONLY'
    elif stop2: cls='NO_EDGE_DETECTED'
    else: cls='BETA_ONLY'
    ecls.append(dict(bar_idx=b,datetime=unc[b]['datetime'],mfe_R=mfe,capped=cap,vstair=vstair,letrun=letrun,edge_class=cls))
from collections import Counter
print("\nT6 — EDGE SOURCE:",dict(Counter(r['edge_class'] for r in ecls)))
with open(f"{D}/l2_bpt_edge_source_classification.csv","w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=list(ecls[0].keys()),lineterminator="\n");w.writeheader();w.writerows(ecls)
print("\nDONE T4-T6.")
