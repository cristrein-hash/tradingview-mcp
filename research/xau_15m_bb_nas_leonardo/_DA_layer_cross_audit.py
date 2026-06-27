#!/usr/bin/env python3
"""DA audit of layer_cross.py claims [1][2][3][4].
Rebuilds the SAME universe (sweep-gated BULL longs, let-run R) and tests:
 T1: is [4] circular? P(R>0|acc8) regardless of RSI; does RSI add anything beyond acc8?
 T2: [1] RSI-folgado lift real & per-year stable? monotonic? Bonferroni.
 T3: [2] NAS>=2 thin — per-year breakdown.
 T4: [3] deep-macroleg negative — per-year.
 T5: look-ahead checks on rsi_head, nas_cl, macro_at.
2026-06-26."""
import json,bisect,datetime as dt,statistics as st,math
from pathlib import Path
from collections import defaultdict
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
                  "disp8":disp8,"yr":dt.datetime.utcfromtimestamp(t).year}); last=i

def wr(v): return 100*sum(1 for x in v if x["R"]>0)/len(v) if v else 0
def avg(v): return sum(x["R"] for x in v)/len(v) if v else 0
def line(lab,v): print(f"  {lab}: n={len(v):4d} WR={wr(v):5.1f}% avgR={avg(v):+.2f} sumR={sum(x['R'] for x in v):+.0f}")

print(f"=== UNIVERSE n={len(U)} ===")

print("\n##### T1: IS [4] CIRCULAR? (acc8 = post-entry disp@8>=1, let-run trails up after +1R) #####")
acc=[x for x in U if x["acc8"]]; nacc=[x for x in U if not x["acc8"]]
line("acc8=TRUE  (any RSI)",acc); line("acc8=FALSE (any RSI)",nacc)
print(f"  P(R>0 | acc8) = {wr(acc):.1f}%   P(R>0 | not acc8) = {wr(nacc):.1f}%")
# within acc8, does RSI tercile change anything?
us=sorted(U,key=lambda x:x["rsi_head"]); m=len(us)//3
lowr=set(id(x) for x in us[:m]); hir=set(id(x) for x in us[2*m:])
print("  WITHIN acc8, by RSI tercile:")
line("   acc8 & RSI-esticado",[x for x in acc if id(x) in lowr])
line("   acc8 & RSI-folgado",[x for x in acc if id(x) in hir])
# how many acc8 have R>0 mechanically?
neg_acc=[x for x in acc if x["R"]<=0]
print(f"  acc8 trades with R<=0: {len(neg_acc)}/{len(acc)} (these stopped AFTER reaching +1R then trailed out)")

print("\n##### T2: [1] RSI tercile — per-year + Bonferroni #####")
ter={"esticado":us[:m],"medio":us[m:2*m],"folgado":us[2*m:]}
for k,v in ter.items(): line(k,v)
# per-year WR for esticado vs folgado
print("  per-year WR (esticado | folgado):")
yrs=sorted(set(x["yr"] for x in U))
for y in yrs:
    e=[x for x in ter["esticado"] if x["yr"]==y]; f=[x for x in ter["folgado"] if x["yr"]==y]
    print(f"    {y}: esticado n={len(e):3d} WR={wr(e):4.0f}% | folgado n={len(f):3d} WR={wr(f):4.0f}%")
# 2-proportion z-test esticado vs folgado WR
def ztest(a,b):
    n1,n2=len(a),len(b); x1=sum(1 for z in a if z["R"]>0); x2=sum(1 for z in b if z["R"]>0)
    p=(x1+x2)/(n1+n2); se=math.sqrt(p*(1-p)*(1/n1+1/n2))
    if se==0: return 0,1
    z=(x2/n2-x1/n1)/se; from math import erf
    pv=2*(1-0.5*(1+erf(abs(z)/math.sqrt(2)))); return z,pv
z,pv=ztest(ter["esticado"],ter["folgado"])
print(f"  esticado vs folgado WR: z={z:.2f} p={pv:.3f}  Bonferroni(x12)={min(1,pv*12):.3f}")
print(f"  avgR monotonic? esticado {avg(ter['esticado']):+.2f} medio {avg(ter['medio']):+.2f} folgado {avg(ter['folgado']):+.2f}")

print("\n##### T3: [2] NAS>=2 (n26) per-year #####")
n2=[x for x in U if x["nas_cl"]>=2]
line("NAS>=2 total",n2)
for y in yrs:
    v=[x for x in n2 if x["yr"]==y]
    if v: line(f" {y}",v)
# remove top winner
n2s=sorted(n2,key=lambda x:-x["R"]);
print(f"  top-2 R values: {[round(x['R'],1) for x in n2s[:3]]}")
line("NAS>=2 minus top-1",n2s[1:]); line("NAS>=2 minus top-2",n2s[2:])

print("\n##### T4: [3] deep-macroleg (>=10, n58) per-year #####")
dp=[x for x in U if x["md"]>=10]
line("deep>=10 total",dp)
for y in yrs:
    v=[x for x in dp if x["yr"]==y]
    if v: line(f" {y}",v)

print("\n##### T5: LOOK-AHEAD CHECKS #####")
print("  rsi_head: rsi=s[i].rsi, entry=s[i+1].c. RSI at signal bar i, entry next bar -> OK (causal, no future).")
print("  nas_cl: window [t-16*900, t], events e['t']<=t -> OK (no future events).")
print("  macro_at(t): bisect_right(MEND,t)-1 picks last 4H bar with t_end<=t -> OK if t_end is bar CLOSE.")
mend_sample=M[:2]
print(f"  macro bars_4h sample t_end: {[b['t_end'] for b in mend_sample]} ; macro vals {[b['macro'] for b in mend_sample]}")
# check t_end is close not open: spacing
sp=MEND[1]-MEND[0] if len(MEND)>1 else 0
print(f"  4H t_end spacing = {sp}s (expect 14400 for 4H)")
