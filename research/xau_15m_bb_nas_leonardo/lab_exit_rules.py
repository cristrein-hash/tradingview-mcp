#!/usr/bin/env python3
"""LAB: regra CAUSAL de exit que imite o julgamento do Cris (cris_exit). Cris 2026-06-27.
Alvo = cris_exit (preco que o Cris desenhou em cada long_position). Bimodal: 108<=1.2R, 37 medio, 25 runners(>3R).
Testa conjunto PRINCIPIADO de regras CAUSAIS (so dados ja conhecidos), todas com SL=flush-0.1ATR (=csv_sl, estrutural):
  TGT1/2/3  : alvo fixo +1R/+2R/+3R (referencia)
  LETRUN    : regua atual (trail cf_low-0.1ATR, arma apos +1R)
  SWING     : trail no swing-low confirmado SEM buffer (mais solto -> cavalga mais), arma apos +1R
  CHAND2/3  : chandelier ATR (sai se close <= maxHigh - k*ATR), arma apos +1R
  EMA21     : sai no 1o close<ema21 apos +1R
  NASs      : sai no close da 1a NAS SHORT (t>entry) apos +1R; backstop = SWING
  SELLb     : sai no close da 1a SELL bubble M/L (known_at) apos +1R; backstop = SWING
  STRUCT    : sai no 1o CHoCH/BOS com price<entry (proxy baixista, SHIFT+1 p/ repaint) apos +1R; backstop=SWING
Para cada regra: sumR/WR/DD (causal) + erro vs cris_exit (preco $ e R) + quantos dos 25 runners capturou (>=3R) +
correlacao exit_R x cris_Rpot. So MEDE; sem veredito. RAW-causal."""
import json, csv, bisect, statistics as st
from pathlib import Path
HERE=Path(__file__).parent; HMAX=480; RCAP=20.0; SZ={"S":1,"M":2,"L":3}
PRIM={p.name.split(".")[0].replace("XAUUSD_15m_replay_",""): json.loads(p.read_text())
      for p in sorted((HERE/"primitives").glob("*.primitives.json"))}
PRIM={k[:10]:v for k,v in PRIM.items()}
BUB={}
for bf in sorted((HERE/"bubbles").glob("*.bubbles.jsonl")):
    BUB[bf.name[:10]]=sorted([json.loads(l) for l in bf.read_text().splitlines() if l],key=lambda x:x["t"])
FD={r["t"]:r for r in (json.loads(l) for l in (HERE/"filter_dataset.jsonl").read_text().splitlines())}
GT={int(r["num"]):r for r in csv.DictReader(open(HERE/"cris_ground_truth.csv"))}
T170=list(csv.DictReader(open(HERE/"strategy_5atr_regime170_trades.csv")))
def fnum(x): return float(x) if x not in (None,"","None") else None

def cf_low(s,i):
    L=[b["l"] for b in s]; lo=max(2,i-120); bst=None
    for p in range(lo,i-1):
        if L[p]==min(L[p-2:p+3]): bst=L[p]
    return bst

def sim(rule, s, cj, entry, sl, atr, ctx):
    """retorna exit_price causal."""
    risk=entry-sl; end=min(cj+HMAX,len(s)-1); r1=False; trail=sl; runhi=entry
    nas_t=ctx["nas_short_t"]; sell_t=ctx["sell_t"]; struct=ctx["struct_bear"]
    for k in range(cj+1,end+1):
        b=s[k]; lo,hi,cl=b["l"],b["h"],b["c"]; t=b["t"]
        # SL sempre primeiro (conservador)
        if lo<=sl and not r1: return sl
        if lo<=trail and r1: return trail
        runhi=max(runhi,hi)
        if (hi-entry)/risk>=1:
            if not r1: r1=True
        if rule in ("TGT1","TGT2","TGT3"):
            kk={"TGT1":1,"TGT2":2,"TGT3":3}[rule]
            if hi>=entry+kk*risk: return entry+kk*risk
            continue
        if not r1: continue
        # regras armadas apos +1R
        if rule=="LETRUN":
            sw=cf_low(s,k)
            if sw: trail=max(trail,sw-0.1*atr)
        elif rule=="SWING":
            sw=cf_low(s,k)
            if sw: trail=max(trail,sw)
        elif rule in ("CHAND2","CHAND3"):
            kk=2 if rule=="CHAND2" else 3
            if cl<=runhi-kk*atr: return cl
        elif rule=="EMA21":
            if b.get("ema21") and cl<b["ema21"]: return cl
        elif rule in ("NASs","SELLb","STRUCT"):
            sig=False
            if rule=="NASs": sig = bisect.bisect_right(nas_t,t)>bisect.bisect_left(nas_t,entry+1)
            elif rule=="SELLb": sig = bisect.bisect_right(sell_t,t)>bisect.bisect_left(sell_t,entry+1)
            elif rule=="STRUCT":
                # CHoCH/BOS baixista (price<entry) com t<=t-1bar (shift repaint)
                tcut=s[k-1]["t"]
                sig = any(e<=tcut for e in struct)
            if sig: return cl
            sw=cf_low(s,k)              # backstop swing trail
            if sw: trail=max(trail,sw)
    return s[end]["c"]

RULES=["TGT1","TGT2","TGT3","LETRUN","SWING","CHAND2","CHAND3","EMA21","NASs","SELLb","STRUCT"]
res={r:[] for r in RULES}; rows=[]
for tr in T170:
    num=int(tr["num"]); t=int(tr["entry_t"]); fd=FD.get(t); gt=GT.get(num)
    if not fd: continue
    pr=PRIM[fd["block"]]; s=pr["series"]; i=fd["i"]; cj=fd["cj"]; atr=s[i]["atr"]
    entry=fnum(gt["entry"]); sl=float(tr["sl"]); risk=entry-sl
    cris_exit=fnum(gt["cris_exit"]); cris_Rpot=fnum(gt["cris_Rpot"])
    bkey=fd["block"]; bub=BUB.get(bkey,[])
    nas=sorted(pr["nas_events"],key=lambda x:x["t"]); nas_short_t=[e["t"] for e in nas if e["dir"]=="SHORT"]
    sell_t=[x["t"] for x in bub if x["side"]=="SELL" and x["size"] in("M","L")]
    struct_bear=[e["t"] for e in pr["smc_events"] if e["text"] in("CHoCH","BOS") and e["price"]<entry and e["t"]>t]
    ctx={"nas_short_t":nas_short_t,"sell_t":sell_t,"struct_bear":sorted(struct_bear)}
    row={"num":num,"cris_exit":cris_exit,"cris_Rpot":cris_Rpot}
    for rule in RULES:
        ex=sim(rule,s,cj,entry,sl,atr,ctx); R=max(-1.0,min(RCAP,(ex-entry)/risk))
        res[rule].append({"num":num,"R":R,"ex":ex,"cris_exit":cris_exit,"cris_Rpot":cris_Rpot})
        row[rule+"_R"]=round(R,2)
    rows.append(row)

big_ids={r["num"] for r in rows if r["cris_Rpot"] and r["cris_Rpot"]>3}   # 25 runners
def metr(rs):
    n=len(rs); sm=sum(x["R"] for x in rs); w=sum(1 for x in rs if x["R"]>0)
    eq=pk=dd=0
    for x in sorted(rs,key=lambda y:y["num"]):
        eq+=x["R"]; pk=max(pk,eq); dd=min(dd,eq-pk)
    err_p=st.median([abs(x["ex"]-x["cris_exit"]) for x in rs if x["cris_exit"]])
    err_r=st.median([abs(x["R"]-x["cris_Rpot"]) for x in rs if x["cris_Rpot"] is not None])
    cap=sum(1 for x in rs if x["num"] in big_ids and x["R"]>=3)
    return n,round(100*w/n,1),round(sm,1),round(dd,1),round(err_p,1),round(err_r,2),cap

print(f"runners do Cris (Rpot>3): {len(big_ids)} | alvo = imitar cris_exit\n")
print(f"{'regra':<8}{'N':>4}{'WR':>6}{'sumR':>7}{'DD':>6}{'errPrc$':>8}{'errR':>6}{'capRun/25':>10}")
print(f"{'(atual)':<8}{'170':>4}{'64.1':>6}{'+66.3':>7}{'-3.0':>6}{'-':>8}{'-':>6}{'-':>10}  <- LETRUN regua viva")
ranked=[]
for rule in RULES:
    n,wr,sm,dd,ep,er,cap=metr(res[rule]); ranked.append((rule,n,wr,sm,dd,ep,er,cap))
    print(f"{rule:<8}{n:>4}{wr:>6}{sm:>7}{dd:>6}{ep:>8}{er:>6}{cap:>10}")
print("\nordenado por menor erro de PRECO vs seu exit:")
for rule,n,wr,sm,dd,ep,er,cap in sorted(ranked,key=lambda z:z[5]):
    print(f"  {rule:<8} errPrc=${ep:<6} errR={er:<5} sumR={sm:+} capRun={cap}/25 DD={dd}")
with open(HERE/"lab_exit_rules.csv","w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
print("\n-> lab_exit_rules.csv (R por regra por trade)")
