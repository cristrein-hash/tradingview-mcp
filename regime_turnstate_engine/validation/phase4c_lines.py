#!/usr/bin/env python3
"""RTSE Fase 4c — 4 LINHAS LÓGICAS de refinamento (Cris: rodar todas). Frame ar-limpo, causal, multi-TF.
L1 espelho BEAR->BULL (fundo QUIETO: sweep+reclaim+divergência, NÃO expansão).
L2 combo cross-TF (contexto topo-divergente 4H COMO GATE + gatilho expansão-bear 30M).
L3 aceitação pós-gatilho (close-through sustentado=flip vs pavio-reclaim=dip) como discriminador.
L4 CUSUM change-point rápido (topo=down-alarm, fundo=up-alarm) nos TFs rápidos.
Métrica: recall em [alvo..+K], latência, FP/ano, null base-rate (Monte Carlo mesma densidade). n pequeno=CALIBRAÇÃO."""
import json,csv,math,statistics as st,random,bisect,datetime as dt
from pathlib import Path
ROOT=Path("/Users/cristrein/tradingview-mcp")
REV=ROOT/"my-strategy/research/revalidation";GT=ROOT/"regime_turnstate_engine/ground_truth"
def load(p): b=[json.loads(l) for l in p.read_text().splitlines()];b.sort(key=lambda x:x["t"]);return b
def load15():
    import glob;S={}
    for f in sorted((ROOT/"research/xau_15m_bb_nas_leonardo/primitives").glob("*.primitives.json")):
        for b in json.loads(f.read_text())["series"]:
            S[b["t"]]={"t":b["t"],"o":b.get("o",b["c"]),"h":b["h"],"l":b["l"],"c":b["c"]}
    return [S[t] for t in sorted(S)]
def rsi_series(c,k=14):
    g=[0.0]*len(c);l=[0.0]*len(c)
    for i in range(1,len(c)):
        d=c[i]-c[i-1];g[i]=max(d,0);l[i]=max(-d,0)
    if len(c)<=k: return [50.0]*len(c)
    ag=st.mean(g[1:k+1]);al=st.mean(l[1:k+1]);out=[50.0]*len(c)
    for i in range(k+1,len(c)):
        ag=(ag*(k-1)+g[i])/k;al=(al*(k-1)+l[i])/k;out[i]=100-100/(1+ag/al) if al else 100.0
    return out
def cusum(c,direction):  # standardized-return CUSUM; direction=-1 down(topo) +1 up(fundo)
    ret=[0.0]+[math.log(c[i]/c[i-1]) for i in range(1,len(c))];al=set();s=0.0
    for i in range(1,len(c)):
        w=ret[max(1,i-100):i];mu=st.mean(w) if len(w)>2 else 0;sg=(st.pstdev(w) if len(w)>2 else 1) or 1
        z=(ret[i]-mu)/sg;s=max(0,s+(direction*z-0.5))
        if s>5: al.add(i);s=0.0
    return al
# ground truth
TOPS=[];BOTS=[]
for r in csv.DictReader(open(GT/"cris_regime_boxes.csv")):
    if r["role"]=="MACRO" and r["family"]=="BEAR": TOPS.append(int(r["start"]));BOTS.append(int(r["end"]))
    if r["role"]=="MACRO" and r["family"]=="BULL": TOPS.append(int(r["end"]));BOTS.append(int(r["start"]))
    if r["role"]=="PULLBACK" and r["family"]=="BEAR" and r["parent_fam"]=="BULL": TOPS.append(int(r["start"]))
    if r["role"]=="PULLBACK" and r["family"]=="BULL" and r["parent_fam"]=="BEAR": BOTS.append(int(r["start"]))
TOPS=sorted(set(TOPS));BOTS=sorted(set(BOTS))
def rng(b): return b["h"]-b["l"]
def anchor(B,ts_list,bot,W):
    T=[b["t"] for b in B];n=len(B);out=set()
    for t in ts_list:
        if not(T[0]<=t<=T[-1]): continue
        j=bisect.bisect_right(T,t)-1
        if not(25<j<n-6): continue
        rngk=range(max(25,j-W),min(n-6,j+W))
        out.add(min(rngk,key=lambda k:B[k]["l"]) if bot else max(rngk,key=lambda k:B[k]["h"]))
    return sorted(out)
def evalsig(B,fires,targets,K,name,extra=""):
    n=len(B);T=[b["t"] for b in B];yrs=(T[-1]-T[0])/(365.25*86400);fs=set(fires)
    lats=[];hit=0
    for e in targets:
        f=[i for i in range(e,min(n,e+K+1)) if i in fs]
        if f: hit+=1;lats.append(f[0]-e)
    recall=hit/len(targets) if targets else 0
    topwin=set(e+k for e in targets for k in range(0,K+1));fp=sum(1 for i in fires if i not in topwin);fpy=fp/yrs if yrs else 0
    random.seed(7);M=len(fires);pool=list(range(25,n));dd=[]
    for _ in range(1000):
        rf=set(random.sample(pool,M)) if 0<M<=len(pool) else set(pool)
        dd.append(sum(1 for e in targets if any((e+k) in rf for k in range(0,K+1)))/len(targets) if targets else 0)
    p=sum(1 for x in dd if x>=recall)/len(dd)
    lat=f"{st.median(lats):.0f}" if lats else "-"
    print(f"  {name:30}{len(fires):>6}{recall:>7.2f}{lat:>5}{fpy:>8.0f}{p:>8.3f}{' *' if p<0.05 else ''}  {extra}")
B30=load(GT/"raw_30m_ohlc.jsonl");B15=load15();B1=load(REV/"raw_1h_ohlc.jsonl");B4=load(REV/"raw_4h_ohlc.jsonl")
RS={id(B):rsi_series([b["c"] for b in B]) for B in [B30,B15,B1,B4]}
HEAD=f"  {'signal':30}{'fires':>6}{'recall':>7}{'lat':>5}{'FP/ano':>8}{'null_p':>8}"
# ---------- L1: espelho BEAR->BULL (fundo quieto) ----------
def bot_sig(B,div):
    C=[b["c"] for b in B];H=[b["h"] for b in B];L=[b["l"] for b in B];R=RS[id(B)]
    def S(i):
        if i<25 or i>=len(B): return False
        if C[i-5]>=C[i-14]: return False              # exige perna BEAR antes
        lvl=min(L[i-14:i-5]);sweep=min(L[i-4:i+1])<lvl;reclaim=C[i]>lvl and C[i]>C[i-1]
        if not(sweep and reclaim): return False
        if not div: return True
        lr=min(range(i-4,i+1),key=lambda k:L[k]);lp=min(range(i-14,i-5),key=lambda k:L[k])
        return L[lr]<L[lp] and R[lr]>R[lp]
    return [i for i in range(25,len(B)) if S(i)]
print("\n#### L1 — espelho BEAR->BULL (fundo quieto: sweep+reclaim[+div]) — alvo FUNDOS")
for nm,B,K,W in [("30M",B30,8,12),("15M",B15,16,24),("4H(n+)",B4,4,8)]:
    tg=anchor(B,BOTS,True,W);print(f"\n {nm}: fundos {len(tg)}\n"+HEAD)
    evalsig(B,bot_sig(B,False),tg,K,"A sweep+reclaim")
    evalsig(B,bot_sig(B,True),tg,K,"B +divergência")
# ---------- L2: combo cross-TF ----------
def bear_exp(B):  # variante A do phase4
    C=[b["c"] for b in B]
    def S(i):
        if i<25 or i>=len(B): return False
        if C[i-5]<=C[i-14]: return False
        legvol=st.mean([rng(b) for b in B[i-14:i-4]]) or 1e-9;w=B[i-4:i+1]
        return sum(1 for b in w if b["c"]<b["o"])>=4 and sum(1 for b in w if rng(b)>1.5*legvol)>=2 and C[i]<C[i-5]
    return [i for i in range(25,len(B)) if S(i)]
def divtop4_flag(B4):  # 4H bar marcado se topo divergente recente
    H=[b["h"] for b in B4];R=RS[id(B4)];flag=[False]*len(B4)
    for j in range(25,len(B4)):
        hi=max(range(j-6,j-1),key=lambda k:H[k]);ph=max(range(j-18,j-7),key=lambda k:H[k])
        flag[j]=H[hi]>H[ph] and R[hi]<R[ph]
    return flag
flag4=divtop4_flag(B4);T4=[b["t"] for b in B4]
def gate4(ts):
    j=bisect.bisect_right(T4,ts)-1
    return any(flag4[k] for k in range(max(0,j-6),j+1)) if j>=0 else False
print("\n\n#### L2 — combo cross-TF (gate 4H topo-divergente × gatilho 30M expansão) — alvo TOPOS")
for nm,B,K,W in [("30M",B30,8,12),("15M",B15,16,24)]:
    tg=anchor(B,TOPS,False,W);T=[b["t"] for b in B];fr=bear_exp(B)
    frg=[i for i in fr if gate4(T[i])]
    print(f"\n {nm}: topos {len(tg)}\n"+HEAD)
    evalsig(B,fr,tg,K,f"{nm} expansão sozinho")
    evalsig(B,frg,tg,K,f"{nm} expansão × GATE-4H-div")
tg4=anchor(B4,TOPS,False,8);print(f"\n 4H(n+): topos {len(tg4)}\n"+HEAD)
def bear_exp_div(B4):
    H=[b["h"] for b in B4];R=RS[id(B4)];base=set(bear_exp(B4));out=[]
    for i in base:
        hi=max(range(i-8,i-3),key=lambda k:H[k]);ph=max(range(i-22,i-9),key=lambda k:H[k])
        if H[hi]>H[ph] and R[hi]<R[ph]: out.append(i)
    return out
evalsig(B4,bear_exp(B4),tg4,4,"4H expansão sozinho")
evalsig(B4,bear_exp_div(B4),tg4,4,"4H expansão+div (ref B)")
# ---------- L3: aceitação pós-gatilho ----------
def accept_split(B,M=4):
    H=[b["h"] for b in B];L=[b["l"] for b in B];C=[b["c"] for b in B];base=bear_exp(B);acc=[];rej=[]
    for i in base:
        if i+M>=len(B): continue
        refhi=max(H[i-8:i-3])
        reclaimed=max(H[i+1:i+M+1])>=refhi
        held=min(C[i+1:i+M+1])<C[i]
        (rej if reclaimed else (acc if held else rej)).append(i+M)  # emite em i+M (confirmação)
    return acc,rej
print("\n\n#### L3 — aceitação pós-gatilho (close-through=flip vs pavio-reclaim=dip) — alvo TOPOS")
for nm,B,K,W in [("30M",B30,8,12),("15M",B15,16,24),("4H(n+)",B4,4,8)]:
    tg=anchor(B,TOPS,False,W);acc,rej=accept_split(B)
    print(f"\n {nm}: topos {len(tg)}\n"+HEAD)
    evalsig(B,bear_exp(B),tg,K,"todos (baseline)")
    evalsig(B,acc,tg,K+4,"ACEITAÇÃO (held below)")
    evalsig(B,rej,tg,K+4,"REJEIÇÃO (reclaim)")
# ---------- L4: CUSUM rápido ----------
print("\n\n#### L4 — CUSUM change-point rápido (down=topo / up=fundo)")
for nm,B,K,W in [("30M",B30,8,12),("15M",B15,16,24),("4H(n+)",B4,4,8)]:
    C=[b["c"] for b in B];adn=cusum(C,-1);aup=cusum(C,1)
    tgT=anchor(B,TOPS,False,W);tgB=anchor(B,BOTS,True,W)
    print(f"\n {nm}: topos {len(tgT)} / fundos {len(tgB)}\n"+HEAD)
    evalsig(B,sorted(adn),tgT,K,"CUSUM-down -> TOPOS")
    evalsig(B,sorted(aup),tgB,K,"CUSUM-up -> FUNDOS")
