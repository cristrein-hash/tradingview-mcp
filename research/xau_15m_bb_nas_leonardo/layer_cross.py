#!/usr/bin/env python3
"""CAMADAS anteriores não-cruzadas (RAW, sem SVP-indisponível). Universo sweep-gated (mesmo da base validada).
Por trade (let-run R): rsi_headroom, accepted@8 (dispR@8>=1, pós-entrada validada), NAS-cluster (nº NAS-LONG na janela),
macro_pos (regime + macro_drop). Cruza: RSI-folgado × accept@8 (2 validadas); NAS-cluster próprio; macroleg próprio.
known_at em bubbles não usado aqui (NAS não repinta da mesma forma; usa nas_events). RAW-causal. 2026-06-26."""
import json,bisect,datetime as dt,statistics as st
from pathlib import Path
HERE=Path(__file__).parent
PRIM={p.name.split(".")[0].replace("XAUUSD_15m_replay_",""):json.loads(p.read_text()) for p in sorted((HERE/"primitives").glob("*.primitives.json"))}
M=json.loads((HERE/"macro_regime_4h.json").read_text())["bars_4h"]; MEND=[b["t_end"] for b in M]
def macro_at(t): k=bisect.bisect_right(MEND,t)-1; return M[k]["macro"] if k>=0 else "WARMUP"
K,LB,EPS,MINR,RCAP,HMAX=2,50,0.05,0.5,15.0,480
def sw_low(L,i):
    for p in range(i-K,max(K,i-LB)-1,-1):
        if L[p]==min(L[p-K:p+K+1]): return L[p]
    return None
def cf_low(s,i):
    L=[b["l"] for b in s]; lo=max(K,i-120); bst=None
    for p in range(lo,i-K+1):
        if L[p]==min(L[p-K:p+K+1]): bst=L[p]
    return bst
def gate(s,i,atr,nas_ts):
    t=s[i]["t"]; w0=max(0,i-30)
    ndir=sum(1 for x in nas_ts if s[w0]["t"]<=x<=t); disp=abs(s[i]["c"]-s[w0]["c"])/atr
    if ndir>=6 and disp<1.5: return True
    bos=fail=0
    for j in range(max(40,i-40),i+1):
        rh=max(x["h"] for x in s[j-20:j]); rl=min(x["l"] for x in s[j-20:j])
        if s[j]["c"]>rh:
            bos+=1
            if any(s[k]["c"]<rh for k in range(j+1,min(j+5,i+1))): fail+=1
    if bos>=3 and fail/bos>0.6: return True
    return False
def outcome(s,ei,entry,sl0,atr):
    risk=max(entry-sl0,MINR*atr)
    if risk<=0: return None,None,None
    sl0=entry-risk; trail=sl0; r1=False; ex=None; end=min(ei+HMAX,len(s)-1); disp8=None
    for i in range(ei+1,end+1):
        if i-ei==8: disp8=(s[i]["c"]-entry)/risk
        if s[i]["l"]<=trail: ex=trail; break
        if (s[i]["h"]-entry)/risk>=1: r1=True
        if r1:
            sw=cf_low(s,i)
            if sw: trail=max(trail,sw-0.1*atr)
    if ex is None: ex=s[end]["c"]
    return max(-1.0,min(RCAP,(ex-entry)/risk)), disp8, risk
U=[]
for b,pr in PRIM.items():
    s=pr["series"]; n=len(s); L=[x["l"] for x in s]
    nas=sorted([e for e in pr["nas_events"] if e.get("t") and e.get("dir")],key=lambda e:e["t"])
    nas_ts=sorted([e["t"] for e in nas])
    nlt=[e["t"] for e in nas]
    last=-999
    for i in range(LB+K,n-2):
        t=s[i]["t"]; atr=s[i]["atr"]
        if not atr: continue
        if macro_at(t)!="BULL": continue
        if gate(s,i,atr,nas_ts): continue
        liq=sw_low(L,i)
        if liq is None: continue
        if not (L[i]<liq-EPS*atr and s[i]["c"]>liq): continue
        if i-last<8: continue
        ei=i+1
        if ei+2>=n: continue
        entry=s[ei]["c"]; sl0=L[i]-0.1*atr
        R,disp8,risk=outcome(s,ei,entry,sl0,atr)
        if R is None: continue
        rsi=s[i].get("rsi") or 50; rsi_head=max(0,min(1,(70-rsi)/40))
        a16=bisect.bisect_left(nlt,t-16*900); b16=bisect.bisect_right(nlt,t)
        nas_cl=sum(1 for e in nas[a16:b16] if e["dir"]=="LONG")
        lo=max(0,i-192); macro_drop=(max(x["h"] for x in s[lo:i+1])-s[i]["l"])/atr
        U.append({"R":R,"acc8":(disp8 is not None and disp8>=1),"rsi_head":rsi_head,"nas_cl":nas_cl,"md":macro_drop,
                  "yr":dt.datetime.utcfromtimestamp(t).year}); last=i
def rep(v,lab):
    if len(v)<15: print(f"  {lab}: n={len(v)} (poucos)"); return
    n=len(v); sm=sum(x["R"] for x in v); wr=100*sum(1 for x in v if x["R"]>0)/n; acc=100*sum(1 for x in v if x["acc8"])/n
    print(f"  {lab}: n={n} WR={wr:.0f}% avgR={sm/n:+.2f} sumR={sm:+.0f} accept@8={acc:.0f}%")
print(f"universo sweep BULL: n={len(U)}")
print("\n[1] RSI-FOLGADO (entry quality) — tercis de headroom:")
us=sorted(U,key=lambda x:x["rsi_head"]); m=len(us)//3
rep(us[:m],"RSI baixo(esticado)"); rep(us[m:2*m],"RSI médio"); rep(us[2*m:],"RSI folgado")
print("\n[2] NAS-CLUSTER próprio (nº NAS-LONG janela 16b):")
rep([x for x in U if x["nas_cl"]==0],"NAS-LONG=0"); rep([x for x in U if x["nas_cl"]==1],"NAS-LONG=1"); rep([x for x in U if x["nas_cl"]>=2],"NAS-LONG>=2 (cluster)")
print("\n[3] POSIÇÃO MACROLEG própria (macro_drop = profundidade da perna):")
rep([x for x in U if x["md"]<5],"raso(<5ATR)"); rep([x for x in U if 5<=x["md"]<10],"médio(5-10)"); rep([x for x in U if x["md"]>=10],"profundo(>=10)")
print("\n[4] CRUZAMENTO 2 validadas: RSI-folgado × accept@8:")
fol=[x for x in U if x["rsi_head"]>=0.5]
rep([x for x in fol if x["acc8"]],"RSI-folgado & aceito@8"); rep([x for x in fol if not x["acc8"]],"RSI-folgado & NÃO-aceito@8")
rep([x for x in U if x["rsi_head"]<0.5 and x["acc8"]],"RSI-esticado & aceito@8")
print("\n  (accept@8 é pós-entrada já validado; aqui mostra se entrada RSI-folgada ACEITA mais e rende mais)")
