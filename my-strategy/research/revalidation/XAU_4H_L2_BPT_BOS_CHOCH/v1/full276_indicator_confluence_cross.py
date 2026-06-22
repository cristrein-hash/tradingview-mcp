#!/usr/bin/env python3
"""FULL 276 — CONFLUÊNCIA DE INDICADORES EM TODA POTÊNCIA × RE-ENGINE (canon efaf48a).
Cruza os INDICADORES brutos (bubbles L/m/s buy/sell, NAS long/short, SMC BOS/CHoCH, RSI div) — que NÃO entraram
nos 9 especialistas estruturais — POR CIMA da leitura do engine (full276_macro_engine.py).
DIAGNÓSTICO. realR CAPADO. Thresholds DECLARADOS, interpretáveis (Auction Theory + memórias de polaridade),
não tunados a outcome. Polaridade bubbles: bub_SELL grande = distribuição/topo (bear); bub_BUY grande em
pullback bull = acumulação (bull). NAS = LONG/SHORT (nunca TOP/BOTTOM). SMC: BOS=continuação, CHoCH=reversão.
Validação: null/permutation no bucket refinado. Sem produção/OOS/promoção."""
import json, csv, bisect, random
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

# ---------- INDICADORES EM TODA POTÊNCIA (sub-leitores brutos) ----------
def ind_bubbles(P):
    """bub_SELL grande = distribuição/topo (bear); bub_BUY grande = acumulação (bull). plot_*: já agregado."""
    bL=fi(P.get('bub_buy_L')); sL=fi(P.get('bub_sell_L')); blg=fi(P.get('bub_large_buy_10b')); slg=fi(P.get('bub_large_sell_10b'))
    ratio=fn(P.get('bub_buy_sell_ratio'))
    bull = (bL>=1) or (blg>=2) or (ratio is not None and ratio>=1.5)
    bear = (sL>=1) or (slg>=2) or (ratio is not None and ratio<=0.5)
    if bull and not bear: return +1,'BUBBLE_BUY_DOMINANCE'
    if bear and not bull: return -1,'BUBBLE_SELL_DISTRIBUTION'
    return 0,'BUBBLE_MIXED'
def ind_nas(P):
    """NAS LONG recente = bull; NAS SHORT cluster = topo/bear (memória: cluster SHORT no topo antes do drop)."""
    nl=fi(P.get('nas_long_new_8b')); ns=fi(P.get('nas_short_new_8b')); n1d=fi(P.get('nas_1d_long_recent'))
    if ns>=1 and nl==0: return -1,'NAS_SHORT_CLUSTER'
    if nl>=1 and ns==0: return +1,'NAS_LONG_RECENT'
    if n1d>=1: return +1,'NAS_1D_LONG'
    return 0,'NAS_NEUTRAL'
def ind_smc(P):
    """BOS = continuação na direção; CHoCH = mudança de caráter = reversão/aviso."""
    bos=str(P.get('smc_bos')); choch=str(P.get('smc_choch'))
    bos_on = bos not in('0','None','','False','0.0')
    choch_on = choch not in('0','None','','False','0.0')
    if choch_on: return -1,'SMC_CHOCH_REVERSAL'
    if bos_on: return +1,'SMC_BOS_CONTINUATION'
    return 0,'SMC_NONE'
def ind_rsi(P):
    """rsi_bull_div = reversão bull; rsi_bear_div = topo/reversão bear."""
    bd=fn(P.get('rsi_bear_div_20b')); bld=fn(P.get('rsi_bull_div_20b'))
    if bd is not None and bd>0: return -1,'RSI_BEAR_DIV'
    if bld is not None and bld>0: return +1,'RSI_BULL_DIV'
    return 0,'RSI_NO_DIV'

INDS=[ind_bubbles,ind_nas,ind_smc,ind_rsi]
def indicator_confluence(b):
    P=pk[b]; score=0; tags=[]
    for f in INDS:
        s,t=f(P); score+=s; tags.append(t)
    # confluência interpretável
    if score>=2: conf='STRONG_BULL_CONFIRM'
    elif score==1: conf='WEAK_BULL'
    elif score<=-2: conf='STRONG_BEAR_CONFIRM'
    elif score==-1: conf='WEAK_BEAR'
    else: conf='NEUTRAL'
    return score,conf,tags

# ---------- CRUZAMENTO INDICADOR × ENGINE ----------
def cross(b):
    e=eng[b]; fam=e['family']; epol=e['policy']
    score,iconf,tags=indicator_confluence(b)
    # regra de cruzamento (declarada): indicadores CONFIRMAM ou CONTRADIZEM a leitura estrutural
    if epol=='TAKE':
        if iconf in('STRONG_BULL_CONFIRM','WEAK_BULL'): pol='TAKE_CONFIRMED'
        elif iconf in('STRONG_BEAR_CONFIRM',): pol='DOWNGRADE_REVIEW'   # indicadores vetam o TAKE estrutural
        elif iconf=='WEAK_BEAR': pol='TAKE_WEAK'
        else: pol='TAKE_NEUTRAL'
    elif epol=='SKIP':
        if iconf in('STRONG_BEAR_CONFIRM','WEAK_BEAR'): pol='SKIP_CONFIRMED'
        elif iconf=='STRONG_BULL_CONFIRM': pol='UPGRADE_REVIEW'         # indicadores resgatam do SKIP
        else: pol='SKIP_NEUTRAL'
    elif epol=='REVIEW_RISK':
        pol='REVIEW_RISK_BULL' if score>=2 else 'REVIEW_RISK'
    else:
        pol=f'REVIEW_{iconf}'
    return pol,score,iconf,tags,fam,epol

# ---------- EVAL ----------
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
    pol,score,iconf,tags,fam,epol=cross(b)
    rows.append(dict(bar_idx=b,datetime=pk[b]['datetime'][:10],engine_policy=epol,engine_family=fam,
        indicator_score=score,indicator_confluence=iconf,bubbles=tags[0],nas=tags[1],smc=tags[2],rsi=tags[3],
        crossed_policy=pol,EVAL_exitype=outc[b]['exitype'],EVAL_realR=outc[b]['realR']))
with open(f"{D}/l2_bpt_full276_indicator_engine_cross.csv","w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0].keys()),lineterminator="\n");w.writeheader();w.writerows(rows)

from collections import Counter
print("="*70);print("INDICADORES EM TODA POTÊNCIA × RE-ENGINE (full 276)")
print("crossed_policy dist:",dict(Counter(r['crossed_policy'] for r in rows)))
print("indicator_confluence dist:",dict(Counter(r['indicator_confluence'] for r in rows)))

# buckets de interesse
def bk(name): return [r['bar_idx'] for r in rows if r['crossed_policy']==name]
ENG_TAKE=[b for b in ALL if eng[b]['policy']=='TAKE']
print(f"\n--- COMPARAÇÃO (realR CAPADO) | total runners={TOTR} big={TOTB} ---")
print(f"{'bucket':28} {'n':>4} {'WR':>6} {'PF':>6} {'sumR':>7} {'DD':>6} {'Lstk':>5} {'run':>4} {'big':>4}")
comp=[]
for name,bs in [('ENGINE_TAKE (base)',ENG_TAKE),
                ('TAKE_CONFIRMED',bk('TAKE_CONFIRMED')),
                ('TAKE_CONFIRMED+WEAK',bk('TAKE_CONFIRMED')+bk('TAKE_WEAK')),
                ('DOWNGRADE_REVIEW (vetado)',bk('DOWNGRADE_REVIEW')),
                ('SKIP_CONFIRMED',bk('SKIP_CONFIRMED')),
                ('UPGRADE_REVIEW (resgate)',bk('UPGRADE_REVIEW')),
                ('BASELINE_no_gate',ALL)]:
    m=metrics(bs);m['bucket']=name;m['rp']=f"{m['runners']}/{TOTR}";m['bp']=f"{m['big']}/{TOTB}";comp.append(m)
    print(f"{name:28} {m['n']:>4} {m['WR']:>6} {m['PF']:>6} {m['sumR']:>7} {m['maxDD']:>6} {m['Lstreak']:>5} {m['runners']:>4} {m['big']:>4}")
with open(f"{D}/l2_bpt_full276_indicator_engine_eval.csv","w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=['bucket','n','WR','PF','sumR','maxDD','Lstreak','runners','rp','big','bp'],extrasaction='ignore',lineterminator="\n");w.writeheader();w.writerows(comp)

# ---------- NULL no TAKE_CONFIRMED ----------
def null_test(bucket,label,N=2000):
    rng=random.Random(7); obs=metrics(bucket); k=obs['n']
    if k==0: print(f"  {label}: n=0"); return
    ex=[outc[b]['exitype'] for b in ALL]; rr=[fn(outc[b]['realR']) or 0 for b in ALL]
    gw=gp=0
    for _ in range(N):
        idx=list(range(len(ALL)));rng.shuffle(idx);s=idx[:k]
        wins=sum(1 for i in s if ex[i] in WIN);rs=[rr[i] for i in s];pos=sum(r for r in rs if r>0);neg=sum(r for r in rs if r<0)
        wr=100*wins/k;pf=pos/abs(neg) if neg<0 else 999
        if wr>=obs['WR']:gw+=1
        if pf>=obs['PF']:gp+=1
    print(f"  {label}: n={k} WR={obs['WR']}% PF={obs['PF']} | p(WR>=)={gw/N:.3f} p(PF>=)={gp/N:.3f}")
    return dict(bucket=label,n=k,WR=obs['WR'],PF=obs['PF'],p_WR=round(gw/N,3),p_PF=round(gp/N,3))
print("\n--- NULL/PERMUTATION (N=2000) ---")
nl=[]
for nm,bs in [('TAKE_CONFIRMED',bk('TAKE_CONFIRMED')),('TAKE_CONFIRMED+WEAK',bk('TAKE_CONFIRMED')+bk('TAKE_WEAK')),('SKIP_CONFIRMED',bk('SKIP_CONFIRMED'))]:
    r=null_test(bs,nm)
    if r:nl.append(r)
with open(f"{D}/l2_bpt_full276_indicator_engine_null.csv","w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=['bucket','n','WR','PF','p_WR','p_PF'],lineterminator="\n");w.writeheader();w.writerows(nl)

# ---------- sub-janelas TAKE_CONFIRMED ----------
def window(b): return 'P1_2020-22' if pk[b]['datetime'][:10]<'2023-01-01' else 'P2_2023-26'
print("\n--- TAKE_CONFIRMED sub-janelas ---")
tc=bk('TAKE_CONFIRMED')
for w_ in ['P1_2020-22','P2_2023-26']:
    m=metrics([b for b in tc if window(b)==w_]);print(f"  {w_}: n={m['n']} WR={m['WR']} PF={m['PF']} sumR={m['sumR']} runners={m['runners']} Lstk={m['Lstreak']}")
print("\nDONE indicator×engine cross.")
