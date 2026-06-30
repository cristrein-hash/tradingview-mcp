#!/usr/bin/env python3
"""RTSE Fase 10 — FSM HÍBRIDO (evento+estrutura), conserta os 2 pontos do Cris:
(1) ONSET rápido pelo EVENTO de topo/fundo do detector (na mosca no blow-off), NÃO pela estrutura lenta;
(2) RANGE explícito = "bear intra-macrobull" (correção que re-expande = acumulação). Estrutura/BOS só RESISTE ao flip.
Regra: BULL --topo--> RANGE (fim do bull na mosca). RANGE resolve: rompe acima=BULL(acumulação) / quebra abaixo=BEAR(distribuição).
BEAR --fundo--> RANGE. RANGE resolve: rompe topo-anterior=BULL / quebra fundo=BEAR. Rápido a entrar, lento a sair. Causal."""
import json,csv,math,statistics as st,bisect,datetime as dt
from pathlib import Path
ROOT=Path("/Users/cristrein/tradingview-mcp");REV=ROOT/"my-strategy/research/revalidation";GT=ROOT/"regime_turnstate_engine/ground_truth"
def load(p): b=[json.loads(l) for l in p.read_text().splitlines()];b.sort(key=lambda x:x["t"]);return b
B4=load(REV/"raw_4h_ohlc.jsonl");T=[b["t"] for b in B4];C=[b["c"] for b in B4];H=[b["h"] for b in B4];L=[b["l"] for b in B4];n=len(B4)
def rsi(c,k=14):
    g=[0.]*len(c);l=[0.]*len(c)
    for i in range(1,len(c)):
        d=c[i]-c[i-1];g[i]=max(d,0);l[i]=max(-d,0)
    ag=st.mean(g[1:k+1]);al=st.mean(l[1:k+1]);o=[50.]*len(c)
    for i in range(k+1,len(c)):
        ag=(ag*(k-1)+g[i])/k;al=(al*(k-1)+l[i])/k;o[i]=100-100/(1+ag/al) if al else 100.
    return o
def cusum(c,dr):
    r=[0.]+[math.log(c[i]/c[i-1]) for i in range(1,len(c))];a=set();s=0.
    for i in range(1,len(c)):
        w=r[max(1,i-100):i];mu=st.mean(w) if len(w)>2 else 0;sg=(st.pstdev(w) if len(w)>2 else 1) or 1
        z=(r[i]-mu)/sg;s=max(0,s+(dr*z-0.5))
        if s>5:a.add(i);s=0.
    return a
def rng(b):return b["h"]-b["l"]
def bear_exp(B):
    o=[]
    for i in range(25,len(B)):
        if C[i-5]<=C[i-14]:continue
        lv=st.mean([rng(b) for b in B[i-14:i-4]]) or 1e-9;w=B[i-4:i+1]
        if sum(1 for b in w if b["c"]<b["o"])>=4 and sum(1 for b in w if rng(b)>1.5*lv)>=2 and C[i]<C[i-5]:o.append(i)
    return o
def ema(c,k):
    a=2/(k+1);o=[c[0]]
    for x in c[1:]: o.append(a*x+(1-a)*o[-1])
    return o
EMAL=ema(C,300)                   # macro (≈50 dias 4H) p/ sobre-extensão
R4=rsi(C)
cd4=cusum(C,-1);cu4=cusum(C,1)
expdiv4=[i for i in bear_exp(B4) if H[max(range(i-8,i-3),key=lambda k:H[k])]>H[max(range(i-22,i-9),key=lambda k:H[k])] and R4[max(range(i-8,i-3),key=lambda k:H[k])]<R4[max(range(i-22,i-9),key=lambda k:H[k])]]
STRONG_TOP=set(cd4)               # topo FORTE (CUSUM-down/blow-off) -> caracteriza BEAR direto
MILD_TOP=set(expdiv4)-set(cd4)    # topo suave -> RANGE (acumulação, pode re-expandir)
BOT_EV=set(cu4)                   # evento de fundo (onset BULL rápido)
def zigzag(p):
    piv=[];dirn=0;hi_p=C[0];hi_i=0;lo_p=C[0];lo_i=0
    for i in range(1,n):
        if C[i]>hi_p: hi_p=C[i];hi_i=i
        if C[i]<lo_p: lo_p=C[i];lo_i=i
        if dirn>=0 and C[i]<=hi_p*(1-p): piv.append((i,hi_p,'H'));dirn=-1;lo_p=C[i];lo_i=i
        elif dirn<=0 and C[i]>=lo_p*(1+p): piv.append((i,lo_p,'L'));dirn=1;hi_p=C[i];hi_i=i
    return piv
boxes=[]
for r in csv.DictReader(open(GT/"cris_regime_boxes.csv")):
    if r["role"]=="MACRO": boxes.append((int(r["start"]),int(r["end"]),r["family"]))
def gt_at(ts):
    for s,e,f in boxes:
        if s<=ts<=e: return f
    return None
def run(p_f,EXT=1.15,LO=0.88):
    piv=zigzag(p_f);pi=0;SH=None;SL=None
    pivc=zigzag(0.08);pc=0;SHc=None;SLc=None         # zigzag GROSSO p/ saída macro (ambos lados)
    state='BULL';reg=[None]*n;r_hi=r_lo=None
    for i in range(n):
        while pi<len(piv) and piv[pi][0]<=i:
            if piv[pi][2]=='H': SH=piv[pi][1]
            else: SL=piv[pi][1]
            pi+=1
        while pc<len(pivc) and pivc[pc][0]<=i:
            if pivc[pc][2]=='H': SHc=pivc[pc][1]
            else: SLc=pivc[pc][1]
            pc+=1
        overext_hi=C[i]>EMAL[i]*EXT       # blow-off (topo de exaustão)
        overext_lo=C[i]<EMAL[i]*LO        # capitulação (fundo de exaustão)
        if state=='BULL':
            if i in STRONG_TOP and overext_hi:
                state='BEAR'                                   # blow-off SOBRE-ESTENDIDO: BEAR na mosca
            elif (i in MILD_TOP) or (i in STRONG_TOP):
                state='RANGE';r_hi=max(C[max(0,i-8):i+1]);r_lo=(SL if SL is not None else min(L[max(0,i-8):i+1]))
        elif state=='BEAR':
            if i in BOT_EV and overext_lo:
                state='BULL'                                   # capitulação SOBRE-ESTENDIDA: BULL na mosca (simétrico ao topo)
            elif i in BOT_EV:
                state='RANGE';r_lo=min(C[max(0,i-8):i+1]);r_hi=(SH if SH is not None else max(H[max(0,i-8):i+1]))
            elif SHc is not None and C[i]>SHc:                 # rompeu topo MACRO grosso: sai do BEAR
                state='RANGE';r_lo=min(C[max(0,i-8):i+1]);r_hi=SHc
        elif state=='RANGE':
            if r_lo is not None and C[i]<r_lo: state='BEAR'
            elif r_hi is not None and C[i]>r_hi: state='BULL'
        reg[i]=state
    return reg
def validate(p_f,EXT=1.15,LO=0.88):
    reg=run(p_f,EXT,LO);agree=tot=0;cnt={'BULL':0,'RANGE':0,'BEAR':0}
    for i in range(n):
        g=gt_at(T[i]);r=reg[i]
        if g is None: continue
        tot+=1;agree+=(g==r);cnt[g]=cnt.get(g,0)+1
    base=max(cnt.values())/tot if tot else 0
    # 2026 macro-bear: % BEAR/RANGE/BULL + ONSET (1ª barra não-BULL após o pico Jan29)
    b0,b1=1769727600,1782770400;bb=br=bg=0;onset=None
    for i in range(n):
        if b0<=T[i]<=b1:
            if reg[i]=='BEAR':bb+=1
            elif reg[i]=='RANGE':br+=1
            elif reg[i]=='BULL':bg+=1
            if onset is None and reg[i]!='BULL': onset=T[i]
    t26=bb+br+bg
    onset_d=dt.datetime.utcfromtimestamp(onset).strftime('%Y-%m-%d') if onset else '-'
    # quanto RANGE no total
    nrange=sum(1 for r in reg if r=='RANGE')
    return reg,(agree/tot if tot else 0),base,(bb,br,bg,t26),onset_d,nrange/n
print(f"{'pf%':>4}{'LO':>6}{'concord3':>10}{'baseline':>9}{'%RNG':>6}  | 2026 BEAR%")
for p_f in [0.03,0.04]:
    for LO in [0.85,0.88,0.90]:
        reg,acc,base,(bb,br,bg,t26),onset,pr=validate(p_f,1.15,LO)
        print(f"{p_f*100:>4.0f}{LO:>6.2f}{acc*100:>9.0f}%{base*100:>8.0f}%{pr*100:>5.0f}%  | {100*bb/t26 if t26 else 0:>3.0f}")
# dump pf=3% EXT=1.15 LO=0.88
reg=run(0.03,1.15,0.88);segs=[];i0=0
for i in range(1,n):
    if reg[i]!=reg[i-1]: segs.append((T[i0],T[i],reg[i-1]));i0=i
segs.append((T[i0],T[-1],reg[-1]))
out=[]
for s,e,f in segs:
    if e<1672531200 or f is None: continue
    i_s=bisect.bisect_left(T,s);i_e=bisect.bisect_right(T,e)
    if i_e<=i_s: continue
    out.append({"start":int(s),"end":int(e),"regime":f,"hi":round(max(H[i_s:i_e]),2),"lo":round(min(L[i_s:i_e]),2),
                "d0":dt.datetime.utcfromtimestamp(s).strftime("%Y-%m-%d"),"d1":dt.datetime.utcfromtimestamp(e).strftime("%Y-%m-%d")})
json.dump(out,open("/tmp/causal_segments_v10.json","w"))
print(f"\nSEGMENTOS (pf=3%) 2024+: {len(out)}")
for s in out:
    if (s['end']-s['start'])>3*86400: print(f"  {s['regime']:5} {s['d0']} -> {s['d1']}  ({s['lo']}-{s['hi']})")
