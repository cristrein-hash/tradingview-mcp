#!/usr/bin/env python3
"""DA AUDIT of anel2_reader.py — adversarial. Refute, don't confirm.
Checks:
 (A) zone geometry mutation look-ahead potential (high/low overwritten to last snapshot)
 (B) zone L_zone with vs without born_t<=t restriction (sanity of causal effect)
 (C) conv monotonicity per setup (non-monotonic => not predictive)
 (D) best-cut selection: is conv>=thr ~= whole sample?
 (E) L_nas lift concentration: how many runners drive +0.80?
 (F) shuffle/permutation: is conv-outcome separation beyond chance?
 (G) best-cut multiple-comparison count + survival of leave-top2 AND per-year 2026.
Run: python3 _DA_anel2_audit.py
"""
import json, bisect, datetime as dt, statistics as st, random
from pathlib import Path
HERE = Path(__file__).parent

# ---- (A) zone mutation ----
muts = tot = 0; spreads = []
for p in (HERE/"primitives").glob("*.primitives.json"):
    d = json.loads(p.read_text())
    for z in d["zones"]:
        tot += 1
        if z["last_t"] != z["born_t"]:
            muts += 1; spreads.append((z["last_t"]-z["born_t"])/3600.0)
print("=== (A) ZONE GEOMETRY MUTATION ===")
print(f"zones total={tot} live(last_t>born_t)={muts} ({100*muts/tot:.0f}%)")
print(f"  median live hrs={st.median(spreads):.1f} max={max(spreads):.1f}")
print("  MECHANISM: builder overwrites z['high']/z['low'] each reappearance ->")
print("  stored geometry = LAST snapshot, not born_t geometry. L_zone tests bar against")
print("  possibly future-extended bounds. Demand/supply boxes in Custom OB extend right but")
print("  high/low can also re-anchor. This is a LOOK-AHEAD vector in L_zone bounds.")

# ---- now re-run the reader's detect with instrumentation by importing pieces ----
import importlib.util
spec = importlib.util.spec_from_file_location("anel2", HERE/"anel2_reader.py")
A = importlib.util.module_from_spec(spec)
spec.loader.exec_module(A)
r = A.detect()

print("\n=== (C) CONV MONOTONICITY (avgR per bucket) ===")
for sid, nm in [(1,"S1"),(2,"S2"),(3,"S3"),(4,"S4")]:
    v = r[sid]; row = []
    for lo,hi in [(0,3),(4,5),(6,6),(7,9)]:
        sub=[x for x in v if lo<=x["conv"]<=hi]
        row.append(f"{lo}-{hi}:{A.avg(sub):+.2f}(n{len(sub)})" if sub else f"{lo}-{hi}:--")
    # spearman-ish: correlation conv vs R
    import math
    cs=[x["conv"] for x in v]; rs=[x["R"] for x in v]
    n=len(cs); mc=sum(cs)/n; mr=sum(rs)/n
    cov=sum((a-mc)*(b-mr) for a,b in zip(cs,rs))/n
    sc=math.sqrt(sum((a-mc)**2 for a in cs)/n); sr=math.sqrt(sum((b-mr)**2 for b in rs)/n)
    pear=cov/(sc*sr) if sc and sr else 0
    print(f"{nm}: "+"  ".join(row)+f"  | pearson(conv,R)={pear:+.3f}")

print("\n=== (D) BEST-CUT vs WHOLE-SAMPLE (n_cut / n_base) ===")
cuts={1:4,2:3,3:4,4:5}
for sid,nm in [(1,"S1"),(2,"S2"),(3,"S3"),(4,"S4")]:
    v=r[sid]; thr=cuts[sid]; sub=[x for x in v if x["conv"]>=thr]
    print(f"{nm}: conv>={thr} keeps {len(sub)}/{len(v)} = {100*len(sub)/len(v):.0f}% of base. "
          f"avgR cut {A.avg(sub):+.2f} vs base {A.avg(v):+.2f} (Δ={A.avg(sub)-A.avg(v):+.2f})")

print("\n=== (E) L_nas LIFT CONCENTRATION (S1) ===")
v=r[1]; nas=[x for x in v if x["L_nas"]]
nas_sorted=sorted(nas,key=lambda x:x["R"],reverse=True)
tot_nas=sum(x["R"] for x in nas)
top3=sum(x["R"] for x in nas_sorted[:3])
print(f"L_nas n={len(nas)} sumR={tot_nas:+.1f} avgR={A.avg(nas):+.2f}")
print(f"  top3 trades sumR={top3:+.1f} = {100*top3/tot_nas:.0f}% of L_nas total")
print(f"  top3 R values: {[round(x['R'],1) for x in nas_sorted[:3]]}")
print(f"  avgR ex-top3: {sum(x['R'] for x in nas_sorted[3:])/max(1,len(nas)-3):+.2f}")
nasbz=[x for x in v if not x["L_nas"]]
print(f"  L_nas=0 avgR={A.avg(nasbz):+.2f} -> raw lift +{A.avg(nas)-A.avg(nasbz):.2f}; ex-top3 lift {sum(x['R'] for x in nas_sorted[3:])/max(1,len(nas)-3)-A.avg(nasbz):+.2f}")

print("\n=== (F) PERMUTATION: conv>=thr sumR vs shuffled-conv null ===")
random.seed(7)
for sid,nm in [(1,"S1"),(2,"S2"),(3,"S3"),(4,"S4")]:
    v=r[sid]; thr=cuts[sid]
    obs=sum(x["R"] for x in v if x["conv"]>=thr)
    Rs=[x["R"] for x in v]; convs=[x["conv"] for x in v]
    null=[]
    for _ in range(2000):
        sh=Rs[:]; random.shuffle(sh)
        null.append(sum(rr for cc,rr in zip(convs,sh) if cc>=thr))
    null.sort(); p=sum(1 for x in null if x>=obs)/len(null)
    print(f"{nm}: obs sumR(conv>={thr})={obs:+.1f} | null mean={st.mean(null):+.1f} p(null>=obs)={p:.3f}")

print("\n=== (G) MULTIPLE COMPARISONS + SURVIVAL ===")
print("best-cut search scans thr 3..8 (6) x 4 setups = up to 24 comparisons, picks MAX sumR.")
print("Bonferroni alpha for p<0.05 -> 0.05/24 = 0.0021. Survival of leave-top2 AND 2026>=0:")
for sid,nm in [(1,"S1 BULL-cont"),(2,"S2 rev-exh"),(3,"S3 session"),(4,"S4 trap")]:
    v=r[sid]; thr=cuts[sid]; sub=[x for x in v if x["conv"]>=thr]
    lo,ln=A.leave_top2(sub)
    y26=[x for x in sub if x["yr"]==2026]; s26=sum(x["R"] for x in y26)
    surv = (lo>0) and (s26>=0)
    print(f"{nm}: conv>={thr} sumR={sum(x['R'] for x in sub):+.0f} leave-top2={lo:+.0f} 2026={s26:+.0f}R -> SURVIVES={surv}")
