#!/usr/bin/env python3
"""L2/BPT — Tarefa 2: CALIBRAÇÃO DE EXIT (full 276) com custo/slippage honesto. DIAGNÓSTICO.
Walk do frozen 4H path por episódio sob N políticas de exit; agrega sumR/avgR/PF/maxDD/streak/runner-capture/
giveback por P1/P2 e por ano + sensibilidade a custo. Causal stop-first. realR capado nunca árbitro (é 1 das políticas).
Outcome só avaliação. Sem produção/promoção/OOS. Outputs derived/regenerable."""
import json, csv
D="results"; RR="repro_recovery"
frozen=[json.loads(l) for l in open(f"{RR}/raw_features_2020_2026.jsonl")]
N=len(frozen); H=[r['high'] for r in frozen]; L=[r['low'] for r in frozen]; C=[r['close'] for r in frozen]
ATR=[None]*N; trs=[]
for i in range(1,N):
    trs.append(max(H[i]-L[i],abs(H[i]-C[i-1]),abs(L[i]-C[i-1])))
    if i>=14: ATR[i]=sum(trs[i-14:i])/14
outc={int(r['bar_idx']):r for r in csv.DictReader(open(f"{D}/l2_bpt_trade_qualification_outcomes.csv"))}
unc={int(r['bar_idx']):r for r in csv.DictReader(open(f"{D}/l2_bpt_uncapped_or_proxy_outcomes_276.csv"))}
pk={int(json.loads(l)['bar_idx']):json.loads(l) for l in open(f"{RR}/qual_packets.jsonl")}
def fn(v):
    try:return float(v)
    except:return None
RW=6;R_FLOOR=0.3;R_CEIL=1.5
def setup(i):
    p=C[i];atr=ATR[i]
    if not atr: return None
    lo=min(L[max(0,i-RW+1):i+1]);sl=lo-0.1*atr;risk=p-sl
    if risk<=0: return None
    if risk<R_FLOOR*atr: risk=R_FLOOR*atr;sl=p-risk
    if risk>R_CEIL*atr: risk=R_CEIL*atr;sl=p-risk
    return p,sl,risk

STAIR=[(2,0),(5,2),(8,5),(12,8),(16,12),(20,16)]
def exits(i,HZ=120):
    s=setup(i)
    if not s: return None
    p,sl,risk=s; end=min(i+HZ,N-1)
    # policy realized R
    R={}; peak=0.0; lock=-1.0; vstair_done=None; capped_done=None
    be_armed=False; be_done=None; p50_taken=False; p50_R=None; p50trail_done=None
    for j in range(i+1,end+1):
        highR=(H[j]-p)/risk; lowR=(L[j]-p)/risk
        # CAPPED +4R target (orig family)
        if capped_done is None:
            if L[j]<=sl: capped_done=-1.0
            elif highR>=4.0: capped_done=4.0
        # VSTAIR trailing (corrigido)
        if vstair_done is None:
            eff=max(sl,p+lock*risk)
            if L[j]<=eff: vstair_done=(eff-p)/risk
        # BE@2R then let-run
        if be_done is None:
            be_stop=p if be_armed else sl
            if L[j]<=be_stop: be_done=(0.0 if be_armed else -1.0)
            elif highR>=2.0: be_armed=True
        # PARTIAL50 @2R + trail rest
        if p50trail_done is None:
            if not p50_taken and L[j]<=sl: p50trail_done=-1.0   # stopped before partial
            else:
                if not p50_taken and highR>=2.0: p50_taken=True; p50_R=2.0
                if p50_taken:
                    eff=max(sl,p+lock*risk)
                    if L[j]<=eff: p50trail_done=0.5*p50_R+0.5*((eff-p)/risk)
        # advance peak/lock AFTER stop checks (stop-first)
        if L[j]>sl: peak=max(peak,highR)
        for trig,lk in STAIR:
            if peak>=trig and lk>lock: lock=float(lk)
        if L[j]<=sl: break
    close_end=(C[end]-p)/risk
    stopped_orig = any(L[j]<=sl for j in range(i+1,end+1))
    R['capped_4R']= capped_done if capped_done is not None else close_end
    R['letrun_static']= -1.0 if stopped_orig else close_end
    R['vstair']= vstair_done if vstair_done is not None else close_end
    R['be2R_letrun']= be_done if be_done is not None else close_end
    R['partial50_trail']= p50trail_done if p50trail_done is not None else (0.5*p50_R+0.5*close_end if p50_taken else close_end)
    return R, fn(unc[i]['mfe_R'])

POL=['capped_4R','letrun_static','vstair','be2R_letrun','partial50_trail']
COSTS=[0.20,0.35,0.50]
EP=sorted(outc)
per={pl:{} for pl in POL}; mfes={}
for b in EP:
    r=exits(b)
    if not r: continue
    R,mfe=r; mfes[b]=mfe
    for pl in POL: per[pl][b]=R[pl]

def window(b): return 'P1_2020-22' if pk[b]['datetime'][:10]<'2023-01-01' else 'P2_2023-26'
def yr(b): return pk[b]['datetime'][:4]
def agg(pl, sub=None, cost=0.0):
    bs=[b for b in EP if b in per[pl] and (sub is None or sub(b))]
    rs=[per[pl][b]-cost for b in bs]; n=len(rs)
    if not n: return None
    wins=sum(1 for r in rs if r>0); pos=sum(r for r in rs if r>0); neg=sum(r for r in rs if r<0)
    PF=round(pos/abs(neg),2) if neg<0 else 999
    cum=0;peak=0;mdd=0;ls=0;best=0
    order=sorted(bs,key=lambda b:pk[b]['datetime'])
    for b in order:
        r=per[pl][b]-cost; cum+=r; peak=max(peak,cum); mdd=max(mdd,peak-cum)
        if r>0: ls=0
        else: ls+=1; best=max(best,ls)
    # runner capture: realized R nos episódios MFE>=5; giveback = MFE-realized
    runs=[b for b in bs if mfes.get(b,0)>=5]
    run_cap=sum(per[pl][b]-cost for b in runs)
    giveback=sum(mfes[b]-(per[pl][b]) for b in runs)
    return dict(policy=pl,scope=('ALL' if sub is None else sub.__name__),cost=cost,n=n,
        sumR=round(sum(rs),1),avgR=round(sum(rs)/n,3),WR=round(100*wins/n,1),PF=PF,maxDD=round(mdd,1),
        Lstreak=best,runner_cap=round(run_cap,1),giveback=round(giveback,1),big_pres=len(runs))

rows=[]
print("="*92);print("EXIT CALIBRATION full276 (custo 0.35R/trade salvo nota)")
print(f"{'policy':16}{'n':>4}{'sumR':>8}{'avgR':>7}{'WR':>6}{'PF':>6}{'maxDD':>7}{'Lstk':>5}{'run_cap':>8}{'givebk':>8}")
for pl in POL:
    a=agg(pl,cost=0.35); rows.append(a)
    print(f"{pl:16}{a['n']:>4}{a['sumR']:>8}{a['avgR']:>7}{a['WR']:>6}{a['PF']:>6}{a['maxDD']:>7}{a['Lstreak']:>5}{a['runner_cap']:>8}{a['giveback']:>8}")
print("\n-- sensibilidade a custo (sumR) --")
print(f"{'policy':16}"+''.join(f'cost{c:>6}' for c in COSTS))
for pl in POL:
    print(f"{pl:16}"+''.join(f"{agg(pl,cost=c)['sumR']:>10}" for c in COSTS))
    for c in COSTS: rows.append(agg(pl,cost=c))
print("\n-- P1 vs P2 (cost 0.35) --")
def P1(b): return window(b)=='P1_2020-22'
def P2(b): return window(b)=='P2_2023-26'
P1.__name__='P1_2020-22'; P2.__name__='P2_2023-26'
for pl in POL:
    a1=agg(pl,P1,0.35); a2=agg(pl,P2,0.35); rows+=[a1,a2]
    print(f"{pl:16} P1 sumR={a1['sumR']:>7} avgR={a1['avgR']:>6} | P2 sumR={a2['sumR']:>7} avgR={a2['avgR']:>6}")
with open(f"{D}/l2_bpt_exit_calibration_full276.csv","w",newline="") as f:
    cols=['policy','scope','cost','n','sumR','avgR','WR','PF','maxDD','Lstreak','runner_cap','giveback','big_pres']
    w=csv.DictWriter(f,fieldnames=cols,extrasaction='ignore',lineterminator="\n");w.writeheader();w.writerows([r for r in rows if r])
print("\nDONE exit calibration.")
