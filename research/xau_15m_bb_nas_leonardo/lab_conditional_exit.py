#!/usr/bin/env python3
"""Exit ESCALONADO causal (Cris 2026-06-27): o mercado revela o runner ao atingir +Nr (nao adivinha na entrada).
Logica: trail APERTADO (cf_low-0.1ATR) no scalp; ao cruzar +Kr, SOLTA o trail (chandelier kATR / swing puro)
para cavalgar a cauda ate cris_exit. Mantem scalp ~1R na maioria, tenta os 25 runners (Rpot>3) sem flag de entrada.
SL=flush-0.1ATR (=csv_sl). Compara sumR/WR/DD + erro vs cris_exit + runners capturados vs base LETRUN (+66.3).
RAW-causal. So mede; sem veredito."""
import json, csv, statistics as st
from pathlib import Path
HERE=Path(__file__).parent; HMAX=480; RCAP=20.0
PRIM={p.name.split(".")[0].replace("XAUUSD_15m_replay_",""): json.loads(p.read_text())
      for p in sorted((HERE/"primitives").glob("*.primitives.json"))}
PRIM={k[:10]:v for k,v in PRIM.items()}
FD={r["t"]:r for r in (json.loads(l) for l in (HERE/"filter_dataset.jsonl").read_text().splitlines())}
GT={int(r["num"]):r for r in csv.DictReader(open(HERE/"cris_ground_truth.csv"))}
T170=list(csv.DictReader(open(HERE/"strategy_5atr_regime170_trades.csv")))
def fnum(x): return float(x) if x not in (None,"","None") else None
def cf_low(s,i):
    L=[b["l"] for b in s]; lo=max(2,i-120); bst=None
    for p in range(lo,i-1):
        if L[p]==min(L[p-2:p+3]): bst=L[p]
    return bst

def sim(mode,s,cj,entry,sl,atr,K,loose):
    """trail cf_low-0.1ATR apos +1R; ao atingir +Kr solta (loose='chand'kATR ou 'swing')."""
    risk=entry-sl; end=min(cj+HMAX,len(s)-1); r1=False; ridem=False; trail=sl; runhi=entry
    for k in range(cj+1,end+1):
        b=s[k]; lo,hi,cl=b["l"],b["h"],b["c"]
        if lo<=trail and (r1 or trail>sl): return trail
        if lo<=sl and not r1: return sl
        runhi=max(runhi,hi)
        if (hi-entry)/risk>=1: r1=True
        if (hi-entry)/risk>=K: ridem=True
        if not r1: continue
        if mode=="LETRUN":
            sw=cf_low(s,k)
            if sw: trail=max(trail,sw-0.1*atr)
        elif mode=="RIDE":
            if not ridem:
                sw=cf_low(s,k)
                if sw: trail=max(trail,sw-0.1*atr)        # apertado ate +Kr
            else:
                if loose=="swing":
                    sw=cf_low(s,k)
                    if sw: trail=max(trail,sw)            # solto: swing sem buffer
                else:
                    if cl<=runhi-loose*atr: return cl     # chandelier kATR
        elif mode=="RIDER":                                # giveback em R do pico apos +Kr
            if not ridem:
                sw=cf_low(s,k)
                if sw: trail=max(trail,sw-0.1*atr)
            else:
                trail=max(trail, runhi-loose*risk)        # loose = giveback em R
    return s[end]["c"]

CONF=[("LETRUN",None,None)]+[("RIDER",K,gb) for K in (1,2,3,4) for gb in (1.0,1.5,2.0,2.5,3.0)]
big=set()
data=[]
for tr in T170:
    num=int(tr["num"]); t=int(tr["entry_t"]); fd=FD.get(t); gt=GT.get(num)
    if not fd: continue
    pr=PRIM[fd["block"]]; s=pr["series"]; i=fd["i"]; cj=fd["cj"]; atr=s[i]["atr"]
    entry=fnum(gt["entry"]); sl=float(tr["sl"]); risk=entry-sl
    ce=fnum(gt["cris_exit"]); rp=fnum(gt["cris_Rpot"])
    if rp and rp>3: big.add(num)
    data.append((num,s,cj,entry,sl,atr,risk,ce,rp))

def run(mode,K,loose):
    out=[]
    for num,s,cj,entry,sl,atr,risk,ce,rp in data:
        ex=sim(mode,s,cj,entry,sl,atr,K or 3,loose); R=max(-1.0,min(RCAP,(ex-entry)/risk))
        out.append({"num":num,"R":R,"ex":ex,"ce":ce,"rp":rp})
    return out
def metr(rs):
    n=len(rs); sm=sum(x["R"] for x in rs); w=sum(1 for x in rs if x["R"]>0)
    eq=pk=dd=0; st_=mst=0
    for x in sorted(rs,key=lambda y:y["num"]):
        eq+=x["R"]; pk=max(pk,eq); dd=min(dd,eq-pk)
        if x["R"]<=0: st_+=1; mst=max(mst,st_)
        else: st_=0
    ep=st.median([abs(x["ex"]-x["ce"]) for x in rs if x["ce"]])
    cap=sum(1 for x in rs if x["num"] in big and x["R"]>=3)
    return n,round(100*w/n,1),round(sm,1),round(dd,1),mst,round(ep,1),cap

YR={int(r["num"]):int(r["yr"]) for r in T170}
def peryear(rs):
    y={}
    for x in rs: y.setdefault(YR[x["num"]],0.0); y[YR[x["num"]]]+=x["R"]
    return {k:round(v,1) for k,v in sorted(y.items())}
def ndiff(rs,base):
    bb={x["num"]:x["R"] for x in base}; d=[(x["num"],round(x["R"]-bb[x["num"]],2)) for x in rs if abs(x["R"]-bb[x["num"]])>1e-6]
    return d

print(f"runners Cris (Rpot>3): {len(big)}\n")
print("=== GRID sumR (linha K = arma loose apos +Kr; col gb = recuo permitido do pico em R) ===")
base=run("LETRUN",None,None); _,_,bsm,_,_,_,_=metr(base)
print(f"  LETRUN (base regua viva): {bsm:+}")
hdr="K\\gb"; print(f"{hdr:>5}"+"".join(f"{g:>8}" for g in (1.0,1.5,2.0,2.5,3.0)))
grid={}
for K in (1,2,3,4):
    line=f"{K:>5}"
    for gb in (1.0,1.5,2.0,2.5,3.0):
        rs=run("RIDER",K,gb); _,_,sm,_,_,_,_=metr(rs); grid[(K,gb)]=rs; line+=f"{sm:>8}"
    print(line)
print(f"\n{'config':<16}{'N':>4}{'WR':>6}{'sumR':>7}{'DD':>6}{'stk':>4}{'errPrc$':>8}{'capRun/25':>10}{'#difere':>9}")
for tag,rs in [("LETRUN",base),("RIDER K1 gb2.0",grid[(1,2.0)]),("RIDER K2 gb2.0",grid[(2,2.0)]),("RIDER K3 gb2.0",grid[(3,2.0)])]:
    n,wr,sm,dd,stk,ep,cap=metr(rs); nd=len(ndiff(rs,base))
    print(f"{tag:<16}{n:>4}{wr:>6}{sm:>7}{dd:>6}{stk:>4}{ep:>8}{cap:>10}{nd:>9}")
print("\n=== por ANO (sumR) ===")
print(f"{'config':<16}{'2024':>7}{'2025':>7}{'2026':>7}")
for tag,rs in [("LETRUN",base),("RIDER K1 gb2.0",grid[(1,2.0)]),("RIDER K2 gb2.0",grid[(2,2.0)])]:
    y=peryear(rs); print(f"{tag:<16}{y.get(2024,0):>7}{y.get(2025,0):>7}{y.get(2026,0):>7}")
print("\nref base: +66.3R / WR64.1 / DD-3.0. (fill realista candle-low ~ -15R em nivel absoluto, comparacao se mantem - DA.)")
