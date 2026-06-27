#!/usr/bin/env python3
"""DA AUDIT of lab_reversal_power.py — verify measurement, not strategy. Numbers only."""
import json, csv, statistics as st
from pathlib import Path
from collections import Counter, defaultdict
HERE = Path(__file__).parent

# ---- rebuild global series exactly like the lab ----
bars = {}
file_t = defaultdict(list)
for p in sorted((HERE/"primitives").glob("*.primitives.json")):
    d = json.loads(p.read_text())
    for b in d["series"]:
        file_t[p.name].append(b["t"])
        bars.setdefault(b["t"], b)
S = [bars[t] for t in sorted(bars)]
T2I = {b["t"]: i for i, b in enumerate(S)}
print(f"[series] global bars={len(S)}  {S[0]['t']}..{S[-1]['t']}")

# ===== POINT 3: dedup / contiguity / gaps =====
print("\n===== P3 GLOBAL SERIES / DEDUP / GAPS =====")
raw_total = sum(len(v) for v in file_t.values())
print(f"raw bars across 8 files = {raw_total} ; unique-by-t = {len(S)} ; dupes removed = {raw_total-len(S)}")
# overlap between consecutive files
fnames = sorted(file_t.keys())
for a, b in zip(fnames, fnames[1:]):
    sa, sb = set(file_t[a]), set(file_t[b])
    ov = sa & sb
    print(f"  overlap {a[:40]} <-> {b[:40]}: {len(ov)} bars")
# gaps
gaps = []
ts = sorted(bars)
for i in range(1, len(ts)):
    d = ts[i]-ts[i-1]
    if d != 900:
        gaps.append((ts[i-1], ts[i], d))
big = [g for g in gaps if g[2] > 3*24*3600]  # > 3 days
weekendish = [g for g in gaps if 900 < g[2] <= 3*24*3600]
print(f"non-15m steps: {len(gaps)} total ; <=3d (weekend-ish): {len(weekendish)} ; >3d (suspicious): {len(big)}")
for g in sorted(gaps, key=lambda x:-x[2])[:8]:
    print(f"   gap {g[2]/3600:6.1f}h  {g[0]} -> {g[1]}")

# ===== POINT 1: leg definition — pivot kind alternation =====
print("\n===== P1 PIVOT ALTERNATION (leg = pivot k -> k+1) =====")
rev = sorted((r for r in csv.DictReader(open(HERE/"true_reversals_M8.csv"))), key=lambda r:int(r["t"]))
kinds = [r["kind"] for r in rev]
same_adj = [(i, rev[i]["date"], rev[i]["kind"], rev[i+1]["date"]) for i in range(len(rev)-1) if rev[i]["kind"]==rev[i+1]["kind"]]
print(f"total pivots={len(rev)}  BOT={kinds.count('BOT')} TOP={kinds.count('TOP')}")
print(f"same-kind adjacencies (BOT->BOT or TOP->TOP) = {len(same_adj)}")
for s in same_adj[:20]:
    print(f"   idx{s[0]}: {s[2]} {s[1]}  ->next same kind {s[3]}")

# ===== rebuild rows exactly =====
def f(x): return float(x) if x not in (None,"","None") else None
def durability(i,P,kind):
    if kind=="BOT":
        mfe=P
        for k in range(i+1,len(S)):
            if S[k]["l"]<P: return k-i, mfe-P
            mfe=max(mfe,S[k]["h"])
    else:
        mfe=P
        for k in range(i+1,len(S)):
            if S[k]["h"]>P: return k-i, P-mfe
            mfe=min(mfe,S[k]["l"])
    return len(S)-1-i, abs(mfe-P)

rows=[]
for n,r in enumerate(rev):
    t=int(r["t"]); kind=r["kind"]; P=f(r["price"]); A=f(r["atr"]); i=T2I.get(t)
    if i is None or not A: continue
    nxt=rev[n+1] if n+1<len(rev) else None
    trunc=nxt is None
    j=T2I.get(int(nxt["t"])) if nxt else len(S)-1
    seg=S[i:j+1]
    if kind=="BOT":
        mfe=max(b["h"] for b in seg); ext=mfe-P; peak_k=i+max(range(len(seg)),key=lambda x:seg[x]["h"])
    else:
        mfe=min(b["l"] for b in seg); ext=P-mfe; peak_k=i+min(range(len(seg)),key=lambda x:seg[x]["l"])
    trav=sum(abs(seg[x]["c"]-seg[x-1]["c"]) for x in range(1,len(seg)))
    leg_atr=ext/A
    db_bars,db_ext=durability(i,P,kind)
    rows.append({"date":r["date"],"t":t,"kind":kind,"P":P,"A":A,"leg_atr":leg_atr,
                 "ext":ext,"peak_k":peak_k,"i":i,"j":j,"seglen":len(seg),"trav":trav,
                 "path_eff":ext/trav if trav>0 else None,
                 "durab_atr":db_ext/A,"out_atr":f(r["out_atr"]),"yr":int(r["yr"]),
                 "truncated":int(trunc),"price_P":P})

print(f"\n[rebuild] rows built = {len(rows)} (csv lab has {sum(1 for _ in open(HERE/'reversal_power.csv'))-1})")

# ===== POINT 2: ATR normalization bias by year =====
print("\n===== P2 ATR-NORMALIZATION BIAS BY YEAR =====")
byyr=defaultdict(list); atr_byyr=defaultdict(list)
for r in rows:
    byyr[r["yr"]].append(r["leg_atr"]); atr_byyr[r["yr"]].append(r["A"])
for y in sorted(byyr):
    v=byyr[y]; a=atr_byyr[y]
    print(f"  {y}: n={len(v):3d}  leg_atr med={st.median(v):5.1f} mean={st.mean(v):5.1f}  ATR med={st.median(a):5.2f}")
# correlation leg_atr vs year, leg_atr vs ATR-at-pivot, leg_usd vs ATR
import math
def corr(xs,ys):
    n=len(xs); mx=sum(xs)/n; my=sum(ys)/n
    cov=sum((x-mx)*(y-my) for x,y in zip(xs,ys))
    sx=math.sqrt(sum((x-mx)**2 for x in xs)); sy=math.sqrt(sum((y-my)**2 for y in ys))
    return cov/(sx*sy) if sx*sy else 0
yrs=[r["yr"] for r in rows]; legs=[r["leg_atr"] for r in rows]; atrs=[r["A"] for r in rows]; usds=[r["ext"] for r in rows]
print(f"  corr(leg_atr, year)      = {corr(legs,yrs):+.3f}")
print(f"  corr(leg_atr, ATR@pivot) = {corr(legs,atrs):+.3f}")
print(f"  corr(leg_usd, ATR@pivot) = {corr(usds,atrs):+.3f}")
print(f"  corr(leg_atr, leg_usd)   = {corr(legs,usds):+.3f}")

# MONSTRO tier clustering by year (recompute tiers per kind, p90)
def tier_of(vals):
    qs=st.quantiles(vals,n=10)
    def lab(v):
        if v>=qs[8]: return "MONSTRO"
        if v>=qs[6]: return "FORTE"
        if v>=qs[3]: return "MEDIO"
        return "FRACO"
    return lab,qs
tiers={}
qs_store={}
for kind in ("BOT","TOP"):
    g=[r for r in rows if r["kind"]==kind]
    lab,qs=tier_of([r["leg_atr"] for r in g]); qs_store[kind]=qs
    for r in g: r["tier"]=lab(r["leg_atr"])
mon=[r for r in rows if r["tier"]=="MONSTRO"]
print(f"  MONSTRO n={len(mon)} year distribution: {dict(Counter(r['yr'] for r in mon))}")
print(f"  ALL    year distribution: {dict(Counter(r['yr'] for r in rows))}")

# ===== POINT 4: leg_atr vs zigzag_out_atr =====
print("\n===== P4 leg_atr vs zigzag_out_atr =====")
pair=[(r["leg_atr"],r["out_atr"]) for r in rows if r["out_atr"] is not None]
diffs=[abs(a-b) for a,b in pair]
reldiff=[abs(a-b)/b for a,b in pair if b>0]
print(f"  n with out_atr={len(pair)} (of {len(rows)})")
print(f"  corr(leg_atr,out_atr) = {corr([p[0] for p in pair],[p[1] for p in pair]):+.4f}")
print(f"  median|leg_atr-out_atr| = {st.median(diffs):.3f}  ; max = {max(diffs):.2f}")
print(f"  median rel-diff = {st.median(reldiff)*100:.1f}%")
# how many exactly equal (rounded 2dp)?
eq=sum(1 for a,b in pair if abs(a-b)<0.05)
print(f"  near-equal (<0.05 ATR): {eq}/{len(pair)} = {100*eq/len(pair):.0f}%")
worst=sorted(pair,key=lambda x:-abs(x[0]-x[1]))[:6]
print(f"  worst divergences (leg_atr, out_atr): {[ (round(a,1),round(b,1)) for a,b in worst]}")

# ===== POINT 7: tier robustness — sensitivity of decile cutoffs =====
print("\n===== P7 TIER ROBUSTNESS (leave-one-out on p90 cutoff) =====")
for kind in ("BOT","TOP"):
    g=sorted([r["leg_atr"] for r in rows if r["kind"]==kind])
    base_q=st.quantiles(g,n=10)
    p90=base_q[8]
    # how many rows sit within +/-5% of p90 (flip-prone)
    near=[v for v in g if abs(v-p90)<0.05*p90]
    # leave-one-out range of p90
    p90s=[]
    for k in range(len(g)):
        gg=g[:k]+g[k+1:]
        p90s.append(st.quantiles(gg,n=10)[8])
    print(f"  {kind}: n={len(g)} p90={p90:.2f}  LOO p90 range [{min(p90s):.2f},{max(p90s):.2f}] spread={max(p90s)-min(p90s):.2f}")
    print(f"       rows within 5% of p90 cutoff (tier-flip-prone): {len(near)}")
# MONSTRO with terrible path_eff?
print("\n  MONSTRO rows ranked by path_eff (low eff = choppy leg):")
mon_sorted=sorted([r for r in rows if r["tier"]=="MONSTRO"],key=lambda r:(r["path_eff"] or 0))
for r in mon_sorted[:8]:
    print(f"   {r['date']:<17} {r['kind']} leg_atr={r['leg_atr']:5.1f} path_eff={r['path_eff']:.2f} durab_atr={r['durab_atr']:.1f}")
pe_all=[r["path_eff"] for r in rows if r["path_eff"] is not None]
pe_mon=[r["path_eff"] for r in mon if r["path_eff"] is not None]
print(f"  path_eff: all med={st.median(pe_all):.2f}  MONSTRO med={st.median(pe_mon):.2f}")
print(f"  corr(leg_atr, path_eff) = {corr(legs,[r['path_eff'] or 0 for r in rows]):+.3f}")

# ===== POINT 6: spot-check specific rows against raw bars =====
print("\n===== P6 SPOT-CHECK specific rows =====")
def manual_leg(r):
    seg=S[r["i"]:r["j"]+1]
    if r["kind"]=="BOT":
        mfe=max(b["h"] for b in seg); ext=mfe-r["P"]
    else:
        mfe=min(b["l"] for b in seg); ext=r["P"]-mfe
    return ext, mfe, len(seg)
for tgt in ["2026-03-17 05:15","2025-08-27 07:15"]:
    r=next(x for x in rows if x["date"]==tgt)
    ext,mfe,sl=manual_leg(r)
    print(f"  {tgt} {r['kind']}: P={r['P']} seg[{r['i']}..{r['j']}] len={sl} MFE={mfe:.1f} ext={ext:.1f} leg_atr={ext/r['A']:.2f} (lab={r['leg_atr']:.2f})")
# a FRACO bottom
frac=[r for r in rows if r["tier"]=="FRACO" and r["kind"]=="BOT"]
r=frac[len(frac)//2]
ext,mfe,sl=manual_leg(r)
print(f"  FRACO {r['date']} {r['kind']}: P={r['P']} seglen={sl} ext={ext:.1f} leg_atr={ext/r['A']:.2f} (lab={r['leg_atr']:.2f})")

# ===== POINT 5 framing check =====
print("\n===== P5 FORWARD-DATA FRAMING =====")
print(f"  truncated rows (last pivot, no next) = {sum(r['truncated'] for r in rows)}")
print("  leg uses S[i:j+1] where j = index of NEXT pivot => FUTURE bars by construction. Descriptive only.")

# durab vs leg separation: are they measuring different things?
print("\n===== DURAB vs LEG separation =====")
dl=[(r["leg_atr"],r["durab_atr"]) for r in rows]
print(f"  corr(leg_atr, durab_atr) = {corr([a for a,b in dl],[b for a,b in dl]):+.3f}")
print(f"  leg_atr med={st.median([a for a,b in dl]):.1f}  durab_atr med={st.median([b for a,b in dl]):.1f}")
# truncated durab (never violated)
trunc_durab=sum(1 for r in rows if r["durab_atr"]>0 and (r["i"]+1>=len(S) or True) )
