#!/usr/bin/env python3
"""ENGINE v2 — GATE GLOBAL de ambiente (cut-streak), volume-free/estrutural. Aplica 4 vetos à base existente e mede:
o gate corta streak (≤5?) + eleva WR (40-50?) a 1-5/sem SEM cortar runner? + leave-one-block-out. Vetos (causal, bars≤i):
 anti_sequence_veto = whipsaw (muitos NAS ambas-dir em 30b + pouco deslocamento líquido);
 cbfs = follow-through falhando (taxa de breakouts de range que re-fecham dentro >0.6 em 40b);
 value_migration = valor intradiário (typical price médio do dia UTC) migrando CONTRA a direção (proxy POC, volume-free);
 acceleration = entrar contra perna AINDA acelerando (3 closes contra + ranges crescentes).
Saída: GERAL com/sem gate + por bloco + winners-cut. Verified 2026-06-26."""
import csv, json, statistics as st
from pathlib import Path
HERE = Path(__file__).parent
PRIM = {p.name.split(".")[0].replace("XAUUSD_15m_replay_", ""): json.loads(p.read_text())
        for p in (HERE / "primitives").glob("*.primitives.json")}
SER = {b: pr["series"] for b, pr in PRIM.items()}; TID = {b: {x["t"]: i for i, x in enumerate(s)} for b, s in SER.items()}
NASb = {b: sorted([e["t"] for e in pr["nas_events"] if e["t"]]) for b, pr in PRIM.items()}
K, HMAX, MIN_RISK_ATR, R_CAP, RUNNER = 2, 480, 0.5, 15.0, 3.0
def conf_low(s, i):
    L=[b["l"] for b in s]; lo=max(K,i-120); best=None
    for p in range(lo,i-K+1):
        if L[p]==min(L[p-K:p+K+1]): best=L[p]
    return best
def outcome(s, ei, entry, sl0, long, atr):
    struct=(entry-sl0) if long else (sl0-entry)
    if struct<=0: return None
    risk=max(struct,MIN_RISK_ATR*atr); sl0=(entry-risk) if long else (entry+risk)
    trail=sl0; r1=False; mfe=0.0; ex=None; end=min(ei+HMAX,len(s)-1)
    for i in range(ei+1,end+1):
        bar=s[i]
        if long:
            mfe=max(mfe,(bar["h"]-entry)/risk)
            if bar["l"]<=trail: ex=trail; break
            if (bar["h"]-entry)/risk>=1: r1=True
            if r1:
                sw=conf_low(s,i)
                if sw: trail=max(trail,sw-0.1*atr)
        else:
            mfe=max(mfe,(entry-bar["l"])/risk)
            if bar["h"]>=trail: ex=trail; break
            if (entry-bar["l"])/risk>=1: r1=True
            if r1:
                # trailing simétrico (swing high)
                H=[x["h"] for x in s]; lo=max(K,i-120); sh=None
                for p in range(lo,i-K+1):
                    if H[p]==max(H[p-K:p+K+1]): sh=H[p]
                if sh: trail=min(trail,sh+0.1*atr)
    if ex is None: ex=s[end]["c"]
    R=((ex-entry) if long else (entry-ex))/risk
    return max(-1.0,min(R_CAP,R)), mfe
def gate(s, i, long, atr, nas_ts):
    t=s[i]["t"]
    # anti_sequence_veto: whipsaw
    w0=max(0,i-30); ndir=sum(1 for x in nas_ts if s[w0]["t"]<=x<=t); disp=abs(s[i]["c"]-s[w0]["c"])/atr
    anti=ndir>=6 and disp<1.5
    # cbfs: follow-through falhando em 40b
    bos=0; fail=0
    for j in range(max(40,i-40),i+1):
        rh=max(x["h"] for x in s[j-20:j]); rl=min(x["l"] for x in s[j-20:j])
        if s[j]["c"]>rh:
            bos+=1
            if any(s[k]["c"]<rh for k in range(j+1,min(j+5,i+1))): fail+=1
        elif s[j]["c"]<rl:
            bos+=1
            if any(s[k]["c"]>rl for k in range(j+1,min(j+5,i+1))): fail+=1
    cbfs=bos>=3 and fail/bos>0.6
    # value_migration: typical médio do dia UTC vs dia anterior (proxy POC volume-free)
    day=t//86400; tp=lambda x:(x["h"]+x["l"]+x["c"])/3
    cur=[tp(x) for x in s[max(0,i-96):i+1] if x["t"]//86400==day]
    prev=[tp(x) for x in s[max(0,i-192):i+1] if x["t"]//86400==day-1]
    vmig=False
    if cur and prev:
        vt=st.mean(cur); vp=st.mean(prev)
        vmig=(vt<vp*0.999) if long else (vt>vp*1.001)
    # acceleration_veto: entrar contra perna acelerando
    acc=False
    if i>=3:
        if long: acc=s[i]["c"]<s[i-1]["c"]<s[i-2]["c"] and (s[i]["h"]-s[i]["l"])>(s[i-1]["h"]-s[i-1]["l"])>(s[i-2]["h"]-s[i-2]["l"])
        else: acc=s[i]["c"]>s[i-1]["c"]>s[i-2]["c"] and (s[i]["h"]-s[i]["l"])>(s[i-1]["h"]-s[i-1]["l"])>(s[i-2]["h"]-s[i-2]["l"])
    veto = anti or cbfs or vmig or acc
    return veto, {"anti":anti,"cbfs":cbfs,"vmig":vmig,"acc":acc}
def build():
    out=[]
    for r in csv.DictReader(open(HERE/"candidates_annotated.csv")):
        if r["setup_vs_macro"]!="with_macro": continue
        b=r["block"]; s=SER.get(b); ei=TID.get(b,{}).get(int(r["entry_t"]))
        if s is None or ei is None or ei+2>=len(s): continue
        j=TID[b].get(int(r["nas_t"]));
        if j is None: continue
        entry=float(r["entry_close"]); zlo=float(r["zone_low"]); zhi=float(r["zone_high"]); zwa=float(r["zone_width_atr"])
        atr=(zhi-zlo)/zwa if zwa>0 else None
        if not atr: continue
        long=r["dir"]=="LONG"; sl0=(zlo-0.1*atr) if long else (zhi+0.1*atr)
        oc=outcome(s,ei,entry,sl0,long,atr)
        if not oc: continue
        R,mfe=oc; veto,vd=gate(s,j,long,atr,NASb[b])
        out.append({"block":b,"t":int(r["entry_t"]),"dir":r["dir"],"R":R,"mfe":mfe,"win":R>0,"runner":mfe>=RUNNER,"veto":veto,**vd})
    return out
def agg(trs,label):
    if not trs: print(f"  [{label}] vazio"); return
    n=len(trs);w=sum(1 for t in trs if t["win"]);sm=sum(t["R"] for t in trs);run=sum(1 for t in trs if t["runner"])
    ts=sorted(trs,key=lambda t:t["t"]);eq=0;pk=0;dd=0;stk=0;mstk=0
    for t in ts:
        eq+=t["R"];pk=max(pk,eq);dd=min(dd,eq-pk)
        if t["R"]<=0:stk+=1;mstk=max(mstk,stk)
        else:stk=0
    span=(ts[-1]["t"]-ts[0]["t"])/(7*86400) or 1
    print(f"  [{label}] n={n} WR={100*w/n:.0f}% avgR={sm/n:+.2f} sumR={sm:+.1f} run={run}({100*run/n:.0f}%) DD={dd:.1f}R streakL={mstk} freq={n/span:.2f}/sem")
c=build()
print("=== ENGINE v2 — GATE GLOBAL sobre base with_macro (meta aliviada WR40-50/streak≤5/1-5sem/DD-livre) ===")
agg(c,"SEM gate (base)")
kept=[t for t in c if not t["veto"]]; cutt=[t for t in c if t["veto"]]
agg(kept,"COM gate")
print(f"\n  gate cortou {len(cutt)} trades: losers={sum(1 for t in cutt if not t['win'])} winners={sum(1 for t in cutt if t['win'])} RUNNERS={sum(1 for t in cutt if t['runner'])}")
print(f"  vetos isolados: anti={sum(1 for t in c if t['anti'])} cbfs={sum(1 for t in c if t['cbfs'])} vmig={sum(1 for t in c if t['vmig'])} acc={sum(1 for t in c if t['acc'])}")
print("\n COM gate por bloco (leave-one-block-out implícito):")
for b in sorted(set(t["block"] for t in kept)): agg([t for t in kept if t["block"]==b],b[:21])
byb={};
for t in kept: byb.setdefault(t["block"],[]).append(sum(x["R"] for x in [t]))
print("  blocos COM gate net+ :", sum(1 for b in set(t['block'] for t in kept) if sum(x['R'] for x in kept if x['block']==b)>0),"/",len(set(t['block'] for t in kept)))
