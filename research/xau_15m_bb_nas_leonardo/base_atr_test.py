#!/usr/bin/env python3
"""Testa BASE de confirmação 3ATR vs 5ATR vs 8ATR, mantendo R2+R_B, dedup=uma-posição, SL=A(flush-0.1ATR), EXIT=let-run.
Recomputa entrada (cj=1ª barra com high>=low+M*atr), features multi-TF (h1_eff,h4_pos) e R_B no NOVO cj. RAW-causal."""
import json,bisect,datetime as dt,statistics as st
from pathlib import Path
HERE=Path(__file__).parent
PRIM={p.name.split(".")[0].replace("XAUUSD_15m_replay_",""):json.loads(p.read_text()) for p in sorted((HERE/"primitives").glob("*.primitives.json"))}
MRj=json.loads((HERE/"macro_regime_4h.json").read_text())["bars_4h"]
TRANS=[]; prev=None
for b in MRj:
    if b["macro"]!=prev: TRANS.append(b["t_end"]); prev=b["macro"]
def regime_age_h(t):
    k=bisect.bisect_right(TRANS,t)-1; return (t-TRANS[k])/3600 if k>=0 else 0
BUB={k:sorted([json.loads(l) for l in (HERE/"bubbles"/f"{k}.bubbles.jsonl").read_text().splitlines() if l],key=lambda x:x["t"]) for k in PRIM}
SZ={"S":1,"M":2,"L":3}; RCAP=20.0; HMAX=480; PRE=16*900
def htf_bars(s,period):
    g={}
    for b in s:
        kk=b["t"]//period; d=g.setdefault(kk,{"o":b["o"],"h":b["h"],"l":b["l"],"c":b["c"],"t_end":b["t"]+900})
        d["h"]=max(d["h"],b["h"]); d["l"]=min(d["l"],b["l"]); d["c"]=b["c"]; d["t_end"]=b["t"]+900
    return [g[k] for k in sorted(g)]
def ema(v,n):
    if not v: return None
    k=2/(n+1); e=v[0]
    for x in v[1:]: e=x*k+e*(1-k)
    return e
def htf_eff_pos(hb,tc,c15):
    done=[b for b in hb if b["t_end"]<=tc]
    if len(done)<25: return None,None
    closes=[b["c"] for b in done]; highs=[b["h"] for b in done]; lows=[b["l"] for b in done]
    rl=min(lows[-20:]); rh=max(highs[-20:]); pos=(c15-rl)/(rh-rl) if rh>rl else 0.5
    seg=closes[-11:]; net=abs(seg[-1]-seg[0]); path=sum(abs(seg[i]-seg[i-1]) for i in range(1,len(seg))); eff=net/path if path>0 else 0.5
    return eff,pos
def cf_low(s,i):
    L=[b["l"] for b in s]; lo=max(2,i-120); bst=None
    for p in range(lo,i-1):
        if L[p]==min(L[p-2:p+3]): bst=L[p]
    return bst
def letrun(s,cj,entry,sl,atr):
    risk=entry-sl
    if risk<=0: return None,None
    trail=sl; r1=False; ex=None; exi=min(cj+HMAX,len(s)-1); end=exi
    for k in range(cj+1,end+1):
        if s[k]["l"]<=trail: ex=trail; exi=k; break
        if (s[k]["h"]-entry)/risk>=1: r1=True
        if r1:
            sw=cf_low(s,k)
            if sw: trail=max(trail,sw-0.1*atr)
    if ex is None: ex=s[end]["c"]
    return max(-1.0,min(RCAP,(ex-entry)/risk)),exi
def kb(bub,bt,t0,t1,tc):
    a=bisect.bisect_left(bt,t0); b=bisect.bisect_right(bt,t1); return [x for x in bub[a:b] if (x.get("known_at") or x["t"])<=tc]
def RB_feats(s,i,cj,bub,bt):
    tc=s[cj]["t"]; f={}
    v50=[s[b].get("v",0) for b in range(max(0,cj-50),cj+1)]; med=st.median(v50) if v50 else 1
    lb=s[i]; lr=max(lb["h"]-lb["l"],1e-9)
    low_vol_rel=(lb.get("v",0)/med) if med>0 else 1; low_cp=(lb["c"]-lb["l"])/lr
    f["absorption"]=1 if (low_vol_rel>=1.2 and low_cp>=0.66) else 0; f["low_vol_rel"]=low_vol_rel
    t0=s[max(0,i-24)]["t"]; sells=[x for x in kb(bub,bt,t0,tc,tc) if x["side"]=="SELL"]
    half=(t0+tc)//2; old=sum(SZ[x["size"]] for x in sells if x["t"]<half); rec=sum(SZ[x["size"]] for x in sells if x["t"]>=half)
    f["sell_decel"]=(old-rec)/(old+1e-6)
    allb=kb(bub,bt,s[max(0,i-20)]["t"],tc,tc); bb={}
    for x in allb: bb.setdefault(x["t"]//900,{"b":0,"s":0}); bb[x["t"]//900]["b" if x["side"]=="BUY" else "s"]+=SZ[x["size"]]
    bars=sorted(bb); r4b=sum(bb[k]["b"] for k in bars[-4:]) if bars else 0; r4s=sum(bb[k]["s"] for k in bars[-4:]) if bars else 0
    f["buy_sell_ratio4"]=r4b/(r4s+1)
    def skew(lst): L=sum(1 for x in lst if x["size"]=="L"); S=sum(1 for x in lst if x["size"]=="S"); return L/(S+1)
    f["sell_skew_mig"]=skew([x for x in sells if x["t"]<half])-skew([x for x in sells if x["t"]>=half])
    f["regime_age_h"]=regime_age_h(tc)
    return f
def run(Mbase):
    rows=[]
    for k,pr in PRIM.items():
        s=pr["series"]; nn=len(s); L=[x["l"] for x in s]; bub=BUB[k]; bt=[x["t"] for x in bub]
        h1=htf_bars(s,3600); h4=htf_bars(s,14400)
        anch=[]
        for i in range(96,nn-4):
            atr=s[i]["atr"]
            if not atr or L[i]!=min(L[i-4:i+5]): continue
            cj=None
            for q in range(i+1,min(i+HMAX,nn-2)):
                if s[q]["h"]>=s[i]["l"]+Mbase*atr: cj=q; break
            if cj is None or cj+2>=nn: continue
            anch.append((i,cj,atr))
        anch.sort(key=lambda a:a[1]); busy=-10**9
        for i,cj,atr in anch:
            if cj<=busy: continue  # uma-posição
            tc=s[cj]["t"]; c15=s[cj]["c"]
            h1e,_=htf_eff_pos(h1,tc,c15); _,h4p=htf_eff_pos(h4,tc,c15)
            r2_keep=0 if (h1e is not None and h1e<0.20 and h4p is not None and h4p<1.02) else 1
            if not r2_keep: continue
            fb=RB_feats(s,i,cj,bub,bt)
            rb_cut=(fb["absorption"]==1 and round(fb["sell_decel"],2)==0) or (fb["buy_sell_ratio4"]>7 and fb["low_vol_rel"]>1.37) or (fb["regime_age_h"]<=25.2 and fb["sell_skew_mig"]>0)
            if rb_cut: continue
            flush=min(x["l"] for x in s[i:cj+1]); sl=flush-0.1*atr; entry=c15
            R,exi=letrun(s,cj,entry,sl,atr)
            if R is None: continue
            busy=exi; rows.append((s[cj]["t"],R,dt.datetime.utcfromtimestamp(s[cj]["t"]).year))
    rows.sort()
    n=len(rows)
    if not n: return None
    w=sum(1 for _,R,_ in rows if R>0); sm=sum(R for _,R,_ in rows)
    eq=pk=dd=0; stk=mstk=0
    for _,R,_ in rows:
        eq+=R; pk=max(pk,eq); dd=min(dd,eq-pk)
        if R<=0: stk+=1; mstk=max(mstk,stk)
        else: stk=0
    run5=sum(1 for _,R,_ in rows if R>=5); span=(rows[-1][0]-rows[0][0])/(7*86400)
    yr={y:(100*sum(1 for _,R,yy in rows if yy==y and R>0)/max(1,sum(1 for _,R,yy in rows if yy==y))) for y in (2024,2025,2026)}
    return dict(n=n,wr=100*w/n,avgr=sm/n,sumr=sm,dd=dd,streak=mstk,run5=run5,freq=n/span,yr=yr)
print("base | N WR avgR sumR DD streak runners(>=5R) freq/sem | WR ano 24/25/26")
for M in (3,5,8):
    r=run(M)
    if r: print(f" {M}ATR | N={r['n']:>3} WR={r['wr']:.1f}% avgR={r['avgr']:+.2f} sumR={r['sumr']:+.0f} DD={r['dd']:.0f}R streak={r['streak']} runners={r['run5']} freq={r['freq']:.1f} | {r['yr'][2024]:.0f}/{r['yr'][2025]:.0f}/{r['yr'][2026]:.0f}")
