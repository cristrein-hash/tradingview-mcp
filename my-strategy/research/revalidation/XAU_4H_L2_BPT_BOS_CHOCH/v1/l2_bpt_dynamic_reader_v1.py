#!/usr/bin/env python3
"""L2/BPT — DYNAMIC MULTI-FACTORIAL MARKET READING STATE MACHINE v1 (7 sub-leitores).
Implementa `docs/XAU_4H_L2_BPT_DYNAMIC_MARKET_READING_STATE_MACHINE_SPEC.md`. Causal (só barras<=entrada).
Objetivo PRIMÁRIO = correção de mislabel na BASE 276: skip-winners->TAKE, loser-takes->SKIP, medido em convexidade
uncapped (MFE/let-run). Topos = secundário. NÃO eixo único: convergência de ≥2-3 sub-estados. DIAGNÓSTICO.
Sem produção/promoção/OOS. realR capado nunca árbitro. Multi-fatorial + trajetória + duplo-objetivo (satisfaz anti-miopia)."""
import json, csv, random
D="results"; RR="repro_recovery"
frozen=[json.loads(l) for l in open(f"{RR}/raw_features_2020_2026.jsonl")]
N=len(frozen); H=[r['high'] for r in frozen]; L=[r['low'] for r in frozen]; C=[r['close'] for r in frozen]
pk={int(json.loads(l)['bar_idx']):json.loads(l) for l in open(f"{RR}/qual_packets.jsonl")}
unc={int(r['bar_idx']):r for r in csv.DictReader(open(f"{D}/l2_bpt_uncapped_or_proxy_outcomes_276.csv"))}
eng={int(r['bar_idx']):r for r in csv.DictReader(open(f"{D}/l2_bpt_full276_macro_engine_confluence.csv"))}
dec={int(r['bar_idx']):r for r in csv.DictReader(open(f"{D}/l2_bpt_full276_macro_bear_v3_decisions.csv"))}
def fn(v):
    try:return float(v)
    except:return None
def fi(v):
    try:return int(float(v))
    except:return 0
def tb(v): return v in (1,'1',True,'True')
EP=sorted(unc); MFE={b:fn(unc[b]['mfe_R']) for b in EP}
WIN6={919,159,55,391,2053,351}  # 6 curated winners mapeados (E23,E27,E30,E17,E40,E1)

# ---- feature de TRAJETÓRIA derivada do frozen path (causal): desaceleração do slope ----
def decel(i,w=6):
    """down-slope achatando? slope(close) últimas w barras vs w anteriores. True = desacelerando (exaurindo)."""
    if i-2*w<0: return False
    rec=(C[i]-C[i-w])/w; prev=(C[i-w]-C[i-2*w])/w
    return rec>prev  # recente menos negativo que prévio = perda de força de queda

# ---- os 7 SUB-LEITORES (cada um = estado de trajetória, causal) ----
def r1_supply(P,Dx):
    sc=Dx.get('sup_cat',''); broke=tb(P.get('supply_broken_before')); rej=tb(P.get('supply_rejected_before'))
    overhead=tb(P.get('has_4h_supply_overhead')); dist=fn(P.get('dist_4h_supply_low_atr'))
    if sc=='CLEAN_SKY' or not overhead: return 'CLEAR'
    if sc=='SUPPLY_NEAR_BUT_BROKEN' or (broke and not rej): return 'MARKUP_ACCEPTED'
    if broke and dist is not None and dist<1.0: return 'MARKUP_BREAKING'
    if sc in('SUPPLY_NEAR_AND_REJECTING','SUPPLY_FRESH_DANGEROUS','SUPPLY_BLOCKS_TARGET') or rej: return 'REJECTING'
    return 'TESTING'
def r2_leg(P):
    lp90=fn(P.get('legpos90')); trend=fn(P.get('trend_30_atr')); bdiv=fn(P.get('rsi_bear_div_20b'))
    strong=(trend is not None and trend>=1.5)
    if lp90 is not None and lp90>=90 and (trend is not None and trend<0) and (bdiv or 0)>0: return 'EXHAUSTED'
    if lp90 is not None and lp90>=85 and not strong: return 'LATE_EXTENDED'
    if lp90 is not None and lp90<=50 and strong: return 'YOUNG_IMPULSE'
    return 'MID_LEG'
def r3_pullback(P):
    reclaim=fn(P.get('reclaim_body_atr')) or 0; drop=fn(P.get('drop20_atr')) or 0
    buy=fi(P.get('bub_buy_s'))+fi(P.get('bub_buy_m'))+fi(P.get('bub_buy_L'))
    sell=fi(P.get('bub_sell_s'))+fi(P.get('bub_sell_m'))+fi(P.get('bub_sell_L'))
    if reclaim>0.5 and drop<1.5 and buy>=sell: return 'BOUGHT_DIP'
    if sell>buy and reclaim<0.3: return 'DISTRIBUTION'
    if drop>=1.5 and reclaim>0: return 'DEEP_RECLAIM'
    return 'MID'
def r4_capit(P):
    drop=fn(P.get('drop20_atr')) or 0; rmin=fn(P.get('rsi_min8')); reclaim=fn(P.get('reclaim_body_atr'))
    bldiv=fn(P.get('rsi_bull_div_20b')) or 0; demand=tb(P.get('demand_origin_of_leg')) or tb(P.get('demand_touched_on_retest'))
    if drop>=2.0 and rmin is not None and rmin<=35 and (reclaim or 0)>0: return 'CLIMAX_RECLAIM'
    if drop>=2.0 and (reclaim is None or reclaim<=0): return 'FALLING_KNIFE'
    if rmin is not None and rmin<=38 and demand and bldiv>0: return 'BOTTOM_FORMING'
    return 'NONE'
def r5_regime(Dx):
    leg=Dx.get('macro_reader_leg',''); mb=Dx.get('macro_broken')=='True'; wsl=fn(Dx.get('weekly_slope'))
    if leg=='MACRO_BEAR_LEG' or (mb and (wsl is not None and wsl<=0)): return 'BEAR_MARKDOWN'
    if leg=='MACRO_BULL_LEG': return 'BULL'
    return 'RANGE'
def r6_volume(P):
    bv=P.get('below_VAL'); dpoc=fn(P.get('dist_POC_atr')); dval=fn(P.get('dist_VAL_atr'))
    if bv in(True,'True') or (dval is not None and dval<0): return 'REJECTED_BELOW'
    if dpoc is not None and dpoc>0.3: return 'ACCEPTING_ABOVE_VALUE'
    return 'IN_VALUE'
def r7_bearbuy(P,regime,i):
    if regime!='BEAR_MARKDOWN': return 'NOT_BEAR'
    cap=r4_capit(P); reclaim=fn(P.get('reclaim_body_atr')) or 0; bldiv=fn(P.get('rsi_bull_div_20b')) or 0
    demand=tb(P.get('demand_origin_of_leg')) or tb(P.get('demand_touched_on_retest'))
    exhausting=decel(i)
    if exhausting and (cap in('CLIMAX_RECLAIM','BOTTOM_FORMING') or (reclaim>0.3 and (bldiv>0 or demand))): return 'LEGITIMATE_BEAR_BUY'
    return 'BEAR_PULLBACK_TRAP'

# ---- CONVERGÊNCIA (≥2-3 sub-estados; primário=recuperar skip-winner; secundário=cortar loser-take) ----
def read(b):
    P=pk[b]; Dx=dec.get(b,{}); i=b
    s1=r1_supply(P,Dx); s2=r2_leg(P); s3=r3_pullback(P); s4=r4_capit(P); s5=r5_regime(Dx); s6=r6_volume(P); s7=r7_bearbuy(P,s5,i)
    demand=tb(P.get('demand_origin_of_leg')) or tb(P.get('demand_touched_on_retest'))
    # PRIMÁRIO — recuperar skip-winners (convergência)
    if s7=='LEGITIMATE_BEAR_BUY': pol,why='TAKE','LEGITIMATE_BEAR_BUY'
    elif s4 in('CLIMAX_RECLAIM','BOTTOM_FORMING') and s5!='BEAR_MARKDOWN' and (demand or s6=='ACCEPTING_ABOVE_VALUE'): pol,why='TAKE','REVERSAL_RUNNER'
    elif s1 in('MARKUP_ACCEPTED','MARKUP_BREAKING') and s2 in('YOUNG_IMPULSE','MID_LEG') and s3 in('BOUGHT_DIP','DEEP_RECLAIM'): pol,why='TAKE','MARKUP_CONTINUATION'
    # SECUNDÁRIO — cortar loser-takes (não perseguir top-precision)
    elif s7=='BEAR_PULLBACK_TRAP': pol,why='SKIP','BEAR_PULLBACK_TRAP'
    elif s1=='REJECTING' and s2 in('LATE_EXTENDED','EXHAUSTED') and s3=='DISTRIBUTION': pol,why='SKIP','TOP_TRAP_AVOID'
    else: pol,why='REVIEW','AMBIGUOUS'
    return pol,why,(s1,s2,s3,s4,s5,s6,s7)

# ---- RODAR + AVALIAR correção de mislabel ----
rows=[];
for b in EP:
    pol,why,S=read(b); o_pol=eng[b].get('policy'); mfe=MFE[b]
    eng_take = o_pol=='TAKE'; eng_skip = o_pol in('SKIP','REVIEW','REVIEW_RISK')
    new_take = pol=='TAKE'; new_skip = pol=='SKIP'
    runner=mfe>=5; loser=mfe<2
    rows.append(dict(bar_idx=b,datetime=unc[b]['datetime'],new_pol=pol,why=why,eng_pol=o_pol,mfe_R=mfe,
        letrun=fn(unc[b]['realized_letrun_120']),
        skip_winner_recovered=int(runner and eng_skip and new_take),
        loser_take_cut=int(loser and eng_take and new_skip),
        s_supply=S[0],s_leg=S[1],s_pullback=S[2],s_capit=S[3],s_regime=S[4],s_vol=S[5],s_bearbuy=S[6]))
with open(f"{D}/l2_bpt_dynamic_reader_v1_reading.csv","w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0].keys()),lineterminator="\n");w.writeheader();w.writerows(rows)

from collections import Counter
nR=sum(1 for b in EP if MFE[b]>=5); nL=sum(1 for b in EP if MFE[b]<2); base=nR/len(EP)
NEW_TAKE=[b for b in EP if read(b)[0]=='TAKE']; ENG_TAKE=[b for b in EP if eng[b].get('policy')=='TAKE']
def sumlet(bs): return round(sum(fn(unc[b]['realized_letrun_120']) for b in bs),1)
def runrate(bs):
    n=len(bs); return (round(100*sum(1 for b in bs if MFE[b]>=5)/n,1) if n else 0)
print("="*70);print("DYNAMIC READER v1 — 7 sub-leitores (base 276)")
print("convergência (why):",dict(Counter(r['why'] for r in rows)))
print("new policy:",dict(Counter(r['new_pol'] for r in rows)))
print(f"\nbase runner_rate={base*100:.1f}% (R{nR}/L{nL})")
sw=sum(r['skip_winner_recovered'] for r in rows); lc=sum(r['loser_take_cut'] for r in rows)
print(f"\n--- CORREÇÃO DE MISLABEL (vs engine policy) ---")
print(f"PRIMÁRIO  skip-winners recuperados (runner que engine skipou, agora TAKE): {sw}")
print(f"SECUNDÁRIO loser-takes cortados (loser que engine tomou, agora SKIP):      {lc}")
print(f"\nNEW_TAKE  n={len(NEW_TAKE)} runner_rate={runrate(NEW_TAKE)}% (lift {runrate(NEW_TAKE)/100/base:.2f}) sumR_letrun={sumlet(NEW_TAKE)}")
print(f"ENG_TAKE  n={len(ENG_TAKE)} runner_rate={runrate(ENG_TAKE)}% (lift {runrate(ENG_TAKE)/100/base:.2f}) sumR_letrun={sumlet(ENG_TAKE)}")
print(f"BASELINE  n={len(EP)} runner_rate={base*100:.1f}% sumR_letrun={sumlet(EP)}")
print(f"ΔsumR_letrun (NEW_TAKE - ENG_TAKE) = {sumlet(NEW_TAKE)-sumlet(ENG_TAKE):+.1f}R")
# recall-gate
miss=[b for b in WIN6 if b in EP and read(b)[0]=='SKIP']
print(f"\nRECALL-GATE 6 winners curados: {'PASS (0 skipados)' if not miss else f'FAIL skipados={miss}'}")
# sub-janela
def win(b): return 'P1' if pk[b]['datetime'][:10]<'2023-01-01' else 'P2'
for w_ in ('P1','P2'):
    bs=[b for b in NEW_TAKE if win(b)==w_]; print(f"  NEW_TAKE {w_}: n={len(bs)} runner_rate={runrate(bs)}% sumR_letrun={sumlet(bs)}")
# null: NEW_TAKE runner_rate vs subset aleatório do mesmo tamanho
rng=random.Random(3); k=len(NEW_TAKE); obs=runrate(NEW_TAKE)/100; ge=0;Nperm=2000
mfev=[MFE[b] for b in EP]
for _ in range(Nperm):
    idx=list(range(len(EP)));rng.shuffle(idx);s=idx[:k]
    if sum(1 for j in s if mfev[j]>=5)/k>=obs: ge+=1
print(f"\nNULL: NEW_TAKE runner_rate {obs*100:.1f}% | p(rand>=obs)={ge/Nperm:.3f}  (baselines estáticos a bater: supply_reject 1.08, bear_leg 1.63)")
print("\nDONE dynamic reader v1.")
