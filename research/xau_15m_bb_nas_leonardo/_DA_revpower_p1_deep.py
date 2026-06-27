#!/usr/bin/env python3
"""Deep dive P1: the 4 TOP->TOP same-kind adjacencies. Each leg there uses NEXT TOP as endpoint
(wrong leg = TOP-to-TOP instead of TOP-to-BOT). Quantify corruption + check block-boundary link."""
import json, csv
from pathlib import Path
HERE=Path(__file__).parent
bars={}
for p in sorted((HERE/"primitives").glob("*.primitives.json")):
    for b in json.loads(p.read_text())["series"]:
        bars.setdefault(b["t"],b)
S=[bars[t] for t in sorted(bars)]
T2I={b["t"]:i for i,b in enumerate(S)}
def f(x): return float(x) if x not in (None,"","None") else None
rev=sorted((r for r in csv.DictReader(open(HERE/"true_reversals_M8.csv"))),key=lambda r:int(r["t"]))

print("=== The 4 same-kind adjacencies: what the leg measures ===")
for n in range(len(rev)-1):
    if rev[n]["kind"]==rev[n+1]["kind"]:
        a,b2=rev[n],rev[n+1]
        ia,ib=T2I[int(a["t"])],T2I[int(b2["t"])]
        seg=S[ia:ib+1]
        P=f(a["price"]);A=f(a["atr"])
        if a["kind"]=="BOT":
            mfe=max(x["h"] for x in seg);ext=mfe-P
        else:
            mfe=min(x["l"] for x in seg);ext=P-mfe
        gapbars=ib-ia
        # time gap between the two pivots (detect block-boundary weekend)
        tgap=(int(b2["t"])-int(a["t"]))/3600
        print(f"\n pivot[{n}] {a['kind']} {a['date']} P={P} block={a['block']}")
        print(f"   ->next {b2['kind']} {b2['date']} block={b2['block']}  (Δ={tgap:.0f}h, {gapbars} bars)")
        print(f"   leg measured TOP-to-TOP: ext={ext:.1f} leg_atr={ext/A:.2f}  out_atr(file)={b2.get('in_atr')}/{a['out_atr']}")
        same_block = a['block']==b2['block']
        print(f"   same block? {same_block}  (if different => missing-BOT likely at block seam)")
