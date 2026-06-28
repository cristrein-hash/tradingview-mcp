#!/usr/bin/env python3
"""Deep verification of the single PASS loser-filter combo for XAU 15M LONG BOTTOM.
Base: swept-sempre + h1_pos>=0.44 (always ON). Candidate = rsi_cj(hi,q0.33)+micro_bos_up(hi,q0.33).
Runs: (1) reproduce panel via score_lens math, (2) leave-one-YEAR-out, (3) per-block (calendar
quarter) stability, (4) orthogonality to h1_pos (does rsi_cj/micro_bos_up just re-select high h1_pos?),
(5) marginal value of each leg alone, (6) Bonferroni context (27 combos tested).
RAW-causal, single-source math copied from score_lens.apply/panel. Reproducible/committed."""
import json, statistics as st, random
from pathlib import Path
HERE = Path(__file__).parent
RECS = [json.loads(l) for l in (HERE/"sweptsempre_micro.jsonl").read_text().splitlines()]
for r in RECS:
    r["_F"] = {**r["micro"], **{k:v for k,v in r["feat"].items() if isinstance(v,(int,float))}}
H = [r for r in RECS if r.get("h1_pos",0.5) >= 0.44]  # h1_pos base always applied

def quant(vals,q):
    vs=sorted(vals); i=min(len(vs)-1,max(0,int(q*len(vs)))); return vs[i]
def apply(combo,pool):
    kept=pool
    for c in combo:
        ft=c["feat"]; q=c["q"]
        vals=[r["_F"][ft] for r in kept if r["_F"].get(ft) is not None]
        if len(vals)<10: continue
        thr=quant(vals,q); kept=[r for r in kept if r["_F"].get(ft) is None or r["_F"][ft]>=thr]
    return kept
def panel(rows):
    R=[x["R"] for x in sorted(rows,key=lambda z:z["cj_t"])]; n=len(R)
    if not n: return None
    sm=sum(R); w=sum(1 for x in R if x>0); eq=pk=dd=0
    for x in R: eq+=x; pk=max(pk,eq); dd=min(dd,eq-pk)
    py={y:round(sum(x["R"] for x in rows if x["yr"]==y),1) for y in (2024,2025,2026)}
    return {"N":n,"WR":round(100*w/n,1),"sumR":round(sm,1),"avgR":round(sm/n,3),"DD":round(dd,1),
            "losers":sum(1 for x in R if x<=0),"runners":sum(1 for x in R if x>=3),"yr":py}

WIN = [{"feat":"rsi_cj","dir":"hi","q":0.33},{"feat":"micro_bos_up","dir":"hi","q":0.33}]

base = panel(H)
kept = apply(WIN,H); after = panel(kept)
print("=== BASE (h1_pos>=0.44) ==="); print(json.dumps(base))
print("=== AFTER (rsi_cj+micro_bos_up) ==="); print(json.dumps(after))

# 1) Leave-one-YEAR-out: refit thresholds on remaining years, score held-out year
print("\n=== LEAVE-ONE-YEAR-OUT (refit thr on other yrs, score on held-out) ===")
for hold in (2024,2025,2026):
    train=[r for r in H if r["yr"]!=hold]; test=[r for r in H if r["yr"]==hold]
    # compute thresholds on train, apply to test
    keep=test
    for c in WIN:
        ft=c["feat"]; vals=[r["_F"][ft] for r in train if r["_F"].get(ft) is not None]
        thr=quant(vals,c["q"]); keep=[r for r in keep if r["_F"].get(ft) is None or r["_F"][ft]>=thr]
    b=panel(test); a=panel(keep)
    if a is None: print(f"  hold {hold}: empty after filter"); continue
    print(f"  hold {hold}: base N{b['N']} avgR{b['avgR']} sumR{b['sumR']} -> after N{a['N']} avgR{a['avgR']} sumR{a['sumR']} DD{a['DD']} (dAvg{round(a['avgR']-b['avgR'],3):+})")

# 2) Per calendar-quarter stability of the in-sample filter
print("\n=== PER-QUARTER (in-sample applied) ===")
def qid(t): import datetime as dt; d=dt.datetime.utcfromtimestamp(t); return f"{d.year}Q{(d.month-1)//3+1}"
byq={}
for r in kept: byq.setdefault(qid(r["cj_t"]),[]).append(r)
for q in sorted(byq):
    rs=byq[q]; sm=sum(x["R"] for x in rs); n=len(rs); w=sum(1 for x in rs if x["R"]>0)
    print(f"  {q}: N{n:>3} WR{round(100*w/n):>3} sumR{round(sm,1):>7}")

# 3) Orthogonality to h1_pos: does the filter just re-select high h1_pos?
print("\n=== ORTHOGONALITY to h1_pos ===")
h1_base=[r.get("h1_pos",0.5) for r in H]; h1_kept=[r.get("h1_pos",0.5) for r in kept]
print(f"  h1_pos mean: base {st.mean(h1_base):.3f} | kept {st.mean(h1_kept):.3f} | median base {st.median(h1_base):.3f} kept {st.median(h1_kept):.3f}")
# control: cut same N by top-h1_pos only, compare avgR
ncut=base["N"]-after["N"]
by_h1=sorted(H,key=lambda r:-r.get("h1_pos",0.5))[:base["N"]-ncut]
ph1=panel(by_h1)
print(f"  control 'keep top {base['N']-ncut} by h1_pos': avgR{ph1['avgR']} sumR{ph1['sumR']} DD{ph1['DD']} vs combo avgR{after['avgR']} sumR{after['sumR']} DD{after['DD']}")

# 4) Marginal value of each leg alone
print("\n=== EACH LEG ALONE ===")
for c in WIN:
    a=panel(apply([c],H))
    print(f"  {c['feat']} q{c['q']}: N{a['N']} avgR{a['avgR']} sumR{a['sumR']} DD{a['DD']} yr{a['yr']}")

# 5) NULL (random cut same N) + Bonferroni note
print("\n=== NULL (500 random cuts of same N) ===")
rng=random.Random(20260628); avs=[]
for _ in range(500):
    idx=set(rng.sample(range(len(H)),ncut)); kk=[H[i] for i in range(len(H)) if i not in idx]
    avs.append(panel(kk)["avgR"])
p=sum(1 for x in avs if x>=after["avgR"])/len(avs)
print(f"  null avgR mean {st.mean(avs):.3f} p95 {sorted(avs)[475]:.3f} | combo {after['avgR']} | p={p:.3f}")
print(f"  Bonferroni: 27 combos tested -> alpha 0.05/27 = {0.05/27:.4f}; raw p={p:.3f} -> {'PASS' if p<0.05/27 else 'FAIL'} corrected")
