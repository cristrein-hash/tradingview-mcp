#!/usr/bin/env python3
"""ENGINE 3 — R-outcome das seleções do frontier (Cris 2026-06-28). Determinístico. Pergunta: a seleção (alto recall MF,
muito NONE) PAGA via let-run? vs take-all e vs random mesmo-n. Régua: entry=close cj, SL=min low s[p..cj]-0.1ATR, let-run."""
import json,statistics as st,random
from pathlib import Path
HERE=Path(__file__).parent
PRIM={p.name.split(".")[0].replace("XAUUSD_15m_replay_",""):json.loads(p.read_text()) for p in sorted((HERE/"primitives").glob("*.primitives.json"))}
PRIMK={k[:10]:v for k,v in PRIM.items()}
ROWS=[json.loads(l) for l in (HERE/"entry_candidates_htf.jsonl").read_text().splitlines()]
QJ=json.load(open(HERE/"engine3_qualify.json")); base=QJ["base"]; MFtot=QJ["MFtot"]
aucs=dict(QJ["aucs"]); dirn={f:(1 if a>=.5 else -1) for f,a in aucs.items()}
def isnum(v): return isinstance(v,(int,float)) and not isinstance(v,bool)
def thr(f,q):
    vals=sorted(r[f] for r in ROWS if isnum(r.get(f))); return vals[int(q*len(vals))]
TOP=[f for f,_ in QJ["aucs"][:14] if f!="falling_knife"]; TH={f:(thr(f,0.80) if dirn[f]>0 else thr(f,0.20)) for f in TOP}
G=[r for r in ROWS if r.get("falling_knife",0)==0]
def passes(r,cc):
    for f in cc:
        v=r.get(f)
        if not isnum(v): return False
        if dirn[f]>0 and v<TH[f]: return False
        if dirn[f]<0 and v>TH[f]: return False
    return True
HMAX=480; RCAP=20.0
def cf_low(s,i):
    L=[b["l"] for b in s]; lo=max(2,i-120); bst=None
    for p in range(lo,i-1):
        if L[p]==min(L[p-2:p+3]): bst=L[p]
    return bst
def letrun(s,cj,entry,sl,atr):
    risk=entry-sl
    if risk<=0: return None
    trail=sl; r1=False; ex=None; end=min(cj+HMAX,len(s)-1)
    for k in range(cj+1,end+1):
        if s[k]["l"]<=trail: ex=trail; break
        if (s[k]["h"]-entry)/risk>=1: r1=True
        if r1:
            sw=cf_low(s,k)
            if sw: trail=max(trail,sw-0.1*atr)
    if ex is None: ex=s[end]["c"]
    return max(-1.0,min(RCAP,(ex-entry)/risk))
_cache={}
def R_of(r):
    key=(r["block"],r["cj_t"])
    if key in _cache: return _cache[key]
    pr=PRIMK.get(r["block"]); s=pr["series"]; tmap={b["t"]:i for i,b in enumerate(s)}
    p=tmap.get(r["t"]); cj=tmap.get(r["cj_t"])
    R=None
    if p is not None and cj is not None and cj+2<len(s):
        atr=s[p]["atr"] or s[cj]["atr"]
        if atr:
            entry=s[cj]["c"]; sl=min(x["l"] for x in s[p:cj+1])-0.1*atr; R=letrun(s,cj,entry,sl,atr)
    _cache[key]=R; return R
def metr(sel):
    rs=[R_of(r) for r in sel]; rs=[x for x in rs if x is not None]; n=len(rs)
    if not n: return None
    sm=sum(rs); w=sum(1 for x in rs if x>0)
    eq=pk=dd=0
    for x in rs: eq+=x; pk=max(pk,eq); dd=min(dd,eq-pk)
    return {"n":n,"WR":round(100*w/n,1),"sumR":round(sm,1),"avgR":round(sm/n,3),"maxDD":round(dd,1)}
allm=metr(G); print(f"TAKE-ALL (knife-gated, {len(G)}): {allm}")
random.seed(7)
COMBOS=[tuple(m["combo"]) for m in QJ["frontier"][:6]]
print(f"\n{'combo':<48}{'n':>5}{'mf':>4}{'rec':>5}{'WR':>6}{'sumR':>7}{'avgR':>7}{'DD':>7}{'rand_avgR':>10}")
for cc in COMBOS:
    sel=[r for r in G if passes(r,cc)]; m=metr(sel)
    mf=sum(r["is_monforte"] for r in sel)
    # random same-n null (avgR)
    ravg=[]
    for _ in range(300):
        rs=[R_of(r) for r in random.sample(G,min(len(sel),len(G)))]; rs=[x for x in rs if x is not None]
        if rs: ravg.append(sum(rs)/len(rs))
    rm=st.mean(ravg) if ravg else 0
    print(f"{'+'.join(x[:14] for x in cc):<48}{m['n']:>5}{mf:>4}{round(mf/MFtot,2):>5}{m['WR']:>6}{m['sumR']:>7}{m['avgR']:>7}{m['maxDD']:>7}{rm:>10.3f}")
