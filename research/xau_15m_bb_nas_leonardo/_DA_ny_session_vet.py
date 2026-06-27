#!/usr/bin/env python3
"""DEVIL'S ADVOCATE — VET BALANCEADO do lead NY-session (winners 15h UTC / losers 11h UTC; NY 13-18 WR46 vs base 39).
Itens: (1) DST/sessao mapping check; (2) NY remove-top2-blocks; (3) null shuffle de horas (4-bucket multitest);
(4) NY-conditioning sobre BASE LARGA (with_macro todas direcoes, n=131) com mesma logica de outcome do gate_v2;
(5) confound macro-window (NY ~ 2024 BULL?). Causal RAW, sem look-ahead. Verified 2026-06-26."""
import csv, json, statistics as st, random, datetime as dt
from pathlib import Path
HERE = Path(__file__).parent
PRIM = {p.name.split(".")[0].replace("XAUUSD_15m_replay_", ""): json.loads(p.read_text())
        for p in (HERE / "primitives").glob("*.primitives.json")}
SER = {b: pr["series"] for b, pr in PRIM.items()}
TID = {b: {x["t"]: i for i, x in enumerate(s)} for b, s in SER.items()}
K, HMAX, MIN_RISK_ATR, R_CAP, RUNNER = 2, 480, 0.5, 15.0, 3.0

def conf_low(s, i):
    L=[b["l"] for b in s]; lo=max(K,i-120); best=None
    for p in range(lo,i-K+1):
        if L[p]==min(L[p-K:p+K+1]): best=L[p]
    return best

def outcome(s, ei, entry, sl0, long, atr):
    """Replica gate_v2.outcome (trailing swing, simetrico)."""
    struct=(entry-sl0) if long else (sl0-entry)
    if struct<=0: return None
    risk=max(struct,MIN_RISK_ATR*atr); sl0=(entry-risk) if long else (entry+risk)
    trail=sl0; r1=False; mfe=0.0; ex=None; end=min(ei+HMAX,len(s)-1)
    for i in range(ei+1,end+1):
        bar=s[i]
        if long:
            mfe=max(mfe,(bar["h"]-entry)/risk)
            if bar["l"]<=trail: ex=trail; break
            if (bar["h"]-entry)/risk>=1: r1=True
            if r1:
                sw=conf_low(s,i)
                if sw: trail=max(trail,sw-0.1*atr)
        else:
            mfe=max(mfe,(entry-bar["l"])/risk)
            if bar["h"]>=trail: ex=trail; break
            if (entry-bar["l"])/risk>=1: r1=True
            if r1:
                H=[x["h"] for x in s]; lo=max(K,i-120); sh=None
                for p in range(lo,i-K+1):
                    if H[p]==max(H[p-K:p+K+1]): sh=H[p]
                if sh: trail=min(trail,sh+0.1*atr)
    if ex is None: ex=s[end]["c"]
    R=((ex-entry) if long else (entry-ex))/risk
    return max(-1.0,min(R_CAP,R)), mfe

def build_wide():
    """Base LARGA = with_macro (todas direcoes), SEM cbfs-gate, outcome do gate_v2."""
    out=[]
    for r in csv.DictReader(open(HERE/"candidates_annotated.csv")):
        if r["setup_vs_macro"]!="with_macro": continue
        b=r["block"]; s=SER.get(b); ei=TID.get(b,{}).get(int(r["entry_t"]))
        if s is None or ei is None or ei+2>=len(s): continue
        entry=float(r["entry_close"]); zlo=float(r["zone_low"]); zhi=float(r["zone_high"]); zwa=float(r["zone_width_atr"])
        atr=(zhi-zlo)/zwa if zwa>0 else None
        if not atr: continue
        long=r["dir"]=="LONG"; sl0=(zlo-0.1*atr) if long else (zhi+0.1*atr)
        oc=outcome(s,ei,entry,sl0,long,atr)
        if not oc: continue
        R,mfe=oc; t=int(r["entry_t"])
        out.append({"block":b,"t":t,"dir":r["dir"],"R":R,"mfe":mfe,"win":R>0,"runner":mfe>=RUNNER,
                    "hr":dt.datetime.utcfromtimestamp(t).hour,
                    "hour_csv":int(r.get("hour_utc",-1) or -1)})
    return out

def stats(sub):
    n=len(sub); w=sum(1 for r in sub if r["win"]); sm=sum(r["R"] for r in sub)
    return n,(100*w/n if n else 0),(sm/n if n else 0),sm

def span_weeks(sub):
    if len(sub)<2: return 1
    return (max(r["t"] for r in sub)-min(r["t"] for r in sub))/(7*86400) or 1

# ---------------------------------------------------------------------------
print("="*78)
print("ITEM 1 — DST / SESSION MAPPING CHECK")
print("="*78)
# XAU CME/forex sessions in UTC: London ~07-16 UTC (08-16 BST in summer, 08-17 GMT winter).
# NY equities open 13:30 UTC (summer EDT) / 14:30 UTC (winter EST). NY 'killzone' ~12-15 UTC.
# Verify: are entry hours UTC-derived consistently? Compare hr (from t) vs hour_utc col.
wide=build_wide()
mism=[r for r in wide if r["hour_csv"]>=0 and r["hour_csv"]!=r["hr"]]
print(f"  base larga with_macro: n={len(wide)} (LONG+SHORT)")
print(f"  hr(from t) vs hour_utc(csv) mismatches: {len(mism)}  -> {'CONSISTENT' if not mism else 'CHECK'}")
print(f"  hour range present: {min(r['hr'] for r in wide)}..{max(r['hr'] for r in wide)}")
print("  NOTE: 13-18 UTC bucket spans NY-open (13:30 EDT summer / 14:30 EST winter).")
print("  Winter trades labeled '13' are PRE-NY-open (14:30 EST). Off-by-DST risk: ~1h drift.")

# ---------------------------------------------------------------------------
print("\n"+"="*78)
print("ITEM 2 — NY (13-18) on v2 candidate: remove top-2 blocks")
print("="*78)
v2=[r for r in csv.DictReader(open(HERE/"candidates_v2_final.csv")) if r["t"]!="t"]
for r in v2:
    r["R"]=float(r["R"]); r["win"]=(r["win"]=="True"); r["t"]=int(r["t"]); r["hr"]=dt.datetime.utcfromtimestamp(r["t"]).hour
ny=[r for r in v2 if 13<=r["hr"]<19]
n,wr,avg,sm=stats(ny); print(f"  NY all: n={n} WR={wr:.0f}% avgR={avg:+.2f} sumR={sm:+.1f} freq={n/span_weeks(ny):.2f}/wk")
byb={}
for r in ny: byb.setdefault(r["block"][:16],[]).append(r)
top2=sorted(byb,key=lambda b:sum(x["R"] for x in byb[b]),reverse=True)[:2]
rest=[r for r in ny if r["block"][:16] not in top2]
n2,wr2,avg2,sm2=stats(rest)
print(f"  top2 blocks by sumR: {top2}")
print(f"  NY minus top2: n={n2} WR={wr2:.0f}% avgR={avg2:+.2f} sumR={sm2:+.1f}")
posb=sum(1 for b in byb if sum(x['R'] for x in byb[b])>0)
print(f"  NY blocks net-positive: {posb}/{len(byb)}")

# ---------------------------------------------------------------------------
print("\n"+"="*78)
print("ITEM 3 — NULL: shuffle hours, re-bucket, how often does a 6-hr bucket beat base by +7pp?")
print("="*78)
base_wr=stats(v2)[1]
buckets=[(0,7),(7,13),(13,19),(19,24)]
real_best=max(stats([r for r in v2 if lo<=r["hr"]<hi])[1] for lo,hi in buckets if [r for r in v2 if lo<=r["hr"]<hi])
random.seed(42); N=5000; hits_ny=0; hits_anybucket=0
hours=[r["hr"] for r in v2]; wins=[r["win"] for r in v2]; Rs=[r["R"] for r in v2]
for _ in range(N):
    sh=hours[:]; random.shuffle(sh)
    perm=[{"hr":h,"win":w,"R":rr} for h,w,rr in zip(sh,wins,Rs)]
    bwrs=[]
    for lo,hi in buckets:
        sub=[p for p in perm if lo<=p["hr"]<hi]
        if len(sub)>=15: bwrs.append(100*sum(1 for p in sub if p["win"])/len(sub))
    if bwrs and max(bwrs)>=base_wr+7: hits_anybucket+=1
    nysub=[p for p in perm if 13<=p["hr"]<19]
    if nysub and 100*sum(1 for p in nysub if p["win"])/len(nysub)>=46: hits_ny+=1
print(f"  base WR={base_wr:.0f}%  real NY WR=46%  real best-bucket WR={real_best:.0f}%")
print(f"  null P(any bucket n>=15 beats base+7pp)= {hits_anybucket/N:.3f}")
print(f"  null P(NY-position WR>=46%)= {hits_ny/N:.3f}")

# ---------------------------------------------------------------------------
print("\n"+"="*78)
print("ITEM 4 — NY conditioning on BROADER base with_macro (n~131, LONG+SHORT), outcome=gate_v2")
print("="*78)
def report(rows,label):
    n,wr,avg,sm=stats(rows); run=sum(1 for r in rows if r["runner"])
    print(f"  [{label:>20}] n={n} WR={wr:.0f}% avgR={avg:+.2f} sumR={sm:+.1f} run={run} freq={n/span_weeks(rows):.2f}/wk")
report(wide,"ALL with_macro")
for lab,lo,hi in [("Asia 00-06",0,7),("London 07-12",7,13),("NY 13-18",13,19),("Eve 19-23",19,24)]:
    report([r for r in wide if lo<=r["hr"]<hi],lab)
# leave-one-block-out on the wide NY
wny=[r for r in wide if 13<=r["hr"]<19]
print("  -- wide NY per block --")
wbyb={}
for r in wny: wbyb.setdefault(r["block"][:16],[]).append(r)
for b in sorted(wbyb):
    n,wr,avg,sm=stats(wbyb[b]); print(f"     {b}: n={n} WR={wr:.0f}% sumR={sm:+.1f}")
wt2=sorted(wbyb,key=lambda b:sum(x["R"] for x in wbyb[b]),reverse=True)[:2]
wrest=[r for r in wny if r["block"][:16] not in wt2]
n,wr,avg,sm=stats(wrest); print(f"  wide NY minus top2 {wt2}: n={n} WR={wr:.0f}% sumR={sm:+.1f}")

# ---------------------------------------------------------------------------
print("\n"+"="*78)
print("ITEM 5 — CONFOUND: is NY proxying the 2024 BULL window? hour x block crosstab")
print("="*78)
# For the wide base: what fraction of NY trades fall in 2024 blocks vs 2025?
def yr(b): return b[:4]
ny_yr={}
for r in wny: ny_yr[yr(r["block"])]=ny_yr.get(yr(r["block"]),0)+1
all_yr={}
for r in wide: all_yr[yr(r["block"])]=all_yr.get(yr(r["block"]),0)+1
print(f"  NY trades by year: {ny_yr}")
print(f"  ALL trades by year: {all_yr}")
# WR by year, NY vs non-NY, to disentangle
for y in sorted(all_yr):
    nyy=[r for r in wide if yr(r['block'])==y and 13<=r['hr']<19]
    nnyy=[r for r in wide if yr(r['block'])==y and not(13<=r['hr']<19)]
    a=stats(nyy); b=stats(nnyy)
    print(f"  {y}: NY n={a[0]} WR={a[1]:.0f}% sumR={a[3]:+.1f} | non-NY n={b[0]} WR={b[1]:.0f}% sumR={b[3]:+.1f}")
