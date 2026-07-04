#!/usr/bin/env python3
"""LAB B r2 — REGIME BOX probe 4 (LOOK #3): regra final RB-SKIP-1 — métricas de cluster/multi-stop.
RB-SKIP-1: v5h==BULL ∧ prev_hi_dist_atr∈(−10,−2] ∧ (n_supply_overhead>=16 ∨ rbox_age_h∈(178,415])."""
import json,datetime as dt
from pathlib import Path
from collections import Counter,defaultdict
HERE=Path(__file__).parent
FE=json.loads((HERE/"_labB_r2_regime_box_feats.json").read_text())
ALL=[json.loads(l) for l in (HERE/"lab_g_candidates.jsonl").read_text().splitlines()]
_b={r["cj_t"]:r for r in ALL if r.get("g_in_base435")==1 and r.get("g_v5h")!="BEAR"}
assert len(FE)==435 and len(_b)==435
for f in FE:
    f["net"]=f["g_R"]-0.80/f["g_risk"]; f["n_supply_overhead"]=_b[f["cj_t"]]["n_supply_overhead"]
def flag(f):
    p=f["prev_hi_dist_atr"]
    return (f["v5h"]=="BULL" and p is not None and -10<p<=-2 and (f["n_supply_overhead"]>=16 or 178<f["rbox_age_h"]<=415))
FL=[f for f in FE if flag(f)]
print(f"RB-SKIP-1 flags: N{len(FL)} (losers {sum(1 for f in FL if f['net']<=0)}, runners {sum(1 for f in FL if f['g_R']>=3)}, sumNET {sum(f['net'] for f in FL):+.1f})")
for f in sorted(FL,key=lambda z:z["cj_t"]):
    print(f"  {dt.datetime.utcfromtimestamp(f['cj_t']).strftime('%Y-%m-%d %H:%M')} net{f['net']:+.2f}")
def cluster_metrics(rows,tag):
    rows=sorted(rows,key=lambda z:z["cj_t"])
    net=[r["net"] for r in rows]
    eq=pk=dd=0.0; ddi=None
    for i,x in enumerate(net):
        eq+=x; pk=max(pk,eq)
        if eq-pk<dd: dd=eq-pk; ddi=i
    wl=defaultdict(float); dl=defaultdict(float); dstops=Counter()
    for r in rows:
        d=dt.datetime.utcfromtimestamp(r["cj_t"]).strftime("%Y-%m-%d")
        wl[r["g_week"]]+=r["net"]; dl[d]+=r["net"]
        if r["net"]<=-0.9: dstops[d]+=1
    wworst=sorted(wl.values())[:3]; dworst=sorted(dl.values())[:3]
    multi=sum(1 for c in dstops.values() if c>=2); multi3=sum(1 for c in dstops.values() if c>=3)
    ddw=dt.datetime.utcfromtimestamp(rows[ddi]["cj_t"]).strftime("%Y-%m-%d") if ddi is not None else "-"
    print(f"{tag:<22} DD{dd:>6.1f} (fim {ddw}) | piores semanas {['%.1f'%v for v in wworst]} | piores dias {['%.1f'%v for v in dworst]} | dias 2+ full-stops {multi} | 3+ {multi3}")
S={f["cj_t"] for f in FL}
cluster_metrics(FE,"BASE 435")
cluster_metrics([f for f in FE if f["cj_t"] not in S],"BASE − RB-SKIP-1")
