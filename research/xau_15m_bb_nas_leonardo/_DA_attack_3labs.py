#!/usr/bin/env python3
"""DA ATTACK on 3 labs (SL/EXIT bracket, ENTRY engine, diag). RAW-causal in-sample audit.
Attacks A-F. Pure measurement against CSVs + RAW. No verdicts written to disk, prints only."""
import json, csv, statistics as st
from pathlib import Path
HERE=Path(__file__).parent; HMAX=480
PRIM={p.name.split(".")[0].replace("XAUUSD_15m_replay_",""): json.loads(p.read_text())
      for p in sorted((HERE/"primitives").glob("*.primitives.json"))}
PRIM={k[:10]:v for k,v in PRIM.items()}
FD={r["t"]:r for r in (json.loads(l) for l in (HERE/"filter_dataset.jsonl").read_text().splitlines())}
GT={int(r["num"]):r for r in csv.DictReader(open(HERE/"cris_ground_truth.csv"))}
T170=list(csv.DictReader(open(HERE/"strategy_5atr_regime170_trades.csv")))
SL=list(csv.DictReader(open(HERE/"lab_sl_exit.csv")))
ENG=list(csv.DictReader(open(HERE/"lab_entry_engine.csv")))
DIAG=list(csv.DictReader(open(HERE/"lab_entry_diag.csv")))
def f(x):
    try: return float(x)
    except: return None

print("="*70); print("ATTACK A — HINDSIGHT in +148.9 bracket"); print("="*70)
# cris_exit vs csv_exit: how many hand-marked TPs are NEW (above csv_exit)?
gt=list(GT.values())
exit_edited=[g for g in gt if f(g["cris_exit"]) and f(g["csv_exit"]) and abs(f(g["cris_exit"])-f(g["csv_exit"]))>0.05]
exit_higher=[g for g in gt if f(g["cris_exit"]) and f(g["csv_exit"]) and f(g["cris_exit"])>f(g["csv_exit"])+0.05]
print(f"EXIT hand-edited vs csv: {len(exit_edited)}/170 | of those cris_exit HIGHER than csv: {len(exit_higher)}")
# decompose bracket sumR: contribution from trades where cris_exit>csv_exit (the hindsight uplift)
slmap={int(r["num"]):r for r in SL}
sum_all=sum(f(r["br_R"]) for r in SL)
edited_nums={int(g["num"]) for g in exit_higher}
sum_from_edited=sum(f(slmap[n]["br_R"]) for n in edited_nums if n in slmap)
# what would bracket sumR be if for edited trades we capped at csv_exit instead (i.e. removed the uplift)?
print(f"bracket sumR total = {sum_all:+.1f}")
print(f"  sumR contributed by the {len(exit_higher)} cris_exit>csv_exit trades = {sum_from_edited:+.1f}")
# current letrun sumR of those same trades
t170map={int(r["num"]):r for r in T170}
cur_those=sum(f(t170map[n]["R"]) for n in edited_nums if n in t170map)
print(f"  current let-run sumR of those same {len(exit_higher)} trades = {cur_those:+.1f}  (uplift = {sum_from_edited-cur_those:+.1f})")
# how many bracket TPs reached are on hand-raised targets
tp_reached=[int(r["num"]) for r in SL if r["tp_reached"]=="True"]
tp_on_raised=[n for n in tp_reached if n in edited_nums]
print(f"TPs reached: {len(tp_reached)}/170 | of those on a RAISED target: {len(tp_on_raised)}")
# how many cris_exit==csv_exit==csv_sl (i.e. -1R trades where exit=sl, no hindsight gain)
exit_eq_sl=[g for g in gt if f(g["cris_exit"]) and f(g["cris_sl"]) and abs(f(g["cris_exit"])-f(g["cris_sl"]))<0.05]
print(f"trades where cris_exit==cris_sl (forced -1R, exit=sl): {len(exit_eq_sl)}")

print("\n"+"="*70); print("ATTACK B/E — FILL REALISM: gaps through SL, same-bar ambos"); print("="*70)
# B: how many losers had minlow far BELOW cris_sl (worse fill than -1R)
diagmap={int(r["num"]):r for r in DIAG}
# reconstruct minlow per trade from RAW on let-run path, compare to cris_sl and csv_sl
worse_sl=[]; gap_amounts=[]
for tr in T170:
    num=int(tr["num"]); t=int(tr["entry_t"]); fd=FD.get(t); g=GT.get(num)
    if not fd or not g: continue
    pr=PRIM[fd["block"]]; s=pr["series"]; cj=fd["cj"]; exi=int(fd["exi"])
    entry=f(tr["entry"]); csv_sl=f(tr["sl"]); cris_sl=f(g["cris_sl"]); atr=f(slmap[num]["atr"]) if num in slmap else None
    path=s[cj+1:exi+1] or [s[cj]]
    minlow=min(b["l"] for b in path)
    risk=entry-csv_sl
    # find first bar that breaches csv_sl and its low (the actual fill candle low)
    breach_low=None
    for b in path:
        if b["l"]<=csv_sl: breach_low=b["l"]; break
    if breach_low is not None and breach_low < csv_sl-0.001:
        slip=(csv_sl-breach_low)
        slip_R=slip/risk if risk>0 else None
        worse_sl.append((num,round(csv_sl,2),round(breach_low,2),round(slip,2),round(slip_R,3) if slip_R else None,round(atr,2) if atr else None))
        if slip_R: gap_amounts.append(slip_R)
print(f"trades where SL-breach candle LOW < csv_sl (gap/spike through stop, fill worse than -1R): {len(worse_sl)}")
if gap_amounts:
    print(f"  extra slip beyond -1R (R units): median {st.median(gap_amounts):.3f}  mean {st.mean(gap_amounts):.3f}  max {max(gap_amounts):.3f}")
    big=[x for x in worse_sl if x[4] and x[4]>=0.5]
    print(f"  trades slipping >=0.5R extra: {len(big)} -> {[(x[0],x[4]) for x in sorted(big,key=lambda y:-y[4])[:10]]}")
    total_extra=sum(gap_amounts)
    print(f"  TOTAL unmodeled extra loss if filled at candle low: -{total_extra:.1f}R across all SL trades")
# E: same-bar ambos in bracket
ambos=[int(r["num"]) for r in SL if r["br_out"]=="ambos"]
print(f"bracket same-bar SL+TP ('ambos', treated SL-first/conservative): {len(ambos)} -> {ambos}")

print("\n"+"="*70); print("ATTACK C — ENTRY engine limit-fill realism"); print("="*70)
# C1: density of demand zones, nearest-demand distance distribution
ndem=sum(1 for pr in PRIM.values() for z in pr["zones"] if z.get("text")=="DEMAND")
print(f"total DEMAND zones across 8 blocks: {ndem}")
dist_atr=[f(r["dem_atr"]) for r in DIAG if f(r["dem_atr"]) is not None]
print(f"nearest-demand-below dist (ATR): median {st.median(dist_atr):.2f} mean {st.mean(dist_atr):.2f} | <=0.5ATR: {sum(1 for d in dist_atr if d<=0.5)}/{len(dist_atr)}  ==0.0: {sum(1 for d in dist_atr if d<1e-6)}")
# C2: intrabar order bug — engine checks low<=sl THEN low<=limit on same bar; but SL is BELOW limit always?
# verify limit>sl is enforced (yes in code). Check: on fill bar, did the SAME bar also breach SL? (low<=sl)
intrabar_ambig=[]
for r in ENG:
    if r["mode"]!="LIMIT_demanda": continue
    num=int(r["num"]); t=int(GT[num]["entry_t"]) if num in GT else None
    fd=FD.get(int(GT[num]["entry_t"])) if num in GT else None
    if not fd: continue
    pr=PRIM[fd["block"]]; s=pr["series"]; cj=fd["cj"]
    sl=f(r["sl"]); limit=f(r["entry_eff"])
    end=min(cj+HMAX,len(s)-1)
    for k in range(cj+1,end+1):
        lo=s[k]["l"]
        if lo<=limit:
            # this is the fill bar (engine breaks here unless sl hit first)
            if lo<=sl:  # same bar touched BOTH limit and sl
                intrabar_ambig.append(num)
            break
        if lo<=sl: break
print(f"LIMIT fills: {sum(1 for r in ENG if r['mode']=='LIMIT_demanda')} | fill-bar that ALSO breached SL same bar (ambiguous order, engine assumed limit-first/optimistic): {len(intrabar_ambig)} -> {intrabar_ambig[:15]}")
# C3: does engine just shrink risk cosmetically? compare risk0 vs risk_eff and R distribution
lim=[r for r in ENG if r["mode"]=="LIMIT_demanda"]
risk0=[f(r["risk0"]) for r in lim]; riske=[f(r["risk_eff"]) for r in lim]
print(f"risk shrink on {len(lim)} filled: median risk0 ${st.median(risk0):.2f} -> risk_eff ${st.median(riske):.2f} ({100*(1-st.median(riske)/st.median(risk0)):.1f}% smaller)")
# net R change
dR=[f(r["R"])-f(r["R0"]) for r in lim]
print(f"net sumR change from engine on filled: {sum(dR):+.2f}R | mean dR {st.mean(dR):+.3f} | flipped L->W {sum(1 for r in lim if f(r['R0'])<=0 and f(r['R'])>0)} | worsened {sum(1 for r in lim if f(r['R'])<f(r['R0'])-1e-6)}")

print("\n"+"="*70); print("ATTACK F — entry engine DD worsening"); print("="*70)
# recompute equity DD for R0 vs R using num order
def dd_of(rows,key):
    eq=pk=dd=0
    for r in sorted(rows,key=lambda x:int(x["num"])):
        eq+=f(r[key]); pk=max(pk,eq); dd=min(dd,eq-pk)
    return round(dd,1)
print(f"DD base R0={dd_of(ENG,'R0')}  | DD engine R={dd_of(ENG,'R')}")
# which trades drive the worse DD: trades where R worsened and clustered
worsened=[(int(r['num']),f(r['R0']),f(r['R'])) for r in ENG if f(r['R'])<f(r['R0'])-1e-6]
worsened.sort()
print(f"worsened trades ({len(worsened)}): {[(n,round(a,2),round(b,2)) for n,a,b in worsened]}")
