import sys, csv
from pathlib import Path
from datetime import datetime, timezone
L1=Path("my-strategy/strategies/xau_4h_long/continuation/L1_EMA21_CONTINUATION")
sys.path.insert(0,str(L1)); sys.path.insert(0,"my-strategy/core")
import scanner
S=scanner.build_series()
rows=list(csv.DictReader(open(L1/"reports/l1_old_vs_new_regime_comparison.csv")))
def to_u(ts): return int(datetime.fromisoformat(ts).replace(tzinfo=timezone.utc).timestamp())
def outcome(i, entry, sl, target, mx=60):
    for k in range(i+1, min(i+1+mx,S.N)):
        if S.L[k]<=sl: return "STOP",-1.0
        if S.H[k]>=target: return "TARGET",3.0
    e=min(i+mx,S.N-1); return "TIME",round((S.C[e]-entry)/(entry-sl),2)
recs=[]
for r in rows:
    u=to_u(r["timestamp"]); i=S.idx.get(u)
    if i is None or i<60: continue
    O,H,L,C=S.O,S.H,S.L,S.C; entry=C[i]; atr=S.ATR14[i] or 0
    dz=scanner.demand_zone(S,i); zlo=(dz[1] if dz else S.EMA21[i-1]); zhi=(dz[0] if dz else S.EMA21[i-1])
    sl=zlo-0.1*atr; risk=entry-sl
    if risk<=0 or atr<=0: continue
    res,R=outcome(i,entry,sl,entry+3*risk)
    rng=H[i]-L[i]
    recs.append({"id":r["candidate_id"],"res":res,"R":R,
        "rsi_vs_ma": round(scanner.rsi_vs_ma(S,i) or 0,2),
        "risk_atr": round(risk/atr,2),
        "zone_w_atr": round((zhi-zlo)/atr,2) if dz else 0.0,
        "body": round((C[i]-O[i])/rng,2) if rng>0 else 0,
        "ext_ema_atr": round((C[i]-S.EMA21[i])/atr,2),       # extensão acima da EMA21
        "ext_sma_atr": round((C[i]-S.SMA50[i])/atr,2),       # extensão acima da SMA50
        "ret5": round(C[i]/C[i-5]-1,4),
        "dist_zone_atr": round((entry-zhi)/atr,2) if dz else 0.0})  # quão acima do topo da zona entrou
    recs[-1]["res_R"]=R
T=[x for x in recs if x["res"]=="TARGET"]
print(f"recs={len(recs)} TARGET={len(T)} STOP={sum(1 for x in recs if x['res']=='STOP')}")
feats=["rsi_vs_ma","risk_atr","zone_w_atr","body","ext_ema_atr","ext_sma_atr","ret5","dist_zone_atr"]
print("\n=== p/ cada feature: melhor corte que MANTÉM 100% dos TARGET e corta + STOP ===")
import itertools
best=[]
for f in feats:
    tvals=[x[f] for x in T]
    lo,hi=min(tvals),max(tvals)
    # tenta manter winners por cima (keep f>=lo) e por baixo (keep f<=hi)
    for mode,thr in [("ge",lo),("le",hi)]:
        if mode=="ge": keep=[x for x in recs if x[f]>=thr]
        else: keep=[x for x in recs if x[f]<=thr]
        kt=sum(1 for x in keep if x["res"]=="TARGET"); ks=sum(1 for x in keep if x["res"]=="STOP")
        cut=len(recs)-len(keep); cutS=sum(1 for x in recs if x not in keep and x["res"]=="STOP")
        if kt==len(T):  # mantém todos winners
            sr=round(sum(x["R"] for x in keep),1)
            best.append((f,mode,thr,len(keep),kt,ks,cutS,sr))
best.sort(key=lambda z:-z[6])
for f,mode,thr,n,kt,ks,cs,sr in best[:10]:
    print(f"  {f} {mode} {thr}: KEEP n={n} (T={kt}/{len(T)} S={ks}) corta {cs} stops | sumR={sr}")

print("\n=== COMBINAÇÕES (AND) que mantêm 100% dos 17 TARGET ===")
def ev(pred,label):
    keep=[x for x in recs if pred(x)]
    kt=sum(1 for x in keep if x["res"]=="TARGET"); ks=sum(1 for x in keep if x["res"]=="STOP")
    cs=sum(1 for x in recs if not pred(x) and x["res"]=="STOP")
    cw=sum(1 for x in recs if not pred(x) and x["res"]=="TARGET")
    print(f"  {label}: KEEP n={len(keep)} T={kt}/17 S={ks} | corta {cs} stops, {cw} winners | sumR={round(sum(x['R'] for x in keep),1)}")
# principled anti-extensão + zona de qualidade
ev(lambda x: x["ret5"]<=0.0142 and x["ext_ema_atr"]<=2.95, "ret5<=1.42% AND ext_ema<=2.95ATR")
ev(lambda x: x["ret5"]<=0.0142 and x["ext_ema_atr"]<=2.95 and x["zone_w_atr"]>=0.6, "+ zone_w>=0.6ATR")
ev(lambda x: x["ret5"]<=0.0142 and x["ext_ema_atr"]<=2.95 and x["zone_w_atr"]>=0.6 and x["dist_zone_atr"]<=1.81, "+ dist_zone<=1.81ATR (MÁX anti-ext)")
# baseline
ev(lambda x: True, "BASELINE (sem filtro)")
