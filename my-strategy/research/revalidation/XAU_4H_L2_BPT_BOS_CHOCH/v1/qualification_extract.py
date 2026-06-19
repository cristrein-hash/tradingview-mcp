#!/usr/bin/env python3
"""L2/BPT TRADE QUALIFICATION ENGINE — extrator de PACKET MULTIFATORIAL causal por episódio.
Mapeia o MÁXIMO de fatores disponíveis em TODOS os contextos, contemplando TODOS os fatores que
geraram positivo nas estratégias anteriores (Caminho B 7-sinais + Dead Hours + Sweet Spot + climax F9 +
BED/BDF; Capitulation NAS+RSI_1D+ATR; V1.4g A7 anti-div + BASE+SWEEP; Caminho A EMA21/anti-ext/bubble_buy;
Regime Classifier B v3; Volume Session VP real + LOW<VAL + climax wash; L2/BPT legpos+demand-SL+F_STRICT+
reclaim+supply-overhead) + SMC LuxAlgo (BOS/CHoCH/OB) + NAS numérico (dist_ema, nas_rsi).
CAUSAL: tudo <= barra de entrada. SEM SLIM. SEM look-ahead. Outcomes ficam em ARQUIVO SEPARADO
(reasoning é CEGO ao resultado). Reusa demand-SL repaint-auditado + partial50.
Cross-asset NÃO usado (regra do Cris)."""
import json,csv,gzip,math
import os
from datetime import datetime,timezone
from collections import Counter,defaultdict
D=os.environ.get("L2_OUT_DIR","results")

# ============ FROZEN 4H ============
fr=[json.loads(l) for l in open(os.environ.get("L2_RAW_FEATURES","/tmp/raw_features_2020_2026.jsonl"))]
H=[r['high'] for r in fr];L=[r['low'] for r in fr];C=[r['close'] for r in fr];O=[r['open'] for r in fr]
TS=[r['ts_epoch'] for r in fr];RS=[r.get('rsi') for r in fr];BUB=[r.get('bubbles_recent') or [] for r in fr]
N=len(fr);TSidx={t:i for i,t in enumerate(TS)}
ATR=[None]*N;trs=[]
for i in range(1,N):
    trs.append(max(H[i]-L[i],abs(H[i]-C[i-1]),abs(L[i]-C[i-1])))
    if i>=14: ATR[i]=sum(trs[i-14:i])/14
def sma(arr,i,n):
    s=arr[max(0,i-n+1):i+1]; return sum(s)/len(s) if s else None
PL5=[False]*N;PH5=[False]*N
for j in range(5,N-5):
    if L[j]<min(L[j-5:j]) and L[j]<min(L[j+1:j+6]): PL5[j]=True
    if H[j]>max(H[j-5:j]) and H[j]>max(H[j+1:j+6]): PH5[j]=True
def swing_origin(i):
    p=C[i];a=ATR[i];lo=None
    for j in range(i-5,4,-1):
        if PL5[j] and L[j]<p: lo=L[j];break
    if lo is None: lo=min(L[max(0,i-6):i+1])
    return max(p-(lo-0.1*a),0.3*a)
def legpos(i,w):
    p=C[i];hi=max(H[max(0,i-w):i+1]);lo=min(L[max(0,i-w):i+1]);return round(100*(p-lo)/(hi-lo),1) if hi>lo else 50.0

# ---- daily aggregation (causal: usa só barras <= i, dia FECHADO) ----
def daily_closes_upto(i):
    # agrega 4H -> diário usando UTC date; retorna lista de (date, close_do_ultimo_bar_do_dia) p/ dias FECHADOS (< dia atual)
    cur_day=datetime.fromtimestamp(TS[i],tz=timezone.utc).date()
    days={}
    for j in range(max(0,i-400),i+1):
        dd=datetime.fromtimestamp(TS[j],tz=timezone.utc).date()
        if dd>=cur_day: break
        days[dd]=(H[j],L[j],C[j])
    ks=sorted(days);return [days[k] for k in ks]
def rsi_wilder(closes,n=14):
    if len(closes)<n+1: return None
    g=l=0
    for k in range(1,n+1):
        ch=closes[k]-closes[k-1];g+=max(ch,0);l+=max(-ch,0)
    ag,al=g/n,l/n
    for k in range(n+1,len(closes)):
        ch=closes[k]-closes[k-1];ag=(ag*(n-1)+max(ch,0))/n;al=(al*(n-1)+max(-ch,0))/n
    if al==0: return 100.0
    return round(100-100/(1+ag/al),1)

# ---- RSI divergence (causal, em pivôs ja confirmados PH5/PL5 dentro de 20b, shift5) ----
def rsi_bear_div(i,win=20):
    phs=[j for j in range(max(5,i-win),i-4) if PH5[j] and RS[j] is not None]
    c=0
    for a,b in zip(phs,phs[1:]):
        if H[b]>H[a] and RS[b]<RS[a]: c+=1
    return c
def rsi_bull_div(i,win=20):
    pls=[j for j in range(max(5,i-win),i-4) if PL5[j] and RS[j] is not None]
    c=0
    for a,b in zip(pls,pls[1:]):
        if L[b]<L[a] and RS[b]>RS[a]: c+=1
    return c

# ============ gz: OB Detector (demand/supply) + NAS labels+numeric + SMC + RSI-MA ============
RAW="/Volumes/GUTS_ LACIE/TradingData/raw_replay/XAUUSD"
GZ=[os.environ["L2_GZ_4H"]] if os.environ.get("L2_GZ_4H") else [f"{RAW}/4H/XAUUSD_240m_replay_2020-01-01_to_2023-01-01.jsonl.gz",f"{RAW}/4H/XAUUSD_240m_replay_2023-01-03_to_2026-05-25.jsonl.gz"]
demlow_by_ts={};demhigh_by_ts={};suplow_by_ts={}
nas_new={};nas_short_new={};nas_num_by_ts={}
smc_bos_new={};smc_choch_new={}  # ts-> (text, color, price) quando label novo aparece
rsima_by_ts={}
def sv(d,name,key):
    for s in (d.get('study_values') or []):
        if name in (s.get('name') or ''):
            try: return float(str(s['values'].get(key,'')).replace(',',''))
            except: return None
    return None
for gz in GZ:
    prev_nl=prev_ns=None; seen_lbl=set()
    with gzip.open(gz,'rt') as f:
        for line in f:
            try: d=json.loads(line)
            except: continue
            ov=d.get('ohlcv') or []
            if not ov: continue
            t=ov[-1]['time']
            # OB Detector demand/supply
            ob=next((s for s in (d.get('pine_boxes') or []) if 'OB Detector' in (s.get('name') or '')),None)
            if ob:
                bx=ob.get('all_boxes') or []
                demlow_by_ts[t]=[b['low'] for b in bx if (b.get('text') or '').upper()=='DEMAND' and b.get('low') is not None]
                demhigh_by_ts[t]=[b['high'] for b in bx if (b.get('text') or '').upper()=='DEMAND' and b.get('high') is not None]
                suplow_by_ts[t]=[b['low'] for b in bx if (b.get('text') or '').upper()=='SUPPLY' and b.get('low') is not None]
            # NAS labels first-appearance (LONG/SHORT)
            nas=next((s for s in (d.get('pine_labels') or []) if 'NAS' in (s.get('name') or '').upper()),None)
            labs=(nas.get('all_labels') or nas.get('labels') or []) if nas else []
            nl=sum(1 for x in labs if (x.get('text') or '').upper()=='LONG')
            ns=sum(1 for x in labs if (x.get('text') or '').upper()=='SHORT')
            nas_new[t]=1 if (prev_nl is not None and nl>prev_nl) else 0
            nas_short_new[t]=1 if (prev_ns is not None and ns>prev_ns) else 0
            prev_nl,prev_ns=nl,ns
            # NAS numeric study_values
            nas_num_by_ts[t]={'dist_ema_atr':sv(d,'NAS TOP BOTTOM','NAS_DISTANCE_FROM_EMA_ATR'),'nas_rsi':sv(d,'NAS TOP BOTTOM','NAS_RSI')}
            # RSI-based MA
            rsima_by_ts[t]=sv(d,'Relative Strength Index','RSI-based MA')
            # SMC BOS/CHoCH first-appearance (por id)
            smc=next((s for s in (d.get('pine_labels') or []) if 'Smart Money' in (s.get('name') or '')),None)
            if smc:
                for x in (smc.get('all_labels') or smc.get('labels') or []):
                    lid=x.get('id');txt=(x.get('text') or '').upper()
                    if lid in seen_lbl: continue
                    seen_lbl.add(lid)
                    if 'BOS' in txt: smc_bos_new[t]=(txt,x.get('textColor'),x.get('price'))
                    elif 'CHOCH' in txt or 'CHOC' in txt: smc_choch_new[t]=(txt,x.get('textColor'),x.get('price'))
print("gz: demand snaps",len(demlow_by_ts),"| nas_new total",sum(nas_new.values()),"short",sum(nas_short_new.values()),"| BOS ts",len(smc_bos_new),"CHoCH ts",len(smc_choch_new))

# ============ Session VP nativo (volume REAL) ============
svp={}
for l in open(os.environ.get("L2_SVP","/tmp/svp_bars.jsonl")):
    r=json.loads(l);vp=r.get('vp') or []
    # vp=[VAH, POC, VAL] (ordem observada: high, poc, low) -> normalizar
    if len(vp)==3:
        vah,poc,val=max(vp),sorted(vp)[1],min(vp)
        svp[r['time']]={'vol':r.get('vol'),'vah':vah,'poc':poc,'val':val}
vols=[v['vol'] for v in svp.values() if v['vol']]
print("svp bars",len(svp))

# ============ CSV joins: demand/supply quality + macro context ============
def dnum(r,k):
    try: return float(r[k])
    except: return None
dsq={int(r['candidate_id'][1:]):r for r in csv.DictReader(open(f"{D}/l2_bpt_v2_2_pruned_base_v2_demand_supply_quality.csv"))}
mac={int(r['candidate_id'][1:]):r for r in csv.DictReader(open(f"{D}/l2_bpt_v2_2_pruned_base_v2_macro_context.csv"))}

# ============ NAS 1D ============
d1=json.load(open(os.environ.get("L2_D1_SIG","/tmp/d1_sig_v3.json")));NAS1D=d1.get('nas',{});BUY1D=d1.get('buy',{})
def nas1d_recent(i,days=3):
    cur=datetime.fromtimestamp(TS[i],tz=timezone.utc).date()
    for k,v in NAS1D.items():
        try: dd=datetime.fromtimestamp(int(k),tz=timezone.utc).date()
        except: continue
        if v==1 and 0<=(cur-dd).days<=days: return 1
    return 0

# ============ episodes + E-id mapping ============
base=sorted(int(r['candidate_id'][1:]) for r in csv.DictReader(open(f"{D}/l2_bpt_v2_2_pruned_base_v2.csv")))
eps=[];cur=[base[0]]
for a,b in zip(base,base[1:]):
    if b-a<=6: cur.append(b)
    else: eps.append(cur);cur=[b]
eps.append(cur)
reps=[(e[0],e) for e in eps if ATR[e[0]]]
sw={r['episode_id']:r for r in csv.DictReader(open(f"{D}/l2_bpt_swing_anatomy.csv"))}
def idxof(eid):
    try:
        t=int(datetime.strptime(sw[eid]['timestamp'],'%Y-%m-%d %H:%M').replace(tzinfo=timezone.utc).timestamp())
        return TSidx.get(t)
    except: return None
WIN=['E1','E17','E27','E30','E40'];LOSE=['E23','E24','E15','E34','E39']
win_idx={idxof(e) for e in WIN if idxof(e) is not None}
lose_idx={idxof(e) for e in LOSE if idxof(e) is not None}
eid_by_idx={idxof(e):e for e in WIN+LOSE if idxof(e) is not None}

# ============ FEATURE BUILDERS (causais) ============
def bubbles(i):
    rec=BUB[i];cnt=lambda pid,w: sum(1 for b in rec if b.get('plot_id')==pid and b.get('bars_ago',99)<=w)
    out={}
    for w in (8,):
        out.update({f'buy_s':cnt('plot_0',w),f'buy_m':cnt('plot_2',w),f'buy_L':cnt('plot_4',w),
                    f'sell_s':cnt('plot_6',w),f'sell_m':cnt('plot_8',w),f'sell_L':cnt('plot_10',w)})
    poc=[b for b in rec if b.get('plot_id')=='plot_12']
    out['poc_recent']=len(poc)
    nb=out['buy_s']+out['buy_m']+out['buy_L'];ns=out['sell_s']+out['sell_m']+out['sell_L']
    out['buy_total']=nb;out['sell_total']=ns;out['buy_sell_ratio']=round(nb/ns,2) if ns else (nb if nb else 0)
    out['large_sell_10b']=sum(1 for b in rec if b.get('plot_id') in('plot_8','plot_10') and b.get('bars_ago',99)<=10)
    out['large_buy_10b']=sum(1 for b in rec if b.get('plot_id') in('plot_2','plot_4') and b.get('bars_ago',99)<=10)
    return out
def demand_sl(i):
    p=C[i];a=ATR[i];lows=demlow_by_ts.get(TS[i])
    if lows:
        below=[lo for lo in lows if lo<p]
        if below:
            nd=max(below)
            if (p-nd)<=5*a: return max(p-(nd-0.1*a),0.3*a),'demand'
    return swing_origin(i),'swing'
def sl_type(i,risk,dist):
    a=ATR[i];lp=legpos(i,90);rsi=RS[i] or 0
    if lp>=85 and rsi>=70: return 'TOP_EXHAUSTION'
    if dist is not None and dist<=2.0: return 'V_REVERSAL_DEMAND'
    if dist is not None and dist<=5.0: return 'NORMAL_DEMAND_BASE'
    return 'LATE_WIDE'
def realR(i,risk):
    p=C[i];stop=p-risk;pd=False;rz=0.0;rem=1.0;e=min(i+60,N-1)
    for j in range(i+1,e+1):
        if L[j]<=stop:
            f=O[j] if O[j]<=stop else stop;return round(rz+rem*((f-p)/risk)-0.10,2)
        if not pd and H[j]>=p+2*risk: rz+=1.0;rem=0.5;pd=True;stop=p
        if pd and H[j]>=p+6*risk: return round(rz+rem*6.0-0.10,2)
    return round(rz+rem*((C[e]-p)/risk)-0.10,2)
def exitype(i,risk):
    p=C[i];stop=p-risk;pd=False;e=min(i+60,N-1)
    for j in range(i+1,e+1):
        if not pd and L[j]<=stop: return 'STOP_LOSS'
        if not pd and H[j]>=p+2*risk: pd=True
        if pd and H[j]>=p+6*risk: return 'WIN_RUNNER'
        if pd and L[j]<=p: return 'WIN_BE'
    return 'WIN_HELD' if pd else 'SCRATCH'
def hour_utc(i): return datetime.fromtimestamp(TS[i],tz=timezone.utc).hour
def smc_recency(dic,i,maxb=15):
    for j in range(i,max(0,i-maxb)-1,-1):
        if TS[j] in dic:
            txt,col,pr=dic[TS[j]];return {'bars_ago':i-j,'text':txt,'color':col,'price':pr}
    return None

def packet(i):
    a=ATR[i];p=C[i];r=dsq.get(i,{});m=mac.get(i,{})
    risk,slsrc=demand_sl(i);dist_dem=dnum(r,'dist_4h_demand_low_atr')
    closes_d=[c for _,_,c in daily_closes_upto(i)]
    rsi1d=rsi_wilder(closes_d);rsi1d_ma=None
    if rsi1d is not None and len(closes_d)>=28:
        # RSI_1D MA(14) aproximada: média dos últimos 14 rsi diários (recalcula em janela)
        seq=[rsi_wilder(closes_d[:k+1]) for k in range(len(closes_d)-14,len(closes_d))]
        seq=[x for x in seq if x is not None];rsi1d_ma=round(sum(seq)/len(seq),1) if seq else None
    sm20=sma(C,i,20);sm50=sma(C,i,50)
    vpr=svp.get(TS[i]);relvol=None
    if vpr and vpr['vol'] and vols:
        avgv=sum(vols[max(0,0):])/len(vols) if vols else None
        # vol relativo causal: média dos últimos ~50 bars de svp por tempo
        recent=[svp[TS[j]]['vol'] for j in range(max(0,i-50),i) if TS[j] in svp and svp[TS[j]]['vol']]
        relvol=round(vpr['vol']/(sum(recent)/len(recent)),2) if recent else None
    nasn=nas_num_by_ts.get(TS[i],{})
    bub=bubbles(i)
    consec_down=0
    for j in range(i,0,-1):
        if C[j]<C[j-1]: consec_down+=1
        else: break
    consec_up=0
    for j in range(i,0,-1):
        if C[j]>C[j-1]: consec_up+=1
        else: break
    rsi_drop=(max([RS[j] for j in range(max(0,i-6),i+1) if RS[j] is not None] or [50]))-(RS[i] or 50)
    pk={
     'episode_id':eid_by_idx.get(i,''),
     'bar_idx':i,'ts':TS[i],'datetime':datetime.fromtimestamp(TS[i],tz=timezone.utc).strftime('%Y-%m-%d %H:%M'),
     'price':round(p,2),'atr':round(a,2),
     # ---- REGIME / MACRO ----
     'macro_leg_direction':m.get('macro_leg_direction',''),'macro_leg_phase':m.get('macro_leg_phase',''),
     'trend_30_atr':round((p-C[i-30])/a,2) if i>=30 else None,'trend_90_atr':round((p-C[i-90])/a,2) if i>=90 else None,
     'slope20_atr':round((C[i]-C[i-20])/a,2) if i>=20 else None,
     'dist_sma20_atr':round((p-sm20)/a,2) if sm20 else None,'dist_sma50_atr':round((p-sm50)/a,2) if sm50 else None,
     'price_vs_sma50':'above' if sm50 and p>sm50 else 'below',
     'rsi_1d':rsi1d,'rsi_1d_ma':rsi1d_ma,'rsi_1d_sub_ma':(rsi1d is not None and rsi1d_ma is not None and rsi1d<rsi1d_ma),
     # ---- CAPITULATION / MOMENTUM ----
     'drop20_atr':round((max(C[max(0,i-20):i+1])-p)/a,2),'rise20_atr':round((p-min(C[max(0,i-20):i+1]))/a,2),
     'rsi':RS[i],'rsi_min8':min([RS[j] for j in range(max(0,i-7),i+1) if RS[j] is not None] or [50]),
     'rsi_max8':max([RS[j] for j in range(max(0,i-7),i+1) if RS[j] is not None] or [50]),
     'rsi_vs_ma':('above' if (rsima_by_ts.get(TS[i]) and RS[i] and RS[i]>rsima_by_ts[TS[i]]) else 'below') if rsima_by_ts.get(TS[i]) else None,
     'rsi_drop_6b':round(rsi_drop,1),'consec_down':consec_down,'consec_up':consec_up,
     'range_exp':round(trs[i-1]/(sum(trs[max(0,i-15):i-1])/14),2) if i>15 else None,
     'atr_level':round(a,2),'atr_pctile_proxy':round(a/(sum([x for x in ATR[max(0,i-100):i] if x])/max(1,len([x for x in ATR[max(0,i-100):i] if x]))),2) if i>100 else None,
     'sweet_spot_falling_knife':(rsi_drop>=6 and (trs[i-1]/a if a else 0)>=1.1) or consec_down>=6,
     # ---- LEGPOS ----
     'legpos30':legpos(i,30),'legpos60':legpos(i,60),'legpos90':legpos(i,90),
     # ---- RSI DIVERGENCE (A7) ----
     'rsi_bear_div_20b':rsi_bear_div(i),'rsi_bull_div_20b':rsi_bull_div(i),
     # ---- NAS ----
     'nas_long_new_8b':int(any(nas_new.get(TS[j],0) for j in range(max(0,i-7),i+1))),
     'nas_short_new_8b':int(any(nas_short_new.get(TS[j],0) for j in range(max(0,i-7),i+1))),
     'nas_dist_ema_atr':nasn.get('dist_ema_atr'),'nas_rsi':nasn.get('nas_rsi'),'nas_1d_long_recent':nas1d_recent(i),
     # ---- BUBBLES (auction) ----
     **{f'bub_{k}':v for k,v in bub.items()},
     # ---- DEMAND 4H/1D ----
     'has_4h_demand':r.get('has_4h_demand_below'),'dist_4h_demand_low_atr':dist_dem,
     'demand_width_atr':dnum(r,'demand_4h_width_atr'),'demand_age_bars':dnum(r,'demand_4h_age_bars'),
     'demand_touched_on_retest':r.get('demand_4h_touched_on_retest'),'demand_origin_of_leg':r.get('demand_4h_origin_of_leg_cand'),
     'has_d1_demand':r.get('has_d1_demand_below'),'dist_d1_demand_atr':dnum(r,'dist_d1_demand_atr'),
     # ---- SUPPLY / OVERHEAD (rejection risk) ----
     'has_4h_supply_overhead':r.get('has_4h_supply_overhead'),'dist_4h_supply_low_atr':dnum(r,'dist_4h_supply_low_atr'),
     'supply_blocks_2ATR':r.get('supply_4h_blocks_target_2ATR'),'supply_blocks_3ATR':r.get('supply_4h_blocks_target_3ATR'),
     'supply_rejected_before':r.get('supply_4h_rejected_before_entry'),'supply_broken_before':r.get('supply_4h_broken_before_entry'),
     'has_d1_supply':r.get('has_d1_supply_overhead'),'dist_d1_supply_atr':dnum(r,'dist_d1_supply_atr'),
     # ---- SESSION VP (volume REAL) ----
     'rel_volume':relvol,'below_VAL':(vpr is not None and p<vpr['val']) if vpr else None,
     'dist_POC_atr':round((p-vpr['poc'])/a,2) if vpr else None,'dist_VAL_atr':round((p-vpr['val'])/a,2) if vpr else None,
     'va_width_atr':round((vpr['vah']-vpr['val'])/a,2) if vpr else None,
     # ---- SMC LuxAlgo (estrutura) ----
     'smc_bos':smc_recency(smc_bos_new,i),'smc_choch':smc_recency(smc_choch_new,i),
     # ---- RECLAIM QUALITY ----
     'reclaim_body_atr':round((C[i]-O[i])/a,2),'reclaim_dist_from_demand_atr':dnum(r,'reclaim_close_dist_from_demand_atr'),
     'reclaim_dist_from_supply_atr':dnum(r,'reclaim_close_dist_from_supply_atr'),
     # ---- SL / RISK ----
     'sl_atr':round(risk/a,2),'sl_source':slsrc,'sl_type':sl_type(i,risk,dist_dem),
     # ---- ANTI-TOP / TIME ----
     'F_STRICT_top_late':(legpos(i,90)>=85 and (RS[i] or 0)>=70),'hour_utc':hour_utc(i),
     'dead_hour':hour_utc(i) in (2,18,20),
    }
    return pk

# ============ similaridade winners/losers (centroide em eixos-chave) ============
AX=['drop20_atr','rsi_min8','legpos90','dist_4h_demand_low_atr','sl_atr','rsi_bear_div_20b','trend_90_atr']
def vec(pk): return [pk.get(k) if isinstance(pk.get(k),(int,float)) else None for k in AX]
allp={i:packet(i) for i,_ in reps}
def centroid(idxset):
    cols=[[allp[i].get(k) for i in idxset if isinstance(allp[i].get(k),(int,float))] for k in AX]
    return [sum(c)/len(c) if c else 0 for c in cols]
win_c=centroid([i for i in win_idx if i in allp]);lose_c=centroid([i for i in lose_idx if i in allp])
def dist(v,c):
    s=0;n=0
    for x,y in zip(v,c):
        if x is not None: s+=(x-y)**2;n+=1
    return round(math.sqrt(s/n),2) if n else None
# DA fix (ab5e8395): similaridade é DERIVADA DE OUTCOME (centroides dos GT) -> NÃO entra no packet/matrix
# (seria auto-confirmação circular). Vai só p/ arquivo DIAGNÓSTICO; reasoning é cego a ela e forma
# similaridade qualitativamente pelas ASSINATURAS na rubrica.
sim_diag={}
for i,pk in allp.items():
    v=vec(pk);dw=dist(v,win_c);dl=dist(v,lose_c)
    sim_diag[i]={'sim_dist_to_winners':dw,'sim_dist_to_losers':dl,'closer_to':'WINNERS' if (dw or 9)<(dl or 9) else 'LOSERS'}

# ============ WRITE: matrix (factors) + packets (reasoning, NO outcome) + outcomes (separate) ============
order=list(next(iter(allp.values())).keys())
# matrix CSV (flatten smc dicts)
def flat(pk):
    o={}
    for k,v in pk.items():
        if isinstance(v,dict):
            o[k+'_bars_ago']=v.get('bars_ago');o[k+'_text']=v.get('text')
        else: o[k]=v
    return o
flats=[flat(allp[i]) for i,_ in reps]
cols=list(flats[0].keys())
with open(f"{D}/l2_bpt_trade_qualification_matrix.csv","w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=cols);w.writeheader()
    for r in flats: w.writerow({k:r.get(k,'') for k in cols})
# packets JSONL (rico, sem outcome) p/ reasoning cego
with open(os.environ.get("L2_QUAL_PACKETS","/tmp/qual_packets.jsonl"),"w") as f:
    for i,_ in reps: f.write(json.dumps(allp[i])+"\n")
# outcomes (SEPARADO - só validação) + similaridade DIAGNÓSTICO (outcome-derived, NÃO p/ reasoning)
with open(f"{D}/l2_bpt_trade_qualification_outcomes.csv","w",newline="") as f:
    w=csv.writer(f);w.writerow(['bar_idx','episode_id','datetime','sl_atr','realR','exitype','is_winner_gt','is_loser_gt',
                                'sim_dist_to_winners','sim_dist_to_losers','closer_to_DIAG'])
    for i,_ in reps:
        risk,_=demand_sl(i);sd=sim_diag[i]
        w.writerow([i,eid_by_idx.get(i,''),allp[i]['datetime'],round(risk/ATR[i],2),realR(i,risk),exitype(i,risk),
                    int(i in win_idx),int(i in lose_idx),sd['sim_dist_to_winners'],sd['sim_dist_to_losers'],sd['closer_to']])

# ============ verificações: causalidade + recall gate ============
print(f"\n=== EXTRAÍDO: {len(reps)} episódios, {len(cols)} fatores/episódio ===")
print("Recall gate winners (devem estar na base):")
for e in WIN:
    ix=idxof(e);print(f"  {e}: idx={ix} {'PRESENTE' if ix in allp else 'AUSENTE'}")
print("should-not-long presentes:")
for e in LOSE:
    ix=idxof(e);print(f"  {e}: idx={ix} {'PRESENTE' if ix in allp else 'AUSENTE'}")
print("WROTE: results/l2_bpt_trade_qualification_matrix.csv + outcomes.csv + /tmp/qual_packets.jsonl")
