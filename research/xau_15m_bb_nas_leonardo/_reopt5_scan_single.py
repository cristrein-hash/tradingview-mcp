"""
_reopt5_scan_single.py — single-feature WR scan to find directional edges.

Lens: VOL/session, but scan ALL 48 causal features for context.
For each numeric feature, compute WR in deciles. For each binary, WR by 0/1.
Prints features where a tail/bin lifts WR meaningfully (>=62%) with reasonable n,
prioritizing VOL/session features.

Output is materialized to _reopt5_scan_single.out.txt for reproducibility.
"""
import sys, json
sys.path.insert(0, "/Users/cristrein/tradingview-mcp/research/xau_15m_bb_nas_leonardo")
import _reopt5_lib as L

rows = L.load()
FORBIDDEN = L.FORBIDDEN | {"win","R","cj","low_idx","block","low_t","yr"}

# feature universe = keys present, minus forbidden
keys = set()
for r in rows: keys.update(r.keys())
feats = sorted(k for k in keys if k not in FORBIDDEN)

VOL_SESSION = {"atr_regime","vol_low_vs_med","vol_climax","vpnode_dist_atr",
               "is_london_open","is_ny_overlap","is_deadzone","killzone"}

SENTINEL = -10000000.0

def vals(f):
    return [r.get(f) for r in rows if r.get(f) is not None and r.get(f)!=SENTINEL]

def wr(sub):
    if not sub: return None,0
    return 100*sum(r["win"] for r in sub)/len(sub), len(sub)

out = []
def p(s): out.append(s); print(s)

p(f"BASE WR={L.BASE_WR} n={len(rows)}")
p("="*80)

import numpy as np
for f in feats:
    v = vals(f)
    if not v: continue
    uniq = sorted(set(v))
    is_bin = set(uniq) <= {0,1} or len(uniq)<=2
    tag = "[VS]" if f in VOL_SESSION else "    "
    if is_bin:
        line=[f"{tag} {f} (binary {uniq})"]
        for u in uniq:
            sub=[r for r in rows if r.get(f)==u]
            w,n=wr(sub)
            line.append(f"  ={u}: WR={w:.1f} n={n}")
        p("".join(line))
    else:
        arr=np.array(v)
        qs=np.quantile(arr,[0,.1,.25,.5,.75,.9,1.0])
        # bottom and top tertile WR
        lo_th=np.quantile(arr,0.33); hi_th=np.quantile(arr,0.67)
        lo=[r for r in rows if r.get(f) is not None and r.get(f)!=SENTINEL and r.get(f)<=lo_th]
        hi=[r for r in rows if r.get(f) is not None and r.get(f)!=SENTINEL and r.get(f)>=hi_th]
        wlo,nlo=wr(lo); whi,nhi=wr(hi)
        p(f"{tag} {f}: range[{qs[0]:.2f},{qs[-1]:.2f}] med={qs[3]:.2f} | "
          f"low(<= {lo_th:.2f}) WR={wlo:.1f} n={nlo} | high(>= {hi_th:.2f}) WR={whi:.1f} n={nhi}")

with open("/Users/cristrein/tradingview-mcp/research/xau_15m_bb_nas_leonardo/_reopt5_scan_single.out.txt","w") as fh:
    fh.write("\n".join(out))
