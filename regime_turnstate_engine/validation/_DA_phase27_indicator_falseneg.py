#!/usr/bin/env python3
"""DA FALSE-NEGATIVE audit of phase27_indicator_front.py on the 70 RANGE trades (2023+).
Question: did phase27 KILL a real indicator signal via bad feature extraction, or is the front genuinely null?

Checks (priority order):
 1. RSI DIVERGENCE (the user's actual hypothesis) — bull divergence: price lower-low while RSI higher-low
    over recent swing, computed CAUSALLY from raw rsi+close bars. Plus rsi_min-over-8 (exhaustion) and rsi slope.
    phase27 only used SCALAR rsi level at entry — a different feature.
 2. NAS extraction — phase27 used max(x). Empirically x=0 is the MOST RECENT NAS label, x=max the OLDEST
    (window shifts by dropping low-x first, new labels enter at low x). So phase27 read NAS BACKWARDS.
    Recompute "fresh NAS LONG near entry price" correctly.
 3. Bubble window/polarity — phase27 used within<=12, SELL={6,8,10}. Test windows {8,12,16,24} and both polarities.
 4. SHIFT1 — bubbles/nas/smc from bar i-1 (repaint guard); rsi/close from closed bar i. Correct; no over-shift.
 5. Verdict — enumerate ALL corrected candidate rules, permutation-null-of-max (400 shuffles). A corrected
    feature counts as a MISSED signal only if it beats null-of-max at p<0.10. Default = genuinely null.
"""
import json,csv,io,contextlib,sys,datetime as dt,random
from pathlib import Path
import statistics as st
random.seed(20260701)
COST=0.35
VAL=Path("/Users/cristrein/tradingview-mcp/regime_turnstate_engine/validation");sys.path.insert(0,str(VAL))
with contextlib.redirect_stdout(io.StringIO()):
    import phase10_hybrid_regime as P
    P.run(0.03,1.15,0.88)
T=P.T
segs=[s for s in json.load(open("/tmp/causal_segments_v10.json")) if s["regime"]=="RANGE"]
D=Path("/Users/cristrein/tradingview-mcp/my-strategy/research/revalidation/XAU_4H_L2_BPT_BOS_CHOCH/v1")
raw={int(json.loads(l)["ts_epoch"]):json.loads(l) for l in open(D/"repro_recovery/raw_features_2020_2026.jsonl")}
def rf(bi):
    return raw.get(int(T[bi]))

# causal per-bar series (rsi, close) indexed by bar_idx, for divergence lookback
RSI=[None]*len(T); CLOSE=[None]*len(T)
for bi in range(len(T)):
    d=rf(bi)
    if d:
        RSI[bi]=d.get("rsi"); CLOSE[bi]=d.get("close")

SELL={"plot_6","plot_8","plot_10"};BUY={"plot_0","plot_2","plot_4"}
def has_bubble(d,pset,within):
    return any(b.get("plot_id") in pset and b.get("bars_ago",99)<=within for b in (d.get("bubbles_recent") or []))

# ---- corrected NAS: x=0 = most recent. "fresh LONG near entry": among NAS with price within band of entry close,
#      take the one with LOWEST x (most recent) -> its text. Also raw "most-recent NAS text" = x=0 element.
def nas_recent_text(d):
    ns=d.get("nas_recent") or []
    if not ns: return None
    return min(ns,key=lambda z:z.get("x",1e9)).get("text")   # x=0 = newest
def nas_near_entry(d,entry_price,band_frac=0.02):
    ns=d.get("nas_recent") or []
    if not ns or entry_price is None: return None
    band=entry_price*band_frac
    cand=[n for n in ns if n.get("price") is not None and abs(n["price"]-entry_price)<=band]
    if not cand: return None
    return min(cand,key=lambda z:z.get("x",1e9)).get("text")   # nearest-in-price, most recent by x

# ---- RSI bull divergence (causal): over lookback L, find the two most recent local price lows;
#      bull-div = later low is LOWER in price but HIGHER in rsi.
def local_lows(bi,L):
    lows=[]
    lo=max(0,bi-L)
    for j in range(lo+1,bi):   # strictly before entry bar i (uses closed bars < i)
        if CLOSE[j] is None or RSI[j] is None: continue
        pl=CLOSE[j-1];pr=CLOSE[j+1]
        if pl is None or pr is None: continue
        if CLOSE[j]<=pl and CLOSE[j]<=pr:
            lows.append((j,CLOSE[j],RSI[j]))
    return lows
def bull_div(bi,L):
    lows=local_lows(bi,L)
    if len(lows)<2: return None
    (j1,p1,r1),(j2,p2,r2)=lows[-2],lows[-1]   # earlier, later
    if p2<p1 and r2>r1: return True            # price LL, rsi HL -> bull divergence
    return False
def rsi_min_recent(bi,n=8):
    vals=[RSI[j] for j in range(max(0,bi-n+1),bi+1) if RSI[j] is not None]
    return min(vals) if vals else None
def rsi_slope(bi,n=4):
    a=RSI[bi-n] if bi-n>=0 else None; b=RSI[bi]
    if a is None or b is None: return None
    return b-a

# ---- build trade table
tr=[]
for r in csv.DictReader(open(D/"results/l2_bpt_regua_structural.csv")):
    bi=int(r["bar_idx"]);t=T[bi];y=dt.datetime.utcfromtimestamp(t).year
    if y<2023: continue
    if not any(s['start']<=t<=s['end'] for s in segs): continue
    R=round(float(r["letrun_struct"])-COST,2)
    entry=float(r["entry"])
    d_i=rf(bi) or {};d_s=rf(bi-1) or {}   # rsi/close at i; repaint features at i-1
    rec={"bi":bi,"date":dt.datetime.utcfromtimestamp(t).strftime("%Y-%m-%d"),"R":R,"win":R>0,"yr":y,
         "entry":entry,"rsi":d_i.get("rsi"),
         "rsi_min8":rsi_min_recent(bi,8),"rsi_slope4":rsi_slope(bi,4),
         "bulldiv10":bull_div(bi,10),"bulldiv14":bull_div(bi,14),"bulldiv20":bull_div(bi,20),
         # bubbles SHIFT1 across windows/polarity
         "bs8":has_bubble(d_s,SELL,8),"bs12":has_bubble(d_s,SELL,12),"bs16":has_bubble(d_s,SELL,16),"bs24":has_bubble(d_s,SELL,24),
         "bb8":has_bubble(d_s,BUY,8),"bb12":has_bubble(d_s,BUY,12),"bb16":has_bubble(d_s,BUY,16),"bb24":has_bubble(d_s,BUY,24),
         # NAS corrected (SHIFT1)
         "nas_recent_txt":nas_recent_text(d_s),
         "nas_near":nas_near_entry(d_s,entry,0.02),
         "nas_near_wide":nas_near_entry(d_s,entry,0.04),
         # NAS WRONG (phase27 way, max-x) for contrast
         "nas_maxx":(max(d_s.get("nas_recent") or [{"x":-1,"text":None}],key=lambda z:z.get("x",-1)).get("text") if d_s.get("nas_recent") else None),
         }
    tr.append(rec)
W=[x for x in tr if x["win"]];Lz=[x for x in tr if not x["win"]]
print(f"RANGE-trades 2023+: {len(tr)} ({len(W)}W/{len(Lz)}L) | sumR base {sum(x['R'] for x in tr):+.1f}")

print("\n### POINT 2 sanity — NAS ordering (x=0 newest vs phase27 max-x oldest) ###")
mismatch=sum(1 for x in tr if x['nas_recent_txt']!=x['nas_maxx'])
print(f"  trades where corrected(x=0) text != phase27(max-x) text: {mismatch}/{len(tr)}  (proves phase27 read NAS backwards on these)")

print("\n### CHARACTERIZATION (WIN vs LOSS means / rates — exploratory) ###")
def m(rs,k):
    v=[x[k] for x in rs if x.get(k) is not None];return st.mean(v) if v else float('nan')
for k in ("rsi","rsi_min8","rsi_slope4"):
    print(f"  {k:12} WIN {m(W,k):+6.1f}  LOSS {m(Lz,k):+6.1f}")
def rate(rs,k,val=True):
    n=len(rs); return 100*sum(1 for x in rs if x.get(k)==val)/n if n else 0
for k in ("bulldiv10","bulldiv14","bulldiv20","bs12","bs16","bb12","bb16"):
    print(f"  {k:12} WIN {rate(W,k):4.0f}%  LOSS {rate(Lz,k):4.0f}%")
for k in ("nas_near","nas_recent_txt"):
    for v in ("LONG","SHORT"):
        print(f"  {k}=={v:5} WIN {rate(W,k,v):4.0f}%  LOSS {rate(Lz,k,v):4.0f}%")

def curve(rs):
    rs=sorted(rs,key=lambda x:x["bi"]);n=len(rs)
    if not n: return (0,0,0,0)
    s=sum(x["R"] for x in rs);w=sum(1 for x in rs if x["win"]);cum=peak=dd=0
    for x in rs: cum+=x["R"];peak=max(peak,cum);dd=min(dd,cum-peak)
    return (n,100*w/n,s,dd)
def show(nm,rs):
    n,wr,s,dd=curve(rs);print(f"  {nm:40} N={n:2} WR={wr:3.0f}% sumR={s:+6.1f} DD={dd:6.1f}")

# ---- enumerate ALL corrected candidate rules (keep-the-trade predicate)
rules={}
# RSI level (phase27 grid) for continuity
for thr in (45,50,55,60,65):
    rules[f"skip rsi>={thr}"]=[x for x in tr if not (x['rsi'] is not None and x['rsi']>=thr)]
# rsi_min8 exhaustion: keep only oversold-recent (a comprable bottom shows exhaustion)
for thr in (35,40,45):
    rules[f"keep rsi_min8<={thr}"]=[x for x in tr if x['rsi_min8'] is not None and x['rsi_min8']<=thr]
# rsi slope up (turning)
rules["keep rsi_slope4>0"]=[x for x in tr if x['rsi_slope4'] is not None and x['rsi_slope4']>0]
# RSI BULL DIVERGENCE — the actual hypothesis, keep only div bars
for L in (10,14,20):
    rules[f"keep bulldiv{L}"]=[x for x in tr if x[f'bulldiv{L}']]
# divergence combined with exhaustion
rules["keep bulldiv14 & rsi_min8<=40"]=[x for x in tr if x['bulldiv14'] and x['rsi_min8'] is not None and x['rsi_min8']<=40]
# bubbles corrected windows/polarity (SELL=absorption-at-bottom per memory)
for w in (8,12,16,24):
    rules[f"keep bub_SELL<={w}"]=[x for x in tr if x[f'bs{w}']]
    rules[f"keep bub_BUY<={w}"]=[x for x in tr if x[f'bb{w}']]
# NAS corrected: keep only fresh-LONG near entry (reversal signal at range bottom)
rules["keep nas_near==LONG"]=[x for x in tr if x['nas_near']=="LONG"]
rules["keep nas_near_wide==LONG"]=[x for x in tr if x['nas_near_wide']=="LONG"]
rules["skip nas_recent_txt==SHORT"]=[x for x in tr if x['nas_recent_txt']!="SHORT"]
# a couple of convergences
rules["keep bulldiv14 | bub_SELL<=12"]=[x for x in tr if x['bulldiv14'] or x['bs12']]
rules["keep rsi<55 & bub_SELL<=16"]=[x for x in tr if (x['rsi'] is not None and x['rsi']<55) and x['bs16']]

print("\n### CORRECTED CANDIDATE RULES (let-run canonical) ###")
show("BASE (no filter)",tr)
for nm,rs in rules.items(): show(nm,rs)

# ---- permutation-null-of-max over ALL enumerated rules
def best_sum(Rmap):
    best=-1e9
    for rs in rules.values():
        if not rs: continue
        s=sum(Rmap[x["bi"]] for x in rs)
        best=max(best,s)
    return best
obs_best=best_sum({x["bi"]:x["R"] for x in tr})
best_name=max((k for k in rules if rules[k]),key=lambda k:sum(x["R"] for x in rules[k]))
Rs=[x["R"] for x in tr];bis=[x["bi"] for x in tr]
ge=0;ND=400
for _ in range(ND):
    sh=Rs[:];random.shuffle(sh);Rmap=dict(zip(bis,sh))
    if best_sum(Rmap)>=obs_best: ge+=1
p=ge/ND
print(f"\n### PERMUTATION-NULL-OF-MAX ({ND} draws, {sum(1 for r in rules.values() if r)} non-empty rules) ###")
print(f"  best rule = '{best_name}'  sumR={sum(x['R'] for x in rules[best_name]):+.1f} (N={len(rules[best_name])})")
print(f"  best sumR observed among rules = {obs_best:+.1f}")
print(f"  P(null best-rule >= observed)  = {p:.3f}   -> {'PASSES p<0.10 (candidate missed signal)' if p<0.10 else 'FAILS (null / overfit — front dead)'}")

# per-year robustness of best rule
print(f"\n### best rule per-year vs base ###")
for y in (2023,2024,2025,2026):
    b=[x for x in tr if x['yr']==y];f=[x for x in rules[best_name] if x['yr']==y]
    print(f"  {y}: base {sum(x['R'] for x in b):+6.1f} (n{len(b)}) -> best {sum(x['R'] for x in f):+6.1f} (n{len(f)})")

print(f"\n### VERDICT ###")
if p<0.10:
    print(f"  (b) CANDIDATE SIGNAL: '{best_name}' beats null-of-max at p={p:.3f}. Inspect per-year robustness above before trusting.")
else:
    print(f"  (a) GENUINELY NULL. Best corrected feature '{best_name}' does NOT beat null-of-max (p={p:.3f}). Indicator front dead on these 70 range trades.")
