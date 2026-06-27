"""
_reopt5_bruteforce.py — exhaustive atomic-predicate generation over ALL causal features,
then greedy 1-3 combos, evaluated under the harness robustness gate.
Goal: prove (or find) any robust=True stack. RAW-causal.
Forbidden: R,win,cj,low_idx,low_t,yr,block,max_silence(const).
win=R>0.
"""
import itertools, statistics
from _reopt5_harness import ROWS, evaluate, report, BASE_WR, BASE_WINS
SENT=-10000000.0
FORB={'R','win','cj','low_idx','low_t','yr','block','max_silence'}
def nz(v): return v is not None and v!=SENT

feats=[k for k in ROWS[0].keys() if k not in FORB]
# build atomic predicates: for numeric -> >=q and <=q at deciles; binary -> ==val
preds={}
for f in feats:
    vals=[r[f] for r in ROWS if nz(r[f])]
    uniq=sorted(set(vals))
    if len(uniq)<=4:
        for u in uniq:
            preds[f'{f}=={u}']=(lambda r,f=f,u=u: nz(r[f]) and r[f]==u)
    else:
        qs=statistics.quantiles(vals,n=10)
        for i,t in enumerate(qs):
            preds[f'{f}>=q{i+1}({round(t,2)})']=(lambda r,f=f,t=t: nz(r[f]) and r[f]>=t)
            preds[f'{f}<=q{i+1}({round(t,2)})']=(lambda r,f=f,t=t: nz(r[f]) and r[f]<=t)

print(f"atomic predicates: {len(preds)}")

# evaluate each atomic as KEEP filter; keep only those that keep>=85% winners AND wr>base-0.5
singles=[]
for name,fn in preds.items():
    res=evaluate(fn,name)
    if res and res['winners_kept_pct']>=85.0:
        singles.append((name,fn,res))
print(f"single atomics passing winners>=85%: {len(singles)}")
# sort singles by wr
singles.sort(key=lambda x:-x[2]['wr_keep'])
print("top 12 singles by wr:")
for name,_,res in singles[:12]:
    print(f"  {name:32s} wr={res['wr_keep']:.2f} win%={res['winners_kept_pct']:.1f} streak={res['streak_keep']} nonworse={res['nonworse']} robust={res['robust']}")

# use the best ~30 high-winner atomics as building blocks for AND-combos (intersection)
blocks=[x for x in singles if x[2]['wr_keep']>=BASE_WR-0.3][:40]
print(f"\nbuilding-block atomics for combos: {len(blocks)}")
robust=[]; near=[]
checked=0
for r in range(1,4):
    for combo in itertools.combinations(blocks,r):
        names=[c[0] for c in combo]
        # skip same-feature contradictions handled naturally
        fns=[c[1] for c in combo]
        def keepfn(row,fns=fns):
            return all(f(row) for f in fns)
        res=evaluate(keepfn,'+'.join(names))
        checked+=1
        if res and res['winners_kept_pct']>=85.0:
            if res['robust']:
                robust.append(res)
            elif res['wr_keep']>BASE_WR and res['nonworse']>=5 and all(res['yr'][y]>=({2024:58.77,2025:63.47,2026:54.83}[y]-0.5) for y in (2024,2025,2026)):
                near.append(res)
print(f"combos checked: {checked}")
print(f"\n=== ROBUST=True combos: {len(robust)} ===")
for res in sorted(robust,key=lambda r:(r['streak_keep'],-r['wr_keep']))[:10]:
    report(res); print()
print(f"\n=== NEAR-miss (wr>base, 5/8 blocks, years within 0.5): {len(near)} ===")
for res in sorted(near,key=lambda r:(-r['wr_keep']))[:10]:
    report(res); print()
