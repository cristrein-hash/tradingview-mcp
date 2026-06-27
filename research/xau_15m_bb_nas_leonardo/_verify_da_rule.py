import json, statistics
rows=[json.loads(l) for l in open('entry_dataset.jsonl')]

def sel(r):
    return (r['dist_ema_atr']<0 and r['ema_slope_atr']>0 and r['smc_bos']==1)

hit=[r for r in rows if sel(r)]
R=[r['R_reclaim'] for r in hit]  # R_reclaim never null per earlier check
n=len(R)
wr=sum(1 for x in R if x>0)/n*100
avg=sum(R)/n
print(f"n={n} WR={wr:.1f} avgR={avg:.3f} sumR={sum(R):.1f}")

# per year
print("--- per year ---")
peryear={}
for yr in (2024,2025,2026):
    rr=[r['R_reclaim'] for r in hit if r['yr']==yr]
    peryear[yr]=sum(rr)/len(rr) if rr else None
    print(f"{yr}: n={len(rr)} avgR={(sum(rr)/len(rr)):.3f}" if rr else f"{yr}: n=0")

# leave-one-block-out
print("--- leave-one-block-out (avgR of REMAINING) ---")
blocks=sorted(set(r['block'] for r in hit))
folds={}
for b in blocks:
    rr=[r['R_reclaim'] for r in hit if r['block']!=b]
    folds[b]=sum(rr)/len(rr)
    # also the held-out block itself
    ho=[r['R_reclaim'] for r in hit if r['block']==b]
    hoavg=sum(ho)/len(ho) if ho else None
    print(f"drop {b}: remain n={len(rr)} avgR={folds[b]:.3f} | block n={len(ho)} blockAvgR={hoavg:.3f}")
worst=min(folds.values())
print(f"worst leave-block-out avgR={worst:.3f}")

# per-block avgR sign check (stationarity)
print("--- per-block avgR ---")
for b in blocks:
    bb=[r['R_reclaim'] for r in hit if r['block']==b]
    print(f"{b}: n={len(bb)} avgR={(sum(bb)/len(bb)):.3f}")

# ex-top2 / ex-top5
Rs=sorted(R,reverse=True)
for k in (1,2,5):
    rem=Rs[k:]
    print(f"ex-top{k}: n={len(rem)} avgR={sum(rem)/len(rem):.3f} sumR={sum(rem):.1f}")

# top contributors
print("top5 R:",[round(x,2) for x in Rs[:5]])
print("WR breakdown wins/losses:",sum(1 for x in R if x>0),sum(1 for x in R if x<=0))

# --- concentration / cap analysis ---
print("--- concentration ---")
caps=[x for x in R if x>=18]
print(f"trades>=18R: {len(caps)} sum={sum(caps):.1f} of total {sum(R):.1f}")
print(f"median R={statistics.median(R)} mean={avg:.3f}")
losers=[x for x in R if x<=0]
print(f"losers n={len(losers)} avgLoser={sum(losers)/len(losers):.3f} minR={min(R)}")
print(f"ex-top10 avgR={sum(Rs[10:])/len(Rs[10:]):.3f} n={len(Rs[10:])}")
print(f"top5 sumR frac={sum(Rs[:5])/sum(R)*100:.1f}% top10 frac={sum(Rs[:10])/sum(R)*100:.1f}%")

# --- look-ahead sanity: confirm rule features are bar-of-reclaim, no outcome fields ---
feats_used=['dist_ema_atr','ema_slope_atr','smc_bos']
outcome_fields=['R_reclaim','held8','runner','R_8atr','near_M8']
print("--- look-ahead check ---")
print("rule features:",feats_used,"-> none in outcome set:",
      all(f not in outcome_fields for f in feats_used))
