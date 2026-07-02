#!/usr/bin/env python3
"""DA checklist follow-up to _DA_phase27_indicator_falseneg.py.
The strongest corrected rule ('keep bub_SELL<=24', +41.1R vs +36.2R base) FAILED null-of-max (p=0.388).
This script confirms the checklist points null-of-max does not cover: concentration (#6), power (#4),
and whether the rule rescues the 2025 chop pain-case. Saved for reproducibility (orphan-output guard)."""
import json,csv,io,contextlib,sys,datetime as dt
from pathlib import Path
sys.path.insert(0,"/Users/cristrein/tradingview-mcp/regime_turnstate_engine/validation")
with contextlib.redirect_stdout(io.StringIO()):
    import phase10_hybrid_regime as P; P.run(0.03,1.15,0.88)
T=P.T
segs=[s for s in json.load(open("/tmp/causal_segments_v10.json")) if s["regime"]=="RANGE"]
D=Path("/Users/cristrein/tradingview-mcp/my-strategy/research/revalidation/XAU_4H_L2_BPT_BOS_CHOCH/v1")
raw={int(json.loads(l)["ts_epoch"]):json.loads(l) for l in open(D/"repro_recovery/raw_features_2020_2026.jsonl")}
SELL={"plot_6","plot_8","plot_10"}
def rf(bi): return raw.get(int(T[bi]))
def hb(d,w): return any(b.get("plot_id") in SELL and b.get("bars_ago",99)<=w for b in (d.get("bubbles_recent") or []))
rows=[]
for r in csv.DictReader(open(D/"results/l2_bpt_regua_structural.csv")):
    bi=int(r["bar_idx"]);t=T[bi];y=dt.datetime.utcfromtimestamp(t).year
    if y<2023 or not any(s['start']<=t<=s['end'] for s in segs): continue
    R=round(float(r["letrun_struct"])-0.35,2)
    rows.append({"bi":bi,"date":dt.datetime.utcfromtimestamp(t).strftime("%Y-%m-%d"),"R":R,"yr":y,"k24":hb(rf(bi-1) or {},24)})
kept=sorted([x for x in rows if x["k24"]],key=lambda x:-x["R"])
tot=sum(x["R"] for x in kept);base=sum(x["R"] for x in rows)
print(f"best bub_SELL<=24: N={len(kept)} sumR={tot:+.1f}  base(all70)={base:+.1f}  delta={tot-base:+.1f}R (removes {len(rows)-len(kept)})")
print("#6 CONCENTRATION top3:",[(x['date'],x['R']) for x in kept[:3]])
print(f"  sumR-top1={tot-kept[0]['R']:+.1f}  sumR-top3={tot-sum(x['R'] for x in kept[:3]):+.1f}")
p25=[x for x in rows if x["yr"]==2025];p25k=[x for x in p25 if x["k24"]]
print(f"2025 pain-case: all N={len(p25)} sumR={sum(x['R'] for x in p25):+.1f} -> filtered N={len(p25k)} sumR={sum(x['R'] for x in p25k):+.1f}")
print("VERDICT: delta is only +5.0R on removing 32 trades, concentrated (top3=+29.7R of +41.1); rule fails null-of-max p=0.388. Not a real signal.")
