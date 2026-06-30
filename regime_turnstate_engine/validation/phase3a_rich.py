#!/usr/bin/env python3
"""RTSE FASE 3a — features RICAS/DINÂMICAS (as que eu prometi e não rodei): divergência MTF 15M-30M, CUSUM
change-point, gramática de aceitação ordenada (sweep->reclaim->hold), desaceleração (2ª derivada), coil->expand.
Cada uma single + em CONFLUÊNCIA (rica e rica+indicadores). Rótulo LIMPO per-ano-relativo. null + por-ano.
Tudo causal (≤ pivô). M8=gabarito. Determinístico."""
import json,csv,math,statistics as st,random,bisect,datetime as dt
from pathlib import Path
ROOT=Path("/Users/cristrein/tradingview-mcp")
PR=ROOT/"research/xau_15m_bb_nas_leonardo/primitives"; GT=ROOT/"regime_turnstate_engine/ground_truth"
# 15M series + streams
S={};NAS={};SMC={};ZON={}
for f in sorted(PR.glob("*.primitives.json")):
    d=json.loads(f.read_text())
    for b in d["series"]: S[b["t"]]=b
    for e in d.get("nas_events",[]): NAS[e["id"]]=e
    for e in d.get("smc_events",[]): SMC[e["id"]]=e
    for z in d.get("zones",[]): ZON[z["id"]]=z
S=[S[t] for t in sorted(S)];T=[b["t"] for b in S];idx={t:i for i,t in enumerate(T)}
C=[b["c"] for b in S];H=[b["h"] for b in S];Lo=[b["l"] for b in S]
nas=sorted(NAS.values(),key=lambda e:e["t"]);nas_t=[e["t"] for e in nas]
smc=sorted(SMC.values(),key=lambda e:e["t"]);smc_t=[e["t"] for e in smc];zones=list(ZON.values())
# 30M
B30=[json.loads(l) for l in (GT/"raw_30m_ohlc.jsonl").read_text().splitlines()];B30.sort(key=lambda b:b["t"])
t30=[b["t"] for b in B30];c30=[b["c"] for b in B30]
def ema(c,n):
    a=2/(n+1);o=[c[0]]
    for x in c[1:]:o.append(a*x+(1-a)*o[-1])
    return o
e15f=ema(C,9);e15s=ema(C,30);e30f=ema(c30,9);e30s=ema(c30,30)
# CUSUM causal sobre retornos 15M (mu trailing 100), alarmes +/-
ret=[0.0]+[math.log(C[i]/C[i-1]) for i in range(1,len(C))]
# CUSUM PADRÃO sobre retornos PADRONIZADOS (z), k=0.5σ, h=5σ (causal: mu/sigma trailing 100)
alarm_up=set();alarm_dn=set();sp=sn=0.0;kk=0.5;hh=5.0
for i in range(1,len(C)):
    w=ret[max(1,i-100):i]
    mu=st.mean(w) if len(w)>2 else 0.0; sg=st.pstdev(w) if len(w)>2 else 1.0; sg=sg or 1.0
    z=(ret[i]-mu)/sg
    sp=max(0,sp+(z-kk));sn=max(0,sn+(-z-kk))
    if sp>hh: alarm_up.add(i);sp=0.0
    if sn>hh: alarm_dn.add(i);sn=0.0
def atr_at(i,n=14): return sum(max(H[j]-Lo[j],abs(H[j]-C[j-1]),abs(Lo[j]-C[j-1])) for j in range(i-n+1,i+1))/n
def near_alarm(i,aset,W=12): return any((i-w) in aset for w in range(0,W+1))
def ev_in(arr_t,arr,ts,W,dirkey=None,dirval=None,textset=None):
    lo=bisect.bisect_left(arr_t,ts-W);hi=bisect.bisect_right(arr_t,ts)
    for e in arr[lo:hi]:
        if dirkey and e.get(dirkey)!=dirval: continue
        if textset and e.get("text") not in textset: continue
        return True
    return False
m8=[(int(d["t"]),d["kind"]) for d in csv.DictReader(open(ROOT/"research/xau_15m_bb_nas_leonardo/true_reversals_M8.csv"))]
K=96;Wd=12*3600
rows=[]
for t,kind in m8:
    i=idx.get(t)
    if i is None or i<40 or i+K>=len(S): continue
    bot=(kind=="BOT")
    mfe=100*((max(H[i+1:i+K+1])-Lo[i]) if bot else (H[i]-min(Lo[i+1:i+K+1])))/C[i]
    a=atr_at(i)
    # ---- RICAS ----
    # divergência MTF: 15M recupera (close>ema9) enquanto 30M ainda contra
    j=bisect.bisect_right(t30,t)-1
    d30_up = (c30[j]>e30s[j]) if j>=0 else True
    v_div = 1 if ((bot and C[i]>e15f[i] and not d30_up) or ((not bot) and C[i]<e15f[i] and d30_up)) else 0
    # CUSUM alarme da direção da reversão perto do pivô
    v_cusum = 1 if ((bot and near_alarm(i,alarm_up)) or ((not bot) and near_alarm(i,alarm_dn))) else 0
    # gramática sweep->reclaim->hold (causal, ≤ pivô)
    if bot:
        swept = Lo[i]<min(Lo[i-20:i-1]); lev=min(Lo[i-20:i-1])
        v_gram = 1 if (swept and C[i]>lev and C[i-1]>=Lo[i]) else 0
    else:
        swept = H[i]>max(H[i-20:i-1]); lev=max(H[i-20:i-1])
        v_gram = 1 if (swept and C[i]<lev and C[i-1]<=H[i]) else 0
    # desaceleração: velocidade->0 com aceleração contra (2ª derivada)
    v1=(C[i]-C[i-3]);v2=(C[i-3]-C[i-6])
    v_decel = 1 if ((bot and v1>v2 and v1<0) or ((not bot) and v1<v2 and v1>0)) else 0
    # coil->expand: ATR comprimido (<0.8x media20) nas ult. e barra de expansão na direção
    atrm=st.mean([atr_at(x) for x in range(i-20,i)]);comp_recent=any(atr_at(x)<0.8*atrm for x in range(i-6,i))
    expand=(H[i]-Lo[i])>1.4*atrm; dir_ok=(C[i]>C[i-1]) if bot else (C[i]<C[i-1])
    v_coil = 1 if (comp_recent and expand and dir_ok) else 0
    # ---- INDICADORES (reaproveita) ----
    rsi=S[i].get("rsi") or 50
    v_rsi=1 if ((bot and rsi<45) or ((not bot) and rsi>55)) else 0
    v_nas=1 if ev_in(nas_t,nas,t,Wd,"dir",("LONG" if bot else "SHORT")) else 0
    v_smc=1 if ev_in(smc_t,smc,t,Wd,textset={"CHoCH","BOS"}) else 0
    want="DEMAND" if bot else "SUPPLY";px=Lo[i] if bot else H[i];v_ob=0
    for z in zones:
        if z.get("text")==want and z.get("born_t",1e18)<=t and z["low"]<=px<=z["high"]: v_ob=1;break
    rich=v_div+v_cusum+v_gram+v_decel+v_coil
    ind=v_rsi+v_nas+v_smc+v_ob
    rows.append({"t":t,"mfe":mfe,"v_div":v_div,"v_cusum":v_cusum,"v_gram":v_gram,"v_decel":v_decel,"v_coil":v_coil,
                 "v_rsi":v_rsi,"v_nas":v_nas,"v_smc":v_smc,"v_ob":v_ob,"rich":rich,"ind":ind})
def yr(ts): return dt.datetime.utcfromtimestamp(ts).year
medy={y:sorted(r["mfe"] for r in rows if yr(r["t"])==y) for y in set(yr(r["t"]) for r in rows)}
medy={y:v[len(v)//2] for y,v in medy.items()}
for r in rows: r["dur"]=r["mfe"]>=medy[yr(r["t"])]
N=len(rows)
print(f"FASE 3a RICAS — pivôs {N} | rótulo per-ano-relativo | base durável {100*sum(r['dur'] for r in rows)/N:.0f}%")
print("-- CAMADA 1: features RICAS single (taxa de disparo + lift pp) --")
for v in ["v_div","v_cusum","v_gram","v_decel","v_coil"]:
    on=[r for r in rows if r[v]];off=[r for r in rows if not r[v]]
    drn=sum(x["dur"] for x in on)/len(on) if on else 0;dro=sum(x["dur"] for x in off)/len(off) if off else 0
    print(f"  {v:8}: dispara {100*len(on)/N:.0f}% (n{len(on):>3}) | durável voto1 {100*drn:.0f}% vs voto0 {100*dro:.0f}% | lift {100*(drn-dro):+.0f}pp")
# CONFLUÊNCIA RICA (camada 1, primária)
print("-- CONFLUÊNCIA RICA (dose + conf>=2 vs 0 + null + por-ano) --")
for c in range(0,max(r["rich"] for r in rows)+1):
    g=[r for r in rows if r["rich"]==c]
    if g: print(f"  rich={c}: {100*sum(x['dur'] for x in g)/len(g):.0f}% (n{len(g)})")
hi=[r for r in rows if r["rich"]>=2];lo=[r for r in rows if r["rich"]==0]
rl=(sum(x["dur"] for x in hi)/len(hi) if hi else 0)-(sum(x["dur"] for x in lo)/len(lo) if lo else 0)
random.seed(3);labs=[r["dur"] for r in rows];ks=[r["rich"] for r in rows];dd=[]
for _ in range(400):
    random.shuffle(labs);a=[labs[i] for i in range(N) if ks[i]>=2];b=[labs[i] for i in range(N) if ks[i]==0]
    dd.append((sum(a)/len(a) if a else 0)-(sum(b)/len(b) if b else 0))
p=sum(1 for x in dd if abs(x)>=abs(rl))/len(dd)
print(f"  rich>=2({len(hi)}) vs 0({len(lo)}): lift {100*rl:+.0f}pp | null p={p:.3f}")
# CAMADA 2: INDICADORES condicionais ao subconjunto RICH-favorável (não isolados)
print("\n-- CAMADA 2: INDICADORES condicionais (ajudam DEPOIS das ricas?) --")
richfav=[r for r in rows if r["rich"]>=2]
base=sum(r["dur"] for r in richfav)/len(richfav) if richfav else 0
print(f"  subconjunto rich-favorável (rich>=2): n{len(richfav)} | durável base {100*base:.0f}%")
for thr in (1,2):
    add=[r for r in richfav if r["ind"]>=thr];non=[r for r in richfav if r["ind"]<thr]
    da=sum(x["dur"] for x in add)/len(add) if add else 0;dn=sum(x["dur"] for x in non)/len(non) if non else 0
    print(f"    rich-fav & ind>={thr}: {100*da:.0f}% (n{len(add)}) | & ind<{thr}: {100*dn:.0f}% (n{len(non)}) | indicadores add {100*(da-dn):+.0f}pp")
print("\n-- CHECK FINAL dos 2 flickers (null + por-ano) --")
def nulltest(sel_hi,sel_lo,lab):
    hi=[r for r in rows if sel_hi(r)];lo=[r for r in rows if sel_lo(r)]
    if not hi or not lo: print(f"  {lab}: n insuficiente");return
    rl=sum(x["dur"] for x in hi)/len(hi)-sum(x["dur"] for x in lo)/len(lo)
    pool=hi+lo;labs=[r["dur"] for r in pool];random.seed(5);dd=[]
    for _ in range(500):
        random.shuffle(labs);dd.append(sum(labs[:len(hi)])/len(hi)-sum(labs[len(hi):])/len(lo))
    p=sum(1 for x in dd if abs(x)>=abs(rl))/len(dd)
    print(f"  {lab}: lift {100*rl:+.0f}pp (n{len(hi)}/{len(lo)}) null p={p:.3f}")
    for y in sorted(set(yr(r["t"]) for r in rows)):
        h=[r for r in hi if yr(r["t"])==y];l=[r for r in lo if yr(r["t"])==y]
        if h and l: print(f"     {y}: {100*(sum(x['dur'] for x in h)/len(h)-sum(x['dur'] for x in l)/len(l)):+.0f}pp (h{len(h)}/l{len(l)})")
nulltest(lambda r:r["v_coil"]==1, lambda r:r["v_coil"]==0, "v_coil isolado")
nulltest(lambda r:r["rich"]>=2 and r["ind"]>=2, lambda r:r["rich"]>=2 and r["ind"]<2, "ind>=2 dentro de rich>=2")
print("\nVEREDITO: sobrevive só se null p<0.05 E positivo em >=2 anos. Senão = flicker de n pequeno (parede honesta).")
