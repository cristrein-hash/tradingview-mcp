#!/usr/bin/env python3
"""Bottom/Reversal Confluence — PARTE 0 (RAW audit dos componentes do estado) + TESTE A
(o ESTADO tem edge? long-in-state vs legpos-random-geral). SL demand-anchored, exit partial50.
SEM tunar K/θ/janelas (defaults do pré-reg, importados do Caminho B).
NAS LONG INCLUÍDO causalmente via first-appearance no gz (detector 'NAS TOP BOTTOM DETECTOR',
nlong>prev por snapshot — mesmo método de extract_1d_v3.py), mesma passada do demand."""
import json,csv,gzip,random,statistics
random.seed(20260618)
D="results"
fr=[json.loads(l) for l in open("/tmp/raw_features_2020_2026.jsonl")]
H=[r['high'] for r in fr];L=[r['low'] for r in fr];C=[r['close'] for r in fr];O=[r['open'] for r in fr];TS=[r['ts_epoch'] for r in fr];RS=[r.get('rsi') for r in fr];BUB=[r.get('bubbles_recent') or [] for r in fr];N=len(fr)
ATR=[None]*N;trs=[]
for i in range(1,N):
    trs.append(max(H[i]-L[i],abs(H[i]-C[i-1]),abs(L[i]-C[i-1])))
    if i>=14: ATR[i]=sum(trs[i-14:i])/14
PL5=[False]*N
for j in range(5,N-5):
    if L[j]<min(L[j-5:j]) and L[j]<min(L[j+1:j+6]): PL5[j]=True
def swing_origin(i):
    p=C[i];a=ATR[i];lo=None
    for j in range(i-5,4,-1):
        if PL5[j] and L[j]<p: lo=L[j];break
    if lo is None: lo=min(L[max(0,i-6):i+1])
    return max(p-(lo-0.1*a),0.3*a)
# ---- componentes causais (defaults do pré-reg, NÃO tunar) ----
def drop20(i): return (max(C[max(0,i-20):i+1])-C[i])/ATR[i] if ATR[i] else 0   # queda do topo recente (>=4 = capitulação)
def rsimin8(i):
    w=[RS[j] for j in range(max(0,i-7),i+1) if RS[j] is not None];return min(w) if w else 50
SELL={'plot_6','plot_8','plot_10'}
def bubsell8(i): return sum(1 for b in BUB[i] if b.get('plot_id') in SELL and b.get('bars_ago',99)<=8)
def legpos(i):
    p=C[i];hi=max(H[max(0,i-90):i+1]);lo=min(L[max(0,i-90):i+1]);return 100*(p-lo)/(hi-lo) if hi>lo else 50
# demand cache (gz as-of-bar)
RAW="/Volumes/GUTS_ LACIE/TradingData/raw_replay/XAUUSD";COB="OB Detector"
GZ=[f"{RAW}/4H/XAUUSD_240m_replay_2020-01-01_to_2023-01-01.jsonl.gz",f"{RAW}/4H/XAUUSD_240m_replay_2023-01-03_to_2026-05-25.jsonl.gz"]
demlow={};nas_new={}   # nas_new[ts]=1 quando #labels LONG aumentou vs snapshot anterior (first-appearance causal)
for gz in GZ:
    prev_nlong=None
    with gzip.open(gz,'rt') as f:
        for line in f:
            try:d=json.loads(line)
            except:continue
            ov=d.get('ohlcv') or []
            if not ov: continue
            ts=ov[-1]['time']
            cob=next((s for s in (d.get('pine_boxes') or []) if COB in (s.get('name') or '')),None)
            if cob: demlow[ts]=[b.get('low') for b in (cob.get('all_boxes') or []) if (b.get('text') or '').upper()=='DEMAND' and b.get('low') is not None]
            nas=next((s for s in (d.get('pine_labels') or []) if 'NAS' in (s.get('name') or '').upper()),None)
            labs=(nas.get('all_labels') or nas.get('labels') or []) if nas else []
            nlong=sum(1 for l in labs if (l.get('text') or '').upper()=='LONG')
            nas_new[ts]=1 if (prev_nlong is not None and nlong>prev_nlong) else 0
            prev_nlong=nlong
def nas_recent(i):   # NAS LONG novo nos últimos 8 bars (mesma janela de bubsell8; confluência, não gate isolado)
    return any(nas_new.get(TS[j],0)==1 for j in range(max(0,i-7),i+1))
def demand_dist(i):
    lows=demlow.get(TS[i])
    if not lows: return None
    below=[lo for lo in lows if lo<C[i]]
    return (C[i]-max(below))/ATR[i] if below else None
def demand_sl(i):
    d=demand_dist(i);p=C[i];a=ATR[i]
    if d is not None and d<=5:
        nd=max(lo for lo in demlow[TS[i]] if lo<p);return max(p-(nd-0.1*a),0.3*a)
    return swing_origin(i)
def realR(i,risk):
    p=C[i];stop=p-risk;pd=False;rz=0.0;rem=1.0;e=min(i+60,N-1)
    for j in range(i+1,e+1):
        if L[j]<=stop:
            f=O[j] if O[j]<=stop else stop;return rz+rem*((f-p)/risk)-0.10
        if not pd and H[j]>=p+2*risk: rz+=1.0;rem=0.5;pd=True;stop=p
        if pd and H[j]>=p+6*risk: return rz+rem*6.0-0.10
    return rz+rem*((C[e]-p)/risk)-0.10
def exitype(i,risk):
    p=C[i];stop=p-risk;pd=False;e=min(i+60,N-1)
    for j in range(i+1,e+1):
        if not pd and L[j]<=stop: return 'STOP'
        if not pd and H[j]>=p+2*risk: pd=True
        if pd and H[j]>=p+6*risk: return 'WIN'
        if pd and L[j]<=p: return 'WIN'
    return 'WIN' if pd else 'SCRATCH'
def lpb(lp): return 0 if lp<30 else 1 if lp<55 else 2 if lp<75 else 3
# ===== PARTE 0: RAW AUDIT (cobertura/causalidade) =====
bars=[i for i in range(95,N-61) if ATR[i]]
def cov(fn,cond): return sum(1 for i in bars if cond(fn(i)))
print("=== PARTE 0 — RAW AUDIT componentes (universo",len(bars),"barras) ===")
aud=[
 ('drop20_atr','frozen OHLC','causal',f"capitulação >=4ATR: {cov(drop20,lambda x:x>=4)} barras ({100*cov(drop20,lambda x:x>=4)/len(bars):.0f}%)"),
 ('rsi_min_8','frozen rsi Wilder','causal',f"oversold <=30: {cov(rsimin8,lambda x:x<=30)} ({100*cov(rsimin8,lambda x:x<=30)/len(bars):.0f}%)"),
 ('bubble_sell_8','frozen bubbles_recent plot_6/8/10 + bars_ago','causal (bars_ago)',f">=2: {cov(bubsell8,lambda x:x>=2)} ({100*cov(bubsell8,lambda x:x>=2)/len(bars):.0f}%); mapping SELL=plot6/8/10 (memória)"),
 ('demand_dist','gz OB Detector as-of-bar','causal repaint-auditado',f"demanda abaixo presente: {sum(1 for i in bars if demand_dist(i) is not None)} ({100*sum(1 for i in bars if demand_dist(i) is not None)/len(bars):.0f}%)"),
 ('legpos90','frozen OHLC','causal',f"baixo/médio <75: {cov(legpos,lambda x:x<75)} ({100*cov(legpos,lambda x:x<75)/len(bars):.0f}%)"),
 ('NAS_long_recent','gz NAS TOP BOTTOM DETECTOR first-appearance (nlong>prev)','causal (replay bar-a-bar)',f"NAS LONG novo em 8b: {sum(1 for i in bars if nas_recent(i))} ({100*sum(1 for i in bars if nas_recent(i))/len(bars):.0f}%); total nas_new={sum(nas_new.values())}"),
]
for nm,src,caus,c in aud: print(f"  {nm:<16} src={src:<42} {caus:<55} | {c}")
with open(f"{D}/l2_bpt_botrev_raw_audit.csv","w",newline="") as f:
    w=csv.writer(f);w.writerow(['component','source','causal','coverage_note']);w.writerows(aud)
# ===== ESTADO (convergência, defaults pré-reg, NÃO tunado) =====
# NAS = confluência, não gate isolado (pré-reg §2): reporto K=5 estrutural E K=6 (+NAS) — sem escolher/tunar K.
def in_state(i):
    return drop20(i)>=4 and rsimin8(i)<=30 and bubsell8(i)>=2 and (demand_dist(i) is not None and demand_dist(i)<=5) and legpos(i)<75
def nas_recent_lag(i):  # i-1 causal-confirmado (exclui bar i; mata risco repaint do label da barra de entrada)
    return any(nas_new.get(TS[j],0)==1 for j in range(max(0,i-8),i))
def in_state_nas(i): return in_state(i) and nas_recent(i)
def in_state_nas_lag(i): return in_state(i) and nas_recent_lag(i)
def episodes(sb,gap=6):  # 1 evento por cluster (gap>6 bars) — unidade canônica (anti serial-correlation)
    sb=sorted(sb);eps=[];last=None
    for i in sb:
        if last is None or i-last>gap: eps.append(i)
        last=i
    return eps
state_bars=[i for i in bars if in_state(i)]
state_nas_bars=[i for i in bars if in_state_nas(i)]
state_nas_lag_bars=[i for i in bars if in_state_nas_lag(i)]
print(f"\n=== ESTADO: 5-sinais bars={len(state_bars)}(ep{len(episodes(state_bars))}) | +NAS(6) bars={len(state_nas_bars)}(ep{len(episodes(state_nas_bars))}) | +NAS i-1 bars={len(state_nas_lag_bars)}(ep{len(episodes(state_nas_lag_bars))}) ===")
# ===== TESTE A: estado tem edge? long-in-state vs legpos-random-geral =====
uni_by_b={0:[],1:[],2:[],3:[]}
for i in bars:
    if demand_dist(i) is not None: uni_by_b[lpb(legpos(i))].append(i)
def metr(idx):
    rs=[realR(i,demand_sl(i)) for i in idx];ex=[exitype(i,demand_sl(i)) for i in idx]
    from collections import Counter;c=Counter(ex)
    return len(rs),round(sum(rs)/len(rs),3),round(sum(rs),1),c['WIN'],c['STOP'],c['SCRATCH']
def baseline(idx,B=2000):
    from collections import Counter
    bc=Counter(lpb(legpos(i)) for i in idx);means=[]
    for _ in range(B):
        s=[]
        for b,cnt in bc.items():
            pool=uni_by_b[b]
            if pool: s+=[pool[random.randrange(len(pool))] for _ in range(cnt)]
        if s: means.append(sum(realR(i,demand_sl(i)) for i in s)/len(s))
    means.sort();q=lambda p:means[int(p*len(means))];return q(.05),q(.5),q(.95),means
rows=[]
variants=[('STATE_5',state_bars),('STATE_6_NAS',state_nas_bars),('STATE_6_NAS_i-1',state_nas_lag_bars)]
for unit in ['BAR','EPISODE']:
    print(f"\n  --- unidade={unit} (EPISODE=gate honesto anti serial-correlation) ---")
    for tag,sbraw in variants:
        sb=episodes(sbraw) if unit=='EPISODE' else sbraw
        if not sb: print(f"  {tag}: 0 — pulado");continue
        n,avgR,sumR,W,S,SC=metr(sb)
        b5,b50,b95,bd=baseline(sb)
        p=sum(1 for x in bd if avgR>x)/len(bd)
        ver='EDGE' if p>=0.975 else 'sugestivo' if p>=0.85 else 'sem edge'   # 0.975 = Bonferroni desta rodada
        print(f"  {tag:<16} n={n} avgR={avgR:+.3f} (W{W}/S{S}/SC{SC}) sumR={sumR:+.1f} | rand50={b50:.3f} delta={avgR-b50:+.3f} P={p:.3f} -> {ver}")
        rows.append([unit,tag,n,avgR,sumR,W,S,SC,round(b50,3),round(avgR-b50,3),round(p,3)])
print("\n  Bonferroni rodada (3 variantes) -> P>=0.975 p/ EDGE confirmado. Unidade canônica=EPISODE.")
with open(f"{D}/l2_bpt_botrev_testA.csv","w",newline="") as f:
    w=csv.writer(f);w.writerow(['unit','set','n','avgR','sumR','WIN','STOP','SCRATCH','base50','delta','P_gt_rand'])
    w.writerows(rows)
print("WROTE raw_audit.csv + testA.csv")
