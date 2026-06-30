#!/usr/bin/env python3
"""RTSE Fase 5 — DETECTOR ÚNICO de turn-state combinando os 2 braços validados (Fase 4c):
  braço-FUNDO = CUSUM-up (TF rápido 30M/15M)        -> emite potential-bottom
  braço-TOPO  = expansão-bear × gate-4H-divergência -> emite potential-top   (+ CONFIG2: OR 4H CUSUM-down / 4H exp+div)
Engine roda no relógio rápido (30M, 15M); usa 4H como contexto de confiança (a arquitetura live).
Mede por braço (recall/latência/FP-ano/null base-rate) + COMBINADO + CONFUSÃO (braço dispara perto da virada errada).
Alvos: TOPOS e FUNDOS dos retângulos, ancorados na extrema real. n pequeno=calibração; null por densidade=honesto. Causal."""
import json,csv,math,statistics as st,random,bisect,datetime as dt
from pathlib import Path
ROOT=Path("/Users/cristrein/tradingview-mcp")
REV=ROOT/"my-strategy/research/revalidation";GT=ROOT/"regime_turnstate_engine/ground_truth"
def load(p): b=[json.loads(l) for l in p.read_text().splitlines()];b.sort(key=lambda x:x["t"]);return b
def load15():
    S={}
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
def cusum(c,direction):
    ret=[0.0]+[math.log(c[i]/c[i-1]) for i in range(1,len(c))];al=set();s=0.0
    for i in range(1,len(c)):
        w=ret[max(1,i-100):i];mu=st.mean(w) if len(w)>2 else 0;sg=(st.pstdev(w) if len(w)>2 else 1) or 1
        z=(ret[i]-mu)/sg;s=max(0,s+(direction*z-0.5))
        if s>5: al.add(i);s=0.0
    return al
def rng(b): return b["h"]-b["l"]
TOPS=[];BOTS=[]
for r in csv.DictReader(open(GT/"cris_regime_boxes.csv")):
    if r["role"]=="MACRO" and r["family"]=="BEAR": TOPS.append(int(r["start"]));BOTS.append(int(r["end"]))
    if r["role"]=="MACRO" and r["family"]=="BULL": TOPS.append(int(r["end"]));BOTS.append(int(r["start"]))
    if r["role"]=="PULLBACK" and r["family"]=="BEAR" and r["parent_fam"]=="BULL": TOPS.append(int(r["start"]))
    if r["role"]=="PULLBACK" and r["family"]=="BULL" and r["parent_fam"]=="BEAR": BOTS.append(int(r["start"]))
TOPS=sorted(set(TOPS));BOTS=sorted(set(BOTS))
def anchor(B,ts_list,bot,W):
    T=[b["t"] for b in B];n=len(B);out=set()
    for t in ts_list:
        if not(T[0]<=t<=T[-1]): continue
        j=bisect.bisect_right(T,t)-1
        if not(25<j<n-6): continue
        rk=range(max(25,j-W),min(n-6,j+W));out.add(min(rk,key=lambda k:B[k]["l"]) if bot else max(rk,key=lambda k:B[k]["h"]))
    return sorted(out)
B30=load(GT/"raw_30m_ohlc.jsonl");B15=load15();B4=load(REV/"raw_4h_ohlc.jsonl")
RS={id(B):rsi_series([b["c"] for b in B]) for B in [B30,B15,B4]}
def bear_exp(B):
    C=[b["c"] for b in B];out=[]
    for i in range(25,len(B)):
        if C[i-5]<=C[i-14]: continue
        legvol=st.mean([rng(b) for b in B[i-14:i-4]]) or 1e-9;w=B[i-4:i+1]
        if sum(1 for b in w if b["c"]<b["o"])>=4 and sum(1 for b in w if rng(b)>1.5*legvol)>=2 and C[i]<C[i-5]: out.append(i)
    return out
# 4H contexto
H4=[b["h"] for b in B4];R4=RS[id(B4)];T4=[b["t"] for b in B4]
flag4=[False]*len(B4)
for j in range(25,len(B4)):
    hi=max(range(j-6,j-1),key=lambda k:H4[k]);ph=max(range(j-18,j-7),key=lambda k:H4[k]);flag4[j]=H4[hi]>H4[ph] and R4[hi]<R4[ph]
cd4=cusum([b["c"] for b in B4],-1)
expdiv4=[]
for i in bear_exp(B4):
    hi=max(range(i-8,i-3),key=lambda k:H4[k]);ph=max(range(i-22,i-9),key=lambda k:H4[k])
    if H4[hi]>H4[ph] and R4[hi]<R4[ph]: expdiv4.append(i)
t_divctx=sorted(T4[j] for j in range(len(B4)) if flag4[j])
t_cd4=sorted(T4[j] for j in cd4)
t_expdiv4=sorted(T4[j] for j in expdiv4)
def recent(times,t,hours=24):
    j=bisect.bisect_right(times,t)-1
    return j>=0 and (t-times[j])<=hours*3600
def evalarm(B,fires,targets,K):
    n=len(B);T=[b["t"] for b in B];yrs=(T[-1]-T[0])/(365.25*86400);fs=set(fires);lats=[];hit=0
    for e in targets:
        f=[i for i in range(e,min(n,e+K+1)) if i in fs]
        if f: hit+=1;lats.append(f[0]-e)
    recall=hit/len(targets) if targets else 0
    win=set(e+k for e in targets for k in range(0,K+1));fp=sum(1 for i in fires if i not in win)
    random.seed(7);M=len(fires);pool=list(range(25,n));dd=[]
    for _ in range(1000):
        rf=set(random.sample(pool,M)) if 0<M<=len(pool) else set(pool)
        dd.append(sum(1 for e in targets if any((e+k) in rf for k in range(0,K+1)))/len(targets) if targets else 0)
    p=sum(1 for x in dd if x>=recall)/len(dd)
    return dict(fires=len(fires),recall=recall,lat=(st.median(lats) if lats else None),fpy=fp/yrs if yrs else 0,p=p,hit=hit)
def confusion(B,fires,wrong_targets,K):  # fires que caem em [errado-K .. errado] (dispara perto da virada oposta)
    fs=set(fires);bad=0
    for e in wrong_targets:
        if any(i in fs for i in range(max(0,e-K),min(len(B),e+K+1))): bad+=1
    return bad
def run(name,B,K,W,config2=False):
    tops=anchor(B,TOPS,False,W);bots=anchor(B,BOTS,True,W);T=[b["t"] for b in B]
    bot_fires=sorted(cusum([b["c"] for b in B],1))                          # braço-fundo
    top_fast=[i for i in bear_exp(B) if recent(t_divctx,T[i])]              # braço-topo rápido (gate 4H-div)
    if config2:
        top_extra=[i for i in range(25,len(B)) if recent(t_cd4,T[i],12) or recent(t_expdiv4,T[i],12)]
        top_fires=sorted(set(top_fast)|set(top_extra))
    else:
        top_fires=sorted(set(top_fast))
    eb=evalarm(B,bot_fires,bots,K);et=evalarm(B,top_fires,tops,K)
    conf_b=confusion(B,bot_fires,tops,K);conf_t=confusion(B,top_fires,bots,K)
    yrs=(T[-1]-T[0])/(365.25*86400)
    comb_recall=(eb["hit"]+et["hit"])/(len(bots)+len(tops)) if (bots or tops) else 0
    comb_fpy=eb["fpy"]+et["fpy"]
    tag="CONFIG2 (+4H CUSUM-down/exp+div)" if config2 else "CONFIG1 (fast-only)"
    print(f"\n== {name} {tag} | fundos {len(bots)} topos {len(tops)} | {dt.datetime.utcfromtimestamp(T[0]).date()}..{dt.datetime.utcfromtimestamp(T[-1]).date()} ==")
    print(f"  {'braço':14}{'fires':>6}{'recall':>7}{'lat':>5}{'FP/ano':>8}{'null_p':>8}{'confusão↔oposto':>16}")
    print(f"  {'FUNDO CUSUM-up':14}{eb['fires']:>6}{eb['recall']:>7.2f}{str(eb['lat']):>5}{eb['fpy']:>8.0f}{eb['p']:>8.3f}{conf_b:>10}/{len(tops)}")
    print(f"  {'TOPO exp×div':14}{et['fires']:>6}{et['recall']:>7.2f}{str(et['lat']):>5}{et['fpy']:>8.0f}{et['p']:>8.3f}{conf_t:>10}/{len(bots)}")
    print(f"  COMBINADO: recall {comb_recall:.2f} ({eb['hit']+et['hit']}/{len(bots)+len(tops)}) | FP/ano total {comb_fpy:.0f}")
for nm,B,K,W in [("30M",B30,8,12),("15M",B15,16,24)]:
    run(nm,B,K,W,False);run(nm,B,K,W,True)
# ---------- CONFIG3: detector ÚNICO MULTI-RELÓGIO (fundo=CUSUM-up TF rápido | topo=4H nativo exp+div ∪ CUSUM-down) ----------
def run_native(botB,botK,botW,botname):
    Tb=[b["t"] for b in botB];bots=anchor(botB,BOTS,True,botW)
    bot_fires=sorted(cusum([b["c"] for b in botB],1))
    eb=evalarm(botB,bot_fires,bots,botK)
    tops4=anchor(B4,TOPS,False,8);top_fires=sorted(set(expdiv4)|set(cd4))
    et=evalarm(B4,top_fires,tops4,4)
    conf_b=confusion(botB,bot_fires,anchor(botB,TOPS,False,botW),botK)
    conf_t=confusion(B4,top_fires,anchor(B4,BOTS,True,8),4)
    # combinado restrito ao período comum (cobertura do TF rápido de fundos)
    c0,c1=Tb[0],Tb[1-1] if False else Tb[-1]
    tops4_c=[e for e in tops4 if c0<=B4[e]["t"]<=c1]
    th=sum(1 for e in tops4_c if any(i in set(top_fires) for i in range(e,min(len(B4),e+5))))
    nt=len(tops4_c)
    comb=(eb['hit']+th)/(len(bots)+nt) if (bots or tops4_c) else 0
    print(f"\n== CONFIG3 MULTI-RELÓGIO: fundo={botname}(CUSUM-up) | topo=4H(exp+div ∪ CUSUM-down) ==")
    print(f"  {'braço':22}{'fires':>6}{'recall':>7}{'lat':>5}{'FP/ano':>8}{'null_p':>8}{'confusão':>10}")
    print(f"  {'FUNDO '+botname+' CUSUM-up':22}{eb['fires']:>6}{eb['recall']:>7.2f}{str(eb['lat']):>5}{eb['fpy']:>8.0f}{eb['p']:>8.3f}{conf_b:>7}/{len(anchor(botB,TOPS,False,botW))}")
    print(f"  {'TOPO 4H exp+div∪CUSUM':22}{et['fires']:>6}{et['recall']:>7.2f}{str(et['lat']):>5}{et['fpy']:>8.0f}{et['p']:>8.3f}{conf_t:>7}/{len(anchor(B4,BOTS,True,8))}")
    print(f"  COMBINADO (período comum {dt.datetime.utcfromtimestamp(c0).date()}..): recall {comb:.2f} ({eb['hit']+th}/{len(bots)+nt}) | FP/ano {eb['fpy']+et['fpy']:.0f}")
run_native(B30,8,12,"30M")
run_native(B15,16,24,"15M")
