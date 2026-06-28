#!/usr/bin/env python3
"""ENGINE 7 (Cris 2026-06-28): entradas LONG em FUNDO dentro de regime BULL (detector v2). Determinístico, causal.
Confluência de FUNDO: SELL-bubble + NAS LONG + RSI oversold(<40/<30) + OB demand. PROIBIÇÃO de TOPO: BUY-bubble dom /
NAS SHORT / RSI alto / OB supply (evita entrada tardia). Alvo 50-75 melhores entradas. Mede N/WR/R/DD + por-ano."""
import json,bisect,statistics as st,itertools
from pathlib import Path
HERE=Path(__file__).parent
PRIM={p.name.split(".")[0].replace("XAUUSD_15m_replay_",""):json.loads(p.read_text()) for p in sorted((HERE/"primitives").glob("*.primitives.json"))}
PRIMK={k[:10]:v for k,v in PRIM.items()}
ROWS=[json.loads(l) for l in (HERE/"entry_candidates_htf.jsonl").read_text().splitlines()]
# ---- regime diário (detector v2 calibrado), full 2 anos, causal ----
allbars={}
for pr in PRIM.values():
    for b in pr["series"]: allbars.setdefault(b["t"],b)
T15=sorted(allbars)
days={}
for t in T15:
    b=allbars[t]; k=t//86400
    g=days.setdefault(k,{"h":b["h"],"l":b["l"],"c":b["c"]})
    g["h"]=max(g["h"],b["h"]); g["l"]=min(g["l"],b["l"]); g["c"]=b["c"]
DK=sorted(days); DC=[days[k]["c"] for k in DK]; DH=[days[k]["h"] for k in DK]; DL=[days[k]["l"] for k in DK]
TR=[0.0]+[max(DH[i]-DL[i],abs(DH[i]-DC[i-1]),abs(DL[i]-DC[i-1])) for i in range(1,len(DK))]
def atrd(i,n=14): a=TR[max(1,i-n+1):i+1]; return sum(a)/len(a) if a else 1.0
def ema_at(i,n):
    c=DC[max(0,i-3*n):i+1]; k=2/(n+1); e=c[0]
    for v in c[1:]: e=v*k+e*(1-k)
    return e
E50=[ema_at(i,50) for i in range(len(DK))]; E100=[ema_at(i,100) for i in range(len(DK))]
N,eff_thr,slope_thr,R_thr,K,Kbear=15,0.30,0.20,2.0,5,5  # config v2
def raw(i):
    if i<max(2*N,40): return "RANGE"
    a=atrd(i) or 1.0; slope=(E50[i]-E50[i-5])/a
    seg=DC[i-N:i+1]; net=seg[-1]-seg[0]; path=sum(abs(seg[j]-seg[j-1]) for j in range(1,len(seg))); eff=abs(net)/path if path>0 else 0
    hh=max(DH[i-N:i]); ll=min(DL[i-N:i]); pos=(DC[i]-ll)/(hh-ll) if hh>ll else .5; slope100=(E100[i]-E100[i-10])/a
    tu=eff>=eff_thr and slope>slope_thr; td=eff>=eff_thr and slope<-slope_thr
    sb=E50[i]>E100[i] and slope100>0; se=E50[i]<E100[i] and slope100<0
    cont=eff<eff_thr and 0.15<=pos<=0.85 and abs(slope)<slope_thr
    peak=max(DH[i-30:i+1]); retreat=(peak-DC[i])/a; lh=max(DH[i-N:i])<max(DH[i-2*N:i-N]); bef=DC[i]<E50[i] and (E50[i]-E50[i-5])<0; bl=DC[i]<min(DL[i-N:i-2])
    if (bl and bef) or (retreat>=R_thr and lh and bef) or td or (se and pos<0.6 and not cont): return "BEAR"
    if tu or (sb and pos>0.55 and not cont): return "BULL"
    return "RANGE"
rawlab=[raw(i) for i in range(len(DK))]; reg=[]; cur="RANGE"; pend=None; pn=0
for v in rawlab:
    if v==cur: pend=None; pn=0
    elif v==pend: pn+=1
    else: pend=v; pn=1
    need=Kbear if pend=="BEAR" else K
    if pn>=need: cur=pend; pend=None; pn=0
    reg.append(cur)
DAYREG={DK[i]:reg[i] for i in range(len(DK))}
def regime_at(t): return DAYREG.get(t//86400,"RANGE")
# ---- R let-run + nas_short/in_supply causais por candidato ----
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
def f(r,k,d=None):
    v=r.get(k); return v if isinstance(v,(int,float)) and not isinstance(v,bool) else d
for r in ROWS:
    pr=PRIMK.get(r["block"]); s=pr["series"]; tmap={b["t"]:i for i,b in enumerate(s)}
    p=tmap.get(r["t"]); cj=tmap.get(r["cj_t"]); r["R"]=None
    r["reg"]=regime_at(r["cj_t"])
    if p is None or cj is None or cj+2>=len(s): continue
    atr=s[p]["atr"] or s[cj]["atr"]
    if atr:
        entry=s[cj]["c"]; sl=min(x["l"] for x in s[p:cj+1])-0.1*atr; r["R"]=letrun(s,cj,entry,sl,atr)
    # nas_short_16 + in_supply 15M (causal)
    nas=sorted([e for e in pr["nas_events"] if e.get("t") and e.get("dir")],key=lambda e:e["t"]); nt=[e["t"] for e in nas]
    a=bisect.bisect_left(nt,s[max(0,p-16)]["t"]); b=bisect.bisect_right(nt,r["cj_t"])
    r["nas_short_16"]=sum(1 for e in nas[a:b] if e["dir"]=="SHORT")
    zs=[z for z in pr.get("zones",[]) if "SUPPLY" in str(z.get("text","")).upper()]
    lo=s[p]["l"]
    r["in_supply"]=1 if any(z.get("born_t",1e18)<=r["cj_t"] and z["low"]-0.3*atr<=lo<=z["high"]+0.3*atr for z in zs) else 0
G=[r for r in ROWS if r["R"] is not None]
print(f"universo R-ok={len(G)} | BULL={sum(1 for r in G if r['reg']=='BULL')} BEAR={sum(1 for r in G if r['reg']=='BEAR')} RANGE={sum(1 for r in G if r['reg']=='RANGE')}")
# ---- vozes de FUNDO + proibição de TOPO ----
def top_block(r):
    return (f(r,"buy_bub_w",0)>f(r,"sell_bub_w",0) and f(r,"buy_bub_w",0)>=4) or f(r,"nas_short_16",0)>=2 or f(r,"rsi_low",0)>70 or f(r,"in_supply",0)==1
def bottom_voices(r,rsi_thr):
    return sum([f(r,"sell_bub_w",0)>=2, f(r,"nas_long_16",0)>=1, f(r,"rsi_low",50)<rsi_thr, f(r,"in_demand",0)==1])
def metr(sel):
    n=len(sel)
    if not n: return None
    rs=[r["R"] for r in sel]; sm=sum(rs); w=sum(1 for x in rs if x>0); mf=sum(r["is_monforte"] for r in sel)
    eq=pk=dd=0
    for x in rs: eq+=x; pk=max(pk,eq); dd=min(dd,eq-pk)
    py={y:round(sum(r["R"] for r in sel if r["yr"]==y),1) for y in (2024,2025,2026)}
    return n,round(100*w/n,1),round(sm,1),round(sm/n,3),round(dd,1),mf,py
def show(tag,sel):
    m=metr(sel)
    if not m: print(f"{tag:<40} (n<1)"); return
    n,wr,sm,avg,dd,mf,py=m
    flag=" <==50-75" if 50<=n<=75 else (" <100" if n<100 else "")
    print(f"{tag:<40}{n:>4}{wr:>6}{sm:>7}{avg:>7}{dd:>7}{mf:>4}  {py[2024]}/{py[2025]}/{py[2026]}{flag}")
hdr=f"{'config':<40}{'N':>4}{'WR':>6}{'sumR':>7}{'avgR':>7}{'DD':>7}{'MF':>4}  yr24/25/26"
print("\n=== BULL — fundo + confluência ==="); print(hdr)
for rsi_thr in (40,30):
    for k in (2,3,4):
        show(f"BULL+notop+RSI<{rsi_thr} vozes>={k}",[r for r in G if r["reg"]=="BULL" and not top_block(r) and bottom_voices(r,rsi_thr)>=k])
print("\n=== RANGE — compra-baixa em reteste de zona (in_demand + legpos baixo) ==="); print(hdr)
for rsi_thr in (40,30):
    for k in (2,3):
        show(f"RANGE+notop+demand+lp<.4 RSI<{rsi_thr} v>={k}",
             [r for r in G if r["reg"]=="RANGE" and not top_block(r) and f(r,"in_demand",0)==1 and f(r,"legpos90",1)<0.4 and bottom_voices(r,rsi_thr)>=k])
print("\n=== BULL+RANGE combinado (mesmos filtros por regime) ===")
for rsi_thr in (40,30):
    for k in (2,3):
        sel=[r for r in G if ((r["reg"]=="BULL" and bottom_voices(r,rsi_thr)>=k) or (r["reg"]=="RANGE" and f(r,"in_demand",0)==1 and f(r,"legpos90",1)<0.4 and bottom_voices(r,rsi_thr)>=k)) and not top_block(r)]
        show(f"BULL+RANGE RSI<{rsi_thr} v>={k}",sel)
