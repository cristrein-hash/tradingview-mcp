"""
_reopt5_cutwhen.py — CUT-when (loser-dense pocket removal) hunt, VOL/session lens.

Design: KEEP-AND combos cut >90% of winners -> fail the >=85% winner gate by construction.
The robust path for a WR-lift that KEEPS >=85% winners is to CUT only small loser-dense
pockets. We build loser-dense atomic predicates (where WR << base), then OR-union 1-3 of
them (a row is CUT if ANY clause fires). Removing the union should lift WR on every year
and >=6/8 blocks while keeping >=85% winners and lowering max losing streak.

Lens loser pockets (from single scan): is_london_open=1 (WR53.3), vpnode near node,
killzone=1 mildly worse, vol_climax high mildly worse. Combined with cross-lens loser
flags absorption=1, macro_bear=1, naslong_after_smc=1, low h1 alignment to strengthen.

A clause is a (name, predicate, observed cut-pocket WR). We greedily and exhaustively
search unions of CUT clauses for robust gate pass.
RAW-causal; CUT predicates use signal-bar state only.
"""
import sys, itertools, json
sys.path.insert(0, "/Users/cristrein/tradingview-mcp/research/xau_15m_bb_nas_leonardo")
import _reopt5_lib as L

rows = L.load()
BASE_STREAK = L.max_losing_streak(rows)
out=[]
def p(s): out.append(str(s)); print(s)

def wr_of(sub):
    return (100*sum(r["win"] for r in sub)/len(sub), len(sub)) if sub else (None,0)

# ---- candidate CUT clauses (fire => remove row). Build broad, measure cut-pocket WR. ----
CUT = {
  # VOL/session lens
  "london":        lambda r: r.get("is_london_open")==1,
  "vpnode_near2":  lambda r: r.get("vpnode_dist_atr",9)<=2.0,
  "vpnode_near1":  lambda r: r.get("vpnode_dist_atr",9)<=1.0,
  "killzone":      lambda r: r.get("killzone")==1,
  "atr_lo":        lambda r: r.get("atr_regime",9)<=0.9,
  "climax_hi":     lambda r: r.get("vol_climax",0)>=1.8,
  # session+vol conjunctions (lens-internal context)
  "london_killz":  lambda r: r.get("is_london_open")==1 and r.get("killzone")==1,
  "near_climax":   lambda r: r.get("vpnode_dist_atr",9)<=2.0 and r.get("vol_climax",0)>=1.5,
  "near_killz":    lambda r: r.get("vpnode_dist_atr",9)<=1.5 and r.get("killzone")==1,
  "london_climax": lambda r: r.get("is_london_open")==1 and r.get("vol_climax",0)>=1.5,
  # cross-lens loser flags (allowed: causal, not forbidden)
  "macro_bear":    lambda r: r.get("macro_bear")==1,
  "nas_after_smc": lambda r: r.get("naslong_after_smc")==1,
  "absorb":        lambda r: r.get("absorption")==1,
  # session x structure
  "london_h1down": lambda r: r.get("is_london_open")==1 and r.get("h1_trend",0)<0,
  "near_h1down":   lambda r: r.get("vpnode_dist_atr",9)<=2.0 and r.get("h1_trend",0)<0,
}

p("CUT-pocket WR (lower=better cut target). base WR %.2f streak %d"%(L.BASE_WR,BASE_STREAK))
for nm,fn in CUT.items():
    w,n=wr_of([r for r in rows if fn(r)])
    p(f"  {nm:14s} cutWR={w:.1f} n={n}" if w is not None else f"  {nm}: empty")

def eval_union(clauses):
    fns=[CUT[c] for c in clauses]
    kept=[r for r in rows if not any(f(r) for f in fns)]
    m=L.metrics(kept,rows)
    if m is None: return None
    m["robust"]=L.is_robust(m) and m["streak_keep"]<=BASE_STREAK
    m["clauses"]=clauses
    return m

names=list(CUT)
results=[]
# singles, pairs, triples (OR-union of CUTs)
for k in (1,2,3):
    for combo in itertools.combinations(names,k):
        m=eval_union(combo)
        if m: results.append(m)

p("="*80); p("ALL CUT-UNIONS passing robust gate (WR>base, all yrs>=base, winK>=85, blk>=6, streak<=base):")
robs=[m for m in results if m["robust"]]
robs.sort(key=lambda m:(-m["wr_keep"]))
for m in robs:
    p(f"  *** CUT {'|'.join(m['clauses'])}: n={m['n_keep']} WR={m['wr_keep']} winK={m['winners_kept_pct']}% "
      f"losC={m['losers_cut_pct']}% streak{m['streak_keep']} yr={m['by_year']} blk{m['blocks_ok']}/8 avgR={m['avgR']}")
p(f"TOTAL robust unions: {len(robs)}  (tested {len(results)} unions)")

p("="*80); p("Top 12 by WR with winK>=85 (robust or not):")
cand=[m for m in results if m["winners_kept_pct"]>=85]
cand.sort(key=lambda m:-m["wr_keep"])
for m in cand[:12]:
    p(f"  CUT {'|'.join(m['clauses'])}: WR={m['wr_keep']} n={m['n_keep']} winK={m['winners_kept_pct']}% "
      f"streak{m['streak_keep']} yr={m['by_year']} blk{m['blocks_ok']}/8 streakOK={m['streak_keep']<=BASE_STREAK} ROBUST={m['robust']}")

with open("/Users/cristrein/tradingview-mcp/research/xau_15m_bb_nas_leonardo/_reopt5_cutwhen.out.txt","w") as fh:
    fh.write("\n".join(out))
# stash robust + top for downstream verification
json.dump([{k:v for k,v in m.items() if k not in("block_detail",)} for m in robs],
          open("/Users/cristrein/tradingview-mcp/research/xau_15m_bb_nas_leonardo/_reopt5_cutwhen_robust.json","w"),indent=1,default=str)
