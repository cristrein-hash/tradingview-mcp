#!/usr/bin/env python3
"""Plota SUBSTRATO #4 = swept-sempre + h1_pos>=0.44 + pos_recent20>=q0.25 + rsi_cj>=q0.2 (thresholds da pool B 2024-26).
Janela ago2025 -> fim BULL (29-jan-2026). Limpa chart antes. Canônico long_position+#N verde/vermelho. Requer pause flag."""
import sys,json,csv,datetime as dt
from pathlib import Path
HERE=Path(__file__).parent
PRIM={p.name.split(".")[0].replace("XAUUSD_15m_replay_",""):json.loads(p.read_text()) for p in sorted((HERE/"primitives").glob("*.primitives.json"))}
PRIMK={k[:10]:v for k,v in PRIM.items()}
allbars={}
for pr in PRIM.values():
    for b in pr["series"]: allbars.setdefault(b["t"],b)
days={}
for t in sorted(allbars):
    b=allbars[t]; k=t//86400; g=days.setdefault(k,{"h":b["h"],"l":b["l"],"c":b["c"]})
    g["h"]=max(g["h"],b["h"]); g["l"]=min(g["l"],b["l"]); g["c"]=b["c"]
DK=sorted(days); DC=[days[k]["c"] for k in DK]; DH=[days[k]["h"] for k in DK]; DL=[days[k]["l"] for k in DK]
TR=[0.0]+[max(DH[i]-DL[i],abs(DH[i]-DC[i-1]),abs(DL[i]-DC[i-1])) for i in range(1,len(DK))]
def atrd(i,n=14): a=TR[max(1,i-n+1):i+1]; return sum(a)/len(a) if a else 1.0
def ema_at(i,n):
    c=DC[max(0,i-3*n):i+1]; k=2/(n+1); e=c[0]
    for v in c[1:]: e=v*k+e*(1-k)
    return e
E50=[ema_at(i,50) for i in range(len(DK))]; E100=[ema_at(i,100) for i in range(len(DK))]
N,eff_thr,slope_thr,R_thr,K,Kbear=15,0.30,0.20,2.0,5,5
def raw(i):
    if i<max(2*N,40): return "RANGE"
    a=atrd(i) or 1.0; slope=(E50[i]-E50[i-5])/a
    seg=DC[i-N:i+1]; net=seg[-1]-seg[0]; path=sum(abs(seg[j]-seg[j-1]) for j in range(1,len(seg))); eff=abs(net)/path if path>0 else 0
    hh=max(DH[i-N:i]); ll=min(DL[i-N:i]); pos=(DC[i]-ll)/(hh-ll) if hh>ll else .5; s100=(E100[i]-E100[i-10])/a
    tu=eff>=eff_thr and slope>slope_thr; td=eff>=eff_thr and slope<-slope_thr
    sb=E50[i]>E100[i] and s100>0; se=E50[i]<E100[i] and s100<0
    cont=eff<eff_thr and 0.15<=pos<=0.85 and abs(slope)<slope_thr
    peak=max(DH[i-30:i+1]); retreat=(peak-DC[i])/a; lh=max(DH[i-N:i])<max(DH[i-2*N:i-N]); bef=DC[i]<E50[i] and (E50[i]-E50[i-5])<0; bl=DC[i]<min(DL[i-N:i-2])
    if (bl and bef) or (retreat>=R_thr and lh and bef) or td or (se and pos<0.6 and not cont): return "BEAR"
    if tu or (sb and pos>0.55 and not cont): return "BULL"
    return "RANGE"
rl=[raw(i) for i in range(len(DK))]; reg=[]; cur="RANGE"; pend=None; pn=0
for v in rl:
    if v==cur: pend=None; pn=0
    elif v==pend: pn+=1
    else: pend=v; pn=1
    if pn>=(Kbear if pend=="BEAR" else K): cur=pend; pend=None; pn=0
    reg.append(cur)
DAYREG={DK[i]:reg[i] for i in range(len(DK))}
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
def knife_v2(r):
    a=f(r,"buy_bub_w",0)>=8 and f(r,"buy_bub_w",0)>f(r,"sell_bub_w",0)
    b=(f(r,"downleg_eff",0)>=0.45 and f(r,"atr_regime",1)>1.2 and f(r,"reclaim_atr",9)<1.0 and f(r,"up_closes_pc",9)<=1
       and (f(r,"sell_bub_w",0)<8 or f(r,"htf_demand_any",0)==0 or f(r,"swept_prior_low",0)==0))
    return a or b
ROWS=[json.loads(l) for l in (HERE/"entry_candidates_htf.jsonl").read_text().splitlines()]
B=[]
for r in ROWS:
    if f(r,"swept_prior_low",0)!=1: continue
    pr=PRIMK.get(r["block"]); s=pr["series"]; tmap={b["t"]:i for i,b in enumerate(s)}
    p=tmap.get(r["t"]); cj=tmap.get(r["cj_t"])
    if p is None or cj is None or cj+2>=len(s) or knife_v2(r): continue
    if DAYREG.get(r["cj_t"]//86400,"RANGE")=="BEAR": continue
    if not (f(r,"h4n_trend",0)==1 and f(r,"h1n_trend",0)==1): continue
    if f(r,"h1_pos",0.5)<0.44: continue                      # h1_pos>=0.44
    atr=s[p]["atr"] or s[cj]["atr"]
    if not atr: continue
    entry=s[cj]["c"]; sl=min(x["l"] for x in s[p:cj+1])-0.1*atr; R=letrun(s,cj,entry,sl,atr)
    if R is None: continue
    lo20=min(x["l"] for x in s[max(0,cj-19):cj+1]); hi20=max(x["h"] for x in s[max(0,cj-19):cj+1]); cs=f(r,"clean_sky_atr",99)
    pos20=(entry-lo20)/((hi20-lo20) or atr); rsicj=s[cj].get("rsi") or 50
    B.append({"cj_t":r["cj_t"],"entry":entry,"sl":sl,"R":R,"pos20":pos20,"rsi":rsicj,"cs":cs})
def quant(vals,q): vs=sorted(vals); return vs[min(len(vs)-1,max(0,int(q*len(vs))))]
qpos=quant([x["pos20"] for x in B],0.25); qrsi=quant([x["rsi"] for x in B],0.2)
S4all=[x for x in B if x["pos20"]>=qpos and x["rsi"]>=qrsi]; qcs=quant([x["cs"] for x in S4all],0.25); S4=[x for x in S4all if x["cs"]>=qcs]
LO=dt.datetime(2025,8,1).timestamp(); HI=dt.datetime(2026,1,29).timestamp()
sel=sorted([x for x in S4 if LO<=x["cj_t"]<HI],key=lambda z:z["cj_t"])
out=[]
for i,x in enumerate(sel,1):
    ex=x["entry"]+x["R"]*(x["entry"]-x["sl"])
    out.append({"num":i,"cj_t":x["cj_t"],"date":dt.datetime.utcfromtimestamp(x["cj_t"]).strftime("%Y-%m-%d %H:%M"),
                "entry":round(x["entry"],2),"sl":round(x["sl"],2),"exit":round(ex,2),"R":round(x["R"],3),"win":x["R"]>0})
with open(HERE/"cleansky_window.csv","w",newline="") as fh:
    w=csv.DictWriter(fh,fieldnames=["num","cj_t","date","entry","sl","exit","R","win"]); w.writeheader(); w.writerows(out)
sm=sum(x["R"] for x in out); wn=sum(1 for x in out if x["win"])
print(f"SUBSTRATO#4 (qpos={qpos:.3f},qrsi={qrsi:.1f}) janela ago2025->29jan2026: N={len(out)} WR={100*wn/len(out):.1f}% sumR={sm:.1f} | full-S4 N={len(S4)}")
REPO=Path("/Users/cristrein/tradingview-mcp"); sys.path.insert(0,str(REPO/"alert-bridge"))
from draw_xau_4h_trades import MCPClient, price_to_ticks_offset
PAUSE=Path("/tmp/claude_recheck.paused"); SYMBOL,TF,BAR_S,WIDTH="PEPPERSTONE:XAUUSD","15",900,8; GREEN,RED="#1a8917","#cc0000"
if not PAUSE.exists(): print("ERRO: pause flag ausente"); sys.exit(1)
c=MCPClient(); c.start(); drawn=0; fails=[]; chart={}
try:
    st=c.call_tool("chart_get_state")
    if st.get("symbol")!=SYMBOL: c.call_tool("chart_set_symbol",{"symbol":SYMBOL})
    if str(st.get("resolution"))!=TF: c.call_tool("chart_set_timeframe",{"timeframe":TF})
    chk=c.call_tool("chart_get_state"); sym,res=chk.get("symbol"),str(chk.get("resolution"))
    if not (str(sym).endswith("XAUUSD") and res==TF): c.stop(); print(json.dumps({"HARD_STOP":f"{sym}/{res}"})); sys.exit(1)
    # HISTORICAL_ONE_SHOT / DO_NOT_USE_AS_CANONICAL — width original mantida (Cris 2026-07-02).
    # AUTORIDADE: docs/project_authority/PLOTTING_CANON_MASTER.md. draw_clear gated (default NO_CLEAR, MASTER §11).
    if "--authorized-clear" not in sys.argv:
        c.stop(); print(json.dumps({"ABORT": "DRAW_CLEAR_BLOCKED — HISTORICAL_ONE_SHOT; requer --authorized-clear (autorizacao explicita Cris; PLOTTING_CANON_MASTER §11)"})); sys.exit(1)
    c.call_tool("draw_clear"); dl0=c.call_tool("draw_list"); chart["before"]=dl0.get("count") if isinstance(dl0,dict) else None
    for x in out:
        entry,sl,ex,t,win,num=x["entry"],x["sl"],x["exit"],x["cj_t"],x["win"],x["num"]
        risk=abs(entry-sl); ly=entry+0.5*risk; col=GREEN if win else RED
        r1=c.call_tool("draw_shape",{"shape":"long_position","point":{"time":t,"price":entry},
            "point2":{"time":t+WIDTH*BAR_S,"price":ex},
            "overrides":json.dumps({"stopLevel":price_to_ticks_offset(entry,sl),"profitLevel":price_to_ticks_offset(entry,ex)})})
        if r1.get("success"): drawn+=1
        else: fails.append(str(r1)[:80])
        c.call_tool("draw_shape",{"shape":"text","point":{"time":t,"price":round(ly,2)},
            "text":f"#{num}","overrides":json.dumps({"color":col,"bold":True,"fontsize":10})})
    dl=c.call_tool("draw_list"); chart["after"]=dl.get("count") if isinstance(dl,dict) else None
finally:
    try: c.stop()
    except Exception: pass
print(json.dumps({"trades":len(out),"posicoes":drawn,"falhas":len(fails),"chart":chart},indent=2,ensure_ascii=False))
