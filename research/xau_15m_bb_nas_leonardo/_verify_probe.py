"""DA probe: identify which R field + universe reproduces reported n=294, avgR=1.628.
Rule: macro_drop_atr<4 & disp4_atr<-0.5
Reported: n=294 WR=48.6 avgR=1.628 y24=1.985 y25=1.446 y26=1.558
"""
import json

rows = [json.loads(l) for l in open('entry_dataset.jsonl')]

def sub(rows):
    return [r for r in rows if r['macro_drop_atr'] < 4 and r['disp4_atr'] < -0.5]

for rf in ['R_reclaim', 'R_8atr']:
    for univ_name, univ in [('all', rows), ('R8_notnull', [r for r in rows if r['R_8atr'] is not None])]:
        s = sub(univ)
        vals = [r[rf] for r in s if r[rf] is not None]
        if not vals:
            continue
        n = len(vals)
        wr = sum(1 for v in vals if v > 0) / n * 100
        avg = sum(vals) / n
        print(f"rf={rf:10s} univ={univ_name:12s} n={n:4d} WR={wr:5.1f} avgR={avg:.3f}")
