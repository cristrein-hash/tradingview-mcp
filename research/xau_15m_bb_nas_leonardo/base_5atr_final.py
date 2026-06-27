#!/usr/bin/env python3
"""Stack final 5ATR re-otimizado + dedup uma-posição (SL=A flush-0.1, let-run). Filtros estruturais (h1_pos/disp4/dist_supply)
do engine de re-otimização. Junta features de dataset_5atr.jsonl; re-simula com onepos. RAW-causal."""
import json,bisect,datetime as dt
from pathlib import Path
HERE=Path(__file__).parent
PRIM={p.name.split(".")[0].replace("XAUUSD_15m_replay_",""):json.loads(p.read_text()) for p in sorted((HERE/"primitives").glob("*.primitives.json"))}
RCAP=20.0; HMAX=480
# join features
F={}
for l in (HERE/"dataset_5atr.jsonl").read_text().splitlines():
    r=json.loads(l); F[(r["block"],r["low_t"])]=r
def cf_low(s,i):
    L=[b["l"] for b in s]; lo=max(2,i-120); bst=None
    for p in range(lo,i-1):
        if L[p]==min(L[p-2:p+3]): bst=L[p]
    return bst
def letrun(s,cj,entry,sl,atr):
    risk=entry-sl
    if risk<=0: return None,None
    trail=sl; r1=False; ex=None; end=min(cj+HMAX,len(s)-1); exi=end
    for k in range(cj+1,end+1):
        if s[k]["l"]<=trail: ex=trail; exi=k; break
        if (s[k]["h"]-entry)/risk>=1: r1=True
        if r1:
            sw=cf_low(s,k)
            if sw: trail=max(trail,sw-0.1*atr)
    if ex is None: ex=s[end]["c"]
    return max(-1.0,min(RCAP,(ex-entry)/risk)),exi
# filtros re-otimizados (KEEP-condition)
FILTERS={
 "sem filtro (5ATR cru)": lambda r: True,
 "S3 (h1_pos>=0.65)": lambda r: r.get("h1_pos") is not None and r["h1_pos"]>=0.65,
 "A2 (h1_pos>=0.65 & disp4>=0.78)": lambda r: r.get("h1_pos") is not None and r["h1_pos"]>=0.65 and r["disp4_atr"]>=0.78,
 "A1 (disp4>=0.78 & dist_supply>=-0.28)": lambda r: r["disp4_atr"]>=0.78 and r["dist_supply_atr"]>=-0.28,
 "F3 (cut dist_supply<=-0.26)": lambda r: r["dist_supply_atr"]>-0.26,
}
def run(filt):
    rows=[]
    for k,pr in PRIM.items():
        s=pr["series"]; tmap={b["t"]:idx for idx,b in enumerate(s)}
        anch=[]
        for (blk,lt),r in F.items():
            if blk!=k[:10]: continue
            i=tmap.get(lt)
            if i is None: continue
            anch.append((i,r["cj"],s[i]["atr"],r,lt))
        anch.sort(key=lambda a:a[1]); busy=-10**9
        for i,cj,atr,r,lt in anch:
            if not atr or cj<=busy: continue
            if not filt(r): continue
            flush=min(x["l"] for x in s[i:cj+1]); entry=s[cj]["c"]; sl=flush-0.1*atr
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
    span=(rows[-1][0]-rows[0][0])/(7*86400)
    yr={y:(100*sum(1 for _,R,yy in rows if yy==y and R>0)/max(1,sum(1 for _,R,yy in rows if yy==y))) for y in (2024,2025,2026)}
    return dict(n=n,wr=100*w/n,avgr=sm/n,sumr=sm,dd=dd,streak=mstk,freq=n/span,yr=yr)
print("STACK 5ATR re-otimizado + dedup uma-posição (SL=A, let-run):")
print("filtro | N WR avgR sumR DD streak freq/sem | WR ano 24/25/26")
for name,filt in FILTERS.items():
    r=run(filt)
    if r: print(f"  {name:<38} N={r['n']:>3} WR={r['wr']:.1f}% avgR={r['avgr']:+.2f} sumR={r['sumr']:+.0f} DD={r['dd']:.0f}R streak={r['streak']} freq={r['freq']:.1f} | {r['yr'][2024]:.0f}/{r['yr'][2025]:.0f}/{r['yr'][2026]:.0f}")
