#!/usr/bin/env python3
"""DEVIL'S ADVOCATE audit of l2_bpt_dynamic_reader_v2_staged S2.

Question: is S2's significance (lift 1.30, null p=0.001) REAL/structural, or an
in-sample-vote-sign artifact? The two vote signs suspected of in-sample selection:
  (A) vote_ENG: macro_state BULL_PULLBACK_CONTINUATION = -1  (observed lift 0.57 on THIS 276)
  (B) vote_IND: indicator_confluence STRONG_BEAR_CONFIRM = +1 (observed "inversion" on THIS 276)

We re-run S2 with the FULL vote (baseline reproduction) and with STRUCTURAL-ONLY votes
(A and B removed) to see whether the separation survives. We also compute Wilson CI for the
S2 TAKE bucket, audit causality of the read columns, and report the skip-winner-recovery
mechanics. Causal. Base 276. realR uncapped (let-run) is calibration, NOT arbiter.
Run from: .../v1/   (paths relative to that dir, mirroring the v2 script)
DIAGNOSTIC ONLY. No promotion / no OOS. Does NOT modify v2 files.
verified-at: 2026-06-22
"""
import csv, json, random, math

D="results"; RR="repro_recovery"
unc={int(r['bar_idx']):r for r in csv.DictReader(open(f"{D}/l2_bpt_uncapped_or_proxy_outcomes_276.csv"))}
eng={int(r['bar_idx']):r for r in csv.DictReader(open(f"{D}/l2_bpt_full276_macro_engine_confluence.csv"))}
xv2={int(r['bar_idx']):r for r in csv.DictReader(open(f"{D}/l2_bpt_full276_indicator_engine_cross_v2.csv"))}
pk={int(json.loads(l)['bar_idx']):json.loads(l) for l in open(f"{RR}/qual_packets.jsonl")}

def fn(v):
    try: return float(v)
    except: return None

EP=sorted(unc); MFE={b:fn(unc[b]['mfe_R']) for b in EP}
nR=sum(1 for b in EP if MFE[b]>=5); base=nR/len(EP)
WIN6={919,159,55,391,2053,351}

# ---------- VOTE FUNCTIONS ----------
# FULL = exact copy of v2 vote_ENG / vote_IND (reproduction guard)
def vote_ENG_full(b):
    e=eng[b]; v=0
    if e.get('capit')=='CLIMAX_RECLAIM': v+=1
    if e.get('momentum')=='LATE_TOP_EXHAUSTION': v-=1
    if e.get('supply') in('CLEAN_SKY_BULLISH','MARKUP_BREAKING'): v+=1
    if e.get('supply') in('SUPPLY_REJECTING_RISK','SUPPLY_BLOCKS_TARGET'): v-=1
    if e.get('macro_state') in('NO_OVERHEAD_MARKUP','MACRO_BULL_RUN_CONTINUATION','RANGE_MACRO_BULL_RECLAIM','CAPITULATION_RECLAIM_VALID'): v+=1
    if e.get('macro_state') in('BULL_PULLBACK_CONTINUATION','UNKNOWN_CONFLICT'): v-=1
    if e.get('fuel')=='high_fuel': v+=1
    return max(-1,min(1,v))

def vote_IND_full(b):
    x=xv2.get(b,{}); v=0
    if x.get('bubbles')=='BUBBLE_SELL_CLIMAX_BULL': v+=1
    if x.get('bubbles')=='BUBBLE_BUY_LATE': v-=1
    if x.get('smc')=='SMC_CHOCH_BULL_TRIGGER': v+=1
    if x.get('smc')=='SMC_CHOCH_TOP_REVERSAL': v-=1
    if x.get('nas')=='NAS_LONG_RECENT': v+=1
    if x.get('nas')=='NAS_SHORT_TOP': v-=1
    if x.get('indicator_confluence')=='STRONG_BEAR_CONFIRM': v+=1
    return max(-1,min(1,v))

# STRUCTURAL-ONLY = remove the two in-sample-informed signs.
# (A) BULL_PULLBACK_CONTINUATION shares a line with UNKNOWN_CONFLICT. UNKNOWN_CONFLICT=-1 is
#     structurally defensible (conflict => no conviction). So in structural-only we keep
#     UNKNOWN_CONFLICT=-1 and DROP only BULL_PULLBACK_CONTINUATION. We also test a HARSHER
#     variant that drops the whole conflict line, to bracket the effect.
def vote_ENG_struct(b, drop_unknown=False):
    e=eng[b]; v=0
    if e.get('capit')=='CLIMAX_RECLAIM': v+=1
    if e.get('momentum')=='LATE_TOP_EXHAUSTION': v-=1
    if e.get('supply') in('CLEAN_SKY_BULLISH','MARKUP_BREAKING'): v+=1
    if e.get('supply') in('SUPPLY_REJECTING_RISK','SUPPLY_BLOCKS_TARGET'): v-=1
    if e.get('macro_state') in('NO_OVERHEAD_MARKUP','MACRO_BULL_RUN_CONTINUATION','RANGE_MACRO_BULL_RECLAIM','CAPITULATION_RECLAIM_VALID'): v+=1
    # BULL_PULLBACK_CONTINUATION=-1 REMOVED (in-sample). UNKNOWN_CONFLICT kept unless drop_unknown.
    if not drop_unknown and e.get('macro_state')=='UNKNOWN_CONFLICT': v-=1
    if e.get('fuel')=='high_fuel': v+=1
    return max(-1,min(1,v))

def vote_IND_struct(b):
    x=xv2.get(b,{}); v=0
    if x.get('bubbles')=='BUBBLE_SELL_CLIMAX_BULL': v+=1
    if x.get('bubbles')=='BUBBLE_BUY_LATE': v-=1
    if x.get('smc')=='SMC_CHOCH_BULL_TRIGGER': v+=1
    if x.get('smc')=='SMC_CHOCH_TOP_REVERSAL': v-=1
    if x.get('nas')=='NAS_LONG_RECENT': v+=1
    if x.get('nas')=='NAS_SHORT_TOP': v-=1
    # STRONG_BEAR_CONFIRM=+1 REMOVED (in-sample inversion)
    return max(-1,min(1,v))

def policy(b, sources, thr=1):
    net=sum(f(b) for f in sources)
    if net>=thr: return 'TAKE'
    if net<=-thr: return 'SKIP'
    return 'REVIEW'

def wilson(k,n,z=1.96):
    if n==0: return (0,0)
    p=k/n; d=1+z*z/n
    c=(p+z*z/(2*n))/d; h=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/d
    return (c-h,c+h)

def evalstage(name, sources, thr=1):
    rng=random.Random(5)
    TAKE=[b for b in EP if policy(b,sources,thr)=='TAKE']
    n=len(TAKE); run=sum(1 for b in TAKE if MFE[b]>=5); rr=(run/n if n else 0)
    sw=sum(1 for b in EP if MFE[b]>=5 and eng[b]['policy'] in('SKIP','REVIEW','REVIEW_RISK') and policy(b,sources,thr)=='TAKE')
    sumlet=round(sum(fn(unc[b]['realized_letrun_120']) for b in TAKE),1)
    mv=[MFE[b] for b in EP]; ge=0
    if n:
        for _ in range(5000):
            idx=list(range(len(EP)));rng.shuffle(idx);s=idx[:n]
            if sum(1 for j in s if mv[j]>=5)/n>=rr: ge+=1
    p=ge/5000 if n else 1
    def per(b): return 'P1' if pk[b]['datetime'][:10]<'2023-01-01' else 'P2'
    p1=[b for b in TAKE if per(b)=='P1']; p2=[b for b in TAKE if per(b)=='P2']
    rr1=(sum(1 for b in p1 if MFE[b]>=5)/len(p1) if p1 else 0)
    rr2=(sum(1 for b in p2 if MFE[b]>=5)/len(p2) if p2 else 0)
    wlo,whi=wilson(run,n)
    miss=[b for b in WIN6 if b in EP and policy(b,sources,thr)=='SKIP']
    return dict(stage=name,n_take=n,run=run,runner_rate=round(100*rr,1),lift=round(rr/base,2),
        wilson_lo=round(100*wlo,1),wilson_hi=round(100*whi,1),skipW=sw,sumR_letrun=sumlet,null_p=round(p,4),
        recall_miss=len(miss),P1_n=len(p1),P1_rr=round(100*rr1,1),P2_n=len(p2),P2_rr=round(100*rr2,1))

print("="*110)
print(f"DA AUDIT — base={len(EP)} runners={nR} base_rate={base*100:.1f}%  (runner=mfe_R>=5)")
print("baselines to beat: supply_reject lift 1.08, static bear_leg lift 1.63")
print("="*110)

STAGES=[
 ("S2_FULL(repro)",      [vote_ENG_full,   vote_IND_full]),
 ("S2_struct(keepUNK)",  [lambda b: vote_ENG_struct(b,False), vote_IND_struct]),
 ("S2_struct(dropUNK)",  [lambda b: vote_ENG_struct(b,True),  vote_IND_struct]),
 ("S2_dropOnly_BPC",     [lambda b: vote_ENG_struct(b,False), vote_IND_full]),    # remove only sign A
 ("S2_dropOnly_BEAR",    [vote_ENG_full,   vote_IND_struct]),                     # remove only sign B
]
hdr=f"{'stage':22}{'nT':>4}{'run':>4}{'rr%':>6}{'lift':>6}{'wilson95':>14}{'skipW':>6}{'sumLet':>8}{'p':>8}{'miss':>5}{'P1':>10}{'P2':>10}"
print(hdr)
rows=[]
for nm,srcs in STAGES:
    r=evalstage(nm,srcs); rows.append(r)
    print(f"{r['stage']:22}{r['n_take']:>4}{r['run']:>4}{r['runner_rate']:>6}{r['lift']:>6}"
          f"{'['+str(r['wilson_lo'])+','+str(r['wilson_hi'])+']':>14}{r['skipW']:>6}{r['sumR_letrun']:>8}"
          f"{r['null_p']:>8}{r['recall_miss']:>5}{str(r['P1_rr'])+'%(n'+str(r['P1_n'])+')':>10}{str(r['P2_rr'])+'%(n'+str(r['P2_n'])+')':>10}")

# --- isolate each suspect sign's marginal effect on the TAKE set ---
print("\n--- bucket-level runner-rate of the two suspect states (in-sample anchors) ---")
def staterate(col,val,src):
    sel=[b for b in EP if (eng if src=='eng' else xv2).get(b,{}).get(col)==val]
    run=sum(1 for b in sel if MFE[b]>=5); n=len(sel)
    print(f"  {col}={val:30} n={n:3} runner_rate={100*run/n if n else 0:5.1f}% lift={ (run/n)/base if n else 0:.2f}")
staterate('macro_state','BULL_PULLBACK_CONTINUATION','eng')
staterate('macro_state','UNKNOWN_CONFLICT','eng')
staterate('indicator_confluence','STRONG_BEAR_CONFIRM','xv2')

# --- causality audit: confirm vote columns never read an outcome field ---
OUTCOME_COLS={'mfe_R','mae_R','max_run_R','realized_letrun_60','realized_letrun_120',
 'realized_vstair_60','realized_vstair_120','capped_realR','runner_flag','EVAL_realR','EVAL_exitype'}
eng_cols=set(eng[EP[0]].keys()); xv2_cols=set(xv2[EP[0]].keys())
used_eng={'capit','momentum','supply','macro_state','fuel'}
used_xv2={'bubbles','smc','nas','indicator_confluence'}
leak=(used_eng|used_xv2)&OUTCOME_COLS
print("\n--- causality: vote columns vs outcome columns ---")
print(f"  vote_ENG reads: {sorted(used_eng)}  (all in eng file: {used_eng<=eng_cols})")
print(f"  vote_IND reads: {sorted(used_xv2)}  (all in xv2 file: {used_xv2<=xv2_cols})")
print(f"  intersection with OUTCOME cols (mfe/letrun/realR): {leak or 'NONE'}")
print(f"  NOTE eng file also carries EVAL_realR/EVAL_exitype but vote_ENG never reads them.")

with open(f"{D}/_DA_v2_structural_only_results.csv","w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0].keys()),lineterminator="\n");w.writeheader();w.writerows(rows)
print("\nwrote results/_DA_v2_structural_only_results.csv  | DONE")
