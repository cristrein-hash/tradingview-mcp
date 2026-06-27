#!/usr/bin/env python3
"""LAB: define DEDUP × SL × EXIT do stack 8ATR+R2+R_B (LONG). Re-simula cada trade variando regras; mede WR/sumR/maxDD/streak
+ por ano. Trades = final stack (r2_keep==1 & not R_B). RAW-causal. 2026-06-27."""
import json,bisect,datetime as dt,statistics as st
from pathlib import Path
HERE=Path(__file__).parent
PRIM={p.name.split(".")[0].replace("XAUUSD_15m_replay_",""):json.loads(p.read_text()) for p in sorted((HERE/"primitives").glob("*.primitives.json"))}
RCAP=20.0; HMAX=480
# anchors do stack final
def R_B(r): return (r["absorption"]==1 and r["sell_decel"]==0) or (r["buy_sell_ratio4"]>7 and r["low_vol_rel"]>1.37) or (r["regime_age_h"]<=25.2 and r["sell_skew_mig"]>0)
FINAL=set()
for l in (HERE/"dataset_r2refine.jsonl").read_text().splitlines():
    r=json.loads(l)
    if r["r2_keep"]==1 and not R_B(r): FINAL.add((r["block"],r["low_t"]))
def cf_low(s,i):
    L=[b["l"] for b in s]; lo=max(2,i-120); bst=None
    for p in range(lo,i-1):
        if L[p]==min(L[p-2:p+3]): bst=L[p]
    return bst
def trade(s,i,cj,atr,sl_mode,exit_mode):
    entry=s[cj]["c"]; flush=min(x["l"] for x in s[i:cj+1])
    sl={"A":flush-0.1*atr,"B":flush-0.5*atr,"C":s[cj]["l"]-0.1*atr,"D":entry-3*atr,"E":(cf_low(s,cj) or flush)-0.1*atr}[sl_mode]
    risk=entry-sl
    if risk<=0: return None
    end=min(cj+HMAX,len(s)-1); trail=sl; r1=False
    tgt={"tgt1":1,"tgt1.5":1.5,"tgt2":2,"tgt3":3}.get(exit_mode)
    part=False; banked=0.0
    for k in range(cj+1,end+1):
        bar=s[k]
        if bar["l"]<=trail:  # stop
            R=banked+ ( (0.5 if part else 1.0)*((trail-entry)/risk) ); return max(-1.0,min(RCAP,R)),k
        up=(bar["h"]-entry)/risk
        if tgt and up>=tgt: return max(-1.0,min(RCAP,tgt)),k   # alvo fixo
        if up>=1: r1=True
        if exit_mode=="partial" and (not part) and up>=1: part=True; banked=0.5; trail=entry  # banca 0.5R, move BE
        if exit_mode in ("letrun","partial") and r1:
            sw=cf_low(s,k)
            if sw: trail=max(trail,sw-0.1*atr)
    cl=s[end]["c"]; R=banked+((0.5 if part else 1.0)*((cl-entry)/risk)); return max(-1.0,min(RCAP,R)),end
# build anchors com i,cj
ANCH=[]
for k,pr in PRIM.items():
    s=pr["series"]; nn=len(s); L=[x["l"] for x in s]; tmap={b["t"]:idx for idx,b in enumerate(s)}
    for (blk,lt) in [x for x in FINAL if x[0]==k[:10]]:
        i=tmap.get(lt)
        if i is None: continue
        atr=s[i]["atr"]
        if not atr: continue
        cj=None
        for q in range(i+1,min(i+HMAX,nn-2)):
            if s[q]["h"]>=s[i]["l"]+8*atr: cj=q; break
        if cj is None or cj+2>=nn: continue
        ANCH.append((k,i,cj,atr,s[cj]["t"],dt.datetime.utcfromtimestamp(s[cj]["t"]).year))
def dedup(anch,mode):
    by={}
    for a in anch: by.setdefault(a[0],[]).append(a)
    out=[]
    for k,lst in by.items():
        s=PRIM[k]["series"]; lst=sorted(lst,key=lambda a:a[2]); last_cj=-10**9; busy=-10**9
        for a in lst:
            i,cj=a[1],a[2]
            if mode=="none": out.append(a)
            elif mode.startswith("gap"):
                g=int(mode[3:])
                if cj-last_cj>=g: out.append(a); last_cj=cj
            elif mode=="onepos":
                if cj>busy: out.append(a)  # busy set após simular (aprox: usa exit do letrun A)
        # onepos precisa de exit; tratado no agg
    return out
def agg(anch,sl,ex,dd):
    # onepos: processa cronologico por bloco, pula enquanto posicao aberta
    rows=[]
    by={}
    for a in anch: by.setdefault(a[0],[]).append(a)
    for k,lst in by.items():
        lst=sorted(lst,key=lambda a:a[2]); last_cj=-10**9; busy=-10**9; s=PRIM[k]["series"]
        for a in lst:
            i,cj,atr,t,yr=a[1],a[2],a[3],a[4],a[5]
            if dd.startswith("gap"):
                g=int(dd[3:])
                if cj-last_cj<g: continue
            elif dd=="onepos":
                if cj<=busy: continue
            r=trade(s,i,cj,atr,sl,ex)
            if r is None: continue
            R,exi=r; rows.append((t,R,yr)); last_cj=cj; busy=exi
    rows.sort()
    n=len(rows);
    if n==0: return None
    w=sum(1 for _,R,_ in rows if R>0); sm=sum(R for _,R,_ in rows)
    eq=pk=dd2=0; stk=mstk=0
    for _,R,_ in rows:
        eq+=R; pk=max(pk,eq); dd2=min(dd2,eq-pk)
        if R<=0: stk+=1; mstk=max(mstk,stk)
        else: stk=0
    yrwr={y:(100*sum(1 for _,R,yy in rows if yy==y and R>0)/max(1,sum(1 for _,R,yy in rows if yy==y))) for y in (2024,2025,2026)}
    return dict(n=n,wr=100*w/n,avgr=sm/n,sumr=sm,dd=dd2,streak=mstk,yrwr=yrwr)
print(f"anchors stack final: {len(ANCH)}")
print("\n=== DEDUP (SL=A flush-0.1, EXIT=letrun) ===")
for dd in ("none","gap8","gap16","gap32","onepos"):
    r=agg(ANCH,"A","letrun",dd)
    if r: print(f"  {dd:>7}: N={r['n']:>4} WR={r['wr']:.1f}% avgR={r['avgr']:+.2f} sumR={r['sumr']:+.0f} DD={r['dd']:.0f}R streak={r['streak']} | ano {r['yrwr'][2024]:.0f}/{r['yrwr'][2025]:.0f}/{r['yrwr'][2026]:.0f}")
print("\n=== SL (dedup=onepos, EXIT=letrun) ===")
for sl in ("A","B","C","D","E"):
    r=agg(ANCH,sl,"letrun","onepos")
    if r: print(f"  SL_{sl}: N={r['n']:>4} WR={r['wr']:.1f}% avgR={r['avgr']:+.2f} sumR={r['sumr']:+.0f} DD={r['dd']:.0f}R streak={r['streak']} | ano {r['yrwr'][2024]:.0f}/{r['yrwr'][2025]:.0f}/{r['yrwr'][2026]:.0f}")
print("\n=== EXIT (dedup=onepos, SL=A) ===")
for ex in ("letrun","tgt1","tgt1.5","tgt2","tgt3","partial"):
    r=agg(ANCH,"A",ex,"onepos")
    if r: print(f"  {ex:>8}: N={r['n']:>4} WR={r['wr']:.1f}% avgR={r['avgr']:+.2f} sumR={r['sumr']:+.0f} DD={r['dd']:.0f}R streak={r['streak']} | ano {r['yrwr'][2024]:.0f}/{r['yrwr'][2025]:.0f}/{r['yrwr'][2026]:.0f}")
