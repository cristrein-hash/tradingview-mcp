#!/usr/bin/env python3
"""DA deep dive: A (causal rule reproducing cris_exit?) + D (multiple-testing count) + bracket TP-first audit."""
import json, csv, statistics as st, subprocess
from pathlib import Path
HERE=Path(__file__).parent; HMAX=480
PRIM={p.name.split(".")[0].replace("XAUUSD_15m_replay_",""): json.loads(p.read_text())
      for p in sorted((HERE/"primitives").glob("*.primitives.json"))}
PRIM={k[:10]:v for k,v in PRIM.items()}
FD={r["t"]:r for r in (json.loads(l) for l in (HERE/"filter_dataset.jsonl").read_text().splitlines())}
GT={int(r["num"]):r for r in csv.DictReader(open(HERE/"cris_ground_truth.csv"))}
T170=list(csv.DictReader(open(HERE/"strategy_5atr_regime170_trades.csv")))
SL={int(r["num"]):r for r in csv.DictReader(open(HERE/"lab_sl_exit.csv"))}
def f(x):
    try: return float(x)
    except: return None

print("="*70); print("A-deep — does ANY causal rule reproduce cris_exit?"); print("="*70)
# Part3 said supply above != cris_exit in 122/126. Verify + test alternative causal targets.
rows=[]
for tr in T170:
    num=int(tr["num"]); t=int(tr["entry_t"]); fd=FD.get(t); g=GT.get(num)
    if not fd or not g: continue
    pr=PRIM[fd["block"]]; s=pr["series"]; z=pr["zones"]
    i=int(fd["i"]); cj=int(fd["cj"]); atr=s[i]["atr"]; tc=s[cj]["t"]
    entry=f(g["entry"]); cris_exit=f(g["cris_exit"]); cris_sl=f(g["cris_sl"])
    risk=entry-cris_sl if cris_sl else None
    # candidate causal targets
    # supply above
    sup=None
    for zz in z:
        if zz.get("text")=="SUPPLY" and zz.get("born_t",1e18)<=tc and zz["low"]>entry:
            d=zz["low"]-entry
            if sup is None or d<sup[0]: sup=(d,zz["low"])
    sup=sup[1] if sup else None
    rows.append({"num":num,"entry":entry,"cris_exit":cris_exit,"risk":risk,"atr":atr,
                 "sup":sup,"Rpot":(cris_exit-entry)/risk if (cris_exit and risk and risk>0) else None})
# fixed-R targets: does cris_exit cluster at a fixed R multiple? (would mean rule=fixed TP)
rpot=[r["Rpot"] for r in rows if r["Rpot"] is not None]
print(f"cris_Rpot dist (N={len(rpot)}): median {st.median(rpot):.2f} mean {st.mean(rpot):.2f} stdev {st.pstdev(rpot):.2f} min {min(rpot):.2f} max {max(rpot):.2f}")
import collections
buck=collections.Counter(round(r) for r in rpot)
print(f"  Rpot rounded buckets: {dict(sorted(buck.items()))}")
# how well does a FIXED rule (e.g. exit at entry+kR) reproduce cris_exit? best k by abs err
for k in [1,1.5,2,2.7,3]:
    err=[abs((r['entry']+k*r['risk'])-r['cris_exit']) for r in rows if r['risk'] and r['risk']>0 and r['cris_exit']]
    print(f"  fixed {k}R target: median$ err vs cris_exit = {st.median(err):.1f}")
# supply-above as target err (recompute)
hassup=[r for r in rows if r["sup"] and r["cris_exit"]]
err_sup=[abs(r["sup"]-r["cris_exit"]) for r in hassup]
above=sum(1 for r in hassup if r["sup"]>=r["cris_exit"]-0.05)
print(f"  supply-above: N={len(hassup)} median$ err {st.median(err_sup):.1f} | supply>=exit in {above}/{len(hassup)}")

print("\n"+"="*70); print("BRACKET TP-FIRST audit — is +148.9 inflated by ignoring path order?"); print("="*70)
# The bracket loops bar-by-bar SL vs TP. But intrabar it cannot know if low or high came first.
# It checks hit_sl and hit_tp; if both same bar -> ambos(SL). If only TP -> TP. BUT a bar can have
# high>=cris_exit while ALSO earlier bars never hit SL — fine. Real risk: a TP-bar where low also
# dipped (but not to SL). That's ok. The real optimism: TP counted even if that same bar's path
# would've required price to first go down. Count TP bars whose OWN low < entry (price was below entry
# intrabar on the TP bar = ambiguous whether TP filled).
tp_amb=0; tp_total=0
for num,r in SL.items():
    if r["br_out"]!="TP": continue
    tp_total+=1
    t=int(GT[num]["entry_t"]); fd=FD.get(t)
    if not fd: continue
    pr=PRIM[fd["block"]]; s=pr["series"]; cj=int(fd["cj"]); cris_exit=f(GT[num]["cris_exit"]); cris_sl=f(GT[num]["cris_sl"])
    end=min(cj+HMAX,len(s)-1)
    for k in range(cj+1,end+1):
        if s[k]["h"]>=cris_exit:
            # TP bar; check its low
            if s[k]["l"]<f(GT[num]["entry"]):
                tp_amb+=1
            break
        if s[k]["l"]<=cris_sl: break
print(f"bracket TP outcomes: {tp_total} | TP-bars whose intrabar low dipped BELOW entry (order ambiguity, no slippage modeled either): {tp_amb}")

print("\n"+"="*70); print("D — multiple-testing / variant count in research dir"); print("="*70)
import glob,os
allpy=glob.glob(str(HERE/"*.py"))
da=[p for p in allpy if "/_DA_" in p or "/_verify" in p or "/_reopt" in p or "/_r2lap" in p or "/_disc8" in p or "/_engine" in p or "/_combo" in p or "/_losercut" in p or "/_deepen" in p]
print(f"total .py in dir: {len(allpy)} | search/verify/variant scripts (DA/verify/reopt/r2lap/disc8/engine/combo/losercut/deepen): {len(da)}")
# count distinct strategy_*_trades.csv = candidate final strategies tried
strat=glob.glob(str(HERE/"strategy_*_trades.csv"))
print(f"distinct strategy_*_trades.csv (candidate finals): {len(strat)} -> {[os.path.basename(p) for p in strat]}")
cand=glob.glob(str(HERE/"candidates_*.csv"))
print(f"candidate universe CSVs: {len(cand)}")
