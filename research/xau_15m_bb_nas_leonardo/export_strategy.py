#!/usr/bin/env python3
"""Exporta os trades da ESTRATÉGIA (universo sweep-gated macro+global-gate, let-run, add 1u na aceitação bar W=8 dispR>=1.0)
com PREÇOS (entry/SL/saída/P_add) p/ plotagem canônica + reporta N nos 2 anos do RAW. Causal RAW-only. 2026-06-26."""
import json,bisect,datetime as dt,statistics as st,csv
from pathlib import Path
HERE=Path(__file__).parent
PRIM={p.name.split(".")[0].replace("XAUUSD_15m_replay_",""):json.loads(p.read_text()) for p in (HERE/"primitives").glob("*.primitives.json")}
M=json.loads((HERE/"macro_regime_4h.json").read_text())["bars_4h"]; MEND=[b["t_end"] for b in M]
def macro_at(t): k=bisect.bisect_right(MEND,t)-1; return M[k]["macro"] if k>=0 else "WARMUP"
K,LB,EPS,MINR,RCAP,HMAX,W,THR=2,50,0.05,0.5,15.0,480,8,1.0
def sw_low(L,i):
    for p in range(i-K,max(K,i-LB)-1,-1):
        if L[p]==min(L[p-K:p+K+1]): return L[p]
    return None
def sw_high(H,i):
    for p in range(i-K,max(K,i-LB)-1,-1):
        if H[p]==max(H[p-K:p+K+1]): return H[p]
    return None
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
def cap(r): return max(-1.0,min(RCAP,r))
def addcap(r): return min(RCAP,r)
def simulate(s,ei,entry,long,atr,R0):
    sl0=(entry-R0) if long else (entry+R0); trail=sl0; r1=False; added=False; P_add=None; add_t=None; add_stop=None
    end=min(ei+HMAX,len(s)-1); ex=None; lows=[]; highs=[]
    for k in range(1,end-ei+1):
        i=ei+k; bar=s[i]; lows.append(bar["l"]); highs.append(bar["h"])
        if long and bar["l"]<=trail: ex=trail; break
        if (not long) and bar["h"]>=trail: ex=trail; break
        fav=((bar["h"]-entry) if long else (entry-bar["l"]))/R0
        if fav>=1: r1=True
        if r1:
            if long:
                sw=cf_low(s,i)
                if sw: trail=max(trail,sw-0.1*atr)
            else:
                sh=cf_high(s,i)
                if sh: trail=min(trail,sh+0.1*atr)
        if k==W and not added:
            dispR=((bar["c"]-entry) if long else (entry-bar["c"]))/R0
            if dispR>=THR:
                added=True; P_add=bar["c"]; add_t=bar["t"]
                if long: trail=max(trail,min(lows)-0.1*atr)
                else: trail=min(trail,max(highs)+0.1*atr)
                add_stop=trail
    if ex is None: ex=s[end]["c"]
    base_R=cap(((ex-entry) if long else (entry-ex))/R0); add_R=addcap(((ex-P_add) if long else (P_add-ex))/R0) if added else 0.0
    return sl0,ex,P_add,added,base_R,add_R,add_t,add_stop
rows=[]
for b,pr in PRIM.items():
    s=pr["series"]; n=len(s); L=[x["l"] for x in s]; H=[x["h"] for x in s]; nas_ts=sorted([e["t"] for e in pr["nas_events"] if e["t"]])
    last={"L":-999,"S":-999}
    for i in range(LB+K,n-2):
        t=s[i]["t"]; atr=s[i]["atr"]
        if not atr: continue
        mac=macro_at(t); yr=dt.datetime.utcfromtimestamp(t).year
        for long in (True,False):
            if long and mac!="BULL": continue
            if (not long) and mac!="BEAR": continue
            if gate(s,i,long,atr,nas_ts): continue
            liq=(sw_low(L,i) if long else sw_high(H,i))
            if liq is None: continue
            v_sweep=(L[i]<liq-EPS*atr and s[i]["c"]>liq) if long else (H[i]>liq+EPS*atr and s[i]["c"]<liq)
            if not v_sweep: continue
            key="L" if long else "S"
            if i-last[key]<8: continue
            ei=i+1
            if ei+2>=n: continue
            entry=s[ei]["c"]; sl0_struct=(L[i]-0.1*atr) if long else (H[i]+0.1*atr)
            R0=max((entry-sl0_struct) if long else (sl0_struct-entry),MINR*atr)
            if R0<=0: continue
            sl0,ex,P_add,added,base_R,add_R,add_t,add_stop=simulate(s,ei,entry,long,atr,R0)
            rows.append({"entry_t":s[ei]["t"],"dir":"LONG" if long else "SHORT","entry":round(entry,2),"stop":round(sl0,2),
                         "exit":round(ex,2),"P_add":round(P_add,2) if P_add else "","add_t":add_t or "","add_stop":round(add_stop,2) if add_stop else "",
                         "added":int(added),"base_R":round(base_R,2),"add_R":round(add_R,2),"tot_R":round(base_R+add_R,2),"yr":yr}); last[key]=i
rows.sort(key=lambda r:r["entry_t"])
with open(HERE/"strategy_trades.csv","w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
n=len(rows); adds=sum(r["added"] for r in rows); span=(rows[-1]["entry_t"]-rows[0]["entry_t"])/(7*86400)
print(f"N total trades = {n}  | adds(2 unidades) = {adds}  | freq = {n/span:.2f}/sem  ({span:.0f} semanas, 2 anos RAW)")
for yr in (2024,2025,2026):
    yv=[r for r in rows if r["yr"]==yr]
    if yv: print(f"  {yr}: trades={len(yv):>3}  adds={sum(r['added'] for r in yv):>2}  LONG={sum(1 for r in yv if r['dir']=='LONG'):>3} SHORT={sum(1 for r in yv if r['dir']=='SHORT'):>2}  sumR_total={sum(r['tot_R'] for r in yv):+.0f}")
print(f"  → CSV: strategy_trades.csv ({n} linhas) pronto p/ plotagem canônica")