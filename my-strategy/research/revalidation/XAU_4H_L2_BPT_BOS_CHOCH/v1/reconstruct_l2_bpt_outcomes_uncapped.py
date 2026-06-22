#!/usr/bin/env python3
"""L2/BPT — RE-INSTRUMENTAÇÃO DO NÓ OUTCOME/EXIT (uncapped + convexo). DIAGNÓSTICO/derived.
Reconstrói por episódio (276) o alvo econômico que o realR CAPADO (+3.9R) apagou: MFE/MAE, hits 2..10R,
max_run_R uncapped, time-to, runner_flag, e exits CONVEXOS (let-run static + V-stair trailing) vs o capado.
Fonte = frozen 4H OHLC `repro_recovery/raw_features_2020_2026.jsonl` (contíguo, mesma fonte do realR original).
Unidade R = SL estrutural IDÊNTICO ao real_outcome.py (swing low 6b -0.1ATR, risk floor 0.3/ceil 1.5 ATR),
stop-first intrabar (conservador). NÃO produção, NÃO promoção, NÃO OOS, realR capado NUNCA como árbitro.
Outputs derived/regenerable, não source-of-truth."""
import json, csv
D="results"; RR="repro_recovery"
frozen=[json.loads(l) for l in open(f"{RR}/raw_features_2020_2026.jsonl")]
N=len(frozen); H=[r['high'] for r in frozen]; L=[r['low'] for r in frozen]; C=[r['close'] for r in frozen]
ATR=[None]*N; trs=[]
for i in range(1,N):
    trs.append(max(H[i]-L[i],abs(H[i]-C[i-1]),abs(L[i]-C[i-1])))
    if i>=14: ATR[i]=sum(trs[i-14:i])/14
outc={int(r['bar_idx']):r for r in csv.DictReader(open(f"{D}/l2_bpt_trade_qualification_outcomes.csv"))}
pk={int(json.loads(l)['bar_idx']):json.loads(l) for l in open(f"{RR}/qual_packets.jsonl")}
def fn(v):
    try:return float(v)
    except:return None

RW=6; R_FLOOR=0.3; R_CEIL=1.5
def structural_sl(i,p,atr):
    lo=min(L[max(0,i-RW+1):i+1]); sl=lo-0.1*atr; risk=p-sl
    if risk<=0: return None,None
    if risk<R_FLOOR*atr: sl=p-R_FLOOR*atr; risk=R_FLOOR*atr
    if risk>R_CEIL*atr: sl=p-R_CEIL*atr; risk=R_CEIL*atr   # cap risk (R-unit) — same family as census
    return sl,risk

def walk(i,p,sl,risk,HZ):
    """stop-first intrabar. let-run = SL original + time-stop (sem target). V-stair = TRAILING stop REAL:
    o lock vira o stop efetivo (exit quando low retrai ao lock). Bug corrigido (DA a8122f3): lock é gatilho de
    saída, não só piso aditivo. Ordem stop-first: low (checa stop) antes de high (sobe lock)."""
    end=min(i+HZ,N-1); mfe=0.0; mfe_bar=i; mae=0.0; stopped=None
    hits={k:None for k in (2,3,5,8,10)}
    STAIR=[(2,0),(5,2),(8,5),(12,8),(16,12),(20,16)]; lock=-1.0; peakR=0.0
    vstair_exit=None
    for j in range(i+1,end+1):
        highR=(H[j]-p)/risk
        mae=max(mae,(p-L[j])/risk)
        # V-stair trailing: stop efetivo = max(SL original, p+lock*risk); exit quando low <= ele (stop-first)
        eff_stop_price=max(sl, p+lock*risk)
        if vstair_exit is None and L[j]<=eff_stop_price:
            vstair_exit=(eff_stop_price-p)/risk    # = lock se lock>-1, senão -1
        # let-run / MFE usam SL original
        if L[j]<=sl and stopped is None:
            stopped=j
            if vstair_exit is None: vstair_exit=-1.0
            break
        if highR>mfe: mfe=highR; mfe_bar=j
        peakR=max(peakR,highR)
        for k in hits:
            if hits[k] is None and highR>=k: hits[k]=j-i
        # sobe lock DEPOIS de checar stop (stop-first, conservador)
        for trig,lk in STAIR:
            if peakR>=trig and lk>lock: lock=float(lk)
    if stopped is not None: realized_letrun=-1.0
    else: realized_letrun=(C[end]-p)/risk
    if vstair_exit is not None: realized_vstair=vstair_exit
    else: realized_vstair=(C[end]-p)/risk
    mae_before=0.0
    if mfe_bar>i: mae_before=max([(p-L[j])/risk for j in range(i+1,mfe_bar+1)]+[0.0])
    return dict(mfe=round(mfe,2),mae=round(mae,2),mae_before=round(mae_before,2),
        t_max=mfe_bar-i,hit2=hits[2],hit3=hits[3],hit5=hits[5],hit8=hits[8],hit10=hits[10],
        stopped=(stopped is not None),realized_letrun=round(realized_letrun,2),realized_vstair=round(realized_vstair,2))

rows=[]
for bi in sorted(outc):
    p=C[bi]; atr=ATR[bi]
    if not atr: continue
    sl,risk=structural_sl(bi,p,atr)
    if sl is None: continue
    o=outc[bi]; capped=fn(o['realR'])
    w60=walk(bi,p,sl,risk,60); w120=walk(bi,p,sl,risk,120)
    mfe=w120['mfe']
    bucket=('R0_neg' if mfe<2 else 'R2_5' if mfe<5 else 'R5_10' if mfe<10 else 'R10p')
    rows.append(dict(bar_idx=bi,datetime=pk[bi]['datetime'][:10],risk_atr=round(risk/atr,2),
        capped_realR=capped, capped_exitype=o['exitype'],
        mfe_R=mfe, mae_R=w120['mae'], mae_before_mfe=w120['mae_before'], max_run_R=mfe, runner_bucket=bucket,
        runner_flag=int(mfe>=5), monster_flag=int(mfe>=10),
        hit2=w120['hit2'] is not None,hit3=w120['hit3'] is not None,hit5=w120['hit5'] is not None,
        hit8=w120['hit8'] is not None,hit10=w120['hit10'] is not None,
        time_to_2R=w120['hit2'], time_to_max=w120['t_max'],
        stop_before_2R=int(w120['hit2'] is None and w120['stopped']),
        realized_letrun_60=w60['realized_letrun'], realized_letrun_120=w120['realized_letrun'],
        realized_vstair_60=w60['realized_vstair'], realized_vstair_120=w120['realized_vstair']))
with open(f"{D}/l2_bpt_uncapped_or_proxy_outcomes_276.csv","w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0].keys()),lineterminator="\n");w.writeheader();w.writerows(rows)

# ---- SUMMARY: onde a convexidade foi apagada ----
import statistics as st
n=len(rows)
capped_at_39=sum(1 for r in rows if abs(r['capped_realR']-3.9)<0.05)
mfe_gt_5=sum(1 for r in rows if r['mfe_R']>=5); mfe_gt_10=sum(1 for r in rows if r['mfe_R']>=10)
# runners comprimidos = capado em 3.9 mas MFE real >> 3.9
compressed=[r for r in rows if r['capped_realR']>=3.0 and r['mfe_R']>5]
big_mfe_capped=[r for r in rows if r['mfe_R']>=8]
sum_capped=sum(r['capped_realR'] for r in rows)
sum_letrun120=sum(r['realized_letrun_120'] for r in rows)
sum_vstair120=sum(r['realized_vstair_120'] for r in rows)
print("="*68);print("RE-INSTRUMENTAÇÃO OUTCOME/EXIT — UNCAPPED + CONVEXO (276)")
print(f"n={n}")
print(f"capados exatamente em +3.9R: {capped_at_39}")
print(f"MFE_R>=5 (runners reais disponíveis): {mfe_gt_5} | MFE_R>=10 (monstros): {mfe_gt_10}")
print(f"runners COMPRIMIDOS (capado~3.9 mas MFE real >5R): {len(compressed)}")
print(f"  exemplos:",[(r['datetime'],r['mfe_R']) for r in sorted(compressed,key=lambda x:-x['mfe_R'])[:8]])
print(f"\nMFE_R distribuição: median={st.median(r['mfe_R'] for r in rows):.2f} p75={sorted(r['mfe_R'] for r in rows)[int(n*0.75)]:.2f} p90={sorted(r['mfe_R'] for r in rows)[int(n*0.90)]:.2f} max={max(r['mfe_R'] for r in rows):.2f}")
COST=0.35  # 0.2R custo + 0.15R slippage por trade (DA a8122f3)
print(f"\nsumR comparação (mesma entrada, exits diferentes):")
print(f"  CAPADO (+3.9 target):      {sum_capped:+.1f}R")
print(f"  let-run static (H120):     {sum_letrun120:+.1f}R   | c/ custo {COST}R/trade: {sum_letrun120-COST*n:+.1f}R")
print(f"  V-stair trailing (H120):   {sum_vstair120:+.1f}R   | c/ custo {COST}R/trade: {sum_vstair120-COST*n:+.1f}R  (trailing CORRIGIDO)")
print(f"\nbucket MFE_R:",{b:sum(1 for r in rows if r['runner_bucket']==b) for b in ('R0_neg','R2_5','R5_10','R10p')})
# Tarefa 2 output: convexity destruction audit
with open(f"{D}/l2_bpt_convexity_destruction_audit.csv","w",newline="") as f:
    w=csv.writer(f,lineterminator="\n")
    w.writerow(['metric','value','interpretacao'])
    w.writerow(['n_episodes',n,'população'])
    w.writerow(['capped_at_+3.9R',capped_at_39,'trades grudados no teto do target'])
    w.writerow(['MFE_R>=5_available',mfe_gt_5,'runners REAIS que existiram no path'])
    w.writerow(['MFE_R>=10_monsters',mfe_gt_10,'monstros achatados pelo cap'])
    w.writerow(['runners_compressed',len(compressed),'capado~3.9 mas MFE real >5R = convexidade apagada'])
    w.writerow(['sumR_capped',round(sum_capped,1),'régua atual (hit-rate-ish)'])
    w.writerow(['sumR_letrun_H120',round(sum_letrun120,1),'mesma entrada, exit deixa correr'])
    w.writerow(['sumR_vstair_H120',round(sum_vstair120,1),'mesma entrada, exit convexo V-stair'])
    w.writerow(['delta_vstair_vs_capped',round(sum_vstair120-sum_capped,1),'convexidade recuperável trocando SÓ o exit'])
print("\nDONE. outputs: uncapped_or_proxy_outcomes_276, convexity_destruction_audit.")
