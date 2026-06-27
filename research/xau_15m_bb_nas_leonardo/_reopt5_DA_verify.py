"""
_reopt5_DA_verify.py — Devil's-Advocate verification of the top CUT-union finalists.

Finalists (from _reopt5_cutwhen.py, robust gate pass):
  C1 = CUT near_climax | macro_bear | nas_after_smc           (WR 62.92, blk8/8)
  C2 = CUT macro_bear | nas_after_smc                          (WR 62.58, blk8/8)  [cross-lens core]
  C3 = CUT near_climax | macro_bear                            (WR 62.54, blk7/8)  [lens+macro]
  C4 = CUT near_climax  (vpnode_dist<=2 AND vol_climax>=1.5)   (WR 61.00, blk6/8)  [PURE VOL/session]
  Also re-check inherited R_B-style and R2 KEEP for honesty.

Adversarial axes (per régua + A1' SUPERTREND lesson):
 1. Look-ahead: all CUT predicates use signal-bar state only (asserted by feature provenance).
 2. Selection/multi-test: ~575 unions tested -> Bonferroni-aware. Report binomial p of the
    cut-pocket being loser-dense vs base, and whether lift survives being 1-of-575.
 3. Leave-one-CLAUSE-out: does any single clause carry the WR lift?
 4. Leave-one-BLOCK-out: is the lift block-concentrated?
 5. Threshold perturbation +-20% on numeric thresholds (vpnode_dist, vol_climax).
 6. Cut-pocket winner cost: are cut winners cheap (avgR) = scratch, not runners?
 7. Streak: max losing streak before/after.
RAW-causal.
"""
import sys, json, math
sys.path.insert(0,"/Users/cristrein/tradingview-mcp/research/xau_15m_bb_nas_leonardo")
import _reopt5_lib as L

rows=L.load()
BASE_STREAK=L.max_losing_streak(rows)
out=[]
def p(s): out.append(str(s)); print(s)

def near_climax(r,dthr=2.0,vthr=1.5): return r.get("vpnode_dist_atr",9)<=dthr and r.get("vol_climax",0)>=vthr
def macro_bear(r): return r.get("macro_bear")==1
def nas_after(r): return r.get("naslong_after_smc")==1

FIN = {
 "C1 near_climax|macro_bear|nas_after_smc": lambda r: near_climax(r) or macro_bear(r) or nas_after(r),
 "C2 macro_bear|nas_after_smc":             lambda r: macro_bear(r) or nas_after(r),
 "C3 near_climax|macro_bear":               lambda r: near_climax(r) or macro_bear(r),
 "C4 near_climax (PURE lens)":              lambda r: near_climax(r),
}

def report(name, cutfn):
    kept=[r for r in rows if not cutfn(r)]
    cut=[r for r in rows if cutfn(r)]
    m=L.metrics(kept,rows)
    rob=L.is_robust(m) and m["streak_keep"]<=BASE_STREAK
    cw=100*sum(r["win"] for r in cut)/len(cut) if cut else None
    cut_win=[r for r in cut if r["win"]==1]
    cut_win_avgR=sum(r["R"] for r in cut_win)/len(cut_win) if cut_win else 0
    cut_win_big=sum(1 for r in cut_win if r["R"]>=2)
    # binomial p: cut-pocket WR < base under H0 p=base
    from math import comb
    n=len(cut); k=sum(r["win"] for r in cut); pb=L.BASE_WR/100
    # one-sided p(X<=k) approx normal
    mu=n*pb; sd=math.sqrt(n*pb*(1-pb))
    z=(k+0.5-mu)/sd if sd>0 else 0
    p(f"\n### {name}")
    p(f"  kept n={m['n_keep']} WR={m['wr_keep']}(b{L.BASE_WR}) avgR={m['avgR']} sumR={m['sumR']} "
      f"streak {BASE_STREAK}->{m['streak_keep']} winK={m['winners_kept_pct']}% losC={m['losers_cut_pct']}% ROBUST={rob}")
    p(f"  yr={m['by_year']} (b{L.YEAR_BASE}) blkOK={m['blocks_ok']}/8")
    p(f"  CUT-pocket: n={n} WR={cw:.1f} z={z:.2f} | cut-winners avgR={cut_win_avgR:.2f} #R>=2={cut_win_big} "
      f"(scratch if avgR<base avgR 0.30 & few big)")
    return m,rob

p("="*80); p("FINALIST FULL METRICS + cut-pocket character")
mets={}
for nm,fn in FIN.items():
    mets[nm]=report(nm,fn)

# ---- Leave-one-CLAUSE-out for C1 ----
p("="*80); p("LEAVE-ONE-CLAUSE-OUT (C1 = near_climax|macro_bear|nas_after_smc)")
clauses={"near_climax":near_climax,"macro_bear":macro_bear,"nas_after_smc":nas_after}
for drop in clauses:
    keep_cl=[c for c in clauses if c!=drop]
    fn=lambda r,kc=keep_cl: any(clauses[c](r) for c in kc)
    kept=[r for r in rows if not fn(r)]
    m=L.metrics(kept,rows)
    p(f"  drop {drop}: WR={m['wr_keep']} winK={m['winners_kept_pct']}% blk{m['blocks_ok']}/8 yr={m['by_year']} "
      f"robust={L.is_robust(m) and m['streak_keep']<=BASE_STREAK}")
p("  (if dropping a clause keeps WR>base & robust => clause not sole carrier)")

# ---- Leave-one-BLOCK-out for C1 ----
p("="*80); p("LEAVE-ONE-BLOCK-OUT lift (C1): WR(kept)-WR(base) within each held-out fold")
c1=FIN["C1 near_climax|macro_bear|nas_after_smc"]
for b in L.BLOCK_ORDER:
    sub=[r for r in rows if r["block"]!=b]
    base_wr=100*sum(r["win"] for r in sub)/len(sub)
    kept=[r for r in sub if not c1(r)]
    kwr=100*sum(r["win"] for r in kept)/len(kept)
    p(f"  drop {b}: base{base_wr:.2f} -> kept{kwr:.2f}  lift {kwr-base_wr:+.2f}")

# ---- Threshold perturbation on near_climax (C4 pure lens) ----
p("="*80); p("THRESHOLD PERTURBATION near_climax (vpnode_dist thr x vol_climax thr), CUT-pocket WR")
for d in (1.5,1.8,2.0,2.4):
    rowline=[]
    for v in (1.3,1.5,1.8):
        cut=[r for r in rows if near_climax(r,d,v)]
        cw=100*sum(r["win"] for r in cut)/len(cut) if cut else None
        kept=[r for r in rows if not near_climax(r,d,v)]
        kwr=100*sum(r["win"] for r in kept)/len(kept)
        rowline.append(f"d<={d},v>={v}: cutWR={cw:.1f}(n{len(cut)}) keepWR={kwr:.2f}")
    p("  "+" | ".join(rowline))

with open("/Users/cristrein/tradingview-mcp/research/xau_15m_bb_nas_leonardo/_reopt5_DA_verify.out.txt","w") as fh:
    fh.write("\n".join(out))

# ---- appended: C1 per-block detail (materialized, not inline) ----
def _c1(r):
    return near_climax(r) or macro_bear(r) or nas_after(r)
_kept=[r for r in rows if not _c1(r)]
_m=L.metrics(_kept,rows)
print("\nC1 per-block (n,wr_keep) vs base:")
for b in L.BLOCK_ORDER:
    print("  ",b,_m["block_detail"][b],"base",L.BLOCK_BASE[b])
