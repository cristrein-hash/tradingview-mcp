"""
_reopt5_flow_adversarial_audit.py — SELF adversarial audit (my own synthesis; the
Agent tool is not available in this context, so this is hand-written analysis, not a
spawned reviewer). Audits the FLOW-lens robust candidates against the 6 mandated checks.
A1 = disp4_atr>=0.78 & dist_supply_atr>=-0.28
A2 = h1_pos>=0.65 & disp4_atr>=0.78
S3 = h1_pos>=0.65   (convergent with the multi-TF lens R2 axis)
RAW-causal. win=R>0.
"""
import math, statistics
from _reopt5_harness import ROWS, BASE_WR, BASE_WINS, BASE_N, BASE_YR, BLOCKS, BASE_BLOCK
SENT=-10000000.0
def nz(v): return v is not None and v!=SENT
A1=lambda r: nz(r['disp4_atr']) and r['disp4_atr']>=0.78 and nz(r['dist_supply_atr']) and r['dist_supply_atr']>=-0.28
A2=lambda r: nz(r['h1_pos']) and r['h1_pos']>=0.65 and nz(r['disp4_atr']) and r['disp4_atr']>=0.78
S3=lambda r: nz(r['h1_pos']) and r['h1_pos']>=0.65
CANDS={'A1':A1,'A2':A2,'S3':S3}
def wr(rows): return 100*sum(r['win'] for r in rows)/len(rows) if rows else float('nan')

print("### Q4 POWER: keep vs CUT two-proportion z (discriminative) ###")
for nm,fn in CANDS.items():
    keep=[r for r in ROWS if fn(r)]; cut=[r for r in ROWS if not fn(r)]
    n1,x1=len(keep),sum(r['win'] for r in keep); n2,x2=len(cut),sum(r['win'] for r in cut)
    pp=(x1+x2)/(n1+n2); se=math.sqrt(pp*(1-pp)*(1/n1+1/n2)); z=(x1/n1-x2/n2)/se
    print(f"  {nm}: keepWR {x1/n1*100:.2f}(n{n1}) cutWR {x2/n2*100:.2f}(n{n2}) z={z:.2f} {'SIG' if abs(z)>1.96 else 'ns'}")

print("\n### Q3 SELECTION/Bonferroni: ~10,700 combos tested. z_crit~4.42 ###")
for nm,fn in CANDS.items():
    keep=[r for r in ROWS if fn(r)]; cut=[r for r in ROWS if not fn(r)]
    n1,x1=len(keep),sum(r['win'] for r in keep); n2,x2=len(cut),sum(r['win'] for r in cut)
    pp=(x1+x2)/(n1+n2); se=math.sqrt(pp*(1-pp)*(1/n1+1/n2)); z=(x1/n1-x2/n2)/se
    print(f"  {nm}: z={z:.2f} -> {'SURVIVES Bonferroni' if abs(z)>4.42 else 'FAILS Bonferroni (selection-fragile)'}")

print("\n### Q6a LEAVE-ONE-YEAR-OUT lift ###")
for nm,fn in CANDS.items():
    print(f"  {nm}:", end=' ')
    for y in (2024,2025,2026):
        sub=[r for r in ROWS if r['yr']==y]; keep=[r for r in sub if fn(r)]
        print(f"{y} d{wr(keep)-BASE_YR[y]:+.2f}", end='  ')
    print()

print("\n### Q6b LEAVE-ONE-BLOCK-OUT delta stability ###")
for nm,fn in CANDS.items():
    ds=[]
    for b in BLOCKS:
        pool=[r for r in ROWS if r['block']!=b]
        ds.append(wr([r for r in pool if fn(r)])-wr(pool))
    print(f"  {nm}: d[{min(ds):+.2f},{max(ds):+.2f}] mean{statistics.mean(ds):+.2f} allpos={all(d>0 for d in ds)}")

print("\n### Q5 WORST-BLOCK behaviour (2026-02-25 chop) ###")
for nm,fn in CANDS.items():
    b='2026-02-25'; sub=[r for r in ROWS if r['block']==b]
    print(f"  {nm}: {b} base {BASE_BLOCK[b]:.1f} -> {wr([r for r in sub if fn(r)]):.1f}")

print("\n### Q1 LOOK-AHEAD note ###")
print("  disp4_atr/dist_supply_atr/h1_pos/rsi computed up to the 5ATR entry bar (at-entry/structural).")
print("  No daily-close (D0) feature in the stack. CAVEAT: disp4/dist_supply provenance not re-audited here.")

print("\n### Q2 IN-SAMPLE: thresholds 0.78/-0.28/0.65 are dataset deciles -> tuned in-sample;")
print("  mitigated by LOBO/LOYO folds all-positive and coarse decile (not point) thresholds.")
