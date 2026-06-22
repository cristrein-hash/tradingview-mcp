#!/usr/bin/env python3
"""FULL 276 — CONFLUÊNCIA DE INDICADORES v2 CONTEXT-AWARE × RE-ENGINE (canon efaf48a).
Corrige o bug de polaridade da v1 (DA afec87b): a v1 codificou bub_sell e SMC_CHoCH como bear context-free;
em entrada LONG L2/BPT num RECLAIM/FUNDO o sell-bubble = clímax de venda = BULLISH e o CHoCH = gatilho bullish
(memória feedback_bubbles_polarity_rule + canon L2/BPT). Polaridade agora CONDICIONADA ao contexto estrutural
do engine (topo vs fundo/pullback). DIAGNÓSTICO. realR CAPADO (+3.9R) = hit-rate — LIMITAÇÃO declarada: expectancy
real (uncapped) exige re-simulação de saídas (bloco separado autorizado). Thresholds declarados. Sem produção/OOS/promoção."""
import json, csv, random
D="results"; RR="repro_recovery"
pk={int(json.loads(l)['bar_idx']):json.loads(l) for l in open(f"{RR}/qual_packets.jsonl")}
eng={int(r['bar_idx']):r for r in csv.DictReader(open(f"{D}/l2_bpt_full276_macro_engine_confluence.csv"))}
outc={int(r['bar_idx']):r for r in csv.DictReader(open(f"{D}/l2_bpt_trade_qualification_outcomes.csv"))}
def fn(v):
    try:return float(v)
    except:return None
def fi(v):
    try:return int(float(v))
    except:return 0
ALL=sorted(pk.keys(),key=lambda b:pk[b]['datetime'])
WIN={'WIN_HELD','WIN_RUNNER'}
TOTR=sum(1 for b in ALL if outc[b]['exitype']=='WIN_RUNNER'); TOTB=sum(1 for b in ALL if outc[b]['exitype'] in WIN)

RISK_FAM={'BEAR_BOUNCE_RISK','CORRECTIVE_BEAR_LEG','LATE_TOP_EXHAUSTION','SUPPLY_COLADA_REJECTION'}
BOTTOM_STATES={'CAPITULATION_RECLAIM_VALID','BOTTOM_REVERSAL_VALID'}

def context_of(b):
    """classifica o contexto estrutural do engine: TOP / BOTTOM / PULLBACK / NEUTRAL (define a polaridade)."""
    e=eng[b]; ms=e['macro_state']; mom=e['momentum']; cap=e['capit']; fam=e['family']; legpos=fn(pk[b].get('legpos90'))
    if mom=='LATE_TOP_EXHAUSTION' or ms in('LATE_TOP_EXHAUSTION',): return 'TOP'
    if cap=='CLIMAX_RECLAIM' or ms in BOTTOM_STATES: return 'BOTTOM'
    if fam=='RISK': return 'TOP'           # bear/topo-risco: polaridade de distribuição
    if fam=='BULL':
        if legpos is not None and legpos>=85 and mom=='WEAK_MOMENTUM': return 'TOP'
        return 'PULLBACK'                  # bull macro saudável = pullback/continuação
    return 'NEUTRAL'

def ind_bubbles_ctx(P,ctx):
    """polaridade CONDICIONADA: TOP→sell=bear/distribuição; BOTTOM→sell=BULLISH(clímax); PULLBACK→buy=acumulação."""
    bL=fi(P.get('bub_buy_L')); sL=fi(P.get('bub_sell_L')); blg=fi(P.get('bub_large_buy_10b')); slg=fi(P.get('bub_large_sell_10b')); ratio=fn(P.get('bub_buy_sell_ratio'))
    buy_dom=(bL>=1) or (blg>=2) or (ratio is not None and ratio>=1.5)
    sell_dom=(sL>=1) or (slg>=2) or (ratio is not None and ratio<=0.5)
    if ctx=='BOTTOM':
        if sell_dom: return +1,'BUBBLE_SELL_CLIMAX_BULL'   # clímax de venda no fundo = reversão bull
        if buy_dom:  return +1,'BUBBLE_BUY_ACCUM'
        return 0,'BUBBLE_MIXED'
    if ctx=='PULLBACK':
        if buy_dom: return +1,'BUBBLE_BUY_ACCUM_PULLBACK'  # acumulação no pullback = bull
        if sell_dom and (slg>=2): return -1,'BUBBLE_SELL_WARN'
        return 0,'BUBBLE_MIXED'
    if ctx=='TOP':
        if sell_dom: return -1,'BUBBLE_SELL_DISTRIBUTION'  # distribuição no topo = bear
        if buy_dom:  return 0,'BUBBLE_BUY_LATE'            # buy no topo = tarde, não confirma
        return 0,'BUBBLE_MIXED'
    return (0,'BUBBLE_NEUTRAL')

def ind_nas_ctx(P,ctx):
    nl=fi(P.get('nas_long_new_8b')); ns=fi(P.get('nas_short_new_8b')); n1d=fi(P.get('nas_1d_long_recent'))
    if ctx=='TOP':
        if ns>=1: return -1,'NAS_SHORT_TOP'                # cluster short no topo = bear (memória)
        return 0,'NAS_NEUTRAL'
    # fundo/pullback: NAS long confirma bull; short num fundo = exaustão de venda (não veta)
    if nl>=1 or n1d>=1: return +1,'NAS_LONG_RECENT'
    if ns>=1 and ctx=='BOTTOM': return 0,'NAS_SHORT_AT_BOTTOM_IGN'
    if ns>=1: return -1,'NAS_SHORT'
    return 0,'NAS_NEUTRAL'

def ind_smc_ctx(P,ctx):
    bos=str(P.get('smc_bos')); choch=str(P.get('smc_choch'))
    bos_on=bos not in('0','None','','False','0.0'); choch_on=choch not in('0','None','','False','0.0')
    if ctx in('BOTTOM','PULLBACK'):
        if choch_on: return +1,'SMC_CHOCH_BULL_TRIGGER'   # CHoCH no reclaim = gatilho bull de entrada
        if bos_on:   return +1,'SMC_BOS_CONTINUATION'
        return 0,'SMC_NONE'
    if ctx=='TOP':
        if choch_on: return -1,'SMC_CHOCH_TOP_REVERSAL'   # CHoCH no topo = reversão bear
        if bos_on:   return 0,'SMC_BOS_LATE'
        return 0,'SMC_NONE'
    return 0,'SMC_NONE'

def ind_rsi_ctx(P,ctx):
    bd=fn(P.get('rsi_bear_div_20b')); bld=fn(P.get('rsi_bull_div_20b'))
    if ctx=='TOP' and bd is not None and bd>0: return -1,'RSI_BEAR_DIV_TOP'
    if ctx in('BOTTOM','PULLBACK') and bld is not None and bld>0: return +1,'RSI_BULL_DIV'
    if bd is not None and bd>0 and ctx!='BOTTOM': return -1,'RSI_BEAR_DIV'
    return 0,'RSI_NO_DIV'

def indicator_confluence(b):
    P=pk[b]; ctx=context_of(b); score=0; tags=[]
    for f in (ind_bubbles_ctx,ind_nas_ctx,ind_smc_ctx,ind_rsi_ctx):
        s,t=f(P,ctx); score+=s; tags.append(t)
    if score>=2: conf='STRONG_BULL_CONFIRM'
    elif score==1: conf='WEAK_BULL'
    elif score<=-2: conf='STRONG_BEAR_CONFIRM'
    elif score==-1: conf='WEAK_BEAR'
    else: conf='NEUTRAL'
    return ctx,score,conf,tags

def cross(b):
    e=eng[b]; epol=e['policy']; ctx,score,iconf,tags=indicator_confluence(b)
    if epol=='TAKE':
        if iconf in('STRONG_BULL_CONFIRM','WEAK_BULL'): pol='TAKE_CONFIRMED'
        elif iconf=='STRONG_BEAR_CONFIRM': pol='DOWNGRADE_REVIEW'
        elif iconf=='WEAK_BEAR': pol='TAKE_WEAK'
        else: pol='TAKE_NEUTRAL'
    elif epol=='SKIP':
        if iconf=='STRONG_BULL_CONFIRM': pol='UPGRADE_TAKE'    # indicadores resgatam fundo bull mal-lido pelo engine
        elif iconf in('STRONG_BEAR_CONFIRM','WEAK_BEAR'): pol='SKIP_CONFIRMED'
        else: pol='SKIP_NEUTRAL'
    elif epol=='REVIEW_RISK':
        pol='REVIEW_RISK_BULL' if score>=2 else 'REVIEW_RISK'
    else:
        pol='UPGRADE_TAKE' if score>=2 else f'REVIEW_{iconf}'
    return pol,ctx,score,iconf,tags,epol

def metrics(bidxs):
    rows=sorted(bidxs,key=lambda b:pk[b]['datetime']); n=len(rows)
    if n==0: return dict(n=0,WR=0,PF=0,sumR=0,maxDD=0,Lstreak=0,runners=0,big=0)
    wins=sum(1 for b in rows if outc[b]['exitype'] in WIN); runners=sum(1 for b in rows if outc[b]['exitype']=='WIN_RUNNER')
    rs=[fn(outc[b]['realR']) or 0 for b in rows]; pos=sum(r for r in rs if r>0); neg=sum(r for r in rs if r<0)
    PF=round(pos/abs(neg),2) if neg<0 else 999
    cum=0;peak=0;mdd=0
    for r in rs: cum+=r;peak=max(peak,cum);mdd=max(mdd,peak-cum)
    ls=0;best=0
    for b in rows:
        if outc[b]['exitype'] in WIN: ls=0
        else: ls+=1;best=max(best,ls)
    return dict(n=n,WR=round(100*wins/n,1),PF=PF,sumR=round(sum(rs),1),maxDD=round(mdd,1),Lstreak=best,runners=runners,big=wins)

rows=[]
for b in ALL:
    pol,ctx,score,iconf,tags,epol=cross(b)
    rows.append(dict(bar_idx=b,datetime=pk[b]['datetime'][:10],context=ctx,engine_policy=epol,indicator_score=score,
        indicator_confluence=iconf,bubbles=tags[0],nas=tags[1],smc=tags[2],rsi=tags[3],crossed_policy=pol,
        EVAL_exitype=outc[b]['exitype'],EVAL_realR=outc[b]['realR']))
with open(f"{D}/l2_bpt_full276_indicator_engine_cross_v2.csv","w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0].keys()),lineterminator="\n");w.writeheader();w.writerows(rows)

from collections import Counter
print("="*70);print("INDICADORES v2 CONTEXT-AWARE × RE-ENGINE (full 276) — polaridade corrigida")
print("context dist:",dict(Counter(r['context'] for r in rows)))
print("crossed_policy dist:",dict(Counter(r['crossed_policy'] for r in rows)))
def bk(name): return [r['bar_idx'] for r in rows if r['crossed_policy']==name]
ENG_TAKE=[b for b in ALL if eng[b]['policy']=='TAKE']

print(f"\n--- COMPARAÇÃO (realR CAPADO=hit-rate; LIMITAÇÃO: expectancy real precisa uncapped) | runners={TOTR} big={TOTB} ---")
print(f"{'bucket':28} {'n':>4} {'WR':>6} {'PF':>6} {'sumR':>7} {'DD':>6} {'Lstk':>5} {'run':>4} {'big':>4}")
comp=[]
TC=bk('TAKE_CONFIRMED'); TCW=TC+bk('TAKE_WEAK'); UPG=bk('UPGRADE_TAKE'); ALLTAKE=TC+bk('TAKE_WEAK')+UPG
for name,bs in [('ENGINE_TAKE (base)',ENG_TAKE),('TAKE_CONFIRMED',TC),('TAKE_CONFIRMED+WEAK',TCW),
                ('+UPGRADE_TAKE (resgates)',ALLTAKE),('UPGRADE_TAKE only',UPG),
                ('DOWNGRADE_REVIEW',bk('DOWNGRADE_REVIEW')),('SKIP_CONFIRMED',bk('SKIP_CONFIRMED')),('BASELINE',ALL)]:
    m=metrics(bs);m['bucket']=name;comp.append(m)
    print(f"{name:28} {m['n']:>4} {m['WR']:>6} {m['PF']:>6} {m['sumR']:>7} {m['maxDD']:>6} {m['Lstreak']:>5} {m['runners']:>4} {m['big']:>4}")
with open(f"{D}/l2_bpt_full276_indicator_engine_eval_v2.csv","w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=['bucket','n','WR','PF','sumR','maxDD','Lstreak','runners','big'],extrasaction='ignore',lineterminator="\n");w.writeheader();w.writerows(comp)

# NULL nos buckets-chave (Bonferroni-aware: alpha/m)
def null_test(bucket,label,N=2000):
    rng=random.Random(11); obs=metrics(bucket); k=obs['n']
    if k==0: return dict(bucket=label,n=0,WR=0,PF=0,p_WR=1,p_PF=1)
    ex=[outc[b]['exitype'] for b in ALL]; rr=[fn(outc[b]['realR']) or 0 for b in ALL]; gw=gp=0
    for _ in range(N):
        idx=list(range(len(ALL)));rng.shuffle(idx);s=idx[:k]
        wins=sum(1 for i in s if ex[i] in WIN);rs=[rr[i] for i in s];pos=sum(r for r in rs if r>0);neg=sum(r for r in rs if r<0)
        if 100*wins/k>=obs['WR']:gw+=1
        if (pos/abs(neg) if neg<0 else 999)>=obs['PF']:gp+=1
    return dict(bucket=label,n=k,WR=obs['WR'],PF=obs['PF'],p_WR=round(gw/N,3),p_PF=round(gp/N,3))
print("\n--- NULL/PERMUTATION (N=2000; Bonferroni m=5 => alpha 0.010) ---")
nl=[]
for nm,bs in [('TAKE_CONFIRMED',TC),('TAKE_CONFIRMED+WEAK',TCW),('+UPGRADE_TAKE',ALLTAKE),('UPGRADE_TAKE_only',UPG),('SKIP_CONFIRMED',bk('SKIP_CONFIRMED'))]:
    r=null_test(bs,nm);nl.append(r)
    star='***SURVIVES Bonferroni' if r['p_WR']<=0.010 else ('*nominal' if r['p_WR']<0.05 else '')
    print(f"  {nm:22} n={r['n']:>3} WR={r['WR']:>5} PF={r['PF']:>5} p(WR>=)={r['p_WR']:.3f} p(PF>=)={r['p_PF']:.3f} {star}")
with open(f"{D}/l2_bpt_full276_indicator_engine_null_v2.csv","w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=['bucket','n','WR','PF','p_WR','p_PF'],lineterminator="\n");w.writeheader();w.writerows(nl)

def window(b): return 'P1_2020-22' if pk[b]['datetime'][:10]<'2023-01-01' else 'P2_2023-26'
print("\n--- ALL-TAKE (confirmed+weak+upgrade) sub-janelas ---")
for w_ in ['P1_2020-22','P2_2023-26']:
    m=metrics([b for b in ALLTAKE if window(b)==w_]);print(f"  {w_}: n={m['n']} WR={m['WR']} PF={m['PF']} sumR={m['sumR']} runners={m['runners']} Lstk={m['Lstreak']}")
print("\nDONE v2 context-aware.")
