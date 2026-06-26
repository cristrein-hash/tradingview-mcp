"""DA verification of entry rule.
RULE: macro_drop_atr<4 & disp4_atr<-0.5
R field = R_reclaim, universe = all rows (reproduces reported n=294/WR48.6/avgR1.628).

Checks:
 1. per-year avgR (sign stability)
 2. leave-one-block-out (8 blocks) -> worst fold avgR
 3. ex-top1 / ex-top2 (carried by 1-2 trades?)
 4. look-ahead sanity: features used are bar-of-reclaim; flag any outcome-derived feature.
 5. multiple-testing context: how many 2-feature threshold rules of similar form beat this avgR by chance.
"""
import json
from collections import defaultdict

rows = [json.loads(l) for l in open('entry_dataset.jsonl')]

def sub(rows):
    return [r for r in rows if r['macro_drop_atr'] < 4 and r['disp4_atr'] < -0.5]

s = sub(rows)
RF = 'R_reclaim'
vals = [r[RF] for r in s]
n = len(vals)
avg = sum(vals)/n
wr = sum(1 for v in vals if v>0)/n*100
print(f"=== BASE: n={n} WR={wr:.1f} avgR={avg:.3f} sumR={sum(vals):.1f}")

# 1. per year
print("\n--- per YEAR ---")
by_yr = defaultdict(list)
for r in s:
    by_yr[r['yr']].append(r[RF])
peryear_signs = []
for y in sorted(by_yr):
    v = by_yr[y]
    a = sum(v)/len(v)
    peryear_signs.append(a)
    print(f"  y{y}: n={len(v):3d} avgR={a:.3f} WR={sum(1 for x in v if x>0)/len(v)*100:.1f}")
peryear_ok = all(a > 0 for a in peryear_signs)
print(f"  peryear_ok (all positive): {peryear_ok}")

# 2. leave-one-block-out
print("\n--- LEAVE-ONE-BLOCK-OUT ---")
blocks = sorted(set(r['block'] for r in s))
worst = None
for b in blocks:
    v = [r[RF] for r in s if r['block'] != b]
    a = sum(v)/len(v)
    # also report the held-out block itself
    vb = [r[RF] for r in s if r['block'] == b]
    ab = sum(vb)/len(vb) if vb else float('nan')
    print(f"  drop {b}: rest n={len(v):3d} avgR={a:.3f} | block n={len(vb):3d} blkAvgR={ab:.3f}")
    if worst is None or a < worst:
        worst = a
print(f"  worst-fold (rest) avgR = {worst:.3f}")

# per-block standalone avgR sign stability
print("\n--- per BLOCK standalone ---")
blk_avgs=[]
for b in blocks:
    vb=[r[RF] for r in s if r['block']==b]
    a=sum(vb)/len(vb)
    blk_avgs.append(a)
    print(f"  {b}: n={len(vb):3d} avgR={a:.3f}")
print(f"  blocks positive: {sum(1 for a in blk_avgs if a>0)}/{len(blk_avgs)}  min={min(blk_avgs):.3f}")

# 3. ex-top1 / ex-top2
print("\n--- EX-TOP ---")
sv = sorted(vals, reverse=True)
print(f"  top5 R: {[round(x,2) for x in sv[:5]]}")
for k in [1,2,3]:
    rem = sv[k:]
    a = sum(rem)/len(rem)
    print(f"  ex-top{k}: n={len(rem)} avgR={a:.3f}")

# contribution of top2
top2sum = sum(sv[:2])
print(f"  top2 sumR={top2sum:.1f} of total {sum(vals):.1f} = {top2sum/sum(vals)*100:.1f}%")

# 4. look-ahead: list features in rule and whether outcome-derived
print("\n--- LOOK-AHEAD on rule features ---")
print("  macro_drop_atr, disp4_atr = pre-reclaim structure (4-bar displacement, macro decline).")
print("  Neither is an outcome (R/held8/runner/near_M8). OK if computed from bars <= reclaim bar.")

# 5. multiple-testing: scan many 2-feature threshold rules, see rank of this avgR
print("\n--- MULTIPLE-TESTING CONTEXT ---")
import itertools
feat_cols = ['rsi','rsi_low','dist_ema_atr','ema_slope_atr','macro_drop_atr','macro_retr',
             'sweep_depth_atr','disp4_atr','disp8_atr','up_closes8','range_exp','leg_ext',
             'room_atr','low_wick','low_closepos','atr_regime','vol_low_vs_med','sell_pol']
# build candidate thresholds (quartiles) per feature, both directions
def quantiles(col):
    xs=sorted(r[col] for r in rows if r.get(col) is not None)
    return [xs[int(len(xs)*q)] for q in (0.25,0.5,0.75)]
qs={c:quantiles(c) for c in feat_cols}
results=[]
MIN_N=150
for (c1,c2) in itertools.combinations(feat_cols,2):
    for t1 in qs[c1]:
        for d1 in ('<','>'):
            for t2 in qs[c2]:
                for d2 in ('<','>'):
                    def ok(r):
                        v1=r.get(c1); v2=r.get(c2)
                        if v1 is None or v2 is None: return False
                        a = v1<t1 if d1=='<' else v1>t1
                        b = v2<t2 if d2=='<' else v2>t2
                        return a and b
                    ss=[r[RF] for r in rows if ok(r)]
                    if len(ss)>=MIN_N:
                        results.append((sum(ss)/len(ss),len(ss),f"{c1}{d1}{t1:.3g} & {c2}{d2}{t2:.3g}"))
results.sort(reverse=True)
print(f"  scanned {len(results)} rules with n>={MIN_N}")
print(f"  top of scan avgR={results[0][0]:.3f}  median scan avgR={results[len(results)//2][0]:.3f}")
print(f"  our rule avgR={avg:.3f} — rank among scan:")
better=sum(1 for a,_,_ in results if a>=avg)
print(f"    {better} of {len(results)} scanned rules (n>={MIN_N}) reach avgR>={avg:.3f} ({better/len(results)*100:.1f}%)")
print("  top10 scan rules:")
for a,nn,desc in results[:10]:
    print(f"    avgR={a:.3f} n={nn} :: {desc}")

# summary verdict
print("\n=== SUMMARY ===")
print(f"peryear_ok={peryear_ok} worst_block_fold={worst:.3f} extop2_avg={sum(sv[2:])/len(sv[2:]):.3f}")
