#!/usr/bin/env python3
"""PÓS-ENTRADA reader — separar RUNNER de STOP DEPOIS que o trade começa (não no gatilho).
Premissa (Cris): selecionar runner NO ENTRY é parede provada; o edge mora no COMPORTAMENTO pós-entrada
(aceitação real vs absorção nas primeiras velas, continuação estrutural). Cauda (poucos runners) = DESENHO, não defeito.
Universo: o MESMO sweep-gated não-condicionado da v2 (causal, RAW-only). Para cada trade simula o let-run e captura, em
janelas w∈{4,8,12} velas após a entrada, features CAUSAIS conhecidas no bar ei+w (nada do futuro):
  mfeR/maeR (excursões em R) · dispR (deslocamento líquido no close) · up_closes · absorb (pavio-contra médio =
  absorção) · accel (expansão de range) · nas_dir (sinal NAS na direção pós-entrada = continuação).
Mede, ENTRE os trades AINDA VIVOS no bar ei+w, se cada feature separa: runner-rate (R_final>=3) e avgR_final.
Scoring let-run auditado (loser=-1R). 2026-06-26."""
import json, bisect, datetime as dt, statistics as st
from pathlib import Path
HERE=Path(__file__).parent
PRIM={p.name.split(".")[0].replace("XAUUSD_15m_replay_",""):json.loads(p.read_text()) for p in (HERE/"primitives").glob("*.primitives.json")}
M=json.loads((HERE/"macro_regime_4h.json").read_text())["bars_4h"]; MEND=[b["t_end"] for b in M]
def macro_at(t): k=bisect.bisect_right(MEND,t)-1; return M[k]["macro"] if k>=0 else "WARMUP"
K,LB,EPS,MINR,RCAP,HMAX=2,50,0.05,0.5,15.0,480
WINS=[4,8,12]; RUNNER=3.0
def sw_low(L,i):
    for p in range(i-K,max(K,i-LB)-1,-1):
        if L[p]==min(L[p-K:p+K+1]): return L[p],p
    return None,None
def sw_high(H,i):
    for p in range(i-K,max(K,i-LB)-1,-1):
        if H[p]==max(H[p-K:p+K+1]): return H[p],p
    return None,None
def cf_low(s,i):
    L=[b["l"] for b in s]; lo=max(K,i-120); bst=None
    for p in range(lo,i-K+1):
        if L[p]==min(L[p-K:p+K+1]): bst=L[p]
    return bst
def cf_high(s,i):
    H=[b["h"] for b in s]; lo=max(K,i-120); bst=None
    for p in range(lo,i-K+1):
        if H[p]==max(H[p-K:p+K+1]): bst=H[p]
    return bst
def gate(s,i,long,atr,nas_ts):
    t=s[i]["t"]; w0=max(0,i-30)
    ndir=sum(1 for x in nas_ts if s[w0]["t"]<=x<=t); disp=abs(s[i]["c"]-s[w0]["c"])/atr
    anti=ndir>=6 and disp<1.5
    bos=fail=0
    for j in range(max(40,i-40),i+1):
        rh=max(x["h"] for x in s[j-20:j]); rl=min(x["l"] for x in s[j-20:j])
        if s[j]["c"]>rh:
            bos+=1
            if any(s[k]["c"]<rh for k in range(j+1,min(j+5,i+1))): fail+=1
        elif s[j]["c"]<rl:
            bos+=1
            if any(s[k]["c"]>rl for k in range(j+1,min(j+5,i+1))): fail+=1
    cbfs=bos>=3 and fail/bos>0.6
    day=t//86400; tp=lambda x:(x["h"]+x["l"]+x["c"])/3
    cur=[tp(x) for x in s[max(0,i-96):i+1] if x["t"]//86400==day]; prev=[tp(x) for x in s[max(0,i-192):i+1] if x["t"]//86400==day-1]
    vmig=False
    if cur and prev:
        vt=st.mean(cur); vp=st.mean(prev); vmig=(vt<vp*0.999) if long else (vt>vp*1.001)
    acc=False
    if i>=3:
        if long: acc=s[i]["c"]<s[i-1]["c"]<s[i-2]["c"] and (s[i]["h"]-s[i]["l"])>(s[i-1]["h"]-s[i-1]["l"])>(s[i-2]["h"]-s[i-2]["l"])
        else: acc=s[i]["c"]>s[i-1]["c"]>s[i-2]["c"] and (s[i]["h"]-s[i]["l"])>(s[i-1]["h"]-s[i-1]["l"])>(s[i-2]["h"]-s[i-2]["l"])
    return anti or cbfs or vmig or acc
def sim(s,ei,entry,sl0,long,atr,nas_in_dir):
    """let-run + captura features por janela. Retorna (finalR, held, feats{w:dict|None})."""
    risk=max((entry-sl0) if long else (sl0-entry),MINR*atr)
    if risk<=0: return None
    sl0=(entry-risk) if long else (entry+risk); trail=sl0; r1=False; held=False; stop_off=None
    end=min(ei+HMAX,len(s)-1); mfe=0.0; mae=0.0; up=0; absorb_sum=0.0; rngs=[]
    snaps={w:None for w in WINS}
    for k in range(1,end-ei+1):
        i=ei+k; bar=s[i]; rng=max(bar["h"]-bar["l"],1e-9); rngs.append(rng)
        fav=((bar["h"]-entry) if long else (entry-bar["l"]))/risk
        adv=((entry-bar["l"]) if long else (bar["h"]-entry))/risk
        mfe=max(mfe,fav); mae=max(mae,adv)
        if bar["c"]>s[i-1]["c"] if long else bar["c"]<s[i-1]["c"]: up+=1
        wick=((bar["h"]-max(bar["o"],bar["c"])) if long else (min(bar["o"],bar["c"])-bar["l"]))/rng  # pavio-CONTRA = absorção
        absorb_sum+=wick
        stopped_now=(bar["l"]<=trail) if long else (bar["h"]>=trail)
        if k in snaps:
            disp=((bar["c"]-entry) if long else (entry-bar["c"]))/risk
            accel=(st.mean(rngs[-2:])/st.mean(rngs[:2])) if len(rngs)>=4 else 1.0
            snaps[k]={"alive":(stop_off is None),"mfeR":mfe,"maeR":mae,"dispR":disp,"up":up,
                      "absorb":absorb_sum/k,"accel":accel,"nas_dir":nas_in_dir(s[i]["t"])}
        if stop_off is None and stopped_now: stop_off=k
        if stop_off is not None and all(snaps[w] is not None for w in WINS): break
        if long:
            if bar["l"]<=trail and stop_off==k: pass
            if (bar["h"]-entry)/risk>=1: r1=True; held=True
            if r1:
                sw=cf_low(s,i)
                if sw: trail=max(trail,sw-0.1*atr)
        else:
            if (entry-bar["l"])/risk>=1: r1=True; held=True
            if r1:
                sh=cf_high(s,i)
                if sh: trail=min(trail,sh+0.1*atr)
    # R final canônico (mesma engine v2), independente das features
    R=outcome_final(s,ei,entry,(entry-risk) if long else (entry+risk),long,atr,risk)
    return R,held,snaps
def outcome_final(s,ei,entry,sl0,long,atr,risk):
    trail=sl0; r1=False; ex=None; end=min(ei+HMAX,len(s)-1)
    for i in range(ei+1,end+1):
        bar=s[i]
        if long:
            if bar["l"]<=trail: ex=trail; break
            if (bar["h"]-entry)/risk>=1: r1=True
            if r1:
                sw=cf_low(s,i)
                if sw: trail=max(trail,sw-0.1*atr)
        else:
            if bar["h"]>=trail: ex=trail; break
            if (entry-bar["l"])/risk>=1: r1=True
            if r1:
                sh=cf_high(s,i)
                if sh: trail=min(trail,sh+0.1*atr)
    if ex is None: ex=s[end]["c"]
    R=((ex-entry) if long else (entry-ex))/risk
    return max(-1.0,min(RCAP,R))
def build():
    U=[]
    for b,pr in PRIM.items():
        s=pr["series"]; n=len(s); L=[x["l"] for x in s]; H=[x["h"] for x in s]
        nas_ts=sorted([e["t"] for e in pr["nas_events"] if e["t"]])
        nas_ev=sorted([e for e in pr["nas_events"] if e.get("t") and e.get("dir")],key=lambda e:e["t"])
        last={"L":-999,"S":-999}
        for i in range(LB+K,n-2):
            t=s[i]["t"]; atr=s[i]["atr"]
            if not atr: continue
            mac=macro_at(t); yr=dt.datetime.utcfromtimestamp(t).year
            for long in (True,False):
                if long and mac!="BULL": continue
                if (not long) and mac!="BEAR": continue
                if gate(s,i,long,atr,nas_ts): continue
                liq,lp=(sw_low(L,i) if long else sw_high(H,i))
                if liq is None: continue
                v_sweep=(L[i]<liq-EPS*atr and s[i]["c"]>liq) if long else (H[i]>liq+EPS*atr and s[i]["c"]<liq)
                if not v_sweep: continue
                key="L" if long else "S"
                if i-last[key]<8: continue
                ei=i+1
                if ei+2>=n: continue
                entry=s[ei]["c"]; sl0=(L[i]-0.1*atr) if long else (H[i]+0.1*atr)
                entry_t=s[ei]["t"]
                def nas_in_dir(upto_t,_d=long):
                    for ev in nas_ev:
                        if ev["t"]<=entry_t: continue
                        if ev["t"]>upto_t: break
                        if (ev["dir"]=="LONG")==_d: return 1
                    return 0
                r=sim(s,ei,entry,sl0,long,atr,nas_in_dir)
                if r is None: continue
                R,held,snaps=r
                tr={"block":b,"t":t,"yr":yr,"dir":key,"R":R,"runner":R>=RUNNER,"snaps":snaps}
                U.append(tr); last[key]=i
    return U
def rr(v): return 100*sum(1 for x in v if x["runner"])/len(v) if v else 0
def ar(v): return sum(x["R"] for x in v)/len(v) if v else 0
def quint(alive,feat,nb=4):
    vs=sorted([x for x in alive if x["snaps"] and x["s"][feat] is not None],key=lambda x:x["s"][feat])
    m=len(vs)//nb; print(f"     {feat:>8} Q(baixo→alto): "+" | ".join(
        f"Q{q+1} n={len(vs[q*m:(q+1)*m] if q<nb-1 else vs[q*m:]):>2} run%={rr(vs[q*m:(q+1)*m] if q<nb-1 else vs[q*m:]):>3.0f} avgR={ar(vs[q*m:(q+1)*m] if q<nb-1 else vs[q*m:]):+.2f}"
        for q in range(nb)))
U=build()
half=sum(1 for x in U if abs(x["R"]+0.5)<1e-9)
print(f"[AUDIT] n={len(U)} | −0.5R suspeitos={half} | base runner%(R>=3)={rr(U):.0f}% avgR={ar(U):+.2f} | runners={sum(1 for x in U if x['runner'])}")
FEATS=["mfeR","maeR","dispR","up","absorb","accel","nas_dir"]
for w in WINS:
    alive=[{**x,"s":x["snaps"][w]} for x in U if x["snaps"][w] and x["snaps"][w]["alive"]]
    print(f"\n=== janela {w} velas pós-entrada — VIVOS={len(alive)} (de {len(U)}) | runner%={rr(alive):.0f}% avgR_final={ar(alive):+.2f} ===")
    for f in FEATS:
        quint(alive,f,4)

def curve(trs):
    ts=sorted(trs,key=lambda x:x["t"]); eq=pk=dd=0; stk=mstk=0
    for x in ts:
        eq+=x["Rv"]; pk=max(pk,eq); dd=min(dd,eq-pk)
        if x["Rv"]<=0: stk+=1; mstk=max(mstk,stk)
        else: stk=0
    return eq,dd,mstk
def manage_test(W,thr):
    """Regra causal: se VIVO no bar W e dispR_W<=thr → sai no close do bar W (realiza dispR_W). Senão → R_final let-run.
    Preserva runner (alto disp não é cortado). Compara vs baseline let-run puro."""
    out=[]
    for x in U:
        snap=x["snaps"][W]
        if snap and snap["alive"] and snap["dispR"]<=thr:
            Rv=max(-1.0,min(RCAP,snap["dispR"]))   # saída no close do bar W
            cut=True
        else:
            Rv=x["R"]; cut=False
        out.append({**x,"Rv":Rv,"cut":cut})
    n=len(out); sm=sum(x["Rv"] for x in out); w=100*sum(1 for x in out if x["Rv"]>0)/n
    runr=sum(1 for x in out if x["runner"]); runr_kept=sum(1 for x in out if x["runner"] and not x["cut"])
    eq,dd,mstk=curve(out); ncut=sum(1 for x in out if x["cut"])
    byb={};
    for x in out: byb.setdefault(x["block"][:16],[]).append(x)
    drop=set(sorted(byb,key=lambda bb:sum(z["Rv"] for z in byb[bb]),reverse=True)[:2]); rem=sum(x["Rv"] for x in out if x["block"][:16] not in drop)
    yrs=" ".join(f"{y}:{sum(x['Rv'] for x in out if x['yr']==y):+.0f}R" for y in (2024,2025,2026) if any(x['yr']==y for x in out))
    print(f"  W={W} thr={thr:+.1f}: sumR={sm:+.1f} avgR={sm/n:+.2f} WR={w:.0f}% DD={dd:.0f}R streak={mstk} | cortados={ncut} | runners {runr_kept}/{runr} preservados | leave-top2→{rem:+.0f} | {yrs}")
print("\n========== TESTE DE GESTÃO: cortar cedo quem NÃO andou (preservando runner) ==========")
bsm=sum(x["R"] for x in U); beq,bdd,bmstk=0,0,0
ts=sorted(U,key=lambda x:x["t"]); eq=pk=dd=0; stk=mstk=0
for x in ts:
    eq+=x["R"]; pk=max(pk,eq); dd=min(dd,eq-pk)
    if x["R"]<=0: stk+=1; mstk=max(mstk,stk)
    else: stk=0
bwr=100*sum(1 for x in U if x["R"]>0)/len(U)
print(f"  BASELINE let-run puro: sumR={bsm:+.1f} avgR={bsm/len(U):+.2f} WR={bwr:.0f}% DD={dd:.0f}R streak={mstk} | runners={sum(1 for x in U if x['runner'])}")
for W in (4,8,12):
    for thr in (0.0,0.5):
        manage_test(W,thr)
