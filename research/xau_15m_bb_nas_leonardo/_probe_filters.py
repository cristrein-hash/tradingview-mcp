import sys; sys.path.insert(0,"/Users/cristrein/tradingview-mcp/research/xau_15m_bb_nas_leonardo")
from agent_ctx_kit import S,TS,HI,LO,CL,ATR,EMA,RSI,N,ENTRIES,score,causal_swings_upto

def cf(e):
    j=e["j"]; i=e["i"]; a=ATR[i] or 5.0
    sw=causal_swings_upto(j)
    Hs=[(idx,pr) for tp,idx,pr,ci in sw if tp=="H"]
    Ls=[(idx,pr) for tp,idx,pr,ci in sw if tp=="L"]
    f={}
    f["dh_slope"]=(Hs[-1][1]-Hs[-2][1])/a if len(Hs)>=2 else 0.0
    f["hh"]=1 if (len(Hs)>=2 and Hs[-1][1]>Hs[-2][1]) else 0
    f["hl"]=1 if (len(Ls)>=2 and Ls[-1][1]>Ls[-2][1]) else 1
    f["lh2"]=1 if (len(Hs)>=3 and Hs[-1][1]<Hs[-2][1]<Hs[-3][1]) else 0
    push=0
    for k in range(len(Hs)-1,0,-1):
        if Hs[k][1]>Hs[k-1][1]: push+=1
        else: break
    f["push"]=push
    f["reclaim"]=e["reclaim_lag"]
    f["depth"]=(e["leg_top"]-e["demand_low"])/a
    # trajectory: closes above EMA in last 10 bars before j (markup momentum)
    above=sum(1 for k in range(max(0,j-10),j+1) if EMA[k] and CL[k]>EMA[k])
    f["above10"]=above
    # slope of closes over last 20 bars (causal linear-ish): CL[j]-CL[j-20]
    f["mom20"]=(CL[j]-CL[max(0,j-20)])/a
    f["mom40"]=(CL[j]-CL[max(0,j-40)])/a
    # entry vs last confirmed high (how far below the high we entered)
    f["ent_vs_H"]=(e["ent"]-Hs[-1][1])/a if Hs else 0
    # number of confirmed highs above entry recently (overhead resistance) within last 60 bars
    over=sum(1 for idx,pr in Hs if idx>=j-80 and pr>e["ent"])
    f["overhead"]=over
    return f

F={e["n"]:cf(e) for e in ENTRIES}
def hitrate(pred):
    keep=[e["n"] for e in ENTRIES if pred(F[e["n"]])]
    if len(keep)<15: return None
    sc=score(keep); return sc

tests={
 "reclaim<=4": lambda f: f["reclaim"]<=4,
 "reclaim<=3": lambda f: f["reclaim"]<=3,
 "hl==1": lambda f: f["hl"]==1,
 "hh==1": lambda f: f["hh"]==1,
 "not lh2": lambda f: f["lh2"]==0,
 "dh_slope>0.5": lambda f: f["dh_slope"]>0.5,
 "dh_slope>1.5": lambda f: f["dh_slope"]>1.5,
 "push>=2": lambda f: f["push"]>=2,
 "mom20>0": lambda f: f["mom20"]>0,
 "mom40>2": lambda f: f["mom40"]>2,
 "above10>=8": lambda f: f["above10"]>=8,
 "ent_vs_H<-4": lambda f: f["ent_vs_H"]<-4,
 "overhead==0": lambda f: f["overhead"]==0,
 "overhead<=1": lambda f: f["overhead"]<=1,
 "reclaim<=4 & hl": lambda f: f["reclaim"]<=4 and f["hl"]==1,
 "reclaim<=4 & dh>0.5": lambda f: f["reclaim"]<=4 and f["dh_slope"]>0.5,
 "reclaim<=4 & mom40>0": lambda f: f["reclaim"]<=4 and f["mom40"]>0,
 "reclaim<=4 & overhead<=1": lambda f: f["reclaim"]<=4 and f["overhead"]<=1,
}
for name,p in tests.items():
    sc=hitrate(p)
    if sc: print(f"{name:26s} N={sc['N_kept']:2d} hit={sc['hit3r_kept']:.3f} poison={sc['poison_ratio']:.2f} y25={sc['y2025']} y26={sc['y2026']}")

print("\n--- COMBOS around fast-reclaim + structural gate ---")
combos={
 "recl<=4 & not lh2": lambda f: f["reclaim"]<=4 and f["lh2"]==0,
 "recl<=4 & ent_vs_H<-3": lambda f: f["reclaim"]<=4 and f["ent_vs_H"]<-3,
 "recl<=4 & ent_vs_H<-4": lambda f: f["reclaim"]<=4 and f["ent_vs_H"]<-4,
 "recl<=4 & depth>=5": lambda f: f["reclaim"]<=4 and f["depth"]>=5,
 "recl<=4 & depth>=6": lambda f: f["reclaim"]<=4 and f["depth"]>=6,
 "recl<=5 & not lh2": lambda f: f["reclaim"]<=5 and f["lh2"]==0,
 "recl<=5 & ent_vs_H<-3.5": lambda f: f["reclaim"]<=5 and f["ent_vs_H"]<-3.5,
 "recl<=4 & mom40>-1": lambda f: f["reclaim"]<=4 and f["mom40"]>-1,
 "recl<=4 & hl & not lh2": lambda f: f["reclaim"]<=4 and f["hl"]==1 and f["lh2"]==0,
 "B(recl<=4) OR A(push>=2 & ent<-4 & !lh2)":
    lambda f: (f["reclaim"]<=4) or (f["push"]>=2 and f["ent_vs_H"]<-4 and f["lh2"]==0),
 "B(recl<=4 & depth>=5) OR A(push>=2 & !lh2)":
    lambda f: (f["reclaim"]<=4 and f["depth"]>=5) or (f["push"]>=2 and f["lh2"]==0),
 "(recl<=4 OR push>=2) & !lh2 & ent<-3":
    lambda f: (f["reclaim"]<=4 or f["push"]>=2) and f["lh2"]==0 and f["ent_vs_H"]<-3,
}
for name,p in combos.items():
    keep=[e["n"] for e in ENTRIES if p(F[e["n"]])]
    if len(keep)<15:
        print(f"{name:44s} N={len(keep)} (skip <15)"); continue
    sc=score(keep)
    y25w,y25n=map(int,sc["y2025"].split("/")); y26w,y26n=map(int,sc["y2026"].split("/"))
    ok = sc["poison_ratio"]<0.9 and y25w/y25n>0.5 and y26w/y26n>0.5 and sc["N_kept"]>=20
    print(f"{name:44s} N={sc['N_kept']:2d} hit={sc['hit3r_kept']:.3f} poison={sc['poison_ratio']:.2f} y25={sc['y2025']} y26={sc['y2026']} {'<== PASS' if ok else ''}")
