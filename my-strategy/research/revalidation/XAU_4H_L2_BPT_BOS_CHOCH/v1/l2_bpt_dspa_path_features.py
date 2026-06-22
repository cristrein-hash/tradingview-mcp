#!/usr/bin/env python3
"""DSPA CAMADA 1 — FEATURE FOUNDATION / PATH DERIVATION (7 famílias de trajetória 4H/1D). Base 276.
Todas CAUSAIS (só barras <= entrada; pivots confirmados com lag; 1D/regime_B shift D-1; SVP as-of-bar validado 7f3c852;
NENHUM outcome como input). NÃO testa TAKE/SKIP (só cobertura descritiva). Script salvo/reprodutível. DIAGNÓSTICO.
Famílias: (1) liquidity sweep (2) flush geometry (3) multi-bar acceptance (4) swing HH/HL/LH/LL+BOS/CHoCH
(5) dealing-range premium/discount 4H+1D (6) SVP POC/VAH/VAL path (7) regime_B_v3 trajectory."""
import json, csv, bisect, datetime as dt
D="results"; RR="repro_recovery"
F=[json.loads(l) for l in open(f"{RR}/raw_features_2020_2026.jsonl")]
N=len(F); O=[r['open'] for r in F]; H=[r['high'] for r in F]; L=[r['low'] for r in F]; C=[r['close'] for r in F]; TS=[r['ts_epoch'] for r in F]
ATR=[None]*N; trs=[]
for i in range(1,N):
    trs.append(max(H[i]-L[i],abs(H[i]-C[i-1]),abs(L[i]-C[i-1])))
    if i>=14: ATR[i]=sum(trs[i-14:i])/14
def d10(t): return dt.datetime.utcfromtimestamp(t).strftime('%Y-%m-%d')
# 1D
DD=[json.loads(l) for l in open(f"{RR}/XAU_1D_ohlc.jsonl")]; DD.sort(key=lambda r:r['time'])
Dtime=[r['time'] for r in DD]
# SVP (vp=[POC,VAH,VAL]) as-of-bar
SV=[json.loads(l) for l in open(f"{RR}/svp_bars.jsonl") if json.loads(l).get('vp')]; SV.sort(key=lambda r:r['time'])
Stime=[r['time'] for r in SV]
# regime_B daily (shift D-1)
RB=[json.loads(l) for l in open("../../../../strategies/candidates/regime_classifier_v3/regime_B_v3_classifications.jsonl") if json.loads(l).get('ts')]
RB.sort(key=lambda r:r['ts']); RBdate=[r['ts'][:10] for r in RB]
outc={int(r['bar_idx']):r for r in csv.DictReader(open(f"{D}/l2_bpt_trade_qualification_outcomes.csv"))}
EP=sorted(outc)
LB=18  # lookback 4H bars
def fnz(v):
    try:return float(v)
    except:return 0.0

# ---- pivots causais (Williams k=3, confirmado em j+3) ----
def pivots_upto(i,k=3):
    lows=[];highs=[]
    for j in range(k, i-k+1):           # j+k <= i  => confirmado por i
        if all(L[j]<L[j-m] for m in range(1,k+1)) and all(L[j]<=L[j+m] for m in range(1,k+1)): lows.append(j)
        if all(H[j]>H[j-m] for m in range(1,k+1)) and all(H[j]>=H[j+m] for m in range(1,k+1)): highs.append(j)
    return lows,highs

# ---- F1 liquidity sweep / sweep-then-reclaim ----
def f1_sweep(i):
    lows,highs=pivots_upto(i)
    sl=[j for j in lows if j<i-2]; sh=[j for j in highs if j<i-2]
    swept_low=False; depth=0.0; bars_since=-1
    if sl:
        ref=L[sl[-1]]  # swing-low de referência (suporte anterior)
        for j in range(max(sl[-1]+1,i-LB), i+1):
            if L[j]<ref:  # varreu a liquidez abaixo
                for j2 in range(j, i+1):
                    if C[j2]>ref:  # reclaim
                        swept_low=True; depth=(ref-min(L[j:j2+1]))/(ATR[i] or 1); bars_since=i-j2; break
            if swept_low: break
    swept_high=False
    if sh:
        refh=H[sh[-1]]
        for j in range(max(sh[-1]+1,i-LB), i+1):
            if H[j]>refh:
                for j2 in range(j,i+1):
                    if C[j2]<refh: swept_high=True; break
            if swept_high: break
    return dict(f1_swept_low_reclaim=int(swept_low),f1_sweep_depth_atr=round(depth,2),f1_bars_since_sweep=bars_since,
                f1_swept_high_reject=int(swept_high))

# ---- F2 flush geometry (V vs grind) ----
def f2_flush(i):
    lows,highs=pivots_upto(i); recent_high=highs[-1] if highs else max(range(max(0,i-LB),i+1),key=lambda j:H[j])
    lo_idx=min(range(recent_high,i+1),key=lambda j:L[j]) if recent_high<=i else i
    span=lo_idx-recent_high
    drop=(H[recent_high]-L[lo_idx])/(ATR[i] or 1)
    vel=drop/span if span>0 else 0.0
    cdn=0
    for j in range(i,0,-1):
        if C[j]<C[j-1]: cdn+=1
        else: break
    flush_atr=sum(trs[j-1] for j in range(recent_high+1,lo_idx+1) if j-1<len(trs))/max(1,span)
    base_atr=ATR[recent_high] or ATR[i] or 1
    rexp=flush_atr/base_atr if base_atr else 1
    if drop<1.0: st='NO_FLUSH'
    elif vel>=0.8 and rexp>=1.2 and span<=8: st='FLUSH_V'
    elif span>8 and vel<0.6: st='GRIND_DOWN'
    else: st='MIXED_DECLINE'
    return dict(f2_flush_state=st,f2_drop_atr=round(drop,2),f2_velocity_atr_bar=round(vel,2),f2_range_expansion=round(rexp,2),f2_consec_down=cdn,f2_flush_bars=span)

# ---- F3 multi-bar acceptance/rejection (vs swing-high resistência / swing-low suporte) ----
def f3_accept(i):
    lows,highs=pivots_upto(i)
    res=H[highs[-1]] if highs else max(H[max(0,i-LB):i])
    sup=L[lows[-1]] if lows else min(L[max(0,i-LB):i])
    win=range(max(1,i-LB),i+1)
    closes_above_res=sum(1 for j in win if C[j]>res); rej_at_res=sum(1 for j in win if H[j]>res and C[j]<res)
    holds_sup=sum(1 for j in win if C[j]>sup); breaks_sup=sum(1 for j in win if C[j]<sup)
    if closes_above_res>=2: st='ACCEPTED_ABOVE_RES'
    elif rej_at_res>=2: st='REJECTED_AT_RES'
    elif breaks_sup>=2: st='BROKE_SUPPORT'
    elif holds_sup>=LB-2: st='HOLDING_SUPPORT'
    else: st='NEUTRAL'
    return dict(f3_acceptance_state=st,f3_closes_above_res=closes_above_res,f3_rejections_at_res=rej_at_res,f3_breaks_support=breaks_sup)

# ---- F4 swing structure HH/HL/LH/LL + BOS/CHoCH ----
def f4_structure(i):
    lows,highs=pivots_upto(i)
    hh=hl=lh=ll=None
    if len(highs)>=2: hh=H[highs[-1]]>H[highs[-2]]; lh=not hh
    if len(lows)>=2: hl=L[lows[-1]]>L[lows[-2]]; ll=not hl
    if hh and hl: st='STRUCTURE_UP'
    elif lh and ll: st='STRUCTURE_DOWN'
    elif (hh or hl) and (lh or ll): st='STRUCTURE_RANGE'
    else: st='STRUCTURE_UNCLEAR'
    bos=int(bool(highs) and C[i]>H[highs[-1]] and st in('STRUCTURE_UP','STRUCTURE_RANGE'))
    choch=int(bool(lows) and C[i]<L[lows[-1]] and st=='STRUCTURE_UP')
    # FIX DA: contar pivots SÓ na janela LB (bounded), não cumulativo desde barra 0 (corrigia r=1.0 com bar_idx)
    npiv_lb=sum(1 for j in lows+highs if j>=i-LB)
    return dict(f4_structure_state=st,f4_BOS=bos,f4_CHoCH=choch,f4_n_pivots_lb=npiv_lb)

# ---- F5 dealing range premium/discount 4H + 1D ----
def pos_state(c,lo,hi):
    if hi<=lo: return 'EQUILIBRIUM',0.5
    p=(c-lo)/(hi-lo)
    return ('PREMIUM' if p>0.66 else 'DISCOUNT' if p<0.33 else 'EQUILIBRIUM'),round(p,2)
def f5_range(i,ed):
    lo=min(L[max(0,i-LB):i+1]); hi=max(H[max(0,i-LB):i+1]); s4,p4=pos_state(C[i],lo,hi)
    di=bisect.bisect_left(Dtime, dt.datetime.strptime(ed,'%Y-%m-%d').replace(tzinfo=dt.timezone.utc).timestamp())-1  # D-1
    if di>=20:
        dlo=min(d['low'] for d in DD[di-20:di+1]); dhi=max(d['high'] for d in DD[di-20:di+1]); s1,p1=pos_state(C[i],dlo,dhi)
    else: s1,p1='UNAVAILABLE',-1
    return dict(f5_range_pos_4h=s4,f5_range_pct_4h=p4,f5_range_pos_1d=s1,f5_range_pct_1d=p1)

# ---- F6 SVP POC/VAH/VAL path (acceptance relativo ao valor sobre lookback) ----
def svp_asof(t):
    k=bisect.bisect_right(Stime,t)-1
    if k<0: return None
    vp=SV[k]['vp']; return dict(POC=vp[0],VAH=vp[1],VAL=vp[2])
def f6_svp(i):
    cur=svp_asof(TS[i])
    if not cur: return dict(f6_svp_state='UNAVAILABLE',f6_above_value=-1,f6_below_value=-1,f6_dist_poc_atr=-1)
    above=below=0
    for j in range(max(0,i-LB),i+1):
        v=svp_asof(TS[j])
        if not v: continue
        if C[j]>v['VAH']: above+=1
        elif C[j]<v['VAL']: below+=1
    if C[i]>cur['VAH'] and above>=2: st='ACCEPTING_ABOVE_VALUE'
    elif C[i]<cur['VAL'] and below>=2: st='BELOW_VALUE_REJECTED'
    else: st='IN_VALUE'
    return dict(f6_svp_state=st,f6_above_value=above,f6_below_value=below,f6_dist_poc_atr=round((C[i]-cur['POC'])/(ATR[i] or 1),2))

# ---- F7 regime_B_v3 trajectory (shift D-1, sequência não snapshot) ----
def f7_regime(ed):
    k=bisect.bisect_left(RBdate, ed)-1   # último daily com date < ed (D-1)
    if k<6: return dict(f7_regime_traj='UNAVAILABLE',f7_combined_slope=0,f7_cascade_now=0,f7_distribution_onset=-1,f7_macro_broken_recent=-1)
    cs=[fnz(RB[k-m].get('combined_score')) for m in range(6,-1,-1)]
    slope=(cs[-1]-cs[0])/6
    casc=fnz(RB[k].get('cascade_score'))
    # NOTA(DA): distribution_flag é CONSTANTE (False) em todo o regime_B (2582/2582) = campo morto na fonte ->
    # f7_distribution_onset DROPADO como UNAVAILABLE (não fabricar proxy). macro_broken VARIA (1397F/1185T) -> mantido.
    mb=[1 if RB[k-m].get('macro_broken') in(True,'True',1) else 0 for m in range(6,-1,-1)]
    mb_recent=int(mb[-1]==1 and mb[0]==0)
    if slope<-0.3: tr='REGIME_DETERIORATING'
    elif slope>0.3: tr='REGIME_IMPROVING'
    elif casc<=-2: tr='REGIME_STABLE_BEAR'
    elif cs[-1]>0: tr='REGIME_STABLE_BULL'
    else: tr='REGIME_NEUTRAL'
    return dict(f7_regime_traj=tr,f7_combined_slope=round(slope,3),f7_cascade_now=round(casc,1),f7_macro_broken_recent=mb_recent)

# ---- RODAR ----
rows=[]; unavail={}
for b in EP:
    ed=d10(TS[b]); r=dict(bar_idx=b,datetime=ed)
    for fam in (f1_sweep(b),f2_flush(b),f3_accept(b),f4_structure(b),f6_svp(b)): r.update(fam)
    r.update(f5_range(b,ed)); r.update(f7_regime(ed))
    for k,v in r.items():
        if v=='UNAVAILABLE': unavail[k]=unavail.get(k,0)+1
    rows.append(r)
cols=list(rows[0].keys())
with open(f"{D}/l2_bpt_dspa_path_features_276.csv","w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=cols,lineterminator="\n");w.writeheader();w.writerows(rows)

# ---- PROVENANCE TABLE ----
PROV=[
 ('F1_liquidity_sweep','raw_features_2020_2026.jsonl (4H path)','lookback %d bars'%LB,'causal: pivots Williams k=3 confirmados em j+3, só barras<=i','none'),
 ('F2_flush_geometry','4H path','recent_high->entry','causal: só barras<=i','none'),
 ('F3_multi_bar_acceptance','4H path','lookback %d'%LB,'causal: closes/wicks vs swing-high/low confirmados','none'),
 ('F4_swing_structure','4H path','pivots','causal: pivots confirmados','none'),
 ('F5_dealing_range','4H path + XAU_1D_ohlc.jsonl','4H lookback %d / 1D 20 bars'%LB,'causal: 1D shift D-1 (date<entry). NOTA(DA): range path-derivada mas POSICAO (pct/premium-discount) e componente LOCATION/snapshot na barra i','1D needs >=20 daily bars'),
 ('F6_svp_path','svp_bars.jsonl (vp=[POC,VAH,VAL])','lookback %d'%LB,'causal: SVP as-of-bar (validado 7f3c852, sem shift)','none se SVP cobre o ts'),
 ('F7_regime_trajectory','regime_B_v3_classifications.jsonl (daily)','7 daily bars','causal: shift D-1 (date<entry), sequência combined-slope/cascade/macro_broken-transition','needs >=7 daily; distribution_flag UNAVAILABLE (constante False 2582/2582 na fonte) -> dropado'),
]
with open(f"{D}/l2_bpt_dspa_path_features_provenance.csv","w",newline="") as f:
    w=csv.writer(f,lineterminator="\n");w.writerow(['family','source','window','causality','unavailable_reason']);[w.writerow(r) for r in PROV]

from collections import Counter
print("="*78);print(f"DSPA CAMADA 1 — FEATURE FOUNDATION | cobertura: {len(rows)}/276 episódios")
print(f"colunas de feature: {len(cols)-2} (+ bar_idx,datetime)")
print(f"\nUNAVAILABLE (família sem dado p/ alguns episódios): {unavail if unavail else 'NENHUMA'}")
print("\n--- cobertura descritiva por estado (NÃO é teste de edge) ---")
for k in ('f1_swept_low_reclaim','f2_flush_state','f3_acceptance_state','f4_structure_state','f5_range_pos_4h','f5_range_pos_1d','f6_svp_state','f7_regime_traj'):
    print(f"  {k:22}",dict(Counter(str(r[k]) for r in rows)))
# sanity causal: nenhuma feature usa outcome; spot-check pivot lag
print("\n--- SANITY CAUSAL ---")
print("  outcome usado como input? NÃO (script não lê realR/mfe/exitype).")
print(f"  pivots confirmados com lag k=3 (j+3<=i): OK por construção.")
print(f"  1D/regime_B shift D-1 (date<entry): OK. SVP as-of-bar (<=ts): OK.")
print(f"  episódios com F5_1d UNAVAILABLE: {sum(1 for r in rows if r['f5_range_pos_1d']=='UNAVAILABLE')} | F7 UNAVAILABLE: {sum(1 for r in rows if r['f7_regime_traj']=='UNAVAILABLE')} | F6 UNAVAILABLE: {sum(1 for r in rows if r['f6_svp_state']=='UNAVAILABLE')}")
print("\nDONE. outputs: l2_bpt_dspa_path_features_276.csv, l2_bpt_dspa_path_features_provenance.csv")
print("NÃO testado TAKE/SKIP (só cobertura descritiva). Fundação pronta p/ próximo bloco DSPA Aggregation.")
