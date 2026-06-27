import json
from collections import defaultdict

rows = [json.loads(l) for l in open('entry_dataset.jsonl')]

def R(r):
    v = r.get('R_reclaim')
    return v if v is not None else 0.0

def rule(r):
    return r['rsi'] >= 48.01 and r['disp4_atr'] < -0.898

sel = [r for r in rows if rule(r)]
n = len(sel)
Rs = [R(r) for r in sel]
wins = sum(1 for r in sel if R(r) > 0)
avg = sum(Rs)/n
print(f"=== RULE: rsi>=48.01 AND disp4_atr<-0.898 ===")
print(f"n={n}  WR={wins/n:.3f}  avgR={avg:.3f}  sumR={sum(Rs):.1f}")

# per year
print("\n--- per YEAR ---")
for yr in sorted(set(r['yr'] for r in sel)):
    g=[r for r in sel if r['yr']==yr]; gR=[R(r) for r in g]
    print(f"  y{yr}: n={len(g)} WR={sum(1 for x in gR if x>0)/len(g):.3f} avgR={sum(gR)/len(g):.3f}")

# per block + leave-one-block-out
print("\n--- per BLOCK ---")
blocks=sorted(set(r['block'] for r in sel))
for b in blocks:
    g=[r for r in sel if r['block']==b]; gR=[R(r) for r in g]
    print(f"  {b}: n={len(g)} avgR={sum(gR)/len(g):+.3f}")

print("\n--- LEAVE-ONE-BLOCK-OUT (avgR of remainder) ---")
worst=None
for b in blocks:
    rem=[R(r) for r in sel if r['block']!=b]
    a=sum(rem)/len(rem)
    print(f"  drop {b}: n={len(rem)} avgR={a:+.3f}")
    if worst is None or a<worst[1]: worst=(b,a)
print(f"WORST FOLD: drop {worst[0]} -> avgR={worst[1]:+.3f}")

# ex-top2 (remove 2 largest R contributors)
print("\n--- EX-TOP2 ---")
srt=sorted(sel,key=R,reverse=True)
top2=srt[:2]
print(f"  top2 R: {[round(R(x),2) for x in top2]} blocks={[x['block'] for x in top2]} yrs={[x['yr'] for x in top2]}")
rest=srt[2:]
restR=[R(r) for r in rest]
print(f"  ex-top2: n={len(rest)} avgR={sum(restR)/len(rest):+.3f} sumR={sum(restR):.1f}")
# ex-top5 for extra context
rest5=srt[5:]; r5=[R(r) for r in rest5]
print(f"  ex-top5: n={len(rest5)} avgR={sum(r5)/len(rest5):+.3f}")

# per-year ex-top2 sanity (does any year flip sign?)
print("\n--- per YEAR sign check (avgR) ---")
yvals={}
for yr in sorted(set(r['yr'] for r in sel)):
    g=[R(r) for r in sel if r['yr']==yr]
    yvals[yr]=sum(g)/len(g)
signs=set(1 if v>0 else -1 for v in yvals.values())
print("  year avgRs:", {k:round(v,3) for k,v in yvals.items()}, "ALL SAME SIGN:", len(signs)==1)

# block sign check
bsigns=set()
for b in blocks:
    g=[R(r) for r in sel if r['block']==b]
    bsigns.add(1 if sum(g)/len(g)>0 else -1)
print("  block signs all same:", len(bsigns)==1)

# look-ahead check: is near_M8 / runner / R_8atr used? Rule only uses rsi + disp4_atr.
print("\n--- FEATURE PROVENANCE ---")
print("  rule features: rsi, disp4_atr (both bar-of-reclaim features, not outcome)")
print("  NOT used: near_M8, runner, R_8atr, held8 (outcome leakage) -> OK")

# overlap with PRIMARY claim — need primary def. Report distribution
print("\n--- distribution of R ---")
import statistics
print(f"  median R={statistics.median(Rs):.3f}  max={max(Rs):.2f} min={min(Rs):.2f}")
neg=sum(1 for x in Rs if x<0); pos=sum(1 for x in Rs if x>0); zero=sum(1 for x in Rs if x==0)
print(f"  pos={pos} neg={neg} zero={zero}")
