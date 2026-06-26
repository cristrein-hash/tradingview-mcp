"""Final adversarial checks on winner A (h1_notup & lo_h4_eff):
 - streak recomputed explicitly chronological
 - WR with the broken 2025-05 block EXCLUDED (is edge carried by it?)
 - what gets cut: WR of cut set per year (should be << base)
 - small refinement sweep on h4_eff threshold
RAW-causal. win=R>0.
"""
import sys
sys.path.insert(0,'/Users/cristrein/tradingview-mcp/research/xau_15m_bb_nas_leonardo')
from _disc8_lib import load, max_losing_streak

rows=load(); N=len(rows)
BASE=sum(r['win'] for r in rows)/N
def g(r,k): return r.get(k)

def cutA(r):
    return g(r,'h1_trend')!=1 and g(r,'h4_eff') is not None and g(r,'h4_eff')<=0.24

kept=[r for r in rows if not cutA(r)]
cut=[r for r in rows if cutA(r)]
print(f"BASE WR={BASE:.4f} streak={max_losing_streak(rows)}")
print(f"A kept={len(kept)} wr={sum(r['win'] for r in kept)/len(kept):.4f} streak_kept={max_losing_streak(kept)}")
# cut-set WR by year
for y in (2024,2025,2026):
    cy=[r for r in cut if r['yr']==y]
    print(f"  CUT y{y}: n={len(cy)} cutWR={sum(r['win'] for r in cy)/len(cy):.3f}")

# exclude broken block 2025-05-25 entirely, re-eval edge
broken='2025-05-25'
sub=[r for r in rows if r['block']!=broken]
ks=[r for r in sub if not cutA(r)]
bs=sum(r['win'] for r in sub)/len(sub)
print(f"\nExcl broken block {broken}: subBASE={bs:.4f} A-kept WR={sum(r['win'] for r in ks)/len(ks):.4f} (edge persists if > subBASE)")

# threshold sweep on h4_eff
print("\nh4_eff threshold sweep (cut h1_notup & h4_eff<=T):")
for T in (0.18,0.20,0.22,0.24,0.26,0.28,0.30):
    def c(r,T=T): return g(r,'h1_trend')!=1 and g(r,'h4_eff') is not None and g(r,'h4_eff')<=T
    k=[r for r in rows if not c(r)]; cu=[r for r in rows if c(r)]
    wk=sum(r['win'] for r in k)
    yb={y:(lambda s:(sum(x['win'] for x in s)/len(s),len(s)))([r for r in k if r['yr']==y]) for y in (2024,2025,2026)}
    allyr=all(yb[y][0]>=BASE for y in (2024,2025,2026))
    print(f"  T={T}: keep={len(k)} wr={wk/len(k):.4f} Wkept={100*wk/sum(r['win'] for r in rows):.1f}% "
          f"streak={max_losing_streak(k)} y24={yb[2024][0]:.3f} y25={yb[2025][0]:.3f} y26={yb[2026][0]:.3f} allyr>=base={allyr}")
