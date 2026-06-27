"""
_reopt5_volsession.py — VOL/session lens re-optimization on the 5ATR base (n=3047).

Two jobs:
 (A) RE-TEST the 8ATR-calibrated families on the 5ATR base directly:
     - R2 KEEP (multi-TF eff/pos) as a KEEP filter
     - R_B sell-exhaustion CUT (mapped to 5ATR feature names: vol_low_vs_med~low_vol_rel)
 (B) HUNT new VOL/session combos (2-3 contextual) that lift WR with stability.

Lens features: atr_regime, vol_low_vs_med, vol_climax, vpnode_dist_atr,
               is_london_open, is_ny_overlap, is_deadzone, killzone.
A combo can be KEEP-when (positive) or CUT-when (loser-dense removed).
Robust gate = _reopt5_lib.is_robust + streak_keep <= base streak.
RAW-causal: all features are signal-bar state, no R/win/cj/low_idx.
"""
import sys, itertools, json
sys.path.insert(0, "/Users/cristrein/tradingview-mcp/research/xau_15m_bb_nas_leonardo")
import _reopt5_lib as L

rows = L.load()
SENT = -10000000.0
out = []
def p(s): out.append(str(s)); print(s)

def show(name, kept):
    m = L.metrics(kept, rows)
    if m is None:
        p(f"{name}: EMPTY"); return None
    rob = L.is_robust(m) and m["streak_keep"] <= L.max_losing_streak(rows)
    p(f"{name}\n  n={m['n_keep']} WR={m['wr_keep']}(b{L.BASE_WR}) avgR={m['avgR']} sumR={m['sumR']} "
      f"streak {m['streak_base']}->{m['streak_keep']} winK={m['winners_kept_pct']}% losC={m['losers_cut_pct']}%\n  "
      f"yr={m['by_year']} (b{L.YEAR_BASE}) blkOK={m['blocks_ok']}/8 STREAK_ROBUST={m['streak_keep']<=m['streak_base']} ROBUST={rob}")
    m["robust"]=rob; m["name"]=name
    return m

# ---------- (A) re-test inherited families ----------
p("="*80); p("(A) INHERITED 8ATR FAMILIES ON 5ATR BASE")

# R2 KEEP: multi-TF efficiency/position. Original kept rows with confirming higher-TF
# alignment. Map: h1_trend>=0 (not down) and h1_eff/h1_pos confirming + hd alignment.
# We test a few reasonable KEEP forms.
def r2_keep_a(r):  # multi-TF up-efficiency
    return r["h1_trend"]>=0 and r["h1_eff"]>=0.2
def r2_keep_b(r):
    return r["h1_pos"]>=1.0 and r["h1_trend"]>=0
show("R2a KEEP h1_trend>=0 & h1_eff>=0.2", [r for r in rows if r2_keep_a(r)])
show("R2b KEEP h1_pos>=1.0 & h1_trend>=0", [r for r in rows if r2_keep_b(r)])

# R_B sell-exhaustion CUT (map low_vol_rel -> vol_low_vs_med):
def rb_cut(r):
    c1 = r.get("absorption")==1 and r.get("sell_decel")==0
    c2 = r.get("buy_sell_ratio4",0)>7 and r.get("vol_low_vs_med",0)>1.37
    c3 = r.get("regime_age_h",1e9)<=25.2 and r.get("sell_skew_mig",0)>0
    return c1 or c2 or c3
show("R_B CUT (sell-exhaustion, vol_low_vs_med>1.37)", [r for r in rows if not rb_cut(r)])

# ---------- (B) VOL/session single + combo hunt ----------
p("="*80); p("(B) VOL/SESSION COMBO HUNT")

# Build candidate atomic predicates (KEEP-direction friendly), each returns bool.
# numeric thresholds chosen from decile scan; binaries direct.
ATOMS = {
  # KEEP-positive lens atoms
  "deadzone":      lambda r: r.get("is_deadzone")==1,
  "not_london":    lambda r: r.get("is_london_open")==0,
  "atr_hi":        lambda r: r.get("atr_regime",0)>=1.29,
  "atr_mid_hi":    lambda r: r.get("atr_regime",0)>=1.13,
  "vpnode_far":    lambda r: r.get("vpnode_dist_atr",-9)>=4.0,
  "vpnode_far5":   lambda r: r.get("vpnode_dist_atr",-9)>=4.75,
  "not_killzone":  lambda r: r.get("killzone")==0,
  "vol_calm":      lambda r: r.get("vol_low_vs_med",9)<=1.0,
  "not_climax":    lambda r: r.get("vol_climax",9)<=1.2,
}

p("-- single atoms (KEEP) --")
single={}
for nm,fn in ATOMS.items():
    m=show(f"KEEP {nm}", [r for r in rows if fn(r)])
    single[nm]=m

# pairwise KEEP (intersection)
p("-- pairwise KEEP (AND) --")
pair_results=[]
names=list(ATOMS)
for a,b in itertools.combinations(names,2):
    kept=[r for r in rows if ATOMS[a](r) and ATOMS[b](r)]
    m=show(f"KEEP {a} & {b}", kept)
    if m: pair_results.append(m)

# triple KEEP
p("-- triple KEEP (AND) --")
tri_results=[]
for a,b,c in itertools.combinations(names,3):
    kept=[r for r in rows if ATOMS[a](r) and ATOMS[b](r) and ATOMS[c](r)]
    m=show(f"KEEP {a}&{b}&{c}", kept)
    if m: tri_results.append(m)

# ---------- summary: robust finds ----------
p("="*80); p("ROBUST=TRUE FINDS (VOL/session):")
allm = [m for m in (list(single.values())+pair_results+tri_results) if m]
robs=[m for m in allm if m["robust"]]
robs.sort(key=lambda m:(-m["wr_keep"]))
for m in robs:
    p(f"  *** {m['name']}: WR={m['wr_keep']} n={m['n_keep']} winK={m['winners_kept_pct']}% "
      f"streak{m['streak_keep']} yr={m['by_year']} blk{m['blocks_ok']}/8")
if not robs:
    p("  NONE robust under full gate. Best by WR with winK>=85:")
    cand=[m for m in allm if m["winners_kept_pct"]>=85]
    cand.sort(key=lambda m:-m["wr_keep"])
    for m in cand[:6]:
        p(f"  ~ {m['name']}: WR={m['wr_keep']} n={m['n_keep']} winK={m['winners_kept_pct']}% "
          f"streak{m['streak_keep']} yr={m['by_year']} blk{m['blocks_ok']}/8 streakOK={m['streak_keep']<=L.max_losing_streak(rows)}")

with open("/Users/cristrein/tradingview-mcp/research/xau_15m_bb_nas_leonardo/_reopt5_volsession.out.txt","w") as fh:
    fh.write("\n".join(out))
